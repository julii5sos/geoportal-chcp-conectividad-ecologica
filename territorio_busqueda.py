"""Búsqueda tolerante y resumen local verificable de territorios CHCP."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

from corredores import (
    FUENTE_CORTA,
    analizar_interseccion_corredores,
    cargar_catalogo,
    cargar_corredores,
    cargar_puntos_criticos,
)
from territorio_local import coleccion_subcuencas, geometria_cuenca


def normalizar_busqueda(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def _slug(value: str) -> str:
    return normalizar_busqueda(value).replace(" ", "-")


@lru_cache(maxsize=1)
def catalogo_territorial() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = [
        {
            "id": "cuenca:chcp",
            "tipo": "cuenca",
            "nombre": "Cuenca Hidrográfica del Canal de Panamá",
            "grupo": "CHCP",
            "aliases": ["CHCP", "Cuenca del Canal de Panamá"],
            "geometry": geometria_cuenca(),
        }
    ]
    seen = set()
    for feature in coleccion_subcuencas()["features"]:
        props = feature.get("properties", {})
        name = str(props.get("nombre") or "").strip()
        identifier = f"subcuenca:{_slug(name)}"
        if not name or identifier in seen:
            raise ValueError("El catálogo territorial contiene nombres vacíos o duplicados.")
        seen.add(identifier)
        rows.append(
            {
                "id": identifier,
                "tipo": "subcuenca",
                "nombre": name,
                "grupo": str(props.get("grupo") or "Subcuencas CHCP"),
                "aliases": [],
                "geometry": feature["geometry"],
            }
        )
    for index, feature in enumerate(cargar_corredores().get("features", []), start=1):
        props = feature.get("properties", {})
        name = str(props.get("nombre") or f"Corredor {index}").strip()
        identifier = f"corredor:{index:02d}-{_slug(name)}"
        if identifier in seen:
            raise ValueError("El catálogo contiene corredores duplicados.")
        seen.add(identifier)
        rows.append(
            {
                "id": identifier,
                "tipo": "corredor",
                "nombre": name,
                "grupo": "Corredores publicados · Almanaque Azul",
                "aliases": [str(props.get("categoria_etiqueta") or "")],
                "geometry": feature["geometry"],
                "properties": props,
            }
        )
    return tuple(rows)


def buscar_territorios(query: str, *, limit: int = 12) -> list[dict[str, Any]]:
    normalized = normalizar_busqueda(query)
    if not normalized:
        return []
    terms = normalized.split()
    matches = []
    for row in catalogo_territorial():
        searchable = normalizar_busqueda(" ".join([row["nombre"], row["grupo"], *row["aliases"]]))
        if not all(term in searchable for term in terms):
            continue
        name = normalizar_busqueda(row["nombre"])
        score = 0 if name == normalized else 1 if name.startswith(normalized) else 2
        matches.append((score, name, row))
    return [
        {key: row[key] for key in ("id", "tipo", "nombre", "grupo")}
        for _, _, row in sorted(matches, key=lambda item: (item[0], item[1]))[: max(1, min(limit, 25))]
    ]


def obtener_territorio(identifier: str) -> dict[str, Any]:
    for row in catalogo_territorial():
        if row["id"] == identifier:
            return row
    raise KeyError("El territorio solicitado no existe en el catálogo local.")


def _area_ha(geometry: dict[str, Any]) -> float:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:8857", always_xy=True)
    return float(transform(transformer.transform, shape(geometry)).area / 10_000)


def resumen_territorial(identifier: str) -> dict[str, Any]:
    row = obtener_territorio(identifier)
    geometry = shape(row["geometry"])
    corridor_analysis = analizar_interseccion_corredores(row["geometry"])
    corridors = [item["nombre"] for item in corridor_analysis["corredores"]]
    critical = 0
    for feature in cargar_puntos_criticos().get("features", []):
        if geometry.covers(shape(feature["geometry"])):
            critical += 1
    area_ha = _area_ha(row["geometry"])
    return {
        "territory": {key: row[key] for key in ("id", "tipo", "nombre", "grupo")},
        "geometry": row["geometry"],
        "area_ha": round(area_ha, 4),
        "area_km2": round(area_ha / 100, 4),
        "corridors": {"count": len(corridors), "names": sorted(set(str(item) for item in corridors))},
        "corridor_analysis": corridor_analysis,
        "critical_points": critical,
        "scientific_indicators": {
            "status": "not_calculated",
            "message": "No calculado. Ejecute un análisis para obtener cobertura, fragmentación y conectividad.",
        },
        "metadata": {
            "source": "GeoJSON local del Geoportal CHCP",
            "crs": "EPSG:4326",
            "area_method": "Proyección equivalente para calcular superficies sin usar grados",
            "area_crs": "EPSG:8857",
            "corridor_source": FUENTE_CORTA,
            "corridor_catalog": cargar_catalogo(),
        },
    }

