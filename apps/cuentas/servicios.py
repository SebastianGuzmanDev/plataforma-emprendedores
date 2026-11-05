"""
Capa de lógica de negocio del módulo E1: casos de uso CU-01 (registro).

La vista recibe un formulario ya validado y delega aquí la creación de la cuenta.
Las reglas se vuelven a comprobar para que ningún otro punto de entrada
(comandos, futuras épicas) pueda saltarlas.
"""
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Usuario
from .reglas import es_correo_institucional, normalizar_correo, rol_autoregistrable


class RegistroRechazado(Exception):
    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def registrar_usuario(*, correo, contrasena, rol, acepta_aviso):
    """CU-01 · Crea la cuenta con el rol elegido y la evidencia del consentimiento."""
    correo = normalizar_correo(correo)
    if not es_correo_institucional(correo):
        raise RegistroRechazado("no_institucional", "El correo no es institucional.")
    if not acepta_aviso:
        raise RegistroRechazado("sin_consentimiento", "Falta aceptar el aviso de privacidad.")
    if not rol_autoregistrable(rol):
        raise RegistroRechazado("rol_invalido", "El rol no se puede elegir al registrarse.")

    usuario = Usuario(
        correo_institucional=correo,
        rol=rol,
        aviso_privacidad_aceptado=True,
        aviso_privacidad_version=settings.AVISO_PRIVACIDAD_VERSION,
        aviso_privacidad_fecha=timezone.now(),
    )
    usuario.set_password(contrasena)
    try:
        with transaction.atomic():
            usuario.save()
    except IntegrityError as error:  # dos registros simultáneos con el mismo correo
        raise RegistroRechazado("correo_repetido", "Ya existe una cuenta con este correo.") from error
    return usuario
