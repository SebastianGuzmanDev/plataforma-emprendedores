"""
Capa de lógica del módulo E4. Nombres de los diagramas S5 y C1:
iniciarConversacion(producto), enviarMensaje(conversacion, contenido) y
obtenerMensajes(conversacion). La mensajería es asíncrona (D3): no hay tiempo real.
"""
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from .models import Conversacion, Mensaje
from .reglas import limpiar_mensaje


class ContactoNoPermitido(Exception):
    """RN-18: el producto es del propio usuario."""


class CuentaDesactivada(Exception):
    """RN-19 (E7): la otra persona perdió el acceso; no podría leer ni responder."""


class MensajeVacio(Exception):
    """RN-16: no se envía un mensaje vacío."""


def iniciar_conversacion(usuario, producto):
    """S5 · iniciarConversacion(producto): crea la conversación o reabre la existente."""
    propietario_id = producto.emprendimiento.propietario_id
    if propietario_id == usuario.pk:
        raise ContactoNoPermitido("No puedes contactarte a ti mismo: este producto es tuyo.")
    return Conversacion.objects.get_or_create(
        comprador=usuario, producto=producto, defaults={"emprendedor_id": propietario_id}
    )


def enviar_mensaje(conversacion, autor, contenido):
    """S5 · enviarMensaje(conversacion, contenido): guarda el mensaje con leido = falso."""
    if not conversacion.participa(autor):
        raise PermissionDenied
    if not conversacion.otra_persona(autor).activo:
        raise CuentaDesactivada
    texto = limpiar_mensaje(contenido)
    if texto is None:
        raise MensajeVacio
    return Mensaje.objects.create(conversacion=conversacion, autor=autor, contenido=texto)


def obtener_mensajes(conversacion, lector):
    """S5 · obtenerMensajes(conversacion): historial completo; marca como leídos los de la otra persona."""
    if not conversacion.participa(lector):
        raise PermissionDenied
    conversacion.mensajes.filter(leido=False).exclude(autor=lector).update(leido=True)
    return list(conversacion.mensajes.order_by("fecha_envio", "id"))


def conversaciones_de(usuario):
    """
    HU-13 · RN-17: conversaciones del usuario, la del mensaje más reciente primero.
    Al emprendedor solo le aparecen las que ya tienen algún mensaje.
    """
    mensajes = Mensaje.objects.filter(conversacion=OuterRef("pk"))
    ultimo = mensajes.order_by("-fecha_envio", "-id")
    sin_leer = (
        mensajes.filter(leido=False).exclude(autor=usuario).order_by()
        .values("conversacion").annotate(total=Count("id")).values("total")
    )
    return (
        Conversacion.objects.annotate(
            tiene_mensajes=Exists(mensajes),
            ultimo_contenido=Subquery(ultimo.values("contenido")[:1]),
            ultimo_autor=Subquery(ultimo.values("autor")[:1]),
            ultima_fecha=Subquery(ultimo.values("fecha_envio")[:1]),
            sin_leer=Coalesce(Subquery(sin_leer, output_field=IntegerField()), 0),
        )
        .filter(Q(comprador=usuario) | Q(emprendedor=usuario, tiene_mensajes=True))
        .select_related("producto__emprendimiento")
        .order_by(Coalesce("ultima_fecha", "creada").desc(), "-id")
    )


def mensajes_sin_leer(usuario):
    """HU-14 · RF-16: mensajes de otras personas que el usuario aún no ha leído."""
    return (
        Mensaje.objects.filter(leido=False)
        .filter(Q(conversacion__comprador=usuario) | Q(conversacion__emprendedor=usuario))
        .exclude(autor=usuario)
        .count()
    )
