"""Valida una sola comparación 2021–2023 y su PDF sobre un AOI pequeño."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validar_fase_correctiva_gee import SMALL_AREA
from webapp.models import StructuralComparisonRequest
from webapp.service import build_technical_report, run_structural_comparison


def _summary(scenario: dict) -> dict:
    return {
        "forest_ha": scenario["metricas_clase"]["area_total_bosque_ha"],
        "patches": scenario["metricas_clase"]["numero_parches"],
        "components": scenario["metricas_red"]["numero_componentes"],
        "isolated": scenario["metricas_red"]["numero_parches_aislados"],
        "edges": scenario["metricas_red"]["numero_aristas"],
    }


def main() -> None:
    response = run_structural_comparison(StructuralComparisonRequest.model_validate({
        "area": {"mode": "draw", "geometry": SMALL_AREA},
        "maximum_distance_m": 500,
        "minimum_patch_area_ha": 0,
        "territory_id": "validation:small-2021-2023",
    }))
    report = build_technical_report(response["result_id"])
    if not report or not report.startswith(b"%PDF"):
        raise RuntimeError("La comparación no produjo un PDF válido.")
    output = ROOT / "docs" / "capturas" / "validacion_comparacion_estructural_2021_2023.pdf"
    output.write_bytes(report)
    result = response["result"]
    print(json.dumps({
        "result_id": response["result_id"],
        "project_id": response["project_id"],
        "comparison_status": result["comparison_status"],
        "comparable_for_causal_change": result["comparable_for_causal_change"],
        "difference_metrics": result["difference_metrics"],
        "scenario_2021": _summary(result["scenarios"]["2021"]),
        "scenario_2023": _summary(result["scenarios"]["2023"]),
        "pdf": {"path": str(output.relative_to(ROOT)), "bytes": len(report)},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
