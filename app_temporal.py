"""Interfaz V2 del análisis ecológico temporal científicamente recalculado."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import altair as alt
import ee
import folium
import streamlit as st
from folium.plugins import Draw, Fullscreen
from google.oauth2 import service_account
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit_folium import st_folium

from analisis_temporal import (
    FUENTES_TEMPORALES,
    ejecutar_analisis_temporal_ee,
    recortar_area_a_cuenca,
)
from territorio_local import (
    coleccion_cuenca,
    coleccion_subcuencas,
    geometria_cuenca,
    geometria_subcuenca,
    nombres_subcuencas,
)


AZUL = "#0A4393"
AZUL_OSCURO = "#062A5E"
VERDE = "#77CC09"
JRC = "#1F8A70"
ESRI = "#3A7CA5"
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

    proyecto = _secreto("EE_PROJECT", "ee-julissaguevaravega")
    secreto = _secreto("EE_SERVICE_ACCOUNT_JSON")
    if secreto is not None:
        informacion = json.loads(secreto) if isinstance(secreto, str) else dict(secreto)
        credenciales = service_account.Credentials.from_service_account_info(
            informacion,
            scopes=[
                "https://www.googleapis.com/auth/earthengine",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )
        ee.Initialize(credentials=credenciales, project=proyecto)
    else:
        try:
            ee.Initialize(project=proyecto)
        except Exception as exc:
            raise RuntimeError(
                "Earth Engine no está autorizado en este entorno. Configure "
                "EE_SERVICE_ACCOUNT_JSON y EE_PROJECT, o autentique la sesión local."
            ) from exc
    return True


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


def _grafica_barras(valores: list[dict], campo: str, titulo: str, color: str):
    return (
        alt.Chart(alt.Data(values=valores))
        .mark_bar(size=48, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=color)
        .encode(
            x=alt.X("Año:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y(f"{campo}:Q", title=titulo),
            tooltip=["Año:N", alt.Tooltip(f"{campo}:Q", format=",.2f")],
        )
        .properties(height=260)
    )


def _grafica_red(valores: list[dict]):
    largos = []
    colores = {
        "Parches": "#1F8A70",
        "Parches aislados": "#D0442C",
        "Componentes": "#3A7CA5",
    }
    for fila in valores:
        for metrica in colores:
            largos.append({"Año": str(fila["Año"]), "Métrica": metrica, "Valor": fila[metrica]})
    return (
        alt.Chart(alt.Data(values=largos))
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Año:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
            xOffset="Métrica:N",
            y=alt.Y("Valor:Q", title="Conteo"),
            color=alt.Color(
                "Métrica:N",
                scale=alt.Scale(domain=list(colores), range=list(colores.values())),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=["Año:N", "Métrica:N", alt.Tooltip("Valor:Q", format=",.0f")],
        )
        .properties(height=260)
    )


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


st.markdown(
    """
    <section class="temporal-cabecera">
      <div><small>Cuenca Hidrográfica del Canal de Panamá</small>
      <h1>Análisis ecológico temporal</h1></div>
      <div class="temporal-sello">Recálculo científico por período</div>
    </section>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="temporal-nota"><b>Comparación válida:</b> cada año genera una cobertura
    bosque/no bosque independiente y vuelve a calcular parches y red con los mismos
    parámetros. JRC y ESRI usan definiciones distintas y nunca se combinan.</div>
    """,
    unsafe_allow_html=True,
)

tab_fuente, tab_filtros, tab_base = st.sidebar.tabs(["Fuente", "Filtros", "Mapa base"])
fuente = tab_fuente.selectbox(
    "Fuente comparable",
    list(FUENTES_TEMPORALES),
    format_func=lambda clave: FUENTES_TEMPORALES[clave].nombre,
    help="JRC TMF es la fuente principal. ESRI se ejecuta como alternativa independiente.",
)
especificacion = FUENTES_TEMPORALES[fuente]
tab_fuente.markdown(f"**{especificacion.prioridad} · {especificacion.resolucion_m} m**")
tab_fuente.caption(especificacion.definicion_bosque)
tab_fuente.warning(especificacion.limitacion)

unidad = tab_filtros.selectbox(
    "Unidad territorial",
    ["Dibujar polígono", "Seleccionar subcuenca"],
    help="El polígono se recorta automáticamente al límite local de la CHCP.",
)
subcuenca = None
if unidad == "Seleccionar subcuenca":
    subcuenca = tab_filtros.selectbox("Subcuenca", nombres_subcuencas())

opciones_iniciales = list(especificacion.anios[:-1])
indice_2020 = opciones_iniciales.index(2020) if 2020 in opciones_iniciales else 0
anio_inicial = tab_filtros.selectbox(
    "Año inicial",
    opciones_iniciales,
    index=indice_2020,
)
opciones_finales = [anio for anio in especificacion.anios if anio > anio_inicial]
anio_final = tab_filtros.selectbox(
    "Año final",
    opciones_finales,
    index=len(opciones_finales) - 1,
)

with tab_filtros.expander("Parámetros equivalentes", expanded=False):
    distancia_maxima_m = st.select_slider(
        "Distancia máxima entre parches",
        options=[100, 250, 500, 1000, 1500, 3000],
        value=500,
        format_func=lambda valor: f"{valor:,} m",
        help="Se aplica exactamente el mismo umbral a ambos años.",
    )
    area_minima_parche_ha = st.number_input(
        "Área mínima de parche (ha)",
        min_value=0.0,
        value=0.1,
        step=0.1,
        help="Filtra componentes pequeños antes de transferirlos desde Earth Engine.",
    )

mapa_base = tab_base.selectbox("Fondo cartográfico", list(MAPAS_BASE), index=0)
tab_base.caption("El fondo solo cambia la visualización; nunca modifica las métricas.")

if unidad == "Seleccionar subcuenca":
    # Algunas geometrías fuente tocan o sobrepasan mínimamente el límite general.
    # El motor siempre recibe exactamente la porción válida dentro de la CHCP.
    area_geojson = recortar_area_a_cuenca(
        geometria_subcuenca(subcuenca),
        geometria_cuenca(),
    )
    st.markdown('<div class="temporal-subtitulo">Área seleccionada</div>', unsafe_allow_html=True)
    mapa_area = folium.Map(location=[8.75, -79.75], zoom_start=9, tiles=None, control_scale=True)
    _agregar_base(mapa_area, mapa_base)
    folium.GeoJson(
        coleccion_subcuencas(),
        name="Subcuencas",
        style_function=lambda _: {"color": "#8CA0BA", "weight": 1, "fillOpacity": 0.02},
    ).add_to(mapa_area)
    folium.GeoJson(
        area_geojson,
        name=subcuenca,
        style_function=lambda _: {
            "color": "#55D8FF",
            "weight": 4,
            "fillColor": "#55D8FF",
            "fillOpacity": 0.08,
        },
    ).add_to(mapa_area)
    mapa_area.fit_bounds(_limites_geojson(area_geojson))
    st_folium(
        mapa_area,
        height=610,
        use_container_width=True,
        returned_objects=[],
        key=f"area-subcuenca-{subcuenca}-{mapa_base}",
    )
else:
    st.markdown('<div class="temporal-subtitulo">Dibuje el área dentro de la CHCP</div>', unsafe_allow_html=True)
    st.caption("Use la herramienta de polígono. Las partes exteriores se excluyen automáticamente.")
    area_json = mostrar_selector_dibujo(mapa_base)
    area_geojson = json.loads(area_json) if area_json else None
    if area_json and st.button("Borrar polígono", key="borrar-area-temporal"):
        st.session_state.pop("area_temporal_dibujada", None)
        st.session_state.pop("resultado_temporal", None)
        st.session_state["version_dibujo_temporal"] = (
            st.session_state.get("version_dibujo_temporal", 0) + 1
        )
        st.rerun()

firma = (
    fuente,
    anio_inicial,
    anio_final,
    json.dumps(area_geojson, sort_keys=True) if area_geojson else None,
    distancia_maxima_m,
    area_minima_parche_ha,
)
resultado_actual = st.session_state.get("firma_temporal") == firma

ejecutar = st.sidebar.button(
    "Calcular comparación científica",
    type="primary",
    width="stretch",
    disabled=area_geojson is None,
    help="Recupera ambas coberturas y recalcula fragmentación y conectividad.",
)
if area_geojson is None:
    st.sidebar.info("Dibuje un polígono para habilitar el cálculo.")

if ejecutar:
    with st.status("Preparando el análisis temporal...", expanded=True) as estado:
        try:
            estado.write(f"Recuperando cobertura {especificacion.nombre} de {anio_inicial}.")
            estado.write(f"Recuperando cobertura {especificacion.nombre} de {anio_final}.")
            estado.write("Vectorizando parches y calculando dos redes equivalentes.")
            resultado = ejecutar_temporal_cache(
                fuente,
                anio_inicial,
                anio_final,
                json.dumps(area_geojson, ensure_ascii=False, sort_keys=True),
                distancia_maxima_m,
                area_minima_parche_ha,
            )
            st.session_state["resultado_temporal"] = resultado
            st.session_state["firma_temporal"] = firma
            estado.update(label="Comparación científica lista", state="complete", expanded=False)
            st.rerun()
        except Exception as error:
            estado.update(label="No fue posible completar la comparación", state="error")
            st.error(
                "El motor no pudo recuperar o vectorizar una de las coberturas. "
                "No se generaron valores sustitutos ni resultados ficticios."
            )
            with st.expander("Detalle técnico para soporte", expanded=False):
                st.code(f"{type(error).__name__}: {error}")

if not resultado_actual:
    if st.session_state.get("resultado_temporal"):
        st.warning("Cambió el área, la fuente, los años o los parámetros. Ejecute nuevamente.")
    else:
        st.info(
            "Seleccione el área y ejecute el análisis. Antes de calcular no se muestran "
            "estadísticas de demostración."
        )
    st.stop()

resultado = st.session_state["resultado_temporal"]
resumen_i = resultado["periodos"][str(anio_inicial)]["resumen"]
resumen_f = resultado["periodos"][str(anio_final)]["resumen"]
cambios = resultado["cambios"]

st.markdown("## Resultado comparativo")
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Superficie forestal",
    f"{resumen_f['superficie_bosque_ha']:,.2f} ha",
    f"{cambios['superficie_bosque_ha']:+,.2f} ha",
    delta_color="normal",
)
c2.metric(
    "Número de parches",
    f"{resumen_f['numero_parches']:,}",
    f"{cambios['numero_parches']:+,.0f}",
    delta_color="inverse",
)
c3.metric(
    "Parches aislados",
    f"{resumen_f['parches_aislados']:,}",
    f"{cambios['parches_aislados']:+,.0f}",
    delta_color="inverse",
)
c4.metric(
    "Componentes de red",
    f"{resumen_f['numero_componentes']:,}",
    f"{cambios['numero_componentes']:+,.0f}",
    delta_color="inverse",
)

transiciones = resultado["transiciones"]
t1, t2, t3 = st.columns(3)
t1.metric("Bosque estable", f"{transiciones['bosque_estable']['area_ha']:,.2f} ha")
t2.metric("Pérdida de bosque", f"{transiciones['perdida_bosque']['area_ha']:,.2f} ha")
t3.metric("Ganancia de bosque", f"{transiciones['ganancia_bosque']['area_ha']:,.2f} ha")

tab_cambio, tab_inicial, tab_final = st.tabs(
    [f"Cambios {anio_inicial}–{anio_final}", str(anio_inicial), str(anio_final)]
)
with tab_cambio:
    st_folium(
        crear_mapa_transiciones(resultado, mapa_base),
        height=660,
        use_container_width=True,
        returned_objects=[],
        key=f"mapa-transiciones-{hash(firma)}",
    )
with tab_inicial:
    st_folium(
        crear_mapa_periodo(resultado, anio_inicial, mapa_base),
        height=660,
        use_container_width=True,
        returned_objects=[],
        key=f"mapa-periodo-{anio_inicial}-{hash(firma)}",
    )
with tab_final:
    st_folium(
        crear_mapa_periodo(resultado, anio_final, mapa_base),
        height=660,
        use_container_width=True,
        returned_objects=[],
        key=f"mapa-periodo-{anio_final}-{hash(firma)}",
    )

valores = [
    {
        "Año": str(anio),
        "Bosque (ha)": resultado["periodos"][str(anio)]["resumen"]["superficie_bosque_ha"],
        "Parches": resultado["periodos"][str(anio)]["resumen"]["numero_parches"],
        "Parches aislados": resultado["periodos"][str(anio)]["resumen"]["parches_aislados"],
        "Componentes": resultado["periodos"][str(anio)]["resumen"]["numero_componentes"],
    }
    for anio in (anio_inicial, anio_final)
]
g1, g2 = st.columns(2)
with g1:
    st.markdown("### Superficie de bosque")
    st.altair_chart(
        _grafica_barras(
            valores,
            "Bosque (ha)",
            "Superficie forestal (ha)",
            JRC if fuente == "jrc_tmf" else ESRI,
        ),
        width="stretch",
        theme=None,
    )
with g2:
    st.markdown("### Fragmentación y conectividad")
    st.altair_chart(_grafica_red(valores), width="stretch", theme=None)

with st.expander("Tabla comparativa y método", expanded=False):
    st.dataframe(valores, hide_index=True, width="stretch")
    st.markdown(
        f"""
        <div class="temporal-metodo"><b>Fuente:</b> {especificacion.nombre} ·
        {especificacion.version} · {especificacion.resolucion_m} m.<br>
        <b>Definición:</b> {especificacion.definicion_bosque}<br>
        <b>Red:</b> misma distancia máxima de {distancia_maxima_m:,.0f} m y área mínima
        de {area_minima_parche_ha:.2f} ha en ambos años.<br>
        <b>Alcance:</b> conectividad estructural potencial; no demuestra conectividad
        funcional ni movimiento de fauna.</div>
        """,
        unsafe_allow_html=True,
    )

st.download_button(
    "Descargar resultados, GeoJSON y metadatos",
    data=preparar_descarga_zip(resultado),
    file_name=f"analisis_temporal_{fuente}_{anio_inicial}_{anio_final}.zip",
    mime="application/zip",
    type="primary",
    width="stretch",
)
