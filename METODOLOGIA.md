# Metodología del índice operativo de prioridad

**Versión del método:** MT-2026.7-DIAGNOSTICO-INTEGRADO

**Versión de implementación auditada:** UX-0.5.0-DIAGNOSTICO-INTEGRADO

## Finalidad y alcance

El índice organiza áreas para revisión posterior mediante señales satelitales
complementarias. No representa una probabilidad de deforestación, no identifica por
sí solo la causa de un cambio y no constituye validación de campo, certificación ni
determinación de cumplimiento EUDR.

## Fuentes integradas

| Fuente | Resolución de trabajo | Uso |
|---|---:|---|
| JRC Tropical Moist Forest 2025 | 30 m | Estado anual de bosque, degradación y deforestación |
| Hansen Global Forest Change 2025 | 30 m | Pérdida anual de cobertura arbórea |
| ESRI Land Use/Land Cover | 10 m | Transición de la clase árboles a otra cobertura |
| Altura de dosel GEDI / OpenForis | 100 m | Contexto estructural y cobertura válida |
| Sentinel-2 SR Harmonized | 10 m; resumen a 20 m | NDVI y disminución significativa del vigor vegetal |
| Corredores de Almanaque Azul, versión publicada 2024.05 | Vector | Valor estratégico y ubicación respecto a corredores |
| SINIA–MiAMBIENTE, Bosque y otros usos 2021 | Vector aportado | Fragmentación, red de parches y foco espacial de la visita |

Cada producto se procesa en su propia proyección y resolución. Las superficies se
calculan dentro del área seleccionada y se integran como evidencia por fuente para
el índice. Solo el mapa de coincidencia espacial descrito más adelante estandariza
JRC, Hansen y ESRI en una malla común.

## Períodos fijos y controles visuales

Para que todas las áreas sean comparables, el cálculo usa períodos fijos:

- JRC Tropical Moist Forest: estado forestal 2025. La señal mide las clases de
  degradación y deforestación de la banda `Dec2025`; no resta 2020 de 2025.
- Hansen Global Forest Change: edición 2025 y pérdidas 2021-2025, posteriores al
  corte de referencia del 31/12/2020.
- ESRI Land Use/Land Cover: transición 2017-2024, porque 2024 es la última
  anualidad disponible en la serie utilizada.
- GEDI: producto estructural configurado en la metodología.
- NDVI: comparación fija 2020-2025; la disminución significativa puede aportar 0.5 al índice.

El valor inicial 2020 del comparador JRC corresponde al año del corte de referencia
EUDR y 2025 al estado más reciente del producto; ese barrido es exclusivamente
visual. En ESRI se muestran 2017 y 2024 por ser los extremos de la serie utilizada.

Los años que el usuario selecciona modifican únicamente los mapas interactivos y
las imágenes cartográficas. La consulta de una capa anual y los comparadores de dos
años se presentan como opciones separadas. Ninguna cambia los períodos fijos usados
para calcular señales, puntaje o prioridad.

Para JRC TMF se calculan las seis clases anuales: bosque estable, degradación,
deforestación, recuperación, agua y otra cobertura. Las seis se muestran en las
estadísticas; solo degradación y deforestación pueden activar la señal de deterioro.

## Activación de señales

### JRC TMF

La señal se activa cuando se cumple al menos una condición:

- deforestación ≥ 0.5 ha;
- deforestación ≥ 1% del área;
- degradación ≥ 2.0 ha;
- degradación ≥ 5% del área.

Los criterios absoluto y relativo conservan sensibilidad en áreas de tamaños
diferentes. La degradación utiliza valores más conservadores porque puede ser
gradual y presentar mayor ambigüedad espectral.

### Hansen Global Forest Change

La señal se activa con pérdida posterior al 31/12/2020 ≥ 0.18 ha. Este valor
equivale aproximadamente a dos píxeles de 30 m, por lo que evita que un único píxel
aislado determine el resultado y mantiene sensibilidad a eventos pequeños.

### ESRI Land Use/Land Cover

La señal se activa únicamente cuando se cumplen simultáneamente:

- salida de la clase árboles ≥ 0.10 ha; y
- salida de la clase árboles ≥ 5% del área.

A 10 m, 0.10 ha representa diez píxeles. Exigir extensión y proporción reduce
transiciones aisladas por variabilidad de clasificación. Esta regla y el peso 1.5
impiden que ESRI domine a los productos forestales especializados.

