from django.apps import AppConfig


class FinanzasConfig(AppConfig):
    """Módulo E6 · Finanzas (ingresos, gastos y resumen por periodo)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finanzas"
    verbose_name = "E6 · Finanzas"
