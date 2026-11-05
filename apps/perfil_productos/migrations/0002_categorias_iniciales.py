"""Categorías del Entregable 1 (alcance del MVP): comida, artesanías, videojuegos, ocio y «Otros» por el «etc.»."""
from django.db import migrations

CATEGORIAS = ["Comida", "Artesanías", "Videojuegos", "Ocio", "Otros"]


def crear(apps, schema_editor):
    Categoria = apps.get_model("perfil_productos", "Categoria")
    for nombre in CATEGORIAS:
        Categoria.objects.get_or_create(nombre=nombre)


def borrar(apps, schema_editor):
    apps.get_model("perfil_productos", "Categoria").objects.filter(nombre__in=CATEGORIAS).delete()


class Migration(migrations.Migration):
    dependencies = [("perfil_productos", "0001_initial")]
    operations = [migrations.RunPython(crear, borrar)]
