"""
HU-03 · Recuperar mi contraseña (Should) · RF-04 · CU-03.
"""
import re
from datetime import timedelta
from unittest import mock

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, crear_usuario

URL_RECUPERAR = reverse("cuentas:recuperar")
URL_ENVIADO = reverse("cuentas:recuperar_enviado")
NUEVA_CONTRASENA = "Nueva-Clave-Amigo-26"
MENSAJE_NEUTRO = "Si el correo está registrado, te enviamos un enlace"


def extraer_enlace(cuerpo):
    coincidencia = re.search(r"https?://[^/\s]+(/cuentas/restablecer/[^\s]+/)", cuerpo)
    assert coincidencia, f"No se encontró el enlace de recuperación en:\n{cuerpo}"
    return coincidencia.group(1)


class HU03RecuperacionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()

    def test_cp_03_1_correo_registrado_recibe_enlace_para_restablecer(self):
        """CP-03.1 · Esc. 1: correo registrado → recibe un enlace para restablecer la contraseña."""
        respuesta = self.client.post(URL_RECUPERAR, {"email": CORREO_COMPRADOR}, follow=True)
        self.assertRedirects(respuesta, URL_ENVIADO)
        self.assertContains(respuesta, MENSAJE_NEUTRO)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, [CORREO_COMPRADOR])
        self.assertIn("Restablece tu contraseña", correo.subject)
        enlace = extraer_enlace(correo.body)

        # El enlace permite definir una contraseña nueva...
        formulario = self.client.get(enlace, follow=True)
        self.assertContains(formulario, "Nueva contraseña")
        url_formulario = formulario.redirect_chain[-1][0] if formulario.redirect_chain else enlace
        final = self.client.post(
            url_formulario,
            {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
            follow=True,
        )
        self.assertRedirects(final, reverse("cuentas:restablecer_completo"))

        # ...con la que se vuelve a entrar; la anterior deja de servir.
        self.assertTrue(self.client.login(correo_institucional=CORREO_COMPRADOR, password=NUEVA_CONTRASENA))
        self.client.logout()
        self.assertFalse(self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA))

        # El enlace es de un solo uso.
        reutilizado = self.client.get(enlace, follow=True)
        self.assertContains(reutilizado, "El enlace no es válido o ya venció")

    def test_cp_03_2_correo_desconocido_muestra_mensaje_neutro_sin_enviar_nada(self):
        """CP-03.2 · Esc. 2: correo no registrado → mensaje neutro que no revela si la cuenta existe."""
        registrado = self.client.post(URL_RECUPERAR, {"email": CORREO_COMPRADOR}, follow=True)
        mail.outbox.clear()
        desconocido = self.client.post(URL_RECUPERAR, {"email": "nadie@amigo.edu.co"}, follow=True)

        self.assertRedirects(desconocido, URL_ENVIADO)
        self.assertContains(desconocido, MENSAJE_NEUTRO)
        self.assertEqual(len(mail.outbox), 0)
        # Misma redirección y mismo contenido: no se puede deducir si la cuenta existe.
        self.assertEqual(registrado.redirect_chain, desconocido.redirect_chain)
        self.assertEqual(registrado.content, desconocido.content)

    def test_una_cuenta_desactivada_no_recibe_enlace(self):
        self.usuario.activo = False
        self.usuario.save()
        respuesta = self.client.post(URL_RECUPERAR, {"email": CORREO_COMPRADOR}, follow=True)
        self.assertContains(respuesta, MENSAJE_NEUTRO)
        self.assertEqual(len(mail.outbox), 0)

    def test_el_enlace_vence_una_hora_despues(self):
        self.client.post(URL_RECUPERAR, {"email": CORREO_COMPRADOR})
        enlace = extraer_enlace(mail.outbox[0].body)
        ahora = PasswordResetTokenGenerator()._now()
        with mock.patch.object(
            PasswordResetTokenGenerator, "_now", return_value=ahora + timedelta(hours=1, minutes=1)
        ):
            respuesta = self.client.get(enlace, follow=True)
        self.assertContains(respuesta, "El enlace no es válido o ya venció")

    def test_el_correo_no_distingue_mayusculas(self):
        self.client.post(URL_RECUPERAR, {"email": CORREO_COMPRADOR.upper()})
        self.assertEqual(len(mail.outbox), 1)

    def test_la_pagina_de_ingreso_enlaza_la_recuperacion(self):
        respuesta = self.client.get(reverse("cuentas:ingresar"))
        self.assertContains(respuesta, f'href="{URL_RECUPERAR}"')
