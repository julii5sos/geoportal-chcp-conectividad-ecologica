# Historial de versiones

Este historial documenta la evolución de la aplicación UX. Las versiones siguen
el formato `MAJOR.MINOR.PATCH`: una versión principal, mejoras compatibles y
correcciones compatibles, respectivamente.

## [5.3.0] - 2026-11-01 — diseño exacto del portal y límites locales

- Sustituye la interpretación visual anterior por la composición del HTML entregado:
  encabezado azul de dos niveles, marca Conectividad Panamá, navegación institucional,
  portada con corte diagonal, panel de 340 px, mapa central y resultados laterales.
- Cambia las pestañas del panel a **Capas**, **Polígono** y **Mapa base**, con la acción
  principal fija al pie como en la plataforma de referencia.
- Incorpora `area_estudio.geojson` y `subcuencas_canal.geojson` del portal; la cuenca y
  las 53 subcuencas ya no dependen de assets privados de Earth Engine.
- Añade el grupo **Límites** para encender la cuenca y las subcuencas locales, con
  identificación por nombre, grupo y superficie.
- Mantiene el ERI indicativo, los análisis satelitales, corredores, fragmentación,
  gráficas, informes y descargas existentes.

## [5.2.0] - 2026-11-01 — panel de la plataforma HTML

- Adapta la estructura funcional del portal HTML al panel lateral de Streamlit con
  pestañas reales para **Capas**, **Filtros** y **Mapa base**.
- Organiza las fuentes JRC, Hansen, ESRI, NDVI, GEDI, ERI y conectividad dentro de
  Capas; mueve el área, los años y los parámetros técnicos a Filtros.
- Añade tres fondos intercambiables —imagen satelital, mapa claro y OpenStreetMap— sin
  alterar las geometrías, métricas ni reglas de la preevaluación.
- Mantiene las acciones principales fijadas al pie del panel: **Realizar/Actualizar** y,
  cuando existe un resultado, **Resultados**.
- Ajusta el panel a 340 px, igual que el modelo HTML, y conserva el modo de enfoque al
  cerrarlo para que el mapa recupere todo el ancho.

## [5.1.0] - 2026-10-29 — visor centrado en el mapa

- El mapa pasa a ocupar todo el ancho disponible y 780 px de alto en escritorio; la
  lectura rápida, el ERI y la gráfica se presentan debajo cuando existe un resultado.
- Sustituye las cuatro opciones de radio del área por un selector compacto que conserva
  exactamente las mismas unidades territoriales y reglas de recorte.
- Reduce las acciones principales a «Crear/Actualizar análisis» y «Resultados y
  descargas», con «Cambiar enfoque» como acción secundaria.
- Elimina la columna derecha permanente, los accesos duplicados al detalle y la
  explicación redundante de la vista cartográfica.
- Convierte la navegación superior en pestañas visuales ligeras, sin apariencia de
  botones grandes, y conserva foco visible y controles de al menos 44 px.

## [5.0.0] - 2026-10-29 — portal cartográfico con ERI indicativo

- Incorpora el Índice de Resiliencia Ecológica (ERI) como lectura complementaria entre
  0 y 1, separada del índice de indicios y de la prioridad de visita.
- Combina cuatro componentes documentados: integridad estructural, conectividad local,
  estabilidad topográfica y proximidad riparia; sus pesos, clases y limitaciones quedan
  incluidos en el registro metodológico.
- Añade una capa ERI de cinco clases al mapa y gráficas de barras para comparar sus
  componentes y la superficie por clase.
- Organiza el panel derecho en Lectura, ERI y Gráfica para mantener el mapa como centro
  del portal y evitar una página larga.
- Conserva los análisis vigentes del repositorio y utiliza el HTML únicamente como modelo
  de composición visual.

## [4.3.1] - 2026-10-29 — corredores recortados y gráficas comparables

- Muestra por defecto únicamente la parte de los corredores que coincide con la finca,
  subcuenca o polígono analizado.
- Conserva el corredor completo como contexto regional opcional, con menor opacidad para
  que no se confunda con bosque ni con la superficie evaluada.
- Sustituye la comparación ambigua entre corredor y bosque por tres gráficas coherentes:
  dentro/fuera de corredores, bosque/otros usos de 2021 y fragmentos cercanos/separados.
- Añade geometrías recortadas al resultado analítico y mantiene tablas con valores como
  alternativa accesible a las gráficas.

## [4.3.0] - 2026-10-29 — conectividad más rápida y panel simplificado

- Elimina del panel lateral el bloque informativo redundante de fuentes de conectividad;
  las fuentes y su alcance permanecen disponibles en Metodología y ayuda.
