"""
HU-15 · Registrar las existencias de un producto (Should) · RF-17 · CU-15.
HU-16 · Actualizar existencias con entradas y salidas (Should) · RF-18 · CU-16 · A4 · S6 · C2.
"""
from django.test import TestCase

from apps.catalogo.servicios import listar_productos
from apps.inventario.models import MovimientoInventario, TipoMovimiento

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    URL_INVENTARIO,
    EstadoProducto,
    entrar,
    producto_con_existencias,
    url,
)


class HU15RegistrarExistenciasTests(TestCase):
    def setUp(self):
        self.producto = producto_con_existencias()
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_15_1_registrar_una_cantidad_entera_guarda_las_existencias(self):
        """CP-15.1 · Esc. 1: registrar una cantidad en unidades enteras → existencias guardadas."""
        pagina = self.client.get(url("producto", self.producto))
        self.assertContains(pagina, "Sin registrar")
        respuesta = self.client.post(url("existencias", self.producto), {"existencias": "25"}, follow=True)
        self.assertRedirects(respuesta, url("producto", self.producto))
        self.assertContains(respuesta, "Registraste 25 unidades de «Arepa de queso»")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.existencias, 25)
        movimiento = MovimientoInventario.objects.get()
        self.assertEqual((movimiento.tipo, movimiento.cantidad), (TipoMovimiento.ENTRADA, 25))

    def test_cp_15_2_cantidad_negativa_o_decimal_se_rechaza(self):
        """CP-15.2 · Esc. 2: un número negativo o decimal se rechaza."""
        for valor in ["-1", "2.5", "2,5", "abc"]:
            with self.subTest(valor=valor):
                respuesta = self.client.post(url("existencias", self.producto), {"existencias": valor})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Escribe una cantidad en unidades enteras")
        self.producto.refresh_from_db()
        self.assertIsNone(self.producto.existencias)
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_registrar_cero_existencias_deja_el_producto_agotado(self):
        """RN-10: si las existencias quedan en 0, el producto pasa a Agotado."""
        self.client.post(url("existencias", self.producto), {"existencias": "0"})
        self.producto.refresh_from_db()
        self.assertEqual((self.producto.existencias, self.producto.estado), (0, EstadoProducto.AGOTADO))

    def test_las_existencias_se_registran_una_sola_vez_y_luego_se_usan_movimientos(self):
        self.client.post(url("existencias", self.producto), {"existencias": "10"})
        respuesta = self.client.post(url("existencias", self.producto), {"existencias": "99"}, follow=True)
        self.assertContains(respuesta, "ya tiene existencias registradas")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.existencias, 10)


class HU16MovimientosTests(TestCase):
    def setUp(self):
        self.producto = producto_con_existencias(existencias=5)
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def mover(self, tipo, cantidad, follow=False):
        return self.client.post(url("movimiento", self.producto), {"tipo": tipo, "cantidad": cantidad}, follow=follow)

    def test_cp_16_1_entradas_y_salidas_validas_actualizan_las_existencias(self):
        """CP-16.1 · Esc. 1: una entrada o salida válida actualiza las existencias."""
        respuesta = self.mover("ENTRADA", "3", follow=True)
        self.assertContains(respuesta, "Entrada de 3 unidades registrada. Existencias: 8.")
        self.mover("SALIDA", "2")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.existencias, 6)
        self.assertEqual(
            list(MovimientoInventario.objects.order_by("id").values_list("tipo", "cantidad")),
            [(TipoMovimiento.ENTRADA, 3), (TipoMovimiento.SALIDA, 2)],
        )
        historial = self.client.get(url("producto", self.producto))
        self.assertContains(historial, "Entrada")
        self.assertContains(historial, "Salida")

    def test_cp_16_2_una_salida_mayor_a_las_existencias_se_rechaza(self):
        """CP-16.2 · Esc. 2 · S6 alt: existencias 5 y salida 6 → se rechaza y las existencias siguen en 5."""
        respuesta = self.mover("SALIDA", "6")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No puedes sacar 6 unidades: solo hay 5")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.existencias, 5)
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_cp_16_3_una_salida_que_deja_las_existencias_en_0_pasa_el_producto_a_agotado(self):
        """CP-16.3 · Esc. 3 · S6 opt: existencias 5 y salida 5 → quedan en 0 y el producto pasa a Agotado."""
        respuesta = self.mover("SALIDA", "5", follow=True)
        self.assertContains(respuesta, "«Arepa de queso» quedó agotado")
        self.producto.refresh_from_db()
        self.assertEqual((self.producto.existencias, self.producto.estado), (0, EstadoProducto.AGOTADO))
        self.assertEqual(listar_productos().get(pk=self.producto.pk).estado, EstadoProducto.AGOTADO)

    def test_a4_la_cantidad_debe_ser_un_entero_de_al_menos_una_unidad(self):
        for cantidad in ["0", "-2", "1.5", "abc", ""]:
            with self.subTest(cantidad=cantidad):
                respuesta = self.mover("ENTRADA", cantidad)
                self.assertContains(respuesta, "Escribe una cantidad entera de al menos 1 unidad")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.existencias, 5)

    def test_el_tipo_de_movimiento_es_obligatorio(self):
        respuesta = self.mover("REGALO", "1")
        self.assertContains(respuesta, "Elige si es una entrada o una salida")

    def test_cc09_una_entrada_vuelve_a_dejar_disponible_un_producto_agotado(self):
        """CC-09 (punto B.2): al reponer existencias, el producto agotado vuelve a Disponible."""
        self.mover("SALIDA", "5")
        respuesta = self.mover("ENTRADA", "4", follow=True)
        self.assertContains(respuesta, "volvió a estar disponible")
        self.producto.refresh_from_db()
        self.assertEqual((self.producto.existencias, self.producto.estado), (4, EstadoProducto.DISPONIBLE))

    def test_marcar_disponible_a_mano_con_existencias_en_0_no_se_permite(self):
        """Coherencia: un producto con inventario en 0 no puede ofrecerse como disponible."""
        self.mover("SALIDA", "5")
        from django.urls import reverse

        respuesta = self.client.post(
            reverse("emprendimiento:disponible", kwargs={"codigo": self.producto.codigo}), follow=True
        )
        self.assertContains(respuesta, "registra una entrada de inventario")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, EstadoProducto.AGOTADO)

    def test_sin_existencias_registradas_se_pide_registrarlas_primero(self):
        sin_registro = producto_con_existencias(correo="otra.persona@amigo.edu.co", nombre="Pulsera")
        self.client.logout()
        entrar(self.client, "otra.persona@amigo.edu.co")
        respuesta = self.client.post(url("movimiento", sin_registro), {"tipo": "ENTRADA", "cantidad": "1"}, follow=True)
        self.assertContains(respuesta, "Primero registra las existencias")
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_un_producto_desactivado_no_admite_movimientos(self):
        self.producto.estado = EstadoProducto.DESACTIVADO
        self.producto.save()
        respuesta = self.mover("ENTRADA", "1", follow=True)
        self.assertContains(respuesta, "desactivado")
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_los_movimientos_solo_se_aceptan_por_post(self):
        self.assertEqual(self.client.get(url("movimiento", self.producto)).status_code, 405)

    def test_el_panel_de_inventario_lista_los_productos_con_sus_existencias(self):
        respuesta = self.client.get(URL_INVENTARIO)
        self.assertContains(respuesta, "Arepa de queso")
        self.assertContains(respuesta, '<span class="existencias">5</span>')
        self.assertContains(respuesta, f'href="{url("producto", self.producto)}"')
