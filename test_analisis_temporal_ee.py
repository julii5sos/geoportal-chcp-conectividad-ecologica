"""Pruebas de integración opcionales con Google Earth Engine.

Ejecutar únicamente en un entorno autorizado:
  $env:RUN_EE_INTEGRATION="1"
  $env:EE_PROJECT="mi-proyecto"
  python -m unittest test_analisis_temporal_ee -v
"""

import os
import unittest


@unittest.skipUnless(
    os.environ.get("RUN_EE_INTEGRATION") == "1",
    "Requiere RUN_EE_INTEGRATION=1 y credenciales de Earth Engine.",
)
class AnalisisTemporalEarthEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ee

        cls.ee = ee
        ee.Initialize(project=os.environ["EE_PROJECT"])

    def test_jrc_2020_2025_devuelve_pixeles_validos(self):
        from analisis_temporal import construir_cobertura_bosque_ee

        area = self.ee.Geometry.Rectangle([-79.57, 9.03, -79.55, 9.05])
        for anio in (2020, 2025):
            mascara = construir_cobertura_bosque_ee(
                "jrc_tmf", anio, area, ee_module=self.ee
            )
            conteo = mascara.unmask(0).reduceRegion(
                reducer=self.ee.Reducer.count(),
                geometry=area,
                scale=30,
                maxPixels=1e7,
            ).get(f"bosque_{anio}").getInfo()
            self.assertGreater(int(conteo), 0)

    def test_esri_2020_2025_existe_como_serie_separada(self):
        from analisis_temporal import construir_cobertura_bosque_ee

        area = self.ee.Geometry.Rectangle([-79.57, 9.03, -79.55, 9.05])
        for anio in (2020, 2025):
            imagen = construir_cobertura_bosque_ee(
                "esri_lulc", anio, area, ee_module=self.ee
            )
            self.assertEqual(imagen.bandNames().getInfo(), [f"bosque_{anio}"])


if __name__ == "__main__":
    unittest.main()
