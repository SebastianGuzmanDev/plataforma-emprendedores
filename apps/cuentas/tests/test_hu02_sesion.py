"""
HU-02 · Iniciar y cerrar sesión (Must) · RF-02 · CU-02 (diagrama S2).
"""
from django.contrib.auth import get_user
from django.test import TestCase
from django.urls import reverse

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, crear_usuario

URL_INGRESAR = reverse("cuentas:ingresar")
URL_SALIR = reverse("cuentas:salir")
URL_MI_CUENTA = reverse("cuentas:mi_cuenta")


def credenciales(correo=CORREO_COMPRADOR, contrasena=CONTRASENA_VALIDA):
    return {"username": correo, "password": contrasena}


class HU02InicioSesionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()

    def test_cp_02_1_acceso_correcto_entra_a_la_cuenta(self):
        """CP-02.1 · Esc. 1: correo y contraseña correctos → accedo a mi cuenta."""
        respuesta = self.client.post(URL_INGRESAR, credenciales(), follow=True)
        self.assertRedirects(respuesta, URL_MI_CUENTA)
        self.assertEqual(get_user(respuesta.wsgi_request), self.usuario)
        self.assertContains(respuesta, CORREO_COMPRADOR)

    def test_cp_02_1_el_correo_no_distingue_mayusculas(self):
        respuesta = self.client.post(URL_INGRESAR, credenciales(correo=" ANA.PEREZ@amigo.edu.co "))
        self.assertRedirects(respuesta, URL_MI_CUENTA)

    def test_cp_02_2_contrasena_incorrecta_muestra_error_y_no_da_acceso(self):
        """CP-02.2 · Esc. 2: contraseña incorrecta → mensaje de error y sin acceso."""
        respuesta = self.client.post(URL_INGRESAR, credenciales(contrasena="Incorrecta-2026"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Correo o contraseña incorrectos")
        self.assertFalse(get_user(respuesta.wsgi_request).is_authenticated)

    def test_cp_02_2_correo_inexistente_muestra_el_mismo_error(self):
        """El mensaje no revela si el correo tiene cuenta."""
        respuesta = self.client.post(URL_INGRESAR, credenciales(correo="nadie@amigo.edu.co"))
        self.assertContains(respuesta, "Correo o contraseña incorrectos")
        self.assertFalse(get_user(respuesta.wsgi_request).is_authenticated)

    def test_el_inicio_de_sesion_renueva_el_identificador_de_sesion(self):
        """Evita la fijación de sesión: la cookie anterior deja de servir."""
        self.client.get(URL_INGRESAR)
        self.client.session.save()
        clave_anterior = self.client.session.session_key
        self.client.post(URL_INGRESAR, credenciales())
        self.assertNotEqual(self.client.session.session_key, clave_anterior)

    def test_respeta_next_interno_e_ignora_destinos_externos(self):
        interno = self.client.post(f"{URL_INGRESAR}?next={URL_MI_CUENTA}", credenciales())
        self.assertRedirects(interno, URL_MI_CUENTA)
        self.client.logout()
        externo = self.client.post(f"{URL_INGRESAR}?next=https://sitio-malicioso.com/", credenciales())
        self.assertRedirects(externo, URL_MI_CUENTA)


class HU02CierreSesionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)

    def test_cp_02_3_cerrar_sesion_termina_la_sesion_y_bloquea_paginas_privadas(self):
        """CP-02.3 · Esc. 3: al cerrar sesión, las páginas privadas dejan de estar disponibles."""
        self.assertEqual(self.client.get(URL_MI_CUENTA).status_code, 200)
        respuesta = self.client.post(URL_SALIR, follow=True)
        self.assertRedirects(respuesta, reverse("inicio"))
        self.assertContains(respuesta, "Cerraste sesión")
        self.assertFalse(get_user(respuesta.wsgi_request).is_authenticated)
        privada = self.client.get(URL_MI_CUENTA)
        self.assertRedirects(privada, f"{URL_INGRESAR}?next={URL_MI_CUENTA}")

    def test_cerrar_sesion_solo_se_acepta_por_post(self):
        """Un enlace o imagen externa no puede cerrar la sesión (GET no permitido)."""
        self.assertEqual(self.client.get(URL_SALIR).status_code, 405)
        self.assertEqual(self.client.get(URL_MI_CUENTA).status_code, 200)


class HU02CuentaDesactivadaTests(TestCase):
    """CU-02 flujo 2b: una cuenta desactivada por el administrador pierde el acceso (RN-19)."""

    def test_una_cuenta_desactivada_no_puede_iniciar_sesion(self):
        crear_usuario(activo=False)
        respuesta = self.client.post(URL_INGRESAR, credenciales())
        self.assertContains(respuesta, "Correo o contraseña incorrectos")
        self.assertFalse(get_user(respuesta.wsgi_request).is_authenticated)

    def test_desactivar_la_cuenta_corta_la_sesion_activa(self):
        usuario = crear_usuario()
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)
        usuario.activo = False
        usuario.save()
        respuesta = self.client.get(URL_MI_CUENTA)
        self.assertRedirects(respuesta, f"{URL_INGRESAR}?next={URL_MI_CUENTA}")
