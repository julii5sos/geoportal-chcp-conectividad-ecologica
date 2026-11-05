# Auditoría científica de la cobertura del suelo atribuida a Sentinel-2

**Componente auditado:** capa del HTML original «Cobertura del suelo 2025 · Sentinel-2 · 7 clases»  
**Fecha de auditoría:** 5 de noviembre de 2026  
**Rama auditada:** `feature/interfaz-html-definitiva`  
**Alcance:** trazabilidad de datos, implementación, pruebas, validación y comparabilidad temporal.  
**Restricción aplicada:** esta auditoría no modifica los algoritmos de la Fase 3 ni la interfaz en curso.

## 1. Dictamen ejecutivo

La capa de siete clases que aparece en el HTML original **no es una clasificación propia de Sentinel-2**. Las siete etiquetas y sus píxeles proceden de `preparar_datos.py`, que declara expresamente que sus capas de cobertura son sintéticas. El código construye las clases mediante superficies aleatorias, filtros gaussianos, distancias y umbrales heurísticos; no utiliza imágenes Sentinel-2, muestras etiquetadas ni un clasificador entrenado.

El motor alternativo de Earth Engine sí contiene una cobertura anual real, pero esta procede de **Dynamic World V1**. Dynamic World es un producto externo derivado de Sentinel-2 y entrega nueve clases con probabilidades. `motor/gee.py:cobertura_anual()` calcula la moda anual de su banda `label` y la probabilidad media de `trees`; no crea ni valida una taxonomía local de siete clases. `bosque_anual()` reduce esa salida a una máscara binaria bosque/no bosque.

Por tanto, el nombre «Cobertura del suelo 2025 · Sentinel-2 · 7 clases» atribuye a Sentinel-2 un producto que el repositorio no genera científicamente. Hasta implementar y validar una clasificación local, la capa debe presentarse como **demostrativa** o sustituirse por una capa real conservando su nombre, taxonomía y metodología originales, por ejemplo «Dynamic World · cobertura 2025 · 9 clases».

No se encontró evidencia de muestras locales de entrenamiento o validación, separación entrenamiento/prueba, matriz de confusión, exactitud global, exactitud de usuario/productor ni exactitud por clase para las siete categorías. En consecuencia, no se reporta ninguna métrica de precisión.

## 2. Escala de clasificación utilizada en esta auditoría

| Estado | Criterio |
|---|---|
| **Implementado y verificado** | El código existe y hay evidencia versionada de una ejecución operativa real o una prueba reproducible del procedimiento. No implica por sí mismo validación temática local. |
| **Implementado sin validación científica** | El código existe, pero no hay validación local suficiente de la exactitud o de los supuestos científicos. |
| **Demostrativo** | Usa datos sintéticos, reglas de presentación o resultados simulados; no debe emplearse para decisiones. |
| **Pendiente** | No existe implementación comprobable en el repositorio. |

La palabra **verificado** se usa en sentido operativo. Una consulta exitosa a Earth Engine confirma que el flujo funciona, pero no demuestra que la clasificación sea exacta en la CHCP.

## 3. Procedencia real de las siete clases

### 3.1 Evidencia del generador

`fase4_referencia/html_original/preparar_datos.py` documenta en las líneas 11–17 que las capas de cobertura, pérdida, conectividad, núcleos y corredores son sintéticas. La salida se guarda como PNG, JavaScript y estadísticas del portal.

La taxonomía se define en `fase4_referencia/html_original/config.py:37–38` y se materializa en `preparar_datos.py:119–132`:

