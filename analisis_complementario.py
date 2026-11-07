"""Evidencias multifuente recuperadas del visor científico original.

Cada fuente conserva su significado. Este módulo no fusiona Hansen, NDVI, GEDI,
WorldCover ni SINIA con las coberturas temporales JRC/ESRI.
"""

from __future__ import annotations

import os
from typing import Any


HANSEN_ASSET = "UMD/hansen/global_forest_change_2025_v1_13"
SENTINEL_ASSET = "COPERNICUS/S2_SR_HARMONIZED"
GEDI_ASSET = "users/openforisearthmap/World_EarthMap/CanopyHeight_GEDI_V27"
WORLDCOVER_ASSET = "ESA/WorldCover/v200"
FIRMS_ASSET = "FIRMS"


def _tile(image, visualization: dict[str, Any]) -> str:
    map_id = image.getMapId(visualization)
    return map_id["tile_fetcher"].url_format


def _geometry(ee_module, geojson: dict[str, Any]):
    return ee_module.Geometry(geojson, proj="EPSG:4326", geodesic=False)


def _reduce(image, geometry, reducer, *, scale: int, ee_module) -> dict[str, Any]:
    return image.reduceRegion(
        reducer=reducer,
        geometry=geometry,
        scale=scale,
        bestEffort=True,
        maxPixels=1e9,
        tileScale=4,
    ).getInfo() or {}


def analizar_hansen(
    geojson: dict[str, Any], initial_year: int, final_year: int,
    *, threshold: int = 30, ee_module,
) -> dict[str, Any]:
    if not 2001 <= initial_year <= final_year <= 2025:
        raise ValueError("Hansen admite pérdida anual entre 2001 y 2025.")
    geometry = _geometry(ee_module, geojson)
    image = ee_module.Image(HANSEN_ASSET)
    loss_year = image.select("lossyear")
    base = image.select("treecover2000").gte(threshold)
    pixel_ha = ee_module.Image.pixelArea().divide(10_000)
    bands = []
    years = list(range(initial_year, final_year + 1))
    for year in years:
        bands.append(loss_year.eq(year - 2000).multiply(pixel_ha).rename(f"loss_{year}"))
    stats = _reduce(ee_module.Image.cat(bands), geometry, ee_module.Reducer.sum(), scale=30, ee_module=ee_module)
    base_ha = _reduce(base.multiply(pixel_ha).rename("base_ha"), geometry, ee_module.Reducer.sum(), scale=30, ee_module=ee_module).get("base_ha", 0) or 0
    values = [float(stats.get(f"loss_{year}") or 0) for year in years]
    cumulative = sum(values)
    masked_loss = loss_year.updateMask(loss_year.gte(initial_year - 2000).And(loss_year.lte(final_year - 2000))).clip(geometry)
    return {
        "source": "Hansen Global Forest Change v1.13",
        "asset": HANSEN_ASSET,
        "period": {"initial": initial_year, "final": final_year},
        "parameters": {"tree_cover_2000_threshold_pct": threshold},
        "statistics": {
            "tree_cover_2000_above_threshold_ha": round(float(base_ha), 4),
            "loss_interval_ha": round(cumulative, 4),
            "loss_pct_of_2000_threshold_area": round(cumulative / float(base_ha) * 100, 4) if base_ha else None,
            "annual_loss_ha": [{"year": year, "value": round(value, 4)} for year, value in zip(years, values)],
        },
        "maps": {"loss_year": {"tile_url": _tile(masked_loss, {"min": 1, "max": 25, "palette": ["f7d794", "e77f67", "b42318"]}), "legend": "Año de pérdida (2001–2025)"}},
        "limitations": [
            "La pérdida de cobertura arbórea no equivale automáticamente a deforestación ni identifica una causa.",
            "El umbral se aplica a treecover2000; no genera por sí solo un mapa validado de bosque actual.",
        ],
    }


def _mask_sentinel_scl(image, ee_module):
    scl = image.select("SCL")
    valid = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
    return image.updateMask(valid).select(["B8", "B4"]).toFloat()


