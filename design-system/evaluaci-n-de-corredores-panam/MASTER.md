# Sistema de diseño · Evaluación de Corredores Panamá

Este archivo adapta las recomendaciones de UI/UX al sistema institucional ya establecido por la aplicación de origen. La identidad existente prevalece sobre la paleta genérica sugerida por la herramienta.

## Principios

- Interfaz científica de tipo tablero cartográfico, con divulgación progresiva.
- Navegación principal persistente: Mapa, Metodología y ayuda, y Acerca del visor.
  Los resultados no ocupan una pestaña global: se abren únicamente después de ejecutar.
- Una vez elegido el análisis, la pantalla se organiza como visor: controles del área y
  capas a la izquierda, mapa a ancho completo como elemento dominante y resultados debajo.
- La explicación inicial desaparece durante el trabajo para no competir con el mapa.
- La ruta principal prioriza acción y decisión: configurar el área, ejecutar, leer la
  conclusión y revisar el mapa. La explicación técnica aparece únicamente cuando se solicita.
- Separar visualmente evidencia satelital, fuente cartográfica externa y cálculo propio.
- No depender solo del color: toda clase lleva etiqueta y explicación.
- Controles de al menos 44 px, foco visible y contraste WCAG AA.
- Sin desplazamiento horizontal a 375, 768, 1024 y 1440 px.
- Movimiento mínimo y desactivable con `prefers-reduced-motion`.

## Paleta institucional

| Rol | Valor |
|---|---|
| Verde principal | `#00544d` |
| Verde oscuro | `#00403a` |
| Acento | `#76b72a` |
| Fondo claro | `#f6faf8` |
| Superficie | `#ffffff` |
| Texto principal | `#00544d` |
| Texto secundario | `#356b61` |
| Borde | `#b6d1c8` |
| Error / alta atención | `#b42318` |
| Atención media | `#f79009` |

### Paleta de datos

| Fuente o lectura | Color |
|---|---|
| JRC TMF | `#1F8A70` |
| JRC TMF · regeneración forestal | `#43AA8B` |
| Hansen GFC | `#E76F51` |
| ESRI LULC | `#3A7CA5` |
| GEDI | `#7A5195` |
| NDVI | `#9BBF30` |

Las gráficas comparativas usan barras horizontales, una etiqueta de categoría y el
valor con su unidad. Los colores se mantienen estables entre el tablero y el detalle,
pero nunca sustituyen el texto o la tabla accesible.

Los colores originales de Almanaque Azul (`#345a01`, `#a1d303`, `#e0c504`) solo se usan en sus capas y leyendas, acompañados siempre por las etiquetas Alta, Mediana y Media-baja.

## Tipografía y densidad

- Se conserva la tipografía nativa y accesible de Streamlit para evitar descargas externas y saltos de diseño.
- Texto base mínimo de 16 px en controles y lectura principal.
- Interlineado de 1.5 o mayor en textos explicativos.
- Escala de espacio: 4, 8, 16, 24, 32, 48 y 64 px.
- Tarjetas compactas, sin sombras decorativas; jerarquía mediante borde, espaciado y encabezados.

## Componentes

- Barra superior compacta: identifica la cuenca, el tipo de preevaluación y su carácter
  indicativo sin repetir una portada extensa.
- Panel de fuentes: cada producto ocupa un bloque reconocible —JRC TMF, Hansen, ESRI,
  Sentinel-2/NDVI y GEDI— con sus capas y períodos propios. Corredores y bosque 2021
  permanecen en bloques separados.
- Panel de trabajo: tres pestañas de igual jerarquía —Capas, Filtros y Mapa base—
  separan visualización, selección territorial y fondo cartográfico. Las acciones se
  mantienen visibles al pie del panel sin mezclarse con las capas.
- Acción Crear análisis: botón primario al final del panel lateral; distingue los
  controles que solo cambian la visualización de la acción que ejecuta los cálculos.
- Tablero principal: mapa a ancho completo; la unidad, superficie, conclusión y los
  indicadores aparecen en una franja de resultados situada debajo.
- Resultados inmediatos: el mapa permanece visible y el bloque inferior alterna entre
  lectura rápida y gráficas compactas. Las gráficas principales se forman con el
  resultado ya calculado, usan barras a color con valores directos y ofrecen una tabla
  de valores como alternativa accesible.
- Resultados contextuales extensos: pestañas temáticas, descargas y una gráfica por
  fuente solicitada bajo demanda. Se abren con «Resultados y descargas», ofrecen «Volver
  al mapa» y no vuelven a construir el mapa.
- Resultados completos: pestañas visibles por tema —resumen, cambios territoriales,
  corredores y bosque/conectividad—; no se eliminan datos ni se esconden tras casillas.
- Botón primario: fondo `#00544d`, texto blanco y foco de 3 px.
- Botón secundario: superficie blanca, borde `#00544d` y texto del mismo color.
- Resultados: métricas en cuadrícula adaptable; tablas con encabezados explícitos.
- Resumen ejecutivo: una conclusión de prioridad y cuatro indicadores clave antes del mapa.
- Mapas: grupos independientes para capas temáticas, corredores externos, parches calculados y referencias.
- Los controles de capas y las leyendas se mantienen fuera del mapa para no cubrir la evidencia espacial.
- Alertas metodológicas: borde izquierdo de 4–5 px y texto que explique qué participa o no en el índice.
- Ficha PDF: resumen ejecutivo en la primera página, un objetivo cartográfico por
  página y detalle técnico al final.
