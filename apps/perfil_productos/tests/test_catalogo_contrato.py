"""
RN-09 · Contrato con el módulo Catálogo (E3).

«El catálogo muestra los productos disponibles y los agotados (con etiqueta) y oculta
los desactivados». E2 define y prueba esta consulta; E3 construye sobre ella la
pantalla pública, el filtro y la búsqueda.
"""
from django.test import TestCase

from apps.perfil_productos.models import Emprendimiento, EstadoProducto, Producto

from .utilidades import CORREO_EMPRENDEDOR_B, crear_emprendedor, crear_perfil, crear_producto


class ContratoCatalogoTests(TestCase):
    def setUp(self):
        self.emprendimiento = crear_perfil(crear_emprendedor())
        self.disponible = crear_producto(self.emprendimiento, "Arepa", estado=EstadoProducto.DISPONIBLE)
        self.agotado = crear_producto(self.emprendimiento, "Empanada", estado=EstadoProducto.AGOTADO)
        self.desactivado = crear_producto(self.emprendimiento, "Jugo", estado=EstadoProducto.DESACTIVADO)

    def test_rn09_el_catalogo_incluye_disponibles_y_agotados_y_oculta_desactivados(self):
        visibles = set(Producto.objects.visibles_en_catalogo())
        self.assertEqual(visibles, {self.disponible, self.agotado})

    def test_cada_producto_se_clasifica_por_la_categoria_de_su_emprendimiento(self):
        """Supuesto S-1 del Entregable 2."""
        crear_producto(crear_perfil(crear_emprendedor(CORREO_EMPRENDEDOR_B), categoria="Artesanías"), "Pulsera")
        por_categoria = {p.nombre: p.categoria.nombre for p in Producto.objects.visibles_en_catalogo()}
        self.assertEqual(por_categoria, {"Arepa": "Comida", "Empanada": "Comida", "Pulsera": "Artesanías"})

    def test_la_consulta_trae_emprendimiento_y_categoria_en_una_sola_consulta(self):
        with self.assertNumQueries(1):
            for producto in Producto.objects.visibles_en_catalogo():
                producto.emprendimiento.categoria.nombre

    def test_todos_los_perfiles_creados_son_visibles(self):
        self.assertEqual(list(Emprendimiento.objects.visibles_en_catalogo()), [self.emprendimiento])
