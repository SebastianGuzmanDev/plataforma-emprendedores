"""
RF-03: el rol de administrador se asigna internamente, nunca desde el registro.

Uso:  python manage.py promover_administrador correo@amigo.edu.co
"""
from django.core.management.base import BaseCommand, CommandError

from apps.cuentas.models import Rol, Usuario
from apps.cuentas.reglas import normalizar_correo


class Command(BaseCommand):
    help = "Asigna el rol de administrador a una cuenta ya registrada."

    def add_arguments(self, parser):
        parser.add_argument("correo", help="Correo institucional de la cuenta registrada")

    def handle(self, *args, correo, **opciones):
        correo = normalizar_correo(correo)
        try:
            usuario = Usuario.objects.get(correo_institucional=correo)
        except Usuario.DoesNotExist as error:
            raise CommandError(f"No existe una cuenta registrada con el correo {correo}.") from error
        usuario.rol = Rol.ADMINISTRADOR
        usuario.save(update_fields=["rol"])
        self.stdout.write(self.style.SUCCESS(f"{correo} ahora es administrador."))
