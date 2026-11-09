import unittest
from pathlib import Path

from webapp.main import create_app


ROOT = Path(__file__).resolve().parent


class WebFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app(testing=True).test_client()

    def test_home_reproduces_original_identity_and_real_project(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Geoportal de Conectividad Ecológica de la Cuenca Hidrográfica del Canal de Panamá", html)
        self.assertIn("geoportal-513817", html)
        self.assertIn("DM+Sans", html)
        self.assertIn('id="home-map"', html)
        self.assertIn('id="territory-query"', html)
        self.assertIn('class="skip-link"', html)
        self.assertIn("Una entrada clara para cada necesidad", html)
        self.assertIn("Revisar metodología y datos", html)

    def test_territorial_panel_has_real_data_tabs_and_no_prefilled_science(self):
        html = self.client.get("/panel").get_data(as_text=True)
        self.assertIn('id="panel-search"', html)
        self.assertIn('id="panel-map"', html)
        self.assertIn("Concordancia JRC + ESRI", html)
        self.assertIn('id="panel-layer-territory"', html)
        self.assertIn('id="panel-map-opacity"', html)
        self.assertIn('id="panel-more-analysis"', html)
        self.assertIn('id="panel-fit-territory"', html)
        self.assertEqual(html.count('data-territory-tab='), 5)
        self.assertIn("Cobertura y cambio", html)
        self.assertIn("Fragmentación y conectividad", html)
        self.assertIn("Interpretación e informe", html)
        self.assertIn("Explorar mapa", html)
        self.assertIn("Ejecutar análisis", html)
        javascript = (ROOT / "webapp" / "static" / "js" / "panel.js").read_text(encoding="utf-8")
        self.assertIn("moduleShowcase", javascript)
        self.assertIn("requestedTab", javascript)
        self.assertIn("Primer año frente al último disponible", javascript)
        self.assertIn("Cobertura general oficial 2021", javascript)
        self.assertIn("Uso y cobertura detallada 2021", javascript)
        self.assertNotIn("Bosque maduro", javascript)
        self.assertIn("moduleShowcase", javascript)
        self.assertNotIn("No calculado", javascript)
        self.assertNotIn("Math.random", javascript)
        self.assertIn("renderActiveMapLayers", javascript)
        self.assertIn("activeTab !== 'corridors'", javascript)
        self.assertIn("legacyTabAliases", javascript)
        self.assertIn("Generar informe técnico (PDF)", javascript)
        self.assertIn("Descargar datos", javascript)
        self.assertIn("scrollIntoView", javascript)

    def test_platform_contains_three_columns_and_four_step_modal(self):
        html = self.client.get("/platform").get_data(as_text=True)
        for identifier in (
            'id="left-panel"',
            'id="smap"',
            'id="results-panel"',
            'id="analysis-modal"',
            'id="wizard-steps"',
        ):
            self.assertIn(identifier, html)
        self.assertIn("Capas", html)
        self.assertIn("Filtros", html)
        self.assertIn("Mapa base", html)
        self.assertIn("Corredores publicados", (ROOT / "webapp" / "static" / "js" / "platform.js").read_text(encoding="utf-8"))
        self.assertIn("prepareCorridorFromMap", (ROOT / "webapp" / "static" / "js" / "platform.js").read_text(encoding="utf-8"))
        javascript = (ROOT / "webapp" / "static" / "js" / "platform.js").read_text(encoding="utf-8")
        self.assertIn('name="analysis-component"', javascript)
        self.assertIn('id="analysis-integral"', javascript)
        self.assertIn("selectedComponents", javascript)
        self.assertNotIn("Consultas especializadas", javascript)
        self.assertNotIn('id="run-evidence"', html)
        self.assertIn("Resultados del análisis", javascript)
        self.assertIn("Conectividad y riesgos", javascript)
        self.assertIn('data-preview="ndvi"', javascript)
        self.assertIn("Coberturas oficiales de Panamá", javascript)
        self.assertIn("Cobertura general oficial 2021", javascript)
        self.assertIn("Uso y cobertura detallada 2021", javascript)
        self.assertIn("Señales satelitales", javascript)
        for source in ("jrc_tmf", "hansen_gfc", "esri_lulc", "gedi", "sentinel_ndvi"):
            self.assertIn(source, javascript)
        self.assertIn('id="reset-platform"', html)
        self.assertIn('class="res" id="results-panel"', html)
        self.assertIn('id="results-navigation"', html)
        self.assertIn("No calculado", html)
        self.assertIn("mountScientificViews", javascript)
        for section in ("Resumen", "Dinámica del bosque", "Fragmentación y conectividad", "Coberturas oficiales"):
            self.assertIn(section, javascript)
        self.assertIn("corridorResultView", javascript)
        self.assertIn("renderPreparedTerritory", javascript)
        self.assertIn("lastAnalysisFingerprint", javascript)
        self.assertIn("const fitSelectedArea", javascript)
        self.assertIn("window.setTimeout(fitSelectedArea, 320)", javascript)
        self.assertIn("map.invalidateSize({pan:false})", javascript)

    def test_panel_separates_results_from_methodology_and_has_functional_legend(self):
        html = self.client.get("/panel").get_data(as_text=True)
        javascript = (ROOT / "webapp" / "static" / "js" / "panel.js").read_text(encoding="utf-8")
        self.assertIn("referencia 2025", html)
        self.assertIn('id="panel-theme-layers"', html)
        self.assertIn('id="panel-map-legend"', html)
        self.assertIn("loadOfficialPreview", javascript)
        self.assertIn("Estadísticas territoriales no disponibles", javascript)
        self.assertNotIn("Peso máximo por señal", javascript.split("if (key === 'coverage')", 1)[1].split("if (key === 'fragmentation')", 1)[0])

    def test_javascript_connects_controls_to_real_api(self):
        javascript = (ROOT / "webapp" / "static" / "js" / "platform.js").read_text(encoding="utf-8")
        self.assertIn("/api/v1/evaluations/ecological", javascript)
        self.assertIn("/api/v1/evaluations/integrated", javascript)
        self.assertIn("/api/v1/structural-connectivity", javascript)
        self.assertIn("/api/v1/eri", javascript)
        self.assertIn("/download.zip", javascript)
        self.assertIn("/report.pdf", javascript)
        self.assertIn("Generar informe técnico (PDF)", javascript)
        self.assertIn("integratedResultViews", javascript)
        self.assertIn("concordanceState", javascript)
        self.assertIn("/api/v1/catalog/sources", javascript)
        self.assertIn("/api/v1/evidence", javascript)
        self.assertIn("/api/v1/layers/preview", javascript)
        panel_javascript = (ROOT / "webapp" / "static" / "js" / "panel.js").read_text(encoding="utf-8")
        self.assertIn("/results/latest", panel_javascript)
        self.assertIn("result-provenance", panel_javascript)
        self.assertIn("analysisStatus:'processing'", javascript)
        self.assertIn("Error de procesamiento", panel_javascript)
        self.assertNotIn("Math.random", javascript)

    def test_original_css_is_preserved_and_extended(self):
        copied = (ROOT / "webapp" / "static" / "css" / "portal.css").read_text(encoding="utf-8")
        self.assertIn("Conectividad Panamá — hoja de estilos del portal", copied)
        self.assertIn("grid-template-columns:340px minmax(0,1fr) auto", copied)
        self.assertIn("--azul:#0a4393", copied)
        extension = (ROOT / "webapp" / "static" / "css" / "webapp.css").read_text(encoding="utf-8")
        self.assertIn("#v-plataforma", extension)
        self.assertIn(".result-tabs", extension)
        self.assertIn(".panel-results-map-grid", extension)
        self.assertIn(".panel-map-layers", extension)
        self.assertIn("grid-template-columns:minmax(0,600px) minmax(0,1fr)", extension)
        self.assertIn(".panel-context-head", extension)
        self.assertIn(".panel-widget", extension)
        self.assertIn("--result-green", extension)
        self.assertIn("grid-template-columns:23% 39% 38%", extension)
        self.assertIn('.metric-card[data-tone="loss"]', extension)
        self.assertIn(".scientific-result-tabs", extension)
        self.assertIn(".scientific-result-navigation", extension)
        self.assertIn(".app-nav", extension)

    def test_official_catalog_page_documents_eight_assets_without_claiming_validation(self):
        html = self.client.get("/methodology").get_data(as_text=True)
        self.assertEqual(html.count('data-type="IMAGE"') + html.count('data-type="TABLE"'), 8)
        self.assertIn("NoData", html)
        self.assertIn("acceso tipo verificados", html)
        self.assertIn("Fuentes operativas adicionales", html)
        self.assertIn('id="catalog-category"', html)

    def test_about_page_explains_modules_audience_and_limits(self):
        html = self.client.get("/about").get_data(as_text=True)
        self.assertIn("Dirigido a", html)
        self.assertIn("Qué calcula cada módulo", html)
        self.assertIn("Qué no hace", html)


if __name__ == "__main__":
    unittest.main()

