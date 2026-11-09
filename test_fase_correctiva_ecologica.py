import unittest
from unittest.mock import patch
from pathlib import Path

from catalogo_assets_sinia import ASSETS_SINIA
from estructura_cobertura import SOURCE_2021, StructuralCoverageUnavailable

from webapp.main import create_app
from webapp import service
from webapp.cache import ResultCache
from webapp.models import (
    EcologicalEvaluationRequest,
    IntegratedEvaluationRequest,
    OfficialCoverageRequest,
    StructuralComparisonRequest,
    StructuralConnectivityRequest,
)


AREA = {"mode": "basin"}


class CorrectiveApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(testing=True).test_client()

    def test_contracts_accept_supported_area(self):
        self.assertEqual(EcologicalEvaluationRequest.model_validate({"area": AREA}).area.mode, "basin")
        self.assertEqual(IntegratedEvaluationRequest.model_validate({"area": AREA}).maximum_distance_m, 500)
        self.assertEqual(OfficialCoverageRequest.model_validate({"area": AREA}).area.mode, "basin")
        structural = StructuralConnectivityRequest.model_validate({"area": AREA, "scenario": "official_2021"})
        self.assertEqual(structural.maximum_distance_m, 500)
        comparison = StructuralComparisonRequest.model_validate({"area": AREA})
        self.assertEqual(comparison.maximum_distance_m, 500)

    @patch("webapp.main.run_ecological_evaluation")
    def test_ecological_endpoint_is_real_and_guarded(self, operation):
        operation.return_value = {"result_id": "a" * 32, "kind": "ecological_evaluation"}
        response = self.client.post("/api/v1/evaluations/ecological", json={"area": AREA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "ecological_evaluation")
        operation.assert_called_once()

    @patch("webapp.main.run_official_coverage")
    def test_official_coverage_endpoint_is_real_and_guarded(self, operation):
        operation.return_value = {"result_id": "b" * 32, "kind": "official_coverage_2023"}
        response = self.client.post("/api/v1/official-coverages/2023", json={"area": AREA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "official_coverage_2023")
        operation.assert_called_once()

    @patch("webapp.main.run_official_coverage_2021")
    def test_official_coverage_2021_uses_independent_route(self, operation):
        operation.return_value = {"result_id": "e" * 32, "kind": "official_coverage_2021"}
        response = self.client.post("/api/v1/official-coverages/2021", json={"area": AREA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "official_coverage_2021")
        operation.assert_called_once()

    def test_new_endpoints_reject_non_json(self):
        for path in ("/api/v1/evaluations/ecological", "/api/v1/official-coverages/2021", "/api/v1/official-coverages/2023", "/api/v1/structural-connectivity"):
            response = self.client.post(path, data="invalid")
            self.assertEqual(response.status_code, 415)

    def test_structural_asset_is_centralized_on_the_official_vector(self):
        expected = "projects/geoportal-513817/assets/SINIA_2021_COBERTURA_GENERAL_VECTOR"
        self.assertEqual(ASSETS_SINIA["2021_general"]["asset_id"], expected)
        self.assertEqual(SOURCE_2021, expected)

    def test_official_2021_detailed_catalog_keeps_all_documented_codes(self):
        legend = ASSETS_SINIA["2021_detallado"]["leyenda"]
        self.assertEqual(set(legend), set(range(1, 34)))
        self.assertIn("sin documentación", legend[33])

    @patch("webapp.main.run_structural_connectivity")
    def test_structural_asset_failure_returns_compact_public_message(self, operation):
        operation.side_effect = StructuralCoverageUnavailable(
            "detalle interno projects/geoportal-513817/assets/asset-restringido"
        )
        response = self.client.post(
            "/api/v1/structural-connectivity",
            json={"area": AREA, "scenario": "official_2021"},
        )
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error"], StructuralCoverageUnavailable.public_message)
        self.assertNotIn("projects/", body["error"])

    @patch("webapp.main.run_structural_connectivity")
    def test_structural_endpoint_preserves_scenario(self, operation):
        operation.return_value = {"result_id": "c" * 32, "kind": "structural_connectivity"}
        response = self.client.post("/api/v1/structural-connectivity", json={"area": AREA, "scenario": "diagnostic_2023"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(operation.call_args.args[0].scenario, "diagnostic_2023")

    @patch("webapp.main.run_structural_comparison")
    def test_structural_comparison_has_an_explicit_guarded_route(self, operation):
        operation.return_value = {"result_id": "f" * 32, "kind": "structural_comparison_2021_2023"}
        response = self.client.post("/api/v1/structural-comparison", json={"area": AREA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "structural_comparison_2021_2023")
        operation.assert_called_once()

    @patch("webapp.main.run_integrated_evaluation")
    def test_integrated_endpoint_keeps_components_explicit(self, operation):
        operation.return_value = {"result_id": "d" * 32, "kind": "integrated_ecological_analysis"}
        response = self.client.post("/api/v1/evaluations/integrated", json={"area": AREA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["kind"], "integrated_ecological_analysis")
        self.assertEqual(
            operation.call_args.args[0].selected_components,
            ["ecological", "fragmentation", "connectivity"],
        )
        operation.assert_called_once()

    def test_integrated_contract_requires_a_real_combination(self):
        with self.assertRaises(ValueError):
            IntegratedEvaluationRequest.model_validate(
                {"area": AREA, "selected_components": ["ecological"]}
            )
        request = IntegratedEvaluationRequest.model_validate(
            {"area": AREA, "selected_components": ["ecological", "fragmentation"]}
        )
        self.assertEqual(request.selected_components, ["ecological", "fragmentation"])


class CorrectiveFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.javascript = Path("webapp/static/js/platform.js").read_text(encoding="utf-8")
        cls.template = Path("webapp/templates/platform.html").read_text(encoding="utf-8")
        cls.styles = Path("webapp/static/css/webapp.css").read_text(encoding="utf-8")

    def test_complementary_analysis_routes_are_explicit(self):
        for label in ("Preevaluación territorial", "Fragmentación", "Conectividad", "Análisis integral"):
            self.assertIn(label, self.javascript)
        self.assertIn('name="analysis-component"', self.javascript)
        self.assertIn('id="analysis-integral"', self.javascript)
        self.assertNotIn("Consultas especializadas", self.javascript)

    def test_corridors_are_added_on_initial_render(self):
        self.assertIn("activeLayers: new Set(['basin', 'corridors', 'criticalPoints'])", self.javascript)
        self.assertIn("}).addTo(map);", self.javascript)

    def test_all_calculations_start_in_the_wizard(self):
        self.assertNotIn('id="run-official-coverage"', self.template)
        self.assertNotIn('id="run-structural-2021"', self.template)
        self.assertNotIn('id="run-evidence"', self.template)
        self.assertIn('id="open-analysis"', self.template)
        self.assertIn("/api/v1/evaluations/ecological", self.javascript)
        self.assertIn("/api/v1/evaluations/integrated", self.javascript)
        self.assertIn("/api/v1/structural-connectivity", self.javascript)
        self.assertIn("/api/v1/structural-comparison", self.javascript)
        self.assertIn("Comparar conectividad 2021–2023", self.javascript)
        self.assertIn("selected_components:selectedComponents", self.javascript)
        self.assertIn("resultId:ecological.result_id", self.javascript)

    def test_asset_errors_are_compact_non_blocking_toasts(self):
        self.assertIn("max-width:min(460px,calc(100% - 36px))", self.styles)
        self.assertIn("pointer-events:none", self.styles)
        self.assertIn('.toast[data-kind="error"]', self.styles)


class SeparatedAnalysisServiceTests(unittest.TestCase):
    @patch("webapp.service.analizar_estructura_cobertura")
    @patch("webapp.service.ejecutar_evaluacion_ecologica")
    @patch("webapp.service.analizar_interseccion_corredores", return_value={})
    @patch("webapp.service._initialize_ee", return_value="geoportal-513817")
    @patch("webapp.service.resolve_area")
    def test_preevaluation_does_not_prepare_patches(
        self, resolve_area, _initialize, _corridors, evaluate, structural
    ):
        geometry = {"type": "Polygon", "coordinates": [[[-79.8, 9.0], [-79.79, 9.0], [-79.79, 9.01], [-79.8, 9.0]]]}
        resolve_area.return_value = (geometry, {"label": "Prueba", "area_ha": 1.0})
        evaluate.return_value = {"limitations": [], "structural_reference_2021": None}
        with patch.object(service, "_CACHE", ResultCache(max_entries=4, ttl_seconds=60)):
            result = service.run_ecological_evaluation(
                EcologicalEvaluationRequest(area={"mode": "basin"})
            )
        self.assertEqual(result["kind"], "ecological_evaluation")
        structural.assert_not_called()
        self.assertIsNone(evaluate.call_args.kwargs["contexto_fragmentacion"])

    @patch("webapp.service.run_structural_connectivity")
    @patch("webapp.service.run_ecological_evaluation")
    @patch("webapp.service.calcular_prioridad_visita")
    @patch("webapp.service.resolve_area")
    def test_integral_keeps_both_component_results(
        self, resolve_area, priority, ecological, structural
    ):
        geometry = {"type": "Polygon", "coordinates": [[[-79.8, 9.0], [-79.79, 9.0], [-79.79, 9.01], [-79.8, 9.0]]]}
        resolve_area.return_value = (geometry, {"label": "Prueba", "area_ha": 1.0})
        ecological.return_value = {
            "result_id": "a" * 32,
            "project_id": "geoportal-513817",
            "result": {"score": 2.0},
            "corridor_context": {},
            "warnings": ["territorial"],
        }
        structural.return_value = {
            "result_id": "b" * 32,
            "result": {"metricas_clase": {"numero_parches": 2}},
            "warnings": ["estructural"],
        }
        priority.return_value = {
            "prioridad_visita": "Alta",
            "contexto_estructural": {"disponible": True},
        }
        with patch.object(service, "_CACHE", ResultCache(max_entries=4, ttl_seconds=60)):
            result = service.run_integrated_evaluation(
                IntegratedEvaluationRequest(area={"mode": "basin"})
            )
        self.assertEqual(result["kind"], "integrated_ecological_analysis")
        self.assertEqual(result["result"]["evaluation"]["score"], 2.0)
        self.assertEqual(result["result"]["structure"]["metricas_clase"]["numero_parches"], 2)
        self.assertEqual(
            result["result"]["evaluation"]["visit_priority"]["prioridad_visita"],
            "Alta",
        )
        priority.assert_called_once_with(
            puntaje_cambios=2.0,
            contexto_corredores={},
            contexto_fragmentacion=structural.return_value["result"],
        )

    @patch("webapp.service.run_structural_connectivity")
    @patch("webapp.service.resolve_area")
    def test_structural_comparison_reuses_both_engines_without_false_delta(
        self, resolve_area, structural
    ):
        geometry = {"type": "Polygon", "coordinates": [[[-79.8, 9.0], [-79.79, 9.0], [-79.79, 9.01], [-79.8, 9.0]]]}
        resolve_area.return_value = (geometry, {"label": "Prueba", "area_ha": 1.0})
        structural.side_effect = [
            {"result_id": "1" * 32, "project_id": "geoportal-513817", "result": {"scenario": "official_2021"}, "corridor_context": {}},
            {"result_id": "2" * 32, "project_id": "geoportal-513817", "result": {"scenario": "diagnostic_2023"}, "corridor_context": {}},
        ]
        with patch.object(service, "_CACHE", ResultCache(max_entries=4, ttl_seconds=60)):
            result = service.run_structural_comparison(
                StructuralComparisonRequest(area={"mode": "basin"})
            )
        self.assertEqual(result["kind"], "structural_comparison_2021_2023")
        self.assertFalse(result["result"]["comparable_for_causal_change"])
        self.assertIsNone(result["result"]["difference_metrics"])
        self.assertEqual(result["result"]["scenarios"]["2021"]["scenario"], "official_2021")
        self.assertEqual(result["result"]["scenarios"]["2023"]["scenario"], "diagnostic_2023")
        self.assertEqual(structural.call_count, 2)


if __name__ == "__main__":
    unittest.main()
