import unittest

from geoportal_catalogo import (
    FUENTES_GEOSPACIALES,
    anios_disponibles,
    filas_catalogo,
    validar_periodo,
)


class CatalogoGeoportalTests(unittest.TestCase):
    def test_fuentes_temporales_exponen_solo_anios_validos(self):
        self.assertEqual(anios_disponibles("jrc_tmf")[0], 1990)
        self.assertEqual(anios_disponibles("jrc_tmf")[-1], 2025)
        self.assertEqual(anios_disponibles("esri_lulc"), tuple(range(2017, 2026)))

    def test_periodo_invalido_no_se_sustituye_silenciosamente(self):
        with self.assertRaisesRegex(ValueError, "solo admite años"):
            validar_periodo("esri_lulc", 2016, 2024)
        with self.assertRaisesRegex(ValueError, "anterior"):
            validar_periodo("jrc_tmf", 2025, 2020)

    def test_productos_fijos_no_se_presentan_como_series(self):
        for clave in ("gedi", "bosque_2021", "eri"):
            self.assertFalse(FUENTES_GEOSPACIALES[clave].comparable)
            self.assertEqual(anios_disponibles(clave), ())
            with self.assertRaisesRegex(ValueError, "no admite comparación"):
                validar_periodo(clave, 2020, 2025)

    def test_catalogo_contiene_trazabilidad_visible(self):
        filas = filas_catalogo()
        self.assertGreaterEqual(len(filas), 7)
        self.assertTrue(all(fila["Versión"] for fila in filas))
        self.assertTrue(all(fila["Limitación"] for fila in filas))


if __name__ == "__main__":
    unittest.main()
