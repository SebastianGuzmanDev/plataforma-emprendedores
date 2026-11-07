"""Datos y ayudas compartidas por las pruebas de la Épica 7."""
from django.urls import reverse

from apps.administracion.models import MotivoDesactivacion
from apps.cuentas.models import Rol
from apps.cuentas.tests.utilidades import CORREO_ADMIN, crear_usuario
from apps.perfil_productos.tests.utilidades import (  # noqa: F401
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
)

URL_ADMIN = reverse("administracion:panel")
URL_ADMIN_PRODUCTOS = reverse("administracion:productos")
URL_ADMIN_CUENTAS = reverse("administracion:cuentas")
URL_AVISOS = reverse("administracion:avisos")
MOTIVO = MotivoDesactivacion.PRODUCTO_PROHIBIDO


def crear_administrador(correo=CORREO_ADMIN):
    return crear_usuario(correo=correo, rol=Rol.ADMINISTRADOR)


def url_desactivar_producto(producto):
    return reverse("administracion:desactivar_producto", kwargs={"codigo": producto.codigo})


def url_desactivar_cuenta(usuario):
    return reverse("administracion:desactivar_cuenta", kwargs={"codigo": usuario.codigo})


def url_reactivar_cuenta(usuario):
    return reverse("administracion:reactivar_cuenta", kwargs={"codigo": usuario.codigo})


def emprendedor_con_producto(correo=CORREO_EMPRENDEDOR_A, nombre="Arepa de queso"):
    emprendedor = crear_emprendedor(correo)
    producto = crear_producto(crear_perfil(emprendedor), nombre=nombre)
    return emprendedor, producto
