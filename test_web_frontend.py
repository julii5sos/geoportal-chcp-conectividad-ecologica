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
        self.assertIn("Conectividad ecológica de la Cuenca del Canal de Panamá", html)
        self.assertIn("geoportal-513817", html)
        self.assertIn("DM+Sans", html)
        self.assertIn('id="home-map"', html)
        self.assertIn('id="territory-query"', html)
        self.assertIn('class="skip-link"', html)

    def test_territorial_panel_has_real_data_tabs_and_no_prefilled_science(self):
        html = self.client.get("/panel").get_data(as_text=True)
        self.assertIn('id="panel-search"', html)
        self.assertIn('id="panel-map"', html)
        self.assertIn("Concordancia JRC + ESRI", html)
        javascript = (ROOT / "webapp" / "static" / "js" / "panel.js").read_text(encoding="utf-8")
        self.assertIn("notCalculated", javascript)
        self.assertNotIn("Math.random", javascript)

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
        self.assertIn('id="evidence-source"', html)
        self.assertIn('id="run-evidence"', html)

    def test_javascript_connects_controls_to_real_api(self):
        javascript = (ROOT / "webapp" / "static" / "js" / "platform.js").read_text(encoding="utf-8")
        self.assertIn("/api/v1/analyses", javascript)
        self.assertIn("/api/v1/eri", javascript)
        self.assertIn("/download.zip", javascript)
        self.assertIn("integratedResultViews", javascript)
        self.assertIn("concordanceState", javascript)
        self.assertIn("/api/v1/catalog/sources", javascript)
        self.assertIn("/api/v1/evidence", javascript)
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


if __name__ == "__main__":
    unittest.main()

