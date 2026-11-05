"""
HU-04 · Crear el perfil de mi emprendimiento (Must) · RF-05 · CU-04 · diagrama A2.
"""
from django.test import TestCase
from django.urls import reverse

from apps.perfil_productos.models import Categoria, Emprendimiento

from .utilidades import CORREO_COMPRADOR, CORREO_EMPRENDEDOR_A, crear_emprendedor, crear_perfil, entrar
from apps.cuentas.tests.utilidades import crear_usuario

URL_PERFIL = reverse("emprendimiento:perfil")
URL_PANEL = reverse("emprendimiento:panel")
URL_VISTA_PREVIA = reverse("emprendimiento:vista_previa")


def datos_perfil(**cambios):
    datos = {
        "descripcion": "Arepas rellenas hechas en casa con ingredientes frescos.",
        "categoria": str(Categoria.objects.get(nombre="Comida").pk),
        "horarios": "Lunes a viernes, 10:00 a 14:00",
        "zona_entrega": "Bloque 3, frente a la cafetería",
    }
    for campo, valor in cambios.items():
        if valor is None:
            datos.pop(campo, None)
        else:
            datos[campo] = valor
    return datos


class CategoriasTests(TestCase):
    def test_existen_las_categorias_del_entregable_1(self):
        """Comida, artesanías, videojuegos y ocio (Entregable 1, alcance), más «Otros» para el «etc.»."""
        nombres = set(Categoria.objects.values_list("nombre", flat=True))
        self.assertEqual(nombres, {"Comida", "Artesanías", "Videojuegos", "Ocio", "Otros"})


class HU04PerfilTests(TestCase):
    def setUp(self):
        self.emprendedor = crear_emprendedor()
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_04_1_perfil_valido_se_crea_y_queda_visible_en_el_catalogo(self):
        """CP-04.1 · Esc. 1: descripción, categoría, horarios y zona completos → perfil creado y visible."""
        respuesta = self.client.post(URL_PERFIL, datos_perfil(), follow=True)
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "El perfil de tu emprendimiento quedó publicado")
        perfil = Emprendimiento.objects.get(propietario=self.emprendedor)
        self.assertEqual(perfil.categoria.nombre, "Comida")
        # Fuente de datos del catálogo (E3) y vista previa de lo que ven los compradores.
        self.assertIn(perfil, Emprendimiento.objects.visibles_en_catalogo())
        vista = self.client.get(URL_VISTA_PREVIA)
        for texto in ["Arepas rellenas hechas en casa", "Comida", "Lunes a viernes, 10:00 a 14:00", "Bloque 3"]:
            self.assertContains(vista, texto)

    def test_cp_04_2_campo_obligatorio_vacio_rechaza_y_senala_el_campo(self):
        """CP-04.2 · Esc. 2: un campo obligatorio vacío → se rechaza el envío y se señala el campo."""
        mensajes = {
            "descripcion": "Escribe la descripción de tu emprendimiento.",
            "categoria": "Elige la categoría de tu emprendimiento.",
            "horarios": "Indica tus horarios de atención.",
            "zona_entrega": "Indica la zona de entrega.",
        }
        for campo, mensaje in mensajes.items():
            with self.subTest(campo=campo):
                respuesta = self.client.post(URL_PERFIL, datos_perfil(**{campo: ""}))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, mensaje)
                self.assertContains(respuesta, f'id="id_{campo}_error"')
                self.assertFalse(Emprendimiento.objects.exists())

    def test_cp_04_2_solo_espacios_cuenta_como_vacio(self):
        respuesta = self.client.post(URL_PERFIL, datos_perfil(horarios="    "))
        self.assertContains(respuesta, "Indica tus horarios de atención.")
        self.assertFalse(Emprendimiento.objects.exists())

    def test_cp_04_3_edicion_del_perfil_actualiza_lo_que_muestra_el_catalogo(self):
        """CP-04.3 · Esc. 3: con un perfil creado, al modificar y guardar se muestra lo actualizado."""
        crear_perfil(self.emprendedor)
        nuevos = datos_perfil(
            categoria=str(Categoria.objects.get(nombre="Artesanías").pk),
            descripcion="Pulseras tejidas a mano.",
            horarios="Martes y jueves, 8:00 a 12:00",
        )
        formulario = self.client.get(URL_PERFIL)
        self.assertContains(formulario, "Arepas rellenas hechas en casa.")  # carga los datos actuales
        respuesta = self.client.post(URL_PERFIL, nuevos, follow=True)
        self.assertContains(respuesta, "Guardamos los cambios de tu perfil")
        self.assertEqual(Emprendimiento.objects.count(), 1)
        perfil = Emprendimiento.objects.visibles_en_catalogo().get()
        self.assertEqual(perfil.categoria.nombre, "Artesanías")
        vista = self.client.get(URL_VISTA_PREVIA)
        self.assertContains(vista, "Pulseras tejidas a mano.")
        self.assertContains(vista, "Martes y jueves, 8:00 a 12:00")
        self.assertNotContains(vista, "Arepas rellenas")

    def test_un_emprendedor_tiene_como_maximo_un_perfil(self):
        """Supuesto S-2 del Entregable 2 (multiplicidad 0..1)."""
        self.client.post(URL_PERFIL, datos_perfil())
        self.client.post(URL_PERFIL, datos_perfil(descripcion="Otra descripción."))
        self.assertEqual(Emprendimiento.objects.filter(propietario=self.emprendedor).count(), 1)

    def test_el_formulario_avisa_que_el_perfil_sera_publico(self):
        self.assertContains(self.client.get(URL_PERFIL), "se mostrará públicamente en el catálogo")

    def test_la_descripcion_tiene_un_limite_de_500_caracteres(self):
        respuesta = self.client.post(URL_PERFIL, datos_perfil(descripcion="a" * 501))
        self.assertContains(respuesta, "La descripción puede tener hasta 500 caracteres (tiene 501)")
        self.assertFalse(Emprendimiento.objects.exists())

    def test_el_panel_sin_perfil_invita_a_crearlo(self):
        respuesta = self.client.get(URL_PANEL)
        self.assertContains(respuesta, "Crea el perfil de tu emprendimiento")
        self.assertContains(respuesta, f'href="{URL_PERFIL}"')


class HU04AccesoTests(TestCase):
    """Precondición de CU-04: sesión iniciada como emprendedor."""

    def test_un_comprador_no_puede_crear_perfil(self):
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        self.assertEqual(self.client.post(URL_PERFIL, datos_perfil()).status_code, 403)
        self.assertFalse(Emprendimiento.objects.exists())

    def test_sin_sesion_se_pide_iniciar_sesion(self):
        for url in [URL_PANEL, URL_PERFIL, URL_VISTA_PREVIA]:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertRedirects(respuesta, f"{reverse('cuentas:ingresar')}?next={url}")
