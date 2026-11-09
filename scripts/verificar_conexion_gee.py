"""Verificación mínima, sin escribir secretos ni modificar permisos de GEE."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import ee

from analisis_temporal import calcular_estadisticas_cobertura_ee
from gee_config import inicializar_earth_engine


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Comprueba SRTM y, opcionalmente, una comparación JRC pequeña."
    )
    parser.add_argument("--project", default="geoportal-513817")
    parser.add_argument("--jrc", action="store_true")
    args = parser.parse_args()

    entorno = dict(os.environ)
    entorno["GEE_PROJECT_ID"] = args.project
    conexion = inicializar_earth_engine(ee, environ=entorno)
    bandas = ee.Image("USGS/SRTMGL1_003").bandNames().getInfo()
    if "elevation" not in bandas:
        raise RuntimeError("SRTM no devolvió la banda elevation.")
    print(f"OK proyecto={conexion.project_id} autenticacion={conexion.authentication_mode}")
    print("OK USGS/SRTMGL1_003 bandas=elevation")

    if args.jrc:
        area = {
            "type": "Polygon",
            "coordinates": [[
                [-79.57, 9.03],
                [-79.55, 9.03],
                [-79.55, 9.05],
                [-79.57, 9.05],
                [-79.57, 9.03],
            ]],
        }
        estadisticas = calcular_estadisticas_cobertura_ee(
            fuente="jrc_tmf",
            anio_inicial=2020,
            anio_final=2025,
            area_geojson=area,
            ee_module=ee,
        )
        comparacion = estadisticas["comparacion"]
        if not comparacion["transiciones_consistentes"]:
            raise RuntimeError("Las transiciones JRC no cierran en la máscara común.")
        print(
            "OK JRC 2020-2025 "
            f"area_comun_ha={comparacion['area_valida_comun_ha']:.4f} "
            f"diferencia_cierre_ha={comparacion['diferencia_cierre_ha']:+.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

