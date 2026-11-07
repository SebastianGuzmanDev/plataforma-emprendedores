from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    # HU-07 · RF-09 (con HU-08 · RF-10 y HU-10 · RF-11 como parámetros ?categoria= y ?q=)
    path("", views.listado, name="listado"),
    # HU-09 · RF-12 (el botón «Contactar» apunta al módulo E4: contacto:iniciar)
    path("productos/<uuid:codigo>/", views.detalle, name="detalle"),
]
