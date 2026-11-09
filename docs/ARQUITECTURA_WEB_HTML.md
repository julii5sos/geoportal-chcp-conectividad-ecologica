# Arquitectura de la versión web HTML del Geoportal CHCP 2.0

## Alcance

La versión web es una aplicación Flask independiente que reproduce la identidad del
HTML original y reutiliza el motor Python existente. La aplicación Streamlit sigue
disponible como alternativa; no fue eliminada ni sustituida.

```text
Navegador HTML/CSS/JavaScript
          │ JSON/GeoJSON
          ▼
API Flask (`webapp/main.py`)
          │ validación, recorte CHCP, caché y límites
          ▼
`analisis_temporal.py` ── `bosque_conectividad.py`
          │
          ├── JRC TMF (1990–2025)
          ├── ESRI LULC (2017–2025)
          └── Google Earth Engine · proyecto `geoportal-513817`

ERI complementario
`eri_gee.py` ── pesos originales de `eri_indicativo.py`
```

## Componentes

| Componente | Responsabilidad |
|---|---|
| `webapp/main.py` | Rutas HTML y API, límites de cuerpo, encabezados de seguridad y manejo de errores. |
| `webapp/models.py` | Contratos Pydantic para área, análisis temporal y ERI. |
| `webapp/service.py` | Adaptador entre la API y los motores científicos; recorta áreas a la CHCP y prepara descargas. |
| `webapp/cache.py` | Caché TTL acotada y deduplicación de solicitudes idénticas dentro de una instancia. |
| `eri_gee.py` | ERI real en GEE, separado del análisis temporal y con pesos 35/25/20/20. |
| `webapp/templates/` | Portada, plataforma, metodología, acerca y asistente modal. |
| `webapp/static/` | CSS del HTML original, extensiones responsive y comportamiento del visor. |

## API

- `GET /api/v1/health`: estado local y proyecto GEE configurado; no inicia GEE.
- `GET /api/v1/config`: fuentes, años válidos, análisis y pesos ERI.
- `GET /api/v1/territory`: CHCP, 53 subcuencas, corredores y puntos críticos locales.
- `POST /api/v1/analyses`: cobertura, fragmentación y conectividad temporal reales.
- `POST /api/v1/eri`: ERI complementario real para el área resuelta.
- `GET /api/v1/results/<id>/download.zip`: resultado completo, área, transiciones y metadatos.

El navegador no puede enviar identificadores arbitrarios de assets. El servidor usa
un catálogo cerrado de fuentes y años, limita la solicitud a 2 MB, restringe el
número de coordenadas y rechaza áreas superiores al límite operativo configurado.

## Autenticación de Earth Engine

La aplicación usa `GEE_PROJECT_ID=geoportal-513817`. En local, Earth Engine utiliza
las credenciales OAuth/ADC que se encuentran fuera del repositorio. En Cloud Run debe
utilizarse la identidad adjunta al servicio; no debe copiarse una clave JSON a la
imagen ni almacenarse en Git.

## Verificación representativa

El 6 de noviembre de 2026 se ejecutó `scripts/verificar_api_web_gee.py` sobre un
polígono pequeño generado dentro de la CHCP:

- fuente: JRC TMF;
- período: 2020–2025;
- proyecto: `geoportal-513817`;
- máscara común: **175.4569 ha**;
- error de cierre de transiciones: **+0.000000 ha**.

La prueba llamó la API Flask y el motor real; no utilizó datos sintéticos.

## Requisitos para Google Cloud Run

1. Habilitar Earth Engine API en `geoportal-513817` y mantener el proyecto registrado.
2. Crear o seleccionar una cuenta de servicio de ejecución, sin generar una clave JSON.
3. Adjuntar esa cuenta al servicio Cloud Run y conceder únicamente los permisos
   mínimos para usar Earth Engine y consumir servicios del proyecto.
4. Compartir explícitamente con esa identidad cualquier asset privado que se decida
   conservar. La CHCP y sus subcuencas actuales son GeoJSON locales y no requieren un
   asset privado.
5. Configurar `GEE_PROJECT_ID=geoportal-513817`, memoria inicial de 2 GiB, tiempo de
   espera de al menos 420 s y concurrencia baja (1–2) por instancia.
6. Mantener una sola réplica durante la validación. La caché actual es local a cada
   instancia; para escalar horizontalmente se necesitaría una caché externa.
7. Decidir si el servicio será privado o público. Antes de acceso público se recomienda
   añadir límite de tasa por identidad/IP, presupuesto, cuotas y alertas de consumo.
8. Conservar `WEB_MAX_REQUEST_BYTES`, `WEB_MAX_COORDINATES`,
   `WEB_MAX_ANALYSIS_AREA_HA` y `WEB_RESULT_CACHE_TTL` como límites configurables.

El `Dockerfile` ya usa Gunicorn y no contiene credenciales. No se ejecutó ningún
despliegue en esta fase.

## Limitaciones operativas

- El procesamiento continúa siendo síncrono: la solicitud permanece abierta durante
  el cálculo científico. Para trabajos muy grandes conviene migrar a Cloud Tasks y un
  almacén persistente de resultados.
- La respuesta cartográfica limita el número de elementos visibles para proteger el
  navegador; el ZIP conserva el resultado completo guardado en caché.
- Los mapas base, Leaflet y DM Sans requieren acceso a proveedores externos.
- La capa ERI es complementaria y no debe interpretarse como una serie anual.

