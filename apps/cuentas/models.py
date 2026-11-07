"""
Capa de datos del módulo E1 · Cuentas y acceso.

Clase `Usuario` y enumeración `Rol` del modelo de dominio (Entregable 2, 2.1):
correoInstitucional, contrasenaCifrada, rol, avisoPrivacidadAceptado y activo.
"""
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class Rol(models.TextChoices):
    COMPRADOR = "COMPRADOR", "Comprador"
    EMPRENDEDOR = "EMPRENDEDOR", "Emprendedor"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


# RF-03: roles que una persona puede elegir al registrarse.
ROLES_AUTOREGISTRO = (Rol.COMPRADOR, Rol.EMPRENDEDOR)


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, correo):
        return self.get(correo_institucional=(correo or "").strip().lower())


class Usuario(AbstractBaseUser):
    """Cuenta de un miembro de la comunidad universitaria."""

    correo_institucional = models.EmailField("correo institucional", unique=True)
    rol = models.CharField("rol", max_length=13, choices=Rol.choices)
    aviso_privacidad_aceptado = models.BooleanField("aviso de privacidad aceptado", default=False)
    aviso_privacidad_version = models.CharField("versión del aviso aceptado", max_length=10, blank=True)
    aviso_privacidad_fecha = models.DateTimeField("fecha de aceptación del aviso", null=True, blank=True)
    activo = models.BooleanField("activo", default=True)
    # E7: identificador aleatorio para las rutas de administración; ninguna URL lleva el id
    # secuencial de una cuenta (RNF-05). No es un dato personal.
    codigo = models.UUIDField("código", default=uuid.uuid4, unique=True, editable=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "correo_institucional"
    EMAIL_FIELD = "correo_institucional"
    REQUIRED_FIELDS = ["rol"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            # RN-02: ninguna cuenta existe sin consentimiento (Ley 1581 de 2012).
            models.CheckConstraint(
                condition=models.Q(aviso_privacidad_aceptado=True),
                name="usuario_con_aviso_aceptado",
            ),
            # RF-03: solo los tres roles definidos.
            models.CheckConstraint(
                condition=models.Q(rol__in=Rol.values), name="usuario_rol_valido"
            ),
            # RN-01: un correo, una cuenta, sin importar mayúsculas.
            models.UniqueConstraint(Lower("correo_institucional"), name="usuario_correo_unico_ci"),
        ]

    def __str__(self):
        return self.correo_institucional

    def save(self, *args, **kwargs):
        self.correo_institucional = (self.correo_institucional or "").strip().lower()
        super().save(*args, **kwargs)

    # Django consulta `is_active` para autenticar y para mantener la sesión: una
    # cuenta desactivada (E7, HU-22) pierde el acceso inmediatamente.
    @property
    def is_active(self):
        return self.activo

    @property
    def es_emprendedor(self):
        return self.rol == Rol.EMPRENDEDOR

    @property
    def es_administrador(self):
        return self.rol == Rol.ADMINISTRADOR
