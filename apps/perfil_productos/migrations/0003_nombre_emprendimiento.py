"""
CC-03 · Nombre del emprendimiento (obligatorio).

Los perfiles creados antes del cambio reciben «Mi emprendimiento» como nombre
provisional; su dueño lo reemplaza al editar el perfil.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("perfil_productos", "0002_categorias_iniciales")]

    operations = [
        migrations.AddField(
            model_name="emprendimiento",
            name="nombre",
            field=models.CharField(default="Mi emprendimiento", max_length=80, verbose_name="nombre"),
            preserve_default=False,
        ),
    ]
