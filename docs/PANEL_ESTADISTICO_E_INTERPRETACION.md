# Panel estadístico e interpretación ecológica

## Alcance

Este documento describe el panel derecho del comparador temporal del Geoportal
CHCP 2.0. El panel permanece junto al mapa y usa exclusivamente resultados del
motor temporal; no presenta valores de demostración. JRC TMF y ESRI Annual Land
Cover se procesan por separado porque sus dominios, resoluciones y definiciones
de bosque no son equivalentes.

## Área geométrica, área válida y NoData

Para cada año `t` se calculan, en hectáreas:

- `A_geom`: superficie geodésica del polígono seleccionado.
- `A_valid,t`: píxeles con una clase válida de la fuente en el año `t`.
- `A_forest,t`: píxeles válidos clasificados como bosque.
- `A_nonforest,t = A_valid,t - A_forest,t`.
- `A_nodata,t = max(0, A_geom - A_valid,t)`.

Los porcentajes se calculan sobre la clasificación válida:

```text
forest_pct,t    = 100 * A_forest,t / A_valid,t
nonforest_pct,t = 100 * A_nonforest,t / A_valid,t
```

NoData no se suma a no bosque. La rasterización puede incluir píxeles de borde
cuyo centro o superficie efectiva no coincide exactamente con el límite
vectorial. Esa diferencia se informa con una tolerancia geométrica separada de
la tolerancia usada para comprobar el cierre de las transiciones.

## Máscara comparable y transiciones

Las transiciones se calculan solo donde ambos años tienen datos válidos:

```text
V_common = V_initial AND V_final
```

En esa máscara se obtienen cuatro clases mutuamente excluyentes:

```text
stable_forest    = forest_initial AND forest_final
loss             = forest_initial AND NOT forest_final
gain             = NOT forest_initial AND forest_final
stable_nonforest = NOT forest_initial AND NOT forest_final
```

La comprobación de cierre exige:

```text
stable_forest + loss + gain + stable_nonforest = A_common
```

La tolerancia numérica es el área de un píxel nativo: 0.09 ha para JRC TMF a
30 m y 0.01 ha para ESRI a 10 m. Esta tolerancia no se sustituye por una
tolerancia amplia basada en el perímetro.

Los indicadores relativos usan denominadores explícitos:

- Pérdida relativa = `loss / (stable_forest + loss)`.
- Ganancia relativa = `gain / (stable_nonforest + gain)`.
- Bosque estable = `stable_forest / (stable_forest + loss)`.

Si un denominador es cero, el indicador se reporta como no aplicable.

## Cambio forestal neto

Todos los cambios se calculan sobre `V_common`:

```text
net_ha        = gain - loss
initial_pct   = 100 * (stable_forest + loss) / A_common
final_pct     = 100 * (stable_forest + gain) / A_common
net_pp        = final_pct - initial_pct
relative_pct  = 100 * net_ha / (stable_forest + loss)
```

`relative_pct` se muestra como no aplicable cuando el bosque inicial comparable
es cero. Una ganancia es un cambio de clase satelital; no se presenta como
restauración ecológica comprobada.

## Fragmentación y conectividad

El panel reutiliza los resultados de `bosque_conectividad.py` sin cambiar las
reglas científicas. Compara área forestal, número de parches, tamaño medio,
densidad de parches, índice del parche mayor, densidad de bordes y distancia al
vecino más cercano. La etiqueta de aumento de fragmentación exige concordancia
de al menos cuatro de seis señales; si hay señales opuestas se explicita la
contradicción.

La conectividad presenta conexiones, componentes, parches aislados, proporción
de parches con grado mayor que cero y proporción de nodos en el componente
principal. Una tendencia se declara solo con al menos tres de cuatro señales
concordantes y sin señales opuestas. Se trata de conectividad estructural
potencial, no de movimiento observado de fauna.

## Fuentes y máscaras válidas

### JRC Tropical Moist Forest

