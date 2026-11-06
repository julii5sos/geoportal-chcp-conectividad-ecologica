"""Ejecuta una sola integración JRC + ESRI sobre un polígono CHCP pequeño."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from territorio_local import geometria_cuenca
from webapp.main import create_app


def main() -> int:
    os.environ.setdefault("GEE_PROJECT_ID", "geoportal-513817")
    basin = shape(geometria_cuenca())
    point = basin.representative_point()
    geometry = box(
        point.x - 0.0025,
        point.y - 0.0025,
        point.x + 0.0025,
        point.y + 0.0025,
    ).intersection(basin)
    response = create_app(testing=True).test_client().post(
        "/api/v1/analyses",
        json={
            "analyses": ["coverage", "fragmentation", "connectivity"],
            "area": {"mode": "draw", "geometry": mapping(geometry)},
            "source": "integrated",
            "initial_year": 2020,
            "final_year": 2025,
            "maximum_distance_m": 500,
            "minimum_patch_area_ha": 0.1,
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"API {response.status_code}: {response.get_json()}")
    data = response.get_json()
    result = data["result"]
    if result.get("mode") != "integrated" or set(result.get("sources", {})) != {"jrc_tmf", "esri_lulc"}:
        raise RuntimeError("La respuesta no conservó ambos resultados independientes.")
    state = result["concordance"]["estado"]
    if state["area_valida_comun_ha"] <= 0:
        raise RuntimeError("La prueba no produjo un área válida común positiva.")
    summary = {
        "project_id": data["project_id"],
        "period": [result["anio_inicial"], result["anio_final"]],
        "area_valida_comun_ha": state["area_valida_comun_ha"],
        "concordancia_pct": state["concordancia_pct"],
        "diferencia_bosque_final_ha": result["concordance"]["diferencia_superficie_forestal_final_ha"],
    }
    print("OK integración real JRC + ESRI")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
