"""Escenarios estructurales 2021 (referencia) y 2023 (diagnóstico)."""

from __future__ import annotations

import os
from typing import Any, Literal

from bosque_conectividad import analizar_fragmentacion_geojson
from catalogo_assets_sinia import ASSETS_SINIA
from corredores import cargar_corredores


SOURCE_2021 = os.getenv(
    "SINIA_2021_FOREST_ASSET",
    str(ASSETS_SINIA["2021_general"]["asset_id"]),
)
SOURCE_2023 = os.getenv(
    "SINIA_2023_FOREST_ASSET",
    str(ASSETS_SINIA["2023_general"]["asset_id"]),
)
FOREST_CATEGORY_2021 = "Bosques y Otras Tierras Boscosas"
CATEGORIES_2021 = {
    1: {"label": FOREST_CATEGORY_2021, "color": "#237A4B"},
    2: {"label": "Otras Tierras", "color": "#D8C49C"},
    3: {"label": "Aguas Continentales", "color": "#388FC4"},
}
Scenario = Literal["official_2021", "diagnostic_2023"]


class StructuralCoverageUnavailable(ValueError):
    """Fallo operativo con mensaje público breve y diagnóstico trazable."""

    public_message = (
        "No se pudo cargar la cobertura forestal oficial 2021. Los análisis de "
        "fragmentación y conectividad no están disponibles temporalmente."
    )

    def __init__(self, technical_detail: str):
        super().__init__(self.public_message)
        self.technical_detail = technical_detail


def _context_radius(value: float, threshold: float) -> float:
    return min(5_000.0, max(float(threshold), float(value)))


def _forest_geometry_2021(geometry, context_radius_m: float, ee_module) -> dict[str, Any]:
    context = geometry.buffer(context_radius_m)
    collection = (
        ee_module.FeatureCollection(SOURCE_2021)
        .filter(ee_module.Filter.eq("Categoria", FOREST_CATEGORY_2021))
        .filterBounds(context)
    )
    try:
        feature_count = int(collection.size().getInfo())
    except Exception as exc:
        if "not found" in str(exc).lower() or "not have permission" in str(exc).lower():
            raise StructuralCoverageUnavailable(
                "No fue posible leer el FeatureCollection estructural 2021 "
                f"({SOURCE_2021}) con la identidad Earth Engine activa: {exc}"
            ) from exc
        raise
    if feature_count == 0:
        return {"type": "FeatureCollection", "features": []}
    return (
        collection.geometry(10)
        .intersection(context, 10)
        .simplify(10)
        .getInfo()
    )


def _forest_geometry_2023(geometry, context_radius_m: float, ee_module) -> dict[str, Any]:
    context = geometry.buffer(context_radius_m)
    image = ee_module.Image(SOURCE_2023).select("b1")
    # El GeoTIFF se recorta antes de vectorizar. La clase 1 y vecindad de ocho
    # píxeles son explícitas; no se vectoriza el ráster nacional completo.
    forest = image.eq(1).selfMask().clip(context).toByte().rename("forest")
    vectors = forest.reduceToVectors(
        geometry=context,
        scale=10,
        crs="EPSG:32617",
        geometryType="polygon",
        eightConnected=True,
        labelProperty="class_code",
        reducer=ee_module.Reducer.countEvery(),
        maxPixels=1e9,
        tileScale=8,
    )
    if int(vectors.size().getInfo()) == 0:
        return {"type": "FeatureCollection", "features": []}
    return vectors.geometry(10).intersection(context, 10).simplify(10).getInfo()


