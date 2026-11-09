"""Ejecuta una comparación temporal pequeña y reproducible contra Earth Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ee

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from analisis_temporal import ejecutar_analisis_temporal_ee  # noqa: E402


def argumentos():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Proyecto habilitado para Earth Engine")
    parser.add_argument("--fuente", choices=("jrc_tmf", "esri_lulc"), default="jrc_tmf")
    parser.add_argument("--inicial", type=int, default=2020)
    parser.add_argument("--final", type=int, default=2025)
    parser.add_argument("--distancia", type=float, default=500)
    parser.add_argument("--area-minima", type=float, default=0.1)
    return parser.parse_args()


def main():
    args = argumentos()
    ee.Initialize(project=args.project)
    # Ventana de validación dentro de la CHCP, suficientemente pequeña para una
    # comprobación reproducible sin sustituir una validación regional completa.
    area = {
        "type": "Polygon",
        "coordinates": [[
            [-79.5700, 9.0300],
            [-79.5500, 9.0300],
            [-79.5500, 9.0500],
            [-79.5700, 9.0500],
            [-79.5700, 9.0300],
        ]],
    }
    resultado = ejecutar_analisis_temporal_ee(
        fuente=args.fuente,
        anio_inicial=args.inicial,
        anio_final=args.final,
        area_geojson=area,
        distancia_maxima_m=args.distancia,
        area_minima_parche_ha=args.area_minima,
        ee_module=ee,
    )
    salida = {
        "area_validacion_geojson": area,
        "fuente": resultado["fuente"],
        "parametros_equivalentes": resultado["parametros_equivalentes"],
        "periodos": {
            str(args.inicial): resultado["periodos"][str(args.inicial)]["resumen"],
            str(args.final): resultado["periodos"][str(args.final)]["resumen"],
        },
        "cambios": resultado["cambios"],
        "transiciones_ha": {
            clave: valor["area_ha"]
            for clave, valor in resultado["transiciones"].items()
        },
        "metadatos": resultado["metadatos"],
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
