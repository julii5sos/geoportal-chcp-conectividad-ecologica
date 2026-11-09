"""Evaluación ecológica original, desacoplada de Streamlit.

Este módulo conserva los períodos, umbrales y pesos de ``metodologia_indice``.
No sustituye el análisis temporal: responde una pregunta distinta, orientada a
priorizar una revisión territorial mediante señales multifuente.
"""

from __future__ import annotations

from typing import Any

from analisis_complementario import GEDI_ASSET, HANSEN_ASSET, _ndvi
from analisis_temporal import ESRI_ASSET, TMF_ASSET, _estado_y_mascara_valida_ee
from metodologia_indice import (
    JUSTIFICACION_PESOS,
    JUSTIFICACION_UMBRALES,
    PERIODOS_ANALISIS,
    PESOS_INDICE,
    PUNTAJE_MAXIMO,
    REGLAS_MAPA_COINCIDENCIA,
    UMBRALES_INDICE,
    calcular_indice_prioridad,
    calcular_prioridad_visita,
    evaluar_consistencia,
    evaluar_senales,
)


def _number(values: dict[str, Any], key: str) -> float:
    value = values.get(key)
    return float(value) if value is not None else 0.0


def _tile(image, visualization: dict[str, Any]) -> str:
    return image.getMapId(visualization)["tile_fetcher"].url_format


def _reduce_area(image, geometry, scale: int, projection, ee_module):
    kwargs = {
        "reducer": ee_module.Reducer.sum(),
        "geometry": geometry,
        "scale": scale,
        "bestEffort": True,
        "maxPixels": 1e9,
        "tileScale": 4,
    }
    if projection is not None:
        kwargs["crs"] = projection
    return ee_module.Dictionary(image.reduceRegion(**kwargs))


def _gedi(geometry, ee_module):
    collection = (
        ee_module.ImageCollection(GEDI_ASSET)
        .filterBounds(geometry)
        .select([0], ["altura_dosel"])
        .map(lambda image: ee_module.Image(image).toFloat())
    )
    empty = (
        ee_module.Image.constant(0)
        .rename("altura_dosel")
        .updateMask(ee_module.Image(0))
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 100)
    )
    return (
        collection.merge(ee_module.ImageCollection.fromImages([empty]))
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 100)
        .rename("altura_dosel")
        .clip(geometry)
    )


def _hansen(geometry, ee_module):
    image = ee_module.Image(HANSEN_ASSET)
    cover_2000 = image.select("treecover2000").unmask(0).gte(30)
    loss = image.select("loss").unmask(0)
    loss_year = image.select("lossyear")
    post = loss_year.updateMask(loss_year.gt(20)).rename("perdida_post").clip(geometry)
    pre = (
        loss_year.updateMask(loss_year.gt(0).And(loss_year.lte(20)))
        .rename("perdida_pre")
        .clip(geometry)
    )
    baseline = (
        cover_2000.And(loss.eq(0).Or(loss_year.unmask(0).gt(20)))
        .selfMask()
        .rename("linea_base_2020")
        .clip(geometry)
    )
    return post, pre, baseline


def _coincidence(jrc, hansen_post, esri_initial, esri_final, geometry, ee_module):
    reference = ee_module.Image(jrc).projection()
    esri_projection = ee_module.Image(esri_initial).projection()
    jrc_signal = jrc.eq(2).Or(jrc.eq(3)).unmask(0).rename("senal_jrc")
    hansen_signal = (
        hansen_post.gt(0).unmask(0).reproject(crs=reference).rename("senal_hansen")
    )
    esri_10m = (
        esri_initial.eq(2)
        .And(esri_final.neq(2))
        .unmask(0)
        .setDefaultProjection(esri_projection)
    )
    esri_signal = (
        esri_10m.reduceResolution(
            reducer=ee_module.Reducer.max(), bestEffort=True, maxPixels=1024
        )
        .reproject(crs=reference)
        .gt(0)
        .rename("senal_esri")
    )
    return (
        jrc_signal.add(hansen_signal)
        .add(esri_signal)
        .rename("fuentes_coincidentes")
        .toByte()
        .clip(geometry)
    )


