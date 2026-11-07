"""
Reglas de negocio de la Épica 5 (Entregable 2, sección 2.1.3).

- RN-10: las existencias son enteros no negativos; una salida no puede superar las
  existencias; si quedan en 0, el producto pasa a Agotado (servicios.py).
- RN-11: alerta cuando las existencias bajan del umbral (Producto.tiene_stock_bajo).
- RN-12: un insumo requiere nombre, cantidad distinta de 0 y costo.
"""
import re
from decimal import Decimal, InvalidOperation

MAXIMO_UNIDADES = 999_999
_ENTERO = re.compile(r"^\d{1,6}$")
_DECIMAL = re.compile(r"^\d{1,7}([.,]\d{1,3})?$")


def interpretar_entero(texto, minimo=0):
    """RN-10 · Entero sin signos ni decimales, entre `minimo` y 999.999. None si no es válido."""
    limpio = (texto or "").strip() if isinstance(texto, str) or texto is None else str(texto)
    if not _ENTERO.match(limpio):
        return None
    valor = int(limpio)
    return valor if minimo <= valor <= MAXIMO_UNIDADES else None


def interpretar_cantidad_insumo(texto):
    """RN-12 · Cantidad mayor que 0, con coma o punto decimal (hasta 3 decimales): «2,5» kg."""
    limpio = (texto or "").strip() if isinstance(texto, str) or texto is None else str(texto)
    if not _DECIMAL.match(limpio):
        return None
    try:
        valor = Decimal(limpio.replace(",", "."))
    except InvalidOperation:
        return None
    return valor if valor > 0 else None
