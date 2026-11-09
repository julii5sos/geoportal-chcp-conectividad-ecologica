"""Servicios de aplicación para la interfaz HTML y la API Flask."""

from __future__ import annotations

import copy
import io
import json
import os
import threading
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import ee
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

from analisis_temporal import (
    FUENTES_TEMPORALES,
    _estado_y_mascara_valida_ee,
    ejecutar_analisis_temporal_ee,
    normalizar_area_geojson,
    recortar_area_a_cuenca,
)
from analisis_integrado import (
    ANIO_FINAL_COMUN,
    ANIO_INICIAL_COMUN,
    ejecutar_analisis_integrado_ee,
)
from analisis_complementario import (
    GEDI_ASSET,
    HANSEN_ASSET,
    ejecutar_evidencia,
    preparar_capa_ndvi,
)
from cobertura_oficial_2023 import ASSET_COBERTURA_2023, consultar_cobertura_oficial_2023
from catalogo_assets_sinia import ASSETS_SINIA, catalogo_assets_sinia
from catalogo_multifuente import catalogo_por_categoria, matriz_trazabilidad
from corredores import (
    analizar_interseccion_corredores,
    calcular_radio_contexto,
    cargar_corredores,
    cargar_puntos_criticos,
)
from eri_gee import calcular_eri_geojson
from evaluacion_ecologica import ejecutar_evaluacion_ecologica
from gee_config import inicializar_earth_engine, resolver_proyecto_gee
from estructura_cobertura import SOURCE_2021, analizar_estructura_cobertura, consultar_cobertura_oficial_2021
from simbologia_geoportal import catalogo_simbologia
from informe_tecnico import generar_informe_tecnico
from metodologia_indice import calcular_prioridad_visita
from territorio_local import (
    coleccion_subcuencas,
    geometria_cuenca,
    geometria_subcuenca,
    nombres_subcuencas,
)
from webapp.cache import CachedResult, ResultCache
from webapp.models import (
    AnalysisRequest,
    AreaSelection,
    EcologicalEvaluationRequest,
    IntegratedEvaluationRequest,
    EriRequest,
    EvidenceRequest,
    LayerPreviewRequest,
    OfficialCoverageRequest,
    StructuralComparisonRequest,
    StructuralConnectivityRequest,
)


MAX_COORDINATES = int(os.getenv("WEB_MAX_COORDINATES", "5000"))
MAX_ANALYSIS_AREA_HA = float(os.getenv("WEB_MAX_ANALYSIS_AREA_HA", "345000"))
MAX_MAP_FEATURES = int(os.getenv("WEB_MAX_MAP_FEATURES", "1500"))

_CACHE = ResultCache(
    max_entries=int(os.getenv("WEB_RESULT_CACHE_ENTRIES", "6")),
    ttl_seconds=int(os.getenv("WEB_RESULT_CACHE_TTL", "3600")),
)
_EE_LOCK = threading.Lock()
_EE_READY = False


class RequestLimitError(ValueError):
    """La solicitud es válida en forma, pero supera un límite operativo."""


def _coordinate_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_coordinate_count(item) for item in value.values())
    if isinstance(value, list):
        if len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            return 1
        return sum(_coordinate_count(item) for item in value)
    return 0


def _area_ha(geometry: dict[str, Any]) -> float:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:8857", always_xy=True)
    return float(transform(transformer.transform, shape(geometry)).area / 10_000)


def _initialize_ee() -> str:
    global _EE_READY
    if not _EE_READY:
        with _EE_LOCK:
            if not _EE_READY:
                inicializar_earth_engine(ee)
                _EE_READY = True
    return resolver_proyecto_gee()


