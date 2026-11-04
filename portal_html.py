"""Presentación visual basada en el portal HTML entregado por la usuaria."""

from __future__ import annotations

import html

import streamlit as st


CSS_PORTAL_HTML = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap');
:root{
  --azul:#0a4393;--azul-2:#1d529b;--azul-tinta:#062a5e;
  --azul-suave:#eef1f7;--azul-linea:#d6deeb;--azul-medio:#6085b9;
  --verde:#77cc09;--verde-osc:#4f8f00;--amarillo:#fabc20;--rojo:#d0442c;
  --bg:#fff;--bg-2:#f6f8fb;--ink:#1b2433;--muted:#566176;
  --faint:#8a94a6;--line:#e1e6ee;--nav-h:118px;--r:6px;
  --portal-font:"DM Sans",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --portal-shadow:0 1px 2px rgba(10,30,70,.06),0 8px 24px rgba(10,30,70,.08);
}
html,body,[data-testid="stAppViewContainer"],.stApp{font-family:var(--portal-font)!important;background:#fff!important;color:var(--ink)!important;}
[data-testid="stHeader"]{height:0!important;min-height:0!important;background:transparent!important;}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important;}
.block-container{max-width:none!important;padding:calc(var(--nav-h) + 12px) 14px 14px!important;}
.block-container [data-testid="stVerticalBlock"]{gap:10px;}
button,select,input,textarea{font-family:var(--portal-font)!important;}
button,[role="button"]{min-height:44px;}
:focus-visible{outline:2px solid var(--verde)!important;outline-offset:2px!important;}

