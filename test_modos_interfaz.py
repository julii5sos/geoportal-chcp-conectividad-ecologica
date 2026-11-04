import ast
import unittest
from pathlib import Path

import altair as alt
from streamlit.testing.v1 import AppTest

from modos_app import (
    TIPO_AREA_DIBUJADA,
    TIPO_AREA_SUBCUENCA,
    aplicar_limite_cuenca,
    area_debe_recortarse_a_cuenca,
)


class GeometriaPrueba:
    def __init__(self):
        self.intersecciones = []

    def intersection(self, otra, tolerancia):
        self.intersecciones.append((otra, tolerancia))
        return "geometria-recortada"


class ModosInterfazTests(unittest.TestCase):
    def test_grafica_anual_inicia_con_todo_el_periodo_visible(self):
        arbol = ast.parse(Path("app_experiencia.py").read_text(encoding="utf-8"))
        funcion = next(
            nodo
            for nodo in arbol.body
            if isinstance(nodo, ast.FunctionDef)
            and nodo.name == "crear_grafica_serie_barras"
        )
        espacio = {"alt": alt}
        exec(
            compile(
                ast.Module(body=[funcion], type_ignores=[]),
                "grafica_prueba",
                "exec",
            ),
            espacio,
        )
        grafica = espacio["crear_grafica_serie_barras"](
            {
                "columnas": {
                    "Año": list(range(2000, 2026)),
                    "Deforestación (ha)": [10] * 26,
                    "Degradación (ha)": [5] * 26,
                    "Regeneración forestal (ha)": [3] * 26,
                }
            },
            series=[
                "Deforestación (ha)",
                "Degradación (ha)",
                "Regeneración forestal (ha)",
            ],
            colores=["#C73E3A", "#F2A541", "#2E8B57"],
        ).to_dict()

        seleccion = grafica["params"][0]
        self.assertEqual(seleccion["value"]["x"], [2000, 2025])
        self.assertFalse(seleccion["select"]["clear"])
        self.assertEqual(
            grafica["vconcat"][0]["encoding"]["x"]["field"],
            "Periodo",
        )
        self.assertEqual(
            grafica["vconcat"][0]["transform"][0]["filter"]["param"],
            "periodo_visible",
        )
        self.assertEqual(
            grafica["vconcat"][0]["encoding"]["color"]["scale"]["domain"],
            [
                "Deforestación (ha)",
                "Degradación (ha)",
                "Regeneración forestal (ha)",
            ],
        )
        self.assertEqual(grafica["vconcat"][0]["encoding"]["y"]["stack"], "zero")

    def test_aplicacion_importa_la_regla_de_recorte(self):
        arbol = ast.parse(
            Path("app_experiencia.py").read_text(encoding="utf-8")
        )
        importados = {
            alias.name
            for nodo in arbol.body
            if isinstance(nodo, ast.ImportFrom) and nodo.module == "modos_app"
            for alias in nodo.names
        }

        self.assertIn("area_debe_recortarse_a_cuenca", importados)

    def test_la_pantalla_inicial_ofrece_tres_analisis_separados(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()

        self.assertFalse(app.exception)
        html_portada = "\n".join(bloque.value for bloque in app.markdown)
        self.assertIn('class="ref-selector-entry"', html_portada)
        self.assertIn("Realizar análisis", html_portada)
        self.assertNotIn('class="ref-mode-cards"', html_portada)

        app.query_params["seccion"] = "inicio"
        app.query_params["selector"] = "1"
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.radio), 1)
        self.assertEqual(
            app.radio[0].options,
            [
                "Preevaluación territorial",
                "Corredores y conectividad",
                "Preevaluación integral",
            ],
        )
        self.assertTrue(any(boton.label == "Abrir plataforma" for boton in app.button))

    def test_navegacion_explica_objetivo_y_metodo_sin_iniciar_el_motor(self):
        app = AppTest.from_file("app.py", default_timeout=30).run()

        app.query_params["seccion"] = "objetivo"
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Propósito y utilidad" in bloque.value for bloque in app.markdown)
        )

        app.query_params["seccion"] = "datos"
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Capas territoriales del portal" in bloque.value for bloque in app.markdown)
        )

        app.query_params["seccion"] = "metodo"
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any(
                "Cómo se construye la preevaluación" in bloque.value
                for bloque in app.markdown
            )
        )
        self.assertTrue(any(boton.label == "Elegir análisis" for boton in app.button))

        app.query_params["seccion"] = "acerca"
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any("Qué problema ayuda a resolver" in bloque.value for bloque in app.markdown)
        )
        self.assertTrue(any(boton.label == "Elegir análisis" for boton in app.button))

    def test_modo_url_no_cierra_resultados_en_cada_recarga(self):
        codigo = Path("app.py").read_text(encoding="utf-8")

        self.assertIn(
            'st.session_state.get("modo_analisis") != modo_consulta', codigo
        )
        self.assertIn('st.session_state["selector_modo_sidebar"] = modo_consulta', codigo)

    def test_la_navegacion_principal_permanece_antes_del_selector_de_enfoque(self):
        codigo = Path("app.py").read_text(encoding="utf-8")

        self.assertNotIn('SECCION_ANALISIS = "Análisis"', codigo)
        bloque_navegacion = codigo.index("mostrar_cabecera_portal(seccion_tablero)")
        bloque_modo = codigo.index('if modo_analisis is None:')
        bloque_aplicacion = codigo.index('APLICACION_ACTIVA =', bloque_modo)

        self.assertLess(bloque_navegacion, bloque_modo)
        self.assertLess(bloque_modo, bloque_aplicacion)

    def test_el_analisis_se_presenta_como_tablero_cartografico(self):
        codigo = Path("app_experiencia.py").read_text(encoding="utf-8")

        self.assertIn("Evidencia cartográfica", codigo)
        self.assertIn("Centro del análisis", codigo)
        self.assertIn("mapa-cabecera", codigo)
        self.assertIn("Resultado de la preevaluación", codigo)
        self.assertIn("Estadísticas del área", codigo)
        self.assertIn("Visualizada en el mapa", codigo)
        self.assertIn("mostrar_grafica_contextual_dashboard", codigo)
        self.assertIn("resolver_capa_contextual", codigo)
        self.assertIn("configuracion_grafica_contextual_compuesta", codigo)
        self.assertIn("crear_grafica_serie_barras", codigo)
        self.assertIn("mostrar_graficas_dashboard", codigo)
        self.assertIn("crear_grafica_barras_color", codigo)
        self.assertIn("st.altair_chart", codigo)
        self.assertNotIn("st.line_chart", codigo)
        self.assertNotIn('"tipo": "lineas"', codigo)
        self.assertIn("Deforestación por año", codigo)
        self.assertIn("Hectáreas clasificadas anualmente como deforestación", codigo)
        self.assertIn("Regeneración forestal por año", codigo)
        self.assertIn("Regeneración forestal (ha)", codigo)
        self.assertIn("Cambios forestales seleccionados por año", codigo)
        self.assertIn("Las barras apiladas comparan las capas JRC TMF activadas", codigo)
        self.assertIn('stack="zero"', codigo)
        self.assertIn("alt.selection_interval", codigo)
        self.assertIn('value={"x": intervalo_inicial}', codigo)
        self.assertIn("clear=False", codigo)
        self.assertIn("alt.vconcat", codigo)
        self.assertIn("Visualizadas en el mapa", codigo)
        self.assertNotIn('codificacion["xOffset"]', codigo)
        self.assertIn("capas_activas=capas_activas", codigo)
        self.assertIn("construir_grafica_estado_tmf", codigo)
        self.assertIn("Forest regrowth", codigo)
        self.assertIn("VIS_TMF_REGENERACION", codigo)
        self.assertIn("COLORES_FUENTES", codigo)
        self.assertIn('"JRC TMF": "#1F8A70"', codigo)
        self.assertIn('"Hansen GFC": "#E76F51"', codigo)
        self.assertIn('"ESRI LULC": "#3A7CA5"', codigo)
        self.assertIn('"GEDI": "#7A5195"', codigo)
        self.assertIn('"NDVI": "#9BBF30"', codigo)
        self.assertIn('text=alt.Text("Etiqueta:N")', codigo)
        self.assertIn("Aporte de las fuentes al índice", codigo)
        self.assertIn("Superficie con indicios", codigo)
        self.assertIn("Relación entre fragmentos", codigo)
        self.assertIn("Resultados completos", codigo)
        self.assertIn("Realizar análisis", codigo)
        self.assertIn("Resultados y descargas", codigo)
        self.assertNotIn('"Detalle y descargas"', codigo)
        self.assertNotIn("Abrir detalle completo y descargas", codigo)
        self.assertIn("Volver al mapa", codigo)
        self.assertIn('st.session_state["mostrar_resultados"] = False', codigo)
        self.assertIn(
            "El resultado aparece en el panel lateral derecho, como en el portal HTML",
            codigo,
        )
        self.assertIn("Evolución por fuente", codigo)
        self.assertIn("JRC Tropical Moist Forest", codigo)
        self.assertIn("Hansen Global Forest Change", codigo)
        self.assertIn("ESRI Land Use / Land Cover", codigo)
        self.assertIn("Sentinel-2 · NDVI", codigo)
        self.assertIn("GEDI · altura del dosel", codigo)
        self.assertIn('if seccion_tablero == "Análisis":', codigo)
        self.assertIn('["Resumen", "ERI indicativo"]', codigo)
        self.assertNotIn("mostrar_flujo(2)", codigo)
        self.assertNotIn("Ver detalles del análisis · opcional", codigo)

    def test_modelo_html_conserva_el_analisis_y_declara_su_identidad(self):
        portada = Path("app.py").read_text(encoding="utf-8")
        visor = Path("app_experiencia.py").read_text(encoding="utf-8")
        portal = Path("portal_html.py").read_text(encoding="utf-8")

        self.assertIn("mostrar_cabecera_portal", portada)
        self.assertIn("Conectividad Panamá", portal)
        self.assertIn("Google Earth Engine", portal)
        self.assertIn("WGS 84 · EPSG:4326", portal)
        self.assertIn("#0a4393", portal.lower())
        self.assertIn("#77cc09", portal.lower())
        self.assertIn(".ref-nav-btns>.ref-btn-w{display:none}", portal)
        self.assertNotIn(".ref-nav-btns{margin-left:auto}.ref-btn-w{display:none}", portal)
        self.assertIn('class="ref-mobile-menu"', portal)
        self.assertIn('href="?seccion=inicio&amp;selector=1" target="_self"', portal)
        self.assertNotIn('target="_blank"', portal)
        self.assertIn('APP_VERSION = "UX-5.3-HTML-EXACTO-LIMITES-LOCALES"', visor)
        self.assertIn("st.columns([3, 1]", visor)
        self.assertIn("height=780", visor)
        self.assertIn("tipo_area = panel_filtros.selectbox", visor)
        self.assertIn('key="mapa_portal"', visor)
        self.assertIn('["Capas", "Polígono", "Mapa base"]', visor)
        self.assertIn('key="acciones_sidebar"', visor)
        self.assertIn('"Realizar análisis"', visor)
        self.assertIn('"Resultados y descargas"', visor)
        self.assertIn('"Tipo de preevaluación"', visor)
        self.assertIn('on_change=cambiar_modo_desde_sidebar', visor)
        self.assertNotIn('key="cambiar_enfoque_sidebar"', visor)
        self.assertNotIn('key="abrir_resultados_sidebar"', visor)
        self.assertIn('"Imagen satelital"', visor)
        self.assertIn('"Mapa claro"', visor)
        self.assertIn('"OpenStreetMap"', visor)
        self.assertIn("agregar_mapa_base(mapa, mapa_base", visor)
        self.assertIn("agregar_subcuencas_local", visor)
        self.assertIn("agregar_limite_cuenca_local", visor)
        self.assertIn('[data-collapsed="true"]', visor)
        self.assertIn("width: 0 !important", visor)
        self.assertIn("flex-basis: 0 !important", visor)
        self.assertNotIn('st.markdown("### Visor cartográfico")', visor)
        for fuente in ("JRC", "Hansen", "ESRI", "GEDI", "NDVI"):
            self.assertIn(fuente, visor)

    def test_eri_se_presenta_como_indicador_complementario(self):
        visor = Path("app_experiencia.py").read_text(encoding="utf-8")

        self.assertIn("ERI · resiliencia ecológica", visor)
        self.assertIn("ERI complementario", visor)
        self.assertIn('"ERI indicativo": {', visor)
        self.assertIn('"tipo": "eri"', visor)
        self.assertIn("clasificar_imagen_eri", visor)
        self.assertIn('"participa_en_prioridad": False', visor)
        self.assertIn('["Lectura", "ERI", "Gráfica"]', visor)
        self.assertIn("El ERI no modifica el índice de indicios", visor)

    def test_conectividad_evitar_carga_y_texto_tecnico_innecesarios(self):
        visor = Path("app_experiencia.py").read_text(encoding="utf-8")
        corredores = Path("corredores.py").read_text(encoding="utf-8")
        arbol = ast.parse(visor)
        funcion_bosque = next(
            nodo
            for nodo in arbol.body
            if isinstance(nodo, ast.FunctionDef)
            and nodo.name == "analizar_bosque_asset"
        )

        self.assertNotIn('st.sidebar.expander("Fuentes de conectividad"', visor)
        self.assertNotIn("Cobertura lista. La aplicación consultará", visor)
        self.assertIn("Opciones técnicas · opcional", visor)
        self.assertIn("Coincidencia dentro del área analizada", visor)
        self.assertIn("Corredores completos · contexto regional", visor)
        self.assertIn("value=False", visor)
        self.assertIn("distancia_corredor_mas_cercano_m", visor)
        self.assertIn("radio_contexto_m", visor)
        self.assertEqual(funcion_bosque.decorator_list, [])
        self.assertIn("max_entries=24", visor)
        self.assertIn("max_entries=4", visor)
        self.assertIn("if mostrar:", corredores)
        self.assertIn("if mostrar_puntos_criticos:", corredores)

    def test_graficas_de_corredores_comparan_partes_del_mismo_total(self):
        arbol = ast.parse(Path("app_experiencia.py").read_text(encoding="utf-8"))
        funcion = next(
            nodo
            for nodo in arbol.body
            if isinstance(nodo, ast.FunctionDef)
            and nodo.name == "construir_graficas_dashboard"
        )
        colores = {
            "En corredores": "#2E7D5B",
            "Fuera de corredores": "#7B8CA5",
            "Bosque 2021": "#76B72A",
            "Otros usos 2021": "#B7791F",
            "Cercanos": "#2A9D8F",
            "Separados": "#E76F51",
        }
        espacio = {
            "MODO_CORREDORES": "Corredores",
            "COLORES_CONECTIVIDAD": colores,
        }
        exec(
            compile(
                ast.Module(body=[funcion], type_ignores=[]),
                "graficas_corredores_prueba",
                "exec",
            ),
            espacio,
        )
        graficas = espacio["construir_graficas_dashboard"](
            {
                "area_ha": 100,
                "corredores": {"area_en_corredores_ha": 40},
                "fragmentacion": {
                    "metricas_clase": {
                        "area_total_bosque_ha": 30,
                        "numero_parches": 10,
                    },
                    "metricas_red": {"numero_parches_aislados": 2},
                },
            },
            "Corredores",
        )

        self.assertEqual(
            graficas["primaria"]["datos"],
            {
                "Categoría": ["En corredores", "Fuera de corredores"],
                "Hectáreas": [40.0, 60.0],
            },
        )
        self.assertEqual(
            graficas["secundaria"]["datos"],
            {
                "Cobertura": ["Bosque 2021", "Otros usos 2021"],
                "Hectáreas": [30.0, 70.0],
            },
        )
        self.assertEqual(
            graficas["terciaria"]["datos"]["Fragmentos"], [8, 2]
        )
        self.assertIn("no se suman entre sí", graficas["clave"])

    def test_subcuenca_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            TIPO_AREA_SUBCUENCA,
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertEqual(geometria.intersecciones, [("limite-cuenca", 10)])
        self.assertTrue(area_debe_recortarse_a_cuenca(TIPO_AREA_SUBCUENCA))

    def test_poligono_dibujado_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            TIPO_AREA_DIBUJADA,
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertEqual(geometria.intersecciones, [("limite-cuenca", 10)])
        self.assertTrue(area_debe_recortarse_a_cuenca(TIPO_AREA_DIBUJADA))

    def test_finca_se_recorta_a_la_cuenca(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            "Finca de monitoreo",
            geometria,
            "limite-cuenca",
        )

        self.assertEqual(resultado, "geometria-recortada")
        self.assertTrue(area_debe_recortarse_a_cuenca("Finca de monitoreo"))

    def test_cuenca_completa_no_se_recorta_contra_si_misma(self):
        geometria = GeometriaPrueba()

        resultado = aplicar_limite_cuenca(
            "Toda la cuenca",
            geometria,
            "limite-cuenca",
        )

        self.assertIs(resultado, geometria)
        self.assertFalse(geometria.intersecciones)
        self.assertFalse(area_debe_recortarse_a_cuenca("Toda la cuenca"))


if __name__ == "__main__":
    unittest.main()
