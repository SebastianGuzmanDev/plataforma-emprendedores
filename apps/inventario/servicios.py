"""
Capa de lógica del módulo E5. Nombres del diagrama S6 y de C2:
registrarMovimiento(producto, tipo, cantidad) → obtenerExistencias() → descontar(cantidad)
→ [existencias = 0] marcarAgotado() → [existencias < umbral] tieneStockBajo().
"""
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.finanzas.models import CategoriaGasto
from apps.finanzas.servicios import registrar_gasto
from apps.perfil_productos.models import EstadoProducto

from .models import Insumo, MovimientoInventario, TipoMovimiento


class MovimientoRechazado(Exception):
    """A4: «Rechazar el movimiento» o «Rechazar la salida»."""


@dataclass
class Resultado:
    producto: object
    movimiento: MovimientoInventario | None
    cambio_de_estado: str | None  # "agotado", "disponible" o None
    stock_bajo: bool


def unidades(cantidad):
    return f"{cantidad} unidad" if cantidad == 1 else f"{cantidad} unidades"


def _validar_producto(producto):
    if producto.estado == EstadoProducto.DESACTIVADO:
        raise MovimientoRechazado("Este producto está desactivado: no admite movimientos de inventario.")


def registrar_existencias(producto, cantidad):
    """HU-15 · CU-15: registra las existencias iniciales (una sola vez; luego, entradas y salidas)."""
    _validar_producto(producto)
    if producto.existencias is not None:
        raise MovimientoRechazado(
            f"«{producto.nombre}» ya tiene existencias registradas: usa entradas y salidas para cambiarlas."
        )
    with transaction.atomic():
        producto.existencias = cantidad
        cambio = None
        if cantidad == 0 and producto.estado == EstadoProducto.DISPONIBLE:  # RN-10
            producto.marcar_agotado()
            cambio = "agotado"
        producto.save(update_fields=["existencias", "estado"])
        movimiento = None
        if cantidad > 0:
            movimiento = MovimientoInventario.objects.create(
                producto=producto, tipo=TipoMovimiento.ENTRADA, cantidad=cantidad
            )
    return Resultado(producto, movimiento, cambio, producto.tiene_stock_bajo())


def registrar_movimiento(producto, tipo, cantidad):
    """S6 · registrarMovimiento(producto, tipo, cantidad) · HU-16 y HU-17 · diagrama A4."""
    _validar_producto(producto)
    if producto.obtener_existencias() is None:
        raise MovimientoRechazado("Primero registra las existencias de este producto.")
    with transaction.atomic():
        if tipo == TipoMovimiento.SALIDA:
            if not producto.descontar(cantidad):  # RN-10: la salida no supera las existencias
                raise MovimientoRechazado(
                    f"No puedes sacar {unidades(cantidad)}: solo hay {producto.existencias}."
                )
        else:
            producto.reponer(cantidad)
        movimiento = MovimientoInventario.objects.create(producto=producto, tipo=tipo, cantidad=cantidad)
        cambio = None
        if tipo == TipoMovimiento.SALIDA and producto.existencias == 0 and producto.estado == EstadoProducto.DISPONIBLE:
            producto.marcar_agotado()  # ES1 · RN-10
            cambio = "agotado"
        elif tipo == TipoMovimiento.ENTRADA and producto.estado == EstadoProducto.AGOTADO:
            producto.marcar_disponible()  # CC-09: reponer existencias lo vuelve a ofrecer
            cambio = "disponible"
        if cambio:
            producto.save(update_fields=["estado"])
    return Resultado(producto, movimiento, cambio, producto.tiene_stock_bajo())


def definir_umbral(producto, umbral):
    """HU-17: umbral de stock bajo del producto (supuesto S-6). None lo quita."""
    _validar_producto(producto)
    producto.umbral_stock_bajo = umbral
    producto.save(update_fields=["umbral_stock_bajo"])
    return producto


@transaction.atomic
def registrar_insumo(propietario, *, nombre, cantidad, costo, registrar_como_gasto=False):
    """
    HU-18 · CU-18 · RN-12.

    CC-10 (E6): si se pide, el costo queda además como gasto de materia prima con la
    fecha de hoy (HU-20). Un insumo de costo 0 no genera gasto (RN-13: monto > 0).
    Devuelve (insumo, gasto o None); ambos se guardan juntos o ninguno.
    """
    insumo = Insumo.objects.create(propietario=propietario, nombre=nombre.strip(), cantidad=cantidad, costo=costo)
    gasto = None
    if registrar_como_gasto and costo > 0:
        gasto = registrar_gasto(
            propietario, monto=costo, categoria=CategoriaGasto.MATERIA_PRIMA, fecha=timezone.localdate()
        )
    return insumo, gasto
