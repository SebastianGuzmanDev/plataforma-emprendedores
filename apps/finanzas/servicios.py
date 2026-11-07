"""
Servicios de la Épica 6 (casos de uso CU-19 a CU-21; supuestos S-3, S-5 y S-7).

Todas las consultas parten del usuario de la sesión (RN-14 · RNF-05): no existe una
operación que reciba un propietario distinto del que la invoca.
"""
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date

from django.db.models import Sum

from .models import CategoriaGasto, Gasto, Ingreso
from .reglas import limites_del_mes


@dataclass(frozen=True)
class Movimiento:
    """Fila del detalle del resumen (ingreso o gasto)."""

    tipo: str  # "ingreso" | "gasto"
    codigo: object
    monto: int
    fecha: date
    categoria: str = ""


@dataclass
class ResumenFinanciero:
    """Clase DERIVADA del modelo de dominio (supuesto S-7): no se almacena."""

    periodo: date
    total_ingresos: int = 0
    total_gastos: int = 0
    gastos_por_categoria: "OrderedDict[str, int]" = field(default_factory=OrderedDict)
    movimientos: list = field(default_factory=list)

    @property
    def balance(self):
        return self.total_ingresos - self.total_gastos


def registrar_ingreso(propietario, *, monto, fecha):
    """HU-19 · CU-19 · RN-13 (validado en el formulario y en la base de datos)."""
    return Ingreso.objects.create(propietario=propietario, monto=monto, fecha=fecha)


def registrar_gasto(propietario, *, monto, categoria, fecha):
    """HU-20 · CU-20 · RN-13."""
    return Gasto.objects.create(propietario=propietario, monto=monto, categoria=categoria, fecha=fecha)


def _entero(valor):
    return int(valor or 0)


def resumen_financiero(usuario, anio, mes):
    """
    HU-21 · CU-21 · supuesto S-7: se calcula a partir de Ingreso y Gasto.

    RN-15: solo los movimientos con fecha dentro del mes; sin movimientos, todo en 0.
    """
    inicio, fin = limites_del_mes(anio, mes)
    ingresos = Ingreso.objects.filter(propietario=usuario, fecha__gte=inicio, fecha__lt=fin)
    gastos = Gasto.objects.filter(propietario=usuario, fecha__gte=inicio, fecha__lt=fin)

    etiquetas = dict(CategoriaGasto.choices)
    por_categoria = OrderedDict(
        (etiquetas[fila["categoria"]], _entero(fila["total"]))
        for fila in gastos.order_by().values("categoria").annotate(total=Sum("monto")).order_by("-total", "categoria")
    )
    movimientos = [Movimiento("ingreso", i.codigo, _entero(i.monto), i.fecha) for i in ingresos] + [
        Movimiento("gasto", g.codigo, _entero(g.monto), g.fecha, g.get_categoria_display()) for g in gastos
    ]
    movimientos.sort(key=lambda m: m.fecha, reverse=True)  # orden estable: dentro del día, el más reciente primero
    return ResumenFinanciero(
        periodo=inicio,
        total_ingresos=_entero(ingresos.aggregate(total=Sum("monto"))["total"]),
        total_gastos=sum(por_categoria.values()),
        gastos_por_categoria=por_categoria,
        movimientos=movimientos,
    )


def registro_de(tipo):
    """Modelo según el tipo de la URL de eliminación."""
    return {"ingreso": Ingreso, "gasto": Gasto}[tipo]
