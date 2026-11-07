from django.urls import path

from . import views

app_name = "administracion"

urlpatterns = [
    path("", views.panel, name="panel"),
    # HU-22 · RF-24 · Esc. 1
    path("productos/", views.productos, name="productos"),
    path("productos/<uuid:codigo>/desactivar/", views.desactivar_producto, name="desactivar_producto"),
    # HU-22 · RF-24 · Esc. 2
    path("cuentas/", views.cuentas, name="cuentas"),
    path("cuentas/<uuid:codigo>/desactivar/", views.desactivar_cuenta, name="desactivar_cuenta"),
    path("cuentas/<uuid:codigo>/reactivar/", views.reactivar_cuenta, name="reactivar_cuenta"),
    # CC-11: avisos para el dueño del producto
    path("avisos/", views.avisos, name="avisos"),
]
