"""Datos y ayudas compartidas por las pruebas de la Épica 1."""
from django.utils import timezone

from apps.cuentas.models import Rol, Usuario

CONTRASENA_VALIDA = "Clave-Segura-2026"
CORREO_COMPRADOR = "ana.perez@amigo.edu.co"
CORREO_EMPRENDEDOR = "luis.gomez@amigo.edu.co"
CORREO_ADMIN = "admin.plataforma@amigo.edu.co"


def crear_usuario(correo=CORREO_COMPRADOR, rol=Rol.COMPRADOR, contrasena=CONTRASENA_VALIDA, activo=True):
    """Crea un usuario ya registrado (con el aviso de privacidad aceptado)."""
    usuario = Usuario(
        correo_institucional=correo,
        rol=rol,
        aviso_privacidad_aceptado=True,
        aviso_privacidad_version="1.0",
        aviso_privacidad_fecha=timezone.now(),
        activo=activo,
    )
    usuario.set_password(contrasena)
    usuario.save()
    return usuario


def datos_registro(**cambios):
    """Formulario de registro válido; `cambios` sobrescribe o elimina (valor None) campos."""
    datos = {
        "correo_institucional": CORREO_COMPRADOR,
        "contrasena": CONTRASENA_VALIDA,
        "contrasena_confirmacion": CONTRASENA_VALIDA,
        "rol": Rol.COMPRADOR,
        "acepta_aviso": "on",
    }
    for campo, valor in cambios.items():
        if valor is None:
            datos.pop(campo, None)
        else:
            datos[campo] = valor
    return datos
