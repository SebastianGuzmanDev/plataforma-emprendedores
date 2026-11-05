"""
RNF-05 · Privacidad (Must): cada usuario accede solo a sus propios datos.

En E1 los datos propios son los de la cuenta. El mecanismo (identificar al
usuario por la sesión y nunca por un identificador en la URL) es el mismo que
usarán E5 y E6 para inventario y finanzas.
"""
from django.test import TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, CORREO_EMPRENDEDOR, crear_usuario

URL_MI_CUENTA = reverse("cuentas:mi_cuenta")


def rutas(resolver=None, prefijo=""):
    resolver = resolver or get_resolver()
    for patron in resolver.url_patterns:
        if isinstance(patron, URLResolver):
            yield from rutas(patron, prefijo + str(patron.pattern))
        elif isinstance(patron, URLPattern):
            yield prefijo + str(patron.pattern), patron.name


class PrivacidadCuentaTests(TestCase):
    def setUp(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        crear_usuario(correo=CORREO_EMPRENDEDOR, rol="EMPRENDEDOR")

    def test_mi_cuenta_muestra_solo_los_datos_del_usuario_con_sesion(self):
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)
        respuesta = self.client.get(URL_MI_CUENTA)
        self.assertContains(respuesta, CORREO_COMPRADOR)
        self.assertNotContains(respuesta, CORREO_EMPRENDEDOR)

    def test_sin_sesion_no_hay_acceso_a_los_datos_de_la_cuenta(self):
        respuesta = self.client.get(URL_MI_CUENTA)
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn(CORREO_COMPRADOR, respuesta.content.decode())

    def test_ninguna_ruta_recibe_el_identificador_de_otro_usuario(self):
        """Solo el enlace de recuperación lleva un identificador, protegido con token firmado."""
        for ruta, nombre in rutas():
            if nombre == "restablecer":
                self.assertIn("<token>", ruta)
                continue
            with self.subTest(ruta=ruta):
                self.assertNotRegex(ruta, r"<(int:|str:|slug:|uuid:)?(pk|id|usuario|user)")

    def test_las_paginas_vistas_con_sesion_no_quedan_en_cache(self):
        """Tras cerrar sesión, el botón «atrás» no puede mostrar datos privados guardados."""
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)
        for url in [URL_MI_CUENTA, reverse("inicio")]:
            with self.subTest(url=url):
                cabecera = self.client.get(url).get("Cache-Control", "")
                self.assertIn("no-store", cabecera)
                self.assertIn("private", cabecera)
