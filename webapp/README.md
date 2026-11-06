# Geoportal CHCP 2.0 · versión HTML

Esta aplicación Flask conserva `app.py` como alternativa Streamlit y reutiliza
los motores científicos de `analisis_temporal.py`, `bosque_conectividad.py`,
`estadisticas_temporales.py` y `eri_indicativo.py`.

## Ejecución local

```powershell
$env:GEE_PROJECT_ID = "geoportal-513817"
python -m flask --app webapp.main run --host 127.0.0.1 --port 8080
```

Abra `http://127.0.0.1:8080`. La autorización OAuth local de Earth Engine se
administra fuera del repositorio. Para comprobarla:

```powershell
python scripts/verificar_conexion_gee.py --project geoportal-513817 --jrc
```

## API

- `GET /api/v1/health`
- `GET /api/v1/config`
- `GET /api/v1/territory`
- `POST /api/v1/analyses`
- `POST /api/v1/eri`
- `GET /api/v1/results/<id>/download.zip`

Las solicitudes se validan en el servidor, se recortan a la CHCP y usan un
catálogo cerrado de fuentes. No se aceptan identificadores de assets enviados
por el navegador.

## Cloud Run

El `Dockerfile` usa Gunicorn con una solicitud síncrona de hasta siete minutos.
Configure como mínimo `GEE_PROJECT_ID`, una identidad de servicio autorizada y
los assets privados que se decida conservar. No incluya claves JSON en la imagen.

La preparación detallada, límites operativos y permisos mínimos están documentados
en [`docs/ARQUITECTURA_WEB_HTML.md`](../docs/ARQUITECTURA_WEB_HTML.md).

## Prueba representativa

```powershell
$env:GEE_PROJECT_ID = "geoportal-513817"
python scripts/verificar_api_web_gee.py
```

La prueba genera un polígono pequeño dentro de la CHCP y ejecuta JRC 2020–2025 a
través de la API. No debe repetirse durante cada ajuste visual.

