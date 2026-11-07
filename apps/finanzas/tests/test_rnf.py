"""
RNF aplicables a la Épica 6:
- RNF-05 Privacidad (Must): «cada usuario accede solo a sus propios datos, incluidos los
  financieros» (HU-19 Esc. 3 · CP-19.3 · RN-14).
- RNF-06: datos mínimos y aviso de privacidad.
- RNF-03 / RNF-11: viewport y etiquetas.
- CC-10: un insumo puede registrarse también como gasto de materia prima.
"""
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.finanzas.models import CategoriaGasto, Gasto, Ingreso
from apps.inventario.models import Insumo

from .utilidades import (
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    URL_FINANZAS,
    URL_NUEVO_GASTO,
    URL_NUEVO_INGRESO,
    crear_emprendedor,
    crear_usuario,
    entrar,
    gasto,
    ingreso,
)


class PrivacidadTests(TestCase):
    def setUp(self):
        self.a = crear_emprendedor(CORREO_EMPRENDEDOR_A)
        self.ingreso_a = ingreso(self.a, 77777, date(2026, 11, 3))
        self.gasto_a = gasto(self.a, 66666, fecha=date(2026, 11, 4))
        crear_emprendedor(CORREO_EMPRENDEDOR_B)

    def test_cp_19_3_otro_usuario_no_ve_los_ingresos_ajenos(self):
        """CP-19.3 · Esc. 3: el usuario B intenta ver los ingresos de A → se le deniega el acceso."""
        entrar(self.client, CORREO_EMPRENDEDOR_B)
        respuesta = self.client.get(URL_FINANZAS, {"mes": "2026-11"})
        self.assertNotContains(respuesta, "$ 77.777")
        self.assertNotContains(respuesta, "$ 66.666")
        self.assertEqual(respuesta.context["resumen"].total_ingresos, 0)
        for tipo, registro in [("ingreso", self.ingreso_a), ("gasto", self.gasto_a)]:
            url = reverse("finanzas:eliminar", kwargs={"tipo": tipo, "codigo": registro.codigo})
            with self.subTest(tipo=tipo):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Ingreso.objects.filter(pk=self.ingreso_a.pk).exists())
        self.assertTrue(Gasto.objects.filter(pk=self.gasto_a.pk).exists())

    def test_rnf05_un_comprador_no_entra_a_finanzas(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        for destino in [URL_FINANZAS, URL_NUEVO_INGRESO, URL_NUEVO_GASTO]:
            with self.subTest(destino=destino):
                self.assertEqual(self.client.get(destino).status_code, 403)

    def test_sin_sesion_se_pide_iniciar_sesion(self):
        self.assertRedirects(self.client.get(URL_FINANZAS), f"{reverse('cuentas:ingresar')}?next={URL_FINANZAS}")

    def test_las_paginas_de_finanzas_no_quedan_en_cache(self):
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.assertIn("no-store", self.client.get(URL_FINANZAS)["Cache-Control"])


class DatosMinimosTests(TestCase):
    def test_rnf06_solo_se_guardan_los_datos_del_modelo_de_dominio(self):
        self.assertEqual({c.name for c in Ingreso._meta.concrete_fields}, {"id", "codigo", "propietario", "monto", "fecha"})
        self.assertEqual(
            {c.name for c in Gasto._meta.concrete_fields}, {"id", "codigo", "propietario", "monto", "categoria", "fecha"}
        )

    def test_rnf06_el_aviso_informa_el_tratamiento_de_las_finanzas(self):
        self.assertEqual(settings.AVISO_PRIVACIDAD_VERSION, "1.5")
        respuesta = self.client.get(reverse("aviso_privacidad"))
        for texto in ["Versión 1.5", "Tus finanzas", "Solo tú puedes ver tus finanzas"]:
            with self.subTest(texto=texto):
                self.assertContains(respuesta, texto)


class InsumoComoGastoTests(TestCase):
    """CC-10 (punto B.2): relación entre insumos (HU-18) y gastos de materia prima (HU-20)."""

    def setUp(self):
        self.emprendedor = crear_emprendedor(CORREO_EMPRENDEDOR_A)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.url = reverse("inventario:nuevo_insumo")

    def test_la_casilla_viene_marcada_y_crea_el_gasto_de_materia_prima(self):
        formulario = self.client.get(self.url).content.decode()
        inicio = formulario.index('name="registrar_como_gasto"')
        self.assertIn("checked", formulario[formulario.rfind("<input", 0, inicio): formulario.index(">", inicio)])
        respuesta = self.client.post(
            self.url,
            {"nombre": "Queso (lb)", "cantidad": "3", "costo": "21.000", "registrar_como_gasto": "on"},
            follow=True,
        )
        self.assertContains(respuesta, "También quedó como gasto de materia prima")
        gasto = Gasto.objects.get()
        self.assertEqual(
            (gasto.propietario, gasto.monto, gasto.categoria),
            (self.emprendedor, Decimal("21000"), CategoriaGasto.MATERIA_PRIMA),
        )

    def test_sin_la_casilla_solo_se_registra_el_insumo(self):
        self.client.post(self.url, {"nombre": "Harina (kg)", "cantidad": "2", "costo": "8000"})
        self.assertEqual(Insumo.objects.count(), 1)
        self.assertFalse(Gasto.objects.exists())

    def test_un_insumo_de_costo_0_no_crea_un_gasto(self):
        self.client.post(self.url, {"nombre": "Regalo", "cantidad": "1", "costo": "0", "registrar_como_gasto": "on"})
        self.assertEqual(Insumo.objects.count(), 1)
        self.assertFalse(Gasto.objects.exists())


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
        emprendedor = crear_emprendedor(CORREO_EMPRENDEDOR_A)
        ingreso(emprendedor, 1000)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        for destino in [URL_FINANZAS, URL_NUEVO_INGRESO, URL_NUEVO_GASTO]:
            analizador = _Analizador()
            analizador.feed(self.client.get(destino).content.decode())
            with self.subTest(destino=destino):
                self.assertTrue(analizador.viewport)
                for campo in analizador.campos:
                    self.assertIn(campo.get("id"), analizador.etiquetas)

    def test_el_panel_del_emprendedor_enlaza_las_finanzas(self):
        crear_emprendedor(CORREO_EMPRENDEDOR_A)
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.assertContains(self.client.get("/emprendimiento/"), f'href="{URL_FINANZAS}"')
