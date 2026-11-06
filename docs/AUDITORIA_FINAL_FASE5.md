# Auditoría final del Geoportal CHCP 2.0

**Fecha:** 5 de noviembre de 2026  
**Repositorio:** `julii5sos/geoportal-chcp-conectividad-ecologica`  
**Rama auditada:** `feature/interfaz-html-definitiva`  
**Commit base:** `820a7d5bfc0c9b7cd2308fc15b7476561067cc62`  
**Restricción:** sin merge, push, despliegue ni modificación de `main`.

## 1. Dictamen ejecutivo

El geoportal reúne una interfaz coherente con el HTML de referencia, un motor temporal
real para JRC TMF y ESRI, métricas reproducibles de fragmentación/conectividad, ERI
separado y descargas metodológicas. La suite completa es estable con Streamlit 1.63.0:
99 pruebas pasan localmente —dos quedan omitidas en la corrida sin credenciales— y
esas dos integraciones Earth Engine pasan al habilitarlas expresamente.

La recomendación es **preparar una versión candidata interna**, no publicar todavía
como producto final. Antes de producción deben cerrarse la validación visual móvil del
flujo completo, las pruebas de carga/concurrencia y la comunicación pública de las
limitaciones científicas. La clasificación Sentinel-2 de siete clases del prototipo
HTML no es un producto científico: es sintética y no se utiliza como evidencia válida.

## 2. Auditoría visual

### Comparación concreta

| Elemento | HTML/video original | Aplicación auditada | Evaluación |
|---|---|---|---|
| Encabezado | Dos niveles, azul, logo, utilidades y navegación horizontal | Dos niveles, misma familia cromática, navegación y CTA | Alta fidelidad |
| Tipografía | DM Sans | DM Sans importada; `system-ui` como respaldo | Coincide cuando la fuente remota está disponible |
| Portada | Hero azul, identidad CHCP y entrada al panel | Hero equivalente, CTA de mapa/análisis y resumen territorial real | Alta fidelidad |
| Explorador | Panel izquierdo, mapa dominante y panel de resultados | Misma distribución en la interfaz temporal | Alta fidelidad en escritorio |
| Pestañas | Capas, Filtros, Mapas base | Capas, Filtros, Mapas base en `app_temporal.py` | Coincide |
| Capas | Grupos desplegables e interruptores | Límites, cobertura, fragmentación, conectividad y ERI | Funcional; no todos los productos se habilitan sin EE |
| Asistente | Modal con cuatro pasos | Tipo, área, criterios y revisión; conserva estado | Coincide en estructura y comportamiento |
| Resultados | Panel derecho junto al mapa | Área/período/fuente, métricas, barras, transiciones y descargas | Coincide; el contenido es real, no el demo del HTML |
| Responsive | Menú compacto y panel adaptado | Portada validada a 375 px y reglas a 900/640 px | Parcial: falta repetir el flujo científico completo en móvil |

### Hallazgo visual corregido

Streamlit conserva el estado colapsado del panel lateral. El CSS reducía el encabezado
nativo a cero y con ello dejaba el botón de reapertura con tamaño 0×0. Se añadió una
posición fija, 44×44 px, foco y contraste propios para
`stExpandSidebarButton`. La corrección cuenta con una prueba de regresión.

### Capturas reales

| Vista | Referencia | Aplicación |
|---|---|---|
| Panel/plataforma | [video-plataforma.jpg](../artifacts/reference/video-plataforma.jpg) | [fase5-explorar-1440.png](../artifacts/screenshots/fase5-explorar-1440.png) |
| Asistente | [video-asistente.jpg](../artifacts/reference/video-asistente.jpg) | [fase4-asistente-final-real.png](../artifacts/screenshots/fase4-asistente-final-real.png) |
| Resultados | [video-resultados.jpg](../artifacts/reference/video-resultados.jpg) | [fase4-resultados-reales-miraflores.png](../artifacts/screenshots/fase4-resultados-reales-miraflores.png) |
| Portada móvil | — | [fase4-inicio-375.png](../artifacts/screenshots/fase4-inicio-375.png) |
| Portada escritorio | [video-panel-inicio.jpg](../artifacts/reference/video-panel-inicio.jpg) | [fase5-inicio-desktop-full.png](../artifacts/screenshots/fase5-inicio-desktop-full.png) |