def resolve_area(selection: AreaSelection) -> tuple[dict[str, Any], dict[str, Any]]:
    basin = geometria_cuenca()
    if selection.mode == "basin":
        geometry = normalizar_area_geojson(basin)
        label = "Toda la Cuenca Hidrográfica del Canal de Panamá"
        excluded_ha = 0.0
    elif selection.mode == "subbasin":
        name = (selection.subbasin or "").strip()
        if name not in nombres_subcuencas():
            raise ValueError("La subcuenca seleccionada no existe en el catálogo local.")
        original = normalizar_area_geojson(geometria_subcuenca(name))
        original_ha = _area_ha(original)
        geometry = recortar_area_a_cuenca(original, basin)
        label = f"Subcuenca {name}"
        excluded_ha = max(0.0, original_ha - _area_ha(geometry))
    else:
        if _coordinate_count(selection.geometry) > MAX_COORDINATES:
            raise RequestLimitError(
                f"El polígono supera el límite de {MAX_COORDINATES:,} vértices."
            )
        original = normalizar_area_geojson(selection.geometry or {})
        original_ha = _area_ha(original)
        geometry = recortar_area_a_cuenca(original, basin)
        label = "Polígono dibujado"
        excluded_ha = max(0.0, original_ha - _area_ha(geometry))

    area_ha = _area_ha(geometry)
    if area_ha > MAX_ANALYSIS_AREA_HA:
        raise RequestLimitError(
            "El área supera el límite operativo configurado de "
            f"{MAX_ANALYSIS_AREA_HA:,.0f} ha."
        )
    return geometry, {
        "mode": selection.mode,
        "label": label,
        "area_ha": round(area_ha, 4),
        "excluded_outside_basin_ha": round(excluded_ha, 4),
    }


def configuration() -> dict[str, Any]:
    sources = {
        key: {
            **asdict(source),
            "years": list(source.anios),
        }
        for key, source in FUENTES_TEMPORALES.items()
    }
    sources["integrated"] = {
        "clave": "integrated",
        "nombre": "Concordancia JRC TMF + ESRI LULC",
        "anio_inicial": ANIO_INICIAL_COMUN,
        "anio_final": ANIO_FINAL_COMUN,
        "resolucion_m": 30,
        "years": list(range(ANIO_INICIAL_COMUN, ANIO_FINAL_COMUN + 1)),
        "definicion_bosque": "Compara ambas definiciones sin fusionarlas ni promediarlas.",
        "limitacion": "La concordancia entre productos no constituye validación independiente de campo.",
        "prioridad": "Modalidad integrada de comparación",
    }
    return {
        "project_id": resolver_proyecto_gee(),
        "sources": sources,
        "analyses": [
            {
                "key": "coverage",
                "name": "Cobertura forestal",
                "description": "Superficie bosque/no bosque y transiciones comparables.",
            },
            {
                "key": "fragmentation",
                "name": "Fragmentación",
                "description": "Parches, tamaño, densidad y borde para ambos años.",
            },
            {
                "key": "connectivity",
                "name": "Conectividad estructural",
                "description": "Componentes, aislamiento y relaciones bajo un umbral común.",
            },
        ],
        "limits": {
            "maximum_coordinates": MAX_COORDINATES,
            "maximum_area_ha": MAX_ANALYSIS_AREA_HA,
            "maximum_map_features_per_layer": MAX_MAP_FEATURES,
        },
        "eri": {
            "independent": True,
            "participates_in_temporal_metrics": False,
            "weights": {
                "integridad_estructural": 0.35,
                "conectividad": 0.25,
                "estabilidad_topografica": 0.20,
                "proximidad_riparia": 0.20,
            },
        },
        "symbology": catalogo_simbologia(),
    }


def source_catalog() -> dict[str, Any]:
    return {
        "sources": matriz_trazabilidad(),
        "categories": catalogo_por_categoria(),
        "official_assets": catalogo_assets_sinia(),
        "states": [
            "Integrada y operativa",
            "Integrada parcialmente",
            "Disponible pero no conectada",
            "Pendiente de permisos o migración",
            "No disponible",
            "Descartada justificadamente",
        ],
    }


