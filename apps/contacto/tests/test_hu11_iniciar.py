"""
HU-11 · Iniciar una conversación con un emprendedor (Must) · RF-13 · CU-11 · S5 · A3.
"""
from django.test import TestCase
from django.urls import reverse

from apps.contacto.models import Conversacion
from apps.perfil_productos.models import EstadoProducto

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    crear_emprendedor,
    entrar,
    escenario,
    url_conversacion,
    url_iniciar,
)


def url_detalle(producto):
    return reverse("catalogo:detalle", kwargs={"codigo": producto.codigo})


class HU11IniciarTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()

    def test_cp_11_1_contactar_con_sesion_abre_una_conversacion_nueva(self):
        """CP-11.1 · Esc. 1: comprador con sesión presiona «Contactar» → se abre una conversación nueva."""
        entrar(self.client, CORREO_COMPRADOR)
        detalle = self.client.get(url_detalle(self.producto))
        self.assertContains(detalle, f'action="{url_iniciar(self.producto)}"')
        respuesta = self.client.post(url_iniciar(self.producto), follow=True)
        conversacion = Conversacion.objects.get()
        self.assertRedirects(respuesta, url_conversacion(conversacion))
        self.assertEqual(
            (conversacion.comprador, conversacion.emprendedor, conversacion.producto),
            (self.comprador, self.emprendedor, self.producto),
        )
        self.assertContains(respuesta, "Arepas Doña Rosa")
        self.assertContains(respuesta, "Arepa de queso")
        self.assertContains(respuesta, "Escribe tu primer mensaje")

    def test_cp_11_1_volver_a_contactar_reabre_la_misma_conversacion(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.client.post(url_iniciar(self.producto))
        self.client.post(url_iniciar(self.producto))
        self.assertEqual(Conversacion.objects.count(), 1)

    def test_cp_11_2_contactar_sin_sesion_pide_iniciar_sesion(self):
        """CP-11.2 · Esc. 2: sin sesión, «Contactar» pide iniciar sesión."""
        detalle = self.client.get(url_detalle(self.producto))
        self.assertContains(detalle, f'href="{reverse("cuentas:ingresar")}?next={url_detalle(self.producto)}"')
        directo = self.client.post(url_iniciar(self.producto))
        self.assertEqual(directo.status_code, 302)
        self.assertTrue(directo["Location"].startswith(reverse("cuentas:ingresar")))
        self.assertFalse(Conversacion.objects.exists())

    def test_cp_11_3_en_el_producto_propio_no_aparece_contactar(self):
        """CP-11.3 · Esc. 3 · RN-18: si el producto es mío, no aparece el botón de contacto."""
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        detalle = self.client.get(url_detalle(self.producto))
        self.assertNotContains(detalle, url_iniciar(self.producto))
        self.assertNotContains(detalle, ">Contactar<")
        forzado = self.client.post(url_iniciar(self.producto), follow=True)
        self.assertRedirects(forzado, url_detalle(self.producto))
        self.assertContains(forzado, "No puedes contactarte a ti mismo")
        self.assertFalse(Conversacion.objects.exists())

    def test_otro_emprendedor_tambien_puede_contactar(self):
        """Decisión de la Épica 3 (punto 1): cualquier cuenta que no sea la dueña puede contactar."""
        crear_emprendedor(CORREO_EMPRENDEDOR_B)
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        self.client.post(url_iniciar(self.producto))
        self.assertEqual(Conversacion.objects.get().comprador.correo_institucional, CORREO_EMPRENDEDOR_B)

    def test_iniciar_solo_acepta_post_y_por_get_vuelve_al_producto(self):
        """Tras iniciar sesión el navegador vuelve por GET: no se crea nada y regresa al producto (A3)."""
        entrar(self.client, CORREO_COMPRADOR)
        self.assertRedirects(self.client.get(url_iniciar(self.producto)), url_detalle(self.producto))
        self.assertFalse(Conversacion.objects.exists())

    def test_no_se_contacta_por_un_producto_desactivado(self):
        self.producto.estado = EstadoProducto.DESACTIVADO
        self.producto.save()
        entrar(self.client, CORREO_COMPRADOR)
        self.assertEqual(self.client.post(url_iniciar(self.producto)).status_code, 404)
        self.assertFalse(Conversacion.objects.exists())

    def test_la_pagina_provisional_de_la_epica_3_ya_no_existe(self):
        from django.urls import NoReverseMatch

        with self.assertRaises(NoReverseMatch):
            reverse("catalogo:contactar", kwargs={"codigo": self.producto.codigo})
