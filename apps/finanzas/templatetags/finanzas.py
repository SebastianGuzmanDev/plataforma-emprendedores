"""Formato de cifras del resumen financiero."""
from django import template

from apps.perfil_productos.templatetags.portafolio import pesos

register = template.Library()


@register.filter
def pesos_con_signo(valor):
    """-3000 → «−$ 3.000» (signo menos tipográfico); 0 y positivos sin signo."""
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return ""
    return f"−{pesos(-numero)}" if numero < 0 else pesos(numero)


@register.filter
def porcentaje_de(parte, total):
    """Porción entera (0 a 100) de parte sobre total; 0 si el total es 0."""
    try:
        return round(int(parte) * 100 / int(total)) if int(total) else 0
    except (TypeError, ValueError):
        return 0
