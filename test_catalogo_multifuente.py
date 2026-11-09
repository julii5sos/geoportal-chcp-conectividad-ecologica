import unittest

from catalogo_multifuente import ESTADOS, FUENTES_TRAZABILIDAD, matriz_trazabilidad


class SourceCatalogTests(unittest.TestCase):
    def test_every_source_has_a_declared_valid_state(self):
        rows = matriz_trazabilidad()
        self.assertGreaterEqual(len(rows), 10)
        for row in rows:
            self.assertIn(row["estado_html"], ESTADOS)
            self.assertTrue(row["nombre_oficial"])
            self.assertTrue(row["limitaciones"])

    def test_primary_sources_are_operational_but_historic_demo_is_not(self):
        self.assertEqual(FUENTES_TRAZABILIDAD["jrc_tmf"].estado_html, "Integrada y operativa")
        self.assertEqual(FUENTES_TRAZABILIDAD["esri_lulc"].estado_html, "Integrada y operativa")
        self.assertEqual(FUENTES_TRAZABILIDAD["sinia_1992_2000"].estado_html, "No disponible")

    def test_catalog_does_not_present_radd_as_implemented(self):
        source = FUENTES_TRAZABILIDAD["glad_radd"]
        self.assertIsNone(source.identificador)
        self.assertEqual(source.estado_html, "No disponible")


if __name__ == "__main__":
    unittest.main()
