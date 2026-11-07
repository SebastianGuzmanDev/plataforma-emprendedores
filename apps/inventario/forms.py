"""Formularios del módulo E5 (capa de presentación)."""
from django import forms

from apps.perfil_productos.reglas import interpretar_precio

from .models import TipoMovimiento
from .reglas import interpretar_cantidad_insumo, interpretar_entero

ENTERO = {"inputmode": "numeric", "autocomplete": "off"}


class ExistenciasForm(forms.Form):
    """HU-15 · RN-10."""

    existencias = forms.CharField(
        label="Existencias actuales (unidades)",
        help_text="Cuántas unidades tienes hoy. Solo números enteros, por ejemplo 25.",
        widget=forms.TextInput(attrs=ENTERO),
        error_messages={"required": "Escribe una cantidad en unidades enteras (0 o más), sin decimales ni signos."},
    )

    def clean_existencias(self):
        valor = interpretar_entero(self.cleaned_data["existencias"])
        if valor is None:
            raise forms.ValidationError("Escribe una cantidad en unidades enteras (0 o más), sin decimales ni signos.")
        return valor


class MovimientoForm(forms.Form):
    """HU-16 · A4: «¿La cantidad es válida?»."""

    tipo = forms.ChoiceField(
        label="Tipo de movimiento",
        choices=[(TipoMovimiento.ENTRADA, "Entrada: preparé o repuse"), (TipoMovimiento.SALIDA, "Salida: vendí o retiré")],
        widget=forms.RadioSelect,
        error_messages={"required": "Elige si es una entrada o una salida.",
                        "invalid_choice": "Elige si es una entrada o una salida."},
    )
    cantidad = forms.CharField(
        label="Cantidad (unidades)",
        widget=forms.TextInput(attrs=ENTERO),
        error_messages={"required": "Escribe una cantidad entera de al menos 1 unidad."},
    )

    def clean_cantidad(self):
        valor = interpretar_entero(self.cleaned_data["cantidad"], minimo=1)
        if valor is None:
            raise forms.ValidationError("Escribe una cantidad entera de al menos 1 unidad.")
        return valor


class UmbralForm(forms.Form):
    """HU-17 · supuesto S-6: el umbral es de cada producto."""

    umbral_stock_bajo = forms.CharField(
        label="Avisarme cuando queden menos de (unidades)",
        required=False,
        help_text="Déjalo vacío para no recibir alertas.",
        widget=forms.TextInput(attrs=ENTERO),
    )

    def clean_umbral_stock_bajo(self):
        texto = self.cleaned_data["umbral_stock_bajo"].strip()
        if not texto:
            return None
        valor = interpretar_entero(texto, minimo=1)
        if valor is None:
            raise forms.ValidationError("El umbral debe ser un número entero de al menos 1 (o déjalo vacío para quitarlo).")
        return valor


class InsumoForm(forms.Form):
    """HU-18 · RN-12: nombre, cantidad distinta de 0 y costo."""

    nombre = forms.CharField(
        label="Nombre del insumo",
        max_length=80,
        help_text="Incluye la unidad, por ejemplo «Harina de maíz (kg)».",
        error_messages={"required": "Escribe el nombre del insumo."},
    )
    cantidad = forms.CharField(
        label="Cantidad",
        help_text="Puede tener decimales, por ejemplo 2,5.",
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}),
        error_messages={"required": "La cantidad debe ser mayor que 0."},
    )
    costo = forms.CharField(
        label="Costo total (en pesos)",
        help_text="Lo que pagaste por esa cantidad, por ejemplo 12.000.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
        error_messages={"required": "Escribe el costo total del insumo en pesos."},
    )
    # CC-10 (E6): relación insumo → gasto de materia prima (HU-20)
    registrar_como_gasto = forms.BooleanField(
        label="Registrar también este costo como un gasto de materia prima de hoy en Finanzas",
        required=False,
        initial=True,
    )

    def clean_cantidad(self):
        valor = interpretar_cantidad_insumo(self.cleaned_data["cantidad"])
        if valor is None:
            raise forms.ValidationError("La cantidad debe ser mayor que 0 (hasta 3 decimales).")
        return valor

    def clean_costo(self):
        valor = interpretar_precio(self.cleaned_data["costo"])
        if valor is None:
            raise forms.ValidationError("Escribe el costo total del insumo en pesos, solo con números.")
        return valor
