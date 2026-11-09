# Guía de transferencia y operación

## Lo que se entrega

- Aplicación Flask en `webapp/`.
- Motores científicos Python reutilizados por la API.
- Datos territoriales públicos incluidos en `data/territorio/`.
- Catálogo y documentación metodológica.
- Dockerfile sin credenciales y plantilla de Cloud Run.

## Lo que no se entrega en Git

- Credenciales OAuth de Earth Engine.
- Claves JSON de cuentas de servicio.
- Tokens, contraseñas o archivos `.env` reales.
- Copias de los assets institucionales privados.
- Resultados efímeros de la caché en memoria.

## Traspaso a otra identidad

1. Registrar el proyecto de cuota para Earth Engine.
2. Crear o seleccionar una cuenta de servicio de ejecución sin clave descargada.
3. Otorgar los permisos mínimos documentados en
   `FASE6_SEGURIDAD_CLOUD_RUN_PRIVADO.md`.
4. Compartir con esa identidad los assets SINIA requeridos.
5. Definir `GEE_PROJECT_ID=geoportal-513817` y desplegar de forma privada.
6. Ejecutar una lectura mínima y un análisis representativo antes de habilitar usuarios.

## Desactivación

Cloud Run puede deshabilitarse eliminando el servicio o fijando el ingreso privado y
revocando el permiso de invocación. Revocar el acceso de la cuenta de servicio a los
assets detiene los análisis institucionales sin eliminar los datos.

## Pendientes previos a producción

- Prueba real de la identidad de Cloud Run sobre los assets 2021 y 2023.
- Almacenamiento persistente si se necesitan resultados después de reiniciar.
- Monitorización de costos, latencia y errores de Earth Engine.
- Revisión legal final de atribuciones y condiciones de redistribución.
