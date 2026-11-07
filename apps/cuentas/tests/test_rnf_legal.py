"""
RNF-06 · Cumplimiento legal (Must): tratamiento de datos personales conforme a la
Ley 1581 de 2012 (aviso de privacidad, consentimiento explícito y datos mínimos).
"""
from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.cuentas.models import Usuario

from .utilidades import CORREO_COMPRADOR, datos_registro

URL_AVISO = reverse("aviso_privacidad")

# Datos previstos en la matriz (RF-01, RF-03) y en el modelo de dominio del
# Entregable 2 (Usuario), más la evidencia del consentimiento. Agregar cualquier
# otro dato personal exige actualizar la matriz (riesgo R5).
CAMPOS_PERMITIDOS = {
    "id",
    "password",  # contrasenaCifrada (hash)
    "last_login",  # dato técnico: invalida enlaces de recuperación ya usados
    "correo_institucional",
    "rol",
    "aviso_privacidad_aceptado",
    "aviso_privacidad_version",
    "aviso_privacidad_fecha",
    "activo",
    "codigo",  # E7: identificador aleatorio para las rutas de administración (no es dato personal)
}


class AvisoPrivacidadTests(TestCase):
    def test_el_aviso_de_privacidad_es_publico_y_cubre_lo_que_exige_la_ley(self):
        respuesta = self.client.get(URL_AVISO)
        self.assertEqual(respuesta.status_code, 200)
        for seccion in [
            "Ley 1581 de 2012",
            "Responsable del tratamiento",
            "Datos que recolectamos",
            "Finalidad",
            "Tus derechos",
            "conocer, actualizar, rectificar",
            "revocar la autorización",
            "Cómo ejercer tus derechos",
        ]:
            with self.subTest(seccion=seccion):
                self.assertContains(respuesta, seccion)

    @override_settings(CORREO_CONTACTO_PRIVACIDAD="privacidad@amigo.edu.co")
    def test_el_aviso_indica_el_canal_de_contacto(self):
        self.assertContains(self.client.get(URL_AVISO), "privacidad@amigo.edu.co")

    def test_el_formulario_enlaza_el_aviso_y_la_casilla_no_viene_marcada(self):
        html = self.client.get(reverse("cuentas:registro")).content.decode()
        self.assertIn(f'href="{URL_AVISO}"', html)
        inicio = html.index('name="acepta_aviso"')
        etiqueta = html[html.rfind("<input", 0, inicio): html.index(">", inicio)]
        self.assertNotIn("checked", etiqueta)
        self.assertIn("required", etiqueta)

    def test_el_pie_de_pagina_enlaza_el_aviso_en_todas_las_paginas(self):
        self.assertContains(self.client.get(reverse("inicio")), f'href="{URL_AVISO}"')


class EvidenciaConsentimientoTests(TestCase):
    def test_se_guarda_la_version_y_la_fecha_en_que_se_acepto_el_aviso(self):
        antes = timezone.now()
        self.client.post(reverse("cuentas:registro"), datos_registro())
        usuario = Usuario.objects.get(correo_institucional=CORREO_COMPRADOR)
        self.assertTrue(usuario.aviso_privacidad_aceptado)
        self.assertEqual(usuario.aviso_privacidad_version, settings.AVISO_PRIVACIDAD_VERSION)
        self.assertGreaterEqual(usuario.aviso_privacidad_fecha, antes)

    def test_la_base_de_datos_impide_cuentas_sin_consentimiento(self):
        """Defensa en profundidad de RN-02, aunque alguien salte el formulario."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create(
                correo_institucional="sin.aviso@amigo.edu.co", rol="COMPRADOR",
                aviso_privacidad_aceptado=False,
            )


class DatosMinimosTests(TestCase):
    def test_el_modelo_de_usuario_solo_guarda_los_datos_previstos(self):
        campos = {campo.name for campo in Usuario._meta.concrete_fields}
        self.assertEqual(campos, CAMPOS_PERMITIDOS)

    def test_el_registro_no_pide_datos_fuera_de_la_matriz(self):
        html = self.client.get(reverse("cuentas:registro")).content.decode()
        for dato in ["nombre", "apellido", "telefono", "documento", "cedula", "direccion"]:
            with self.subTest(dato=dato):
                self.assertNotIn(f'name="{dato}', html)
