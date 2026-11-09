# Integración del panel de referencia

Fecha de auditoría: 2026-11-07
Rama revisada: `feature/correctiva-evaluacion-ecologica-2023`
Referencia visual: `panel_codex.zip` (`PANEL_SPEC.md`, `panel.html`, `panel.css`, `tokens.css` y `panel_canal.js`).

## Regla de integración

El ZIP define composición, jerarquía visual e interacción. No constituye una fuente científica. Las cifras de `datos_ejemplo.json`, las capas KBA/CONNECT, probabilidades de riesgo y categorías Proteger/Restaurar/Vigilar no se incorporan. El motor Python/Flask, sus pesos, cortes, fuentes y advertencias siguen siendo la única fuente de resultados.

## Estado del proceso revisado

- Aplicación Flask local: `http://127.0.0.1:8083`.
- Rutas comprobadas: `/`, `/panel`, `/platform`, `/methodology` y `/api/v1/health`.
- El Panel recupera un resultado explícito o el último resultado persistido en la sesión; cambiar de pestaña no ejecuta Earth Engine.
- Las descargas PDF y ZIP reutilizan el `result_id`; son acciones diferentes y no recalculan el análisis.
- La cobertura oficial 2021 permanece bloqueada cuando no está disponible el asset configurado. No se sustituye por una cifra simulada.

## Matriz de paridad visual, funcional y científica

| Elemento del ZIP | Equivalente actual | Origen real del dato | Función / API | Representación | Estado | Solución de integración |
|---|---|---|---|---|---|---|
| Panel izquierdo de hasta 600 px | `.panel-results-column` | UI, sin dato científico | `/panel` + `panel.js` | Contenedor de resultados | Presente, estilo inconsistente | Adoptar la rejilla `minmax(0,600px) minmax(0,1fr)` y limitar el desplazamiento a la columna izquierda. |
| Mapa Leaflet permanente | `#panel-map` | Geometrías locales, capas GEE y resultados guardados | `/api/v1/territories/*`, capas del resultado | Mapa | Probado | Mantenerlo montado al cambiar pestañas y ejecutar `invalidateSize()` tras cambios de disposición. |
| Cabecera azul contextual | `.territory-panel-head` separada del panel | Nombre del territorio y estado local | Plantilla + `updateTerritory()` | Título y acciones | Presente, desconectada visualmente | Integrarla en la columna izquierda con título, referencia analítica y acciones compactas. |
| Selector territorial compacto | `#panel-search` | Catálogo local de cuenca y 53 subcuencas | `/api/v1/search`, `/api/v1/territories/<id>` | Buscador y resaltado cartográfico | Probado | Conservar identificadores reales y URL `?territory=`; compactar sin crear una segunda fuente de verdad. |
| Cinco pestañas principales | Seis pestañas + selector secundario | Estado de UI y resultado actual | `renderTab()` | Navegación temática | Presente, redundante | Agrupar en Resumen; Cobertura y cambio; Fragmentación y conectividad; Corredores; Interpretación e informe. Conservar temporal, concordancia, oficiales y ERI como navegación secundaria. |
| Presets de capas por pestaña | `renderThemeLayerControls()` y `syncMapTheme()` | Capas reales disponibles y GeoJSON del resultado | `panel.js` | Mapa + leyenda | Presente, parcial | Usar únicamente claves reales; activar contexto/pérdida/parches/red/corredores según la pestaña sin recalcular. |
| Leyenda flotante y opacidad | `.panel-map-layers`, `#panel-map-legend`, rango de opacidad | Estilos de la capa activa | `renderThemeLayerControls()` | Control cartográfico | Presente | Ordenar como panel compacto; mostrar leyenda real y ocultar entradas no calculadas. |
| Widget blanco `.wg` | `metric-grid`, `priority-banner`, gráficas | Resultado persistido o resumen territorial | `resultTab()`, `moduleShowcase()` | Métricas, gráfica e interpretación | Presente, heterogéneo | Normalizar cada bloque a título, métrica/unidad, año/fuente, gráfica útil, explicación y limitación. |
| Donut de cobertura | No existe como componente general | Clases de cobertura oficial o resultado compatible | `/api/v1/official-coverages/*` | Gráfico | No calculado para el territorio actual | Mostrar solo cuando existan clases y denominador válido; no copiar cifras nacionales del ejemplo. |
| Barras de contribución | `panelBarChart()` | Cinco contribuciones del índice de indicios | Resultado `ecological_evaluation` / integral | Gráfica | Probado con resultado real | Mantener valores 0–6.5 y aclarar que no son probabilidades. |
| Serie de pérdida anual | Vista de evidencia parcial | Hansen anual cuando el resultado la contiene | Motor territorial existente | Barras | Presente, según resultado | Renderizar solo los años devueltos por el motor; no inferir ganancia ni rellenar años ausentes. |
| Parches y red | `structure.parches_geojson`, aristas y métricas | Cobertura estructural oficial/diagnóstica procesada | Motor de fragmentación y conectividad | Mapa, cifras y explicación | Calcula pero depende del asset | Conservar ejecución explícita; reutilizar caché por área/parámetros y declarar el bloqueo del asset 2021 cuando ocurra. |
| Corredores publicados | `territoryReference.corridors` y `corridor_context` | 22 polígonos y 14 puntos críticos publicados | `analizar_interseccion_corredores()` | Mapa, ha, %, nombres | Probado | Separar superposición publicada de la red o ruta potencial modelada. |
| Ruta potencial | Resultado estructural, cuando existe | Parches, red y umbral configurado | Motor original de conectividad/corredores | Línea en mapa + texto | Bajo demanda, no siempre calculada | Ocultar si el análisis no la produjo; nunca reemplazarla con el corredor estático. |
| Prioridad territorial | `evaluation.priority`, `score`, `contributions` | Cinco señales del motor original | `run_ecological_evaluation()` | Tarjeta, barras e interpretación | Probado | Mostrar señal, aporte, máximo 6.5, fuente/período y lectura automática. |
| Prioridad integrada de visita | `visit_priority` | Índice territorial + valor estratégico de corredor | `calcular_prioridad_visita()` | Síntesis interpretativa | Probado | Mantener separada del índice territorial y del ERI; máximo estratégico adicional 1.5. |
| ERI | Vista secundaria `eri` | Motor ERI existente | Resultado específico ERI | Tarjetas/interpretación | Presente, independiente | Conservar como módulo complementario; no presentarlo como pérdida ni probabilidad anual. |
| Coberturas oficiales históricas | Selector de ocho assets SINIA | Assets catalogados en `geoportal-513817` | Catálogo y endpoints 2021/2023 | Mapa, clases y barras | Catálogo presente; 2021 bloqueado por asset operativo faltante | Mostrar metadatos y capa solo cuando el endpoint real responda; separar productos no comparables. |
| Botón Explorar | Enlaces al Panel/Plataforma | Navegación | Rutas Flask | Acción | Presente | Mantener como navegación sin ejecutar análisis. |
| Botón Ejecutar análisis | `Crear análisis` / Plataforma | Parámetros del usuario | Endpoints de análisis | Modal/flujo científico | Presente | Abrir la Plataforma y ejecutar solo tras confirmación; no duplicar con Explorar. |
| Botón PDF | Enlace `report.pdf` | Resultado guardado | `/api/v1/results/<id>/report.pdf` | Descarga PDF | Probado con resultado real | Hacerlo visible en Interpretación e informe; deshabilitar con explicación si no hay `result_id`. |
| Botón Datos | Enlace `download.zip` | Resultado guardado y metadatos | `/api/v1/results/<id>/download.zip` | Descarga ZIP | Presente | Mantener separado del PDF; no volver a ejecutar Earth Engine. |
| URL sincronizada | `?territory=...&tab=...` | Estado del Panel | `history.replaceState()` | Navegación reproducible | Presente | Conservar compatibilidad; mapear las pestañas antiguas a los nuevos grupos. |
| Mensajes interpretativos | Textos en `resultTab()` y motor | Valores calculados + reglas originales | Python y JS | 2–4 frases | Presente, parcial | Recuperar lectura científica específica y ocultar frases cuyos datos no estén calculados. |
| KBA, riesgo 0–1, CONNECT y acciones de manejo | Solo en el ejemplo del ZIP | Sin fuente implementada validada | Ninguna | Ninguna | Inexistente | No incorporar. Mostrar “No calculado” únicamente si resulta necesario explicar una ausencia. |

