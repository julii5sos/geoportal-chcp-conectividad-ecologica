"""Validación representativa y acotada de la fase correctiva en Earth Engine."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ee

from cobertura_oficial_2023 import consultar_cobertura_oficial_2023
from corredores import analizar_interseccion_corredores
from evaluacion_ecologica import ejecutar_evaluacion_ecologica
from estructura_cobertura import analizar_estructura_cobertura
from gee_config import inicializar_earth_engine, resolver_proyecto_gee


SMALL_AREA = {
    "type": "Polygon",
    "coordinates": [[
        [-79.7200, 9.0900], [-79.7100, 9.0900],
        [-79.7100, 9.1000], [-79.7200, 9.1000],
        [-79.7200, 9.0900],
    ]],
}


def main() -> None:
    inicializar_earth_engine(ee)
    corridors = analizar_interseccion_corredores(SMALL_AREA)
    structure_2021 = analizar_estructura_cobertura(
        "official_2021", SMALL_AREA, maximum_distance_m=500,
        minimum_patch_area_ha=0, context_radius_m=500, ee_module=ee,
    )
    evaluation = ejecutar_evaluacion_ecologica(
        SMALL_AREA, contexto_corredores=corridors,
        contexto_fragmentacion=structure_2021, ee_module=ee
    )
    official = consultar_cobertura_oficial_2023(SMALL_AREA, ee_module=ee)
    structure_2023 = analizar_estructura_cobertura(
        "diagnostic_2023", SMALL_AREA, maximum_distance_m=500,
        minimum_patch_area_ha=0, context_radius_m=500, ee_module=ee,
    )
    print(json.dumps({
        "project_id": resolver_proyecto_gee(),
        "evaluation": {
            "priority": evaluation["priority"],
            "score": evaluation["score"],
            "signals": evaluation["signals"],
            "area_ha": round(evaluation["metrics"]["area_ha"], 4),
            "map_count": len(evaluation["maps"]),
            "visit_priority": evaluation["visit_priority"]["prioridad_visita"],
        },
        "structure_2021": {
            "patches": structure_2021["metricas_clase"]["numero_parches"],
            "forest_ha": structure_2021["metricas_clase"]["area_total_bosque_ha"],
            "components": structure_2021["metricas_red"]["numero_componentes"],
            "isolated": structure_2021["metricas_red"]["numero_parches_aislados"],
            "edges": structure_2021["metricas_red"]["numero_aristas"],
        },
        "official_2023": {
            "legend_status": official["legend_status"],
            "codes": [row["code"] for row in official["statistics"]["classes"]],
            "total_classified_ha": official["statistics"]["total_classified_ha"],
        },
        "structure_2023": {
            "patches": structure_2023["metricas_clase"]["numero_parches"],
            "forest_ha": structure_2023["metricas_clase"]["area_total_bosque_ha"],
            "components": structure_2023["metricas_red"]["numero_componentes"],
            "isolated": structure_2023["metricas_red"]["numero_parches_aislados"],
            "edges": structure_2023["metricas_red"]["numero_aristas"],
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
