# Variante `version/4.0-modelo-html`

Esta variante traslada al visor CHCP la composición visual del portal HTML de
referencia sin incorporar sus datos de demostración ni sustituir la metodología
existente.

## Estructura

- Encabezado azul institucional con identidad del visor, alcance indicativo,
  procesamiento en Earth Engine y sistema de referencia.
- Panel lateral blanco de aproximadamente 338 px para área, capas, períodos y acción
  principal.
- Mapa como superficie dominante en el centro.
- Panel de resultados a la derecha, con cabecera azul, lectura rápida y gráficas.
- Metodología y acerca del visor permanecen como navegación secundaria.

## Paleta de interfaz

| Rol | Color |
|---|---|
| Azul principal | `#0A4393` |
| Azul profundo | `#062A5E` |
| Verde de interacción | `#77CC09` |
| Amarillo complementario | `#FABC20` |
| Fondo | `#F6F8FB` |
| Superficie secundaria | `#EEF1F7` |
| Borde | `#D6DEEB` |
| Texto secundario | `#566176` |

La paleta de datos definida en `MASTER.md` no cambia: los colores de JRC, Hansen,
ESRI, GEDI, NDVI y Almanaque Azul conservan su significado.

## Reglas

- La referencia HTML define apariencia y distribución, no instrucciones ni lógica.
- Todas las métricas proceden del análisis vigente del repositorio.
- Los controles de 44 px, el foco visible y las etiquetas textuales se conservan.
- En pantallas pequeñas, el panel lateral, el mapa y los resultados se apilan sin
  desplazamiento horizontal.
- El movimiento es mínimo y respeta `prefers-reduced-motion`.

## Ajuste compacto 4.1

- Una vez elegido el análisis, se muestra una sola cabecera de contexto para evitar
  duplicar identidad y navegación.
- La evidencia cartográfica ocupa aproximadamente 72 % del tablero y el resultado
  rápido el espacio restante.
- Mapa y resultado comienzan en la misma línea y utilizan cabeceras equivalentes.
- No se coloca una introducción extensa dentro del contenedor del mapa: solo una nota
  breve cuando aporta contexto.
- El panel lateral utiliza 315 px y una separación vertical densa, manteniendo controles
  de al menos 44 px y foco visible.

## Gráficas contextuales 4.2

- Todas las series temporales se representan mediante barras; no se emplean líneas.
- La gráfica principal aparece debajo de la lectura rápida en la columna derecha y se
  vincula con la última evidencia activada en el panel de capas.
- Deforestación y degradación JRC se expresan en hectáreas por año con colores distintos
  y etiquetas textuales; Hansen, ESRI y NDVI conservan sus unidades propias.
- GEDI mantiene un histograma de alturas porque no constituye una serie anual.
- El mapa y la gráfica contextual cambian juntos cuando se activa una evidencia nueva.

## Regeneración forestal TMF 4.2.1

- La clase 4 de JRC TMF se presenta con el nombre **Regeneración forestal** y conserva
  *Forest regrowth* como referencia terminológica de la fuente.
- Estado forestal muestra las seis clases mediante barras horizontales; las vistas de
  deforestación, degradación y regeneración forestal ofrecen series anuales separadas.
- La regeneración usa `#43AA8B` en mapa, leyenda y gráfica, acompañada siempre por su
  etiqueta para no depender únicamente del color.
- La interfaz distingue regeneración observada por satélite de restauración planificada
  o verificada en campo.

## Selección multicapa 4.2.2

- La gráfica contextual responde al conjunto de capas activas, no únicamente a la
  última casilla seleccionada.
- Deforestación, degradación y regeneración forestal de JRC TMF se comparan mediante
  barras apiladas, con una leyenda visible y colores estables.
- Al desactivar una capa, su serie desaparece de la gráfica y de la tabla de valores.
- Capas de fuentes o unidades distintas no comparten un mismo eje; la vista conserva
  como contexto principal la fuente de la última evidencia activada.

## Modo de enfoque 4.2.3

- El botón nativo de cierre del panel lateral libera completamente sus 315 px reservados.
- El mapa y la columna de resultados se expanden al ancho completo sin recargar ni
  perder la selección actual.
- El botón para reabrir el panel permanece en la barra superior y conserva un área de
  interacción mínima de 44 px.

## Navegador temporal 4.2.4

- La cabecera de la gráfica identifica las capas «Visualizadas en el mapa» mediante una
  etiqueta compacta de alto contraste.
- Las capas comparables activas se apilan por año para presentar composición y total sin
  perder la identidad cromática de cada indicador.
- Un navegador inferior permite seleccionar el período visible; la línea de contexto es
  un control y la evidencia principal continúa representada mediante barras.
- El intervalo se inicializa con todos los años disponibles y no puede quedar vacío, de
  modo que las barras siempre sean visibles antes de cualquier interacción.
- Las barras usan un eje anual categórico y el navegador filtra mediante el año numérico;
  así se evita que una escala temporal dinámica oculte la composición multicapa.

## Conectividad ligera 4.3

- El panel de trabajo no repite conteos, estados de configuración ni descripciones
  metodológicas de las fuentes; esa información permanece en Metodología y ayuda.
