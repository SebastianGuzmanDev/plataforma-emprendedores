"""
Modelo de datos de la Épica 6 · Finanzas (Entregable 2, diagrama de clases).

- Ingreso (monto, fecha) y Gasto (monto, categoría, fecha) pertenecen a un usuario.
- ResumenFinanciero es DERIVADO (supuesto S-7): no se almacena, se calcula en
  servicios.resumen_financiero a partir de Ingreso y Gasto.
- RN-13: el monto es mayor a 0 (también como restricción de la base de datos).
- RN-14: cada emprendedor ve solo sus datos financieros (consultas filtradas por propietario).
"""
import uuid

from django.conf import settings
from django.db import models


class CategoriaGasto(models.TextChoices):
    """HU-20: el gasto se clasifica en una categoría (lista cerrada, DT-E6-02)."""

    MATERIA_PRIMA = "MATERIA_PRIMA", "Materia prima"
    EMPAQUES = "EMPAQUES", "Empaques"
    TRANSPORTE = "TRANSPORTE", "Transporte"
    PUBLICIDAD = "PUBLICIDAD", "Publicidad"
    HERRAMIENTAS = "HERRAMIENTAS", "Herramientas y equipos"
    OTROS = "OTROS", "Otros"


class _Registro(models.Model):
    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    monto = models.DecimalField("monto", max_digits=12, decimal_places=0)
    fecha = models.DateField("fecha")

    class Meta:
        abstract = True
        ordering = ["-fecha", "-id"]


class Ingreso(_Registro):
    """HU-19 · RF-21."""

    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ingresos")

    class Meta(_Registro.Meta):
        verbose_name = "ingreso"
        indexes = [models.Index(fields=["propietario", "fecha"], name="ingreso_propietario_fecha")]
        constraints = [models.CheckConstraint(condition=models.Q(monto__gt=0), name="ingreso_monto_positivo")]

    def __str__(self):
        return f"Ingreso de {self.monto} ({self.fecha:%Y-%m-%d})"


class Gasto(_Registro):
    """HU-20 · RF-22."""

    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gastos")
    categoria = models.CharField("categoría", max_length=20, choices=CategoriaGasto.choices)

    class Meta(_Registro.Meta):
        verbose_name = "gasto"
        indexes = [models.Index(fields=["propietario", "fecha"], name="gasto_propietario_fecha")]
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name="gasto_monto_positivo"),
            models.CheckConstraint(condition=models.Q(categoria__in=CategoriaGasto.values), name="gasto_categoria_valida"),
        ]

    def __str__(self):
        return f"Gasto de {self.monto} en {self.get_categoria_display()} ({self.fecha:%Y-%m-%d})"
