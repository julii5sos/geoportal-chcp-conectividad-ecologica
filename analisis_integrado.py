"""Comparación JRC TMF + ESRI sin fusionar sus definiciones forestales."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from analisis_temporal import (
    construir_estado_binario_ee,
    ejecutar_analisis_temporal_ee,
    validar_solicitud_temporal,
)
from simbologia_geoportal import CONCORDANCIA_CAMBIO, CONCORDANCIA_ESTADO


ANIO_INICIAL_COMUN = 2017
ANIO_FINAL_COMUN = 2025
RESOLUCION_CONCORDANCIA_M = 30


def validar_periodo_integrado(anio_inicial: int, anio_final: int) -> tuple[int, int]:
    if anio_inicial >= anio_final:
        raise ValueError("El año inicial debe ser anterior al año final.")
    if anio_inicial < ANIO_INICIAL_COMUN or anio_final > ANIO_FINAL_COMUN:
        raise ValueError(
            f"La comparación JRC + ESRI admite únicamente {ANIO_INICIAL_COMUN}–{ANIO_FINAL_COMUN}."
        )
    return int(anio_inicial), int(anio_final)


def clasificar_estado(*, jrc_bosque: bool, esri_bosque: bool, comparable: bool = True) -> int:
    if not comparable:
        return 5
    if jrc_bosque and esri_bosque:
        return 1
    if not jrc_bosque and not esri_bosque:
        return 2
    return 3 if jrc_bosque else 4


def clasificar_cambio(
    *,
    jrc_inicial: bool,
    jrc_final: bool,
    esri_inicial: bool,
    esri_final: bool,
    comparable: bool = True,
) -> int:
    if not comparable:
        return 8
    loss_j = jrc_inicial and not jrc_final
    loss_e = esri_inicial and not esri_final
    gain_j = not jrc_inicial and jrc_final
    gain_e = not esri_inicial and esri_final
    if loss_j and loss_e:
        return 1
    if loss_j and not loss_e and not gain_e:
        return 2
    if loss_e and not loss_j and not gain_j:
        return 3
    if gain_j and gain_e:
        return 4
    if gain_j and not gain_e and not loss_e:
        return 5
    if gain_e and not gain_j and not loss_j:
        return 6
    return 7


def _area_summary(values: dict[str, Any], classes: dict[int, dict[str, str]]) -> dict[str, float]:
    return {
        definition["clave"]: round(float(values.get(f"clase_{code}") or 0.0), 4)
        for code, definition in classes.items()
    }


def _percent(value: float, denominator: float) -> float:
    return round(value / denominator * 100, 4) if denominator > 0 else 0.0


def resumir_concordancia(
    *,
    estado_areas: dict[str, float],
    cambio_areas: dict[str, float],
    bosque_jrc_final_ha: float,
    bosque_esri_final_ha: float,
) -> dict[str, Any]:
    estado_comun = sum(
        estado_areas.get(key, 0.0)
        for key in ("bosque_ambas", "no_bosque_ambas", "bosque_solo_jrc", "bosque_solo_esri")
    )
    estado_coincidente = estado_areas.get("bosque_ambas", 0.0) + estado_areas.get("no_bosque_ambas", 0.0)
    estado_discrepante = estado_areas.get("bosque_solo_jrc", 0.0) + estado_areas.get("bosque_solo_esri", 0.0)
    cambio_comun = sum(value for key, value in cambio_areas.items() if key != "sin_datos")
    cambio_coincidente = cambio_areas.get("perdida_ambas", 0.0) + cambio_areas.get("ganancia_ambas", 0.0)
    return {
        "estado": {
            "areas_ha": estado_areas,
            "area_valida_comun_ha": round(estado_comun, 4),
            "superficie_coincidente_ha": round(estado_coincidente, 4),
            "superficie_discrepante_ha": round(estado_discrepante, 4),
            "concordancia_pct": _percent(estado_coincidente, estado_comun),
        },
        "cambio": {
            "areas_ha": cambio_areas,
            "area_valida_comun_ha": round(cambio_comun, 4),
            "eventos_coincidentes_ha": round(cambio_coincidente, 4),
            "eventos_coincidentes_pct_area_comun": _percent(cambio_coincidente, cambio_comun),
        },
        "diferencia_superficie_forestal_final_ha": round(
            float(bosque_jrc_final_ha) - float(bosque_esri_final_ha), 4
        ),
    }


def _alinear_esri_a_jrc(imagen, proyeccion_jrc, ee):
    """Agrega la clase binaria ESRI por moda; nunca usa interpolación bilineal."""

    return (
        ee.Image(imagen)
        .reduceResolution(reducer=ee.Reducer.mode(), bestEffort=False, maxPixels=1024)
        .reproject(crs=proyeccion_jrc)
        .toByte()
    )


def _areas_por_clase(imagen, classes: dict[int, dict[str, str]], geometry, ee) -> dict[str, float]:
    pixel_ha = ee.Image.pixelArea().divide(10_000)
    bands = [
        ee.Image(imagen).eq(code).multiply(pixel_ha).rename(f"clase_{code}")
        for code in classes
    ]
    raw = ee.Image.cat(bands).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=RESOLUCION_CONCORDANCIA_M,
        maxPixels=1e9,
        tileScale=4,
        bestEffort=False,
    ).getInfo()
    return _area_summary(raw or {}, classes)


def _map_layer(image, classes: dict[int, dict[str, str]], ee) -> dict[str, Any]:
    map_id = ee.Image(image).getMapId(
        {
            "min": min(classes),
            "max": max(classes),
            "palette": [classes[index]["color"].lstrip("#") for index in sorted(classes)],
        }
    )
    return {
        "tile_url": map_id["tile_fetcher"].url_format,
        "classes": [
            {"value": code, **definition} for code, definition in sorted(classes.items())
        ],
        "opacity": 0.76,
    }


def calcular_concordancia_ee(
    *,
    anio_inicial: int,
    anio_final: int,
    area_geojson: dict[str, Any],
    resultados_fuente: dict[str, dict[str, Any]],
    ee_module,
) -> dict[str, Any]:
    ee = ee_module
    geometry = ee.Geometry(area_geojson)
    j_i, jv_i = construir_estado_binario_ee("jrc_tmf", anio_inicial, geometry, ee_module=ee)
    j_f, jv_f = construir_estado_binario_ee("jrc_tmf", anio_final, geometry, ee_module=ee)
    e_i, ev_i = construir_estado_binario_ee("esri_lulc", anio_inicial, geometry, ee_module=ee)
    e_f, ev_f = construir_estado_binario_ee("esri_lulc", anio_final, geometry, ee_module=ee)
    projection = ee.Image(j_f).projection()

    e_i = _alinear_esri_a_jrc(e_i, projection, ee).unmask(0)
    e_f = _alinear_esri_a_jrc(e_f, projection, ee).unmask(0)
    ev_i = _alinear_esri_a_jrc(ev_i, projection, ee).unmask(0).eq(1)
    ev_f = _alinear_esri_a_jrc(ev_f, projection, ee).unmask(0).eq(1)
    j_i, j_f = ee.Image(j_i).unmask(0), ee.Image(j_f).unmask(0)
    jv_i, jv_f = ee.Image(jv_i).unmask(0).eq(1), ee.Image(jv_f).unmask(0).eq(1)

    common_final = jv_f.And(ev_f)
    state = ee.Image.constant(5).setDefaultProjection(projection).clip(geometry).toByte()
    state = state.where(common_final.And(j_f).And(e_f), 1)
    state = state.where(common_final.And(j_f.Not()).And(e_f.Not()), 2)
    state = state.where(common_final.And(j_f).And(e_f.Not()), 3)
    state = state.where(common_final.And(j_f.Not()).And(e_f), 4).rename("concordancia_estado")

    common_change = jv_i.And(jv_f).And(ev_i).And(ev_f)
    loss_j, loss_e = j_i.And(j_f.Not()), e_i.And(e_f.Not())
    gain_j, gain_e = j_i.Not().And(j_f), e_i.Not().And(e_f)
    change = ee.Image.constant(8).setDefaultProjection(projection).clip(geometry).toByte()
    change = change.where(common_change, 7)
    change = change.where(common_change.And(loss_j).And(loss_e), 1)
    change = change.where(common_change.And(loss_j).And(loss_e.Not()).And(gain_e.Not()), 2)
    change = change.where(common_change.And(loss_e).And(loss_j.Not()).And(gain_j.Not()), 3)
    change = change.where(common_change.And(gain_j).And(gain_e), 4)
    change = change.where(common_change.And(gain_j).And(gain_e.Not()).And(loss_e.Not()), 5)
    change = change.where(common_change.And(gain_e).And(gain_j.Not()).And(loss_j.Not()), 6)
    change = change.rename("concordancia_cambio")

    state_areas = _areas_por_clase(state, CONCORDANCIA_ESTADO, geometry, ee)
    change_areas = _areas_por_clase(change, CONCORDANCIA_CAMBIO, geometry, ee)
    jrc_stats = resultados_fuente["jrc_tmf"]["estadisticas_cobertura"]["periodos"][str(anio_final)]
    esri_stats = resultados_fuente["esri_lulc"]["estadisticas_cobertura"]["periodos"][str(anio_final)]
    summary = resumir_concordancia(
        estado_areas=state_areas,
        cambio_areas=change_areas,
        bosque_jrc_final_ha=jrc_stats["bosque_ha"],
        bosque_esri_final_ha=esri_stats["bosque_ha"],
    )
    summary["maps"] = {
        "state": _map_layer(state, CONCORDANCIA_ESTADO, ee),
        "change": _map_layer(change, CONCORDANCIA_CAMBIO, ee),
    }
    return summary


def ejecutar_analisis_integrado_ee(
    *,
    anio_inicial: int,
    anio_final: int,
    area_geojson: dict[str, Any],
    distancia_maxima_m: float = 500,
    area_minima_parche_ha: float = 0.0,
    ee_module=None,
) -> dict[str, Any]:
    """Ejecuta ambas fuentes de forma independiente y luego calcula concordancia."""

    validar_periodo_integrado(anio_inicial, anio_final)
    validar_solicitud_temporal("jrc_tmf", anio_inicial, anio_final, distancia_maxima_m, area_minima_parche_ha)
    validar_solicitud_temporal("esri_lulc", anio_inicial, anio_final, distancia_maxima_m, area_minima_parche_ha)
    if ee_module is None:
        import ee as ee_module

    results = {
        source: ejecutar_analisis_temporal_ee(
            fuente=source,
            anio_inicial=anio_inicial,
            anio_final=anio_final,
            area_geojson=area_geojson,
            distancia_maxima_m=distancia_maxima_m,
            area_minima_parche_ha=area_minima_parche_ha,
            ee_module=ee_module,
        )
        for source in ("jrc_tmf", "esri_lulc")
    }
    concordance = calcular_concordancia_ee(
        anio_inicial=anio_inicial,
        anio_final=anio_final,
        area_geojson=area_geojson,
        resultados_fuente=results,
        ee_module=ee_module,
    )
    return {
        "mode": "integrated",
        "anio_inicial": int(anio_inicial),
        "anio_final": int(anio_final),
        "sources": results,
        "concordance": concordance,
        "metadata": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "common_period": [ANIO_INICIAL_COMUN, ANIO_FINAL_COMUN],
            "comparison_grid_m": RESOLUCION_CONCORDANCIA_M,
            "alignment": (
                "JRC conserva su malla de 30 m. La máscara binaria ESRI de 10 m se agrega "
                "por moda a la proyección JRC; no se usa interpolación bilineal."
            ),
            "valid_mask": "Intersección de píxeles válidos de ambas fuentes y ambos años.",
            "scientific_scope": (
                "La concordancia compara productos; no crea una cobertura definitiva, no promedia "
                "superficies y no constituye validación de campo."
            ),
        },
        "warnings": [
            "JRC y ESRI conservan definiciones forestales distintas.",
            "La ganancia de clase bosque no confirma restauración ecológica.",
            "La conectividad calculada es estructural y no demuestra movimiento de fauna.",
        ],
    }

