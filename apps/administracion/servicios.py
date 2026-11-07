"""
Capa de lógica del Módulo Administración (CU-22 · RN-19).

Cada operación verifica que quien actúa sea administrador, además del control de las vistas
(defensa en profundidad, decisión D4 del Entregable 2).
"""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.cuentas.models import Usuario
from apps.perfil_productos import servicios as perfil_productos
from apps.perfil_productos.models import EstadoProducto, Producto

from .models import Desactivacion


class DesactivacionNoPermitida(Exception):
    """La acción no aplica (por ejemplo, el producto ya está desactivado)."""


def _exigir_administrador(actor):
    """RN-19: solo el administrador desactiva productos o cuentas."""
    if not getattr(actor, "es_administrador", False):
        raise PermissionDenied


@transaction.atomic
def desactivar_producto(administrador, producto, *, motivo, detalle=""):
    """
    CU-22 · 1–2 (producto): ES1 Disponible/Agotado → Desactivado; deja de mostrarse en el
    catálogo (RN-09) y queda un aviso para su dueño (CC-11).
    """
    _exigir_administrador(administrador)
    producto = Producto.objects.select_for_update().get(pk=producto.pk)
    if producto.estado == EstadoProducto.DESACTIVADO:
        raise DesactivacionNoPermitida(f"«{producto.nombre}» ya está desactivado.")
    perfil_productos.desactivar_producto(producto)  # misma transición de ES1 que usa el emprendedor
    return Desactivacion.objects.create(
        administrador=administrador, producto=producto, motivo=motivo, detalle=detalle.strip()
    )


def motivo_para_no_desactivar(administrador, cuenta):
    """
    DT-E7-03: ni la propia cuenta ni la de otro administrador se desactivan desde la
    plataforma (evita dejarla sin administración). Devuelve el motivo, o "" si se puede.
    """
    if cuenta.pk == administrador.pk:
        return "Tu propia cuenta no se puede desactivar desde aquí."
    if cuenta.es_administrador:
        return f"La cuenta {cuenta.correo_institucional} es de administración y no se puede desactivar desde aquí."
    return ""


def _validar_cuenta_objetivo(administrador, cuenta):
    motivo = motivo_para_no_desactivar(administrador, cuenta)
    if motivo:
        raise DesactivacionNoPermitida(motivo)


@transaction.atomic
def desactivar_cuenta(administrador, cuenta, *, motivo, detalle=""):
    """
    CU-22 · 1 (cuenta) y CU-02 2b: la cuenta pierde el acceso. `Usuario.is_active` es falso,
    así que Django rechaza el inicio de sesión y la sesión abierta en la siguiente petición.
    Sus productos dejan de mostrarse sin cambiar de estado (se recuperan si se reactiva).
    """
    _exigir_administrador(administrador)
    _validar_cuenta_objetivo(administrador, cuenta)
    cuenta = Usuario.objects.select_for_update().get(pk=cuenta.pk)
    if not cuenta.activo:
        raise DesactivacionNoPermitida(f"La cuenta {cuenta.correo_institucional} ya está desactivada.")
    cuenta.activo = False
    cuenta.save(update_fields=["activo"])
    return Desactivacion.objects.create(
        administrador=administrador, cuenta=cuenta, motivo=motivo, detalle=detalle.strip()
    )


@transaction.atomic
def reactivar_cuenta(administrador, cuenta):
    """DT-E7-04: corrige una desactivación equivocada de una cuenta."""
    _exigir_administrador(administrador)
    cuenta = Usuario.objects.select_for_update().get(pk=cuenta.pk)
    if cuenta.activo:
        raise DesactivacionNoPermitida(f"La cuenta {cuenta.correo_institucional} ya está activa.")
    cuenta.activo = True
    cuenta.save(update_fields=["activo"])
    Desactivacion.objects.filter(cuenta=cuenta, reactivada_en__isnull=True).update(reactivada_en=timezone.now())
    return cuenta


# ------------------------------------------------------------------ Avisos al dueño (CC-11)
def avisos_de(usuario):
    """Desactivaciones de los productos del usuario, la más reciente primero (RN-14: solo las suyas)."""
    return Desactivacion.objects.filter(producto__emprendimiento__propietario=usuario).select_related("producto")


def avisos_pendientes(usuario):
    return avisos_de(usuario).filter(vista_en__isnull=True)


def marcar_avisos_vistos(usuario):
    return avisos_pendientes(usuario).update(vista_en=timezone.now())


# ------------------------------------------------------------------ Consultas del administrador
def buscar_productos(consulta=""):
    """Productos que hoy se muestran en el catálogo, por nombre del producto o del emprendimiento."""
    productos = Producto.objects.visibles_en_catalogo().select_related("emprendimiento__propietario")
    consulta = (consulta or "").strip()
    if consulta:
        productos = productos.filter(Q(nombre__icontains=consulta) | Q(emprendimiento__nombre__icontains=consulta))
    return productos.order_by("nombre", "id")


def buscar_cuentas(consulta=""):
    cuentas = Usuario.objects.all()
    consulta = (consulta or "").strip()
    if consulta:
        cuentas = cuentas.filter(correo_institucional__icontains=consulta)
    return cuentas.order_by("correo_institucional")


def historial(limite=30):
    return Desactivacion.objects.select_related("administrador", "producto", "cuenta")[:limite]
