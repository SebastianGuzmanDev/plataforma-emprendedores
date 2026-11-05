from django.conf import settings


def plataforma(request):
    """Datos comunes a todas las plantillas."""
    return {
        "NOMBRE_PLATAFORMA": settings.NOMBRE_PLATAFORMA,
        "CORREO_CONTACTO_PRIVACIDAD": settings.CORREO_CONTACTO_PRIVACIDAD,
        "AVISO_PRIVACIDAD_VERSION": settings.AVISO_PRIVACIDAD_VERSION,
    }
