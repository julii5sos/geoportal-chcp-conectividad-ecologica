# Inventario para reproducción

| Elemento | Ubicación | Estado |
|---|---|---|
| Entrada Flask | `webapp/main.py` | Operativa |
| Servicio y caché | `webapp/service.py`, `webapp/cache.py` | Operativo |
| Modelos de solicitudes | `webapp/models.py` | Operativos |
| Interfaz de plataforma | `webapp/templates/platform.html` | Operativa |
| Lógica de mapa y resultados | `webapp/static/js/platform.js` | Operativa |
| Estilos | `webapp/static/css/webapp.css` | Operativos |
| Fragmentación/conectividad | `bosque_conectividad.py` | Conservado |
| Escenarios 2021/2023 | `estructura_cobertura.py` | Implementados |
| Cobertura 2023 | `cobertura_oficial_2023.py` | Implementada |
| Preevaluación | `metodologia_indice.py` y módulos de evidencia | Conservada |
| Corredores | `corredores.py` y datos asociados | Conservados |
| ERI | motor ERI existente | Conservado y separado |
| Informe PDF | `informe_tecnico.py` | Operativo para resultados en caché |
| Catálogo SINIA | `catalogo_assets_sinia.py` | Ocho assets registrados |
| Configuración GEE | `gee_config.py` | Proyecto centralizado |
| Dependencias web | `requirements-web.txt` | Flask sin Streamlit |
| Contenedor | `Dockerfile`, `deploy/` | Preparado; no desplegado |

La evidencia local de interfaz y PDF se conserva en `docs/capturas/`. Es evidencia de
la ejecución revisada, no datos fuente ni métricas inventadas.