- Evita serializar 22 polígonos nacionales y 14 puntos críticos cuando sus capas están
  apagadas, reduciendo aproximadamente 1,2 MB del mapa inicial.
- Calcula un contexto forestal adaptativo según la distancia al corredor más cercano,
  sin superar 5 km, y simplifica a 10 m la geometría transferida desde Earth Engine.
- Reduce el costo de centralidad en redes grandes y muestra el avance por etapa durante
  la preparación de la preevaluación.
- Evita retener globalmente los GeoJSON de fragmentación y limita la cantidad y duración
  de los cachés de series, análisis e imágenes de informe para controlar el uso de memoria.

## [4.2.6] - 2026-10-29 — composición multicapa visible

- Separa el eje categórico de las barras del control temporal para evitar que la escala
  interactiva comprima todas las series en el borde izquierdo.
- El navegador inferior filtra los años mediante un campo numérico estable; una, dos o
  tres capas conservan barras visibles y apiladas.
- Evita desplazamientos de año causados por conversiones de fecha y zona horaria.

## [4.2.5] - 2026-10-29 — barras visibles desde la carga inicial

- Inicializa el navegador temporal con el intervalo completo de años disponibles para
  que las barras seleccionadas aparezcan desde la primera renderización.
- Evita que el control temporal pueda quedar vacío y ocultar accidentalmente todas las
  series del gráfico principal.
- Mantiene el selector inferior para enfocar períodos sin alterar los datos del análisis.

## [4.2.4] - 2026-10-29 — gráfica temporal inspirada en MapBiomas

- Presenta las capas anuales comparables mediante barras apiladas, con una leyenda y
  colores estables para reconocer cada indicador seleccionado.
- Añade un navegador temporal inferior que permite enfocar un intervalo de años sin
  convertir la gráfica analítica principal en una gráfica de líneas.
- Incorpora la etiqueta «Visualizadas en el mapa» para reforzar la relación entre las
  capas activas, la evidencia cartográfica y las series visibles.
- Conserva tooltips con valores exactos y una tabla accesible con las mismas series.

## [4.2.3] - 2026-10-29 — modo de enfoque al cerrar el panel

- Al contraer el panel lateral, su ancho reservado pasa realmente a cero y el mapa con
  los resultados utiliza todo el espacio horizontal disponible.
- El control nativo para reabrir el panel permanece visible y conserva su área de
  interacción accesible.
- En pantallas pequeñas, el panel abierto continúa adaptándose al ancho disponible sin
  producir desplazamiento horizontal.

## [4.2.2] - 2026-10-29 — gráficas vinculadas a varias capas

- Cuando se activan varias capas comparables de una misma fuente, la columna de
  resultados las reúne en una gráfica de barras agrupadas con colores y leyenda propios.
- Deforestación, degradación y regeneración forestal de JRC TMF pueden compararse por
  año sin perder su nombre, unidad ni color.
- La tabla accesible reproduce exactamente las series visibles y la cabecera indica
  cuántas capas del mapa participan en la gráfica.
- Las fuentes con unidades o significados incompatibles no se superponen en un mismo
  eje, evitando comparaciones engañosas.

## [4.2.1] - 2026-10-28 — regeneración forestal JRC TMF

- Incorpora **Regeneración forestal** como capa independiente, correspondiente a la
  clase oficial *Forest regrowth* de JRC TMF.
- Amplía la serie anual JRC con barras de deforestación, degradación y regeneración
  forestal, manteniendo cada lectura separada y con color estable.
- La vista **Estado forestal** muestra las seis clases JRC en una distribución de
  barras: bosque no perturbado, bosque degradado, tierra deforestada, regeneración
  forestal, agua y otra cobertura.
- Aclara que la regeneración observada por satélite no demuestra por sí sola la
  ejecución ni el éxito de un proyecto de restauración.

## [4.2.0] - 2026-10-28 — barras vinculadas con la evidencia

- Sustituye las series de líneas por gráficas de barras con colores estables por fuente.
- Añade en la columna derecha una gráfica contextual vinculada con la evidencia activa
  del mapa, incluida la deforestación JRC en hectáreas por año.
- Mantiene GEDI como distribución de alturas y conserva tablas de valores accesibles.

## [4.1.0] - 2026-10-28 — evidencia cartográfica como foco

- Oculta la cabecera institucional duplicada después de elegir una preevaluación y
  conserva una sola barra compacta de contexto.
- Reduce márgenes, separación vertical, ancho del panel lateral y altura de tarjetas
  para mostrar más información útil sin perder legibilidad.
- Amplía la relación del mapa frente al panel de resultados y alinea ambas columnas
  con cabeceras visuales equivalentes.
