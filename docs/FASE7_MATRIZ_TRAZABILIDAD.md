# Fase 7 · Auditoría y matriz de trazabilidad de fuentes

Fecha de auditoría: 2026-11-06. Rama: `feature/fase7-integracion-multifuente`.

## Alcance y evidencia revisada

Se comparó la copia local del repositorio original en la rama `feature/geoportal-chcp-v2` (referencia visual `b011956`) con la versión HTML/API actual. Se revisaron módulos Python, plantillas, JavaScript, archivos de `data/`, documentación, identificadores de Earth Engine y las imágenes demostrativas del HTML original.

La matriz ejecutable vive en `catalogo_multifuente.py`. El endpoint `GET /api/v1/catalog/sources` expone exactamente esa matriz; una fuente no aparece como operativa solo por estar mencionada en una pantalla.

## Diferencias entre el proyecto original y el actual

| Capacidad | Repositorio original | Geoportal actual | Estado |
|---|---|---|---|
| Preevaluación territorial | `app_experiencia.py`, JRC, Hansen, ESRI, NDVI y GEDI | Se conserva la aplicación Streamlit; la API HTML expone el motor temporal JRC/ESRI | Conservada; varias capas complementarias aún parciales en HTML |
| Cobertura anual comparable | Vista y cálculos dentro de la aplicación principal | `analisis_temporal.py` separa obtención, máscara válida y estadísticas | Implementada y probada funcionalmente |
| Fragmentación/conectividad | `bosque_conectividad.py` | Reutilizado sin reescribir fórmulas | Conservada |
| Comparación temporal | Controles y comparadores dispersos | Motor explícito por fuente y dos años | Ampliada |
| ERI | Módulo indicativo con cuatro componentes | `eri_gee.py`, API `/api/v1/eri`, panel independiente | Conservada, pesos sin cambios |
| Subcuencas | Cargadas como unidad territorial | GeoJSON local, catálogo estable CHCP + 53 subcuencas | Recuperada y desacoplada de assets GEE |
| Buscador territorial | No existía como flujo central | `territorio_busqueda.py`, portada, Panel y estado local | Nueva |
| JRC + ESRI | Análisis individuales | `analisis_integrado.py` ejecuta ambos y calcula concordancia | Nueva; requiere integración real final |
| Coberturas SINIA 1992/2000 | Solo se localizaron imágenes demostrativas del HTML | No se publican como datos | No disponible |
| FIRMS, GLAD/RADD, WorldCover | Referencias o ausentes | Catalogadas con estado explícito; no simulan integración | Pendientes |

## Matriz resumida