def ejecutar_evaluacion_ecologica(
    area_geojson: dict[str, Any], *, contexto_corredores: dict[str, Any],
    contexto_fragmentacion: dict[str, Any] | None = None, ee_module
) -> dict[str, Any]:
    """Ejecuta el mismo índice multifuente del visor científico original."""

    geometry = ee_module.Geometry(area_geojson, proj="EPSG:4326", geodesic=False)
    jrc_year = PERIODOS_ANALISIS["jrc_diagnostico"]
    esri_initial_year = PERIODOS_ANALISIS["esri_inicial"]
    esri_final_year = PERIODOS_ANALISIS["esri_final"]
    ndvi_initial_year = PERIODOS_ANALISIS["ndvi_inicial"]
    ndvi_final_year = PERIODOS_ANALISIS["ndvi_final"]

    jrc, _ = _estado_y_mascara_valida_ee("jrc_tmf", jrc_year, geometry, ee_module=ee_module)
    esri_initial, _ = _estado_y_mascara_valida_ee(
        "esri_lulc", esri_initial_year, geometry, ee_module=ee_module
    )
    esri_final, _ = _estado_y_mascara_valida_ee(
        "esri_lulc", esri_final_year, geometry, ee_module=ee_module
    )
    hansen_post, hansen_pre, baseline = _hansen(geometry, ee_module)
    coincidence = _coincidence(
        jrc, hansen_post, esri_initial, esri_final, geometry, ee_module
    )
    gedi = _gedi(geometry, ee_module)
    ndvi_initial = _ndvi(ndvi_initial_year, geometry, ee_module)
    ndvi_final = _ndvi(ndvi_final_year, geometry, ee_module)
    ndvi_delta = ndvi_final.subtract(ndvi_initial).rename("ndvi_delta")
    ndvi_valid = ndvi_initial.mask().And(ndvi_final.mask())
    ndvi_decrease = (
        ndvi_initial.gte(UMBRALES_INDICE["ndvi_vigor_inicial_minimo"])
        .And(ndvi_delta.lte(UMBRALES_INDICE["ndvi_delta_disminucion"]))
        .updateMask(ndvi_valid)
    )
    pixel_ha = ee_module.Image.pixelArea().divide(10_000)

    areas_jrc = ee_module.Image.cat([
        jrc.eq(1).unmask(0).multiply(pixel_ha).rename("tmf_estable"),
        jrc.eq(2).unmask(0).multiply(pixel_ha).rename("tmf_degradacion"),
        jrc.eq(3).unmask(0).multiply(pixel_ha).rename("tmf_deforestacion"),
        jrc.eq(4).unmask(0).multiply(pixel_ha).rename("tmf_recuperacion"),
        jrc.eq(5).unmask(0).multiply(pixel_ha).rename("tmf_agua"),
        jrc.eq(6).unmask(0).multiply(pixel_ha).rename("tmf_otra_cobertura"),
        coincidence.eq(1).unmask(0).multiply(pixel_ha).rename("coincidencia_1_fuente"),
        coincidence.eq(2).unmask(0).multiply(pixel_ha).rename("coincidencia_2_fuentes"),
        coincidence.eq(3).unmask(0).multiply(pixel_ha).rename("coincidencia_3_fuentes"),
    ])
    areas_hansen = ee_module.Image.cat([
        hansen_post.gt(0).unmask(0).multiply(pixel_ha).rename("hansen_post"),
        hansen_pre.gt(0).unmask(0).multiply(pixel_ha).rename("hansen_pre"),
        baseline.unmask(0).multiply(pixel_ha).rename("linea_base"),
    ])
    areas_esri = ee_module.Image.cat([
        esri_final.eq(2).unmask(0).multiply(pixel_ha).rename("esri_arboles_final"),
        esri_initial.eq(2).And(esri_final.neq(2)).unmask(0).multiply(pixel_ha).rename("esri_salida"),
        esri_initial.neq(2).And(esri_final.eq(2)).unmask(0).multiply(pixel_ha).rename("esri_ganancia"),
        esri_initial.eq(2).And(esri_final.eq(2)).unmask(0).multiply(pixel_ha).rename("esri_estable"),
    ])
    areas_ndvi = ee_module.Image.cat([
        ndvi_decrease.unmask(0).multiply(pixel_ha).rename("ndvi_disminucion"),
        ndvi_valid.unmask(0).multiply(pixel_ha).rename("ndvi_area_datos"),
    ])
    ndvi_stats = ee_module.Image.cat([
        ndvi_initial.rename("ndvi_inicial_medio"),
        ndvi_final.rename("ndvi_final_medio"),
        ndvi_delta.rename("ndvi_delta_medio"),
    ]).updateMask(ndvi_valid)

    summary = (
        _reduce_area(areas_jrc, geometry, 30, jrc.projection(), ee_module)
        .combine(_reduce_area(areas_hansen, geometry, 30, ee_module.Image(HANSEN_ASSET).projection(), ee_module), True)
        .combine(_reduce_area(areas_esri, geometry, 10, esri_final.projection(), ee_module), True)
        .combine(_reduce_area(areas_ndvi, geometry, 20, ndvi_final.projection(), ee_module), True)
        .combine(ee_module.Dictionary(ndvi_stats.reduceRegion(
            reducer=ee_module.Reducer.mean(), geometry=geometry, scale=20,
            bestEffort=True, maxPixels=1e9, tileScale=4,
        )), True)
        .combine(ee_module.Dictionary({
            "area_ha": geometry.area(1).divide(10_000),
            "gedi_altura": gedi.reduceRegion(
                reducer=ee_module.Reducer.mean(), geometry=geometry, scale=100,
                bestEffort=True, maxPixels=1e9, tileScale=4,
            ).get("altura_dosel"),
            "gedi_area_datos": gedi.mask().multiply(pixel_ha).reduceRegion(
                reducer=ee_module.Reducer.sum(), geometry=geometry, scale=100,
                bestEffort=True, maxPixels=1e9, tileScale=4,
            ).get("altura_dosel"),
        }), True)
        .getInfo()
    )

    area_keys = [
        "tmf_estable", "tmf_degradacion", "tmf_deforestacion", "tmf_recuperacion",
        "tmf_agua", "tmf_otra_cobertura", "coincidencia_1_fuente",
        "coincidencia_2_fuentes", "coincidencia_3_fuentes", "hansen_post",
        "hansen_pre", "linea_base", "esri_arboles_final", "esri_salida",
        "esri_ganancia", "esri_estable", "ndvi_disminucion", "ndvi_area_datos",
    ]
    metrics = {key: _number(summary, key) for key in area_keys}
    area_ha = _number(summary, "area_ha")
    metrics.update({
        "area_ha": area_ha,
        "gedi_altura": _number(summary, "gedi_altura"),
        "gedi_area_datos": _number(summary, "gedi_area_datos"),
        "gedi_cobertura_pct": _number(summary, "gedi_area_datos") / area_ha * 100 if area_ha else 0,
        "ndvi_inicial_medio": _number(summary, "ndvi_inicial_medio"),
        "ndvi_final_medio": _number(summary, "ndvi_final_medio"),
        "ndvi_delta_medio": _number(summary, "ndvi_delta_medio"),
        "ndvi_cobertura_pct": _number(summary, "ndvi_area_datos") / area_ha * 100 if area_ha else 0,
    })
    pct = lambda key: metrics[key] / area_ha * 100 if area_ha else 0.0
    metrics.update({
        "pct_tmf_defor": pct("tmf_deforestacion"),
        "pct_tmf_degrad": pct("tmf_degradacion"),
        "pct_tmf_recuperacion": pct("tmf_recuperacion"),
        "pct_esri_salida": pct("esri_salida"),
        "pct_esri_ganancia": pct("esri_ganancia"),
        "pct_linea_base": pct("linea_base"),
        "pct_ndvi_disminucion": pct("ndvi_disminucion"),
        "coincidencia_varias_fuentes": metrics["coincidencia_2_fuentes"] + metrics["coincidencia_3_fuentes"],
    })
    metrics["pct_coincidencia_varias_fuentes"] = (
        metrics["coincidencia_varias_fuentes"] / area_ha * 100 if area_ha else 0
    )

    signals, availability = evaluar_senales(
        tmf_deforestacion_ha=metrics["tmf_deforestacion"],
        tmf_deforestacion_pct=metrics["pct_tmf_defor"],
        tmf_degradacion_ha=metrics["tmf_degradacion"],
        tmf_degradacion_pct=metrics["pct_tmf_degrad"],
        hansen_post_2020_ha=metrics["hansen_post"],
        esri_salida_arboles_ha=metrics["esri_salida"],
        esri_salida_arboles_pct=metrics["pct_esri_salida"],
        gedi_altura_media_m=metrics["gedi_altura"],
        gedi_cobertura_valida_pct=metrics["gedi_cobertura_pct"],
        linea_base_arborea_pct=metrics["pct_linea_base"],
        ndvi_disminucion_ha=metrics["ndvi_disminucion"],
        ndvi_disminucion_pct=metrics["pct_ndvi_disminucion"],
        ndvi_cobertura_valida_pct=metrics["ndvi_cobertura_pct"],
    )
    contributions, score, priority = calcular_indice_prioridad(
        senal_tmf=signals["tmf"], senal_hansen=signals["hansen"],
        senal_esri=signals["esri"], senal_gedi=signals["gedi"],
        senal_ndvi=signals["ndvi"],
    )
    consistency = evaluar_consistencia(
        senal_tmf=signals["tmf"], senal_hansen=signals["hansen"], senal_esri=signals["esri"],
        tmf_recuperacion_ha=metrics["tmf_recuperacion"],
        tmf_recuperacion_pct=metrics["pct_tmf_recuperacion"],
        esri_ganancia_arboles_ha=metrics["esri_ganancia"],
        esri_ganancia_arboles_pct=metrics["pct_esri_ganancia"],
    )
    visit = calcular_prioridad_visita(
        puntaje_cambios=score, contexto_corredores=contexto_corredores,
        contexto_fragmentacion=contexto_fragmentacion,
    )
    return {
        "mode": "ecological_evaluation",
        "score": score,
        "maximum_score": PUNTAJE_MAXIMO,
        "priority": priority,
        "signals": signals,
        "availability": availability,
        "contributions": contributions,
        "consistency": consistency,
        "visit_priority": visit,
        "structural_reference_2021": contexto_fragmentacion,
        "metrics": metrics,
        "periods": dict(PERIODOS_ANALISIS),
        "weights": dict(PESOS_INDICE),
        "thresholds": dict(UMBRALES_INDICE),
        "methodology": {
            "weight_justification": dict(JUSTIFICACION_PESOS),
            "threshold_justification": dict(JUSTIFICACION_UMBRALES),
            "coincidence": REGLAS_MAPA_COINCIDENCIA,
        },
        "maps": {
            "coincidence": {
                "tile_url": _tile(coincidence.selfMask(), {
                    "min": 1, "max": 3,
                    "palette": ["F9A825", "E65100", "8E1B16"],
                }),
                "classes": [
                    {"value": value, "label": item["etiqueta"], "color": item["color"]}
                    for value, item in REGLAS_MAPA_COINCIDENCIA["clases"].items()
                ],
            },
            "jrc_state": {
                "tile_url": _tile(jrc.updateMask(jrc.gte(1).And(jrc.lte(6))), {
                    "min": 1, "max": 6,
                    "palette": ["005a32", "f9c74f", "d62828", "74c476", "3182bd", "c7c7c7"],
                }),
                "classes": [
                    {"value": 1, "label": "Bosque no perturbado", "color": "#005a32"},
                    {"value": 2, "label": "Degradación", "color": "#f9c74f"},
                    {"value": 3, "label": "Deforestación", "color": "#d62828"},
                    {"value": 4, "label": "Regeneración forestal", "color": "#74c476"},
                    {"value": 5, "label": "Agua", "color": "#3182bd"},
                    {"value": 6, "label": "Otra cobertura", "color": "#c7c7c7"},
                ],
            },
        },
        "limitations": [
            "Preevaluación indicativa: no sustituye verificación documental o de campo.",
            "La coincidencia espacial orienta dónde revisar y no participa en el puntaje.",
            "La superposición con corredores aumenta valor estratégico, no prueba conectividad funcional.",
        ],
    }
