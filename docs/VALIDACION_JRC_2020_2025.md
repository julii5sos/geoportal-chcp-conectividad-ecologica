# Validación verificable JRC TMF 2020–2025

Fecha de ejecución: 4 de noviembre de 2026, zona horaria de Panamá.

## Comando

```powershell
python scripts/validar_analisis_temporal.py `
  --project geoportal-513817 `
  --fuente jrc_tmf `
  --inicial 2020 `
  --final 2025 `
  --distancia 500 `
  --area-minima 0.1
```

La tabla inferior conserva los resultados de la ejecución histórica del 4 de noviembre
de 2026. El cambio del identificador de proyecto no altera la fuente pública JRC ni las
fórmulas; una nueva ejecución requiere que la identidad local tenga permiso para usar
`geoportal-513817`.

Área de validación: rectángulo `[-79.57, 9.03]` a `[-79.55, 9.05]`, dentro de la CHCP.
Fuente: `projects/JRC/TMF/v1_2025/AnnualChanges`, resolución 30 m. Se consideran bosque
las clases 1, 2 y 4.

## Resultados

| Métrica | 2020 | 2025 | Cambio |
|---|---:|---:|---:|
| Superficie forestal | 254.8865 ha | 269.3374 ha | +14.4509 ha |
| Porcentaje de bosque | 52.4018 % | 55.3727 % | +2.9709 pp |
| Número de parches | 30 | 28 | -2 |
| Área media del parche | 8.4962 ha | 9.6192 ha | +1.1230 ha |
| Parches aislados | 0 | 0 | 0 |
| Componentes de red | 1 | 1 | 0 |
| Relaciones dentro de 500 m | 131 | 141 | +10 |

Transiciones espaciales:

- bosque estable: **254.7973 ha**;
- pérdida de bosque: **0.0889 ha**;
- ganancia de bosque: **14.5399 ha**.

La identidad `bosque estable + pérdida ≈ bosque 2020` y `bosque estable + ganancia ≈
bosque 2025` se cumple con una diferencia de redondeo inferior a 0.001 ha.

## Interpretación

En esta ventana, JRC clasifica más superficie dentro de las clases de bosque en 2025
y la cobertura aparece en menos parches. La red continúa formando un solo componente
con el umbral de 500 m. Esto verifica el motor; no constituye una conclusión para toda
la CHCP ni confirma restauración en campo.

## Verificación de la interfaz

También se ejecutó el flujo completo en Streamlit para **Lago Miraflores**, recortado al
límite de la CHCP, con JRC 2020–2025, 500 m y parche mínimo de 0.1 ha. La interfaz
terminó sin errores y mostró 6,933.79 ha de bosque en 2025, un cambio de +234.97 ha,
223 parches, 3 componentes, 4.85 ha de pérdida y 239.82 ha de ganancia. Estas cifras
son una comprobación operativa adicional y no sustituyen la ventana sintética y
reproducible de la sección anterior.

- [Selección territorial y años](captura_analisis_temporal.png)
- [Indicadores del resultado](captura_resultado_temporal_mapa.png)
- [Mapa de transiciones](captura_mapa_transiciones_2020_2025.png)
- [Gráficas comparativas de barras](captura_graficas_temporales_completas.png)
