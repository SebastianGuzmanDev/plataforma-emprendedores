from django.urls import path

from . import views

app_name = "contacto"

urlpatterns = [
    # HU-13 · RF-15
    path("", views.lista, name="lista"),
    # HU-11 · RF-13 (botón «Contactar» del detalle del producto)
    path("iniciar/<uuid:codigo_producto>/", views.iniciar, name="iniciar"),
    # HU-12 · RF-14 (historial y envío) · HU-14 (al abrirla se marcan como leídos)
    path("<uuid:codigo>/", views.conversacion, name="conversacion"),
]
