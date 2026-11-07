"""Ayudas de las pruebas de la Épica 3 (reutiliza las de E1 y E2)."""
from django.urls import reverse

from apps.perfil_productos.models import Categoria, Emprendimiento, EstadoProducto, Producto
from apps.perfil_productos.tests.utilidades import (  # noqa: F401
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    MediaTemporalMixin,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
    imagen,
)

URL_CATALOGO = reverse("catalogo:listado")


def url_detalle(producto):
    return reverse("catalogo:detalle", kwargs={"codigo": producto.codigo})


def cargar_productos(cantidad, emprendimiento, estado=EstadoProducto.DISPONIBLE, prefijo="Producto"):
    """Crea muchos productos de una vez (sin archivos de foto reales)."""
    return Producto.objects.bulk_create(
        Producto(
            emprendimiento=emprendimiento,
            nombre=f"{prefijo} {i:03d}",
            precio_referencia=1000 + i,
            estado=estado,
            foto=f"productos/{prefijo.lower()}-{i}.jpg",
        )
        for i in range(cantidad)
    )


def emprendimientos_de_prueba():
    """Dos emprendimientos de categorías distintas."""
    comida = crear_perfil(crear_emprendedor(CORREO_EMPRENDEDOR_A), categoria="Comida", nombre="Arepas Doña Rosa")
    artesanias = crear_perfil(
        crear_emprendedor(CORREO_EMPRENDEDOR_B), categoria="Artesanías", nombre="Tejidos Juana",
        descripcion="Pulseras y mochilas tejidas a mano.",
    )
    return comida, artesanias


__all__ = ["Categoria", "Emprendimiento", "EstadoProducto", "Producto"]