- Elimina el bloque introductorio grande que antecedía al mapa; la ayuda cartográfica
  pasa a una nota breve y la evidencia aparece inmediatamente.
- Compacta las estadísticas, métricas y pestañas del resultado para mantener una
  lectura armónica junto al mapa.

## [4.0.0] - 2026-10-27 — modelo visual basado en el portal HTML

### Nueva variante en una rama independiente

- Adapta la composición visual del HTML de referencia a la aplicación Streamlit sin
  incorporar sus datos demostrativos, cálculos ni metodología.
- Introduce una cabecera institucional azul, acento verde, panel lateral compacto,
  mapa dominante y panel analítico a la derecha.
- Conserva los análisis reales del repositorio: JRC TMF, Hansen GFC, ESRI LULC,
  GEDI, Sentinel-2/NDVI, corredores, bosque 2021 y fragmentación.
- Mantiene las tres rutas de preevaluación, la selección por finca, subcuenca,
  polígono o cuenca completa, así como las gráficas, tablas, PDF y descargas.
- Documenta la variante en `design-system/evaluaci-n-de-corredores-panam/pages/modelo-html.md`.
- Se publica desde `version/4.0-modelo-html`; `main` y la aplicación actualmente
  desplegada no se modifican.

## [3.2.0] - 2026-10-27 — gráficas a color y lectura directa

### Lenguaje visual inspirado en tableros cartográficos

- Sustituye las barras monocromáticas del tablero por barras horizontales con un
  color reconocible para cada fuente, indicador o condición de conectividad.
- Añade el valor y la unidad directamente junto a cada barra, además del detalle al
  pasar el cursor y la tabla accesible ya disponible.
- Conserva una paleta estable para JRC, Hansen, ESRI, GEDI y NDVI, evitando depender
  únicamente del color para comunicar el resultado.
- Aplica el mismo tratamiento a las distribuciones JRC, los cambios ESRI y la
  comparación de aportes del resultado completo.
- Refuerza las tarjetas de gráficas con contraste, bordes y acentos institucionales
  para que el panel sea más claro y visualmente activo.

## [3.1.0] - 2026-10-27 — mapa y gráficas en un mismo tablero

### Panel analítico inspirado en visores ambientales

- Mantiene el mapa visible después de ejecutar la preevaluación; el cálculo ya no
  cambia automáticamente a una página separada de resultados.
- Añade una columna analítica a la derecha con pestañas de **Lectura** y **Gráficas**.
- Muestra de inmediato el aporte ponderado de JRC, Hansen, ESRI, GEDI y NDVI y la
  superficie de los principales indicios territoriales.
- En corredores, compara la superficie dentro de corredores, el bosque 2021 y la
  relación entre fragmentos cercanos y separados.
- Incluye los valores tabulares de cada gráfica como alternativa accesible y mantiene
  el detalle técnico, las series temporales, el PDF y las descargas mediante una acción
  contextual, sin recargar el mapa durante la exploración principal.

## [3.0.0] - 2026-10-27 — versión de prueba en rama independiente

### Navegación por mapa, fuentes y análisis

- Simplifica la navegación superior a **Mapa**, **Metodología y ayuda** y **Acerca del
  visor**. Los resultados se abren de forma contextual después de crear la
  preevaluación, evitando que «Mapa» y «Análisis» muestren la misma portada.
- Reemplaza el selector genérico de capas por bloques reconocibles para JRC TMF,
  Hansen, ESRI, Sentinel-2/NDVI y GEDI, además de las fuentes de conectividad.
- Lleva **Crear análisis** al panel lateral y evita volver a construir el mapa cuando
  la persona consulta los resultados.
- Añade **Ver resultados** y **Volver al mapa** como acciones contextuales; al terminar
  el cálculo se abre automáticamente la lectura del resultado.
- Organiza los resultados completos en pestañas y permite preparar una gráfica por
  fuente bajo demanda para reducir el tiempo de carga.
- Presenta series anuales únicamente cuando tienen sentido metodológico: cambio JRC,
  pérdida Hansen, cobertura arbórea ESRI y vigor NDVI. GEDI se representa mediante
  una distribución de altura del dosel.
- Conserva la aplicación estable en `main`; esta versión se publica desde la rama
  `version/3.0-tablero-cartografico` como una app nueva de Streamlit.

## [2.4.0] - 2026-10-27

### Tablero cartográfico profesional

- Reorganiza la vista de trabajo con controles a la izquierda, mapa dominante en el
  centro y lectura rápida del resultado a la derecha.
- Sustituye la cabecera extensa por una barra institucional compacta después de
  elegir el análisis.
- Retira el indicador de pasos durante el trabajo para que la interfaz se comporte
  como visor y no como una guía lineal.
