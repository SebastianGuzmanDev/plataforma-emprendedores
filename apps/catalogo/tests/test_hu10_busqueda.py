"""
HU-10 · Buscar por palabra clave (Should) · RF-11 · CU-10 «extend» CU-07.
"""
from django.test import TestCase

from .utilidades import URL_CATALOGO, EstadoProducto, crear_producto, emprendimientos_de_prueba


class HU10BusquedaTests(TestCase):
    def setUp(self):
        self.comida, self.artesanias = emprendimientos_de_prueba()
        crear_producto(self.comida, "Café de origen", 3000)
        crear_producto(self.comida, "Arepa de queso", 5000)
        crear_producto(self.artesanias, "Pulsera tejida", 12000)

    def test_cp_10_1_la_palabra_encuentra_el_producto(self):
        """CP-10.1 · Esc. 1: existe un producto que coincide → aparece en los resultados."""
        respuesta = self.client.get(URL_CATALOGO, {"q": "arepa"})
        self.assertContains(respuesta, "Arepa de queso")
        self.assertNotContains(respuesta, "Café de origen")
        self.assertNotContains(respuesta, "Pulsera tejida")
        self.assertContains(respuesta, "1 producto para «arepa»")

    def test_cp_10_2_sin_coincidencias_indica_que_no_hay_resultados(self):
        """CP-10.2 · Esc. 2: ningún producto coincide → mensaje de que no hay resultados."""
        respuesta = self.client.get(URL_CATALOGO, {"q": "pizza"})
        self.assertContains(respuesta, "No encontramos productos para «pizza»")
        self.assertNotContains(respuesta, 'class="tarjeta-producto"')

    def test_cp_10_3_mayusculas_y_tildes_dan_los_mismos_resultados(self):
        """CP-10.3 · Esc. 3: escribir en mayúsculas o sin tildes da los mismos resultados."""
        resultados = {}
        for consulta in ["café", "CAFÉ", "cafe", "Cafe"]:
            with self.subTest(consulta=consulta):
                respuesta = self.client.get(URL_CATALOGO, {"q": consulta})
                self.assertContains(respuesta, "Café de origen")
                resultados[consulta] = [p.pk for p in respuesta.context["productos"]]
        self.assertEqual(len({tuple(v) for v in resultados.values()}), 1)

    def test_busca_en_el_nombre_del_producto_y_no_en_el_del_emprendimiento(self):
        """RF-11 busca productos: «arepa» no trae el café de «Arepas Doña Rosa»."""
        respuesta = self.client.get(URL_CATALOGO, {"q": "dona rosa"})
        self.assertContains(respuesta, "No encontramos productos para «dona rosa»")

    def test_busqueda_y_filtro_se_combinan(self):
        respuesta = self.client.get(URL_CATALOGO, {"q": "tejida", "categoria": "comida"})
        self.assertContains(respuesta, "No encontramos productos para «tejida» en la categoría Comida")

    def test_la_busqueda_nunca_muestra_desactivados(self):
        crear_producto(self.comida, "Arepa vieja", estado=EstadoProducto.DESACTIVADO)
        self.assertNotContains(self.client.get(URL_CATALOGO, {"q": "arepa"}), "Arepa vieja")

    def test_la_consulta_se_conserva_en_el_buscador_y_en_la_paginacion(self):
        html = self.client.get(URL_CATALOGO, {"q": "café", "categoria": "comida"}).content.decode()
        self.assertIn('value="café"', html)
        self.assertIn('name="categoria" value="comida"', html)

    def test_la_consulta_se_muestra_escapada(self):
        respuesta = self.client.get(URL_CATALOGO, {"q": "<script>alert(1)</script>"})
        self.assertNotContains(respuesta, "<script>alert(1)</script>")
        self.assertContains(respuesta, "&lt;script&gt;")

    def test_las_consultas_muy_largas_se_recortan(self):
        respuesta = self.client.get(URL_CATALOGO, {"q": "a" * 500})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["consulta"]), 80)
