"""
RNF aplicables a la Épica 4:
- RNF-05 Privacidad (Must): solo los dos participantes ven y escriben en la conversación.
- RNF-10 Persistencia (Must): ver test_hu12_mensajes (CP-12.3).
- RNF-06 Cumplimiento legal (Must): el aviso informa el tratamiento de los mensajes.
- RNF-03 / RNF-11: viewport, etiquetas y anuncio del contador.
- RNF-09: la lista no hace más consultas con más conversaciones.
"""
from html.parser import HTMLParser

from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.contacto.models import Conversacion, Mensaje

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    URL_MENSAJES,
    crear_conversacion,
    crear_emprendedor,
    crear_producto,
    crear_usuario,
    entrar,
    escenario,
    url_conversacion,
)


class PrivacidadTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()
        self.conversacion = crear_conversacion(self.comprador, self.producto, [(self.comprador, "Mensaje privado")])
        self.url = url_conversacion(self.conversacion)

    def test_rnf05_un_tercero_no_puede_leer_ni_escribir_en_la_conversacion(self):
        crear_emprendedor(CORREO_EMPRENDEDOR_B)
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        lectura = self.client.get(self.url)
        self.assertEqual(lectura.status_code, 403)
        self.assertNotContains(lectura, "Mensaje privado", status_code=403)
        self.assertEqual(self.client.post(self.url, {"contenido": "Intruso"}).status_code, 403)
        self.assertFalse(Mensaje.objects.filter(contenido="Intruso").exists())
        self.assertNotContains(self.client.get(URL_MENSAJES), "Arepas Doña Rosa")

    def test_rnf05_un_tercero_no_marca_como_leidos_los_mensajes_ajenos(self):
        crear_emprendedor(CORREO_EMPRENDEDOR_B)
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        self.client.get(self.url)
        self.assertFalse(self.conversacion.mensajes.get().leido)

    def test_las_conversaciones_usan_un_codigo_no_secuencial(self):
        self.assertRegex(self.url, r"/mensajes/[0-9a-f-]{36}/$")
        self.assertNotIn(f"/{self.conversacion.pk}/", self.url)

    def test_un_codigo_inexistente_responde_404(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.conversacion.delete()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_los_mensajes_no_quedan_en_cache(self):
        entrar(self.client, CORREO_COMPRADOR)
        self.assertIn("no-store", self.client.get(self.url)["Cache-Control"])


class LegalTests(TestCase):
    CAMPOS_CONVERSACION = {"id", "codigo", "comprador", "emprendedor", "producto", "creada"}
    CAMPOS_MENSAJE = {"id", "conversacion", "autor", "contenido", "fecha_envio", "leido"}

    def test_rnf06_solo_se_guardan_los_datos_del_modelo_de_dominio(self):
        self.assertEqual({c.name for c in Conversacion._meta.concrete_fields}, self.CAMPOS_CONVERSACION)
        self.assertEqual({c.name for c in Mensaje._meta.concrete_fields}, self.CAMPOS_MENSAJE)

    def test_rnf06_el_aviso_informa_el_tratamiento_de_los_mensajes(self):
        # La versión vigente la fija el último cambio del aviso (1.4 desde E5).
        respuesta = self.client.get(reverse("aviso_privacidad"))
        for texto in [
            f"Versión {settings.AVISO_PRIVACIDAD_VERSION}",
            "Los mensajes que envías",
            "solo las dos personas de la conversación",
            "no ve tu correo institucional",
        ]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)


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
    def test_rnf03_viewport_y_rnf11_etiquetas_en_lista_y_conversacion(self):
        comprador, _, producto = escenario()
        conversacion = crear_conversacion(comprador, producto, [(comprador, "Hola")])
        entrar(self.client, CORREO_COMPRADOR)
        for url in [URL_MENSAJES, url_conversacion(conversacion)]:
            analizador = _Analizador()
            analizador.feed(self.client.get(url).content.decode())
            with self.subTest(url=url):
                self.assertTrue(analizador.viewport)
                for campo in analizador.campos:
                    self.assertIn(campo.get("id"), analizador.etiquetas)

    def test_el_encabezado_enlaza_los_mensajes_con_sesion(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        self.assertContains(self.client.get("/"), f'href="{URL_MENSAJES}"')


class EscalabilidadTests(TestCase):
    def test_las_consultas_de_la_lista_no_crecen_con_las_conversaciones(self):
        comprador, emprendedor, producto = escenario()
        perfil = producto.emprendimiento
        entrar(self.client, CORREO_EMPRENDEDOR_A)

        def consultas():
            with CaptureQueriesContext(connection) as contexto:
                self.assertEqual(self.client.get(URL_MENSAJES).status_code, 200)
            return len(contexto.captured_queries)

        def agregar(desde, hasta):
            for i in range(desde, hasta):
                comprador_i = crear_usuario(correo=f"c{i}@amigo.edu.co")
                crear_conversacion(comprador_i, crear_producto(perfil, f"P{i}"), [(comprador_i, "Hola")])

        agregar(0, 3)
        pocas = consultas()
        agregar(3, 40)
        self.assertEqual(consultas(), pocas)
