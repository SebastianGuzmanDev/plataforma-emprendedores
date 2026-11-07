"""
Capa de datos del módulo E4 · Contacto por chat. Clases del modelo de dominio
(Entregable 2, 2.1): Conversacion (comprador, emprendedor y producto de origen) y Mensaje
(contenido, fecha de envío, autor e indicador de lectura).
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .reglas import LONGITUD_MAXIMA_MENSAJE


class Conversacion(models.Model):
    """Conversación entre un comprador y un emprendedor, originada desde un producto (HU-11)."""

    codigo = models.UUIDField("código", default=uuid.uuid4, unique=True, editable=False)
    comprador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversaciones_como_comprador"
    )
    emprendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversaciones_como_emprendedor"
    )
    producto = models.ForeignKey(
        "perfil_productos.Producto", on_delete=models.CASCADE, related_name="conversaciones"
    )
    creada = models.DateTimeField("creada", default=timezone.now)

    class Meta:
        verbose_name = "conversación"
        verbose_name_plural = "conversaciones"
        constraints = [
            # Volver a pulsar «Contactar» en el mismo producto reabre la misma conversación.
            models.UniqueConstraint(fields=["comprador", "producto"], name="conversacion_unica_por_producto"),
            # RN-18: nadie conversa consigo mismo.
            models.CheckConstraint(
                condition=~models.Q(comprador=models.F("emprendedor")), name="conversacion_sin_contacto_propio"
            ),
        ]

    def __str__(self):
        return f"Conversación sobre {self.producto}"

    def participa(self, usuario):
        return usuario.is_authenticated and usuario.pk in (self.comprador_id, self.emprendedor_id)

    @property
    def alias_comprador(self):
        """Identifica al comprador ante el emprendedor sin mostrar su correo (RNF-06)."""
        return self.codigo.hex[:4].upper()

    def otra_persona(self, usuario):
        return self.emprendedor if usuario.pk == self.comprador_id else self.comprador

    def nombre_de_la_otra_persona(self, usuario):
        if usuario.pk == self.comprador_id:
            return self.producto.emprendimiento.nombre
        return f"Comprador {self.alias_comprador}"

    def ultimo_mensaje(self):
        return self.mensajes.order_by("-fecha_envio", "-id").first()


class Mensaje(models.Model):
    """Mensaje de una conversación (HU-12). Se guarda en la base de datos (RNF-10)."""

    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mensajes")
    contenido = models.TextField("contenido", max_length=LONGITUD_MAXIMA_MENSAJE)
    fecha_envio = models.DateTimeField("fecha de envío", default=timezone.now)
    leido = models.BooleanField("leído", default=False)

    class Meta:
        verbose_name = "mensaje"
        ordering = ["fecha_envio", "id"]
        constraints = [
            # RN-16: defensa en profundidad, aunque alguien salte el formulario.
            models.CheckConstraint(condition=~models.Q(contenido=""), name="mensaje_no_vacio"),
        ]

    def __str__(self):
        return self.contenido[:40]

    def marcar_leido(self):
        self.leido = True
        self.save(update_fields=["leido"])
