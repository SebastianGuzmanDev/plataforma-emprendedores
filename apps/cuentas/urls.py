from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    # HU-01 · RF-01, RF-03
    path("registro/", views.RegistroView.as_view(), name="registro"),
    # HU-02 · RF-02
    path("ingresar/", views.IngresoView.as_view(), name="ingresar"),
    path("salir/", views.SalidaView.as_view(), name="salir"),
    path("mi-cuenta/", views.mi_cuenta, name="mi_cuenta"),
    # RF-03 · acceso por rol
    path("panel/emprendedor/", views.panel_emprendedor, name="panel_emprendedor"),
    path("panel/administracion/", views.panel_administracion, name="panel_administracion"),
    # HU-03 · RF-04
    path("recuperar/", views.RecuperarView.as_view(), name="recuperar"),
    path("recuperar/enviado/", views.RecuperarEnviadoView.as_view(), name="recuperar_enviado"),
    path("restablecer/<uidb64>/<token>/", views.RestablecerView.as_view(), name="restablecer"),
    path("restablecer/completo/", views.RestablecerCompletoView.as_view(), name="restablecer_completo"),
]
