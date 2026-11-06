# Fase 6 — seguridad y publicación privada en Cloud Run

## Alcance y estado

Esta preparación corresponde a la rama `feature/web-html-api-chcp`. No crea
recursos, no cambia IAM, no publica el servicio y no modifica los algoritmos
científicos. La versión web conserva los motores temporales, el panel estadístico,
el ERI y la configuración compartida de Earth Engine del proyecto
`geoportal-513817`.

Cloud Run IAM será la barrera de autenticación primaria. La API Flask añade una
segunda barrera contra errores y abuso: tamaño máximo de solicitud, validación de
origen, catálogo cerrado de fuentes, límites geométricos, limitador por instancia,
semáforo de análisis y cabeceras de seguridad. El limitador en memoria **no es una
cuota global**: con dos instancias cada una conserva su propia ventana.

## Configuración conservadora preparada

| Control | Valor inicial | Motivo |
|---|---:|---|
| Instancias mínimas | 0 | Evita costo ocioso durante la prueba. |
| Instancias máximas | 2 | Limita gasto y presión sobre Earth Engine. |
| CPU / memoria | 2 vCPU / 2 GiB | Punto de partida para geometrías y resultados vectoriales. |
| Concurrencia Cloud Run | 4 solicitudes | Permite servir archivos y UI sin multiplicar procesos. |
| Análisis simultáneos por instancia | 1 | Evita dos cálculos pesados en la misma memoria. |
| Timeout Cloud Run / Gunicorn | 600 s / 540 s | Da margen para que Gunicorn cierre antes que la plataforma. |
| Área máxima | 345 000 ha | Admite la CHCP completa (~341 045 ha) sin aceptar áreas arbitrarias mayores. |
| Coordenadas máximas | 5 000 | Reduce geometrías patológicas. |
| Cuerpo HTTP máximo | 1 MiB | Suficiente para el GeoJSON permitido. |
| Elementos vectoriales para mapa | 1 500 | Acota el tamaño de respuesta y el navegador. |
| Caché | 4 resultados, 15 min | Reutilización breve; no es almacenamiento persistente. |
| Solicitudes de análisis/ERI | 4 por 10 min e identidad/instancia | Protección inicial para un grupo privado pequeño. |
| Descargas | 20 por 10 min e identidad/instancia | Evita repetición accidental. |

## Identidades y permisos mínimos

### 1. Identidad de ejecución

Usar una cuenta de servicio dedicada, por ejemplo:

`geoportal-chcp-runtime@geoportal-513817.iam.gserviceaccount.com`

No usar la cuenta predeterminada con `Editor`, no crear una clave JSON y no definir
`GOOGLE_APPLICATION_CREDENTIALS`. Cloud Run entrega credenciales de corta duración
mediante Application Default Credentials (ADC).

Roles de proyecto para la identidad de ejecución:

- `roles/earthengine.viewer` — Earth Engine Resource Viewer.
- `roles/serviceusage.serviceUsageConsumer` — necesario para consumir
  `geoportal-513817` como proyecto de cuota.

No requiere `earthengine.writer`, `earthengine.admin`, `Editor` ni `Owner` para los
cálculos interactivos de lectura implementados.

Los assets privados se autorizan en su propio control de acceso, solo en lectura:

- `EE_ASSET_BOSQUE_2021`: compartir con la cuenta de ejecución si se incorpora al
  servicio web o si también se publica la aplicación Streamlit.
- `EE_ASSET_FINCAS`: legado opcional; la interfaz pública no ofrece fincas y no debe
  migrarse salvo decisión expresa.
- `users/openforisearthmap/World_EarthMap/CanopyHeight_GEDI_V27`: recurso externo;
  comprobar lectura con la identidad final. No se puede migrar desde este repositorio.

JRC TMF, ESRI, SRTM, Dynamic World y los demás catálogos públicos no requieren
migración. Cuenca, subcuencas, corredores y puntos críticos se distribuyen como datos
locales del repositorio.

