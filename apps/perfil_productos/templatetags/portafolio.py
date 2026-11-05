"""Formato de valores del portafolio."""
from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """5000 → «$ 5.000» (separador de miles colombiano)."""
    try:
        return "$ " + f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return ""
