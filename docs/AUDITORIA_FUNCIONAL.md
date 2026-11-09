# Auditoría funcional de cierre local

Fecha: 2026-11-08. Rama local:
`feature/correctiva-evaluacion-ecologica-2023`. Esta auditoría no autoriza push,
merge ni despliegue.

## Resultado representativo comprobado

Se revisó en un navegador Chromium real la subcuenca **Qda. Bonita** mediante el
proyecto `geoportal-513817`. Resultado en caché:
`ba80bf90e3ae4aaea22968c9afcf3ed3`.

| Indicador | Valor observado |
|---|---:|
| Superficie analizada | 507.8993 ha |
| Índice territorial | 4.0 / 6.5 |
| Prioridad territorial | Alta |
| Prioridad de visita | Muy alta |
| Bosque oficial 2021 | 377.6973 ha (74.3646 %) |
| Parches | 6 |
| Componentes | 1 |
| Parches aislados | 0 |
| Conexiones | 9 |
| Contexto dentro de corredores | 330.6153 ha (65.0947 %) |

JRC TMF y Hansen aportaron señal; ESRI, GEDI y NDVI no aportaron señal en este
resultado. La ausencia de señal no significa ausencia de datos en el catálogo.

## Matriz de aceptación

| Función | Estado | Evidencia | Pendiente o limitación |
|---|---|---|---|
| Portada, panel y plataforma | Verificada | Rutas HTTP y navegador real | Ninguno relevante en escritorio |
| Tres columnas | Verificada | Captura `capturas/auditoria_cdp_resumen.png` | Repetir inspección visual en dispositivos físicos |
| Mapa centrado en resultado | Corregida y verificada | Escala de 500 m tras el análisis | La escala anterior quedaba en 10 km |
| Activación de capas | Verificada | JRC, Hansen, ESRI, NDVI, GEDI y ocho productos SINIA generaron tesela y leyenda; corredores apagado/encendido | Las capas estructurales requieren primero un resultado real |
| Pestañas de resultados | Verificada | Cuatro pestañas con contenido distinto y cero solicitudes analíticas al navegar | Ninguno |
| Gráficas e interpretación | Verificada | Valores reales recibidos por API y visibles en navegador | No constituyen validación temática de exactitud |
| Preevaluación territorial | Verificada | Resultado Qda. Bonita | Indicativa; requiere verificación de campo |
| Fragmentación 2021 | Verificada | 377.6973 ha, 6 parches | Depende del acceso al asset privado |
| Conectividad 2021 | Verificada | 1 componente, 0 aislados, 9 conexiones | Estructural, no funcional para especies |
| Corredores | Verificada | 330.6153 ha y 65.0947 %; control cartográfico probado | Contexto publicado, no corredor generado por el modelo |
| PDF real | Verificada | `capturas/auditoria_qda_bonita_informe.pdf`, 6 páginas, 49.902 bytes | Se genera desde caché; no persiste tras reinicio |
| Coincidencia PDF/panel | Verificada | 4.0/6.5, 377.70 ha, 6, 1, 0, 9, 330.62 ha y 65.09 % coinciden | Redondeos de presentación esperados |
| Consola JavaScript | Verificada | Sin excepciones ni respuestas HTTP >= 400 durante el recorrido | Revisar nuevamente en la versión que se despliegue |
| Comparación estructural 2021–2023 | Verificada en AOI pequeño | Resultado `d12f736827404ab798a0d7e9ce75592e`; dos escenarios EE y PDF de 5 páginas | Falta repetir en una subcuenca moderada antes de producción |
| ERI | Conservado | Motor y presentación separados | No se revalidó con Earth Engine en este cierre focalizado |
| Descarga ZIP/GeoJSON | Cubierta por contratos y flujo existente | API y pruebas | Repetir descarga manual en el candidato final |
| Móvil/responsive | Verificada en navegador automatizado | 1920, 1440, 1366, 1024, 536 y 375 px sin desbordamiento horizontal | Recomendada una revisión adicional en dispositivos físicos |
| Cloud Run | Preparado, no desplegado | Dockerfile, `requirements-web.txt`, guía de Fase 6 | Permisos de cuenta de servicio y prueba privada pendientes |

## Evidencia visual

- Resumen: `capturas/auditoria_cdp_resumen.png`.
- Dinámica: `capturas/auditoria_cdp_dinamica_bosque.png`.
- Conectividad: `capturas/auditoria_cdp_conectividad.png`.
- Corredores apagados/encendidos:
  `capturas/auditoria_cdp_corredores_apagados.png` y
  `capturas/auditoria_cdp_corredores_encendidos.png`.
