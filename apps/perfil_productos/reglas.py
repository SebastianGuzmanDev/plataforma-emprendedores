"""
Reglas de negocio de la Épica 2 (Entregable 2, sección 2.1.3) como funciones puras.

- RN-05: un emprendedor necesita su perfil para publicar (ver servicios.py).
- RN-06: descripción, categoría, horarios y zona de entrega son obligatorios (forms.py).
- RN-07: la foto pesa hasta 5 MB y el precio no es negativo ni contiene letras.
- RN-08: solo el dueño modifica sus productos (views.py).
- RN-09: el catálogo oculta los productos desactivados (models.py).
"""
import io
import re
import uuid
import warnings

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

LIMITE_FOTO_BYTES = settings.FOTO_LIMITE_MB * 1024 * 1024
FORMATOS_FOTO = {"JPEG", "PNG", "WEBP"}
TIPOS_FOTO = "image/jpeg,image/png,image/webp"
MAXIMO_PIXELES = 40_000_000  # protege contra imágenes diseñadas para agotar la memoria

_PRECIO_SIMPLE = re.compile(r"^\d{1,10}$")
_PRECIO_CON_MILES = re.compile(r"^\d{1,3}(\.\d{3}){1,3}$")


def interpretar_precio(texto):
    """
    RN-07 · Devuelve el precio en pesos (entero ≥ 0) o None si no es válido.

    Acepta «5000», «5.000» y «$ 5.000». Rechaza negativos, letras, decimales y
    separadores ambiguos («12,5», «5.00»).
    """
    if texto is None:
        return None
    limpio = str(texto).strip()
    if limpio.startswith("$"):
        limpio = limpio[1:].strip()
    if _PRECIO_SIMPLE.match(limpio):
        return int(limpio)
    if _PRECIO_CON_MILES.match(limpio):
        return int(limpio.replace(".", ""))
    return None


def _megabytes(tamano):
    return f"{tamano / (1024 * 1024):.1f}".replace(".", ",")


def _abrir_imagen(archivo):
    archivo.seek(0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        imagen = Image.open(archivo)
        if imagen.width * imagen.height > MAXIMO_PIXELES:
            raise Image.DecompressionBombError("demasiados píxeles")
    return imagen


def validar_foto(archivo):
    """RN-07 · Foto de hasta 5 MB y que realmente sea JPG, PNG o WebP."""
    if archivo.size > LIMITE_FOTO_BYTES:
        raise ValidationError(
            f"La foto pesa {_megabytes(archivo.size)} MB y el límite es {settings.FOTO_LIMITE_MB} MB.",
            code="foto_pesada",
        )
    try:
        imagen = _abrir_imagen(archivo)
        formato = imagen.format
        imagen.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as error:
        raise ValidationError(
            "El archivo no es una imagen JPG, PNG o WebP.", code="foto_invalida"
        ) from error
    finally:
        archivo.seek(0)
    if formato not in FORMATOS_FOTO:
        raise ValidationError("El archivo no es una imagen JPG, PNG o WebP.", code="foto_invalida")


def procesar_foto(archivo):
    """
    Normaliza la foto antes de guardarla (D5):
    - corrige la orientación y elimina todos los metadatos EXIF, incluida la ubicación GPS (RNF-06);
    - limita el lado mayor a 1600 px y la guarda como JPEG (catálogo liviano, RNF-01);
    - usa un nombre aleatorio que no revela el nombre original del archivo.
    """
    imagen = _abrir_imagen(archivo)
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ("RGBA", "LA", "P"):
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.getchannel("A"))
        imagen = fondo
    else:
        imagen = imagen.convert("RGB")
    lado = settings.FOTO_LADO_MAXIMO_PX
    imagen.thumbnail((lado, lado), Image.Resampling.LANCZOS)
    salida = io.BytesIO()
    imagen.save(salida, "JPEG", quality=85, optimize=True, progressive=True)
    archivo.seek(0)
    return ContentFile(salida.getvalue(), name=f"{uuid.uuid4().hex}.jpg")
