"""Rutas de la aplicación: un grupo de rutas por módulo (épica)."""
from django.conf import settings
from django.conf.urls.static import static
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
    # E2 · Perfil y productos
    path("emprendimiento/", include("apps.perfil_productos.urls")),
    # E3 · Catálogo
    path("catalogo/", include("apps.catalogo.urls")),
    # E4 · Contacto por chat
    path("mensajes/", include("apps.contacto.urls")),
    # E5 · Inventario
    path("inventario/", include("apps.inventario.urls")),
    path("finanzas/", include("apps.finanzas.urls")),
    path("administracion/", include("apps.administracion.urls")),
]

if settings.DEBUG:
    # En desarrollo Django sirve las fotos; en producción las sirve el almacenamiento (D5).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
