"""
Control de acceso por rol (RF-03). Lo usan las épicas siguientes, por ejemplo:

    @rol_requerido(Rol.EMPRENDEDOR)
    def mis_productos(request): ...
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """Sin sesión → pide iniciar sesión. Con otro rol → 403 (acceso denegado)."""

    def decorador(vista):
        @wraps(vista)
        @login_required
        def vista_protegida(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return vista_protegida

    return decorador