| Clase mostrada | Regla realmente utilizada | Insumos reales de Sentinel-2 | Estado |
|---|---|---:|---|
| Bosque maduro | Bosque sintético cuyo campo `Sx` supera el percentil 27 de los valores forestales | Ninguno | **Demostrativo** |
| Bosque secundario | Bosque sintético cuyo campo `Sx` es menor o igual al percentil 27 | Ninguno | **Demostrativo** |
| Manglar | Máscara costera sintética basada en distancia, lado Caribe, ruido y exclusión urbana | Ninguno | **Demostrativo** |
| Pastos | Clase predeterminada para tierra no forestal sintética | Ninguno | **Demostrativo** |
| Cultivos | Tierra no forestal sintética donde un campo aleatorio supera un umbral | Ninguno | **Demostrativo** |
| Urbano | Superficie urbana sintética combinada con ruido y un umbral | Ninguno | **Demostrativo** |
| Agua | Máscara de agua sintética del generador | Ninguno | **Demostrativo** |

La pérdida 2001–2025 también se simula con campos gaussianos y números aleatorios (`preparar_datos.py:105–117`). Después, `smooth_cls()` aplica un filtro de mediana para limpiar visualmente las clases (`preparar_datos.py:275–287`). Ese suavizado es cartográfico; no constituye entrenamiento ni validación.

El archivo `static/data/motor/motor.js` confirma que los artefactos versionados fueron generados con `"modo": "demo"`, a 90 m, el 27 de octubre de 2026. `demo_rasters.npz` se crea expresamente para el modo demostración (`preparar_datos.py:316–324`).

### 3.2 Conclusión sobre el origen

Las siete clases proceden de un **modelo gráfico sintético de demostración**. No existe una cadena de procedencia píxel a píxel hacia Sentinel-2 ni hacia otro producto observado. Las cifras derivadas de esos rásteres sirven para probar la interfaz, no para describir el territorio.

## 4. ¿Clasificación Sentinel-2 propia o Dynamic World?

### 4.1 Flujo de cobertura implementado en el HTML original

`fase4_referencia/html_original/motor/gee.py` implementa:

- `dynamic_world()` (`78–80`): consulta `GOOGLE/DYNAMICWORLD/V1`.
- `cobertura_anual()` (`83–88`): moda anual de `label` y media anual de la probabilidad `trees`.
- `bosque_anual()` (`91–94`): bosque si la clase modal es `trees` y la probabilidad media es al menos 0,5.
- `perdida_ganancia()` (`104–112`): transiciones binarias entre dos máscaras de bosque.

`motor/pipeline.py:55–74` descarga esas máscaras y solo conserva la clase Dynamic World del año final. No existe una función que entrene siete clases con bandas Sentinel-2 ni una remapee científicamente Dynamic World a las siete etiquetas del HTML.

Dynamic World es un producto de cobertura externo de 10 m, derivado de imágenes Sentinel-2 L1C, con nueve clases y probabilidades. La documentación oficial recomienda usar las probabilidades para filtrar predicciones inciertas. El repositorio no implementa esa taxonomía como siete clases; únicamente usa `trees` para bosque/no bosque.

**Clasificación:** `cobertura_anual()` y `bosque_anual()` están **implementados sin validación científica local**. Además, el propio encabezado de `motor/gee.py:13–15` advierte que ese módulo no pudo ejecutarse contra Earth Engine cuando fue escrito.

### 4.2 Otros usos de Sentinel-2 que no son una clasificación de cobertura

`motor/gee.py:157–184` usa `COPERNICUS/S2_SR_HARMONIZED` solo cuando existen parcelas de área basal. Construye una mediana anual, NDVI y un Random Forest de regresión para estimar área basal. Este procedimiento:

- no produce las siete clases;
- es condicional a parcelas suministradas externamente;
- filtra escenas por `CLOUDY_PIXEL_PERCENTAGE < 60`, pero no implementa una máscara de nubes y sombras a nivel de píxel;
- no incluye una partición de validación ni métricas de error en el repositorio.

`modelo_riesgo()` (`212–249`) entrena otro Random Forest para riesgo de pérdida, no para cobertura del suelo. Tampoco valida la taxonomía de siete clases.

Ambos componentes se clasifican como **implementados sin validación científica** para su propósito específico y **no aplicables** como evidencia de una clasificación Sentinel-2 de siete clases.

## 5. Pruebas reales, pruebas sintéticas y ausencia de validación temática

