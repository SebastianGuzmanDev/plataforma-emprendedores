"""
HU-17 · Recibir alerta de stock bajo (Could) · RF-19 · CU-17 «extend» CU-16 · RN-11.
HU-18 · Registrar insumos (materia prima) (Could) · RF-20 · CU-18 · RN-12.
"""
from decimal import Decimal

from django.test import TestCase

from apps.inventario.models import Insumo

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    URL_INVENTARIO,
    URL_NUEVO_INSUMO,
    entrar,
    producto_con_existencias,
    url,
)

ALERTA = "Stock bajo"


class HU17AlertaStockBajoTests(TestCase):
    def setUp(self):
        self.producto = producto_con_existencias(existencias=10)
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def definir_umbral(self, valor):
        return self.client.post(url("umbral", self.producto), {"umbral_stock_bajo": valor}, follow=True)

    def test_cp_17_1_al_bajar_del_umbral_aparece_la_alerta(self):
        """CP-17.1 · Esc. 1: con un umbral definido, si las existencias bajan de él veo la alerta."""
        self.definir_umbral("5")
        respuesta = self.client.post(url("movimiento", self.producto), {"tipo": "SALIDA", "cantidad": "6"}, follow=True)
        self.assertContains(respuesta, "Stock bajo: quedan 4 unidades de «Arepa de queso» (umbral: 5)")
        self.assertContains(self.client.get(URL_INVENTARIO), ALERTA)
        self.assertContains(self.client.get("/emprendimiento/"), ALERTA)

    def test_cp_17_2_por_encima_del_umbral_no_hay_alerta(self):
        """CP-17.2 · Esc. 2: con existencias por encima del umbral no veo ninguna alerta."""
        self.definir_umbral("5")
        self.client.post(url("movimiento", self.producto), {"tipo": "SALIDA", "cantidad": "4"})
        for pagina in [URL_INVENTARIO, url("producto", self.producto), "/emprendimiento/"]:
            with self.subTest(pagina=pagina):
                self.assertNotContains(self.client.get(pagina), ALERTA)

    def test_rn11_existencias_iguales_al_umbral_no_generan_alerta(self):
        """C2: la condición es existencias < umbral."""
        self.definir_umbral("10")
        self.assertNotContains(self.client.get(URL_INVENTARIO), ALERTA)

    def test_el_umbral_se_define_y_se_puede_quitar(self):
        respuesta = self.definir_umbral("3")
        self.assertContains(respuesta, "Te avisaremos cuando queden menos de 3 unidades")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.umbral_stock_bajo, 3)
        self.definir_umbral("")
        self.producto.refresh_from_db()
        self.assertIsNone(self.producto.umbral_stock_bajo)

    def test_el_umbral_debe_ser_un_entero_de_al_menos_1(self):
        for valor in ["0", "-1", "2.5", "abc"]:
            with self.subTest(valor=valor):
                respuesta = self.client.post(url("umbral", self.producto), {"umbral_stock_bajo": valor})
                self.assertContains(respuesta, "El umbral debe ser un número entero de al menos 1")
        self.producto.refresh_from_db()
        self.assertIsNone(self.producto.umbral_stock_bajo)


class HU18InsumosTests(TestCase):
    def setUp(self):
        self.producto = producto_con_existencias()
        self.emprendedor = self.producto.emprendimiento.propietario
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_18_1_registrar_un_insumo_con_nombre_cantidad_y_costo(self):
        """CP-18.1 · Esc. 1: un insumo con nombre, cantidad y costo queda guardado."""
        respuesta = self.client.post(
            URL_NUEVO_INSUMO, {"nombre": "Harina de maíz (kg)", "cantidad": "2,5", "costo": "12.000"}, follow=True
        )
        self.assertRedirects(respuesta, URL_INVENTARIO)
        self.assertContains(respuesta, "Registraste el insumo «Harina de maíz (kg)»")
        insumo = Insumo.objects.get()
        self.assertEqual(
            (insumo.propietario, insumo.nombre, insumo.cantidad, insumo.costo),
            (self.emprendedor, "Harina de maíz (kg)", Decimal("2.5"), Decimal("12000")),
        )
        self.assertContains(respuesta, "Harina de maíz (kg)")
        self.assertContains(respuesta, "2,5")
        self.assertContains(respuesta, "$ 12.000")

    def test_cp_18_2_costo_vacio_o_cantidad_0_se_rechaza(self):
        """CP-18.2 · Esc. 2: con el costo vacío o la cantidad en 0 se rechaza."""
        casos = [
            ({"nombre": "Queso", "cantidad": "1", "costo": ""}, "Escribe el costo"),
            ({"nombre": "Queso", "cantidad": "0", "costo": "5000"}, "La cantidad debe ser mayor que 0"),
            ({"nombre": "", "cantidad": "1", "costo": "5000"}, "Escribe el nombre del insumo"),
        ]
        for datos, mensaje in casos:
            with self.subTest(datos=datos):
                respuesta = self.client.post(URL_NUEVO_INSUMO, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, mensaje)
        self.assertFalse(Insumo.objects.exists())

    def test_el_panel_muestra_el_costo_total_de_los_insumos(self):
        Insumo.objects.create(propietario=self.emprendedor, nombre="Queso (lb)", cantidad=Decimal("3"), costo=15000)
        Insumo.objects.create(propietario=self.emprendedor, nombre="Harina (kg)", cantidad=Decimal("2"), costo=8000)
        respuesta = self.client.get(URL_INVENTARIO)
        self.assertContains(respuesta, "Costo total de los insumos registrados: $ 23.000")

    def test_sin_insumos_se_invita_a_registrar_el_primero(self):
        self.assertContains(self.client.get(URL_INVENTARIO), "Aún no has registrado insumos")
