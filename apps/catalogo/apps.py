from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    """Módulo E3 · Catálogo (listado, filtro por categoría, búsqueda y detalle)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogo"
    verbose_name = "E3 · Catálogo"
