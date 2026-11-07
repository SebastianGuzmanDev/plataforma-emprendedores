"""
Vistas del Módulo Administración (E7, capa de presentación).

Las de moderación son solo para el administrador (RN-19; HU-22 Esc. 3 → 403). El
administrador no accede a mensajes, inventario ni finanzas de nadie (RN-14).
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cuentas.decorators import rol_requerido
from apps.cuentas.models import Rol, Usuario
from apps.perfil_productos.models import EstadoProducto, Producto

from . import servicios
from .forms import BusquedaForm, DesactivacionForm
from .servicios import DesactivacionNoPermitida

solo_administrador = rol_requerido(Rol.ADMINISTRADOR)
POR_PAGINA = 20


def _pagina(request, consulta):
    return Paginator(consulta, POR_PAGINA).get_page(request.GET.get("pagina"))


@solo_administrador
def panel(request):
    """Inicio del administrador: accesos a la moderación e historial (trazabilidad, CC-11)."""
    return render(
        request,
        "administracion/panel.html",
        {
            "productos_visibles": Producto.objects.visibles_en_catalogo().count(),
            "cuentas_activas": Usuario.objects.filter(activo=True).count(),
            "cuentas_desactivadas": Usuario.objects.filter(activo=False).count(),
            "historial": servicios.historial(),
        },
    )


@solo_administrador
def productos(request):
    """Productos que hoy se muestran en el catálogo, con búsqueda."""
    busqueda = BusquedaForm(request.GET)
    consulta = busqueda.cleaned_data["q"] if busqueda.is_valid() else ""
    return render(
        request,
        "administracion/productos.html",
        {"busqueda": busqueda, "consulta": consulta, "pagina": _pagina(request, servicios.buscar_productos(consulta))},
    )


@solo_administrador
def desactivar_producto(request, codigo):
    """CU-22 · HU-22 Esc. 1."""
    producto = get_object_or_404(Producto.objects.select_related("emprendimiento__propietario"), codigo=codigo)
    if producto.estado == EstadoProducto.DESACTIVADO:
        messages.error(request, f"«{producto.nombre}» ya está desactivado.")
        return redirect("administracion:productos")
    form = DesactivacionForm(
        request.POST or None,
        ayuda_detalle="Se le muestra al dueño junto con el motivo. No incluyas datos personales.",
    )
    if request.method == "POST" and form.is_valid():
        try:
            servicios.desactivar_producto(request.user, producto, **form.cleaned_data)
        except DesactivacionNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(
                request,
                f"«{producto.nombre}» quedó desactivado: ya no aparece en el catálogo y se le notificó a su dueño.",
            )
        return redirect("administracion:productos")
    return render(request, "administracion/desactivar_producto.html", {"producto": producto, "form": form})


@solo_administrador
def cuentas(request):
    busqueda = BusquedaForm(request.GET)
    consulta = busqueda.cleaned_data["q"] if busqueda.is_valid() else ""
    return render(
        request,
        "administracion/cuentas.html",
        {"busqueda": busqueda, "consulta": consulta, "pagina": _pagina(request, servicios.buscar_cuentas(consulta))},
    )


@solo_administrador
def desactivar_cuenta(request, codigo):
    """CU-22 · HU-22 Esc. 2 (y CU-02 flujo 2b)."""
    cuenta = get_object_or_404(Usuario, codigo=codigo)
    error = servicios.motivo_para_no_desactivar(request.user, cuenta)
    if error:
        messages.error(request, error)
        return redirect("administracion:cuentas")
    form = DesactivacionForm(
        request.POST or None,
        ayuda_detalle="Queda en el historial de administración.",
    )
    if request.method == "POST" and form.is_valid():
        try:
            servicios.desactivar_cuenta(request.user, cuenta, **form.cleaned_data)
        except DesactivacionNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(
                request,
                f"La cuenta {cuenta.correo_institucional} quedó desactivada: ya no puede iniciar sesión "
                "y sus productos no aparecen en el catálogo.",
            )
        return redirect("administracion:cuentas")
    return render(request, "administracion/desactivar_cuenta.html", {"cuenta": cuenta, "form": form})


@solo_administrador
@require_POST
def reactivar_cuenta(request, codigo):
    """DT-E7-04: corregir una desactivación equivocada."""
    cuenta = get_object_or_404(Usuario, codigo=codigo)
    try:
        servicios.reactivar_cuenta(request.user, cuenta)
    except DesactivacionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"La cuenta {cuenta.correo_institucional} volvió a estar activa.")
    return redirect("administracion:cuentas")


@rol_requerido(Rol.EMPRENDEDOR)
def avisos(request):
    """CC-11 · HU-22 Esc. 1: «se notifica a su dueño». Al verlos dejan de estar pendientes."""
    lista = list(servicios.avisos_de(request.user))
    servicios.marcar_avisos_vistos(request.user)
    return render(request, "administracion/avisos.html", {"avisos": lista})
