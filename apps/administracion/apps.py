from django.apps import AppConfig


class AdministracionConfig(AppConfig):
    """Módulo E7 · Administración (desactivación de productos y cuentas que incumplen las reglas)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.administracion"
    verbose_name = "E7 · Administración"
