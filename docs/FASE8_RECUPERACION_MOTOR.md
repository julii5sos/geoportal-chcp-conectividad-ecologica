# Fase 8 — recuperación del motor científico

## Alcance auditado

Se comparó la rama de trabajo con `evaluacion-corredores-panama/app_experiencia.py`,
`bosque_conectividad.py`, `corredores.py`, sus GeoJSON y el catálogo local. La
interfaz HTML no considera integrada una fuente solo porque figure en el catálogo.

| Fuente | Procedimiento original | Implementación HTML | Estado | Evidencia |
|---|---|---|---|---|
| JRC TMF | `obtener_tmf` y motor temporal | `analisis_temporal.py` | Implementado y verificado | Pruebas previas Fases 3–7 |
| ESRI LULC | serie anual clase Trees | `analisis_temporal.py` | Implementado y verificado | Pruebas previas Fases 3–7 |
| JRC + ESRI | no fusionar metodologías | `analisis_integrado.py` | Implementado y verificado | Comparación real previa |
| Hansen v1.13 | `imagenes_hansen`, serie `lossyear`, umbral 30 % | `analisis_complementario.analizar_hansen` | Implementado y verificado con EE | lectura pequeña en `geoportal-513817` |
| Sentinel-2 NDVI | mediana anual, SCL, respaldo del año anterior | `analisis_complementario.analizar_ndvi` | Implementado y verificado con EE | dos años y tres mapas |
| GEDI/OpenForis | mosaico de `CanopyHeight_GEDI_V27` convertido a float | `analisis_complementario.analizar_gedi` | Implementado y verificado localmente | estadísticas y tesela real |
| ESA WorldCover | no existía como cálculo original | referencia 2021 real | Implementado como evidencia, no como serie | histograma y tesela real |
| SINIA 2021 | `SINIA_2021_COBERTURA_GENERAL_VECTOR` | contrato, estadísticas y motor estructural | Verificado localmente el 2026-11-07 | lectura de la cuenta de servicio pendiente antes del despliegue |
| SINIA 1992/2000 | solo imágenes demostrativas | no se publica como resultado | Pendiente | faltan archivos, CRS y leyenda auditables |
| FIRMS | no se encontró proceso original | bloqueado con mensaje explícito | Pendiente | falta consulta temporal validada |
| GLAD/RADD | no se encontró ruta implementada | no disponible | Pendiente | falta proveedor/API/licencia verificada |
| Corredores | intersección EPSG:8857 y red estructural | catálogo, resumen y motor temporal existente | Implementado | 22 polígonos y 14 puntos |

## Qué se recuperó

- Hansen: superficie `treecover2000` sobre umbral, pérdida anual, pérdida acumulada,
  porcentaje sobre el denominador y mapa `lossyear`.
- NDVI: B8/B4 de Sentinel-2 SR Harmonized, máscara SCL, media, mediana, superficie
  válida, diferencia temporal y mapas inicial/final/diferencia.
- GEDI: altura media, mediana, percentiles 25/75, superficie observada y mapa.
- WorldCover: clases originales 2021 y superficie aproximada por clase; la clase
  10 no se presenta como validación de bosque natural.

Todas estas fuentes son evidencias independientes. No alteran ERI, JRC, ESRI ni
las fórmulas de fragmentación/conectividad.

## Matriz funcional

| Fuente | Carga | Visualización | Proceso científico | Estadística | Descarga | EE real |
|---|---:|---:|---:|---:|---:|---:|
| JRC | sí | sí | sí | sí | sí | sí (fase previa) |
| ESRI | sí | sí | sí | sí | sí | sí (fase previa) |
| Hansen | sí | sí | sí | sí | sí | sí |
| Sentinel-2 NDVI | sí | sí | sí | sí | sí | sí |
| GEDI/OpenForis | sí | sí | sí | sí | sí | sí, identidad local |
| WorldCover 2021 | sí | sí | sí, referencia fija | sí | sí | sí |
| SINIA 2021 | no | no | no | no | no | no |
| FIRMS | no | no | no | no | no | no |
| GLAD/RADD | no | no | no | no | no | no |

## Riesgos y pendientes

1. El asset GEDI externo debe compartirse con la identidad futura de Cloud Run.
2. La máscara NDVI replica el procedimiento original; conviene comparar en una
   futura validación con Cloud Probability/S2 Cloudless.
3. FIRMS no debe presentarse como área quemada; se integrará solo tras definir una
   consulta espacial-temporal y unidades reproducibles.
4. SINIA necesita asset, licencia, campo de clase y permisos verificables.

