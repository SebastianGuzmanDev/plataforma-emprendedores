"""Ayudas de las pruebas de la Épica 6."""
from datetime import date

from django.urls import reverse

from apps.cuentas.tests.utilidades import crear_usuario  # noqa: F401
from apps.finanzas.models import CategoriaGasto, Gasto, Ingreso
from apps.perfil_productos.tests.utilidades import (  # noqa: F401
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    crear_emprendedor,
    entrar,
)

URL_FINANZAS = reverse("finanzas:resumen")
URL_NUEVO_INGRESO = reverse("finanzas:nuevo_ingreso")
URL_NUEVO_GASTO = reverse("finanzas:nuevo_gasto")


def ingreso(usuario, monto, fecha=None):
    return Ingreso.objects.create(propietario=usuario, monto=monto, fecha=fecha or date.today())


def gasto(usuario, monto, categoria=CategoriaGasto.MATERIA_PRIMA, fecha=None):
    return Gasto.objects.create(propietario=usuario, monto=monto, categoria=categoria, fecha=fecha or date.today())
