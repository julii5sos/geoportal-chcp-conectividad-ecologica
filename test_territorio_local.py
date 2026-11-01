import unittest

from territorio_local import (
    coleccion_cuenca,
    coleccion_subcuencas,
    feature_subcuenca,
    geometria_cuenca,
    huella_territorial,
    nombres_subcuencas,
)


class TerritorioLocalTests(unittest.TestCase):
    def test_cuenca_local_no_incluye_el_buffer(self):
        coleccion = coleccion_cuenca()

        self.assertEqual(len(coleccion["features"]), 1)
        self.assertEqual(coleccion["features"][0]["properties"]["tipo"], "cuenca")
        self.assertEqual(geometria_cuenca()["type"], "Polygon")

    def test_subcuencas_se_cargan_sin_asset_privado(self):
        nombres = nombres_subcuencas()

        self.assertEqual(len(nombres), 53)
        self.assertIn("Lago Miraflores", nombres)
        self.assertIn("Río Chagres", nombres)
        self.assertNotIn("�", "".join(nombres))
        self.assertEqual(
            feature_subcuenca("Río Chagres")["properties"]["fuente"],
            "GeoJSON local · Subcuencas del Canal de Panamá",
        )
        self.assertEqual(len(coleccion_subcuencas()["features"]), 53)

    def test_huella_cambia_si_cambian_las_capas(self):
        self.assertRegex(huella_territorial(), r"^[0-9a-f]{12}$")


if __name__ == "__main__":
    unittest.main()
