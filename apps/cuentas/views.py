"""
Vistas del módulo E1 · Cuentas y acceso (capa de presentación).

CU-01 registro · CU-02 inicio y cierre de sesión · CU-03 recuperación de contraseña.
"""
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import FormView

from .forms import IngresoForm, RecuperarContrasenaForm, RegistroForm, RestablecerContrasenaForm
from .servicios import RegistroRechazado, registrar_usuario


class RegistroView(FormView):
    """HU-01 · CU-01 (diagramas A1 y S1)."""

    template_name = "cuentas/registro.html"
    form_class = RegistroForm
    success_url = reverse_lazy("cuentas:ingresar")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("cuentas:mi_cuenta")
        return super().dispatch(request, *args, **kwargs)

    def destino_seguro(self):
        """RNF-02: conserva la página de origen (p. ej. un producto) si es de este mismo sitio."""
        destino = self.request.POST.get("next") or self.request.GET.get("next") or ""
        seguro = url_has_allowed_host_and_scheme(
            destino, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()
        )
        return destino if destino and seguro else ""

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "next": self.destino_seguro()}

    def get_success_url(self):
        destino = self.destino_seguro()
        ingreso = reverse("cuentas:ingresar")
        return f"{ingreso}?next={quote(destino, safe='/')}" if destino else ingreso

    def form_valid(self, form):
        datos = form.cleaned_data
        try:
            usuario = registrar_usuario(
                correo=datos["correo_institucional"],
                contrasena=datos["contrasena"],
                rol=datos["rol"],
                acepta_aviso=datos["acepta_aviso"],
            )
        except RegistroRechazado as rechazo:
            campo = "acepta_aviso" if rechazo.codigo == "sin_consentimiento" else "correo_institucional"
            form.add_error(campo, rechazo.mensaje)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Tu cuenta fue creada con el rol {usuario.get_rol_display().lower()}. "
            "Ya puedes iniciar sesión.",
        )
        return super().form_valid(form)


class IngresoView(auth_views.LoginView):
    """HU-02 · CU-02. La sesión se renueva al ingresar (evita la fijación de sesión)."""

    template_name = "cuentas/ingresar.html"
    authentication_form = IngresoForm
    redirect_authenticated_user = True


class SalidaView(auth_views.LogoutView):
    """HU-02 Esc. 3. Solo acepta POST, con token CSRF."""

    next_page = reverse_lazy("inicio")

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.info(request, "Cerraste sesión. Tus páginas privadas ya no están disponibles.")
        return respuesta


@login_required
def mi_cuenta(request):
    """Página privada con los datos de la cuenta del usuario con sesión (RNF-05)."""
    return render(request, "cuentas/mi_cuenta.html", {"usuario": request.user})


class RecuperarView(auth_views.PasswordResetView):
    """HU-03 · CU-03. Siempre redirige a la misma página con un mensaje neutro."""

    template_name = "cuentas/recuperar.html"
    form_class = RecuperarContrasenaForm
    email_template_name = "cuentas/correo/recuperar.txt"
    subject_template_name = "cuentas/correo/recuperar_asunto.txt"
    success_url = reverse_lazy("cuentas:recuperar_enviado")

    def form_valid(self, form):
        # Los correos no pasan por los procesadores de contexto: se envía el nombre explícitamente.
        self.extra_email_context = {"NOMBRE_PLATAFORMA": settings.NOMBRE_PLATAFORMA}
        return super().form_valid(form)


class RecuperarEnviadoView(auth_views.PasswordResetDoneView):
    template_name = "cuentas/recuperar_enviado.html"


class RestablecerView(auth_views.PasswordResetConfirmView):
    template_name = "cuentas/restablecer.html"
    form_class = RestablecerContrasenaForm
    success_url = reverse_lazy("cuentas:restablecer_completo")


class RestablecerCompletoView(auth_views.PasswordResetCompleteView):
    template_name = "cuentas/restablecer_completo.html"