### 2. Identidad que despliega

La persona o automatización que despliega necesita, como mínimo y con alcance
restringido:

- permisos para crear/actualizar el servicio Cloud Run (habitualmente
  `roles/run.developer`; una administración inicial puede requerir permisos
  adicionales concretos);
- `roles/iam.serviceAccountUser` **sobre la cuenta de ejecución**, para adjuntarla;
- permiso de escritura en el repositorio específico de Artifact Registry;
- permiso para ejecutar Cloud Build si se usa `gcloud builds submit`.

La habilitación inicial de APIs requiere `serviceusage.services.enable`; debe hacerla
una persona autorizada. No debe concederse `Owner` o `Editor` solo por comodidad.

### 3. Personas de prueba

Cada correo o grupo autorizado recibe `roles/run.invoker` exclusivamente sobre el
servicio `geoportal-chcp-private`. Confirmar que no existan vinculaciones para
`allUsers` ni `allAuthenticatedUsers`.

## Procedimiento exacto — acciones de la administradora

Los comandos siguientes son una guía; no fueron ejecutados por Codex. Sustituya
`CORREO_ADMIN` y confirme la región antes de crear recursos facturables.

```bash
gcloud auth login
gcloud config set project geoportal-513817

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  earthengine.googleapis.com

gcloud iam service-accounts create geoportal-chcp-runtime \
  --display-name="Geoportal CHCP Cloud Run runtime"

gcloud projects add-iam-policy-binding geoportal-513817 \
  --member="serviceAccount:geoportal-chcp-runtime@geoportal-513817.iam.gserviceaccount.com" \
  --role="roles/earthengine.viewer"

gcloud projects add-iam-policy-binding geoportal-513817 \
  --member="serviceAccount:geoportal-chcp-runtime@geoportal-513817.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

Después, compartir en Earth Engine únicamente los assets privados necesarios. No
crear ni descargar una clave JSON.

Crear el repositorio de imágenes y construir una imagen implica facturación:

```bash
gcloud artifacts repositories create geoportal \
  --repository-format=docker \
  --location=us-central1 \
  --description="Imágenes privadas del Geoportal CHCP"

gcloud builds submit \
  --tag us-central1-docker.pkg.dev/geoportal-513817/geoportal/geoportal-chcp:phase6-candidate
```

Copiar `deploy/cloud-run-service.template.yaml` a un archivo local no confirmado en
Git, reemplazar la cuenta, región y etiqueta, revisar el diff y aplicar:

```bash
gcloud run services replace deploy/cloud-run-service.yaml \
  --region=us-central1 \
  --project=geoportal-513817
```

Mantener el servicio privado y autorizar solo a las personas de prueba:

```bash
gcloud run services remove-iam-policy-binding geoportal-chcp-private \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding geoportal-chcp-private \
  --region=us-central1 \
  --member="user:CORREO_ADMIN" \
  --role="roles/run.invoker"

gcloud run services get-iam-policy geoportal-chcp-private \
  --region=us-central1
```

La forma recomendada de probar un sitio privado desde un navegador es el proxy de
Cloud Run, que añade el token de la cuenta activa:

```bash
gcloud run services proxy geoportal-chcp-private \
  --project=geoportal-513817 \
  --region=us-central1 \
  --port=8080
```

Abrir `http://127.0.0.1:8080`. Dar `run.invoker` no convierte por sí solo la URL
`run.app` en un inicio de sesión web interactivo. Para acceso directo en navegador
sin CLI se debe evaluar IAP y un balanceador HTTPS, lo que añade configuración y
costos; no forma parte de la primera prueba privada.

## Comprobaciones posteriores al despliegue de prueba

1. Confirmar que la revisión usa la cuenta `geoportal-chcp-runtime`.
2. Confirmar que no existen variables `GOOGLE_APPLICATION_CREDENTIALS`,
   `GEE_SERVICE_ACCOUNT_JSON` ni secretos de claves.
