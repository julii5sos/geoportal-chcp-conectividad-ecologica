# Fase 7 · Buscador, panel territorial y comparación JRC–ESRI

## Flujo implementado

`Inicio → búsqueda territorial → Panel → Plataforma → asistente de cuatro pasos → resultado/descarga`.

La selección se guarda en `localStorage` con un identificador estable (`cuenca:chcp` o `subcuenca:<slug>`). Al abrir Plataforma, el territorio se recupera, se resalta, se centra y prepara la unidad del asistente. Cambiar de pestaña no ejecuta Earth Engine.

## Consulta frente a análisis

- **Consulta:** `territorio_busqueda.resumen_territorial` calcula área local e intersecciones con corredores/puntos. No incluye cifras forestales inventadas.
- **Análisis:** `POST /api/v1/analyses` valida geometría y límites, inicializa Earth Engine de forma diferida y utiliza caché por solicitud científica completa.
- **ERI:** `POST /api/v1/eri` permanece independiente.

## Modalidad integrada

`analisis_integrado.ejecutar_analisis_integrado_ee` ejecuta `ejecutar_analisis_temporal_ee` una vez para JRC y una vez para ESRI, con el mismo polígono, años, distancia y área mínima. Los resultados completos de cada fuente se conservan.

### Período común

La comparación admite 2017–2025. No interpola años ausentes ni permite elegir años fuera de la intersección temporal.

### Armonización

1. JRC conserva su malla de 30 m.
2. ESRI se transforma primero en una clase binaria con máscara válida propia.
3. ESRI se agrega a la proyección JRC con `ee.Reducer.mode()`; al ser categórico no usa interpolación bilineal.
4. La comparación se limita a la intersección de máscaras válidas de ambas fuentes y ambos años.
5. El área de cada clase se calcula con `pixelArea` a 30 m.

Esta operación permite comparar, pero no hace equivalentes las definiciones temáticas.

## Clases mutuamente excluyentes

### Estado final

1. Bosque en ambas.
2. No bosque en ambas.
3. Bosque solo según JRC.
4. Bosque solo según ESRI.
5. Sin datos comparables.

### Cambio

1. Pérdida en ambas.
2. Pérdida solo JRC.
3. Pérdida solo ESRI.
4. Ganancia en ambas.
5. Ganancia solo JRC.
6. Ganancia solo ESRI.
7. Otros cambios o ausencia de cambio, incluidas direcciones opuestas.
8. Sin datos comparables.

Las funciones puras `clasificar_estado` y `clasificar_cambio` se prueban sin Earth Engine. La simbología procede de `simbologia_geoportal.py` y se entrega por `/api/v1/config` para mapa, leyenda y gráficas.

## Indicadores

- superficie coincidente y discrepante;
- porcentaje de concordancia con denominador de área válida común;
- diferencia JRC menos ESRI de superficie forestal final;
- áreas de pérdida y ganancia coincidentes o exclusivas;
- métricas independientes de fragmentación y conectividad de ambas fuentes.

La concordancia entre productos no se presenta como validación de campo.

## Interfaz

- El buscador acepta coincidencias parciales, ignora tildes/mayúsculas y tiene navegación por teclado.
- El Panel contiene ocho pestañas y marca indicadores científicos sin cálculo como **No calculado**.
- Plataforma ofrece JRC, ESRI e Integrado en el mismo selector con años reales.
- El panel izquierdo conserva fuentes complementarias catalogadas, pero deshabilita las que no poseen ruta funcional.
- Las capas de concordancia tienen leyenda dinámica y control de opacidad; este control no recalcula resultados.
- La descarga integrada incluye el resultado completo, resumen de concordancia, resultados individuales de ambas fuentes, área y metodología.

## Limitaciones

- La definición JRC TMF no es la clase `Trees` de ESRI.
- Un cambio de clase no demuestra restauración o deforestación verificada en campo.
- La conectividad es estructural; no representa desplazamiento de especies.
- El borde del polígono afecta parches, aristas y aislamiento.
- No hay métricas independientes de exactitud temática para esta zona dentro del proyecto.
- Los mapas de teselas son temporales y se excluyen de los ZIP; el JSON conserva clases, áreas, método y resultados vectoriales disponibles.

## Pruebas focalizadas

- `test_territorio_busqueda.py`: catálogo, búsqueda y ausencia de cifras ficticias.
- `test_analisis_integrado.py`: período, exclusividad de clases, denominadores y diferencia forestal.
- `test_catalogo_multifuente.py`: estados de integración y fuentes no operativas.
- `test_simbologia_geoportal.py`: semántica y unicidad de paletas.
- `test_web_api.py`: endpoints de búsqueda, Panel, catálogo y contrato integrado.
- `test_web_frontend.py`: componentes del buscador, Panel y concordancia.

La integración real en Earth Engine debe ejecutarse una sola vez sobre un polígono pequeño con credenciales locales. Un fallo de autenticación o cuota no debe convertirse en reintentos automáticos.

