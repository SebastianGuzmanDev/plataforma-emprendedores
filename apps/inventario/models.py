"""
Capa de datos del módulo E5 · Inventario. Clases del modelo de dominio (Entregable 2, 2.1):
MovimientoInventario (tipo, cantidad, fecha), la enumeración TipoMovimiento e Insumo
(nombre, cantidad, costo), asociado al usuario emprendedor (supuesto S-3).
Las existencias y el umbral son atributos de Producto (módulo E2).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class TipoMovimiento(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SALIDA = "SALIDA", "Salida"


class MovimientoInventario(models.Model):
    """Entrada o salida de existencias de un producto (HU-16)."""

    producto = models.ForeignKey("perfil_productos.Producto", on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField("tipo", max_length=7, choices=TipoMovimiento.choices)
    cantidad = models.PositiveIntegerField("cantidad")
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"
        ordering = ["-fecha", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="movimiento_cantidad_positiva"),
            models.CheckConstraint(condition=models.Q(tipo__in=TipoMovimiento.values), name="movimiento_tipo_valido"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} · {self.producto}"


class Insumo(models.Model):
    """Materia prima con su cantidad y su costo (HU-18 · RN-12)."""

    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="insumos")
    nombre = models.CharField("nombre", max_length=80)
    cantidad = models.DecimalField("cantidad", max_digits=10, decimal_places=3)
    costo = models.DecimalField("costo", max_digits=12, decimal_places=0)

    class Meta:
        verbose_name = "insumo"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name="insumo_cantidad_positiva"),
            models.CheckConstraint(condition=models.Q(costo__gte=0), name="insumo_costo_no_negativo"),
        ]

    def __str__(self):
        return self.nombre
