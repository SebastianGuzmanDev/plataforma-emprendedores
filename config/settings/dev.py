"""Entorno de desarrollo local y de pruebas automatizadas."""
from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = "solo-para-desarrollo-no-usar-en-produccion-1f7c9a"  # noqa: S105
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

# Los correos de recuperación se muestran en la consola en lugar de enviarse.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
