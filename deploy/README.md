# Preparación de Cloud Run

`cloud-run-service.template.yaml` contiene una configuración inicial conservadora.
No contiene credenciales y no concede acceso público.

Antes de usarla:

1. Copiarla como `cloud-run-service.yaml` y no confirmar esa copia si contiene
   valores específicos del entorno.
2. Reemplazar la cuenta de servicio, la región de Artifact Registry y la etiqueta.
3. Revisar que la cuenta sea la identidad dedicada del Geoportal.
4. Aplicar el servicio y administrar `roles/run.invoker` por separado.
5. Verificar que no existan miembros `allUsers` o `allAuthenticatedUsers`.

La guía completa, los roles mínimos, los comandos de prueba privada y el
procedimiento de apagado están en
[`docs/FASE6_SEGURIDAD_CLOUD_RUN_PRIVADO.md`](../docs/FASE6_SEGURIDAD_CLOUD_RUN_PRIVADO.md).

