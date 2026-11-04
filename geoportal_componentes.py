"""Componentes reutilizables del cascarón cartográfico del Geoportal CHCP 2.0.

El estado sin Earth Engine conserva herramientas territoriales locales reales y
nunca inventa indicadores. Cuando el motor remoto está disponible,
``app_experiencia.py`` continúa ejecutando los análisis científicos existentes.
"""

from __future__ import annotations

import json
from html import escape

import folium
import streamlit as st
from folium.plugins import Draw, Fullscreen
from pyproj import Geod
from shapely.geometry import shape
from streamlit_folium import st_folium

from geoportal_catalogo import FUENTES_GEOSPACIALES, anios_disponibles
from territorio_local import (
    coleccion_cuenca,
    coleccion_subcuencas,
    feature_subcuenca,
    nombres_subcuencas,
)


TIPO_DIBUJO = "Dibujar un área en el mapa"
TIPO_SUBCUENCA = "Subcuenca de la CHCP"
TIPO_CUENCA = "Toda la cuenca (análisis regional)"

FUENTES_PANEL = (
    ("jrc_tmf", "JRC Tropical Moist Forest"),
    ("hansen_gfc", "Hansen Global Forest Change"),
    ("esri_lulc", "ESRI Land Use / Land Cover"),
    ("sentinel_ndvi", "Sentinel-2 · NDVI"),
    ("gedi", "GEDI · altura del dosel"),
    ("bosque_2021", "Bosque 2021 · fragmentación y conectividad"),
    ("eri", "ERI · resiliencia ecológica"),
)

LEYENDAS_PANEL = {
    "jrc_tmf": (
        ("#006400", "Bosque no perturbado"),
        ("#FFCC00", "Degradación"),
        ("#FF0000", "Deforestación"),
        ("#43AA8B", "Regeneración forestal"),
        ("#0000FF", "Agua"),
        ("#BDBDBD", "Otra cobertura"),
    ),
    "hansen_gfc": (
        ("#00C853", "Cobertura arbórea de referencia"),
        ("#F9A825", "Pérdida histórica"),
        ("#D50000", "Pérdida reciente"),
    ),
    "esri_lulc": (
        ("#1A5BAB", "Agua"),
        ("#358221", "Árboles"),
        ("#87D19E", "Vegetación inundada"),
        ("#FFDB5C", "Cultivos"),
        ("#ED022A", "Área construida"),
        ("#EDE9E4", "Suelo desnudo"),
        ("#C6AD8D", "Pastizal/matorral"),
    ),
    "sentinel_ndvi": (
        ("#7F0000", "Vigor muy bajo"),
        ("#FF7043", "Vigor bajo"),
        ("#FFF9C4", "Vigor intermedio"),
        ("#66BB6A", "Vigor alto"),
        ("#1B5E20", "Vigor muy alto"),
    ),
    "gedi": (
        ("#FFFFCC", "Dosel bajo"),
        ("#78C679", "Dosel medio"),
        ("#006837", "Dosel alto"),
    ),
    "bosque_2021": (
        ("#2F6B45", "Bosque y otras tierras boscosas"),
        ("#00544D", "Relación estructural entre fragmentos"),
        ("#D97904", "Conexión potencial hacia un corredor"),
    ),
    "eri": (
        ("#C73E3A", "Resiliencia baja"),
        ("#F2C14E", "Resiliencia media"),
        ("#77CC09", "Resiliencia alta"),
    ),
}

MAPAS_BASE_LOCALES = {
    "Mapa claro": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
            "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Esri Light Gray Canvas",
    },
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": None,
    },
    "Imagen satelital": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Esri World Imagery",
    },
}


def calcular_area_geojson_ha(geometria: dict) -> float:
    """Calcula área geodésica real en hectáreas para una geometría WGS84."""

    poligono = shape(geometria)
    area_m2, _ = Geod(ellps="WGS84").geometry_area_perimeter(poligono)
    return abs(float(area_m2)) / 10_000.0


def _limites_coleccion(coleccion: dict) -> list[list[float]]:
    geometria = shape(
        {
            "type": "GeometryCollection",
            "geometries": [
                feature["geometry"] for feature in coleccion.get("features", [])
            ],
        }
    )
    xmin, ymin, xmax, ymax = geometria.bounds
    return [[ymin, xmin], [ymax, xmax]]


def _agregar_base(mapa: folium.Map, nombre: str) -> None:
    configuracion = MAPAS_BASE_LOCALES[nombre]
    folium.TileLayer(
        tiles=configuracion["tiles"],
        attr=configuracion["attr"],
        name=nombre,
        control=False,
        show=True,
    ).add_to(mapa)


def _panel_fuentes(panel) -> None:
    panel.markdown("### Capas y fuentes")
    panel.caption(
        "Los controles se habilitan al conectar Earth Engine. Los períodos mostrados "
        "provienen del catálogo real del portal."
    )
    with panel.expander("Límites", expanded=True):
        st.checkbox("Cuenca del Canal", value=True, disabled=True, key="local_limite")
        st.checkbox("Subcuencas del Canal", value=True, disabled=True, key="local_subcuencas")
    for clave, etiqueta in FUENTES_PANEL:
        fuente = FUENTES_GEOSPACIALES[clave]
        with panel.expander(etiqueta, expanded=False):
            st.checkbox(
                "Activar en el mapa",
                value=False,
                disabled=True,
                key=f"local_fuente_{clave}",
            )
            if fuente.temporal:
                st.caption(
                    f"Años disponibles: {fuente.anio_inicial}–{fuente.anio_final} · "
                    f"{fuente.resolucion}"
                )
            else:
                st.caption(f"Referencia: {fuente.version} · {fuente.resolucion}")
            st.caption(fuente.nota)
            entradas = "".join(
                '<span class="leyenda-fuente-item">'
                f'<i style="background:{escape(color)}"></i>{escape(etiqueta)}</span>'
                for color, etiqueta in LEYENDAS_PANEL[clave]
            )
            st.markdown(
                f'<div class="leyenda-fuente" aria-label="Leyenda de {escape(etiqueta)}">'
                f"{entradas}</div>",
                unsafe_allow_html=True,
            )


