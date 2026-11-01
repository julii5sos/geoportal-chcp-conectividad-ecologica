import html as html_lib
import hashlib
import hmac
import json
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from io import BytesIO

import altair as alt
import ee
import folium
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from folium.plugins import Draw, Fullscreen
from google.oauth2 import service_account
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as ReportLabImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from streamlit_folium import st_folium

from bosque_conectividad import (
    agregar_resultados_fragmentacion,
    analizar_fragmentacion_geojson,
)
from comparador_mapa import (
    ComparadorCapasSincronizadas,
    opciones_interaccion_mapa,
)
from corredores import (
    FUENTE_CORTA as FUENTE_CORREDORES,
    URL_MAPA as URL_MAPA_CORREDORES,
    agregar_capas_corredores,
    analizar_interseccion_corredores,
    calcular_radio_contexto,
    cargar_catalogo as cargar_catalogo_corredores,
    cargar_corredores,
    leyenda_corredores,
)
from eri_indicativo import (
    CLASES_ERI,
    COLORES_COMPONENTES_ERI,
    ETIQUETAS_COMPONENTES_ERI,
    PESOS_ERI,
    construir_resultado_eri,
)
from metodologia_indice import (
    CLASES_VIGOR_NDVI,
    JUSTIFICACION_PESOS,
    JUSTIFICACION_UMBRALES,
    PERIODOS_ANALISIS,
    PESOS_INDICE,
    PUNTAJE_MAXIMO,
    PUNTAJE_MAXIMO_VISITA,
    REGLAS_CONSISTENCIA,
    REGLAS_CONTEXTO_ESTRUCTURAL,
    REGLAS_MAPA_COINCIDENCIA,
    REGLAS_PRIORIDAD,
    REGLAS_PRIORIDAD_VISITA,
    UMBRALES_INDICE,
    calcular_indice_prioridad,
    calcular_prioridad_visita,
    evaluar_consistencia,
    evaluar_senales,
    texto_recomendacion_visita,
)
from modos_app import (
    MODO_CORREDORES,
    MODO_INTEGRAL,
    MODO_TERRITORIAL,
    MODOS_ANALISIS,
    TOLERANCIA_RECORTE_M,
    TIPO_AREA_DIBUJADA,
    TIPO_AREA_SUBCUENCA,
    aplicar_limite_cuenca,
    area_debe_recortarse_a_cuenca,
)
from reporte_cartografico import crear_mapa_conectividad, crear_mapa_fragmentacion
from portal_html import inyectar_estilo_portal
from territorio_local import (
    FUENTE_CUENCA,
    FUENTE_SUBCUENCAS,
    coleccion_cuenca,
    coleccion_subcuencas,
    geometria_cuenca,
    geometria_subcuenca,
    huella_territorial,
    nombres_subcuencas,
)


if not st.session_state.get("_pagina_configurada"):
    st.set_page_config(
        page_title="Visor CHCP | Preevaluación territorial y conectividad",
        page_icon=":material/map:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.session_state["_pagina_configurada"] = True

st.markdown(
    """
    <style>
    :root {
        --institucional-verde: #0a4393;
        --institucional-verde-oscuro: #062a5e;
        --institucional-verde-acento: #77cc09;
        --institucional-verde-claro: #eef1f7;
        --institucional-tinta: #062a5e;
        --institucional-suave: #566176;
        --institucional-borde: #d6deeb;
        --institucional-fondo: #f6f8fb;
        --portal-amarillo: #fabc20;
    }
    .stApp {background: var(--institucional-fondo); color: var(--institucional-tinta);}
    html {color-scheme: light;}
    .block-container {
        padding: 3.35rem .45rem .7rem;
        max-width: none;
    }
    .block-container [data-testid="stVerticalBlock"] {gap: .55rem;}
    .block-container [data-testid="stHorizontalBlock"] {gap: .6rem;}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp label, .stApp li, .stApp small, .stApp summary,
    .stApp legend, .stApp th, .stApp td,
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stExpander"] summary {
        color: var(--institucional-tinta);
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: var(--institucional-suave) !important;
    }
    [data-testid="stMetricValue"] {font-size: 1.55rem;}
    .stApp a {
        color: var(--institucional-verde);
        text-decoration-color: var(--institucional-verde-acento);
        text-underline-offset: .16em;
    }
    .stApp a:hover {color: var(--institucional-verde-oscuro);}
    .stButton > button,
    .stDownloadButton > button {
        border-color: var(--institucional-verde);
        color: var(--institucional-verde);
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: var(--institucional-verde-oscuro);
        color: var(--institucional-verde-oscuro);
    }
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    .stButton button[data-testid="stBaseButton-primary"],
    .stDownloadButton button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"] {
        border-color: var(--institucional-verde) !important;
        background: var(--institucional-verde) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700;
    }
    .stButton > button[kind="primary"] *,
    .stDownloadButton > button[kind="primary"] *,
    .stButton button[data-testid="stBaseButton-primary"] *,
    .stDownloadButton button[data-testid="stBaseButton-primary"] *,
    button[data-testid="stBaseButton-primary"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover,
    .stButton button[data-testid="stBaseButton-primary"]:hover,
    .stDownloadButton button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        border-color: var(--institucional-verde-oscuro) !important;
        background: var(--institucional-verde-oscuro) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-testid="stSidebar"][data-collapsed="false"] {
        border-right: 1px solid var(--institucional-borde);
        width: 340px !important;
        min-width: 340px;
        max-width: 340px;
        box-shadow: 6px 0 20px rgba(6,42,94,.05);
    }
    [data-testid="stSidebar"][data-collapsed="true"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        flex-basis: 0 !important;
        border-right: 0;
        box-shadow: none;
    }
    [data-testid="stSidebar"] > div:first-child {background: #ffffff; padding-top: .35rem;}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap: .45rem;}
    [data-testid="stSidebar"] hr {margin: .35rem 0;}
    [data-testid="stSidebar"] * {overflow-wrap: anywhere;}
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {color: var(--institucional-verde);}
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        margin-bottom:.35rem;border:1px solid var(--institucional-borde);
        border-radius:6px;background:var(--institucional-verde-claro);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] {
        background:#ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color:var(--institucional-verde)!important;font-weight:700;
    }
    [data-testid="stSidebar"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
        position: sticky;
        top: 0;
        z-index: 20;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0;
        background: #ffffff;
        border-bottom: 1px solid var(--institucional-borde);
    }
    [data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"] {
        min-width: 0;
        min-height: 48px;
        padding: .45rem .25rem;
        color: var(--institucional-suave) !important;
        font-size: .68rem;
        font-weight: 750;
        letter-spacing: .045em;
        text-transform: uppercase;
    }
    [data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--institucional-verde) !important;
        box-shadow: inset 0 -4px 0 var(--institucional-verde-acento);
    }
    [data-testid="stSidebar"] [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding: .65rem 0 5.5rem;
    }
    [data-testid="stSidebar"] .st-key-acciones_sidebar {
        position: fixed;
        left: 0;
        bottom: 0;
        z-index: 30;
        width: 340px;
        margin: 0;
        padding: .65rem .85rem calc(.65rem + env(safe-area-inset-bottom, 0px));
        border-top: 1px solid var(--institucional-borde);
        background: rgba(255,255,255,.98);
        box-shadow: 0 -8px 18px rgba(6,42,94,.08);
    }
    [data-testid="stSidebar"][data-collapsed="true"] .st-key-acciones_sidebar {
        display: none;
    }
    #MainMenu, footer {visibility: hidden;}
    iframe {max-width: 100% !important;}
    button, [role="button"] {min-height: 44px;}
    button:focus-visible, [role="button"]:focus-visible,
    input:focus-visible, select:focus-visible, textarea:focus-visible,
    .leyenda-info:focus-visible {
        outline: 3px solid var(--institucional-verde-acento);
        outline-offset: 2px;
    }
    .cabecera-app {
        padding: 1.45rem 1.6rem 1.5rem;
        border: 1px solid var(--institucional-borde);
        border-left: 6px solid var(--institucional-verde);
        border-radius: .2rem;
        background: #ffffff;
        color: var(--institucional-tinta);
        margin-bottom: .8rem;
    }
    .cabecera-app h1 {
        margin: 0;
        font-size: clamp(2.15rem, 4vw, 3.35rem);
        line-height: 1.12;
        letter-spacing: -.025em;
        color: var(--institucional-verde);
        overflow-wrap: normal;
    }
    .cabecera-app .subtitulo-app {
        margin-top: .45rem;
        font-size: 1.2rem;
        line-height: 1.35;
        font-weight: 650;
        color: var(--institucional-tinta);
    }
    .cabecera-app p {margin: .65rem 0 0; color: var(--institucional-suave); max-width: 980px;}
    .alcance-app {margin-top: .65rem; font-size: .86rem; color: var(--institucional-suave);}
    .selector-modos-intro {
        max-width: 780px;
        margin: 1.25rem 0 .85rem;
    }
    .selector-modos-intro h2 {
        margin-bottom: .3rem;
        color: var(--institucional-verde);
        font-size: clamp(1.55rem, 2.5vw, 2.05rem);
    }
    .selector-modos-intro p {
        margin: 0;
        color: var(--institucional-suave);
        font-size: 1.02rem;
        line-height: 1.55;
    }
    .modo-card {
        min-height: 205px;
        padding: .2rem .1rem 0;
    }
    .modo-card small {
        display: block;
        margin-bottom: .4rem;
        color: var(--institucional-suave);
        font-weight: 700;
        letter-spacing: .035em;
        text-transform: uppercase;
    }
    .modo-card h3 {
        margin: 0 0 .45rem;
        color: var(--institucional-verde);
        font-size: 1.22rem;
        line-height: 1.3;
    }
    .modo-card p {
        margin: 0 0 .65rem;
        color: var(--institucional-suave);
        line-height: 1.5;
    }
    .modo-card .modo-resultado {
        padding-top: .6rem;
        border-top: 1px solid var(--institucional-borde);
        color: var(--institucional-tinta);
        font-size: .92rem;
    }
    .modo-activo {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem .8rem;
        align-items: baseline;
        margin: .15rem 0 .75rem;
        padding: .7rem .85rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: var(--institucional-verde-claro);
    }
    .modo-activo b {color: var(--institucional-verde);}
    .modo-activo span {color: var(--institucional-suave);}
    .resumen-inicial {
        margin: .9rem 0 1rem;
        padding: 1rem 1.1rem 1.05rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: #ffffff;
    }
    .resumen-inicial h2 {
        margin: 0 0 .35rem;
        color: var(--institucional-verde);
        font-size: 1.35rem;
        line-height: 1.3;
    }
    .resumen-inicial > p {
        max-width: 75ch;
        margin: 0;
        color: var(--institucional-suave);
        font-size: 1rem;
        line-height: 1.6;
    }
    .resumen-principiante {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin: .85rem 0;
    }
    .resumen-paso {
        position: relative;
        min-height: 136px;
        padding: .85rem .9rem .85rem 3.25rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: var(--institucional-fondo);
    }
    .resumen-paso-numero {
        position: absolute;
        top: .85rem;
        left: .85rem;
        display: inline-grid;
        place-items: center;
        width: 1.8rem;
        height: 1.8rem;
        border-radius: 50%;
        background: var(--institucional-verde);
        color: #ffffff;
        font-weight: 750;
    }
    .resumen-paso h3 {
        margin: 0 0 .3rem;
        color: var(--institucional-verde);
        font-size: 1rem;
        line-height: 1.35;
    }
    .resumen-paso p {
        margin: 0;
        color: var(--institucional-suave);
        font-size: .92rem;
        line-height: 1.5;
    }
    .resumen-aclaracion {
        margin-top: .25rem;
        padding: .75rem .85rem;
        border-left: 4px solid var(--institucional-verde);
        border-radius: 0 .25rem .25rem 0;
        background: var(--institucional-verde-claro);
        color: var(--institucional-tinta);
        font-size: .93rem;
        line-height: 1.55;
    }
    .resumen-aclaracion strong {color: var(--institucional-verde);}
    .flujo-pasos {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .55rem;
        margin: .2rem 0 .8rem;
    }
    .flujo-paso {
        position: relative;
        min-height: 74px;
        padding: .75rem .8rem .7rem 3.2rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: #ffffff;
        color: var(--institucional-suave);
        font-size: .84rem;
        line-height: 1.4;
    }
    .flujo-paso b {
        display: block;
        margin-bottom: .12rem;
        color: var(--institucional-tinta);
        font-size: .94rem;
    }
    .flujo-numero {
        position: absolute;
        top: .72rem;
        left: .72rem;
        display: inline-grid;
        place-items: center;
        width: 1.9rem;
        height: 1.9rem;
        border: 1px solid var(--institucional-borde);
        border-radius: 50%;
        background: var(--institucional-fondo);
        color: var(--institucional-suave);
        font-weight: 750;
    }
    .flujo-paso.completado {
        border-color: #8dbeae;
        background: #f2f8f5;
    }
    .flujo-paso.completado .flujo-numero {
        border-color: var(--institucional-verde);
        background: var(--institucional-verde);
        color: #ffffff;
    }
    .flujo-paso.actual {
        border: 2px solid var(--institucional-verde);
        background: var(--institucional-verde-claro);
        box-shadow: 0 3px 10px rgba(0, 84, 77, .09);
    }
    .flujo-paso.actual .flujo-numero {
        border-color: var(--institucional-verde);
        background: #ffffff;
        color: var(--institucional-verde);
    }
    .flujo-paso.pendiente .flujo-estado {
        color: var(--institucional-suave);
    }
    .flujo-estado {
        display: block;
        margin-top: .3rem;
        color: var(--institucional-verde);
        font-size: .73rem;
        font-weight: 700;
        letter-spacing: .035em;
        text-transform: uppercase;
    }
    .tarjeta-resumen {
        border: 1px solid var(--institucional-borde);
        border-radius: .2rem;
        padding: .85rem 1rem;
        background: #ffffff;
        height: 100%;
    }
    .entregables {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin: .75rem 0 1rem;
    }
    .entregable {
        min-height: 92px;
        padding: .75rem .85rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: #ffffff;
    }
    .entregable small {
        display: block;
        margin-bottom: .2rem;
        color: var(--institucional-verde);
        font-weight: 750;
        letter-spacing: .035em;
        text-transform: uppercase;
    }
    .entregable b {
        display: block;
        margin-bottom: .18rem;
        color: var(--institucional-tinta);
    }
    .entregable span {
        color: var(--institucional-suave);
        font-size: .84rem;
        line-height: 1.4;
    }
    .contexto-analisis {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1px;
        margin: .3rem 0 1rem;
        border: 1px solid var(--institucional-borde);
        background: var(--institucional-borde);
    }
    .contexto-item {background: #ffffff; padding: .75rem .85rem; min-height: 72px;}
    .contexto-item small {display: block; color: var(--institucional-suave); margin-bottom: .2rem;}
    .contexto-item strong {color: var(--institucional-tinta);}
    .lectura-rapida {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .7rem;
        margin: .65rem 0 1rem;
    }
    .lectura-tarjeta {
        min-height: 132px;
        padding: .85rem .95rem;
        border: 1px solid var(--institucional-borde);
        border-top: 4px solid var(--institucional-verde);
        border-radius: .3rem;
        background: #ffffff;
    }
    .lectura-tarjeta small {
        display: block;
        margin-bottom: .35rem;
        color: var(--institucional-suave);
        font-size: .75rem;
        font-weight: 750;
        letter-spacing: .045em;
        text-transform: uppercase;
    }
    .lectura-tarjeta b {
        display: block;
        margin-bottom: .28rem;
        color: var(--institucional-tinta);
        font-size: 1rem;
    }
    .lectura-tarjeta p {
        margin: 0;
        color: var(--institucional-suave);
        font-size: .86rem;
        line-height: 1.48;
    }
    .resultado-prioridad {
        padding: 1rem 1.1rem;
        border: 1px solid var(--institucional-borde);
        border-left: 6px solid var(--prioridad-color);
        border-radius: .3rem;
        background: #ffffff;
        margin: .5rem 0 1rem;
    }
    .resultado-prioridad small {
        display: block;
        margin-bottom: .2rem;
        color: var(--institucional-suave);
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .05em;
        text-transform: uppercase;
    }
    .resultado-prioridad strong {
        display: block;
        color: var(--prioridad-color);
        font-size: 1.35rem;
        line-height: 1.25;
    }
    .resultado-prioridad p {
        margin: .45rem 0 0;
        color: var(--institucional-tinta);
        line-height: 1.5;
    }
    .eri-resumen {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: .75rem;
        align-items: center;
        margin: .8rem 0 .45rem;
        padding: .85rem .9rem;
        border: 1px solid var(--institucional-borde);
        border-left: 6px solid var(--eri-color);
        border-radius: .3rem;
        background: #ffffff;
    }
    .eri-resumen small {
        display: block;
        color: var(--institucional-suave);
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .045em;
        text-transform: uppercase;
    }
    .eri-resumen strong {
        display: block;
        margin-top: .16rem;
        color: var(--eri-color);
        font-size: 1.08rem;
        line-height: 1.25;
    }
    .eri-resumen p {
        margin: .28rem 0 0;
        color: var(--institucional-suave);
        font-size: .82rem;
        line-height: 1.4;
    }
    .eri-resumen > span {
        display: grid;
        place-items: center;
        width: 3.2rem;
        height: 3.2rem;
        border: 3px solid var(--eri-color);
        border-radius: 50%;
        color: var(--eri-color);
        font-size: 1rem;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
    }
    .recuperacion-error {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin: .7rem 0 1rem;
    }
    .recuperacion-paso {
        padding: .8rem .9rem;
        border: 1px solid #dfb8b3;
        border-radius: .35rem;
        background: #fffafa;
    }
    .recuperacion-paso b {
        display: block;
        margin-bottom: .22rem;
        color: #8f2921;
    }
    .recuperacion-paso span {
        color: #5c4946;
        font-size: .85rem;
        line-height: 1.45;
    }
    .bloque-metodo {
        border: 1px solid var(--institucional-borde);
        border-radius: .2rem;
        background: #ffffff;
        padding: .8rem 1rem;
        margin: .5rem 0;
    }
    .leyenda-fila {
        display: grid;
        grid-template-columns: 1.05rem minmax(0, 1fr);
        align-items: start;
        gap: .55rem;
        margin: .22rem 0;
        font-size: .9rem;
    }
    .leyenda-color {
        width: 1.05rem;
        height: 1.05rem;
        border: 1px solid rgba(0,0,0,.35);
        flex: 0 0 1.05rem;
    }
    .leyenda-texto {
        align-self: center;
        line-height: 1.4;
    }
    .leyenda-detalle {
        min-width: 0;
        margin: 0;
    }
    .leyenda-detalle summary {
        display: flex;
        align-items: center;
        gap: .45rem;
        min-height: 2.75rem;
        margin: 0;
        padding: .35rem 0;
        cursor: pointer;
        list-style: none;
        touch-action: manipulation;
    }
    .leyenda-detalle summary::-webkit-details-marker {display: none;}
    .leyenda-detalle summary:focus-visible {
        outline: 3px solid rgba(0, 84, 77, .35);
        outline-offset: 2px;
        border-radius: .2rem;
    }
    .leyenda-info {
        display: inline-grid;
        place-items: center;
        width: 1.55rem;
        height: 1.55rem;
        border: 1.5px solid currentColor;
        border-radius: 50%;
        color: var(--institucional-verde);
        background: #ffffff;
        font-size: .88rem;
        font-weight: 700;
        line-height: 1;
        flex: 0 0 1.55rem;
        transition: background-color .18s ease, color .18s ease;
    }
    .leyenda-detalle summary:hover .leyenda-info,
    .leyenda-detalle[open] .leyenda-info {
        color: #ffffff;
        background: var(--institucional-verde);
    }
    .leyenda-ayuda {
        margin: .35rem 0 .55rem;
        padding: .5rem .65rem;
        border-left: 3px solid var(--institucional-verde);
        border-radius: 0 .2rem .2rem 0;
        background: var(--institucional-verde-claro);
        color: var(--institucional-verde);
        font-size: .84rem;
        line-height: 1.45;
    }
    .ndvi-metodo-fila {
        display: flex;
        align-items: center;
        gap: .75rem;
        min-height: 52px;
        padding: .55rem .7rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .35rem;
        background: #ffffff;
    }
    .ndvi-metodo-color {
        width: 1.35rem;
        height: 1.35rem;
        border: 1px solid rgba(0,0,0,.42);
        border-radius: .15rem;
        flex: 0 0 1.35rem;
    }
    .ndvi-metodo-texto {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: .25rem .6rem;
        min-width: 0;
    }
    .ndvi-metodo-rango {
        color: var(--institucional-suave);
        font-variant-numeric: tabular-nums;
    }
    @media (prefers-reduced-motion: reduce) {
        .leyenda-info {transition: none;}
    }
    .resultado-fuente {
        padding: .7rem .85rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .2rem;
        background: #ffffff;
        margin-bottom: .45rem;
    }
    .lectura-bosque {
        margin: .6rem 0 1rem;
        padding: .9rem 1rem;
        border: 1px solid var(--institucional-borde);
        border-left: 5px solid var(--institucional-verde);
        border-radius: .3rem;
        background: #ffffff;
        color: var(--institucional-tinta);
        line-height: 1.55;
    }
    .lectura-bosque b {
        display: block;
        margin-bottom: .2rem;
        color: var(--institucional-verde);
        font-size: 1.02rem;
    }
    .lectura-bosque p {margin: 0; color: var(--institucional-suave);}
    .comparador-anios {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: .65rem .85rem;
        margin: .25rem 0 .55rem;
        border: 1px solid rgba(0,84,77,.28);
        border-radius: .2rem;
        background: var(--institucional-verde-claro);
        color: var(--institucional-verde);
    }
    .comparador-anios span:last-child {text-align: right;}
    .corredor-aviso {
        margin: .75rem 0 1rem;
        padding: .9rem 1rem;
        border: 1px solid var(--institucional-borde);
        border-left: 5px solid var(--institucional-verde-acento);
        border-radius: .3rem;
        background: #ffffff;
        color: var(--institucional-tinta);
        line-height: 1.55;
    }
    .corredor-aviso strong {color: var(--institucional-verde);}
    .categoria-corredor {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        min-height: 32px;
        padding: .25rem .55rem;
        margin: .15rem .25rem .15rem 0;
        border: 1px solid var(--institucional-borde);
        border-radius: 999px;
        background: #ffffff;
        font-size: .86rem;
        font-weight: 700;
    }
    .visor-barra {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: .65rem;
        min-height: 46px;
        margin: 0 0 .2rem;
        padding: .4rem .65rem;
        border: 0;
        border-bottom: 5px solid var(--institucional-verde-acento);
        border-radius: 0;
        background: linear-gradient(112deg, var(--institucional-verde) 0 78%, var(--institucional-verde-oscuro) 78%);
        box-shadow: 0 8px 22px rgba(6,42,94,.12);
    }
    .visor-marca {min-width: 0;}
    .visor-marca small {
        display: block;
        margin-bottom: .12rem;
        color: #dce8f8;
        font-size: .68rem;
        font-weight: 750;
        letter-spacing: .055em;
        text-transform: uppercase;
    }
    .visor-marca strong {
        display: block;
        color: #ffffff;
        font-size: clamp(1rem, 1.5vw, 1.28rem);
        line-height: 1.2;
    }
    .visor-contexto {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: .3rem;
    }
    .visor-etiqueta {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: .2rem .55rem;
        border: 1px solid rgba(255,255,255,.55);
        border-radius: 999px;
        background: rgba(255,255,255,.1);
        color: #ffffff;
        font-size: .76rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .panel-titulo {margin:0;color:var(--institucional-verde);font-size:.78rem;font-weight:750;letter-spacing:.055em;text-transform:uppercase;}
    .panel-ayuda {
        margin: -.35rem 0 .8rem;
        color: var(--institucional-suave);
        font-size: .9rem;
        line-height: 1.5;
    }
    .mapa-cabecera,
    .resultado-cabecera {
        margin:0 0 .4rem;
        padding:.55rem .7rem;
        border-bottom:5px solid var(--institucional-verde-acento);
        background:var(--institucional-verde);
        color:#ffffff;
    }
    .mapa-cabecera {background:linear-gradient(112deg,var(--institucional-verde) 0 82%,var(--institucional-verde-oscuro) 82%);}
    .mapa-cabecera small,
    .resultado-cabecera small {
        display:block;margin-bottom:.18rem;color:#cfe0f5;font-size:.7rem;
        font-weight:750;letter-spacing:.065em;text-transform:uppercase;
    }
    .mapa-cabecera strong,
    .resultado-cabecera strong {display:block;color:#ffffff;font-size:1rem;line-height:1.2;}
    .mapa-nota {margin:0 0 .35rem;padding:.35rem .5rem;border-left:4px solid var(--institucional-verde-acento);background:#f3f8e9;color:var(--institucional-suave);font-size:.8rem;line-height:1.35;}
    .dashboard-area {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1px;
        margin: .15rem 0 .45rem;
        border: 1px solid var(--institucional-borde);
        border-radius: 6px;
        overflow: hidden;
        background: var(--institucional-borde);
    }
    .dashboard-area > div {
        min-width: 0;
        padding: .48rem .55rem;
        background: var(--institucional-verde-claro);
    }
    .dashboard-area small {
        display: block;
        margin-bottom: .08rem;
        color: var(--institucional-suave);
        font-size: .74rem;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
    }
    .dashboard-area strong {
        display: block;
        color: var(--institucional-tinta);
        line-height: 1.25;
        font-size: .92rem;
        overflow-wrap: anywhere;
    }
    .dashboard-estado {
        margin: .35rem 0 .5rem;
        padding: .75rem .85rem;
        border-left: 4px solid var(--institucional-verde-acento);
        background: #f3f8e9;
        color: var(--institucional-tinta);
        font-size: .9rem;
        line-height: 1.5;
    }
    .dashboard-grafica-intro {
        margin: .15rem 0 .65rem;
        padding: .68rem .78rem;
        border: 1px solid var(--institucional-borde);
        border-left: 5px solid var(--institucional-verde-acento);
        border-radius: .45rem;
        background: linear-gradient(135deg, var(--institucional-verde-claro) 0%, #f4f9e9 100%);
        color: var(--institucional-tinta);
        font-size: .86rem;
        line-height: 1.45;
    }
    .grafica-contextual-cabecera {
        margin: .55rem 0 .35rem;
        padding: .55rem .65rem;
        border: 1px solid var(--institucional-borde);
        border-left: 5px solid var(--institucional-verde-acento);
        border-radius: 6px;
        background: #ffffff;
    }
    .grafica-contextual-cabecera small {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        margin-bottom: .3rem;
        padding: .18rem .55rem;
        border: 2px solid #78a9bd;
        border-radius: 999px;
        background: #e8f3f7;
        color: var(--institucional-tinta);
        font-size: .68rem;
        font-weight: 750;
        letter-spacing: .025em;
        text-transform: none;
    }
    .grafica-contextual-cabecera strong {
        display: block;
        color: var(--institucional-tinta);
        font-size: .94rem;
        line-height: 1.25;
    }
    .grafica-contextual-nota {
        margin: -.1rem 0 .35rem;
        color: var(--institucional-suave);
        font-size: .78rem;
        line-height: 1.35;
    }
    .dashboard-dato-clave {
        margin: .55rem 0 .25rem;
        padding: .7rem .78rem;
        border: 1px solid var(--institucional-borde);
        border-left: 5px solid var(--institucional-verde-acento);
        border-radius: .45rem;
        background: #f4f9e9;
        color: var(--institucional-tinta);
        font-size: .86rem;
        line-height: 1.45;
    }
    .dashboard-dato-clave b {color: var(--institucional-verde);}
    [data-testid="stVegaLiteChart"] {
        padding: .7rem .65rem .35rem;
        border: 1px solid var(--institucional-borde);
        border-radius: .55rem;
        background: #ffffff;
        box-shadow: 0 8px 22px rgba(6,42,94,.08);
    }
    [data-testid="stMetric"] {
        min-height: 88px;
        padding: .55rem .65rem;
        border: 1px solid var(--institucional-borde);
        border-radius: 6px;
        background: var(--institucional-verde-claro);
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {font-weight: 650;}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: .15rem;
        border-bottom: 1px solid var(--institucional-borde);
    }
    [data-testid="stTabs"] button[role="tab"] {min-height: 42px;}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--institucional-verde) !important;
        box-shadow: inset 0 -4px 0 var(--institucional-verde-acento);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--institucional-borde) !important;
        background: #ffffff;
        border-radius: 6px !important;
    }
    .resultado-bajo-mapa {
        margin-top: .2rem;
        padding: .2rem .1rem 0;
    }
    iframe[title="streamlit_folium.st_folium"] {
        border: 1px solid var(--institucional-borde);
        border-radius: 6px;
        background: var(--institucional-verde-claro);
        box-shadow: 0 8px 24px rgba(6,42,94,.08);
    }
    @media (max-width: 760px) {
        .flujo-pasos, .contexto-analisis, .entregables, .resumen-principiante,
        .lectura-rapida, .recuperacion-error {grid-template-columns: 1fr 1fr;}
        .block-container {padding: 3.5rem .75rem 2rem;}
        [data-testid="stSidebar"][data-collapsed="false"] {
            width: auto !important;
            min-width: auto;
            max-width: none;
        }
        [data-testid="stSidebar"] .st-key-acciones_sidebar {
            width: 100%;
            max-width: 100vw;
        }
        .cabecera-app {padding: 1.2rem;}
        .cabecera-app h1 {font-size: 2rem; line-height: 1.15;}
        .visor-barra {align-items: flex-start; flex-direction: column;}
        .visor-contexto {justify-content: flex-start;}
        .dashboard-area {grid-template-columns: 1fr 1fr;}
    }
    @media (max-width: 480px) {
        .flujo-pasos, .contexto-analisis, .entregables, .resumen-principiante,
        .lectura-rapida, .recuperacion-error {grid-template-columns: 1fr;}
        .flujo-paso {min-height: 82px;}
        .resumen-inicial {padding: .9rem;}
        .resumen-inicial > p {font-size: 1rem;}
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# El CSS del HTML entregado es la fuente visual final y prevalece sobre los
# estilos históricos que aún usan componentes internos de la aplicación.
inyectar_estilo_portal()


# -----------------------------------------------------------------------------
# Configuración centralizada
# -----------------------------------------------------------------------------


def secreto_opcional(nombre, predeterminado=None):
    """Lee un secreto sin fallar cuando el archivo local todavía no existe."""

    try:
        return st.secrets.get(nombre, predeterminado)
    except StreamlitSecretNotFoundError:
        return predeterminado


APP_VERSION = "UX-5.3-HTML-EXACTO-LIMITES-LOCALES"

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
        "subdomains": "abcd",
    },
    "OpenStreetMap": {
        "tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "OpenStreetMap contributors",
        "max_zoom": 19,
    },
}

COLORES_FUENTES = {
    "JRC TMF": "#1F8A70",
    "Hansen GFC": "#E76F51",
    "ESRI LULC": "#3A7CA5",
    "GEDI": "#7A5195",
    "NDVI": "#9BBF30",
}
COLORES_CAMBIOS = {
    "Deforestación JRC": "#C73E3A",
    "Degradación JRC": "#F2A541",
    "Regeneración forestal JRC": "#43AA8B",
    "Pérdida Hansen post-2020": "#E76F51",
    "Salida de árboles ESRI": "#3A7CA5",
    "Disminución NDVI": "#9BBF30",
}
COLORES_CONECTIVIDAD = {
    "En corredores": "#2E7D5B",
    "Fuera de corredores": "#7B8CA5",
    "Bosque 2021": "#76B72A",
    "Otros usos 2021": "#B7791F",
    "Cercanos": "#2A9D8F",
    "Separados": "#E76F51",
}
METHODOLOGY_VERSION = "MT-2026.17-PORTAL-ERI-INDICATIVO"
PROYECTO_EE = secreto_opcional("EE_PROJECT", "ee-julissaguevaravega")
FUENTE_BOSQUE_NOMBRE = "Bosque y otros usos"
FUENTE_BOSQUE_ORGANIZACION = "SINIA–MiAMBIENTE"
ANO_BOSQUE_REFERENCIA = 2021
FUENTE_BOSQUE_CORTA = (
    f"{FUENTE_BOSQUE_ORGANIZACION} · {FUENTE_BOSQUE_NOMBRE} · "
    f"{ANO_BOSQUE_REFERENCIA}"
)
CAMPO_COBERTURA_BOSQUE_2021 = "Categoria"
VALOR_COBERTURA_BOSQUE_2021 = "Bosques y Otras Tierras Boscosas"
RADIO_BUSQUEDA_CORREDOR_M = 5_000
TOLERANCIA_GEOMETRIA_CONECTIVIDAD_M = 10

ASSET_FINCAS = secreto_opcional("EE_ASSET_FINCAS")
ASSET_BOSQUE_2021 = secreto_opcional("EE_ASSET_BOSQUE_2021")
ACCESO_FINCA_DURACION_SEG = 30 * 60
ACCESO_FINCA_MAX_INTENTOS = 5
ACCESO_FINCA_BLOQUEO_SEG = 60
HANSEN_ASSET = "UMD/hansen/global_forest_change_2025_v1_13"
TMF_ASSET = "projects/JRC/TMF/v1_2025/AnnualChanges"
ESRI_ASSET = (
    "projects/sat-io/open-datasets/landcover/"
    "ESRI_Global-LULC_10m_TS"
)
GEDI_ASSET = (
    "users/openforisearthmap/World_EarthMap/"
    "CanopyHeight_GEDI_V27"
)

ANO_REFERENCIA_ANALISIS = PERIODOS_ANALISIS["referencia"]
ANO_HANSEN_MAX = PERIODOS_ANALISIS["hansen_diagnostico"]
ANO_TMF_MAX = PERIODOS_ANALISIS["jrc_diagnostico"]
ANO_DIAG_TMF = PERIODOS_ANALISIS["jrc_diagnostico"]
ANO_ESRI_MIN = PERIODOS_ANALISIS["esri_inicial"]
ANO_ESRI_MAX = PERIODOS_ANALISIS["esri_final"]
ANO_NDVI_INICIAL_ANALISIS = PERIODOS_ANALISIS["ndvi_inicial"]
ANO_NDVI_FINAL_ANALISIS = PERIODOS_ANALISIS["ndvi_final"]
ANO_NDVI_MAX = PERIODOS_ANALISIS["ndvi_final_visual"]
ESCALA_ANALISIS_NDVI_M = 20
ANO_ERI_REFERENCIA = min(2024, ANO_ESRI_MAX)
ESCALA_ERI_M = 90
RADIO_CONECTIVIDAD_ERI_M = 1_500
DISTANCIA_RIPARIA_ERI_M = 1_000
ALTURA_REFERENCIA_ERI_M = 35
AREA_DRENAJE_ERI_KM2 = 1.0
CUTOFF_YEAR = 20
CUTOFF_LABEL = "31/12/2020"

UMBRAL_ALERTA_HANSEN_HA = UMBRALES_INDICE["hansen_post_2020_ha"]
UMBRAL_REVISION_TMF_DEGRAD_HA = UMBRALES_INDICE["jrc_degradacion_ha"]
UMBRAL_REVISION_TMF_DEFOR_HA = UMBRALES_INDICE["jrc_deforestacion_ha"]
UMBRAL_PCT_TMF_DEFOR = UMBRALES_INDICE["jrc_deforestacion_pct"]
UMBRAL_PCT_TMF_DEGRAD = UMBRALES_INDICE["jrc_degradacion_pct"]
UMBRAL_PCT_ESRI_SALIDA = UMBRALES_INDICE["esri_salida_arboles_pct"]
UMBRAL_ESRI_SALIDA_HA = UMBRALES_INDICE["esri_salida_arboles_ha"]
UMBRAL_DOSEL_BAJO_M = UMBRALES_INDICE["gedi_dosel_bajo_m"]
UMBRAL_COBERTURA_GEDI_PCT = UMBRALES_INDICE["gedi_cobertura_minima_pct"]
UMBRAL_LINEA_BASE_GEDI_PCT = UMBRALES_INDICE["gedi_linea_base_minima_pct"]
UMBRAL_DELTA_NDVI = UMBRALES_INDICE["ndvi_delta_disminucion"]
UMBRAL_VIGOR_INICIAL_NDVI = UMBRALES_INDICE["ndvi_vigor_inicial_minimo"]

ESRI_ORIG = [1, 2, 4, 5, 7, 8, 9, 10, 11]
ESRI_VIS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
ESRI_COLORES = [
    "1A5BAB",
    "358221",
    "87D19E",
    "FFDB5C",
    "ED022A",
    "EDE9E4",
    "F2FAFF",
    "C8C8C8",
    "C6AD8D",
]

VIS_TMF = {
    "min": 1,
    "max": 6,
    "palette": ["006400", "FFCC00", "FF0000", "43AA8B", "0000FF", "BDBDBD"],
}
VIS_ESRI = {"min": 1, "max": 9, "palette": ESRI_COLORES}
VIS_HANSEN_POST = {
    "min": 21,
    "max": 25,
    "palette": ["FF1744", "D50000", "B71C1C", "7F0000", "4A0000"],
}
VIS_HANSEN_PRE = {
    "min": 1,
    "max": 20,
    "palette": ["FFF9C4", "F9A825", "E65100", "C62828"],
}
VIS_HANSEN_TOTAL = {
    "min": 1,
    "max": 25,
    "palette": ["FFF9C4", "F9A825", "E65100", "FF1744", "7F0000"],
}
VIS_LINEA_BASE = {"min": 1, "max": 1, "palette": ["00C853"]}
VIS_TMF_DEFOR = {"min": 1, "max": 1, "palette": ["FF0000"]}
VIS_TMF_DEGRAD = {"min": 1, "max": 1, "palette": ["FFCC00"]}
VIS_TMF_REGENERACION = {"min": 1, "max": 1, "palette": ["43AA8B"]}
VIS_ESRI_CAMBIO = {
    "min": 1,
    "max": 3,
    "palette": ["00FF00", "FF0000", "006400"],
}
VIS_GEDI = {
    "min": 0,
    "max": 35,
    "palette": ["FFFFCC", "C2E699", "78C679", "31A354", "006837"],
}
VIS_ERI = {
    "min": 1,
    "max": 5,
    "palette": [clase["color"].lstrip("#") for clase in CLASES_ERI],
}
VIS_NDVI_DELTA = {
    "min": -0.3,
    "max": 0.3,
    "palette": ["7F0000", "D32F2F", "FF7043", "FFF9C4", "66BB6A", "2E7D32", "1B5E20"],
}
VIS_NDVI_CLASES = {
    "min": 0,
    "max": 4,
    "palette": ["B30000", "F4A582", "FFFFBF", "78C679", "006837"],
}
VIS_COINCIDENCIA_REVISION = {
    "min": 1,
    "max": 3,
    "palette": [
        REGLAS_MAPA_COINCIDENCIA["clases"][clase]["color"].lstrip("#")
        for clase in (1, 2, 3)
    ],
}
VIS_RGB = {"min": 150, "max": 3200, "gamma": 1.15, "bands": ["B4", "B3", "B2"]}

PERFILES_VISUALIZACION = {
    "Resumen de cambios territoriales": {
        "descripcion": (
            "Muestra primero los sectores donde coinciden las señales principales "
            "de cambio territorial."
        ),
        "modo": "Explorar capas",
        "comparador": "Sin comparador",
        "capas": [
            "Sectores para revisión",
        ],
    },
    "Corredores y conectividad": {
        "descripcion": (
            "Muestra corredores publicados, fragmentos de bosque y conexiones "
            "estructurales sin añadir capas satelitales de cambio."
        ),
        "modo": "Explorar capas",
        "comparador": "Sin comparador",
        "capas": [],
    },
    "Diagnóstico territorial integrado": {
        "descripcion": (
            "Conecta señales recientes, corredores y la estructura del bosque de 2021 "
            "para orientar la prioridad y el lugar de una visita."
        ),
        "modo": "Explorar capas",
        "comparador": "Sin comparador",
        "capas": [
            "Sectores para revisión",
        ],
    },
    "Consultar capas individuales": {
        "descripcion": (
            "Elija una o varias capas. Para JRC, ESRI y NDVI puede consultar un "
            "solo año, sin barrido temporal."
        ),
        "modo": "Explorar capas",
        "comparador": "Sin comparador",
        "capas": [
            "Sectores para revisión",
        ],
    },
    "Comparar estado forestal entre dos años (JRC TMF)": {
        "descripcion": "Compare visualmente el estado forestal de dos años mediante el swipe.",
        "modo": "Comparar años",
        "comparador": "JRC TMF",
        "capas": [],
    },
    "Comparar uso del suelo entre dos años (ESRI)": {
        "descripcion": "Compare visualmente las clases de uso y cobertura de dos años.",
        "modo": "Comparar años",
        "comparador": "ESRI LULC",
        "capas": [],
    },
    "Comparar vigor vegetal entre dos años (NDVI)": {
        "descripcion": "Compare clases de vigor vegetal de dos años; esta vista no modifica el índice.",
        "modo": "Comparar años",
        "comparador": "NDVI Sentinel-2",
        "capas": [],
    },
}

PERFILES_POR_MODO = {
    MODO_TERRITORIAL: [
        "Resumen de cambios territoriales",
        "Consultar capas individuales",
        "Comparar estado forestal entre dos años (JRC TMF)",
        "Comparar uso del suelo entre dos años (ESRI)",
        "Comparar vigor vegetal entre dos años (NDVI)",
    ],
    MODO_CORREDORES: ["Corredores y conectividad"],
    MODO_INTEGRAL: [
        "Diagnóstico territorial integrado",
    ],
}

LEYENDAS = {
    "Corredores Almanaque Azul": leyenda_corredores(),
    "Bosque 2021 de contexto": [
        (
            "#2f6b45",
            "Bosque 2021 dentro y alrededor del área",
            "Cobertura institucional visible en el contexto adaptativo; solo el bosque dentro del polígono se suma a las hectáreas",
        ),
    ],
    "Importancia de parches": [
        (
            "#a63f35",
            "Valor alto para mantener unido el bosque",
            "Fragmento ubicado en el grupo superior del cálculo; conviene conservarlo y revisarlo con atención",
        ),
        (
            "#d58a24",
            "Valor intermedio",
            "Fragmento con una contribución intermedia dentro del área analizada",
        ),
        (
            "#4f875f",
            "Valor menor",
            "Fragmento con menor contribución relativa dentro de esta área; no significa que carezca de valor ecológico",
        ),
    ],
    "Estructura esencial": [
        (
            "#00544d",
            "Enlaces estructurales esenciales",
            "Cada grupo se muestra con el mínimo de líneas necesario; el cálculo sí conserva todas las relaciones",
        ),
    ],
    "Ruta potencial al corredor": [
        (
            "#d97904",
            "Conexión estructural potencial",
            "Cadena de fragmentos cuyos saltos no superan la distancia elegida hasta un corredor publicado",
        ),
    ],
    "Separaciones potenciales": [
        (
            "#f6c7b8",
            "Fragmento separado",
            "No tiene otro fragmento dentro de la distancia elegida, incluso al considerar el entorno exterior",
        ),
        (
            "#7c2d12",
            "Distancia al vecino más próximo",
            "Línea discontinua desde un fragmento separado hacia su vecino más próximo; no confirma un corredor",
        ),
    ],
    "Sectores para revisión": [
        (
            REGLAS_MAPA_COINCIDENCIA["clases"][clase]["color"],
            REGLAS_MAPA_COINCIDENCIA["clases"][clase]["etiqueta"],
            REGLAS_MAPA_COINCIDENCIA["clases"][clase]["interpretacion"],
        )
        for clase in (1, 2, 3)
    ],
    "JRC TMF": [
        ("#006400", "Bosque no perturbado"),
        ("#FFCC00", "Degradación"),
        ("#FF0000", "Deforestación"),
        ("#43AA8B", "Regeneración forestal (Forest regrowth)"),
        ("#0000FF", "Agua"),
        ("#BDBDBD", "Otra cobertura"),
    ],
    "ESRI LULC": [
        ("#1A5BAB", "Agua"),
        ("#358221", "Árboles"),
        ("#87D19E", "Vegetación inundada"),
        ("#FFDB5C", "Cultivos"),
        ("#ED022A", "Área construida"),
        ("#EDE9E4", "Suelo desnudo"),
        ("#F2FAFF", "Nieve/hielo"),
        ("#C8C8C8", "Nubes"),
        ("#C6AD8D", "Pastizal/matorral"),
    ],
    "Pérdida Hansen post-2020": [
        ("#FF1744", "2021"),
        ("#D50000", "2022"),
        ("#B71C1C", "2023"),
        ("#7F0000", "2024"),
        ("#4A0000", "2025"),
    ],
    "Pérdida Hansen 2001-2020": [
        ("#FFF9C4", "Pérdida más antigua"),
        ("#F9A825", "Pérdida intermedia"),
        ("#C62828", "Pérdida próxima a 2020"),
    ],
    "Cobertura arbórea persistente": [("#00C853", "Cobertura arbórea persistente hasta 2020")],
    "Deforestación JRC": [("#FF0000", "Deforestación")],
    "Degradación JRC": [("#FFCC00", "Degradación")],
    "Regeneración forestal JRC": [
        (
            "#43AA8B",
            "Regeneración forestal",
            "Área antes deforestada que JRC TMF clasifica actualmente como bosque en regeneración",
        )
    ],
    "ERI indicativo": [
        (
            clase["color"],
            f"{clase['etiqueta']} · {clase['minimo']:.2f}–{min(clase['maximo'], 1):.2f}",
            clase["lectura"],
        )
        for clase in CLASES_ERI
    ],
    "Transiciones ESRI": [
        ("#00FF00", "No árbol → árboles"),
        ("#FF0000", "Árboles → no árbol"),
        ("#006400", "Árboles estables"),
    ],
    "Altura GEDI": [
        ("#FFFFCC", "Dosel bajo"),
        ("#78C679", "Dosel medio"),
        ("#006837", "Dosel alto"),
    ],
    "ΔNDVI": [
        ("#7F0000", "Pérdida fuerte de vigor"),
        ("#FF7043", "Pérdida moderada"),
        ("#FFF9C4", "Cambio pequeño"),
        ("#66BB6A", "Aumento de vigor"),
        ("#1B5E20", "Aumento fuerte"),
    ],
    "Vegetación NDVI": [
        (
            clase["color"],
            f"{clase['etiqueta']} · {clase['rango']}",
            clase["interpretacion"],
        )
        for clase in CLASES_VIGOR_NDVI
    ],
    "NDVI Sentinel-2": [
        (
            clase["color"],
            f"{clase['etiqueta']} · {clase['rango']}",
            clase["interpretacion"],
        )
        for clase in CLASES_VIGOR_NDVI
    ],
}


def construir_registro_metodologico(
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
    anio_tmf_visual_inicial,
    anio_tmf_visual_final,
    anio_esri_visual_inicial,
    anio_esri_visual_final,
    anio_ndvi_visual_inicial,
    anio_ndvi_visual_final,
    anio_tmf_capa,
    anio_esri_capa,
    anio_ndvi_capa,
    modo_analisis,
    modo_comparador,
    capas_activas,
    resultados=None,
):
    if tipo_area == "Finca de monitoreo":
        especificacion_area = {
            "tipo": "finca_privada",
            "identificador": str(finca_id),
            "geometria_vectorial_incluida": False,
            "fuente": "coleccion_privada_configurada_en_el_servidor",
            "recorte": FUENTE_CUENCA,
        }
    elif tipo_area == TIPO_AREA_SUBCUENCA:
        especificacion_area = {
            "tipo": "subcuenca",
            "identificador": str(subcuenca_nombre),
            "fuente": FUENTE_SUBCUENCAS,
            "geometria_vectorial_incluida": True,
            "geojson": geometria_subcuenca(subcuenca_nombre),
            "recorte": FUENTE_CUENCA,
        }
    elif tipo_area == TIPO_AREA_DIBUJADA:
        especificacion_area = {
            "tipo": "poligono_dibujado",
            "geojson": json.loads(geometria_geojson),
            "recorte": FUENTE_CUENCA,
        }
    else:
        especificacion_area = {
            "tipo": "cuenca",
            "fuente": FUENTE_CUENCA,
            "geometria_vectorial_incluida": True,
            "geojson": geometria_cuenca(),
        }

    configuracion = {
        "metodologia": METHODOLOGY_VERSION,
        "modo_analisis": modo_analisis,
        "version_limites_locales": huella_territorial(),
        "area": especificacion_area,
        "periodos": {
            "referencia_metodologica": ANO_REFERENCIA_ANALISIS,
            "diagnostico_fijo": {
                "jrc": ANO_DIAG_TMF,
                "hansen": ANO_HANSEN_MAX,
                "esri_inicial": ANO_ESRI_MIN,
                "esri_final": ANO_ESRI_MAX,
                "ndvi_inicial": ANO_NDVI_INICIAL_ANALISIS,
                "ndvi_final": ANO_NDVI_FINAL_ANALISIS,
            },
            "visualizacion": {
                "comparador": modo_comparador,
                "jrc_inicial": anio_tmf_visual_inicial,
                "jrc_final": anio_tmf_visual_final,
                "esri_inicial": anio_esri_visual_inicial,
                "esri_final": anio_esri_visual_final,
                "ndvi_inicial": anio_ndvi_visual_inicial,
                "ndvi_final": anio_ndvi_visual_final,
                "capas_un_ano": {
                    "jrc": anio_tmf_capa,
                    "esri": anio_esri_capa,
                    "ndvi": anio_ndvi_capa,
                },
                "capas_disponibles": list(capas_activas),
            },
            "corte_referencia": CUTOFF_LABEL,
        },
        "fuentes": [
            {
                "nombre": "JRC Tropical Moist Forest",
                "asset": TMF_ASSET,
                "banda": f"Dec{ANO_DIAG_TMF}",
                "escala_m": 30,
                "uso": "diagnostico",
            },
            {
                "nombre": "Hansen Global Forest Change",
                "asset": HANSEN_ASSET,
                "bandas": ["treecover2000", "loss", "lossyear"],
                "escala_m": 30,
                "uso": "diagnostico",
            },
            {
                "nombre": "ESRI Land Use Land Cover",
                "asset": ESRI_ASSET,
                "escala_m": 10,
                "uso": "diagnostico",
            },
            {
                "nombre": "GEDI Canopy Height",
                "asset": GEDI_ASSET,
                "escala_m": 100,
                "uso": "contexto",
            },
            {
                "nombre": "Índice de Resiliencia Ecológica indicativo",
                "componentes": [
                    "integridad estructural",
                    "conectividad local del bosque",
                    "estabilidad topográfica",
                    "proximidad riparia",
                ],
                "fuentes": [
                    "Dynamic World",
                    "GEDI / OpenForis",
                    "Copernicus DEM GLO-30",
                    "MERIT Hydro",
                ],
                "escala_resumen_m": ESCALA_ERI_M,
                "pesos": dict(PESOS_ERI),
                "uso": (
                    "lectura ecologica complementaria; no modifica el indice de indicios "
                    "ni la prioridad de visita"
                ),
            },
            {
                "nombre": "Sentinel-2 Surface Reflectance Harmonized",
                "asset": "COPERNICUS/S2_SR_HARMONIZED",
                "bandas": ["B8", "B4", "SCL"],
                "escala_m": 10,
                "uso": "diagnostico corroborativo de disminucion del vigor vegetal",
            },
            {
                "nombre": "Mapa de conectividad ecologica de Panama",
                "organizacion": "Fundacion Almanaque Azul",
                "version": cargar_catalogo_corredores()["version_publicada"],
                "url": URL_MAPA_CORREDORES,
                "categorias": ["alta", "mediana", "media-baja"],
                "uso": (
                    "valor estrategico de la prioridad de visita; no modifica "
                    "el indice satelital de cambios"
                ),
            },
            {
                "nombre": FUENTE_BOSQUE_NOMBRE,
                "organizacion": FUENTE_BOSQUE_ORGANIZACION,
                "ano_referencia": ANO_BOSQUE_REFERENCIA,
                "formato": "asset vectorial institucional privado de Earth Engine",
                "configurado": bool(ASSET_BOSQUE_2021),
                "campo_clase": CAMPO_COBERTURA_BOSQUE_2021,
                "valor_bosque": VALOR_COBERTURA_BOSQUE_2021,
                "uso": (
                    "fragmentacion y conectividad estructural para focalizar "
                    "la visita; no participa en el puntaje ni constituye una serie anual"
                ),
            },
        ],
        "umbrales": dict(UMBRALES_INDICE),
        "justificacion_umbrales": dict(JUSTIFICACION_UMBRALES),
        "pesos": dict(PESOS_INDICE),
        "justificacion_pesos": dict(JUSTIFICACION_PESOS),
        "reglas_prioridad": dict(REGLAS_PRIORIDAD),
        "reglas_prioridad_visita": dict(REGLAS_PRIORIDAD_VISITA),
        "reglas_contexto_estructural": dict(REGLAS_CONTEXTO_ESTRUCTURAL),
        "reglas_consistencia": dict(REGLAS_CONSISTENCIA),
        "mapa_coincidencia_espacial": {
            "nombre": REGLAS_MAPA_COINCIDENCIA["nombre"],
            "malla_referencia_m": REGLAS_MAPA_COINCIDENCIA[
                "malla_referencia_m"
            ],
            "fuentes": dict(REGLAS_MAPA_COINCIDENCIA["fuentes"]),
            "clases": {
                str(clase): dict(especificacion)
                for clase, especificacion in REGLAS_MAPA_COINCIDENCIA[
                    "clases"
                ].items()
            },
            "participa_indice": REGLAS_MAPA_COINCIDENCIA["participa_indice"],
            "limitacion": REGLAS_MAPA_COINCIDENCIA["limitacion"],
        },
        "clases_vigor_ndvi": [dict(clase) for clase in CLASES_VIGOR_NDVI],
        "eri_indicativo": {
            "clases": [dict(clase) for clase in CLASES_ERI],
            "pesos": dict(PESOS_ERI),
            "radio_conectividad_m": RADIO_CONECTIVIDAD_ERI_M,
            "distancia_riparia_m": DISTANCIA_RIPARIA_ERI_M,
            "participa_en_prioridad": False,
            "limitacion": (
                "Indicador exploratorio que requiere validacion de campo. La conectividad "
                "es un proxy de cobertura local y no demuestra movimiento de fauna."
            ),
        },
        "procesamiento": {
            "unidad_area": "hectareas",
            "reduccion": "suma de area por clase en la proyeccion de cada fuente",
            "respuesta_earth_engine": "reducciones agrupadas en una sola respuesta",
            "ndvi": "mediana anual con mascara SCL y respaldo del ano anterior",
            "formula_ndvi": "(B8 - B4) / (B8 + B4)",
            "ndvi_escala_resumen_m": ESCALA_ANALISIS_NDVI_M,
            "coincidencia_espacial": (
                "JRC conserva su malla de 30 m; Hansen se reproyecta por vecino "
                "más cercano y ESRI se agrega desde 10 m por presencia máxima "
                "antes de sumar las tres señales binarias."
            ),
            "corredores": (
                "Interseccion vectorial en Equal Earth Americas (EPSG:8857); "
                "conserva las categorias originales de Almanaque Azul. El "
                "solapamiento y la pertenencia al Corredor Biologico "
                "Mesoamericano aportan a la prioridad separada de visita."
            ),
            "estructura_bosque": (
                "Los parches de Bosque y otros usos 2021 forman una red según el "
                "umbral seleccionado. Su condición orienta la focalización de la "
                "visita sin añadir un peso ecológico no calibrado."
            ),
            "eri": (
                "Promedio ponderado normalizado entre 0 y 1: integridad estructural 35 %, "
                "conectividad local 25 %, estabilidad topográfica 20 % y proximidad "
                "riparia 20 %. Se reporta por separado del puntaje operativo."
            ),
        },
    }
    huella = hashlib.sha256(
        json.dumps(configuracion, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    registro = {
        "aplicacion": APP_VERSION,
        "fecha_generacion": date.today().isoformat(),
        "codigo_reproducibilidad": huella,
        "explicacion_codigo": (
            "Identificador técnico generado a partir del área, las fuentes, los períodos, "
            "los umbrales, los pesos y las reglas de esta configuración."
        ),
        **configuracion,
        "alcance": (
            "Preevaluacion indicativa para priorizar revisiones. No constituye validacion "
            "de campo ni determina cumplimiento EUDR."
        ),
    }
    if resultados and "puntaje" in resultados:
        registro["resultados_resumen"] = {
            "area_ha": resultados["area_ha"],
            "puntaje": resultados["puntaje"],
            "prioridad": resultados["prioridad"],
            "senal_jrc": resultados["senal_tmf"],
            "senal_hansen": resultados["senal_hansen"],
            "senal_esri": resultados["senal_esri"],
            "senal_gedi": resultados["senal_gedi"],
            "senal_ndvi": resultados["senal_ndvi"],
            "aportes_indice": resultados["aportes_indice"],
            "consistencia": resultados["consistencia"],
            "corredores": resultados.get("corredores"),
            "prioridad_visita": resultados.get("prioridad_visita"),
            "eri_indicativo": (
                {
                    "valor": resultados["eri"].get("valor"),
                    "clase": resultados["eri"].get("clase"),
                    "componente_limitante": resultados["eri"].get(
                        "componente_limitante"
                    ),
                    "participa_en_prioridad": False,
                }
                if resultados.get("eri")
                else None
            ),
            "estadisticas": {
                "cobertura_arborea_persistente_2020_ha": resultados["linea_base"],
                "hansen_pre_2021_ha": resultados["hansen_pre"],
                "hansen_post_2020_ha": resultados["hansen_post"],
                "tmf_clases_ha": {
                    "bosque_estable": resultados["tmf_estable"],
                    "degradacion": resultados["tmf_degradacion"],
                    "deforestacion": resultados["tmf_deforestacion"],
                    "recuperacion": resultados["tmf_recuperacion"],
                    "agua": resultados["tmf_agua"],
                    "otra_cobertura": resultados["tmf_otra_cobertura"],
                },
                "esri_arboles_final_ha": resultados["esri_arboles_final"],
                "esri_salida_arboles_ha": resultados["esri_salida"],
                "esri_ganancia_arboles_ha": resultados["esri_ganancia"],
                "gedi_altura_media_m": resultados["gedi_altura"],
                "gedi_cobertura_valida_pct": resultados["gedi_cobertura_pct"],
                "ndvi_inicial_medio": resultados["ndvi_inicial_medio"],
                "ndvi_final_medio": resultados["ndvi_final_medio"],
                "ndvi_delta_medio": resultados["ndvi_delta_medio"],
                "ndvi_disminucion_ha": resultados["ndvi_disminucion"],
                "ndvi_disminucion_pct": resultados["pct_ndvi_disminucion"],
                "ndvi_cobertura_valida_pct": resultados["ndvi_cobertura_pct"],
                "coincidencia_espacial_ha": {
                    "una_fuente": resultados["coincidencia_1_fuente"],
                    "dos_fuentes": resultados["coincidencia_2_fuentes"],
                    "tres_fuentes": resultados["coincidencia_3_fuentes"],
                    "dos_o_tres_fuentes": resultados[
                        "coincidencia_varias_fuentes"
                    ],
                },
            },
        }
    elif resultados:
        registro["resultados_resumen"] = {
            "area_ha": resultados.get("area_ha"),
            "corredores": resultados.get("corredores"),
            "eri_indicativo": resultados.get("eri"),
        }

    if resultados and resultados.get("fragmentacion"):
        registro["resultados_resumen"]["fragmentacion_conectividad"] = {
            "metricas_clase": resultados["fragmentacion"]["metricas_clase"],
            "metricas_red": resultados["fragmentacion"]["metricas_red"],
            "conexion_corredor": resultados["fragmentacion"].get(
                "conexion_corredor"
            ),
            "top_conectores": resultados["fragmentacion"]["top_conectores"],
            "campo_clase": resultados["fragmentacion"]["campo_clase"],
            "valores_bosque": resultados["fragmentacion"]["valores_bosque"],
            "fuente_cobertura": resultados["fragmentacion"].get(
                "fuente_cobertura", FUENTE_BOSQUE_CORTA
            ),
            "ano_referencia_cobertura": resultados["fragmentacion"].get(
                "ano_referencia_cobertura", ANO_BOSQUE_REFERENCIA
            ),
            "metodo": resultados["fragmentacion"]["metodo"],
            "participa_indice_prioridad": False,
            "papel_diagnostico": (
                "orienta la focalizacion espacial de la visita y permite "
                "identificar conectores y componentes aislados"
            ),
        }
    return registro


# -----------------------------------------------------------------------------
# Earth Engine y datos
# -----------------------------------------------------------------------------

@st.cache_resource
def iniciar_earth_engine():
    secreto = secreto_opcional("EE_SERVICE_ACCOUNT_JSON")
    if secreto is None:
        raise RuntimeError(
            "Falta EE_SERVICE_ACCOUNT_JSON en los secretos de esta aplicación."
        )
    if isinstance(secreto, str):
        informacion = json.loads(secreto)
    else:
        informacion = dict(secreto)
    credenciales = service_account.Credentials.from_service_account_info(
        informacion,
        scopes=[
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/cloud-platform",
        ],
    )
    ee.Initialize(credentials=credenciales, project=PROYECTO_EE)
    return True


def acceso_fincas_vigente():
    return time.time() < float(st.session_state.get("fincas_acceso_hasta", 0))


def cerrar_acceso_fincas():
    st.session_state.pop("fincas_acceso_hasta", None)
    st.session_state.pop("codigo_acceso_fincas", None)
    st.session_state.pop("mensaje_acceso_fincas", None)


def procesar_codigo_acceso_fincas():
    ahora = time.time()
    codigo_configurado = str(secreto_opcional("FINCAS_ACCESS_CODE", ""))
    codigo_ingresado = str(st.session_state.get("codigo_acceso_fincas", ""))
    bloqueo_hasta = float(st.session_state.get("fincas_bloqueo_hasta", 0))

    if ahora < bloqueo_hasta:
        st.session_state["mensaje_acceso_fincas"] = (
            "warning",
            "Acceso temporalmente bloqueado. Espere un minuto antes de volver a intentarlo.",
        )
    elif hmac.compare_digest(codigo_ingresado, codigo_configurado):
        st.session_state["fincas_acceso_hasta"] = ahora + ACCESO_FINCA_DURACION_SEG
        st.session_state["fincas_intentos_acceso"] = 0
        st.session_state["mensaje_acceso_fincas"] = (
            "success",
            "Acceso autorizado para esta sesión.",
        )
    else:
        intentos = int(st.session_state.get("fincas_intentos_acceso", 0)) + 1
        if intentos >= ACCESO_FINCA_MAX_INTENTOS:
            st.session_state["fincas_bloqueo_hasta"] = ahora + ACCESO_FINCA_BLOQUEO_SEG
            st.session_state["fincas_intentos_acceso"] = 0
            mensaje = (
                "warning",
                "Demasiados intentos. El acceso quedó bloqueado durante un minuto.",
            )
        else:
            st.session_state["fincas_intentos_acceso"] = intentos
            restantes = ACCESO_FINCA_MAX_INTENTOS - intentos
            mensaje = (
                "error",
                f"Código incorrecto. Quedan {restantes} intentos antes del bloqueo temporal.",
            )
        st.session_state["mensaje_acceso_fincas"] = mensaje

    # El código digitado no permanece almacenado en la sesión.
    st.session_state["codigo_acceso_fincas"] = ""


def solicitar_acceso_fincas(contenedor=None):
    if contenedor is None:
        contenedor = st.sidebar
    codigo_configurado = str(secreto_opcional("FINCAS_ACCESS_CODE", ""))
    if not ASSET_FINCAS or len(codigo_configurado) < 8:
        contenedor.error(
            "El acceso privado a las fincas no está configurado. El administrador debe "
            "definir EE_ASSET_FINCAS y FINCAS_ACCESS_CODE en los secretos de Streamlit."
        )
        return False

    mensaje = st.session_state.pop("mensaje_acceso_fincas", None)
    if acceso_fincas_vigente():
        contenedor.success("Acceso privado a fincas activo")
        contenedor.caption("La autorización caduca automáticamente después de 30 minutos.")
        contenedor.button(
            "Cerrar acceso a fincas",
            on_click=cerrar_acceso_fincas,
            use_container_width=True,
        )
        if mensaje and mensaje[0] == "success":
            contenedor.success(mensaje[1])
        return True

    bloqueo_hasta = float(st.session_state.get("fincas_bloqueo_hasta", 0))
    if time.time() < bloqueo_hasta:
        contenedor.warning(
            "Acceso temporalmente bloqueado. Espere un minuto antes de volver a intentarlo."
        )
        return False

    contenedor.info(
        "Esta opción contiene información privada. Ingrese el código autorizado para "
        "consultar la lista de fincas."
    )
    contenedor.text_input(
        "Código de acceso",
        type="password",
        key="codigo_acceso_fincas",
        help="El código no se guarda en GitHub ni se incluye en los informes.",
    )
    contenedor.button(
        "Acceder a las fincas",
        type="primary",
        on_click=procesar_codigo_acceso_fincas,
        use_container_width=True,
    )
    if mensaje:
        getattr(contenedor, mensaje[0])(mensaje[1])
    return False


def nombre_area_legible(
    tipo_area,
    finca_id=None,
    subcuenca_nombre=None,
):
    if tipo_area == "Toda la cuenca":
        return "Cuenca hidrográfica de interés"
    if tipo_area == TIPO_AREA_SUBCUENCA:
        return f"Subcuenca {subcuenca_nombre}"
    if tipo_area == TIPO_AREA_DIBUJADA:
        return "Polígono dibujado por el usuario"
    nombre = str(finca_id).strip()
    return nombre if nombre.casefold().startswith("finca") else f"Finca {nombre}"


def clave_orden_natural(valor):
    partes = re.split(r"(\d+)", str(valor).strip())
    return tuple(
        (0, int(parte)) if parte.isdigit() else (1, parte.casefold())
        for parte in partes
        if parte
    )


@st.cache_data(ttl=3600, max_entries=4)
def obtener_ids_fincas():
    if not ASSET_FINCAS or not acceso_fincas_vigente():
        raise PermissionError("La colección privada requiere un acceso autorizado.")
    valores = (
        ee.FeatureCollection(ASSET_FINCAS)
        .aggregate_array("FincaID")
        .distinct()
        .getInfo()
    )
    return sorted(
        [valor for valor in valores if valor is not None],
        key=clave_orden_natural,
    )


@st.cache_data(max_entries=4)
def obtener_ids_subcuencas():
    return sorted(nombres_subcuencas(), key=clave_orden_natural)


def obtener_geometria_solicitada(
    tipo_area,
    finca_id=None,
    subcuenca_nombre=None,
    geometria_geojson=None,
):
    if tipo_area == "Finca de monitoreo":
        if not ASSET_FINCAS or not acceso_fincas_vigente():
            raise PermissionError("La finca privada requiere un acceso autorizado.")
        return (
            ee.FeatureCollection(ASSET_FINCAS)
            .filter(ee.Filter.eq("FincaID", finca_id))
            .geometry()
        )

    if tipo_area == TIPO_AREA_SUBCUENCA:
        if subcuenca_nombre is None:
            raise ValueError("Debe seleccionar una subcuenca antes de ejecutar el análisis.")
        return ee.Geometry(geometria_subcuenca(subcuenca_nombre))

    if tipo_area == TIPO_AREA_DIBUJADA:
        if not geometria_geojson:
            raise ValueError("Debe dibujar un polígono antes de ejecutar el análisis.")
        datos_geometria = (
            json.loads(geometria_geojson)
            if isinstance(geometria_geojson, str)
            else geometria_geojson
        )
        return ee.Geometry(datos_geometria)

    return ee.Geometry(geometria_cuenca())


def obtener_area(
    tipo_area,
    finca_id=None,
    subcuenca_nombre=None,
    geometria_geojson=None,
):
    geometria_solicitada = obtener_geometria_solicitada(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria_cuenca_local = ee.Geometry(geometria_cuenca())
    geometria_analisis = aplicar_limite_cuenca(
        tipo_area,
        geometria_solicitada,
        geometria_cuenca_local,
    )
    return ee.FeatureCollection(
        [ee.Feature(geometria_analisis, {"Origen": tipo_area})]
    )


@st.cache_data(ttl=3600, max_entries=64, show_spinner=False)
def obtener_superficies_area_cache(
    tipo_area,
    finca_id=None,
    subcuenca_nombre=None,
    geometria_geojson=None,
):
    area = obtener_area(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria_solicitada = obtener_geometria_solicitada(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria_analizada = area.geometry(TOLERANCIA_RECORTE_M)
    superficies = ee.Dictionary(
        {
            "analizada": geometria_analizada.area(TOLERANCIA_RECORTE_M).divide(10000),
            "solicitada": geometria_solicitada.area(TOLERANCIA_RECORTE_M).divide(10000),
        }
    ).getInfo()
    return {
        "analizada": float(superficies.get("analizada") or 0.0),
        "solicitada": float(superficies.get("solicitada") or 0.0),
    }


def serializar_poligono_dibujado(dibujo):
    geometria = dibujo.get("geometry", dibujo) if dibujo else None
    if not isinstance(geometria, dict):
        raise ValueError("No fue posible interpretar la geometría dibujada.")
    if geometria.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("La figura debe ser un polígono cerrado.")
    return json.dumps(geometria, sort_keys=True, separators=(",", ":"))


def obtener_limites(objeto):
    coordenadas = objeto.geometry().bounds(1).coordinates().getInfo()[0]
    longitudes = [punto[0] for punto in coordenadas]
    latitudes = [punto[1] for punto in coordenadas]
    return [
        [min(latitudes), min(longitudes)],
        [max(latitudes), max(longitudes)],
    ]


def obtener_limites_geojson(contenido):
    """Obtiene límites Leaflet de un GeoJSON sin depender de librerías GIS."""

    puntos = []

    def recorrer(valor):
        if not isinstance(valor, (list, tuple)):
            return
        if (
            len(valor) >= 2
            and isinstance(valor[0], (int, float))
            and isinstance(valor[1], (int, float))
        ):
            puntos.append((float(valor[1]), float(valor[0])))
            return
        for elemento in valor:
            recorrer(elemento)

    for feature in (contenido or {}).get("features", []):
        recorrer((feature.get("geometry") or {}).get("coordinates", []))
    if not puntos:
        return None
    latitudes = [punto[0] for punto in puntos]
    longitudes = [punto[1] for punto in puntos]
    return [
        [min(latitudes), min(longitudes)],
        [max(latitudes), max(longitudes)],
    ]


def convertir_imagen_byte(imagen):
    """Uniforma las colecciones categóricas antes de añadir un respaldo."""

    return ee.Image(imagen).toByte()


def obtener_tmf(anio, geometria):
    nombre_banda = f"Dec{anio}"
    coleccion_tmf = (
        ee.ImageCollection(TMF_ASSET)
        .filterBounds(geometria)
        .select([nombre_banda], [nombre_banda])
        .map(convertir_imagen_byte)
    )
    respaldo = (
        ee.Image.constant(0)
        .rename(nombre_banda)
        .updateMask(ee.Image(0))
        .toByte()
        .setDefaultProjection("EPSG:4326", None, 30)
    )
    return (
        coleccion_tmf
        .merge(ee.ImageCollection.fromImages([respaldo]))
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 30)
        .rename(f"tmf_{anio}")
        .clip(geometria)
    )


def obtener_esri(anio, geometria):
    anio_seguro = max(ANO_ESRI_MIN, min(ANO_ESRI_MAX, anio))
    nombre_banda = f"esri_{anio_seguro}"
    coleccion_anual_esri = (
        ee.ImageCollection(ESRI_ASSET)
        .filterDate(f"{anio_seguro}-01-01", f"{anio_seguro}-12-31")
    )
    coleccion_esri = (
        coleccion_anual_esri
        .filterBounds(geometria)
        .select([0], [nombre_banda])
        .map(convertir_imagen_byte)
    )
    respaldo = (
        ee.Image.constant(0)
        .rename(nombre_banda)
        .updateMask(ee.Image(0))
        .toByte()
        .setDefaultProjection("EPSG:4326", None, 10)
    )
    return (
        coleccion_esri
        .merge(ee.ImageCollection.fromImages([respaldo]))
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 10)
        .rename(nombre_banda)
        .clip(geometria)
    )


def obtener_esri_visual(anio, geometria):
    return (
        obtener_esri(anio, geometria)
        .remap(ESRI_ORIG, ESRI_VIS)
        .rename(f"esri_visual_{anio}")
        .selfMask()
    )


def mascara_sentinel_scl(imagen):
    scl = imagen.select("SCL")
    mascara = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
    return imagen.updateMask(mascara).select(["B8", "B4"]).toFloat()


def mascara_sentinel_rgb(imagen):
    scl = imagen.select("SCL")
    mascara = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
    return imagen.updateMask(mascara).select(["B4", "B3", "B2"]).toFloat()


def obtener_rgb_sentinel(anio, geometria):
    coleccion = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometria)
        .filterDate(f"{anio}-01-01", f"{anio}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
        .map(mascara_sentinel_rgb)
    )
    respaldo = (
        ee.Image.constant([0, 0, 0])
        .rename(["B4", "B3", "B2"])
        .updateMask(ee.Image(0))
        .toFloat()
    )
    return (
        coleccion.merge(ee.ImageCollection.fromImages([respaldo]))
        .median()
        .clip(geometria)
    )


def obtener_ndvi(anio, geometria):
    anio_respaldo = max(anio - 1, 2017)

    def coleccion(anio_consulta):
        return (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometria)
            .filterDate(f"{anio_consulta}-01-01", f"{anio_consulta}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
            .map(mascara_sentinel_scl)
        )

    fallback = (
        ee.Image.constant([0, 0])
        .rename(["B8", "B4"])
        .updateMask(ee.Image(0))
        .toFloat()
    )

    def mediana_con_fallback(coleccion_s2):
        return coleccion_s2.merge(
            ee.ImageCollection.fromImages([fallback])
        ).median()

    actual = mediana_con_fallback(coleccion(anio))
    anterior = mediana_con_fallback(coleccion(anio_respaldo))
    compuesto = ee.ImageCollection.fromImages(
        [fallback, anterior, actual]
    ).mosaic().setDefaultProjection("EPSG:4326", None, 10)

    return (
        compuesto.normalizedDifference(["B8", "B4"])
        .rename(f"ndvi_{anio}")
        .toFloat()
        .clip(geometria)
    )


def clasificar_ndvi(ndvi):
    clases = (
        ee.Image(0)
        .where(ndvi.lt(0.0), 0)
        .where(ndvi.gte(0.0).And(ndvi.lt(0.2)), 1)
        .where(ndvi.gte(0.2).And(ndvi.lt(0.4)), 2)
        .where(ndvi.gte(0.4).And(ndvi.lt(0.6)), 3)
        .where(ndvi.gte(0.6), 4)
    )
    return clases.updateMask(ndvi.mask()).rename("ndvi_clases").toInt()


def imagenes_hansen(geometria):
    hansen = ee.Image(HANSEN_ASSET)
    cobertura_2000 = hansen.select("treecover2000").unmask(0).gte(30)
    perdida = hansen.select("loss").unmask(0)
    anio_perdida = hansen.select("lossyear")

    perdida_post = (
        anio_perdida.updateMask(anio_perdida.gt(CUTOFF_YEAR))
        .rename("perdida_post")
        .clip(geometria)
    )
    perdida_pre = (
        anio_perdida.updateMask(
            anio_perdida.gt(0).And(anio_perdida.lte(CUTOFF_YEAR))
        )
        .rename("perdida_pre")
        .clip(geometria)
    )
    linea_base = (
        cobertura_2000.And(
            perdida.eq(0).Or(anio_perdida.unmask(0).gt(CUTOFF_YEAR))
        )
        .selfMask()
        .rename("linea_base_2020")
        .clip(geometria)
    )
    return perdida_post, perdida_pre, linea_base


def imagen_coincidencia_revision(
    geometria,
    tmf=None,
    perdida_post=None,
    esri_inicial=None,
    esri_final=None,
):
    """Estandariza tres señales de deterioro en la malla JRC de 30 m."""
    if tmf is None:
        tmf = obtener_tmf(ANO_DIAG_TMF, geometria)
    if perdida_post is None:
        perdida_post, _, _ = imagenes_hansen(geometria)
    if esri_inicial is None:
        esri_inicial = obtener_esri(ANO_ESRI_MIN, geometria)
    if esri_final is None:
        esri_final = obtener_esri(ANO_ESRI_MAX, geometria)

    proyeccion_referencia = ee.Image(tmf).projection()
    proyeccion_esri = ee.Image(esri_inicial).projection()
    senal_jrc = (
        ee.Image(tmf)
        .eq(2)
        .Or(ee.Image(tmf).eq(3))
        .unmask(0)
        .rename("senal_jrc")
    )
    senal_hansen = (
        ee.Image(perdida_post)
        .gt(0)
        .unmask(0)
        .reproject(crs=proyeccion_referencia)
        .rename("senal_hansen")
    )
    senal_esri_10m = (
        ee.Image(esri_inicial)
        .eq(2)
        .And(ee.Image(esri_final).neq(2))
        .unmask(0)
        .setDefaultProjection(proyeccion_esri)
    )
    senal_esri = (
        senal_esri_10m.reduceResolution(
            reducer=ee.Reducer.max(),
            bestEffort=True,
            maxPixels=1024,
        )
        .reproject(crs=proyeccion_referencia)
        .gt(0)
        .rename("senal_esri")
    )
    return (
        senal_jrc.add(senal_hansen)
        .add(senal_esri)
        .rename("fuentes_coincidentes")
        .toByte()
        .clip(geometria)
    )


def convertir_altura_gedi_float(imagen):
    """Uniforma el tipo de píxel antes de añadir el respaldo sin datos."""

    return ee.Image(imagen).toFloat()


def imagen_gedi(geometria):
    coleccion_gedi = (
        ee.ImageCollection(GEDI_ASSET)
        .filterBounds(geometria)
        .select([0], ["altura_dosel"])
        .map(convertir_altura_gedi_float)
    )
    respaldo = (
        ee.Image.constant(0)
        .rename("altura_dosel")
        .updateMask(ee.Image(0))
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 100)
    )
    return (
        coleccion_gedi
        .merge(ee.ImageCollection.fromImages([respaldo]))
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 100)
        .rename("altura_dosel")
        .clip(geometria)
    )


def convertir_probabilidad_arboles_float(imagen):
    """Uniforma Dynamic World antes de calcular la probabilidad anual de árboles."""

    return ee.Image(imagen).select(["trees"], ["p_arboles"]).toFloat()


def obtener_probabilidad_arboles(anio, geometria):
    """Probabilidad media anual de la clase árboles según Dynamic World."""

    coleccion = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(geometria)
        .filterDate(f"{anio}-01-01", f"{anio + 1}-01-01")
        .map(convertir_probabilidad_arboles_float)
    )
    respaldo = (
        ee.Image.constant(0)
        .rename("p_arboles")
        .updateMask(ee.Image(0))
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 10)
    )
    return (
        coleccion.merge(ee.ImageCollection.fromImages([respaldo]))
        .mean()
        .setDefaultProjection("EPSG:4326", None, 10)
        .rename("p_arboles")
        .clip(geometria)
    )


def construir_imagenes_eri(geometria):
    """Construye un ERI indicativo y sus cuatro componentes en Earth Engine.

    La conectividad se representa con la proporción local de bosque en una ventana
    de 1.5 km. Es un proxy espacial ligero, no reemplaza ECA/A ni una evaluación
    funcional por especie. Esta decisión mantiene el cálculo viable en Streamlit y
    se declara de forma explícita en la interfaz.
    """

    p_arboles = obtener_probabilidad_arboles(
        ANO_ERI_REFERENCIA,
        geometria,
    ).unmask(0).clamp(0, 1)

    altura_normalizada = (
        imagen_gedi(geometria)
        .divide(ALTURA_REFERENCIA_ERI_M)
        .clamp(0, 1)
        .unmask(p_arboles)
    )
    integridad = (
        altura_normalizada.multiply(0.5)
        .add(p_arboles.multiply(0.5))
        .rename("integridad_estructural")
    )

    proyeccion_eri = ee.Projection("EPSG:4326").atScale(ESCALA_ERI_M)
    bosque = (
        p_arboles.gte(0.5)
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 10)
    )
    bosque_eri = (
        bosque.reduceResolution(
            reducer=ee.Reducer.mean(),
            bestEffort=True,
            maxPixels=1024,
        )
        .reproject(crs=proyeccion_eri)
    )
    conectividad = (
        bosque_eri.focalMean(
            radius=RADIO_CONECTIVIDAD_ERI_M,
            kernelType="circle",
            units="meters",
        )
        .clamp(0, 1)
        .rename("conectividad")
    )

    dem_coleccion = (
        ee.ImageCollection("COPERNICUS/DEM/GLO30")
        .filterBounds(geometria)
        .select("DEM")
    )
    dem = (
        dem_coleccion.mosaic()
        .setDefaultProjection(ee.Image(dem_coleccion.first()).projection())
        .clip(geometria)
    )
    pendiente = ee.Terrain.slope(dem).divide(45).clamp(0, 1)
    estabilidad = (
        ee.Image(1)
        .subtract(pendiente.multiply(ee.Image(1).subtract(p_arboles)))
        .clamp(0, 1)
        .rename("estabilidad_topografica")
    )

    acumulacion = ee.Image("MERIT/Hydro/v1_0_1").select("upa")
    proyeccion_merit = acumulacion.projection()
    cauces = (
        acumulacion.gte(AREA_DRENAJE_ERI_KM2)
        .unmask(0)
        .setDefaultProjection(proyeccion_merit)
    )
    distancia_cauce_m = (
        cauces.fastDistanceTransform(256, "pixels", "squared_euclidean")
        .sqrt()
        .multiply(proyeccion_merit.nominalScale())
    )
    proximidad_riparia = (
        ee.Image(1)
        .subtract(distancia_cauce_m.divide(DISTANCIA_RIPARIA_ERI_M).clamp(0, 1))
        .rename("proximidad_riparia")
        .clip(geometria)
    )

    componentes = {
        "integridad_estructural": integridad.clip(geometria),
        "conectividad": conectividad.clip(geometria),
        "estabilidad_topografica": estabilidad.clip(geometria),
        "proximidad_riparia": proximidad_riparia,
    }
    eri = ee.Image(0)
    for clave, peso in PESOS_ERI.items():
        eri = eri.add(componentes[clave].multiply(peso))
    eri = eri.clamp(0, 1).rename("eri").clip(geometria)
    return eri, componentes


def clasificar_imagen_eri(eri):
    """Convierte el ERI continuo en cinco clases cartográficas etiquetadas."""

    clases = ee.Image(1)
    for indice, clase in enumerate(CLASES_ERI[1:], start=2):
        clases = clases.where(ee.Image(eri).gte(clase["minimo"]), indice)
    return clases.updateMask(ee.Image(eri).mask()).rename("eri_clase").toByte()


def capa_gee(
    mapa,
    imagen,
    visualizacion,
    nombre,
    mostrar=True,
    opacidad=1.0,
    control=True,
    z_index=None,
):
    datos = ee.Image(imagen).getMapId(visualizacion)
    opciones_capa = {}
    if z_index is not None:
        opciones_capa["z_index"] = int(z_index)
    capa = folium.TileLayer(
        tiles=datos["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=nombre,
        overlay=True,
        control=control,
        show=mostrar,
        opacity=opacidad,
        **opciones_capa,
    )
    capa.add_to(mapa)
    return capa


def agregar_mapa_base(mapa, nombre_mapa, control=False):
    """Agrega al visor el fondo elegido en la pestaña Mapa base."""

    configuracion = dict(MAPAS_BASE.get(nombre_mapa, MAPAS_BASE["Imagen satelital"]))
    folium.TileLayer(
        name=nombre_mapa,
        overlay=False,
        control=control,
        **configuracion,
    ).add_to(mapa)


def agregar_limite_cuenca_local(mapa, *, control=False, mostrar=True):
    """Dibuja la cuenca incluida con la app, sin consultar un asset de EE."""

    capa = folium.GeoJson(
        coleccion_cuenca(),
        name="Límite de la cuenca",
        control=control,
        show=mostrar,
        style_function=lambda _: {
            "color": "#062A5E",
            "weight": 2.4,
            "opacity": 0.95,
            "fillColor": "#062A5E",
            "fillOpacity": 0.025,
        },
        highlight_function=lambda _: {
            "color": "#0A4393",
            "weight": 3.2,
            "fillOpacity": 0.05,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre"],
            aliases=["Área:"],
            sticky=False,
        ),
    )
    capa.add_to(mapa)
    return capa


def agregar_subcuencas_local(mapa, *, control=False, mostrar=False):
    """Agrega la capa local de subcuencas entregada con el portal HTML."""

    capa = folium.GeoJson(
        coleccion_subcuencas(),
        name="Subcuencas del Canal",
        control=control,
        show=mostrar,
        style_function=lambda _: {
            "color": "#6085B9",
            "weight": 1.1,
            "opacity": 0.78,
            "fillColor": "#0A4393",
            "fillOpacity": 0.015,
        },
        highlight_function=lambda _: {
            "color": "#77CC09",
            "weight": 2.2,
            "fillOpacity": 0.08,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nombre", "grupo", "area_ha"],
            aliases=["Subcuenca:", "Grupo:", "Superficie (ha):"],
            localize=True,
            sticky=False,
        ),
    )
    capa.add_to(mapa)
    return capa


def imagen_bosque_contexto(geometria, distancia_m=RADIO_BUSQUEDA_CORREDOR_M):
    """Pinta la cobertura institucional dentro del área y su entorno de consulta."""

    limite_contexto = geometria.buffer(float(distancia_m))
    bosque = (
        ee.FeatureCollection(ASSET_BOSQUE_2021)
        .filter(
            ee.Filter.eq(
                CAMPO_COBERTURA_BOSQUE_2021,
                VALOR_COBERTURA_BOSQUE_2021,
            )
        )
        .filterBounds(limite_contexto)
    )
    return ee.Image(0).byte().paint(bosque, 1).selfMask().clip(limite_contexto)


def agregar_rotulos_comparador(mapa, limites, etiqueta_inicial, etiqueta_final):
    (sur, oeste), (norte, este) = limites
    margen_latitud = (norte - sur) * 0.045
    margen_longitud = (este - oeste) * 0.035
    latitud = norte - margen_latitud
    estilo = (
        "background:rgba(17,50,74,.92);color:white;padding:7px 10px;"
        "border:2px solid white;border-radius:6px;box-shadow:0 2px 7px rgba(0,0,0,.35);"
        "font:12px Arial,sans-serif;line-height:1.25;white-space:nowrap;"
    )
    folium.Marker(
        location=[latitud, oeste + margen_longitud],
        icon=folium.DivIcon(
            class_name="rotulo-comparador-mapa",
            icon_size=(185, 48),
            icon_anchor=(0, 0),
            html=(
                f'<div style="{estilo}"><span style="font-size:10px;">◀ AÑO INICIAL</span>'
                f'<br><b>{etiqueta_inicial}</b></div>'
            ),
        ),
        z_index_offset=1000,
    ).add_to(mapa)
    folium.Marker(
        location=[latitud, este - margen_longitud],
        icon=folium.DivIcon(
            class_name="rotulo-comparador-mapa",
            icon_size=(185, 48),
            icon_anchor=(185, 0),
            html=(
                f'<div style="{estilo}text-align:right;"><span style="font-size:10px;">'
                f'AÑO FINAL ▶</span><br><b>{etiqueta_final}</b></div>'
            ),
        ),
        z_index_offset=1000,
    ).add_to(mapa)


# -----------------------------------------------------------------------------
# Análisis bajo demanda
# -----------------------------------------------------------------------------

def numero(diccionario, clave):
    valor = diccionario.get(clave)
    return float(valor) if valor is not None else 0.0


def reducir_superficies(imagen, geometria, escala, proyeccion=None):
    parametros = {
        "reducer": ee.Reducer.sum(),
        "geometry": geometria,
        "scale": escala,
        "bestEffort": True,
        "maxPixels": 1e9,
        "tileScale": 4,
    }
    if proyeccion is not None:
        parametros["crs"] = proyeccion
    return ee.Dictionary(imagen.reduceRegion(**parametros))


def normalizar_histograma_gedi(histograma):
    """Convierte los intervalos devueltos por Earth Engine en columnas graficables."""

    intervalos = histograma or []
    return {
        "Altura (m)": [round((float(fila[0]) + float(fila[1])) / 2, 1) for fila in intervalos],
        "Observaciones": [int(round(float(fila[2]))) for fila in intervalos],
    }


@st.cache_data(ttl=1800, max_entries=48, show_spinner=False)
def calcular_serie_fuente(
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
    fuente,
):
    """Calcula una sola gráfica por solicitud para no sobrecargar Earth Engine."""

    area_fc = obtener_area(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria = area_fc.geometry(TOLERANCIA_RECORTE_M)
    pixel_ha = ee.Image.pixelArea().divide(10000)

    if fuente == "JRC Tropical Moist Forest":
        anios = list(range(2000, ANO_TMF_MAX + 1))
        bandas = []
        for anio in anios:
            tmf = obtener_tmf(anio, geometria)
            bandas.extend(
                [
                    tmf.eq(3).unmask(0).multiply(pixel_ha).rename(f"def_{anio}"),
                    tmf.eq(2).unmask(0).multiply(pixel_ha).rename(f"deg_{anio}"),
                    tmf.eq(4).unmask(0).multiply(pixel_ha).rename(f"regen_{anio}"),
                ]
            )
        resumen = reducir_superficies(
            ee.Image.cat(bandas),
            geometria,
            30,
            obtener_tmf(ANO_TMF_MAX, geometria).projection(),
        ).getInfo()
        return {
            "titulo": "Cambio forestal anual según JRC TMF",
            "descripcion": (
                "Superficie clasificada cada año como deforestación, degradación o "
                "regeneración forestal. Las tres series pertenecen a la misma fuente "
                "y sí pueden compararse."
            ),
            "tipo": "barras",
            "columnas": {
                "Año": anios,
                "Deforestación (ha)": [numero(resumen, f"def_{anio}") for anio in anios],
                "Degradación (ha)": [numero(resumen, f"deg_{anio}") for anio in anios],
                "Regeneración forestal (ha)": [
                    numero(resumen, f"regen_{anio}") for anio in anios
                ],
            },
        }

    if fuente == "Hansen Global Forest Change":
        anios = list(range(2001, ANO_HANSEN_MAX + 1))
        anio_perdida = ee.Image(HANSEN_ASSET).select("lossyear")
        bandas = [
            anio_perdida.eq(anio - 2000)
            .unmask(0)
            .multiply(pixel_ha)
            .rename(f"perdida_{anio}")
            for anio in anios
        ]
        resumen = reducir_superficies(
            ee.Image.cat(bandas),
            geometria,
            30,
            ee.Image(HANSEN_ASSET).projection(),
        ).getInfo()
        return {
            "titulo": "Pérdida anual de cobertura arbórea según Hansen",
            "descripcion": (
                "Hectáreas con pérdida anual de cobertura arbórea. La fuente detecta "
                "pérdida, pero por sí sola no identifica su causa."
            ),
            "tipo": "barras",
            "columnas": {
                "Año": anios,
                "Pérdida (ha)": [
                    numero(resumen, f"perdida_{anio}") for anio in anios
                ],
            },
        }

    if fuente == "ESRI Land Use / Land Cover":
        anios = list(range(ANO_ESRI_MIN, ANO_ESRI_MAX + 1))
        bandas = [
            obtener_esri(anio, geometria)
            .eq(2)
            .unmask(0)
            .multiply(pixel_ha)
            .rename(f"arboles_{anio}")
            for anio in anios
        ]
        resumen = reducir_superficies(
            ee.Image.cat(bandas),
            geometria,
            10,
            obtener_esri(ANO_ESRI_MAX, geometria).projection(),
        ).getInfo()
        return {
            "titulo": "Cobertura arbórea anual según ESRI",
            "descripcion": (
                "Superficie clasificada como árboles en cada edición anual. Cambios "
                "pequeños pueden reflejar tanto cambios reales como diferencias de clasificación."
            ),
            "tipo": "barras",
            "columnas": {
                "Año": anios,
                "Cobertura arbórea (ha)": [
                    numero(resumen, f"arboles_{anio}") for anio in anios
                ],
            },
        }

    if fuente == "Sentinel-2 · NDVI":
        anios = list(range(2017, ANO_NDVI_MAX + 1))
        bandas = [
            obtener_ndvi(anio, geometria).rename(f"ndvi_{anio}") for anio in anios
        ]
        resumen = ee.Image.cat(bandas).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometria,
            scale=max(100, ESCALA_ANALISIS_NDVI_M),
            bestEffort=True,
            maxPixels=1e9,
            tileScale=4,
        ).getInfo()
        return {
            "titulo": "Vigor medio de la vegetación según NDVI",
            "descripcion": (
                "Promedio anual del NDVI calculado con Sentinel-2. Sirve como señal "
                "corroborativa; nubes, estacionalidad y agua pueden afectar la lectura."
            ),
            "tipo": "barras",
            "columnas": {
                "Año": anios,
                "NDVI medio": [numero(resumen, f"ndvi_{anio}") for anio in anios],
            },
        }

    if fuente == "GEDI · altura del dosel":
        histograma = (
            imagen_gedi(geometria)
            .reduceRegion(
                reducer=ee.Reducer.fixedHistogram(0, 60, 12),
                geometry=geometria,
                scale=100,
                bestEffort=True,
                maxPixels=1e9,
                tileScale=4,
            )
            .get("altura_dosel")
            .getInfo()
        )
        return {
            "titulo": "Distribución de altura del dosel según GEDI",
            "descripcion": (
                "GEDI no es una serie anual comparable. Por eso se muestra la distribución "
                "de alturas disponibles y no una serie temporal artificial."
            ),
            "tipo": "barras",
            "columnas": normalizar_histograma_gedi(histograma),
        }

    raise ValueError(f"Fuente no reconocida: {fuente}")


@st.cache_data(ttl=3600, max_entries=64, show_spinner=False)
def analizar_corredores_cache(aoi_geojson_serializado):
    return analizar_interseccion_corredores(json.loads(aoi_geojson_serializado))


def analizar_bosque_asset(
    asset_id,
    campo_clase,
    valor_bosque,
    aoi_geojson_serializado,
    umbral_m,
    area_min_ha,
    radio_contexto_m,
):
    aoi_geojson = json.loads(aoi_geojson_serializado)
    aoi_ee = ee.Geometry(aoi_geojson)
    radio_contexto_m = min(
        float(RADIO_BUSQUEDA_CORREDOR_M),
        max(float(umbral_m), float(radio_contexto_m)),
    )
    contexto_ee = aoi_ee.buffer(radio_contexto_m)
    bosque_en_contexto = (
        ee.FeatureCollection(asset_id)
        .filter(ee.Filter.eq(campo_clase, valor_bosque))
        .filterBounds(contexto_ee)
    )
    if int(bosque_en_contexto.size().getInfo()) == 0:
        geometria_bosque = {"type": "FeatureCollection", "features": []}
    else:
        geometria_bosque = (
            bosque_en_contexto
            .geometry(TOLERANCIA_GEOMETRIA_CONECTIVIDAD_M)
            .intersection(contexto_ee, TOLERANCIA_GEOMETRIA_CONECTIVIDAD_M)
            .simplify(TOLERANCIA_GEOMETRIA_CONECTIVIDAD_M)
            .getInfo()
        )
    return analizar_fragmentacion_geojson(
        bosque_geojson=geometria_bosque,
        aoi_geojson=aoi_geojson,
        umbral_m=umbral_m,
        area_min_ha=area_min_ha,
        incluir_contexto_exterior=True,
        corredores_geojson=cargar_corredores(),
        radio_busqueda_corredor_m=radio_contexto_m,
    )


@st.cache_data(ttl=1800, max_entries=24, show_spinner=False)
def calcular_eri_indicativo(
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
):
    """Resume el ERI y su distribución sin alterar el puntaje de prioridad."""

    area_fc = obtener_area(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria = area_fc.geometry(TOLERANCIA_RECORTE_M)
    eri, componentes = construir_imagenes_eri(geometria)
    imagen_medias = ee.Image.cat(
        [componentes[clave].rename(clave) for clave in PESOS_ERI]
        + [eri.rename("eri")]
    )
    medias = ee.Dictionary(
        imagen_medias.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometria,
            scale=ESCALA_ERI_M,
            bestEffort=True,
            maxPixels=1e9,
            tileScale=4,
        )
    )
    clases = clasificar_imagen_eri(eri)
    pixel_ha = ee.Image.pixelArea().divide(10000)
    bandas_areas = []
    for indice, clase in enumerate(CLASES_ERI, start=1):
        bandas_areas.append(
            clases.eq(indice)
            .unmask(0)
            .multiply(pixel_ha)
            .rename(f"eri_{clase['clave']}_ha")
        )
    areas = reducir_superficies(
        ee.Image.cat(bandas_areas),
        geometria,
        ESCALA_ERI_M,
    )
    resumen = medias.combine(areas, True).getInfo()
    resultado = construir_resultado_eri(resumen)
    resultado.update(
        {
            "anio_referencia": ANO_ERI_REFERENCIA,
            "escala_resumen_m": ESCALA_ERI_M,
            "radio_conectividad_m": RADIO_CONECTIVIDAD_ERI_M,
            "distancia_riparia_m": DISTANCIA_RIPARIA_ERI_M,
            "fuentes": [
                "Dynamic World",
                "GEDI / OpenForis",
                "Copernicus DEM GLO-30",
                "MERIT Hydro",
            ],
            "nota_conectividad": (
                "La conectividad usa la proporción local de bosque en una ventana de "
                "1.5 km como proxy espacial ligero. No representa conectividad funcional "
                "por especie ni sustituye ECA/A."
            ),
            "nota_estructura": (
                "La integridad combina altura GEDI normalizada y probabilidad de árboles. "
                "Cuando GEDI no tiene cobertura, la probabilidad de árboles actúa como respaldo."
            ),
        }
    )
    return resultado


@st.cache_data(ttl=1800, max_entries=24, show_spinner=False)
def ejecutar_analisis(
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
    anio_tmf_diagnostico,
    anio_esri_inicial,
    anio_esri_final,
):
    area_fc = obtener_area(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )
    geometria = area_fc.geometry(TOLERANCIA_RECORTE_M)

    tmf = obtener_tmf(anio_tmf_diagnostico, geometria)
    esri_inicial = obtener_esri(anio_esri_inicial, geometria)
    esri_final = obtener_esri(anio_esri_final, geometria)
    perdida_post, perdida_pre, linea_base = imagenes_hansen(geometria)
    coincidencia_revision = imagen_coincidencia_revision(
        geometria,
        tmf=tmf,
        perdida_post=perdida_post,
        esri_inicial=esri_inicial,
        esri_final=esri_final,
    )
    gedi = imagen_gedi(geometria)
    ndvi_inicial = obtener_ndvi(ANO_NDVI_INICIAL_ANALISIS, geometria)
    ndvi_final = obtener_ndvi(ANO_NDVI_FINAL_ANALISIS, geometria)
    delta_ndvi = ndvi_final.subtract(ndvi_inicial).rename("ndvi_delta")
    mascara_ndvi_valida = ndvi_inicial.mask().And(ndvi_final.mask())
    disminucion_ndvi = (
        ndvi_inicial.gte(UMBRAL_VIGOR_INICIAL_NDVI)
        .And(delta_ndvi.lte(UMBRAL_DELTA_NDVI))
        .updateMask(mascara_ndvi_valida)
    )
    pixel_ha = ee.Image.pixelArea().divide(10000)

    # Cada fuente se reduce en su propia resolución y proyección. Esto evita
    # forzar los datos ESRI de 10 m a la malla de los productos de 30 m.
    areas_tmf = ee.Image.cat(
        [
            tmf.eq(1).unmask(0).multiply(pixel_ha).rename("tmf_estable"),
            tmf.eq(2).unmask(0).multiply(pixel_ha).rename("tmf_degradacion"),
            tmf.eq(3).unmask(0).multiply(pixel_ha).rename("tmf_deforestacion"),
            tmf.eq(4).unmask(0).multiply(pixel_ha).rename("tmf_recuperacion"),
            tmf.eq(5).unmask(0).multiply(pixel_ha).rename("tmf_agua"),
            tmf.eq(6).unmask(0).multiply(pixel_ha).rename("tmf_otra_cobertura"),
            coincidencia_revision.eq(1).unmask(0).multiply(pixel_ha).rename(
                "coincidencia_1_fuente"
            ),
            coincidencia_revision.eq(2).unmask(0).multiply(pixel_ha).rename(
                "coincidencia_2_fuentes"
            ),
            coincidencia_revision.eq(3).unmask(0).multiply(pixel_ha).rename(
                "coincidencia_3_fuentes"
            ),
        ]
    )
    areas_hansen = ee.Image.cat(
        [
            perdida_post.gt(0).unmask(0).multiply(pixel_ha).rename("hansen_post"),
            perdida_pre.gt(0).unmask(0).multiply(pixel_ha).rename("hansen_pre"),
            linea_base.unmask(0).multiply(pixel_ha).rename("linea_base"),
        ]
    )
    areas_esri = ee.Image.cat(
        [
            esri_final.eq(2).unmask(0).multiply(pixel_ha).rename("esri_arboles_final"),
            esri_inicial.eq(2).And(esri_final.neq(2)).unmask(0).multiply(pixel_ha).rename("esri_salida"),
            esri_inicial.neq(2).And(esri_final.eq(2)).unmask(0).multiply(pixel_ha).rename("esri_ganancia"),
            esri_inicial.eq(2).And(esri_final.eq(2)).unmask(0).multiply(pixel_ha).rename("esri_estable"),
        ]
    )
    areas_ndvi = ee.Image.cat(
        [
            disminucion_ndvi.unmask(0)
            .multiply(pixel_ha)
            .rename("ndvi_disminucion"),
            mascara_ndvi_valida.unmask(0)
            .multiply(pixel_ha)
            .rename("ndvi_area_datos"),
        ]
    )
    estadisticas_ndvi = ee.Image.cat(
        [
            ndvi_inicial.rename("ndvi_inicial_medio"),
            ndvi_final.rename("ndvi_final_medio"),
            delta_ndvi.rename("ndvi_delta_medio"),
        ]
    ).updateMask(mascara_ndvi_valida)

    # Las reducciones conservan la escala y proyección de cada fuente, pero se
    # agrupan en una sola respuesta para evitar varios viajes de red consecutivos.
    resumen = (
        reducir_superficies(areas_tmf, geometria, 30, tmf.projection())
        .combine(
            reducir_superficies(
                areas_hansen,
                geometria,
                30,
                ee.Image(HANSEN_ASSET).projection(),
            ),
            True,
        )
        .combine(
            reducir_superficies(
                areas_esri,
                geometria,
                10,
                esri_final.projection(),
            ),
            True,
        )
        .combine(
            reducir_superficies(
                areas_ndvi,
                geometria,
                ESCALA_ANALISIS_NDVI_M,
                ndvi_final.projection(),
            ),
            True,
        )
        .combine(
            ee.Dictionary(
                estadisticas_ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=geometria,
                    scale=ESCALA_ANALISIS_NDVI_M,
                    bestEffort=True,
                    maxPixels=1e9,
                    tileScale=4,
                )
            ),
            True,
        )
        .combine(
            ee.Dictionary(
                {
                    "area_ha": geometria.area(1).divide(10000),
                    "gedi_altura": gedi.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=geometria,
                        scale=100,
                        bestEffort=True,
                        maxPixels=1e9,
                        tileScale=4,
                    ).get("altura_dosel"),
                    "gedi_area_datos": gedi.mask()
                    .multiply(pixel_ha)
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=geometria,
                        scale=100,
                        bestEffort=True,
                        maxPixels=1e9,
                        tileScale=4,
                    )
                    .get("altura_dosel"),
                }
            ),
            True,
        )
        .getInfo()
    )

    claves_areas = [
        "tmf_estable",
        "tmf_degradacion",
        "tmf_deforestacion",
        "tmf_recuperacion",
        "tmf_agua",
        "tmf_otra_cobertura",
        "coincidencia_1_fuente",
        "coincidencia_2_fuentes",
        "coincidencia_3_fuentes",
        "hansen_post",
        "hansen_pre",
        "linea_base",
        "esri_arboles_final",
        "esri_salida",
        "esri_ganancia",
        "esri_estable",
        "ndvi_disminucion",
        "ndvi_area_datos",
    ]
    resultados = {clave: numero(resumen, clave) for clave in claves_areas}
    area_ha = numero(resumen, "area_ha")
    resultados["area_ha"] = area_ha
    resultados["gedi_altura"] = numero(resumen, "gedi_altura")
    resultados["gedi_area_datos"] = numero(resumen, "gedi_area_datos")
    resultados["gedi_cobertura_pct"] = (
        resultados["gedi_area_datos"] / area_ha * 100 if area_ha else 0
    )
    resultados["ndvi_inicial_medio"] = numero(resumen, "ndvi_inicial_medio")
    resultados["ndvi_final_medio"] = numero(resumen, "ndvi_final_medio")
    resultados["ndvi_delta_medio"] = numero(resumen, "ndvi_delta_medio")
    resultados["ndvi_cobertura_pct"] = (
        resultados["ndvi_area_datos"] / area_ha * 100 if area_ha else 0
    )
    resultados["coincidencia_varias_fuentes"] = (
        resultados["coincidencia_2_fuentes"]
        + resultados["coincidencia_3_fuentes"]
    )
    resultados["pct_coincidencia_varias_fuentes"] = (
        resultados["coincidencia_varias_fuentes"] / area_ha * 100
        if area_ha
        else 0
    )

    pct_tmf_defor = resultados["tmf_deforestacion"] / area_ha * 100 if area_ha else 0
    pct_tmf_degrad = resultados["tmf_degradacion"] / area_ha * 100 if area_ha else 0
    pct_tmf_recuperacion = (
        resultados["tmf_recuperacion"] / area_ha * 100 if area_ha else 0
    )
    pct_esri_salida = resultados["esri_salida"] / area_ha * 100 if area_ha else 0
    pct_esri_ganancia = (
        resultados["esri_ganancia"] / area_ha * 100 if area_ha else 0
    )
    pct_linea_base = resultados["linea_base"] / area_ha * 100 if area_ha else 0
    pct_ndvi_disminucion = (
        resultados["ndvi_disminucion"] / area_ha * 100 if area_ha else 0
    )

    senales, disponibilidad = evaluar_senales(
        tmf_deforestacion_ha=resultados["tmf_deforestacion"],
        tmf_deforestacion_pct=pct_tmf_defor,
        tmf_degradacion_ha=resultados["tmf_degradacion"],
        tmf_degradacion_pct=pct_tmf_degrad,
        hansen_post_2020_ha=resultados["hansen_post"],
        esri_salida_arboles_ha=resultados["esri_salida"],
        esri_salida_arboles_pct=pct_esri_salida,
        gedi_altura_media_m=resultados["gedi_altura"],
        gedi_cobertura_valida_pct=resultados["gedi_cobertura_pct"],
        linea_base_arborea_pct=pct_linea_base,
        ndvi_disminucion_ha=resultados["ndvi_disminucion"],
        ndvi_disminucion_pct=pct_ndvi_disminucion,
        ndvi_cobertura_valida_pct=resultados["ndvi_cobertura_pct"],
    )
    senal_tmf = senales["tmf"]
    senal_hansen = senales["hansen"]
    senal_esri = senales["esri"]
    senal_gedi = senales["gedi"]
    senal_ndvi = senales["ndvi"]

    aportes_indice, puntaje, prioridad = calcular_indice_prioridad(
        senal_tmf=senal_tmf,
        senal_hansen=senal_hansen,
        senal_esri=senal_esri,
        senal_gedi=senal_gedi,
        senal_ndvi=senal_ndvi,
    )
    consistencia = evaluar_consistencia(
        senal_tmf=senal_tmf,
        senal_hansen=senal_hansen,
        senal_esri=senal_esri,
        tmf_recuperacion_ha=resultados["tmf_recuperacion"],
        tmf_recuperacion_pct=pct_tmf_recuperacion,
        esri_ganancia_arboles_ha=resultados["esri_ganancia"],
        esri_ganancia_arboles_pct=pct_esri_ganancia,
    )

    resultados.update(
        {
            "pct_tmf_defor": pct_tmf_defor,
            "pct_tmf_degrad": pct_tmf_degrad,
            "pct_tmf_recuperacion": pct_tmf_recuperacion,
            "pct_esri_salida": pct_esri_salida,
            "pct_esri_ganancia": pct_esri_ganancia,
            "pct_linea_base": pct_linea_base,
            "pct_ndvi_disminucion": pct_ndvi_disminucion,
            "senal_tmf": senal_tmf,
            "senal_hansen": senal_hansen,
            "senal_esri": senal_esri,
            "senal_gedi": senal_gedi,
            "senal_ndvi": senal_ndvi,
            "gedi_disponible": disponibilidad["gedi"],
            "ndvi_disponible": disponibilidad["ndvi"],
            "aportes_indice": aportes_indice,
            "puntaje": puntaje,
            "prioridad": prioridad,
            "consistencia": consistencia,
        }
    )
    return resultados


def texto_recomendacion(prioridad):
    return {
        "Alta": "Visita de campo prioritaria en los sectores con señales coincidentes.",
        "Media": "Revisar imágenes recientes y evaluar si se justifica una visita.",
        "Preventiva": "Mantener monitoreo periódico y revisar condiciones de riesgo.",
        "Baja": "Sin acción inmediata. Continuar el monitoreo anual normal.",
    }[prioridad]


def visualizar_con_borde(imagen, visualizacion, area_fc, fondo=None):
    visual = ee.Image(imagen).visualize(**visualizacion)
    if fondo is not None:
        visual = ee.Image(fondo).visualize(**VIS_RGB).blend(visual)
    borde = (
        ee.Image()
        .byte()
        .paint(featureCollection=area_fc, color=1, width=4)
        .selfMask()
        .visualize(min=1, max=1, palette=["00E5FF"])
    )
    return visual.blend(borde)


def crear_url_miniatura(imagen, region, dimension):
    """Solicita a Earth Engine una URL temporal sin descargar todavía el PNG."""
    return ee.Image(imagen).getThumbURL(
        {
            "region": region,
            # Una dimensión conserva la proporción original del territorio.
            "dimensions": dimension,
            "format": "png",
        }
    )


def descargar_url_miniatura(url):
    """Descarga y valida una miniatura ya preparada por Earth Engine."""
    respuesta = requests.get(
        url,
        timeout=(10, 60),
        headers={"User-Agent": "visor-preevaluacion-territorial/1.0"},
    )
    respuesta.raise_for_status()
    if len(respuesta.content) < 1000 or not respuesta.content.startswith(b"\x89PNG"):
        raise RuntimeError("respuesta PNG no válida")
    return respuesta.content


def descargar_miniaturas(especificaciones, geometria, mapas_existentes=None):
    """Descarga los mapas en paralelo y reintenta únicamente los que fallan."""
    # Antes se consultaban estos límites una vez por cada mapa. Una sola consulta
    # reduce siete viajes innecesarios a Earth Engine.
    region = geometria.bounds(1).coordinates().getInfo()
    existentes_por_titulo = {
        mapa["titulo"]: mapa
        for mapa in (mapas_existentes or [])
        if mapa.get("imagen")
    }
    resultados = [
        existentes_por_titulo.get(titulo)
        for titulo, _, _ in especificaciones
    ]
    pendientes = {
        indice for indice, resultado in enumerate(resultados) if resultado is None
    }
    fallos = {indice: [] for indice in pendientes}

    # 1200 px conserva buena definición para el PDF. El segundo intento a 800 px
    # reduce el costo solo cuando Earth Engine no logra servir el mapa principal.
    for dimension in (1200, 800):
        if not pendientes:
            break

        urls = {}
        for indice in list(pendientes):
            titulo, imagen, _ = especificaciones[indice]
            try:
                urls[indice] = crear_url_miniatura(imagen, region, dimension)
            except Exception as error:
                fallos[indice].append(
                    f"{dimension}px al solicitar: {type(error).__name__}"
                )

        if not urls:
            continue

        # Tres solicitudes simultáneas acortan la espera sin saturar la cuota de
        # Earth Engine ni la memoria limitada de Streamlit Community Cloud.
        trabajadores = min(3, len(urls))
        with ThreadPoolExecutor(max_workers=trabajadores) as ejecutor:
            futuros = {
                ejecutor.submit(descargar_url_miniatura, url): indice
                for indice, url in urls.items()
            }
            for futuro in as_completed(futuros):
                indice = futuros[futuro]
                titulo, _, leyenda = especificaciones[indice]
                try:
                    resultados[indice] = {
                        "titulo": titulo,
                        "imagen": futuro.result(),
                        "leyenda": leyenda,
                    }
                    pendientes.discard(indice)
                except Exception as error:
                    # No se registran la URL ni sus tokens temporales.
                    fallos[indice].append(f"{dimension}px: {type(error).__name__}")

    errores = []
    for indice in sorted(pendientes):
        titulo, _, leyenda = especificaciones[indice]
        resultados[indice] = {"titulo": titulo, "imagen": None, "leyenda": leyenda}
        errores.append(
            f"{titulo}: Miniatura no disponible después de reintentos "
            f"({', '.join(fallos[indice]) or 'sin respuesta'})."
        )
    return resultados, errores


@st.cache_data(ttl=900, max_entries=4, show_spinner=False)
def generar_mapas_reporte(
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
    anio_tmf_diagnostico,
    anio_esri_inicial,
    anio_esri_final,
    anio_ndvi_inicial,
    intento_cache=0,
    _mapas_existentes=None,
):
    _ = intento_cache

    area_fc = obtener_area(
        tipo_area=tipo_area,
        finca_id=finca_id,
        subcuenca_nombre=subcuenca_nombre,
        geometria_geojson=geometria_geojson,
    )

    geometria = area_fc.geometry(TOLERANCIA_RECORTE_M)
    # El número de intento forma parte de la clave de caché y permite reintentar
    # si Earth Engine no entrega alguna miniatura temporalmente.
    tmf = obtener_tmf(anio_tmf_diagnostico, geometria)
    gedi = imagen_gedi(geometria)
    ndvi_final = obtener_ndvi(ANO_NDVI_MAX, geometria)
    ndvi_inicial = obtener_ndvi(anio_ndvi_inicial, geometria)
    delta_ndvi = ndvi_final.subtract(ndvi_inicial).rename("delta_ndvi")

    hansen = ee.Image(HANSEN_ASSET).select("lossyear")
    rgb = obtener_rgb_sentinel(ANO_NDVI_MAX, geometria)
    perdida_post, _, _ = imagenes_hansen(geometria)
    coincidencia_revision = imagen_coincidencia_revision(
        geometria,
        tmf=tmf,
        perdida_post=perdida_post,
        esri_inicial=obtener_esri(ANO_ESRI_MIN, geometria),
        esri_final=obtener_esri(ANO_ESRI_MAX, geometria),
    )

    especificaciones = [
        (
            f"ESRI - Uso y cobertura {anio_esri_final}",
            visualizar_con_borde(
                obtener_esri_visual(anio_esri_final, geometria),
                VIS_ESRI,
                area_fc,
            ),
            "Azul: agua | Verde: árboles | Amarillo: cultivos | Rojo: construido | Beige: pastizal",
        ),
        (
            f"JRC TMF - Estado forestal {anio_tmf_diagnostico}",
            visualizar_con_borde(tmf, VIS_TMF, area_fc),
            "Verde oscuro: bosque no perturbado | Amarillo: degradación | Rojo: deforestación | Verde claro: regeneración forestal",
        ),
        (
            f"Hansen - Pérdida arbórea 2001-{ANO_HANSEN_MAX}",
            visualizar_con_borde(
                hansen.updateMask(hansen.gt(0)).clip(geometria),
                VIS_HANSEN_TOTAL,
                area_fc,
                fondo=rgb,
            ),
            "Amarillo: pérdida antigua | Naranja: intermedia | Rojo oscuro: pérdida más reciente",
        ),
        (
            "GEDI - Altura del dosel",
            visualizar_con_borde(gedi, VIS_GEDI, area_fc),
            "Amarillo claro: dosel bajo | Verde medio: dosel intermedio | Verde oscuro: dosel alto",
        ),
        (
            f"ΔNDVI - Cambio de vigor {anio_ndvi_inicial}-{ANO_NDVI_MAX}",
            visualizar_con_borde(delta_ndvi, VIS_NDVI_DELTA, area_fc),
            "Rojo: disminución de vigor | Crema: cambio pequeño | Verde: aumento de vigor",
        ),
        (
            f"Vigor vegetal NDVI - {ANO_NDVI_MAX}",
            visualizar_con_borde(
                clasificar_ndvi(ndvi_final),
                VIS_NDVI_CLASES,
                area_fc,
            ),
            "Rojo: NDVI inferior a 0, sin vegetación activa | Rosado: NDVI 0.0 a menos de 0.2, suelo o cobertura muy escasa | Amarillo: NDVI 0.2 a menos de 0.4, vegetación escasa | Verde claro: NDVI 0.4 a menos de 0.6, vegetación moderada | Verde oscuro: NDVI mayor o igual a 0.6, vegetación densa",
        ),
        (
            "Sectores que requieren revisión - Coincidencia espacial",
            visualizar_con_borde(
                coincidencia_revision.updateMask(coincidencia_revision.gt(0)),
                VIS_COINCIDENCIA_REVISION,
                area_fc,
                fondo=rgb,
            ),
            (
                "Amarillo: señal de 1 fuente | Naranja: coincidencia de 2 fuentes | "
                "Rojo oscuro: coincidencia de 3 fuentes. Integra JRC TMF 2025, "
                "Hansen posterior a 2020 y ESRI 2017-2024 en una malla común de "
                "30 m. GEDI y NDVI no participan en esta suma espacial; el aporte "
                "NDVI se calcula por separado y este mapa no modifica el índice."
            ),
        ),
    ]

    return descargar_miniaturas(especificaciones, geometria, _mapas_existentes)


# -----------------------------------------------------------------------------
# PDF institucional
# -----------------------------------------------------------------------------

def generar_pdf(
    nombre_area,
    resultados,
    anio_tmf_diagnostico,
    anio_esri_inicial,
    anio_esri_final,
    anio_ndvi_inicial,
    mapas=None,
):
    memoria = BytesIO()
    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        rightMargin=1.45 * cm,
        leftMargin=1.45 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.55 * cm,
        title="Ficha ejecutiva de preevaluación territorial y conectividad",
        author="Aplicación de preevaluación territorial y corredores",
    )

    tinta = colors.HexColor("#123b45")
    verde = colors.HexColor("#00544d")
    verde_claro = colors.HexColor("#eaf4f0")
    superficie = colors.HexColor("#f7faf8")
    azul_claro = colors.HexColor("#e9f1fb")
    borde = colors.HexColor("#b6d1c8")
    naranja_claro = colors.HexColor("#fff1e6")
    gris = colors.HexColor("#52706f")
    estilos = getSampleStyleSheet()

    def registrar_estilo(nombre, base, **opciones):
        estilos.add(ParagraphStyle(name=nombre, parent=estilos[base], **opciones))

    registrar_estilo(
        "TituloFicha", "Title", fontName="Helvetica-Bold", fontSize=17,
        leading=20, textColor=tinta, alignment=TA_CENTER, spaceAfter=4,
    )
    registrar_estilo(
        "SubtituloFicha", "BodyText", fontName="Helvetica", fontSize=8.5,
        leading=11, textColor=gris, alignment=TA_CENTER, spaceAfter=9,
    )
    registrar_estilo(
        "TituloPagina", "Heading1", fontName="Helvetica-Bold", fontSize=15,
        leading=18, textColor=tinta, spaceAfter=3,
    )
    registrar_estilo(
        "BajadaPagina", "BodyText", fontName="Helvetica", fontSize=8.5,
        leading=11.2, textColor=gris, spaceAfter=8,
    )
    registrar_estilo(
        "SeccionFicha", "Heading2", fontName="Helvetica-Bold", fontSize=10.2,
        leading=12.5, textColor=verde, spaceBefore=7, spaceAfter=4,
    )
    registrar_estilo(
        "CuerpoFicha", "BodyText", fontName="Helvetica", fontSize=8.4,
        leading=11.2, textColor=tinta, spaceAfter=4,
    )
    registrar_estilo(
        "CuerpoPequeno", "BodyText", fontName="Helvetica", fontSize=7.2,
        leading=9.1, textColor=tinta, spaceAfter=3,
    )
    registrar_estilo(
        "Etiqueta", "BodyText", fontName="Helvetica", fontSize=7,
        leading=8.4, textColor=gris, spaceAfter=1,
    )
    registrar_estilo(
        "Valor", "BodyText", fontName="Helvetica-Bold", fontSize=11,
        leading=13, textColor=tinta,
    )
    registrar_estilo(
        "MapaTitulo", "BodyText", fontName="Helvetica-Bold", fontSize=9.2,
        leading=11, textColor=tinta, alignment=TA_CENTER, spaceAfter=3,
    )
    registrar_estilo(
        "MapaNota", "BodyText", fontName="Helvetica", fontSize=6.7,
        leading=8.2, textColor=gris, alignment=TA_CENTER,
    )
    registrar_estilo(
        "CabeceraTabla", "BodyText", fontName="Helvetica-Bold", fontSize=7.4,
        leading=9, textColor=tinta,
    )
    registrar_estilo(
        "Prioridad", "BodyText", fontName="Helvetica", fontSize=9,
        leading=12, textColor=tinta,
    )

    def parrafo(texto, estilo="CuerpoFicha"):
        return Paragraph(str(texto), estilos[estilo])

    def tabla_simple(filas, anchos, *, cabecera=False, fondo=None):
        contenido = [
            [parrafo(celda, "CabeceraTabla" if cabecera and i == 0 else "CuerpoPequeno") for celda in fila]
            for i, fila in enumerate(filas)
        ]
        tabla = Table(contenido, colWidths=anchos, repeatRows=1 if cabecera else 0)
        comandos = [
            ("GRID", (0, 0), (-1, -1), 0.35, borde),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if fondo:
            comandos.append(("BACKGROUND", (0, 0), (-1, -1), fondo))
        if cabecera:
            comandos.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), verde_claro),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.8, verde),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, superficie]),
                ]
            )
        tabla.setStyle(TableStyle(comandos))
        return tabla

    def tarjeta(texto, *, fondo=verde_claro, acento=verde, estilo="CuerpoFicha"):
        tabla = Table([[parrafo(texto, estilo)]], colWidths=[17.0 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), fondo),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, acento),
                    ("BOX", (0, 0), (-1, -1), 0.35, borde),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return tabla

    def tarjetas_metricas(items):
        celdas = []
        for etiqueta, valor in items:
            celdas.append([parrafo(etiqueta, "Etiqueta"), parrafo(valor, "Valor")])
        tabla = Table([celdas], colWidths=[4.25 * cm] * len(celdas))
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), superficie),
                    ("BOX", (0, 0), (-1, -1), 0.4, borde),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, borde),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return tabla

    def leyenda(items):
        filas = []
        for color, etiqueta, detalle in items:
            filas.append(["", parrafo(f"<b>{etiqueta}</b><br/>{detalle}", "CuerpoPequeno")])
        tabla = Table(filas, colWidths=[0.45 * cm, 7.95 * cm], hAlign="LEFT")
        comandos = [
            ("GRID", (0, 0), (-1, -1), 0.25, borde),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        for i, (color, _, _) in enumerate(items):
            comandos.append(("BACKGROUND", (0, i), (0, i), colors.HexColor(color)))
        tabla.setStyle(TableStyle(comandos))
        return tabla

    r = resultados
    aportes = r["aportes_indice"]
    area = r["area_ha"]
    pct_arbol = r["esri_arboles_final"] / area * 100 if area else 0
    pct_ganancia = r["esri_ganancia"] / area * 100 if area else 0
    visita = r.get("prioridad_visita")
    prioridad_pdf = visita["prioridad_visita"] if visita else r["prioridad"]
    puntaje_cambios = visita["puntaje_cambios"] if visita else r["puntaje"]
    aporte_corredor = visita["aporte_corredor"] if visita else 0.0
    puntaje_integrado = visita["puntaje_integrado"] if visita else r["puntaje"]
    maximo_integrado = PUNTAJE_MAXIMO_VISITA if visita else PUNTAJE_MAXIMO
    accion_pdf = (
        texto_recomendacion_visita(prioridad_pdf)
        if visita
        else texto_recomendacion(prioridad_pdf)
    )
    fuentes = sum(
        bool(valor)
        for valor in (
            r["senal_tmf"],
            r["senal_esri"],
            r["senal_hansen"],
            r["senal_gedi"],
            r["senal_ndvi"],
        )
    )
    resultado_general = (
        "varias señales de cambio que justifican una revisión prioritaria"
        if fuentes >= 2
        else "una señal localizada que conviene revisar"
        if fuentes == 1
        else "sin señales relevantes de deterioro reciente en las fuentes evaluadas"
    )
    coincidencia = f"{r['consistencia']['nivel']}: {r['consistencia']['detalle']}"
    contexto_corredores = r.get("corredores") or {}
    contexto_fragmentacion = r.get("fragmentacion") or {}
    conexion_corredor = contexto_fragmentacion.get("conexion_corredor") or {}

    historia = [
        Paragraph("FICHA EJECUTIVA DE PREEVALUACIÓN TERRITORIAL", estilos["TituloFicha"]),
        Paragraph(
            "Lectura rápida para orientar una visita. Los mapas y cálculos son indicativos y no sustituyen la verificación de campo.",
            estilos["SubtituloFicha"],
        ),
    ]

    identificacion = tabla_simple(
        [
            ["Área evaluada", nombre_area, "Superficie", f"{area:,.2f} ha"],
            ["Fecha", date.today().strftime("%d/%m/%Y"), "Método", METHODOLOGY_VERSION],
        ],
        [2.2 * cm, 6.2 * cm, 2.0 * cm, 6.6 * cm],
        fondo=superficie,
    )
    historia.extend([identificacion, Spacer(1, 7)])

    color_prioridad = {
        "Muy alta": "#9b1c1c",
        "Alta": "#b42318",
        "Media": "#c85d0a",
        "Preventiva": "#9a6a00",
        "Baja": "#2f6b4f",
    }[prioridad_pdf]
    historia.extend(
        [
            tarjeta(
                f"<b>Prioridad {prioridad_pdf.lower()} de visita</b> &nbsp;·&nbsp; "
                f"<b>{puntaje_integrado:.2f} de {maximo_integrado:.1f} puntos</b><br/>"
                f"{accion_pdf}",
                fondo=colors.HexColor("#fff7ed") if prioridad_pdf != "Baja" else verde_claro,
                acento=colors.HexColor(color_prioridad),
                estilo="Prioridad",
            ),
            Spacer(1, 7),
            Paragraph("Qué significa el puntaje", estilos["SeccionFicha"]),
            Paragraph(
                "El valor total es una suma de criterios. Mide prioridad operativa para revisar el área; "
                "no es una probabilidad de deforestación ni indica cuántas capas se superponen.",
                estilos["CuerpoFicha"],
            ),
        ]
    )

    filas_puntaje = [
        ["Fuente o criterio", "Qué observó", "Aporte"],
        [f"JRC TMF {anio_tmf_diagnostico}", "Señal" if r["senal_tmf"] else "Sin señal", f"{aportes['tmf']:.1f} / {PESOS_INDICE['tmf']:.1f}"],
        ["Hansen GFC", "Señal" if r["senal_hansen"] else "Sin señal", f"{aportes['hansen']:.1f} / {PESOS_INDICE['hansen']:.1f}"],
        [f"ESRI {anio_esri_inicial}-{anio_esri_final}", "Señal" if r["senal_esri"] else "Sin señal", f"{aportes['esri']:.1f} / {PESOS_INDICE['esri']:.1f}"],
        ["GEDI · altura del dosel", "Contexto" if r["senal_gedi"] else "Sin aporte", f"{aportes['gedi']:.1f} / {PESOS_INDICE['gedi']:.1f}"],
        [
            f"NDVI {anio_ndvi_inicial}-{ANO_NDVI_FINAL_ANALISIS}",
            "Disminución significativa" if r["senal_ndvi"] else "Sin señal",
            f"{aportes['ndvi']:.1f} / {PESOS_INDICE['ndvi']:.1f}",
        ],
    ]
    if visita:
        filas_puntaje.append(["Valor estratégico de corredores", "Aporta al total de visita", f"{aporte_corredor:.2f} / 1.5"])
    filas_puntaje.extend(
        [
            ["Subtotal de cambios", "Suma de JRC + Hansen + ESRI + GEDI + NDVI", f"{puntaje_cambios:.2f} / {PUNTAJE_MAXIMO:.1f}"],
            ["TOTAL INTEGRADO", "Cambios + valor del corredor" if visita else "Índice de cambios", f"{puntaje_integrado:.2f} / {maximo_integrado:.1f}"],
        ]
    )
    tabla_puntaje = tabla_simple(
        filas_puntaje,
        [5.2 * cm, 7.7 * cm, 4.1 * cm],
        cabecera=True,
    )
    tabla_puntaje.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), azul_claro),
                ("LINEABOVE", (0, -1), (-1, -1), 1, tinta),
            ]
        )
    )
    historia.extend([tabla_puntaje, Spacer(1, 7)])
    eri_pdf = r.get("eri") or {}
    if eri_pdf:
        historia.extend(
            [
                tarjeta(
                    "<b>ERI indicativo · lectura complementaria</b><br/>"
                    f"{float(eri_pdf.get('valor', 0) or 0):.2f} / 1.00 · "
                    f"clase {eri_pdf.get('clase', 'sin clasificar')}. "
                    "Se reporta por separado y no modifica la prioridad anterior.",
                    fondo=azul_claro,
                    acento=colors.HexColor(str(eri_pdf.get("color", "#0A4393"))),
                ),
                Spacer(1, 7),
            ]
        )

    historia.extend(
        [
            tarjetas_metricas(
                [
                    ("Árboles en ESRI", f"{r['esri_arboles_final']:.1f} ha"),
                    ("Pérdida Hansen posterior a 2020", f"{r['hansen_post']:.2f} ha"),
                    ("Deforestación señalada por JRC", f"{r['tmf_deforestacion']:.1f} ha"),
                    ("Señal en 2 o 3 fuentes", f"{r['coincidencia_varias_fuentes']:.2f} ha"),
                ]
            ),
            Spacer(1, 7),
            tarjeta(
                f"<b>Lectura rápida.</b> El análisis encontró {resultado_general}. "
                f"La coincidencia espacial más sólida ocupa {r['coincidencia_varias_fuentes']:.2f} ha "
                f"({r['pct_coincidencia_varias_fuentes']:.2f}% del área). "
                "Revise primero esos sectores y contraste el resultado con imágenes recientes, "
                "documentos del predio y observación de campo.",
                fondo=azul_claro,
                acento=tinta,
            ),
            Spacer(1, 5),
            Paragraph("Puntaje y coincidencia espacial son cosas distintas", estilos["SeccionFicha"]),
            tabla_simple(
                [
                    ["Señal de una fuente", f"{r['coincidencia_1_fuente']:.2f} ha", "Revisión inicial"],
                    ["Coincidencia de dos fuentes", f"{r['coincidencia_2_fuentes']:.2f} ha", "Mayor respaldo espacial"],
                    ["Coincidencia de tres fuentes", f"{r['coincidencia_3_fuentes']:.2f} ha", "Revisión prioritaria"],
                ],
                [6.0 * cm, 3.0 * cm, 8.0 * cm],
                fondo=superficie,
            ),
            Paragraph(
                "Estas hectáreas indican dónde coinciden las señales. No se suman al puntaje y no confirman por sí solas la causa del cambio.",
                estilos["CuerpoPequeno"],
            ),
        ]
    )

    if contexto_fragmentacion:
        clase = contexto_fragmentacion["metricas_clase"]
        red = contexto_fragmentacion["metricas_red"]

        historia.extend(
            [
                PageBreak(),
                Paragraph("1. Cómo está distribuido el bosque", estilos["TituloPagina"]),
                Paragraph(
                    f"Este mapa muestra únicamente los fragmentos de {FUENTE_BOSQUE_CORTA} dentro del área evaluada. "
                    "No utiliza fondo satelital para que la forma, el tamaño y la distribución se lean con claridad.",
                    estilos["BajadaPagina"],
                ),
                tarjetas_metricas(
                    [
                        ("Bosque dentro del área", f"{clase['area_total_bosque_ha']:.2f} ha"),
                        ("Fragmentos identificados", f"{clase['numero_parches']}"),
                        ("Mayor fragmento", f"{clase['indice_parche_mayor_pct']:.1f}% del área"),
                        ("Tamaño mediano", f"{clase['area_mediana_parche_ha']:.2f} ha"),
                    ]
                ),
                Spacer(1, 8),
                crear_mapa_fragmentacion(contexto_fragmentacion, ancho=17.0 * cm, alto=10.2 * cm),
                Spacer(1, 6),
                Table(
                    [[
                        leyenda(
                            [
                                ("#2f6b4f", "Valor alto", "Fragmentos relativamente importantes para mantener unido el bosque."),
                                ("#78a66a", "Valor intermedio", "Aportan a la continuidad, con menor influencia relativa."),
                            ]
                        ),
                        leyenda(
                            [
                                ("#c7dbc4", "Valor bajo", "Menor influencia relativa dentro de esta área; no significa que carezca de valor ecológico."),
                                ("#eef5f1", "Área evaluada", "La superficie reportada siempre queda dentro de este límite."),
                            ]
                        ),
                    ]],
                    colWidths=[8.5 * cm, 8.5 * cm],
                    style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]),
                ),
                Spacer(1, 6),
                tarjeta(
                    f"<b>Lectura sencilla.</b> Se identificaron {clase['numero_parches']} fragmentos que reúnen "
                    f"{clase['area_total_bosque_ha']:.2f} ha, equivalentes al "
                    f"{clase['porcentaje_paisaje_bosque']:.1f}% del área. "
                    "Los colores comparan los fragmentos entre sí dentro de este análisis; no son categorías oficiales de Almanaque Azul.",
                    fondo=verde_claro,
                ),
                Paragraph("Datos adicionales", estilos["SeccionFicha"]),
                tabla_simple(
                    [
                        ["Área media por fragmento", f"{clase['area_media_parche_ha']:.2f} ha", "Densidad de fragmentos", f"{clase['densidad_parches_por_100ha']:.2f} por 100 ha"],
                        ["Densidad de bordes", f"{clase['densidad_borde_m_ha']:.2f} m/ha", "Índice de forma medio", f"{clase['indice_forma_medio']:.2f}"],
                    ],
                    [4.1 * cm, 4.4 * cm, 4.1 * cm, 4.4 * cm],
                    fondo=superficie,
                ),
            ]
        )

        conecta = bool(conexion_corredor.get("conecta"))
        lectura_ruta = (
            f"La cadena potencial llega a <b>{conexion_corredor.get('corredor_nombre')}</b> "
            f"(categoría publicada {str(conexion_corredor.get('categoria_etiqueta') or 'no indicada').lower()}) "
            f"por medio de {conexion_corredor.get('numero_fragmentos_ruta', 0)} fragmentos. "
            f"El salto mayor es de {float(conexion_corredor.get('mayor_separacion_m') or 0):.1f} m."
            if conecta
            else "No se identificó una cadena completa hacia un corredor publicado dentro del entorno evaluado."
        )
        historia.extend(
            [
                PageBreak(),
                Paragraph("2. Cómo puede mantenerse la continuidad del bosque", estilos["TituloPagina"]),
                Paragraph(
                    "Este segundo mapa conserva los fragmentos como contexto y añade solo las relaciones esenciales, "
                    "las separaciones que conviene revisar y una ruta potencial hacia un corredor de referencia.",
                    estilos["BajadaPagina"],
                ),
                tarjetas_metricas(
                    [
                        ("Distancia evaluada", f"{red['umbral_m']:.0f} m"),
                        ("Fragmentos con vecino cercano", f"{red.get('numero_parches_conectados', 0)} de {red['numero_nodos']}"),
                        ("Fragmentos separados", f"{red.get('numero_parches_aislados', 0)}"),
                        ("Grupos de bosque", f"{red['numero_componentes']}"),
                    ]
                ),
                Spacer(1, 8),
                crear_mapa_conectividad(contexto_fragmentacion, ancho=17.0 * cm, alto=10.2 * cm),
                Spacer(1, 6),
                Table(
                    [[
                        leyenda(
                            [
                                ("#b8d1bd", "Fragmentos de bosque", "Cobertura 2021 usada para el análisis estructural."),
                                ("#176b61", "Estructura esencial", "Línea continua entre bordes próximos; el cálculo usa todas las relaciones válidas."),
                                ("#9a4a25", "Separación para revisar", "Línea discontinua desde un fragmento sin vecino dentro del umbral."),
                            ]
                        ),
                        leyenda(
                            [
                                ("#e97719", "Ruta potencial al corredor", "Una sola cadena de saltos; no demuestra movimiento de fauna."),
                                ("#dce8a5", "Corredor de referencia", "Polígono publicado por Almanaque Azul."),
                                ("#eef5f1", "Área evaluada", "El bosque exterior puede apoyar el cálculo sin aumentar las hectáreas reportadas."),
                            ]
                        ),
                    ]],
                    colWidths=[8.5 * cm, 8.5 * cm],
                    style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]),
                ),
                Spacer(1, 6),
                tarjeta(
                    f"<b>Lectura sencilla.</b> Con una distancia máxima de {red['umbral_m']:.0f} m, "
                    f"{red.get('numero_parches_conectados', 0)} fragmentos tienen al menos un vecino cercano y "
                    f"{red.get('numero_parches_aislados', 0)} quedan separados. {lectura_ruta}",
                    fondo=naranja_claro if conecta else azul_claro,
                    acento=colors.HexColor("#e97719") if conecta else tinta,
                ),
                Paragraph("Qué se calculó y qué se muestra", estilos["SeccionFicha"]),
                tabla_simple(
                    [
                        ["Relaciones usadas en el cálculo", f"{red['numero_aristas']}", "Relaciones esenciales dibujadas", f"{red.get('numero_relaciones_mostradas', 0)}"],
                        ["Fragmentos del entorno considerados", f"{red.get('numero_parches_contexto', red['numero_nodos'])}", "Con continuidad o conexión exterior", f"{red.get('numero_parches_continuidad_exterior', 0)}"],
                        ["Separaciones potenciales", f"{red.get('numero_brechas_potenciales', 0)}", "Distancia media de separaciones", f"{red.get('distancia_media_brechas_potenciales_m', 0):.1f} m"],
                    ],
                    [4.5 * cm, 2.2 * cm, 7.1 * cm, 3.2 * cm],
                    fondo=superficie,
                ),
                Paragraph(
                    "Importante: esta es conectividad estructural potencial basada en cobertura y distancia. "
                    "No demuestra conectividad funcional para una especie, calidad de hábitat ni uso real del corredor.",
                    estilos["CuerpoPequeno"],
                ),
            ]
        )

    historia.extend(
        [
            PageBreak(),
            Paragraph("Evidencia temática por fuente", estilos["TituloPagina"]),
            Paragraph(
                "Estas imágenes permiten revisar el detalle de cada fuente. Se presentan después de la conclusión y de los mapas explicativos para no sobrecargar la lectura inicial.",
                estilos["BajadaPagina"],
            ),
        ]
    )

    def tarjeta_mapa(mapa):
        titulo_mapa = mapa["titulo"].replace("ΔNDVI", "Variación NDVI")
        contenido = [parrafo(titulo_mapa, "MapaTitulo")]
        if mapa.get("imagen"):
            imagen = ReportLabImage(BytesIO(mapa["imagen"]))
            escala = min((15.8 * cm) / imagen.imageWidth, (6.5 * cm) / imagen.imageHeight)
            imagen.drawWidth = imagen.imageWidth * escala
            imagen.drawHeight = imagen.imageHeight * escala
            contenido.append(
                Table(
                    [[imagen]],
                    colWidths=[15.8 * cm],
                    style=TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]),
                )
            )
        else:
            contenido.append(
                Table(
                    [[parrafo("Imagen no disponible. Consulte el mapa interactivo.", "MapaNota")]],
                    colWidths=[15.8 * cm],
                    rowHeights=[5.5 * cm],
                    style=TableStyle([("BOX", (0, 0), (-1, -1), 0.35, borde), ("BACKGROUND", (0, 0), (-1, -1), superficie), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]),
                )
            )
        contenido.append(parrafo(mapa["leyenda"], "MapaNota"))
        tabla = Table([[contenido]], colWidths=[16.4 * cm], hAlign="CENTER")
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.4, borde),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        return KeepTogether([tabla, Spacer(1, 6)])

    for indice, mapa in enumerate(mapas or []):
        historia.append(tarjeta_mapa(mapa))
        if indice % 2 == 1 and indice < len(mapas or []) - 1:
            historia.append(PageBreak())

    historia.extend(
        [
            Paragraph("Detalle técnico y trazabilidad", estilos["TituloPagina"]),
            Paragraph(
                "Esta sección conserva la información completa para personal técnico. No es necesaria para comprender la conclusión ejecutiva.",
                estilos["BajadaPagina"],
            ),
        ]
    )
    filas_fuentes = [
        ["Fuente", "Resultado específico", "Aporte"],
        [f"JRC TMF {anio_tmf_diagnostico}", f"Bosque no perturbado {r['tmf_estable']:.1f}; degradación {r['tmf_degradacion']:.1f}; deforestación {r['tmf_deforestacion']:.1f}; regeneración forestal {r['tmf_recuperacion']:.1f}; agua {r['tmf_agua']:.1f}; otra cobertura {r['tmf_otra_cobertura']:.1f} ha", f"{aportes['tmf']:.1f}/{PESOS_INDICE['tmf']:.1f}"],
        ["Hansen GFC", f"Pérdida 2001-2020: {r['hansen_pre']:.2f} ha; posterior al {CUTOFF_LABEL}: {r['hansen_post']:.2f} ha", f"{aportes['hansen']:.1f}/{PESOS_INDICE['hansen']:.1f}"],
        [f"ESRI {anio_esri_inicial}-{anio_esri_final}", f"Árboles finales {r['esri_arboles_final']:.1f} ha; salida {r['esri_salida']:.1f} ha ({r['pct_esri_salida']:.1f}%); ganancia {r['esri_ganancia']:.1f} ha ({pct_ganancia:.1f}%)", f"{aportes['esri']:.1f}/{PESOS_INDICE['esri']:.1f}"],
        ["GEDI", f"Dosel {r['gedi_altura']:.1f} m; datos válidos en {r['gedi_cobertura_pct']:.0f}% del área" if r["gedi_disponible"] else "Datos insuficientes", f"{aportes['gedi']:.1f}/{PESOS_INDICE['gedi']:.1f}"],
        [
            f"NDVI {anio_ndvi_inicial}-{ANO_NDVI_FINAL_ANALISIS}",
            f"Media {r['ndvi_inicial_medio']:.3f} → {r['ndvi_final_medio']:.3f}; "
            f"Δ medio {r['ndvi_delta_medio']:+.3f}; disminución significativa "
            f"{r['ndvi_disminucion']:.2f} ha ({r['pct_ndvi_disminucion']:.1f}%); "
            f"datos válidos {r['ndvi_cobertura_pct']:.0f}%",
            f"{aportes['ndvi']:.1f}/{PESOS_INDICE['ndvi']:.1f}",
        ],
    ]
    historia.extend(
        [
            tabla_simple(filas_fuentes, [3.0 * cm, 10.8 * cm, 3.2 * cm], cabecera=True),
            Paragraph("Contexto de corredores", estilos["SeccionFicha"]),
        ]
    )
    if contexto_corredores:
        nombres = ", ".join(
            dict.fromkeys(detalle["nombre"] for detalle in contexto_corredores.get("corredores", []))
        ) or "ninguno"
        historia.append(
            Paragraph(
                f"El área intersecta {contexto_corredores['area_en_corredores_ha']:.2f} ha de corredores "
                f"({contexto_corredores['porcentaje_aoi_en_corredores']:.2f}% del área). "
                f"Corredores presentes: {nombres}. Intersección con el Corredor Biológico Mesoamericano: "
                f"{'sí' if contexto_corredores['intersecta_mesoamericano'] else 'no'}. "
                "Este valor aporta al puntaje integrado de visita; la estructura del bosque sirve para focalizar la revisión, pero no añade puntos.",
                estilos["CuerpoFicha"],
            )
        )
    else:
        historia.append(Paragraph("No se obtuvo contexto de corredores para esta área.", estilos["CuerpoFicha"]))

    texto_justificacion_pesos = " ".join(
        JUSTIFICACION_PESOS[fuente] for fuente in ("tmf", "hansen", "esri", "gedi", "ndvi")
    )
    texto_justificacion_umbrales = " ".join(
        JUSTIFICACION_UMBRALES[criterio]
        for criterio in (
            "hansen_post_2020_ha", "jrc_deforestacion", "jrc_degradacion",
            "esri_salida_arboles", "gedi_dosel_y_cobertura", "ndvi",
        )
    )
    texto_clases_ndvi = "; ".join(
        f"{clase['etiqueta']} ({clase['rango']})" for clase in CLASES_VIGOR_NDVI
    )
    historia.extend(
        [
            Paragraph("Cómo se interpreta", estilos["SeccionFicha"]),
            Paragraph(
                f"<b>Consistencia entre fuentes.</b> {coincidencia} La superposición espacial se calcula en una malla común de 30 m con JRC, Hansen y ESRI. GEDI y NDVI no se suman a ese mapa; NDVI aporta de forma separada al índice cuando supera sus umbrales.",
                estilos["CuerpoFicha"],
            ),
            Paragraph(
                f"<b>Justificación de los pesos.</b> {texto_justificacion_pesos}",
                estilos["CuerpoPequeno"],
            ),
            Paragraph(
                f"<b>Justificación de los umbrales.</b> {texto_justificacion_umbrales}",
                estilos["CuerpoPequeno"],
            ),
            Paragraph(
                f"<b>Escala visual NDVI.</b> {texto_clases_ndvi}. Describe vigor espectral, no identifica por sí sola bosque natural.",
                estilos["CuerpoPequeno"],
            ),
            tarjeta(
                "<b>Alcance.</b> Esta ficha orienta dónde revisar. No es una certificación, una determinación legal, una confirmación definitiva de deforestación ni una evaluación de conectividad funcional para fauna.",
                fondo=azul_claro,
                acento=tinta,
            ),
        ]
    )

    def pie_pagina(canvas_pdf, documento_pdf):
        canvas_pdf.saveState()
        ancho, _ = A4
        canvas_pdf.setStrokeColor(colors.HexColor("#9aab96"))
        canvas_pdf.setLineWidth(0.4)
        canvas_pdf.line(1.55 * cm, 1.2 * cm, ancho - 1.55 * cm, 1.2 * cm)
        canvas_pdf.setFont("Helvetica", 7.2)
        canvas_pdf.setFillColor(gris)
        canvas_pdf.drawString(1.45 * cm, 0.82 * cm, "Preevaluación territorial indicativa · requiere verificación")
        canvas_pdf.drawRightString(ancho - 1.45 * cm, 0.82 * cm, f"Página {documento_pdf.page}")
        canvas_pdf.restoreState()

    documento.build(historia, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
    memoria.seek(0)
    return memoria.getvalue()


# -----------------------------------------------------------------------------
# Presentación de leyendas y resultados
# -----------------------------------------------------------------------------

CLAVES_ESTADO_RESULTADOS = (
    "resultados_analisis",
    "firma_analisis",
    "pdf_analisis",
    "firma_informe",
    "errores_mapas",
    "intento_informe",
    "mapas_reporte",
    "grafica_fuente",
    "firma_grafica_fuente",
    "error_grafica_fuente",
)


def limpiar_estado_resultados():
    for clave in CLAVES_ESTADO_RESULTADOS:
        st.session_state.pop(clave, None)


def mostrar_barra_visor(contenido_modo):
    """Cabecera compacta para que el mapa, no una guía, domine la pantalla."""

    st.markdown(
        f"""
        <header class="visor-barra" aria-label="Identificación del visor">
          <div class="visor-marca">
            <small>Cuenca Hidrográfica del Canal de Panamá</small>
            <strong>Evidencia cartográfica y resultados</strong>
          </div>
          <div class="visor-contexto">
            <span class="visor-etiqueta">{html_lib.escape(contenido_modo['titulo'])}</span>
            <span class="visor-etiqueta">ERI complementario</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def mostrar_panel_dashboard(resultados, modo_analisis):
    """Resume la decisión junto al mapa y deja el desglose completo en pestañas."""

    st.markdown('<div class="panel-titulo">Lectura rápida</div>', unsafe_allow_html=True)
    if modo_analisis == MODO_CORREDORES:
        corredores = resultados.get("corredores") or {}
        fragmentacion = resultados.get("fragmentacion") or {}
        clase = fragmentacion.get("metricas_clase") or {}
        red = fragmentacion.get("metricas_red") or {}
        conexion = fragmentacion.get("conexion_corredor") or {}
        if conexion.get("conecta"):
            titulo = "Conexión estructural potencial identificada"
            detalle = "Revise en el mapa la cadena de fragmentos y el corredor de referencia."
        elif corredores.get("intersecta"):
            titulo = "El área coincide con corredores publicados"
            detalle = "La coincidencia aporta contexto estratégico, no prueba conectividad funcional."
        else:
            titulo = "Sin contacto directo con los corredores publicados"
            detalle = "Revise los fragmentos separados y el bosque del entorno."
        color = "#00544d"
        st.markdown(
            f"""
            <div class="resultado-prioridad" style="--prioridad-color:{color};">
              <small>Resultado de conectividad</small>
              <strong>{html_lib.escape(titulo)}</strong>
              <p>{html_lib.escape(detalle)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        izquierda, derecha = st.columns(2)
        izquierda.metric(
            "Dentro de corredores",
            f"{float(corredores.get('area_en_corredores_ha', 0) or 0):,.1f} ha",
            f"{float(corredores.get('porcentaje_aoi_en_corredores', 0) or 0):.1f}% del área",
            delta_color="off",
        )
        derecha.metric(
            "Bosque 2021",
            f"{float(clase.get('area_total_bosque_ha', 0) or 0):,.1f} ha"
            if fragmentacion
            else "No disponible",
        )
        izquierda, derecha = st.columns(2)
        izquierda.metric("Fragmentos", f"{int(clase.get('numero_parches', 0) or 0):,}")
        derecha.metric(
            "Separados",
            f"{int(red.get('numero_parches_aislados', 0) or 0):,}",
        )
        return

    visita = resultados.get("prioridad_visita")
    prioridad = visita["prioridad_visita"] if visita else resultados["prioridad"]
    color = {
        "Muy alta": "#7f0000",
        "Alta": "#b71c1c",
        "Media": "#a33a00",
        "Preventiva": "#8a5b00",
        "Baja": "#2e7d32",
    }[prioridad]
    recomendacion = (
        texto_recomendacion_visita(prioridad)
        if visita
        else texto_recomendacion(prioridad)
    )
    st.markdown(
        f"""
        <div class="resultado-prioridad" style="--prioridad-color:{color};">
          <small>Orientación para la revisión</small>
          <strong>Prioridad {html_lib.escape(prioridad.lower())}</strong>
          <p>{html_lib.escape(recomendacion)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if modo_analisis == MODO_INTEGRAL and visita:
        corredores = resultados.get("corredores") or {}
        fragmentacion = resultados.get("fragmentacion") or {}
        clase = fragmentacion.get("metricas_clase") or {}
        izquierda, derecha = st.columns(2)
        izquierda.metric("Urgencia por cambios", resultados["prioridad"])
        derecha.metric("Valor del corredor", visita["valor_corredor"])
        izquierda, derecha = st.columns(2)
        izquierda.metric(
            "Dentro de corredores",
            f"{float(corredores.get('area_en_corredores_ha', 0) or 0):,.1f} ha",
        )
        derecha.metric(
            "Bosque 2021",
            f"{float(clase.get('area_total_bosque_ha', 0) or 0):,.1f} ha"
            if fragmentacion
            else "No disponible",
        )
        st.markdown(
            f'<div class="dashboard-estado"><b>Dónde empezar:</b> '
            f'{html_lib.escape(visita["foco_visita"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        senales = sum(
            bool(resultados.get(clave))
            for clave in ("senal_tmf", "senal_hansen", "senal_esri", "senal_ndvi")
        )
        izquierda, derecha = st.columns(2)
        izquierda.metric(
            "Índice de indicios",
            f"{float(resultados.get('puntaje', 0) or 0):.1f}/{PUNTAJE_MAXIMO:.1f}",
        )
        derecha.metric("Fuentes con señal", f"{senales} de 4")
        izquierda, derecha = st.columns(2)
        izquierda.metric(
            "Deforestación JRC",
            f"{float(resultados.get('tmf_deforestacion', 0) or 0):,.1f} ha",
        )
        derecha.metric(
            "Pérdida post-2020",
            f"{float(resultados.get('hansen_post', 0) or 0):,.2f} ha",
        )


def construir_grafica_componentes_eri(resultados):
    eri = resultados.get("eri") or {}
    componentes = eri.get("componentes") or {}
    claves = list(PESOS_ERI)
    return {
        "titulo": "Componentes del ERI indicativo",
        "descripcion": (
            "Cada barra se expresa entre 0 y 1. Un valor menor identifica el componente "
            "que más limita la lectura ecológica del área."
        ),
        "datos": {
            "Componente": [ETIQUETAS_COMPONENTES_ERI[clave] for clave in claves],
            "Valor": [float(componentes.get(clave, 0) or 0) for clave in claves],
        },
        "eje_x": "Componente",
        "eje_y": "Valor",
        "unidad": "",
        "decimales": 2,
        "colores": [COLORES_COMPONENTES_ERI[clave] for clave in claves],
    }


def construir_grafica_distribucion_eri(resultados):
    distribucion = (resultados.get("eri") or {}).get("distribucion_clases") or []
    return {
        "titulo": "Superficie por clase de ERI",
        "descripcion": (
            "Distribución de la superficie analizada según las cinco clases del ERI."
        ),
        "datos": {
            "Clase": [item["clase"] for item in distribucion],
            "Hectáreas": [float(item.get("area_ha", 0) or 0) for item in distribucion],
        },
        "eje_x": "Clase",
        "eje_y": "Hectáreas",
        "unidad": "ha",
        "colores": [item["color"] for item in distribucion],
    }


def mostrar_resumen_eri(resultados):
    """Presenta el ERI junto al mapa sin convertirlo en un segundo índice de prioridad."""

    eri = resultados.get("eri") or {}
    if not eri:
        if resultados.get("eri_error"):
            st.info(
                "El análisis principal está disponible, pero el ERI indicativo no pudo "
                "calcularse en esta ejecución."
            )
            with st.expander("Detalle técnico del ERI", expanded=False):
                st.code(resultados["eri_error"])
        return
    valor = float(eri.get("valor", 0) or 0)
    clase = str(eri.get("clase", "Sin clasificar"))
    color = str(eri.get("color", "#0A4393"))
    limitante = str(eri.get("componente_limitante_etiqueta", "No disponible"))
    st.markdown(
        f"""
        <div class="eri-resumen" style="--eri-color:{html_lib.escape(color)};">
          <div>
            <small>Resiliencia ecológica · lectura complementaria</small>
            <strong>ERI {valor:.2f} · {html_lib.escape(clase)}</strong>
            <p>Componente que requiere mayor atención: <b>{html_lib.escape(limitante)}</b>.</p>
          </div>
          <span>{valor:.2f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    grafica = construir_grafica_componentes_eri(resultados)
    st.altair_chart(
        crear_grafica_barras_color(grafica, altura=158),
        use_container_width=True,
        theme=None,
        key="eri_componentes_panel",
    )
    st.caption(
        "El ERI no modifica el índice de indicios ni la prioridad de visita. "
        "Se interpreta como contexto ecológico indicativo."
    )


def mostrar_detalle_eri(resultados):
    """Desglosa método, componentes y clases del ERI para usuarios técnicos."""

    eri = resultados.get("eri") or {}
    if not eri:
        st.warning("El ERI indicativo no estuvo disponible en esta ejecución.")
        if resultados.get("eri_error"):
            with st.expander("Detalle para soporte", expanded=False):
                st.code(resultados["eri_error"])
        return
    st.markdown("### Índice de Resiliencia Ecológica indicativo")
    st.caption(
        "Lectura complementaria entre 0 y 1. No certifica condición ecológica, no "
        "demuestra conectividad funcional y requiere validación de campo."
    )
    valor = float(eri.get("valor", 0) or 0)
    primera, segunda, tercera = st.columns([1, 1, 1.4])
    primera.metric("ERI", f"{valor:.2f} / 1.00")
    segunda.metric("Clase", eri.get("clase", "—"))
    tercera.metric(
        "Componente limitante",
        eri.get("componente_limitante_etiqueta", "—"),
    )
    grafica_componentes = construir_grafica_componentes_eri(resultados)
    grafica_distribucion = construir_grafica_distribucion_eri(resultados)
    columna_componentes, columna_clases = st.columns(2)
    with columna_componentes:
        st.markdown(f"**{grafica_componentes['titulo']}**")
        st.caption(grafica_componentes["descripcion"])
        st.altair_chart(
            crear_grafica_barras_color(grafica_componentes, altura=230),
            use_container_width=True,
            theme=None,
            key="eri_componentes_detalle",
        )
    with columna_clases:
        st.markdown(f"**{grafica_distribucion['titulo']}**")
        st.caption(grafica_distribucion["descripcion"])
        st.altair_chart(
            crear_grafica_barras_color(grafica_distribucion, altura=230),
            use_container_width=True,
            theme=None,
            key="eri_clases_detalle",
        )
    with st.expander("Método y limitaciones del ERI", expanded=False):
        st.markdown(
            f"""
            - **Integridad estructural · 35 %:** altura del dosel GEDI normalizada y
              probabilidad anual de árboles de Dynamic World.
            - **Conectividad · 25 %:** proporción local de bosque en una ventana de
              {float(eri.get('radio_conectividad_m', RADIO_CONECTIVIDAD_ERI_M)) / 1000:.1f} km.
            - **Estabilidad topográfica · 20 %:** pendiente Copernicus DEM ponderada por
              la probabilidad de cobertura arbórea.
            - **Proximidad riparia · 20 %:** distancia a cauces derivados de MERIT Hydro,
              limitada a {int(eri.get('distancia_riparia_m', DISTANCIA_RIPARIA_ERI_M)):,} m.

            {eri.get('nota_conectividad', '')}

            Año de referencia de la cobertura: **{eri.get('anio_referencia', ANO_ERI_REFERENCIA)}**.
            Resolución del resumen: aproximadamente **{int(eri.get('escala_resumen_m', ESCALA_ERI_M))} m**.
            """
        )
        st.info(
            "El ERI se mantiene separado del índice de indicios. Sus pesos y umbrales "
            "deben validarse con información de campo antes de emplearlo para decisiones normativas."
        )


def construir_graficas_dashboard(resultados, modo_analisis):
    """Prepara comparaciones compactas para el panel contiguo al mapa."""

    if modo_analisis == MODO_CORREDORES:
        corredores = resultados.get("corredores") or {}
        fragmentacion = resultados.get("fragmentacion") or {}
        clase = fragmentacion.get("metricas_clase") or {}
        red = fragmentacion.get("metricas_red") or {}
        area_total_ha = float(
            resultados.get("area_ha") or corredores.get("area_aoi_ha", 0) or 0
        )
        area_corredor_ha = min(
            area_total_ha,
            max(0.0, float(corredores.get("area_en_corredores_ha", 0) or 0)),
        )
        area_fuera_corredor_ha = max(0.0, area_total_ha - area_corredor_ha)
        area_bosque_ha = min(
            area_total_ha,
            max(0.0, float(clase.get("area_total_bosque_ha", 0) or 0)),
        )
        area_otros_usos_ha = max(0.0, area_total_ha - area_bosque_ha)
        total_fragmentos = int(clase.get("numero_parches", 0) or 0)
        separados = int(red.get("numero_parches_aislados", 0) or 0)
        cercanos = max(0, total_fragmentos - separados)
        porcentaje_corredor = (
            area_corredor_ha / area_total_ha * 100 if area_total_ha else 0.0
        )
        porcentaje_bosque = (
            area_bosque_ha / area_total_ha * 100 if area_total_ha else 0.0
        )
        return {
            "primaria": {
                "titulo": "Presencia de corredores en el área",
                "descripcion": (
                    "Divide el área analizada entre la parte que coincide con corredores "
                    "publicados y la parte restante. El corredor es una delimitación "
                    "estratégica, no una clase de bosque."
                ),
                "datos": {
                    "Categoría": ["En corredores", "Fuera de corredores"],
                    "Hectáreas": [
                        area_corredor_ha,
                        area_fuera_corredor_ha,
                    ],
                },
                "eje_x": "Categoría",
                "eje_y": "Hectáreas",
                "unidad": "ha",
                "colores": [
                    COLORES_CONECTIVIDAD["En corredores"],
                    COLORES_CONECTIVIDAD["Fuera de corredores"],
                ],
            },
            "secundaria": {
                "titulo": "Cobertura de bosque en 2021",
                "descripcion": (
                    "Divide la misma área entre bosque identificado en 2021 y otros usos "
                    "o coberturas. Esta lectura es independiente del corredor."
                ),
                "datos": {
                    "Cobertura": ["Bosque 2021", "Otros usos 2021"],
                    "Hectáreas": [area_bosque_ha, area_otros_usos_ha],
                },
                "eje_x": "Cobertura",
                "eje_y": "Hectáreas",
                "unidad": "ha",
                "colores": [
                    COLORES_CONECTIVIDAD["Bosque 2021"],
                    COLORES_CONECTIVIDAD["Otros usos 2021"],
                ],
                "disponible": bool(fragmentacion),
            },
            "terciaria": {
                "titulo": "Relación entre fragmentos",
                "descripcion": (
                    "Distingue fragmentos cercanos de los que aparecen separados con la "
                    "distancia configurada."
                ),
                "datos": {
                    "Condición": ["Cercanos", "Separados"],
                    "Fragmentos": [cercanos, separados],
                },
                "eje_x": "Condición",
                "eje_y": "Fragmentos",
                "unidad": "fragmentos",
                "decimales": 0,
                "colores": [
                    COLORES_CONECTIVIDAD["Cercanos"],
                    COLORES_CONECTIVIDAD["Separados"],
                ],
            },
            "clave": (
                f"El {porcentaje_corredor:.1f}% del área coincide con corredores y el "
                f"{porcentaje_bosque:.1f}% fue identificado como bosque en 2021. "
                "Son lecturas diferentes y no se suman entre sí."
                if fragmentacion
                else (
                    f"El {porcentaje_corredor:.1f}% del área coincide con corredores. "
                    "La cobertura de bosque 2021 no estuvo disponible."
                )
            ),
        }

    aportes = resultados.get("aportes_indice") or {}
    cambios = {
        "Indicador": [
            "Deforestación JRC",
            "Degradación JRC",
            "Pérdida Hansen post-2020",
            "Salida de árboles ESRI",
            "Disminución NDVI",
        ],
        "Hectáreas": [
            float(resultados.get("tmf_deforestacion", 0) or 0),
            float(resultados.get("tmf_degradacion", 0) or 0),
            float(resultados.get("hansen_post", 0) or 0),
            float(resultados.get("esri_salida", 0) or 0),
            float(resultados.get("ndvi_disminucion", 0) or 0),
        ],
    }
    fuentes = ["JRC TMF", "Hansen GFC", "ESRI LULC", "GEDI", "NDVI"]
    valores_aporte = [
        float(aportes.get("tmf", 0) or 0),
        float(aportes.get("hansen", 0) or 0),
        float(aportes.get("esri", 0) or 0),
        float(aportes.get("gedi", 0) or 0),
        float(aportes.get("ndvi", 0) or 0),
    ]
    senales = sum(valor > 0 for valor in valores_aporte)
    return {
        "primaria": {
            "titulo": "Aporte de las fuentes al índice",
            "descripcion": (
                "Muestra el aporte ponderado de cada producto; no representa hectáreas "
                "comparables entre fuentes."
            ),
            "datos": {"Fuente": fuentes, "Aporte": valores_aporte},
            "eje_x": "Fuente",
            "eje_y": "Aporte",
            "unidad": "puntos",
            "colores": [COLORES_FUENTES[fuente] for fuente in fuentes],
        },
        "secundaria": {
            "titulo": "Superficie con indicios",
            "descripcion": (
                "Resume las superficies detectadas por cada indicador. Las metodologías "
                "y fechas son distintas y deben interpretarse por separado."
            ),
            "datos": cambios,
            "eje_x": "Indicador",
            "eje_y": "Hectáreas",
            "unidad": "ha",
            "colores": [
                COLORES_CAMBIOS[indicador] for indicador in cambios["Indicador"]
            ],
        },
        "clave": f"{senales} de 5 fuentes aportan al índice de indicios.",
    }


def crear_grafica_barras_color(grafica, altura=None):
    """Construye barras horizontales, etiquetadas y con colores accesibles."""

    eje_categoria = grafica["eje_x"]
    eje_valor = grafica["eje_y"]
    categorias = list(grafica["datos"].get(eje_categoria, []))
    valores = [float(valor or 0) for valor in grafica["datos"].get(eje_valor, [])]
    colores = list(grafica.get("colores") or ["#1F8A70"] * len(categorias))
    if len(colores) < len(categorias):
        colores.extend([colores[-1] if colores else "#1F8A70"] * (len(categorias) - len(colores)))
    unidad = grafica.get("unidad", "")
    decimales = int(grafica.get("decimales", 1))

    def etiqueta_valor(valor):
        numero_formateado = f"{valor:,.{decimales}f}"
        if unidad == "puntos":
            return f"{numero_formateado} pts"
        if unidad:
            return f"{numero_formateado} {unidad}"
        return numero_formateado

    filas = [
        {
            eje_categoria: categoria,
            eje_valor: valor,
            "Etiqueta": etiqueta_valor(valor),
        }
        for categoria, valor in zip(categorias, valores)
    ]
    maximo = max(valores, default=0)
    dominio_maximo = max(1, maximo * 1.28)
    altura_grafica = altura or max(180, min(310, 48 * max(1, len(categorias))))
    datos_altair = alt.Data(values=filas)
    escala_valores = alt.Scale(domain=[0, dominio_maximo], nice=False, zero=True)
    eje_categorias = alt.Y(
        f"{eje_categoria}:N",
        sort=categorias,
        title=None,
        axis=alt.Axis(
            domain=False,
            ticks=False,
            labelColor="#062A5E",
            labelFontSize=12,
            labelFontWeight=600,
            labelLimit=178,
            labelPadding=8,
        ),
    )
    eje_valores = alt.X(
        f"{eje_valor}:Q",
        title=f"{eje_valor} ({unidad})" if unidad else eje_valor,
        scale=escala_valores,
        axis=alt.Axis(
            domain=False,
            tickColor="#D6DEEB",
            gridColor="#E1E6EE",
            gridOpacity=1,
            labelColor="#566176",
            labelFontSize=11,
            titleColor="#566176",
            titleFontSize=11,
            titleFontWeight=600,
            tickCount=4,
        ),
    )
    informacion = [
        alt.Tooltip(f"{eje_categoria}:N", title=eje_categoria),
        alt.Tooltip(f"{eje_valor}:Q", title=eje_valor, format=",.2f"),
    ]
    barras = (
        alt.Chart(datos_altair)
        .mark_bar(cornerRadiusEnd=6, size=22)
        .encode(
            y=eje_categorias,
            x=eje_valores,
            color=alt.Color(
                f"{eje_categoria}:N",
                scale=alt.Scale(domain=categorias, range=colores[: len(categorias)]),
                legend=None,
            ),
            tooltip=informacion,
        )
    )
    etiquetas = (
        alt.Chart(datos_altair)
        .mark_text(
            align="left",
            baseline="middle",
            dx=6,
            color="#062A5E",
            fontSize=11,
            fontWeight=600,
        )
        .encode(
            y=eje_categorias,
            x=eje_valores,
            text=alt.Text("Etiqueta:N"),
            tooltip=informacion,
        )
    )
    return (
        (barras + etiquetas)
        .properties(height=altura_grafica)
        .configure_view(stroke=None)
        .configure(background="#FFFFFF")
    )


def resolver_capa_contextual(modo_analisis, modo_comparador, capas_activas):
    """Mantiene la gráfica alineada con la última evidencia activada en el mapa."""

    comparadores = {
        "JRC TMF": "Estado forestal JRC",
        "ESRI LULC": "Uso y cobertura ESRI",
        "NDVI Sentinel-2": "Vegetación NDVI",
    }
    if modo_comparador in comparadores:
        return comparadores[modo_comparador]

    opciones = list(dict.fromkeys(capas_activas))
    if not opciones and modo_analisis == MODO_CORREDORES:
        opciones = ["Conectividad y fragmentos"]
    if not opciones:
        return "Sectores para revisión"

    clave_activas = f"capas_contextuales_anteriores_{modo_analisis}"
    clave_elegida = f"capa_contextual_{modo_analisis}"
    anteriores = set(st.session_state.get(clave_activas, []))
    nuevas = [capa for capa in opciones if capa not in anteriores]
    elegida_anterior = st.session_state.get(clave_elegida)
    if nuevas:
        elegida = nuevas[-1]
    elif elegida_anterior in opciones:
        elegida = elegida_anterior
    else:
        elegida = opciones[0]
    st.session_state[clave_activas] = opciones
    st.session_state[clave_elegida] = elegida
    return elegida


def configuracion_grafica_contextual(capa):
    """Relaciona cada evidencia cartográfica con una gráfica interpretable."""

    configuraciones = {
        "Estado forestal JRC": {
            "tipo": "distribucion_tmf",
            "titulo": f"Estado forestal JRC {ANO_DIAG_TMF}",
            "descripcion": (
                "Distribución de las seis clases de JRC TMF dentro del área analizada; "
                "incluye la regeneración forestal."
            ),
        },
        "Deforestación JRC": {
            "fuente": "JRC Tropical Moist Forest",
            "series": ["Deforestación (ha)"],
            "titulo": "Deforestación por año",
            "descripcion": "Hectáreas clasificadas anualmente como deforestación por JRC TMF.",
            "colores": [COLORES_CAMBIOS["Deforestación JRC"]],
        },
        "Degradación JRC": {
            "fuente": "JRC Tropical Moist Forest",
            "series": ["Degradación (ha)"],
            "titulo": "Degradación por año",
            "descripcion": "Hectáreas clasificadas anualmente como degradación por JRC TMF.",
            "colores": [COLORES_CAMBIOS["Degradación JRC"]],
        },
        "Regeneración forestal JRC": {
            "fuente": "JRC Tropical Moist Forest",
            "series": ["Regeneración forestal (ha)"],
            "titulo": "Regeneración forestal por año",
            "descripcion": (
                "Hectáreas previamente deforestadas que JRC TMF clasifica como bosque "
                "en regeneración (Forest regrowth)."
            ),
            "colores": [COLORES_CAMBIOS["Regeneración forestal JRC"]],
        },
        "Pérdida Hansen post-2020": {
            "fuente": "Hansen Global Forest Change",
            "series": ["Pérdida (ha)"],
            "titulo": "Pérdida de cobertura arbórea por año",
            "descripcion": "Hectáreas de pérdida registradas por Hansen desde 2021.",
            "anio_min": 2021,
            "colores": [COLORES_FUENTES["Hansen GFC"]],
        },
        "Pérdida Hansen 2001-2020": {
            "fuente": "Hansen Global Forest Change",
            "series": ["Pérdida (ha)"],
            "titulo": "Pérdida histórica de cobertura arbórea",
            "descripcion": "Hectáreas de pérdida anual registradas por Hansen entre 2001 y 2020.",
            "anio_max": 2020,
            "colores": [COLORES_FUENTES["Hansen GFC"]],
        },
        "Cobertura arbórea persistente": {
            "fuente": "Hansen Global Forest Change",
            "series": ["Pérdida (ha)"],
            "titulo": "Pérdida anual de cobertura arbórea",
            "descripcion": "Serie de pérdida que ayuda a interpretar la cobertura persistente mostrada en el mapa.",
            "colores": [COLORES_FUENTES["Hansen GFC"]],
        },
        "Uso y cobertura ESRI": {
            "fuente": "ESRI Land Use / Land Cover",
            "series": ["Cobertura arbórea (ha)"],
            "titulo": "Cobertura arbórea por año",
            "descripcion": "Hectáreas clasificadas como árboles en cada edición anual de ESRI.",
            "colores": [COLORES_FUENTES["ESRI LULC"]],
        },
        "Transiciones ESRI": {
            "fuente": "ESRI Land Use / Land Cover",
            "series": ["Cobertura arbórea (ha)"],
            "titulo": "Cobertura arbórea por año",
            "descripcion": "La serie anual aporta contexto para interpretar las transiciones de la clase árboles.",
            "colores": [COLORES_FUENTES["ESRI LULC"]],
        },
        "ΔNDVI": {
            "fuente": "Sentinel-2 · NDVI",
            "series": ["NDVI medio"],
            "titulo": "Vigor medio de la vegetación por año",
            "descripcion": "Promedio anual del NDVI; se interpreta como señal corroborativa, no como cobertura.",
            "colores": [COLORES_FUENTES["NDVI"]],
        },
        "Vegetación NDVI": {
            "fuente": "Sentinel-2 · NDVI",
            "series": ["NDVI medio"],
            "titulo": "Vigor medio de la vegetación por año",
            "descripcion": "Promedio anual del NDVI para comparar el vigor vegetal entre años.",
            "colores": [COLORES_FUENTES["NDVI"]],
        },
        "Altura GEDI": {
            "fuente": "GEDI · altura del dosel",
            "series": ["Observaciones"],
            "titulo": "Distribución de la altura del dosel",
            "descripcion": "Número de observaciones disponibles por intervalo de altura; GEDI no es una serie anual.",
            "colores": [COLORES_FUENTES["GEDI"]],
        },
        "ERI indicativo": {
            "tipo": "eri",
            "titulo": "Componentes del ERI indicativo",
            "descripcion": (
                "Comparación normalizada de los cuatro componentes ecológicos. "
                "El valor menor señala el componente que conviene revisar primero."
            ),
        },
    }
    return configuraciones.get(capa)


def configuracion_grafica_contextual_compuesta(capa_principal, capas_activas):
    """Agrupa en una sola gráfica las evidencias activas que sí son comparables."""

    configuracion_principal = configuracion_grafica_contextual(capa_principal)
    if (
        not configuracion_principal
        or configuracion_principal.get("tipo")
        or not configuracion_principal.get("fuente")
    ):
        return configuracion_principal, [capa_principal] if capa_principal else []

    fuente_principal = configuracion_principal["fuente"]
    configuraciones_compatibles = []
    for capa in dict.fromkeys(capas_activas or []):
        configuracion = configuracion_grafica_contextual(capa)
        if (
            configuracion
            and not configuracion.get("tipo")
            and configuracion.get("fuente") == fuente_principal
        ):
            configuraciones_compatibles.append((capa, configuracion))

    if not any(capa == capa_principal for capa, _ in configuraciones_compatibles):
        configuraciones_compatibles.append(
            (capa_principal, configuracion_principal)
        )

    configuracion_compuesta = dict(configuracion_principal)
    series = []
    colores = []
    for _, configuracion in configuraciones_compatibles:
        colores_configuracion = configuracion.get("colores") or ["#1F8A70"]
        for indice, serie in enumerate(configuracion.get("series", [])):
            if serie in series:
                continue
            series.append(serie)
            colores.append(
                colores_configuracion[min(indice, len(colores_configuracion) - 1)]
            )
    configuracion_compuesta["series"] = series
    configuracion_compuesta["colores"] = colores

    if len(configuraciones_compatibles) > 1:
        limites_minimos = [
            configuracion.get("anio_min")
            for _, configuracion in configuraciones_compatibles
        ]
        limites_maximos = [
            configuracion.get("anio_max")
            for _, configuracion in configuraciones_compatibles
        ]
        if all(limite is not None for limite in limites_minimos):
            configuracion_compuesta["anio_min"] = min(limites_minimos)
        else:
            configuracion_compuesta.pop("anio_min", None)
        if all(limite is not None for limite in limites_maximos):
            configuracion_compuesta["anio_max"] = max(limites_maximos)
        else:
            configuracion_compuesta.pop("anio_max", None)

        if fuente_principal == "JRC Tropical Moist Forest":
            configuracion_compuesta.update(
                titulo="Cambios forestales seleccionados por año",
                descripcion=(
                    "Las barras apiladas comparan las capas JRC TMF activadas. "
                    "Cada indicador conserva un color y una etiqueta propios."
                ),
            )
        elif fuente_principal == "Hansen Global Forest Change":
            configuracion_compuesta.update(
                titulo="Pérdida de cobertura arbórea por año",
                descripcion=(
                    "La serie reúne los períodos Hansen seleccionados sin duplicar "
                    "los años ni cambiar la unidad de hectáreas."
                ),
            )

    return configuracion_compuesta, [
        capa for capa, _ in configuraciones_compatibles
    ]


def crear_grafica_serie_barras(
    grafica,
    series=None,
    colores=None,
    anio_min=None,
    anio_max=None,
    altura=245,
):
    """Construye barras apiladas y, para años, un navegador temporal inferior."""

    columnas = grafica["columnas"]
    eje_x = next(iter(columnas))
    series_disponibles = list(columnas)[1:]
    series = [serie for serie in (series or series_disponibles) if serie in columnas]
    if not series:
        series = series_disponibles
    valores_x = list(columnas.get(eje_x, []))
    es_serie_anual = eje_x.strip().lower() in {"año", "ano"}
    filas = []
    periodos = []
    anios_disponibles = []
    for indice, valor_x in enumerate(valores_x):
        try:
            valor_numerico_x = float(valor_x)
        except (TypeError, ValueError):
            valor_numerico_x = None
        if anio_min is not None and valor_numerico_x is not None and valor_numerico_x < anio_min:
            continue
        if anio_max is not None and valor_numerico_x is not None and valor_numerico_x > anio_max:
            continue
        periodo = str(int(valor_x)) if isinstance(valor_x, int) else str(valor_x)
        periodos.append(periodo)
        for orden_serie, serie in enumerate(series):
            valores_serie = columnas.get(serie, [])
            valor = float(valores_serie[indice] or 0) if indice < len(valores_serie) else 0.0
            fila = {
                "Periodo": periodo,
                "Serie": serie,
                "OrdenSerie": orden_serie,
                "Valor": valor,
            }
            if es_serie_anual and valor_numerico_x is not None:
                anio_periodo = int(valor_numerico_x)
                fila["Anio"] = anio_periodo
                anios_disponibles.append(anio_periodo)
            filas.append(fila)

    colores = list(colores or ["#1F8A70"])
    if len(colores) < len(series):
        colores.extend([colores[-1]] * (len(series) - len(colores)))
    if all("(ha)" in serie for serie in series):
        titulo_eje = "Superficie (ha)"
        formato_tooltip = ",.2f"
    elif series == ["NDVI medio"]:
        titulo_eje = "NDVI medio"
        formato_tooltip = ".3f"
    elif series == ["Observaciones"]:
        titulo_eje = "Observaciones"
        formato_tooltip = ",.0f"
    else:
        titulo_eje = "Valor"
        formato_tooltip = ",.2f"

    datos = alt.Data(values=filas)
    navegador_periodo = None
    if es_serie_anual and len(set(periodos)) > 8:
        intervalo_inicial = (
            min(anios_disponibles),
            max(anios_disponibles),
        )
        navegador_periodo = alt.selection_interval(
            encodings=["x"],
            name="periodo_visible",
            value={"x": intervalo_inicial},
            clear=False,
            mark=alt.BrushConfig(
                fill="#D6DEEB",
                fillOpacity=0.38,
                stroke="#3A7CA5",
                strokeWidth=1.5,
            ),
        )
        eje_periodo = alt.X(
            "Periodo:O",
            sort=list(dict.fromkeys(periodos)),
            title=eje_x,
            axis=alt.Axis(
                labelAngle=0,
                labelOverlap="greedy",
                labelColor="#566176",
                labelFontSize=10,
                titleColor="#566176",
                titleFontSize=11,
                tickColor="#D6DEEB",
                domainColor="#D6DEEB",
                tickCount=6,
            ),
        )
    else:
        eje_periodo = alt.X(
            "Periodo:N",
            sort=list(dict.fromkeys(periodos)),
            title=eje_x,
            axis=alt.Axis(
                labelAngle=-45 if len(set(periodos)) > 10 else 0,
                labelOverlap="greedy",
                labelColor="#566176",
                labelFontSize=10,
                titleColor="#566176",
                titleFontSize=11,
                tickColor="#D6DEEB",
                domainColor="#D6DEEB",
            ),
        )

    base = alt.Chart(datos)
    if navegador_periodo is not None:
        base = base.transform_filter(navegador_periodo)
    base = base.mark_bar(
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3,
    )
    codificacion = {
        "x": eje_periodo,
        "y": alt.Y(
            "Valor:Q",
            title=titulo_eje,
            stack="zero",
            scale=alt.Scale(zero=True),
            axis=alt.Axis(
                gridColor="#E1E6EE",
                domain=False,
                labelColor="#566176",
                labelFontSize=10,
                titleColor="#566176",
                titleFontSize=11,
                tickCount=4,
            ),
        ),
        "color": alt.Color(
            "Serie:N",
            scale=alt.Scale(domain=series, range=colores[: len(series)]),
            legend=(
                alt.Legend(
                    orient="top",
                    direction="horizontal",
                    title=None,
                    labelColor="#062A5E",
                    labelFontSize=10,
                )
                if len(series) > 1
                else None
            ),
        ),
        "tooltip": [
            alt.Tooltip("Periodo:N", title=eje_x),
            alt.Tooltip("Serie:N", title="Indicador"),
            alt.Tooltip("Valor:Q", title=titulo_eje, format=formato_tooltip),
        ],
        "order": alt.Order("OrdenSerie:Q", sort="ascending"),
    }
    grafica_principal = base.encode(**codificacion).properties(height=altura)

    if navegador_periodo is not None:
        navegador = (
            alt.Chart(datos)
            .mark_area(
                color="#78A9BD",
                opacity=0.3,
                line=alt.LineConfig(color="#3A7CA5", strokeWidth=1),
            )
            .encode(
                x=alt.X(
                    "Anio:Q",
                    title=None,
                    axis=alt.Axis(
                        format="d",
                        labelAngle=0,
                        labelColor="#566176",
                        labelFontSize=9,
                        tickCount=6,
                        grid=False,
                        domainColor="#D6DEEB",
                    ),
                ),
                y=alt.Y("sum(Valor):Q", title=None, axis=None),
            )
            .properties(height=52)
            .add_params(navegador_periodo)
        )
        grafica_final = alt.vconcat(
            grafica_principal,
            navegador,
            spacing=8,
        )
    else:
        grafica_final = grafica_principal

    return (
        grafica_final.configure_view(stroke=None)
        .configure(background="#FFFFFF")
    )


def construir_grafica_estado_tmf(resultados):
    """Resume las seis clases oficiales de JRC TMF para el año diagnóstico."""

    return {
        "titulo": f"Estado forestal JRC {ANO_DIAG_TMF}",
        "descripcion": (
            "Muestra la distribución completa del área, incluida la regeneración "
            "forestal; no representa por sí sola un proyecto de restauración."
        ),
        "eje_x": "Clase",
        "eje_y": "Hectáreas",
        "unidad": "ha",
        "colores": [
            "#006400",
            "#F2A541",
            "#C73E3A",
            COLORES_CAMBIOS["Regeneración forestal JRC"],
            "#4D9DE0",
            "#A8B3B0",
        ],
        "datos": {
            "Clase": [
                "Bosque no perturbado",
                "Bosque degradado",
                "Tierra deforestada",
                "Regeneración forestal",
                "Agua",
                "Otra cobertura",
            ],
            "Hectáreas": [
                float(resultados.get("tmf_estable", 0) or 0),
                float(resultados.get("tmf_degradacion", 0) or 0),
                float(resultados.get("tmf_deforestacion", 0) or 0),
                float(resultados.get("tmf_recuperacion", 0) or 0),
                float(resultados.get("tmf_agua", 0) or 0),
                float(resultados.get("tmf_otra_cobertura", 0) or 0),
            ],
        },
    }


def filtrar_tabla_serie(grafica, series=None, anio_min=None, anio_max=None):
    """Devuelve una tabla accesible con exactamente los valores visibles en la gráfica."""

    columnas = grafica["columnas"]
    eje_x = next(iter(columnas))
    series = [
        serie
        for serie in (series or list(columnas)[1:])
        if serie in columnas
    ]
    indices = []
    for indice, valor_x in enumerate(columnas.get(eje_x, [])):
        try:
            valor_numerico_x = float(valor_x)
        except (TypeError, ValueError):
            valor_numerico_x = None
        if anio_min is not None and valor_numerico_x is not None and valor_numerico_x < anio_min:
            continue
        if anio_max is not None and valor_numerico_x is not None and valor_numerico_x > anio_max:
            continue
        indices.append(indice)
    return {
        nombre: [valores[indice] for indice in indices if indice < len(valores)]
        for nombre, valores in columnas.items()
        if nombre == eje_x or nombre in series
    }


def mostrar_grafica_contextual_dashboard(
    resultados,
    modo_analisis,
    capa_contextual,
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
    capas_activas=None,
):
    """Muestra debajo del resultado la gráfica vinculada con la evidencia activa."""

    configuracion = None
    capas_representadas = [capa_contextual] if capa_contextual else []
    if capa_contextual not in (None, "Sectores para revisión", "Conectividad y fragmentos"):
        configuracion, capas_representadas = configuracion_grafica_contextual_compuesta(
            capa_contextual,
            capas_activas,
        )
    etiqueta_capa = " · ".join(capas_representadas) or "Resumen del resultado"
    if capa_contextual in (None, "Sectores para revisión"):
        rotulo_cabecera = "Resumen visualizado en el mapa"
    elif len(capas_representadas) > 1:
        rotulo_cabecera = f"Visualizadas en el mapa · {len(capas_representadas)} capas"
    else:
        rotulo_cabecera = "Visualizada en el mapa"
    st.markdown(
        f'<div class="grafica-contextual-cabecera"><small>{rotulo_cabecera}</small>'
        f'<strong>{html_lib.escape(etiqueta_capa)}</strong></div>',
        unsafe_allow_html=True,
    )

    if capa_contextual in (None, "Sectores para revisión"):
        grafica = construir_graficas_dashboard(resultados, modo_analisis)["secundaria"]
        st.markdown(
            '<div class="grafica-contextual-nota">Resumen de las superficies detectadas '
            'por los indicadores visibles en la preevaluación.</div>',
            unsafe_allow_html=True,
        )
        st.altair_chart(
            crear_grafica_barras_color(grafica, altura=220),
            use_container_width=True,
            theme=None,
            key="grafica_contextual_resumen",
        )
        return

    if capa_contextual == "Conectividad y fragmentos":
        grafica = construir_graficas_dashboard(resultados, modo_analisis)["primaria"]
        st.markdown(
            f'<div class="grafica-contextual-nota">{html_lib.escape(grafica["descripcion"])}</div>',
            unsafe_allow_html=True,
        )
        st.altair_chart(
            crear_grafica_barras_color(grafica, altura=190),
            use_container_width=True,
            theme=None,
            key="grafica_contextual_conectividad",
        )
        return

    if not configuracion:
        st.info("Esta evidencia se interpreta directamente en el mapa y en la lectura del resultado.")
        return

    st.markdown(
        f'<div class="grafica-contextual-nota"><b>{html_lib.escape(configuracion["titulo"])}</b><br>'
        f'{html_lib.escape(configuracion["descripcion"])}</div>',
        unsafe_allow_html=True,
    )
    if configuracion.get("tipo") == "distribucion_tmf":
        grafica = construir_grafica_estado_tmf(resultados)
        st.altair_chart(
            crear_grafica_barras_color(grafica, altura=260),
            use_container_width=True,
            theme=None,
            key="grafica_contextual_estado_tmf",
        )
        with st.expander("Ver valores de la gráfica", expanded=False):
            st.dataframe(grafica["datos"], hide_index=True, use_container_width=True)
        return

    if configuracion.get("tipo") == "eri":
        if not resultados.get("eri"):
            mostrar_resumen_eri(resultados)
            return
        grafica = construir_grafica_componentes_eri(resultados)
        st.altair_chart(
            crear_grafica_barras_color(grafica, altura=245),
            use_container_width=True,
            theme=None,
            key="grafica_contextual_eri",
        )
        with st.expander("Ver valores de la gráfica", expanded=False):
            st.dataframe(grafica["datos"], hide_index=True, use_container_width=True)
        return

    try:
        mensaje_carga = (
            "Preparando las barras de las capas seleccionadas..."
            if len(capas_representadas) > 1
            else f"Preparando barras de {etiqueta_capa.lower()}..."
        )
        with st.spinner(mensaje_carga):
            grafica = calcular_serie_fuente(
                tipo_area,
                finca_id,
                subcuenca_nombre,
                geometria_geojson,
                configuracion["fuente"],
            )
    except Exception as error:
        st.warning(
            "El mapa y el resultado permanecen disponibles, pero la gráfica de esta "
            "evidencia no pudo prepararse en este momento."
        )
        with st.expander("Detalle técnico de la gráfica", expanded=False):
            st.code(f"{type(error).__name__}: {error}")
        return

    clave_capas = "_".join(capas_representadas)
    st.altair_chart(
        crear_grafica_serie_barras(
            grafica,
            series=configuracion.get("series"),
            colores=configuracion.get("colores"),
            anio_min=configuracion.get("anio_min"),
            anio_max=configuracion.get("anio_max"),
            altura=245,
        ),
        use_container_width=True,
        theme=None,
        key=(
            "grafica_contextual_"
            f"{re.sub(r'[^a-z0-9]+', '_', clave_capas.lower()).strip('_')}"
        ),
    )
    with st.expander("Ver valores de la gráfica", expanded=False):
        st.dataframe(
            filtrar_tabla_serie(
                grafica,
                series=configuracion.get("series"),
                anio_min=configuracion.get("anio_min"),
                anio_max=configuracion.get("anio_max"),
            ),
            hide_index=True,
            use_container_width=True,
        )


def mostrar_graficas_dashboard(resultados, modo_analisis):
    """Muestra gráficas inmediatas sin abandonar el mapa principal."""

    graficas = construir_graficas_dashboard(resultados, modo_analisis)
    st.markdown(
        '<div class="dashboard-grafica-intro">Las gráficas se actualizan con el área '
        'analizada. Pase el cursor sobre las barras para consultar valores exactos.</div>',
        unsafe_allow_html=True,
    )
    if modo_analisis == MODO_CORREDORES:
        nombres = ["Corredores", "Bosque 2021", "Fragmentos"]
        claves = ["primaria", "secundaria", "terciaria"]
    else:
        nombres = ["Fuentes", "Cambios"]
        claves = ["primaria", "secundaria"]
    pestanas = st.tabs(nombres)
    for pestana, clave in zip(pestanas, claves):
        grafica = graficas[clave]
        with pestana:
            st.markdown(f"**{grafica['titulo']}**")
            st.caption(grafica["descripcion"])
            if grafica.get("disponible", True):
                st.altair_chart(
                    crear_grafica_barras_color(grafica),
                    use_container_width=True,
                    theme=None,
                    key=f"dashboard_{grafica['eje_x']}_{grafica['eje_y']}",
                )
                with st.expander("Ver valores de la gráfica", expanded=False):
                    st.dataframe(
                        grafica["datos"], hide_index=True, use_container_width=True
                    )
            else:
                st.info("La cobertura de bosque 2021 no estuvo disponible en esta ejecución.")
    st.markdown(
        f'<div class="dashboard-dato-clave"><b>Lectura clave:</b> '
        f'{html_lib.escape(graficas["clave"])}</div>',
        unsafe_allow_html=True,
    )


def mostrar_grafica_por_fuente(
    firma_analisis,
    tipo_area,
    finca_id,
    subcuenca_nombre,
    geometria_geojson,
):
    """Presenta una gráfica elegida por el usuario, sin calcular todas de entrada."""

    st.markdown("### Evolución por fuente")
    st.caption(
        "Seleccione una fuente y prepare únicamente esa gráfica. Así se conserva la "
        "capacidad analítica sin aumentar el tiempo de carga inicial."
    )
    columna_fuente, columna_accion = st.columns([2.2, 1])
    fuente = columna_fuente.selectbox(
        "Fuente para la gráfica",
        [
            "JRC Tropical Moist Forest",
            "Hansen Global Forest Change",
            "ESRI Land Use / Land Cover",
            "Sentinel-2 · NDVI",
            "GEDI · altura del dosel",
        ],
        key="fuente_grafica_analisis",
        help=(
            "Cada gráfica conserva la unidad y el significado propios de su fuente. "
            "No se mezclan indicadores incompatibles en una misma escala."
        ),
    )
    preparar = columna_accion.button(
        "Preparar gráfica",
        type="primary",
        use_container_width=True,
        key="preparar_grafica_fuente",
    )
    firma_grafica = (firma_analisis, fuente)
    if preparar:
        try:
            with st.spinner(f"Consultando {fuente} para el área seleccionada..."):
                st.session_state["grafica_fuente"] = calcular_serie_fuente(
                    tipo_area,
                    finca_id,
                    subcuenca_nombre,
                    geometria_geojson,
                    fuente,
                )
                st.session_state["firma_grafica_fuente"] = firma_grafica
                st.session_state.pop("error_grafica_fuente", None)
        except Exception as error:
            st.session_state.pop("grafica_fuente", None)
            st.session_state["firma_grafica_fuente"] = firma_grafica
            st.session_state["error_grafica_fuente"] = (
                f"{type(error).__name__}: {error}"
            )

    if st.session_state.get("firma_grafica_fuente") != firma_grafica:
        st.info(
            "La gráfica se calcula solo cuando usted la solicita. Los resultados principales "
            "de la preevaluación ya están disponibles en las pestañas superiores."
        )
        return

    error_grafica = st.session_state.get("error_grafica_fuente")
    if error_grafica:
        st.warning(
            "La preevaluación permanece disponible, pero esta gráfica temporal no pudo "
            "prepararse en este momento."
        )
        with st.expander("Detalle técnico de la gráfica", expanded=False):
            st.code(error_grafica)
        return

    grafica = st.session_state.get("grafica_fuente")
    if not grafica:
        return
    st.markdown(f"#### {grafica['titulo']}")
    st.caption(grafica["descripcion"])
    columnas = grafica["columnas"]
    eje_x = next(iter(columnas))
    series = list(columnas)[1:]
    paletas_fuente = {
        "JRC Tropical Moist Forest": [
            "#C73E3A",
            "#F2A541",
            COLORES_CAMBIOS["Regeneración forestal JRC"],
        ],
        "Hansen Global Forest Change": [COLORES_FUENTES["Hansen GFC"]],
        "ESRI Land Use / Land Cover": [COLORES_FUENTES["ESRI LULC"]],
        "Sentinel-2 · NDVI": [COLORES_FUENTES["NDVI"]],
        "GEDI · altura del dosel": [COLORES_FUENTES["GEDI"]],
    }
    colores_series = paletas_fuente.get(fuente, ["#1F8A70"])
    st.altair_chart(
        crear_grafica_serie_barras(
            grafica,
            series=series,
            colores=(colores_series * len(series))[: len(series)],
            altura=360,
        ),
        use_container_width=True,
        theme=None,
        key=f"grafica_detalle_{re.sub(r'[^a-z0-9]+', '_', fuente.lower()).strip('_')}",
    )
    st.download_button(
        "Descargar datos de la gráfica",
        data=json.dumps(
            {
                "fuente": fuente,
                "titulo": grafica["titulo"],
                "columnas": columnas,
            },
            ensure_ascii=False,
            indent=2,
        ),
        file_name=f"grafica_{re.sub(r'[^a-z0-9]+', '_', fuente.lower()).strip('_')}.json",
        mime="application/json",
        use_container_width=True,
    )


def establecer_modo_analisis(modo):
    limpiar_estado_resultados()
    st.session_state["modo_analisis"] = modo
    st.session_state["mostrar_resultados"] = False
    st.session_state.pop("orden_capas_personalizado", None)
    st.session_state.pop("capa_a_reordenar", None)


def abrir_resultados_contextuales():
    st.session_state["mostrar_resultados"] = True


def volver_al_mapa():
    st.session_state["mostrar_resultados"] = False


def mostrar_selector_modos():
    st.markdown(
        """
        <div class="selector-modos-intro">
          <h2>¿Qué desea preevaluar?</h2>
          <p>Elija un enfoque. Solo verá los controles y resultados necesarios para esa pregunta.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    columnas = st.columns(3)
    for columna, (modo, contenido) in zip(columnas, MODOS_ANALISIS.items()):
        with columna:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="modo-card">
                      <small>{html_lib.escape(contenido['pregunta'])}</small>
                      <h3>{html_lib.escape(contenido['titulo'])}</h3>
                      <p>{html_lib.escape(contenido['descripcion'])}</p>
                      <div class="modo-resultado"><b>Recibirá:</b> {html_lib.escape(contenido['resultado'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Elegir {contenido['titulo'].lower()}",
                    key=f"elegir-modo-{modo}",
                    type="primary" if modo == MODO_INTEGRAL else "secondary",
                    use_container_width=True,
                ):
                    establecer_modo_analisis(modo)
                    st.rerun()
    st.info(
        "Puede cambiar de opción después. La aplicación conservará separadas las "
        "conclusiones territoriales, de conectividad e integrales."
    )


def mostrar_flujo(paso_actual, contenedor=None):
    pasos = [
        ("Objetivo", "Elija qué desea preevaluar."),
        ("Área", "Seleccione la unidad territorial."),
        ("Preevaluar", "Procese únicamente la información necesaria."),
        ("Revisar", "Consulte la conclusión, el mapa y los detalles."),
    ]
    tarjetas = []
    for numero, (titulo, descripcion) in enumerate(pasos, start=1):
        if numero < paso_actual:
            estado = "completado"
            texto_estado = "Completado"
        elif numero == paso_actual:
            estado = "actual"
            texto_estado = "Paso actual"
        else:
            estado = "pendiente"
            texto_estado = "Pendiente"
        aria_actual = ' aria-current="step"' if numero == paso_actual else ""
        tarjetas.append(
            f'<div class="flujo-paso {estado}"{aria_actual}>'
            f'<span class="flujo-numero">{numero}</span>'
            f"<b>{html_lib.escape(titulo)}</b>"
            f"{html_lib.escape(descripcion)}"
            f'<span class="flujo-estado">{texto_estado}</span>'
            f"</div>"
        )
    destino = contenedor if contenedor is not None else st
    destino.markdown(
        '<div class="flujo-pasos" aria-label="Progreso de la preevaluación">'
        + "".join(tarjetas)
        + "</div>",
        unsafe_allow_html=True,
    )


def mostrar_entregables(contenedor=None):
    destino = contenedor if contenedor is not None else st
    destino.markdown(
        """
        <div class="entregables" aria-label="Contenido que entregará el análisis">
          <div class="entregable">
            <small>Primero</small>
            <b>Una conclusión resumida</b>
            <span>Indica la prioridad de revisión y explica qué significa en lenguaje sencillo.</span>
          </div>
          <div class="entregable">
            <small>Después</small>
            <b>La evidencia en el mapa</b>
            <span>Permite ubicar visualmente las señales y comparar los períodos disponibles.</span>
          </div>
          <div class="entregable">
            <small>Al finalizar</small>
            <b>Un informe trazable</b>
            <span>Reúne resultados, mapas, fuentes y parámetros para documentar la revisión.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_error_amigable(error):
    if isinstance(error, json.JSONDecodeError):
        explicacion = (
            "La conexión segura con los datos necesita ser corregida por el administrador. "
            "El problema no está relacionado con el área que intentó analizar."
        )
    elif "permission" in str(error).lower():
        explicacion = (
            "La aplicación no tiene autorización para consultar una de las fuentes de datos. "
            "El administrador debe revisar los permisos de Earth Engine."
        )
    else:
        explicacion = (
            "La aplicación no pudo completar la conexión inicial con las fuentes territoriales. "
            "Sus datos y selecciones no causaron este problema."
        )
    st.error("El visor no pudo iniciar la preevaluación seleccionada.")
    st.markdown(f"**Qué ocurrió:** {explicacion}")
    st.markdown(
        """
        <div class="recuperacion-error" aria-label="Cómo continuar">
          <div class="recuperacion-paso">
            <b>1. Intente nuevamente</b>
            <span>Recargue la página una vez para descartar una interrupción temporal.</span>
          </div>
          <div class="recuperacion-paso">
            <b>2. Avise al administrador</b>
            <span>Si continúa, indique que el visor no logró conectarse con Earth Engine.</span>
          </div>
          <div class="recuperacion-paso">
            <b>3. Comparta el detalle</b>
            <span>Abra el detalle técnico inferior y envíe únicamente el mensaje de error.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_leyenda(titulo, elementos):
    st.markdown(f"**{titulo}**")
    filas = []
    for elemento in elementos:
        color, texto = elemento[:2]
        explicacion = elemento[2] if len(elemento) > 2 else None
        texto_seguro = html_lib.escape(texto)
        if explicacion:
            ayuda = html_lib.escape(explicacion)
            etiqueta = html_lib.escape(
                f"{texto}: pulse para ver la explicación",
                quote=True,
            )
            contenido = (
                f'<details class="leyenda-detalle">'
                f'<summary aria-label="{etiqueta}">'
                f'<span class="leyenda-texto">{texto_seguro}</span>'
                f'<span class="leyenda-info" aria-hidden="true">i</span>'
                f'</summary>'
                f'<div class="leyenda-ayuda">{ayuda}</div>'
                f'</details>'
            )
        else:
            contenido = f'<span class="leyenda-texto">{texto_seguro}</span>'
        filas.append(
            f'<div class="leyenda-fila"><span class="leyenda-color" '
            f'style="background:{color};"></span>'
            f'{contenido}</div>'
        )
    st.markdown("".join(filas), unsafe_allow_html=True)


def mostrar_escala_ndvi_metodologia():
    st.markdown("**Escala visual del vigor vegetal (NDVI)**")
    st.caption(
        "Los intervalos se muestran siempre. Pulse el botón de información de "
        "cada clase para conocer su interpretación y sus precauciones."
    )
    for clase in CLASES_VIGOR_NDVI:
        contenido, ayuda = st.columns(
            [5, 1.35],
            gap="small",
            vertical_alignment="center",
        )
        with contenido:
            etiqueta = html_lib.escape(clase["etiqueta"])
            rango = html_lib.escape(clase["rango"])
            st.markdown(
                f"""
                <div class="ndvi-metodo-fila">
                  <span class="ndvi-metodo-color" style="background:{clase['color']};"></span>
                  <span class="ndvi-metodo-texto">
                    <strong>{etiqueta}</strong>
                    <span class="ndvi-metodo-rango">{rango}</span>
                  </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with ayuda:
            with st.popover(
                "Información",
                icon=":material/info:",
                help=f"Cómo interpretar: {clase['etiqueta']}",
                use_container_width=True,
            ):
                st.markdown(f"**{clase['etiqueta']}**")
                st.code(clase["rango"], language=None)
                st.write(clase["interpretacion"])
    st.caption(
        "Esta escala describe vigor espectral, no tipo de cobertura. Un NDVI alto "
        "no confirma por sí solo la presencia de bosque natural."
    )


def mostrar_resumen_ejecutivo(resultados):
    """Muestra únicamente la decisión principal antes del mapa."""

    prioridad_cambios = resultados["prioridad"]
    visita = resultados.get("prioridad_visita")
    prioridad = visita["prioridad_visita"] if visita else prioridad_cambios
    recomendacion = (
        texto_recomendacion_visita(prioridad)
        if visita
        else texto_recomendacion(prioridad)
    )
    color = {
        "Muy alta": "#7f0000",
        "Alta": "#b71c1c",
        "Media": "#a33a00",
        "Preventiva": "#8a5b00",
        "Baja": "#2e7d32",
    }[prioridad]
    if visita:
        estructura = visita["contexto_estructural"]
        detalle = (
            f"Cambios {visita['puntaje_cambios']:.1f}/{PUNTAJE_MAXIMO:.1f} · "
            f"corredor +{visita['aporte_corredor']:.2f} · "
            f"estructura {estructura['estado'].lower()}"
        )
    else:
        estructura = None
        detalle = f"Índice operativo {resultados['puntaje']:.1f}/{PUNTAJE_MAXIMO:.1f}"

    st.markdown(
        f"""
        <div class="resultado-prioridad" style="--prioridad-color:{color};">
          <small>{html_lib.escape(detalle)}</small>
          <strong>Prioridad {prioridad.lower()} de visita</strong>
          <p>{html_lib.escape(recomendacion)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if visita:
        col_cambios, col_corredor, col_estructura, col_final = st.columns(4)
        col_cambios.metric("Urgencia por cambios", prioridad_cambios)
        col_corredor.metric("Valor del corredor", visita["valor_corredor"])
        col_estructura.metric("Estructura del bosque", estructura["estado"])
        col_final.metric("Prioridad integrada", prioridad)
    st.caption(
        "Revise ahora el mapa. El desglose de las fuentes, los corredores y la "
        "conectividad permanece disponible después, si necesita profundizar."
    )


def mostrar_resumen_integral(resultados):
    """Presenta la decisión integrada sin obligar a interpretar capas técnicas."""

    visita = resultados.get("prioridad_visita")
    if not visita:
        mostrar_resumen_ejecutivo(resultados)
        return

    prioridad = visita["prioridad_visita"]
    color = {
        "Muy alta": "#7f0000",
        "Alta": "#b71c1c",
        "Media": "#a33a00",
        "Preventiva": "#8a5b00",
        "Baja": "#2e7d32",
    }[prioridad]
    recomendacion = texto_recomendacion_visita(prioridad)
    corredores = resultados.get("corredores") or {}
    fragmentacion = resultados.get("fragmentacion") or {}
    clase = fragmentacion.get("metricas_clase") or {}
    estructura = visita["contexto_estructural"]
    consistencia = resultados.get("consistencia") or {}

    cambios_senalados_ha = sum(
        float(resultados.get(clave, 0) or 0)
        for clave in (
            "coincidencia_1_fuente",
            "coincidencia_2_fuentes",
            "coincidencia_3_fuentes",
        )
    )
    fuentes_con_senal = sum(
        bool(resultados.get(clave))
        for clave in ("senal_tmf", "senal_hansen", "senal_esri")
    )
    area_corredor_ha = float(corredores.get("area_en_corredores_ha", 0) or 0)
    porcentaje_corredor = float(
        corredores.get("porcentaje_aoi_en_corredores", 0) or 0
    )
    bosque_ha = float(clase.get("area_total_bosque_ha", 0) or 0)
    porcentaje_bosque = float(clase.get("porcentaje_paisaje_bosque", 0) or 0)

    st.markdown(
        f"""
        <div class="resultado-prioridad" style="--prioridad-color:{color};">
          <small>Conclusión integrada</small>
          <strong>Prioridad {html_lib.escape(prioridad.lower())} de visita</strong>
          <p>{html_lib.escape(recomendacion)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="resultado-fuente">
          <b>Dónde empezar</b><br/>
          {html_lib.escape(visita['foco_visita'])}<br/>
          <small>{html_lib.escape(visita['combinacion_territorial'])}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cambios, col_corredor, col_bosque, col_estructura = st.columns(4)
    col_cambios.metric(
        "Cambios señalados",
        f"{cambios_senalados_ha:,.2f} ha",
        f"{fuentes_con_senal} de 3 fuentes principales",
        delta_color="off",
    )
    col_corredor.metric(
        "Dentro de corredores",
        f"{area_corredor_ha:,.1f} ha",
        f"{porcentaje_corredor:.1f}% del área",
        delta_color="off",
    )
    if fragmentacion:
        col_bosque.metric(
            f"Bosque {ANO_BOSQUE_REFERENCIA}",
            f"{bosque_ha:,.1f} ha",
            f"{porcentaje_bosque:.1f}% del área",
            delta_color="off",
        )
    else:
        col_bosque.metric(f"Bosque {ANO_BOSQUE_REFERENCIA}", "No disponible")
    col_estructura.metric(
        "Conectividad del bosque",
        estructura["estado"],
        f"Consistencia satelital: {consistencia.get('nivel', 'No disponible')}",
        delta_color="off",
    )

    razon_cambios = (
        f"La evidencia territorial produjo una prioridad {resultados['prioridad'].lower()} "
        f"y una consistencia {str(consistencia.get('nivel', 'no disponible')).lower()}."
    )
    razon_corredor = (
        f"El área coincide con {area_corredor_ha:,.1f} ha de corredores publicados."
        if corredores.get("intersecta")
        else "No se identificó una coincidencia directa con los corredores publicados."
    )
    razon_estructura = estructura.get(
        "interpretacion",
        "La estructura del bosque no estuvo disponible para esta ejecución.",
    )
    st.markdown("#### Por qué se obtuvo este resultado")
    st.markdown(
        "\n".join(
            [
                f"- {razon_cambios}",
                f"- {razon_corredor}",
                f"- {razon_estructura}",
            ]
        )
    )
    st.caption(
        "El mapa siguiente ya está preparado con la evidencia principal. Abra los "
        "detalles o personalice las capas solo si necesita profundizar."
    )


def mostrar_resumen_conectividad(resultados):
    corredores = resultados.get("corredores") or {}
    fragmentacion = resultados.get("fragmentacion") or {}
    clase = fragmentacion.get("metricas_clase") or {}
    red = fragmentacion.get("metricas_red") or {}
    conexion = fragmentacion.get("conexion_corredor") or {}

    if conexion.get("conecta"):
        titulo = "Se identificó una conexión estructural potencial hacia un corredor"
        detalle = (
            "La cadena de fragmentos respeta la distancia configurada. Representa una "
            "posibilidad estructural que debe contrastarse con especies, campo y uso del suelo."
        )
    elif corredores.get("intersecta"):
        titulo = "El área coincide con corredores publicados"
        detalle = (
            "La superposición aporta contexto estratégico, aunque no se identificó una "
            "cadena completa de fragmentos hacia el corredor con los parámetros actuales."
        )
    else:
        titulo = "No se identificó contacto directo con los corredores publicados"
        detalle = (
            "Revise los fragmentos separados y el bosque del entorno para reconocer "
            "oportunidades de continuidad fuera del área seleccionada."
        )

    st.markdown(
        f"""
        <div class="resultado-prioridad" style="--prioridad-color:#00544d;">
          <small>Lectura de corredores y conectividad</small>
          <strong>{html_lib.escape(titulo)}</strong>
          <p>{html_lib.escape(detalle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_corredor, col_bosque, col_parches, col_separados = st.columns(4)
    col_corredor.metric(
        "Dentro de corredores",
        f"{float(corredores.get('area_en_corredores_ha', 0)):,.1f} ha",
        f"{float(corredores.get('porcentaje_aoi_en_corredores', 0)):.1f}% del área",
        delta_color="off",
    )
    if fragmentacion:
        col_bosque.metric(
            f"Bosque {ANO_BOSQUE_REFERENCIA}",
            f"{float(clase.get('area_total_bosque_ha', 0)):,.1f} ha",
            f"{float(clase.get('porcentaje_paisaje_bosque', 0)):.1f}% del área",
            delta_color="off",
        )
        col_parches.metric(
            "Fragmentos evaluados",
            f"{int(clase.get('numero_parches', 0)):,}",
        )
        col_separados.metric(
            "Fragmentos separados",
            f"{int(red.get('numero_parches_aislados', 0)):,}",
            f"Distancia: {float(red.get('umbral_m', 0)):,.0f} m",
            delta_color="off",
        )
    else:
        col_bosque.metric(f"Bosque {ANO_BOSQUE_REFERENCIA}", "No disponible")
        col_parches.metric("Fragmentos evaluados", "No disponible")
        col_separados.metric("Fragmentos separados", "No disponible")
        st.warning(
            "La cobertura institucional de bosque no estuvo disponible. La lectura de "
            "corredores permanece válida, pero no debe interpretarse como un resultado "
            "completo de conectividad."
        )
    st.caption(
        "Este modo describe contexto espacial y conectividad estructural. No calcula "
        "una prioridad de deforestación ni confirma conectividad funcional para una especie."
    )


def mostrar_resultados(
    resultados,
    anio_tmf_diagnostico,
    anio_esri_inicial,
    anio_esri_final,
):
    prioridad_cambios = resultados["prioridad"]
    visita = resultados.get("prioridad_visita")
    prioridad = (
        visita["prioridad_visita"] if visita else prioridad_cambios
    )
    recomendacion_resultado = (
        texto_recomendacion_visita(prioridad)
        if visita
        else texto_recomendacion(prioridad)
    )
    color = {
        "Muy alta": "#7f0000",
        "Alta": "#b71c1c",
        "Media": "#a33a00",
        "Preventiva": "#8a5b00",
        "Baja": "#2e7d32",
    }[prioridad]
    fuentes_principales = sum(
        bool(resultados[clave])
        for clave in ("senal_tmf", "senal_hansen", "senal_esri")
    )
    if fuentes_principales == 0 and resultados["senal_ndvi"]:
        titulo_hallazgo = "NDVI presenta una disminución significativa"
        detalle_hallazgo = (
            f"La disminución ocupa {resultados['ndvi_disminucion']:.2f} ha "
            f"({resultados['pct_ndvi_disminucion']:.1f}% del área). Es una señal "
            "corroborativa que requiere contraste con cobertura, clima e imágenes recientes."
        )
        titulo_ubicacion = "Revise la capa de cambio del vigor vegetal"
        detalle_ubicacion = (
            "Una señal NDVI aislada no confirma pérdida de bosque ni identifica su causa."
        )
    elif fuentes_principales == 0:
        titulo_hallazgo = "Sin señales principales que eleven la prioridad"
        detalle_hallazgo = (
            "JRC, ESRI y Hansen no superaron los umbrales operativos definidos para esta área."
        )
        titulo_ubicacion = "No hay un sector prioritario confirmado"
        detalle_ubicacion = (
            "Aun así, revise el mapa si necesita documentar la condición actual del predio."
        )
    elif fuentes_principales == 1:
        titulo_hallazgo = "Una fuente principal presenta una señal"
        detalle_hallazgo = (
            "Conviene contrastarla con los demás mapas y con información del predio antes de interpretarla."
        )
        titulo_ubicacion = "Revise primero las zonas resaltadas"
        detalle_ubicacion = (
            "El mapa permite ubicar la señal; su color no establece automáticamente la causa del cambio."
        )
    else:
        titulo_hallazgo = f"{fuentes_principales} fuentes principales presentan señales"
        detalle_hallazgo = (
            "La necesidad de revisión aumenta. El mapa de coincidencia permite comprobar "
            "si las señales también se superponen espacialmente."
        )
        titulo_ubicacion = "Priorice los sectores señalados en varios mapas"
        detalle_ubicacion = (
            "Compare la ubicación visual y luego confróntela con imágenes recientes y documentos del predio."
        )
    if resultados["coincidencia_varias_fuentes"] > 0:
        titulo_ubicacion = (
            f"Revise primero {resultados['coincidencia_varias_fuentes']:.2f} ha "
            "con coincidencia espacial"
        )
        detalle_ubicacion = (
            "Active «Sectores que requieren revisión»: naranja indica dos fuentes "
            "y rojo oscuro tres. Después confronte esos lugares con imágenes "
            "recientes y documentos del predio."
        )
    elif resultados["coincidencia_1_fuente"] > 0:
        titulo_ubicacion = "Hay señales localizadas, pero ninguna coincide espacialmente"
        detalle_ubicacion = (
            "El séptimo mapa las muestra en amarillo como señales de una sola "
            "fuente. Revise cada producto y mantenga una interpretación cautelosa."
        )
    elif resultados["senal_ndvi"]:
        titulo_ubicacion = "La señal NDVI se consulta en su mapa específico"
        detalle_ubicacion = (
            "No aparece en el mapa de coincidencia JRC–Hansen–ESRI. Consulte ΔNDVI "
            "para localizar la disminución y contrastarla con imágenes recientes."
        )
    else:
        titulo_ubicacion = "No se delimitaron sectores en el mapa de coincidencia"
        detalle_ubicacion = (
            "No se detectaron píxeles con las tres señales espaciales definidas. "
            "Consulte los mapas individuales si necesita documentar el área."
        )
    if visita:
        estructura = visita["contexto_estructural"]
        detalle_resultado = (
            f"Resultado integrado · cambios {visita['puntaje_cambios']:.1f}/"
            f"{PUNTAJE_MAXIMO:.1f} + corredor {visita['aporte_corredor']:.2f}/"
            f"{REGLAS_PRIORIDAD_VISITA['aporte_maximo_corredor']:.1f} · "
            f"estructura: {estructura['estado']}"
        )
        titulo_ubicacion = visita["combinacion_territorial"]
        detalle_ubicacion = f"{visita['foco_visita']} {detalle_ubicacion}"
    else:
        detalle_resultado = (
            f"Índice operativo {resultados['puntaje']:.1f}/{PUNTAJE_MAXIMO:.1f}"
        )
    st.markdown(
        f"""
        <div class="resultado-prioridad" style="--prioridad-color:{color};">
          <small>{html_lib.escape(detalle_resultado)}</small>
          <strong>Prioridad {prioridad.lower()} de visita</strong>
          <p>{html_lib.escape(recomendacion_resultado)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if visita:
        col_cambios, col_corredor, col_estructura, col_final = st.columns(4)
        col_cambios.metric(
            "Urgencia por cambios",
            prioridad_cambios,
            f"{visita['puntaje_cambios']:.1f} de {PUNTAJE_MAXIMO:.1f}",
            delta_color="off",
        )
        col_corredor.metric(
            "Valor estratégico del corredor",
            visita["valor_corredor"],
            f"+{visita['aporte_corredor']:.2f} puntos",
            delta_color="off",
        )
        detalle_estructura = (
            f"{estructura['numero_componentes']} componentes · "
            f"{estructura['porcentaje_componente_mayor']:.1f}% en la red mayor"
            if estructura["disponible"]
            else "Cargue la cobertura 2021"
        )
        col_estructura.metric(
            "Condición estructural 2021",
            estructura["estado"],
            detalle_estructura,
            delta_color="off",
        )
        col_final.metric(
            "Prioridad integrada",
            prioridad,
            f"{visita['puntaje_integrado']:.2f} de {PUNTAJE_MAXIMO_VISITA:.1f}",
            delta_color="off",
        )
        st.caption(
            "Las señales recientes determinan la urgencia; el corredor aumenta el "
            "valor estratégico; y la estructura del bosque 2021 orienta dónde "
            "concentrar la visita. La estructura no suma puntos hasta contar con "
            "umbrales ecológicos calibrados."
        )
        st.markdown(
            f"""
            <div class="resultado-fuente">
              <b>{html_lib.escape(visita['combinacion_territorial'])}</b><br/>
              {html_lib.escape(visita['foco_visita'])}<br/>
              <small>{html_lib.escape(estructura['interpretacion'])}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    aportes = resultados["aportes_indice"]
    st.markdown("#### Evidencia de cambio territorial")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("JRC TMF", f"{aportes['tmf']:.1f} / {PESOS_INDICE['tmf']:.1f}")
    c2.metric("Hansen GFC", f"{aportes['hansen']:.1f} / {PESOS_INDICE['hansen']:.1f}")
    c3.metric("ESRI LULC", f"{aportes['esri']:.1f} / {PESOS_INDICE['esri']:.1f}")
    c4.metric("GEDI", f"{aportes['gedi']:.1f} / {PESOS_INDICE['gedi']:.1f}")
    c5.metric("NDVI", f"{aportes['ndvi']:.1f} / {PESOS_INDICE['ndvi']:.1f}")
    st.caption(
        "Cada fuente puede sumar una sola vez. JRC y Hansen tienen el mayor peso "
        "(2.0 cada uno); ESRI aporta como máximo 1.5, GEDI 0.5 y NDVI 0.5."
    )
    consistencia = resultados["consistencia"]
    fuentes_deterioro = ", ".join(consistencia["fuentes_deterioro"]) or "ninguna"
    fuentes_recuperacion = (
        ", ".join(consistencia["fuentes_recuperacion"]) or "ninguna"
    )
    st.markdown(
        f"""
        <div class="resultado-fuente">
          <b>Consistencia entre fuentes: {html_lib.escape(consistencia['nivel'])}</b><br/>
          {html_lib.escape(consistencia['detalle'])}<br/>
          <small>Señales de deterioro: {html_lib.escape(fuentes_deterioro)} ·
          Regeneración forestal o ganancia: {html_lib.escape(fuentes_recuperacion)}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Lectura rápida")
    st.markdown(
        f"""
        <div class="lectura-rapida" aria-label="Interpretación resumida del resultado">
          <div class="lectura-tarjeta">
            <small>Qué se detectó</small>
            <b>{html_lib.escape(titulo_hallazgo)}</b>
            <p>{html_lib.escape(detalle_hallazgo)}</p>
          </div>
          <div class="lectura-tarjeta">
            <small>Dónde mirar</small>
            <b>{html_lib.escape(titulo_ubicacion)}</b>
            <p>{html_lib.escape(detalle_ubicacion)}</p>
          </div>
          <div class="lectura-tarjeta">
            <small>Qué hacer después</small>
            <b>Documente la revisión</b>
            <p>{html_lib.escape(recomendacion_resultado)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    area = resultados["area_ha"]
    resumen, detalle = st.tabs(["Resumen para decidir", "Evidencia por fuente"])
    with resumen:
        st.markdown(
            "**¿Qué significa?** La prioridad sirve para decidir dónde conviene revisar "
            "imágenes, documentos o realizar una visita. No demuestra por sí sola la causa del cambio."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Deforestación JRC", f"{resultados['tmf_deforestacion']:.1f} ha")
        c2.metric("Pérdida Hansen post-2020", f"{resultados['hansen_post']:.2f} ha")
        c3.metric(
            "Salida de árboles ESRI",
            f"{resultados['esri_salida']:.1f} ha",
            f"{resultados['pct_esri_salida']:.1f}% del área",
            delta_color="off",
        )
        c4.metric(
            "Altura media GEDI",
            (
                f"{resultados['gedi_altura']:.1f} m"
                if resultados["gedi_disponible"]
                else "Datos insuficientes"
            ),
        )
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Disminución significativa NDVI",
            f"{resultados['ndvi_disminucion']:.2f} ha",
            f"{resultados['pct_ndvi_disminucion']:.1f}% del área",
            delta_color="off",
        )
        c2.metric(
            f"ΔNDVI medio {ANO_NDVI_INICIAL_ANALISIS}-{ANO_NDVI_FINAL_ANALISIS}",
            f"{resultados['ndvi_delta_medio']:+.3f}",
        )
        c3.metric(
            "Cobertura válida NDVI",
            f"{resultados['ndvi_cobertura_pct']:.0f}%",
        )
        st.info(
            f"Mapa «Sectores que requieren revisión»: "
            f"{resultados['coincidencia_1_fuente']:.2f} ha con señal de una fuente; "
            f"{resultados['coincidencia_2_fuentes']:.2f} ha con dos fuentes; "
            f"{resultados['coincidencia_3_fuentes']:.2f} ha con tres fuentes. "
            "Priorice las coincidencias de dos o tres fuentes. Este mapa no modifica "
            "el índice y no confirma por sí solo la causa del cambio."
        )
        st.markdown(f"**Acción sugerida:** {recomendacion_resultado}")

    filas = [
        (
            f"Mapa forestal JRC {anio_tmf_diagnostico}",
            f"Deforestación {resultados['tmf_deforestacion']:.1f} ha; "
            f"degradación {resultados['tmf_degradacion']:.1f} ha · "
            f"aporte {aportes['tmf']:.1f}/{PESOS_INDICE['tmf']:.1f}",
            resultados["senal_tmf"],
        ),
        (
            "Pérdida arbórea Hansen",
            f"Pérdida post-{CUTOFF_LABEL}: {resultados['hansen_post']:.2f} ha · "
            f"aporte {aportes['hansen']:.1f}/{PESOS_INDICE['hansen']:.1f}",
            resultados["senal_hansen"],
        ),
        (
            f"Transiciones ESRI {anio_esri_inicial} → {anio_esri_final}",
            f"Árboles → no árbol: {resultados['esri_salida']:.1f} ha "
            f"({resultados['pct_esri_salida']:.1f}%) · "
            f"aporte {aportes['esri']:.1f}/{PESOS_INDICE['esri']:.1f}",
            resultados["senal_esri"],
        ),
        (
            "Altura del dosel GEDI",
            (
                f"Dosel {resultados['gedi_altura']:.1f} m; "
                f"{resultados['gedi_cobertura_pct']:.0f}% del área con datos válidos · "
                f"aporte {aportes['gedi']:.1f}/{PESOS_INDICE['gedi']:.1f}"
                if resultados["gedi_disponible"]
                else "Sin datos válidos suficientes; aporte 0.0/0.5"
            ),
            resultados["senal_gedi"],
        ),
        (
            "ΔNDVI Sentinel-2",
            f"Disminución desde vegetación inicial moderada: "
            f"{resultados['ndvi_disminucion']:.2f} ha "
            f"({resultados['pct_ndvi_disminucion']:.1f}%) · "
            f"Δ medio {resultados['ndvi_delta_medio']:+.3f} · "
            f"aporte {aportes['ndvi']:.1f}/{PESOS_INDICE['ndvi']:.1f}",
            resultados["senal_ndvi"],
        ),
    ]
    with detalle:
        st.markdown("**Estadísticas territoriales y forestales**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Área evaluada", f"{resultados['area_ha']:.1f} ha")
        c2.metric(
            "Cobertura arbórea persistente a 2020",
            f"{resultados['linea_base']:.1f} ha",
            f"{resultados['pct_linea_base']:.1f}% del área",
            delta_color="off",
        )
        c3.metric("Pérdida Hansen 2001-2020", f"{resultados['hansen_pre']:.2f} ha")
        c4.metric("Pérdida Hansen post-2020", f"{resultados['hansen_post']:.2f} ha")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Bosque no perturbado JRC", f"{resultados['tmf_estable']:.1f} ha")
        c2.metric("Degradación JRC", f"{resultados['tmf_degradacion']:.1f} ha")
        c3.metric("Deforestación JRC", f"{resultados['tmf_deforestacion']:.1f} ha")
        c4.metric("Regeneración forestal JRC", f"{resultados['tmf_recuperacion']:.1f} ha")
        for titulo, texto_detalle, alerta in filas:
            estado = "SEÑAL" if alerta else "SIN SEÑAL OPERATIVA"
            color_texto = "#c62828" if alerta else "#2e7d32"
            st.markdown(
                f'<div class="resultado-fuente"><b style="color:{color_texto};">'
                f"{estado} · {titulo}</b><br/>{texto_detalle}</div>",
                unsafe_allow_html=True,
            )
        st.caption("Use el menú de cada gráfico para guardarlo como imagen o descargar sus datos.")
        grafico_jrc, grafico_esri = st.columns(2)
        with grafico_jrc:
            st.markdown("**Distribución del estado forestal JRC**")
            st.altair_chart(
                crear_grafica_barras_color(
                    {
                        "eje_x": "Clase",
                        "eje_y": "Hectáreas",
                        "unidad": "ha",
                        "colores": [
                            "#2E7D32",
                            "#F2A541",
                            "#C73E3A",
                            "#43AA8B",
                            "#4D9DE0",
                            "#A8B3B0",
                        ],
                        "datos": {
                            "Clase": [
                                "Bosque no perturbado",
                                "Bosque degradado",
                                "Tierra deforestada",
                                "Regeneración forestal",
                                "Agua",
                                "Otra cobertura",
                            ],
                            "Hectáreas": [
                                resultados["tmf_estable"],
                                resultados["tmf_degradacion"],
                                resultados["tmf_deforestacion"],
                                resultados["tmf_recuperacion"],
                                resultados["tmf_agua"],
                                resultados["tmf_otra_cobertura"],
                            ],
                        },
                    },
                    altura=300,
                ),
                use_container_width=True,
                theme=None,
                key="detalle_jrc_barras_color",
            )
        with grafico_esri:
            st.markdown("**Cambios de la clase árboles ESRI**")
            st.altair_chart(
                crear_grafica_barras_color(
                    {
                        "eje_x": "Clase",
                        "eje_y": "Hectáreas",
                        "unidad": "ha",
                        "colores": ["#2E7D32", "#E76F51", "#9BBF30"],
                        "datos": {
                            "Clase": [
                                "Árboles estables",
                                "Salida de árboles",
                                "Ganancia de árboles",
                            ],
                            "Hectáreas": [
                                resultados["esri_estable"],
                                resultados["esri_salida"],
                                resultados["esri_ganancia"],
                            ],
                        },
                    },
                    altura=220,
                ),
                use_container_width=True,
                theme=None,
                key="detalle_esri_barras_color",
            )
        st.markdown("**Comparación del aporte de las fuentes al índice**")
        st.altair_chart(
            crear_grafica_barras_color(
                {
                    "eje_x": "Fuente",
                    "eje_y": "Aporte",
                    "unidad": "puntos",
                    "colores": [
                        COLORES_FUENTES[fuente]
                        for fuente in [
                            "JRC TMF",
                            "Hansen GFC",
                            "ESRI LULC",
                            "GEDI",
                            "NDVI",
                        ]
                    ],
                    "datos": {
                        "Fuente": [
                            "JRC TMF",
                            "Hansen GFC",
                            "ESRI LULC",
                            "GEDI",
                            "NDVI",
                        ],
                        "Aporte": [
                            aportes["tmf"],
                            aportes["hansen"],
                            aportes["esri"],
                            aportes["gedi"],
                            aportes["ndvi"],
                        ],
                    },
                },
                altura=270,
            ),
            use_container_width=True,
            theme=None,
            key="detalle_aportes_barras_color",
        )
        st.caption(
            "El gráfico representa aportes ponderados, no superficies comparables "
            "píxel a píxel. NDVI es una señal corroborativa y no identifica por sí solo "
            "bosque natural ni la causa del cambio."
        )


def mostrar_resultados_corredores(resultados):
    st.subheader("Contexto de corredores ecológicos")
    columna_estado, columna_area, columna_meso = st.columns(3)
    columna_estado.metric(
        "Intersección con corredores",
        "Sí" if resultados["intersecta"] else "No",
    )
    columna_area.metric(
        "Área dentro de corredores",
        f"{resultados['area_en_corredores_ha']:,.2f} ha",
        f"{resultados['porcentaje_aoi_en_corredores']:.1f}% del área",
    )
    columna_meso.metric(
        "Corredor Mesoamericano",
        "Sí" if resultados["intersecta_mesoamericano"] else "No",
        f"{resultados['area_corredor_mesoamericano_ha']:,.2f} ha",
    )
    st.markdown(
        """
        <div class="corredor-aviso"><strong>Valor estratégico:</strong> esta superposición
        describe el contexto territorial publicado por Almanaque Azul. No modifica el índice
        satelital de cambios; aporta únicamente a la prioridad integrada de visita y no demuestra
        por sí sola conectividad funcional para una especie.</div>
        """,
        unsafe_allow_html=True,
    )
    areas = resultados["areas_categoria_ha"]
    st.markdown(
        " ".join(
            [
                (
                    '<span class="categoria-corredor">'
                    f'{etiqueta}: {areas[clave]:,.2f} ha</span>'
                )
                for clave, etiqueta in (
                    ("alta", "Alta"),
                    ("mediana", "Mediana"),
                    ("mediabaja", "Media-baja"),
                )
            ]
        ),
        unsafe_allow_html=True,
    )
    if resultados["corredores"]:
        tabla = [
            {
                "Corredor": fila["nombre"],
                "Categoría original": fila["categoria_etiqueta"],
                "Intersección (ha)": fila["interseccion_ha"],
                "% del área": fila["porcentaje_aoi"],
                "Mesoamericano": "Sí" if fila["es_mesoamericano"] else "No",
            }
            for fila in resultados["corredores"]
        ]
        st.dataframe(tabla, hide_index=True, use_container_width=True)
    else:
        st.info("El área evaluada no intersecta los polígonos de corredores publicados.")
    st.caption(
        f"Fuente: {resultados['fuente']}. Categorías originales: alta, mediana y media-baja."
    )


def mostrar_resultados_fragmentacion(resultados):
    st.subheader(f"Cómo está distribuido el bosque en {ANO_BOSQUE_REFERENCIA}")
    st.caption(
        f"Fuente de cobertura: {resultados.get('fuente_cobertura', FUENTE_BOSQUE_CORTA)}. "
        "Esta fotografía de cobertura permite observar áreas continuas de bosque; "
        "no representa una serie anual de deforestación."
    )
    clase = resultados["metricas_clase"]
    red = resultados["metricas_red"]
    numero_parches = int(clase["numero_parches"])
    numero_conectados = int(red.get("numero_parches_conectados", 0))
    numero_aislados = int(red.get("numero_parches_aislados", 0))
    numero_continuidad_exterior = int(
        red.get("numero_parches_continuidad_exterior", 0)
    )
    conexion_corredor = resultados.get("conexion_corredor") or {}

    col_bosque, col_fragmentos, col_separados, col_mayor = st.columns(4)
    col_bosque.metric("Bosque identificado", f"{clase['area_total_bosque_ha']:,.2f} ha")
    col_fragmentos.metric(
        "Fragmentos de bosque",
        f"{numero_parches:,}",
        help="Cada fragmento es una superficie continua de bosque dentro del área.",
    )
    col_separados.metric(
        "Fragmentos separados",
        f"{numero_aislados:,}",
        help=(
            f"No tienen otro fragmento a {red['umbral_m']:.0f} m o menos, "
            "considerando también el bosque del entorno exterior."
        ),
    )
    col_mayor.metric(
        "Área ocupada por el fragmento mayor",
        f"{clase['indice_parche_mayor_pct']:.1f}%",
        help="Porcentaje del área total que corresponde al fragmento de bosque más grande.",
    )

    if numero_parches == 0:
        lectura_bosque = (
            "La cobertura institucional de 2021 no identifica parches de bosque "
            "dentro del área seleccionada."
        )
    elif numero_parches == 1:
        lectura_bosque = (
            "El bosque identificado forma un solo fragmento continuo dentro del área. "
            "Por eso no es necesario dibujar relaciones con otros fragmentos."
        )
    else:
        lectura_bosque = (
            f"Se identificaron {numero_parches:,} fragmentos de bosque. Con la distancia "
            f"de referencia de {red['umbral_m']:.0f} m, {numero_conectados:,} están cerca "
            f"de al menos otro fragmento y {numero_aislados:,} aparecen separados. "
            f"En {numero_continuidad_exterior:,} fragmentos se detectó continuidad o una "
            "conexión con bosque exterior. "
            "Esta es una relación espacial; no demuestra por sí sola el movimiento de fauna."
        )

    st.markdown(
        f"""
        <div class="lectura-bosque" role="status">
          <b>Lectura rápida del bosque</b>
          <p>{html_lib.escape(lectura_bosque)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if conexion_corredor.get("conecta"):
        recorrido_exterior = (
            " La cadena continúa por bosque exterior al polígono."
            if conexion_corredor.get("cruza_fuera_area")
            else ""
        )
        st.success(
            f"Conexión estructural potencial hacia «{conexion_corredor['corredor_nombre']}» "
            f"(categoría {str(conexion_corredor['categoria_etiqueta']).lower()}). "
            f"La ruta enlaza {conexion_corredor['numero_fragmentos_ruta']:,} fragmentos; "
            f"su mayor separación es {conexion_corredor['mayor_separacion_m']:,.1f} m "
            f"y no supera el umbral de {red['umbral_m']:,.0f} m.{recorrido_exterior} "
            "Es una posibilidad estructural, no evidencia de movimiento de fauna."
        )
    elif conexion_corredor.get("evaluada"):
        st.info(
            f"No se encontró una cadena continua de fragmentos hacia un corredor publicado "
            f"dentro de {conexion_corredor.get('radio_busqueda_m', 0) / 1000:,.0f} km, "
            f"exigiendo que cada salto fuera de {red['umbral_m']:,.0f} m o menos."
        )
    with st.expander("Entender esta lectura", expanded=False):
        st.markdown(
            f"""
            - **Fragmento de bosque:** superficie continua de bosque dentro del área elegida.
            - **Fragmentos cercanos:** sus bordes están separados por {red['umbral_m']:.0f} m o menos.
            - **Fragmento separado:** no tiene otro fragmento dentro de esa distancia,
              ni dentro ni en el entorno exterior evaluado.
            - **Contexto exterior:** se revisa hasta {resultados.get('distancia_contexto_m', red['umbral_m']) / 1000:.1f} km
              alrededor del polígono para buscar la conexión con un corredor. Un fragmento
              solo se enlaza con otro si sus bordes están a {red['umbral_m']:.0f} m o menos.
              El bosque exterior participa en la red, pero no se suma a las hectáreas reportadas.

            La red completa se usa en las métricas. Para no llenar el mapa, la capa de estructura
            esencial dibuja únicamente los enlaces mínimos que mantienen unido cada grupo.
            Las líneas no son caminos de animales ni corredores ecológicos confirmados.
            """
        )

    detalle_tecnico = st.expander("Ver detalle técnico y descargas", expanded=False)
    red_tab, paisaje_tab, conectores_tab, descarga_tab = detalle_tecnico.tabs(
        [
            "Cercanía entre fragmentos",
            "Estructura del bosque",
            "Fragmentos relevantes",
            "Descargas",
        ]
    )
    with red_tab:
        st.dataframe(
            [
                {"Métrica": "Fragmentos cercanos a otro", "Valor": f"{numero_conectados:,}"},
                {"Métrica": "Fragmentos separados", "Valor": f"{numero_aislados:,}"},
                {"Métrica": "Fragmentos con continuidad o conexión exterior", "Valor": f"{numero_continuidad_exterior:,}"},
                {"Métrica": "Grupos de fragmentos", "Valor": f"{red['numero_componentes']:,}"},
                {"Métrica": "Relaciones de cercanía calculadas", "Valor": f"{red['numero_aristas']:,}"},
                {"Métrica": "Enlaces esenciales mostrados en el mapa", "Valor": f"{red.get('numero_relaciones_mostradas', 0):,}"},
                {"Métrica": "Separación media", "Valor": f"{red.get('distancia_media_conexiones_m', 0):,.1f} m"},
                {"Métrica": "Separación máxima", "Valor": f"{red.get('distancia_maxima_conexiones_m', 0):,.1f} m"},
                {"Métrica": "Separaciones potenciales para revisar", "Valor": f"{red.get('numero_brechas_potenciales', 0):,}"},
                {"Métrica": "Densidad de la red", "Valor": f"{red['densidad_red']:.6f}"},
                {"Métrica": "Distancia usada para considerar cercanía", "Valor": f"{red['umbral_m']:.0f} m"},
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "La tabla cuenta todas las relaciones utilizadas en el cálculo. El mapa dibuja "
            "solo una estructura mínima sin enlaces redundantes; no representa rutas confirmadas."
        )
        if conexion_corredor.get("evaluada"):
            st.dataframe(
                [
                    {
                        "Conexión hacia corredor": conexion_corredor.get("tipo"),
                        "Corredor de referencia": conexion_corredor.get("corredor_nombre") or "No alcanzado",
                        "Categoría publicada": conexion_corredor.get("categoria_etiqueta") or "—",
                        "Fragmentos en la cadena": conexion_corredor.get("numero_fragmentos_ruta", 0),
                        "Mayor salto": (
                            f"{conexion_corredor['mayor_separacion_m']:,.1f} m"
                            if conexion_corredor.get("mayor_separacion_m") is not None
                            else "—"
                        ),
                        "Usa bosque exterior": "Sí" if conexion_corredor.get("cruza_fuera_area") else "No",
                    }
                ],
                hide_index=True,
                use_container_width=True,
            )
    with paisaje_tab:
        st.dataframe(
            [
                {"Métrica": "Bosque en el paisaje", "Valor": f"{clase['porcentaje_paisaje_bosque']:.2f}%"},
                {"Métrica": "Densidad de fragmentos", "Valor": f"{clase['densidad_parches_por_100ha']:.3f} por 100 ha"},
                {"Métrica": "Densidad de borde", "Valor": f"{clase['densidad_borde_m_ha']:.2f} m/ha"},
                {"Métrica": "Área media por fragmento", "Valor": f"{clase['area_media_parche_ha']:.2f} ha"},
                {"Métrica": "Área mediana por fragmento", "Valor": f"{clase['area_mediana_parche_ha']:.2f} ha"},
                {"Métrica": "Área ocupada por el fragmento mayor", "Valor": f"{clase['indice_parche_mayor_pct']:.2f}%"},
            ],
            hide_index=True,
            use_container_width=True,
        )
    with conectores_tab:
        if resultados["top_conectores"]:
            st.dataframe(
                resultados["top_conectores"],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "patch_id": "Fragmento",
                    "area_ha": st.column_config.NumberColumn("Área (ha)", format="%.2f"),
                    "indice_conector": st.column_config.NumberColumn("Puntaje técnico", format="%.3f"),
                    "prioridad_conectividad": "Valor para mantener unido el bosque",
                    "grado": "Fragmentos cercanos",
                    "componente": "Grupo",
                    "esta_aislado": "Separado",
                    "distancia_vecino_mas_cercano_m": st.column_config.NumberColumn(
                        "Vecino más cercano (m)", format="%.1f"
                    ),
                },
                column_order=[
                    "patch_id",
                    "area_ha",
                    "prioridad_conectividad",
                    "indice_conector",
                    "grado",
                    "componente",
                    "esta_aislado",
                    "distancia_vecino_mas_cercano_m",
                ],
            )
        else:
            st.info(
                "La cobertura institucional de 2021 no identifica parches de bosque "
                "dentro del área seleccionada."
            )
    with descarga_tab:
        red_geojson = {
            "type": "FeatureCollection",
            "features": (
                resultados.get("conexiones_geojson", {}).get("features", [])
                + resultados.get("conexiones_potenciales_geojson", {}).get("features", [])
                + resultados.get("ruta_corredor_geojson", {}).get("features", [])
            ),
        }
        col_descarga_parches, col_descarga_red = st.columns(2)
        col_descarga_parches.download_button(
            "Descargar fragmentos y métricas (GeoJSON)",
            data=json.dumps(resultados["parches_geojson"], ensure_ascii=False),
            file_name=f"parches_bosque_{ANO_BOSQUE_REFERENCIA}.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )
        col_descarga_red.download_button(
            "Descargar estructura y ruta potencial (GeoJSON)",
            data=json.dumps(red_geojson, ensure_ascii=False),
            file_name=f"red_conectividad_bosque_{ANO_BOSQUE_REFERENCIA}.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )
    detalle_tecnico.caption(
        "El valor alto, medio o bajo se calcula comparando los fragmentos dentro del área "
        "analizada. No corresponde a las categorías de Almanaque Azul y no modifica por sí "
        "solo el puntaje de prioridad; ayuda a orientar la revisión espacial."
    )


# -----------------------------------------------------------------------------
# Aplicación
# -----------------------------------------------------------------------------

modo_analisis = st.session_state.get("modo_analisis")
seccion_tablero = (
    "Análisis" if st.session_state.get("mostrar_resultados", False) else "Mapa"
)
if modo_analisis not in MODOS_ANALISIS:
    st.session_state.pop("modo_analisis", None)
    modo_analisis = None

if modo_analisis is None:
    st.markdown(
        """
        <div class="cabecera-app">
          <h1>Preevaluación territorial y corredores</h1>
          <div class="subtitulo-app">Evidencia inicial para orientar dónde conviene revisar</div>
          <p>Primero elija qué necesita conocer. Después seleccione una finca, una
          subcuenca, un polígono o toda la cuenca.</p>
          <div class="alcance-app">Resultado indicativo · requiere interpretación y
          verificación de campo · no determina cumplimiento EUDR</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    mostrar_flujo(1)
    mostrar_selector_modos()
    st.sidebar.info("Empiece eligiendo el enfoque de preevaluación en la página principal.")
    st.stop()

contenido_modo = MODOS_ANALISIS[modo_analisis]
analiza_cambios = modo_analisis in (MODO_TERRITORIAL, MODO_INTEGRAL)
analiza_conectividad = modo_analisis in (MODO_CORREDORES, MODO_INTEGRAL)

try:
    iniciar_earth_engine()

    panel_capas, panel_filtros, panel_mapa_base = st.sidebar.tabs(
        ["Capas", "Polígono", "Mapa base"]
    )
    acciones_sidebar = st.sidebar.container(key="acciones_sidebar")

    mapa_base = panel_mapa_base.selectbox(
        "Fondo cartográfico",
        list(MAPAS_BASE),
        help="Cambia únicamente el fondo de referencia; no modifica los cálculos.",
    )
    panel_mapa_base.caption(
        "Use imagen satelital para inspección visual y mapa claro cuando necesite "
        "distinguir mejor las capas temáticas."
    )

    panel_filtros.markdown("### Área de análisis")
    if panel_filtros.button(
        "Cambiar enfoque",
        use_container_width=True,
        key="cambiar_enfoque_sidebar",
        help="Volver a la selección de preevaluación territorial, conectividad o análisis integral.",
    ):
        limpiar_estado_resultados()
        st.session_state.pop("modo_analisis", None)
        st.session_state["mostrar_resultados"] = False
        st.rerun()
    etiquetas_area = {
        "Finca de monitoreo": "Finca registrada (recomendado)",
        "Subcuenca": "Subcuenca de la CHCP",
        "Dibujar polígono en el mapa": "Dibujar un área en el mapa",
        "Toda la cuenca": "Toda la cuenca (análisis regional)",
    }
    descripciones_area = {
        "Finca de monitoreo": "Seleccione una finca registrada.",
        "Subcuenca": "Se recorta automáticamente al límite de la CHCP.",
        "Dibujar polígono en el mapa": "La parte exterior de la CHCP se excluye.",
        "Toda la cuenca": "Análisis regional; puede requerir más tiempo.",
    }
    tipo_area = panel_filtros.selectbox(
        "Unidad territorial",
        ["Finca de monitoreo", "Subcuenca", "Dibujar polígono en el mapa", "Toda la cuenca"],
        format_func=lambda valor: etiquetas_area[valor],
        help="Se recomienda iniciar con una finca. El análisis de toda la cuenca puede tardar varios minutos.",
    )
    panel_filtros.caption(descripciones_area[tipo_area])
    finca_seleccionada = None
    subcuenca_seleccionada = None
    geometria_dibujada_json = st.session_state.get("geometria_dibujada_json")
    version_mapa_dibujo = st.session_state.get("version_mapa_dibujo", 0)
    if tipo_area == "Finca de monitoreo":
        if not solicitar_acceso_fincas(panel_filtros):
            st.info(
                "El acceso a las fincas está protegido. Ingrese el código en el panel lateral "
                "o seleccione otra unidad territorial."
            )
            st.stop()
        finca_seleccionada = panel_filtros.selectbox(
            "Finca:",
            obtener_ids_fincas(),
            format_func=str,
            help="Las fincas están ordenadas de forma natural: 1, 2, 3...",
        )
    elif tipo_area == TIPO_AREA_SUBCUENCA:
        subcuenca_seleccionada = panel_filtros.selectbox(
            "Subcuenca:",
            obtener_ids_subcuencas(),
            format_func=str,
            help=(
                "Seleccione una de las subcuencas incluidas en la aplicación. "
                "Esta geometría ya no depende de un asset privado de Earth Engine."
            ),
        )
    elif tipo_area == TIPO_AREA_DIBUJADA:
        st.subheader("1. Dibuje el área que desea preevaluar")
        st.markdown(
            "Seleccione la herramienta de polígono en el mapa, marque los vértices y "
            "haga clic en el primer punto para cerrar la figura. El área se limitará "
            "automáticamente a la cuenca hidrográfica."
        )
        if geometria_dibujada_json and st.button("Borrar polígono y dibujar otro"):
            st.session_state.pop("geometria_dibujada_json", None)
            st.session_state.pop("resultados_analisis", None)
            st.session_state.pop("pdf_analisis", None)
            st.session_state.pop("firma_analisis", None)
            st.session_state.pop("errores_mapas", None)
            st.session_state["version_mapa_dibujo"] = version_mapa_dibujo + 1
            st.rerun()

        mapa_dibujo = folium.Map(
            location=[8.7, -80.0],
            zoom_start=8,
            tiles=None,
            control_scale=True,
        )
        agregar_mapa_base(mapa_dibujo, mapa_base, control=False)
        agregar_limite_cuenca_local(mapa_dibujo, control=False)
        if geometria_dibujada_json:
            folium.GeoJson(
                json.loads(geometria_dibujada_json),
                name="Polígono dibujado",
                style_function=lambda _: {
                    "color": "#D0442C",
                    "weight": 2.6,
                    "fillColor": "#D0442C",
                    "fillOpacity": 0.08,
                },
            ).add_to(mapa_dibujo)
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
                    "shapeOptions": {"color": "#D0442C", "weight": 2.6},
                },
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(mapa_dibujo)
        mapa_dibujo.fit_bounds(obtener_limites_geojson(coleccion_cuenca()))
        resultado_dibujo = st_folium(
            mapa_dibujo,
            height=520,
            use_container_width=True,
            returned_objects=["all_drawings"],
            key=f"mapa-seleccion-poligono-{version_mapa_dibujo}",
        )
        dibujos = (resultado_dibujo or {}).get("all_drawings") or []
        if dibujos:
            nuevo_poligono = serializar_poligono_dibujado(dibujos[-1])
            if nuevo_poligono != geometria_dibujada_json:
                st.session_state["geometria_dibujada_json"] = nuevo_poligono
                st.rerun()
        geometria_dibujada_json = st.session_state.get("geometria_dibujada_json")
        if not geometria_dibujada_json:
            st.info("Dibuje un polígono para continuar con la preevaluación.")
            st.stop()
        st.success(
            "Polígono listo. Puede continuar con el tipo de revisión y ejecutar la preevaluación."
        )
    nombre_area = nombre_area_legible(
        tipo_area,
        finca_seleccionada,
        subcuenca_seleccionada,
    )

    area_seleccionada = obtener_area(
        tipo_area,
        finca_seleccionada,
        subcuenca_seleccionada,
        geometria_dibujada_json,
    )
    superficies = obtener_superficies_area_cache(
        tipo_area,
        finca_seleccionada,
        subcuenca_seleccionada,
        geometria_dibujada_json,
    )
    geometria = area_seleccionada.geometry(TOLERANCIA_RECORTE_M)
    superficie_ha = superficies["analizada"]
    superficie_original_ha = superficies["solicitada"]
    if superficie_ha <= 0:
        st.error(
            "El área seleccionada no intersecta la cuenca. Seleccione otra unidad o "
            "dibuje un polígono dentro del límite de la cuenca."
        )
        st.stop()
    superficie_excluida_ha = max(0.0, superficie_original_ha - superficie_ha)
    if area_debe_recortarse_a_cuenca(tipo_area) and superficie_excluida_ha > 0.01:
        panel_filtros.warning(
            f"El área seleccionada sobrepasa el límite de la cuenca. Se excluyeron "
            f"{superficie_excluida_ha:,.1f} ha; el análisis usará únicamente las "
            f"{superficie_ha:,.1f} ha ubicadas dentro de la cuenca."
        )
    elif area_debe_recortarse_a_cuenca(tipo_area):
        panel_filtros.caption(
            "El análisis se limita al área ubicada dentro del límite de la cuenca."
        )

    bosque_automatico_disponible = bool(ASSET_BOSQUE_2021)
    umbral_conectividad_m = 500
    area_min_parche_ha = 0.0
    huella_bosque = (
        hashlib.sha256(
            (
                f"{ASSET_BOSQUE_2021}|{CAMPO_COBERTURA_BOSQUE_2021}|"
                f"{VALOR_COBERTURA_BOSQUE_2021}"
            ).encode("utf-8")
        ).hexdigest()[:16]
        if bosque_automatico_disponible
        else "sin-asset-bosque"
    )
    catalogo_corredores = cargar_catalogo_corredores()

    if analiza_conectividad:
        if not bosque_automatico_disponible:
            panel_filtros.warning(
                "La red de fragmentos no está disponible. Aun puede consultar los "
                "corredores publicados."
            )

        with panel_filtros.expander("Opciones técnicas · opcional", expanded=False):
            st.caption(
                "Conserve los valores recomendados salvo que necesite una lectura técnica."
            )
            umbral_conectividad_m = st.select_slider(
                "Distancia para considerar cercanos dos fragmentos",
                options=[100, 250, 500, 1000, 1500, 3000, 6000],
                value=500,
                format_func=lambda valor: f"{valor:,} m",
                help=(
                    "Dos fragmentos se consideran cercanos cuando la separación entre sus "
                    "bordes no supera esta distancia. El valor recomendado es 500 m."
                ),
            )
            area_min_parche_ha = st.number_input(
                "Tamaño mínimo del fragmento (ha)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help=(
                    "Deje 0 para conservar todos los fragmentos. Aumente el valor únicamente "
                    "si desea excluir áreas muy pequeñas del análisis técnico."
                ),
            )

    with panel_capas.expander("Límites", expanded=True):
        mostrar_limite_cuenca = st.checkbox(
            "Cuenca del Canal",
            value=True,
            help="Límite local incluido con la aplicación; no consulta un asset de Earth Engine.",
        )
        mostrar_subcuencas_local = st.checkbox(
            "Subcuencas del Canal",
            value=False,
            help="Muestra las 53 unidades territoriales incluidas en el portal HTML.",
        )

    panel_capas.markdown("### Capas del mapa")
    opciones_objetivo = PERFILES_POR_MODO[modo_analisis]
    if len(opciones_objetivo) == 1:
        objetivo = opciones_objetivo[0]
        if modo_analisis == MODO_INTEGRAL:
            panel_capas.caption("Vista combinada preparada automáticamente.")
        else:
            panel_capas.markdown(f"**{objetivo}**")
    else:
        objetivo = panel_capas.selectbox(
            "¿Qué desea ver en el mapa?",
            opciones_objetivo,
            help=(
                "Puede consultar capas de un solo año o comparar dos años. "
                "La selección organiza el mapa; no cambia el método de cálculo."
            ),
        )
    perfil = PERFILES_VISUALIZACION[objetivo]
    panel_capas.caption(perfil["descripcion"])

    opciones_capas = [
        "Sectores para revisión",
        "Pérdida Hansen post-2020",
        "Pérdida Hansen 2001-2020",
        "Cobertura arbórea persistente",
        "Estado forestal JRC",
        "Deforestación JRC",
        "Degradación JRC",
        "Regeneración forestal JRC",
        "Uso y cobertura ESRI",
        "Transiciones ESRI",
        "Altura GEDI",
        "ΔNDVI",
        "Vegetación NDVI",
        "ERI indicativo",
    ]
    nombres_capas = {
        "Sectores para revisión": "Sectores que requieren revisión (3 fuentes)",
        "Pérdida Hansen post-2020": "Pérdida de árboles posterior a 2020",
        "Pérdida Hansen 2001-2020": "Pérdida histórica de árboles (2001-2020)",
        "Cobertura arbórea persistente": "Cobertura arbórea persistente hasta 2020",
        "Estado forestal JRC": "Estado forestal de un año (JRC)",
        "Deforestación JRC": "Señales de deforestación (JRC)",
        "Degradación JRC": "Señales de degradación (JRC)",
        "Regeneración forestal JRC": "Regeneración forestal (JRC)",
        "Uso y cobertura ESRI": "Uso y cobertura del suelo (ESRI)",
        "Transiciones ESRI": "Cambios de la clase árboles (ESRI)",
        "Altura GEDI": "Altura del dosel (GEDI)",
        "ΔNDVI": "Cambio del vigor vegetal (ΔNDVI)",
        "Vegetación NDVI": "Vigor vegetal de un año (NDVI)",
        "ERI indicativo": "Resiliencia ecológica indicativa (ERI)",
    }

    modo_comparador = perfil["comparador"]
    capas_activas = list(perfil["capas"])
    modo_mapa = (
        "Comparar años" if modo_comparador != "Sin comparador" else "Explorar capas"
    )
    orden_capas_mapa = list(capas_activas)
    capa_visible_inicial = capas_activas[0] if capas_activas else None
    anio_tmf_inicial, anio_tmf_final = 2020, ANO_TMF_MAX
    anio_esri_inicial, anio_esri_final = ANO_ESRI_MIN, ANO_ESRI_MAX
    anio_ndvi_inicial, anio_ndvi_final = 2022, ANO_NDVI_MAX
    anio_tmf_capa = ANO_TMF_MAX
    anio_esri_capa = ANO_ESRI_MAX
    anio_ndvi_capa = ANO_NDVI_MAX
    mostrar_interseccion_corredores_mapa = False
    mostrar_corredores_contexto_mapa = False
    mostrar_puntos_criticos_mapa = False
    mostrar_fragmentos_bosque = False
    mostrar_bosque_contexto = False
    mostrar_conexiones_bosque = False
    mostrar_brechas_bosque = False
    mostrar_ruta_corredor = False

    if modo_mapa == "Comparar años":
        capas_activas = []
        orden_capas_mapa = []
        capa_visible_inicial = None
        if modo_comparador == "JRC TMF":
            opciones_inicio_tmf = list(range(1990, ANO_TMF_MAX))
            anio_tmf_inicial = panel_filtros.selectbox(
                "Año inicial (JRC):",
                opciones_inicio_tmf,
                index=opciones_inicio_tmf.index(2020),
            )
            opciones_final_tmf = list(range(anio_tmf_inicial + 1, ANO_TMF_MAX + 1))
            anio_tmf_final = panel_filtros.selectbox(
                "Año final (JRC):",
                opciones_final_tmf,
                index=len(opciones_final_tmf) - 1,
            )
            panel_filtros.caption(
                f"Comparación visual. El análisis no resta estos años: clasifica el "
                f"estado JRC de {ANO_DIAG_TMF}."
            )
        elif modo_comparador == "ESRI LULC":
            opciones_inicio_esri = list(range(ANO_ESRI_MIN, ANO_ESRI_MAX))
            anio_esri_inicial = panel_filtros.selectbox(
                "Año inicial (ESRI):",
                opciones_inicio_esri,
            )
            opciones_final_esri = list(range(anio_esri_inicial + 1, ANO_ESRI_MAX + 1))
            anio_esri_final = panel_filtros.selectbox(
                "Año final (ESRI):",
                opciones_final_esri,
                index=len(opciones_final_esri) - 1,
            )
            panel_filtros.caption(
                f"El análisis usa los extremos disponibles {ANO_ESRI_MIN} y "
                f"{ANO_ESRI_MAX}; esta selección solo cambia el comparador."
            )
        else:
            opciones_inicio_ndvi = list(range(2017, ANO_NDVI_MAX))
            anio_ndvi_inicial = panel_filtros.selectbox(
                "Año inicial (NDVI):",
                opciones_inicio_ndvi,
                index=opciones_inicio_ndvi.index(2022),
            )
            opciones_final_ndvi = list(range(anio_ndvi_inicial + 1, ANO_NDVI_MAX + 1))
            anio_ndvi_final = panel_filtros.selectbox(
                "Año final (NDVI):",
                opciones_final_ndvi,
                index=len(opciones_final_ndvi) - 1,
            )
            panel_filtros.caption(
                "Comparación visual de vigor vegetal. El período elegido aquí no cambia "
                f"la señal ponderada, que utiliza {ANO_NDVI_INICIAL_ANALISIS}-{ANO_NDVI_FINAL_ANALISIS}."
            )
    else:
        modo_comparador = "Sin comparador"
        capas_activas = []
        panel_capas.markdown("### Capas e indicadores")
        panel_capas.caption(
            "Active una o varias fuentes. Cada bloque explica qué información aporta."
        )

        if analiza_cambios:
            if panel_capas.checkbox(
                "Resultado combinado · sectores para revisión",
                value="Sectores para revisión" in perfil["capas"],
                key=f"capa_resultado_{modo_analisis}",
                help="Coincidencia espacial de las señales principales de JRC, Hansen y ESRI.",
            ):
                capas_activas.append("Sectores para revisión")

            with panel_capas.expander("JRC Tropical Moist Forest", expanded=True):
                st.caption("Estado anual del bosque tropical desde 1990.")
                if st.checkbox(
                    "Estado forestal",
                    value="Estado forestal JRC" in perfil["capas"],
                    key=f"capa_jrc_estado_{modo_analisis}",
                ):
                    capas_activas.append("Estado forestal JRC")
                if st.checkbox(
                    "Deforestación",
                    value="Deforestación JRC" in perfil["capas"],
                    key=f"capa_jrc_deforestacion_{modo_analisis}",
                ):
                    capas_activas.append("Deforestación JRC")
                if st.checkbox(
                    "Degradación",
                    value="Degradación JRC" in perfil["capas"],
                    key=f"capa_jrc_degradacion_{modo_analisis}",
                ):
                    capas_activas.append("Degradación JRC")
                if st.checkbox(
                    "Regeneración forestal",
                    value="Regeneración forestal JRC" in perfil["capas"],
                    key=f"capa_jrc_regeneracion_{modo_analisis}",
                    help=(
                        "Clase Forest regrowth de JRC TMF: área antes deforestada que "
                        "actualmente presenta bosque en regeneración."
                    ),
                ):
                    capas_activas.append("Regeneración forestal JRC")
                anio_tmf_capa = st.selectbox(
                    "Año JRC",
                    list(range(1990, ANO_TMF_MAX + 1)),
                    index=ANO_TMF_MAX - 1990,
                    key=f"anio_jrc_{modo_analisis}",
                )

            with panel_capas.expander("Hansen Global Forest Change", expanded=False):
                st.caption("Pérdida anual de cobertura arbórea desde 2001.")
                if st.checkbox(
                    "Pérdida posterior a 2020",
                    value="Pérdida Hansen post-2020" in perfil["capas"],
                    key=f"capa_hansen_reciente_{modo_analisis}",
                ):
                    capas_activas.append("Pérdida Hansen post-2020")
                if st.checkbox(
                    "Pérdida histórica 2001-2020",
                    value="Pérdida Hansen 2001-2020" in perfil["capas"],
                    key=f"capa_hansen_historica_{modo_analisis}",
                ):
                    capas_activas.append("Pérdida Hansen 2001-2020")
                if st.checkbox(
                    "Cobertura arbórea persistente",
                    value="Cobertura arbórea persistente" in perfil["capas"],
                    key=f"capa_hansen_base_{modo_analisis}",
                ):
                    capas_activas.append("Cobertura arbórea persistente")

            with panel_capas.expander("ESRI Land Use / Land Cover", expanded=False):
                st.caption("Cobertura del suelo y cambios de la clase árboles.")
                if st.checkbox(
                    "Uso y cobertura del suelo",
                    value="Uso y cobertura ESRI" in perfil["capas"],
                    key=f"capa_esri_cobertura_{modo_analisis}",
                ):
                    capas_activas.append("Uso y cobertura ESRI")
                if st.checkbox(
                    "Transiciones de la clase árboles",
                    value="Transiciones ESRI" in perfil["capas"],
                    key=f"capa_esri_transiciones_{modo_analisis}",
                ):
                    capas_activas.append("Transiciones ESRI")
                anio_esri_capa = st.selectbox(
                    "Año ESRI",
                    list(range(ANO_ESRI_MIN, ANO_ESRI_MAX + 1)),
                    index=ANO_ESRI_MAX - ANO_ESRI_MIN,
                    key=f"anio_esri_{modo_analisis}",
                )

            with panel_capas.expander("Sentinel-2 · NDVI", expanded=False):
                st.caption("Vigor de la vegetación y disminución entre períodos.")
                if st.checkbox(
                    "Cambio del vigor vegetal",
                    value="ΔNDVI" in perfil["capas"],
                    key=f"capa_ndvi_cambio_{modo_analisis}",
                ):
                    capas_activas.append("ΔNDVI")
                if st.checkbox(
                    "Vigor vegetal de un año",
                    value="Vegetación NDVI" in perfil["capas"],
                    key=f"capa_ndvi_anual_{modo_analisis}",
                ):
                    capas_activas.append("Vegetación NDVI")
                anio_ndvi_capa = st.selectbox(
                    "Año NDVI",
                    list(range(2017, ANO_NDVI_MAX + 1)),
                    index=ANO_NDVI_MAX - 2017,
                    key=f"anio_ndvi_{modo_analisis}",
                )
                anio_ndvi_inicial = st.selectbox(
                    f"Año inicial del cambio · final {ANO_NDVI_MAX}",
                    list(range(2017, ANO_NDVI_MAX)),
                    index=list(range(2017, ANO_NDVI_MAX)).index(2023),
                    key=f"anio_ndvi_cambio_{modo_analisis}",
                )

            with panel_capas.expander("GEDI · altura del dosel", expanded=False):
                st.caption("Estructura vertical disponible; no es una serie anual continua.")
                if st.checkbox(
                    "Altura del dosel",
                    value="Altura GEDI" in perfil["capas"],
                    key=f"capa_gedi_{modo_analisis}",
                ):
                    capas_activas.append("Altura GEDI")

        with panel_capas.expander("ERI · resiliencia ecológica", expanded=False):
            st.caption(
                "Síntesis complementaria de estructura, conectividad local, estabilidad "
                "topográfica y proximidad riparia."
            )
            if st.checkbox(
                "Índice ERI indicativo",
                value="ERI indicativo" in perfil["capas"],
                key=f"capa_eri_{modo_analisis}",
                help=(
                    "Muestra cinco clases entre muy baja y muy alta. No modifica el "
                    "índice de indicios ni la prioridad de visita."
                ),
            ):
                capas_activas.append("ERI indicativo")

        if analiza_conectividad:
            with panel_capas.expander("Almanaque Azul · corredores", expanded=True):
                mostrar_interseccion_corredores_mapa = st.checkbox(
                    "Coincidencia dentro del área analizada",
                    value=True,
                    key=f"capa_interseccion_corredores_{modo_analisis}",
                    help=(
                        "Después de crear el análisis muestra únicamente la parte de los "
                        "corredores que queda dentro de la finca o subcuenca."
                    ),
                )
                mostrar_corredores_contexto_mapa = st.checkbox(
                    "Corredores completos · contexto regional",
                    value=False,
                    key=f"capa_contexto_corredores_{modo_analisis}",
                    help=(
                        "Vista opcional. Puede extenderse fuera del área seleccionada y no "
                        "representa cobertura de bosque."
                    ),
                )
                mostrar_puntos_criticos_mapa = st.checkbox(
                    "Puntos críticos publicados",
                    value=False,
                    key=f"capa_puntos_{modo_analisis}",
                )
            with panel_capas.expander(
                f"{FUENTE_BOSQUE_ORGANIZACION} · bosque {ANO_BOSQUE_REFERENCIA}",
                expanded=modo_analisis == MODO_CORREDORES,
            ):
                mostrar_fragmentos_bosque = st.checkbox(
                    "Fragmentos de bosque",
                    value=True,
                    key=f"capa_fragmentos_{modo_analisis}",
                )
                mostrar_ruta_corredor = st.checkbox(
                    "Conexión potencial hacia corredor",
                    value=True,
                    key=f"capa_ruta_{modo_analisis}",
                )
                mostrar_bosque_contexto = st.checkbox(
                    "Bosque en el área y el entorno",
                    value=False,
                    disabled=not bosque_automatico_disponible,
                    key=f"capa_contexto_{modo_analisis}",
                )
                mostrar_conexiones_bosque = st.checkbox(
                    "Estructura esencial entre fragmentos",
                    value=False,
                    disabled=not bosque_automatico_disponible,
                    key=f"capa_red_{modo_analisis}",
                )
                mostrar_brechas_bosque = st.checkbox(
                    "Fragmentos separados y distancia",
                    value=False,
                    disabled=not bosque_automatico_disponible,
                    key=f"capa_brechas_{modo_analisis}",
                )

        orden_capas_mapa = list(capas_activas)
        if not capas_activas and not analiza_conectividad:
            panel_capas.warning("Active al menos una capa territorial para mostrarla en el mapa.")

    capa_contextual = resolver_capa_contextual(
        modo_analisis,
        modo_comparador,
        capas_activas,
    )
    if modo_mapa == "Explorar capas":
        capa_visible_inicial = (
            capa_contextual if capa_contextual in capas_activas else None
        )

    firma_analisis_actual = (
        METHODOLOGY_VERSION,
        modo_analisis,
        tipo_area,
        finca_seleccionada,
        subcuenca_seleccionada,
        ANO_DIAG_TMF,
        ANO_ESRI_MIN,
        ANO_ESRI_MAX,
        geometria_dibujada_json,
        catalogo_corredores["version_publicada"],
        huella_territorial(),
        huella_bosque,
        umbral_conectividad_m,
        area_min_parche_ha,
    )
    firma_visual_actual = (
        firma_analisis_actual,
        mapa_base,
        modo_mapa,
        modo_comparador,
        anio_tmf_inicial,
        anio_tmf_final,
        anio_esri_inicial,
        anio_esri_final,
        anio_ndvi_inicial,
        anio_ndvi_final,
        anio_tmf_capa,
        anio_esri_capa,
        anio_ndvi_capa,
        tuple(orden_capas_mapa),
        capa_visible_inicial,
        mostrar_fragmentos_bosque,
        mostrar_bosque_contexto,
        mostrar_conexiones_bosque,
        mostrar_brechas_bosque,
        mostrar_ruta_corredor,
        mostrar_interseccion_corredores_mapa,
        mostrar_corredores_contexto_mapa,
        mostrar_puntos_criticos_mapa,
        mostrar_limite_cuenca,
        mostrar_subcuencas_local,
    )
    analisis_actual = (
        st.session_state.get("firma_analisis") == firma_analisis_actual
    )
    if seccion_tablero == "Análisis":
        acciones_sidebar.button(
            "Volver al mapa",
            type="primary",
            use_container_width=True,
            key="volver_mapa_sidebar",
            on_click=volver_al_mapa,
        )
        solicitar_analisis = False
    else:
        columna_analizar = acciones_sidebar
        columna_resultados = None
        if analisis_actual:
            columna_analizar, columna_resultados = acciones_sidebar.columns([1.1, 1])
        solicitar_analisis = columna_analizar.button(
            "Actualizar" if analisis_actual else "Realizar análisis",
            type="primary",
            use_container_width=True,
            key="crear_analisis_panel",
            help=f"Procesa únicamente la información de {contenido_modo['titulo'].lower()}.",
        )
        if columna_resultados is not None:
            columna_resultados.button(
                "Resultados",
                use_container_width=True,
                key="abrir_resultados_sidebar",
                on_click=abrir_resultados_contextuales,
                help=(
                    "Abre las tablas completas, la gráfica temporal por fuente y los "
                    "archivos de respaldo."
                ),
            )

    if seccion_tablero == "Análisis":
        st.markdown("### Resultados y descargas")
        st.caption(
            "Consulte el detalle por tema y descargue los archivos de respaldo."
        )
        columna_panel = st.container(border=True)
        mapa_resultados_contenedor = None
    else:
        mostrar_panel_resultados = analisis_actual or solicitar_analisis
        if mostrar_panel_resultados:
            columna_mapa, columna_resultados = st.columns([3, 1], gap="small")
            mapa_resultados_contenedor = columna_mapa.container(
                key="mapa_portal"
            )
            columna_panel = columna_resultados.container(
                key="panel_resultados_visible"
            )
        else:
            mapa_resultados_contenedor = st.container(key="mapa_portal")
            columna_panel = st.container(key="panel_resultados_oculto")
        mapa_resultados_contenedor.markdown(
            '<div class="mapa-cabecera"><small>Centro del análisis</small>'
            '<strong>Evidencia cartográfica</strong></div>',
            unsafe_allow_html=True,
        )

    with columna_panel:
        st.markdown(
            '<div class="resultado-cabecera"><small>Estadísticas del área</small>'
            '<strong>Resultado de la preevaluación</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="dashboard-area">
              <div><small>Área seleccionada</small><strong>{html_lib.escape(nombre_area)}</strong></div>
              <div><small>Superficie analizada</small><strong>{superficie_ha:,.1f} ha</strong></div>
              <div><small>Análisis</small><strong>{html_lib.escape(contenido_modo['titulo'])}</strong></div>
              <div><small>Estado</small><strong>{'Resultado listo' if analisis_actual else 'Pendiente de generar'}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if tipo_area == "Toda la cuenca":
            st.warning(
                "El análisis regional puede tardar varios minutos. Para una revisión rápida "
                "se recomienda seleccionar una finca o subcuenca."
            )

        if not analisis_actual:
            st.markdown(
                '<div class="dashboard-estado"><b>Selección lista.</b> Revise el área y genere '
                'la preevaluación para ver la conclusión y todos los indicadores.</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Información que se calculará", expanded=False):
                st.markdown(f"**Resultado esperado:** {contenido_modo['resultado']}")
                if analiza_cambios:
                    st.markdown(
                        f"- JRC {ANO_DIAG_TMF}, Hansen 2021-{ANO_HANSEN_MAX}, "
                        f"ESRI {ANO_ESRI_MIN}-{ANO_ESRI_MAX}, GEDI y NDVI."
                    )
                if analiza_conectividad:
                    st.markdown(
                        f"- Corredores de Almanaque Azul y estructura del bosque "
                        f"{ANO_BOSQUE_REFERENCIA}."
                    )
        else:
            resultados = st.session_state["resultados_analisis"]
            pestana_lectura, pestana_eri, pestana_grafica = st.tabs(
                ["Lectura", "ERI", "Gráfica"]
            )
            with pestana_lectura:
                mostrar_panel_dashboard(resultados, modo_analisis)
            with pestana_eri:
                mostrar_resumen_eri(resultados)
            with pestana_grafica:
                mostrar_grafica_contextual_dashboard(
                    resultados=resultados,
                    modo_analisis=modo_analisis,
                    capa_contextual=capa_contextual,
                    tipo_area=tipo_area,
                    finca_id=finca_seleccionada,
                    subcuenca_nombre=subcuenca_seleccionada,
                    geometria_geojson=geometria_dibujada_json,
                    capas_activas=capas_activas,
                )
        if solicitar_analisis:
            firma_anterior = st.session_state.get("firma_analisis")
            with st.status(
                f"Preparando {contenido_modo['titulo'].lower()}...",
                expanded=True,
            ) as estado_analisis:
                if analiza_cambios:
                    estado_analisis.write("Calculando las señales territoriales seleccionadas.")
                    resultados_nuevos = ejecutar_analisis(
                        tipo_area=tipo_area,
                        finca_id=finca_seleccionada,
                        subcuenca_nombre=subcuenca_seleccionada,
                        geometria_geojson=geometria_dibujada_json,
                        anio_tmf_diagnostico=ANO_DIAG_TMF,
                        anio_esri_inicial=ANO_ESRI_MIN,
                        anio_esri_final=ANO_ESRI_MAX,
                    )
                else:
                    resultados_nuevos = {"area_ha": superficie_ha}

                if analiza_conectividad:
                    estado_analisis.write("Revisando la relación con los corredores publicados.")
                    aoi_geojson_serializado = json.dumps(
                        geometria.getInfo(),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    resultados_nuevos["corredores"] = analizar_corredores_cache(
                        aoi_geojson_serializado
                    )
                    if bosque_automatico_disponible:
                        try:
                            distancia_corredor_m = resultados_nuevos["corredores"].get(
                                "distancia_corredor_mas_cercano_m"
                            )
                            radio_contexto_m = calcular_radio_contexto(
                                distancia_corredor_m,
                                umbral_conectividad_m,
                                RADIO_BUSQUEDA_CORREDOR_M,
                            )
                            resultados_nuevos["radio_contexto_conectividad_m"] = (
                                radio_contexto_m
                            )
                            estado_analisis.write(
                                "Analizando fragmentos de bosque en el área y solo el "
                                f"entorno necesario ({radio_contexto_m / 1000:.1f} km)."
                            )
                            resultados_nuevos["fragmentacion"] = analizar_bosque_asset(
                                ASSET_BOSQUE_2021,
                                CAMPO_COBERTURA_BOSQUE_2021,
                                VALOR_COBERTURA_BOSQUE_2021,
                                aoi_geojson_serializado,
                                umbral_conectividad_m,
                                area_min_parche_ha,
                                radio_contexto_m,
                            )
                            resultados_nuevos["fragmentacion"][
                                "fuente_cobertura"
                            ] = FUENTE_BOSQUE_CORTA
                            resultados_nuevos["fragmentacion"][
                                "ano_referencia_cobertura"
                            ] = ANO_BOSQUE_REFERENCIA
                        except Exception as error:
                            resultados_nuevos["fragmentacion_error"] = str(error)

                estado_analisis.write(
                    "Calculando el Índice de Resiliencia Ecológica indicativo."
                )
                try:
                    resultados_nuevos["eri"] = calcular_eri_indicativo(
                        tipo_area=tipo_area,
                        finca_id=finca_seleccionada,
                        subcuenca_nombre=subcuenca_seleccionada,
                        geometria_geojson=geometria_dibujada_json,
                    )
                except Exception as error:
                    resultados_nuevos["eri_error"] = str(error)

                if modo_analisis == MODO_INTEGRAL:
                    resultados_nuevos["prioridad_visita"] = calcular_prioridad_visita(
                        puntaje_cambios=resultados_nuevos["puntaje"],
                        contexto_corredores=resultados_nuevos["corredores"],
                        contexto_fragmentacion=resultados_nuevos.get("fragmentacion"),
                    )
                resultados_nuevos["modo_analisis"] = modo_analisis
                st.session_state["resultados_analisis"] = resultados_nuevos
                st.session_state["firma_analisis"] = firma_analisis_actual
                # El resultado aparece en el panel lateral derecho, como en el portal HTML.
                # La vista extensa se abre únicamente si el usuario solicita las descargas.
                st.session_state["mostrar_resultados"] = False
                if firma_anterior != firma_analisis_actual:
                    st.session_state.pop("pdf_analisis", None)
                    st.session_state.pop("firma_informe", None)
                    st.session_state.pop("errores_mapas", None)
                    st.session_state.pop("intento_informe", None)
                    st.session_state.pop("mapas_reporte", None)
                estado_analisis.update(
                    label="Preevaluación preparada.",
                    state="complete",
                    expanded=False,
                )
            st.rerun()

        analisis_actual = (
            st.session_state.get("firma_analisis") == firma_analisis_actual
        )

    if seccion_tablero == "Análisis" and analisis_actual:
        resultados = st.session_state["resultados_analisis"]
        st.markdown("### Resultados completos")
        st.caption(
            "Toda la información permanece disponible, organizada por tema para evitar "
            "una pantalla extensa y difícil de interpretar."
        )
        nombres_pestanas = ["Resumen", "ERI indicativo"]
        if analiza_cambios:
            nombres_pestanas.append("Cambios territoriales")
        if analiza_conectividad:
            nombres_pestanas.extend(["Corredores", "Bosque y conectividad"])
        pestanas = st.tabs(nombres_pestanas)
        indice_pestana = 0
        with pestanas[indice_pestana]:
            if modo_analisis == MODO_CORREDORES:
                mostrar_resumen_conectividad(resultados)
            elif modo_analisis == MODO_INTEGRAL:
                mostrar_resumen_integral(resultados)
            else:
                mostrar_resumen_ejecutivo(resultados)
        indice_pestana += 1
        with pestanas[indice_pestana]:
            mostrar_detalle_eri(resultados)
        indice_pestana += 1
        if analiza_cambios:
            with pestanas[indice_pestana]:
                mostrar_resultados(
                    resultados,
                    ANO_DIAG_TMF,
                    ANO_ESRI_MIN,
                    ANO_ESRI_MAX,
                )
            indice_pestana += 1
        if analiza_conectividad:
            with pestanas[indice_pestana]:
                mostrar_resultados_corredores(resultados["corredores"])
            indice_pestana += 1
            with pestanas[indice_pestana]:
                if resultados.get("fragmentacion"):
                    mostrar_resultados_fragmentacion(resultados["fragmentacion"])
                elif resultados.get("fragmentacion_error"):
                    st.warning(
                        "El componente de bosque y conectividad no estuvo disponible en esta "
                        "ejecución. Los demás resultados permanecen disponibles."
                    )
                    with st.expander(
                        "Detalle para soporte de bosque y conectividad",
                        expanded=False,
                    ):
                        st.code(resultados["fragmentacion_error"])
        registro_resultados = construir_registro_metodologico(
            tipo_area=tipo_area,
            finca_id=finca_seleccionada,
            subcuenca_nombre=subcuenca_seleccionada,
            geometria_geojson=geometria_dibujada_json,
            anio_tmf_visual_inicial=anio_tmf_inicial,
            anio_tmf_visual_final=anio_tmf_final,
            anio_esri_visual_inicial=anio_esri_inicial,
            anio_esri_visual_final=anio_esri_final,
            anio_ndvi_visual_inicial=anio_ndvi_inicial,
            anio_ndvi_visual_final=anio_ndvi_final,
            anio_tmf_capa=anio_tmf_capa,
            anio_esri_capa=anio_esri_capa,
            anio_ndvi_capa=anio_ndvi_capa,
            modo_analisis=modo_analisis,
            modo_comparador=modo_comparador,
            capas_activas=capas_activas,
            resultados=resultados,
        )
        nombre_archivo = re.sub(r"[^A-Za-z0-9_-]+", "_", nombre_area).strip("_").lower()
        columna_pdf, columna_metodo = st.columns(2)
        informe_actual = (
            st.session_state.get("firma_informe") == firma_visual_actual
            and st.session_state.get("pdf_analisis")
        )
        errores_informe = (
            st.session_state.get("errores_mapas", [])
            if st.session_state.get("firma_informe") == firma_visual_actual
            else []
        )
        if modo_analisis != MODO_CORREDORES and (not informe_actual or errores_informe):
            etiqueta_informe = (
                "Reintentar mapas faltantes"
                if informe_actual and errores_informe
                else "Preparar informe PDF"
            )
            preparar_informe = columna_pdf.button(
                etiqueta_informe,
                use_container_width=True,
                key="preparar-informe-pdf",
                help=(
                    "Solicita en paralelo las siete imágenes temáticas a Earth Engine y arma "
                    "el documento. Si ya existe un informe parcial, vuelve a intentar los mapas."
                ),
            )
            if preparar_informe:
                # El primer intento conserva una clave de caché estable. Solo se
                # crea una clave nueva cuando el usuario reintenta mapas faltantes.
                intento_informe = (
                    st.session_state.get("intento_informe", 0) + 1
                    if errores_informe
                    else 0
                )
                st.session_state["intento_informe"] = intento_informe
                with st.status(
                    "Preparando el informe cartográfico...",
                    expanded=True,
                ) as estado_informe:
                    try:
                        estado_informe.write(
                            "Solicitando siete mapas a Earth Engine en grupos de tres."
                        )
                        mapas_reporte, errores_mapas = generar_mapas_reporte(
                            tipo_area=tipo_area,
                            finca_id=finca_seleccionada,
                            subcuenca_nombre=subcuenca_seleccionada,
                            geometria_geojson=geometria_dibujada_json,
                            anio_tmf_diagnostico=ANO_DIAG_TMF,
                            anio_esri_inicial=anio_esri_inicial,
                            anio_esri_final=anio_esri_final,
                            anio_ndvi_inicial=ANO_NDVI_INICIAL_ANALISIS,
                            intento_cache=intento_informe,
                            _mapas_existentes=(
                                st.session_state.get("mapas_reporte")
                                if errores_informe
                                else None
                            ),
                        )
                        disponibles = sum(
                            1 for mapa_reporte in mapas_reporte if mapa_reporte.get("imagen")
                        )
                        estado_informe.write(
                            f"Earth Engine entregó {disponibles} de 7 mapas. Armando el PDF."
                        )
                        st.session_state["errores_mapas"] = errores_mapas
                        st.session_state["mapas_reporte"] = mapas_reporte
                        st.session_state["firma_informe"] = firma_visual_actual
                        if disponibles:
                            st.session_state["pdf_analisis"] = generar_pdf(
                                nombre_area,
                                resultados,
                                ANO_DIAG_TMF,
                                ANO_ESRI_MIN,
                                ANO_ESRI_MAX,
                                ANO_NDVI_INICIAL_ANALISIS,
                                mapas_reporte,
                            )
                            estado_informe.update(
                                label="Informe listo para descargar",
                                state="complete",
                                expanded=False,
                            )
                        else:
                            st.session_state.pop("pdf_analisis", None)
                            estado_informe.update(
                                label="Earth Engine no entregó los mapas",
                                state="error",
                                expanded=True,
                            )
                    except Exception as error:
                        st.session_state.pop("pdf_analisis", None)
                        st.session_state.pop("firma_informe", None)
                        st.session_state["errores_mapas"] = [
                            f"Preparación del informe: {type(error).__name__}"
                        ]
                        estado_informe.update(
                            label="No fue posible preparar el informe",
                            state="error",
                            expanded=True,
                        )
                        st.error(
                            "La solicitud cartográfica no finalizó. Puede intentarlo nuevamente; "
                            "los resultados del análisis permanecen disponibles."
                        )
                informe_actual = st.session_state.get("pdf_analisis")

        if modo_analisis == MODO_CORREDORES:
            columna_pdf.caption(
                "El registro metodológico incluye el resultado de corredores y conectividad. "
                "Los archivos geográficos se descargan desde el detalle del resultado."
            )
        elif informe_actual:
            columna_pdf.download_button(
                "Descargar informe PDF",
                data=informe_actual,
                file_name=f"ficha_preevaluacion_{nombre_archivo}.pdf",
                mime="application/pdf",
                on_click="ignore",
                type="primary",
                use_container_width=True,
            )
        else:
            columna_pdf.caption(
                "El PDF se prepara por separado. Los siete mapas se solicitan en paralelo para reducir la espera."
            )
        columna_metodo.download_button(
            "Descargar registro metodológico",
            data=json.dumps(
                registro_resultados,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file_name=f"metodologia_preevaluacion_{nombre_archivo}.json",
            mime="application/json",
            on_click="ignore",
            use_container_width=True,
            help="Contiene fuentes, períodos, umbrales, pesos, reglas y el resumen del resultado.",
        )

        if (
            modo_analisis != MODO_CORREDORES
            and st.session_state.get("firma_informe") == firma_visual_actual
        ):
            errores_mapas = st.session_state.get("errores_mapas", [])
            if errores_mapas:
                disponibles = 7 - len(errores_mapas)
                if disponibles:
                    st.warning(
                        f"El informe contiene {disponibles} de 7 mapas. Algunas imágenes no "
                        "estuvieron disponibles temporalmente; puede volver a preparar el PDF."
                    )
                else:
                    st.error(
                        "Earth Engine no entregó las imágenes cartográficas. No se generó un PDF "
                        "incompleto. Vuelva a preparar el informe y, si continúa, envíe el detalle "
                        "técnico mostrado abajo."
                    )
                with st.expander("Detalle de los mapas no disponibles", expanded=False):
                    st.code("\n".join(errores_mapas))
    elif seccion_tablero == "Análisis" and "resultados_analisis" in st.session_state:
        st.warning(
            "Cambió el área o el período. Ejecute nuevamente la preevaluación para "
            "actualizar los resultados y el informe."
        )
    elif seccion_tablero == "Análisis":
        st.info(
            "Cuando genere la preevaluación aparecerán el resumen, el detalle por fuente y los archivos de respaldo."
        )

    if seccion_tablero == "Análisis":
        if analisis_actual and analiza_cambios:
            mostrar_grafica_por_fuente(
                firma_analisis_actual,
                tipo_area,
                finca_seleccionada,
                subcuenca_seleccionada,
                geometria_dibujada_json,
            )
        elif analisis_actual:
            st.info(
                "Este enfoque utiliza corredores publicados y métricas de fragmentación. "
                "Sus gráficas y archivos geográficos están en las pestañas de resultados; "
                "no se crea una serie temporal que mezcle fuentes incompatibles."
            )
        st.stop()

    if analisis_actual:
        if modo_analisis == MODO_INTEGRAL:
            mapa_resultados_contenedor.markdown(
                '<div class="mapa-nota">Vista resumida automática: muestra la evidencia '
                'principal para ubicar dónde conviene revisar primero.</div>',
                unsafe_allow_html=True,
            )
        else:
            mapa_resultados_contenedor.markdown(
                '<div class="mapa-nota">Active las capas del panel lateral para ubicar la '
                'evidencia; el detalle técnico permanece disponible bajo demanda.</div>',
                unsafe_allow_html=True,
            )

    mapa = folium.Map(
        location=[8.7, -80.0],
        zoom_start=8,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
        **opciones_interaccion_mapa(modo_comparador != "Sin comparador"),
    )
    agregar_mapa_base(mapa, mapa_base, control=True)
    Fullscreen(position="topleft", title="Pantalla completa").add_to(mapa)

    capa_izquierda = None
    capa_derecha = None
    etiqueta_inicial = None
    etiqueta_final = None
    if modo_comparador == "JRC TMF":
        etiqueta_inicial = f"JRC TMF {anio_tmf_inicial}"
        etiqueta_final = f"JRC TMF {anio_tmf_final}"
        capa_izquierda = capa_gee(
            mapa,
            obtener_tmf(anio_tmf_inicial, geometria),
            VIS_TMF,
            etiqueta_inicial,
            control=False,
            z_index=200,
        )
        capa_derecha = capa_gee(
            mapa,
            obtener_tmf(anio_tmf_final, geometria),
            VIS_TMF,
            etiqueta_final,
            control=False,
            z_index=200,
        )
    elif modo_comparador == "ESRI LULC":
        etiqueta_inicial = f"ESRI {anio_esri_inicial}"
        etiqueta_final = f"ESRI {anio_esri_final}"
        capa_izquierda = capa_gee(
            mapa,
            obtener_esri_visual(anio_esri_inicial, geometria),
            VIS_ESRI,
            etiqueta_inicial,
            control=False,
            z_index=200,
        )
        capa_derecha = capa_gee(
            mapa,
            obtener_esri_visual(anio_esri_final, geometria),
            VIS_ESRI,
            etiqueta_final,
            control=False,
            z_index=200,
        )
    elif modo_comparador == "NDVI Sentinel-2":
        etiqueta_inicial = f"NDVI {anio_ndvi_inicial}"
        etiqueta_final = f"NDVI {anio_ndvi_final}"
        capa_izquierda = capa_gee(
            mapa,
            clasificar_ndvi(obtener_ndvi(anio_ndvi_inicial, geometria)),
            VIS_NDVI_CLASES,
            etiqueta_inicial,
            control=False,
            z_index=200,
        )
        capa_derecha = capa_gee(
            mapa,
            clasificar_ndvi(obtener_ndvi(anio_ndvi_final, geometria)),
            VIS_NDVI_CLASES,
            etiqueta_final,
            control=False,
            z_index=200,
        )
    if capa_izquierda is not None and capa_derecha is not None:
        ComparadorCapasSincronizadas(
            layer_left=capa_izquierda,
            layer_right=capa_derecha,
        ).add_to(mapa)

    # En el modo de capas, el z-index conserva el orden configurado aunque una
    # capa se apague y se vuelva a encender desde el control del mapa.
    prioridades_capas = {
        nombre: 400 + (len(orden_capas_mapa) - indice) * 10
        for indice, nombre in enumerate(orden_capas_mapa)
    }
    capas_tematicas_mapa = []
    errores_capas_tematicas = []

    def agregar_tematica(clave, imagen, visualizacion, nombre):
        try:
            capa = capa_gee(
                mapa,
                imagen,
                visualizacion,
                nombre,
                mostrar=(
                    modo_comparador == "Sin comparador"
                    and clave in capas_activas
                ),
                z_index=prioridades_capas.get(clave, 400),
            )
        except Exception:
            errores_capas_tematicas.append(nombres_capas.get(clave, nombre))
            return None
        capas_tematicas_mapa.append((clave, capa))
        return capa

    perdida_post = perdida_pre = linea_base = None
    if any(
        nombre in capas_activas
        for nombre in [
            "Sectores para revisión",
            "Pérdida Hansen post-2020",
            "Pérdida Hansen 2001-2020",
            "Cobertura arbórea persistente",
        ]
    ):
        perdida_post, perdida_pre, linea_base = imagenes_hansen(geometria)

    if "Sectores para revisión" in capas_activas:
        coincidencia_revision = imagen_coincidencia_revision(
            geometria,
            tmf=obtener_tmf(ANO_DIAG_TMF, geometria),
            perdida_post=perdida_post,
            esri_inicial=obtener_esri(ANO_ESRI_MIN, geometria),
            esri_final=obtener_esri(ANO_ESRI_MAX, geometria),
        )
        agregar_tematica(
            "Sectores para revisión",
            coincidencia_revision.updateMask(coincidencia_revision.gt(0)),
            VIS_COINCIDENCIA_REVISION,
            "Sectores que requieren revisión · JRC + Hansen + ESRI",
        )

    if "Pérdida Hansen post-2020" in capas_activas:
        agregar_tematica(
            "Pérdida Hansen post-2020",
            perdida_post,
            VIS_HANSEN_POST,
            f"Hansen 2021-{ANO_HANSEN_MAX}",
        )
    if "Pérdida Hansen 2001-2020" in capas_activas:
        agregar_tematica(
            "Pérdida Hansen 2001-2020",
            perdida_pre,
            VIS_HANSEN_PRE,
            "Hansen 2001-2020",
        )
    if "Cobertura arbórea persistente" in capas_activas:
        agregar_tematica(
            "Cobertura arbórea persistente",
            linea_base,
            VIS_LINEA_BASE,
            "Cobertura arbórea persistente",
        )

    if "Estado forestal JRC" in capas_activas:
        agregar_tematica(
            "Estado forestal JRC",
            obtener_tmf(anio_tmf_capa, geometria),
            VIS_TMF,
            f"Estado forestal JRC {anio_tmf_capa}",
        )
    if "Deforestación JRC" in capas_activas:
        agregar_tematica(
            "Deforestación JRC",
            obtener_tmf(anio_tmf_capa, geometria).eq(3).selfMask(),
            VIS_TMF_DEFOR,
            f"Deforestación JRC {anio_tmf_capa}",
        )
    if "Degradación JRC" in capas_activas:
        agregar_tematica(
            "Degradación JRC",
            obtener_tmf(anio_tmf_capa, geometria).eq(2).selfMask(),
            VIS_TMF_DEGRAD,
            f"Degradación JRC {anio_tmf_capa}",
        )
    if "Regeneración forestal JRC" in capas_activas:
        agregar_tematica(
            "Regeneración forestal JRC",
            obtener_tmf(anio_tmf_capa, geometria).eq(4).selfMask(),
            VIS_TMF_REGENERACION,
            f"Regeneración forestal JRC {anio_tmf_capa}",
        )
    if "Uso y cobertura ESRI" in capas_activas:
        agregar_tematica(
            "Uso y cobertura ESRI",
            obtener_esri_visual(anio_esri_capa, geometria),
            VIS_ESRI,
            f"Uso y cobertura ESRI {anio_esri_capa}",
        )
    if "Transiciones ESRI" in capas_activas:
        esri_i = obtener_esri(anio_esri_inicial, geometria)
        esri_f = obtener_esri(anio_esri_final, geometria)
        transicion = (
            ee.Image(0)
            .where(esri_i.neq(2).And(esri_f.eq(2)), 1)
            .where(esri_i.eq(2).And(esri_f.neq(2)), 2)
            .where(esri_i.eq(2).And(esri_f.eq(2)), 3)
            .selfMask()
        )
        agregar_tematica(
            "Transiciones ESRI",
            transicion,
            VIS_ESRI_CAMBIO,
            f"Transiciones ESRI {anio_esri_inicial}-{anio_esri_final}",
        )
    if "Altura GEDI" in capas_activas:
        gedi = imagen_gedi(geometria)
        agregar_tematica(
            "Altura GEDI",
            gedi,
            VIS_GEDI,
            "Altura del dosel GEDI",
        )
    ndvi_final = None
    if "ΔNDVI" in capas_activas:
        ndvi_final = obtener_ndvi(ANO_NDVI_MAX, geometria)
    if "ΔNDVI" in capas_activas:
        ndvi_inicial = obtener_ndvi(anio_ndvi_inicial, geometria)
        delta_ndvi = ndvi_final.subtract(ndvi_inicial).rename("delta_ndvi")
        agregar_tematica(
            "ΔNDVI",
            delta_ndvi,
            VIS_NDVI_DELTA,
            f"ΔNDVI {anio_ndvi_inicial}-{ANO_NDVI_MAX}",
        )
    if "Vegetación NDVI" in capas_activas:
        agregar_tematica(
            "Vegetación NDVI",
            clasificar_ndvi(obtener_ndvi(anio_ndvi_capa, geometria)),
            VIS_NDVI_CLASES,
            f"Vegetación NDVI {anio_ndvi_capa}",
        )
    if "ERI indicativo" in capas_activas:
        eri_mapa, _ = construir_imagenes_eri(geometria)
        agregar_tematica(
            "ERI indicativo",
            clasificar_imagen_eri(eri_mapa),
            VIS_ERI,
            "Índice de Resiliencia Ecológica indicativo",
        )

    resultados_mapa = (
        st.session_state.get("resultados_analisis", {})
        if st.session_state.get("firma_analisis") == firma_analisis_actual
        else {}
    )
    fragmentacion_mapa = resultados_mapa.get("fragmentacion") or {}
    radio_contexto_mapa = float(
        fragmentacion_mapa.get("distancia_contexto_m", RADIO_BUSQUEDA_CORREDOR_M)
    )

    capa_bosque_contexto = None
    if (
        modo_mapa == "Explorar capas"
        and mostrar_bosque_contexto
        and bosque_automatico_disponible
    ):
        capa_bosque_contexto = capa_gee(
            mapa,
            imagen_bosque_contexto(geometria, radio_contexto_mapa),
            {"min": 1, "max": 1, "palette": ["2f6b45"]},
            f"Bosque {ANO_BOSQUE_REFERENCIA} · área y entorno",
            mostrar=True,
            opacidad=0.44,
            control=False,
            z_index=310,
        )

    corredores_resultado_mapa = resultados_mapa.get("corredores") or {}
    intersecciones_corredores_mapa = corredores_resultado_mapa.get(
        "intersecciones_geojson"
    )
    capas_corredores_mapa = agregar_capas_corredores(
        mapa,
        mostrar=(
            mostrar_interseccion_corredores_mapa
            and bool((intersecciones_corredores_mapa or {}).get("features"))
        ),
        corredores_geojson=intersecciones_corredores_mapa,
        etiqueta_contexto="Dentro del área analizada",
        opacidad_relleno=0.42,
        grosor_linea=2.4,
    )
    capas_corredores_mapa.extend(
        agregar_capas_corredores(
            mapa,
            mostrar=mostrar_corredores_contexto_mapa,
            mostrar_puntos_criticos=mostrar_puntos_criticos_mapa,
            opacidad_relleno=0.10,
            grosor_linea=1.2,
        )
    )
    capas_fragmentacion_mapa = []
    if fragmentacion_mapa:
        capas_fragmentacion_mapa = agregar_resultados_fragmentacion(
            mapa,
            fragmentacion_mapa,
            mostrar_parches=mostrar_fragmentos_bosque,
            mostrar_conexiones=mostrar_conexiones_bosque,
            mostrar_brechas=mostrar_brechas_bosque,
            mostrar_ruta_corredor=mostrar_ruta_corredor,
        )

    capa_limite_cuenca = agregar_limite_cuenca_local(
        mapa,
        control=False,
        mostrar=mostrar_limite_cuenca,
    )
    capa_subcuencas = agregar_subcuencas_local(
        mapa,
        control=False,
        mostrar=mostrar_subcuencas_local,
    )
    capa_area_seleccionada = capa_gee(
        mapa,
        area_seleccionada.style(color="D0442C", fillColor="D0442C14", width=3),
        {},
        "Área seleccionada",
        z_index=1010,
    )
    limites_area = obtener_limites(area_seleccionada)
    if etiqueta_inicial and etiqueta_final:
        agregar_rotulos_comparador(
            mapa,
            limites_area,
            etiqueta_inicial,
            etiqueta_final,
        )
    limites_mapa = limites_area
    if mostrar_bosque_contexto and bosque_automatico_disponible:
        contexto_mapa = ee.FeatureCollection(
            [ee.Feature(geometria.buffer(radio_contexto_mapa))]
        )
        limites_mapa = obtener_limites(contexto_mapa)
    if mostrar_ruta_corredor and analisis_actual:
        ruta_actual = (
            st.session_state.get("resultados_analisis", {})
            .get("fragmentacion", {})
            .get("ruta_corredor_geojson", {})
        )
        limites_ruta = obtener_limites_geojson(ruta_actual)
        if limites_ruta:
            limites_mapa = [
                [
                    min(limites_mapa[0][0], limites_ruta[0][0]),
                    min(limites_mapa[0][1], limites_ruta[0][1]),
                ],
                [
                    max(limites_mapa[1][0], limites_ruta[1][0]),
                    max(limites_mapa[1][1], limites_ruta[1][1]),
                ],
            ]
    mapa.fit_bounds(limites_mapa)

    if etiqueta_inicial and etiqueta_final:
        mapa_resultados_contenedor.markdown(
            f"""
            <div class="comparador-anios">
              <span>◀ <b>Año inicial</b><br>{etiqueta_inicial}</span>
              <span><b>Año final</b> ▶<br>{etiqueta_final}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mapa_resultados_contenedor.caption(
            "Arrastre el control circular del divisor vertical. El lado izquierdo muestra el "
            "año inicial y el derecho el año final. Al acercar, alejar o mover el mapa, ambas "
            "imágenes deben permanecer en la misma ubicación y escala. La línea queda donde "
            "usted la deje para facilitar la comparación."
        )
    else:
        if modo_analisis == MODO_INTEGRAL:
            if not analisis_actual:
                mapa_resultados_contenedor.caption(
                    "Sectores de cambio, corredores y fragmentos clave se muestran de forma "
                    "automática. La ruta naranja aparece únicamente cuando existe una conexión "
                    "estructural potencial."
                )
        elif analiza_conectividad:
            mapa_resultados_contenedor.caption(
                "La vista principal recorta los corredores al área analizada. Active el "
                "contexto regional solo si necesita ver su extensión completa."
            )
        else:
            mapa_resultados_contenedor.caption(
                "Elija las capas desde el panel lateral para ubicar las señales de cambio "
                "y revisar las fuentes que coinciden en un mismo sector."
            )
    with mapa_resultados_contenedor:
        st_folium(
            mapa,
            height=780,
            use_container_width=True,
            returned_objects=[],
            key=(
                f"mapa-{APP_VERSION}-{mapa_base}-{modo_analisis}-{tipo_area}-{finca_seleccionada}-{subcuenca_seleccionada}-{modo_mapa}-{modo_comparador}-"
                f"{anio_tmf_inicial}-{anio_tmf_final}-{anio_esri_inicial}-"
                f"{anio_esri_final}-{anio_ndvi_inicial}-{anio_ndvi_final}-"
                f"{anio_tmf_capa}-{anio_esri_capa}-{anio_ndvi_capa}-"
                f"{'-'.join(orden_capas_mapa)}-"
                f"{capa_visible_inicial}-"
                f"{catalogo_corredores['version_publicada']}-{huella_territorial()}-{huella_bosque}-"
                f"{umbral_conectividad_m}-{area_min_parche_ha}-"
                f"{mostrar_fragmentos_bosque}-{mostrar_conexiones_bosque}-"
                f"{mostrar_bosque_contexto}-"
                f"{mostrar_brechas_bosque}-{mostrar_ruta_corredor}-"
                f"{mostrar_interseccion_corredores_mapa}-"
                f"{mostrar_corredores_contexto_mapa}-"
                f"{mostrar_puntos_criticos_mapa}-"
                f"{mostrar_limite_cuenca}-{mostrar_subcuencas_local}-"
                f"{hash(geometria_dibujada_json or '')}"
            ),
        )
    if errores_capas_tematicas:
        capas_no_disponibles = ", ".join(dict.fromkeys(errores_capas_tematicas))
        mapa_resultados_contenedor.warning(
            "El mapa principal continúa disponible, pero no fue posible dibujar esta "
            f"evidencia sobre el área seleccionada: {capas_no_disponibles}. "
            "Esto suele indicar que la fuente no tiene cobertura espacial en esa zona; "
            "las demás capas y resultados permanecen disponibles."
        )

    fragmentacion_actual = fragmentacion_mapa or None
    if mostrar_bosque_contexto and bosque_automatico_disponible:
        mapa_resultados_contenedor.info(
            f"Contexto forestal visible: el verde muestra la cobertura de bosque "
            f"{ANO_BOSQUE_REFERENCIA} dentro del área y hasta "
            f"{radio_contexto_mapa / 1000:,.1f} km alrededor. El bosque exterior "
            "ayuda a interpretar la ruta naranja, pero no aumenta las hectáreas reportadas."
        )
    if (
        mostrar_brechas_bosque
        and analisis_actual
        and fragmentacion_actual
        and int(
            fragmentacion_actual.get("metricas_red", {}).get(
                "numero_parches_aislados", 0
            )
        )
        == 0
    ):
        detalle_contexto = (
            "La cobertura exterior está visible en verde."
            if mostrar_bosque_contexto
            else "Puede activar «Cobertura completa de bosque 2021 · área + entorno» para verla."
        )
        mapa_resultados_contenedor.info(
            f"No se encontraron fragmentos separados con la distancia de "
            f"{umbral_conectividad_m:,.0f} m. El cálculo también revisó el bosque "
            f"del entorno exterior. {detalle_contexto}"
        )
    if (
        mostrar_ruta_corredor
        and analisis_actual
        and fragmentacion_actual
        and not (
            fragmentacion_actual.get("ruta_corredor_geojson", {}).get("features")
        )
        and not fragmentacion_actual.get("conexion_corredor", {}).get("conecta")
    ):
        mapa_resultados_contenedor.info(
            f"No hay una ruta estructural visible hacia los corredores publicados dentro "
            f"de {radio_contexto_mapa / 1000:,.1f} km con saltos máximos de "
            f"{umbral_conectividad_m:,.0f} m."
        )

    with mapa_resultados_contenedor.expander(
        "Leyenda y significado de los colores",
        expanded=False,
    ):
        st.caption(
            "La leyenda se mantiene fuera del mapa para no cubrir la información espacial. "
            "Solo incluye la información visible en esta vista."
        )
        columnas_leyenda = st.columns(2)
        leyendas_activas = []
        if capa_bosque_contexto is not None:
            leyendas_activas.append(
                ("Cobertura completa de bosque 2021", LEYENDAS["Bosque 2021 de contexto"])
            )
        if (
            mostrar_interseccion_corredores_mapa
            and bool((intersecciones_corredores_mapa or {}).get("features"))
        ):
            leyendas_activas.append(
                (
                    "Corredor dentro del área analizada",
                    LEYENDAS["Corredores Almanaque Azul"],
                )
            )
        if mostrar_corredores_contexto_mapa or mostrar_puntos_criticos_mapa:
            leyendas_activas.append(
                (
                    "Contexto regional · Almanaque Azul",
                    LEYENDAS["Corredores Almanaque Azul"],
                )
            )
        if capas_fragmentacion_mapa and mostrar_fragmentos_bosque:
            leyendas_activas.append(
                (
                    "Valor de los fragmentos para mantener unido el bosque",
                    LEYENDAS["Importancia de parches"],
                )
            )
        if capas_fragmentacion_mapa and mostrar_conexiones_bosque:
            leyendas_activas.append(
                ("Estructura esencial", LEYENDAS["Estructura esencial"])
            )
        if capas_fragmentacion_mapa and mostrar_ruta_corredor:
            leyendas_activas.append(
                (
                    "Conexión potencial hacia corredor",
                    LEYENDAS["Ruta potencial al corredor"],
                )
            )
        if capas_fragmentacion_mapa and mostrar_brechas_bosque:
            leyendas_activas.append(
                (
                    "Fragmentos separados y distancia al vecino",
                    LEYENDAS["Separaciones potenciales"],
                )
            )
        if modo_comparador in ("JRC TMF", "ESRI LULC", "NDVI Sentinel-2"):
            leyendas_activas.append((modo_comparador, LEYENDAS[modo_comparador]))
        claves_tematicas_renderizadas = {
            clave for clave, _ in capas_tematicas_mapa
        }
        for nombre in capas_activas:
            if nombre not in claves_tematicas_renderizadas:
                continue
            if nombre in LEYENDAS:
                leyendas_activas.append((nombres_capas.get(nombre, nombre), LEYENDAS[nombre]))
            elif nombre == "Estado forestal JRC":
                leyendas_activas.append((nombres_capas[nombre], LEYENDAS["JRC TMF"]))
            elif nombre == "Uso y cobertura ESRI":
                leyendas_activas.append((nombres_capas[nombre], LEYENDAS["ESRI LULC"]))
        for indice, (titulo, elementos) in enumerate(leyendas_activas):
            with columnas_leyenda[indice % 2]:
                mostrar_leyenda(titulo, elementos)

    if modo_comparador == "NDVI Sentinel-2":
        periodo_ndvi_visual = f"{anio_ndvi_inicial}-{anio_ndvi_final}"
    elif "ΔNDVI" in capas_activas:
        periodo_ndvi_visual = f"{anio_ndvi_inicial}-{ANO_NDVI_MAX}"
    elif "Vegetación NDVI" in capas_activas:
        periodo_ndvi_visual = str(anio_ndvi_capa)
    else:
        periodo_ndvi_visual = f"hasta {ANO_NDVI_MAX}"

    with st.expander("Metodología y reproducibilidad", expanded=False):
        st.markdown(f"**Metodología aplicada:** {METHODOLOGY_VERSION}")
        st.caption(
            f"Opción ejecutada: {contenido_modo['titulo']}. Esta sección documenta también "
            "las fuentes de las otras opciones para mantener trazabilidad de la aplicación."
        )
        tab_fuentes, tab_reglas, tab_limites = st.tabs(
            ["Fuentes y períodos", "Reglas del análisis", "Alcance y limitaciones"]
        )
        with tab_fuentes:
            st.markdown(
                f"""
                | Fuente | Período o referencia | Resolución de trabajo | Función |
                |---|---:|---:|---|
                | JRC Tropical Moist Forest | Estado {ANO_DIAG_TMF} | 30 m | Señales de degradación y deforestación |
                | Hansen Global Forest Change | 2001-{ANO_HANSEN_MAX}; corte {CUTOFF_LABEL} | 30 m | Pérdida de cobertura arbórea |
                | ESRI Land Use/Land Cover | Diagnóstico {ANO_ESRI_MIN}-{ANO_ESRI_MAX} | 10 m | Transiciones de la clase árboles |
                | GEDI / OpenForis | Producto disponible | 100 m | Altura y cobertura válida del dosel |
                | Sentinel-2 SR Harmonized | Diagnóstico {ANO_NDVI_INICIAL_ANALISIS}-{ANO_NDVI_FINAL_ANALISIS}; mapa {periodo_ndvi_visual} | 10 m; resumen a {ESCALA_ANALISIS_NDVI_M} m | Disminución del vigor vegetal; señal corroborativa |
                | ERI indicativo · Dynamic World + GEDI + Copernicus DEM + MERIT Hydro | Cobertura {ANO_ERI_REFERENCIA} y productos de referencia | Resumen aproximado a {ESCALA_ERI_M} m | Contexto ecológico complementario; no cambia la prioridad |
                | Almanaque Azul | {catalogo_corredores['version_publicada']} | Vector interpretado | Valor estratégico para planificar visitas |
                | SINIA–MiAMBIENTE · Bosque y otros usos | {ANO_BOSQUE_REFERENCIA if bosque_automatico_disponible else 'Pendiente de configuración'} | Vector institucional en Earth Engine | Fragmentación y red de parches; contexto |
                """
            )
            st.markdown(
                f"""
                **Cómo se interpretan los períodos**

                - JRC aporta el **estado forestal de {ANO_DIAG_TMF}**. La señal se obtiene
                  de sus clases de degradación y deforestación; no de una resta 2020-2025.
                - Hansen aporta la pérdida anual **posterior al 31/12/2020**, es decir,
                  2021-{ANO_HANSEN_MAX}.
                - ESRI compara la clase árboles entre **{ANO_ESRI_MIN} y {ANO_ESRI_MAX}**,
                  los extremos de la serie utilizada por el análisis.
                - NDVI compara compuestos anuales **{ANO_NDVI_INICIAL_ANALISIS}-{ANO_NDVI_FINAL_ANALISIS}**
                  para medir disminución significativa del vigor vegetal.
                - Los años seleccionables del mapa son parámetros de visualización y no
                  cambian el índice de prioridad.
                """
            )
            with st.expander("Identificadores técnicos de los datos", expanded=False):
                st.code(
                    "\n".join(
                        [TMF_ASSET, HANSEN_ASSET, ESRI_ASSET, GEDI_ASSET, "COPERNICUS/S2_SR_HARMONIZED"]
                    )
                )
        with tab_reglas:
            st.markdown(
                f"""
                1. Cada fuente se procesa en su propia resolución y proyección.
                2. Las superficies se expresan en hectáreas dentro del área seleccionada.
                3. Las señales se activan con umbrales documentados: JRC, Hansen, ESRI, GEDI y NDVI.
                4. El índice suma cada fuente una sola vez: **JRC 2.0**, **Hansen 2.0**,
                   **ESRI 1.5**, **GEDI 0.5** y **NDVI 0.5**.
                5. La prioridad es **alta desde 3.0**, **media desde 1.5**, **preventiva desde 0.5** y **baja por debajo de 0.5**.
                6. El mapa **Sectores que requieren revisión** suma, en una malla común
                   de 30 m, las señales binarias de JRC, Hansen y ESRI. Muestra una,
                   dos o tres fuentes coincidentes, pero **no modifica el índice**.
                7. Los corredores de Almanaque Azul conservan sus categorías publicadas:
                   **alta, mediana y media-baja**. Su intersección se mide en un sistema
                   equivalente en área y **no modifica el índice satelital**. Para la prioridad
                   de visita, el solapamiento aporta proporcionalmente hasta **1.0 punto al
                   alcanzar 25% del área** y el Corredor Biológico Mesoamericano aporta **0.5**.
                8. El corredor por sí solo nunca genera una prioridad alta: sin señales de
                   cambio, el resultado integrado queda limitado a **preventiva**.
                9. El recorte institucional de **Bosque y otros usos 2021** de
                   SINIA–MiAMBIENTE se carga automáticamente. Cada parche de bosque es un nodo y se conecta con
                   otros dentro del umbral elegido. El índice conector usa 40% grado,
                   30% intermediación, 20% área y 10% fuerza; sus categorías son relativas
                   al área evaluada y no deben confundirse con las de Almanaque Azul.
                10. La estructura 2021 se conecta con el diagnóstico para indicar **dónde**
                    focalizar la visita —conectores y componentes aislados—, pero no suma
                    puntos hasta contar con umbrales calibrados para el territorio y las
                    especies objetivo.

                El NDVI se calcula como `(B8 - B4) / (B8 + B4)`. Aporta 0.5 cuando
                la disminución supera conjuntamente los umbrales de magnitud, superficie,
                proporción y cobertura válida; no identifica por sí solo bosque natural.
                """
            )
            mostrar_escala_ndvi_metodologia()
            st.markdown("**Justificación de los pesos**")
            st.markdown(
                "\n".join(
                    [
                        f"- **JRC TMF · 2.0:** {JUSTIFICACION_PESOS['tmf']}",
                        f"- **Hansen GFC · 2.0:** {JUSTIFICACION_PESOS['hansen']}",
                        f"- **ESRI LULC · 1.5:** {JUSTIFICACION_PESOS['esri']}",
                        f"- **GEDI · 0.5:** {JUSTIFICACION_PESOS['gedi']}",
                        f"- **NDVI · 0.5:** {JUSTIFICACION_PESOS['ndvi']}",
                    ]
                )
            )
            st.markdown("**Justificación de los umbrales**")
            st.markdown(
                "\n".join(
                    [
                        f"- **Hansen ≥ {UMBRAL_ALERTA_HANSEN_HA:.2f} ha:** {JUSTIFICACION_UMBRALES['hansen_post_2020_ha']}",
                        f"- **JRC deforestación ≥ {UMBRAL_REVISION_TMF_DEFOR_HA:.1f} ha o {UMBRAL_PCT_TMF_DEFOR:.0f}%:** {JUSTIFICACION_UMBRALES['jrc_deforestacion']}",
                        f"- **JRC degradación ≥ {UMBRAL_REVISION_TMF_DEGRAD_HA:.1f} ha o {UMBRAL_PCT_TMF_DEGRAD:.0f}%:** {JUSTIFICACION_UMBRALES['jrc_degradacion']}",
                        f"- **ESRI ≥ {UMBRAL_ESRI_SALIDA_HA:.2f} ha y {UMBRAL_PCT_ESRI_SALIDA:.0f}%:** {JUSTIFICACION_UMBRALES['esri_salida_arboles']}",
                        f"- **GEDI < {UMBRAL_DOSEL_BAJO_M:.0f} m, cobertura válida ≥ {UMBRAL_COBERTURA_GEDI_PCT:.0f}% y línea base ≥ {UMBRAL_LINEA_BASE_GEDI_PCT:.0f}%:** {JUSTIFICACION_UMBRALES['gedi_dosel_y_cobertura']}",
                        f"- **NDVI:** {JUSTIFICACION_UMBRALES['ndvi']}",
                    ]
                )
            )
            st.caption(
                "Todos los años seleccionables cambian únicamente la visualización. "
                f"El diagnóstico conserva JRC {ANO_DIAG_TMF}, Hansen 2021-{ANO_HANSEN_MAX} "
                f"posterior al corte {CUTOFF_LABEL}, ESRI {ANO_ESRI_MIN}-{ANO_ESRI_MAX} "
                f"y NDVI {ANO_NDVI_INICIAL_ANALISIS}-{ANO_NDVI_FINAL_ANALISIS}."
            )
            st.markdown("**Lectura de consistencia entre fuentes**")
            st.markdown(
                "\n".join(
                    [
                        f"- **Alta consistencia:** {REGLAS_CONSISTENCIA['alta']}.",
                        f"- **Consistencia parcial:** {REGLAS_CONSISTENCIA['parcial']}.",
                        f"- **Lectura mixta:** {REGLAS_CONSISTENCIA['mixta']}.",
                        f"- **Sin señal consistente:** {REGLAS_CONSISTENCIA['sin_senal']}.",
                    ]
                )
            )
            st.caption(
                "La consistencia complementa la interpretación y nunca suma, resta ni "
                "compensa puntos del índice."
            )
            st.markdown("**Mapa de coincidencia espacial**")
            st.markdown(
                "\n".join(
                    [
                        "- **1 fuente · amarillo:** señal aislada; revise el producto correspondiente.",
                        "- **2 fuentes · naranja:** coincidencia espacial que merece revisión prioritaria.",
                        "- **3 fuentes · rojo oscuro:** coincidencia espacial de las tres fuentes principales.",
                        f"- **Limitación:** {REGLAS_MAPA_COINCIDENCIA['limitacion']}",
                    ]
                )
            )
            st.markdown("**Índice de Resiliencia Ecológica indicativo (ERI)**")
            st.markdown(
                "\n".join(
                    [
                        "- **Integridad estructural · 35 %:** probabilidad de árboles y altura GEDI normalizada.",
                        f"- **Conectividad local · 25 %:** proporción de bosque en una ventana de {RADIO_CONECTIVIDAD_ERI_M / 1000:.1f} km.",
                        "- **Estabilidad topográfica · 20 %:** pendiente ponderada por la cobertura arbórea.",
                        f"- **Proximidad riparia · 20 %:** cercanía a cauces hasta {DISTANCIA_RIPARIA_ERI_M:,} m.",
                    ]
                )
            )
            st.caption(
                "El ERI se expresa entre 0 y 1, se presenta en cinco clases y permanece "
                "separado del índice de indicios y de la prioridad de visita. La conectividad "
                "es un proxy espacial y no demuestra conectividad funcional por especie."
            )
        with tab_limites:
            st.markdown(
                """
                - Una señal satelital no confirma por sí sola la causa de un cambio.
                - Las fuentes tienen fechas, resoluciones y metodologías diferentes.
                - La altura GEDI depende de la disponibilidad espacial del producto.
                - El NDVI puede responder a estacionalidad, humedad, nubes, cultivos o pastizales.
                - Los resultados deben contrastarse con documentos, imágenes recientes y campo.
                - Los corredores publicados representan conectividad estructural a escala de paisaje;
                  no garantizan movimiento efectivo de una especie concreta.
                - La cobertura SINIA–MiAMBIENTE representa bosque y otros usos en 2021; no indica por sí sola el año de una pérdida.
                - La calidad del análisis de fragmentación depende de la escala, topología y clasificación del asset institucional configurado.
                - El ERI es exploratorio: sus pesos y clases requieren calibración y validación de campo antes de cualquier uso normativo.
                - El componente de conectividad del ERI resume cobertura local; no reemplaza ECA/A ni un modelo funcional por especie.

                **Esta herramienta orienta revisiones. No es una certificación, una validación de
                campo ni una determinación de cumplimiento EUDR.**
                """
            )

except Exception as error:
    mostrar_error_amigable(error)
    with st.expander("Detalle técnico para soporte", expanded=False):
        st.code(traceback.format_exc())