- Presenta toda la evidencia en pestañas visibles de resumen, cambios territoriales,
  corredores y bosque/conectividad, sin eliminar métricas, gráficos ni tablas.
- Mantiene metodología, informes y descargas, pero los separa de la lectura principal.
- Amplía el área útil del mapa y conserva una composición adaptable para pantallas
  pequeñas.

## [2.3.1] - 2026-10-27

### Comparador temporal sincronizado

- Fuerza la actualización del recorte de ambos años durante el zoom, el
  desplazamiento, la carga de mosaicos, el cambio de tamaño y la pantalla completa.
- Desactiva las transformaciones animadas únicamente en la vista comparativa para
  evitar que una mitad parezca quedar fija mientras cambia la escala.
- Conserva la posición elegida del divisor y aclara que las dos imágenes deben
  permanecer en la misma ubicación y escala al navegar.
- Amplía la compatibilidad del divisor con teclado, mouse y pantalla táctil mediante
  una etiqueta accesible y un área real de arrastre de 44 px, independiente del
  desplazamiento del mapa.

## [2.3.0] - 2026-10-27

### Preevaluación guiada y alcance explícito

- Sustituye los títulos **Evaluación territorial** y **Evaluación integral** por
  **Preevaluación territorial** y **Preevaluación integral** para evitar que el
  resultado se interprete como un hallazgo ya verificado en campo.
- Añade navegación persistente entre **Preevaluar un área**, **Objetivo y alcance**
  y **Método y fuentes**.
- Explica que el producto sirve para justificar una revisión posterior, ubicar dónde
  conviene mirar y documentar los indicios que respaldan esa orientación.
- Separa explícitamente lo que la aplicación puede orientar de lo que requiere
  conocimiento local, documentos, imágenes recientes o validación de campo.
- Ofrece una lectura sencilla de cinco pasos y conserva pesos, umbrales, fuentes y
  limitaciones en secciones opcionales para usuarios técnicos.
- Las páginas explicativas se muestran sin iniciar Earth Engine, reduciendo la espera
  para quienes solo necesitan comprender el objetivo o el método.

## [2.2.0] - 2026-09-29

### NDVI integrado al índice territorial

- Compara compuestos Sentinel-2 de 2020 y 2025 con máscara SCL.
- Identifica disminución desde vegetación inicialmente moderada cuando ΔNDVI es
  menor o igual a -0.15.
- Exige simultáneamente 0.12 ha, 5% del área y 70% de cobertura válida antes de
  activar la señal.
- Incorpora un peso corroborativo de 0.5; el índice satelital pasa a un máximo de
  6.5 puntos sin modificar el mapa espacial JRC–Hansen–ESRI.
- Muestra NDVI inicial y final medios, cambio medio, superficie, porcentaje,
  cobertura válida y aporte en la aplicación, el PDF y el registro metodológico.

## [1.0.0] - 2026-09-11

### Ficha ejecutiva con cartografía explicativa

- Reorganiza el PDF con divulgación progresiva: conclusión y acción primero,
  evidencia espacial después y trazabilidad técnica al final.
- Desglosa el puntaje fuente por fuente y distingue explícitamente el índice de
  prioridad de las hectáreas donde coinciden dos o tres señales.
- Añade un mapa limpio de fragmentación, sin fondo satelital y sin líneas de red.
- Añade un segundo mapa limpio de conectividad estructural con relaciones
  esenciales, separaciones potenciales, ruta al corredor y polígono de referencia.
- Mantiene las leyendas fuera de los mapas y acompaña cada color o trazo con una
  explicación en lenguaje sencillo.
- Conserva todos los mapas por fuente y la información metodológica como evidencia
  secundaria, sin eliminar resultados del análisis.

## [0.9.0] - 2026-09-11

### Divulgación progresiva orientada a decisiones

- Conserva todos los cálculos, métricas, gráficos, tablas y descargas del diagnóstico.
- Reduce la información visible antes de ejecutar a tres elementos: área, superficie y vista elegida.
- Presenta después del análisis una conclusión ejecutiva, cuatro indicadores clave y el mapa antes del detalle técnico.
- Agrupa la configuración, los períodos, las fuentes y el contenido esperado en una explicación opcional cerrada.
- Permite abrir por separado los detalles de cambios satelitales, corredores ecológicos y bosque y conectividad.
- Simplifica el recorrido principal a configurar, analizar y revisar para personas sin experiencia previa en GIS.

## [0.8.1] - 2026-09-10

### Bosque completo como contexto visual opcional

