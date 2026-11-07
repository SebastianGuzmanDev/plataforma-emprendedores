"""
CC-06 · Miniatura de cada producto para el catálogo (RNF-01).

Genera las miniaturas de los productos que ya existían. Si la foto original no está
en el almacenamiento (por ejemplo, datos de prueba), se deja vacía y el catálogo usa
la foto completa.
"""
import io

from django.core.files.base import ContentFile
from django.db import migrations, models

LADO = 600


def generar(apps, schema_editor):
    from PIL import Image, ImageOps

    Producto = apps.get_model("perfil_productos", "Producto")
    for producto in Producto.objects.filter(miniatura=""):
        if not producto.foto or not producto.foto.storage.exists(producto.foto.name):
            continue
        with producto.foto.open("rb") as archivo:
            imagen = ImageOps.exif_transpose(Image.open(archivo)).convert("RGB")
        imagen.thumbnail((LADO, LADO))
        salida = io.BytesIO()
        imagen.save(salida, "JPEG", quality=80, optimize=True, progressive=True)
        nombre = producto.foto.name.rsplit("/", 1)[-1]
        producto.miniatura.save(nombre, ContentFile(salida.getvalue()), save=False)
        producto.save(update_fields=["miniatura"])


class Migration(migrations.Migration):
    dependencies = [("perfil_productos", "0003_nombre_emprendimiento")]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="miniatura",
            field=models.ImageField(blank=True, upload_to="productos/miniaturas/", verbose_name="miniatura"),
        ),
        migrations.RunPython(generar, migrations.RunPython.noop),
    ]
