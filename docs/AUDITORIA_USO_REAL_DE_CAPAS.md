# Auditoría de uso real de capas en el Geoportal CHCP

Fecha de revisión: 2026-11-07. Rama de trabajo: `feature/correctiva-evaluacion-ecologica-2023`.

## Alcance y criterio

Esta auditoría distingue cuatro estados: **visualización**, **estadística territorial**, **entrada científica** y **documentación**. La presencia de un asset en el catálogo no demuestra que participe en una fórmula ni autoriza comparaciones históricas. No se ejecutó una consulta nueva y costosa de Earth Engine durante esta revisión.

## Hallazgo principal

Los ocho productos SINIA–MiAMBIENTE estaban registrados en `catalogo_assets_sinia.py`, pero la interfaz de Plataforma omitía `2021_general` y `2021_detallado`. Además, `run_layer_preview()` rechazaba cualquier asset de tipo `TABLE`, por lo que la cobertura general oficial 2021 no podía mostrarse aunque estuviera catalogada. Se corrigió el contrato API, el selector y la visualización vectorial pintada por el campo `Categoria`.

## Matriz de trazabilidad

| Producto | Asset y tipo | Visualización | Estadística / motor | Estado y restricción |
|---|---|---|---|---|
| Cobertura histórica 1992 | `SINIA_1992_COBERTURA_HISTORICA_RASTER30M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Implementado para exploración; no comparable automáticamente |
| Cobertura histórica 2000 | `SINIA_2000_COBERTURA_HISTORICA_RASTER30M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Implementado para exploración; códigos distintos de 1992 |
| Bosque/no bosque 2012 | `SINIA_2012_BOSQUE_BINARIO_RASTER5M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Implementado para exploración |
| Uso y cobertura 2012 | `SINIA_2012_USO_SUELO_RASTER5M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Implementado para exploración; 32 clases documentadas |
| Cobertura general 2019 | `SINIA_2019_COBERTURA_GENERAL_RASTER20M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Implementado para exploración |
| Cobertura general oficial 2021 | `SINIA_2021_COBERTURA_GENERAL_VECTOR`, TABLE | `run_layer_preview()` pinta las tres categorías por `Categoria` | `consultar_cobertura_oficial_2021()` y `analizar_estructura_cobertura()` usan el mismo asset centralizado | Implementado y verificado funcionalmente; sin comparación entidad a entidad contra el asset retirado |
| Uso y cobertura detallada 2021 | `SINIA_2021_USO_SUELO_RASTER10M`, IMAGE | `run_layer_preview()` | No participa en el motor actual | Visualización implementada; solo tres grupos documentados, no se inventan las demás clases |
| Diagnóstico general 2023 | `SINIA_2023_COBERTURA_GENERAL_RASTER10M`, IMAGE | `run_layer_preview()` | `cobertura_oficial_2023.py` y escenario diagnóstico de `estructura_cobertura.py` | Integrado sin validación comparativa 2021–2023 |

## Fuentes operativas no pertenecientes al catálogo oficial

- **JRC TMF:** estados forestales y señales de deforestación, degradación y regeneración. Se usa en la preevaluación y el análisis temporal.
- **Hansen GFC:** pérdida arbórea; no se presenta como sinónimo automático de deforestación.
- **ESRI LULC:** clase `Trees`, mantenida metodológicamente separada de JRC.
- **Sentinel-2 NDVI:** composición anual para vigor vegetal; una disminución necesita interpretación.
- **GEDI, relieve e hidrología:** insumos complementarios, no series históricas homogéneas.
- **Corredores publicados y puntos críticos:** contexto territorial. Las conexiones y rutas modeladas se rotulan separadamente.

## Correcciones aplicadas

1. `webapp/models.py`: admite ambos productos 2021 en `LayerPreviewRequest`.
2. `webapp/service.py`: genera teselas de la tabla 2021 sin vectorizar ni reducir regiones; filtra por `Categoria` y pinta únicamente las tres clases documentadas.
3. `webapp/static/js/platform.js`: incorpora ambos productos 2021 al selector y reduce solicitudes de teselas durante movimiento del mapa.
4. `webapp/static/js/panel.js`: el Panel agrupa las ocho coberturas, ofrece una leyenda real y mantiene separados resultados calculados, capas publicadas y rutas potenciales.
5. `webapp/templates/base.html`: la metodología tiene acceso explícito en la navegación; el Panel deja de actuar como catálogo metodológico.

## Riesgos pendientes

- La caché de resultados de `webapp/cache.py` es temporal y en memoria. Reiniciar el servidor elimina los resultados; antes de publicación se necesita almacenamiento persistente si se desea un Panel 2025 precalculado.
- Se demostró equivalencia temática de la clase y compatibilidad geométrica funcional con el motor original. No puede demostrarse igualdad entidad por entidad con el asset retirado.
- Las cartografías 1992, 2000, 2012, 2019, 2021 y 2023 no constituyen por sí solas una serie comparable.
- La leyenda completa del ráster detallado 2021 no está documentada en el repositorio; el visor muestra solo los grupos sustentados.
- Las cifras nacionales de las capturas de referencia son ejemplos visuales y no se incorporaron como resultados del Geoportal CHCP.

## Plan reproducible de cierre

1. Verificar una sola vez los dos previews 2021 con la identidad de Earth Engine autorizada y un AOI pequeño.
2. Conservar el registro de la limitación: el asset retirado no permite una comparación entidad por entidad; cualquier nueva versión debe validarse contra esta línea base operativa.
3. Generar y versionar un resultado territorial de referencia 2025 con metadatos y `result_id`, en vez de insertar cifras estáticas en JavaScript.
4. Implementar un almacén persistente de resultados para el despliegue; el Panel debe leer, no recalcular.
5. Validar visualmente leyendas, carga parcial y errores de teselas en escritorio y móvil.
