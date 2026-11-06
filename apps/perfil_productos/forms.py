"""Formularios del módulo E2 (capa de presentación)."""
from django import forms

from .models import Categoria, Emprendimiento
from .reglas import TIPOS_FOTO, interpretar_precio, validar_foto

MENSAJE_PRECIO = "Escribe el precio solo con números, sin signos negativos ni letras (por ejemplo, 5000 o 5.000)."


class PerfilForm(forms.ModelForm):
    """HU-04 · RF-05 · RN-06: todos los campos son obligatorios (el nombre lo agrega CC-03)."""

    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=Categoria.objects.all(),
        empty_label=None,
        widget=forms.RadioSelect,
        error_messages={
            "required": "Elige la categoría de tu emprendimiento.",
            "invalid_choice": "Elige la categoría de tu emprendimiento.",
        },
    )

    class Meta:
        model = Emprendimiento
        fields = ["nombre", "descripcion", "categoria", "horarios", "zona_entrega"]
        labels = {
            "nombre": "Nombre del emprendimiento",
            "descripcion": "Descripción",
            "horarios": "Horarios de atención",
            "zona_entrega": "Zona de entrega",
        }
        help_texts = {
            "nombre": "Así te reconocerán los compradores. Por ejemplo: Arepas Doña Rosa.",
            "descripcion": "Cuenta qué vendes y qué hace especial a tu emprendimiento (máximo 500 caracteres).",
            "horarios": "Por ejemplo: lunes a viernes, 10:00 a 14:00.",
            "zona_entrega": "Dónde entregas dentro del campus. Por ejemplo: bloque 3, frente a la cafetería.",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"maxlength": 80}),
            "descripcion": forms.Textarea(attrs={"rows": 4, "maxlength": 500}),
            "horarios": forms.TextInput(attrs={"maxlength": 120}),
            "zona_entrega": forms.TextInput(attrs={"maxlength": 120}),
        }
        error_messages = {
            "nombre": {
                "required": "Escribe el nombre de tu emprendimiento.",
                "max_length": "El nombre puede tener hasta 80 caracteres (tiene %(show_value)d).",
            },
            "descripcion": {
                "required": "Escribe la descripción de tu emprendimiento.",
                "max_length": "La descripción puede tener hasta 500 caracteres (tiene %(show_value)d).",
            },
            "horarios": {"required": "Indica tus horarios de atención."},
            "zona_entrega": {"required": "Indica la zona de entrega."},
        }


class ProductoForm(forms.Form):
    """HU-05 / HU-06 · RF-06, RF-07 · RN-07."""

    nombre = forms.CharField(
        label="Nombre del producto",
        max_length=80,
        error_messages={"required": "Escribe el nombre del producto.",
                        "max_length": "El nombre puede tener hasta 80 caracteres."},
    )
    foto = forms.FileField(
        label="Foto",
        help_text="JPG, PNG o WebP de hasta 5 MB. Quitamos los datos ocultos de la foto, como la ubicación.",
        widget=forms.ClearableFileInput(attrs={"accept": TIPOS_FOTO}),
        error_messages={"required": "Agrega una foto del producto."},
    )
    precio_referencia = forms.CharField(
        label="Precio de referencia (en pesos)",
        max_length=20,
        help_text="Solo números, por ejemplo 5000 o 5.000. Es un precio de referencia: la venta se acuerda por chat.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
        error_messages={"required": MENSAJE_PRECIO},
    )

    def __init__(self, *args, foto_obligatoria=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["foto"].required = foto_obligatoria
        if not foto_obligatoria:
            self.fields["foto"].label = "Cambiar foto (opcional)"
            self.fields["foto"].widget = forms.FileInput(attrs={"accept": TIPOS_FOTO})

    def clean_foto(self):
        """A2 / S3: primero se valida el tamaño de la foto…"""
        foto = self.cleaned_data.get("foto")
        if foto:
            validar_foto(foto)
        return foto

    def clean_precio_referencia(self):
        """…y luego el precio."""
        precio = interpretar_precio(self.cleaned_data.get("precio_referencia"))
        if precio is None:
            raise forms.ValidationError(MENSAJE_PRECIO, code="precio_invalido")
        return precio
