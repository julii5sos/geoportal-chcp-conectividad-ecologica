# Fase 9 — diagnóstico inicial de paridad científica

Fecha de corte: 7 de noviembre de 2026
Base auditada: `feature/fase8-motor-panel-corredores`, commit `93dd629`
Rama correctiva: `feature/correctiva-evaluacion-ecologica-2023`

## Resultado ejecutivo

El commit `93dd629` contiene el HTML que sirve de base a la fase correctiva. Los módulos
`metodologia_indice.py`, `bosque_conectividad.py` y `corredores.py` conservan el método
original, pero la API Flask de Fase 8 no invocaba la preevaluación original. El asistente
HTML enviaba todas las solicitudes a `POST /api/v1/analyses`, que ejecutaba exclusivamente
el motor temporal de JRC/ESRI. La pérdida principal fue, por tanto, de orquestación y
presentación, no de las fórmulas fuente.

El motor estructural original de 2021 también está presente, pero permanecía confinado a
`app_experiencia.py` y dependía de un asset configurable. Aún no estaba conectado a Flask.
El asset concreto suministrado para Fase 9 debe comprobarse antes de declarar paridad.

## Cadena de ejecución en Fase 8

`Asistente HTML` → `POST /api/v1/analyses` → `webapp.main.api_analysis` →
`webapp.service.run_analysis` → `ejecutar_analisis_temporal_ee` o
`ejecutar_analisis_integrado_ee` → JSON temporal → `platform.js` → Leaflet/Panel.

La cadena original esperaba:

`Área` → señales JRC/Hansen/ESRI/GEDI/NDVI → reglas de `metodologia_indice.py` →
índice 0–6.5 → prioridad/consistencia → corredores → estructura 2021 → prioridad de
visita → mapas, interpretación y descarga.

La interrupción estaba entre la API Flask y los servicios originales: no existía endpoint
para esa segunda cadena.

## Matriz obligatoria previa a la corrección

