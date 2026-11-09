import unittest

from estadisticas_temporales import (
    construir_estadisticas_cobertura,
    generar_interpretacion_ecologica,
)


class EstadisticasCoberturaTests(unittest.TestCase):
    def _estadisticas(self, **cambios):
        datos = {
            "anio_inicial": 2020,
            "anio_final": 2025,
            "area_geometrica_ha": 100.0,
            "area_valida_inicial_ha": 90.0,
            "bosque_inicial_ha": 55.0,
            "area_valida_final_ha": 80.0,
            "bosque_final_ha": 50.0,
            "area_valida_comun_ha": 70.0,
            "bosque_estable_ha": 35.0,
            "perdida_bosque_ha": 10.0,
            "ganancia_bosque_ha": 5.0,
            "no_bosque_estable_ha": 20.0,
            "tolerancia_ha": 0.01,
        }
        datos.update(cambios)
        return construir_estadisticas_cobertura(**datos)

    def test_porcentajes_usan_area_valida_y_no_geometrica(self):
        resultado = self._estadisticas()
        inicial = resultado["periodos"]["2020"]
        self.assertAlmostEqual(inicial["porcentaje_bosque"], 55 / 90 * 100, places=4)
        self.assertAlmostEqual(inicial["porcentaje_no_bosque"], 35 / 90 * 100, places=4)
        self.assertAlmostEqual(
            inicial["porcentaje_bosque"] + inicial["porcentaje_no_bosque"],
            100.0,
            places=4,
        )

    def test_porcentajes_de_cobertura_y_validez_quedan_entre_cero_y_cien(self):
        resultado = self._estadisticas()
        for periodo in resultado["periodos"].values():
            for clave in (
                "porcentaje_bosque",
                "porcentaje_no_bosque",
                "porcentaje_area_valida",
                "porcentaje_sin_datos",
            ):
                self.assertGreaterEqual(periodo[clave], 0.0)
                self.assertLessEqual(periodo[clave], 100.0)

    def test_tolerancia_de_borde_no_produce_porcentaje_mayor_de_cien(self):
        resultado = self._estadisticas(
            area_geometrica_ha=100.0,
            area_valida_inicial_ha=100.2,
            bosque_inicial_ha=55.0,
            area_valida_final_ha=100.1,
            bosque_final_ha=50.0,
            tolerancia_geometria_ha=0.25,
        )
        self.assertEqual(
            resultado["periodos"]["2020"]["porcentaje_area_valida"], 100.0
        )
        self.assertEqual(
            resultado["periodos"]["2025"]["porcentaje_area_valida"], 100.0
        )

    def test_nodata_no_se_convierte_en_no_bosque(self):
        resultado = self._estadisticas()
        inicial = resultado["periodos"]["2020"]
        self.assertEqual(inicial["sin_datos_ha"], 10.0)
        self.assertEqual(inicial["no_bosque_ha"], 35.0)

    def test_mascaras_distintas_usan_area_comun(self):
        comparacion = self._estadisticas()["comparacion"]
        self.assertEqual(comparacion["area_valida_comun_ha"], 70.0)
        self.assertEqual(comparacion["suma_transiciones_ha"], 70.0)
        self.assertTrue(comparacion["transiciones_consistentes"])

    def test_perdida_ganancia_y_cambio_neto(self):
        comparacion = self._estadisticas()["comparacion"]
        self.assertEqual(comparacion["cambio_neto_bosque_ha"], -5.0)
        self.assertAlmostEqual(
            comparacion["porcentaje_perdida_bosque_inicial"], 10 / 45 * 100, places=4
        )
        self.assertAlmostEqual(
            comparacion["porcentaje_ganancia_no_bosque_inicial"], 5 / 25 * 100, places=4
        )

    def test_puntos_porcentuales_sobre_misma_mascara(self):
        comparacion = self._estadisticas()["comparacion"]
        esperado = (40 / 70 * 100) - (45 / 70 * 100)
        self.assertAlmostEqual(
            comparacion["cambio_neto_puntos_porcentuales"], esperado, places=3
        )

    def test_variacion_relativa_sobre_bosque_inicial_comparable(self):
        comparacion = self._estadisticas()["comparacion"]
        self.assertAlmostEqual(
            comparacion["variacion_relativa_bosque_pct"], -5 / 45 * 100, places=4
        )

    def test_bosque_inicial_cero_devuelve_no_aplica(self):
        resultado = self._estadisticas(
            bosque_inicial_ha=0,
            bosque_final_ha=5,
            bosque_estable_ha=0,
            perdida_bosque_ha=0,
            ganancia_bosque_ha=5,
            no_bosque_estable_ha=65,
        )
        self.assertIsNone(resultado["comparacion"]["variacion_relativa_bosque_pct"])

    def test_rechaza_transiciones_que_no_cierran(self):
        with self.assertRaisesRegex(ValueError, "no reproducen"):
            self._estadisticas(no_bosque_estable_ha=19.0)

    def test_rechaza_bosque_mayor_que_area_valida(self):
        with self.assertRaisesRegex(ValueError, "supera el área válida"):
            self._estadisticas(bosque_inicial_ha=91.0)

    def test_cambio_de_area_se_refleja_en_nodata(self):
        resultado = self._estadisticas(area_geometrica_ha=120.0)
        self.assertEqual(resultado["periodos"]["2020"]["sin_datos_ha"], 30.0)
        self.assertEqual(resultado["periodos"]["2025"]["sin_datos_ha"], 40.0)


