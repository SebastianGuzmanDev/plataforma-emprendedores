"""
RNF aplicables a la Épica 2:
- RNF-03 Compatibilidad (Must) y RNF-11 Accesibilidad (Could): viewport, etiquetas y
  texto alternativo en las fotos.
- RNF-05 Privacidad (Must): acceso solo a lo propio (ver también test_hu06_mantener).
- RNF-06 Cumplimiento legal (Must): datos mínimos y aviso actualizado.
- RNF-09 Escalabilidad (Should): 100 usuarios y 300 productos registrados.
"""
from html.parser import HTMLParser

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.cuentas.models import Rol, Usuario
from apps.perfil_productos.models import Categoria, Emprendimiento, EstadoProducto, Producto

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    MediaTemporalMixin,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
)
from apps.cuentas.tests.utilidades import CONTRASENA_VALIDA, crear_usuario


class _Analizador(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imagenes, self.campos, self.etiquetas, self.viewport = [], [], set(), False

    def handle_starttag(self, etiqueta, atributos):
        attrs = dict(atributos)
        if etiqueta == "img":
            self.imagenes.append(attrs)
        elif etiqueta in ("input", "select", "textarea") and attrs.get("type") not in ("hidden", "submit"):
            self.campos.append(attrs)
        elif etiqueta == "label" and attrs.get("for"):
            self.etiquetas.add(attrs["for"])
        elif etiqueta == "meta" and attrs.get("name") == "viewport":
            self.viewport = "width=device-width" in attrs.get("content", "")


class InterfazE2Tests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.producto = crear_producto(crear_perfil(crear_emprendedor()), nombre="Arepa de queso")
        crear_producto(self.producto.emprendimiento, nombre="Empanada", estado=EstadoProducto.AGOTADO)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        codigo = {"codigo": self.producto.codigo}
        self.urls = [
            reverse("emprendimiento:panel"),
            reverse("emprendimiento:perfil"),
            reverse("emprendimiento:publicar"),
            reverse("emprendimiento:vista_previa"),
            reverse("emprendimiento:editar", kwargs=codigo),
            reverse("emprendimiento:desactivar", kwargs=codigo),
        ]

    def paginas(self):
        for url in self.urls:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            analizador = _Analizador()
            analizador.feed(respuesta.content.decode())
            yield url, analizador

    def test_rnf03_todas_las_paginas_declaran_viewport_movil(self):
        for url, pagina in self.paginas():
            with self.subTest(url=url):
                self.assertTrue(pagina.viewport)

    def test_rnf11_cada_campo_tiene_etiqueta(self):
        for url, pagina in self.paginas():
            for campo in pagina.campos:
                with self.subTest(url=url, campo=campo.get("name")):
                    self.assertIn(campo.get("id"), pagina.etiquetas)

    def test_rnf11_las_fotos_de_productos_tienen_texto_alternativo_con_su_nombre(self):
        for url, pagina in self.paginas():
            fotos = [img for img in pagina.imagenes if "/productos/" in img.get("src", "")]
            for foto in fotos:
                with self.subTest(url=url, src=foto["src"]):
                    self.assertTrue(foto.get("alt", "").strip())
        vista = self.client.get(reverse("emprendimiento:vista_previa"))
        self.assertContains(vista, 'alt="Arepa de queso"')
        self.assertContains(vista, 'alt="Empanada"')

    def test_el_encabezado_del_emprendedor_enlaza_su_emprendimiento(self):
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), f'href="{reverse("emprendimiento:panel")}"')


