# Arquitectura actual del Geoportal CHCP

## Componentes

```text
Navegador
  ├─ HTML/CSS/JavaScript y Leaflet
  ├─ panel izquierdo: área, capas y parámetros
  ├─ mapa central permanente
  └─ panel derecho: métricas, gráficas, interpretación y descargas
          │
          ▼
API Flask (`webapp/main.py`)
          │
          ├─ preevaluación territorial
          ├─ fragmentación y conectividad
          ├─ comparación estructural 2021–2023
          ├─ corredores y ERI
          └─ PDF y paquetes de descarga
          │
          ▼
Motores científicos Python + Google Earth Engine
          └─ proyecto `geoportal-513817`
```

La aplicación Streamlit permanece como respaldo histórico y no es la interfaz web
principal. El contenedor Flask instala `requirements-web.txt`, que excluye Streamlit y
Folium.

## Rutas principales

| Método | Ruta | Función |
|---|---|---|
| GET | `/` | Portada |
| GET | `/panel` | Panel territorial |
| GET | `/platform` | Plataforma de análisis |
| POST | `/api/v1/evidence` | Cinco señales y preevaluación |
| POST | `/api/v1/structural-connectivity` | Fragmentación o conectividad de un escenario |
| POST | `/api/v1/structural-comparison` | Diagnósticos paralelos 2021 y 2023 |
| POST | `/api/v1/integrated-analysis` | Preevaluación y estructura solicitada |
| GET | `/api/v1/results/<id>` | Resultado conservado en caché |
| GET | `/api/v1/results/<id>/report.pdf` | Informe PDF sin recalcular Earth Engine |
| GET | `/api/v1/results/<id>/download` | Paquete de resultados y metadatos |

## Estado y caché

`webapp/cache.py` mantiene por defecto seis resultados durante 3.600 segundos. La
caché deduplica solicitudes científicas equivalentes y evita repetir cálculos al
cambiar de pestaña o preparar el PDF. Es memoria del proceso: se pierde al reiniciar y
no es adecuada como repositorio permanente de resultados.

## Comparación estructural

`run_structural_comparison()` ejecuta `official_2021` y `diagnostic_2023` con la misma
geometría y parámetros. Reutiliza `run_structural_connectivity()` y, por tanto, las
funciones científicas ya probadas. Devuelve escenarios separados y fija
`comparable_for_causal_change=false`; no fabrica una diferencia numérica entre fuentes
incompatibles.

## Seguridad

- La API valida superficie y complejidad geométrica antes de iniciar Earth Engine.
- Cloud Run debe usar Application Default Credentials con una cuenta de servicio y
  acceso de lectura a los assets; no se usan claves JSON en la imagen.
- Las credenciales locales de Earth Engine permanecen fuera del repositorio.
- El servidor registra identificadores técnicos; la interfaz muestra errores breves y
  comprensibles.