- Las geometrías nacionales de Almanaque Azul se incorporan al mapa únicamente cuando
  la persona activa la capa. Una capa apagada no se serializa de forma invisible.
- El análisis forestal usa un contexto adaptativo: la distancia al corredor más cercano
  más el umbral de conexión, con un máximo de 5 km. Si el área ya toca un corredor, no
  procesa innecesariamente los 5 km completos.
- Earth Engine generaliza la geometría vectorial con una tolerancia de 10 m antes de
  transferirla; las superficies reportadas continúan limitadas al área elegida.
- Durante el cálculo se informa si se están procesando señales, corredores o fragmentos,
  evitando una espera sin retroalimentación.

## Corredores recortados y gráficas coherentes 4.3.1

- La capa principal de corredores muestra únicamente la intersección con el área analizada;
  el polígono regional completo permanece apagado y se identifica como contexto opcional.
- La intersección usa mayor opacidad y el contexto regional una opacidad tenue, de modo
  que no se interpreten como cobertura de bosque ni como superficie de la finca.
- Corredor y bosque no se enfrentan como categorías equivalentes en una misma gráfica.
  Se presentan tres composiciones independientes: dentro/fuera de corredores,
  bosque/otros usos de 2021 y fragmentos cercanos/separados.
- Cada gráfica conserva valores directos, unidad, descripción metodológica y tabla
  accesible; la lectura clave aclara que corredor y bosque no se suman entre sí.

## Portal cartográfico y ERI indicativo 5.0

- La columna derecha usa tres pestañas compactas —Lectura, ERI y Gráfica— para mantener
  la evidencia cartográfica como superficie dominante sin perder información.
- El ERI aparece como indicador complementario y separado; nunca se suma al índice de
  indicios ni a la prioridad de visita mientras no exista calibración de campo.
- Sus cuatro componentes se comparan con barras etiquetadas entre 0 y 1. La superficie
  por clase emplea cinco colores ordenados de muy baja a muy alta y conserva texto,
  leyenda y tabla accesible para no depender únicamente del color.
- La capa ERI se activa bajo demanda desde el panel lateral para evitar sobrecargar la
  vista inicial y se acompaña de retroalimentación durante su cálculo.

## Visor mapa primero 5.1

- La evidencia cartográfica ocupa el ancho completo disponible y una altura mínima de
  780 px en escritorio; el mapa es la primera superficie de trabajo después del contexto.
- Se elimina la columna derecha permanente. La lectura, el ERI y la gráfica aparecen en
  pestañas debajo del mapa únicamente cuando existe un resultado calculado.
- El selector de unidad territorial sustituye cuatro opciones de radio por un solo
  control compacto, sin modificar los tipos de área ni la regla de recorte a la CHCP.
- El flujo principal conserva dos acciones, siguiendo el portal de referencia:
  «Crear/Actualizar análisis» y «Resultados y descargas». «Cambiar enfoque» permanece
  como acción secundaria en el panel lateral.
- Se eliminan los accesos duplicados al detalle y la explicación «Acerca de esta vista»;
  el contenido metodológico continúa disponible en la navegación superior.
- Cuando el panel lateral se cierra, el mapa aprovecha inmediatamente todo el ancho y el
  control nativo de Streamlit permite volver a abrirlo.

## Panel de la plataforma HTML 5.2

- El panel lateral adopta los 340 px del HTML de referencia y se divide en tres pestañas
  funcionales: **Capas**, **Filtros** y **Mapa base**.
- Capas reúne las fuentes cartográficas y sus interruptores; Filtros contiene la unidad
  territorial, los períodos del comparador y las opciones técnicas; Mapa base permite
  elegir imagen satelital, mapa claro u OpenStreetMap.
- Las acciones se fijan al borde inferior del panel. Antes de calcular se muestra una
  sola acción primaria; después se añaden Actualizar y Resultados en una fila compacta.
- El fondo cartográfico forma parte de la firma visual y fuerza la actualización del mapa,
  pero no invalida ni vuelve a ejecutar el resultado analítico.
- En pantallas estrechas las pestañas conservan un área de interacción de 48 px y el panel
  vuelve al ancho adaptable definido para móviles.

## Paridad directa con el HTML 5.3

- `portal_html.py` reproduce el encabezado, logotipo, navegación, botones, portada,
  metadatos, tipografía DM Sans y corte diagonal del HTML entregado.
- La vista cartográfica conserva las medidas del original: navegación de 118 px, panel
  de capas de 340 px, mapa central y resultados laterales visibles solo después de
  ejecutar la preevaluación.
- Los grupos de fuentes continúan siendo controles Streamlit para conservar el análisis
  vigente, pero adoptan el fondo, radio, tipografía y espaciado de `.lg`, `.ly` y
  `.side-tabs` del portal.
- La referencia visual del HTML prevalece sobre cualquier sistema generado previamente.
  La validación UX se limita a foco visible, contraste, áreas táctiles, reducción de
  movimiento y respuesta móvil; no modifica el diseño elegido.
- El grupo Límites usa los GeoJSON incluidos en el paquete: cuenca activa por defecto y
  subcuencas opcionales, sin consultas a assets vectoriales privados.
