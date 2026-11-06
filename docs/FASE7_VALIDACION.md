# Fase 7 · Validación focalizada

Fecha: 2026-11-06. Proyecto Earth Engine: `geoportal-513817`.

## Prueba real JRC + ESRI

Se ejecutó una sola vez:

```powershell
python scripts/verificar_integracion_multifuente_gee.py
```

El script construye un polígono pequeño alrededor de un punto interior de la CHCP, lo recorta a la cuenca y solicita 2020–2025 con 500 m de distancia máxima y 0.1 ha de área mínima. La API ejecutó JRC y ESRI de forma independiente y después calculó concordancia.

Resultado observado:

```json
{
  "project_id": "geoportal-513817",
  "period": [2020, 2025],
  "area_valida_comun_ha": 30.5122,
  "concordancia_pct": 52.8602,
  "diferencia_bosque_final_ha": -10.5939
}
```

Estos valores validan la ruta técnica y los contratos para **esa geometría de prueba**. No son estadísticas representativas de toda la CHCP ni una evaluación de exactitud temática. La concordancia entre productos no sustituye validación independiente de campo.

## Pruebas automatizadas focalizadas

Se ejecutaron 34 pruebas de:

- catálogo y búsqueda territorial;
- resumen local sin cifras científicas ficticias;
- clases de estado y cambio integradas;
- denominadores de concordancia;
- matriz de fuentes;
- simbología;
- endpoints Flask;
- componentes frontend;
- geometrías territoriales.

También se verificó la sintaxis de `platform.js`, `panel.js` y `home.js` con `node --check`.

No se repitió la batería científica completa ni se procesó toda la CHCP.

