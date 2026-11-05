"""
RNF-09 · Escalabilidad (Should), parte de cuentas: la plataforma soporta 100 usuarios
registrados. La parte de 300 productos se verifica en la Épica 2.
"""
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cuentas.models import Rol, Usuario

from .utilidades import CONTRASENA_VALIDA, datos_registro


class CienUsuariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        hash_comun = make_password(CONTRASENA_VALIDA)
        Usuario.objects.bulk_create(
            Usuario(
                correo_institucional=f"persona{i:03d}@amigo.edu.co",
                rol=Rol.EMPRENDEDOR if i % 3 == 0 else Rol.COMPRADOR,
                password=hash_comun,
                aviso_privacidad_aceptado=True,
                aviso_privacidad_version="1.0",
                aviso_privacidad_fecha=timezone.now(),
            )
            for i in range(100)
        )

    def test_con_100_usuarios_el_registro_y_el_ingreso_siguen_funcionando(self):
        self.assertEqual(Usuario.objects.count(), 100)
        self.client.post(reverse("cuentas:registro"), datos_registro(correo_institucional="nuevo@amigo.edu.co"))
        self.assertEqual(Usuario.objects.count(), 101)
        respuesta = self.client.post(
            reverse("cuentas:ingresar"),
            {"username": "persona099@amigo.edu.co", "password": CONTRASENA_VALIDA},
        )
        self.assertRedirects(respuesta, reverse("cuentas:mi_cuenta"))

    def test_con_100_usuarios_se_sigue_impidiendo_el_correo_repetido(self):
        respuesta = self.client.post(
            reverse("cuentas:registro"), datos_registro(correo_institucional="persona050@amigo.edu.co")
        )
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")
        self.assertEqual(Usuario.objects.count(), 100)
