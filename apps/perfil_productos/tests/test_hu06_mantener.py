"""
HU-06 · Editar, desactivar y marcar agotado un producto (Must) · RF-07, RF-08, RNF-05
· CU-06 · diagrama ES1.
"""
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.perfil_productos.models import EstadoProducto, Producto

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    MediaTemporalMixin,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
    imagen,
)

URL_VISTA_PREVIA = reverse("emprendimiento:vista_previa")
URL_PANEL = reverse("emprendimiento:panel")


def url(nombre, producto):
    return reverse(f"emprendimiento:{nombre}", kwargs={"codigo": producto.codigo})


class HU06MantenerProductoTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.producto = crear_producto(crear_perfil(crear_emprendedor()))
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_06_1_cambio_de_precio_se_refleja_en_el_catalogo(self):
        """CP-06.1 · Esc. 1: al cambiar el precio y guardar, el catálogo muestra el precio nuevo."""
        formulario = self.client.get(url("editar", self.producto))
        self.assertContains(formulario, 'value="5000"')
        respuesta = self.client.post(
            url("editar", self.producto), {"nombre": "Arepa de queso", "precio_referencia": "7.500"}, follow=True
        )
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "Guardamos los cambios de «Arepa de queso»")
        self.assertEqual(Producto.objects.visibles_en_catalogo().get().precio_referencia, 7500)
        vista = self.client.get(URL_VISTA_PREVIA)
        self.assertContains(vista, "$ 7.500")
        self.assertNotContains(vista, "$ 5.000")

    def test_cp_06_1_editar_sin_foto_conserva_la_actual(self):
        foto_anterior = self.producto.foto.name
        self.client.post(url("editar", self.producto), {"nombre": "Arepa doble", "precio_referencia": "6000"})
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Arepa doble")
        self.assertEqual(self.producto.foto.name, foto_anterior)

    def test_cp_06_1_cambiar_la_foto_borra_la_anterior_del_almacenamiento(self):
        self.client.post(url("editar", self.producto), {"nombre": "A", "precio_referencia": "1", "foto": imagen()})
        self.producto.refresh_from_db()
        primera = Path(settings.MEDIA_ROOT) / self.producto.foto.name
        self.assertTrue(primera.is_file())
        self.client.post(url("editar", self.producto), {"nombre": "A", "precio_referencia": "1", "foto": imagen()})
        self.producto.refresh_from_db()
        self.assertFalse(primera.exists())
        self.assertTrue((Path(settings.MEDIA_ROOT) / self.producto.foto.name).is_file())

    def test_la_edicion_valida_el_precio_igual_que_la_publicacion(self):
        respuesta = self.client.post(url("editar", self.producto), {"nombre": "Arepa", "precio_referencia": "-5"})
        self.assertContains(respuesta, "Escribe el precio solo con números")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.precio_referencia, 5000)

    def test_cp_06_2_marcar_como_agotado_muestra_la_etiqueta_agotado(self):
        """CP-06.2 · Esc. 2: al marcarlo como agotado, el catálogo lo muestra con la etiqueta «Agotado»."""
        respuesta = self.client.post(url("agotado", self.producto), follow=True)
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "«Arepa de queso» quedó marcado como agotado")
        visible = Producto.objects.visibles_en_catalogo().get()
        self.assertEqual(visible.estado, EstadoProducto.AGOTADO)
        vista = self.client.get(URL_VISTA_PREVIA)
        self.assertContains(vista, "Arepa de queso")
        self.assertContains(vista, "Agotado")

    def test_cp_06_3_desactivar_lo_retira_del_catalogo(self):
        """CP-06.3 · Esc. 3: al desactivarlo, deja de aparecer en el catálogo."""
        confirmacion = self.client.get(url("desactivar", self.producto))
        self.assertContains(confirmacion, "¿Desactivar «Arepa de queso»?")
        self.assertContains(confirmacion, "no se puede deshacer")
        respuesta = self.client.post(url("desactivar", self.producto), follow=True)
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "«Arepa de queso» quedó desactivado y ya no aparece en el catálogo")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, EstadoProducto.DESACTIVADO)
        self.assertFalse(Producto.objects.visibles_en_catalogo().exists())
        self.assertNotContains(self.client.get(URL_VISTA_PREVIA), "Arepa de queso")

    def test_un_producto_agotado_tambien_se_puede_desactivar(self):
        self.client.post(url("agotado", self.producto))
        self.client.post(url("desactivar", self.producto))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, EstadoProducto.DESACTIVADO)

    def test_cp_06_6_un_producto_agotado_vuelve_a_estar_disponible(self):
        """CP-06.6 · CC-02: Agotado → Disponible; el catálogo vuelve a mostrar «Disponible»."""
        self.client.post(url("agotado", self.producto))
        respuesta = self.client.post(url("disponible", self.producto), follow=True)
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "«Arepa de queso» volvió a estar disponible")
        self.assertEqual(Producto.objects.visibles_en_catalogo().get().estado, EstadoProducto.DISPONIBLE)
        vista = self.client.get(URL_VISTA_PREVIA)
        self.assertContains(vista, "Disponible")
        self.assertNotContains(vista, ">Agotado<")

    def test_cp_06_7_un_producto_agotado_se_edita_y_sigue_agotado(self):
        """CP-06.7 · CC-02: editar no cambia el estado."""
        self.client.post(url("agotado", self.producto))
        self.client.post(url("editar", self.producto), {"nombre": "Arepa de queso", "precio_referencia": "6000"})
        self.producto.refresh_from_db()
        self.assertEqual((self.producto.precio_referencia, self.producto.estado), (6000, EstadoProducto.AGOTADO))

    def test_es1_transiciones_no_permitidas_se_informan_sin_cambiar_el_estado(self):
        """ES1 + CC-02: un producto desactivado no se edita, no se agota y no se reactiva."""
        self.client.post(url("desactivar", self.producto))
        for accion, datos, mensaje in [
            ("editar", {"nombre": "Otro", "precio_referencia": "1"}, "no se puede editar"),
            ("agotado", {}, "No se puede marcar como agotado un producto desactivado"),
            ("disponible", {}, "no se puede reactivar"),
        ]:
            with self.subTest(accion=accion):
                self.assertContains(self.client.post(url(accion, self.producto), datos, follow=True), mensaje)
        disponible = self.client.post(url("disponible", crear_producto(self.producto.emprendimiento)), follow=True)
        self.assertContains(disponible, "ya está disponible")
        self.producto.refresh_from_db()
        self.assertEqual((self.producto.nombre, self.producto.estado), ("Arepa de queso", EstadoProducto.DESACTIVADO))

    def test_los_cambios_de_estado_solo_se_aceptan_por_post(self):
        self.assertEqual(self.client.get(url("agotado", self.producto)).status_code, 405)
        self.assertEqual(self.client.get(url("disponible", self.producto)).status_code, 405)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.estado, EstadoProducto.DISPONIBLE)

    def test_un_codigo_inexistente_responde_404(self):
        self.producto.delete()
        self.assertEqual(self.client.get(url("editar", self.producto)).status_code, 404)

    def test_el_panel_muestra_las_acciones_que_permite_cada_estado(self):
        agotado = crear_producto(self.producto.emprendimiento, nombre="Empanada", estado=EstadoProducto.AGOTADO)
        desactivado = crear_producto(self.producto.emprendimiento, nombre="Jugo", estado=EstadoProducto.DESACTIVADO)
        html = self.client.get(URL_PANEL).content.decode()
        self.assertIn(url("editar", self.producto), html)
        self.assertIn(url("agotado", self.producto), html)
        self.assertNotIn(url("disponible", self.producto), html)
        self.assertIn(url("editar", agotado), html)
        self.assertIn(url("disponible", agotado), html)
        self.assertNotIn(url("agotado", agotado), html)
        self.assertIn(url("desactivar", agotado), html)
        for accion in ("editar", "agotado", "disponible", "desactivar"):
            self.assertNotIn(url(accion, desactivado), html)


