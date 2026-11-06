"""Cálculo reutilizable del ERI indicativo en Google Earth Engine.

Las fórmulas, fuentes y pesos son los mismos que utiliza ``app_experiencia.py``.
El módulo no depende de Streamlit y permite que la API web mantenga el ERI como
resultado complementario e independiente.
"""

from __future__ import annotations

from typing import Any

from eri_indicativo import CLASES_ERI, PESOS_ERI, construir_resultado_eri


GEDI_ASSET = "users/openforisearthmap/World_EarthMap/CanopyHeight_GEDI_V27"
ANO_ERI_REFERENCIA = 2024
ESCALA_ERI_M = 90
RADIO_CONECTIVIDAD_ERI_M = 1_500
DISTANCIA_RIPARIA_ERI_M = 1_000
ALTURA_REFERENCIA_ERI_M = 35
AREA_DRENAJE_ERI_KM2 = 1.0


def _convertir_altura_gedi_float(imagen, ee):
    return ee.Image(imagen).toFloat()


def imagen_gedi(geometria, ee):
    coleccion = (
        ee.ImageCollection(GEDI_ASSET)
        .filterBounds(geometria)
        .select([0], ["altura_dosel"])
        .map(lambda imagen: _convertir_altura_gedi_float(imagen, ee))
    )
    respaldo = (
        ee.Image.constant(0)
        .rename("altura_dosel")
        .updateMask(ee.Image(0))
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 100)
    )
    return (
        coleccion.merge(ee.ImageCollection.fromImages([respaldo]))
        .mosaic()
        .setDefaultProjection("EPSG:4326", None, 100)
        .rename("altura_dosel")
        .clip(geometria)
    )


def _convertir_probabilidad_arboles_float(imagen, ee):
    return ee.Image(imagen).select(["trees"], ["p_arboles"]).toFloat()


def obtener_probabilidad_arboles(anio: int, geometria, ee):
    coleccion = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(geometria)
        .filterDate(f"{anio}-01-01", f"{anio + 1}-01-01")
        .map(lambda imagen: _convertir_probabilidad_arboles_float(imagen, ee))
    )
    respaldo = (
        ee.Image.constant(0)
        .rename("p_arboles")
        .updateMask(ee.Image(0))
        .toFloat()
        .setDefaultProjection("EPSG:4326", None, 10)
    )
    return (
        coleccion.merge(ee.ImageCollection.fromImages([respaldo]))
        .mean()
        .setDefaultProjection("EPSG:4326", None, 10)
        .rename("p_arboles")
        .clip(geometria)
    )


def construir_imagenes_eri(geometria, ee):
    p_arboles = obtener_probabilidad_arboles(
        ANO_ERI_REFERENCIA, geometria, ee
    ).unmask(0).clamp(0, 1)
    altura_normalizada = (
        imagen_gedi(geometria, ee)
        .divide(ALTURA_REFERENCIA_ERI_M)
        .clamp(0, 1)
        .unmask(p_arboles)
    )
    integridad = (
        altura_normalizada.multiply(0.5)
        .add(p_arboles.multiply(0.5))
        .rename("integridad_estructural")
    )

    proyeccion_eri = ee.Projection("EPSG:4326").atScale(ESCALA_ERI_M)
    bosque = p_arboles.gte(0.5).toFloat().setDefaultProjection("EPSG:4326", None, 10)
    bosque_eri = bosque.reduceResolution(
        reducer=ee.Reducer.mean(), bestEffort=True, maxPixels=1024
    ).reproject(crs=proyeccion_eri)
    conectividad = (
        bosque_eri.focalMean(
            radius=RADIO_CONECTIVIDAD_ERI_M,
            kernelType="circle",
            units="meters",
        )
        .clamp(0, 1)
        .rename("conectividad")
    )

    dem_coleccion = (
        ee.ImageCollection("COPERNICUS/DEM/GLO30")
        .filterBounds(geometria)
        .select("DEM")
    )
    dem = (
        dem_coleccion.mosaic()
        .setDefaultProjection(ee.Image(dem_coleccion.first()).projection())
        .clip(geometria)
    )
    pendiente = ee.Terrain.slope(dem).divide(45).clamp(0, 1)
    estabilidad = (
        ee.Image(1)
        .subtract(pendiente.multiply(ee.Image(1).subtract(p_arboles)))
        .clamp(0, 1)
        .rename("estabilidad_topografica")
    )

    acumulacion = ee.Image("MERIT/Hydro/v1_0_1").select("upa")
    proyeccion_merit = acumulacion.projection()
    cauces = (
        acumulacion.gte(AREA_DRENAJE_ERI_KM2)
        .unmask(0)
        .setDefaultProjection(proyeccion_merit)
    )
    distancia_cauce_m = (
        cauces.fastDistanceTransform(256, "pixels", "squared_euclidean")
        .sqrt()
        .multiply(proyeccion_merit.nominalScale())
    )
    proximidad_riparia = (
        ee.Image(1)
        .subtract(distancia_cauce_m.divide(DISTANCIA_RIPARIA_ERI_M).clamp(0, 1))
        .rename("proximidad_riparia")
        .clip(geometria)
    )

    componentes = {
        "integridad_estructural": integridad.clip(geometria),
        "conectividad": conectividad.clip(geometria),
        "estabilidad_topografica": estabilidad.clip(geometria),
        "proximidad_riparia": proximidad_riparia,
    }
    eri = ee.Image(0)
    for clave, peso in PESOS_ERI.items():
        eri = eri.add(componentes[clave].multiply(peso))
    return eri.clamp(0, 1).rename("eri").clip(geometria), componentes


