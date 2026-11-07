import unittest

from analisis_complementario import analizar_hansen, analizar_ndvi, ejecutar_evidencia


class AnalisisComplementarioTests(unittest.TestCase):
    def test_hansen_rejects_years_outside_product_availability_before_ee(self):
        with self.assertRaisesRegex(ValueError, "2001 y 2025"):
            analizar_hansen({}, 2000, 2025, ee_module=None)

    def test_ndvi_requires_two_valid_sentinel_years_before_ee(self):
        with self.assertRaisesRegex(ValueError, "2017 y 2026"):
            analizar_ndvi({}, 2016, 2025, ee_module=None)
        with self.assertRaises(ValueError):
            analizar_ndvi({}, 2025, 2025, ee_module=None)

    def test_pending_sources_do_not_generate_fictitious_results(self):
        with self.assertRaisesRegex(ValueError, "pendiente"):
            ejecutar_evidencia("firms", {}, None, None, {}, ee_module=None)
        with self.assertRaisesRegex(ValueError, "no está configurado"):
            ejecutar_evidencia("sinia_2021", {}, None, None, {}, ee_module=None)


if __name__ == "__main__":
    unittest.main()
