"""
Pruebas UNITARIAS de las reglas de negocio de la Épica 1 (RN-01 a RN-03).

Nivel U del plan de pruebas (Entregable 2, 4.1.3): la regla se verifica sola,
sin interfaz ni peticiones HTTP.
"""
from django.test import SimpleTestCase, TestCase, override_settings

from apps.cuentas.forms import RegistroForm
from apps.cuentas.models import Rol, Usuario
from apps.cuentas.reglas import es_correo_institucional, normalizar_correo, rol_autoregistrable

from .utilidades import CORREO_COMPRADOR, crear_usuario, datos_registro


class ReglaCorreoInstitucionalTests(SimpleTestCase):
    """RN-01 · RF-01: el correo de registro debe ser institucional."""

    def test_rn01_acepta_correo_del_dominio_institucional(self):
        self.assertTrue(es_correo_institucional("ana.perez@amigo.edu.co"))

    def test_rn01_no_distingue_mayusculas_ni_espacios(self):
        self.assertTrue(es_correo_institucional("  Ana.Perez@AMIGO.EDU.CO "))

    def test_rn01_rechaza_correos_de_otros_dominios(self):
        for correo in [
            "ana@gmail.com",
            "ana@hotmail.com",
            "ana@amigo.edu.co.dominio-falso.com",
            "ana@falsoamigo.edu.co",
            "ana@sub.amigo.edu.co",
            "ana@amigo.edu",
        ]:
            with self.subTest(correo=correo):
                self.assertFalse(es_correo_institucional(correo))

    def test_rn01_rechaza_valores_que_no_son_correo(self):
        for valor in ["", "   ", "amigo.edu.co", "ana@", "@amigo.edu.co", None]:
            with self.subTest(valor=valor):
                self.assertFalse(es_correo_institucional(valor))

    @override_settings(DOMINIOS_INSTITUCIONALES=["amigo.edu.co", "est.amigo.edu.co"])
    def test_rn01_los_dominios_se_configuran_sin_cambiar_codigo(self):
        self.assertTrue(es_correo_institucional("ana@est.amigo.edu.co"))

    def test_normaliza_correo_a_minusculas_sin_espacios(self):
        self.assertEqual(normalizar_correo("  Ana.Perez@Amigo.EDU.co "), "ana.perez@amigo.edu.co")


class ReglaRolTests(SimpleTestCase):
    """RN-03 · RF-03: al registrarse solo se elige comprador o emprendedor."""

    def test_rn03_comprador_y_emprendedor_son_autoregistrables(self):
        self.assertTrue(rol_autoregistrable(Rol.COMPRADOR))
        self.assertTrue(rol_autoregistrable(Rol.EMPRENDEDOR))

    def test_rn03_administrador_no_es_autoregistrable(self):
        self.assertFalse(rol_autoregistrable(Rol.ADMINISTRADOR))

    def test_rn03_rol_desconocido_no_es_autoregistrable(self):
        self.assertFalse(rol_autoregistrable("SUPERUSUARIO"))


class FormularioRegistroUnitTests(TestCase):
    """Validaciones del formulario de registro sin pasar por HTTP."""

    def test_cp_01_3_sin_consentimiento_el_formulario_es_invalido(self):
        """CP-01.3 · RN-02: sin aceptar el aviso no se crea la cuenta y se pide aceptarlo."""
        form = RegistroForm(data=datos_registro(acepta_aviso=None))
        self.assertFalse(form.is_valid())
        self.assertIn("acepta_aviso", form.errors)
        self.assertIn("aviso de privacidad", form.errors["acepta_aviso"][0])

    def test_cp_01_4_correo_no_institucional_hace_invalido_el_formulario(self):
        """CP-01.4 · RN-01: se rechaza el correo y se pide uno institucional."""
        form = RegistroForm(data=datos_registro(correo_institucional="ana@gmail.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("correo institucional", form.errors["correo_institucional"][0])

    def test_correo_repetido_se_detecta_sin_importar_mayusculas(self):
        """RN-01: el correo no debe tener ya una cuenta."""
        crear_usuario(correo=CORREO_COMPRADOR)
        form = RegistroForm(data=datos_registro(correo_institucional=CORREO_COMPRADOR.upper()))
        self.assertFalse(form.is_valid())
        self.assertIn("Ya existe una cuenta", form.errors["correo_institucional"][0])

    def test_rol_administrador_no_es_una_opcion_valida(self):
        """RN-03: el rol de administrador no se puede elegir al registrarse."""
        form = RegistroForm(data=datos_registro(rol=Rol.ADMINISTRADOR))
        self.assertFalse(form.is_valid())
        self.assertIn("rol", form.errors)

    def test_las_contrasenas_deben_coincidir(self):
        form = RegistroForm(data=datos_registro(contrasena_confirmacion="Otra-Clave-2026"))
        self.assertFalse(form.is_valid())
        self.assertIn("contrasena_confirmacion", form.errors)

    def test_la_contrasena_debe_cumplir_la_politica(self):
        for debil in ["1234", "12345678", "password", "anaperez"]:
            with self.subTest(contrasena=debil):
                form = RegistroForm(
                    data=datos_registro(contrasena=debil, contrasena_confirmacion=debil)
                )
                self.assertFalse(form.is_valid())
                self.assertIn("contrasena", form.errors)

    def test_formulario_valido_no_crea_cuenta_hasta_guardar(self):
        form = RegistroForm(data=datos_registro())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(Usuario.objects.count(), 0)
