"""Ayudas de plantilla para formularios accesibles (RNF-11)."""
from django import template

register = template.Library()


@register.filter
def campo_accesible(campo):
    """Renderiza el campo enlazando su ayuda y su error con aria-describedby."""
    descripciones = []
    atributos = {}
    if campo.help_text:
        descripciones.append(f"{campo.auto_id}_helptext")
    if campo.errors:
        descripciones.append(f"{campo.auto_id}_error")
        atributos["aria-invalid"] = "true"
    if descripciones:
        atributos["aria-describedby"] = " ".join(descripciones)
    return campo.as_widget(attrs=atributos)


@register.filter
def descripcion_rol(valor):
    """Texto que explica cada rol en el formulario de registro."""
    from apps.cuentas.forms import DESCRIPCION_ROLES

    return DESCRIPCION_ROLES.get(valor, "")
