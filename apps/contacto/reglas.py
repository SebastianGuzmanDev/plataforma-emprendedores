"""
Reglas de negocio de la Épica 4 (Entregable 2, sección 2.1.3).

- RN-16: un mensaje vacío no se envía; el historial se conserva al reabrir la sesión y la
  mensajería es asíncrona (la respuesta se ve al actualizar la vista, D3).
- RN-17: la lista de conversaciones se ordena por el mensaje más reciente (servicios.py).
- RN-18: en un producto propio no aparece «Contactar» (servicios.py y la base de datos).
"""
LONGITUD_MAXIMA_MENSAJE = 1000


def limpiar_mensaje(texto):
    """RN-16 · Devuelve el texto sin espacios sobrantes, o None si está vacío o es demasiado largo."""
    limpio = (texto or "").strip()
    if not limpio or len(limpio) > LONGITUD_MAXIMA_MENSAJE:
        return None
    return limpio