La captura `fase5-explorar-1440.png` documenta el defecto del panel colapsado antes de
la corrección. No se presenta como evidencia de la corrección ya aplicada.

## 3. Uso y cobertura del suelo

El informe detallado está en
[AUDITORIA_COBERTURA_SENTINEL2.md](AUDITORIA_COBERTURA_SENTINEL2.md).

Conclusiones principales:

- la capa «Sentinel-2 · 7 clases» del prototipo original fue generada con superficies
  sintéticas en `preparar_datos.py`;
- no existe un clasificador local entrenado y validado para esas siete clases;
- el flujo original real usa Dynamic World, producto derivado de Sentinel-2, con nueve
  clases; no es una clasificación propia del proyecto;
- no hay evidencia de matriz de confusión, exactitud global o exactitud por clase;
- bosque maduro, bosque secundario y manglar no pueden publicarse como clases locales
  validadas con los insumos actuales;
- la Fase 3 sustituye el demo para análisis binario con JRC y ESRI reales, manteniendo
  metodologías y resoluciones separadas.

## 4. Fragmentación y conectividad

El informe detallado está en
[VALIDACION_FRAGMENTACION_CONECTIVIDAD.md](VALIDACION_FRAGMENTACION_CONECTIVIDAD.md).

El motor recorta la cobertura, identifica componentes con ocho vecinos, filtra por
área mínima, calcula métricas en `EPSG:8857` y construye una red por distancia entre
bordes. Las pruebas sintéticas cubren parches conocidos, aislamiento, componentes,
contexto exterior, geometrías compuestas y recorte. La comparación temporal usa el
mismo AOI y los mismos parámetros en ambos años.

Limitaciones principales: efecto de borde, umbral no específico de especie y distancia
aproximada en una proyección equal-area. El resultado es conectividad estructural
potencial, no funcional.

## 5. ERI

El informe detallado está en [VERIFICACION_ERI.md](VERIFICACION_ERI.md).

Los pesos 35/25/20/20 se conservan, suman uno, cada componente se limita a [0,1] y
las cinco clases cubren todo el intervalo. Las pruebas confirman fronteras, promedio
ponderado, componente limitante y separación del índice territorial. El ERI sigue
siendo complementario, indicativo y no anual.

## 6. Recorrido de usuario auditado

| Paso | Resultado |
|---|---|
| Abrir el geoportal | Correcto en servidor local |
| Activar capas | Correcto; controles reales y sin resultados ficticios |
| Dibujar polígono | Herramienta disponible; el recorte a CHCP está probado automáticamente |
| Abrir asistente | Correcto; modal de cuatro pasos |
| Seleccionar análisis integral | Correcto; cubre cobertura, fragmentación y conectividad |
| Elegir JRC 2020–2025 | Correcto; años válidos y parámetros equivalentes |
| Ejecutar | Correcto con credenciales Earth Engine |
| Consultar mapas/estadísticas/gráficos | Correcto; captura real de Miraflores disponible |
| Revisar ERI | Correcto y separado del temporal |
| Descargar | Generación ZIP/GeoJSON/estadísticas/metadatos cubierta por código y pruebas |
| Repetir con ESRI | Correcto en prueba y validación de Earth Engine 2020–2025 |
| Escritorio | Validado visualmente |
| Móvil | Portada validada; flujo completo de resultados pendiente de repetición |

No se utilizaron cifras del HTML sintético como evidencia. Las cifras JRC y ESRI del
informe científico proceden de consultas actuales a Earth Engine.

## 7. Pruebas

### Suite completa

Con Streamlit 1.63.0:

```text
Ran 99 tests in 7.393s
OK (skipped=2)
```

Las dos omitidas requieren `RUN_EE_INTEGRATION=1`. En ejecución separada con proyecto
autorizado:

```text
Ran 2 tests in 4.350s
OK
```

También finalizaron dos ejecuciones completas del script de validación para JRC y ESRI.

### Compatibilidad de Streamlit