### GEDI

La señal contextual se activa únicamente cuando:

- al menos 20% del área tiene datos válidos;
- la altura media del dosel es menor de 8 m; y
- la línea base arbórea cubre al menos 10% del área.

La combinación evita interpretar dosel bajo en zonas sin cobertura arbórea previa o
con disponibilidad espacial insuficiente.

### NDVI de Sentinel-2

Se calcula como `(B8 - B4) / (B8 + B4)` sobre compuestos anuales con máscara SCL.
El diagnóstico compara 2020 con 2025. La señal se activa cuando el NDVI disminuye
al menos 0.15 desde píxeles con vigor inicial mayor o igual a 0.4, la superficie
afectada alcanza simultáneamente 0.12 ha —tres celdas del resumen a 20 m— y 5% del área, y existen datos válidos en
al menos 70% del territorio evaluado. El aporte máximo es 0.5.

La regla es corroborativa: NDVI también puede responder a estacionalidad, humedad,
cultivos, pastizales, nubes y sombras. Por ello recibe el menor peso y no se incorpora
al mapa de coincidencia espacial de las tres fuentes principales.

La clasificación visual utilizada en el mapa y el informe es:

| Intervalo NDVI | Lectura visual | Interpretación orientativa |
|---:|---|---|
| < 0 | Sin vegetación activa | Agua, sombra, nubes residuales o superficies no vegetadas |
| 0.0 a < 0.2 | Suelo o cobertura muy escasa | Suelo desnudo, área construida o vegetación muy dispersa |
| 0.2 a < 0.4 | Vegetación escasa | Cobertura poco densa, pastizal o cultivo en etapa temprana |
| 0.4 a < 0.6 | Vegetación moderada | Actividad vegetal y cobertura intermedias |
| ≥ 0.6 | Vegetación densa | Señal alta de vegetación verde y densa |

Los intervalos describen vigor espectral, no tipo de cobertura. Un valor alto no
confirma por sí solo bosque natural, y uno bajo no demuestra por sí solo pérdida
forestal. En la aplicación, cada clase incluye un botón de información accesible
mediante pulsación o teclado.

## Índice ponderado

Cada fuente puede sumar una sola vez:

| Fuente | Peso |
|---|---:|
| JRC TMF | 2.0 |
| Hansen GFC | 2.0 |
| ESRI LULC | 1.5 |
| GEDI | 0.5 |
| NDVI | 0.5 |

La fórmula es:

`puntaje = 2·JRC + 2·Hansen + 1.5·ESRI + 0.5·GEDI + 0.5·NDVI`

donde cada variable vale `1` si su señal está activa y `0` en caso contrario. El
puntaje máximo es 6.5. No se suman áreas, píxeles ni subcriterios adicionales al
peso de una misma fuente.

## Reglas de prioridad

| Puntaje | Prioridad |
|---:|---|
| ≥ 3.0 | Alta |
| ≥ 1.5 y < 3.0 | Media |
| ≥ 0.5 y < 1.5 | Preventiva |
| < 0.5 | Baja |

Una señal ESRI aislada produce 1.5 puntos. Una señal JRC aislada produce 2.0 y una
señal Hansen aislada produce 2.0. Por diseño, ESRI nunca aporta más que cualquiera
de las dos fuentes forestales principales.

## Consistencia entre fuentes

La consistencia es una lectura adicional y no modifica el puntaje:

| Lectura | Regla |
|---|---|
| Alta consistencia | JRC TMF, Hansen GFC y ESRI LULC presentan señal de deterioro |
| Consistencia parcial | Exactamente dos de las tres fuentes presentan señal |
| Lectura mixta | Coexisten señales de deterioro y de recuperación o ganancia |
| Sin señal consistente | Menos de dos fuentes principales coinciden en deterioro |

Para evitar que cambios mínimos produzcan una lectura mixta, la recuperación JRC
se filtra con 0.5 ha o 1% del área y la ganancia de árboles ESRI con 0.10 ha y 5%
del área. Son criterios simétricos a los umbrales de cambio usados para esas
fuentes. Las ganancias no compensan ni restan puntos a una señal de deterioro,
porque pueden ocurrir simultáneamente en sectores diferentes de la misma área.

## Mapa de coincidencia espacial