- Mapas impresos de fragmentación y conectividad: fondo neutro sin imagen satelital,
  límite visible y leyenda externa. El mapa de fragmentación no dibuja relaciones;
  el de conectividad muestra únicamente la estructura esencial y una ruta potencial.
- Puntaje impreso: tabla de aportes por fuente y nota explícita de que el total no
  representa número de capas coincidentes ni probabilidad de deforestación.

## Reglas de interacción

- La cobertura institucional se configura una sola vez mediante un asset privado; la interfaz pública no solicita shapefiles.
- Antes de ejecutar se muestran el área, las capas y el mapa; períodos, fuentes y entregables permanecen en desplegables cerrados.
- Después de ejecutar, los bloques completos de cambios, corredores y conectividad se activan por separado y comienzan cerrados.
- Ninguna métrica, gráfico, tabla o descarga se elimina para reducir la densidad visual; solo cambia el momento en que se presenta.
- Los controles del mapa permanecen en el panel lateral y los resultados se consultan por
  pestañas, siguiendo el patrón de los visores ambientales profesionales.
- Capas es la pestaña inicial; Filtros reúne el área, los años y los parámetros técnicos;
  Mapa base cambia únicamente el contexto visual y nunca la metodología.
- Al cerrar el panel lateral, el tablero entra en modo de enfoque: mapa y resultados
  ocupan todo el ancho, mientras el control nativo para reabrir el panel permanece visible.
- Las gráficas de JRC, Hansen, ESRI y NDVI conservan su propia unidad y significado; no
  se superponen fuentes incompatibles en una misma escala. GEDI usa una distribución de
  alturas y no una falsa serie temporal.
- Cuando se activan dos o tres capas comparables de una misma fuente, la gráfica
  contextual las reúne como barras apiladas. Cada serie mantiene color, leyenda,
  tooltip y columna propia en la tabla accesible.
- Las series anuales extensas incorporan un navegador temporal inferior; su área fina
  funciona únicamente como control de rango y no sustituye la lectura principal de barras.
- Las series se calculan una por vez, se almacenan temporalmente en caché y nunca bloquean
  la carga inicial del mapa o del resultado principal.
- Antes de ejecutar solo aparece una indicación compacta bajo el mapa; no se reserva una
  columna permanente para resultados vacíos. Al finalizar, la lectura rápida aparece debajo.
- La conectividad se presenta con parches, estructura esencial, ruta potencial al corredor y separaciones en capas independientes.
- La lectura principal usa «fragmentos cercanos o separados»; nodo, arista, componente y densidad quedan reservados para el detalle técnico opcional.
- Los fragmentos se muestran por defecto. La red completa nunca se dibuja: la capa técnica usa el árbol mínimo de cada grupo, con trazo verde oscuro y halo blanco.
- La ruta potencial al corredor usa una única línea naranja discontinua con halo blanco; no compite con las categorías originales de Almanaque Azul.
- El contexto forestal exterior participa en la conectividad y puede mostrarse mediante una capa verde independiente, apagada por defecto. Al activarla, el mapa amplía la vista solo al contexto adaptativo necesario —hasta 5 km— para explicar la ruta al corredor, pero nunca amplía la superficie reportada.
- Los errores aparecen junto al archivo o campo que los produce.
- La aplicación nunca presenta `Alta/Media/Baja` de parches como si fueran las categorías de Almanaque Azul.
- Los enlaces de fuente permanecen visibles en resultados, metodología y atribuciones.

## Verificación previa a entrega

- [x] Foco visible y controles de 44 px.
- [x] `prefers-reduced-motion` respetado.
- [x] Sin desbordamiento horizontal a 375, 768 y 1440 px.
- [x] Leyendas con texto además de color.
- [x] Leyendas y controles temáticos fuera del mapa interactivo.
- [x] Red técnica apagada por defecto y explicación para personas sin experiencia GIS.
- [x] Carga sin secretos produce un mensaje amigable, no un traceback público.
- [ ] Verificar el flujo completo con secretos válidos de Earth Engine en el entorno de despliegue.
- [x] Verificar el shapefile nacional real y confirmar el campo/valor de bosque.
- [x] Ofrecer una tabla alternativa a la red cartográfica para no depender solo del mapa o del color.
- [x] Eliminar enlaces redundantes y asegurar contraste de las líneas sobre imagen satelital.
- [x] Explicar que la ruta al corredor es estructural potencial, no conectividad funcional.
- [x] Mostrar acción y resultado antes de los detalles, con todos los datos técnicos disponibles bajo demanda.
- [x] Separar fragmentación y conectividad en dos mapas impresos sin fondo satelital.
- [x] Mantener las leyendas fuera de los mapas en la ficha PDF.
- [x] Desglosar el puntaje y diferenciarlo de la coincidencia espacial.
