"""Componentes de interfaz de la Fase 4 inspirados en el HTML suministrado.

Este módulo no realiza cálculos científicos. Conserva la configuración del
asistente y presenta la gramática visual del portal original para que el motor
temporal pueda reutilizarla sin mezclar CSS, navegación y procesamiento.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


TIPOS_ANALISIS = {
    "cobertura": {
        "titulo": "Cobertura forestal",
        "descripcion": "Compara bosque y no bosque en dos años equivalentes.",
    },
    "fragmentacion": {
        "titulo": "Fragmentación",
        "descripcion": "Recalcula superficie, número y aislamiento de parches.",
    },
    "conectividad": {
        "titulo": "Conectividad",
        "descripcion": "Recalcula enlaces y componentes con el mismo umbral.",
    },
    "integral": {
        "titulo": "Análisis integral",
        "descripcion": "Reúne cobertura, fragmentación y conectividad temporal.",
    },
}

UNIDADES_ANALISIS = {
    "dibujo": "Dibujar un polígono",
    "subcuenca": "Seleccionar una subcuenca",
    "cuenca": "Toda la CHCP",
}


@dataclass(frozen=True)
class ConfiguracionAnalisis:
    tipo: str
    unidad: str
    subcuenca: str | None
    fuente: str
    anio_inicial: int
    anio_final: int
    distancia_maxima_m: float
    area_minima_parche_ha: float

    def firma(self, area_json: str | None) -> tuple:
        """Firma estable para impedir ejecuciones duplicadas o desactualizadas."""

        return (
            self.tipo,
            self.unidad,
            self.subcuenca,
            self.fuente,
            self.anio_inicial,
            self.anio_final,
            area_json,
            self.distancia_maxima_m,
            self.area_minima_parche_ha,
        )


CSS_FASE4 = r"""
<style>
:root{
  --azul:#0a4393;--azul-2:#1d529b;--azul-tinta:#062a5e;
  --azul-suave:#eef1f7;--azul-linea:#d6deeb;--azul-medio:#6085b9;
  --verde:#77cc09;--verde-osc:#4f8f00;--amarillo:#fabc20;--rojo:#d0442c;
  --bg:#fff;--bg-2:#f6f8fb;--ink:#1b2433;--muted:#566176;
  --faint:#8a94a6;--line:#e1e6ee;--r:6px;
}

