"""Configuración compartida y segura de Google Earth Engine.

El módulo no contiene credenciales. Resuelve el proyecto de cuota, valida la
configuración de una cuenta de servicio cuando existe y, en desarrollo local,
delega en las credenciales OAuth/ADC administradas por Earth Engine.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping


DEFAULT_GEE_PROJECT_ID = "geoportal-513817"
PROJECT_KEYS = ("GEE_PROJECT_ID", "EE_PROJECT")
SERVICE_ACCOUNT_KEYS = ("GEE_SERVICE_ACCOUNT_JSON", "EE_SERVICE_ACCOUNT_JSON")
PRIVATE_ASSET_KEYS = ("EE_ASSET_BOSQUE_2021", "EE_ASSET_FINCAS")

SecretGetter = Callable[[str, Any], Any]


@dataclass(frozen=True)
class GeeConnection:
    project_id: str
    authentication_mode: str


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    limpio = str(valor).strip()
    return limpio or None


def _leer_configuracion(
    nombre: str,
    *,
    secret_getter: SecretGetter | None,
    environ: Mapping[str, str],
) -> Any:
    valor_entorno = environ.get(nombre)
    if _texto(valor_entorno) is not None:
        return valor_entorno
    if secret_getter is None:
        return None
    return secret_getter(nombre, None)


def resolver_proyecto_gee(
    *,
    secret_getter: SecretGetter | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resuelve el proyecto, priorizando GEE_PROJECT_ID sobre el alias anterior."""

    entorno = os.environ if environ is None else environ
    for nombre in PROJECT_KEYS:
        valor = _texto(
            _leer_configuracion(
                nombre,
                secret_getter=secret_getter,
                environ=entorno,
            )
        )
        if valor:
            return valor
    return DEFAULT_GEE_PROJECT_ID


def _informacion_cuenta_servicio(valor: Any, proyecto: str) -> dict[str, Any] | None:
    if valor is None:
        return None
    try:
        informacion = json.loads(valor) if isinstance(valor, str) else dict(valor)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("El secreto de la cuenta de servicio no es un JSON válido.") from exc

    faltantes = [
        clave
        for clave in ("project_id", "client_email", "private_key")
        if not _texto(informacion.get(clave))
    ]
    if faltantes:
        raise ValueError(
            "El secreto de la cuenta de servicio está incompleto; faltan: "
            + ", ".join(faltantes)
            + "."
        )
    if informacion["project_id"] != proyecto:
        raise ValueError(
            "La cuenta de servicio pertenece a un proyecto distinto del configurado. "
            "Revise GEE_PROJECT_ID antes de iniciar la aplicación."
        )
    return informacion


def inicializar_earth_engine(
    ee_module,
    *,
    secret_getter: SecretGetter | None = None,
    environ: Mapping[str, str] | None = None,
    credentials_factory=None,
) -> GeeConnection:
    """Inicializa EE con la misma política en todos los módulos del geoportal."""

    entorno = os.environ if environ is None else environ
    proyecto = resolver_proyecto_gee(
        secret_getter=secret_getter,
        environ=entorno,
    )
    secreto = None
    for nombre in SERVICE_ACCOUNT_KEYS:
        secreto = _leer_configuracion(
            nombre,
            secret_getter=secret_getter,
            environ=entorno,
        )
        if secreto is not None:
            break
    informacion = _informacion_cuenta_servicio(secreto, proyecto)

    if informacion is None:
        ee_module.Initialize(project=proyecto)
        return GeeConnection(proyecto, "credenciales_locales")

    if credentials_factory is None:
        from google.oauth2 import service_account

        credentials_factory = service_account.Credentials.from_service_account_info
    credenciales = credentials_factory(
        informacion,
        scopes=[
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/cloud-platform",
        ],
    )
    ee_module.Initialize(credentials=credenciales, project=proyecto)
    return GeeConnection(proyecto, "cuenta_de_servicio")


def assets_privados_configurados(
    *,
    secret_getter: SecretGetter | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str | None]:
    """Devuelve solo identificadores de assets; nunca inspecciona credenciales."""

    entorno = os.environ if environ is None else environ
    return {
        nombre: _texto(
            _leer_configuracion(
                nombre,
                secret_getter=secret_getter,
                environ=entorno,
            )
        )
        for nombre in PRIVATE_ASSET_KEYS
    }

