from django import forms

from .reglas import LONGITUD_MAXIMA_MENSAJE


class MensajeForm(forms.Form):
    """HU-12 · RN-16: el mensaje no puede estar vacío ni pasar de 1000 caracteres."""

    contenido = forms.CharField(
        label="Escribe tu mensaje",
        max_length=LONGITUD_MAXIMA_MENSAJE,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": LONGITUD_MAXIMA_MENSAJE, "autofocus": True}),
        error_messages={
            "required": "Escribe un mensaje antes de enviarlo.",
            "max_length": "El mensaje puede tener hasta 1000 caracteres (tiene %(show_value)d).",
        },
    )