class InterpretacionEcologicaTests(unittest.TestCase):
    def _resultado(self):
        estadisticas = construir_estadisticas_cobertura(
            anio_inicial=2020,
            anio_final=2025,
            area_geometrica_ha=100,
            area_valida_inicial_ha=100,
            bosque_inicial_ha=60,
            area_valida_final_ha=100,
            bosque_final_ha=55,
            area_valida_comun_ha=100,
            bosque_estable_ha=50,
            perdida_bosque_ha=10,
            ganancia_bosque_ha=5,
            no_bosque_estable_ha=35,
        )
        inicial = {
            "numero_parches": 3,
            "area_media_parche_ha": 20,
            "densidad_parches_por_100ha": 3,
            "indice_parche_mayor_pct": 40,
            "densidad_borde_m_ha": 4,
            "porcentaje_parches_aislados": 0,
            "numero_aristas": 3,
            "numero_componentes": 1,
            "porcentaje_nodos_componente_mayor": 100,
        }
        final = {
            "numero_parches": 6,
            "area_media_parche_ha": 9,
            "densidad_parches_por_100ha": 6,
            "indice_parche_mayor_pct": 25,
            "densidad_borde_m_ha": 7,
            "porcentaje_parches_aislados": 33.3,
            "numero_aristas": 2,
            "numero_componentes": 4,
            "porcentaje_nodos_componente_mayor": 50,
        }
        return {
            "anio_inicial": 2020,
            "anio_final": 2025,
            "estadisticas_cobertura": estadisticas,
            "periodos": {
                "2020": {"resumen": inicial},
                "2025": {"resumen": final},
            },
            "fuente": {
                "limitacion": "Limitación de prueba.",
                "resolucion_m": 30,
            },
        }

    def test_interpretacion_coincide_con_metricas(self):
        interpretacion = generar_interpretacion_ecologica(self._resultado())
        self.assertIn("disminución neta", interpretacion["cobertura"])
        self.assertIn("más fragmentada", interpretacion["fragmentacion"])
        self.assertIn("menos integrada", interpretacion["conectividad"])
        self.assertNotIn("agricultura", str(interpretacion).lower())

    def test_reglas_deterministas_quedan_documentadas(self):
        interpretacion = generar_interpretacion_ecologica(self._resultado())
        self.assertIn("cuatro de seis", interpretacion["reglas"]["fragmentacion"])
        self.assertIn("tres de cuatro", interpretacion["reglas"]["conectividad"])


if __name__ == "__main__":
    unittest.main()