### 5.1 HTML original

| Evidencia | Qué comprueba | Qué no comprueba | Estado |
|---|---|---|---|
| `preparar_datos.py` y `motor/pipeline.py:insumos_demo()` | Que la interfaz y el motor pueden operar con rásteres plausibles | La existencia o exactitud de cobertura observada | **Demostrativo** |
| `static/data/motor/motor.js` | Artefacto completo de ejemplo en modo `demo` | Una ejecución real de Earth Engine | **Demostrativo** |
| `evaluacion/test_bosque_conectividad.py` | Geometría, fragmentos y red con datos controlados | Exactitud de la clasificación de cobertura | **Implementado y verificado** como prueba de software |
| `evaluacion/test_metodologia_indice.py` | Reglas y pesos de la preevaluación | Exactitud temática de una capa Sentinel-2 | **Implementado y verificado** como prueba de software |
| `motor/verificar.py` | Diseña una verificación en vivo con Dynamic World cuando hay EE | Validación local de clases o precisión | **Implementado sin validación científica** |

No se encontró un test que compare la capa de siete clases con observaciones de referencia. Tampoco se encontraron conjuntos de entrenamiento/validación locales. `static/data/motor/valido.tif` es una máscara de píxeles válidos del motor, no verdad-terreno.

### 5.2 Repositorio nuevo y Fase 3

El repositorio nuevo incorpora una verificación real documentada para **JRC TMF 2020–2025**, no para la capa Sentinel-2 de siete clases:

- `docs/VALIDACION_JRC_2020_2025.md` conserva el comando, área, fuente, parámetros y resultados de una ejecución de Earth Engine del 4 de noviembre de 2026.
- `test_analisis_temporal.py` usa geometrías sintéticas de áreas conocidas para probar superficies, transiciones, fragmentación, red y recorte.
- `test_analisis_temporal_ee.py` define dos pruebas de integración opcionales para JRC y ESRI 2020–2025.

En la reejecución de esta auditoría se instalaron las dependencias declaradas y se
habilitó explícitamente `RUN_EE_INTEGRATION=1` con un proyecto Earth Engine
autorizado. Las dos pruebas pasaron: JRC devolvió píxeles válidos para 2020 y 2025 y
ESRI confirmó ambas ediciones como una serie independiente. Además, el script
`scripts/validar_analisis_temporal.py` terminó correctamente para las dos fuentes en
la misma ventana de validación de la CHCP.

La ejecución JRC y ESRI verifica el funcionamiento y la trazabilidad del flujo
temporal; no constituye una evaluación independiente de la exactitud temática de
ninguno de los productos ni valida las siete clases del HTML.

## 6. Evidencia de entrenamiento y validación

### 6.1 Clasificador local de siete clases

| Elemento exigible | Evidencia encontrada | Clasificación |
|---|---|---|
| Definiciones operativas de clase | Solo etiquetas; no hay criterios observables formales para siete clases | **Pendiente** |
| Muestras etiquetadas locales | Ninguna | **Pendiente** |
| Diseño muestral probabilístico o estratificado | Ninguno | **Pendiente** |
| Algoritmo entrenado para siete clases | Ninguno | **Pendiente** |
| Separación entrenamiento/validación | Ninguna | **Pendiente** |
| Matriz de confusión | Ninguna | **Pendiente** |
| Exactitud global | Ninguna | **Pendiente** |
| Exactitud por clase | Ninguna | **Pendiente** |
| Incertidumbre o intervalo de confianza | Ninguno | **Pendiente** |
| Validación temporal entre años | Ninguna | **Pendiente** |

Dynamic World sí posee entrenamiento y validación publicados por sus productores. Esa evidencia respalda el producto global Dynamic World en su taxonomía original; no puede transferirse automáticamente a una taxonomía local distinta ni presentarse como validación de las siete clases del portal.

## 7. Bosque maduro, bosque secundario y manglar

### 7.1 Bosque maduro frente a bosque secundario

