"""
Vistas del módulo E4 · Contacto por chat (capa de presentación). Todas exigen sesión.
Solo los dos participantes ven y escriben en una conversación (RNF-05).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.perfil_productos.models import Producto

from . import servicios
from .forms import MensajeForm
from .models import Conversacion


@login_required
def lista(request):
    """HU-13 · CU-13: mis conversaciones, la del mensaje más reciente primero (RN-17)."""
    conversaciones = [
        {"conversacion": c, "con_quien": c.nombre_de_la_otra_persona(request.user), "propio": c.ultimo_autor == request.user.pk}
        for c in servicios.conversaciones_de(request.user)
    ]
    return render(request, "contacto/lista.html", {"conversaciones": conversaciones})


@login_required
@require_http_methods(["GET", "POST"])
def iniciar(request, codigo_producto):
    """HU-11 · CU-11 · S5: «Contactar» en un producto abre la conversación con su emprendedor."""
    producto = get_object_or_404(
        Producto.objects.select_related("emprendimiento__propietario"), codigo=codigo_producto
    )
    if request.method == "GET":  # p. ej. al volver de iniciar sesión: se regresa al producto (A3)
        return redirect("catalogo:detalle", codigo=producto.codigo)
    if not producto.es_visible_en_catalogo:
        return render(request, "catalogo/no_disponible.html", status=404)
    try:
        conversacion, _ = servicios.iniciar_conversacion(request.user, producto)
    except servicios.ContactoNoPermitido as error:
        messages.error(request, str(error))
        return redirect("catalogo:detalle", codigo=producto.codigo)
    return redirect("contacto:conversacion", codigo=conversacion.codigo)


@login_required
@require_http_methods(["GET", "POST"])
def conversacion(request, codigo):
    """HU-12 · CU-12 · S5: historial y envío de mensajes (asíncrono: se actualiza al recargar)."""
    conversacion = get_object_or_404(
        Conversacion.objects.select_related("producto__emprendimiento__categoria", "comprador", "emprendedor"),
        codigo=codigo,
    )
    if not conversacion.participa(request.user):
        raise PermissionDenied
    form = MensajeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            servicios.enviar_mensaje(conversacion, request.user, form.cleaned_data["contenido"])
        except servicios.MensajeVacio:
            form.add_error("contenido", "Escribe un mensaje antes de enviarlo.")
        except servicios.CuentaDesactivada:
            return redirect("contacto:conversacion", codigo=conversacion.codigo)
        else:
            return redirect("contacto:conversacion", codigo=conversacion.codigo)
    return render(
        request,
        "contacto/conversacion.html",
        {
            "conversacion": conversacion,
            "producto": conversacion.producto,
            "con_quien": conversacion.nombre_de_la_otra_persona(request.user),
            "otra_cuenta_activa": conversacion.otra_persona(request.user).activo,
            "mensajes_conversacion": servicios.obtener_mensajes(conversacion, request.user),
            "form": form,
        },
    )