| Funcionalidad | Archivo y función original | Archivo y función HTML en `93dd629` | Estado inicial | Diferencia concreta | Acción necesaria |
|---|---|---|---|---|---|
| Señal JRC | `app_experiencia.ejecutar_analisis`, `metodologia_indice.evaluar_senales` | `analisis_temporal.ejecutar_analisis_temporal_ee` | Sustituida | El HTML calculaba cobertura temporal, no la señal fija JRC 2025 | Conectar flujo original independiente |
| Señal Hansen | `imagenes_hansen`, `evaluar_senales` | `analisis_complementario.analizar_hansen` bajo demanda | Conservada pero desconectada | Estadística disponible, sin activar señal ni peso | Restaurar reducción y umbral original |
| Señal ESRI | `obtener_esri(2017/2024)`, `evaluar_senales` | Comparador anual ESRI | Sustituida | Los años del usuario podían reemplazar el período fijo 2017–2024 | Separar Modo A y B |
| Señal GEDI | `imagen_gedi`, `evaluar_senales` | `analizar_gedi` bajo demanda | Conservada pero desconectada | No llegaba al índice original | Restaurar cobertura válida, altura y línea base |
| Señal NDVI | `obtener_ndvi(2020/2025)`, `evaluar_senales` | `analizar_ndvi` bajo demanda | Conservada pero desconectada | No aplicaba simultáneamente área, porcentaje y cobertura válida del índice | Restaurar regla fija original |
| Índice ponderado | `calcular_indice_prioridad` | Sin llamada Flask | Conservada pero desconectada | Pesos 2/2/1.5/.5/.5 no se presentaban | Endpoint y panel propios |
| Clasificación de prioridad | `clasificar_prioridad` | Sin equivalente en resultado temporal | Conservada pero desconectada | No había Alta/Media/Preventiva/Baja original | Presentar sin renormalizar |
| Consistencia | `evaluar_consistencia` | Sin equivalente | Conservada pero desconectada | No se reportaba coincidencia lógica ni lectura mixta | Restaurar resultado y explicación |
| Sectores para revisión | `imagen_coincidencia_revision` | Concordancia JRC+ESRI temporal | Sustituida | Se confundían productos diferentes; faltaba Hansen y la malla original | Recuperar mapa JRC+Hansen+ESRI 1/2/3 |
| Prioridad de visita | `calcular_prioridad_visita` | Solo contexto vectorial de corredores | Conservada pero desconectada | No se sumaba aporte estratégico máximo 1.5 | Conectar luego del índice |
| Corredores | `corredores.cargar_corredores` | `/api/v1/territory` + `platform.js` | Error de integración | Los interruptores nacían marcados, pero las capas no se añadían a Leaflet | Añadir capas al iniciar y mantener conmutadores |
| Intersección de corredores | `analizar_interseccion_corredores` | `run_analysis` | Conservada y conectada | Se calculaba, pero el visor temporal no mostraba toda la prioridad integrada | Integrar con Modo A y Panel |
| Fragmentación original | `bosque_conectividad.analizar_fragmentacion_geojson` | Motor temporal con máscaras JRC/ESRI | Sustituida | El temporal no usa cobertura oficial 2021 ni contexto exterior | Restaurar escenario 2021 por separado |
| Red de conectividad original | `analizar_fragmentacion_conectividad` | Red temporal por período | Sustituida | Metodología temporal válida, pero no equivalente a la original | Mantener ambas con etiquetas claras |
| Contexto forestal exterior | `app_experiencia.analizar_bosque_asset` | Ausente | Conservada pero desconectada | Falta buffer adaptativo hasta 5 km en Flask | Verificar asset 2021 y conectar función original |
| Índice conector | `bosque_conectividad.py` (grado 40 %, intermediación 30 %, área 20 %, fuerza 10 %) | No presentado por HTML | Conservada pero desconectada | Resultado potencial existe solo en Streamlit | Exponer en JSON/Panel sin cambiar pesos |
| Brechas potenciales | `bosque_conectividad.py`, `reporte_cartografico.py` | No representadas | Calculada pero no presentada | No había capa Leaflet | Exponer GeoJSON y simbología distinta |
| Ruta potencial a corredor | `bosque_conectividad.py` | No representada | Conservada pero desconectada | La ruta original no llegaba a Flask | Restaurar con contexto 2021, no usar centroides nuevos |
| ERI | `eri_gee.calcular_eri_geojson` | `POST /api/v1/eri` | Conservada y conectada | Correctamente separado; faltaba integración uniforme en algunos resultados | Mantener independiente |
| Comparación temporal | Fase 3, independiente del original | `POST /api/v1/analyses` | Conservada y conectada | Había reemplazado visualmente al flujo original | Mantener como Modo B |
| Panel | Salidas Streamlit originales | `panel.js` | Calculada pero no presentada | Solo entendía temporal/evidencia; fallaba semánticamente con otros `kind` | Añadir vistas por modo |
| Mapas | Folium/EE original | Leaflet | Parcial | Capas temporales sí; coincidencia, red original, brechas y rutas no | Agregar descriptores y GeoJSON reales |
| Reportes/descargas | `reporte_cartografico.py` + registros | ZIP genérico Flask | Parcial | Conserva JSON/área, pero no todos los productos originales | Ampliar al restaurar estructura 2021/2023 |

## Elementos que pueden conservarse

- API segura, caché y `result_id` de Fases 7–8.
- Motor temporal JRC/ESRI y concordancia, como Modo B.
- Evidencias Hansen, NDVI, GEDI y WorldCover bajo demanda, como Modo C.
- ERI independiente.
- Buscador territorial, límites GeoJSON locales y sincronización Plataforma–Panel.
- `bosque_conectividad.py`, `corredores.py` y `metodologia_indice.py` sin alterar fórmulas.

## Bloqueos y verificaciones obligatorias

1. Confirmar tipo, bandas, códigos, máscara, proyección y metadatos del asset 2021.
2. Determinar si el asset 2021 reproduce la categoría vectorial original o es un derivado.
3. Verificar los códigos 1/2/3 del GeoTIFF 2023 y su NoData antes de usar clase 1.
4. No comparar 2021–2023 como cambio hasta demostrar compatibilidad de definición,
   método, escala, huella y reglas geométricas.

Esta matriz es un diagnóstico de la base `93dd629`. Las correcciones de la rama actual se
documentarán en la matriz final de paridad y no se confunden con el estado inicial.