Con los insumos y reglas actuales **no es científicamente válido** afirmar que se distinguen estas dos clases:

- Dynamic World contiene una única clase `trees`; no codifica edad sucesional.
- Una diferencia espectral de un solo año no identifica por sí sola edad, historia de perturbación o estado sucesional.
- El percentil sintético de `Sx` usado por el HTML no tiene relación calibrada con edad, estructura o historia del bosque.
- No existen parcelas, cronosecuencias, interpretación experta ni validación local por clase.

JRC TMF sí distingue estados de bosque tropical en su producto temporal —incluidos bosque no perturbado, degradado y regeneración posterior a deforestación—, pero esas clases deben conservar sus nombres y definiciones JRC. No deben renombrarse automáticamente como «maduro» y «secundario» sin una correspondencia documentada y validada.

### 7.2 Manglar

La regla costera sintética no demuestra manglar. Dynamic World puede asignar vegetación arbórea o vegetación inundada, pero el repositorio no integra una capa oficial de manglares, régimen de inundación/mareas, salinidad, topografía costera ni muestras locales para una clase específica.

**Conclusión:** la separación local de bosque maduro, secundario y manglar está **pendiente**. Como solución inmediata y honesta, se deben mostrar las taxonomías originales de los productos fuente y evitar equivalencias no validadas.

## 8. Comparabilidad anual, nubosidad, resolución y variabilidad temporal

### 8.1 Lo que sí controla el código original

- Usa la misma colección Dynamic World para cada año.
- Calcula la moda de `label` y la media de `trees` dentro de cada año calendario.
- Aplica un umbral fijo de 0,5 para la máscara de bosque.
- El motor general reproyecta sus salidas a UTM 17N y 30 m (`motor/gee.py:10–11`), aunque Dynamic World es de 10 m.

Esto aporta consistencia procedimental, pero no basta para demostrar comparabilidad temática anual.

### 8.2 Controles faltantes

| Riesgo | Situación actual | Estado |
|---|---|---|
| Nubosidad y sombras | Dynamic World enmascara nubes en el producto fuente, pero el compuesto anual no controla cantidad mínima de observaciones claras por píxel | **Pendiente** |
| Confianza de clase | Se usa la moda y solo la media de `trees`; no se filtra la probabilidad de la clase ganadora ni se informa incertidumbre | **Pendiente** |
| Estacionalidad | Se mezcla todo el año calendario sin ventana fenológica común ni análisis de sensibilidad | **Pendiente** |
| Año incompleto | No hay verificación de que el año final tenga cobertura temporal completa antes de compararlo | **Pendiente** |
| Resolución | Dynamic World 10 m se lleva a una grilla de 30 m en el motor; no se documenta explícitamente el método de remuestreo de clases | **Implementado sin validación científica** |
| Variación de observaciones | No se entrega mapa de conteo de observaciones ni cobertura válida por año | **Pendiente** |
| Cambio de versión | No existe una prueba de estabilidad entre versiones del producto | **Pendiente** |

La documentación oficial de Dynamic World indica que cada predicción corresponde a una adquisición Sentinel-2 y que las clases tienen probabilidades. También recomienda umbralizar la probabilidad de la predicción principal. Para una comparación anual reproducible se debe conservar la versión, cuantificar observaciones válidas, aplicar reglas de confianza y documentar el tratamiento de píxeles sin evidencia suficiente.

## 9. Referencias a Landsat antes de 2015

`templates/herramienta.html:79` afirma que «los años anteriores a 2015 se completan con Landsat». No se encontró una implementación que produzca una clasificación anual de las mismas siete clases a partir de Landsat ni una armonización Sentinel-2/Landsat.

Lo que sí existe es `motor/gee.py:hansen()`, que consulta Hansen Global Forest Change, un producto basado en Landsat para cobertura arbórea 2000 y año de pérdida 2001–2025. `METODOLOGIA.md:74–76` recomienda usar Hansen antes de Dynamic World. Hansen no equivale a una clasificación anual simétrica de siete clases ni rellena por sí mismo una serie de cobertura comparable.

