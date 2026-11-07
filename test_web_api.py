import io
import os
import unittest
import zipfile
from unittest.mock import patch

from webapp.cache import ResultCache
from webapp.main import create_app
from webapp import service


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.client = self.app.test_client()

    def test_health_uses_new_gee_project_without_initializing_remote_service(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["project_id"], "geoportal-513817")
        self.assertEqual(response.json["earth_engine"], "lazy")

    def test_config_exposes_only_real_years_and_preserves_eri_weights(self):
        response = self.client.get("/api/v1/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["sources"]["jrc_tmf"]["years"][0], 1990)
        self.assertEqual(response.json["sources"]["jrc_tmf"]["years"][-1], 2025)
        self.assertEqual(response.json["sources"]["esri_lulc"]["years"], list(range(2017, 2026)))
        self.assertEqual(response.json["sources"]["integrated"]["years"], list(range(2017, 2026)))
        self.assertIn("concordancia_estado", response.json["symbology"])
        self.assertEqual(
            response.json["eri"]["weights"],
            {
                "integridad_estructural": 0.35,
                "conectividad": 0.25,
                "estabilidad_topografica": 0.2,
                "proximidad_riparia": 0.2,
            },
        )

    def test_territory_is_local_and_contains_subbasins(self):
        response = self.client.get("/api/v1/territory")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["basin"]["geometry"]["type"], "Polygon")
        self.assertGreater(len(response.json["subbasins"]["features"]), 10)
        self.assertGreater(len(response.json["corridors"]["features"]), 0)
        self.assertGreater(len(response.json["critical_points"]["features"]), 0)

    def test_search_summary_and_source_catalog_are_traceable(self):
        search = self.client.get("/api/v1/territories/search?q=miraflores")
        self.assertEqual(search.status_code, 200)
        self.assertTrue(any("Miraflores" in item["nombre"] for item in search.json["results"]))
        identifier = search.json["results"][0]["id"]
        summary = self.client.get(f"/api/v1/territories/{identifier}/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json["scientific_indicators"]["status"], "not_calculated")
        catalog = self.client.get("/api/v1/catalog/sources")
        self.assertEqual(catalog.status_code, 200)
        by_key = {item["clave"]: item for item in catalog.json["sources"]}
        self.assertEqual(by_key["jrc_tmf"]["estado_html"], "Integrada y operativa")
        self.assertEqual(by_key["sinia_1992_2000"]["estado_html"], "No disponible")

    @patch("webapp.main.run_analysis")
    def test_integrated_analysis_is_accepted_by_contract(self, run_analysis):
        run_analysis.return_value = {"result_id": "c" * 32, "kind": "integrated_analysis"}
        response = self.client.post(
            "/api/v1/analyses",
            json={
                "analyses": ["coverage", "fragmentation", "connectivity"],
                "area": {"mode": "basin"},
                "source": "integrated",
                "initial_year": 2020,
                "final_year": 2025,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["kind"], "integrated_analysis")

    def test_analysis_request_is_validated_before_engine(self):
        response = self.client.post(
            "/api/v1/analyses",
            json={
                "analyses": ["coverage"],
                "area": {"mode": "basin"},
                "source": "invented_source",
                "initial_year": 2020,
                "final_year": 2025,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Revise", response.json["error"])

    @patch("webapp.main.run_analysis")
    def test_analysis_endpoint_returns_only_engine_result(self, run_analysis):
        run_analysis.return_value = {
            "result_id": "a" * 32,
            "kind": "temporal_analysis",
            "result": {"anio_inicial": 2020, "anio_final": 2025},
        }
        response = self.client.post(
            "/api/v1/analyses",
            json={
                "analyses": ["coverage", "fragmentation"],
                "area": {"mode": "basin"},
                "source": "jrc_tmf",
                "initial_year": 2020,
                "final_year": 2025,
                "maximum_distance_m": 500,
                "minimum_patch_area_ha": 0,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["result_id"], "a" * 32)
        run_analysis.assert_called_once()

    def test_security_headers_are_present(self):
        response = self.client.get("/")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        self.assertTrue(response.headers["X-Request-ID"])

    def test_analysis_rejects_cross_site_browser_request(self):
        response = self.client.post(
            "/api/v1/analyses",
            json={"analyses": ["coverage"], "area": {"mode": "basin"}, "source": "jrc_tmf", "initial_year": 2020, "final_year": 2025},
            headers={"Origin": "https://example.invalid", "Sec-Fetch-Site": "cross-site"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["code"], "cross_site")

    def test_analysis_requires_json_content_type(self):
        response = self.client.post("/api/v1/analyses", data="not-json")
        self.assertEqual(response.status_code, 415)

    def test_busy_instance_returns_retryable_429(self):
        gate = self.app.extensions["chcp_analysis_gate"]
        self.assertTrue(gate.acquire())
        try:
            response = self.client.post(
                "/api/v1/analyses",
                json={"analyses": ["coverage"], "area": {"mode": "basin"}, "source": "jrc_tmf", "initial_year": 2020, "final_year": 2025},
            )
        finally:
            gate.release()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json["code"], "busy")
        self.assertEqual(response.headers["Retry-After"], "15")

    def test_analysis_rate_limit_is_bounded_per_instance(self):
        with patch.dict(os.environ, {"WEB_ANALYSIS_RATE_LIMIT": "1", "WEB_RATE_LIMIT_WINDOW_SECONDS": "600"}):
            app = create_app(testing=True)
        client = app.test_client()
        payload = {"analyses": ["coverage"], "area": {"mode": "basin"}, "source": "jrc_tmf", "initial_year": 2020, "final_year": 2025}
        with patch("webapp.main.run_analysis", return_value={"result_id": "b" * 32}):
            first = client.post("/api/v1/analyses", json=payload)
            second = client.post("/api/v1/analyses", json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json["code"], "rate_limit")
        self.assertGreater(int(second.headers["Retry-After"]), 0)

    def test_cache_deduplicates_equal_scientific_requests(self):
        cache = ResultCache(max_entries=2, ttl_seconds=60)
        calls = []

        def operation():
            calls.append(True)
            return {"value": 1}

        first, first_hit = cache.run_once({"source": "jrc"}, operation)
        second, second_hit = cache.run_once({"source": "jrc"}, operation)
        self.assertFalse(first_hit)
        self.assertTrue(second_hit)
        self.assertEqual(first.identifier, second.identifier)
        self.assertEqual(len(calls), 1)

    def test_cache_indexes_latest_result_by_territory(self):
        cache = ResultCache(max_entries=2, ttl_seconds=60)
        item, _ = cache.run_once({"source": "jrc"}, lambda: {"value": 1}, territory_key="subcuenca:test")
        self.assertEqual(cache.latest("subcuenca:test").identifier, item.identifier)

    def test_cache_releases_signature_lock_after_failed_operation(self):
        cache = ResultCache(max_entries=2, ttl_seconds=60)

        with self.assertRaises(RuntimeError):
            cache.run_once({"source": "jrc"}, lambda: (_ for _ in ()).throw(RuntimeError("falló")))

        self.assertEqual(cache._locks, {})
        item, hit = cache.run_once({"source": "jrc"}, lambda: {"value": 2})
        self.assertFalse(hit)
        self.assertEqual(item.value["value"], 2)

    @patch("webapp.main.public_cached_result")
    def test_cached_result_endpoint_returns_exact_result(self, public_cached_result):
        public_cached_result.return_value = {"result_id": "e" * 32, "kind": "temporal_analysis"}
        response = self.client.get(f"/api/v1/results/{'e' * 32}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["result_id"], "e" * 32)

    @patch("webapp.main.latest_result")
    def test_latest_territory_result_has_explicit_empty_state(self, latest_result):
        latest_result.return_value = None
        response = self.client.get("/api/v1/territories/subcuenca:test/results/latest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"result": None, "status": "not_calculated"})

    @patch("webapp.main.run_evidence")
    def test_complementary_evidence_endpoint_uses_real_contract(self, run_evidence):
        run_evidence.return_value = {"result_id": "d" * 32, "kind": "complementary_evidence"}
        response = self.client.post("/api/v1/evidence", json={"source":"hansen_gfc","area":{"mode":"basin"},"initial_year":2020,"final_year":2025})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["kind"], "complementary_evidence")

    def test_complementary_download_identifies_its_own_methodology(self):
        item, _ = service._CACHE.run_once(
            {"test": "evidence-download"},
            lambda: {
                "kind": "complementary_evidence",
                "source_key": "hansen_gfc",
                "area": {"geometry": {"type": "Polygon", "coordinates": []}},
                "result": {"source": "Hansen Global Forest Change v1.13", "asset": "UMD/hansen/test"},
            },
        )
        content = service.build_download(item.identifier)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            methodology = archive.read("METODOLOGIA.txt").decode("utf-8")
        self.assertIn("evidencia complementaria", methodology)
        self.assertIn("Hansen Global Forest Change", methodology)
        self.assertNotIn("reutilizan analisis_temporal.py", methodology)


if __name__ == "__main__":
    unittest.main()

