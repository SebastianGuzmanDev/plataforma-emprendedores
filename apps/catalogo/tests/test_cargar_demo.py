"""
Comando `cargar_demo`: datos de demostración para probar el catálogo y medir RNF-01.
Mitiga el riesgo R4 (demo sin contenido) del Entregable 1.
"""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.cuentas.models import Usuario
from apps.cuentas.tests.utilidades import crear_usuario
from apps.perfil_productos.models import Emprendimiento, Producto

from .utilidades import MediaTemporalMixin


class CargarDemoTests(MediaTemporalMixin, TestCase):
    def cargar(self, *argumentos):
        salida = StringIO()
        call_command("cargar_demo", *argumentos, stdout=salida)
        return salida.getvalue()

    def test_en_produccion_se_niega_salvo_que_se_fuerce(self):
        with self.assertRaisesMessage(CommandError, "--forzar"):
            self.cargar("--productos", "2")
        self.assertFalse(Producto.objects.exists())

    @override_settings(DEBUG=True)
    def test_crea_emprendimientos_productos_y_un_comprador_de_demostracion(self):
        salida = self.cargar("--emprendimientos", "3", "--productos", "12")
        self.assertEqual(Emprendimiento.objects.count(), 3)
        self.assertEqual(Producto.objects.count(), 12)
        self.assertTrue(Producto.objects.visibles_en_catalogo().exists())
        self.assertTrue(all(p.miniatura for p in Producto.objects.all()))
        correos = list(Usuario.objects.values_list("correo_institucional", flat=True))
        self.assertTrue(all(c.startswith("demo.") and c.endswith("@amigo.edu.co") for c in correos))
        self.assertIn("demo.comprador@amigo.edu.co", correos)
        self.assertIn("demo.comprador@amigo.edu.co", salida)

    @override_settings(DEBUG=True)
    def test_crea_conversaciones_de_demostracion_con_mensajes_sin_leer(self):
        from apps.contacto.models import Conversacion
        from apps.contacto.servicios import mensajes_sin_leer

        self.cargar("--emprendimientos", "3", "--productos", "9", "--conversaciones", "2", "--solo-disponibles")
        self.assertEqual(Conversacion.objects.count(), 2)
        comprador = Usuario.objects.get(correo_institucional="demo.comprador@amigo.edu.co")
        self.assertTrue(all(c.comprador == comprador for c in Conversacion.objects.all()))
        emprendedor = Usuario.objects.get(correo_institucional="demo.emprendedor02@amigo.edu.co")
        self.assertGreater(mensajes_sin_leer(emprendedor), 0)

    @override_settings(DEBUG=True)
    def test_carga_existencias_coherentes_e_insumos_de_demostracion(self):
        from apps.inventario.models import Insumo

        self.cargar("--emprendimientos", "2", "--productos", "8")
        con_inventario = Producto.objects.exclude(existencias=None)
        self.assertTrue(con_inventario.exists())
        self.assertFalse(con_inventario.filter(estado="DISPONIBLE", existencias=0).exists())
        self.assertFalse(con_inventario.filter(estado="AGOTADO").exclude(existencias=0).exists())
        self.assertTrue(Insumo.objects.exists())

    @override_settings(DEBUG=True)
    def test_solo_disponibles_deja_todos_los_productos_visibles(self):
        self.cargar("--emprendimientos", "2", "--productos", "6", "--solo-disponibles")
        self.assertEqual(Producto.objects.visibles_en_catalogo().filter(estado="DISPONIBLE").count(), 6)

    @override_settings(DEBUG=True)
    def test_limpiar_borra_solo_los_datos_de_demostracion(self):
        real = crear_usuario(correo="persona.real@amigo.edu.co")
        self.cargar("--emprendimientos", "2", "--productos", "4")
        self.cargar("--limpiar", "--emprendimientos", "1", "--productos", "2")
        self.assertEqual(Producto.objects.count(), 2)
        self.assertTrue(Usuario.objects.filter(pk=real.pk).exists())

    @override_settings(DEBUG=True)
    def test_carga_ingresos_y_gastos_de_demostracion_en_varios_meses(self):
        """E6: el resumen financiero de la demo no aparece vacío y permite cambiar de mes."""
        from django.utils import timezone

        from apps.finanzas.models import CategoriaGasto, Gasto, Ingreso
        from apps.finanzas.reglas import mes_anterior

        self.cargar("--emprendimientos", "2", "--productos", "4")
        hoy = timezone.localdate()
        inicio = hoy.replace(day=1)
        emprendedor = Usuario.objects.get(correo_institucional="demo.emprendedor01@amigo.edu.co")
        self.assertTrue(Ingreso.objects.filter(propietario=emprendedor, fecha__gte=inicio).exists())
        self.assertTrue(Gasto.objects.filter(propietario=emprendedor, fecha__gte=inicio).exists())
        self.assertTrue(Ingreso.objects.filter(
            propietario=emprendedor, fecha__gte=mes_anterior(inicio), fecha__lt=inicio).exists())
        self.assertFalse(Ingreso.objects.filter(fecha__gt=hoy).exists())
        self.assertFalse(Gasto.objects.filter(fecha__gt=hoy).exists())
        # CC-10: los insumos de la demo también quedan como gasto de materia prima
        self.assertEqual(
            Gasto.objects.filter(propietario=emprendedor, categoria=CategoriaGasto.MATERIA_PRIMA, fecha=hoy).count(),
            emprendedor.insumos.count(),
        )

    @override_settings(DEBUG=True)
    def test_crea_un_administrador_y_una_desactivacion_con_aviso_pendiente(self):
        """E7: cuenta de administración y un producto desactivado por ella, con aviso para su dueño."""
        from apps.administracion.models import Desactivacion
        from apps.administracion.servicios import avisos_pendientes
        from apps.cuentas.models import Rol

        self.cargar("--emprendimientos", "2", "--productos", "6")
        admin = Usuario.objects.get(correo_institucional="demo.administrador@amigo.edu.co")
        self.assertEqual(admin.rol, Rol.ADMINISTRADOR)
        registro = Desactivacion.objects.get()
        self.assertEqual((registro.administrador, registro.producto.estado), (admin, "DESACTIVADO"))
        dueno = registro.producto.emprendimiento.propietario
        self.assertEqual(dueno.correo_institucional, "demo.emprendedor02@amigo.edu.co")
        self.assertEqual(avisos_pendientes(dueno).count(), 1)
        # Cargar de nuevo no duplica la desactivación
        self.cargar("--emprendimientos", "2", "--productos", "0")
        self.assertEqual(Desactivacion.objects.count(), 1)