El séptimo mapa, **Sectores que requieren revisión**, responde a una pregunta
distinta del índice: ubica dónde se superponen las señales de deterioro de las tres
fuentes principales. Utiliza:

- JRC TMF 2025: degradación o deforestación;
- Hansen GFC: pérdida posterior al 31/12/2020;
- ESRI LULC 2017-2024: transición de árboles a no árboles.

JRC conserva su malla de 30 m. Hansen se reproyecta por vecino más cercano y la
señal ESRI de 10 m se agrega por presencia máxima antes de llevarse a la misma malla.
Las tres imágenes binarias se suman y producen:

| Valor | Clase | Lectura |
|---:|---|---|
| 1 | Señal de una fuente | Evidencia aislada; revisar el producto correspondiente |
| 2 | Coincidencia de dos fuentes | Sector de revisión prioritaria |
| 3 | Coincidencia de tres fuentes | Sector con coincidencia espacial de JRC, Hansen y ESRI |

GEDI y NDVI no participan en esta superposición: GEDI aporta contexto estructural y
NDVI se evalúa por separado mediante su superficie de disminución. El mapa no agrega
puntos, no modifica la prioridad, no demuestra causalidad y no sustituye la revisión
documental, imágenes recientes o verificación de campo.

## Trazabilidad

Las constantes y funciones se mantienen en `metodologia_indice.py`. Las pruebas de
`test_metodologia_indice.py` verifican pesos, umbrales, suma única por fuente,
clasificación, consistencia, señal conservadora de NDVI e integración estructural sin aumento
del puntaje. El registro JSON conserva fuentes,
períodos, umbrales, justificaciones, pesos, aportes efectivos, estadísticas y reglas
de prioridad, consistencia y contexto estructural, además de la regla y las
superficies del mapa de coincidencia espacial.

## Corredores ecológicos de Almanaque Azul

La capa vectorial externa contiene 22 polígonos interpretados y 14 puntos críticos. Se conservan sus atributos `nombre`, `notas`, `cond_promedio`, `area_ha` y `cat`. Las tres categorías verificadas en el dato publicado son:

| Valor original | Etiqueta mostrada | Color original |
|---|---|---|
| `alta` | Alta | `#345a01` |
| `mediana` | Mediana | `#a1d303` |
| `mediabaja` | Media-baja | `#e0c504` |

Los originales están en EPSG:3857 y se convierten a EPSG:4326 mediante `scripts/preparar_datos_corredores.py`. Para medir intersecciones, el área evaluada y los corredores se proyectan a Equal Earth Americas (EPSG:8857). Se informa el área y porcentaje de superposición total, por categoría y con los tramos mesoamericanos.

Esta superposición no modifica el índice satelital de cambios. Se utiliza como
valor estratégico en una prioridad separada de visita y tampoco demuestra
conectividad funcional para una especie particular.

## Prioridad integrada de visita

La aplicación conserva tres dimensiones visibles para evitar que el contexto
ecológico se confunda con evidencia de deterioro:

1. **Urgencia por cambios:** el índice satelital, de 0 a 6.5 puntos.
2. **Valor estratégico del corredor:** hasta 1.5 puntos adicionales.
3. **Condición estructural 2021:** indica dónde focalizar la visita, sin sumar puntos.

El aporte por corredor se calcula así:

```text
aporte por solapamiento = mínimo(% del AOI en corredores / 25, 1.0)
aporte mesoamericano = 0.5 cuando existe intersección
puntaje integrado = puntaje de cambios + ambos aportes
```

El aporte por superficie alcanza su máximo cuando al menos 25% del área está
dentro de corredores. Las categorías alta, mediana y media-baja publicadas por
Almanaque Azul se muestran como atributos, pero no se convierten en señales de
deterioro ni en una jerarquía inventada de valor ecológico.

El corredor por sí solo puede justificar seguimiento preventivo, pero nunca una
prioridad alta o muy alta. La clase **Muy alta** exige que la prioridad por
cambios ya sea alta y que el aporte estratégico del corredor alcance al menos
1 punto. Así, la herramienta responde dos preguntas diferentes: por qué urge
revisar el área y por qué esa revisión tiene relevancia para la continuidad ecológica.
La tercera pregunta —dónde concentrar el trabajo de campo— se responde con la red
de parches de la cobertura 2021.

## Fragmentación del bosque de referencia 2021

