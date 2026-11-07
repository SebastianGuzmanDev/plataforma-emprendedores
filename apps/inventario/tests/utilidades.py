"""Ayudas de las pruebas de la Épica 5 (reutiliza las de E1 y E2)."""
from django.urls import reverse

from apps.perfil_productos.models import EstadoProducto, Producto  # noqa: F401
from apps.perfil_productos.tests.utilidades import (  # noqa: F401
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
)

URL_INVENTARIO = reverse("inventario:panel")
URL_NUEVO_INSUMO = reverse("inventario:nuevo_insumo")


def url(nombre, producto):
    return reverse(f"inventario:{nombre}", kwargs={"codigo": producto.codigo})


def producto_con_existencias(existencias=None, umbral=None, correo=CORREO_EMPRENDEDOR_A, nombre="Arepa de queso"):
    emprendedor = crear_emprendedor(correo)
    producto = crear_producto(crear_perfil(emprendedor), nombre)
    if existencias is not None or umbral is not None:
        Producto.objects.filter(pk=producto.pk).update(existencias=existencias, umbral_stock_bajo=umbral)
        producto.refresh_from_db()
    return producto
