"""Formularios del módulo E7 (capa de presentación)."""
from django import forms

from .models import MotivoDesactivacion

LIMITE_DETALLE = 300


class DesactivacionForm(forms.Form):
    """HU-22: el administrador indica por qué el producto o la cuenta incumple las reglas."""

    motivo = forms.ChoiceField(
        label="Motivo",
        choices=MotivoDesactivacion.choices,
        widget=forms.RadioSelect,
        error_messages={
            "required": "Elige el motivo de la desactivación.",
            "invalid_choice": "Elige el motivo de la desactivación.",
        },
    )
    detalle = forms.CharField(
        label="Detalle (opcional)",
        required=False,
        max_length=LIMITE_DETALLE,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": LIMITE_DETALLE}),
        error_messages={"max_length": f"El detalle admite hasta {LIMITE_DETALLE} caracteres."},
    )

    def __init__(self, *args, ayuda_detalle="", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["detalle"].help_text = ayuda_detalle


class BusquedaForm(forms.Form):
    q = forms.CharField(label="Buscar", required=False, max_length=100)