## Clasificación por disponibilidad

- **Precalculado/local:** límites de cuenca y subcuencas, corredores publicados, puntos críticos, catálogo de assets y metadatos.
- **Persistido/en caché:** resultados identificados por `result_id`, preevaluación, estructura, mapas derivados, PDF y ZIP asociados.
- **Bajo demanda:** cinco señales, fragmentación, conectividad, rutas potenciales, ERI y estadísticas oficiales que requieren cálculo.
- **No calculado o bloqueado:** cualquier módulo sin resultado compatible; cobertura oficial 2021 cuando el asset configurado no existe o no tiene permisos; comparaciones oficiales sin armonización demostrada.

## Regresiones y desconexiones encontradas

1. La estructura visual actual usa una cabecera territorial fuera de la rejilla y seis pestañas, por lo que no reproduce la columna analítica continua del ZIP.
2. Fragmentación y conectividad aparecen como vistas separadas aunque responden a una misma pregunta estructural; esto fragmenta el relato.
3. Preevaluación, prioridad e informe están relegados al selector secundario y no forman un cierre interpretativo visible.
4. Los widgets se construyen con varias familias CSS y no comparten encabezado, fuente, año y explicación de manera uniforme.
5. Los botones PDF y Datos existen solo cuando hay un resultado y están dentro de procedencia; necesitan una ubicación semántica en la vista de informe.
6. Las capas oficiales pueden consultarse visualmente, pero no todas disponen de estadísticas conectadas. La interfaz debe distinguir claramente “capa disponible” de “resultado calculado”.

## Plan de corrección reproducible

1. Reorganizar la plantilla sin alterar endpoints ni motores.
2. Introducir cinco pestañas principales y alias de compatibilidad para URLs antiguas.
3. Normalizar widgets y explicaciones usando exclusivamente datos presentes en el resultado.
4. Sincronizar cada pestaña con un preset de capas reales y su leyenda, sin llamadas GEE automáticas.
5. Asegurar disposición responsive, ausencia de scroll horizontal e invalidación del tamaño de Leaflet.
6. Añadir pruebas focalizadas de navegación, acciones distintas, ausencia de datos demostrativos y estructura responsive.
