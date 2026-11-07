"""E5 · Atributos existencias y umbralStockBajo de Producto (modelo de dominio del Entregable 2)."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("perfil_productos", "0004_miniatura")]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="existencias",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="existencias"),
        ),
        migrations.AddField(
            model_name="producto",
            name="umbral_stock_bajo",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="umbral de stock bajo"),
        ),
    ]
