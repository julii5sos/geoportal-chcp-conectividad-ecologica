"""Inspección reproducible de assets oficiales sin recodificar clases.

Use ``--catalogo --solo-metadatos`` para la verificación liviana de acceso y
tipo. La inspección espacial detallada permanece disponible de forma explícita.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ee

from gee_config import inicializar_earth_engine, resolver_proyecto_gee
from catalogo_assets_sinia import catalogo_assets_sinia
from territorio_local import geometria_cuenca


ASSETS = {
    "referencia_2021": "projects/geoportal-513817/assets/SINIA_2021_COBERTURA_GENERAL_VECTOR",
    "diagnostico_2023": "projects/geoportal-513817/assets/SINIA_2023_COBERTURA_GENERAL_RASTER10M",
}


def inspect_asset(asset_id: str) -> dict:
    metadata = ee.data.getAsset(asset_id)
    result = {"asset_id": asset_id, "metadata": metadata}
    asset_type = metadata.get("type")
    basin = ee.Geometry(geometria_cuenca())
    if asset_type == "TABLE":
        collection = ee.FeatureCollection(asset_id)
        first = ee.Feature(collection.first())
        properties = first.propertyNames()
        result["table"] = {
            "feature_count": collection.size().getInfo(),
            "first_properties": first.toDictionary().getInfo(),
            "property_names": properties.getInfo(),
            "geometry_type": first.geometry().type().getInfo(),
            "bounds": collection.geometry(1).bounds(1).getInfo(),
            "intersecting_chcp_count": collection.filterBounds(basin).size().getInfo(),
        }
        for candidate in ("Categoria", "categoria", "CLASS_NAME", "class", "Clase"):
            if candidate in result["table"]["property_names"]:
                result["table"][f"histogram_{candidate}"] = (
                    collection.aggregate_histogram(candidate).getInfo()
                )
    elif asset_type == "IMAGE":
        image = ee.Image(asset_id)
        projection = image.select(0).projection()
        result["image"] = {
            "band_names": image.bandNames().getInfo(),
            "projection": projection.getInfo(),
            "properties": image.toDictionary().getInfo(),
            "bounds": image.geometry().bounds(1).getInfo(),
            "histogram_chcp": image.select(0).reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(), geometry=basin,
                scale=projection.nominalScale(), maxPixels=1e9, tileScale=8,
            ).getInfo(),
            "valid_area_chcp_ha": ee.Image.pixelArea().divide(10_000)
                .updateMask(image.select(0).mask())
                .rename("valid_ha")
                .reduceRegion(
                    reducer=ee.Reducer.sum(), geometry=basin,
                    scale=projection.nominalScale(), maxPixels=1e9, tileScale=8,
                ).get("valid_ha").getInfo(),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogo", action="store_true", help="Inspeccionar los ocho assets registrados.")
    parser.add_argument("--solo-metadatos", action="store_true", help="No ejecutar estadísticas espaciales.")
    args = parser.parse_args()
    inicializar_earth_engine(ee)
    assets = (
        {item["clave"]: item["asset_id"] for item in catalogo_assets_sinia()}
        if args.catalogo else ASSETS
    )
    if args.solo_metadatos:
        inspected = {
            key: {
                "asset_id": asset_id,
                "type": (metadata := ee.data.getAsset(asset_id)).get("type"),
                "name": metadata.get("name"),
                "updateTime": metadata.get("updateTime"),
            }
            for key, asset_id in assets.items()
        }
    else:
        inspected = {key: inspect_asset(asset_id) for key, asset_id in assets.items()}
    report = {
        "project_id": resolver_proyecto_gee(),
        "assets": inspected,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
