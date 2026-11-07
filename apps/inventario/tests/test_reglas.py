"""
Pruebas UNITARIAS de las reglas de la Épica 5 (RN-10, RN-11, RN-12) y de las operaciones
de Producto del diagrama de colaboración C2. Valores límite del plan de pruebas (4.1.4):
existencias 0, 1, 25 válidas y -1, 2.5 inválidas; existencias 5 y salida 6 rechazada;
insumo con costo vacío o cantidad 0 rechazado.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from apps.inventario.reglas import interpretar_cantidad_insumo, interpretar_entero
from apps.perfil_productos.models import Producto

from .utilidades import producto_con_existencias


class ReglaCantidadEnteraTests(SimpleTestCase):
    """RN-10: las existencias son enteros no negativos."""

    def test_rn10_acepta_enteros_no_negativos(self):
        for texto, esperado in [("0", 0), ("1", 1), ("25", 25), (" 7 ", 7)]:
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_entero(texto), esperado)

    def test_rn10_rechaza_negativos_decimales_y_letras(self):
        for texto in ["-1", "2.5", "2,5", "abc", "", "  ", None, "1e3", "1000000"]:
            with self.subTest(texto=texto):
                self.assertIsNone(interpretar_entero(texto))

    def test_un_movimiento_exige_al_menos_una_unidad(self):
        self.assertIsNone(interpretar_entero("0", minimo=1))
        self.assertEqual(interpretar_entero("1", minimo=1), 1)


class ReglaInsumoTests(SimpleTestCase):
    """RN-12: un insumo requiere nombre, cantidad distinta de 0 y costo."""

    def test_rn12_cantidad_decimal_mayor_que_cero(self):
        for texto, esperado in [("2", Decimal("2")), ("2,5", Decimal("2.5")), ("0.75", Decimal("0.75"))]:
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_cantidad_insumo(texto), esperado)

    def test_rn12_cantidad_cero_negativa_o_invalida_se_rechaza(self):
        for texto in ["0", "0,0", "-1", "abc", "", None, "1,2345"]:
            with self.subTest(texto=texto):
                self.assertIsNone(interpretar_cantidad_insumo(texto))


class OperacionesProductoTests(TestCase):
    """C2: obtenerExistencias(), descontar(cantidad), marcarAgotado() y tieneStockBajo()."""

    def test_c2_tiene_stock_bajo_cuando_las_existencias_bajan_del_umbral(self):
        producto = producto_con_existencias(existencias=4, umbral=5)
        self.assertTrue(producto.tiene_stock_bajo())

    def test_rn11_en_el_umbral_o_por_encima_no_hay_alerta(self):
        for existencias in (5, 6, 50):
            with self.subTest(existencias=existencias):
                producto = Producto(existencias=existencias, umbral_stock_bajo=5)
                self.assertFalse(producto.tiene_stock_bajo())

    def test_sin_umbral_o_sin_existencias_registradas_no_hay_alerta(self):
        self.assertFalse(Producto(existencias=1, umbral_stock_bajo=None).tiene_stock_bajo())
        self.assertFalse(Producto(existencias=None, umbral_stock_bajo=5).tiene_stock_bajo())

    def test_obtener_existencias(self):
        self.assertEqual(producto_con_existencias(existencias=7).obtener_existencias(), 7)
        self.assertIsNone(Producto().obtener_existencias())

    def test_la_base_de_datos_impide_existencias_negativas(self):
        producto = producto_con_existencias(existencias=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.filter(pk=producto.pk).update(existencias=-1)
