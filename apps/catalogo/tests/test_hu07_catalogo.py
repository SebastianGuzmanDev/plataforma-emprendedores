"""
HU-07 · Ver el catálogo de productos (Must) · RF-09, RNF-01 · CU-07 · diagrama S4.
"""
import re

from django.test import TestCase

from .utilidades import (
    URL_CATALOGO,
    EstadoProducto,
    Producto,
    cargar_productos,
    crear_producto,
    emprendimientos_de_prueba,
    url_detalle,
)


class HU07CatalogoTests(TestCase):
    def setUp(self):
        self.comida, self.artesanias = emprendimientos_de_prueba()

    def test_cp_07_1_con_productos_activos_muestra_el_listado(self):
        """CP-07.1 · Esc. 1: hay productos activos → veo el listado."""
        arepa = crear_producto(self.comida, "Arepa de queso", 5000)
        pulsera = crear_producto(self.artesanias, "Pulsera tejida", 12000)
        respuesta = self.client.get(URL_CATALOGO)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "catalogo/listado.html")
        for producto, precio in [(arepa, "$ 5.000"), (pulsera, "$ 12.000")]:
            with self.subTest(producto=producto.nombre):
                self.assertContains(respuesta, producto.nombre)
                self.assertContains(respuesta, precio)
                self.assertContains(respuesta, f'href="{url_detalle(producto)}"')
        self.assertContains(respuesta, "2 productos")

    def test_cp_07_1_cada_tarjeta_muestra_el_emprendimiento_y_la_categoria(self):
        crear_producto(self.comida, "Arepa de queso")
        respuesta = self.client.get(URL_CATALOGO)
        self.assertContains(respuesta, "Arepas Doña Rosa")
        self.assertContains(respuesta, "Comida")

    def test_cp_07_2_sin_productos_activos_indica_que_el_catalogo_esta_vacio(self):
        """CP-07.2 · Esc. 2: no hay productos activos → mensaje de catálogo vacío."""
        crear_producto(self.comida, "Jugo", estado=EstadoProducto.DESACTIVADO)
        respuesta = self.client.get(URL_CATALOGO)
        self.assertContains(respuesta, "Todavía no hay productos en el catálogo")
        self.assertNotContains(respuesta, "Jugo")

    def test_cp_07_3_los_productos_desactivados_no_aparecen(self):
        """CP-07.3 · Esc. 3: hay productos desactivados → no aparecen en el listado."""
        crear_producto(self.comida, "Arepa de queso")
        desactivado = crear_producto(self.comida, "Jugo de mango", estado=EstadoProducto.DESACTIVADO)
        respuesta = self.client.get(URL_CATALOGO)
        self.assertContains(respuesta, "Arepa de queso")
        self.assertNotContains(respuesta, "Jugo de mango")
        self.assertNotContains(respuesta, str(desactivado.codigo))
        self.assertContains(respuesta, "1 producto")

    def test_rn09_los_agotados_aparecen_con_su_etiqueta_despues_de_los_disponibles(self):
        crear_producto(self.comida, "Empanada", estado=EstadoProducto.AGOTADO)
        crear_producto(self.comida, "Arepa de queso")
        html = self.client.get(URL_CATALOGO).content.decode()
        self.assertIn(">Agotado<", html)
        self.assertLess(html.index("Arepa de queso"), html.index("Empanada"))

    def test_s4_el_catalogo_se_consulta_sin_iniciar_sesion(self):
        """Supuesto S-4 del Entregable 2: catálogo, búsqueda y detalle no exigen sesión."""
        crear_producto(self.comida, "Arepa de queso")
        self.assertContains(self.client.get(URL_CATALOGO), "Arepa de queso")

    def test_el_listado_se_pagina_de_24_en_24(self):
        cargar_productos(30, self.comida)
        primera = self.client.get(URL_CATALOGO).content.decode()
        segunda = self.client.get(URL_CATALOGO, {"pagina": 2}).content.decode()
        self.assertEqual(len(re.findall(r'class="tarjeta-producto"', primera)), 24)
        self.assertEqual(len(re.findall(r'class="tarjeta-producto"', segunda)), 6)
        self.assertIn("Página 1 de 2", primera)
        self.assertIn('href="?pagina=2"', primera)
        self.assertIn("30 productos", primera)

    def test_una_pagina_invalida_muestra_la_primera_o_la_ultima(self):
        cargar_productos(3, self.comida)
        for pagina in ["abc", "-1", "99"]:
            with self.subTest(pagina=pagina):
                self.assertEqual(self.client.get(URL_CATALOGO, {"pagina": pagina}).status_code, 200)

    def test_las_tarjetas_usan_la_miniatura_con_texto_alternativo(self):
        producto = crear_producto(self.comida, "Arepa de queso")
        respuesta = self.client.get(URL_CATALOGO)
        self.assertContains(respuesta, f'src="{producto.url_miniatura}" alt="Arepa de queso"')

    def test_el_encabezado_enlaza_el_catalogo_para_todos(self):
        self.assertContains(self.client.get("/"), f'href="{URL_CATALOGO}"')


class HU07ListarProductosTests(TestCase):
    """S4 · listarProductos(): consulta los productos no desactivados."""

    def test_listar_productos_aplica_rn09_y_ordena_disponibles_primero(self):
        from apps.catalogo.servicios import listar_productos

        comida, _ = emprendimientos_de_prueba()
        agotado = crear_producto(comida, "Empanada", estado=EstadoProducto.AGOTADO)
        disponible = crear_producto(comida, "Arepa")
        crear_producto(comida, "Jugo", estado=EstadoProducto.DESACTIVADO)
        self.assertEqual(list(listar_productos()), [disponible, agotado])
        self.assertTrue(all(isinstance(p, Producto) for p in listar_productos()))
