# Datos de terceros

## Corredores naturales de Panamá

La aplicación incorpora dos GeoJSON publicados por la Fundación Almanaque Azul:

- `interpretacion_conectividad_5_3857.geojson` (22 polígonos de corredores);
- `ojos_5_3857.geojson` (14 puntos críticos).

Fuente: [Mapa de corredores naturales de Panamá](https://www.almanaqueazul.org/conectividad/mapa/), versión mostrada por el visor `2024.05`. El sitio de la Fundación indica que su contenido se publica bajo licencias Creative Commons. Estos datos conservan su atribución y no se relicencian como parte del código de la aplicación.

Los originales están en EPSG:3857. El script `scripts/preparar_datos_corredores.py` los convierte a EPSG:4326 sin cambiar geometrías, nombres, notas, conductividad promedio ni categorías. Las categorías originales verificadas son `alta`, `mediana` y `media-baja`.

El raster continuo de conectividad de 6 km no se redistribuye en este repositorio. El visor enlaza al mapa original para esa lectura y utiliza los polígonos interpretados publicados para el análisis de intersección.

## Cobertura bosque/no bosque

La cobertura utilizada corresponde a la capa **Bosque y otros usos**, referencia 2021,
publicada por SINIA–MiAMBIENTE. El repositorio no incluye el archivo nacional: la
administración lo mantiene como el asset privado de Earth Engine
`projects/geoportal-513817/assets/SINIA_2021_COBERTURA_GENERAL_VECTOR`. La aplicación
selecciona automáticamente `Categoria = Bosques y Otras Tierras Boscosas` y recorta
esos polígonos al área evaluada. La identidad local o de Cloud Run necesita permiso
de lectura; los datos no se redistribuyen con el código.

El diagnóstico 2023 utiliza el asset raster privado
`projects/geoportal-513817/assets/SINIA_2023_COBERTURA_GENERAL_RASTER10M`. Su código 1
se interpreta como bosques y otras tierras boscosas para un escenario estructural
independiente. No se presenta como una serie homogénea con 2021 ni se utiliza para
inferir transiciones sin una validación adicional de compatibilidad.

## Cuenca y subcuencas del Canal de Panamá

Los archivos `data/territorio/area_estudio.geojson` y
`data/territorio/subcuencas_canal.geojson` proceden del paquete del portal
**Conectividad Panamá** entregado para esta aplicación. Incluyen el límite de la Cuenca
del Canal y 53 unidades territoriales. Se sirven directamente con la aplicación y se
envían como geometrías a Earth Engine; no requieren un asset vectorial privado.

El archivo de subcuencas recibido contenía algunos caracteres sustituidos en los
atributos. `territorio_local.py` corrige únicamente los nombres visibles; no altera las
geometrías ni las superficies de la fuente.
