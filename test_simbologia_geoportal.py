import unittest

from simbologia_geoportal import CONCORDANCIA_CAMBIO, CONCORDANCIA_ESTADO, TRANSICIONES_FORESTALES


class SymbologyTests(unittest.TestCase):
    def test_transition_palette_has_stable_semantics(self):
        self.assertEqual(TRANSICIONES_FORESTALES["perdida_bosque"]["color"], "#D94438")
        self.assertEqual(TRANSICIONES_FORESTALES["ganancia_bosque"]["color"], "#76B852")
        self.assertNotEqual(
            TRANSICIONES_FORESTALES["perdida_bosque"]["color"],
            TRANSICIONES_FORESTALES["ganancia_bosque"]["color"],
        )

    def test_concordance_codes_and_colors_are_unique(self):
        for catalog in (CONCORDANCIA_ESTADO, CONCORDANCIA_CAMBIO):
            self.assertEqual(len(catalog), len(set(catalog)))
            self.assertEqual(len(catalog), len({item["color"] for item in catalog.values()}))
            self.assertTrue(all(item["etiqueta"] for item in catalog.values()))


if __name__ == "__main__":
    unittest.main()
