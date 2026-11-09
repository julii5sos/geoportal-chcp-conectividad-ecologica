"""Pruebas de integración opcionales con Google Earth Engine.

Ejecutar únicamente en un entorno autorizado:
  $env:RUN_EE_INTEGRATION="1"
  $env:GEE_PROJECT_ID="geoportal-513817"
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
        from gee_config import resolver_proyecto_gee

        cls.ee = ee
        ee.Initialize(project=resolver_proyecto_gee(environ=os.environ))

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

    def test_estadisticas_jrc_respetan_mascara_comun(self):
        from analisis_temporal import calcular_estadisticas_cobertura_ee

        area = {
            "type": "Polygon",
            "coordinates": [[
                [-79.57, 9.03], [-79.55, 9.03], [-79.55, 9.05],
                [-79.57, 9.05], [-79.57, 9.03],
            ]],
        }
        resultado = calcular_estadisticas_cobertura_ee(
            fuente="jrc_tmf",
            anio_inicial=2020,
            anio_final=2025,
            area_geojson=area,
            ee_module=self.ee,
        )
        comparacion = resultado["comparacion"]
        self.assertTrue(comparacion["transiciones_consistentes"])
        self.assertGreater(comparacion["area_valida_comun_ha"], 0)
        self.assertAlmostEqual(
            comparacion["suma_transiciones_ha"],
            comparacion["area_valida_comun_ha"],
            delta=comparacion["tolerancia_ha"],
        )


if __name__ == "__main__":
    unittest.main()
