"""
HU-09 · Ver el detalle de un producto y su emprendimiento (Must) · RF-12 · CU-09 · A3.
"""
from django.test import TestCase
from django.urls import reverse

from apps.cuentas.tests.utilidades import crear_usuario

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    EstadoProducto,
    crear_producto,
    emprendimientos_de_prueba,
    entrar,
    url_detalle,
)


class HU09DetalleTests(TestCase):
    def setUp(self):
        self.comida, self.artesanias = emprendimientos_de_prueba()
        self.producto = crear_producto(self.comida, "Arepa de queso", 5000)

    def test_cp_09_1_detalle_completo_del_producto_y_su_emprendimiento(self):
        """CP-09.1 · Esc. 1: al abrir un producto veo su información, la del emprendimiento y «Contactar»."""
        respuesta = self.client.get(url_detalle(self.producto))
        self.assertEqual(respuesta.status_code, 200)
        for texto in [
            "Arepa de queso",
            "$ 5.000",
            "Disponible",
            "Arepas Doña Rosa",
            "Comida",
            "Arepas rellenas hechas en casa.",
            "Lunes a viernes, 10:00 a 14:00",
            "Bloque 3, frente a la cafetería",
            "Contactar",
        ]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)
        self.assertContains(respuesta, f'src="{self.producto.foto.url}" alt="Arepa de queso"')

    def test_cp_09_1_el_detalle_no_expone_el_correo_del_emprendedor(self):
        """RNF-06: el catálogo público no muestra datos personales del emprendedor."""
        self.assertNotContains(self.client.get(url_detalle(self.producto)), CORREO_EMPRENDEDOR_A)

    def test_cp_09_2_producto_desactivado_por_enlace_directo_avisa_que_no_esta_disponible(self):
        """CP-09.2 · Esc. 2: un producto desactivado abierto por enlace directo muestra un aviso."""
        self.producto.estado = EstadoProducto.DESACTIVADO
        self.producto.save()
        respuesta = self.client.get(url_detalle(self.producto))
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "Este producto ya no está disponible", status_code=404)
        self.assertNotContains(respuesta, "$ 5.000", status_code=404)
        self.assertContains(respuesta, f'href="{reverse("catalogo:listado")}"', status_code=404)

    def test_un_producto_agotado_se_ve_con_su_etiqueta(self):
        self.producto.estado = EstadoProducto.AGOTADO
        self.producto.save()
        respuesta = self.client.get(url_detalle(self.producto))
        self.assertContains(respuesta, "Agotado")
        self.assertContains(respuesta, "Contactar")

    def test_un_codigo_inexistente_responde_404(self):
        self.producto.delete()
        self.assertEqual(self.client.get(url_detalle(self.producto)).status_code, 404)


class HU09BotonContactarTests(TestCase):
    """A3: el botón «Contactar» y su comportamiento según la sesión (HU-11 lo completa en E4)."""

    def setUp(self):
        self.comida, _ = emprendimientos_de_prueba()
        self.producto = crear_producto(self.comida, "Arepa de queso")
        self.url_contactar = reverse("catalogo:contactar", kwargs={"codigo": self.producto.codigo})

    def test_sin_sesion_contactar_pide_iniciar_sesion_y_regresa_al_producto(self):
        """A3: sin sesión → pedir iniciar sesión; luego continúa en el producto."""
        respuesta = self.client.get(url_detalle(self.producto))
        destino = f'{reverse("cuentas:ingresar")}?next={url_detalle(self.producto)}'
        self.assertContains(respuesta, f'href="{destino}"')

    def test_con_sesion_contactar_lleva_al_contacto_con_el_emprendedor(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        self.assertContains(self.client.get(url_detalle(self.producto)), f'href="{self.url_contactar}"')
        contacto = self.client.get(self.url_contactar)
        self.assertEqual(contacto.status_code, 200)
        self.assertContains(contacto, "Arepas Doña Rosa")

    def test_rn18_en_un_producto_propio_no_aparece_contactar(self):
        """RN-18 · A3: si el producto es del propio usuario no se muestra el botón."""
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        respuesta = self.client.get(url_detalle(self.producto))
        self.assertNotContains(respuesta, self.url_contactar)
        self.assertNotContains(respuesta, ">Contactar<")
        self.assertContains(respuesta, "Este producto es tuyo")
        self.assertContains(respuesta, reverse("emprendimiento:editar", kwargs={"codigo": self.producto.codigo}))
        # Tampoco puede contactarse a sí mismo escribiendo la ruta.
        self.assertRedirects(self.client.get(self.url_contactar), url_detalle(self.producto))

    def test_otro_emprendedor_si_ve_contactar(self):
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        self.assertContains(self.client.get(url_detalle(self.producto)), f'href="{self.url_contactar}"')

    def test_la_ruta_de_contacto_exige_sesion(self):
        respuesta = self.client.get(self.url_contactar)
        self.assertRedirects(respuesta, f'{reverse("cuentas:ingresar")}?next={self.url_contactar}')
