"""
Pruebas UNITARIAS de la búsqueda por palabra clave (HU-10 · RF-11).

Valores del plan de pruebas (Entregable 2, 4.1.4): «café», «CAFÉ» y «cafe» dan los
mismos resultados.
"""
from django.test import SimpleTestCase

from apps.catalogo.busqueda import coincide, normalizar_texto


class NormalizacionTests(SimpleTestCase):
    def test_quita_tildes_y_mayusculas(self):
        for texto in ["café", "CAFÉ", "cafe", "Café", " CAFE "]:
            with self.subTest(texto=texto):
                self.assertEqual(normalizar_texto(texto), "cafe")

    def test_trata_la_enie_y_la_dieresis_como_letras_base(self):
        self.assertEqual(normalizar_texto("Piñata Pingüino"), "pinata pinguino")

    def test_valores_vacios(self):
        self.assertEqual(normalizar_texto(None), "")
        self.assertEqual(normalizar_texto("   "), "")


class CoincidenciaTests(SimpleTestCase):
    def test_cp_10_3_mayusculas_y_tildes_dan_el_mismo_resultado(self):
        for consulta in ["café", "CAFÉ", "cafe"]:
            with self.subTest(consulta=consulta):
                self.assertTrue(coincide("Café de origen", consulta))

    def test_encuentra_la_palabra_dentro_del_texto(self):
        self.assertTrue(coincide("Arepa de queso", "queso"))
        self.assertTrue(coincide("Arepa de queso", "are"))

    def test_todas_las_palabras_de_la_consulta_deben_aparecer(self):
        self.assertTrue(coincide("Arepa de queso", "queso arepa"))
        self.assertFalse(coincide("Arepa de queso", "arepa pollo"))

    def test_busca_en_varios_textos(self):
        self.assertTrue(coincide(["Brownie", "Postres Doña Rosa"], "dona rosa"))

    def test_sin_coincidencia(self):
        self.assertFalse(coincide("Arepa de queso", "pizza"))

    def test_una_consulta_vacia_no_filtra(self):
        self.assertTrue(coincide("Arepa", ""))
        self.assertTrue(coincide("Arepa", "   "))
