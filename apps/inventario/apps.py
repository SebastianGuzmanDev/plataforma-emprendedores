from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Módulo E5 · Inventario (existencias, entradas y salidas, alerta de stock bajo e insumos)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inventario"
    verbose_name = "E5 · Inventario"
