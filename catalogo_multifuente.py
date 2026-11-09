"""Matriz verificable de fuentes del Geoportal CHCP.

El estado describe una ruta funcional comprobable. Una mención en documentación o
un identificador de catálogo no convierten una fuente en integración operativa.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from catalogo_assets_sinia import ASSETS_SINIA


ESTADOS = (
    "Integrada y operativa",
    "Integrada parcialmente",
    "Disponible pero no conectada",
    "Pendiente de permisos o migración",
    "No disponible",
    "Descartada justificadamente",
)


@dataclass(frozen=True)
class FuenteTrazable:
    clave: str
    nombre_oficial: str
    proveedor_version: str
    identificador: str | None
    periodo: str
    resolucion: str
    sistema_referencia: str
    definicion_tematica: str
    funcion_ecologica: str
    categoria: str
    modulos: tuple[str, ...]
    estado_original: str
    estado_html: str
    disponibilidad_proyecto: str
    asset_privado: bool
    limitaciones: str
    accion: str


FUENTES_TRAZABILIDAD: dict[str, FuenteTrazable] = {
    "jrc_tmf": FuenteTrazable(
        "jrc_tmf", "JRC Tropical Moist Forest", "JRC TMF v1_2025",
        "projects/JRC/TMF/v1_2025/AnnualChanges", "1990–2025", "30 m",
        "Malla nativa del producto", "Estados anuales del dominio de bosque húmedo tropical.",
        "Cobertura, cambio, fragmentación y conectividad.", "A · principal",
        ("temporal", "fragmentación", "conectividad", "concordancia"),
        "Integrada y operativa", "Integrada y operativa", "Pública; verificada con geoportal-513817", False,
        "No equivale a una clasificación general de toda cobertura arbórea.", "Conservar definición y resolución nativas.",
    ),
    "esri_lulc": FuenteTrazable(
        "esri_lulc", "ESRI Global Land Use / Land Cover", "Annual 10 m 2017–2025",
        "projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS", "2017–2025", "10 m",
        "Malla nativa anual", "Clase Trees de una clasificación anual multiclase.",
        "Escenario independiente de cobertura, fragmentación y conectividad.", "A · principal",
        ("temporal", "fragmentación", "conectividad", "concordancia"),
        "Integrada y operativa", "Integrada y operativa", "Pública; verificada con geoportal-513817", False,
        "Trees no reproduce la definición de bosque húmedo tropical de JRC.", "Comparar sin fusionar ni promediar resultados.",
    ),
    "hansen_gfc": FuenteTrazable(
        "hansen_gfc", "Hansen Global Forest Change", "v1.13 (2000–2025)",
        "UMD/hansen/global_forest_change_2025_v1_13", "Cobertura 2000; pérdida 2001–2025; ganancia 2000–2012", "30.92 m",
        "Malla nativa del producto", "Cobertura de dosel 2000 y perturbación de reemplazo de rodal.",
        "Contexto histórico de pérdida de cobertura arbórea.", "B · complementaria",
        ("preevaluación Streamlit", "API evidencia", "serie de pérdida", "panel territorial"),
        "Integrada y operativa", "Integrada y operativa", "Pública; verificada con geoportal-513817", False,
        "La banda gain no se actualizó después de 2012; pérdida no equivale automáticamente a deforestación.", "Exponer como capa complementaria, no como cobertura anual simétrica.",
    ),
    "worldcover": FuenteTrazable(
        "worldcover", "ESA WorldCover 10 m 2021", "v200",
        "ESA/WorldCover/v200", "2021", "10 m", "Malla nativa del producto",
        "Once clases de cobertura derivadas de Sentinel-1 y Sentinel-2.",
        "Referencia temática independiente.", "B · complementaria", ("API evidencia", "mapa", "panel territorial"),
        "No disponible", "Integrada y operativa", "Pública; verificada con geoportal-513817", False,
        "Un solo año; no sustituye una serie anual ni valida JRC/ESRI.", "Añadir visualización y metadatos antes de usar en cálculos.",
    ),
    "dynamic_world": FuenteTrazable(
        "dynamic_world", "Dynamic World V1", "Google / WRI V1",
        "GOOGLE/DYNAMICWORLD/V1", "2015–actualidad", "10 m", "Malla Sentinel-2",
        "Probabilidades y etiqueta de nueve clases por escena Sentinel-2.",
        "Integridad estructural del ERI y referencia dinámica.", "B · complementaria", ("ERI",),
        "Integrada y operativa", "Integrada y operativa", "Pública; usada por ERI", False,
        "No es una clasificación propia entrenada por el proyecto; variación por escena y nubes.", "Mantener separado de la cobertura anual principal.",
    ),
    "sentinel_ndvi": FuenteTrazable(
        "sentinel_ndvi", "Sentinel-2 Surface Reflectance Harmonized", "Colección armonizada",
        "COPERNICUS/S2_SR_HARMONIZED", "2017–actualidad", "10/20/60 m; resumen del proyecto a 20 m",
        "Malla de cada escena", "Reflectancia superficial para NDVI anual.",
        "Señal corroborativa de vigor vegetal.", "B · complementaria", ("preevaluación Streamlit", "comparador NDVI", "API evidencia", "panel territorial"),
        "Integrada y operativa", "Integrada y operativa", "Pública; verificada con geoportal-513817", False,
        "NDVI responde a estacionalidad, humedad, cultivos, nubes y sombras; no mide biodiversidad.", "Recuperar capa y gráfico con máscara de nubes documentada.",
    ),
    "gedi": FuenteTrazable(
        "gedi", "Canopy Height GEDI / OpenForis", "CanopyHeight_GEDI_V27",
        "users/openforisearthmap/World_EarthMap/CanopyHeight_GEDI_V27", "Referencia fija", "Producto agregado (~100 m en la implementación)",
        "Según el producto externo", "Altura de dosel agregada.", "Contexto estructural y componente del ERI.",
        "B · complementaria", ("ERI", "preevaluación Streamlit", "API evidencia", "panel territorial"),
        "Integrada y operativa", "Integrada y operativa", "Lectura local verificada con geoportal-513817; Cloud Run aún requiere permiso", True,
        "Cobertura espacial e incertidumbre; altura no equivale a edad del bosque.", "Verificar acceso y exponer distribución, no falsa serie anual.",
    ),
    "firms": FuenteTrazable(
        "firms", "FIRMS active fire", "NASA / LANCE / EOSDIS",
        "FIRMS", "2000–actualidad; diario", "1 km", "Malla raster del producto",
        "Detecciones activas MODIS con confianza; producto cercano a tiempo real.",
        "Contexto de focos de calor.", "B · complementaria", ("catálogo de capas",),
        "No disponible", "Disponible pero no conectada", "Pública en Earth Engine", False,
        "El catálogo advierte que no es de calidad científica final; coincidencia no demuestra causa de pérdida.", "Integrar consulta temporal acotada y conteos con advertencia causal.",
    ),
    "glad_radd": FuenteTrazable(
        "glad_radd", "Alertas GLAD / RADD", "Global Forest Watch / proveedores originales",
        None, "Según producto y disponibilidad", "Según producto", "Según servicio de origen",
        "Alertas tempranas de perturbación forestal.", "Contexto de monitoreo reciente.",
        "B · complementaria", ("catálogo de capas",),
        "No disponible", "No disponible", "No existe una ruta implementada ni credenciales/API verificadas", False,
        "Una alerta no es cambio confirmado; acceso y licencia deben verificarse por producto.", "Definir proveedor, API, licencia y validación antes de implementar.",
    ),
    "hydro": FuenteTrazable(
        "hydro", "MERIT Hydro / contexto HydroSHEDS", "MERIT Hydro v1.0.1",
        "MERIT/Hydro/v1_0_1", "Referencia estática", "3 arc-sec (~90 m)", "Malla global",
        "Área de drenaje aguas arriba y red hidrográfica derivada.",
        "Proximidad riparia del ERI.", "C · territorial", ("ERI",),
        "Integrada y operativa", "Integrada y operativa", "Pública; usada por ERI", False,
        "No sustituye cartografía hidrográfica local de mayor detalle.", "Mantener escala y umbral documentados.",
    ),
    "sinia_2021": FuenteTrazable(
        "sinia_2021", "SINIA–MiAMBIENTE · Bosque y otros usos", "Referencia 2021",
        str(ASSETS_SINIA["2021_general"]["asset_id"]), "2021", "Vector institucional", "Según asset institucional",
        "Bosques y otras tierras boscosas según la cartografía oficial aportada.",
        "Fragmentación, conectividad y superficies institucionales de referencia.", "C · histórica/territorial", ("Flask/API", "fragmentación", "conectividad"),
        "Integrada y operativa", "Integrada y operativa", "Asset privado disponible en geoportal-513817", True,
        "No es directamente equivalente a JRC, ESRI ni al diagnóstico 2023.", "Mantener acceso de lectura para la identidad de despliegue.",
    ),
    "sinia_1992_2000": FuenteTrazable(
        "sinia_1992_2000", "SINIA–MiAMBIENTE · coberturas históricas 1992 y 2000", "Por validar",
        None, "1992 y 2000", "No verificada", "No verificado",
        "Clases históricas aún no auditadas.", "Contexto histórico potencial.", "C · histórica/territorial", ("pendiente",),
        "No disponible", "No disponible", "No se hallaron archivos geoespaciales validables; solo imágenes demostrativas del HTML", True,
        "Las leyendas, geometrías, CRS y equivalencia temática no están disponibles.", "Solicitar archivos fuente y metadatos; no publicar los PNG demostrativos.",
    ),
    "corredores": FuenteTrazable(
        "corredores", "Corredores naturales de Panamá · Almanaque Azul", "Versión local documentada 2024.05",
        "data/corredores_almanaque_azul.geojson", "Referencia publicada", "Vector", "GeoJSON WGS 84",
        "Categorías Alta, Mediana y Media-baja y puntos críticos publicados.",
        "Referencia territorial para conectividad estructural.", "C · territorial", ("mapa", "corredores", "conectividad"),
        "Integrada y operativa", "Integrada y operativa", "Datos locales incluidos", False,
        "Proximidad geométrica no prueba conectividad funcional.", "Conservar categorías y atribución originales.",
    ),
    "territorio_chcp": FuenteTrazable(
        "territorio_chcp", "CHCP y subcuencas del Canal de Panamá", "GeoJSON local del portal de referencia",
        "data/territorio/*.geojson", "Referencia territorial", "Vector", "WGS 84 / EPSG:4326",
        "Una cuenca y 53 subcuencas reales incluidas.", "Selección, recorte y resumen territorial.",
        "C · territorial", ("buscador", "mapa", "análisis"),
        "Integrada y operativa", "Integrada y operativa", "Datos locales incluidos", False,
        "Requiere conservar trazabilidad institucional del archivo fuente.", "Usar identificadores locales estables y no volver a depender de un asset GEE.",
    ),
    "eri": FuenteTrazable(
        "eri", "Índice de Resiliencia Ecológica indicativo", "Método interno de referencia 2024",
        None, "Referencia 2024", "Resumen 90 m", "Procesamiento en Earth Engine",
        "Índice ponderado: integridad 35 %, conectividad 25 %, estabilidad 20 %, proximidad riparia 20 %.",
        "Lectura complementaria independiente.", "B · complementaria", ("ERI",),
        "Integrada y operativa", "Integrada y operativa", "Operativo con fuentes públicas/externas", False,
        "Proxy indicativo no validado como resiliencia ecológica real.", "Mantener pesos y separación metodológica.",
    ),
}


def matriz_trazabilidad() -> list[dict[str, object]]:
    return [{**asdict(source), "modulos": list(source.modulos)} for source in FUENTES_TRAZABILIDAD.values()]


def catalogo_por_categoria() -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for source in FUENTES_TRAZABILIDAD.values():
        result.setdefault(source.categoria, []).append({**asdict(source), "modulos": list(source.modulos)})
    return result