/* Encabezado: copia de la composición del HTML entregado. */
.ref-nav{position:fixed;inset:0 0 auto 0;z-index:999999;height:var(--nav-h);background:var(--azul);color:#fff;box-shadow:none;}
.ref-skip{position:fixed;left:16px;top:-70px;z-index:1000000;padding:10px 14px;border-radius:0 0 4px 4px;background:#fff;color:var(--azul)!important;font-weight:700;text-decoration:none;}
.ref-skip:focus{top:0;}
.ref-nav-in{max-width:1800px;height:100%;margin:0 auto;padding:0 max(24px,env(safe-area-inset-right,0px)) 0 max(24px,env(safe-area-inset-left,0px));}
.ref-util{height:35px;display:flex;justify-content:flex-end;align-items:center;gap:22px;font-size:12.5px;}
.ref-util a,.ref-util span{color:#fff;text-decoration:none;opacity:.94;}
.ref-main-row{height:83px;display:flex;align-items:center;gap:24px;border-bottom:1px solid rgba(255,255,255,.18);}
.ref-wm{display:flex;align-items:center;gap:10px;color:#fff!important;text-decoration:none!important;flex:none;}
.ref-wm svg{width:44px;height:44px;}
.ref-wm b{display:block;color:#fff;font-size:22px;line-height:1;font-weight:700;}
.ref-wm small{display:block;margin-top:4px;color:#fff;font-size:8.5px;line-height:1.15;font-weight:700;letter-spacing:.09em;text-transform:uppercase;opacity:.9;}
.ref-links{display:flex;align-items:center;gap:2px;margin-left:auto;}
.ref-links a{display:inline-flex;align-items:center;min-height:40px;padding:8px 11px;border-radius:4px;color:#fff!important;text-decoration:none!important;font-size:12.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;white-space:nowrap;}
.ref-links a:hover{background:rgba(255,255,255,.1);}
.ref-links a[aria-current="page"]{border-radius:0;box-shadow:inset 0 -3px 0 var(--verde);}
.ref-chev{display:inline-block;width:7px;height:7px;margin-left:8px;border-right:2px solid var(--verde);border-bottom:2px solid var(--verde);transform:rotate(45deg) translate(-2px,-2px);}
.ref-nav-btns{display:flex;align-items:center;gap:10px;}
.ref-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:42px;border:1.5px solid transparent;border-radius:999px;padding:8px 19px;font-size:13px;font-weight:700;text-decoration:none!important;white-space:nowrap;}
.ref-btn-w{background:#fff;color:var(--azul)!important;}
.ref-btn-o{border-color:rgba(255,255,255,.85);background:transparent;color:#fff!important;}
.ref-btn svg{width:15px;height:15px;}
.ref-lang,.ref-mobile-menu{position:relative;}
.ref-lang>summary,.ref-mobile-menu>summary{list-style:none;cursor:pointer;}
.ref-lang>summary::-webkit-details-marker,.ref-mobile-menu>summary::-webkit-details-marker{display:none;}
.ref-lang-menu,.ref-mobile-links{position:absolute;right:0;top:calc(100% + 7px);min-width:160px;padding:7px;border:1px solid var(--line);border-radius:var(--r);background:#fff;box-shadow:var(--portal-shadow);color:var(--ink);}
.ref-lang-menu button{display:flex;width:100%;min-height:40px;align-items:center;justify-content:space-between;gap:10px;padding:8px 10px;border:0;border-radius:4px;background:transparent;color:var(--ink);font-size:13.5px;text-align:left;}
.ref-lang-menu button[disabled]{color:var(--faint);cursor:default;}
.ref-mobile-menu{display:none;}
.ref-burger{display:inline-flex;min-height:42px;align-items:center;justify-content:center;padding:8px 16px;border:1.5px solid rgba(255,255,255,.85);border-radius:999px;color:#fff;font-size:13px;font-weight:700;}
.ref-mobile-links{display:flex;min-width:240px;flex-direction:column;padding:8px;}
.ref-mobile-links a{display:block;min-height:44px;padding:12px;border-radius:4px;color:var(--azul)!important;font-size:13px;font-weight:700;text-decoration:none!important;}
.ref-mobile-links a:hover{background:var(--azul-suave);}

/* Portada del portal. */
.ref-hero{position:relative;min-height:455px;margin:-12px -14px 0;background:var(--azul);color:#fff;overflow:hidden;}
.ref-hero-in{position:relative;z-index:1;max-width:1180px;margin:0 auto;padding:40px 20px 165px;}
.ref-hero h1{max-width:22ch;margin:0;color:#fff!important;font-size:clamp(34px,4.4vw,54px);font-weight:500;line-height:1.08;letter-spacing:-.02em;}
.ref-hero p{max-width:62ch;margin:24px 0 0;color:#fff!important;font-size:15px;line-height:1.65;text-align:justify;}
.ref-hero .ref-acts{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px;}
.ref-hero-cut{position:absolute;left:0;right:0;bottom:-1px;width:100%;height:150px;display:block;z-index:0;}
.ref-start{max-width:1180px;margin:0 auto;padding:18px 6px 24px;}
.ref-meta{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin:0 0 30px;background:var(--azul-suave);border-radius:var(--r);overflow:hidden;}
.ref-meta>div{display:flex;flex-direction:column;gap:3px;padding:16px 18px;}
.ref-meta>div+div{border-left:1px solid var(--azul-linea);}
.ref-meta span{color:var(--azul-medio)!important;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;}
.ref-meta b{color:var(--azul)!important;font-size:14.5px;}
.ref-intro{max-width:760px;margin:0 auto 26px;text-align:center;}
.ref-intro h2{margin:0;color:var(--azul)!important;font-size:clamp(26px,3vw,34px);}
.ref-intro p{margin:12px 0 0;color:var(--muted)!important;line-height:1.6;}
.ref-modes{margin:0 -14px;padding:30px 20px 44px;background:var(--bg-2);}
.ref-mode-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;max-width:1180px;margin:0 auto;}
.ref-mode-card{display:flex;min-width:0;min-height:290px;flex-direction:column;gap:12px;padding:26px 26px 22px;border-radius:var(--r);background:var(--azul-suave);color:var(--ink)!important;text-decoration:none!important;transition:box-shadow .15s ease,transform .15s ease;}
.ref-mode-card:hover{box-shadow:var(--portal-shadow);transform:translateY(-2px);}
.ref-mode-card .date{color:var(--azul)!important;font-size:11.5px;font-weight:700;letter-spacing:.04em;line-height:1.35;text-transform:uppercase;}
.ref-mode-card h3{margin:0;color:var(--azul)!important;font-size:19px;line-height:1.25;}
.ref-mode-card p{margin:0;color:var(--ink)!important;font-size:13.5px;line-height:1.55;}
.ref-mode-card .result{padding-top:10px;border-top:1px solid var(--azul-linea);}
.ref-mode-card .more{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:auto;color:var(--azul)!important;font-size:14px;font-weight:700;}
.ref-mode-card .more .ref-chev{flex:none;}
.ref-selector-entry{display:flex;max-width:1180px;align-items:center;justify-content:space-between;gap:24px;margin:0 auto;padding:26px;border-radius:var(--r);background:var(--azul-suave);}
.ref-selector-entry .eyebrow{display:block;margin-bottom:5px;color:var(--azul)!important;font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;}
.ref-selector-entry h2{margin:0;color:var(--azul)!important;font-size:22px;}
.ref-selector-entry p{max-width:70ch;margin:7px 0 0;color:var(--muted)!important;line-height:1.55;}
.ref-selector-entry .ref-btn{flex:none;background:var(--azul);color:#fff!important;}

/* Selector modal: reproduce el asistente del HTML de referencia. */
div[role="dialog"]{border-radius:10px!important;overflow:hidden!important;}
div[role="dialog"] [data-testid="stDialogHeader"]{padding:16px 22px!important;background:var(--azul)!important;}
div[role="dialog"] [data-testid="stDialogHeader"] h2,div[role="dialog"] [data-testid="stDialogHeader"] button{color:#fff!important;}
div[role="dialog"] button{min-height:44px!important;}
div[role="dialog"] button[aria-label="Close"]{display:grid!important;width:44px!important;min-width:44px!important;height:44px!important;padding:0!important;place-items:center!important;}
.selector-pasos{list-style:none;margin:0;padding:8px 6px;display:flex;flex-direction:column;gap:6px;}
.selector-pasos li{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:999px;color:var(--muted);font-size:13px;font-weight:700;}
.selector-pasos li i{display:grid;place-items:center;flex:none;width:25px;height:25px;border:1.5px solid var(--azul-linea);border-radius:50%;background:#fff;color:var(--muted);font-style:normal;font-size:11px;}
.selector-pasos li.actual{background:#fff;color:var(--azul);}
.selector-pasos li.actual i{border-color:var(--azul);background:var(--azul);color:#fff;}
.st-key-selector_portal_dialogo [role="radiogroup"]{gap:8px!important;}
.st-key-selector_portal_dialogo [role="radiogroup"]>label{align-items:flex-start!important;min-height:72px;padding:12px 14px!important;border:1.5px solid var(--azul-linea)!important;border-radius:var(--r)!important;background:#fff!important;cursor:pointer;}
.st-key-selector_portal_dialogo [role="radiogroup"]>label:has(input:checked){border-color:var(--azul)!important;background:var(--azul-suave)!important;box-shadow:inset 4px 0 0 var(--verde);}
.st-key-selector_portal_dialogo [role="radiogroup"]>label p{color:var(--muted)!important;line-height:1.45!important;}

/* Componentes Streamlit con la misma gramática del HTML. */
.stButton>button,.stDownloadButton>button{border:1.5px solid var(--azul)!important;border-radius:999px!important;background:#fff!important;color:var(--azul)!important;font-size:13.5px!important;font-weight:700!important;box-shadow:none!important;}
.stButton>button:hover,.stDownloadButton>button:hover{background:var(--azul-suave)!important;color:var(--azul)!important;}
.stButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{border-color:var(--azul)!important;background:var(--azul)!important;color:#fff!important;-webkit-text-fill-color:#fff!important;}
.stButton>button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{background:var(--azul-tinta)!important;border-color:var(--azul-tinta)!important;}
[data-testid="stVerticalBlockBorderWrapper"]{border:0!important;border-radius:var(--r)!important;background:var(--azul-suave)!important;box-shadow:none!important;}
[class*="st-key-tarjeta_modo_"]{height:100%;border:0!important;border-radius:var(--r)!important;background:var(--azul-suave)!important;box-shadow:none!important;}
[class*="st-key-tarjeta_modo_"][data-testid="stVerticalBlockBorderWrapper"],[class*="st-key-tarjeta_modo_"] [data-testid="stVerticalBlockBorderWrapper"],[class*="st-key-tarjeta_modo_"] [data-testid="stVerticalBlock"],[class*="st-key-tarjeta_modo_"]>div{border-color:transparent!important;background:var(--azul-suave)!important;box-shadow:none!important;}
.tarjeta{min-height:215px!important;padding:18px 18px 6px!important;}
.tarjeta small{color:var(--azul)!important;font-size:11.5px!important;letter-spacing:.04em!important;}
.tarjeta h3{color:var(--azul)!important;font-size:19px!important;}
.tarjeta p{color:var(--ink)!important;font-size:13.5px!important;}

/* Plataforma cartográfica: panel 340px + mapa + resultados. */
[data-testid="stSidebar"]{top:var(--nav-h)!important;height:calc(100vh - var(--nav-h))!important;border-right:1px solid var(--line)!important;background:#fff!important;box-shadow:none!important;}
[data-testid="stSidebar"][data-collapsed="false"]{width:340px!important;min-width:340px!important;max-width:340px!important;}
[data-testid="stSidebar"]>div:first-child{height:100%!important;padding:0!important;background:#fff!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:8px!important;}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:var(--azul)!important;}
[data-testid="stSidebar"] [data-testid="stTabs"] [data-baseweb="tab-list"]{position:sticky;top:0;z-index:20;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;padding:0 14px;background:#fff;border-bottom:1px solid var(--line);}
[data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"]{min-width:0;min-height:48px;padding:14px 6px 11px;color:var(--muted)!important;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;background:none!important;box-shadow:none!important;}
[data-testid="stSidebar"] [data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:var(--azul)!important;box-shadow:inset 0 -4px 0 var(--verde)!important;}
[data-testid="stSidebar"] [data-testid="stTabs"] [data-baseweb="tab-panel"]{padding:12px 14px 88px!important;}
[data-testid="stSidebar"] [data-testid="stExpander"]{margin:0 0 10px;border:0!important;border-radius:var(--r)!important;background:var(--azul-suave)!important;box-shadow:none!important;overflow:hidden;}
[data-testid="stSidebar"] [data-testid="stExpander"] details[open]{background:#fff!important;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{min-height:48px;padding:10px 14px!important;color:var(--azul)!important;font-size:13px!important;font-weight:700!important;}
[data-testid="stSidebar"] [data-testid="stSelectbox"]>div>div,[data-testid="stSidebar"] [data-baseweb="select"]>div{border-color:var(--azul-linea)!important;border-radius:999px!important;background:#fff!important;}
[data-testid="stSidebar"] .st-key-acciones_sidebar{position:fixed;left:0;bottom:0;z-index:30;width:340px;margin:0;padding:12px 14px calc(12px + env(safe-area-inset-bottom,0px));border-top:1px solid var(--line);background:#fff;box-shadow:none;}
[data-testid="stSidebar"] .st-key-acciones_sidebar button{width:100%;}

.mapa-cabecera,.resultado-cabecera{margin:0!important;padding:15px 18px!important;border:0!important;border-bottom:5px solid var(--verde)!important;background:var(--azul)!important;}
.mapa-cabecera small,.resultado-cabecera small{color:var(--verde)!important;font-size:11.5px!important;}
.mapa-cabecera strong,.resultado-cabecera strong{margin-top:3px;color:#fff!important;font-size:20px!important;font-weight:500!important;}
.dashboard-area{grid-template-columns:1fr 1fr!important;margin:0!important;border:0!important;border-radius:0!important;background:var(--line)!important;}
.dashboard-area>div{padding:13px 14px!important;background:var(--azul-suave)!important;}
.dashboard-area small{color:var(--azul-medio)!important;font-size:10.5px!important;}
.dashboard-area strong{color:var(--azul-tinta)!important;font-size:14px!important;}
.st-key-panel_resultados_visible{min-width:0;border-left:1px solid var(--line);background:#fff;}
.st-key-panel_resultados_oculto{display:none!important;}
.st-key-mapa_portal{min-width:0;}
iframe[title="streamlit_folium.st_folium"]{display:block;border:0!important;border-radius:0!important;background:var(--azul-suave)!important;box-shadow:none!important;}
[data-testid="stVegaLiteChart"]{border:1px solid var(--line)!important;border-radius:var(--r)!important;background:#fff!important;box-shadow:none!important;}
[data-testid="stMetric"]{border:0!important;border-radius:var(--r)!important;background:var(--azul-suave)!important;}

@media(max-width:1240px){.ref-links{display:none}.ref-main-row{gap:12px}.ref-nav-btns{margin-left:auto}.ref-nav-btns>.ref-btn-w{display:none}.ref-mobile-menu{display:block}}
@media(max-width:900px){
  :root{--nav-h:76px}.ref-util{display:none}.ref-main-row{height:76px}.ref-nav-in{padding:0 16px}.ref-wm b{font-size:18px}.ref-wm small{font-size:7.5px}.ref-lang{display:none}
  .block-container{padding:calc(var(--nav-h) + 8px) 10px 12px!important}
  [data-testid="stSidebar"]{top:var(--nav-h)!important;height:calc(100vh - var(--nav-h))!important}
  [data-testid="stSidebar"][data-collapsed="false"]{width:min(340px,100vw)!important;min-width:min(340px,100vw)!important;max-width:min(340px,100vw)!important}
  [data-testid="stSidebar"] .st-key-acciones_sidebar{width:min(340px,100vw)}
  .ref-hero{margin:-8px -10px 0;min-height:420px}.ref-meta{grid-template-columns:1fr 1fr}.ref-meta>div+div{border-left:0;border-top:1px solid var(--azul-linea)}
  .ref-modes{margin:0 -10px;padding:24px 16px 32px}.ref-mode-cards{grid-template-columns:1fr}.ref-mode-card{min-height:0}.ref-selector-entry{align-items:stretch;flex-direction:column}.ref-selector-entry .ref-btn{width:100%}
}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.01ms!important;}}
</style>
"""


LOGO_PORTAL = """
<svg viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="20" fill="none" stroke="#ffffff" stroke-opacity=".35" stroke-width="1.5"/><path d="M8 30 C15 28 16 15 22 15 S30 26 36 12" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round"/><circle cx="8" cy="30" r="4.6" fill="#77cc09"/><circle cx="22" cy="15" r="3.8" fill="#ffffff"/><circle cx="36" cy="12" r="4.6" fill="#fabc20"/></svg>
"""


def inyectar_estilo_portal() -> None:
    st.markdown(CSS_PORTAL_HTML, unsafe_allow_html=True)


def mostrar_navegacion_portal(seccion: str) -> None:
    activa = {
        "mapa": seccion == "Mapa",
        "objetivo": seccion == "Conoce la herramienta",
        "datos": seccion == "Uso de datos",
        "metodo": seccion == "Metodología y ayuda",
        "acerca": seccion == "Acerca del visor",
    }
    modo_actual = st.session_state.get("modo_analisis")
    destino_plataforma = (
        f"?seccion=mapa&amp;modo={html.escape(str(modo_actual))}"
        if modo_actual
        else "?seccion=inicio#seleccionar-analisis"
    )

    def actual(clave: str) -> str:
        return ' aria-current="page"' if activa[clave] else ""

    st.markdown(
        f"""
        <a class="ref-skip" href="#stMain" target="_self">Saltar al contenido principal</a>
        <header class="ref-nav">
          <div class="ref-nav-in">
            <div class="ref-util"><a href="?seccion=inicio" target="_self">Inicio</a><a href="?seccion=datos" target="_self">Atribución de datos</a><span>WGS 84 · EPSG:4326</span></div>
            <div class="ref-main-row">
              <a class="ref-wm" href="?seccion=inicio" target="_self" aria-label="Inicio · Conectividad Panamá">{LOGO_PORTAL}<span><b>Conectividad Panamá</b><small>Cuenca del Canal de Panamá</small></span></a>
              <nav class="ref-links" aria-label="Secciones">
                <a href="?seccion=objetivo" target="_self"{actual('objetivo')}>Conoce la herramienta<i class="ref-chev"></i></a>
                <a href="{destino_plataforma}" target="_self"{actual('mapa')}>Plataforma<i class="ref-chev"></i></a>
                <a href="?seccion=datos" target="_self"{actual('datos')}>Uso de datos<i class="ref-chev"></i></a>
                <a href="?seccion=acerca" target="_self"{actual('acerca')}>FAQ<i class="ref-chev"></i></a>
              </nav>
              <div class="ref-nav-btns">
                <a class="ref-btn ref-btn-w" href="{destino_plataforma}" target="_self">Explorar datos <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></a>
                <details class="ref-lang"><summary class="ref-btn ref-btn-o" aria-label="Idioma: español">ES <i class="ref-chev"></i></summary><div class="ref-lang-menu"><button type="button" aria-checked="true">Español <span>✓</span></button><button type="button" disabled>English <span>pronto</span></button></div></details>
                <details class="ref-mobile-menu"><summary class="ref-burger">Menú</summary><nav class="ref-mobile-links" aria-label="Secciones móviles"><a href="?seccion=objetivo" target="_self">Conoce la herramienta</a><a href="{destino_plataforma}" target="_self">Plataforma</a><a href="?seccion=datos" target="_self">Uso de datos</a><a href="?seccion=acerca" target="_self">FAQ</a></nav></details>
              </div>
            </div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def mostrar_hero_inicio() -> None:
    st.markdown(
        f"""
        <section class="ref-hero">
          <div class="ref-hero-in">
            <h1>Conectividad ecológica de la Cuenca del Canal de Panamá</h1>
            <p>Portal SIG para detectar dónde hay conectividad, dónde hay fragmentación, dónde se está perdiendo bosque y dónde conviene revisar. Integra JRC, Hansen, ESRI, GEDI y Sentinel en Google Earth Engine, los corredores de Almanaque Azul, el bosque 2021 de MiAMBIENTE y el Índice de Resiliencia Ecológica (ERI).</p>
            <div class="ref-acts"><a class="ref-btn ref-btn-w" href="?seccion=inicio&amp;selector=1" target="_self">Realizar análisis</a><a class="ref-btn ref-btn-o" href="?seccion=metodo" target="_self">Conocer el método</a></div>
          </div>
          <svg class="ref-hero-cut" viewBox="0 0 1440 150" preserveAspectRatio="none" aria-hidden="true"><polygon points="0,150 1440,40 1440,150" fill="#fff"/><g fill="none" stroke="#fabc20" stroke-opacity=".7" stroke-width="1.3"><path d="M1150 150 C1210 112 1320 96 1440 92"/><path d="M1200 150 C1255 120 1340 108 1440 106"/><path d="M1250 150 C1300 128 1365 120 1440 119"/></g><polygon points="960,62.7 1440,26 1440,34 960,70.7" fill="#fff"/><polygon points="880,78.8 1440,36 1440,46 880,88.8" fill="#77cc09"/><polygon points="990,84.4 1440,50 1440,59 990,93.4" fill="#fabc20"/></svg>
        </section>
        <section class="ref-start">
          <div class="ref-meta"><div><span>Sistema de referencia</span><b>WGS 84 · EPSG:4326</b></div><div><span>Resolución</span><b>10 m · 30 m</b></div><div><span>Serie temporal</span><b>1990–2025</b></div><div><span>Área de estudio</span><b>Cuenca del Canal</b></div><div><span>Procesamiento</span><b>Google Earth Engine</b></div></div>
          <div class="ref-intro"><h2>¿Qué desea preevaluar?</h2><p>Elija una lectura. Después podrá seleccionar una finca, una subcuenca, un polígono o la cuenca completa.</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def mostrar_tarjetas_modos(modos: dict[str, dict[str, str]]) -> None:
    """Presenta las opciones con la tarjeta reutilizable del HTML de referencia."""

    tarjetas = []
    for modo, contenido in modos.items():
        pregunta = escapar(contenido["pregunta"])
        titulo = escapar(contenido["titulo"])
        descripcion = escapar(contenido["descripcion"])
        resultado = escapar(contenido["resultado"])
        tarjetas.append(
            f'<a class="ref-mode-card" href="?seccion=mapa&amp;modo={escapar(modo)}" target="_self">'
            f'<span class="date">{pregunta}</span>'
            f"<h3>{titulo}</h3>"
            f"<p>{descripcion}</p>"
            f'<p class="result"><b>Recibirá:</b> {resultado}</p>'
            f'<span class="more">Abrir {titulo.lower()} '
            '<i class="ref-chev" aria-hidden="true"></i></span></a>'
        )

    st.markdown(
        '<section class="ref-modes" id="seleccionar-analisis"><div class="ref-mode-cards">'
        + "".join(tarjetas)
        + "</div></section>",
        unsafe_allow_html=True,
    )


def mostrar_acceso_selector() -> None:
    """Muestra la única entrada al asistente, como el botón del HTML original."""

    st.markdown(
        """
        <section class="ref-modes" id="seleccionar-analisis">
          <div class="ref-selector-entry">
            <div>
              <span class="eyebrow">Asistente de análisis</span>
              <h2>Seleccione qué desea conocer</h2>
              <p>El asistente presenta las tres preevaluaciones, explica qué entrega cada una y después abre el mapa con los controles correspondientes.</p>
            </div>
            <a class="ref-btn" href="?seccion=inicio&amp;selector=1" target="_self">Realizar análisis</a>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def escapar(texto: object) -> str:
    return html.escape(str(texto))