- Añade una capa apagada por defecto que muestra en verde la cobertura de bosque 2021 dentro del área y hasta 5 km alrededor.
- Mantiene aparte los fragmentos analíticos coloreados, que siguen limitados al polígono evaluado.
- Amplía temporalmente la vista del mapa al entorno cuando se activa la cobertura completa para poder interpretar la ruta naranja.
- Explica junto al mapa y en la leyenda que el bosque exterior participa como contexto estructural, pero no aumenta las hectáreas reportadas.

## [0.8.0] - 2026-09-10

### Red legible y conexión potencial hacia un corredor

- Mantiene todas las relaciones entre fragmentos para las métricas, pero muestra en el mapa solo la estructura mínima necesaria de cada grupo.
- Sustituye las líneas radiales entre puntos interiores por segmentos entre los bordes más próximos de los fragmentos.
- Añade un halo blanco y un trazo institucional oscuro para que los enlaces sigan siendo visibles sobre la imagen satelital.
- Busca en un entorno de 5 km una cadena estructural hacia un corredor publicado, exigiendo que cada salto respete la distancia seleccionada.
- Prefiere corredores de categoría original alta, luego mediana y media-baja, y muestra una sola ruta naranja para evitar ruido visual.
- Usa la ruta para orientar la revisión, sin añadir puntos ni presentarla como movimiento de fauna o conectividad funcional confirmada.

## [0.7.1] - 2026-09-10

### Contexto exterior sin ampliar el mapa ni las hectáreas

- Evalúa la conectividad con un entorno exterior igual a la distancia seleccionada.
- Mantiene las geometrías visibles y las hectáreas reportadas dentro del polígono original.
- Evita clasificar como separado un fragmento que continúa o se conecta con bosque exterior.
- Indica en cada fragmento si existe continuidad o una conexión fuera del área.
- La capa opcional resalta los fragmentos realmente separados y muestra su distancia al vecino.

## [0.7.0] - 2026-09-10

### Lectura guiada y mapa sin ruido visual

- Sustituye los términos principales de red por explicaciones sobre fragmentos cercanos o separados.
- Presenta primero cuatro indicadores comprensibles y una lectura rápida en lenguaje cotidiano.
- Conserva métricas, tablas y descargas técnicas dentro de una sección opcional cerrada.
- Traslada la activación de capas satelitales, bosque, relaciones y corredores al panel lateral.
- Elimina los controles flotantes superpuestos que cubrían el mapa y mantiene la leyenda fuera del área cartográfica.
- Muestra los fragmentos de bosque con menor opacidad y deja apagadas por defecto las relaciones y separaciones potenciales.
- Simplifica los textos emergentes para que indiquen área, valor relativo y condición de separación.

## [0.6.1] - 2026-09-09

### Red de conectividad visible y descargable

- Dibuja en el mapa las conexiones entre parches que cumplen el umbral seleccionado.
- Identifica los parches aislados y propone una línea discontinua a su vecino más cercano como brecha para revisión, no como corredor confirmado.
- Separa los controles de parches, conexiones y brechas potenciales para evitar ruido visual.
- Añade métricas de parches conectados y aislados, distancias de las aristas y componentes de red.
- Permite descargar los parches y la red de conectividad en GeoJSON.
- Mantiene Earth Engine como fuente oficial; no usa la copia nacional simplificada porque su integridad espacial no está validada.

## [0.6.0] - 2026-09-08

### Cobertura de bosque automática

- Elimina el cargador de shapefiles de la interfaz pública.
- Lee el recorte forestal 2021 desde un asset institucional privado de Earth Engine.
- Filtra automáticamente la categoría oficial `Bosques y Otras Tierras Boscosas` de la capa nacional; el usuario no selecciona clases.
- Recorta automáticamente la cobertura al área seleccionada antes de calcular fragmentación y conectividad.
- Mantiene configurables únicamente la distancia entre parches y el área mínima, como opciones de análisis.
- Distingue correctamente un recorte sin bosque de un paisaje formado por un solo parche.
- Documenta el secreto `EE_ASSET_BOSQUE_2021` y el flujo de publicación administrado.
- Coloca el mapa interactivo inmediatamente después de ejecutar el análisis, antes de las tablas y descargas.

## [0.5.0] - 2026-09-08

### Diagnóstico territorial integrado

- Conecta cambios recientes, corredores y estructura del bosque 2021 en una sola lectura operativa.
- Mantiene el puntaje trazable: los cambios determinan urgencia y los corredores aportan valor estratégico.
- Usa la fragmentación y la red de parches para focalizar la visita sin asignar un peso ecológico no calibrado.
- Presenta cuatro resultados coordinados: urgencia, valor del corredor, condición estructural y prioridad final.
- Lleva la combinación territorial y el foco de visita al mapa, al informe PDF y al registro metodológico JSON.
- Activa automáticamente los corredores en el perfil **Diagnóstico territorial integrado** y reduce las capas iniciales para evitar ruido visual.

