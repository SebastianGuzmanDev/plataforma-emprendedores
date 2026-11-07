"""E7: código aleatorio por cuenta para las rutas de administración (sin ids secuenciales en las URL)."""
import uuid

from django.db import migrations, models


def asignar_codigos(apps, schema_editor):
    Usuario = apps.get_model("cuentas", "Usuario")
    for usuario in Usuario.objects.filter(codigo__isnull=True).only("pk"):
        usuario.codigo = uuid.uuid4()
        usuario.save(update_fields=["codigo"])


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0001_initial"),
    ]

    operations = [
        # En tres pasos para que las cuentas existentes reciban códigos distintos.
        migrations.AddField(
            model_name="usuario",
            name="codigo",
            field=models.UUIDField(editable=False, null=True, verbose_name="código"),
        ),
        migrations.RunPython(asignar_codigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="usuario",
            name="codigo",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="código"),
        ),
    ]