class PrivacidadE2Tests(TestCase):
    def test_rnf05_un_comprador_no_entra_a_ninguna_pantalla_del_emprendedor(self):
        producto = crear_producto(crear_perfil(crear_emprendedor()))
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        for nombre in ["panel", "perfil", "publicar", "vista_previa"]:
            with self.subTest(pantalla=nombre):
                self.assertEqual(self.client.get(reverse(f"emprendimiento:{nombre}")).status_code, 403)
        for nombre in ["editar", "agotado", "disponible", "desactivar"]:
            with self.subTest(pantalla=nombre):
                destino = reverse(f"emprendimiento:{nombre}", kwargs={"codigo": producto.codigo})
                self.assertEqual(self.client.post(destino).status_code, 403)

    def test_las_rutas_de_productos_usan_un_codigo_no_secuencial(self):
        """Los enlaces no revelan cuántos productos hay ni permiten recorrerlos en orden."""
        producto = crear_producto(crear_perfil(crear_emprendedor()))
        ruta = reverse("emprendimiento:editar", kwargs={"codigo": producto.codigo})
        self.assertRegex(ruta, r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/")
        self.assertNotIn(f"/{producto.pk}/", ruta)


class LegalE2Tests(TestCase):
    CAMPOS_EMPRENDIMIENTO = {"id", "propietario", "nombre", "categoria", "descripcion", "horarios", "zona_entrega"}
    # «miniatura» llega con CC-06 (cambio de diseño para RNF-01).
    CAMPOS_PRODUCTO = {"id", "codigo", "emprendimiento", "nombre", "foto", "miniatura", "precio_referencia", "estado"}

    def test_rnf06_el_perfil_y_el_producto_solo_guardan_los_datos_previstos(self):
        """RF-05 (con el nombre de CC-03), RF-06 y el modelo de dominio; existencias y umbral llegan con E5."""
        self.assertEqual({c.name for c in Emprendimiento._meta.concrete_fields}, self.CAMPOS_EMPRENDIMIENTO)
        self.assertEqual({c.name for c in Producto._meta.concrete_fields}, self.CAMPOS_PRODUCTO)

    def test_rnf06_el_aviso_informa_la_publicacion_en_el_catalogo(self):
        self.assertEqual(settings.AVISO_PRIVACIDAD_VERSION, "1.2")
        respuesta = self.client.get(reverse("aviso_privacidad"))
        for texto in [
            "Versión 1.2",
            "perfil de tu emprendimiento: nombre, descripción, categoría",
            "se publican en el catálogo",
            "ubicación GPS",
        ]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)

    def test_rnf06_quien_acepto_una_version_anterior_ve_el_aviso_de_actualizacion(self):
        usuario = crear_usuario()
        Usuario.objects.filter(pk=usuario.pk).update(aviso_privacidad_version="1.0")
        entrar(self.client, usuario.correo_institucional)
        respuesta = self.client.get(reverse("cuentas:mi_cuenta"))
        self.assertContains(respuesta, "Actualizamos el aviso de privacidad")


class EscalabilidadE2Tests(TestCase):
    """RNF-09: 100 usuarios y 300 productos registrados."""

    @classmethod
    def setUpTestData(cls):
        hash_comun = make_password(CONTRASENA_VALIDA)
        ahora = timezone.now()
        usuarios = Usuario.objects.bulk_create(
            Usuario(
                correo_institucional=f"persona{i:03d}@amigo.edu.co",
                rol=Rol.EMPRENDEDOR if i < 30 else Rol.COMPRADOR,
                password=hash_comun,
                aviso_privacidad_aceptado=True,
                aviso_privacidad_version="1.2",
                aviso_privacidad_fecha=ahora,
            )
            for i in range(100)
        )
        categorias = list(Categoria.objects.all())
        emprendimientos = Emprendimiento.objects.bulk_create(
            Emprendimiento(
                propietario=usuario,
                nombre=f"Emprendimiento {i}",
                categoria=categorias[i % len(categorias)],
                descripcion=f"Emprendimiento {i}",
                horarios="Lunes a viernes",
                zona_entrega="Bloque 1",
            )
            for i, usuario in enumerate(usuarios[:30])
        )
        Producto.objects.bulk_create(
            Producto(
                emprendimiento=emprendimientos[i % 30],
                nombre=f"Producto {i}",
                precio_referencia=1000 + i,
                estado=EstadoProducto.DESACTIVADO if i % 10 == 0 else EstadoProducto.DISPONIBLE,
                foto=f"productos/p{i}.jpg",
            )
            for i in range(300)
        )

    def test_rnf09_con_300_productos_el_catalogo_responde_completo(self):
        self.assertEqual(Usuario.objects.count(), 100)
        self.assertEqual(Producto.objects.count(), 300)
        self.assertEqual(Producto.objects.visibles_en_catalogo().count(), 270)

    def test_rnf09_las_consultas_del_panel_no_crecen_con_la_cantidad_de_productos(self):
        def consultas_del_panel(correo):
            self.client.logout()
            entrar(self.client, correo)
            with CaptureQueriesContext(connection) as contexto:
                self.assertEqual(self.client.get(reverse("emprendimiento:panel")).status_code, 200)
            return len(contexto.captured_queries)

        pocos = consultas_del_panel("persona000@amigo.edu.co")  # 10 productos
        destino = Emprendimiento.objects.get(propietario__correo_institucional="persona002@amigo.edu.co")
        Producto.objects.filter(pk__in=Producto.objects.values("pk")[:150]).update(emprendimiento=destino)
        self.assertGreater(destino.productos.count(), 100)
        muchos = consultas_del_panel("persona002@amigo.edu.co")
        self.assertEqual(pocos, muchos)