def consultar_cobertura_oficial_2021(
    area_geojson: dict[str, Any], *, ee_module
) -> dict[str, Any]:
    """Resume las categorías reales del vector institucional dentro del AOI.

    Esta consulta reutiliza el mismo asset que alimenta la fragmentación original.
    Las tres categorías se mantienen amplias y no se reinterpretan como una
    clasificación detallada de uso del suelo.
    """

    geometry = ee_module.Geometry(area_geojson, proj="EPSG:4326", geodesic=False)
    collection = ee_module.FeatureCollection(SOURCE_2021).filterBounds(geometry)
    rows: list[dict[str, Any]] = []
    display = ee_module.Image(0).toByte().clip(geometry)
    total_classified = 0.0
    for code, definition in CATEGORIES_2021.items():
        category = collection.filter(ee_module.Filter.eq("Categoria", definition["label"]))
        count = int(category.size().getInfo() or 0)
        hectares = 0.0
        if count:
            clipped = category.geometry(10).intersection(geometry, 10)
            hectares = float(clipped.area(1).divide(10_000).getInfo() or 0)
            display = display.paint(category, code)
        total_classified += hectares
        rows.append({
            "code": code,
            "label": definition["label"],
            "feature_count": count,
            "area_ha": round(hectares, 4),
        })

    area_aoi = float(geometry.area(1).divide(10_000).getInfo() or 0)
    for row in rows:
        row["percentage"] = (
            round(row["area_ha"] / total_classified * 100, 4)
            if total_classified else 0.0
        )
    palette = [CATEGORIES_2021[code]["color"].lstrip("#") for code in CATEGORIES_2021]
    map_id = display.selfMask().getMapId({"min": 1, "max": 3, "palette": palette})
    return {
        "mode": "official_coverage_2021",
        "source": "SINIA–MiAMBIENTE · Bosque y otros usos",
        "asset": SOURCE_2021,
        "year": 2021,
        "native_grid": {"type": "vector", "scale": "institucional"},
        "statistics": {
            "aoi_area_ha": round(area_aoi, 4),
            "total_classified_ha": round(total_classified, 4),
            "unclassified_or_nodata_ha": round(max(0.0, area_aoi - total_classified), 4),
            "percentage_denominator": "superficie clasificada por las tres categorías institucionales",
            "classes": rows,
        },
        "map": {
            "tile_url": map_id["tile_fetcher"].url_format,
            "classes": [
                {"value": code, "label": item["label"], "color": item["color"]}
                for code, item in CATEGORIES_2021.items()
            ],
        },
        "legend_status": "verified_from_asset_categories",
        "forest_class_available": True,
        "allowed_uses": [
            "superficie por categoría dentro del área",
            "referencia oficial 2021 para fragmentación y conectividad estructural",
        ],
        "prohibited_interpretations": [
            "La categoría forestal agrupa bosques y otras tierras boscosas.",
            "El asset no distingue usos detallados dentro de Otras Tierras.",
            "No debe compararse directamente con 2023 hasta demostrar compatibilidad temática y geométrica.",
        ],
    }


def analizar_estructura_cobertura(
    scenario: Scenario,
    area_geojson: dict[str, Any],
    *,
    maximum_distance_m: float = 500,
    minimum_patch_area_ha: float = 0,
    context_radius_m: float = 5_000,
    ee_module,
) -> dict[str, Any]:
    if scenario not in {"official_2021", "diagnostic_2023"}:
        raise ValueError("Escenario estructural no admitido.")
    geometry = ee_module.Geometry(area_geojson, proj="EPSG:4326", geodesic=False)
    radius = _context_radius(context_radius_m, maximum_distance_m)
    if scenario == "official_2021":
        forest_geometry = _forest_geometry_2021(geometry, radius, ee_module)
        source = SOURCE_2021
        year = 2021
        authority = "referencia oficial del diagnóstico original"
        adaptation = "Colección vectorial filtrada por Categoria; misma entrada metodológica del motor original."
    else:
        forest_geometry = _forest_geometry_2023(geometry, radius, ee_module)
        source = SOURCE_2023
        year = 2023
        authority = "escenario diagnóstico complementario"
        adaptation = (
            "GeoTIFF clase 1 vectorizado dentro del AOI y contexto; píxel 10 m, "
            "vecindad de ocho y sin interpolación de clases."
        )
    analysis = analizar_fragmentacion_geojson(
        bosque_geojson=forest_geometry,
        aoi_geojson=area_geojson,
        umbral_m=maximum_distance_m,
        area_min_ha=minimum_patch_area_ha,
        incluir_contexto_exterior=True,
        corredores_geojson=cargar_corredores(),
        radio_busqueda_corredor_m=radius,
    )
    analysis.update({
        "scenario": scenario,
        "source_asset": source,
        "reference_year": year,
        "authority": authority,
        "context_radius_m": radius,
        "source_adaptation": adaptation,
        "forest_definition": FOREST_CATEGORY_2021 if scenario == "official_2021" else "Código 1 · Bosques y otras tierras boscosas",
        "comparability_warning": (
            "Los escenarios 2021 y 2023 no se interpretan como cambio temporal "
            "hasta demostrar compatibilidad de clasificación, escala y geometría."
        ),
    })
    return analysis