La cobertura utilizada corresponde a la capa **Bosque y otros usos**, referencia 2021, publicada por SINIA–MiAMBIENTE. La administración publica el shapefile nacional una sola vez como asset privado de Earth Engine. La aplicación filtra internamente el campo `Categoria` por el valor `Bosques y Otras Tierras Boscosas`; la persona usuaria no carga archivos ni selecciona campos de clase. Para la conectividad se obtiene el área evaluada más un contexto exterior adaptativo: la distancia al corredor más cercano más el umbral de conexión, sin superar 5 km. Las geometrías se generalizan con una tolerancia de 10 m, se transforman a EPSG:8857, se validan y se separan en parches poligonales.

El bosque del contexto exterior participa únicamente en la construcción de la red. Las hectáreas, la cantidad de fragmentos y los polígonos analíticos entregados se limitan al área original. De esta manera, un fragmento que continúa o se conecta con bosque inmediatamente fuera del límite no se clasifica erróneamente como aislado, sin incorporar superficie exterior al resultado del predio. Para explicar la conexión encontrada, el mapa permite activar una cobertura verde de referencia dentro del área y el contexto adaptativo calculado, que nunca supera 5 km; esta capa visual comienza apagada, no tiene categorías de importancia y no altera ninguna superficie reportada. La ruta potencial hacia un corredor también puede extenderse visualmente fuera del límite.

Esta capa representa la cobertura clasificada para 2021. Se utiliza para describir la fragmentación y conectividad estructural del bosque de ese año; por sí sola no permite determinar cuándo ocurrió un cambio ni debe interpretarse como una serie anual de deforestación.

Las métricas de clase son:

- número de parches;
- área total y porcentaje de bosque en el paisaje;
- densidad de parches por 100 ha;
- densidad de borde en m/ha;
- porcentaje ocupado por el parche mayor;
- área media, mediana y desviación poblacional;
- índice de forma medio `perímetro / (2 × √(π × área))`.

## Red de conectividad estructural

Cada parche es un nodo. Dos nodos se conectan cuando la distancia mínima entre sus polígonos es menor o igual al umbral seleccionado. Para una distancia `d` y umbral `u`, la fuerza de la arista es `exp(-d/u)` y el costo mínimo utilizado es 1 m.

Las métricas y el índice se calculan con todas las relaciones válidas. Para evitar abanicos de líneas redundantes, el mapa representa únicamente el árbol de expansión mínimo de cada componente: el conjunto de enlaces más cortos que mantiene unido ese grupo. Cada segmento une los puntos de borde más próximos de dos fragmentos y muestra la distancia mínima realmente calculada entre sus polígonos. Un halo blanco y un trazo verde oscuro conservan el contraste sobre la imagen satelital.
Las relaciones ordinarias con bosque exterior participan en las métricas, pero no se dibujan como líneas fuera del polígono. La ruta potencial destacada sí puede salir del área y la persona usuaria puede activar la cobertura verde completa del entorno para reconocer el bosque que sostiene visualmente esa cadena.
Un parche con grado cero, después de considerar ese contexto, se considera aislado al umbral elegido. Para ayudar a
planificar la inspección, la aplicación puede dibujar una línea discontinua desde
cada parche aislado hacia el parche más cercano disponible. La geometría visible se corta en el límite del área. Esa línea
es una **brecha potencial para revisión**: no es un corredor confirmado, una ruta de
menor costo ni evidencia de movimiento de fauna.

Además de nodos, aristas, componentes y densidad de red, el resultado informa el
número y porcentaje de parches aislados, el número de parches conectados, la distancia
media y máxima de las conexiones y el número de brechas potenciales representadas.

El índice conector por parche reproduce los pesos de los ejercicios R:

```text
0.40 × grado normalizado
+ 0.30 × intermediación normalizada
+ 0.20 × área normalizada
+ 0.10 × fuerza normalizada
```

La importancia `Alta`, `Media` o `Baja` se asigna mediante los cuantiles 75% y 50% del índice dentro del área analizada. Es una clasificación relativa y no equivale a las categorías publicadas por Almanaque Azul. Con más de 250 nodos, la intermediación se aproxima con una muestra reproducible de hasta 64 nodos. La cercanía, que no participa en el índice ni en la lectura principal, se omite en esas redes grandes para evitar un cálculo cuadrático innecesario.

La condición estructural se resume con reglas operativas transparentes:

