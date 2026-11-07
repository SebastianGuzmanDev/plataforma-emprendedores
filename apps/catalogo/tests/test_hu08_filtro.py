"""
HU-08 · Filtrar el catálogo por categoría (Must) · RF-10 · CU-08 «extend» CU-07 · S4.
"""
from django.test import TestCase

from .utilidades import URL_CATALOGO, crear_producto, emprendimientos_de_prueba


class HU08FiltroTests(TestCase):
    def setUp(self):
        self.comida, self.artesanias = emprendimientos_de_prueba()
        crear_producto(self.comida, "Arepa de queso")
        crear_producto(self.comida, "Empanada")
        crear_producto(self.artesanias, "Pulsera tejida")

    def test_cp_08_1_filtrar_por_una_categoria_muestra_solo_sus_productos(self):
        """CP-08.1 · Esc. 1: al filtrar por una categoría solo veo sus productos."""
        respuesta = self.client.get(URL_CATALOGO, {"categoria": "artesanias"})
        self.assertContains(respuesta, "Pulsera tejida")
        self.assertNotContains(respuesta, "Arepa de queso")
        self.assertNotContains(respuesta, "Empanada")
        self.assertContains(respuesta, "1 producto en Artesanías")

    def test_cp_08_2_categoria_sin_productos_indica_que_no_hay_resultados(self):
        """CP-08.2 · Esc. 2: la categoría no tiene productos → mensaje de que no hay resultados."""
        respuesta = self.client.get(URL_CATALOGO, {"categoria": "videojuegos"})
        self.assertContains(respuesta, "No hay productos en la categoría Videojuegos")
        self.assertNotContains(respuesta, 'class="tarjeta-producto"')

    def test_cp_08_3_limpiar_el_filtro_vuelve_a_mostrar_todo(self):
        """CP-08.3 · Esc. 3: con un filtro aplicado, al limpiarlo vuelvo a ver todo el catálogo."""
        filtrado = self.client.get(URL_CATALOGO, {"categoria": "comida"})
        self.assertContains(filtrado, f'href="{URL_CATALOGO}"')  # «Todas» / «Limpiar filtros»
        self.assertContains(filtrado, "Limpiar filtros")
        completo = self.client.get(URL_CATALOGO)
        for nombre in ["Arepa de queso", "Empanada", "Pulsera tejida"]:
            self.assertContains(completo, nombre)
        self.assertNotContains(completo, "Limpiar filtros")

    def test_las_categorias_se_ofrecen_como_enlaces_y_marcan_la_actual(self):
        html = self.client.get(URL_CATALOGO, {"categoria": "comida"}).content.decode()
        for slug in ["artesanias", "comida", "ocio", "otros", "videojuegos"]:
            self.assertIn(f'href="?categoria={slug}"', html)
        self.assertRegex(html, r'href="\?categoria=comida"[^>]*aria-current="page"')
        self.assertNotRegex(html, r'href="\?categoria=artesanias"[^>]*aria-current="page"')

    def test_una_categoria_inexistente_muestra_todo_el_catalogo(self):
        respuesta = self.client.get(URL_CATALOGO, {"categoria": "no-existe"})
        self.assertContains(respuesta, "3 productos")
        html = respuesta.content.decode()
        self.assertNotRegex(html, r'href="\?categoria=[^"]*"[^>]*aria-current="page"')
        self.assertRegex(html, r'>Todas</a>')

    def test_filtrar_por_categoria_del_modulo_catalogo(self):
        """S4 · filtrarPorCategoria(categoria)."""
        from apps.catalogo.servicios import filtrar_por_categoria, listar_productos
        from apps.perfil_productos.models import Categoria

        artesanias = Categoria.objects.get(nombre="Artesanías")
        nombres = [p.nombre for p in filtrar_por_categoria(listar_productos(), artesanias)]
        self.assertEqual(nombres, ["Pulsera tejida"])
