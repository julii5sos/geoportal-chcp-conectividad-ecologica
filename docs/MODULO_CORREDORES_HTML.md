# Módulo de corredores biológicos

## Datos y clasificación

El catálogo usa únicamente `data/corredores_almanaque_azul.geojson` y
`data/puntos_criticos_almanaque_azul.geojson`: 22 polígonos y 14 puntos. La fuente
declarada es Almanaque Azul, versión local documentada 2024.05. Los tres tramos
mesoamericanos provienen del metadato local; no se inventaron delimitaciones.

Los corredores son referencias publicadas. Las líneas producidas por
`bosque_conectividad.py` son conexiones estructurales modeladas por distancia entre
parches; no son límites oficiales ni rutas comprobadas de fauna.

## Funciones recuperadas

- Búsqueda por nombre y selección de corredor como territorio.
- Área medida en EPSG:8857 y geometría WGS84 para mapa.
- Intersección de subcuencas/corredores, área y porcentaje solapado.
- Distancia geométrica al corredor más cercano.
- Identificación de puntos críticos publicados dentro del territorio.
- Reutilización del análisis JRC/ESRI para cobertura, fragmentación, red y cambios
  temporales dentro de la geometría de un corredor.
- Descarga del resultado y metadatos mediante el mismo `result_id`.

## Interpretación

Una intersección o proximidad es contexto territorial. Las métricas de nodos,
aristas, componentes y aislamiento representan conectividad estructural bajo el
umbral configurado. No prueban conectividad funcional para una especie. Los puntos
críticos son ubicaciones publicadas en el archivo fuente, no resultados recalculados
por el Geoportal.

