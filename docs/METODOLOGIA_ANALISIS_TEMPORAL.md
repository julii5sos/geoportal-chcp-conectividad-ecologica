# Metodología del análisis ecológico temporal

## Alcance

El módulo **Comparar** recalcula cobertura, fragmentación y conectividad estructural
para dos años. No reutiliza las métricas de la preevaluación territorial ni interpreta
un cambio visual del mapa como un resultado científico.

Cada período se procesa de forma independiente con exactamente la misma fuente,
versión, resolución espacial, área, distancia máxima entre parches, superficie mínima
de parche y regla de vecindad del ráster. El ERI, los corredores publicados y el índice
de preevaluación permanecen separados.

## Fuentes admitidas

### JRC Tropical Moist Forest — fuente principal

- Asset: `projects/JRC/TMF/v1_2025/AnnualChanges`.
- Período: 1990–2025.
- Resolución: 30 m.
- Bosque: clases 1 (TMF no perturbado), 2 (TMF degradado) y 4
  (*Forest regrowth* o regeneración forestal posterior a deforestación).
- No bosque: clases 3, 5 y 6.

La colección y las clases proceden de la documentación y el tutorial oficiales de
[JRC Forest Observations](https://forobs.jrc.ec.europa.eu/TMF/resources/tutorial/gee).

### ESRI Annual Land Cover — alternativa independiente

- Asset comunitario en Earth Engine:
  `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS`.
- Período: 2017–2025.
- Resolución: 10 m.
- Bosque operativo: clase 2, `Trees`.

La disponibilidad y la leyenda se verifican en el
[catálogo comunitario de Earth Engine](https://gee-community-catalog.org/projects/S2TSLULC/).
ESRI clasifica cobertura arbórea; no reproduce la definición de bosque húmedo tropical
de JRC. Sus métricas se muestran como un análisis alternativo y no se combinan con JRC.

### Fuentes que no generan este análisis

- NDVI describe vigor vegetal y no una cobertura bosque/no bosque.
- Hansen registra pérdida de cobertura arbórea respecto de una línea base; no ofrece en
  este módulo dos clasificaciones anuales simétricas de bosque/no bosque.
- GEDI no constituye una serie anual continua de cobertura.
- Bosque SINIA–MiAMBIENTE 2021 y ERI son referencias fijas.

La interfaz no ofrece estas fuentes para el recálculo temporal de fragmentación.

## Flujo de cálculo

1. El polígono dibujado se recorta al límite local de la CHCP, o se utiliza la
   subcuenca seleccionada.
2. Earth Engine recupera la banda anual y aplica la definición binaria de la fuente.
3. La máscara se vectoriza a la resolución nativa, con conectividad de ocho vecinos y
   sin `bestEffort`.
4. Los componentes menores al área mínima configurada se excluyen de ambos años.
5. `bosque_conectividad.py` calcula por separado superficie, parches, borde,
   aislamiento, componentes, relaciones dentro del umbral y estructura mínima.
6. Las geometrías se proyectan a Equal Earth Americas (`EPSG:8857`) para superficies
   y distancias.
7. Intersección y diferencias calculan bosque estable, pérdida y ganancia. GeoJSON,
   tabla comparativa y metadatos se entregan en un ZIP.

## Interpretación y limitaciones

- La red representa cercanía estructural potencial; no demuestra movimiento de fauna
  ni conectividad funcional para una especie.
- Un aumento de parches puede indicar fragmentación, pero debe interpretarse junto con
  superficie, componentes, aislamiento y escala espacial.
- Los bordes del área pueden cortar un parche. El módulo no usa bosque exterior para
  evitar que la comparación dependa de un contexto cambiante.
- El umbral de distancia debe justificarse según el objetivo ecológico y mantenerse
  idéntico entre años.
- La simplificación geométrica de media celda reduce el volumen transferido. La
  diferencia residual por redondeo debe permanecer muy por debajo de una celda.
- Errores de clasificación, nubes, dominio del producto y cambios de versión pueden
  afectar las diferencias. El resultado requiere interpretación y verificación de campo.

## Validación

- Las pruebas sintéticas construyen polígonos en `EPSG:8857` con áreas y separaciones
  conocidas y comprueban superficie, pérdida, parches, componentes y aislamiento.
- Las pruebas de integración verifican JRC y ESRI 2020–2025 cuando
  `RUN_EE_INTEGRATION=1` y `GEE_PROJECT_ID` están configurados.
- `scripts/validar_analisis_temporal.py` ejecuta el flujo completo sobre una ventana
  pequeña dentro de la CHCP y emite un resumen JSON reproducible.
