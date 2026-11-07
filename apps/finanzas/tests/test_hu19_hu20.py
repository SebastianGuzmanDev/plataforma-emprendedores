"""
HU-19 · Registrar un ingreso (Should) · RF-21, RNF-05 · CU-19 · RN-13, RN-14.
HU-20 · Registrar un gasto (Should) · RF-22 · CU-20 · RN-13.
"""
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.finanzas.models import CategoriaGasto, Gasto, Ingreso

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    URL_FINANZAS,
    URL_NUEVO_GASTO,
    URL_NUEVO_INGRESO,
    crear_emprendedor,
    entrar,
    ingreso,
)


def hoy():
    return timezone.localdate()


class HU19IngresoTests(TestCase):
    def setUp(self):
        self.emprendedor = crear_emprendedor()
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_19_1_un_ingreso_valido_se_guarda_y_se_suma_al_total(self):
        """CP-19.1 · Esc. 1: un ingreso con monto válido queda guardado y se suma al total."""
        ingreso(self.emprendedor, 10000)
        formulario = self.client.get(URL_NUEVO_INGRESO)
        self.assertContains(formulario, f'value="{hoy().isoformat()}"')  # la fecha propone hoy
        respuesta = self.client.post(URL_NUEVO_INGRESO, {"monto": "25.000", "fecha": hoy().isoformat()}, follow=True)
        self.assertRedirects(respuesta, f"{URL_FINANZAS}?mes={hoy():%Y-%m}")
        self.assertContains(respuesta, "Registraste un ingreso de $ 25.000")
        self.assertEqual(Ingreso.objects.filter(propietario=self.emprendedor).count(), 2)
        self.assertEqual(respuesta.context["resumen"].total_ingresos, 35000)
        self.assertContains(respuesta, '<span class="cifra__valor">$ 35.000</span>')

    def test_cp_19_2_monto_cero_o_negativo_se_rechaza(self):
        """CP-19.2 · Esc. 2: un ingreso de 0 o negativo se rechaza."""
        for monto in ["0", "-5000", "abc"]:
            with self.subTest(monto=monto):
                respuesta = self.client.post(URL_NUEVO_INGRESO, {"monto": monto, "fecha": hoy().isoformat()})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Escribe un monto mayor a 0")
        self.assertFalse(Ingreso.objects.exists())

    def test_la_fecha_no_puede_ser_futura_ni_faltar(self):
        manana = (hoy() + timedelta(days=1)).isoformat()
        for fecha, mensaje in [(manana, "no puede ser futura"), ("", "Indica la fecha"), ("31/02/2026", "Indica la fecha")]:
            with self.subTest(fecha=fecha):
                respuesta = self.client.post(URL_NUEVO_INGRESO, {"monto": "1000", "fecha": fecha})
                self.assertContains(respuesta, mensaje)
        self.assertFalse(Ingreso.objects.exists())

    def test_se_puede_registrar_un_ingreso_de_un_dia_anterior(self):
        ayer = hoy() - timedelta(days=1)
        self.client.post(URL_NUEVO_INGRESO, {"monto": "1000", "fecha": ayer.isoformat()})
        self.assertEqual(Ingreso.objects.get().fecha, ayer)


class HU20GastoTests(TestCase):
    def setUp(self):
        self.emprendedor = crear_emprendedor()
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_20_1_un_gasto_con_monto_y_categoria_se_guarda(self):
        """CP-20.1 · Esc. 1: un gasto con monto y categoría queda guardado."""
        formulario = self.client.get(URL_NUEVO_GASTO)
        for categoria in ["Materia prima", "Empaques", "Transporte", "Publicidad", "Herramientas y equipos", "Otros"]:
            self.assertContains(formulario, categoria)
        respuesta = self.client.post(
            URL_NUEVO_GASTO,
            {"monto": "12.000", "categoria": CategoriaGasto.MATERIA_PRIMA, "fecha": hoy().isoformat()},
            follow=True,
        )
        self.assertContains(respuesta, "Registraste un gasto de $ 12.000 en Materia prima")
        gasto = Gasto.objects.get()
        self.assertEqual(
            (gasto.propietario, gasto.monto, gasto.categoria, gasto.fecha),
            (self.emprendedor, 12000, CategoriaGasto.MATERIA_PRIMA, hoy()),
        )

    def test_cp_20_2_un_gasto_sin_categoria_se_rechaza(self):
        """CP-20.2 · Esc. 2: un gasto sin categoría se rechaza."""
        for categoria in [None, "", "VIAJES"]:
            with self.subTest(categoria=categoria):
                datos = {"monto": "5000", "fecha": hoy().isoformat()}
                if categoria is not None:
                    datos["categoria"] = categoria
                respuesta = self.client.post(URL_NUEVO_GASTO, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Elige la categoría del gasto")
        self.assertFalse(Gasto.objects.exists())

    def test_rn13_el_gasto_tambien_exige_un_monto_mayor_a_0(self):
        respuesta = self.client.post(
            URL_NUEVO_GASTO, {"monto": "0", "categoria": CategoriaGasto.OTROS, "fecha": hoy().isoformat()}
        )
        self.assertContains(respuesta, "Escribe un monto mayor a 0")
        self.assertFalse(Gasto.objects.exists())


class EliminarRegistroTests(TestCase):
    """Corregir un error: un registro se elimina con confirmación (DT-E6-05)."""

    def setUp(self):
        self.emprendedor = crear_emprendedor()
        self.registro = ingreso(self.emprendedor, 8000, date(2026, 11, 3))
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_eliminar_pide_confirmacion_y_luego_borra(self):
        from django.urls import reverse

        url = reverse("finanzas:eliminar", kwargs={"tipo": "ingreso", "codigo": self.registro.codigo})
        confirmacion = self.client.get(url)
        self.assertContains(confirmacion, "¿Eliminar el ingreso de $ 8.000")
        respuesta = self.client.post(url, follow=True)
        self.assertRedirects(respuesta, f"{URL_FINANZAS}?mes=2026-11")
        self.assertContains(respuesta, "Eliminaste el ingreso de $ 8.000")
        self.assertFalse(Ingreso.objects.exists())
