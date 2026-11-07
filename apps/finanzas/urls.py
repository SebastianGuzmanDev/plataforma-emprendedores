from django.urls import path

from . import views

app_name = "finanzas"

urlpatterns = [
    # HU-21 · RF-23
    path("", views.resumen, name="resumen"),
    # HU-19 · RF-21
    path("ingresos/nuevo/", views.nuevo_ingreso, name="nuevo_ingreso"),
    # HU-20 · RF-22
    path("gastos/nuevo/", views.nuevo_gasto, name="nuevo_gasto"),
    path("<str:tipo>/<uuid:codigo>/eliminar/", views.eliminar, name="eliminar"),
]