**Clasificación:** la clasificación anual Landsat anterior a 2015 es **pendiente**. La referencia del HTML es una propuesta o afirmación no respaldada por código implementado.

## 10. Procedimientos demostrativos ya reemplazados en el repositorio nuevo

La Fase 3 reemplaza la comparación temporal sintética de bosque, no la clasificación general de siete clases.

| Función nueva | Reemplazo efectivo | Evidencia | Estado |
|---|---|---|---|
| `analisis_temporal.py:construir_cobertura_bosque_ee()` | Recupera máscaras reales bosque/no bosque por año desde JRC TMF o ESRI | Reglas separadas, años válidos y metadatos de fuente | **Implementado y verificado** para JRC de forma operativa; ESRI **implementado sin validación científica local** |
| `recuperar_cobertura_geojson_ee()` | Sustituye la cobertura sintética por componentes vectorizados de Earth Engine | Usa resolución nativa y área activa | **Implementado** |
| `analizar_comparacion_geojson()` | Recalcula independientemente fragmentación y conectividad para ambos años | Pruebas sintéticas de geometría conocida | **Implementado y verificado** como motor geométrico |
| `ejecutar_analisis_temporal_ee()` | Orquesta recuperación real y recálculo completo | Ejecución JRC 2020–2025 documentada | **Implementado y verificado** operativamente |
| `test_analisis_temporal.py` | Prueba áreas, parches, transiciones, red y recorte | Geometrías sintéticas con resultados conocidos | **Implementado y verificado** como prueba de software |
| `test_analisis_temporal_ee.py` | Comprueba existencia y lectura de JRC/ESRI con credenciales | Ambas pruebas pasaron en esta auditoría; no miden exactitud temática | **Implementado y verificado operativamente** |
| Clasificador Sentinel-2 local de siete clases | Ninguno | No existe código ni datos | **Pendiente** |

`analisis_temporal.py` mantiene correctamente separadas las metodologías:

- JRC TMF 1990–2025, 30 m: clases 1, 2 y 4 como bosque dentro del dominio TMF.
- ESRI anual 2017–2025, 10 m: clase 2 `Trees` como cobertura arbórea.

El código impide sustituir años inexistentes y conserva parámetros equivalentes entre períodos. Esto es una mejora científica frente a la demostración, pero no autoriza a etiquetar sus resultados como las siete clases Sentinel-2 del HTML.

## 11. Matriz consolidada de hallazgos

| Componente | Clasificación | Hallazgo principal |
|---|---|---|
| Siete clases de `preparar_datos.py` | **Demostrativo** | Clases creadas con heurísticas y aleatoriedad |
| PNG y estadísticas estáticas de cobertura | **Demostrativo** | Artefactos derivados del generador sintético |
| Dynamic World anual del HTML | **Implementado sin validación científica** | Producto real externo, nueve clases; agregado anual sin validación local |
| Máscara bosque/no bosque Dynamic World | **Implementado sin validación científica** | Regla fija `trees` + probabilidad media ≥ 0,5 |
| Regresión Sentinel-2 de área basal | **Implementado sin validación científica** | Condicional; no clasifica cobertura ni presenta evaluación independiente |
| Random Forest de riesgo | **Implementado sin validación científica** | Predice riesgo, no siete clases; sin evaluación almacenada |
| Entrenamiento local de siete clases | **Pendiente** | No existe |
| Validación local de siete clases | **Pendiente** | No existe |
| Separación maduro/secundario/manglar | **Pendiente** | No soportada por los insumos/reglas actuales |
| Clasificación Landsat pre-2015 | **Pendiente** | Solo existe Hansen; no hay serie comparable de siete clases |
| Motor temporal JRC de Fase 3 | **Implementado y verificado** | Ejecución real JRC 2020–2025 documentada; no es validación temática local |
| Motor temporal ESRI de Fase 3 | **Implementado y verificado operativamente, sin validación temática local** | Ruta real, prueba Earth Engine y comparación 2020–2025 ejecutadas; falta evidencia local de exactitud |
| Fragmentación/conectividad con geometrías conocidas | **Implementado y verificado** | Pruebas de software reproducibles, independientes de la clasificación |

