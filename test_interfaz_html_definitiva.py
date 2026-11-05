import unittest
from pathlib import Path

from interfaz_html_definitiva import (
    CSS_FASE4,
    TIPOS_ANALISIS,
    UNIDADES_ANALISIS,
    ConfiguracionAnalisis,
    stepper_html,
)


class InterfazHtmlDefinitivaTests(unittest.TestCase):
    def test_conserva_los_cuatro_analisis_y_el_orden_territorial(self):
        self.assertEqual(
            list(TIPOS_ANALISIS),
            ["cobertura", "fragmentacion", "conectividad", "integral"],
        )
        self.assertEqual(list(UNIDADES_ANALISIS), ["dibujo", "subcuenca", "cuenca"])

    def test_firma_incluye_parametros_cientificos_y_area(self):
        config = ConfiguracionAnalisis(
            tipo="integral",
            unidad="subcuenca",
            subcuenca="Río Chagres",
            fuente="jrc_tmf",
            anio_inicial=2020,
            anio_final=2025,
            distancia_maxima_m=500,
            area_minima_parche_ha=0.1,
        )
        firma = config.firma("geometria")
        self.assertIn("geometria", firma)
        self.assertIn(500, firma)
        self.assertEqual(firma[4:6], (2020, 2025))

    def test_stepper_distingue_completados_actual_y_pendientes(self):
        html = stepper_html(3)
        self.assertEqual(html.count('class="fase4-step done"'), 2)
        self.assertEqual(html.count('class="fase4-step current"'), 1)
        self.assertIn("Criterios", html)
        self.assertIn("Revisión", html)

    def test_css_reproduce_distribucion_y_respuesta_movil_del_html(self):
        self.assertIn("width:340px", CSS_FASE4)
        self.assertIn("fase4-res-h", CSS_FASE4)
        self.assertIn("fase4-stepper", CSS_FASE4)
        self.assertIn("@media(max-width:900px)", CSS_FASE4)
        self.assertIn("--azul:#0a4393", CSS_FASE4)
        self.assertIn("--verde:#77cc09", CSS_FASE4)

    def test_aplicacion_conecta_modal_motor_descarga_y_eri(self):
        codigo = Path("app_temporal.py").read_text(encoding="utf-8")
        self.assertIn('@st.dialog("Realizar análisis"', codigo)
        self.assertIn("ejecutar_temporal_cache", codigo)
        self.assertIn("preparar_descarga_zip", codigo)
        self.assertIn('"Descargas"', codigo)
        self.assertIn('href="?seccion=eri"', codigo)
        self.assertIn('["Capas", "Filtros", "Mapas base"]', codigo)
        self.assertNotIn("valor de demostración", codigo.lower())


if __name__ == "__main__":
    unittest.main()
