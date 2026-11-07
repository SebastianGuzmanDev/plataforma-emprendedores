from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("productos/<uuid:codigo>/", views.producto, name="producto"),
    # HU-15 · RF-17
    path("productos/<uuid:codigo>/existencias/", views.existencias, name="existencias"),
    # HU-16 · RF-18 (y HU-17 · RF-19, alerta)
    path("productos/<uuid:codigo>/movimiento/", views.movimiento, name="movimiento"),
    path("productos/<uuid:codigo>/umbral/", views.umbral, name="umbral"),
    # HU-18 · RF-20
    path("insumos/nuevo/", views.nuevo_insumo, name="nuevo_insumo"),
]
