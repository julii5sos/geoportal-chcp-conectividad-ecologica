"""Interfaz V2 del análisis ecológico temporal científicamente recalculado."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import ee
import folium
import streamlit as st
from folium.plugins import Draw, Fullscreen
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit_folium import st_folium

from analisis_temporal import (
    FUENTES_TEMPORALES,
    ejecutar_analisis_temporal_ee,
    recortar_area_a_cuenca,
)
from gee_config import inicializar_earth_engine
from territorio_local import (
    coleccion_cuenca,
    coleccion_subcuencas,
    geometria_cuenca,
    geometria_subcuenca,
    nombres_subcuencas,
)
from interfaz_html_definitiva import (
    CSS_FASE4,
    TIPOS_ANALISIS,
    UNIDADES_ANALISIS,
    construir_configuracion,
    configurar_asistente_inicial,
    stepper_html,
)
from panel_estadistico import renderizar_panel_estadistico


AZUL = "#0A4393"
AZUL_OSCURO = "#062A5E"
VERDE = "#77CC09"
PERDIDA = "#D0442C"
GANANCIA = "#43AA8B"
ESTABLE = "#2E7D32"

MAPAS_BASE = {
    "Imagen satelital": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Esri",
        "max_zoom": 20,
    },
    "Mapa claro": {
        "tiles": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "attr": "OpenStreetMap contributors · CARTO",
        "max_zoom": 20,
    },
    "OpenStreetMap": {
        "tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "OpenStreetMap contributors",
        "max_zoom": 19,
    },
}


st.markdown(
    """
    <style>
    .temporal-cabecera {
      background:#0a4393; color:#fff; border-bottom:6px solid #77cc09;
      padding:18px 22px; margin:0 0 14px; display:flex; gap:18px;
      align-items:center; justify-content:space-between;
    }
    .temporal-cabecera small {display:block; text-transform:uppercase; letter-spacing:.08em; font-weight:700;}
    .temporal-cabecera h1 {font-size:1.65rem; margin:4px 0 0; color:#fff;}
    .temporal-sello {border:1px solid rgba(255,255,255,.7); border-radius:999px; padding:8px 14px; white-space:nowrap; font-weight:700;}
    .temporal-nota {border-left:5px solid #77cc09; background:#f3f8ec; padding:12px 16px; margin:8px 0 14px; color:#1b2433;}
    .temporal-metodo {border:1px solid #d6deeb; background:#fff; padding:14px 16px; margin:10px 0;}
    .temporal-metodo b {color:#062a5e;}
    .temporal-subtitulo {color:#062a5e; font-size:1.1rem; font-weight:800; margin:8px 0;}
    [data-testid="stMetric"] {border:1px solid #d6deeb; padding:12px; background:#fff; min-height:118px;}
    [data-testid="stSidebar"] button {min-height:44px;}
    @media (max-width: 760px) {
      .temporal-cabecera {align-items:flex-start; flex-direction:column;}
      .temporal-sello {white-space:normal;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _secreto(nombre: str, predeterminado=None):
    try:
        return st.secrets.get(nombre, predeterminado)
    except StreamlitSecretNotFoundError:
        return predeterminado


@st.cache_resource
def iniciar_earth_engine_temporal():
    """Inicializa EE con secretos de despliegue o credenciales locales existentes."""

    try:
        return inicializar_earth_engine(ee, secret_getter=_secreto)
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine no está autorizado para GEE_PROJECT_ID. Configure "
            "GEE_SERVICE_ACCOUNT_JSON en el servidor o autentique explícitamente "
            "la cuenta local correcta."
        ) from exc


@st.cache_data(ttl=3600, max_entries=12, show_spinner=False)
def ejecutar_temporal_cache(
    fuente: str,
    anio_inicial: int,
    anio_final: int,
    area_json: str,
    distancia_maxima_m: float,
    area_minima_parche_ha: float,
):
    iniciar_earth_engine_temporal()
    return ejecutar_analisis_temporal_ee(
        fuente=fuente,
        anio_inicial=anio_inicial,
        anio_final=anio_final,
        area_geojson=json.loads(area_json),
        distancia_maxima_m=distancia_maxima_m,
        area_minima_parche_ha=area_minima_parche_ha,
        ee_module=ee,
    )


def _limites_geojson(contenido: dict) -> list[list[float]]:
    coordenadas: list[tuple[float, float]] = []

    def recorrer(valor):
        if isinstance(valor, (list, tuple)):
            if len(valor) >= 2 and all(isinstance(v, (int, float)) for v in valor[:2]):
                coordenadas.append((float(valor[0]), float(valor[1])))
            else:
                for parte in valor:
                    recorrer(parte)
        elif isinstance(valor, dict):
            if "coordinates" in valor:
                recorrer(valor["coordinates"])
            if "geometries" in valor:
                recorrer(valor["geometries"])
            if "geometry" in valor:
                recorrer(valor["geometry"])
            if "features" in valor:
                recorrer(valor["features"])

    recorrer(contenido)
    if not coordenadas:
        return [[8.0, -80.5], [9.5, -79.0]]
    xs = [p[0] for p in coordenadas]
    ys = [p[1] for p in coordenadas]
    return [[min(ys), min(xs)], [max(ys), max(xs)]]


def _serializar_dibujo(dibujo: dict) -> str:
    geometria = dibujo.get("geometry", dibujo)
    if geometria.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Use únicamente la herramienta de polígono.")
    recorte = recortar_area_a_cuenca(geometria, geometria_cuenca())
    return json.dumps(recorte, ensure_ascii=False, sort_keys=True)


def _agregar_base(mapa: folium.Map, nombre: str) -> None:
    config = MAPAS_BASE[nombre]
    folium.TileLayer(
        tiles=config["tiles"],
        attr=config["attr"],
        max_zoom=config["max_zoom"],
        name=nombre,
        control=False,
    ).add_to(mapa)


def _estilo_area(_):
    return {"color": "#55D8FF", "weight": 3, "fillOpacity": 0.02}


def mostrar_selector_dibujo(mapa_base: str) -> str | None:
    version = st.session_state.get("version_dibujo_temporal", 0)
    dibujo_json = st.session_state.get("area_temporal_dibujada")
    mapa = folium.Map(location=[8.75, -79.75], zoom_start=9, tiles=None, control_scale=True)
    _agregar_base(mapa, mapa_base)
    folium.GeoJson(coleccion_cuenca(), name="Límite CHCP", style_function=_estilo_area).add_to(mapa)
    if dibujo_json:
        folium.GeoJson(
            json.loads(dibujo_json),
            name="Área recortada a la CHCP",
            style_function=lambda _: {
                "color": "#D0442C",
                "weight": 3,
                "fillColor": "#D0442C",
                "fillOpacity": 0.1,
            },
        ).add_to(mapa)
    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "rectangle": False,
            "circle": False,
            "marker": False,
            "circlemarker": False,
            "polygon": {
                "allowIntersection": False,
                "showArea": True,
                "shapeOptions": {"color": "#D0442C", "weight": 3},
            },
        },
        edit_options={"edit": False, "remove": True},
    ).add_to(mapa)
    mapa.fit_bounds(_limites_geojson(coleccion_cuenca()))
    respuesta = st_folium(
        mapa,
        height=610,
        use_container_width=True,
        returned_objects=["all_drawings"],
        key=f"dibujo-temporal-{version}",
    )
    dibujos = (respuesta or {}).get("all_drawings") or []
    if dibujos:
        nuevo = _serializar_dibujo(dibujos[-1])
        if nuevo != dibujo_json:
            st.session_state["area_temporal_dibujada"] = nuevo
            st.session_state.pop("resultado_temporal", None)
            st.rerun()
    return st.session_state.get("area_temporal_dibujada")


def _estilo_parche(feature):
    prioridad = feature.get("properties", {}).get("prioridad_conectividad", "Baja")
    color = {"Alta": "#0B5D1E", "Media": "#77CC09", "Baja": "#FABC20"}.get(
        prioridad, "#77CC09"
    )
    return {"color": color, "weight": 1.8, "fillColor": color, "fillOpacity": 0.26}


def crear_mapa_periodo(resultado: dict, anio: int, mapa_base: str) -> folium.Map:
    periodo = resultado["periodos"][str(anio)]
    analisis = periodo["analisis"]
    area = analisis["area_objetivo_geojson"]
    mapa = folium.Map(location=[8.75, -79.75], zoom_start=9, tiles=None, control_scale=True)
    _agregar_base(mapa, mapa_base)
    Fullscreen(position="topleft", title="Pantalla completa").add_to(mapa)
    folium.GeoJson(
        periodo["cobertura_geojson"],
        name=f"Cobertura de bosque {anio}",
        style_function=lambda _: {
            "color": ESTABLE,
            "weight": 0.8,
            "fillColor": ESTABLE,
            "fillOpacity": 0.38,
        },
    ).add_to(mapa)
    folium.GeoJson(
        analisis["parches_geojson"],
        name=f"Parches y métricas {anio}",
        style_function=_estilo_parche,
        tooltip=folium.GeoJsonTooltip(
            fields=["patch_id", "area_ha", "prioridad_conectividad", "componente"],
            aliases=["Parche", "Área (ha)", "Valor estructural", "Componente"],
            localize=True,
        ),
    ).add_to(mapa)
    folium.GeoJson(
        analisis["conexiones_geojson"],
        name=f"Red esencial {anio}",
        style_function=lambda _: {"color": AZUL_OSCURO, "weight": 3, "opacity": 0.9},
    ).add_to(mapa)
    folium.GeoJson(area, name="Área analizada", style_function=_estilo_area).add_to(mapa)
    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds(_limites_geojson(area))
    return mapa


def crear_mapa_transiciones(resultado: dict, mapa_base: str) -> folium.Map:
    area = resultado["periodos"][str(resultado["anio_inicial"])]["analisis"][
        "area_objetivo_geojson"
    ]
    mapa = folium.Map(location=[8.75, -79.75], zoom_start=9, tiles=None, control_scale=True)
    _agregar_base(mapa, mapa_base)
    Fullscreen(position="topleft", title="Pantalla completa").add_to(mapa)
    for clave, color, nombre in (
        ("bosque_estable", ESTABLE, "Bosque estable"),
        ("perdida_bosque", PERDIDA, "Pérdida de bosque"),
        ("ganancia_bosque", GANANCIA, "Ganancia de bosque"),
    ):
        folium.GeoJson(
            resultado["transiciones"][clave]["geojson"],
            name=nombre,
            style_function=lambda _, c=color: {
                "color": c,
                "weight": 1.2,
                "fillColor": c,
                "fillOpacity": 0.56,
            },
        ).add_to(mapa)
    folium.GeoJson(area, name="Área analizada", style_function=_estilo_area).add_to(mapa)
    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds(_limites_geojson(area))
    return mapa


def preparar_descarga_zip(resultado: dict) -> bytes:
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as archivo:
        resumen = {
            "fuente": resultado["fuente"],
            "anio_inicial": resultado["anio_inicial"],
            "anio_final": resultado["anio_final"],
            "parametros_equivalentes": resultado["parametros_equivalentes"],
            "cambios": resultado["cambios"],
            "transiciones_ha": {
                clave: valor["area_ha"] for clave, valor in resultado["transiciones"].items()
            },
            "estadisticas_cobertura": resultado["estadisticas_cobertura"],
            "interpretacion_ecologica": resultado["interpretacion_ecologica"],
            "metadatos": resultado["metadatos"],
        }
        archivo.writestr(
            "resumen_y_metadatos.json",
            json.dumps(resumen, ensure_ascii=False, indent=2),
        )
        csv_memoria = io.StringIO()
        campos = ["anio"] + list(
            resultado["periodos"][str(resultado["anio_inicial"])]["resumen"]
        )
        escritor = csv.DictWriter(csv_memoria, fieldnames=campos)
        escritor.writeheader()
        for anio in (resultado["anio_inicial"], resultado["anio_final"]):
            escritor.writerow(
                {"anio": anio, **resultado["periodos"][str(anio)]["resumen"]}
            )
        archivo.writestr("estadisticas_comparativas.csv", csv_memoria.getvalue())
        cobertura_memoria = io.StringIO()
        campos_cobertura = [
            "anio",
            "area_geometrica_ha",
            "area_valida_ha",
            "bosque_ha",
            "no_bosque_ha",
            "sin_datos_ha",
            "porcentaje_bosque",
            "porcentaje_no_bosque",
        ]
        escritor_cobertura = csv.DictWriter(
            cobertura_memoria, fieldnames=campos_cobertura
        )
        escritor_cobertura.writeheader()
        for anio in (resultado["anio_inicial"], resultado["anio_final"]):
            periodo = resultado["estadisticas_cobertura"]["periodos"][str(anio)]
            escritor_cobertura.writerow(
                {campo: periodo.get(campo) for campo in campos_cobertura}
            )
        archivo.writestr(
            "cobertura_valida_por_periodo.csv", cobertura_memoria.getvalue()
        )
        comparacion_memoria = io.StringIO()
        escritor_comparacion = csv.writer(comparacion_memoria)
        escritor_comparacion.writerow(["indicador", "valor"])
        for clave, valor in resultado["estadisticas_cobertura"]["comparacion"].items():
            if not isinstance(valor, dict):
                escritor_comparacion.writerow([clave, valor])
        archivo.writestr(
            "transiciones_mascara_comun.csv", comparacion_memoria.getvalue()
        )
        for anio in (resultado["anio_inicial"], resultado["anio_final"]):
            periodo = resultado["periodos"][str(anio)]
            archivo.writestr(
                f"cobertura_bosque_{anio}.geojson",
                json.dumps(periodo["cobertura_geojson"], ensure_ascii=False),
            )
            archivo.writestr(
                f"parches_{anio}.geojson",
                json.dumps(periodo["analisis"]["parches_geojson"], ensure_ascii=False),
            )
            archivo.writestr(
                f"red_conectividad_{anio}.geojson",
                json.dumps(periodo["analisis"]["conexiones_geojson"], ensure_ascii=False),
            )
        for clave, valor in resultado["transiciones"].items():
            archivo.writestr(
                f"{clave}.geojson",
                json.dumps(valor["geojson"], ensure_ascii=False),
            )
    return memoria.getvalue()


st.markdown(CSS_FASE4, unsafe_allow_html=True)
st.markdown('<div class="fase4-plataforma" aria-hidden="true"></div>', unsafe_allow_html=True)
configurar_asistente_inicial()


def _normalizar_anios(fuente: str) -> tuple[list[int], list[int]]:
    disponibles = list(FUENTES_TEMPORALES[fuente].anios)
    iniciales = disponibles[:-1]
    inicial = st.session_state.get("fase4_anio_inicial", 2020)
    if inicial not in iniciales:
        inicial = 2020 if 2020 in iniciales else iniciales[0]
        st.session_state["fase4_anio_inicial"] = inicial
    finales = [anio for anio in disponibles if anio > inicial]
    final = st.session_state.get("fase4_anio_final", 2025)
    if final not in finales:
        st.session_state["fase4_anio_final"] = finales[-1]
    return iniciales, finales


@st.dialog("Realizar análisis", width="large")
def mostrar_asistente_fase4() -> None:
    """Asistente de cuatro pasos conectado a la configuración científica real."""

    paso = int(st.session_state.get("fase4_paso", 1))
    lateral, contenido = st.columns([0.25, 0.75], gap="medium")
    with lateral:
        st.markdown(stepper_html(paso), unsafe_allow_html=True)

    with contenido:
        if paso == 1:
            st.markdown('<div class="fase4-wizard-title">Seleccione el análisis</div>', unsafe_allow_html=True)
            st.markdown('<p class="fase4-wizard-help">Cada opción utiliza resultados científicos del motor temporal; no son botones de demostración.</p>', unsafe_allow_html=True)
            tipo_actual = st.session_state.get("fase4_tipo", "integral")
            tipo_elegido = st.radio(
                "Tipo de análisis",
                list(TIPOS_ANALISIS),
                format_func=lambda clave: TIPOS_ANALISIS[clave]["titulo"],
                captions=[TIPOS_ANALISIS[clave]["descripcion"] for clave in TIPOS_ANALISIS],
                index=list(TIPOS_ANALISIS).index(tipo_actual),
                key="fase4_widget_tipo",
                label_visibility="collapsed",
            )
            st.session_state["fase4_tipo"] = tipo_elegido
        elif paso == 2:
            st.markdown('<div class="fase4-wizard-title">Defina el área de interés</div>', unsafe_allow_html=True)
            st.markdown('<p class="fase4-wizard-help">El dibujo es la primera opción. Toda geometría se recorta al límite local de la CHCP antes de calcular.</p>', unsafe_allow_html=True)
            unidad_actual = st.session_state.get("fase4_unidad", "dibujo")
            unidad_elegida = st.radio(
                "Área de interés",
                list(UNIDADES_ANALISIS),
                format_func=lambda clave: UNIDADES_ANALISIS[clave],
                index=list(UNIDADES_ANALISIS).index(unidad_actual),
                key="fase4_widget_unidad",
                label_visibility="collapsed",
            )
            st.session_state["fase4_unidad"] = unidad_elegida
            if unidad_elegida == "subcuenca":
                st.selectbox("Subcuenca", nombres_subcuencas(), key="fase4_subcuenca")
        elif paso == 3:
            st.markdown('<div class="fase4-wizard-title">Configure fuente y criterios</div>', unsafe_allow_html=True)
            st.markdown('<p class="fase4-wizard-help">JRC TMF y ESRI permanecen separados. Los mismos parámetros se aplican a ambos años.</p>', unsafe_allow_html=True)
            fuente_actual = st.session_state.get("fase4_fuente", "jrc_tmf")
            fuente_elegida = st.selectbox(
                "Fuente comparable",
                list(FUENTES_TEMPORALES),
                format_func=lambda clave: FUENTES_TEMPORALES[clave].nombre,
                index=list(FUENTES_TEMPORALES).index(fuente_actual),
                key="fase4_widget_fuente",
            )
            st.session_state["fase4_fuente"] = fuente_elegida
            iniciales, finales = _normalizar_anios(fuente_elegida)
            c1, c2 = st.columns(2)
            inicial_actual = st.session_state.get("fase4_anio_inicial", 2020)
            inicial_elegido = c1.selectbox(
                "Año inicial",
                iniciales,
                index=iniciales.index(inicial_actual),
                key=f"fase4_widget_inicial_{fuente_elegida}",
            )
            st.session_state["fase4_anio_inicial"] = inicial_elegido
            finales = [anio for anio in FUENTES_TEMPORALES[fuente_elegida].anios if anio > inicial_elegido]
            final_actual = st.session_state.get("fase4_anio_final", finales[-1])
            if final_actual not in finales:
                final_actual = finales[-1]
            final_elegido = c2.selectbox(
                "Año final",
                finales,
                index=finales.index(final_actual),
                key=f"fase4_widget_final_{fuente_elegida}_{inicial_elegido}",
            )
            st.session_state["fase4_anio_final"] = final_elegido
            distancia_elegida = st.select_slider(
                "Distancia máxima entre parches",
                options=[100, 250, 500, 1000, 1500, 3000],
                value=st.session_state.get("fase4_distancia", 500),
                format_func=lambda valor: f"{valor:,} m",
                key="fase4_widget_distancia",
            )
            st.session_state["fase4_distancia"] = distancia_elegida
            area_minima_elegida = st.number_input(
                "Área mínima de parche (ha)",
                min_value=0.0,
                value=float(st.session_state.get("fase4_area_minima", 0.1)),
                step=0.1,
                key="fase4_widget_area_minima",
            )
            st.session_state["fase4_area_minima"] = area_minima_elegida
        else:
            _normalizar_anios(st.session_state["fase4_fuente"])
            config = construir_configuracion()
            especificacion = FUENTES_TEMPORALES[config.fuente]
            st.markdown('<div class="fase4-wizard-title">Revise la solicitud</div>', unsafe_allow_html=True)
            st.markdown('<p class="fase4-wizard-help">La ejecución recuperará dos coberturas independientes y recalculará fragmentación y red para cada período.</p>', unsafe_allow_html=True)
            st.markdown(
                f"""<div class="fase4-review">
                <div><small>Análisis</small><b>{TIPOS_ANALISIS[config.tipo]['titulo']}</b></div>
                <div><small>Área</small><b>{UNIDADES_ANALISIS[config.unidad]}</b></div>
                <div><small>Fuente</small><b>{especificacion.nombre}</b></div>
                <div><small>Período</small><b>{config.anio_inicial}–{config.anio_final}</b></div>
                <div><small>Distancia</small><b>{config.distancia_maxima_m:,.0f} m</b></div>
                <div><small>Resolución</small><b>{especificacion.resolucion_m} m</b></div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.warning("El ERI conserva su metodología original y se consulta como evaluación complementaria; no se convierte en índice anual.")

    atras, siguiente = st.columns(2)
    if paso > 1 and atras.button("Atrás", use_container_width=True):
        st.session_state["fase4_paso"] = paso - 1
        st.rerun()
    if paso < 4:
        if siguiente.button("Siguiente", type="primary", use_container_width=True):
            st.session_state["fase4_paso"] = paso + 1
            st.rerun()
    else:
        if siguiente.button("Aplicar configuración", type="primary", use_container_width=True):
            st.session_state["configuracion_temporal_fase4"] = construir_configuracion()
            st.session_state["fase4_asistente_abierto"] = False
            st.session_state["fase4_paso"] = 1
            st.rerun()


if "fase4_anio_inicial" not in st.session_state:
    st.session_state["fase4_anio_inicial"] = 2020
if "fase4_anio_final" not in st.session_state:
    st.session_state["fase4_anio_final"] = 2025
_normalizar_anios(st.session_state["fase4_fuente"])
configuracion = st.session_state.get("configuracion_temporal_fase4")
if configuracion is None:
    configuracion = construir_configuracion()

tab_capas, tab_filtros, tab_base = st.sidebar.tabs(["Capas", "Filtros", "Mapas base"])
with tab_capas:
    st.markdown('<div class="fase4-marca-seccion"><small>Explorador</small><strong>Capas disponibles</strong></div>', unsafe_allow_html=True)
    with st.expander("Límites", expanded=True):
        mostrar_limite = st.checkbox("Cuenca hidrográfica", value=True, key="fase4_limite")
        mostrar_subcuencas = st.checkbox("Subcuencas del Canal", value=True, key="fase4_subcuencas")
        st.markdown('<div class="fase4-grupo-meta"><span>Territorio local</span><span class="fase4-tag">Real</span></div>', unsafe_allow_html=True)
    with st.expander("Cobertura forestal", expanded=True):
        fuente_vista = st.radio(
            "Fuente visible",
            list(FUENTES_TEMPORALES),
            format_func=lambda clave: FUENTES_TEMPORALES[clave].nombre,
            index=list(FUENTES_TEMPORALES).index(configuracion.fuente),
            disabled=True,
            help="La fuente visible corresponde a la configuración científica activa.",
        )
        st.markdown(f'<div class="fase4-grupo-meta"><span>{FUENTES_TEMPORALES[fuente_vista].resolucion_m} m</span><span class="fase4-tag">Real</span></div>', unsafe_allow_html=True)
    with st.expander("Fragmentación", expanded=False):
        st.checkbox("Parches forestales", value=True, disabled=True)
        st.checkbox("Parches aislados", value=True, disabled=True)
    with st.expander("Conectividad", expanded=False):
        st.checkbox("Red entre parches", value=True, disabled=True)
        st.checkbox("Componentes de conectividad", value=True, disabled=True)
    with st.expander("ERI complementario", expanded=False):
        st.caption("Integridad, conectividad local, estabilidad topográfica y proximidad riparia. No altera la comparación temporal.")
        st.markdown('<a href="?seccion=eri" target="_self">Abrir evaluación ERI</a>', unsafe_allow_html=True)

with tab_filtros:
    st.markdown("### Configuración activa")
    st.caption(f"{TIPOS_ANALISIS[configuracion.tipo]['titulo']} · {UNIDADES_ANALISIS[configuracion.unidad]}")
    st.caption(f"{FUENTES_TEMPORALES[configuracion.fuente].nombre} · {configuracion.anio_inicial}–{configuracion.anio_final}")
    st.caption(f"Distancia entre parches: {configuracion.distancia_maxima_m:,.0f} m")
    if st.button("Cambiar criterios", use_container_width=True):
        st.session_state["fase4_asistente_abierto"] = True
        st.rerun()

mapa_base = tab_base.radio("Fondo cartográfico", list(MAPAS_BASE), index=0)
tab_base.caption("El mapa base solo cambia la visualización y nunca modifica las métricas.")

area_geojson = None
area_json = None
if configuracion.unidad == "subcuenca":
    nombre_subcuenca = configuracion.subcuenca or nombres_subcuencas()[0]
    area_geojson = recortar_area_a_cuenca(geometria_subcuenca(nombre_subcuenca), geometria_cuenca())
elif configuracion.unidad == "cuenca":
    area_geojson = geometria_cuenca()

if area_geojson is not None:
    area_json = json.dumps(area_geojson, ensure_ascii=False, sort_keys=True)

resultado = st.session_state.get("resultado_temporal")
firma = configuracion.firma(area_json or st.session_state.get("area_temporal_dibujada"))
resultado_actual = resultado is not None and st.session_state.get("firma_temporal") == firma
descarga_zip = preparar_descarga_zip(resultado) if resultado_actual else None

acciones = st.sidebar.container(key="acciones_sidebar")
if "configuracion_temporal_fase4" not in st.session_state:
    if acciones.button("Realizar análisis", type="primary", use_container_width=True):
        st.session_state["fase4_asistente_abierto"] = True
        st.rerun()
    ejecutar = False
else:
    if acciones.button(
        "Ejecutar análisis",
        type="primary",
        use_container_width=True,
        disabled=configuracion.unidad == "dibujo" and not st.session_state.get("area_temporal_dibujada"),
    ):
        ejecutar = True
    else:
        ejecutar = False
    if descarga_zip is not None:
        acciones.download_button(
            "Descargas",
            data=descarga_zip,
            file_name=f"analisis_temporal_{configuracion.fuente}_{configuracion.anio_inicial}_{configuracion.anio_final}.zip",
            mime="application/zip",
            use_container_width=True,
        )

if st.session_state.get("fase4_asistente_abierto"):
    mostrar_asistente_fase4()

st.markdown(
    f"""<div class="fase4-topline"><div><strong>Panel de cuencas · Conectividad Panamá</strong>
    <p>Explorador científico de cobertura, fragmentación y conectividad estructural.</p></div>
    <span class="fase4-periodo">{configuracion.anio_inicial}–{configuracion.anio_final} · {FUENTES_TEMPORALES[configuracion.fuente].resolucion_m} m</span></div>""",
    unsafe_allow_html=True,
)

col_mapa, col_resultado = st.columns([3.55, 1.35], gap=None)
with col_mapa:
    with st.container(key="fase4_mapa_central"):
        if configuracion.unidad == "dibujo" and not resultado_actual:
            area_json_dibujo = mostrar_selector_dibujo(mapa_base)
            if area_json_dibujo:
                area_json = area_json_dibujo
                area_geojson = json.loads(area_json_dibujo)
                firma = configuracion.firma(area_json)
        elif resultado_actual:
            capa_resultado = tab_capas.radio(
                "Vista del resultado",
                ["Transiciones", str(configuracion.anio_inicial), str(configuracion.anio_final)],
                horizontal=False,
            )
            if capa_resultado == "Transiciones":
                mapa_resultado = crear_mapa_transiciones(resultado, mapa_base)
            else:
                mapa_resultado = crear_mapa_periodo(resultado, int(capa_resultado), mapa_base)
            if mostrar_limite:
                folium.GeoJson(coleccion_cuenca(), name="Límite CHCP", style_function=lambda _: {"color": "#0A4393", "weight": 2.5, "fillOpacity": 0}).add_to(mapa_resultado)
            if mostrar_subcuencas:
                folium.GeoJson(coleccion_subcuencas(), name="Subcuencas", style_function=lambda _: {"color": "#77CC09", "weight": 1, "fillOpacity": 0}).add_to(mapa_resultado)
            st_folium(mapa_resultado, height=720, use_container_width=True, returned_objects=[], key=f"fase4-resultado-{capa_resultado}-{hash(firma)}")
        else:
            mapa_area = folium.Map(location=[9.1, -79.7], zoom_start=9, tiles=None, control_scale=True)
            _agregar_base(mapa_area, mapa_base)
            if mostrar_limite:
                folium.GeoJson(coleccion_cuenca(), name="Límite CHCP", style_function=lambda _: {"color": "#0A4393", "weight": 3, "fillOpacity": 0.03}).add_to(mapa_area)
            if mostrar_subcuencas:
                folium.GeoJson(coleccion_subcuencas(), name="Subcuencas", style_function=lambda _: {"color": "#77CC09", "weight": 1, "fillOpacity": 0}).add_to(mapa_area)
            if area_geojson:
                folium.GeoJson(area_geojson, name="Área seleccionada", style_function=lambda _: {"color": "#FABC20", "weight": 4, "fillColor": "#FABC20", "fillOpacity": .12}).add_to(mapa_area)
                mapa_area.fit_bounds(_limites_geojson(area_geojson))
            st_folium(mapa_area, height=720, use_container_width=True, returned_objects=[], key=f"fase4-area-{configuracion.unidad}-{configuracion.subcuenca}-{mapa_base}")

with col_resultado:
    st.markdown(
        f"""<div class="fase4-res-h"><small>Estadísticas</small><h2>{TIPOS_ANALISIS[configuracion.tipo]['titulo']}</h2>
        <p>{configuracion.anio_inicial}–{configuracion.anio_final} · {FUENTES_TEMPORALES[configuracion.fuente].nombre}</p></div>""",
        unsafe_allow_html=True,
    )
    if not resultado_actual:
        st.markdown(
            """<div class="fase4-res-body"><div class="fase4-estado-vacio"><div>
            <h2>Prepare el análisis</h2><p>Seleccione los criterios, defina el área y ejecute el cálculo. No se muestran indicadores ficticios antes de procesar.</p>
            </div></div></div>""",
            unsafe_allow_html=True,
        )
    else:
        renderizar_panel_estadistico(
            resultado,
            tipo_analisis=configuracion.tipo,
            descarga_zip=descarga_zip,
        )

if ejecutar:
    if configuracion.unidad == "dibujo":
        area_json = st.session_state.get("area_temporal_dibujada")
        area_geojson = json.loads(area_json) if area_json else None
    if area_geojson is None:
        st.warning("Dibuje un polígono antes de ejecutar el análisis.")
    else:
        area_json = json.dumps(area_geojson, ensure_ascii=False, sort_keys=True)
        firma = configuracion.firma(area_json)
        with st.status("Procesando el análisis científico...", expanded=True) as estado:
            try:
                estado.write(f"Recuperando {FUENTES_TEMPORALES[configuracion.fuente].nombre} para {configuracion.anio_inicial} y {configuracion.anio_final}.")
                estado.write("Vectorizando parches con parámetros equivalentes.")
                estado.write("Calculando redes, transiciones y estadísticas.")
                resultado_nuevo = ejecutar_temporal_cache(
                    configuracion.fuente,
                    configuracion.anio_inicial,
                    configuracion.anio_final,
                    area_json,
                    configuracion.distancia_maxima_m,
                    configuracion.area_minima_parche_ha,
                )
                st.session_state["resultado_temporal"] = resultado_nuevo
                st.session_state["firma_temporal"] = firma
                estado.update(label="Análisis científico listo", state="complete", expanded=False)
                st.rerun()
            except Exception as error:
                estado.update(label="No fue posible completar el análisis", state="error")
                st.error("No se generaron valores sustitutos ni resultados ficticios.")
                with st.expander("Detalle técnico para soporte"):
                    st.code(f"{type(error).__name__}: {error}")
