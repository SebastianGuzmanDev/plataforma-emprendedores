"""
Reglas de negocio de la Épica 1 (Entregable 2, sección 2.1.3).

Funciones puras, sin acceso a la base de datos ni a la interfaz, para poder
probarlas de forma unitaria.

- RN-01: el correo de registro debe ser institucional y no tener ya una cuenta.
- RN-02: no se crea la cuenta si no se acepta el aviso de privacidad.
- RN-03: el rol (comprador o emprendedor) se elige al registrarse; el de
  administrador se asigna internamente.
- RN-04: las contraseñas se almacenan cifradas (ver PASSWORD_HASHERS).
"""
from django.conf import settings

from .models import ROLES_AUTOREGISTRO


def normalizar_correo(correo):
    """Quita espacios y pasa a minúsculas para comparar correos sin ambigüedad."""
    return (correo or "").strip().lower()


def es_correo_institucional(correo):
    """RN-01: el dominio del correo debe coincidir exactamente con uno institucional."""
    correo = normalizar_correo(correo)
    usuario, arroba, dominio = correo.rpartition("@")
    if not arroba or not usuario or not dominio:
        return False
    return dominio in settings.DOMINIOS_INSTITUCIONALES


def rol_autoregistrable(rol):
    """RN-03: solo comprador o emprendedor se eligen en el registro."""
    return rol in ROLES_AUTOREGISTRO
