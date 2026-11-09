"""Inspección reproducible del asset oficial 2023 sin inferir su esquema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gee_config import inicializar_earth_engine
from territorio_local import geometria_cuenca


ASSET_ID = "projects/geoportal-513817/assets/SINIA_2023_COBERTURA_GENERAL_RASTER10M"


def inspeccionar() -> dict:
    conexion = inicializar_earth_engine(ee)
    metadata = ee.data.getAsset(ASSET_ID)
    asset_type = metadata.get("type")
    result = {
        "project_id": conexion.project_id,
        "authentication_mode": conexion.authentication_mode,
        "asset_id": ASSET_ID,
        "metadata": metadata,
    }
    if asset_type == "TABLE":
        collection = ee.FeatureCollection(ASSET_ID)
        first = ee.Feature(collection.first())
        result["table"] = {
            "feature_count": collection.size().getInfo(),
            "first_properties": first.toDictionary().getInfo(),
            "geometry_type": first.geometry().type().getInfo(),
            "bounds": collection.geometry(1).bounds(1).getInfo(),
        }
    elif asset_type in {"IMAGE", "IMAGE_COLLECTION"}:
        image = (
            ee.Image(ASSET_ID)
            if asset_type == "IMAGE"
            else ee.ImageCollection(ASSET_ID).first()
        )
        result["image"] = {
            "band_names": image.bandNames().getInfo(),
            "projection": image.select(0).projection().getInfo(),
            "properties": image.toDictionary().getInfo(),
            "bounds": image.geometry().bounds(1).getInfo(),
        }
        if asset_type == "IMAGE":
            geometry = ee.Geometry(geometria_cuenca())
            result["image"]["class_histogram_chcp"] = (
                image.select(0)
                .reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=10,
                    maxPixels=1e9,
                    tileScale=8,
                )
                .getInfo()
            )
    return result


if __name__ == "__main__":
    report = inspeccionar()
    image = report.get("image", {})
    summary = {
        "project_id": report["project_id"],
        "authentication_mode": report["authentication_mode"],
        "asset_id": report["asset_id"],
        "type": report["metadata"].get("type"),
        "bands": report["metadata"].get("bands"),
        "properties": image.get("properties"),
        "class_histogram_chcp": image.get("class_histogram_chcp"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