| Condición | Regla |
|---|---|
| Un solo parche | La cobertura seleccionada forma un parche |
| Conectada al umbral | Todos los parches forman un componente |
| Conectividad predominante | El componente mayor reúne al menos 75% de los parches |
| Conectividad intermedia | El componente mayor reúne entre 50% y menos de 75% |
| Red dividida | El componente mayor reúne menos de 50% |

Estas categorías dependen del umbral de distancia elegido y describen conectividad
estructural, no movimiento comprobado de fauna. Se conectan con el diagnóstico para
orientar la visita hacia parches conectores y componentes aislados, pero no modifican
el puntaje: asignarles peso requeriría calibración ecológica para el territorio y las
especies objetivo.

## Conexión estructural potencial hacia un corredor de referencia

La aplicación examina los corredores publicados por Almanaque Azul dentro del contexto adaptativo, limitado a un máximo de 5 km. Para cada corredor identifica los fragmentos situados dentro del umbral elegido y busca, sobre la red completa, una cadena desde el área evaluada. La ruta solo se acepta cuando **cada salto** entre fragmentos y el salto final al corredor es menor o igual al umbral seleccionado.

Cuando existe más de una alternativa, se conserva una sola para mantener legible el mapa. Primero se prefieren las categorías originales de Almanaque Azul en el orden alta, mediana y media-baja; dentro de la misma categoría se selecciona la menor suma de separaciones. La ruta se dibuja en naranja con halo blanco y puede incluir bosque exterior al polígono, aunque esa superficie exterior no se suma a las hectáreas del área.

Esta salida responde a una pregunta limitada: si la geometría del bosque clasificado en 2021 permite encadenar fragmentos hasta un corredor de referencia usando el umbral indicado. No es una ruta de menor costo del paisaje, no incorpora resistencia de coberturas, topografía o requerimientos de especies, no crea un nuevo corredor oficial y no demuestra conectividad funcional ni movimiento de fauna. Por esa razón orienta el foco de revisión, pero no añade puntos al índice de prioridad.

## Índice de Resiliencia Ecológica indicativo (ERI)

El ERI es una lectura complementaria entre 0 y 1 y se mantiene separado del índice de
indicios y de la prioridad de visita. Combina cuatro componentes normalizados:

| Componente | Peso | Aproximación utilizada |
|---|---:|---|
| Integridad estructural | 35 % | Probabilidad de árboles de Dynamic World y altura GEDI normalizada |
| Conectividad local | 25 % | Proporción de bosque en una ventana circular de 1,5 km |
| Estabilidad topográfica | 20 % | Pendiente Copernicus DEM ponderada por cobertura arbórea |
| Proximidad riparia | 20 % | Distancia a cauces derivados de MERIT Hydro hasta 1 km |

El resultado se clasifica como muy bajo, bajo, medio, alto o muy alto y el visor también
identifica el componente con menor valor. La conectividad es un proxy espacial ligero:
no equivale a ECA/A, no modela resistencia ni demuestra movimiento de fauna. Los pesos
y las clases deben calibrarse con información de campo antes de cualquier uso normativo.

## Comparación estructural 2021–2023

El geoportal puede ejecutar dos diagnósticos con el mismo polígono, distancia máxima
entre parches y superficie mínima de parche:

- **2021:** cobertura vectorial institucional `SINIA_2021_COBERTURA_GENERAL_VECTOR`,
  filtrada por `Categoria = Bosques y Otras Tierras Boscosas`;
- **2023:** raster diagnóstico `SINIA_2023_COBERTURA_GENERAL_RASTER10M`, donde el
  código 1 representa bosques y otras tierras boscosas, convertido a polígonos para
  aplicar el mismo motor estructural.

Cada escenario produce por separado superficie forestal, parches, bordes, componentes,
aislamiento, conexiones y geometrías descargables. La interfaz y el PDF los presentan
en columnas y mapas independientes. Se conservan sus fuentes y definiciones originales.

Esta salida **no es una matriz de transición ni una estimación causal de cambio**. Los
productos difieren en formato, resolución, proceso de clasificación y naturaleza de la
fuente. Por ello el motor no calcula una diferencia científica de hectáreas ni afirma
pérdida, ganancia o restauración entre 2021 y 2023. Una comparación temporal de cambio
requiere demostrar compatibilidad temática, espacial y metodológica antes de habilitar
esas operaciones.
