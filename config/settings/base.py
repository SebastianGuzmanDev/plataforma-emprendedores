"""
Configuración común de la Plataforma de Emprendedores (MVP).

Arquitectura (Entregable 2, sección 2.2): una sola aplicación web modular con
tres capas y un módulo de lógica por épica. Este archivo reúne lo que comparten
los entornos de desarrollo, pruebas y producción.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _lista_desde_entorno(nombre, por_defecto):
    valor = os.environ.get(nombre, por_defecto)
    return [parte.strip().lower() for parte in valor.split(",") if parte.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = []

# ---------------------------------------------------------------------------
# Módulos (un módulo por épica, D2 del Entregable 2)
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # E1 · Cuentas y acceso
    "apps.cuentas",
    # E2 · Perfil y productos
    "apps.perfil_productos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # RNF-05 / HU-02 Esc. 3: ninguna página vista con sesión queda en caché.
    "apps.cuentas.middleware.SinCacheParaSesionesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.cuentas.context_processors.plataforma",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", BASE_DIR / "db.sqlite3"),
    }
}

# ---------------------------------------------------------------------------
# E1 · Cuentas y acceso
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "cuentas.Usuario"
LOGIN_URL = "cuentas:ingresar"
LOGIN_REDIRECT_URL = "cuentas:mi_cuenta"

# RNF-04: contraseñas con hash Argon2id (sal aleatoria por usuario). PBKDF2 queda
# solo como respaldo para verificar hashes antiguos.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("correo_institucional",)},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# RF-01 / RN-01: dominios aceptados como correo institucional.
DOMINIOS_INSTITUCIONALES = _lista_desde_entorno("DOMINIOS_INSTITUCIONALES", "amigo.edu.co")

# RNF-06 (Ley 1581 de 2012): versión del aviso que acepta cada titular.
AVISO_PRIVACIDAD_VERSION = "1.1"  # 1.1 (E2): perfil y productos publicados en el catálogo
CORREO_CONTACTO_PRIVACIDAD = os.environ.get(
    "CORREO_CONTACTO_PRIVACIDAD", "privacidad@por-definir.amigo.edu.co"
)

# RF-04 / HU-03: el enlace de recuperación vence en 1 hora.
PASSWORD_RESET_TIMEOUT = 60 * 60

NOMBRE_PLATAFORMA = "Plataforma de Emprendedores"

# ---------------------------------------------------------------------------
# Sesión y cookies (RNF-04)
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 horas
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Idioma, zona horaria y archivos estáticos
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-co"
LANGUAGES = [("es-co", "Español (Colombia)")]
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# E2 · Almacenamiento de fotos (D5: separado de la base de datos)
# ---------------------------------------------------------------------------
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
FOTO_LIMITE_MB = 5  # RF-06 · RN-07
FOTO_LADO_MAXIMO_PX = 1600

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-responder@amigo.edu.co")