## [0.4.0] - 2026-09-08

### Prioridad integrada de visita

- Conserva sin cambios el índice satelital de 0 a 6 puntos y lo presenta como urgencia por cambios.
- Añade hasta 1 punto según la proporción del área dentro de corredores y 0.5 por intersección con el Corredor Biológico Mesoamericano.
- Presenta por separado la urgencia por cambios, el valor estratégico del corredor y la prioridad final de visita.
- Impide que la presencia de un corredor, sin señales suficientes de cambio, genere por sí sola una prioridad alta.
- Incorpora la prioridad de visita en la interfaz, el PDF y el registro metodológico JSON.
- Identifica la cobertura usada para fragmentación como **SINIA–MiAMBIENTE, Bosque y otros usos, 2021**, y separa este corte de cobertura de las series anuales de cambio.

## [0.3.0] - 2026-09-01

### Corredores y conectividad

- Integra los corredores y puntos críticos publicados por Fundación Almanaque Azul.
- Conserva las categorías originales alta, mediana y media-baja y destaca los tramos mesoamericanos oeste, San Lorenzo y este.
- Calcula la intersección del área evaluada con corredores sin alterar el índice satelital.
- Permite cargar temporalmente un shapefile bosque/no bosque y reproducir métricas de fragmentación y conectividad de los ejercicios R.
- Añade resultados contextuales a la interfaz, el PDF y el registro metodológico JSON.
- Separa visual y metodológicamente las categorías externas de Almanaque Azul y los cuantiles internos del índice conector de parches.

## [0.2.10] - 2026-08-03

### Proyección explícita para mosaicos de Earth Engine

- Los mosaicos JRC TMF y ESRI conservan la proyección nativa de su primera
  imagen antes de cualquier operación espacial.
- La señal ESRI establece nuevamente esa proyección antes de ejecutar
  `reduceResolution`, evitando el error de proyección predeterminada inválida.
- El índice, sus pesos, umbrales y períodos metodológicos no cambian.

## [0.2.9] - 2026-08-03

### Vistas y períodos comprensibles

- Se eliminaron las etiquetas que presentaban JRC como vista recomendada frente a
  ESRI; las cuatro opciones principales ahora describen acciones neutrales.
- **Consultar capas individuales** pasó al selector principal y permite elegir un
  solo año para JRC, ESRI o NDVI sin activar el comparador.
- Los barridos de JRC, ESRI y NDVI quedaron como tres opciones independientes con
  selección explícita de año inicial y final.
- El orden de las capas y la capa visible al abrir continúan disponibles, pero en
  un panel secundario que no interfiere con la selección principal.
- La interfaz y la documentación distinguen el comparador JRC 2020-2025 del
  diagnóstico JRC 2025, la pérdida Hansen 2021-2025 y la transición ESRI 2017-2024.

## [0.2.8] - 2026-08-01

### Comparador y explorador de capas independientes

- La visualización personalizada separa **Comparar años** de **Explorar capas**,
  evitando que el barrido temporal cubra GEDI, Hansen, JRC, ESRI o NDVI.
- El comparador admite JRC TMF, ESRI LULC y clases de vigor NDVI; sus años son
  exclusivamente visuales y no alteran el diagnóstico.
- El explorador permite encender varias capas, conservarlas disponibles y
  ordenarlas de arriba hacia abajo mediante controles explícitos.
- Las capas utilizan niveles de dibujo estables y los límites de referencia
  permanecen por encima de la información temática.
- Se reforzó el estilo del botón primario para mantener texto blanco en las
  versiones actuales de Streamlit.
- La portada incorpora una explicación en lenguaje sencillo para personas sin
  conocimientos de sistemas de información geográfica.

## [0.2.7] - 2026-07-24

### Séptimo mapa de orientación espacial

- Se incorporó **Sectores que requieren revisión**, un mapa que suma las señales
  espaciales de JRC TMF 2025, Hansen posterior a 2020 y ESRI 2017-2024.
- Las tres fuentes se estandarizan en la malla JRC de 30 m y se muestran como
  señal de una fuente, coincidencia de dos fuentes o coincidencia de tres fuentes.
- La lectura rápida, el PDF y el registro metodológico informan las hectáreas de
  cada clase y priorizan las coincidencias de dos o tres fuentes.
- GEDI y NDVI no participan en la superposición. El séptimo mapa no modifica el
  índice ponderado ni constituye evidencia causal o una determinación EUDR.

## [0.2.6] - 2026-07-24

### Identidad visual Natura Panamá

