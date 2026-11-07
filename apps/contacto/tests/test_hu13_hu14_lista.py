"""
HU-13 · Ver mis conversaciones (Must) · RF-15 · CU-13 · RN-17.
HU-14 · Ver cuántos mensajes tengo sin leer (Should) · RF-16 · CU-14.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.contacto.models import Mensaje

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    URL_MENSAJES,
    crear_conversacion,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
    escenario,
    url_conversacion,
)


class HU13ListaTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()
        otro = crear_emprendedor(CORREO_EMPRENDEDOR_B)
        self.pulsera = crear_producto(crear_perfil(otro, categoria="Artesanías", nombre="Tejidos Juana"), "Pulsera")

    def test_cp_13_1_la_lista_se_ordena_por_el_mensaje_mas_reciente(self):
        """CP-13.1 · Esc. 1 · RN-17: varias conversaciones → ordenadas por el mensaje más reciente."""
        # La conversación creada primero es la del mensaje más reciente: el orden no depende de la creación.
        crear_conversacion(self.comprador, self.pulsera, [(self.comprador, "Mensaje reciente")])
        antigua = crear_conversacion(self.comprador, self.producto, [(self.comprador, "Mensaje antiguo")])
        Mensaje.objects.filter(conversacion=antigua).update(fecha_envio=timezone.now() - timedelta(days=2))
        entrar(self.client, CORREO_COMPRADOR)
        html = self.client.get(URL_MENSAJES).content.decode()
        self.assertLess(html.index("Tejidos Juana"), html.index("Arepas Doña Rosa"))
        self.assertIn("Mensaje reciente", html)
        self.assertIn(f'href="{url_conversacion(antigua)}"', html)

    def test_cp_13_2_sin_conversaciones_indica_que_no_hay(self):
        """CP-13.2 · Esc. 2: sin conversaciones → mensaje de que no hay conversaciones."""
        entrar(self.client, CORREO_COMPRADOR)
        respuesta = self.client.get(URL_MENSAJES)
        self.assertContains(respuesta, "Todavía no tienes conversaciones")
        self.assertContains(respuesta, 'href="/catalogo/"')

    def test_el_emprendedor_ve_al_comprador_sin_su_correo(self):
        """RNF-06: el emprendedor identifica la conversación sin conocer el correo del comprador."""
        conversacion = crear_conversacion(self.comprador, self.producto, [(self.comprador, "Hola")])
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        for url in [URL_MENSAJES, url_conversacion(conversacion)]:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertContains(respuesta, f"Comprador {conversacion.alias_comprador}")
                self.assertNotContains(respuesta, CORREO_COMPRADOR)

    def test_al_emprendedor_no_le_aparecen_conversaciones_sin_mensajes(self):
        """Si el comprador abre la conversación pero no escribe, el emprendedor no recibe una conversación vacía."""
        crear_conversacion(self.comprador, self.producto)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.assertContains(self.client.get(URL_MENSAJES), "Todavía no tienes conversaciones")
        self.client.logout()
        entrar(self.client, CORREO_COMPRADOR)
        self.assertContains(self.client.get(URL_MENSAJES), "Arepas Doña Rosa")

    def test_la_lista_exige_sesion(self):
        respuesta = self.client.get(URL_MENSAJES)
        self.assertRedirects(respuesta, f"/cuentas/ingresar/?next={URL_MENSAJES}")


class HU14SinLeerTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()
        self.conversacion = crear_conversacion(
            self.comprador,
            self.producto,
            [(self.comprador, "Hola"), (self.comprador, "¿Tienes arepas?"), (self.comprador, "¿A qué hora?")],
        )

    def test_cp_14_1_al_entrar_veo_un_indicador_con_la_cantidad_sin_leer(self):
        """CP-14.1 · Esc. 1: con mensajes sin leer, al entrar veo un indicador con la cantidad (p. ej. «3»)."""
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.context["mensajes_sin_leer"], 3)
        self.assertContains(respuesta, '<span class="contador" aria-hidden="true">3</span>')
        self.assertContains(respuesta, "3 mensajes sin leer")
        lista = self.client.get(URL_MENSAJES)
        self.assertContains(lista, "3 sin leer")

    def test_cp_14_2_al_abrir_y_leer_la_conversacion_el_indicador_baja_a_0(self):
        """CP-14.2 · Esc. 2: al abrir la conversación y leer los mensajes, el indicador baja a 0."""
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.client.get(url_conversacion(self.conversacion))
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.context["mensajes_sin_leer"], 0)
        self.assertNotContains(respuesta, 'class="contador"')

    def test_los_mensajes_propios_no_cuentan_como_sin_leer(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.assertEqual(self.client.get("/").context["mensajes_sin_leer"], 0)

    def test_sin_sesion_no_hay_indicador_ni_consulta(self):
        with self.assertNumQueries(0):
            respuesta = self.client.get("/")
        self.assertEqual(respuesta.context["mensajes_sin_leer"], 0)
