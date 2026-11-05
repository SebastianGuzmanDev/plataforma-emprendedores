from django.utils.cache import add_never_cache_headers, patch_cache_control


class SinCacheParaSesionesMiddleware:
    """
    RNF-05 y HU-02 Esc. 3: toda respuesta servida a un usuario con sesión se marca
    como privada y no almacenable. Así, tras cerrar sesión, el botón «atrás» del
    navegador no vuelve a mostrar páginas con datos privados.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        usuario = getattr(request, "user", None)
        if usuario is not None and usuario.is_authenticated:
            add_never_cache_headers(respuesta)
            patch_cache_control(respuesta, private=True)
        return respuesta
