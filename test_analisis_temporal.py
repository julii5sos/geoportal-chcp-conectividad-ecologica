import unittest

from pyproj import Transformer
from shapely.geometry import GeometryCollection, LineString, box, mapping
from shapely.ops import transform

from analisis_temporal import (
    FUENTES_TEMPORALES,
    analizar_comparacion_geojson,
    calcular_transiciones_cobertura,
    recortar_area_a_cuenca,
    validar_solicitud_temporal,
)


class AnalisisTemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a_m = Transformer.from_crs("EPSG:4326", "EPSG:8857", always_xy=True)
        a_wgs = Transformer.from_crs("EPSG:8857", "EPSG:4326", always_xy=True)
        centro_x, centro_y = a_m.transform(-79.55, 9.05)
        cls._a_wgs = a_wgs
        cls._x = centro_x
        cls._y = centro_y

    def _geojson(self, *geometrias):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": mapping(transform(self._a_wgs.transform, geometria)),
                }
                for geometria in geometrias
            ],
        }

    def test_catalogo_separa_jrc_y_esri(self):
        jrc = FUENTES_TEMPORALES["jrc_tmf"]
        esri = FUENTES_TEMPORALES["esri_lulc"]
        self.assertEqual(jrc.clases_bosque, (1, 2, 4))
        self.assertEqual(jrc.resolucion_m, 30)
        self.assertEqual(esri.clases_bosque, (2,))
        self.assertEqual(esri.resolucion_m, 10)
        self.assertNotEqual(jrc.definicion_bosque, esri.definicion_bosque)

    def test_periodo_inexistente_no_se_sustituye(self):
        with self.assertRaisesRegex(ValueError, "solo admite años"):
            validar_solicitud_temporal("esri_lulc", 2010, 2025, 500, 0.1)
        with self.assertRaisesRegex(ValueError, "anterior"):
            validar_solicitud_temporal("jrc_tmf", 2025, 2020, 500, 0.1)

    def test_comparacion_sintetica_recalcula_ambos_periodos(self):
        x, y = self._x, self._y
        area = self._geojson(box(x - 100, y - 100, x + 600, y + 300))
        cobertura_2020 = self._geojson(box(x, y, x + 500, y + 200))
        cobertura_2025 = self._geojson(
            box(x, y, x + 200, y + 200),
            box(x + 300, y, x + 500, y + 200),
        )

        resultado = analizar_comparacion_geojson(
            fuente="jrc_tmf",
            anio_inicial=2020,
            anio_final=2025,
            cobertura_inicial=cobertura_2020,
            cobertura_final=cobertura_2025,
            area_geojson=area,
            distancia_maxima_m=50,
            area_minima_parche_ha=0,
        )

        inicial = resultado["periodos"]["2020"]["resumen"]
        final = resultado["periodos"]["2025"]["resumen"]
        self.assertEqual(inicial["numero_parches"], 1)
        self.assertEqual(final["numero_parches"], 2)
        self.assertEqual(inicial["numero_componentes"], 1)
        self.assertEqual(final["numero_componentes"], 2)
        self.assertAlmostEqual(inicial["superficie_bosque_ha"], 10.0, places=2)
        self.assertAlmostEqual(final["superficie_bosque_ha"], 8.0, places=2)
        self.assertAlmostEqual(resultado["cambios"]["superficie_bosque_ha"], -2.0, places=2)
        self.assertAlmostEqual(
            resultado["transiciones"]["perdida_bosque"]["area_ha"], 2.0, places=2
        )
        self.assertAlmostEqual(
            resultado["transiciones"]["ganancia_bosque"]["area_ha"], 0.0, places=2
        )
        self.assertEqual(resultado["parametros_equivalentes"]["distancia_maxima_m"], 50)

    def test_distancia_equivalente_cambia_la_red_no_la_cobertura(self):
        x, y = self._x, self._y
        area = self._geojson(box(x - 100, y - 100, x + 600, y + 300))
        dos_parches = self._geojson(
            box(x, y, x + 200, y + 200),
            box(x + 300, y, x + 500, y + 200),
        )
        resultado = analizar_comparacion_geojson(
            fuente="jrc_tmf",
            anio_inicial=2020,
            anio_final=2025,
            cobertura_inicial=dos_parches,
            cobertura_final=dos_parches,
            area_geojson=area,
            distancia_maxima_m=150,
            area_minima_parche_ha=0,
        )
        for anio in ("2020", "2025"):
            resumen = resultado["periodos"][anio]["resumen"]
            self.assertEqual(resumen["numero_parches"], 2)
            self.assertEqual(resumen["parches_aislados"], 0)
            self.assertEqual(resumen["numero_componentes"], 1)
            self.assertEqual(resumen["numero_aristas"], 1)

    def test_dibujo_se_recorta_a_la_cuenca(self):
        x, y = self._x, self._y
        area = self._geojson(box(x, y, x + 400, y + 400))
        cuenca = self._geojson(box(x, y, x + 200, y + 400))
        recorte = recortar_area_a_cuenca(area, cuenca)
        recorte_m = transform(
            Transformer.from_crs("EPSG:4326", "EPSG:8857", always_xy=True).transform,
            __import__("shapely").geometry.shape(recorte),
        )
        self.assertAlmostEqual(recorte_m.area / 10_000, 8.0, places=2)

    def test_transiciones_no_exponen_geometry_collection_a_folium(self):
        x, y = self._x, self._y
        area = self._geojson(box(x - 50, y - 50, x + 250, y + 250))
        geometria_mixta = GeometryCollection(
            [box(x, y, x + 200, y + 200), LineString([(x, y), (x + 200, y)])]
        )
        cobertura_inicial = self._geojson(geometria_mixta)
        cobertura_final = self._geojson(box(x, y, x + 100, y + 200))

        transiciones = calcular_transiciones_cobertura(
            cobertura_inicial,
            cobertura_final,
            area,
        )

        for resultado in transiciones.values():
            for feature in resultado["geojson"]["features"]:
                self.assertIn(feature["geometry"]["type"], {"Polygon", "MultiPolygon"})
                self.assertIn("coordinates", feature["geometry"])


if __name__ == "__main__":
    unittest.main()
