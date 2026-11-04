"""Geometrías territoriales locales incluidas con la aplicación.

La cuenca y las subcuencas provienen del portal HTML de referencia. Se cargan
desde GeoJSON para que la selección territorial no dependa de assets privados
de Google Earth Engine. Earth Engine sigue procesando las imágenes; recibe la
geometría elegida directamente desde estos archivos locales.
"""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path


DIRECTORIO_TERRITORIO = Path(__file__).with_name("data") / "territorio"
ARCHIVO_AREA_ESTUDIO = DIRECTORIO_TERRITORIO / "area_estudio.geojson"
ARCHIVO_SUBCUENCAS = DIRECTORIO_TERRITORIO / "subcuencas_canal.geojson"

FUENTE_CUENCA = "GeoJSON local · portal Conectividad Panamá"
FUENTE_SUBCUENCAS = "GeoJSON local · Subcuencas del Canal de Panamá"

_CORRECCIONES_NOMBRES = {
    "Gat�n": "Gatún",
    "R�o": "Río",
    "Cara�a": "Caraña",
    "Ca�ito": "Cañito",
    "Ca�o": "Caño",
    "Cir�": "Cirí",
    "Lim�n": "Limón",
    "Pel�n": "Pelón",
    "Pequen�": "Pequení",
}


def normalizar_nombre(nombre: str) -> str:
    """Repara caracteres sustituidos en los atributos de la fuente entregada."""

    resultado = str(nombre or "").strip()
    for original, correccion in _CORRECCIONES_NOMBRES.items():
        resultado = resultado.replace(original, correccion)
    return resultado


@lru_cache(maxsize=2)
def _leer_geojson(ruta: str) -> dict:
    with Path(ruta).open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _copia_geojson(ruta: Path) -> dict:
    return copy.deepcopy(_leer_geojson(str(ruta)))


@lru_cache(maxsize=1)
def geometria_cuenca() -> dict:
    """Devuelve únicamente la cuenca, sin la franja externa de 10 km."""

    coleccion = _leer_geojson(str(ARCHIVO_AREA_ESTUDIO))
    for feature in coleccion.get("features", []):
        if feature.get("properties", {}).get("tipo") == "cuenca":
            return copy.deepcopy(feature["geometry"])
    raise ValueError("El archivo territorial no contiene la geometría de la cuenca.")


def coleccion_cuenca() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "nombre": "Cuenca del Canal de Panamá",
                    "tipo": "cuenca",
                    "fuente": FUENTE_CUENCA,
                },
                "geometry": geometria_cuenca(),
            }
        ],
    }


@lru_cache(maxsize=1)
def _subcuencas_normalizadas() -> tuple[dict, ...]:
    coleccion = _leer_geojson(str(ARCHIVO_SUBCUENCAS))
    features = []
    for feature in coleccion.get("features", []):
        copia = copy.deepcopy(feature)
        propiedades = copia.setdefault("properties", {})
        propiedades["nombre"] = normalizar_nombre(propiedades.get("nombre", ""))
        propiedades["grupo"] = normalizar_nombre(propiedades.get("grupo", ""))
        propiedades["fuente"] = FUENTE_SUBCUENCAS
        features.append(copia)
    return tuple(features)


def coleccion_subcuencas() -> dict:
    return {
        "type": "FeatureCollection",
        "features": copy.deepcopy(list(_subcuencas_normalizadas())),
    }


@lru_cache(maxsize=1)
def nombres_subcuencas() -> tuple[str, ...]:
    return tuple(
        feature["properties"]["nombre"] for feature in _subcuencas_normalizadas()
    )


def feature_subcuenca(nombre: str) -> dict:
    nombre_buscado = normalizar_nombre(nombre)
    for feature in _subcuencas_normalizadas():
        if feature["properties"]["nombre"] == nombre_buscado:
            return copy.deepcopy(feature)
    raise KeyError(f"No se encontró la subcuenca local: {nombre_buscado}")


def geometria_subcuenca(nombre: str) -> dict:
    return feature_subcuenca(nombre)["geometry"]


@lru_cache(maxsize=1)
def huella_territorial() -> str:
    digest = hashlib.sha256()
    for ruta in (ARCHIVO_AREA_ESTUDIO, ARCHIVO_SUBCUENCAS):
        digest.update(ruta.read_bytes())
    return digest.hexdigest()[:12]
