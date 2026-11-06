"""Ejecuta una única integración real JRC a través de la API web."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp.main import create_app
from territorio_local import geometria_cuenca


def main() -> int:
    os.environ.setdefault("GEE_PROJECT_ID", "geoportal-513817")
    cuenca = shape(geometria_cuenca())
    punto = cuenca.representative_point()
    area_pequena = box(
        punto.x - 0.006,
        punto.y - 0.006,
        punto.x + 0.006,
        punto.y + 0.006,
    ).intersection(cuenca)
    payload = {
        "analyses": ["coverage", "fragmentation", "connectivity"],
        "area": {
            "mode": "draw",
            "geometry": mapping(area_pequena),
        },
        "source": "jrc_tmf",
        "initial_year": 2020,
        "final_year": 2025,
        "maximum_distance_m": 500,
        "minimum_patch_area_ha": 0.1,
    }
    response = create_app(testing=True).test_client().post(
        "/api/v1/analyses", json=payload
    )
    if response.status_code != 200:
        raise RuntimeError(f"API {response.status_code}: {response.get_json()}")
    data = response.get_json()
    comparison = data["result"]["estadisticas_cobertura"]["comparacion"]
    if not comparison["transiciones_consistentes"]:
        raise RuntimeError("Las transiciones no cerraron en la máscara común.")
    print(
        "OK API web JRC 2020-2025 "
        f"project={data['project_id']} "
        f"area_comun_ha={comparison['area_valida_comun_ha']:.4f} "
        f"cierre_ha={comparison['diferencia_cierre_ha']:+.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

