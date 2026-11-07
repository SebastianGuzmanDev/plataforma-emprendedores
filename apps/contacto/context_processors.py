from .servicios import mensajes_sin_leer as contar_sin_leer


def mensajes_sin_leer(request):
    """HU-14: indicador del encabezado. Sin sesión no consulta la base de datos."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {"mensajes_sin_leer": 0}
    return {"mensajes_sin_leer": contar_sin_leer(usuario)}
