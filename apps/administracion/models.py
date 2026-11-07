"""
Modelo de datos de la Épica 7 · Administración.

- `Usuario.activo` (E1) y `EstadoProducto.DESACTIVADO` (E2, ES1) ya existen en el modelo de
  dominio; esta épica agrega quién los cambia y por qué.
- CC-11: `Desactivacion` registra cada desactivación hecha por el administrador. Sirve a la
  vez de notificación al dueño del producto (HU-22 Esc. 1, punto B.2 resuelto: aviso dentro
  de la plataforma, porque D6 limita el correo a la recuperación de contraseña) y de
  trazabilidad de las acciones del administrador.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class MotivoDesactivacion(models.TextChoices):
    """Motivos por los que un producto o una cuenta "incumple las reglas" (HU-22)."""

    CONTENIDO_OFENSIVO = "CONTENIDO_OFENSIVO", "Contenido ofensivo o discriminatorio"
    PRODUCTO_PROHIBIDO = "PRODUCTO_PROHIBIDO", "Producto no permitido en la universidad"
    ENGANOSO = "ENGANOSO", "Información engañosa o fraudulenta"
    DATOS_PERSONALES = "DATOS_PERSONALES", "Expone datos personales de otras personas"
    SUPLANTACION = "SUPLANTACION", "Suplantación de identidad"
    OTRO = "OTRO", "Otro incumplimiento de las reglas"


class Desactivacion(models.Model):
    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    administrador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="desactivaciones_hechas"
    )
    producto = models.ForeignKey(
        "perfil_productos.Producto", on_delete=models.CASCADE, null=True, blank=True, related_name="desactivaciones"
    )
    cuenta = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="desactivaciones"
    )
    motivo = models.CharField("motivo", max_length=20, choices=MotivoDesactivacion.choices)
    detalle = models.CharField("detalle", max_length=300, blank=True)
    fecha = models.DateTimeField("fecha", default=timezone.now)
    # Notificación al dueño del producto: pendiente hasta que la ve.
    vista_en = models.DateTimeField("vista por el dueño", null=True, blank=True)
    # Corrección de un error del administrador (solo cuentas: un producto desactivado es definitivo, ES1).
    reactivada_en = models.DateTimeField("reactivada", null=True, blank=True)

    class Meta:
        verbose_name = "desactivación"
        verbose_name_plural = "desactivaciones"
        ordering = ["-fecha", "-id"]
        constraints = [
            # Cada registro es de un producto o de una cuenta, nunca de ambos.
            models.CheckConstraint(
                condition=(models.Q(producto__isnull=False, cuenta__isnull=True)
                           | models.Q(producto__isnull=True, cuenta__isnull=False)),
                name="desactivacion_de_producto_o_cuenta",
            ),
            models.CheckConstraint(
                condition=models.Q(motivo__in=MotivoDesactivacion.values), name="desactivacion_motivo_valido"
            ),
        ]

    def __str__(self):
        objetivo = self.producto or self.cuenta
        return f"Desactivación de {objetivo} ({self.get_motivo_display()})"
