"""
HU-21 · Ver el resumen financiero de un periodo (Should) · RF-23 · CU-21 · RN-15.
"""
from datetime import date

from django.test import TestCase
from django.utils import timezone

from apps.finanzas.models import CategoriaGasto

from .utilidades import CORREO_EMPRENDEDOR_A, URL_FINANZAS, crear_emprendedor, entrar, gasto, ingreso


class HU21ResumenTests(TestCase):
    def setUp(self):
        self.emprendedor = crear_emprendedor()
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def resumen(self, mes):
        return self.client.get(URL_FINANZAS, {"mes": mes})

    def test_cp_21_1_resumen_del_mes_con_ingresos_gastos_y_balance(self):
        """CP-21.1 · Esc. 1: con ingresos y gastos en un mes veo ingresos, gastos y balance."""
        ingreso(self.emprendedor, 80000, date(2026, 11, 4))
        gasto(self.emprendedor, 30000, CategoriaGasto.MATERIA_PRIMA, date(2026, 11, 6))
        gasto(self.emprendedor, 5000, CategoriaGasto.TRANSPORTE, date(2026, 11, 8))
        respuesta = self.resumen("2026-11")
        self.assertContains(respuesta, "Noviembre de 2026")
        for etiqueta, valor in [("Ingresos", "$ 80.000"), ("Gastos", "$ 35.000"), ("Balance", "$ 45.000")]:
            with self.subTest(etiqueta=etiqueta):
                self.assertRegex(
                    respuesta.content.decode(),
                    rf'<span class="cifra__etiqueta">{etiqueta}</span>\s*<span class="cifra__valor">\{valor}</span>',
                )
        self.assertContains(respuesta, "Ganancia")
        self.assertContains(respuesta, "Materia prima")
        self.assertContains(respuesta, "Transporte")

    def test_cp_21_2_un_periodo_sin_movimientos_muestra_todo_en_0(self):
        """CP-21.2 · Esc. 2: sin movimientos en el periodo, todos los valores aparecen en 0."""
        respuesta = self.resumen("2026-11")
        resumen = respuesta.context["resumen"]
        self.assertEqual((resumen.total_ingresos, resumen.total_gastos, resumen.balance), (0, 0, 0))
        self.assertEqual(respuesta.content.decode().count('<span class="cifra__valor">$ 0</span>'), 3)
        self.assertContains(respuesta, "No registraste movimientos en este mes")

    def test_cp_21_3_al_elegir_un_mes_no_aparecen_los_de_otros_meses(self):
        """CP-21.3 · Esc. 3: con movimientos en varios meses, al elegir uno no se muestran los demás."""
        ingreso(self.emprendedor, 11111, date(2026, 10, 15))
        ingreso(self.emprendedor, 22222, date(2026, 11, 15))
        gasto(self.emprendedor, 33333, fecha=date(2026, 12, 1))
        respuesta = self.resumen("2026-11")
        self.assertContains(respuesta, "$ 22.222")
        self.assertNotContains(respuesta, "$ 11.111")
        self.assertNotContains(respuesta, "$ 33.333")
        octubre = self.resumen("2026-10")
        self.assertContains(octubre, "$ 11.111")
        self.assertNotContains(octubre, "$ 22.222")

    def test_un_balance_negativo_se_indica_como_perdida(self):
        ingreso(self.emprendedor, 1000, date(2026, 11, 1))
        gasto(self.emprendedor, 4000, fecha=date(2026, 11, 2))
        respuesta = self.resumen("2026-11")
        self.assertContains(respuesta, '<span class="cifra__valor">−$ 3.000</span>')
        self.assertContains(respuesta, "Pérdida")

    def test_se_navega_al_mes_anterior_y_al_siguiente(self):
        html = self.resumen("2026-01").content.decode()
        self.assertIn('href="?mes=2025-12"', html)
        self.assertIn('href="?mes=2026-02"', html)

    def test_sin_mes_o_con_un_mes_invalido_muestra_el_mes_actual(self):
        hoy = timezone.localdate()
        for parametros in [{}, {"mes": "2026-13"}, {"mes": "abc"}]:
            with self.subTest(parametros=parametros):
                periodo = self.client.get(URL_FINANZAS, parametros).context["resumen"].periodo
                self.assertEqual((periodo.year, periodo.month), (hoy.year, hoy.month))

    def test_el_mes_se_elige_con_un_formulario_accesible(self):
        html = self.resumen("2026-11").content.decode()
        self.assertIn('<label for="id_mes"', html)
        self.assertIn('value="2026-11"', html)