## 12. Riesgos

1. **Atribución incorrecta:** presentar el ráster sintético como Sentinel-2 puede inducir a creer que existe una clasificación observada y validada.
2. **Confusión taxonómica:** renombrar `trees` o estados JRC como maduro/secundario/manglar mezcla definiciones no equivalentes.
3. **Falsa precisión:** las hectáreas calculadas sobre clases sintéticas parecen cuantitativas aunque no representan observaciones.
4. **Cambios espurios:** diferencias anuales pueden reflejar nubes, estacionalidad, observaciones desiguales o incertidumbre de clase.
5. **Mezcla de resolución:** comparar o combinar directamente productos de 10 m y 30 m sin una regla documentada altera parches, bordes y conectividad.
6. **Transferencia indebida de validación:** la validación global de Dynamic World o JRC no sustituye una evaluación local de la CHCP ni valida una taxonomía modificada.
7. **Landsat no implementado:** la afirmación sobre años anteriores a 2015 puede llevar al usuario a seleccionar períodos que el sistema no calcula de forma comparable.

## 13. Plan de corrección reproducible

### Etapa 0 — corrección inmediata de comunicación, sin cambiar algoritmos

1. Retirar o marcar como demostrativa la capa «Sentinel-2 · 7 clases».
2. Si se expone Dynamic World, usar su nombre, nueve clases, resolución, período y leyenda originales.
3. Mostrar por capa: productor, asset, versión, año, resolución, método de composición y condición de validación.
4. Mantener JRC y ESRI como análisis separados; no mezclar superficies ni cambios entre fuentes.
5. Eliminar de la documentación la afirmación Landsat pre-2015 hasta que exista una implementación armonizada.

### Etapa 1 — producto real inmediato, sin clasificador local

1. Crear una función explícita `dynamic_world_anual()` separada del motor de siete clases.
2. Definir una regla reproducible de composición anual basada en probabilidades, no solo en la moda de etiquetas.
3. Generar por año: conteo de observaciones válidas, probabilidad de la clase ganadora y máscara de insuficiencia de datos.
4. Bloquear años incompletos o identificarlos claramente.
5. Mantener 10 m para visualización; si las métricas se calculan a 30 m, declarar el método de agregación y realizar análisis de sensibilidad.
6. Añadir pruebas de invariantes: mismas fechas, versión, resolución, AOI y regla de composición para ambos años.

Esta etapa permitiría mostrar Dynamic World de forma honesta, pero no produciría bosque maduro/secundario/manglar.

### Etapa 2 — si se decide construir una clasificación local de siete clases

1. Aprobar definiciones observables y mutuamente excluyentes de cada clase.
2. Diseñar un muestreo estratificado espacial y temporal independiente para entrenamiento y validación.
3. Reunir referencias locales: parcelas/interpretación experta, inventarios forestales, cartografía oficial de manglar y series históricas de perturbación.
4. Construir predictores con series Sentinel-2 en ventanas fenológicas comparables; añadir Sentinel-1, topografía, hidrología, distancia costera e historia JRC/Hansen cuando esté científicamente justificado.
5. Separar unidades espaciales de entrenamiento y prueba para evitar fuga espacial.
6. Entrenar algoritmos candidatos dentro de un protocolo versionado y reproducible.
7. Evaluar con una matriz de confusión independiente, exactitud de usuario y productor por clase, intervalos de confianza y análisis de errores espaciales.
8. Publicar también probabilidad/incertidumbre y una clase «sin evidencia suficiente».
9. Validar específicamente la transferencia entre años antes de denominar la serie comparable.

No se debe fijar una meta numérica de exactitud antes de definir el uso, las clases y el diseño de validación.

