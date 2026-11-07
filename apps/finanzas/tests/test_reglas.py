"""
Pruebas UNITARIAS de las reglas de la Épica 6 (RN-13, RN-15) y del ResumenFinanciero
derivado (supuesto S-7). Valores límite del plan 4.1.4: ingreso con monto 0 o negativo
rechazado; gasto sin categoría rechazado.
"""
from datetime import date

from django.test import SimpleTestCase, TestCase

from apps.finanzas.models import CategoriaGasto
from apps.finanzas.reglas import interpretar_monto, interpretar_periodo
from apps.finanzas.servicios import resumen_financiero

from .utilidades import crear_emprendedor, gasto, ingreso


class ReglaMontoTests(SimpleTestCase):
    """RN-13: el monto es mayor a 0."""

    def test_rn13_acepta_montos_positivos_en_pesos(self):
        for texto, esperado in [("5000", 5000), ("5.000", 5000), ("$ 12.500", 12500), ("1", 1)]:
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_monto(texto), esperado)

    def test_rn13_rechaza_cero_negativos_y_letras(self):
        for texto in ["0", "-1000", "abc", "12a", "", None, "12,5"]:
            with self.subTest(texto=texto):
                self.assertIsNone(interpretar_monto(texto))


class ReglaPeriodoTests(SimpleTestCase):
    def test_interpreta_anio_y_mes(self):
        self.assertEqual(interpretar_periodo("2026-11"), (2026, 11))
        self.assertEqual(interpretar_periodo("2027-01"), (2027, 1))

    def test_un_periodo_invalido_devuelve_none(self):
        for texto in ["2026-13", "2026-00", "noviembre", "", None, "26-11", "1999-01"]:
            with self.subTest(texto=texto):
                self.assertIsNone(interpretar_periodo(texto))


class ResumenFinancieroTests(TestCase):
    """RN-15 · S-7: el resumen se calcula a partir de Ingreso y Gasto; no se almacena."""

    def setUp(self):
        self.emprendedor = crear_emprendedor()

    def test_rn15_ingresos_gastos_y_balance_del_mes(self):
        ingreso(self.emprendedor, 50000, date(2026, 11, 3))
        ingreso(self.emprendedor, 20000, date(2026, 11, 20))
        gasto(self.emprendedor, 15000, CategoriaGasto.MATERIA_PRIMA, date(2026, 11, 5))
        gasto(self.emprendedor, 5000, CategoriaGasto.EMPAQUES, date(2026, 11, 30))
        resumen = resumen_financiero(self.emprendedor, 2026, 11)
        self.assertEqual((resumen.total_ingresos, resumen.total_gastos, resumen.balance), (70000, 20000, 50000))
        self.assertEqual(dict(resumen.gastos_por_categoria), {"Materia prima": 15000, "Empaques": 5000})

    def test_rn15_sin_movimientos_todo_es_cero(self):
        resumen = resumen_financiero(self.emprendedor, 2026, 11)
        self.assertEqual((resumen.total_ingresos, resumen.total_gastos, resumen.balance), (0, 0, 0))
        self.assertEqual(resumen.movimientos, [])

    def test_rn15_solo_cuenta_el_mes_elegido(self):
        ingreso(self.emprendedor, 10000, date(2026, 10, 31))
        ingreso(self.emprendedor, 30000, date(2026, 11, 1))
        gasto(self.emprendedor, 7000, fecha=date(2026, 12, 1))
        resumen = resumen_financiero(self.emprendedor, 2026, 11)
        self.assertEqual((resumen.total_ingresos, resumen.total_gastos), (30000, 0))

    def test_el_balance_puede_ser_negativo(self):
        ingreso(self.emprendedor, 1000, date(2026, 11, 1))
        gasto(self.emprendedor, 4000, fecha=date(2026, 11, 2))
        self.assertEqual(resumen_financiero(self.emprendedor, 2026, 11).balance, -3000)

    def test_rn14_solo_cuenta_los_datos_del_usuario(self):
        otro = crear_emprendedor("otra.persona@amigo.edu.co")
        ingreso(otro, 99000, date(2026, 11, 1))
        self.assertEqual(resumen_financiero(self.emprendedor, 2026, 11).total_ingresos, 0)

    def test_los_movimientos_del_mes_van_del_mas_reciente_al_mas_antiguo(self):
        ingreso(self.emprendedor, 1000, date(2026, 11, 2))
        gasto(self.emprendedor, 500, fecha=date(2026, 11, 9))
        fechas = [m.fecha for m in resumen_financiero(self.emprendedor, 2026, 11).movimientos]
        self.assertEqual(fechas, [date(2026, 11, 9), date(2026, 11, 2)])
