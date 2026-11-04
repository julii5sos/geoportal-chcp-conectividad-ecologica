"""Punto de entrada ligero para Streamlit Community Cloud."""

import runpy
from pathlib import Path

import streamlit as st

from eri_indicativo import PESOS_ERI
from metodologia_indice import (
    PERIODOS_ANALISIS,
    PESOS_INDICE,
    PUNTAJE_MAXIMO,
    UMBRALES_INDICE,
)
from modos_app import MODO_INTEGRAL, MODOS_ANALISIS
from portal_html import (
    inyectar_estilo_portal,
    mostrar_acceso_selector,
    mostrar_hero_inicio,
    mostrar_navegacion_portal,
)


st.set_page_config(
    page_title="Visor CHCP | Preevaluación territorial y conectividad",
    page_icon=":material/map:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state["_pagina_configurada"] = True

SECCION_MAPA = "Mapa"
SECCION_OBJETIVO = "Conoce la herramienta"
SECCION_DATOS = "Uso de datos"
SECCION_METODO = "Metodología y ayuda"
SECCION_ACERCA = "Acerca del visor"
SECCIONES_PRINCIPALES = (
    SECCION_MAPA,
    SECCION_OBJETIVO,
    SECCION_DATOS,
    SECCION_METODO,
    SECCION_ACERCA,
)


st.markdown(
    """
    <style>
    :root {
        --azul:#0a4393;--azul-profundo:#062a5e;--azul-suave:#eef1f7;
        --verde:#0a4393;--verde-oscuro:#062a5e;--acento:#77cc09;
        --amarillo:#fabc20;--suave:#566176;--borde:#d6deeb;
        --fondo:#f6f8fb;--claro:#eef1f7;
    }
    .stApp {background:var(--fondo);color:var(--azul-profundo);}
    .block-container {padding-top:3.5rem;padding-bottom:1.25rem;max-width:none;}
    button, [role="button"] {min-height:44px;touch-action:manipulation;}
    button:focus-visible, [role="button"]:focus-visible, input:focus-visible {
        outline:3px solid var(--acento);outline-offset:2px;
    }
    .portal-nav {
        display:flex;align-items:center;justify-content:space-between;gap:1rem;
        min-height:74px;margin:0 0 .65rem;padding:.8rem 1rem;
        color:#fff;background:linear-gradient(112deg,var(--azul) 0 78%,var(--azul-profundo) 78%);
        border-bottom:5px solid var(--acento);box-shadow:0 8px 22px rgba(6,42,94,.14);
    }
    .portal-marca {display:flex;align-items:center;gap:.75rem;min-width:0;}
    .portal-logo {
        display:grid;place-items:center;flex:0 0 42px;width:42px;height:42px;
        color:var(--azul);background:#fff;border-radius:50%;
    }
    .portal-logo svg{width:25px;height:25px;}
    .portal-marca strong{display:block;font-size:1.18rem;line-height:1.15;color:#fff;}
    .portal-marca small{display:block;margin-top:.2rem;font-size:.72rem;font-weight:700;letter-spacing:.055em;text-transform:uppercase;color:#dce8f8;}
    .portal-util{display:flex;align-items:center;justify-content:flex-end;gap:.45rem;flex-wrap:wrap;}
    .portal-chip{padding:.28rem .62rem;border:1px solid rgba(255,255,255,.5);border-radius:999px;font-size:.73rem;font-weight:700;color:#fff;white-space:nowrap;}
    .portal-chip.acento{border-color:var(--acento);background:var(--acento);color:#183400;}
    [data-testid="stSegmentedControl"] {
        margin-bottom:.35rem;padding:0;background:transparent;
        border:0;border-bottom:1px solid var(--borde);border-radius:0;
    }
    [data-testid="stSegmentedControl"] button[aria-checked="true"] {
        color:var(--azul)!important;box-shadow:inset 0 -4px 0 var(--acento);
    }
    [data-testid="stSegmentedControl"] button {
        cursor:pointer;border-radius:0!important;background:transparent!important;
    }
    .stButton button[data-testid="stBaseButton-primary"] {
        border-color:var(--azul)!important;background:var(--azul)!important;color:#fff!important;font-weight:700;
    }
    .stButton button[data-testid="stBaseButton-primary"]:hover {
        border-color:var(--azul-profundo)!important;background:var(--azul-profundo)!important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color:var(--borde)!important;border-radius:6px!important;background:#fff;
        box-shadow:0 8px 22px rgba(6,42,94,.06);
    }
    .entrada {
        position:relative;overflow:hidden;padding:1.55rem 1.7rem;
        border:0;border-bottom:6px solid var(--acento);
        background:linear-gradient(112deg,var(--azul) 0 78%,var(--azul-profundo) 78%);
        box-shadow:0 8px 22px rgba(6,42,94,.12);margin-bottom:1.2rem;
    }
    .entrada h1 {margin:0;color:#fff;font-size:clamp(2rem,4vw,3.25rem);line-height:1.12;}
    .entrada .subtitulo {margin:.45rem 0 0;color:#fff;font-size:1.2rem;font-weight:650;line-height:1.4;}
    .entrada p {color:#e0e9f7;max-width:75ch;line-height:1.6;margin:.65rem 0 0;}
    .entrada small {display:block;margin-top:.65rem;color:#d1def0;line-height:1.5;}
    .pregunta {margin:.1rem 0 1rem;color:var(--verde);}
    .tarjeta {min-height:220px;padding:.1rem;}
    .tarjeta small {display:block;color:var(--suave);font-weight:700;text-transform:uppercase;line-height:1.4;}
    .tarjeta h3 {margin:.45rem 0;color:var(--verde);line-height:1.35;}
    .tarjeta p {color:var(--suave);line-height:1.55;}
    .resultado {padding-top:.6rem;border-top:1px solid var(--borde);line-height:1.5;}
    .ruta-simple, .metodo-pasos {
        display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:.8rem 0 1.25rem;
    }
    .ruta-paso, .metodo-paso {
        position:relative;padding:1rem 1rem 1rem 3.7rem;border:1px solid var(--borde);
        background:var(--azul-suave);min-height:130px;line-height:1.5;
    }
    .ruta-numero, .metodo-numero {
        position:absolute;top:1rem;left:1rem;display:grid;place-items:center;width:2rem;height:2rem;
        border-radius:50%;background:var(--verde);color:#fff;font-weight:750;
    }
    .ruta-paso b, .metodo-paso b {display:block;margin-bottom:.3rem;color:var(--verde);}
    .ruta-paso span, .metodo-paso span {color:var(--suave);font-size:.94rem;}
    .alcance-grid {display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin:.8rem 0 1.25rem;}
    .alcance-card {padding:1rem 1.1rem;border:1px solid var(--borde);background:#fff;line-height:1.6;}
    .alcance-card h3 {margin:0 0 .45rem;color:var(--verde);font-size:1.15rem;}
    .alcance-card ul {margin:.3rem 0 0;padding-left:1.25rem;color:var(--suave);}
    .alcance-card li {margin:.35rem 0;}
    .nota-alcance {
        padding:.9rem 1rem;border-left:5px solid var(--verde);background:var(--claro);
        color:var(--verde);line-height:1.6;margin:.75rem 0 1rem;
    }
    .texto-legible {max-width:75ch;color:var(--suave);line-height:1.65;}
    @media(max-width:760px){
        .block-container{padding-top:3.5rem}.entrada{padding:1.1rem}
        .ruta-simple,.metodo-pasos,.alcance-grid{grid-template-columns:1fr}
        .tarjeta{min-height:auto}
        .portal-nav{align-items:flex-start;flex-direction:column}.portal-util{justify-content:flex-start}
    }
    @media(prefers-reduced-motion:reduce){
        *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# La referencia entregada por la usuaria prevalece sobre el estilo histórico.
inyectar_estilo_portal()


def mostrar_cabecera_portal(seccion=SECCION_MAPA):
    mostrar_navegacion_portal(seccion)


def elegir_modo(modo):
    st.session_state["modo_analisis"] = modo
    st.session_state["selector_modo_sidebar"] = modo
    st.session_state["seccion_tablero"] = SECCION_MAPA
    st.session_state["mostrar_resultados"] = False
    st.query_params.clear()
    st.query_params["seccion"] = "mapa"
    st.query_params["modo"] = modo


def abrir_selector_analisis():
    """Regresa al inicio sin conservar un enfoque anterior en sesión o URL."""

    st.session_state.pop("modo_analisis", None)
    st.session_state.pop("selector_modo_sidebar", None)
    st.session_state["mostrar_resultados"] = False
    st.session_state["seccion_tablero"] = SECCION_MAPA
    st.query_params.clear()
    st.query_params["seccion"] = "inicio"


def cerrar_selector_analisis():
    st.query_params.clear()
    st.query_params["seccion"] = "inicio"


@st.dialog("Realizar análisis", width="large")
def mostrar_selector_dialogo():
    """Replica el primer paso del asistente incluido en el HTML de referencia."""

    modos = list(MODOS_ANALISIS)
    if st.session_state.get("selector_modo_inicio") not in MODOS_ANALISIS:
        st.session_state["selector_modo_inicio"] = MODO_INTEGRAL

    columna_pasos, columna_pregunta = st.columns([0.28, 0.72], gap="medium")
    with columna_pasos:
        st.markdown(
            """
            <ol class="selector-pasos" aria-label="Pasos del asistente">
              <li class="actual"><i>1</i><span>Pregunta</span></li>
              <li><i>2</i><span>Área</span></li>
              <li><i>3</i><span>Parámetros</span></li>
              <li><i>4</i><span>Revisión</span></li>
            </ol>
            """,
            unsafe_allow_html=True,
        )
    with columna_pregunta:
        with st.container(key="selector_portal_dialogo"):
            st.markdown("### ¿Qué quiere saber?")
            st.caption(
                "Seleccione una preevaluación. El mapa mostrará únicamente los controles "
                "y resultados necesarios para esa pregunta."
            )
            modo = st.radio(
                "Tipo de preevaluación",
                modos,
                format_func=lambda valor: MODOS_ANALISIS[valor]["titulo"],
                captions=[MODOS_ANALISIS[valor]["descripcion"] for valor in modos],
                key="selector_modo_inicio",
                label_visibility="collapsed",
                width="stretch",
            )
            st.caption(f"Recibirá: {MODOS_ANALISIS[modo]['resultado']}")

    cancelar, continuar = st.columns([1, 1])
    if cancelar.button("Cancelar", use_container_width=True):
        cerrar_selector_analisis()
        st.rerun()
    if continuar.button(
        "Abrir plataforma",
        type="primary",
        use_container_width=True,
    ):
        elegir_modo(modo)
        st.rerun()


def abrir_vista(vista):
    st.session_state["seccion_tablero"] = vista
    st.query_params["seccion"] = {
        SECCION_MAPA: "mapa",
        SECCION_OBJETIVO: "objetivo",
        SECCION_DATOS: "datos",
        SECCION_METODO: "metodo",
        SECCION_ACERCA: "acerca",
    }.get(vista, "mapa")
    if vista == SECCION_MAPA:
        st.session_state["mostrar_resultados"] = False


def mostrar_cabecera(titulo, subtitulo, descripcion, alcance=None):
    alcance_html = f"<small>{alcance}</small>" if alcance else ""
    st.markdown(
        f"""
        <div class="entrada">
          <h1>{titulo}</h1>
          <div class="subtitulo">{subtitulo}</div>
          <p>{descripcion}</p>
          {alcance_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_objetivo():
    mostrar_cabecera(
        "¿Para qué sirve esta preevaluación?",
        "Convierte un área de interés en evidencia inicial para orientar una decisión.",
        "En pocos pasos, la aplicación ayuda a explicar por qué un territorio merece una "
        "revisión más detallada, dónde conviene mirar primero y qué información respalda esa orientación.",
        "Herramienta de orientación · no sustituye una visita de campo ni una decisión técnica o legal definitiva",
    )
    st.markdown("## Propósito y utilidad de la preevaluación")
    st.markdown(
        """
        <div class="ruta-simple" aria-label="Cómo ayuda la preevaluación">
          <div class="ruta-paso"><span class="ruta-numero">1</span><b>Seleccione el área</b><span>Use una finca, una subcuenca, un polígono dibujado o la cuenca completa.</span></div>
          <div class="ruta-paso"><span class="ruta-numero">2</span><b>Reúna indicios</b><span>La aplicación consulta señales satelitales, corredores publicados y estructura del bosque según el enfoque elegido.</span></div>
          <div class="ruta-paso"><span class="ruta-numero">3</span><b>Sustente el siguiente paso</b><span>Reciba una orientación, un mapa y evidencia trazable para decidir si conviene profundizar o visitar el área.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("## Qué puede concluir y qué debe confirmar")
    st.markdown(
        """
        <div class="alcance-grid">
          <section class="alcance-card">
            <h3>La aplicación sí permite</h3>
            <ul>
              <li>detectar indicios que justifican una revisión más detallada;</li>
              <li>comparar varias fuentes sin exigir experiencia previa en teledetección;</li>
              <li>ubicar sectores donde coinciden señales o donde la conectividad merece atención;</li>
              <li>documentar fuentes, períodos, reglas y parámetros para respaldar la conversación.</li>
            </ul>
          </section>
          <section class="alcance-card">
            <h3>La aplicación no pretende</h3>
            <ul>
              <li>confirmar en campo una pérdida, degradación o causa específica;</li>
              <li>demostrar conectividad funcional o movimiento de una especie;</li>
              <li>emitir una certificación, sanción o conclusión legal;</li>
              <li>determinar por sí sola cumplimiento de EUDR u otra norma.</li>
            </ul>
          </section>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="nota-alcance"><b>Resultado esperado:</b> una preevaluación reproducible
        que ayuda a justificar por qué un área debe tomarse en cuenta. La decisión final debe
        complementarse con conocimiento local, documentos, imágenes recientes y, cuando corresponda,
        verificación de campo.</div>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Elegir análisis",
        type="primary",
        width="stretch",
        on_click=abrir_selector_analisis,
    )


def mostrar_metodo():
    mostrar_cabecera(
        "Cómo se construye la preevaluación",
        "Una explicación sencilla primero; las reglas técnicas permanecen disponibles después.",
        "Cada fuente responde una pregunta diferente. La aplicación conserva esas diferencias, "
        "aplica reglas documentadas y presenta una orientación que puede rastrearse hasta sus datos de origen.",
        "Los años del comparador cambian el mapa, pero no modifican las reglas del índice configurado",
    )
    st.markdown("## El proceso en cinco pasos")
    st.markdown(
        """
        <div class="metodo-pasos" aria-label="Pasos del método">
          <div class="metodo-paso"><span class="metodo-numero">1</span><b>Delimitar</b><span>El área elegida se recorta al límite institucional de la cuenca cuando corresponde.</span></div>
          <div class="metodo-paso"><span class="metodo-numero">2</span><b>Consultar</b><span>Se solicitan únicamente las fuentes necesarias para el enfoque seleccionado.</span></div>
          <div class="metodo-paso"><span class="metodo-numero">3</span><b>Medir</b><span>Las señales se expresan en hectáreas, porcentajes, cambios o métricas de conectividad.</span></div>
          <div class="metodo-paso"><span class="metodo-numero">4</span><b>Aplicar reglas</b><span>Los umbrales y pesos documentados convierten los indicios en una orientación comparable.</span></div>
          <div class="metodo-paso"><span class="metodo-numero">5</span><b>Explicar</b><span>El resumen, el mapa y el registro metodológico muestran qué influyó y qué no.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Qué aporta cada fuente")
    st.caption("La tabla usa lenguaje cotidiano. La identificación técnica completa permanece en el registro metodológico descargable.")
    st.dataframe(
        [
            {
                "Fuente": "JRC Tropical Moist Forest",
                "Pregunta que ayuda a responder": "¿Hay indicios de degradación o deforestación en bosque tropical?",
                "Referencia": str(PERIODOS_ANALISIS["jrc_diagnostico"]),
                "Papel": "Señal forestal principal",
            },
            {
                "Fuente": "Hansen Global Forest Change",
                "Pregunta que ayuda a responder": "¿Se registró pérdida anual de cobertura arbórea después de 2020?",
                "Referencia": f"2021–{PERIODOS_ANALISIS['hansen_diagnostico']}",
                "Papel": "Señal forestal principal",
            },
            {
                "Fuente": "ESRI Land Use/Land Cover",
                "Pregunta que ayuda a responder": "¿Sectores clasificados como árboles pasaron a otra cobertura?",
                "Referencia": f"{PERIODOS_ANALISIS['esri_inicial']}–{PERIODOS_ANALISIS['esri_final']}",
                "Papel": "Señal corroborativa",
            },
            {
                "Fuente": "Sentinel-2 · NDVI",
                "Pregunta que ayuda a responder": "¿Disminuyó de forma importante el vigor de la vegetación?",
                "Referencia": f"{PERIODOS_ANALISIS['ndvi_inicial']}–{PERIODOS_ANALISIS['ndvi_final']}",
                "Papel": "Señal corroborativa",
            },
            {
                "Fuente": "GEDI / OpenForis",
                "Pregunta que ayuda a responder": "¿Qué contexto aporta la altura observada del dosel?",
                "Referencia": "Producto disponible",
                "Papel": "Contexto estructural",
            },
            {
                "Fuente": "ERI indicativo",
                "Pregunta que ayuda a responder": "¿Qué componente ecológico presenta la condición relativa más limitada?",
                "Referencia": "Dynamic World + GEDI + DEM + MERIT Hydro",
                "Papel": "Lectura complementaria; no cambia la prioridad",
            },
            {
                "Fuente": "Almanaque Azul",
                "Pregunta que ayuda a responder": "¿El área coincide con corredores naturales publicados?",
                "Referencia": "Versión publicada 2024.05",
                "Papel": "Valor estratégico",
            },
            {
                "Fuente": "SINIA–MiAMBIENTE · Bosque y otros usos",
                "Pregunta que ayuda a responder": "¿Cómo se distribuyen y relacionan los fragmentos de bosque?",
                "Referencia": "2021",
                "Papel": "Estructura y conectividad",
            },
        ],
        hide_index=True,
        width="stretch",
    )

    with st.expander("Para usuarios técnicos: pesos, umbrales y separación de resultados", expanded=False):
        st.markdown(
            f"""
            **Índice de indicios territoriales**

            - JRC: **{PESOS_INDICE['tmf']:.1f}** puntos.
            - Hansen: **{PESOS_INDICE['hansen']:.1f}** puntos.
            - ESRI: **{PESOS_INDICE['esri']:.1f}** puntos.
            - GEDI: **{PESOS_INDICE['gedi']:.1f}** puntos.
            - NDVI: **{PESOS_INDICE['ndvi']:.1f}** puntos.
            - Máximo configurado: **{PUNTAJE_MAXIMO:.1f}** puntos.

            **ERI indicativo, presentado por separado**

            - Integridad estructural: **{PESOS_ERI['integridad_estructural'] * 100:.0f}%**.
            - Conectividad local: **{PESOS_ERI['conectividad'] * 100:.0f}%**.
            - Estabilidad topográfica: **{PESOS_ERI['estabilidad_topografica'] * 100:.0f}%**.
            - Proximidad riparia: **{PESOS_ERI['proximidad_riparia'] * 100:.0f}%**.

            El ERI se expresa entre 0 y 1 y **no se suma** al índice anterior ni a la
            prioridad de visita. Es una síntesis exploratoria que requiere calibración
            y validación de campo.

            La señal NDVI exige simultáneamente una disminución de
            **{abs(UMBRALES_INDICE['ndvi_delta_disminucion']):.2f}**, al menos
            **{UMBRALES_INDICE['ndvi_disminucion_ha']:.2f} ha** y
            **{UMBRALES_INDICE['ndvi_disminucion_pct']:.0f}% del área**, con una cobertura
            válida mínima de **{UMBRALES_INDICE['ndvi_cobertura_minima_pct']:.0f}%**.

            Los corredores publicados **no aumentan el índice satelital**. La opción integral
            los incorpora por separado para orientar la visita; un corredor sin indicios de
            cambio no produce por sí solo una prioridad alta. La estructura del bosque ayuda
            a decidir **dónde** revisar, pero no recibe un peso inventado.
            """
        )

    with st.expander("Alcance técnico y limitaciones", expanded=False):
        st.markdown(
            """
            - Cada producto tiene fecha, resolución, clasificación y cobertura propias.
            - Una coincidencia entre fuentes fortalece la necesidad de revisar, pero no demuestra causalidad.
            - NDVI puede responder a humedad, estacionalidad, cultivos, nubes o sombras y no identifica por sí solo bosque natural.
            - GEDI tiene cobertura espacial limitada y se interpreta como contexto, no como pérdida confirmada.
            - La red de fragmentos representa conectividad estructural potencial; no modela especies, conducta ni conectividad funcional.
            - La conectividad del ERI es un proxy de cobertura local; no reemplaza ECA/A ni un modelo funcional por especie.
            - Los resultados deben contrastarse con conocimiento local, imágenes recientes, documentos y campo.
            """
        )

    st.button(
        "Elegir análisis",
        type="primary",
        width="stretch",
        on_click=abrir_selector_analisis,
    )


def mostrar_datos():
    mostrar_cabecera(
        "Uso y atribución de los datos",
        "Cada capa conserva su función, su escala y su fuente original.",
        "Los límites de la cuenca y las subcuencas se sirven desde archivos locales del portal. "
        "Las capas ráster se consultan en Google Earth Engine únicamente para el área elegida.",
        "Los productos no se fusionan en una verdad única: cada uno aporta una evidencia diferente",
    )
    st.markdown("## Capas territoriales del portal")
    st.markdown(
        """
        <div class="alcance-grid">
          <section class="alcance-card">
            <h3>Límites locales</h3>
            <ul>
              <li>límite de la Cuenca Hidrográfica del Canal de Panamá;</li>
              <li>subcuencas incluidas en el archivo territorial del portal;</li>
              <li>se usan para seleccionar, recortar y centrar el análisis.</li>
            </ul>
          </section>
          <section class="alcance-card">
            <h3>Capas de análisis</h3>
            <ul>
              <li>JRC TMF, Hansen, ESRI, Sentinel-2 NDVI y GEDI;</li>
              <li>corredores publicados y bosque 2021 para conectividad;</li>
              <li>relieve e hidrología como componentes del ERI indicativo.</li>
            </ul>
          </section>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("## Principios de uso")
    st.markdown(
        """
        - La aplicación consulta solo las capas necesarias para el análisis seleccionado.
        - Las fechas, resoluciones y definiciones no son idénticas entre productos.
        - Una coincidencia entre fuentes aumenta la evidencia para revisar, pero no confirma una causa.
        - La atribución técnica completa acompaña los resultados y las descargas metodológicas.
        """
    )
    st.info(
        "El visor presenta una preevaluación. Los resultados deben contrastarse con "
        "conocimiento local, documentos, imágenes recientes y verificación de campo."
    )
    st.button(
        "Elegir análisis",
        type="primary",
        width="stretch",
        on_click=abrir_selector_analisis,
    )


def mostrar_acerca():
    mostrar_cabecera(
        "Acerca del visor",
        "Una herramienta para preparar y documentar revisiones territoriales.",
        "El visor reúne evidencia satelital, corredores publicados y estructura del bosque "
        "para ayudar a decidir dónde conviene profundizar, sin sustituir la verificación de campo.",
        "Preevaluación indicativa · no constituye certificación ni determinación legal",
    )
    st.markdown("## Qué problema ayuda a resolver")
    st.markdown(
        """
        <div class="alcance-grid">
          <section class="alcance-card">
            <h3>Para personas usuarias</h3>
            <ul>
              <li>seleccionar una finca, subcuenca, polígono o la cuenca completa;</li>
              <li>consultar capas sin necesitar experiencia previa en teledetección;</li>
              <li>obtener una lectura resumida y evidencia descargable;</li>
              <li>reconocer qué información debe confirmarse con campo o documentos.</li>
            </ul>
          </section>
          <section class="alcance-card">
            <h3>Para equipos técnicos</h3>
            <ul>
              <li>revisar fuentes, períodos, pesos, umbrales y parámetros;</li>
              <li>comparar años y consultar capas por fuente;</li>
              <li>descargar resultados metodológicos y geográficos;</li>
              <li>reproducir y documentar la preevaluación.</li>
            </ul>
          </section>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="nota-alcance"><b>Alcance:</b> los resultados orientan una revisión.
        No confirman causas de pérdida, movimiento de fauna, cumplimiento normativo ni
        condiciones verificadas en campo.</div>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Elegir análisis",
        type="primary",
        width="stretch",
        on_click=abrir_selector_analisis,
    )


if st.session_state.get("seccion_tablero") == "Análisis":
    st.session_state["seccion_tablero"] = SECCION_MAPA

seccion_consulta = str(st.query_params.get("seccion", "")).strip().lower()
modo_consulta = str(st.query_params.get("modo", "")).strip().lower()
selector_consulta = str(st.query_params.get("selector", "")).strip().lower()
if (
    modo_consulta in MODOS_ANALISIS
    and st.session_state.get("modo_analisis") != modo_consulta
):
    st.session_state["modo_analisis"] = modo_consulta
    st.session_state["selector_modo_sidebar"] = modo_consulta
    st.session_state["seccion_tablero"] = SECCION_MAPA
    st.session_state["mostrar_resultados"] = False
if seccion_consulta == "inicio":
    st.session_state.pop("modo_analisis", None)
    st.session_state.pop("selector_modo_sidebar", None)
    st.session_state["seccion_tablero"] = SECCION_MAPA
elif seccion_consulta in {"mapa", "plataforma"}:
    st.session_state["seccion_tablero"] = SECCION_MAPA
elif seccion_consulta == "objetivo":
    st.session_state["seccion_tablero"] = SECCION_OBJETIVO
elif seccion_consulta == "datos":
    st.session_state["seccion_tablero"] = SECCION_DATOS
elif seccion_consulta == "metodo":
    st.session_state["seccion_tablero"] = SECCION_METODO
elif seccion_consulta in {"acerca", "faq"}:
    st.session_state["seccion_tablero"] = SECCION_ACERCA

seccion_tablero = st.session_state.get("seccion_tablero", SECCION_MAPA)
if seccion_tablero not in SECCIONES_PRINCIPALES:
    seccion_tablero = SECCION_MAPA
    st.session_state["seccion_tablero"] = seccion_tablero

mostrar_cabecera_portal(seccion_tablero)

seccion_anterior = st.session_state.get("_seccion_publica_anterior")
if (
    seccion_tablero == SECCION_MAPA
    and seccion_anterior
    in (SECCION_OBJETIVO, SECCION_DATOS, SECCION_METODO, SECCION_ACERCA)
):
    st.session_state["mostrar_resultados"] = False
st.session_state["_seccion_publica_anterior"] = seccion_tablero

if seccion_tablero == SECCION_OBJETIVO:
    mostrar_objetivo()
    st.stop()
if seccion_tablero == SECCION_DATOS:
    mostrar_datos()
    st.stop()
if seccion_tablero == SECCION_METODO:
    mostrar_metodo()
    st.stop()
if seccion_tablero == SECCION_ACERCA:
    mostrar_acerca()
    st.stop()


modo_analisis = st.session_state.get("modo_analisis")
if modo_analisis not in MODOS_ANALISIS:
    st.session_state.pop("modo_analisis", None)
    modo_analisis = None

if modo_analisis is None:
    mostrar_hero_inicio()
    mostrar_acceso_selector()
    if selector_consulta in {"1", "true", "si", "sí"}:
        mostrar_selector_dialogo()
    st.stop()


APLICACION_ACTIVA = Path(__file__).with_name("app_experiencia.py")
if not APLICACION_ACTIVA.is_file():
    raise FileNotFoundError(
        "No se encontró app_experiencia.py, la implementación activa del visor."
    )

runpy.run_path(str(APLICACION_ACTIVA), run_name="__main__")