- Streamlit 1.66.1: las cinco pruebas `AppTest` no terminan.
- Streamlit 1.63.0: las 22 pruebas de los módulos de interfaz terminan en 3,836 s.
- Corrección: `requirements.txt` fija `streamlit==1.63.0`.

Las advertencias de `shapely.ops.transform()` son deprecaciones, no fallos; se registran
como deuda técnica.

## 8. Preparación para publicación

### Dependencias y secretos

- Dependencias declaradas y versión Streamlit compatible fijada.
- `.streamlit/secrets.toml`, `.env`, claves y credenciales no están versionados.
- El README usa únicamente marcadores de ejemplo para la cuenta de servicio.
- `GEE_SERVICE_ACCOUNT_JSON` y `GEE_PROJECT_ID` son el mecanismo previsto para
  Community Cloud; los alias anteriores se aceptan solo durante la migración y las
  credenciales locales solo se usan en desarrollo.
- `app.py` es el punto de entrada y enruta `Comparar` hacia `app_temporal.py`.

### Rendimiento y límites

- Caché temporal: TTL 3.600 s, hasta 12 entradas.
- Earth Engine vectoriza a resolución nativa con `maxPixels=1e9`, `tileScale=4` y sin
  `bestEffort` en la comparación científica.
- Redes mayores de 250 nodos aproximan intermediación con una muestra reproducible de
  hasta 64 nodos.
- Áreas grandes y parche mínimo muy pequeño pueden producir demasiados polígonos,
  exceder memoria/tiempo de Streamlit o consumir cuota de Earth Engine.
- Falta una prueba formal de concurrencia y una cuota por sesión/usuario.

### Manejo de errores

La interfaz no inventa resultados cuando Earth Engine no está disponible; deshabilita
los productos satelitales y muestra una explicación operativa. El asistente captura y
presenta los fallos de ejecución. Para producción conviene añadir telemetría sin datos
sensibles y mensajes específicos para cuota, timeout y permisos.

## 9. Problemas por gravedad

### Críticos

Ninguno abierto en el motor auditado.

### Altos

1. **Validación temática ausente para siete clases Sentinel-2.** No publicar esa capa
   como resultado observado; el portal actual debe mantenerla fuera del flujo real.
2. **Validación pública incompleta.** JRC/ESRI funcionan, pero no existe evaluación
   independiente de exactitud en la CHCP.
3. **Carga/concurrencia sin validar.** Antes de acceso público simultáneo, medir cuotas,
   memoria, tiempo y caché con AOI pequeño, subcuenca y cuenca completa.

### Medios

1. Flujo completo móvil pendiente de repetición visual.
2. Distancias en `EPSG:8857` requieren sensibilidad frente a una proyección local.
3. El efecto del límite puede aumentar aislamiento aparente.
4. Umbral de conectividad no corresponde a una especie concreta.
5. DM Sans depende de Google Fonts; existe respaldo tipográfico, pero no identidad
   exacta sin conexión.

### Bajos

1. Deprecaciones de Shapely pendientes de migración.
2. La captura posterior de la corrección del botón lateral no pudo repetirse en esta
   sesión; la regla y su prueba sí están incorporadas.

## 10. Correcciones implementadas durante la auditoría

1. Botón visible y accesible para reabrir el panel lateral colapsado.
2. Prueba de regresión de tamaño/posición del botón.
3. Fijación de Streamlit 1.63.0 tras comprobar la incompatibilidad de 1.66.1.
4. Actualización de la auditoría Sentinel-2 con las pruebas Earth Engine reales.
5. Informes separados de fragmentación/conectividad y ERI.
6. Exclusión de dependencias temporales de auditoría mediante `.gitignore`.

## 11. Recomendación

**Apto para una versión candidata interna y controlada; no apto aún para producción
pública.** El siguiente hito debe exigir: prueba móvil completa, prueba de carga,
revisión de cuotas Earth Engine, confirmación de secretos en un entorno de ensayo y
aceptación explícita de las limitaciones científicas. La publicación debe conservar
JRC y ESRI separados, excluir la capa sintética de siete clases y presentar el ERI y la
conectividad como resultados indicativos.
