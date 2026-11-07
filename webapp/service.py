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
    ejecutar_analisis_temporal_ee,
    normalizar_area_geojson,
    recortar_area_a_cuenca,
)
from analisis_integrado import (
    ANIO_FINAL_COMUN,
    ANIO_INICIAL_COMUN,
    ejecutar_analisis_integrado_ee,
)
from analisis_complementario import ejecutar_evidencia
from catalogo_multifuente import catalogo_por_categoria, matriz_trazabilidad
from corredores import analizar_interseccion_corredores, cargar_corredores, cargar_puntos_criticos
from eri_gee import calcular_eri_geojson
from gee_config import inicializar_earth_engine, resolver_proyecto_gee
from simbologia_geoportal import catalogo_simbologia
from territorio_local import (
    coleccion_subcuencas,
    geometria_cuenca,
    geometria_subcuenca,
    nombres_subcuencas,
)
from webapp.cache import CachedResult, ResultCache
from webapp.models import AnalysisRequest, AreaSelection, EriRequest, EvidenceRequest


MAX_COORDINATES = int(os.getenv("WEB_MAX_COORDINATES", "5000"))
MAX_ANALYSIS_AREA_HA = float(os.getenv("WEB_MAX_ANALYSIS_AREA_HA", "345000"))
MAX_MAP_FEATURES = int(os.getenv("WEB_MAX_MAP_FEATURES", "1500"))

_CACHE = ResultCache(
    max_entries=int(os.getenv("WEB_RESULT_CACHE_ENTRIES", "4")),
    ttl_seconds=int(os.getenv("WEB_RESULT_CACHE_TTL", "900")),
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
                "Geoportal CHCP 2.0 — evidencia complementaria\n"
                f"Fuente: {result.get('source', value.get('source_key', 'no indicada'))}\n"
                f"Asset: {result.get('asset', 'no indicado')}\n"
                "Este producto conserva su metodología y no se fusiona automáticamente con JRC, ESRI, ERI ni corredores.\n"
                "Revise resultado_completo.json para parámetros, período y limitaciones.\n"
            )
        elif kind == "eri":
            methodology = (
                "Geoportal CHCP 2.0 — ERI complementario\n"
                "El ERI permanece separado de cobertura, fragmentación y conectividad temporal.\n"
                "Sus pesos originales no fueron modificados.\n"
            )
        else:
            methodology = (
                "Geoportal CHCP 2.0 — análisis temporal\n"
                "Los cálculos reutilizan analisis_temporal.py y bosque_conectividad.py.\n"
                "El ERI permanece separado de las métricas temporales.\n"
                "La modalidad integrada calcula JRC y ESRI por separado y compara su concordancia; no fusiona productos.\n"
                "Consulte docs/METODOLOGIA_ANALISIS_TEMPORAL.md para las limitaciones.\n"
            )
        archive.writestr("METODOLOGIA.txt", methodology)
    return output.getvalue()


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