- La interfaz adopta el verde institucional `#00544D` de Natura Panamá para
  títulos, texto principal, controles y enlaces.
- El texto secundario utiliza un verde complementario de alto contraste y el
  verde `#76B72A` queda reservado para acentos y subrayados.
- La configuración global de Streamlit aplica la misma identidad cromática a
  los widgets nativos, la barra lateral y ambas entradas de la aplicación.
- Los colores científicos de las capas, las prioridades y los avisos
  semánticos se conservan para no alterar su interpretación.

## [0.2.5] - 2026-07-24

### Claridad entre cálculo y visualización

- El paso 2 se presenta como **Vista inicial de los mapas** y deja de prometer
  que la opción seleccionada cambia el método analítico.
- Todas las vistas ejecutan el mismo cálculo; únicamente determinan qué
  comparador y qué capas aparecen primero.
- Los selectores de años se identifican como controles exclusivamente visuales.
- Los períodos del diagnóstico quedaron centralizados y fijos: referencia 2025,
  JRC 2025, Hansen 2025 y ESRI 2017-2024 por ser la última serie disponible.
- El registro metodológico separa los períodos fijos del diagnóstico de los años
  elegidos para la visualización.

## [0.2.4] - 2026-07-24

### Control de capas del mapa

- Las capas temáticas funcionan como opciones exclusivas: al seleccionar una,
  la anterior se apaga automáticamente.
- Se añadió la opción **Sin capa temática** para volver a la imagen satelital
  sin superposiciones.
- El límite de la cuenca y el área seleccionada permanecen en un grupo de
  referencias independiente.
- La configuración avanzada ahora aclara que allí se eligen las capas
  disponibles, mientras que dentro del mapa se visualiza una temática a la vez.

## [0.2.3] - 2026-07-24

### Lectura del vigor vegetal

- La metodología muestra los cinco intervalos numéricos de NDVI junto a su clase
  de vigor vegetal.
- Cada clase dispone de una ayuda nativa y accesible que se abre mediante
  pulsación o teclado.
- La escala y sus precauciones de interpretación se incorporaron al PDF y al
  registro metodológico JSON.
- La leyenda activa conserva los intervalos visibles sin depender únicamente del
  color.

## [0.2.2] - 2026-07-24

### Correspondencia con el visor original

- Se documentó la matriz funcional entre el visor de Google Earth Engine y la
  aplicación Streamlit.
- El análisis ahora conserva las seis clases JRC: bosque estable, degradación,
  deforestación, recuperación, agua y otra cobertura.
- Se muestran la cobertura arbórea persistente a 2020 y las pérdidas Hansen
  anteriores y posteriores al corte.
- Se añadió la lectura de consistencia alta, parcial, mixta o sin señal
  consistente, sin modificar el índice ponderado.
- El detalle incorpora un gráfico comparable del aporte de JRC, Hansen, ESRI,
  GEDI y NDVI.
- El PDF y el registro metodológico incluyen las nuevas estadísticas y la
  consistencia entre fuentes.

### Validación

- Se ampliaron las pruebas unitarias para cubrir las cuatro lecturas de
  consistencia y evitar que ganancias mínimas produzcan una lectura mixta.

## [0.2.1] - 2026-07-24

### Metodología y trazabilidad

- Se centralizaron pesos, umbrales, justificaciones y reglas de prioridad en
  `metodologia_indice.py`.
- El índice suma cada fuente una sola vez: JRC 2.0, Hansen 2.0, ESRI 1.5,
  GEDI 0.5 y NDVI 0.0.
- Se añadieron pruebas que demuestran que ESRI no puede superar el aporte
  individual de JRC ni de Hansen.
- El registro metodológico JSON incluye la justificación de cada peso y umbral,
  además del aporte efectivo por fuente.

### Interfaz e informe

- La composición ponderada se muestra antes que las métricas temáticas.
- JRC, Hansen, ESRI y GEDI reciben una métrica principal cada uno, en ese orden.
- El PDF incorpora una columna de aporte al índice y la justificación de pesos y
  umbrales; NDVI queda identificado explícitamente como evidencia visual.

## [0.2.0] - 2026-07-24

### Mejorado

- El recorrido muestra visualmente qué etapas están completadas, cuál es el paso
  actual y qué falta por hacer.
- Las opciones de área utilizan nombres cotidianos y explican cuándo conviene usar
  una finca, dibujar un polígono o analizar la cuenca completa.
- Antes de ejecutar se anticipan los tres productos que recibirá el usuario:
  conclusión resumida, evidencia cartográfica e informe trazable.
- El resultado incorpora una lectura rápida organizada en tres preguntas:
  qué se detectó, dónde mirar y qué hacer después.

### Accesibilidad y recuperación

