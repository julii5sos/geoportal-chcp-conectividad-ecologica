import json
import unittest

from gee_config import (
    DEFAULT_GEE_PROJECT_ID,
    assets_privados_configurados,
    inicializar_earth_engine,
    resolver_proyecto_gee,
)


class _EarthEngineFalso:
    def __init__(self):
        self.llamadas = []

    def Initialize(self, **kwargs):
        self.llamadas.append(kwargs)


class ConfiguracionGeeTests(unittest.TestCase):
    def test_proyecto_predeterminado_es_el_nuevo(self):
        self.assertEqual(
            resolver_proyecto_gee(environ={}),
            "geoportal-513817",
        )
        self.assertEqual(DEFAULT_GEE_PROJECT_ID, "geoportal-513817")

    def test_gee_project_id_tiene_prioridad_sobre_alias_anterior(self):
        proyecto = resolver_proyecto_gee(
            environ={
                "GEE_PROJECT_ID": "geoportal-513817",
                "EE_PROJECT": "proyecto-anterior",
            }
        )
        self.assertEqual(proyecto, "geoportal-513817")

    def test_inicializacion_local_usa_el_proyecto_configurado(self):
        ee_falso = _EarthEngineFalso()
        conexion = inicializar_earth_engine(
            ee_falso,
            environ={"GEE_PROJECT_ID": "geoportal-513817"},
        )
        self.assertEqual(conexion.project_id, "geoportal-513817")
        self.assertEqual(conexion.authentication_mode, "credenciales_locales")
        self.assertEqual(ee_falso.llamadas, [{"project": "geoportal-513817"}])

    def test_cloud_run_usa_application_default_credentials_sin_clave(self):
        ee_falso = _EarthEngineFalso()
        conexion = inicializar_earth_engine(
            ee_falso,
            environ={
                "GEE_PROJECT_ID": "geoportal-513817",
                "K_SERVICE": "geoportal-chcp-private",
            },
        )
        self.assertEqual(conexion.authentication_mode, "application_default_credentials")
        self.assertEqual(ee_falso.llamadas, [{"project": "geoportal-513817"}])

    def test_cloud_run_rechaza_clave_json_inline(self):
        with self.assertRaisesRegex(ValueError, "Application Default Credentials"):
            inicializar_earth_engine(
                _EarthEngineFalso(),
                environ={
                    "GEE_PROJECT_ID": "geoportal-513817",
                    "K_SERVICE": "geoportal-chcp-private",
                    "GEE_SERVICE_ACCOUNT_JSON": json.dumps(
                        {
                            "project_id": "geoportal-513817",
                            "client_email": "geoportal@example.invalid",
                            "private_key": "valor-solo-para-prueba",
                        }
                    ),
                },
            )

    def test_cuenta_de_servicio_se_valida_sin_exponer_el_secreto(self):
        ee_falso = _EarthEngineFalso()
        informacion = {
            "project_id": "geoportal-513817",
            "client_email": "geoportal@example.invalid",
            "private_key": "valor-solo-para-prueba",
        }
        credencial_falsa = object()
        llamadas_fabrica = []

        def fabricar(info, scopes):
            llamadas_fabrica.append((info, scopes))
            return credencial_falsa

        conexion = inicializar_earth_engine(
            ee_falso,
            environ={
                "GEE_PROJECT_ID": "geoportal-513817",
                "GEE_SERVICE_ACCOUNT_JSON": json.dumps(informacion),
            },
            credentials_factory=fabricar,
        )
        self.assertEqual(conexion.authentication_mode, "cuenta_de_servicio")
        self.assertEqual(
            ee_falso.llamadas,
            [{"credentials": credencial_falsa, "project": "geoportal-513817"}],
        )
        self.assertEqual(llamadas_fabrica[0][0], informacion)

    def test_rechaza_cuenta_de_servicio_de_otro_proyecto(self):
        with self.assertRaisesRegex(ValueError, "proyecto distinto"):
            inicializar_earth_engine(
                _EarthEngineFalso(),
                environ={
                    "GEE_PROJECT_ID": "geoportal-513817",
                    "GEE_SERVICE_ACCOUNT_JSON": json.dumps(
                        {
                            "project_id": "proyecto-anterior",
                            "client_email": "anterior@example.invalid",
                            "private_key": "valor-solo-para-prueba",
                        }
                    ),
                },
                credentials_factory=lambda *_args, **_kwargs: object(),
            )

    def test_assets_privados_son_configuracion_independiente(self):
        assets = assets_privados_configurados(
            environ={
                "EE_ASSET_BOSQUE_2021": "projects/geoportal-513817/assets/bosque",
            }
        )
        self.assertEqual(
            assets["EE_ASSET_BOSQUE_2021"],
            "projects/geoportal-513817/assets/bosque",
        )
        self.assertIsNone(assets["EE_ASSET_FINCAS"])


if __name__ == "__main__":
    unittest.main()