### Etapa 3 — serie Landsat/Sentinel armonizada, solo si es necesaria

1. Definir un período común y una taxonomía que ambos sensores puedan observar.
2. Construir composiciones Landsat Collection 2 y Sentinel-2 con ventanas temporales equivalentes y máscaras de calidad.
3. Calibrar diferencias de sensor y resolución con años de solapamiento.
4. Validar por sensor, año y clase con muestras independientes.
5. Publicar la incertidumbre del cambio y prohibir comparaciones donde la evidencia sea insuficiente.

Hasta completar esta etapa, Hansen debe describirse como historial de pérdida de cobertura arbórea, no como relleno de una clasificación anual de siete clases.

## 14. Comandos de reproducción

### Pruebas locales del motor temporal

```powershell
python -m unittest test_analisis_temporal -v
```

### Pruebas opcionales con Earth Engine

```powershell
$env:RUN_EE_INTEGRATION="1"
$env:EE_PROJECT="SU_PROYECTO_AUTORIZADO"
python -m unittest test_analisis_temporal_ee -v
```

### Ejecución real documentada de JRC

```powershell
python scripts/validar_analisis_temporal.py `
  --project SU_PROYECTO_AUTORIZADO `
  --fuente jrc_tmf `
  --inicial 2020 `
  --final 2025 `
  --distancia 500 `
  --area-minima 0.1
```

### Búsqueda de evidencia de validación local

```powershell
rg -n "errorMatrix|confusionMatrix|accuracy|muestras|sampleRegions|train" .
```

## 15. Criterios de aceptación para cerrar la corrección

- Ninguna capa sintética se presenta como observación Sentinel-2.
- Cada capa declara fuente, versión, taxonomía, resolución, período y calidad.
- Las siete clases solo se publican si existe código reproducible, muestras y validación independiente.
- Los años comparados usan la misma metodología y reportan suficiencia de observaciones e incertidumbre.
- JRC, ESRI, Dynamic World, Hansen y una eventual clasificación local permanecen separados.
- El cálculo de fragmentación/conectividad conserva la fuente y resolución en sus metadatos.
- Las referencias a Landsat coinciden con código ejecutable y pruebas verificables.

## 16. Referencias primarias consultadas

- Google Earth Engine Data Catalog. **Dynamic World V1**: `GOOGLE/DYNAMICWORLD/V1`. https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- Brown, C. F. et al. (2022). **Dynamic World, Near real-time global 10 m land use land cover mapping**. *Scientific Data*, 9, 251. https://doi.org/10.1038/s41597-022-01307-4
- Google Earth Engine Data Catalog. **Harmonized Sentinel-2 MSI Level-2A**: `COPERNICUS/S2_SR_HARMONIZED`. https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- JRC Forest Observations. **Tropical Moist Forest GEE tutorial**. https://forobs.jrc.ec.europa.eu/TMF/resources/tutorial/gee

## 17. Archivos principales auditados

### HTML original

- `fase4_referencia/html_original/preparar_datos.py`
- `fase4_referencia/html_original/config.py`
- `fase4_referencia/html_original/motor/gee.py`
- `fase4_referencia/html_original/motor/pipeline.py`
- `fase4_referencia/html_original/motor/verificar.py`
- `fase4_referencia/html_original/METODOLOGIA.md`
- `fase4_referencia/html_original/templates/herramienta.html`
- `fase4_referencia/html_original/static/data/motor/motor.js`
- `fase4_referencia/html_original/evaluacion/test_bosque_conectividad.py`
- `fase4_referencia/html_original/evaluacion/test_metodologia_indice.py`

### Repositorio nuevo

- `analisis_temporal.py`
- `bosque_conectividad.py`
- `geoportal_catalogo.py`
- `app_temporal.py`
- `test_analisis_temporal.py`
- `test_analisis_temporal_ee.py`
- `docs/METODOLOGIA_ANALISIS_TEMPORAL.md`
- `docs/VALIDACION_JRC_2020_2025.md`

