"""
Vistas del módulo E6 · Finanzas (capa de presentación). Solo para emprendedores
(RF-03) y siempre sobre sus propios registros (RN-14 · RNF-05).
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.cuentas.decorators import rol_requerido
from apps.cuentas.models import Rol
from apps.perfil_productos.templatetags.portafolio import pesos

from . import servicios
from .forms import GastoForm, IngresoForm, PeriodoForm
from .reglas import interpretar_periodo, mes_anterior, mes_siguiente, nombre_del_mes

solo_emprendedor = rol_requerido(Rol.EMPRENDEDOR)


def _url_del_mes(fecha):
    return f"{reverse('finanzas:resumen')}?mes={fecha:%Y-%m}"


@solo_emprendedor
def resumen(request):
    """HU-21 · RF-23 · CU-21 (supuestos S-5 y S-7). Un mes inválido o ausente muestra el mes actual."""
    hoy = timezone.localdate()
    anio, mes = interpretar_periodo(request.GET.get("mes")) or (hoy.year, hoy.month)
    resumen = servicios.resumen_financiero(request.user, anio, mes)
    return render(
        request,
        "finanzas/resumen.html",
        {
            "resumen": resumen,
            "nombre_periodo": nombre_del_mes(resumen.periodo),
            "periodo_form": PeriodoForm(initial={"mes": f"{resumen.periodo:%Y-%m}"}),
            "anterior": mes_anterior(resumen.periodo),
            "siguiente": mes_siguiente(resumen.periodo),
            "es_mes_actual": (anio, mes) == (hoy.year, hoy.month),
        },
    )


@solo_emprendedor
def nuevo_ingreso(request):
    """HU-19 · RF-21 · CU-19."""
    form = IngresoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ingreso = servicios.registrar_ingreso(request.user, **form.cleaned_data)
        messages.success(request, f"Registraste un ingreso de {pesos(ingreso.monto)} el {ingreso.fecha:%d/%m/%Y}.")
        return redirect(_url_del_mes(ingreso.fecha))
    return render(request, "finanzas/registro_form.html", {"form": form, "tipo": "ingreso"})


@solo_emprendedor
def nuevo_gasto(request):
    """HU-20 · RF-22 · CU-20."""
    form = GastoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        gasto = servicios.registrar_gasto(request.user, **form.cleaned_data)
        messages.success(
            request,
            f"Registraste un gasto de {pesos(gasto.monto)} en {gasto.get_categoria_display()} el {gasto.fecha:%d/%m/%Y}.",
        )
        return redirect(_url_del_mes(gasto.fecha))
    return render(request, "finanzas/registro_form.html", {"form": form, "tipo": "gasto"})


@solo_emprendedor
def eliminar(request, tipo, codigo):
    """Corrección de un error de registro, con confirmación (DT-E6-05). RN-14: 403 si es ajeno."""
    try:
        modelo = servicios.registro_de(tipo)
    except KeyError:
        raise Http404 from None
    registro = get_object_or_404(modelo, codigo=codigo)
    if registro.propietario_id != request.user.pk:
        raise PermissionDenied
    if request.method == "POST":
        destino = _url_del_mes(registro.fecha)
        registro.delete()
        messages.success(request, f"Eliminaste el {tipo} de {pesos(registro.monto)} del {registro.fecha:%d/%m/%Y}.")
        return redirect(destino)
    return render(
        request,
        "finanzas/eliminar.html",
        {"registro": registro, "tipo": tipo, "volver": _url_del_mes(registro.fecha)},
    )
