"""Simbología única para API, mapa, leyendas, gráficas y exportaciones.

Los colores siempre se acompañan de una etiqueta. Las paletas de ERI, NDVI y
fuentes complementarias permanecen separadas de las transiciones forestales.
"""

from __future__ import annotations


TRANSICIONES_FORESTALES = {
    "bosque_estable": {"etiqueta": "Bosque estable", "color": "#187A45", "patron": "sólido"},
    "perdida_bosque": {"etiqueta": "Pérdida forestal detectada", "color": "#D94438", "patron": "diagonal"},
    "ganancia_bosque": {"etiqueta": "Ganancia de clase bosque", "color": "#76B852", "patron": "puntos"},
    "no_bosque_estable": {"etiqueta": "No bosque estable", "color": "#D7C2A1", "patron": "sólido"},
    "sin_datos": {"etiqueta": "Sin datos comparables", "color": "#A8ADB4", "patron": "cruzado"},
}

CONECTIVIDAD = {
    "conexiones": {"etiqueta": "Conexiones estructurales", "color": "#2878B5", "patron": "línea continua"},
    "aislados": {"etiqueta": "Parches aislados", "color": "#E69F00", "patron": "círculo"},
    "perdidas": {"etiqueta": "Conexiones perdidas", "color": "#C83E4D", "patron": "línea discontinua"},
}

CONCORDANCIA_ESTADO = {
    1: {"clave": "bosque_ambas", "etiqueta": "Bosque en ambas fuentes", "color": "#187A45"},
    2: {"clave": "no_bosque_ambas", "etiqueta": "No bosque en ambas fuentes", "color": "#D7C2A1"},
    3: {"clave": "bosque_solo_jrc", "etiqueta": "Bosque solo según JRC", "color": "#6B5FB5"},
    4: {"clave": "bosque_solo_esri", "etiqueta": "Bosque solo según ESRI", "color": "#2F8FB3"},
    5: {"clave": "sin_datos", "etiqueta": "Sin datos comparables", "color": "#A8ADB4"},
}

CONCORDANCIA_CAMBIO = {
    1: {"clave": "perdida_ambas", "etiqueta": "Pérdida detectada por ambas", "color": "#8B1E1E"},
    2: {"clave": "perdida_solo_jrc", "etiqueta": "Pérdida solo según JRC", "color": "#D94438"},
    3: {"clave": "perdida_solo_esri", "etiqueta": "Pérdida solo según ESRI", "color": "#F07A52"},
    4: {"clave": "ganancia_ambas", "etiqueta": "Ganancia detectada por ambas", "color": "#3D7E3A"},
    5: {"clave": "ganancia_solo_jrc", "etiqueta": "Ganancia solo según JRC", "color": "#76B852"},
    6: {"clave": "ganancia_solo_esri", "etiqueta": "Ganancia solo según ESRI", "color": "#9BCB68"},
    7: {"clave": "otros_cambios", "etiqueta": "Otros cambios o ausencia de cambio", "color": "#D6DCE5"},
    8: {"clave": "sin_datos", "etiqueta": "Sin datos comparables", "color": "#A8ADB4"},
}

FUENTES = {
    "jrc_tmf": {"etiqueta": "JRC TMF", "color": "#1F8A70"},
    "esri_lulc": {"etiqueta": "ESRI LULC", "color": "#3A7CA5"},
    "hansen_gfc": {"etiqueta": "Hansen GFC", "color": "#E76F51"},
    "sentinel_ndvi": {"etiqueta": "Sentinel-2 · NDVI", "color": "#9BBF30"},
    "gedi": {"etiqueta": "GEDI", "color": "#7A5195"},
    "integrated": {"etiqueta": "Concordancia JRC + ESRI", "color": "#0A4393"},
}


def catalogo_simbologia() -> dict[str, object]:
    return {
        "transiciones_forestales": TRANSICIONES_FORESTALES,
        "conectividad": CONECTIVIDAD,
        "concordancia_estado": CONCORDANCIA_ESTADO,
        "concordancia_cambio": CONCORDANCIA_CAMBIO,
        "fuentes": FUENTES,
        "regla_accesibilidad": (
            "Toda clase se identifica mediante texto y, cuando corresponde, patrón o tipo de geometría; "
            "el color no es el único portador de significado."
        ),
    }