def _ndvi(year: int, geometry, ee_module):
    fallback_year = max(year - 1, 2017)

    def collection(value):
        return (ee_module.ImageCollection(SENTINEL_ASSET)
                .filterBounds(geometry).filterDate(f"{value}-01-01", f"{value + 1}-01-01")
                .filter(ee_module.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
                .map(lambda image: _mask_sentinel_scl(image, ee_module)))

    empty = ee_module.Image.constant([0, 0]).rename(["B8", "B4"]).updateMask(ee_module.Image(0)).toFloat()
    current = collection(year).merge(ee_module.ImageCollection.fromImages([empty])).median()
    previous = collection(fallback_year).merge(ee_module.ImageCollection.fromImages([empty])).median()
    composite = ee_module.ImageCollection.fromImages([empty, previous, current]).mosaic().setDefaultProjection("EPSG:4326", None, 10)
    return composite.normalizedDifference(["B8", "B4"]).rename("ndvi").toFloat().clip(geometry)


def analizar_ndvi(geojson: dict[str, Any], initial_year: int, final_year: int, *, ee_module) -> dict[str, Any]:
    if not 2017 <= initial_year < final_year <= 2026:
        raise ValueError("NDVI Sentinel-2 requiere dos años entre 2017 y 2026.")
    geometry = _geometry(ee_module, geojson)
    initial = _ndvi(initial_year, geometry, ee_module)
    final = _ndvi(final_year, geometry, ee_module)
    delta = final.subtract(initial).rename("delta_ndvi")
    valid_ha = final.mask().multiply(ee_module.Image.pixelArea()).divide(10_000).rename("valid_ha")
    reducer = ee_module.Reducer.mean().combine(ee_module.Reducer.median(), sharedInputs=True)
    s0 = _reduce(initial, geometry, reducer, scale=20, ee_module=ee_module)
    s1 = _reduce(final, geometry, reducer, scale=20, ee_module=ee_module)
    sd = _reduce(delta, geometry, reducer, scale=20, ee_module=ee_module)
    valid = _reduce(valid_ha, geometry, ee_module.Reducer.sum(), scale=20, ee_module=ee_module)
    palette = ["8c510a", "d8b365", "f6e8c3", "5ab4ac", "01665e"]
    return {
        "source": "Sentinel-2 Surface Reflectance Harmonized",
        "asset": SENTINEL_ASSET,
        "period": {"initial": initial_year, "final": final_year},
        "statistics": {
            "initial_mean": s0.get("ndvi_mean"), "initial_median": s0.get("ndvi_median"),
            "final_mean": s1.get("ndvi_mean"), "final_median": s1.get("ndvi_median"),
            "difference_mean": sd.get("delta_ndvi_mean"), "difference_median": sd.get("delta_ndvi_median"),
            "valid_area_final_ha": valid.get("valid_ha"),
        },
        "maps": {
            "initial": {"tile_url": _tile(initial, {"min": -0.2, "max": 0.9, "palette": palette}), "legend": f"NDVI {initial_year}"},
            "final": {"tile_url": _tile(final, {"min": -0.2, "max": 0.9, "palette": palette}), "legend": f"NDVI {final_year}"},
            "difference": {"tile_url": _tile(delta, {"min": -0.4, "max": 0.4, "palette": ["b2182b", "f7f7f7", "1a9850"]}), "legend": "Diferencia NDVI"},
        },
        "method": "Mediana anual; máscara SCL de vegetación, suelo, agua y nieve; respaldo del año anterior solo donde falta el año solicitado.",
        "limitations": ["NDVI no identifica bosque maduro, biodiversidad ni restauración por sí solo.", "La estacionalidad, humedad, nubes residuales y uso agrícola pueden modificar el valor."],
    }


def analizar_gedi(geojson: dict[str, Any], *, ee_module) -> dict[str, Any]:
    geometry = _geometry(ee_module, geojson)
    collection = (ee_module.ImageCollection(GEDI_ASSET).filterBounds(geometry)
                  .select([0], ["canopy_height"]).map(lambda image: ee_module.Image(image).toFloat()))
    empty = ee_module.Image.constant(0).rename("canopy_height").updateMask(ee_module.Image(0)).toFloat().setDefaultProjection("EPSG:4326", None, 100)
    image = collection.merge(ee_module.ImageCollection.fromImages([empty])).mosaic().setDefaultProjection("EPSG:4326", None, 100).clip(geometry)
    reducer = ee_module.Reducer.mean().combine(ee_module.Reducer.median(), sharedInputs=True).combine(ee_module.Reducer.percentile([25, 75]), sharedInputs=True)
    stats = _reduce(image, geometry, reducer, scale=100, ee_module=ee_module)
    valid = image.mask().multiply(ee_module.Image.pixelArea()).divide(10_000).rename("valid_ha")
    valid_ha = _reduce(valid, geometry, ee_module.Reducer.sum(), scale=100, ee_module=ee_module).get("valid_ha")
    return {
        "source": "OpenForis World EarthMap CanopyHeight GEDI V27",
        "asset": GEDI_ASSET,
        "period": {"type": "fixed_reference"},
        "statistics": {**stats, "valid_area_ha": valid_ha},
        "maps": {"canopy_height": {"tile_url": _tile(image, {"min": 0, "max": 45, "palette": ["fff7bc", "7fcdbb", "225ea8", "081d58"]}), "legend": "Altura del dosel (m)"}},
        "limitations": ["Es un producto derivado de altura del dosel, no huellas GEDI L2 descargadas por la aplicación.", "No convierte altura en edad, biomasa ni calidad del hábitat y puede contener zonas sin observación."],
    }


def analizar_worldcover(geojson: dict[str, Any], *, ee_module) -> dict[str, Any]:
    geometry = _geometry(ee_module, geojson)
    image = ee_module.ImageCollection(WORLDCOVER_ASSET).first().select("Map").clip(geometry)
    histogram = _reduce(image, geometry, ee_module.Reducer.frequencyHistogram(), scale=10, ee_module=ee_module).get("Map", {})
    pixel_area = 0.01
    classes = {str(key): round(float(value) * pixel_area, 4) for key, value in (histogram or {}).items()}
    class_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
    display = image.remap(class_values, list(range(1, len(class_values) + 1))).rename("Map")
    return {
        "source": "ESA WorldCover v200",
        "asset": WORLDCOVER_ASSET,
        "period": {"year": 2021},
        "statistics": {"class_area_ha_approx": classes, "tree_cover_ha_approx": classes.get("10", 0)},
        "maps": {"land_cover": {"tile_url": _tile(display, {"min": 1, "max": 11, "palette": ["006400", "ffbb22", "ffff4c", "f096ff", "fa0000", "b4b4b4", "f0f0f0", "0064c8", "0096a0", "00cf75", "fae6a0"]}), "legend": "Clases WorldCover 2021"}},
        "limitations": ["WorldCover v200 es una referencia 2021; no se presenta como serie anual.", "La clase 10 es cobertura arbórea según la leyenda del producto, no una validación independiente de bosque natural."],
    }


def ejecutar_evidencia(source: str, geojson: dict[str, Any], initial_year: int | None, final_year: int | None, parameters: dict[str, Any], *, ee_module) -> dict[str, Any]:
    if source == "hansen_gfc":
        return analizar_hansen(geojson, initial_year or 2001, final_year or 2025, threshold=int(parameters.get("tree_cover_threshold", 30)), ee_module=ee_module)
    if source == "sentinel_ndvi":
        return analizar_ndvi(geojson, initial_year or 2020, final_year or 2025, ee_module=ee_module)
    if source == "gedi":
        return analizar_gedi(geojson, ee_module=ee_module)
    if source == "worldcover":
        return analizar_worldcover(geojson, ee_module=ee_module)
    if source == "sinia_2021" and not os.getenv("EE_ASSET_BOSQUE_2021"):
        raise ValueError("SINIA 2021 no está configurado en este proyecto Earth Engine.")
    if source == "firms":
        raise ValueError("FIRMS permanece pendiente de una consulta temporal validada; no se generan focos ficticios.")
    raise ValueError("La fuente solicitada no está configurada para procesamiento.")
