import unittest

from analisis_integrado import (
    clasificar_cambio,
    clasificar_estado,
    resumir_concordancia,
    validar_periodo_integrado,
)


class IntegratedAnalysisTests(unittest.TestCase):
    def test_common_period_is_enforced(self):
        self.assertEqual(validar_periodo_integrado(2020, 2025), (2020, 2025))
        for period in ((2016, 2025), (2020, 2026), (2025, 2025)):
            with self.assertRaises(ValueError):
                validar_periodo_integrado(*period)

    def test_state_classes_are_mutually_exclusive(self):
        self.assertEqual(clasificar_estado(jrc_bosque=True, esri_bosque=True), 1)
        self.assertEqual(clasificar_estado(jrc_bosque=False, esri_bosque=False), 2)
        self.assertEqual(clasificar_estado(jrc_bosque=True, esri_bosque=False), 3)
        self.assertEqual(clasificar_estado(jrc_bosque=False, esri_bosque=True), 4)
        self.assertEqual(clasificar_estado(jrc_bosque=True, esri_bosque=True, comparable=False), 5)

    def test_change_classes_distinguish_agreement_disagreement_and_nodata(self):
        self.assertEqual(clasificar_cambio(jrc_inicial=True, jrc_final=False, esri_inicial=True, esri_final=False), 1)
        self.assertEqual(clasificar_cambio(jrc_inicial=True, jrc_final=False, esri_inicial=True, esri_final=True), 2)
        self.assertEqual(clasificar_cambio(jrc_inicial=False, jrc_final=True, esri_inicial=False, esri_final=True), 4)
        self.assertEqual(clasificar_cambio(jrc_inicial=True, jrc_final=False, esri_inicial=False, esri_final=True), 7)
        self.assertEqual(clasificar_cambio(jrc_inicial=True, jrc_final=True, esri_inicial=True, esri_final=True, comparable=False), 8)

    def test_summary_uses_only_common_valid_area(self):
        summary = resumir_concordancia(
            estado_areas={
                "bosque_ambas": 40,
                "no_bosque_ambas": 30,
                "bosque_solo_jrc": 20,
                "bosque_solo_esri": 10,
                "sin_datos": 50,
            },
            cambio_areas={"perdida_ambas": 5, "ganancia_ambas": 3, "sin_datos": 50},
            bosque_jrc_final_ha=60,
            bosque_esri_final_ha=50,
        )
        self.assertEqual(summary["estado"]["area_valida_comun_ha"], 100)
        self.assertEqual(summary["estado"]["concordancia_pct"], 70)
        self.assertEqual(summary["diferencia_superficie_forestal_final_ha"], 10)
        self.assertEqual(summary["cambio"]["area_valida_comun_ha"], 8)


if __name__ == "__main__":
    unittest.main()