| Fuente | Identificador / archivo | Período y resolución | Función actual | Estado HTML | Riesgo o acción |
|---|---|---|---|---|---|
| JRC Tropical Moist Forest | `projects/JRC/TMF/v1_2025/AnnualChanges` | 1990–2025; 30 m | Cobertura, cambio, fragmentación, conectividad y concordancia | Integrada y operativa | Mantener el dominio y estados propios del producto |
| ESRI Global LULC | `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS` | 2017–2025; 10 m | Escenario anual independiente y concordancia | Integrada y operativa | `Trees` no equivale a la definición JRC |
| Hansen GFC v1.13 | `UMD/hansen/global_forest_change_2025_v1_13` | cobertura 2000; pérdida 2001–2025; ganancia 2000–2012; 30.92 m | Contexto de pérdida en Streamlit | Integrada parcialmente | No presentar `gain` como serie actualizada |
| ESA WorldCover v200 | `ESA/WorldCover/v200` | 2021; 10 m; 11 clases | Referencia temática potencial | Disponible pero no conectada | Un año no constituye una serie anual |
| Dynamic World V1 | `GOOGLE/DYNAMICWORLD/V1` | 2015–actualidad; 10 m; 9 clases | Componente de integridad del ERI | Integrada y operativa | Producto derivado de Sentinel-2, no clasificación propia del proyecto |
| Sentinel-2 SR armonizado | `COPERNICUS/S2_SR_HARMONIZED` | 2017–actualidad; 10/20/60 m | NDVI corroborativo en Streamlit | Integrada parcialmente | Documentar nubes, estacionalidad y composición |
| GEDI / OpenForis | `users/openforisearthmap/World_EarthMap/CanopyHeight_GEDI_V27` | referencia fija | Altura de dosel y ERI | Integrada parcialmente | Asset externo; verificar lectura con identidad de Cloud Run |
| FIRMS | `FIRMS` | 2000–actualidad; diario; 1 km | Catálogo complementario | Disponible pero no conectada | Producto NRT, no atribuir causalidad ni calidad científica final |
| GLAD/RADD | Sin ruta verificada | según proveedor | Alertas potenciales | No disponible | Definir proveedor, licencia, API y validación |
| MERIT Hydro | `MERIT/Hydro/v1_0_1` | referencia; ~90 m | Proximidad riparia del ERI | Integrada y operativa | No sustituye hidrografía local detallada |
| SINIA/MiAMBIENTE 2021 | `SINIA_2021_COBERTURA_GENERAL_VECTOR` | 2021; vector oficial | Cobertura, fragmentación y conectividad estructural | Verificado localmente en `geoportal-513817` | Otorgar lectura a la cuenta de servicio antes de desplegar |
| SINIA 1992/2000 | No se halló archivo geoespacial validable | 1992 y 2000 | Ninguna | No disponible | Solicitar datos, leyendas, CRS y metadatos; no usar PNG demostrativos |
| Corredores Almanaque Azul | `data/corredores_almanaque_azul.geojson` | referencia vectorial | Consulta territorial y mapa | Integrada y operativa | Intersección no prueba conectividad funcional |
| CHCP y 53 subcuencas | `data/territorio/*.geojson` | referencia vectorial WGS 84 | Búsqueda, selección y recorte | Integrada y operativa | Conservar trazabilidad institucional |
| ERI indicativo | método interno | referencia 2024; salida 90 m | Índice complementario | Integrada y operativa | Proxy no validado de resiliencia real |

## Evidencia por función

- `analisis_temporal._estado_y_mascara_valida_ee`: colecciones, clases válidas y NoData de JRC/ESRI.
- `analisis_temporal.construir_estado_binario_ee`: bosque/no bosque conservando ceros y máscara válida explícita.
- `analisis_temporal.ejecutar_analisis_temporal_ee`: resultados temporales por fuente.
- `bosque_conectividad.py`: parches, distancias, componentes y aislamiento reutilizados por cada período.
- `analisis_integrado.ejecutar_analisis_integrado_ee`: dos ejecuciones independientes y concordancia posterior.
- `eri_gee.calcular_eri_geojson`: ERI separado de las métricas temporales.
- `territorio_busqueda.catalogo_territorial`: identificadores reales y geometrías locales.
- `webapp.service.configuration` y `source_catalog`: contratos públicos para años, simbología y trazabilidad.

## Verificación documental externa

- [ESA WorldCover v200](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200): 2021, 10 m, 11 clases, derivado de Sentinel-1/2.
- [Hansen Global Forest Change v1.13](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2025_v1_13): 30.92 m; `gain` únicamente 2000–2012.
- [Dynamic World V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1): 10 m, nueve clases, predicciones por escena Sentinel-2 con enmascaramiento de nubes.
- [FIRMS](https://developers.google.com/earth-engine/datasets/catalog/FIRMS): MODIS NRT de 1 km; el catálogo advierte que no es de calidad científica final.
- [MERIT Hydro v1.0.1](https://developers.google.com/earth-engine/datasets/catalog/MERIT_Hydro_v1_0_1): 3 arc-sec (~90 m) y limitaciones hidrográficas documentadas.

## Cifras de interfaz

La portada muestra únicamente conteos derivados del archivo local (53 subcuencas) y datos de configuración. El Panel calcula área en EPSG:8857 e intersecciones con corredores/puntos locales. Cobertura, pérdida, fragmentación, conectividad y ERI aparecen como **No calculado** hasta ejecutar el motor; no se rellenan con porcentajes demostrativos.

## Pendientes trazables

1. Autorizar o migrar SINIA 2021 y verificar GEDI para la identidad de servicio.
2. Obtener archivos geoespaciales y metadatos de SINIA 1992/2000.
3. Implementar WorldCover y FIRMS solo como módulos complementarios con leyenda, metadatos y advertencias.
4. Definir acceso/licencia antes de integrar GLAD/RADD.
5. Mantener Hansen y NDVI visibles como contexto sin convertirlos en una serie anual equivalente a JRC/ESRI.