- PDF: `capturas/auditoria_qda_bonita_informe.pdf` y sus páginas renderizadas.
- Comparación real 2021–2023:
  `capturas/validacion_comparacion_estructural_2021_2023.pdf` y cinco páginas PNG.
- Comparación en navegador y seis tamaños:
  `capturas/comparacion_2021_2023/auditoria_cdp_resultado.json` y capturas
  `auditoria_responsive_*`.

La comparación real acotada consultó ambos assets con `geoportal-513817`. Con 500 m
de distancia y sin filtro mínimo, ambos escenarios devolvieron 121.5838 ha, un parche,
un componente, un parche aislado y cero conexiones. El resultado fija
`comparable_for_causal_change=false` y `difference_metrics=null`; estos valores solo
describen el AOI pequeño de validación.

La auditoría ligera de capas produjo teselas reales para JRC, Hansen, ESRI, NDVI,
GEDI y los ocho productos SINIA. El producto detallado 2021 expone sus 33 códigos;
los códigos sin nombre institucional disponible se etiquetan como «sin documentación»
en vez de inventar una clase.

## Comparación con el repositorio original

La inspección del código confirmó equivalencia de las funciones principales:

- `metodologia_indice.py`: `clasificar_prioridad`, `calcular_prioridad_visita` y
  `calcular_indice_prioridad`;
- `bosque_conectividad.py`: `analizar_fragmentacion_conectividad`,
  `analizar_fragmentacion_geojson` y `_calcular_metricas_parches`;
- `corredores.py`: `analizar_interseccion_corredores` y
  `calcular_radio_contexto`.

La nueva API reorganiza la ejecución, el estado y la presentación, pero no cambia
estas fórmulas. La comparación 2021–2023 reutiliza el mismo motor con entradas
separadas y no modifica los resultados originales.

## Pruebas automatizadas del cierre

```text
node --check webapp/static/js/platform.js
python -m unittest test_fase_correctiva_ecologica.py test_web_api.py
                   test_web_frontend.py test_web_container_security.py
Pruebas focalizadas: 57 aprobadas después de añadir el contrato de 33 códigos.
Suite completa: 196 aprobadas y 3 omitidas por depender de integración opcional.
```

Las advertencias observadas corresponden a una deprecación futura de
`shapely.ops.transform`; no alteraron los resultados actuales.
El entorno aislado de Windows emitió una advertencia al limpiar un directorio temporal
después de terminar la suite; el proceso de pruebas ya había finalizado con estado OK.

## Auditoría de seguridad e historial

- La búsqueda en el árbol activo no encontró claves privadas, `private_key_id`,
  archivos de credenciales ni secretos incrustados.
- La configuración vigente utiliza exclusivamente `geoportal-513817`; no quedan
  referencias operativas al proyecto personal anterior.
- El historial conserva seis commits antiguos que mencionan el proyecto anterior
  (`9fc4d6c`, `3e45100`, `bbf3c85`, `5ba80b9`, `509c4e3` y `5ee4d83`). Son
  trazabilidad histórica, no configuración ejecutable. Deben revisarse nuevamente
  antes de hacer público el repositorio.
- No se encontraron marcadores `BEGIN PRIVATE KEY` ni `private_key_id` en el
  historial inspeccionado.
- `.gitignore` y `.dockerignore` excluyen credenciales locales; `.env.example`
  contiene únicamente nombres de variables y valores de ejemplo no sensibles.

## Problemas clasificados

## Matriz final de aceptación

