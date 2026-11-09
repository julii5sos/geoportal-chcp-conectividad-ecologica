# Registro de assets oficiales SINIA–MiAMBIENTE

Verificación ejecutada el 7 de noviembre de 2026 con el proyecto Earth Engine
`geoportal-513817`. Además de `ee.data.getAsset`, se comprobó el vector oficial
2021 mediante una consulta territorial controlada sobre Qda. Bonita.

| Producto | Asset | Tipo comprobado |
|---|---|---|
| Cobertura histórica 1992 | `SINIA_1992_COBERTURA_HISTORICA_RASTER30M` | IMAGE |
| Cobertura histórica 2000 | `SINIA_2000_COBERTURA_HISTORICA_RASTER30M` | IMAGE |
| Bosque/no bosque 2012 | `SINIA_2012_BOSQUE_BINARIO_RASTER5M` | IMAGE |
| Uso y cobertura 2012 | `SINIA_2012_USO_SUELO_RASTER5M` | IMAGE |
| Cobertura general 2019 | `SINIA_2019_COBERTURA_GENERAL_RASTER20M` | IMAGE |
| Cobertura general 2021 | `SINIA_2021_COBERTURA_GENERAL_VECTOR` | TABLE |
| Uso y cobertura 2021 | `SINIA_2021_USO_SUELO_RASTER10M` | IMAGE |
| Cobertura diagnóstica 2023 | `SINIA_2023_COBERTURA_GENERAL_RASTER10M` | IMAGE |

## Alcance de la verificación

- **Confirmado:** el identificador existe, la identidad local puede leer sus
  metadatos y el tipo coincide con el catálogo.
- **No confirmado:** exactitud temática, integridad espacial, leyenda completa,
  equivalencia metodológica, licencia o comparabilidad interanual.
- La cobertura vectorial 2021 contiene 28 288 entidades y tres categorías. La
  clase forestal exacta del motor original tiene 10 994 entidades. En Qda. Bonita
  cubrió 379.2601 ha de 509.9985 ha y produjo seis parches y nueve aristas.
- Se verificó equivalencia temática y compatibilidad funcional con el motor. No
  se verificó igualdad entidad por entidad con el asset anterior, porque ya no
  está disponible para efectuar una comparación directa.
- El diagnóstico 2023 permanece independiente. No se interpreta como cambio
  2021–2023 hasta contar con un dictamen de comparabilidad.

La inspección es reproducible con:

```powershell
.\.venv\Scripts\python.exe scripts\inspeccionar_assets_cobertura.py --catalogo --solo-metadatos
```