def clasificar_imagen_eri(eri, ee):
    clases = ee.Image(1)
    for indice, clase in enumerate(CLASES_ERI[1:], start=2):
        clases = clases.where(ee.Image(eri).gte(clase["minimo"]), indice)
    return clases.updateMask(ee.Image(eri).mask()).rename("eri_clase").toByte()


def calcular_eri_geojson(area_geojson: dict[str, Any], *, ee_module) -> dict[str, Any]:
    ee = ee_module
    geometria = ee.Geometry(area_geojson)
    eri, componentes = construir_imagenes_eri(geometria, ee)
    imagen_medias = ee.Image.cat(
        [componentes[clave].rename(clave) for clave in PESOS_ERI]
        + [eri.rename("eri")]
    )
    medias = ee.Dictionary(
        imagen_medias.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometria,
            scale=ESCALA_ERI_M,
            bestEffort=True,
            maxPixels=1e9,
            tileScale=4,
        )
    )
    clases = clasificar_imagen_eri(eri, ee)
    pixel_ha = ee.Image.pixelArea().divide(10_000)
    bandas = [
        clases.eq(indice)
        .unmask(0)
        .multiply(pixel_ha)
        .rename(f"eri_{clase['clave']}_ha")
        for indice, clase in enumerate(CLASES_ERI, start=1)
    ]
    areas = ee.Dictionary(
        ee.Image.cat(bandas).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometria,
            scale=ESCALA_ERI_M,
            bestEffort=True,
            maxPixels=1e9,
            tileScale=4,
        )
    )
    resumen = medias.combine(areas, True).getInfo()
    resultado = construir_resultado_eri(resumen)
    map_id = clasificar_imagen_eri(eri, ee).getMapId(
        {
            "min": 1,
            "max": len(CLASES_ERI),
            "palette": [item["color"].lstrip("#") for item in CLASES_ERI],
        }
    )
    resultado.update(
        {
            "anio_referencia": ANO_ERI_REFERENCIA,
            "escala_resumen_m": ESCALA_ERI_M,
            "radio_conectividad_m": RADIO_CONECTIVIDAD_ERI_M,
            "distancia_riparia_m": DISTANCIA_RIPARIA_ERI_M,
            "fuentes": [
                "Dynamic World",
                "GEDI / OpenForis",
                "Copernicus DEM GLO-30",
                "MERIT Hydro",
            ],
            "tile_url": map_id["tile_fetcher"].url_format,
            "nota_conectividad": (
                "La conectividad usa la proporción local de bosque en una ventana de "
                "1.5 km como proxy espacial ligero; no representa conectividad funcional."
            ),
        }
    )
    return resultado

