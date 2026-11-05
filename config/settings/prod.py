"""
Entorno de pruebas desplegado y de producción.

RNF-04: toda la comunicación viaja por HTTPS. Las cookies de sesión y CSRF solo
se envían por HTTPS y el navegador recuerda usar HTTPS (HSTS).
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import _lista_desde_entorno

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "Define DJANGO_SECRET_KEY con al menos 50 caracteres aleatorios."
    )

ALLOWED_HOSTS = _lista_desde_entorno("DJANGO_ALLOWED_HOSTS", "")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("Define DJANGO_ALLOWED_HOSTS (separados por coma).")

# HTTPS obligatorio (RNF-04)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if os.environ.get("DJANGO_DETRAS_DE_PROXY") == "1":
    # La plataforma de despliegue termina TLS y avisa con X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Servicio de correo para la recuperación de contraseña (D6, HU-03)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
