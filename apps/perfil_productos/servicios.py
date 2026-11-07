"""
Capa de lógica de negocio del módulo E2: casos de uso CU-04, CU-05 y CU-06.

Los nombres siguen el diagrama de secuencia S3: publicarProducto(nombre, foto, precio)
→ obtenerEmprendimiento(emprendedor) → guardar(foto) → guardar Producto(estado = DISPONIBLE).
"""
from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.cuentas.models import Rol

from .models import Emprendimiento, EstadoProducto, Producto
from .reglas import crear_miniatura, procesar_foto


class PerfilRequerido(Exception):
    """RN-05: el emprendedor aún no tiene perfil de emprendimiento."""


def obtener_emprendimiento(emprendedor):
    """S3 · obtenerEmprendimiento(emprendedor)."""
    return Emprendimiento.objects.select_related("categoria", "propietario").filter(propietario=emprendedor).first()


def guardar_perfil(form, emprendedor):
    """CU-04 · Crea el perfil o edita el existente (un perfil por emprendedor)."""
    if emprendedor.rol != Rol.EMPRENDEDOR:
        raise PermissionDenied
    perfil = form.save(commit=False)
    creado = perfil.pk is None
    perfil.propietario = emprendedor
    perfil.save()
    return perfil, creado


def publicar_producto(emprendedor, *, nombre, foto, precio):
    """CU-05 · S3: publica el producto con estado Disponible."""
    emprendimiento = obtener_emprendimiento(emprendedor)
    if emprendimiento is None:
        raise PerfilRequerido
    producto = Producto(
        emprendimiento=emprendimiento,
        nombre=nombre.strip(),
        precio_referencia=precio,
        estado=EstadoProducto.DISPONIBLE,
    )
    with transaction.atomic():
        _guardar_fotos(producto, foto)
        producto.save()
    return producto


def _guardar_fotos(producto, foto):
    """S3 · guardar(foto): la foto normalizada y su miniatura (CC-06) con el mismo nombre aleatorio."""
    foto_procesada = procesar_foto(foto)
    miniatura = crear_miniatura(foto, nombre=foto_procesada.name)
    producto.foto.save(foto_procesada.name, foto_procesada, save=False)
    producto.miniatura.save(miniatura.name, miniatura, save=False)


def editar_producto(producto, *, nombre, precio, foto=None):
    """CU-06 · Cambia nombre, precio y, si se envía, la foto (la anterior se borra)."""
    producto.validar_edicion()
    producto.nombre = nombre.strip()
    producto.precio_referencia = precio
    anteriores = [producto.foto.name, producto.miniatura.name] if foto else []
    if foto:
        _guardar_fotos(producto, foto)
    producto.save()
    actuales = {producto.foto.name, producto.miniatura.name}
    for nombre in anteriores:
        if nombre and nombre not in actuales:
            producto.foto.storage.delete(nombre)
    return producto


def marcar_agotado(producto):
    """CU-06 · ES1: Disponible → Agotado."""
    producto.marcar_agotado()
    producto.save(update_fields=["estado"])
    return producto


def marcar_disponible(producto):
    """CC-02 · Agotado → Disponible."""
    producto.marcar_disponible()
    producto.save(update_fields=["estado"])
    return producto


def desactivar_producto(producto):
    """CU-06 · ES1: Disponible o Agotado → Desactivado."""
    producto.desactivar()
    producto.save(update_fields=["estado"])
    return producto
