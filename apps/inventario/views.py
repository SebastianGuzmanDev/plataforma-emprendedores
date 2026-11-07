"""
Vistas del módulo E5 · Inventario (capa de presentación). Solo para emprendedores
(RF-03) y siempre sobre sus propios productos e insumos (RN-08, RNF-05).
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cuentas.decorators import rol_requerido
from apps.cuentas.models import Rol
from apps.perfil_productos.models import ESTADOS_VISIBLES_EN_CATALOGO, EstadoProducto, Producto
from apps.perfil_productos.servicios import obtener_emprendimiento

from . import servicios
from .forms import ExistenciasForm, InsumoForm, MovimientoForm, UmbralForm
from .servicios import MovimientoRechazado, unidades

solo_emprendedor = rol_requerido(Rol.EMPRENDEDOR)


def _producto_propio(request, codigo):
    producto = get_object_or_404(Producto.objects.select_related("emprendimiento"), codigo=codigo)
    if producto.emprendimiento.propietario_id != request.user.pk:
        raise PermissionDenied
    return producto


def _avisar(request, producto, resultado, texto):
    messages.success(request, texto)
    if resultado.cambio_de_estado == "agotado":
        messages.info(request, f"«{producto.nombre}» quedó agotado: sus existencias llegaron a 0.")
    elif resultado.cambio_de_estado == "disponible":
        messages.info(request, f"«{producto.nombre}» volvió a estar disponible en el catálogo.")
    if resultado.stock_bajo:  # HU-17 · A4: «Mostrar alerta de stock bajo»
        messages.warning(
            request,
            f"Stock bajo: quedan {unidades(producto.existencias)} de «{producto.nombre}» "
            f"(umbral: {producto.umbral_stock_bajo}).",
        )


@solo_emprendedor
def panel(request):
    """Inventario del emprendedor: existencias de sus productos publicados e insumos."""
    emprendimiento = obtener_emprendimiento(request.user)
    productos = (
        emprendimiento.productos.filter(estado__in=ESTADOS_VISIBLES_EN_CATALOGO).order_by("nombre")
        if emprendimiento else []
    )
    insumos = request.user.insumos.all()
    return render(
        request,
        "inventario/panel.html",
        {
            "emprendimiento": emprendimiento,
            "productos": productos,
            "insumos": insumos,
            "costo_total": insumos.aggregate(total=Sum("costo"))["total"] or 0,
        },
    )


def _pagina_producto(request, producto, **formularios):
    contexto = {
        "producto": producto,
        "existencias_form": formularios.get("existencias_form") or ExistenciasForm(),
        "movimiento_form": formularios.get("movimiento_form") or MovimientoForm(),
        "umbral_form": formularios.get("umbral_form")
        or UmbralForm(initial={"umbral_stock_bajo": producto.umbral_stock_bajo or ""}),
        "movimientos": producto.movimientos.all()[:20],
    }
    return render(request, "inventario/producto.html", contexto)


@solo_emprendedor
def producto(request, codigo):
    """CU-15 a CU-17 · A4: «Seleccionar un producto publicado»."""
    producto = _producto_propio(request, codigo)
    if producto.estado == EstadoProducto.DESACTIVADO:
        messages.error(request, "Ese producto está desactivado: no tiene inventario.")
        return redirect("inventario:panel")
    return _pagina_producto(request, producto)


@solo_emprendedor
@require_POST
def existencias(request, codigo):
    """HU-15 · RF-17."""
    producto = _producto_propio(request, codigo)
    form = ExistenciasForm(request.POST)
    if not form.is_valid():
        return _pagina_producto(request, producto, existencias_form=form)
    try:
        resultado = servicios.registrar_existencias(producto, form.cleaned_data["existencias"])
    except MovimientoRechazado as error:
        messages.error(request, str(error))
    else:
        _avisar(request, producto, resultado, f"Registraste {unidades(producto.existencias)} de «{producto.nombre}».")
    return redirect("inventario:producto", codigo=producto.codigo)


@solo_emprendedor
@require_POST
def movimiento(request, codigo):
    """HU-16 · RF-18 · S6 (y HU-17, alerta de stock bajo)."""
    producto = _producto_propio(request, codigo)
    if producto.estado == EstadoProducto.DESACTIVADO:
        messages.error(request, "Este producto está desactivado: no admite movimientos de inventario.")
        return redirect("inventario:panel")
    form = MovimientoForm(request.POST)
    if not form.is_valid():
        return _pagina_producto(request, producto, movimiento_form=form)
    tipo, cantidad = form.cleaned_data["tipo"], form.cleaned_data["cantidad"]
    try:
        resultado = servicios.registrar_movimiento(producto, tipo, cantidad)
    except MovimientoRechazado as error:
        if producto.existencias is None:
            messages.error(request, str(error))
            return redirect("inventario:producto", codigo=producto.codigo)
        form.add_error("cantidad", str(error))
        return _pagina_producto(request, producto, movimiento_form=form)
    nombre_tipo = "Entrada" if tipo == "ENTRADA" else "Salida"
    _avisar(request, producto, resultado,
            f"{nombre_tipo} de {unidades(cantidad)} registrada. Existencias: {producto.existencias}.")
    return redirect("inventario:producto", codigo=producto.codigo)


@solo_emprendedor
@require_POST
def umbral(request, codigo):
    """HU-17 · RF-19."""
    producto = _producto_propio(request, codigo)
    form = UmbralForm(request.POST)
    if not form.is_valid():
        return _pagina_producto(request, producto, umbral_form=form)
    try:
        servicios.definir_umbral(producto, form.cleaned_data["umbral_stock_bajo"])
    except MovimientoRechazado as error:
        messages.error(request, str(error))
        return redirect("inventario:panel")
    if producto.umbral_stock_bajo:
        messages.success(request, f"Te avisaremos cuando queden menos de {unidades(producto.umbral_stock_bajo)}.")
    else:
        messages.success(request, "Quitaste el umbral de stock bajo.")
    return redirect("inventario:producto", codigo=producto.codigo)


@solo_emprendedor
def nuevo_insumo(request):
    """HU-18 · RF-20 · CU-18."""
    form = InsumoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        insumo, gasto = servicios.registrar_insumo(request.user, **form.cleaned_data)
        texto = f"Registraste el insumo «{insumo.nombre}»."
        if gasto:  # CC-10
            texto += " También quedó como gasto de materia prima en Finanzas."
        messages.success(request, texto)
        return redirect("inventario:panel")
    return render(request, "inventario/insumo_form.html", {"form": form})