| # | Requisito | Archivo o función | Prueba | Resultado | Evidencia | Pendiente |
|---:|---|---|---|---|---|---|
| 1 | Servidor y `/platform` | `webapp/main.py` | GET `/`, `/panel`, `/platform` | Comprobado: HTTP 200 en una sola instancia 8090 | Auditoría CDP | Ninguno local |
| 2 | Tres columnas y responsive | `webapp.css`, `platform.html` | 1920, 1440, 1366, 1024, 536 y 375 px | Comprobado sin overflow X | Capturas `auditoria_responsive_*` | Dispositivos físicos recomendados |
| 3 | Cuenca, subcuenca y dibujo | `territorio_local.py`, `platform.js` | Qda. Bonita y AOI dibujado | Comprobado | Panel preparado y comparación real | Ampliar recorrido manual a otra subcuenca |
| 4 | Switches, leyendas y opacidad | `run_layer_preview()`, `renderLayers()` | 13 fuentes/capas consultadas | Comprobado | Teselas y leyendas reales | Prueba manual combinada de todas sería ilegible y no se recomienda |
| 5 | Ocho assets oficiales | `catalogo_assets_sinia.py` | Metadatos y vistas ligeras | Comprobado con identidad local | 8 teselas listas; 2021 detallado con 33 códigos | ACL de Cloud Run |
| 6 | Cinco señales e índice | `evaluacion_ecologica.py`, `metodologia_indice.py` | AOI controlado y equivalencia de funciones | Comprobado | 2.0/6.5 en AOI pequeño; 4.0/6.5 en Qda. Bonita | Validación de campo fuera de alcance |
| 7 | Tres modos | Asistente de `platform.js` | Modal de cuatro pasos | Comprobado | ecological, fragmentation, connectivity; integral excluyente | Ninguno |
| 8 | Estructura 2021 | `analizar_estructura_cobertura()` | AOI pequeño y Qda. Bonita | Comprobado | 121.5838 ha/1 parche y 377.6973 ha/6 parches | Sensibilidad a escala moderada |
| 9 | Estructura 2023 | mismo motor, escenario `diagnostic_2023` | AOI pequeño | Comprobado | 121.5838 ha, 1 parche, 1 componente | Repetir en subcuenca moderada |
| 10 | Comparador 2021–2023 | `run_structural_comparison()` | API, navegador y PDF | Comprobado sin delta causal | `comparable_for_causal_change=false` | Homologación necesaria para transiciones |
| 11 | Corredores y rutas | `corredores.py`, motor estructural | Qda. Bonita y AOI pequeño | Comprobado | 22 polígonos, 14 puntos; intersecciones reales | No demuestra movimiento de fauna |
| 12 | Estadísticas SINIA | catálogos y coberturas 2021/2023 | Clases, NoData y superficie | Comprobado parcialmente | 2021/2023 calculados; ocho productos visuales | Estadística por clase de todos los históricos no se ejecuta al activar capa |
| 13 | Interpretación científica | renderizadores de resultados | Inspección CDP | Comprobado | Textos con número, fuente y cautela | Revisión editorial final |
| 14 | PDF verdadero | `build_technical_report()` | `%PDF`, 5/6 páginas renderizadas | Comprobado | PDFs en `docs/capturas` | Mapas del AOI mínimo son geométricamente simples |
| 15 | Descarga separada | `build_download()` y rutas Flask | Contratos y enlace en navegador | Comprobado | `download.zip` separado de `report.pdf` | Descarga manual final antes de publicar |
| 16 | Rendimiento/caché | `ResultCache` | Repetición y navegación por pestañas | Comprobado | 0 solicitudes analíticas al cambiar pestañas | Caché no persiste reinicios |
| 17 | Independencia y secretos | `gee_config.py`, ignore files | búsqueda de marcadores y rutas activas | Comprobado | Proyecto único vigente; sin claves detectadas | Auditar de nuevo antes del push |
| 18 | Documentación | README, metodología y `docs/` | Enlaces y contenido revisados | Comprobado | Catálogo, arquitectura, instalación y transferencia | Consolidar historia en una fase posterior |
| 19 | Pruebas y consola | suite Python, Node y CDP | 196 tests + 3 skip; consola | Comprobado | 0 respuestas >=400 y 0 excepciones JS | Deprecación Shapely no bloqueante |
| 20 | Comparación visual | `docs/capturas/` | Capturas reales mapa+panel+gráficas | Comprobado | escritorio y móvil renderizados | No sustituye prueba de usuario final |

### Bloqueantes para producción

1. Verificar permisos de la cuenta de servicio de Cloud Run sobre los assets privados.
2. Realizar la prueba privada de contenedor y concurrencia antes de abrir acceso.
3. Repetir la comparación estructural en una subcuenca moderada para evaluar tiempos y
   sensibilidad; la integración acotada ya está verificada.

### Importantes

1. Definir persistencia si los informes deben sobrevivir al reinicio del servidor.
2. Resolver la deprecación de Shapely en una fase sin cambios metodológicos.
3. Confirmar en dispositivos físicos el comportamiento ya verificado por emulación.

### Menores

1. Consolidar documentos históricos que aún describen fallos ya corregidos, sin
   borrar su valor de trazabilidad.

## Recomendación

El geoportal es un **candidato local funcional**, pero no debe declararse listo para
producción. La preevaluación, la estructura 2021, corredores, capas y PDF tienen
evidencia real. La comparación 2021–2023 fue verificada en un AOI pequeño y mantiene
los diagnósticos separados. Cloud Run y una prueba de escala moderada todavía
permanecen pendientes; el responsive no presentó desbordamiento en los seis tamaños.
