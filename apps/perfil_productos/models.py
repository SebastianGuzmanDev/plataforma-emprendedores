"""
Capa de datos del módulo E2 · Perfil y productos.

Clases del modelo de dominio (Entregable 2, 2.1): Categoria, Emprendimiento, Producto y
la enumeración EstadoProducto. Las existencias y el umbral de stock de Producto se
agregan con la Épica 5 (inventario).
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class TransicionNoPermitida(Exception):
    """El diagrama de estados ES1 no permite el cambio pedido."""


class EstadoProducto(models.TextChoices):
    DISPONIBLE = "DISPONIBLE", "Disponible"
    AGOTADO = "AGOTADO", "Agotado"
    DESACTIVADO = "DESACTIVADO", "Desactivado"


# RN-09: el catálogo muestra los disponibles y los agotados (con etiqueta).
ESTADOS_VISIBLES_EN_CATALOGO = (EstadoProducto.DISPONIBLE, EstadoProducto.AGOTADO)


class Categoria(models.Model):
    """Tipo de producto por el que se filtra el catálogo (comida, artesanías, etc.)."""

    nombre = models.CharField("nombre", max_length=40, unique=True)

    class Meta:
        verbose_name = "categoría"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def slug(self):
        """Identificador legible para el filtro del catálogo: «Artesanías» → «artesanias»."""
        return slugify(self.nombre)


class EmprendimientoQuerySet(models.QuerySet):
    def visibles_en_catalogo(self):
        """Perfiles que el catálogo (E3) muestra a los compradores."""
        return self.select_related("categoria")


class Emprendimiento(models.Model):
    """Perfil del emprendimiento (RF-05). Un emprendedor tiene como máximo uno (S-2)."""

    propietario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emprendimiento"
    )
    # CC-03: nombre con el que los compradores reconocen el emprendimiento.
    nombre = models.CharField("nombre", max_length=80)
    # S-1: la categoría pertenece al emprendimiento y clasifica a todos sus productos.
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="emprendimientos")
    descripcion = models.TextField("descripción", max_length=500)
    horarios = models.CharField("horarios", max_length=120)
    zona_entrega = models.CharField("zona de entrega", max_length=120)

    objects = EmprendimientoQuerySet.as_manager()

    class Meta:
        verbose_name = "emprendimiento"

    def __str__(self):
        return self.nombre


class ProductoQuerySet(models.QuerySet):
    def visibles_en_catalogo(self):
        """RN-09 · Contrato con el módulo Catálogo (E3): oculta los productos desactivados."""
        return self.filter(estado__in=ESTADOS_VISIBLES_EN_CATALOGO).select_related("emprendimiento__categoria")


class Producto(models.Model):
    """Producto del portafolio (RF-06 a RF-08) con su estado según el diagrama ES1."""

    # Código público no secuencial para las rutas: no revela cuántos productos hay.
    codigo = models.UUIDField("código", default=uuid.uuid4, unique=True, editable=False)
    emprendimiento = models.ForeignKey(Emprendimiento, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField("nombre", max_length=80)
    foto = models.ImageField("foto", upload_to="productos/")
    # CC-06: versión reducida para las tarjetas del catálogo (RNF-01).
    miniatura = models.ImageField("miniatura", upload_to="productos/miniaturas/", blank=True)
    # Pesos colombianos enteros; RN-07: nunca negativo.
    precio_referencia = models.DecimalField("precio de referencia", max_digits=10, decimal_places=0)
    estado = models.CharField(
        "estado", max_length=11, choices=EstadoProducto.choices, default=EstadoProducto.DISPONIBLE
    )

    objects = ProductoQuerySet.as_manager()

    class Meta:
        verbose_name = "producto"
        ordering = ["-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(precio_referencia__gte=0), name="producto_precio_no_negativo"),
            models.CheckConstraint(condition=models.Q(estado__in=EstadoProducto.values), name="producto_estado_valido"),
        ]

    def __str__(self):
        return self.nombre

    @property
    def url_miniatura(self):
        """Miniatura para las tarjetas; si aún no existe, la foto completa."""
        return self.miniatura.url if self.miniatura else self.foto.url

    @property
    def categoria(self):
        return self.emprendimiento.categoria

    @property
    def es_visible_en_catalogo(self):
        return self.estado in ESTADOS_VISIBLES_EN_CATALOGO

    # ------------------------------------------------------------ Diagrama ES1 (con CC-02)
    def validar_edicion(self):
        """ES1 + CC-02: se editan los productos disponibles y los agotados; editar no cambia el estado."""
        if self.estado == EstadoProducto.DESACTIVADO:
            raise TransicionNoPermitida("Este producto está desactivado: no se puede editar.")

    def marcar_agotado(self):
        """ES1: Disponible → Agotado."""
        if self.estado != EstadoProducto.DISPONIBLE:
            raise TransicionNoPermitida(
                f"No se puede marcar como agotado un producto {self.get_estado_display().lower()}."
            )
        self.estado = EstadoProducto.AGOTADO

    def marcar_disponible(self):
        """CC-02: Agotado → Disponible. Desactivado sigue siendo definitivo (protege la moderación de HU-22)."""
        if self.estado == EstadoProducto.DESACTIVADO:
            raise TransicionNoPermitida(
                "Un producto desactivado no se puede reactivar. Para volver a ofrecerlo, publícalo de nuevo."
            )
        if self.estado != EstadoProducto.AGOTADO:
            raise TransicionNoPermitida("Este producto ya está disponible.")
        self.estado = EstadoProducto.DISPONIBLE

    def desactivar(self):
        """ES1: Disponible → Desactivado y Agotado → Desactivado. Es definitivo."""
        if self.estado == EstadoProducto.DESACTIVADO:
            raise TransicionNoPermitida("Este producto ya está desactivado.")
        self.estado = EstadoProducto.DESACTIVADO
