# Datos cartográficos

Los archivos `corredores_almanaque_azul.geojson`, `puntos_criticos_almanaque_azul.geojson` y `catalogo_corredores.json` se generan con:

```powershell
python scripts/preparar_datos_corredores.py `
  --corredores data/raw/interpretacion_conectividad_5_3857.geojson `
  --ojos data/raw/ojos_5_3857.geojson `
  --salida data
```

Consulte [THIRD_PARTY_DATA.md](../THIRD_PARTY_DATA.md) para la procedencia y las condiciones de uso.

El subdirectorio `territorio/` contiene la cuenca y las subcuencas incluidas en el
portal HTML. Estos límites se cargan localmente y sustituyen las colecciones privadas
que antes debían configurarse en Earth Engine.