def _limit_feature_collections(value: Any, report: list[dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        if value.get("type") == "FeatureCollection" and isinstance(value.get("features"), list):
            total = len(value["features"])
            limited = dict(value)
            limited["features"] = value["features"][:MAX_MAP_FEATURES]
            if total > MAX_MAP_FEATURES:
                report.append({"total": total, "shown": MAX_MAP_FEATURES})
            return limited
        return {key: _limit_feature_collections(item, report) for key, item in value.items()}
    if isinstance(value, list):
        return [_limit_feature_collections(item, report) for item in value]
    return value


def _public_record(item: CachedResult, *, cache_hit: bool) -> dict[str, Any]:
    value = copy.deepcopy(item.value)
    limits: list[dict[str, Any]] = []
    value = _limit_feature_collections(value, limits)
    return {
        "result_id": item.identifier,
        "cache_hit": cache_hit,
        "created_utc": datetime.fromtimestamp(item.created_at, timezone.utc).isoformat(),
        "map_feature_limits": limits,
        **value,
    }


def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "temporal_analysis",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        if request.source == "integrated":
            result = ejecutar_analisis_integrado_ee(
                anio_inicial=request.initial_year,
                anio_final=request.final_year,
                area_geojson=geometry,
                distancia_maxima_m=request.maximum_distance_m,
                area_minima_parche_ha=request.minimum_patch_area_ha,
                ee_module=ee,
            )
        else:
            result = ejecutar_analisis_temporal_ee(
                fuente=request.source,
                anio_inicial=request.initial_year,
                anio_final=request.final_year,
                area_geojson=geometry,
                distancia_maxima_m=request.maximum_distance_m,
                area_minima_parche_ha=request.minimum_patch_area_ha,
                ee_module=ee,
            )
        return {
            "kind": "integrated_analysis" if request.source == "integrated" else "temporal_analysis",
            "project_id": project,
            "selected_analyses": request.analyses,
            "area": {**area, "geometry": geometry},
            "result": result,
            "corridor_context": analizar_interseccion_corredores(geometry),
            "warnings": [
                "Resultado indicativo: requiere interpretación y verificación de campo.",
                "La conectividad calculada es estructural y no demuestra movimiento de fauna.",
                "JRC y ESRI conservan definiciones de bosque diferentes y no se mezclan.",
            ] + (result.get("warnings", []) if request.source == "integrated" else []),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_ecological_evaluation(request: EcologicalEvaluationRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "ecological_evaluation",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "algorithm_version": "original-ecological-evaluation-2026.1",
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        corridor_context = analizar_interseccion_corredores(geometry)
        result = ejecutar_evaluacion_ecologica(
            geometry, contexto_corredores=corridor_context,
            contexto_fragmentacion=None, ee_module=ee
        )
        return {
            "kind": "ecological_evaluation",
            "project_id": project,
            "area": {**area, "geometry": geometry},
            "result": result,
            "corridor_context": corridor_context,
            "warnings": result.get("limitations", []),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_integrated_evaluation(request: IntegratedEvaluationRequest) -> dict[str, Any]:
    """Combina resultados reales sin mezclar ni volver a formular sus métodos.

    ``run_ecological_evaluation`` y ``run_structural_connectivity`` conservan
    cachés independientes. Por eso una estructura ya calculada para la misma
    área y parámetros se reutiliza también en el análisis integral.
    """

    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "integrated_ecological_analysis",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "algorithm_version": "complementary-original-engines-2026.1",
    }

    def operation() -> dict[str, Any]:
        ecological = run_ecological_evaluation(
            EcologicalEvaluationRequest(
                area=request.area,
                territory_id=request.territory_id,
            )
        )
        structural = run_structural_connectivity(
            StructuralConnectivityRequest(
                area=request.area,
                scenario="official_2021",
                maximum_distance_m=request.maximum_distance_m,
                minimum_patch_area_ha=request.minimum_patch_area_ha,
                territory_id=request.territory_id,
            )
        )
        evaluation = copy.deepcopy(ecological["result"])
        # El primer cálculo territorial se mantiene rápido y no prepara parches.
        # Cuando el usuario solicita un análisis combinado, recuperamos aquí la
        # lectura integrada original con el contexto estructural ya calculado.
        # La estructura orienta la focalización, pero no suma un peso nuevo al
        # índice satelital de 6.5 puntos.
        evaluation["visit_priority"] = calcular_prioridad_visita(
            puntaje_cambios=evaluation.get("score", 0.0),
            contexto_corredores=ecological.get("corridor_context", {}),
            contexto_fragmentacion=structural["result"],
        )
        evaluation["structural_reference_2021"] = structural["result"]
        return {
            "kind": "integrated_ecological_analysis",
            "project_id": ecological["project_id"],
            "area": {**area, "geometry": geometry},
            "result": {
                "evaluation": evaluation,
                "structure": structural["result"],
                "selected_components": request.selected_components,
                "component_result_ids": {
                    "evaluation": ecological["result_id"],
                    "structure": structural["result_id"],
                },
            },
            "corridor_context": ecological.get("corridor_context", {}),
            "warnings": list(dict.fromkeys(
                ecological.get("warnings", []) + structural.get("warnings", [])
            )),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_structural_connectivity(request: StructuralConnectivityRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "structural_connectivity",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "algorithm_version": "original-landscape-engine-2026.1",
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        corridor_context = analizar_interseccion_corredores(geometry)
        radius = calcular_radio_contexto(
            corridor_context.get("distancia_corredor_mas_cercano_m"),
            request.maximum_distance_m,
        )
        result = analizar_estructura_cobertura(
            request.scenario,
            geometry,
            maximum_distance_m=request.maximum_distance_m,
            minimum_patch_area_ha=request.minimum_patch_area_ha,
            context_radius_m=radius,
            ee_module=ee,
        )
        return {
            "kind": "structural_connectivity",
            "project_id": project,
            "area": {**area, "geometry": geometry},
            "result": result,
            "corridor_context": corridor_context,
            "warnings": [
                "La conectividad es estructural y no demuestra desplazamiento de fauna.",
                result["comparability_warning"],
            ],
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_structural_comparison(request: StructuralComparisonRequest) -> dict[str, Any]:
    """Calcula 2021 y 2023 por separado sin presentar un cambio causal.

    Cada escenario conserva su propia fuente y se obtiene mediante el servicio
    estructural ya auditado. Esto permite reutilizar la caché de cada red y evita
    mantener una segunda implementación de fragmentación o conectividad.
    """

    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "structural_comparison_2021_2023",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "asset_versions": {"2021": SOURCE_2021, "2023": ASSET_COBERTURA_2023},
        "algorithm_version": "parallel-structural-scenarios-2026.1",
    }

    def operation() -> dict[str, Any]:
        common = {
            "area": request.area,
            "maximum_distance_m": request.maximum_distance_m,
            "minimum_patch_area_ha": request.minimum_patch_area_ha,
            "territory_id": request.territory_id,
        }
        reference = run_structural_connectivity(
            StructuralConnectivityRequest(scenario="official_2021", **common)
        )
        diagnostic = run_structural_connectivity(
            StructuralConnectivityRequest(scenario="diagnostic_2023", **common)
        )
        warning = (
            "Comparación exploratoria estructural entre cartografías 2021 y 2023. "
            "Las fuentes difieren en método y soporte (vector y ráster de 10 m); "
            "por ello se presentan diagnósticos paralelos y no un cambio causal."
        )
        return {
            "kind": "structural_comparison_2021_2023",
            "project_id": reference.get("project_id") or diagnostic.get("project_id"),
            "area": {**area, "geometry": geometry},
            "result": {
                "comparison_status": "parallel_diagnostics_only",
                "comparable_for_causal_change": False,
                "difference_metrics": None,
                "parameters": {
                    "maximum_distance_m": request.maximum_distance_m,
                    "minimum_patch_area_ha": request.minimum_patch_area_ha,
                },
                "scenarios": {
                    "2021": reference["result"],
                    "2023": diagnostic["result"],
                },
                "component_result_ids": {
                    "2021": reference["result_id"],
                    "2023": diagnostic["result_id"],
                },
                "interpretation": warning,
            },
            "corridor_context": reference.get("corridor_context", {}),
            "warnings": [
                warning,
                "Las conexiones son relaciones estructurales modeladas; no son corredores biológicos oficiales ni demuestran movimiento de fauna.",
                "No se publica una matriz de transición 2021–2023 porque todavía no existe un dictamen de homologación temática y geométrica.",
            ],
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_official_coverage(request: OfficialCoverageRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "official_coverage_2023",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "asset_version": ASSET_COBERTURA_2023,
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        result = consultar_cobertura_oficial_2023(geometry, ee_module=ee)
        return {
            "kind": "official_coverage_2023",
            "project_id": project,
            "area": {**area, "geometry": geometry},
            "result": result,
            "warnings": result.get("prohibited_interpretations", []),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_official_coverage_2021(request: OfficialCoverageRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "official_coverage_2021",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "asset_version": SOURCE_2021,
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        result = consultar_cobertura_oficial_2021(geometry, ee_module=ee)
        return {
            "kind": "official_coverage_2021",
            "project_id": project,
            "area": {**area, "geometry": geometry},
            "result": result,
            "warnings": result.get("prohibited_interpretations", []),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


def run_evidence(request: EvidenceRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "complementary_evidence",
        "request": request.model_dump(mode="json"),
        "resolved_geometry": geometry,
        "algorithm_version": "complementary-evidence-2026.1",
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        result = ejecutar_evidencia(
            request.source, geometry, request.initial_year, request.final_year,
            request.parameters, ee_module=ee,
        )
        return {
            "kind": "complementary_evidence",
            "project_id": project,
            "source_key": request.source,
            "area": {**area, "geometry": geometry},
            "result": result,
            "corridor_context": analizar_interseccion_corredores(geometry),
            "warnings": result.get("limitations", []),
        }

    territory_key = request.territory_id or ResultCache.signature({"geometry": geometry})
    item, cache_hit = _CACHE.run_once(payload, operation, territory_key=territory_key)
    return _public_record(item, cache_hit=cache_hit)


_PREVIEW_PALETTE = [
    "#2B83BA", "#1B7837", "#4D9221", "#A6D96A", "#01665E", "#DFC27D",
    "#80CDC1", "#8C510A", "#E6AB02", "#B35806", "#5E3C99", "#C2A5CF",
    "#FEE08B", "#D73027", "#66C2A5", "#3288BD", "#ABDDA4", "#FDAE61",
    "#9ECAE1", "#756BB1", "#31A354", "#E6550D", "#636363", "#BDB76B",
    "#6BAED6", "#74C476", "#FD8D3C", "#9E9AC8", "#969696", "#D9D9D9",
    "#3182BD", "#E7BA52", "#A6CEE3",
]

_PREVIEW_PALETTES_BY_SOURCE = {
    "2012_binario": ["#237A4B", "#D8C49C"],
    "2019_general": ["#237A4B", "#D8C49C", "#388FC4"],
    "2021_general": ["#237A4B", "#D8C49C", "#388FC4"],
    "2023_general": ["#237A4B", "#D8C49C", "#388FC4"],
}


def run_layer_preview(request: LayerPreviewRequest) -> dict[str, Any]:
    """Genera una tesela ligera; no reduce regiones ni ejecuta el motor científico."""
    geometry, area = resolve_area(request.area)
    inicializar_earth_engine(ee)
    ee_module = ee
    if request.source == "sentinel_ndvi":
        year = request.year or 2025
        descriptor = preparar_capa_ndvi(geometry, year, ee_module=ee_module)
        return {"kind": "layer_preview", "source_key": request.source, "area": {**area, "geometry": geometry}, "layer": descriptor}

    area_ee = ee_module.Geometry(geometry)
    if request.source in {"jrc_tmf", "esri_lulc"}:
        year = request.year or 2025
        state, valid = _estado_y_mascara_valida_ee(
            request.source, year, area_ee, ee_module=ee_module
        )
        if request.source == "jrc_tmf":
            classes = [
                {"value": 1, "etiqueta": "Bosque no perturbado", "color": "#005a32"},
                {"value": 2, "etiqueta": "Degradación", "color": "#f9c74f"},
                {"value": 3, "etiqueta": "Deforestación", "color": "#d62828"},
                {"value": 4, "etiqueta": "Regeneración forestal", "color": "#74c476"},
                {"value": 5, "etiqueta": "Agua", "color": "#3182bd"},
                {"value": 6, "etiqueta": "Otra cobertura", "color": "#c7c7c7"},
            ]
            source_name = "JRC Tropical Moist Forest v1_2025"
            limitation = "Clasificación anual JRC TMF; no representa todos los tipos de bosque de Panamá."
        else:
            classes = [
                {"value": 1, "etiqueta": "Agua", "color": "#419bdf"},
                {"value": 2, "etiqueta": "Árboles", "color": "#397d49"},
                {"value": 4, "etiqueta": "Vegetación inundada", "color": "#7a87c6"},
                {"value": 5, "etiqueta": "Cultivos", "color": "#e49635"},
                {"value": 7, "etiqueta": "Área construida", "color": "#c4281b"},
                {"value": 8, "etiqueta": "Suelo desnudo", "color": "#a59b8f"},
                {"value": 9, "etiqueta": "Nieve o hielo", "color": "#a8ebff"},
                {"value": 11, "etiqueta": "Pastos o matorral", "color": "#88b053"},
            ]
            source_name = "ESRI Global Land Use / Land Cover"
            limitation = "La clase Trees es cobertura arbórea según ESRI y no equivale a bosque natural validado."
        values = [item["value"] for item in classes]
        display = state.updateMask(valid).remap(values, list(range(len(values)))).rename("class")
        map_id = display.getMapId({
            "min": 0,
            "max": max(1, len(values) - 1),
            "palette": [item["color"].lstrip("#") for item in classes],
        })
        descriptor = {
            "tile_url": map_id["tile_fetcher"].url_format,
            "legend": f"{source_name} · {year}",
            "classes": classes,
            "year": year,
            "source": source_name,
            "limitation": limitation,
        }
        return {"kind": "layer_preview", "source_key": request.source, "area": {**area, "geometry": geometry}, "layer": descriptor}

    if request.source == "hansen_gfc":
        year = request.year or 2025
        if year < 2001 or year > 2025:
            raise ValueError("Hansen admite años de pérdida entre 2001 y 2025.")
        loss = ee_module.Image(HANSEN_ASSET).select("lossyear").eq(year - 2000).selfMask().clip(area_ee)
        map_id = loss.getMapId({"min": 1, "max": 1, "palette": ["b42318"]})
        descriptor = {
            "tile_url": map_id["tile_fetcher"].url_format,
            "legend": f"Pérdida de cobertura arbórea Hansen · {year}",
            "classes": [{"value": 1, "etiqueta": f"Pérdida detectada en {year}", "color": "#b42318"}],
            "year": year,
            "source": "Hansen Global Forest Change v1.13",
            "limitation": "La pérdida de cobertura arbórea no equivale automáticamente a deforestación.",
        }
        return {"kind": "layer_preview", "source_key": request.source, "area": {**area, "geometry": geometry}, "layer": descriptor}

    if request.source == "gedi":
        collection = (ee_module.ImageCollection(GEDI_ASSET).filterBounds(area_ee)
                      .select([0], ["canopy_height"])
                      .map(lambda image: ee_module.Image(image).toFloat()))
        empty = (ee_module.Image.constant(0).rename("canopy_height")
                 .updateMask(ee_module.Image(0)).toFloat()
                 .setDefaultProjection("EPSG:4326", None, 100))
        image = (collection.merge(ee_module.ImageCollection.fromImages([empty])).mosaic()
                 .setDefaultProjection("EPSG:4326", None, 100).clip(area_ee))
        classes = [
            {"value": "0-10", "etiqueta": "0–10 m", "color": "#fff7bc"},
            {"value": "10-20", "etiqueta": "10–20 m", "color": "#7fcdbb"},
            {"value": "20-30", "etiqueta": "20–30 m", "color": "#225ea8"},
            {"value": ">30", "etiqueta": "Más de 30 m", "color": "#081d58"},
        ]
        map_id = image.getMapId({"min": 0, "max": 45, "palette": ["fff7bc", "7fcdbb", "225ea8", "081d58"]})
        descriptor = {
            "tile_url": map_id["tile_fetcher"].url_format,
            "legend": "Altura del dosel GEDI",
            "classes": classes,
            "year": None,
            "source": "OpenForis World EarthMap CanopyHeight GEDI V27",
            "limitation": "Referencia fija con zonas sin observación; no convierte altura en edad o biomasa.",
        }
        return {"kind": "layer_preview", "source_key": request.source, "area": {**area, "geometry": geometry}, "layer": descriptor}

    ficha = ASSETS_SINIA[request.source]
    codes = [int(code) for code in ficha["leyenda"].keys()]
    if ficha["tipo_esperado"] == "TABLE":
        field = str(ficha.get("campo_tematico") or "Categoria")
        collection = ee_module.FeatureCollection(ficha["asset_id"]).filterBounds(area_ee)
        indexed = ee_module.Image(0).toByte().clip(area_ee)
        for code in codes:
            label = ficha["leyenda"][code]
            indexed = indexed.paint(collection.filter(ee_module.Filter.eq(field, label)), code)
        indexed = indexed.selfMask().remap(codes, list(range(len(codes)))).rename("class")
    else:
        image = ee_module.Image(ficha["asset_id"]).select(0)
        nodata = ficha.get("nodata")
        if nodata is not None:
            image = image.updateMask(image.neq(nodata))
        indexed = image.remap(codes, list(range(len(codes)))).rename("class").clip(area_ee)
    palette = _PREVIEW_PALETTES_BY_SOURCE.get(request.source, _PREVIEW_PALETTE)[: len(codes)]
    map_id = indexed.getMapId({"min": 0, "max": max(1, len(codes) - 1), "palette": [color.lstrip("#") for color in palette]})
    descriptor = {
        "tile_url": map_id["tile_fetcher"].url_format,
        "legend": f"{ficha['nombre']} · {ficha['anio']}",
        "classes": [
            {"value": code, "etiqueta": ficha["leyenda"][code], "color": palette[index]}
            for index, code in enumerate(codes)
        ],
        "year": ficha["anio"],
        "source": "SINIA–MiAMBIENTE",
        "limitation": ficha["limitacion"],
    }
    return {"kind": "layer_preview", "source_key": request.source, "area": {**area, "geometry": geometry}, "layer": descriptor}


def run_eri(request: EriRequest) -> dict[str, Any]:
    geometry, area = resolve_area(request.area)
    payload = {
        "kind": "eri",
        "area": request.area.model_dump(mode="json"),
        "resolved_geometry": geometry,
    }

    def operation() -> dict[str, Any]:
        project = _initialize_ee()
        return {
            "kind": "eri",
            "project_id": project,
            "area": {**area, "geometry": geometry},
            "result": calcular_eri_geojson(geometry, ee_module=ee),
            "warnings": [
                "El ERI es complementario, indicativo y no modifica el análisis temporal.",
                "Sus pesos requieren validación de campo antes de un uso normativo.",
            ],
        }

    item, cache_hit = _CACHE.run_once(payload, operation)
    return _public_record(item, cache_hit=cache_hit)


def cached_result(identifier: str) -> CachedResult | None:
    if len(identifier) != 32 or any(char not in "0123456789abcdef" for char in identifier):
        return None
    return _CACHE.get(identifier)


def public_cached_result(identifier: str) -> dict[str, Any] | None:
    item = cached_result(identifier)
    return _public_record(item, cache_hit=True) if item else None


def latest_result(territory_key: str) -> dict[str, Any] | None:
    if not territory_key or len(territory_key) > 180:
        return None
    item = _CACHE.latest(territory_key)
    return _public_record(item, cache_hit=True) if item else None


def build_download(identifier: str) -> bytes | None:
    item = cached_result(identifier)
    if item is None:
        return None
    value = copy.deepcopy(item.value)

    def remove_ephemeral_urls(content: Any) -> Any:
        if isinstance(content, dict):
            return {
                key: remove_ephemeral_urls(child)
                for key, child in content.items()
                if key != "tile_url"
            }
        if isinstance(content, list):
            return [remove_ephemeral_urls(child) for child in content]
        return content

    value = remove_ephemeral_urls(value)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "resultado_completo.json",
            json.dumps(value, ensure_ascii=False, indent=2),
        )
        area = value.get("area", {})
        if area.get("geometry"):
            archive.writestr(
                "area_analizada.geojson",
                json.dumps(area["geometry"], ensure_ascii=False, indent=2),
            )
        result = value.get("result", {})
        for key, transition in (result.get("transiciones") or {}).items():
            if transition.get("geojson"):
                archive.writestr(
                    f"transicion_{key}.geojson",
                    json.dumps(transition["geojson"], ensure_ascii=False, indent=2),
                )
        if result.get("mode") == "integrated":
            archive.writestr(
                "concordancia_resumen.json",
                json.dumps(result.get("concordance", {}), ensure_ascii=False, indent=2),
            )
            for source_key, source_result in (result.get("sources") or {}).items():
                archive.writestr(
                    f"fuente_{source_key}_resultado.json",
                    json.dumps(source_result, ensure_ascii=False, indent=2),
                )
        kind = value.get("kind")
        if kind == "complementary_evidence":
            methodology = (
                "Geoportal de Conectividad Ecológica de la CHCP — evidencia complementaria\n"
                f"Fuente: {result.get('source', value.get('source_key', 'no indicada'))}\n"
                f"Asset: {result.get('asset', 'no indicado')}\n"
                "Este producto conserva su metodología y no se fusiona automáticamente con JRC, ESRI, ERI ni corredores.\n"
                "Revise resultado_completo.json para parámetros, período y limitaciones.\n"
            )
        elif kind == "eri":
            methodology = (
                "Geoportal de Conectividad Ecológica de la CHCP — ERI complementario\n"
                "El ERI permanece separado de cobertura, fragmentación y conectividad temporal.\n"
                "Sus pesos originales no fueron modificados.\n"
            )
        elif kind == "structural_comparison_2021_2023":
            methodology = (
                "Geoportal de Conectividad Ecológica de la CHCP — escenarios estructurales 2021 y 2023\n"
                "Cada escenario reutiliza bosque_conectividad.py con el mismo umbral y área mínima.\n"
                "2021 procede del vector institucional; 2023 de la clase 1 del ráster diagnóstico a 10 m.\n"
                "Se entregan diagnósticos paralelos. No se afirma cambio causal, pérdida o ganancia entre productos.\n"
            )
        else:
            methodology = (
                "Geoportal de Conectividad Ecológica de la CHCP — análisis temporal\n"
                "Los cálculos reutilizan analisis_temporal.py y bosque_conectividad.py.\n"
                "El ERI permanece separado de las métricas temporales.\n"
                "La modalidad integrada calcula JRC y ESRI por separado y compara su concordancia; no fusiona productos.\n"
                "Consulte docs/METODOLOGIA_ANALISIS_TEMPORAL.md para las limitaciones.\n"
            )
        archive.writestr("METODOLOGIA.txt", methodology)
    return output.getvalue()


def build_technical_report(identifier: str) -> bytes | None:
    """Genera un PDF desde el valor persistido; nunca vuelve a llamar a EE."""
    item = cached_result(identifier)
    if item is None:
        return None
    value = copy.deepcopy(item.value)
    value["result_id"] = item.identifier
    return generar_informe_tecnico(value)


def territory_payload() -> dict[str, Any]:
    return {
        "basin": {
            "type": "Feature",
            "properties": {"name": "CHCP"},
            "geometry": geometria_cuenca(),
        },
        "subbasins": coleccion_subcuencas(),
        "corridors": cargar_corredores(),
        "critical_points": cargar_puntos_criticos(),
    }


def corridor_context(geometry: dict[str, Any]) -> dict[str, Any]:
    return analizar_interseccion_corredores(geometry)

