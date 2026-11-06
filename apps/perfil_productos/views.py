"""
Vistas del módulo E2 · Perfil y productos (capa de presentación).

Todas exigen el rol Emprendedor (RF-03, `rol_requerido` de E1). El emprendedor se
identifica por la sesión; los productos, por un código no secuencial, y solo su dueño
puede modificarlos (RN-08, RNF-05).
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.decorators import rol_requerido
from apps.cuentas.models import Rol

from . import servicios
from .forms import PerfilForm, ProductoForm
from .models import EstadoProducto, Producto, TransicionNoPermitida

solo_emprendedor = rol_requerido(Rol.EMPRENDEDOR)
MENSAJE_PERFIL_REQUERIDO = "Antes de publicar productos, crea el perfil de tu emprendimiento."


def _producto_propio(request, codigo):
    """HU-06 Esc. 4 · RN-08: un producto ajeno responde «acceso denegado» (403)."""
    producto = get_object_or_404(Producto.objects.select_related("emprendimiento"), codigo=codigo)
    if producto.emprendimiento.propietario_id != request.user.pk:
        raise PermissionDenied
    return producto


@solo_emprendedor
def panel(request):
    """Inicio del emprendedor: estado del perfil y su portafolio."""
    emprendimiento = servicios.obtener_emprendimiento(request.user)
    productos = list(emprendimiento.productos.all()) if emprendimiento else []
    return render(
        request,
        "perfil_productos/panel.html",
        {
            "emprendimiento": emprendimiento,
            "productos_visibles": [p for p in productos if p.es_visible_en_catalogo],
            "productos_desactivados": [p for p in productos if p.estado == EstadoProducto.DESACTIVADO],
        },
    )


@solo_emprendedor
def perfil(request):
    """HU-04 · CU-04: crear o editar el perfil del emprendimiento."""
    actual = servicios.obtener_emprendimiento(request.user)
    form = PerfilForm(request.POST or None, instance=actual)
    if request.method == "POST" and form.is_valid():
        _, creado = servicios.guardar_perfil(form, request.user)
        if creado:
            messages.success(request, "El perfil de tu emprendimiento quedó publicado. Ya puedes publicar productos.")
        else:
            messages.success(request, "Guardamos los cambios de tu perfil.")
        return redirect("emprendimiento:panel")
    return render(request, "perfil_productos/perfil.html", {"form": form, "editando": actual is not None})


@solo_emprendedor
def publicar(request):
    """HU-05 · CU-05 · diagramas A2 y S3."""
    if servicios.obtener_emprendimiento(request.user) is None:
        messages.info(request, MENSAJE_PERFIL_REQUERIDO)
        return redirect("emprendimiento:perfil")
    form = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        producto = servicios.publicar_producto(
            request.user, nombre=datos["nombre"], foto=datos["foto"], precio=datos["precio_referencia"]
        )
        messages.success(request, f"Publicaste «{producto.nombre}». Ya aparece en el catálogo como Disponible.")
        return redirect("emprendimiento:panel")
    return render(request, "perfil_productos/producto_form.html", {"form": form, "producto": None})


@solo_emprendedor
def editar(request, codigo):
    """HU-06 Esc. 1 · RF-07."""
    producto = _producto_propio(request, codigo)
    try:
        producto.validar_edicion()
    except TransicionNoPermitida as error:
        messages.error(request, str(error))
        return redirect("emprendimiento:panel")
    inicial = {"nombre": producto.nombre, "precio_referencia": str(producto.precio_referencia)}
    form = ProductoForm(request.POST or None, request.FILES or None, initial=inicial, foto_obligatoria=False)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        servicios.editar_producto(
            producto, nombre=datos["nombre"], precio=datos["precio_referencia"], foto=datos.get("foto")
        )
        messages.success(request, f"Guardamos los cambios de «{producto.nombre}».")
        return redirect("emprendimiento:panel")
    return render(request, "perfil_productos/producto_form.html", {"form": form, "producto": producto})


@solo_emprendedor
@require_POST
def agotado(request, codigo):
    """HU-06 Esc. 2 · RF-08 · ES1: Disponible → Agotado."""
    producto = _producto_propio(request, codigo)
    try:
        servicios.marcar_agotado(producto)
    except TransicionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"«{producto.nombre}» quedó marcado como agotado. Sigue visible con esa etiqueta.")
    return redirect("emprendimiento:panel")


@solo_emprendedor
@require_POST
def disponible(request, codigo):
    """CC-02: Agotado → Disponible."""
    producto = _producto_propio(request, codigo)
    try:
        servicios.marcar_disponible(producto)
    except TransicionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"«{producto.nombre}» volvió a estar disponible en el catálogo.")
    return redirect("emprendimiento:panel")


@solo_emprendedor
@require_http_methods(["GET", "POST"])
def desactivar(request, codigo):
    """HU-06 Esc. 3 · RF-08 · ES1: → Desactivado. Pide confirmación porque no se puede deshacer."""
    producto = _producto_propio(request, codigo)
    if request.method == "POST":
        try:
            servicios.desactivar_producto(producto)
        except TransicionNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"«{producto.nombre}» quedó desactivado y ya no aparece en el catálogo.")
        return redirect("emprendimiento:panel")
    return render(request, "perfil_productos/desactivar.html", {"producto": producto})


@solo_emprendedor
def vista_previa(request):
    """Así verán los compradores el emprendimiento: misma regla RN-09 que usará el catálogo (E3)."""
    emprendimiento = servicios.obtener_emprendimiento(request.user)
    if emprendimiento is None:
        messages.info(request, "Crea el perfil de tu emprendimiento para ver cómo lo verán los compradores.")
        return redirect("emprendimiento:perfil")
    productos = Producto.objects.visibles_en_catalogo().filter(emprendimiento=emprendimiento)
    return render(
        request, "perfil_productos/vista_previa.html", {"emprendimiento": emprendimiento, "productos": productos}
    )
