# Validación de Fase 8 y etapas 14–15

## Alcance comprobado

- Plataforma HTML, buscador territorial, panel, asistente y descargas conservados.
- JRC TMF, ESRI y concordancia permanecen en el motor temporal existente.
- Hansen, Sentinel-2 NDVI, GEDI/OpenForis y WorldCover se ejecutan bajo demanda
  como evidencias independientes.
- El Panel recupera el resultado exacto o el último resultado en memoria para el
  mismo identificador territorial; no inicia Earth Engine al abrirse.
- Los corredores publicados son buscables, seleccionables en el mapa y analizables
  con el mismo motor temporal JRC/ESRI.

## Comprobaciones reales de Earth Engine

Se usó una geometría pequeña y el proyecto `geoportal-513817`:

| Producto | Comprobación | Resultado |
|---|---|---|
| Hansen v1.13 | pérdida 2020–2025 y tesela | correcta; 0.4416 ha en la geometría de prueba |
| Sentinel-2 NDVI | medias/medianas de dos años y tres teselas | correcto |
| GEDI/OpenForis V27 | media, mediana, P25/P75 y tesela | correcto |
| WorldCover v200 | histograma, clase arbórea y tesela categórica | correcto |

Estas verificaciones comprueban ejecución y contratos, no exactitud temática de
campo. JRC y ESRI no se recalcularon porque sus algoritmos no fueron modificados.

## Regresión focalizada

Comando:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_web_api test_web_frontend `
  test_territorio_busqueda test_corredores test_catalogo_multifuente `
  test_analisis_complementario
node --check webapp/static/js/platform.js
node --check webapp/static/js/panel.js
```

Resultado: **43 pruebas correctas**, ambos archivos JavaScript válidos y
`git diff --check` sin errores. Persisten avisos de deprecación de
`shapely.ops.transform`; no afectan los resultados actuales y deben atenderse en
una actualización controlada.

## Validación visual real

- [Captura de la Plataforma](captura_plataforma_fase8.png)
- [Captura del Panel](captura_panel_fase8.png)

Se verificaron también las rutas `/`, `/platform`, `/panel`, salud y búsqueda
territorial en `http://127.0.0.1:8088`.

## Estados y límites

- El navegador diferencia procesando, disponible, no calculado y error; una
  respuesta tardía no reemplaza la selección activa.
- La caché RAM es temporal. En Cloud Run debe sustituirse o complementarse con
  Firestore para metadatos y Cloud Storage para ZIP/GeoJSON.
- SINIA 2021 requiere asset y permisos; 1992/2000 carecen de insumos auditables.
- FIRMS, GLAD y RADD permanecen pendientes y no generan valores ficticios.
- GEDI/OpenForis requiere que la identidad de despliegue pueda leer el asset.
- Los corredores y conexiones modeladas representan contexto y conectividad
  estructural; no prueban movimiento de fauna.
