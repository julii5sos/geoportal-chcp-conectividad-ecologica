# Configuración de Earth Engine — `geoportal-513817`

## Implementación

La conexión se centraliza en `gee_config.py`. `app_temporal.py` y
`app_experiencia.py` usan el mismo inicializador, por lo que cobertura temporal,
fragmentación, conectividad, ERI y estadísticas comparten el proyecto de cuota
y la identidad de ejecución.

Orden de resolución del proyecto:

1. Variable/secreto `GEE_PROJECT_ID`.
2. Alias transitorio `EE_PROJECT`.
3. Valor predeterminado `geoportal-513817`.

No existen tokens ni claves en el código. Si no hay una cuenta de servicio,
Earth Engine usa las credenciales locales administradas fuera del repositorio.
En servidor, `GEE_SERVICE_ACCOUNT_JSON` tiene prioridad; el nombre anterior
`EE_SERVICE_ACCOUNT_JSON` se admite durante la migración. La aplicación rechaza
un JSON cuyo `project_id` no coincida con el proyecto configurado.

## Autenticación local con la cuenta nueva

Ejecute una sola vez en una terminal local:

```powershell
$env:GEE_PROJECT_ID = "geoportal-513817"
earthengine authenticate --force --auth_mode=localhost
python scripts/verificar_conexion_gee.py --project geoportal-513817 --jrc
```

`--force` evita reutilizar silenciosamente el token anterior. En la ventana de
Google se debe seleccionar expresamente la cuenta nueva. El repositorio no puede
deducir con seguridad el correo asociado a un token OAuth y, por diseño, no lo
imprime en registros.

El verificador realiza dos consultas: confirma la banda `elevation` de
`USGS/SRTMGL1_003` y, con `--jrc`, calcula una comparación JRC TMF 2020–2025 en
un rectángulo pequeño y comprueba el cierre de las transiciones.

## Despliegue futuro en Streamlit Cloud

Pendiente de autorización administrativa:

1. Confirmar que `geoportal-513817` esté registrado para Earth Engine y tenga la
   API de Earth Engine habilitada.
2. Crear o seleccionar una cuenta de servicio dentro de ese proyecto.
3. Asignar solo los roles necesarios. Earth Engine documenta
   `Earth Engine Resource Viewer` y, según la configuración, `Service Usage
   Consumer` para operaciones de lectura/cómputo.
4. Solo si se autoriza, crear una clave JSON para Streamlit Community Cloud.
   Cuando existe identidad administrada/ADC es preferible no crear claves, pero
   Community Cloud normalmente requiere el secreto JSON.
5. Guardar en **App settings > Secrets**, nunca en Git:
   `GEE_PROJECT_ID`, `GEE_SERVICE_ACCOUNT_JSON` y los identificadores privados
   de assets que se decida conservar.

## Inventario de assets

| Recurso | Tipo | Acción |
|---|---|---|
| `projects/JRC/TMF/v1_2025/AnnualChanges` | Público JRC | Sin migración; lectura e integración 2020–2025 verificadas con el proyecto nuevo. |
| `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS` | Público ESRI | Sin migración; el algoritmo no fue modificado. |
| `USGS/SRTMGL1_003` | Público USGS | Sin migración; prueba mínima de conexión. |
| `EE_ASSET_BOSQUE_2021` | Privado institucional | Compartir con la cuenta de servicio o migrar a `projects/geoportal-513817/assets/...`. Necesario para la fragmentación/conectividad institucional de 2021. |
| `EE_ASSET_FINCAS` | Privado, legado opcional | La interfaz pública ya no ofrece fincas. Migrar solo si se decide conservar el flujo administrativo legado. |
| Cuenca y subcuencas CHCP | GeoJSON local | No requiere permisos de Earth Engine. |
| Corredores y puntos críticos | Datos locales públicos | No requiere permisos de Earth Engine. |
| `users/openforisearthmap/.../CanopyHeight_GEDI_V27` | Recurso externo | No migrar; comprobar disponibilidad para la identidad del despliegue. |

No se modificaron permisos IAM ni se generaron claves durante esta tarea.

## Resultado de la verificación local

Después de autenticar expresamente la cuenta nueva, Earth Engine inicializó con
`geoportal-513817` usando credenciales locales. La prueba mínima confirmó la banda
`elevation` de `USGS/SRTMGL1_003`.

La única integración JRC solicitada comparó 2020–2025 sobre el rectángulo pequeño de
prueba: área válida común de `486.5978 ha` y diferencia de cierre de transiciones
`-0.000000 ha`. No se repitió ESRI porque su algoritmo no fue modificado. Esta tarea
no efectuó cambios IAM.

## Pruebas específicas

- `test_gee_config.py`: precedencia de proyecto, inicialización local, cuenta de
  servicio, rechazo de proyecto cruzado y assets opcionales.
- `scripts/verificar_conexion_gee.py`: lectura mínima SRTM y una integración JRC
  opcional.
- `test_analisis_temporal_ee.py`: ahora resuelve `GEE_PROJECT_ID` mediante la
  misma configuración compartida.

Las fuentes públicas y los algoritmos científicos no fueron modificados.

