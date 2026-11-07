"""
Pruebas UNITARIAS de las reglas de la Épica 4 (RN-16, RN-17, RN-18) y del modelo
Conversacion / Mensaje del Entregable 2.
"""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.contacto import servicios
from apps.contacto.models import Conversacion, Mensaje
from apps.contacto.reglas import LONGITUD_MAXIMA_MENSAJE, limpiar_mensaje

from .utilidades import CORREO_EMPRENDEDOR_B, crear_conversacion, crear_emprendedor, crear_perfil, crear_producto, escenario


class ReglaMensajeVacioTests(SimpleTestCase):
    """RN-16 · HU-12 Esc. 4: un mensaje vacío no se envía."""

    def test_rn16_vacio_o_solo_espacios_no_es_un_mensaje(self):
        for texto in ["", "   ", "\n\t  \n", None]:
            with self.subTest(texto=repr(texto)):
                self.assertIsNone(limpiar_mensaje(texto))

    def test_rn16_conserva_el_texto_sin_espacios_sobrantes(self):
        self.assertEqual(limpiar_mensaje("  ¿Tienes arepas hoy?  \n"), "¿Tienes arepas hoy?")

    def test_el_mensaje_tiene_un_limite_de_1000_caracteres(self):
        self.assertEqual(LONGITUD_MAXIMA_MENSAJE, 1000)
        self.assertIsNone(limpiar_mensaje("a" * 1001))
        self.assertEqual(len(limpiar_mensaje("a" * 1000)), 1000)


class ModeloConversacionTests(TestCase):
    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()

    def test_una_conversacion_por_comprador_y_producto(self):
        crear_conversacion(self.comprador, self.producto)
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_conversacion(self.comprador, self.producto)

    def test_rn18_la_base_de_datos_impide_conversar_consigo_mismo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Conversacion.objects.create(comprador=self.emprendedor, emprendedor=self.emprendedor, producto=self.producto)

    def test_ultimo_mensaje_es_el_mas_reciente(self):
        conversacion = crear_conversacion(
            self.comprador, self.producto, [(self.comprador, "Hola"), (self.emprendedor, "¡Hola! ¿Qué deseas?")]
        )
        self.assertEqual(conversacion.ultimo_mensaje().contenido, "¡Hola! ¿Qué deseas?")

    def test_marcar_leido(self):
        conversacion = crear_conversacion(self.comprador, self.producto, [(self.comprador, "Hola")])
        mensaje = conversacion.mensajes.get()
        self.assertFalse(mensaje.leido)
        mensaje.marcar_leido()
        mensaje.refresh_from_db()
        self.assertTrue(mensaje.leido)


class ServiciosTests(TestCase):
    """Nombres del diagrama S5: iniciarConversacion, enviarMensaje y obtenerMensajes."""

    def setUp(self):
        self.comprador, self.emprendedor, self.producto = escenario()

    def test_iniciar_conversacion_crea_o_reabre_la_misma(self):
        primera, creada = servicios.iniciar_conversacion(self.comprador, self.producto)
        segunda, creada_otra_vez = servicios.iniciar_conversacion(self.comprador, self.producto)
        self.assertTrue(creada)
        self.assertFalse(creada_otra_vez)
        self.assertEqual(primera, segunda)
        self.assertEqual(primera.emprendedor, self.emprendedor)

    def test_rn18_no_se_inicia_una_conversacion_con_un_producto_propio(self):
        with self.assertRaises(servicios.ContactoNoPermitido):
            servicios.iniciar_conversacion(self.emprendedor, self.producto)

    def test_rn16_enviar_mensaje_vacio_no_registra_nada(self):
        conversacion, _ = servicios.iniciar_conversacion(self.comprador, self.producto)
        with self.assertRaises(servicios.MensajeVacio):
            servicios.enviar_mensaje(conversacion, self.comprador, "   ")
        self.assertFalse(Mensaje.objects.exists())

    def test_enviar_mensaje_queda_sin_leer_para_el_destinatario(self):
        conversacion, _ = servicios.iniciar_conversacion(self.comprador, self.producto)
        mensaje = servicios.enviar_mensaje(conversacion, self.comprador, "¿Tienes arepas hoy?")
        self.assertEqual((mensaje.autor, mensaje.leido), (self.comprador, False))
        self.assertEqual(servicios.mensajes_sin_leer(self.emprendedor), 1)
        self.assertEqual(servicios.mensajes_sin_leer(self.comprador), 0)

    def test_obtener_mensajes_marca_como_leidos_solo_los_de_la_otra_persona(self):
        conversacion = crear_conversacion(
            self.comprador, self.producto, [(self.comprador, "Hola"), (self.emprendedor, "Hola, ¿qué deseas?")]
        )
        mensajes = servicios.obtener_mensajes(conversacion, self.emprendedor)
        self.assertEqual([m.contenido for m in mensajes], ["Hola", "Hola, ¿qué deseas?"])
        self.assertTrue(conversacion.mensajes.get(contenido="Hola").leido)
        self.assertFalse(conversacion.mensajes.get(contenido="Hola, ¿qué deseas?").leido)

    def test_rn17_las_conversaciones_se_ordenan_por_el_mensaje_mas_reciente(self):
        otro = crear_producto(crear_perfil(crear_emprendedor(CORREO_EMPRENDEDOR_B), nombre="Tejidos Juana"), "Pulsera")
        antigua = crear_conversacion(self.comprador, self.producto, [(self.comprador, "Primera")])
        reciente = crear_conversacion(self.comprador, otro, [(self.comprador, "Segunda")])
        Mensaje.objects.filter(conversacion=antigua).update(fecha_envio=timezone.now() - timedelta(days=1))
        self.assertEqual(list(servicios.conversaciones_de(self.comprador)), [reciente, antigua])
        servicios.enviar_mensaje(antigua, self.comprador, "Vuelvo a escribir")
        self.assertEqual(list(servicios.conversaciones_de(self.comprador)), [antigua, reciente])
