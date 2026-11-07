"""
RNF-02 · Usabilidad (Must): un comprador nuevo encuentra un producto y abre el chat en
3 minutos o menos. La medición con personas se hace con el protocolo de EPICA-4.md y
scripts/flujo_comprador.mjs; aquí se verifica que el recorrido no tenga tropiezos.
"""
from django.test import TestCase
from django.urls import reverse

from apps.contacto.models import Conversacion
from apps.cuentas.tests.utilidades import CONTRASENA_VALIDA, datos_registro

from .utilidades import escenario, url_iniciar

CORREO_NUEVO = "nuevo.comprador@amigo.edu.co"


class RNF02CompradorNuevoTests(TestCase):
    def setUp(self):
        _, _, self.producto = escenario()
        self.detalle = reverse("catalogo:detalle", kwargs={"codigo": self.producto.codigo})

    def test_rnf02_quien_no_tiene_cuenta_se_registra_y_vuelve_al_producto(self):
        ingreso = self.client.get(reverse("cuentas:ingresar"), {"next": self.detalle})
        self.assertContains(ingreso, f'href="{reverse("cuentas:registro")}?next={self.detalle}"')
        formulario = self.client.get(reverse("cuentas:registro"), {"next": self.detalle})
        self.assertContains(formulario, f'name="next" value="{self.detalle}"')
        registro = self.client.post(
            reverse("cuentas:registro"), {**datos_registro(correo_institucional=CORREO_NUEVO), "next": self.detalle}
        )
        self.assertRedirects(
            registro, f'{reverse("cuentas:ingresar")}?next={self.detalle}', fetch_redirect_response=False
        )
        entrada = self.client.post(
            f'{reverse("cuentas:ingresar")}?next={self.detalle}',
            {"username": CORREO_NUEVO, "password": CONTRASENA_VALIDA, "next": self.detalle},
        )
        self.assertRedirects(entrada, self.detalle)
        chat = self.client.post(url_iniciar(self.producto), follow=True)
        self.assertContains(chat, "Escribe tu primer mensaje")
        self.assertEqual(Conversacion.objects.get().comprador.correo_institucional, CORREO_NUEVO)

    def test_un_destino_externo_se_ignora_en_el_registro(self):
        respuesta = self.client.post(
            reverse("cuentas:registro"),
            {**datos_registro(correo_institucional=CORREO_NUEVO), "next": "https://sitio-malicioso.com/"},
        )
        self.assertRedirects(respuesta, reverse("cuentas:ingresar"), fetch_redirect_response=False)

    def test_el_registro_sin_destino_sigue_como_en_la_epica_1(self):
        respuesta = self.client.post(reverse("cuentas:registro"), datos_registro(correo_institucional=CORREO_NUEVO))
        self.assertRedirects(respuesta, reverse("cuentas:ingresar"))
