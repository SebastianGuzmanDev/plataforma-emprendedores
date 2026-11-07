"""
Reglas de negocio de la Épica 6 (Entregable 2, sección 2.1.3) como funciones puras.

- RN-13: el monto de un ingreso o de un gasto es mayor a 0.
- RN-14: cada emprendedor ve solo sus datos financieros (servicios.py y views.py).
- RN-15: el resumen financiero incluye solo los movimientos del periodo elegido.
"""
import re
from datetime import date

from apps.perfil_productos.reglas import interpretar_precio

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
PRIMER_ANIO = 2000
ULTIMO_ANIO = 2100
_PERIODO = re.compile(r"^(\d{4})-(\d{2})$")


def interpretar_monto(texto):
    """RN-13 · Monto en pesos (entero > 0) o None. Acepta «5000», «5.000» y «$ 5.000»."""
    valor = interpretar_precio(texto)
    return valor if valor else None


def interpretar_periodo(texto):
    """RN-15 · «AAAA-MM» → (año, mes), o None si no es un mes válido."""
    coincidencia = _PERIODO.match(str(texto or "").strip())
    if not coincidencia:
        return None
    anio, mes = int(coincidencia[1]), int(coincidencia[2])
    if not (PRIMER_ANIO <= anio <= ULTIMO_ANIO and 1 <= mes <= 12):
        return None
    return anio, mes


def limites_del_mes(anio, mes):
    """Primer día del mes y primer día del mes siguiente (intervalo semiabierto)."""
    inicio = date(anio, mes, 1)
    return inicio, mes_siguiente(inicio)


def mes_anterior(dia):
    return date(dia.year - 1, 12, 1) if dia.month == 1 else date(dia.year, dia.month - 1, 1)


def mes_siguiente(dia):
    return date(dia.year + 1, 1, 1) if dia.month == 12 else date(dia.year, dia.month + 1, 1)


def nombre_del_mes(dia):
    """date(2026, 11, 1) → «Noviembre de 2026»."""
    return f"{MESES[dia.month - 1].capitalize()} de {dia.year}"
