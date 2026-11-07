from django import template

register = template.Library()


@register.filter
def cantidad(valor):
    """Decimal(2.500) → «2,5»."""
    if valor is None:
        return ""
    texto = format(valor.normalize(), "f") if hasattr(valor, "normalize") else str(valor)
    return texto.replace(".", ",")
