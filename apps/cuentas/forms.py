"""
Formularios del módulo E1 (capa de presentación). Validan los datos de entrada
aplicando las reglas de `reglas.py`; la creación de la cuenta la hace `servicios.py`.
"""
from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

from .models import ROLES_AUTOREGISTRO, Rol, Usuario
from .reglas import es_correo_institucional, normalizar_correo, rol_autoregistrable

DESCRIPCION_ROLES = {
    Rol.COMPRADOR: "Estudiante, docente, personal administrativo o directivo que quiere ver "
    "lo que se vende en el campus y contactar a los emprendedores.",
    Rol.EMPRENDEDOR: "Miembro de la comunidad que publica su portafolio y lleva su "
    "inventario y sus finanzas.",
}


def texto_dominios():
    return " o ".join(f"@{dominio}" for dominio in settings.DOMINIOS_INSTITUCIONALES)


class RegistroForm(forms.Form):
    """HU-01 · RF-01, RF-03, RNF-06."""

    correo_institucional = forms.EmailField(
        label="Correo institucional",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
        error_messages={"required": "Escribe tu correo institucional.",
                        "invalid": "Escribe un correo válido."},
    )
    contrasena = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        error_messages={"required": "Escribe una contraseña."},
    )
    contrasena_confirmacion = forms.CharField(
        label="Confirma la contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        error_messages={"required": "Confirma tu contraseña."},
    )
    rol = forms.ChoiceField(
        label="¿Cómo vas a usar la plataforma?",
        choices=[(rol.value, rol.label) for rol in ROLES_AUTOREGISTRO],
        widget=forms.RadioSelect,
        error_messages={"required": "Elige tu rol: comprador o emprendedor.",
                        "invalid_choice": "Elige tu rol: comprador o emprendedor."},
    )
    acepta_aviso = forms.BooleanField(
        label="He leído y acepto el aviso de privacidad y autorizo el tratamiento de mis datos personales.",
        error_messages={"required": "Debes aceptar el aviso de privacidad para crear tu cuenta."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["correo_institucional"].help_text = f"Debe terminar en {texto_dominios()}."
        self.fields["contrasena"].help_text = password_validation.password_validators_help_text_html()

    def clean_correo_institucional(self):
        correo = normalizar_correo(self.cleaned_data["correo_institucional"])
        if not es_correo_institucional(correo):
            raise forms.ValidationError(
                f"Usa tu correo institucional ({texto_dominios()}).", code="no_institucional"
            )
        if Usuario.objects.filter(correo_institucional=correo).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo. Inicia sesión o recupera tu contraseña.",
                code="correo_repetido",
            )
        return correo

    def clean_rol(self):
        rol = self.cleaned_data["rol"]
        if not rol_autoregistrable(rol):
            raise forms.ValidationError("Elige tu rol: comprador o emprendedor.", code="rol_invalido")
        return rol

    def clean(self):
        datos = super().clean()
        contrasena = datos.get("contrasena")
        confirmacion = datos.get("contrasena_confirmacion")
        if contrasena and confirmacion and contrasena != confirmacion:
            self.add_error("contrasena_confirmacion", "Las contraseñas no coinciden.")
        if contrasena:
            candidato = Usuario(correo_institucional=datos.get("correo_institucional", ""))
            try:
                password_validation.validate_password(contrasena, candidato)
            except forms.ValidationError as error:
                self.add_error("contrasena", error)
        return datos

    def descripcion_rol(self, valor):
        return DESCRIPCION_ROLES.get(valor, "")


class IngresoForm(AuthenticationForm):
    """HU-02 · RF-02. Mensaje único que no revela si el correo existe o está desactivado."""

    error_messages = {
        "invalid_login": "Correo o contraseña incorrectos. Revisa los datos e inténtalo de nuevo.",
        "inactive": "Correo o contraseña incorrectos. Revisa los datos e inténtalo de nuevo.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Correo institucional"
        self.fields["username"].widget = forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})
        self.fields["username"].error_messages["required"] = "Escribe tu correo institucional."
        self.fields["password"].label = "Contraseña"
        self.fields["password"].error_messages["required"] = "Escribe tu contraseña."

    def clean_username(self):
        return normalizar_correo(self.cleaned_data.get("username"))


class RecuperarContrasenaForm(PasswordResetForm):
    """HU-03 · RF-04. Solo envía el enlace a cuentas activas; la respuesta es siempre la misma."""

    email = forms.EmailField(
        label="Correo institucional",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
        error_messages={"required": "Escribe tu correo institucional.", "invalid": "Escribe un correo válido."},
    )

    def get_users(self, email):
        return (
            usuario
            for usuario in Usuario.objects.filter(
                correo_institucional=normalizar_correo(email), activo=True
            )
            if usuario.has_usable_password()
        )


class RestablecerContrasenaForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirma la nueva contraseña"
