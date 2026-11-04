import unittest

from streamlit.testing.v1 import AppTest

from geoportal_componentes import (
    FUENTES_PANEL,
    LEYENDAS_PANEL,
    calcular_area_geojson_ha,
)


class ComponentesGeoportalTests(unittest.TestCase):
    def test_panel_reune_las_fuentes_solicitadas(self):
        claves = {clave for clave, _ in FUENTES_PANEL}
        self.assertEqual(
            claves,
            {
                "jrc_tmf",
                "hansen_gfc",
                "esri_lulc",
                "sentinel_ndvi",
                "gedi",
                "bosque_2021",
                "eri",
            },
        )
        self.assertEqual(claves, set(LEYENDAS_PANEL))
        self.assertTrue(all(LEYENDAS_PANEL[clave] for clave in claves))

    def test_area_geodesica_no_usa_grados_cuadrados(self):
        cuadrado_aproximado_un_km = {
            "type": "Polygon",
            "coordinates": [[
                [-79.7000, 9.0000],
                [-79.6909, 9.0000],
                [-79.6909, 9.0090],
                [-79.7000, 9.0090],
                [-79.7000, 9.0000],
            ]],
        }
        area_ha = calcular_area_geojson_ha(cuadrado_aproximado_un_km)
        self.assertGreater(area_ha, 90)
        self.assertLess(area_ha, 110)

    def test_explorar_sin_motor_mantiene_controles_reales_y_orden_publico(self):
        app = AppTest.from_file("app.py", default_timeout=60)
        app.query_params["seccion"] = "explorar"
        app.run()

        self.assertFalse(app.exception)
        self.assertEqual(
            [pestana.label for pestana in app.tabs],
            ["Capas", "Polígono", "Mapa base"],
        )
        unidad = next(
            selector for selector in app.selectbox if selector.label == "Unidad territorial"
        )
        self.assertEqual(
            unidad.options,
            [
                "Dibujar un área en el mapa",
                "Subcuenca de la CHCP",
                "Toda la cuenca (análisis regional)",
            ],
        )
        self.assertEqual(unidad.value, "Dibujar un área en el mapa")
        ejecutar = next(
            boton for boton in app.button if boton.label == "Realizar análisis"
        )
        self.assertTrue(ejecutar.disabled)
        self.assertTrue(
            any("Earth Engine" in aviso.value for aviso in app.warning),
            "El portal debe explicar por qué no ejecuta cálculos sin credenciales.",
        )

    def test_comparar_ofrece_solo_fuentes_y_anios_compatibles(self):
        app = AppTest.from_file("app.py", default_timeout=60)
        app.query_params["seccion"] = "comparar"
        app.run()

        self.assertFalse(app.exception)
        fuente = next(
            selector for selector in app.selectbox if selector.label == "Fuente comparable"
        )
        self.assertEqual(
            fuente.options,
            [
                "JRC Tropical Moist Forest",
                "ESRI Land Use / Land Cover",
                "Sentinel-2 / NDVI",
            ],
        )
        inicial = next(
            selector for selector in app.selectbox if selector.label == "Año inicial"
        )
        final = next(
            selector for selector in app.selectbox if selector.label == "Año final"
        )
        self.assertEqual(inicial.options[0], "1990")
        self.assertEqual(inicial.options[-1], "2024")
        self.assertEqual(final.options[-1], "2025")
        self.assertGreater(final.value, inicial.value)

    def test_resultados_no_inventa_indicadores_antes_del_analisis(self):
        app = AppTest.from_file("app.py", default_timeout=60)
        app.query_params["seccion"] = "resultados"
        app.run()

        self.assertFalse(app.exception)
        contenido = "\n".join(bloque.value for bloque in app.markdown)
        self.assertIn("Todavía no existe una ejecución", contenido)
        self.assertNotIn("Índice de indicios", contenido)
        self.assertNotIn("ERI calculado", contenido)


if __name__ == "__main__":
    unittest.main()
