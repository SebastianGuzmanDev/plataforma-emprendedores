"""
RNF aplicables a la Épica 5:
- RNF-05 Privacidad (Must): cada emprendedor ve y modifica solo su inventario e insumos.
- RNF-06: solo se guardan los datos del modelo de dominio.
- RNF-03 / RNF-11: viewport y etiquetas en las pantallas de inventario.
"""
from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse

from apps.cuentas.tests.utilidades import crear_usuario
from apps.inventario.models import Insumo, MovimientoInventario
from apps.perfil_productos.models import Producto

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    URL_INVENTARIO,
    URL_NUEVO_INSUMO,
    entrar,
    producto_con_existencias,
    url,
)


class PrivacidadTests(TestCase):
    def setUp(self):
        self.producto_a = producto_con_existencias(existencias=5, correo=CORREO_EMPRENDEDOR_A)
        Insumo.objects.create(
            propietario=self.producto_a.emprendimiento.propietario, nombre="Insumo secreto", cantidad=1, costo=1000
        )
        producto_con_existencias(existencias=2, correo=CORREO_EMPRENDEDOR_B, nombre="Pulsera")

    def test_rnf05_cada_emprendedor_ve_solo_su_inventario_e_insumos(self):
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        panel = self.client.get(URL_INVENTARIO)
        self.assertContains(panel, "Pulsera")
        self.assertNotContains(panel, "Arepa de queso")
        self.assertNotContains(panel, "Insumo secreto")

    def test_rnf05_el_inventario_de_otro_emprendedor_responde_acceso_denegado(self):
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        self.assertEqual(self.client.get(url("producto", self.producto_a)).status_code, 403)
        for nombre, datos in [
            ("movimiento", {"tipo": "SALIDA", "cantidad": "5"}),
            ("umbral", {"umbral_stock_bajo": "3"}),
            ("existencias", {"existencias": "1"}),
        ]:
            with self.subTest(accion=nombre):
                self.assertEqual(self.client.post(url(nombre, self.producto_a), datos).status_code, 403)
        self.producto_a.refresh_from_db()
        self.assertEqual((self.producto_a.existencias, self.producto_a.umbral_stock_bajo), (5, None))
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_rnf05_un_comprador_no_entra_al_inventario(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        for destino in [URL_INVENTARIO, URL_NUEVO_INSUMO, url("producto", self.producto_a)]:
            with self.subTest(destino=destino):
                self.assertEqual(self.client.get(destino).status_code, 403)

    def test_sin_sesion_se_pide_iniciar_sesion(self):
        respuesta = self.client.get(URL_INVENTARIO)
        self.assertRedirects(respuesta, f"{reverse('cuentas:ingresar')}?next={URL_INVENTARIO}")

    def test_el_catalogo_publico_no_muestra_las_existencias(self):
        html = self.client.get(reverse("catalogo:detalle", kwargs={"codigo": self.producto_a.codigo})).content.decode()
        self.assertNotIn("existencias", html.lower())


class AvisoPrivacidadTests(TestCase):
    def test_rnf06_el_aviso_informa_el_tratamiento_del_inventario_y_los_insumos(self):
        from django.conf import settings

        # La versión vigente la fija el último cambio del aviso (1.5 desde E6).
        respuesta = self.client.get(reverse("aviso_privacidad"))
        for texto in [f"Versión {settings.AVISO_PRIVACIDAD_VERSION}", "Tu inventario", "los insumos que registres", "Solo tú puedes ver tu inventario"]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)


class DatosMinimosTests(TestCase):
    def test_rnf06_solo_se_guardan_los_datos_del_modelo_de_dominio(self):
        self.assertEqual(
            {c.name for c in MovimientoInventario._meta.concrete_fields},
            {"id", "producto", "tipo", "cantidad", "fecha"},
        )
        self.assertEqual(
            {c.name for c in Insumo._meta.concrete_fields}, {"id", "propietario", "nombre", "cantidad", "costo"}
        )
        self.assertTrue({"existencias", "umbral_stock_bajo"} <= {c.name for c in Producto._meta.concrete_fields})


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
        con_existencias = producto_con_existencias(existencias=3, umbral=5)
        sin_existencias = Producto.objects.create(
            emprendimiento=con_existencias.emprendimiento, nombre="Empanada", precio_referencia=2000,
            foto="productos/x.jpg",
        )
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        for destino in [URL_INVENTARIO, URL_NUEVO_INSUMO, url("producto", con_existencias), url("producto", sin_existencias)]:
            analizador = _Analizador()
            analizador.feed(self.client.get(destino).content.decode())
            with self.subTest(destino=destino):
                self.assertTrue(analizador.viewport)
                ids = [campo.get("id") for campo in analizador.campos]
                self.assertEqual(len(ids), len(set(ids)), "ids repetidos entre formularios")
                for campo in analizador.campos:
                    self.assertIn(campo.get("id"), analizador.etiquetas)

    def test_el_panel_del_emprendedor_enlaza_el_inventario(self):
        producto_con_existencias()
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.assertContains(self.client.get("/emprendimiento/"), f'href="{URL_INVENTARIO}"')
