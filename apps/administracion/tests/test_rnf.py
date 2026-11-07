"""
RNF aplicables a la Épica 7:
- RNF-05 / RN-14: el administrador no accede a los datos privados de nadie (mensajes,
  inventario ni finanzas); cada emprendedor ve solo sus avisos.
- RNF-06: datos mínimos y aviso de privacidad 1.6.
- RNF-03 / RNF-11: viewport y etiquetas.
"""
from html.parser import HTMLParser

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.administracion import servicios
from apps.administracion.models import Desactivacion, MotivoDesactivacion
from apps.contacto import servicios as contacto

from .utilidades import (
    CORREO_ADMIN,
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    MOTIVO,
    URL_ADMIN,
    URL_ADMIN_CUENTAS,
    URL_ADMIN_PRODUCTOS,
    URL_AVISOS,
    crear_administrador,
    crear_usuario,
    emprendedor_con_producto,
    entrar,
    url_desactivar_cuenta,
    url_desactivar_producto,
)


class PrivacidadTests(TestCase):
    def setUp(self):
        self.admin = crear_administrador()
        self.emprendedor, self.producto = emprendedor_con_producto()
        self.comprador = crear_usuario(correo=CORREO_COMPRADOR)

    def test_rn14_el_administrador_no_ve_mensajes_inventario_ni_finanzas(self):
        conversacion, _ = contacto.iniciar_conversacion(self.comprador, self.producto)
        entrar(self.client, CORREO_ADMIN)
        for destino in [
            reverse("finanzas:resumen"),
            reverse("inventario:panel"),
            reverse("contacto:conversacion", kwargs={"codigo": conversacion.codigo}),
            URL_AVISOS,
        ]:
            with self.subTest(destino=destino):
                self.assertEqual(self.client.get(destino).status_code, 403)

    def test_rnf05_cada_emprendedor_ve_solo_sus_avisos(self):
        servicios.desactivar_producto(self.admin, self.producto, motivo=MOTIVO, detalle="Detalle privado de A")
        emprendedor_con_producto(CORREO_EMPRENDEDOR_B, "Pulsera")
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        avisos = self.client.get(URL_AVISOS)
        self.assertNotContains(avisos, "Arepa de queso")
        self.assertNotContains(avisos, "Detalle privado de A")
        self.assertContains(avisos, "No tienes avisos de la administración")

    def test_las_paginas_de_administracion_no_quedan_en_cache(self):
        entrar(self.client, CORREO_ADMIN)
        self.assertIn("no-store", self.client.get(URL_ADMIN_CUENTAS)["Cache-Control"])

    def test_la_lista_de_cuentas_muestra_solo_correo_rol_y_estado(self):
        entrar(self.client, CORREO_ADMIN)
        html = self.client.get(URL_ADMIN_CUENTAS).content.decode()
        self.assertIn(CORREO_COMPRADOR, html)
        self.assertNotIn("Versión", html)  # ni datos del consentimiento ni contraseñas


class DatosMinimosTests(TestCase):
    def test_rnf06_la_desactivacion_guarda_solo_lo_necesario(self):
        self.assertEqual(
            {c.name for c in Desactivacion._meta.concrete_fields},
            {"id", "codigo", "administrador", "producto", "cuenta", "motivo", "detalle", "fecha", "vista_en",
             "reactivada_en"},
        )

    def test_rnf06_el_aviso_informa_la_administracion(self):
        self.assertEqual(settings.AVISO_PRIVACIDAD_VERSION, "1.6")
        respuesta = self.client.get(reverse("aviso_privacidad"))
        for texto in [
            "Versión 1.6",
            "La administración",
            "no puede ver tus mensajes, tu inventario ni tus finanzas",
            "te lo informamos en la plataforma con el motivo",
        ]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)


class HistorialTests(TestCase):
    def test_el_panel_muestra_el_historial_de_desactivaciones(self):
        admin = crear_administrador()
        _, producto = emprendedor_con_producto()
        servicios.desactivar_producto(admin, producto, motivo=MOTIVO)
        entrar(self.client, CORREO_ADMIN)
        panel = self.client.get(URL_ADMIN)
        for texto in ["Arepa de queso", MotivoDesactivacion(MOTIVO).label, CORREO_ADMIN]:
            with self.subTest(texto=texto):
                self.assertContains(panel, texto)


class _Analizador(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos, self.etiquetas, self.viewport = [], set(), False

    def handle_starttag(self, etiqueta, atributos):
        attrs = dict(atributos)
        if etiqueta in ("input", "select", "textarea") and attrs.get("type") not in ("hidden", "submit"):
            self.campos.append(attrs)
        elif etiqueta == "label" and attrs.get("for"):
            self.etiquetas.add(attrs["for"])
        elif etiqueta == "meta" and attrs.get("name") == "viewport":
            self.viewport = "width=device-width" in attrs.get("content", "")


class InterfazTests(TestCase):
    def test_rnf03_viewport_y_rnf11_etiquetas(self):
        crear_administrador()
        _, producto = emprendedor_con_producto()
        comprador = crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_ADMIN)
        for destino in [URL_ADMIN, URL_ADMIN_PRODUCTOS, URL_ADMIN_CUENTAS, url_desactivar_producto(producto),
                        url_desactivar_cuenta(comprador)]:
            analizador = _Analizador()
            analizador.feed(self.client.get(destino).content.decode())
            with self.subTest(destino=destino):
                self.assertTrue(analizador.viewport)
                if destino != URL_ADMIN:  # el panel no tiene formularios
                    self.assertTrue(analizador.campos)
                for campo in analizador.campos:
                    self.assertIn(campo.get("id"), analizador.etiquetas)

    def test_solo_el_administrador_ve_el_enlace_de_administracion(self):
        crear_administrador()
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_ADMIN)
        self.assertContains(self.client.get("/"), f'href="{URL_ADMIN}"')
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), f'href="{URL_ADMIN}"')
        self.client.logout()
        entrar(self.client, CORREO_COMPRADOR)
        self.assertNotContains(self.client.get("/"), f'href="{URL_ADMIN}"')

    def test_el_aviso_pendiente_se_anuncia_como_texto(self):
        admin = crear_administrador()
        emprendedor, producto = emprendedor_con_producto()
        servicios.desactivar_producto(admin, producto, motivo=MOTIVO)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        html = self.client.get("/").content.decode()
        self.assertIn('class="aviso aviso--alerta aviso-administracion"', html)
        self.assertIn("La administración desactivó 1 de tus productos", html)
