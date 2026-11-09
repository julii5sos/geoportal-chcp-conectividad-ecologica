# Catálogo operativo de datos

Fecha de revisión local: 2026-11-08. Proyecto de Earth Engine:
`geoportal-513817`.

## Coberturas institucionales SINIA–MiAMBIENTE

| Producto | Asset | Tipo | Uso actual | Comparabilidad |
|---|---|---|---|---|
| Cobertura histórica 1992 | `SINIA_1992_COBERTURA_HISTORICA_RASTER30M` | IMAGE | Consulta cartográfica | Producto independiente |
| Cobertura histórica 2000 | `SINIA_2000_COBERTURA_HISTORICA_RASTER30M` | IMAGE | Consulta cartográfica | Producto independiente |
| Bosque/no bosque 2012 | `SINIA_2012_BOSQUE_BINARIO_RASTER5M` | IMAGE | Consulta cartográfica | Producto binario independiente |
| Uso y cobertura 2012 | `SINIA_2012_USO_SUELO_RASTER5M` | IMAGE | Consulta cartográfica | Producto temático independiente |
| Cobertura general 2019 | `SINIA_2019_COBERTURA_GENERAL_RASTER20M` | IMAGE | Consulta cartográfica | Producto independiente |
| Cobertura general 2021 | `SINIA_2021_COBERTURA_GENERAL_VECTOR` | TABLE | Cobertura oficial, fragmentación y conectividad | Referencia estructural oficial |
| Uso de suelo 2021 | `SINIA_2021_USO_SUELO_RASTER10M` | IMAGE | Consulta cartográfica; 33 códigos | Producto temático independiente |
| Diagnóstico general 2023 | `SINIA_2023_COBERTURA_GENERAL_RASTER10M` | IMAGE | Diagnóstico estructural separado | No causalmente comparable con 2021 |

Todos los identificadores completos se construyen bajo
`projects/geoportal-513817/assets/`. La inspección de metadatos local confirmó los
tipos indicados; la cuenta de servicio futura deberá recibir permiso de lectura.
En el producto detallado 2021 están documentados los grupos de bosque natural
(códigos 1–6), bosque plantado (7–8) y rastrojo (9). Los códigos 10–33 permanecen
visibles como «sin documentación» hasta contar con una leyenda institucional completa.

## Evidencia satelital y ambiental

| Fuente | Período usado | Resolución nominal | Función |
|---|---:|---:|---|
| JRC Tropical Moist Forest | 1990–2025 | 30 m | Estado, deforestación, degradación y regeneración forestal |
| Hansen Global Forest Change | 2001–2025 | 30 m | Pérdida anual y pérdida posterior a 2020 |
| ESRI Land Use/Land Cover | 2017–2025 visual; 2017–2024 en el índice validado | 10 m | Árboles y transiciones de cobertura |
| Sentinel-2 SR Harmonized | 2017–2025 | 10 m | NDVI anual corroborativo |
| GEDI/OpenForis | referencia no anual | producto agregado | Contexto de altura del dosel |
| Copernicus DEM y MERIT Hydro | referencia | según producto | Componentes topográfico y ripario del ERI |

Los períodos válidos se centralizan en `geoportal_catalogo.py`. Una capa visible no
implica automáticamente que participe en una fórmula científica.

## Datos vectoriales locales

- `data/territorio/area_estudio.geojson`: límite de la CHCP.
- `data/territorio/subcuencas_canal.geojson`: 53 subcuencas.
- Corredores de Almanaque Azul: 22 polígonos y 14 puntos críticos, documentados en
  `THIRD_PARTY_DATA.md`.

## Reglas de publicación

Los assets institucionales privados no se copian al repositorio ni al contenedor.
El código, metadatos, atribuciones y variables de configuración sí son versionables.
No se incluyen tokens, credenciales OAuth ni claves JSON.
