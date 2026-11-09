"""Comprueba que cada control cartográfico real produzca una tesela, sin estadísticas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validar_fase_correctiva_gee import SMALL_AREA
from webapp.models import LayerPreviewRequest
from webapp.service import run_layer_preview


SOURCES = {
    "jrc_tmf": 2025,
    "hansen_gfc": 2025,
    "esri_lulc": 2025,
    "sentinel_ndvi": 2025,
    "gedi": None,
    "1992_historico": None,
    "2000_historico": None,
    "2012_binario": None,
    "2012_detallado": None,
    "2019_general": None,
    "2021_general": None,
    "2021_detallado": None,
    "2023_general": None,
}


def main() -> None:
    results = {}
    requested = sys.argv[1:] or list(SOURCES)
    unknown = [source for source in requested if source not in SOURCES]
    if unknown:
        raise ValueError(f"Fuentes no configuradas: {', '.join(unknown)}")
    for source in requested:
        year = SOURCES[source]
        response = run_layer_preview(LayerPreviewRequest.model_validate({
            "source": source,
            "year": year,
            "area": {"mode": "draw", "geometry": SMALL_AREA},
        }))
        layer = response["layer"]
        results[source] = {
            "tile_ready": bool(layer.get("tile_url")),
            "legend": layer.get("legend"),
            "class_count": len(layer.get("classes") or []),
        }
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
