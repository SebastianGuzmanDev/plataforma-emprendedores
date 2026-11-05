"""Rutas de la aplicación: un grupo de rutas por módulo (épica)."""
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="inicio.html"), name="inicio"),
    path(
        "privacidad/",
        TemplateView.as_view(template_name="legal/aviso_privacidad.html"),
        name="aviso_privacidad",
    ),
    # E1 · Cuentas y acceso
    path("cuentas/", include("apps.cuentas.urls")),
]
