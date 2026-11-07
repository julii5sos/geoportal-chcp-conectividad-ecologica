import unittest

from territorio_busqueda import (
    buscar_territorios,
    catalogo_territorial,
    obtener_territorio,
    resumen_territorial,
)


class TerritorySearchTests(unittest.TestCase):
    def test_catalog_has_basin_and_53_unique_subbasins(self):
        catalog = catalogo_territorial()
        self.assertEqual(len({item["id"] for item in catalog}), len(catalog))
        self.assertEqual(sum(item["tipo"] == "subcuenca" for item in catalog), 53)
        self.assertEqual(sum(item["tipo"] == "corredor" for item in catalog), 22)

    def test_corridors_are_searchable_and_have_real_geometry(self):
        result = buscar_territorios("corredor biologico mesoamericano")
        self.assertTrue(any(item["tipo"] == "corredor" for item in result))
        corridor = obtener_territorio(next(item["id"] for item in result if item["tipo"] == "corredor"))
        self.assertIn(corridor["geometry"]["type"], {"Polygon", "MultiPolygon"})

    def test_search_ignores_accents_case_and_accepts_partial_terms(self):
        by_case = buscar_territorios("MIRAFLORES")
        by_accent = buscar_territorios("canal de panama")
        self.assertTrue(any("Miraflores" in item["nombre"] for item in by_case))
        self.assertTrue(any(item["id"] == "cuenca:chcp" for item in by_accent))

    def test_unknown_identifier_is_rejected(self):
        with self.assertRaises(KeyError):
            obtener_territorio("subcuenca:no-existe")

    def test_summary_keeps_scientific_values_explicitly_uncalculated(self):
        summary = resumen_territorial("cuenca:chcp")
        self.assertGreater(summary["area_ha"], 0)
        self.assertEqual(summary["scientific_indicators"]["status"], "not_calculated")
        self.assertNotIn("forest_ha", summary)
        self.assertEqual(summary["metadata"]["area_crs"], "EPSG:8857")


if __name__ == "__main__":
    unittest.main()
