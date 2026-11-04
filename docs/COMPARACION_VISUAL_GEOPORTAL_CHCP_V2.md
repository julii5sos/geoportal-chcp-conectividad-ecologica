# Comparación visual · HTML original y Geoportal CHCP 2.0

Fecha de verificación local: 4 de noviembre de 2026

Rama: `feature/geoportal-chcp-v2`

URL comprobada: `http://127.0.0.1:8510`

## Referencias usadas

- Fuente principal: plantillas y estilos extraídos de `conectividad_canal.zip`.
- Referencias complementarias: Copernicus Browser para la jerarquía cartográfica,
  MapBiomas para las fuentes/categorías/años y Global Forest Watch para la lectura
  de resultados.
- Capturas actuales verificadas con Chrome mediante CDP, después de que Streamlit
  terminara de renderizar. No son maquetas ni imágenes inventadas.

## Diferencias y resolución

| Elemento | Situación anterior | HTML original | Implementación actual |
|---|---|---|---|
| Encabezado | Barra de Streamlit y navegación poco jerárquica | Franja azul fija, utilidad superior, marca, navegación y CTA | Encabezado fijo de 118 px con la misma composición, colores y estados activos |
| Identidad | Verde grisáceo y tarjetas genéricas | Azul `#0a4393`, azul profundo `#062a5e`, verde `#77cc09`, amarillo `#fabc20` | Variables visuales unificadas con esos colores y tipografía DM Sans |
| Navegación | Pestañas que repetían funciones y abrían vistas poco claras | Navegación institucional y plataforma diferenciadas | Inicio, Explorar, Comparar, Analizar, ERI, Resultados, Metodología y Acerca; todos los enlaces permanecen en la misma ventana |
| Panel lateral | Formulario largo y mezcla de configuración/metodología | Panel fijo de 340 px con pestañas y acción inferior | `Capas / Polígono / Mapa base`, grupos plegables y botón inferior fijo |
| Área territorial | Finca, subcuenca, dibujo y cuenca | Flujo cartográfico directo | Dibujo primero, subcuenca segundo y cuenca completa tercero; las fincas no aparecen |
| Selector de capas | Lista extensa sin jerarquía consistente | Bloques temáticos con interruptores y metadatos | Límites, JRC TMF, Hansen, ESRI, Sentinel-2 NDVI, GEDI y ERI, con años o referencia real |
| Mapa | Compartía protagonismo con texto y pasos | Superficie central dominante | Mapa ocupa el centro; panel y resultados quedan subordinados |
| Resultados | Elementos dispersos y navegación vertical larga | Panel de lectura compacto | Mantiene indicadores, estadísticas, barras, tablas y descargas solo después de un cálculo real |
| Botones | Algunos controles podían parecer disponibles sin motor | Acciones con estado claro | El cálculo se deshabilita y explica cuando faltan credenciales; no se generan resultados de demostración |
| Tipografía y radios | Estilos heredados de Streamlit | DM Sans, radios pequeños y botones tipo píldora | Se aplican los mismos criterios, con foco visible y objetivos táctiles de 44 px |

## Fidelidad verificada

- Encabezado: 1600 × 118 px en la captura de escritorio.
- Panel: 340 px de ancho, inicia debajo del encabezado.
- Contenido del mapa: comienza en `y=118`, sin franja vacía superior.
- Ancho total: 1600 px para un viewport de 1600 px; no existe desplazamiento horizontal.
- Portada móvil: 375 px de viewport y 375 px de contenido, sin desplazamiento horizontal.
- Vista horizontal: el mapa y el panel comienzan en `y=76`, exactamente debajo del
  encabezado móvil, sin franja vacía.
- La acción principal permanece fija en la parte inferior del panel.
- El mapa local usa límites reales de cuenca y subcuencas y permite dibujar,
  editar y eliminar polígonos.

## Capturas reales

- `artifacts/screenshots/geoportal-v2-inicio.png`
- `artifacts/screenshots/geoportal-v2-explorar-local.png`
- `artifacts/screenshots/geoportal-v2-comparar-local.png`
- `artifacts/screenshots/geoportal-v2-inicio-375.png`
- `artifacts/screenshots/geoportal-v2-explorar-horizontal.png`

La captura local muestra el estado honesto sin secretos de Earth Engine: el mapa
territorial funciona y los productos remotos quedan deshabilitados con una explicación.

## Desviaciones deliberadas respecto al HTML

- No se incorporaron fincas ni un radio artificial de 10 km.
- No se copiaron resultados de demostración ni botones sin implementación.
- El selector de idioma conserva español; inglés aparece como no disponible.
- Los análisis científicos existentes siguen en Python/Earth Engine y no se
  reemplazaron por el motor de demostración incluido en la referencia.
- Las tarjetas de resultados solo aparecen tras una ejecución válida.

## Comparación temporal: alcance científico actual

Los selectores temporales de JRC TMF, ESRI y Sentinel-2 NDVI cambian las capas y
la comparación visual. Actualmente **no recalculan** el índice territorial, la
fragmentación, la conectividad, los corredores ni el ERI con los años elegidos.

La ejecución científica continúa usando los períodos metodológicos fijados en
`metodologia_indice.py`: JRC hasta 2025, Hansen 2001–2025 con lectura post-2020,
ESRI 2017–2024 y NDVI 2020–2025. La consulta visual ESRI sí ofrece su edición
publicada 2025, sin incorporarla silenciosamente al índice. Las series anuales se calculan para el área
activa cuando se solicitan, pero sirven como evidencia contextual y no alteran
el puntaje. GEDI y ERI se presentan como referencias fijas, no como series
temporales homogéneas.

## Pendientes de la fase siguiente

- Repetir las capturas con una sesión que disponga de credenciales válidas de
  Earth Engine para documentar mapa, indicadores y gráficos finales.
- Hacer que la elección de años pueda iniciar una variante científica del
  análisis; requiere definir y validar una metodología nueva, no solo interfaz.
- Completar una prueba manual multiusuario en Streamlit Cloud antes de publicar.
- Validar el diseño en móviles físicos y con lectores de pantalla.
