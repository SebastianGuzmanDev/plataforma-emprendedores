"""Ayudas de las pruebas de la Épica 4 (reutiliza las de E1 a E3)."""
from django.urls import reverse
from django.utils import timezone

from apps.contacto.models import Conversacion, Mensaje
from apps.cuentas.tests.utilidades import CONTRASENA_VALIDA, crear_usuario  # noqa: F401
from apps.perfil_productos.tests.utilidades import (  # noqa: F401
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    crear_emprendedor,
    crear_perfil,
    crear_producto,
    entrar,
)

URL_MENSAJES = reverse("contacto:lista")


def url_iniciar(producto):
    return reverse("contacto:iniciar", kwargs={"codigo_producto": producto.codigo})


def url_conversacion(conversacion):
    return reverse("contacto:conversacion", kwargs={"codigo": conversacion.codigo})


def escenario():
    """Un comprador y un emprendedor con un producto publicado."""
    comprador = crear_usuario(correo=CORREO_COMPRADOR)
    emprendedor = crear_emprendedor(CORREO_EMPRENDEDOR_A)
    producto = crear_producto(crear_perfil(emprendedor, nombre="Arepas Doña Rosa"), "Arepa de queso")
    return comprador, emprendedor, producto


def crear_conversacion(comprador, producto, mensajes=()):
    """`mensajes` es una lista de (autor, texto) en orden de envío."""
    conversacion = Conversacion.objects.create(
        comprador=comprador, emprendedor=producto.emprendimiento.propietario, producto=producto
    )
    for i, (autor, texto) in enumerate(mensajes):
        Mensaje.objects.create(
            conversacion=conversacion, autor=autor, contenido=texto,
            fecha_envio=timezone.now() + timezone.timedelta(seconds=i),
        )
    return conversacion
