# Geoportal CHCP · aplicación web HTML

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

## Cloud Run privado

El `Dockerfile` ejecuta Gunicorn como usuario sin privilegios y aplica límites de
solicitud, concurrencia y reciclado de procesos. En Cloud Run la aplicación usa la
identidad de servicio adjunta mediante Application Default Credentials; rechaza por
defecto una clave JSON incrustada.

La configuración inicial se encuentra en `deploy/` y la guía completa —roles
mínimos, acceso privado, costos, riesgos y apagado— está en
[`docs/FASE6_SEGURIDAD_CLOUD_RUN_PRIVADO.md`](../docs/FASE6_SEGURIDAD_CLOUD_RUN_PRIVADO.md).

## Prueba representativa

```powershell
$env:GEE_PROJECT_ID = "geoportal-513817"
python scripts/verificar_api_web_gee.py
```

La prueba genera un polígono pequeño dentro de la CHCP y ejecuta JRC 2020–2025 a
través de la API. No debe repetirse durante cada ajuste visual.