class HU06ProductoAjenoTests(MediaTemporalMixin, TestCase):
    """CP-06.4 · Esc. 4 · RN-08 · RNF-05: solo el dueño puede editar, agotar o desactivar."""

    def setUp(self):
        self.producto_de_a = crear_producto(crear_perfil(crear_emprendedor(CORREO_EMPRENDEDOR_A)))
        crear_perfil(crear_emprendedor(CORREO_EMPRENDEDOR_B), categoria="Artesanías")
        entrar(self.client, CORREO_EMPRENDEDOR_B)

    def test_cp_06_4_otro_emprendedor_recibe_acceso_denegado_y_el_producto_no_cambia(self):
        for nombre, metodo, datos in [
            ("editar", "get", None),
            ("editar", "post", {"nombre": "Hackeado", "precio_referencia": "1"}),
            ("agotado", "post", None),
            ("disponible", "post", None),
            ("desactivar", "get", None),
            ("desactivar", "post", None),
        ]:
            with self.subTest(accion=nombre, metodo=metodo):
                respuesta = getattr(self.client, metodo)(url(nombre, self.producto_de_a), datos or {})
                self.assertEqual(respuesta.status_code, 403)
                self.assertContains(respuesta, "No tienes permiso", status_code=403)
        self.producto_de_a.refresh_from_db()
        self.assertEqual(
            (self.producto_de_a.nombre, self.producto_de_a.precio_referencia, self.producto_de_a.estado),
            ("Arepa de queso", 5000, EstadoProducto.DISPONIBLE),
        )

    def test_el_panel_y_la_vista_previa_solo_muestran_productos_propios(self):
        self.assertNotContains(self.client.get(URL_PANEL), "Arepa de queso")
        self.assertNotContains(self.client.get(URL_VISTA_PREVIA), "Arepa de queso")
