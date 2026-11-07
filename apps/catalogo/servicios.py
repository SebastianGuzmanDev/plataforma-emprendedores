"""
Capa de lógica del módulo E3 · Catálogo. Nombres del diagrama de secuencia S4:
listarProductos() y filtrarPorCategoria(categoria). Consume el contrato RN-09 de E2.
"""
from django.db.models import Case, IntegerField, Value, When

from apps.perfil_productos.models import Categoria, EstadoProducto, Producto

from .busqueda import coincide


def listar_productos():
    """S4 · listarProductos(): productos no desactivados; primero los disponibles y luego los más recientes."""
    disponibles_primero = Case(
        When(estado=EstadoProducto.DISPONIBLE, then=Value(0)), default=Value(1), output_field=IntegerField()
    )
    return Producto.objects.visibles_en_catalogo().order_by(disponibles_primero, "-id")


def filtrar_por_categoria(productos, categoria):
    """S4 · filtrarPorCategoria(categoria): S-1, la categoría es la del emprendimiento."""
    return productos.filter(emprendimiento__categoria=categoria)


def buscar_por_palabra(productos, consulta):
    """CU-10 · RF-11: compara con el nombre del producto, sin distinguir mayúsculas ni tildes."""
    return [producto for producto in productos if coincide(producto.nombre, consulta)]


def categoria_por_slug(categorias, slug):
    return next((categoria for categoria in categorias if categoria.slug == slug), None)


def categorias():
    return list(Categoria.objects.all())
