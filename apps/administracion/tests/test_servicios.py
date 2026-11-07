"""
Pruebas de la capa de lógica de la Épica 7 (Módulo Administración).

- RN-19: solo el administrador desactiva productos o cuentas; una cuenta desactivada pierde el acceso.
- ES1: Disponible → Desactivado y Agotado → Desactivado también por el administrador.
- CC-11: cada desactivación queda registrada y, si es un producto, se notifica a su dueño en la plataforma.
"""
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.administracion import servicios
from apps.administracion.models import Desactivacion, MotivoDesactivacion
from apps.administracion.servicios import DesactivacionNoPermitida
from apps.perfil_productos.models import EstadoProducto, Producto

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_B,
    MOTIVO,
    crear_administrador,
    crear_usuario,
    emprendedor_con_producto,
)


class DesactivarProductoTests(TestCase):
    def setUp(self):
        self.admin = crear_administrador()
        self.emprendedor, self.producto = emprendedor_con_producto()

    def test_rn19_el_administrador_desactiva_el_producto_y_queda_registrado(self):
        servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO, detalle="Venta de licor en el campus")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, EstadoProducto.DESACTIVADO)
        registro = Desactivacion.objects.get()
        self.assertEqual(
            (registro.administrador, registro.producto, registro.cuenta, registro.motivo, registro.detalle),
            (self.admin, self.producto, None, MOTIVO, "Venta de licor en el campus"),
        )
        self.assertEqual(list(servicios.avisos_pendientes(self.emprendedor)), [registro])

    def test_es1_un_producto_agotado_tambien_se_desactiva(self):
        self.producto.estado = EstadoProducto.AGOTADO
        self.producto.save()
        servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO)
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).estado, EstadoProducto.DESACTIVADO)

    def test_rn19_solo_el_administrador_puede_desactivar_un_producto(self):
        comprador = crear_usuario(correo=CORREO_COMPRADOR)
        for actor in [comprador, self.emprendedor]:
            with self.subTest(actor=actor.rol), self.assertRaises(PermissionDenied):
                servicios.desactivar_producto(actor, self.producto, motivo=MOTIVO)
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).estado, EstadoProducto.DISPONIBLE)
        self.assertFalse(Desactivacion.objects.exists())

    def test_un_producto_ya_desactivado_no_se_vuelve_a_desactivar(self):
        self.producto.estado = EstadoProducto.DESACTIVADO
        self.producto.save()
        with self.assertRaises(DesactivacionNoPermitida):
            servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO)
        self.assertFalse(Desactivacion.objects.exists())

    def test_al_ver_los_avisos_dejan_de_estar_pendientes_pero_se_conservan(self):
        servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO)
        servicios.marcar_avisos_vistos(self.emprendedor)
        self.assertEqual(list(servicios.avisos_pendientes(self.emprendedor)), [])
        self.assertEqual(servicios.avisos_de(self.emprendedor).count(), 1)

    def test_los_avisos_son_solo_del_dueno(self):
        otro, _ = emprendedor_con_producto(CORREO_EMPRENDEDOR_B, "Pulsera")
        servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO)
        self.assertEqual(list(servicios.avisos_pendientes(otro)), [])


class DesactivarCuentaTests(TestCase):
    def setUp(self):
        self.admin = crear_administrador()
        self.emprendedor, self.producto = emprendedor_con_producto()

    def test_rn19_la_cuenta_queda_inactiva_y_registrada(self):
        servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MotivoDesactivacion.SUPLANTACION)
        self.emprendedor.refresh_from_db()
        self.assertFalse(self.emprendedor.activo)
        registro = Desactivacion.objects.get()
        self.assertEqual((registro.cuenta, registro.producto, registro.reactivada_en), (self.emprendedor, None, None))

    def test_rn19_solo_el_administrador_puede_desactivar_una_cuenta(self):
        comprador = crear_usuario(correo=CORREO_COMPRADOR)
        with self.assertRaises(PermissionDenied):
            servicios.desactivar_cuenta(comprador, self.emprendedor, motivo=MOTIVO)
        self.emprendedor.refresh_from_db()
        self.assertTrue(self.emprendedor.activo)

    def test_no_se_desactiva_la_propia_cuenta_ni_la_de_otro_administrador(self):
        otro_admin = crear_administrador("otra.admin@amigo.edu.co")
        for cuenta in [self.admin, otro_admin]:
            with self.subTest(cuenta=cuenta.correo_institucional), self.assertRaises(DesactivacionNoPermitida):
                servicios.desactivar_cuenta(self.admin, cuenta, motivo=MOTIVO)
        self.assertTrue(all(u.activo for u in [self.admin, otro_admin]))
        self.assertFalse(Desactivacion.objects.exists())

    def test_una_cuenta_ya_desactivada_no_se_vuelve_a_desactivar(self):
        servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MOTIVO)
        with self.assertRaises(DesactivacionNoPermitida):
            servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MOTIVO)
        self.assertEqual(Desactivacion.objects.count(), 1)

    def test_los_productos_de_una_cuenta_desactivada_salen_del_catalogo_sin_cambiar_su_estado(self):
        servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MOTIVO)
        self.assertFalse(Producto.objects.visibles_en_catalogo().exists())
        producto = Producto.objects.get(pk=self.producto.pk)
        self.assertFalse(producto.es_visible_en_catalogo)
        self.assertEqual(producto.estado, EstadoProducto.DISPONIBLE)

    def test_reactivar_devuelve_el_acceso_y_los_productos(self):
        servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MOTIVO)
        servicios.reactivar_cuenta(self.admin, self.emprendedor)
        self.emprendedor.refresh_from_db()
        self.assertTrue(self.emprendedor.activo)
        self.assertIsNotNone(Desactivacion.objects.get().reactivada_en)
        self.assertTrue(Producto.objects.visibles_en_catalogo().filter(pk=self.producto.pk).exists())

    def test_reactivar_exige_administrador_y_una_cuenta_desactivada(self):
        with self.assertRaises(DesactivacionNoPermitida):
            servicios.reactivar_cuenta(self.admin, self.emprendedor)
        servicios.desactivar_cuenta(self.admin, self.emprendedor, motivo=MOTIVO)
        with self.assertRaises(PermissionDenied):
            servicios.reactivar_cuenta(crear_usuario(correo=CORREO_COMPRADOR), self.emprendedor)
        self.emprendedor.refresh_from_db()
        self.assertFalse(self.emprendedor.activo)