3. Verificar IAM sin `allUsers`/`allAuthenticatedUsers`.
4. Probar `/api/v1/health` a través del proxy.
5. Ejecutar una sola comparación JRC pequeña 2020–2025.
6. Ejecutar ERI sobre un polígono pequeño.
7. Descargar el ZIP y verificar que expira después del TTL.
8. Revisar Cloud Logging sin geometrías completas, tokens ni datos sensibles.
9. Observar memoria, tiempo, instancias y errores de Earth Engine antes de ampliar
   límites.

## Riesgos operativos pendientes

- Los análisis son solicitudes HTTP síncronas. Si el cliente cierra el navegador, el
  cálculo del servidor puede continuar hasta terminar o alcanzar el timeout.
- La caché y el limitador viven en memoria y no se comparten entre instancias. Un
  reinicio elimina resultados y descargas. No son apropiados para ejecución pública
  masiva.
- Cuatro resultados vectoriales grandes pueden presionar 2 GiB. Medir memoria real;
  reducir `WEB_RESULT_CACHE_ENTRIES` a 2 o aumentar memoria antes de ampliar usuarios.
- `maxScale=2` y un análisis por instancia permiten, como máximo práctico, dos
  cálculos simultáneos del servicio, aunque cada instancia pueda servir otras
  solicitudes livianas.
- El rate limit local reduce errores accidentales, pero no reemplaza Cloud Armor,
  API Gateway o una cuota distribuida si el servicio se hace público.
- Los resultados no se guardan en una base de datos. La descarga depende de la
  instancia que conserva el resultado; Cloud Run no garantiza afinidad entre
  solicitudes. Para más de una instancia se debe probar esta ruta y, si falla,
  migrar resultados a Cloud Storage con expiración antes de una versión pública.

## Costos y control

La plantilla usa facturación por solicitud, `minScale=0` y `maxScale=2`. Cloud Run
cobra CPU, memoria, solicitudes y transferencia según región, después de aplicar el
nivel gratuito de la cuenta de facturación. También pueden cobrarse Cloud Build y el
almacenamiento de Artifact Registry. Earth Engine conserva sus propios términos y
cuotas.

Antes de crear recursos, usar la calculadora oficial con 2 vCPU, 2 GiB, duración
media observada y la región seleccionada. Configurar un presupuesto y alertas; una
alerta de presupuesto **no detiene automáticamente** el servicio.

## Desactivar o retirar la prueba

Bloqueo inmediato y recuperable: retirar `roles/run.invoker` a usuarios/grupos. Sin
tráfico y con `minScale=0`, las instancias vuelven a cero.

Eliminar el servicio detiene nuevas ejecuciones:

```bash
gcloud run services delete geoportal-chcp-private \
  --region=us-central1 \
  --project=geoportal-513817
```

Las imágenes de Artifact Registry permanecen y pueden generar un costo pequeño de
almacenamiento. Su eliminación es una acción separada y destructiva. No deshabilitar
APIs ni borrar el repositorio de imágenes si otros sistemas del proyecto los usan.

## Referencias oficiales

- Cloud Run service identity y ADC: <https://docs.cloud.google.com/run/docs/securing/service-identity>
- Prueba privada mediante proxy: <https://docs.cloud.google.com/run/docs/authenticating/developers>
- Identidades de servicio: <https://docs.cloud.google.com/run/docs/configuring/services/service-identity>
- Earth Engine, cuentas de servicio: <https://developers.google.com/earth-engine/guides/service_account>
- Earth Engine, roles y acceso: <https://developers.google.com/earth-engine/guides/access_control>
- Facturación por solicitud: <https://docs.cloud.google.com/run/docs/configuring/billing-settings>
- Precios de Cloud Run: <https://cloud.google.com/run/pricing>

