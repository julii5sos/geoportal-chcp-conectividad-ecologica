# Instalación y reproducción

## Requisitos

- Python 3.11 o superior.
- Cuenta autorizada en Google Earth Engine.
- Acceso de lectura a los assets institucionales del proyecto `geoportal-513817`.

## Instalación web mínima

```powershell
git clone https://github.com/julii5sos/geoportal-chcp-conectividad-ecologica.git
cd geoportal-chcp-conectividad-ecologica
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-web.txt
$env:GEE_PROJECT_ID = "geoportal-513817"
earthengine authenticate --force --auth_mode=localhost
python scripts/verificar_conexion_gee.py --project geoportal-513817 --jrc
python -m webapp.main
```

Abra `http://127.0.0.1:8080`. En Windows, `ABRIR_GEOPORTAL.cmd` usa el puerto 8090 y
abre el navegador del equipo.

## Configuración

Copie `.env.example` únicamente como referencia. El servidor lee variables del
entorno; no requiere ni debe contener secretos versionados. Las variables principales
son `GEE_PROJECT_ID`, `PORT`, `WEB_RESULT_CACHE_ENTRIES`,
`WEB_RESULT_CACHE_TTL`, `SINIA_2021_FOREST_ASSET` y
`SINIA_2023_FOREST_ASSET`.

## Pruebas focalizadas

```powershell
node --check webapp/static/js/platform.js
python -m unittest test_fase_correctiva_ecologica.py test_web_api.py `
  test_web_frontend.py test_web_container_security.py
```

La prueba real de Earth Engine debe ejecutarse una sola vez sobre una geometría pequeña:

```powershell
python scripts/validar_fase_correctiva_gee.py
```

No confunda una prueba unitaria o contractual con validación temática cartográfica.

## Reproducción científica

1. Conserve la misma geometría y los mismos parámetros para ambos escenarios.
2. Registre proyecto, asset, fecha, distancia máxima y área mínima de parche.
3. Preserve por separado las salidas 2021 y 2023.
4. No calcule cambio causal entre ambos productos sin una validación de compatibilidad.
5. Exporte el JSON metodológico junto con los mapas y tablas.