/* El explorador ocupa la ventana, igual que plataforma.html. */
.block-container:has(.fase4-plataforma){padding:118px 0 0!important;}
.block-container:has(.fase4-plataforma)>div{gap:0!important;}
.fase4-plataforma{height:0;margin:0;padding:0;}
.fase4-marca-seccion{padding:11px 15px;border-bottom:1px solid var(--line);background:#fff;}
.fase4-marca-seccion small{display:block;color:var(--azul-medio);font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}
.fase4-marca-seccion strong{display:block;margin-top:2px;color:var(--azul-tinta);font-size:15px;}

/* Panel izquierdo: pestañas y grupos del HTML original. */
[data-testid="stSidebar"]{top:118px!important;height:calc(100vh - 118px)!important;}
[data-testid="stSidebar"] [data-testid="stTabs"] [data-baseweb="tab-panel"]{padding-bottom:128px!important;}
[data-testid="stSidebar"] .stCheckbox label{min-height:38px;padding:5px 2px;color:var(--ink);}
[data-testid="stSidebar"] .stCheckbox [data-testid="stCheckbox"]{border-radius:999px!important;}
.fase4-grupo-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:-4px 0 8px;color:var(--faint);font-size:11px;}
.fase4-tag{display:inline-flex;align-items:center;min-height:24px;padding:2px 8px;border:1px solid #c7df9b;border-radius:5px;background:#f5faeb;color:var(--verde-osc);font-size:10px;font-weight:700;}
.fase4-tag.alt{border-color:#f1d28a;background:#fff8e7;color:#8a5b00;}
.fase4-side-actions{position:fixed;left:0;bottom:0;z-index:35;display:grid;grid-template-columns:1fr .72fr;gap:9px;width:340px;padding:12px 14px;border-top:1px solid var(--line);background:#fff;}
.fase4-side-actions-spacer{height:76px;}

/* Centro cartográfico y panel derecho. */
.fase4-topline{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:66px;padding:10px 15px;border-bottom:1px solid var(--line);background:#fff;}
.fase4-topline strong{display:block;margin:0!important;color:var(--azul-tinta)!important;font-size:17px!important;line-height:1.25!important;}
.fase4-topline p{margin:2px 0 0!important;color:var(--muted)!important;font-size:11px!important;}
.fase4-periodo{display:inline-flex;min-height:31px;align-items:center;padding:5px 10px;border:1px solid var(--azul-linea);border-radius:999px;color:var(--azul);font-size:11px;font-weight:700;white-space:nowrap;}
.fase4-map-card{border-right:1px solid var(--line);background:var(--sea,#e6ebf3);}
.block-container:has(.fase4-plataforma) iframe[title="streamlit_folium.st_folium"]{height:calc(100vh - 184px)!important;min-height:590px!important;}
.fase4-estado-vacio{display:grid;min-height:calc(100vh - 190px);place-items:center;padding:36px;background:var(--azul-suave);text-align:center;}
.fase4-estado-vacio div{max-width:420px;}
.fase4-estado-vacio h2{color:var(--azul)!important;font-size:22px!important;}
.fase4-estado-vacio p{color:var(--muted)!important;line-height:1.6;}

.fase4-res-h{position:relative;padding:18px 20px 16px;border-bottom:5px solid var(--verde);background:var(--azul);color:#fff;}
.fase4-res-h small{display:block;color:var(--verde);font-size:10.5px;font-weight:800;letter-spacing:.09em;text-transform:uppercase;}
.fase4-res-h h2{margin:4px 0 0!important;color:#fff!important;font-size:20px!important;font-weight:600!important;line-height:1.2!important;}
.fase4-res-h p{margin:5px 0 0;color:#dbe7f7;font-size:11px;}
.fase4-res-body{padding:14px;background:#fff;}
.fase4-big{margin-bottom:10px;padding:14px;border-radius:var(--r);background:var(--azul-suave);}
.fase4-big small,.fase4-mc small{display:block;color:var(--azul-medio);font-size:9.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;}
.fase4-big strong{display:block;margin-top:4px;color:var(--azul-tinta);font-size:23px;}
.fase4-cards{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;}
.fase4-mc{min-height:78px;padding:11px;border:1px solid var(--azul-linea);border-radius:var(--r);background:#fff;}
.fase4-mc strong{display:block;margin-top:5px;color:var(--azul-tinta);font-size:16px;line-height:1.2;}
.fase4-delta-neg{color:var(--rojo)!important}.fase4-delta-pos{color:#25864c!important}
.fase4-chart-title{margin:12px 0 7px;color:var(--azul-tinta);font-size:12px;font-weight:800;}
.fase4-warning{margin-top:10px;padding:10px 12px;border-left:4px solid var(--amarillo);background:#fff8e5;color:var(--muted);font-size:11px;line-height:1.45;}

/* Modal de cuatro pasos: misma jerarquía que dlg/stp del HTML. */
section[role="dialog"]{width:min(900px,calc(100vw - 32px))!important;max-width:900px!important;padding:0!important;border-radius:8px!important;overflow:hidden!important;}
section[role="dialog"]>h2{position:sticky!important;top:0!important;z-index:4!important;margin:0!important;padding:19px 62px 17px 24px!important;border-bottom:5px solid var(--verde)!important;background:var(--azul)!important;color:#fff!important;font-size:20px!important;}
section[role="dialog"]>h2 p{color:#fff!important;}
section[role="dialog"]>button[aria-label="Close"]{top:14px!important;right:17px!important;z-index:3!important;color:#fff!important;}
section[role="dialog"]>div:last-child{padding:20px 24px 22px!important;}
div[role="dialog"] [data-testid="stDialogHeader"]{min-height:66px!important;padding:14px 22px!important;border-bottom:5px solid var(--verde);background:var(--azul)!important;}
div[role="dialog"] [data-testid="stDialogHeader"] h2{font-size:20px!important;font-weight:600!important;}
.fase4-stepper{display:flex;flex-direction:column;gap:5px;padding:3px 0;}
.fase4-step{display:flex;align-items:center;gap:9px;min-height:43px;padding:7px 10px;border-radius:999px;color:var(--muted);font-size:12px;font-weight:700;}
.fase4-step i{display:grid;flex:0 0 25px;width:25px;height:25px;place-items:center;border:1.5px solid var(--azul-linea);border-radius:50%;background:#fff;color:var(--muted);font-style:normal;}
.fase4-step.current{background:var(--azul-suave);color:var(--azul);}
.fase4-step.current i{border-color:var(--azul);background:var(--azul);color:#fff;}
.fase4-step.done{color:var(--verde-osc);}.fase4-step.done i{border-color:var(--verde);background:var(--verde);color:#183400;}
.fase4-wizard-title{margin:2px 0 2px;color:var(--azul-tinta);font-size:20px;font-weight:700;}
.fase4-wizard-help{margin:0 0 12px;color:var(--muted);font-size:12px;line-height:1.5;}
.fase4-review{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.fase4-review div{padding:11px;border:1px solid var(--azul-linea);border-radius:var(--r);background:var(--azul-suave);}
.fase4-review small{display:block;color:var(--azul-medio);font-size:9px;font-weight:800;text-transform:uppercase;}
.fase4-review b{display:block;margin-top:3px;color:var(--azul-tinta);font-size:12px;}

@media(max-width:1050px){
  .block-container:has(.fase4-plataforma) iframe[title="streamlit_folium.st_folium"]{height:620px!important;min-height:620px!important;}
}
@media(max-width:900px){
  .block-container:has(.fase4-plataforma){padding-top:76px!important;}
  [data-testid="stSidebar"]{top:76px!important;height:calc(100vh - 76px)!important;}
  .fase4-side-actions{width:min(340px,100vw);}
  .fase4-topline{align-items:flex-start;flex-direction:column;}
  .block-container:has(.fase4-plataforma) iframe[title="streamlit_folium.st_folium"]{height:66vh!important;min-height:480px!important;}
}
@media(max-width:640px){
  .fase4-stepper{display:grid;grid-template-columns:repeat(4,1fr);}
  .fase4-step{justify-content:center;padding:6px}.fase4-step span{display:none}
  .fase4-review{grid-template-columns:1fr}
}
</style>
"""


def inyectar_css_fase4() -> None:
    st.markdown(CSS_FASE4, unsafe_allow_html=True)


def configurar_asistente_inicial() -> None:
    valores = {
        "fase4_paso": 1,
        "fase4_tipo": "integral",
        "fase4_unidad": "dibujo",
        "fase4_fuente": "jrc_tmf",
        "fase4_distancia": 500,
        "fase4_area_minima": 0.1,
    }
    for clave, valor in valores.items():
        st.session_state.setdefault(clave, valor)


def stepper_html(paso: int) -> str:
    etiquetas = ("Tipo de análisis", "Área de interés", "Criterios", "Revisión")
    filas = []
    for numero, etiqueta in enumerate(etiquetas, 1):
        clase = "current" if numero == paso else "done" if numero < paso else ""
        simbolo = "✓" if numero < paso else str(numero)
        filas.append(
            f'<div class="fase4-step {clase}"><i>{simbolo}</i><span>{etiqueta}</span></div>'
        )
    return '<div class="fase4-stepper" aria-label="Pasos del análisis">' + "".join(filas) + "</div>"


def construir_configuracion() -> ConfiguracionAnalisis:
    return ConfiguracionAnalisis(
        tipo=str(st.session_state["fase4_tipo"]),
        unidad=str(st.session_state["fase4_unidad"]),
        subcuenca=st.session_state.get("fase4_subcuenca"),
        fuente=str(st.session_state["fase4_fuente"]),
        anio_inicial=int(st.session_state["fase4_anio_inicial"]),
        anio_final=int(st.session_state["fase4_anio_final"]),
        distancia_maxima_m=float(st.session_state["fase4_distancia"]),
        area_minima_parche_ha=float(st.session_state["fase4_area_minima"]),
    )