- Las tarjetas se reorganizan en una sola columna en pantallas pequeñas y no
  dependen del color para comunicar el estado.
- Los errores de conexión incluyen una explicación comprensible y tres pasos de
  recuperación, conservando el detalle técnico en un panel secundario.

### Metodología

- No se modificaron fuentes, umbrales, pesos, reglas de prioridad ni cálculos
  territoriales.

## [0.1.7] - 2026-07-24

### Corregido

- Los controles de información de la leyenda NDVI ahora se abren con clic o toque,
  además de admitir navegación mediante teclado.
- Cada explicación aparece debajo de su categoría y muestra el intervalo NDVI
  correspondiente sin depender de una ayuda emergente al pasar el cursor.

### Accesibilidad

- El área interactiva ocupa toda la línea de la categoría, conserva un indicador
  de foco visible y funciona en pantallas táctiles.

## [0.1.6] - 2026-07-22

### Añadido

- Acceso mediante código privado antes de consultar o mostrar la lista de fincas.
- Caducidad de la autorización a los 30 minutos, cierre manual y bloqueo temporal
  después de cinco intentos incorrectos.

### Seguridad

- La dirección del asset de fincas se trasladó a los secretos de Streamlit.
- El mapa dejó de solicitar y mostrar la colección completa de fincas; conserva
  únicamente el contorno del área seleccionada.
- El registro metodológico JSON ya no contiene la dirección del asset ni la
  geometría vectorial de las fincas privadas.

## [0.1.5] - 2026-07-22

### Corregido

- Descargar el registro metodológico JSON ya no reinicia la aplicación ni
  interrumpe la preparación de los mapas del informe PDF.
- Descargar un PDF ya preparado tampoco provoca una nueva ejecución de
  Streamlit.

## [0.1.4] - 2026-07-21

### Mejorado

- Los seis mapas del informe se descargan en paralelo, en grupos de tres, en vez
  de esperar cada mapa de forma consecutiva.
- Los límites del área se solicitan una sola vez a Earth Engine para toda la
  generación cartográfica.
- Cada mapa dispone de un intento principal y un segundo intento más liviano;
  se eliminaron esperas consecutivas innecesarias.
- Cuando el usuario reintenta un informe parcial, se conservan los mapas que ya
  fueron descargados y se solicitan únicamente los faltantes.
- El primer informe conserva una clave de caché estable y solo se invalida cuando
  es necesario reintentar mapas faltantes.
- La interfaz informa cuántos mapas fueron entregados antes de armar el PDF y
  conserva los resultados si la generación cartográfica falla.

## [0.1.3] - 2026-07-21

### Mejorado

- El análisis entrega primero los resultados y deja la creación del PDF como una
  acción posterior solicitada por el usuario.
- Las reducciones de JRC, Hansen, ESRI y GEDI se agrupan en una sola respuesta de
  Earth Engine para reducir viajes de red.
- Los intentos de generación cartográfica pueden repetirse si una miniatura no
  está disponible temporalmente.

## [0.1.2] - 2026-07-21

### Mejorado

- El identificador técnico dejó de mostrarse en la experiencia principal y en el
  PDF.
- La interfaz indica de forma comprensible si la configuración es recomendada o
  personalizada.
- El identificador permanece en el JSON metodológico con una explicación de su
  finalidad técnica.

## [0.1.1] - 2026-07-21

### Mejorado

- Se corrigió el espacio superior de la aplicación para evitar que la barra de
  Streamlit cubriera la cabecera.
- “Preevaluación territorial” pasó a ser el título principal, con mayor tamaño y
  adaptación para pantallas pequeñas.
- Se retiró de la pantalla principal la línea interna de versión y metodología.

## [0.1.0] - 2026-07-21

### Añadido

- Nueva aplicación independiente en `app_experiencia.py`.
- Recorrido guiado para seleccionar el área, elegir el enfoque, revisar resultados
  y explorar evidencia cartográfica.
- Configuración recomendada para usuarios no especialistas y modo técnico mediante
  divulgación progresiva.
- Registro metodológico JSON con fuentes, periodos, umbrales, pesos y reglas.
- Informe PDF con resultados y seis mapas temáticos.
- Compatibilidad con fincas, toda la cuenca y polígonos dibujados por el usuario.

### Conservado

- El motor analítico de JRC TMF, Hansen, ESRI, GEDI y Sentinel-2/NDVI.
- El alcance indicativo: la aplicación no constituye validación de campo ni
  determina cumplimiento EUDR.

[0.2.0]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.7...v0.2.0
[0.1.7]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/julii5sos/visor-preevaluacion-territorial/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/julii5sos/visor-preevaluacion-territorial/releases/tag/v0.1.0
