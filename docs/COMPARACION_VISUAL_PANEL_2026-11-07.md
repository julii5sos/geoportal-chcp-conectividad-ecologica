# Comparación visual del Panel territorial

Referencia de diseño: capturas entregadas por la usuaria (panel analítico a la
izquierda, mapa persistente a la derecha, pestañas, tarjetas, gráficas y control
compacto de capas). Las cifras y categorías demostrativas de esas referencias
no se trasladaron al geoportal.

## Antes de esta mejora

- En el ancho reducido observado durante la inspección, las tarjetas aparecían
  antes del mapa y este quedaba fuera de la primera pantalla.
- La vista informativa dependía principalmente de texto y tarjetas.
- Las cifras utilizaban una jerarquía cromática débil.
- Las descargas no distinguían entre informe interpretativo y datos técnicos.
- Los ocho assets oficiales no tenían un catálogo central visible.

## Después

### Plataforma de análisis

- La plataforma usa la composición aprobada de tres áreas: controles 23 %, mapa
  39 % y resultados 38 % en escritorio. El mapa conserva el protagonismo y no se
  desmonta al cambiar de resultado.
- La navegación científica ya no aparece como una matriz de seis botones blancos.
  Cuatro secciones forman una sola franja azul integrada en la cabecera del panel:
  `Resumen`, `Dinámica del bosque`, `Fragmentación y conectividad` y
  `Coberturas oficiales`.
- Corredores se presentan dentro de conectividad; interpretación, limitaciones e
  informe se mantienen como detalle desplegable del resumen. Esto elimina rutas
  visuales duplicadas sin ocultar resultados científicos.
- Antes de ejecutar Earth Engine, el panel muestra solo contexto territorial real
  calculado localmente: superficie, corredores y puntos críticos. No presenta
  indicadores científicos ficticios.
- Repetir exactamente la misma área, componentes y parámetros en la sesión reutiliza
  el resultado ya montado. La caché del servidor conserva hasta seis resultados por
  una hora; no se modificaron fórmulas ni umbrales científicos.

- En escritorio, resultados y mapa se presentan como un único espacio de
  trabajo en una relación aproximada 40/60; el mapa permanece fijo mientras se
  recorre el panel.
- El selector territorial, la procedencia del resultado, los dos indicadores de
  contexto y el contenido temático forman ahora una sola columna analítica. Ya
  no existe una tercera barra lateral ni una fila de cuatro KPI desconectada.
- Las cinco preguntas principales (`Resumen`, `Cobertura y cambio`,
  `Fragmentación y conectividad`, `Corredores` e `Interpretación e informe`)
  son visibles sin scroll horizontal. Comparación, concordancia, coberturas
  nacionales y ERI están en un selector secundario explícito.
- La cabecera azul, el selector territorial, las pestañas y los widgets forman
  una única columna analítica de hasta 600 px; el mapa ocupa todo el espacio
  restante y no se desmonta al navegar.
- Cambiar de vista sincroniza el título y las capas del mapa sin ejecutar un
  análisis nuevo. En `Corredores` se activan los polígonos y puntos críticos
  publicados; las rutas modeladas solo aparecen cuando pertenecen a un resultado
  estructural guardado.
- En móvil, el mapa se presenta primero y luego el contenido analítico.
- La validación real del navegador a 536 px confirmó
  `scrollWidth = clientWidth = 536`: no existe desbordamiento horizontal del
  documento; el mapa conserva 360 px de altura útil.
- Las pestañas preservan los módulos existentes y admiten enlaces directos con
  `?tab=` para revisión y documentación.
- Sin un resultado, el Panel ya no dibuja barras de disponibilidad temporal:
  muestra fuentes en fichas compactas y una acción clara para calcular. Así no
  se confunden años disponibles con superficie, tendencia o cambio forestal.
- Cuando existe un resultado real, las gráficas utilizan sus métricas calculadas.
- Las tarjetas y alertas usan colores semánticos de alto contraste para bosque,
  agua, alertas, prioridad y datos neutros.
- El control de capas y opacidad está sobre el mapa y evita botones dispersos.
- El PDF y el ZIP son acciones separadas y se construyen desde el mismo
  `result_id`; descargar no vuelve a ejecutar Earth Engine.
- `Explorar mapa` ajusta y enfoca la cartografía; `Ejecutar análisis` abre el
  flujo científico. Ya no son dos enlaces equivalentes.

## Validación de interacción de esta integración

- `?tab=fragmentation` continúa aceptándose y abre la vista agrupada
  `Fragmentación y conectividad`.
- La navegación estructural actualiza el título del mapa a `Parches y red
  estructural` y conserva el mapa Leaflet montado.
- La vista `Interpretación e informe` presenta el estado vacío correcto si no
  hay un resultado persistido; no inventa un PDF ni cifras.
- Cambiar pestaña no invoca endpoints de análisis de Earth Engine.

## Evidencia real

- [Panel corregido con mapa simultáneo](capturas/panel_corregido.png)
- [Plataforma con controles NDVI y coberturas nacionales](capturas/plataforma_capas_corregida.png)
- [Portada ampliada](capturas/inicio_ampliado.png)
- [Catálogo de ocho assets oficiales](capturas/catalogo_assets.png)

## Diferencias deliberadas respecto a las referencias

- No se muestran cifras nacionales ni clases de demostración.
- No se presentan bosque maduro, bosque secundario o manglar como resultados si
  la fuente real seleccionada no los distingue.
- No se dibuja una serie anual inventada. Sin resultado científico, solo se
  comunica fuente, método, alcance y la acción necesaria para calcular.
- La comparación 2021–2023 continúa deshabilitada hasta demostrar equivalencia
  metodológica.
