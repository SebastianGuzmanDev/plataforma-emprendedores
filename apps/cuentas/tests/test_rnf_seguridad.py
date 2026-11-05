"""
RNF-04 · Seguridad (Must): conexión por HTTPS y contraseñas almacenadas cifradas.
"""
import importlib
import os
from unittest import mock

from django.conf import settings
from django.contrib.auth.hashers import check_password, identify_hasher
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.cuentas.models import Usuario

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, datos_registro

ENTORNO_PRODUCCION = {
    "DJANGO_SECRET_KEY": "k" * 20 + "Z9-x_q!" + "w" * 30 + "#Lm2",
    "DJANGO_ALLOWED_HOSTS": "emprendedores.amigo.edu.co",
}

AJUSTES_SEGURIDAD = [
    "DEBUG",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "SECURE_SSL_REDIRECT",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_CONTENT_TYPE_NOSNIFF",
    "SECURE_REFERRER_POLICY",
    "X_FRAME_OPTIONS",
]


def cargar_ajustes_produccion(entorno=ENTORNO_PRODUCCION):
    with mock.patch.dict(os.environ, entorno, clear=False):
        import config.settings.prod as prod

        return importlib.reload(prod)


class ContrasenaCifradaTests(TestCase):
    def setUp(self):
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.usuario = Usuario.objects.get(correo_institucional=CORREO_COMPRADOR)

    def test_la_contrasena_se_guarda_con_hash_argon2id(self):
        self.assertEqual(identify_hasher(self.usuario.password).algorithm, "argon2")
        self.assertTrue(self.usuario.password.startswith("argon2$argon2id$"))
        self.assertTrue(check_password(CONTRASENA_VALIDA, self.usuario.password))

    def test_la_base_de_datos_nunca_contiene_la_contrasena_en_texto_legible(self):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {Usuario._meta.db_table}")
            filas = cursor.fetchall()
        self.assertTrue(filas)
        for fila in filas:
            self.assertNotIn(CONTRASENA_VALIDA, " ".join(str(valor) for valor in fila))

    def test_cada_hash_lleva_una_sal_distinta(self):
        otro = Usuario(correo_institucional="otro@amigo.edu.co", rol="COMPRADOR")
        otro.set_password(CONTRASENA_VALIDA)
        self.assertNotEqual(otro.password, self.usuario.password)

    def test_argon2_es_el_algoritmo_principal_configurado(self):
        self.assertEqual(
            settings.PASSWORD_HASHERS[0], "django.contrib.auth.hashers.Argon2PasswordHasher"
        )


class HttpsTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_una_peticion_http_se_redirige_a_https(self):
        respuesta = self.client.get(reverse("cuentas:ingresar"))
        self.assertEqual(respuesta.status_code, 301)
        self.assertTrue(respuesta["Location"].startswith("https://"))

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000)
    def test_por_https_se_envia_hsts(self):
        respuesta = self.client.get(reverse("cuentas:ingresar"), secure=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("max-age=31536000", respuesta["Strict-Transport-Security"])

    def test_ajustes_de_produccion_obligan_https_y_cookies_seguras(self):
        prod = cargar_ajustes_produccion()
        self.assertFalse(prod.DEBUG)
        self.assertTrue(prod.SECURE_SSL_REDIRECT)
        self.assertTrue(prod.SESSION_COOKIE_SECURE)
        self.assertTrue(prod.CSRF_COOKIE_SECURE)
        self.assertGreaterEqual(prod.SECURE_HSTS_SECONDS, 31536000)

    def test_ajustes_de_produccion_pasan_las_revisiones_de_despliegue(self):
        """Equivale a `manage.py check --deploy` sin advertencias de seguridad."""
        prod = cargar_ajustes_produccion()
        valores = {nombre: getattr(prod, nombre) for nombre in AJUSTES_SEGURIDAD}
        with override_settings(**valores):
            mensajes = checks.run_checks(include_deployment_checks=True, tags=[checks.Tags.security])
        self.assertEqual(mensajes, [], [str(m) for m in mensajes])

    def test_produccion_exige_una_clave_secreta_fuerte(self):
        with self.assertRaises(ImproperlyConfigured):
            cargar_ajustes_produccion({**ENTORNO_PRODUCCION, "DJANGO_SECRET_KEY": "corta"})


class ProteccionFormulariosTests(TestCase):
    def test_un_formulario_enviado_sin_token_csrf_se_rechaza(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("cuentas:registro"), datos_registro())
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Usuario.objects.exists())

    def test_la_cookie_de_sesion_no_es_accesible_desde_javascript(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.client.post(reverse("cuentas:registro"), datos_registro())
        self.client.post(
            reverse("cuentas:ingresar"), {"username": CORREO_COMPRADOR, "password": CONTRASENA_VALIDA}
        )
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME]["httponly"])

    def test_las_paginas_no_se_pueden_incrustar_en_otros_sitios(self):
        respuesta = self.client.get(reverse("cuentas:ingresar"))
        self.assertEqual(respuesta["X-Frame-Options"], "DENY")
