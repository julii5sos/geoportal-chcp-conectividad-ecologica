# Matriz de restauración del motor original

Fecha de revisión: 2026-11-07
Rama: `feature/correctiva-evaluacion-ecologica-2023`

Esta matriz compara funciones, no solamente nombres de módulos. La referencia es el
repositorio original `evaluacion-corredores-panama` y la implementación Flask actual.

| Capacidad | Implementación original | Integración HTML/Flask | Estado comprobado | Corrección o pendiente |
|---|---|---|---|---|
| Cinco señales territoriales | `app_experiencia.ejecutar_analisis`, `metodologia_indice.evaluar_senales` y `calcular_indice_prioridad` | `evaluacion_ecologica.ejecutar_evaluacion_ecologica`, llamada por `webapp.service.run_ecological_evaluation` | Conectada. Usa JRC TMF, Hansen, ESRI, GEDI y NDVI y conserva el máximo de 6.5 | Mantener la preevaluación separada del motor de parches |
| Consistencia de señales | `metodologia_indice.evaluar_consistencia` | Incluida en `ejecutar_evaluacion_ecologica` y mostrada por `renderEcologicalEvaluation` | Conectada y visible | La UI debe explicar señal, ausencia de señal y falta de datos por separado |
| Prioridad territorial | `clasificar_prioridad` y `calcular_prioridad_visita` | La preevaluación calculaba prioridad con corredores, pero sin estructura; el análisis integral mostraba después la estructura sin actualizar la lectura | Parcial antes de esta corrección | `run_integrated_evaluation` vuelve a llamar la función original con el resultado estructural ya calculado. La estructura orienta el foco y no suma puntos |
| Fragmentación 2021 | `bosque_conectividad.analizar_fragmentacion_conectividad` sobre cobertura institucional | `estructura_cobertura.analizar_estructura_cobertura` reutiliza `analizar_fragmentacion_geojson` desde `run_structural_connectivity` | Conectada | Mantener área, número, tamaño, densidad y borde; no ejecutar en preevaluación territorial |
| Contexto exterior adaptativo | `corredores.calcular_radio_contexto` y análisis forestal hasta 5 km | `run_structural_connectivity` calcula el radio antes de llamar al motor estructural | Conectado | El contexto no debe aumentar la superficie reportada del AOI |
| Red estructural | Métricas de componentes, aislamiento, árbol mínimo y brechas en `bosque_conectividad.py` | GeoJSON y métricas devueltos por `analizar_estructura_cobertura`; capas en `platform.js` | Conectada | La gráfica y la interpretación estaban incompletas; ahora se presentan parches en red/aislados y distribución de tamaños cuando los atributos están disponibles |
| Corredores publicados | `corredores.analizar_interseccion_corredores` | Se ejecuta en preevaluación y estructura; el mapa usa `territory_payload` | Conectada | Mantener distinta la intersección publicada de la ruta estructural potencial |
| Ruta potencial a corredor | `bosque_conectividad._conexion_hacia_corredor` | `ruta_corredor_geojson` en el resultado estructural y capa Leaflet | Conectada | No presentarla como corredor oficial ni como prueba de movimiento de fauna |
| ERI | `eri_indicativo.py` y cálculo GEE del visor anterior | `eri_gee.calcular_eri_geojson`, endpoint `/api/v1/eri` | Conectada como módulo independiente | No sumarla al índice territorial ni convertirla en índice anual |
| Mapas impresos | `reporte_cartografico.crear_mapa_fragmentacion` y `crear_mapa_conectividad` | Reutilizados por `informe_tecnico.generar_informe_tecnico` | Conectados | Verificar visualmente cada tipo de resultado real antes de publicación |
| Informe PDF | `app_experiencia.generar_pdf` más mapas de `reporte_cartografico.py` | `/api/v1/results/<id>/report.pdf` genera desde caché con `informe_tecnico.py` | Implementado, sin recalcular Earth Engine | Falta validar una descarga real de una evaluación controlada con credenciales y revisar todas las páginas renderizadas |
| Descarga de datos | Registro metodológico, mapas y resultados del visor original | `build_download` crea ZIP desde el resultado almacenado | Conectada | Añadir archivos especializados solo cuando el módulo correspondiente fue ejecutado |
| Series temporales | `calcular_serie_fuente` y gráficas contextuales del visor original | Motor temporal independiente y vistas de Panel | Conectada como análisis separado | No mezclar fuentes incompatibles en un eje común |
| Ocho coberturas oficiales | Assets históricos y diagnósticos | `catalogo_assets_sinia.py`, vistas previas y endpoints 2021/2023 | Catálogo conectado; estadísticas reales disponibles para 2021 y 2023 mediante solicitud explícita | 1992, 2000, 2012 y 2019 son productos independientes; no declarar una serie homogénea sin homologación |

## Diferencias metodológicas que deben permanecer visibles

- El índice territorial usa cinco señales y un máximo de 6.5 puntos.
- El aporte estratégico de corredores pertenece a la prioridad de visita, no al índice
  satelital.
- La condición estructural orienta la focalización y no añade un peso no calibrado.
- La fragmentación y la conectividad usan la cobertura oficial 2021; el diagnóstico
  2023 es un escenario independiente.
- ERI, JRC, ESRI y productos oficiales conservan sus definiciones, escalas y años.

## Verificación pendiente de alto costo

Se requiere una sola ejecución representativa sobre una subcuenca pequeña para comprobar
el flujo completo con Earth Engine: cinco señales, estructura 2021, corredores, ruta,
Panel, ZIP y PDF. No debe repetirse hasta que las pruebas locales y los contratos de la
API estén estables.
