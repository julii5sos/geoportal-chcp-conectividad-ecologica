"""Consulta segura de la cartografía oficial 2023 aún sin leyenda verificada."""

from __future__ import annotations

from typing import Any

from catalogo_assets_sinia import ASSETS_SINIA


ASSET_COBERTURA_2023 = str(ASSETS_SINIA["2023_general"]["asset_id"])
CLASSES = {
    1: {"label": "Bosques y otras tierras boscosas", "color": "#237A4B"},
    2: {"label": "Otras tierras", "color": "#D8C49C"},
    3: {"label": "Superficie de agua", "color": "#388FC4"},
}


def consultar_cobertura_oficial_2023(
    area_geojson: dict[str, Any], *, ee_module
) -> dict[str, Any]:
    geometry = ee_module.Geometry(area_geojson, proj="EPSG:4326", geodesic=False)
    image = ee_module.Image(ASSET_COBERTURA_2023).select([0], ["codigo"]).clip(geometry)
    classified = image.remap(list(CLASSES), [1, 1, 1], 0).eq(1).updateMask(image.mask())
    grouped = (
        ee_module.Image.pixelArea().divide(10_000).rename("ha")
        .addBands(image)
        .reduceRegion(
            reducer=ee_module.Reducer.sum().group(groupField=1, groupName="codigo"),
            geometry=geometry, scale=10, crs="EPSG:32617", bestEffort=True,
            maxPixels=1e9, tileScale=4,
        )
        .get("groups")
        .getInfo()
    ) or []
    rows = []
    total = sum(float(item.get("sum") or 0) for item in grouped)
    area_aoi = float(geometry.area(1).divide(10_000).getInfo() or 0)
    valid = float(
        ee_module.Image.pixelArea().divide(10_000).updateMask(classified)
        .rename("valid_ha").reduceRegion(
            reducer=ee_module.Reducer.sum(), geometry=geometry, scale=10,
            crs="EPSG:32617", maxPixels=1e9, tileScale=4,
        ).get("valid_ha").getInfo() or 0
    )
    for item in sorted(grouped, key=lambda value: int(value.get("codigo", 0))):
        code = int(item.get("codigo", 0))
        hectares = float(item.get("sum") or 0)
        definition = CLASSES.get(code)
        rows.append({
            "code": code,
            "label": definition["label"] if definition else f"Código {code} · no descrito",
            "legend_verified": definition is not None,
            "area_ha": round(hectares, 4),
            "percentage": round(hectares / total * 100, 4) if total else 0.0,
        })
    codes = [row["code"] for row in rows]
    colors = [CLASSES.get(code, {"color": "#777777"})["color"].lstrip("#") for code in codes]
    # ``remap`` produce una imagen categórica derivada y conserva vecino más cercano;
    # no se usa interpolación bilineal/cúbica ni el pyramiding MEAN del asset fuente.
    display = image.remap(codes, list(range(1, len(codes) + 1)), 0).toByte().selfMask()
    map_id = display.getMapId({"min": 1, "max": max(1, len(codes)), "palette": colors})
    return {
        "mode": "official_coverage_2023",
        "source": "Cartografía de uso y cobertura 2023",
        "asset": ASSET_COBERTURA_2023,
        "year": 2023,
        "native_grid": {"crs": "EPSG:32617", "pixel_size_m": 10},
        "statistics": {
            "aoi_area_ha": round(area_aoi, 4),
            "valid_area_ha": round(valid, 4),
            "unclassified_or_nodata_ha": round(max(0.0, area_aoi - valid), 4),
            "valid_coverage_pct": round(valid / area_aoi * 100, 4) if area_aoi else 0.0,
            "total_classified_ha": round(total, 4),
            "percentage_denominator": "área válida clasificada (códigos 1, 2 y 3)",
            "classes": rows,
        },
        "map": {
            "tile_url": map_id["tile_fetcher"].url_format,
            "classes": [
                {"value": row["code"], "label": row["label"], "color": f"#{color}"}
                for row, color in zip(rows, colors)
            ],
        },
        "legend_status": "user_supplied_verified_against_codes" if rows and all(row["legend_verified"] for row in rows) else "contains_undocumented_codes",
        "forest_class_available": any(row["code"] == 1 for row in rows),
        "allowed_uses": ["visualización por código", "superficie por código dentro del área"],
        "prohibited_interpretations": [
            "La clase 1 agrupa bosques y otras tierras boscosas; no distingue bosque natural, maduro, secundario ni manglar.",
            "La conectividad derivada de clase 1 es un escenario diagnóstico independiente, no conectividad funcional.",
            "El sufijo 25K del asset no implica una resolución de 25 m; la cuadrícula observada es de 10 m.",
        ],
    }
