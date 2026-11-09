# Validación controlada de la restauración de resultados

Fecha: 2026-11-07
Área: subcuenca Qda. Bonita (507.8993 ha según el límite local)
Proyecto Earth Engine: `geoportal-513817`

## Resultado comprobado

La preevaluación territorial se ejecutó una sola vez y quedó almacenada en la caché
del servidor. No se utilizaron valores de demostración.

| Indicador | Resultado real |
|---|---:|
| Índice de indicios | 4.0 / 6.5 |
| Prioridad territorial | Alta |
| Señal JRC TMF | Activa, 2.0 puntos |
| Señal Hansen GFC | Activa, 2.0 puntos |
| Señal ESRI | Sin señal, 0.0 puntos |
| Señal GEDI | Sin señal, 0.0 puntos |
| Señal NDVI | Sin señal, 0.0 puntos |
| Deforestación JRC TMF 2025 | 22.8600 ha |
| Degradación JRC TMF 2025 | 111.4747 ha |
| Regeneración forestal JRC TMF 2025 | 127.4330 ha |
| Pérdida Hansen posterior a 2020 | 2.1516 ha |
| Área dentro de corredores publicados | 330.6153 ha |
| Proporción dentro de corredores | 65.0947 % |

La lectura fue mixta porque existen señales de deterioro y de regeneración o
ganancia. Estas extensiones no se compensan entre sí.

## Fragmentación y conectividad

El segundo paso del análisis integral no se ejecutó. Earth Engine devolvió:

`Collection asset 'projects/geoportal-513817/assets/CBOTB_2021_CHCP_15KM_GEE_FINAL' not found.`

> **Estado posterior:** este fallo histórico quedó superado al centralizar
> `SINIA_2021_COBERTURA_GENERAL_VECTOR`. Véase
> `VALIDACION_ASSET_OFICIAL_2021_2026-11-07.md` para la prueba territorial real.

Esto confirma una dependencia ausente, no un resultado estructural nulo. No se
declaran parches, componentes, aislamiento ni rutas como validados. La cobertura
general vectorial 2021 disponible en el catálogo no se sustituye automáticamente
porque su equivalencia con el asset del motor original no ha sido demostrada.

## Informe PDF

Se generó un PDF desde el resultado almacenado, sin repetir Earth Engine. La revisión
visual de cuatro páginas confirmó portada, mapa de ubicación, resumen, gráfico de
aportes, tabla por fuente, contexto de corredores, limitaciones y atribuciones
legibles. El informe omite correctamente fragmentación y conectividad porque esos
módulos no terminaron.

## Conclusión

- Preevaluación territorial: implementada y verificada con datos reales.
- Panel, mapas JRC y coincidencia: el resultado incluye teselas reales.
- PDF territorial: generado y revisado visualmente.
- Fragmentación y conectividad 2021: bloqueadas por migración o permisos del asset.
- Análisis integral: parcialmente operativo; no debe declararse completo hasta resolver
  la cobertura estructural 2021 y repetir una sola prueba representativa.