- Producto: JRC TMF `AnnualChanges`.
- Versión registrada por la aplicación: `JRC TMF v1_2025`.
- Resolución nominal: 30 m.
- Clases válidas: 1 a 6.
- Fuera del dominio/NoData: 0 o píxel enmascarado.
- Bosque: clases 1 y 2, de acuerdo con la definición documentada en
  `analisis_temporal.py`.

### ESRI Annual Land Cover

- Producto: `Esri/AnnualLandCover/9-Class`.
- Versión registrada: `ESRI 10 m Annual Land Cover 2017–2025`.
- Resolución nominal: 10 m.
- Bosque: clase 2 (`Trees`).
- Válidas para la comparación: clases 1, 2, 4, 5, 7, 8, 9 y 11.
- Nube (10), desconocido y píxeles enmascarados: NoData.

No se combinan métricas de ambas fuentes dentro de una comparación.

## Interpretación automática

`generar_interpretacion_ecologica()` usa reglas deterministas. Describe los
porcentajes inicial y final, pérdida, ganancia y cambio neto; después evalúa
fragmentación y conectividad mediante las reglas de concordancia anteriores.
También enumera señales contradictorias y limitaciones de la fuente. No atribuye
causas como agricultura, incendios o urbanización sin evidencia adicional.

El ERI permanece independiente. Puede consultarse como evaluación
complementaria, pero no forma parte del cambio temporal ni modifica sus pesos.

## Ejemplo real verificado con Earth Engine

El 5 de noviembre de 2026 se ejecutó desde la interfaz local una comparación
JRC TMF 2020–2025 para la subcuenca Lago Miraflores. El panel reportó:

| Indicador | Resultado |
|---|---:|
| Área geométrica | 4,453.6 ha |
| Área válida 2020 | 4,452.6 ha |
| Área válida 2025 | 4,452.6 ha |
| NoData por año | 1.0 ha |
| Bosque 2020 | 163.7 ha (3.7 %) |
| Bosque 2025 | 180.8 ha (4.1 %) |
| Bosque estable | 163.2 ha |
| Pérdida bruta | 0.5 ha |
| Ganancia detectada | 17.5 ha |
| No bosque estable | 4,271.4 ha |
| Cambio neto | +17.0 ha |
| Cambio en cobertura | +0.38 puntos porcentuales |
| Variación relativa | +10.4 % |

Las cuatro transiciones sumaron 4,452.62 ha, con diferencia `+0.0000 ha`
respecto a la máscara común, dentro de la tolerancia de 0.09 ha. Este ejemplo
verifica funcionamiento y consistencia aritmética; no constituye una validación
temática independiente de la clasificación.

## Pruebas

- 114 pruebas del repositorio: aprobadas; 3 pruebas de Earth Engine se omiten
  automáticamente cuando no hay credenciales.
- 3 pruebas de integración con credenciales: aprobadas (ESRI 2020–2025, máscara
  JRC y cierre real de transiciones JRC).
- Casos unitarios nuevos: porcentajes, NoData, máscaras no coincidentes,
  pérdida, ganancia, cambio neto, puntos porcentuales, bosque inicial cero,
  cierre de transiciones e interpretación con señales concordantes y
  contradictorias.
- Recorrido de interfaz real: selección de subcuenca, asistente de cuatro pasos,
  ejecución JRC 2020–2025, actualización del mapa, gráficos, interpretación y
  control de descarga.

## Limitaciones pendientes

1. El análisis mide cambios de clasificación; no identifica por sí solo causas
   ni confirma restauración.
2. Los parches pequeños y los bordes son sensibles a la resolución, al umbral
   mínimo de parche y al recorte por el polígono.
3. La conectividad es estructural y depende de la distancia máxima configurada.
4. JRC TMF representa su dominio de bosque húmedo tropical; ESRI usa una clase
   global de árboles. Sus valores no deben compararse directamente.
5. Hace falta validación temática independiente con datos de campo o muestras
   de referencia para estimar exactitud por clase y del cambio.
6. La prueba visual en navegador fue realizada en escritorio. El diseño móvil
   conserva el flujo, pero los gráficos complejos requieren una última revisión
   manual en varios dispositivos antes de publicar.

