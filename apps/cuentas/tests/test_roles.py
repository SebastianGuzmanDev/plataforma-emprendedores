"""
Control de acceso por rol (componente transversal de E1, RF-03 · RN-03).

Las épicas E2 a E7 reutilizan `rol_requerido` para proteger sus pantallas.
"""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from apps.cuentas.models import Rol, Usuario

from .utilidades import (
    CONTRASENA_VALIDA,
    CORREO_ADMIN,
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR,
    crear_usuario,
)

URL_PANEL_EMPRENDEDOR = reverse("cuentas:panel_emprendedor")
URL_PANEL_ADMIN = reverse("cuentas:panel_administracion")


class AccesoPorRolTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        crear_usuario(correo=CORREO_COMPRADOR, rol=Rol.COMPRADOR)
        crear_usuario(correo=CORREO_EMPRENDEDOR, rol=Rol.EMPRENDEDOR)
        crear_usuario(correo=CORREO_ADMIN, rol=Rol.ADMINISTRADOR)

    def entrar(self, correo):
        self.assertTrue(self.client.login(correo_institucional=correo, password=CONTRASENA_VALIDA))

    def test_el_panel_del_emprendedor_solo_lo_abre_un_emprendedor(self):
        self.entrar(CORREO_EMPRENDEDOR)
        self.assertEqual(self.client.get(URL_PANEL_EMPRENDEDOR).status_code, 200)

    def test_un_comprador_recibe_acceso_denegado_en_el_panel_del_emprendedor(self):
        self.entrar(CORREO_COMPRADOR)
        respuesta = self.client.get(URL_PANEL_EMPRENDEDOR)
        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(respuesta, "No tienes permiso", status_code=403)

    def test_el_panel_de_administracion_solo_lo_abre_un_administrador(self):
        self.entrar(CORREO_ADMIN)
        self.assertEqual(self.client.get(URL_PANEL_ADMIN).status_code, 200)
        for correo in [CORREO_COMPRADOR, CORREO_EMPRENDEDOR]:
            with self.subTest(correo=correo):
                self.client.logout()
                self.entrar(correo)
                self.assertEqual(self.client.get(URL_PANEL_ADMIN).status_code, 403)

    def test_sin_sesion_los_paneles_piden_iniciar_sesion(self):
        for url in [URL_PANEL_EMPRENDEDOR, URL_PANEL_ADMIN]:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertRedirects(respuesta, f"{reverse('cuentas:ingresar')}?next={url}")

    def test_mi_cuenta_muestra_el_rol_del_usuario(self):
        self.entrar(CORREO_EMPRENDEDOR)
        self.assertContains(self.client.get(reverse("cuentas:mi_cuenta")), "Emprendedor")


class AsignacionInternaAdministradorTests(TestCase):
    """RF-03: el rol de administrador se asigna internamente (comando de gestión)."""

    def test_promover_administrador_cambia_el_rol(self):
        usuario = crear_usuario(correo=CORREO_EMPRENDEDOR, rol=Rol.EMPRENDEDOR)
        salida = StringIO()
        call_command("promover_administrador", CORREO_EMPRENDEDOR.upper(), stdout=salida)
        usuario.refresh_from_db()
        self.assertEqual(usuario.rol, Rol.ADMINISTRADOR)
        self.assertIn("ahora es administrador", salida.getvalue())

    def test_promover_un_correo_inexistente_falla_sin_crear_cuentas(self):
        with self.assertRaises(CommandError):
            call_command("promover_administrador", "nadie@amigo.edu.co", stdout=StringIO())
        self.assertFalse(Usuario.objects.exists())
