"""Catálogo verificable de fuentes y disponibilidad temporal del Geoportal CHCP.

Este módulo no depende de Streamlit ni de Earth Engine. Centraliza la información
que la interfaz necesita para no ofrecer años inexistentes ni presentar productos
de referencia fija como si fueran series anuales homogéneas.
"""

from __future__ import annotations

from dataclasses import dataclass

from metodologia_indice import PERIODOS_ANALISIS


@dataclass(frozen=True)
class FuenteGeoportal:
    clave: str
    nombre: str
    resolucion: str
    proyeccion: str
    version: str
    anio_inicial: int | None
    anio_final: int | None
    temporal: bool
    comparable: bool
    nota: str

    @property
    def anios(self) -> tuple[int, ...]:
        if not self.temporal or self.anio_inicial is None or self.anio_final is None:
            return ()
        return tuple(range(self.anio_inicial, self.anio_final + 1))


FUENTES_GEOSPACIALES: dict[str, FuenteGeoportal] = {
    "jrc_tmf": FuenteGeoportal(
        clave="jrc_tmf",
        nombre="JRC Tropical Moist Forest",
        resolucion="30 m",
        proyeccion="Malla nativa del producto",
        version="v1_2025",
        anio_inicial=1990,
        anio_final=PERIODOS_ANALISIS["jrc_diagnostico"],
        temporal=True,
        comparable=True,
        nota="Estado anual del bosque tropical; las clases conservan la definición de JRC.",
    ),
    "hansen_gfc": FuenteGeoportal(
        clave="hansen_gfc",
        nombre="Hansen Global Forest Change",
        resolucion="30 m",
        proyeccion="Malla nativa del producto",
        version="v1.13 (2025)",
        anio_inicial=2001,
        anio_final=PERIODOS_ANALISIS["hansen_diagnostico"],
        temporal=True,
        comparable=True,
        nota="Año de detección de pérdida de cobertura arbórea; no equivale por sí solo a deforestación.",
    ),
    "esri_lulc": FuenteGeoportal(
        clave="esri_lulc",
        nombre="ESRI Land Use / Land Cover",
        resolucion="10 m",
        proyeccion="Malla nativa anual",
        version=f"{PERIODOS_ANALISIS['esri_inicial']}–{PERIODOS_ANALISIS['esri_final_visual']}",
        anio_inicial=PERIODOS_ANALISIS["esri_inicial"],
        anio_final=PERIODOS_ANALISIS["esri_final_visual"],
        temporal=True,
        comparable=True,
        nota=(
            "Cobertura anual. El mapa admite la edición 2025; el índice conserva "
            "su período metodológico 2017–2024."
        ),
    ),
    "sentinel_ndvi": FuenteGeoportal(
        clave="sentinel_ndvi",
        nombre="Sentinel-2 / NDVI",
        resolucion="10 m",
        proyeccion="Composición anual en Earth Engine",
        version="Sentinel-2 SR Harmonized",
        anio_inicial=2017,
        anio_final=PERIODOS_ANALISIS["ndvi_final_visual"],
        temporal=True,
        comparable=True,
        nota="El comparador cambia la visualización; el índice conserva su período metodológico documentado.",
    ),
    "gedi": FuenteGeoportal(
        clave="gedi",
        nombre="GEDI / OpenForis · altura del dosel",
        resolucion="Producto agregado",
        proyeccion="Según producto de origen",
        version="CanopyHeight_GEDI_V27",
        anio_inicial=None,
        anio_final=None,
        temporal=False,
        comparable=False,
        nota="Distribución de alturas disponible; no constituye una serie anual comparable.",
    ),
    "bosque_2021": FuenteGeoportal(
        clave="bosque_2021",
        nombre="SINIA–MiAMBIENTE · Bosque y otros usos",
        resolucion="Escala institucional",
        proyeccion="Vector institucional",
        version="2021",
        anio_inicial=2021,
        anio_final=2021,
        temporal=False,
        comparable=False,
        nota="Referencia fija empleada por el análisis vigente de fragmentación y conectividad.",
    ),
    "eri": FuenteGeoportal(
        clave="eri",
        nombre="Índice de Resiliencia Ecológica indicativo",
        resolucion="Componentes con resoluciones propias",
        proyeccion="Procesamiento en Earth Engine",
        version="Referencia 2024",
        anio_inicial=2024,
        anio_final=2024,
        temporal=False,
        comparable=False,
        nota="Índice complementario de referencia fija; no es una serie anual ni modifica la prioridad.",
    ),
}


def obtener_fuente(clave: str) -> FuenteGeoportal:
    try:
        return FUENTES_GEOSPACIALES[clave]
    except KeyError as exc:
        raise KeyError(f"Fuente no registrada en el catálogo: {clave}") from exc


def anios_disponibles(clave: str) -> tuple[int, ...]:
    return obtener_fuente(clave).anios


def validar_periodo(clave: str, anio_inicial: int, anio_final: int) -> tuple[int, int]:
    """Valida un período sin sustituir silenciosamente años no disponibles."""

    fuente = obtener_fuente(clave)
    if not fuente.comparable:
        raise ValueError(f"{fuente.nombre} no admite comparación temporal anual.")
    if anio_inicial >= anio_final:
        raise ValueError("El año inicial debe ser anterior al año final.")
    disponibles = fuente.anios
    if anio_inicial not in disponibles or anio_final not in disponibles:
        raise ValueError(
            f"{fuente.nombre} solo admite años entre {fuente.anio_inicial} y {fuente.anio_final}."
        )
    return anio_inicial, anio_final


def filas_catalogo() -> list[dict[str, object]]:
    """Representación tabular para metodología y trazabilidad."""

    filas = []
    for fuente in FUENTES_GEOSPACIALES.values():
        periodo = (
            f"{fuente.anio_inicial}–{fuente.anio_final}"
            if fuente.temporal
            else fuente.version
        )
        filas.append(
            {
                "Fuente": fuente.nombre,
                "Período disponible": periodo,
                "Resolución": fuente.resolucion,
                "Versión": fuente.version,
                "Comparación anual": "Sí" if fuente.comparable else "No",
                "Limitación": fuente.nota,
            }
        )
    return filas
