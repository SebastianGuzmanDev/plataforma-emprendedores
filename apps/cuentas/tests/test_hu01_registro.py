"""
HU-01 · Registrarme eligiendo mi rol (Must) · RF-01, RF-03, RNF-06 · CU-01.

Pruebas de INTEGRACIÓN: recorren interfaz web → módulo Cuentas → base de datos,
como en el diagrama de secuencia S1 del Entregable 2.
"""
from django.contrib.auth import get_user
from django.test import TestCase
from django.urls import reverse

from apps.cuentas.models import Rol, Usuario

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, crear_usuario, datos_registro

URL_REGISTRO = reverse("cuentas:registro")


class HU01RegistroTests(TestCase):
    def test_cp_01_1_registro_exitoso_crea_la_cuenta_con_el_rol_elegido(self):
        """CP-01.1 · Esc. 1: correo institucional sin cuenta + rol + aviso aceptado → cuenta creada."""
        for indice, rol in enumerate([Rol.COMPRADOR, Rol.EMPRENDEDOR]):
            with self.subTest(rol=rol):
                correo = f"persona{indice}@amigo.edu.co"
                respuesta = self.client.post(
                    URL_REGISTRO, datos_registro(correo_institucional=correo, rol=rol), follow=True
                )
                self.assertRedirects(respuesta, reverse("cuentas:ingresar"))
                self.assertContains(respuesta, "Tu cuenta fue creada")
                usuario = Usuario.objects.get(correo_institucional=correo)
                self.assertEqual(usuario.rol, rol)
                self.assertTrue(usuario.activo)
                # A1: tras crear la cuenta, la persona ingresa con su correo y contraseña.
                self.assertTrue(self.client.login(correo_institucional=correo, password=CONTRASENA_VALIDA))
                self.client.logout()

    def test_cp_01_1_el_correo_se_guarda_normalizado(self):
        self.client.post(URL_REGISTRO, datos_registro(correo_institucional="  Ana.Perez@AMIGO.edu.co "))
        self.assertTrue(Usuario.objects.filter(correo_institucional=CORREO_COMPRADOR).exists())

    def test_cp_01_1_registrarse_no_inicia_sesion_automaticamente(self):
        respuesta = self.client.post(URL_REGISTRO, datos_registro(), follow=True)
        self.assertFalse(get_user(respuesta.wsgi_request).is_authenticated)

    def test_cp_01_2_correo_repetido_rechaza_el_registro_e_informa(self):
        """CP-01.2 · Esc. 2: el correo ya tiene cuenta → se rechaza e informa que ya existe."""
        crear_usuario(correo=CORREO_COMPRADOR)
        for variante in [CORREO_COMPRADOR, CORREO_COMPRADOR.upper()]:
            with self.subTest(correo=variante):
                respuesta = self.client.post(URL_REGISTRO, datos_registro(correo_institucional=variante))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Ya existe una cuenta con este correo")
                self.assertEqual(Usuario.objects.count(), 1)

    def test_cp_01_3_sin_consentimiento_no_se_crea_la_cuenta(self):
        """CP-01.3 · Esc. 3: sin aceptar el aviso de privacidad → no se crea y se pide aceptarlo."""
        respuesta = self.client.post(URL_REGISTRO, datos_registro(acepta_aviso=None))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debes aceptar el aviso de privacidad")
        self.assertFalse(Usuario.objects.exists())

    def test_cp_01_4_correo_no_institucional_rechaza_el_registro(self):
        """CP-01.4 · Esc. 4: correo no institucional → se rechaza y se pide uno institucional."""
        respuesta = self.client.post(URL_REGISTRO, datos_registro(correo_institucional="ana@gmail.com"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Usa tu correo institucional")
        self.assertContains(respuesta, "@amigo.edu.co")
        self.assertFalse(Usuario.objects.exists())

    def test_los_datos_validos_se_conservan_al_mostrar_un_error(self):
        respuesta = self.client.post(URL_REGISTRO, datos_registro(acepta_aviso=None))
        self.assertContains(respuesta, f'value="{CORREO_COMPRADOR}"')
        self.assertNotContains(respuesta, CONTRASENA_VALIDA)


class HU01RolTests(TestCase):
    """RF-03: rol elegido al registrarse; el de administrador se asigna internamente."""

    def test_el_formulario_solo_ofrece_comprador_y_emprendedor(self):
        respuesta = self.client.get(URL_REGISTRO)
        self.assertContains(respuesta, 'value="COMPRADOR"')
        self.assertContains(respuesta, 'value="EMPRENDEDOR"')
        self.assertNotContains(respuesta, 'value="ADMINISTRADOR"')

    def test_enviar_rol_administrador_manipulando_el_formulario_no_crea_cuenta(self):
        respuesta = self.client.post(URL_REGISTRO, datos_registro(rol=Rol.ADMINISTRADOR))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.exists())

    def test_sin_rol_no_se_crea_la_cuenta(self):
        respuesta = self.client.post(URL_REGISTRO, datos_registro(rol=None))
        self.assertContains(respuesta, "Elige tu rol")
        self.assertFalse(Usuario.objects.exists())


class HU01PaginaRegistroTests(TestCase):
    def test_la_pagina_de_registro_responde(self):
        respuesta = self.client.get(URL_REGISTRO)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, "cuentas/registro.html")

    def test_la_politica_de_contrasena_se_muestra_como_lista_legible(self):
        """Regresión: la ayuda no debe mostrarse como una lista de Python ['...']."""
        html = self.client.get(URL_REGISTRO).content.decode()
        self.assertNotIn("[&#x27;", html)
        self.assertRegex(html, r'id="id_contrasena_helptext"><ul><li>')

    def test_un_usuario_con_sesion_es_enviado_a_su_cuenta(self):
        crear_usuario()
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)
        respuesta = self.client.get(URL_REGISTRO)
        self.assertRedirects(respuesta, reverse("cuentas:mi_cuenta"))
