from django.urls import path

from . import views

app_name = "emprendimiento"

urlpatterns = [
    path("", views.panel, name="panel"),
    # HU-04 · RF-05
    path("perfil/", views.perfil, name="perfil"),
    path("vista-previa/", views.vista_previa, name="vista_previa"),
    # HU-05 · RF-06
    path("productos/nuevo/", views.publicar, name="publicar"),
    # HU-06 · RF-07, RF-08
    path("productos/<uuid:codigo>/editar/", views.editar, name="editar"),
    path("productos/<uuid:codigo>/agotado/", views.agotado, name="agotado"),
    path("productos/<uuid:codigo>/desactivar/", views.desactivar, name="desactivar"),
]
