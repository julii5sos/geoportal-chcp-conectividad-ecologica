"""Motor científico para comparar cobertura, fragmentación y conectividad.

El módulo mantiene separadas las definiciones de bosque de JRC TMF y ESRI LULC.
No depende de Streamlit y puede validarse con geometrías sintéticas sin credenciales
de Earth Engine. La integración con Earth Engine se limita a recuperar una máscara
bosque/no bosque por año y vectorizarla a la resolución nativa de cada producto.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from bosque_conectividad import analizar_fragmentacion_geojson


TMF_ASSET = "projects/JRC/TMF/v1_2025/AnnualChanges"
ESRI_ASSET = (
    "projects/sat-io/open-datasets/landcover/"
    "ESRI_Global-LULC_10m_TS"
)
CRS_METRICAS = "EPSG:8857"


@dataclass(frozen=True)
class FuenteTemporal:
    clave: str
    nombre: str
    asset_id: str
    anio_inicial: int
    anio_final: int
    resolucion_m: int
    clases_bosque: tuple[int, ...]
    definicion_bosque: str
    version: str
    prioridad: str
    limitacion: str

    @property
    def anios(self) -> tuple[int, ...]:
        return tuple(range(self.anio_inicial, self.anio_final + 1))


FUENTES_TEMPORALES: dict[str, FuenteTemporal] = {
    "jrc_tmf": FuenteTemporal(
        clave="jrc_tmf",
        nombre="JRC Tropical Moist Forest",
        asset_id=TMF_ASSET,
        anio_inicial=1990,
        anio_final=2025,
        resolucion_m=30,
        clases_bosque=(1, 2, 4),
        definicion_bosque=(
            "Bosque húmedo tropical no perturbado (1), degradado (2) o en "
            "regeneración forestal posterior a deforestación (4)."
        ),
        version="JRC TMF v1_2025",
        prioridad="Fuente principal",
        limitacion=(
            "Representa el dominio de bosque húmedo tropical de JRC. No equivale a "
            "una clasificación general de todos los árboles o usos del suelo."
        ),
    ),
    "esri_lulc": FuenteTemporal(
        clave="esri_lulc",
        nombre="ESRI Global Land Use / Land Cover",
        asset_id=ESRI_ASSET,
        anio_inicial=2017,
        anio_final=2025,
        resolucion_m=10,
        clases_bosque=(2,),
        definicion_bosque=(
            "Píxeles clasificados como Trees (clase 2) en cada edición anual."
        ),
        version="ESRI 10 m Annual Land Cover 2017–2025",
        prioridad="Alternativa independiente",
        limitacion=(
            "La clase Trees incluye cobertura arbórea según ESRI y no reproduce la "
            "definición de bosque húmedo tropical de JRC. Sus resultados no se mezclan "
            "ni se restan con JRC."
        ),
    ),
}


def obtener_fuente_temporal(clave: str) -> FuenteTemporal:
    try:
        return FUENTES_TEMPORALES[clave]
    except KeyError as exc:
        raise ValueError(f"Fuente temporal no admitida: {clave}") from exc


def validar_solicitud_temporal(
    fuente: str,
    anio_inicial: int,
    anio_final: int,
    distancia_maxima_m: float,
    area_minima_parche_ha: float,
) -> FuenteTemporal:
    especificacion = obtener_fuente_temporal(fuente)
    if anio_inicial >= anio_final:
        raise ValueError("El año inicial debe ser anterior al año final.")
    if anio_inicial not in especificacion.anios or anio_final not in especificacion.anios:
        raise ValueError(
            f"{especificacion.nombre} solo admite años entre "
            f"{especificacion.anio_inicial} y {especificacion.anio_final}."
        )
    if float(distancia_maxima_m) <= 0:
        raise ValueError("La distancia máxima entre parches debe ser mayor que cero.")
    if float(area_minima_parche_ha) < 0:
        raise ValueError("El área mínima de parche no puede ser negativa.")
    return especificacion


def _ee(ee_module=None):
    if ee_module is not None:
        return ee_module
    import ee  # Importación diferida: las pruebas sintéticas no requieren EE.

    return ee


def construir_cobertura_bosque_ee(
    fuente: str,
    anio: int,
    geometria,
    *,
    ee_module=None,
):
    """Devuelve una máscara binaria bosque/no bosque a resolución nativa.

    La función no sustituye años inexistentes. JRC y ESRI se procesan con reglas
    diferentes y sus productos deben analizarse por separado.
    """

    especificacion = obtener_fuente_temporal(fuente)
    if int(anio) not in especificacion.anios:
        raise ValueError(
            f"{especificacion.nombre} no dispone de cobertura comparable para {anio}."
        )
    ee = _ee(ee_module)
    geometria = ee.Geometry(geometria)

    if fuente == "jrc_tmf":
        banda = f"Dec{anio}"
        coleccion = (
            ee.ImageCollection(especificacion.asset_id)
            .filterBounds(geometria)
            .select([banda], ["estado"])
        )
        referencia = ee.Image(coleccion.first()).select("estado")
        estado = (
            coleccion.mosaic()
            .setDefaultProjection(referencia.projection())
            .rename("estado")
            .clip(geometria)
        )
        bosque = estado.eq(1).Or(estado.eq(2)).Or(estado.eq(4))
    elif fuente == "esri_lulc":
        coleccion = (
            ee.ImageCollection(especificacion.asset_id)
            .filterDate(f"{anio}-01-01", f"{anio}-12-31")
            .filterBounds(geometria)
            .select([0], ["clase"])
        )
        referencia = ee.Image(coleccion.first()).select("clase")
        estado = (
            coleccion.mosaic()
            .setDefaultProjection(referencia.projection())
            .rename("clase")
            .clip(geometria)
        )
        bosque = estado.eq(2)
    else:  # La validación anterior hace explícito cualquier alta futura incompleta.
        raise ValueError(f"No existe una regla bosque/no bosque para {fuente}.")

    return (
        bosque.rename(f"bosque_{anio}")
        .toByte()
        .updateMask(bosque)
        .set(
            {
                "fuente": especificacion.nombre,
                "fuente_clave": fuente,
                "anio": int(anio),
                "resolucion_m": especificacion.resolucion_m,
                "definicion_bosque": especificacion.definicion_bosque,
            }
        )
    )


def vectorizar_cobertura_ee(
    mascara_bosque,
    geometria,
    *,
    escala_m: int,
    area_minima_parche_ha: float = 0.0,
    ee_module=None,
) -> dict[str, Any]:
    """Vectoriza componentes de bosque sin usar ``bestEffort``.

    Mantener la escala fija es indispensable para que ambos años sean comparables.
    La simplificación cartográfica usa media celda y ocurre después de calcular el
    área de cada componente.
    """

    ee = _ee(ee_module)
    geometria = ee.Geometry(geometria)
    vectores = ee.Image(mascara_bosque).rename("bosque").reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=geometria,
        scale=int(escala_m),
        geometryType="polygon",
        eightConnected=True,
        labelProperty="bosque",
        maxPixels=1e9,
        tileScale=4,
        bestEffort=False,
    )

    tolerancia = max(1.0, float(escala_m) / 2.0)

    def preparar(feature):
        feature = ee.Feature(feature)
        area_ha = feature.geometry().area(1).divide(10_000)
        geometria_simplificada = feature.geometry().simplify(tolerancia)
        return feature.setGeometry(geometria_simplificada).set("area_ha", area_ha)

    vectores = vectores.map(preparar)
    if float(area_minima_parche_ha) > 0:
        vectores = vectores.filter(
            ee.Filter.gte("area_ha", float(area_minima_parche_ha))
        )
    return vectores.getInfo()


def recuperar_cobertura_geojson_ee(
    fuente: str,
    anio: int,
    area_geojson: dict[str, Any],
    *,
    area_minima_parche_ha: float = 0.0,
    ee_module=None,
) -> dict[str, Any]:
    especificacion = obtener_fuente_temporal(fuente)
    ee = _ee(ee_module)
    geometria = ee.Geometry(area_geojson)
    mascara = construir_cobertura_bosque_ee(
        fuente, anio, geometria, ee_module=ee
    )
    return vectorizar_cobertura_ee(
        mascara,
        geometria,
        escala_m=especificacion.resolucion_m,
        area_minima_parche_ha=area_minima_parche_ha,
        ee_module=ee,
    )


def _geometrias_geojson(contenido: dict[str, Any]) -> list[dict[str, Any]]:
    tipo = contenido.get("type")
    if tipo == "FeatureCollection":
        return [
            feature["geometry"]
            for feature in contenido.get("features", [])
            if feature.get("geometry")
        ]
    if tipo == "Feature":
        return [contenido["geometry"]] if contenido.get("geometry") else []
    if tipo in {"Polygon", "MultiPolygon", "GeometryCollection"}:
        return [contenido]
    raise ValueError("El contenido no incluye una geometría GeoJSON compatible.")


def normalizar_area_geojson(contenido: dict[str, Any]) -> dict[str, Any]:
    """Convierte FeatureCollection, Feature o geometría en una geometría poligonal."""

    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    from shapely.validation import make_valid

    geometria = unary_union(
        [make_valid(shape(item)) for item in _geometrias_geojson(contenido)]
    )
    if geometria.is_empty or geometria.area <= 0:
        raise ValueError("El área de análisis está vacía.")
    return mapping(make_valid(geometria))


def recortar_area_a_cuenca(
    area_geojson: dict[str, Any], cuenca_geojson: dict[str, Any]
) -> dict[str, Any]:
    """Recorta un dibujo a la CHCP y rechaza intersecciones vacías."""

    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    from shapely.validation import make_valid

    area = make_valid(shape(normalizar_area_geojson(area_geojson)))
    cuenca = make_valid(shape(normalizar_area_geojson(cuenca_geojson)))
    recorte = make_valid(area.intersection(cuenca))
    if recorte.is_empty or recorte.area <= 0:
        raise ValueError("El polígono no intersecta la Cuenca del Canal de Panamá.")
    return mapping(recorte)


def _union_proyectada(
    contenido: dict[str, Any], transformar
):
    from shapely.geometry import shape
    from shapely.ops import transform, unary_union
    from shapely.validation import make_valid

    geometrias = []
    for geometria_geojson in _geometrias_geojson(contenido):
        geometria = make_valid(shape(geometria_geojson))
        if not geometria.is_empty:
            geometrias.append(transform(transformar, geometria))
    return unary_union(geometrias) if geometrias else None


def calcular_transiciones_cobertura(
    cobertura_inicial: dict[str, Any],
    cobertura_final: dict[str, Any],
    area_geojson: dict[str, Any],
) -> dict[str, Any]:
    """Calcula bosque estable, pérdida y ganancia en una proyección equivalente."""

    from pyproj import Transformer
    from shapely.geometry import GeometryCollection, mapping
    from shapely.ops import transform, unary_union

    a_m = Transformer.from_crs("EPSG:4326", CRS_METRICAS, always_xy=True)
    a_wgs = Transformer.from_crs(CRS_METRICAS, "EPSG:4326", always_xy=True)
    area_m = _union_proyectada(area_geojson, a_m.transform)
    inicial_m = _union_proyectada(cobertura_inicial, a_m.transform)
    final_m = _union_proyectada(cobertura_final, a_m.transform)
    vacia = GeometryCollection()
    inicial_m = (inicial_m or vacia).intersection(area_m)
    final_m = (final_m or vacia).intersection(area_m)
    estable_m = inicial_m.intersection(final_m)
    perdida_m = inicial_m.difference(final_m)
    ganancia_m = final_m.difference(inicial_m)

    def partes_poligonales(geometria) -> list:
        """Devuelve solo superficies; Folium no calcula límites de GeometryCollection."""

        if geometria.is_empty:
            return []
        if geometria.geom_type == "Polygon":
            return [geometria]
        if geometria.geom_type in {"MultiPolygon", "GeometryCollection"}:
            partes = []
            for subgeometria in geometria.geoms:
                partes.extend(partes_poligonales(subgeometria))
            return partes
        # Las intersecciones pueden producir líneas o puntos de área cero. No son
        # cambios de cobertura y no deben enviarse como evidencia forestal.
        return []

    def salida(nombre: str, geometria) -> dict[str, Any]:
        partes = partes_poligonales(geometria)
        superficie = unary_union(partes) if partes else GeometryCollection()
        return {
            "tipo": nombre,
            "area_ha": round(float(superficie.area) / 10_000, 4),
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"tipo": nombre},
                        "geometry": mapping(transform(a_wgs.transform, parte)),
                    }
                    for parte in partes
                ],
            },
        }

    return {
        "bosque_estable": salida("Bosque estable", estable_m),
        "perdida_bosque": salida("Pérdida de bosque", perdida_m),
        "ganancia_bosque": salida("Ganancia de bosque", ganancia_m),
    }


def _resumen_periodo(resultado: dict[str, Any]) -> dict[str, float | int | bool]:
    clase = resultado["metricas_clase"]
    red = resultado["metricas_red"]
    return {
        "superficie_bosque_ha": clase["area_total_bosque_ha"],
        "porcentaje_bosque": clase["porcentaje_paisaje_bosque"],
        "numero_parches": clase["numero_parches"],
        "area_media_parche_ha": clase["area_media_parche_ha"],
        "indice_parche_mayor_pct": clase["indice_parche_mayor_pct"],
        "densidad_borde_m_ha": clase["densidad_borde_m_ha"],
        "parches_aislados": red["numero_parches_aislados"],
        "porcentaje_parches_aislados": red["porcentaje_parches_aislados"],
        "numero_componentes": red["numero_componentes"],
        "porcentaje_nodos_componente_mayor": red[
            "porcentaje_nodos_componente_mayor"
        ],
        "numero_aristas": red["numero_aristas"],
        "red_totalmente_conectada": red["red_totalmente_conectada"],
    }


def analizar_comparacion_geojson(
    *,
    fuente: str,
    anio_inicial: int,
    anio_final: int,
    cobertura_inicial: dict[str, Any],
    cobertura_final: dict[str, Any],
    area_geojson: dict[str, Any],
    distancia_maxima_m: float = 500,
    area_minima_parche_ha: float = 0.0,
) -> dict[str, Any]:
    """Ejecuta dos análisis independientes con parámetros idénticos."""

    especificacion = validar_solicitud_temporal(
        fuente,
        anio_inicial,
        anio_final,
        distancia_maxima_m,
        area_minima_parche_ha,
    )
    area_geometria = normalizar_area_geojson(area_geojson)
    parametros = {
        "umbral_m": float(distancia_maxima_m),
        "area_min_ha": float(area_minima_parche_ha),
        "incluir_contexto_exterior": False,
    }
    analisis_inicial = analizar_fragmentacion_geojson(
        bosque_geojson=cobertura_inicial,
        aoi_geojson=area_geometria,
        **parametros,
    )
    analisis_final = analizar_fragmentacion_geojson(
        bosque_geojson=cobertura_final,
        aoi_geojson=area_geometria,
        **parametros,
    )
    resumen_inicial = _resumen_periodo(analisis_inicial)
    resumen_final = _resumen_periodo(analisis_final)
    claves_delta = (
        "superficie_bosque_ha",
        "porcentaje_bosque",
        "numero_parches",
        "area_media_parche_ha",
        "parches_aislados",
        "porcentaje_parches_aislados",
        "numero_componentes",
        "numero_aristas",
    )
    cambios = {
        clave: round(float(resumen_final[clave]) - float(resumen_inicial[clave]), 4)
        for clave in claves_delta
    }
    # Las transiciones se calculan sobre los mismos parches que superaron el
    # filtro mínimo en ``bosque_conectividad``. Así, bosque estable + pérdida
    # reproduce la superficie inicial reportada, sin reincorporar polígonos que
    # hayan quedado por debajo del umbral tras la simplificación geométrica.
    cobertura_analizada_inicial = analisis_inicial["parches_geojson"]
    cobertura_analizada_final = analisis_final["parches_geojson"]
    transiciones = calcular_transiciones_cobertura(
        cobertura_analizada_inicial,
        cobertura_analizada_final,
        area_geometria,
    )
    return {
        "fuente": asdict(especificacion),
        "anio_inicial": int(anio_inicial),
        "anio_final": int(anio_final),
        "parametros_equivalentes": {
            "distancia_maxima_m": float(distancia_maxima_m),
            "area_minima_parche_ha": float(area_minima_parche_ha),
            "resolucion_m": especificacion.resolucion_m,
            "ocho_vecinos_raster": True,
            "contexto_exterior": False,
            "crs_metricas": CRS_METRICAS,
        },
        "periodos": {
            str(anio_inicial): {
                "resumen": resumen_inicial,
                "analisis": analisis_inicial,
                "cobertura_geojson": cobertura_analizada_inicial,
            },
            str(anio_final): {
                "resumen": resumen_final,
                "analisis": analisis_final,
                "cobertura_geojson": cobertura_analizada_final,
            },
        },
        "cambios": cambios,
        "transiciones": transiciones,
        "metadatos": {
            "generado_utc": datetime.now(timezone.utc).isoformat(),
            "metodo": (
                "Cobertura bosque/no bosque por año; vectorización de componentes "
                "contiguos; parches como nodos y aristas cuando la distancia entre "
                "bordes no supera el umbral configurado. Cada año se calcula de forma "
                "independiente con parámetros idénticos."
            ),
            "definicion_bosque": especificacion.definicion_bosque,
            "limitacion_fuente": especificacion.limitacion,
            "interpretacion": (
                "Conectividad estructural potencial. No demuestra movimiento de fauna, "
                "conectividad funcional ni causalidad de los cambios."
            ),
        },
    }


def ejecutar_analisis_temporal_ee(
    *,
    fuente: str,
    anio_inicial: int,
    anio_final: int,
    area_geojson: dict[str, Any],
    distancia_maxima_m: float = 500,
    area_minima_parche_ha: float = 0.0,
    ee_module=None,
) -> dict[str, Any]:
    """Recupera ambas coberturas y ejecuta el recálculo científico completo."""

    validar_solicitud_temporal(
        fuente,
        anio_inicial,
        anio_final,
        distancia_maxima_m,
        area_minima_parche_ha,
    )
    cobertura_inicial = recuperar_cobertura_geojson_ee(
        fuente,
        anio_inicial,
        area_geojson,
        area_minima_parche_ha=area_minima_parche_ha,
        ee_module=ee_module,
    )
    cobertura_final = recuperar_cobertura_geojson_ee(
        fuente,
        anio_final,
        area_geojson,
        area_minima_parche_ha=area_minima_parche_ha,
        ee_module=ee_module,
    )
    return analizar_comparacion_geojson(
        fuente=fuente,
        anio_inicial=anio_inicial,
        anio_final=anio_final,
        cobertura_inicial=cobertura_inicial,
        cobertura_final=cobertura_final,
        area_geojson=area_geojson,
        distancia_maxima_m=distancia_maxima_m,
        area_minima_parche_ha=area_minima_parche_ha,
    )