def _controles_comparacion(panel) -> None:
    panel.markdown("### Comparación temporal")
    clave = panel.selectbox(
        "Fuente comparable",
        ["jrc_tmf", "esri_lulc", "sentinel_ndvi"],
        format_func=lambda valor: FUENTES_GEOSPACIALES[valor].nombre,
        key="local_fuente_comparacion",
    )
    disponibles = anios_disponibles(clave)
    inicial = panel.selectbox(
        "Año inicial",
        disponibles[:-1],
        index=max(0, len(disponibles) - 6),
        key=f"local_inicial_{clave}",
    )
    finales = tuple(anio for anio in disponibles if anio > inicial)
    panel.selectbox(
        "Año final",
        finales,
        index=len(finales) - 1,
        key=f"local_final_{clave}_{inicial}",
    )
    panel.caption(
        "La selección es válida, pero las imágenes comparativas requieren la conexión "
        "a Earth Engine. No se sustituye otro año."
    )


def mostrar_portal_sin_motor(error: Exception, vista: str) -> None:
    """Muestra la plataforma local y explica por qué el cálculo está deshabilitado."""

    panel_capas, panel_area, panel_mapa = st.sidebar.tabs(
        ["Capas", "Polígono", "Mapa base"]
    )
    acciones = st.sidebar.container(key="acciones_sidebar")
    _panel_fuentes(panel_capas)

    panel_area.markdown("### Área de análisis")
    tipo = panel_area.selectbox(
        "Unidad territorial",
        [TIPO_DIBUJO, TIPO_SUBCUENCA, TIPO_CUENCA],
        key="local_tipo_area",
        help="El dibujo es la opción principal del flujo público.",
    )
    subcuenca = None
    if tipo == TIPO_SUBCUENCA:
        subcuenca = panel_area.selectbox(
            "Subcuenca",
            nombres_subcuencas(),
            key="local_subcuenca",
        )
    if vista == "comparar":
        _controles_comparacion(panel_area)

    mapa_base = panel_mapa.selectbox(
        "Fondo cartográfico",
        list(MAPAS_BASE_LOCALES),
        key="local_mapa_base",
    )
    panel_mapa.caption("El fondo no modifica los cálculos ni la geometría seleccionada.")

    acciones.button(
        "Realizar análisis",
        type="primary",
        use_container_width=True,
        disabled=True,
        help="Conecte las credenciales de Earth Engine para ejecutar el análisis.",
    )

    st.markdown(
        '<div class="mapa-cabecera"><small>Centro del análisis</small>'
        '<strong>Evidencia cartográfica</strong></div>',
        unsafe_allow_html=True,
    )
    st.warning(
        "La plataforma territorial local está disponible, pero los productos satelitales "
        "y los cálculos permanecen deshabilitados hasta conectar Earth Engine."
    )

    mapa = folium.Map(
        location=[9.1, -79.7],
        zoom_start=9,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )
    _agregar_base(mapa, mapa_base)
    Fullscreen(position="topleft", title="Pantalla completa").add_to(mapa)
    cuenca = coleccion_cuenca()
    folium.GeoJson(
        cuenca,
        name="Cuenca del Canal",
        style_function=lambda _: {
            "color": "#0A4393",
            "weight": 3,
            "fillColor": "#0A4393",
            "fillOpacity": 0.04,
        },
    ).add_to(mapa)
    folium.GeoJson(
        coleccion_subcuencas(),
        name="Subcuencas",
        style_function=lambda _: {
            "color": "#77CC09",
            "weight": 1,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(fields=["nombre"], aliases=["Subcuenca"]),
    ).add_to(mapa)

    geometria_activa = None
    if subcuenca:
        seleccion = feature_subcuenca(subcuenca)
        geometria_activa = seleccion["geometry"]
        folium.GeoJson(
            seleccion,
            name="Subcuenca seleccionada",
            style_function=lambda _: {
                "color": "#FABC20",
                "weight": 4,
                "fillColor": "#FABC20",
                "fillOpacity": 0.14,
            },
        ).add_to(mapa)
        mapa.fit_bounds(_limites_coleccion({"features": [seleccion]}))
    else:
        mapa.fit_bounds(_limites_coleccion(cuenca))

    if tipo == TIPO_DIBUJO:
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
            edit_options={"edit": True, "remove": True},
        ).add_to(mapa)

    respuesta = st_folium(
        mapa,
        height=720,
        use_container_width=True,
        returned_objects=["all_drawings"] if tipo == TIPO_DIBUJO else [],
        key=f"geoportal-local-{vista}-{tipo}-{subcuenca}-{mapa_base}",
    )
    dibujos = (respuesta or {}).get("all_drawings") or []
    if tipo == TIPO_DIBUJO and dibujos:
        geometria_activa = dibujos[-1].get("geometry")
    if tipo == TIPO_CUENCA:
        geometria_activa = cuenca["features"][0]["geometry"]

    if geometria_activa:
        st.caption(f"Superficie territorial seleccionada: {calcular_area_geojson_ha(geometria_activa):,.1f} ha")
    else:
        st.caption("Dibuje un polígono para medir su superficie y preparar la selección.")

    with st.expander("Detalle técnico de la conexión", expanded=False):
        st.code(f"{type(error).__name__}: {error}")
