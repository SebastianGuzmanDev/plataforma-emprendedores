"""
HU-12 · Intercambiar mensajes con historial (Must) · RF-14, RNF-10 · CU-12 · S5 · C1.
"""
from django.test import Client, TestCase

from apps.contacto.models import Mensaje

from .utilidades import (
    CONTRASENA_VALIDA,
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    crear_conversacion,
    entrar,
    escenario,
    url_conversacion,
)


class HU12MensajesTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()
        self.conversacion = crear_conversacion(self.comprador, self.producto)
        self.url = url_conversacion(self.conversacion)

    def test_cp_12_1_enviar_un_mensaje_lo_registra_en_la_conversacion(self):
        """CP-12.1 · Esc. 1: al escribir y enviar, el mensaje queda registrado en la conversación."""
        entrar(self.client, CORREO_COMPRADOR)
        respuesta = self.client.post(self.url, {"contenido": "¿Tienes arepas de queso hoy?"}, follow=True)
        self.assertRedirects(respuesta, self.url)
        mensaje = Mensaje.objects.get()
        self.assertEqual((mensaje.autor, mensaje.contenido), (self.comprador, "¿Tienes arepas de queso hoy?"))
        self.assertContains(respuesta, "¿Tienes arepas de queso hoy?")

    def test_cp_12_2_la_respuesta_se_ve_al_actualizar_la_vista(self):
        """CP-12.2 · Esc. 2: la otra persona responde → la veo en la misma vista al actualizarla (asíncrono, D3)."""
        comprador = Client()
        emprendedor = Client()
        entrar(comprador, CORREO_COMPRADOR)
        entrar(emprendedor, CORREO_EMPRENDEDOR_A)
        comprador.post(self.url, {"contenido": "Hola, ¿a qué hora entregas?"})
        self.assertContains(emprendedor.get(self.url), "Hola, ¿a qué hora entregas?")
        emprendedor.post(self.url, {"contenido": "A las 12 en el bloque 3."})
        vista = comprador.get(self.url)
        self.assertContains(vista, "A las 12 en el bloque 3.")
        self.assertContains(vista, f'href="{self.url}"')  # botón «Actualizar»
        html = vista.content.decode()
        self.assertLess(html.index("Hola, ¿a qué hora entregas?"), html.index("A las 12 en el bloque 3."))

    def test_cp_12_3_el_historial_se_conserva_al_cerrar_y_volver_a_entrar(self):
        """CP-12.3 · Esc. 3 · RNF-10: tras cerrar sesión y volver a entrar, el historial sigue disponible."""
        entrar(self.client, CORREO_COMPRADOR)
        self.client.post(self.url, {"contenido": "Mensaje que debe persistir"})
        self.client.post("/cuentas/salir/")
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertTrue(self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA))
        self.assertContains(self.client.get(self.url), "Mensaje que debe persistir")

    def test_cp_12_4_un_mensaje_vacio_no_se_envia(self):
        """CP-12.4 · Esc. 4 · RN-16: un mensaje vacío no se envía."""
        entrar(self.client, CORREO_COMPRADOR)
        for vacio in ["", "    ", "\n\n"]:
            with self.subTest(texto=repr(vacio)):
                respuesta = self.client.post(self.url, {"contenido": vacio})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Escribe un mensaje antes de enviarlo")
        self.assertFalse(Mensaje.objects.exists())

    def test_un_mensaje_de_mas_de_1000_caracteres_no_se_envia(self):
        entrar(self.client, CORREO_COMPRADOR)
        respuesta = self.client.post(self.url, {"contenido": "a" * 1001})
        self.assertContains(respuesta, "1000 caracteres")
        self.assertFalse(Mensaje.objects.exists())

    def test_los_mensajes_se_muestran_escapados_y_con_saltos_de_linea(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.client.post(self.url, {"contenido": "<b>hola</b>\nsegunda línea"})
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "&lt;b&gt;hola&lt;/b&gt;<br>segunda línea")

    def test_cada_quien_identifica_sus_mensajes_y_los_de_la_otra_persona(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.client.post(self.url, {"contenido": "Mío"})
        html = self.client.get(self.url).content.decode()
        self.assertIn('class="mensaje mensaje--propio"', html)
        self.assertIn("Tú", html)
