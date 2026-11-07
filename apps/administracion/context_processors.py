from .servicios import avisos_pendientes


def avisos_administracion(request):
    """CC-11: aviso en todas las páginas mientras el emprendedor tenga desactivaciones sin ver."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated or not usuario.es_emprendedor:
        return {"avisos_administracion": 0}
    return {"avisos_administracion": avisos_pendientes(usuario).count()}
