# Validación de fragmentación y conectividad estructural

**Fecha:** 5 de noviembre de 2026  
**Rama:** `feature/interfaz-html-definitiva`  
**Commit base auditado:** `820a7d5bfc0c9b7cd2308fc15b7476561067cc62`

## Dictamen

El motor calcula de forma reproducible fragmentación y conectividad **estructural
potencial** sobre una cobertura binaria bosque/no bosque. Las pruebas sintéticas
confirman el recorte, las superficies, el número de parches, las relaciones por
distancia, los componentes y los parches aislados. Las ejecuciones reales de JRC TMF
y ESRI 2020–2025 confirman que el flujo Earth Engine funciona.

Esto no constituye validación ecológica funcional ni prueba de movimiento de fauna.
La sensibilidad a la fuente, la resolución, el umbral de distancia, el área mínima y
el borde del polígono debe mantenerse visible en toda interpretación.

## Trazabilidad del procedimiento

| Etapa | Implementación | Evidencia | Estado |
|---|---|---|---|
| Cobertura anual | `analisis_temporal.construir_cobertura_bosque_ee()` | JRC: estados 1, 2 y 4; ESRI: clase 2 `Trees` | Implementado y verificado operativamente |
| Componentes ráster | `vectorizar_cobertura_ee()` | `reduceToVectors`, ocho vecinos, escala nativa, `bestEffort=False` | Implementado y verificado |
| Recorte territorial | `analizar_fragmentacion_geojson()` | Intersección con el AOI y reparación geométrica | Implementado y verificado |
| Parches | `_calcular_metricas_parches()` | Una geometría poligonal válida por componente conservado | Implementado y verificado |
| Red | `_calcular_metricas_parches()` | Nodos = parches; aristas si la distancia entre bordes no supera el umbral | Implementado y verificado |
| Comparación | `analizar_comparacion_geojson()` | Ambos años se recalculan con los mismos parámetros | Implementado y verificado |
| Transiciones | `calcular_transiciones_cobertura()` | Bosque estable, pérdida y ganancia sobre la cobertura filtrada | Implementado y verificado |

## Métricas auditadas

- **Área forestal:** suma del área proyectada de los parches conservados, en hectáreas.
- **Porcentaje de bosque:** área forestal / área del paisaje × 100.
- **Número de parches:** componentes poligonales después de recorte y filtro mínimo.
- **Tamaño medio y mediano:** estadísticos de las áreas de los parches.
- **Densidad de parches:** parches / área del paisaje × 100 ha.
- **Densidad de borde:** suma de perímetros / área del paisaje, en m/ha.
- **Distancia entre parches:** distancia mínima borde a borde en la proyección métrica.
- **Componentes:** componentes conexos del grafo definido por el umbral.
- **Parches aislados:** nodos con grado cero.
- **Componente mayor:** porcentaje de nodos perteneciente al mayor componente.
- **Densidad de red:** densidad de NetworkX sobre la red de parches.

El mapa de relaciones muestra un árbol de expansión mínimo por componente para evitar
una maraña visual, pero `numero_aristas` conserva todas las relaciones que cumplen el
umbral. La diferencia se prueba en
`test_mapa_resume_la_red_completa_con_una_estructura_minima()`.

## Unidades, escala y proyección

- Las coberturas se vectorizan a **30 m para JRC TMF** y **10 m para ESRI**.
- Las áreas y distancias se calculan en `EPSG:8857` (Equal Earth).
- `EPSG:8857` conserva áreas globalmente y evita calcular hectáreas en grados; es
  apropiada para las superficies. No es una proyección equidistante, por lo que las
  distancias borde a borde son aproximadas.
- Para publicación se recomienda un análisis de sensibilidad frente a una proyección
  local apropiada para la CHCP, manteniendo los resultados existentes sin alterar
  hasta documentar el efecto.
- La simplificación posterior a la vectorización usa media celda; el área del
  componente se calcula antes de simplificar en Earth Engine.

## Efecto del límite del polígono

El análisis temporal usa `contexto_exterior=False`. Por tanto:

1. la cobertura se recorta al área elegida;
2. un parche que continúa fuera del límite queda truncado;
3. la superficie, el perímetro, el tamaño del parche y su relación con vecinos pueden
   cambiar por el borde;
4. un parche conectado fuera del AOI puede aparecer aislado dentro del AOI.

Este comportamiento es coherente para comparar dos años dentro del mismo límite, pero
las métricas describen el **paisaje recortado**, no toda la red ecológica circundante.
El motor general sí posee un modo explícito de contexto exterior y una prueba que
confirma que puede considerarlo sin dibujar geometrías fuera del área; la comparación
temporal lo desactiva deliberadamente para mantener igual el dominio de ambos años.

## Casos sintéticos

Las pruebas verifican, entre otros casos:

- tres parches, una arista y dos componentes con umbral de 500 m;
- dos parches conectados y uno aislado;
- cobertura vacía con todas las métricas en cero;
- `GeometryCollection` válida sin depender de la clave `coordinates`;
- cambio del umbral que modifica la red, pero no la superficie forestal;
- recorte de un dibujo al límite de la cuenca;
- comparación con un parche inicial y dos finales;
- identidad espacial de bosque estable, pérdida y ganancia.

Los módulos `test_bosque_conectividad.py` y `test_analisis_temporal.py` pasaron durante
la auditoría. El conjunto completo terminó con **99 pruebas correctas y 2 omitidas por
configuración**; esas dos integraciones Earth Engine se ejecutaron después, de manera
explícita, y también pasaron.

## Ejecuciones reales 2020–2025

Ventana: `[-79.57, 9.03]` a `[-79.55, 9.05]`; distancia 500 m; parche mínimo 0,1 ha.

### JRC TMF

| Métrica | 2020 | 2025 | Cambio |
|---|---:|---:|---:|
| Bosque | 254,8865 ha | 269,3374 ha | +14,4509 ha |
| Parches | 30 | 28 | -2 |
| Área media | 8,4962 ha | 9,6192 ha | +1,1230 ha |
| Componentes | 1 | 1 | 0 |
| Aislados | 0 | 0 | 0 |
| Relaciones ≤500 m | 131 | 141 | +10 |

Transiciones: 254,7975 ha estables, 0,0889 ha de pérdida y 14,5399 ha de ganancia.

### ESRI LULC

| Métrica | 2020 | 2025 | Cambio |
|---|---:|---:|---:|
| `Trees` | 365,1823 ha | 394,7072 ha | +29,5249 ha |
| Parches | 6 | 5 | -1 |
| Área media | 60,8637 ha | 78,9414 ha | +18,0777 ha |
| Componentes | 1 | 1 | 0 |
| Aislados | 0 | 0 | 0 |
| Relaciones ≤500 m | 9 | 7 | -2 |

Transiciones: 353,1400 ha estables, 12,0422 ha de pérdida y 41,5671 ha de ganancia.

Las cifras JRC y ESRI **no deben compararse entre sí**: las definiciones de bosque y
las resoluciones son distintas. Cada tabla solo compara años dentro de la misma fuente.

## Riesgos y severidad

| Gravedad | Riesgo | Tratamiento recomendado |
|---|---|---|
| Alta | Interpretar conectividad estructural como conectividad funcional | Mantener la advertencia visible y evitar afirmaciones sobre especies |
| Alta | Mezclar JRC 30 m y ESRI 10 m | Conservar análisis y leyendas separados |
| Media | Efecto de borde del AOI | Mostrar `contexto_exterior=False` y advertir el truncamiento |
| Media | Distancias en una proyección no equidistante | Ejecutar sensibilidad con proyección local antes de publicación científica |
| Media | Umbral de 500 m sin especie objetivo | Presentarlo como parámetro exploratorio, no como umbral ecológico universal |
| Baja | Uso de `shapely.ops.transform()` deprecado | Migrar en una fase técnica, conservando pruebas de equivalencia |

## Criterio de aceptación

El motor está listo para una **versión candidata técnica** de análisis estructural si
la interfaz mantiene visibles fuente, resolución, AOI, umbral, parche mínimo y
advertencias. No está validado como modelo de conectividad funcional ni como evaluación
de campo.
