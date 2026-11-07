"""Formularios del módulo E6 (capa de presentación)."""
from django import forms
from django.utils import timezone

from .models import CategoriaGasto
from .reglas import PRIMER_ANIO, interpretar_monto

MENSAJE_MONTO = "Escribe un monto mayor a 0 en pesos, solo con números (por ejemplo 25.000)."
MENSAJE_FECHA = "Indica la fecha (día, mes y año)."


class _RegistroForm(forms.Form):
    monto = forms.CharField(
        label="Monto (en pesos)",
        help_text="Solo números, por ejemplo 25.000.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
        error_messages={"required": MENSAJE_MONTO},
    )
    fecha = forms.DateField(
        label="Fecha",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"required": MENSAJE_FECHA, "invalid": MENSAJE_FECHA},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.localdate()
        self.fields["fecha"].initial = hoy  # se propone el día de hoy
        self.fields["fecha"].widget.attrs["max"] = hoy.isoformat()

    def clean_monto(self):
        """RN-13: el monto es mayor a 0."""
        valor = interpretar_monto(self.cleaned_data["monto"])
        if valor is None:
            raise forms.ValidationError(MENSAJE_MONTO)
        return valor

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha > timezone.localdate():
            raise forms.ValidationError("La fecha no puede ser futura: registra lo que ya ocurrió.")
        if fecha.year < PRIMER_ANIO:
            raise forms.ValidationError(f"Indica una fecha a partir del año {PRIMER_ANIO}.")
        return fecha


class IngresoForm(_RegistroForm):
    """HU-19 · RF-21: monto y fecha."""


class GastoForm(_RegistroForm):
    """HU-20 · RF-22: monto, categoría y fecha."""

    categoria = forms.ChoiceField(
        label="Categoría del gasto",
        choices=CategoriaGasto.choices,
        widget=forms.RadioSelect,
        error_messages={"required": "Elige la categoría del gasto.", "invalid_choice": "Elige la categoría del gasto."},
    )
    field_order = ["monto", "categoria", "fecha"]


class PeriodoForm(forms.Form):
    """HU-21: selector del mes del resumen."""

    # Los navegadores sin selector de mes muestran un campo de texto: se indica el formato.
    mes = forms.CharField(
        label="Mes",
        widget=forms.DateInput(attrs={"type": "month", "placeholder": "AAAA-MM", "pattern": r"\d{4}-\d{2}"}),
    )
