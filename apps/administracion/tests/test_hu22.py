"""
HU-22 · Desactivar contenido o cuentas inapropiadas (Could) · RF-24 · CU-22 · RN-19.
"""
from django.contrib.auth import get_user
from django.test import Client, TestCase
from django.urls import reverse

from apps.administracion.models import Desactivacion, MotivoDesactivacion
from apps.contacto import servicios as contacto
from apps.contacto.models import Mensaje
from apps.perfil_productos.models import EstadoProducto, Producto

from .utilidades import (
    CORREO_ADMIN,
    CORREO_COMPRADOR,
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    MOTIVO,
    URL_ADMIN,
    URL_ADMIN_CUENTAS,
    URL_ADMIN_PRODUCTOS,
    URL_AVISOS,
    crear_administrador,
    crear_usuario,
    emprendedor_con_producto,
    entrar,
    url_desactivar_cuenta,
    url_desactivar_producto,
    url_reactivar_cuenta,
)

URL_CATALOGO = reverse("catalogo:listado")
URL_MI_CUENTA = reverse("cuentas:mi_cuenta")
URL_INGRESAR = reverse("cuentas:ingresar")


class HU22ProductoTests(TestCase):
    def setUp(self):
        self.admin = crear_administrador()
        self.emprendedor, self.producto = emprendedor_con_producto()
        self.url = url_desactivar_producto(self.producto)

    def test_cp_22_1_producto_desactivado_deja_de_mostrarse_y_se_notifica_a_su_dueno(self):
        """CP-22.1 · Esc. 1: deja de mostrarse y se notifica a su dueño."""
        entrar(self.client, CORREO_ADMIN)
        lista = self.client.get(URL_ADMIN_PRODUCTOS, {"q": "arepa"})
        self.assertContains(lista, "Arepa de queso")
        self.assertContains(lista, f'href="{self.url}"')
        self.assertContains(self.client.get(self.url), "Motivo")
        respuesta = self.client.post(self.url, {"motivo": MOTIVO, "detalle": "No se permite su venta."}, follow=True)
        self.assertContains(respuesta, "«Arepa de queso» quedó desactivado")
        self.assertContains(respuesta, "se le notificó a su dueño")
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).estado, EstadoProducto.DESACTIVADO)

        # Deja de mostrarse en el catálogo y por enlace directo (RN-09)
        self.client.logout()
        self.assertNotContains(self.client.get(URL_CATALOGO), "Arepa de queso")
        detalle = self.client.get(reverse("catalogo:detalle", kwargs={"codigo": self.producto.codigo}))
        self.assertContains(detalle, "Este producto ya no está disponible", status_code=404)

        # Se notifica a su dueño: aviso en cualquier página hasta que lo lea
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        self.assertContains(self.client.get(URL_CATALOGO), f'href="{URL_AVISOS}"')
        avisos = self.client.get(URL_AVISOS)
        for texto in ["Arepa de queso", MotivoDesactivacion(MOTIVO).label, "No se permite su venta."]:
            with self.subTest(texto=texto):
                self.assertContains(avisos, texto)
        self.assertNotContains(self.client.get(URL_CATALOGO), "aviso-administracion")

    def test_el_motivo_es_obligatorio_y_el_detalle_tiene_limite(self):
        entrar(self.client, CORREO_ADMIN)
        sin_motivo = self.client.post(self.url, {"detalle": "x"})
        self.assertContains(sin_motivo, "Elige el motivo de la desactivación")
        largo = self.client.post(self.url, {"motivo": MOTIVO, "detalle": "x" * 301})
        self.assertContains(largo, "300 caracteres")
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).estado, EstadoProducto.DISPONIBLE)
        self.assertFalse(Desactivacion.objects.exists())

    def test_un_producto_ya_desactivado_muestra_un_aviso_y_no_se_registra_dos_veces(self):
        self.producto.estado = EstadoProducto.DESACTIVADO
        self.producto.save()
        entrar(self.client, CORREO_ADMIN)
        respuesta = self.client.post(self.url, {"motivo": MOTIVO}, follow=True)
        self.assertContains(respuesta, "ya está desactivado")
        self.assertFalse(Desactivacion.objects.exists())

    def test_el_administrador_puede_desactivar_desde_el_detalle_del_producto(self):
        detalle = reverse("catalogo:detalle", kwargs={"codigo": self.producto.codigo})
        entrar(self.client, CORREO_ADMIN)
        self.assertContains(self.client.get(detalle), f'href="{self.url}"')
        self.client.logout()
        crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_COMPRADOR)
        self.assertNotContains(self.client.get(detalle), self.url)

    def test_el_panel_del_emprendedor_enlaza_los_avisos(self):
        entrar(self.client, CORREO_ADMIN)
        self.client.post(self.url, {"motivo": MOTIVO})
        self.client.logout()
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        panel = self.client.get(reverse("emprendimiento:panel"))
        self.assertContains(panel, "Desactivado por la administración")
        self.assertContains(panel, f'href="{URL_AVISOS}"')


class HU22CuentaTests(TestCase):
    def setUp(self):
        self.admin = crear_administrador()
        self.comprador = crear_usuario(correo=CORREO_COMPRADOR)
        entrar(self.client, CORREO_ADMIN)

    def test_cp_22_2_una_cuenta_desactivada_pierde_el_acceso(self):
        """CP-22.2 · Esc. 2: el usuario pierde el acceso (también su sesión abierta)."""
        sesion_comprador = Client()
        entrar(sesion_comprador, CORREO_COMPRADOR)
        lista = self.client.get(URL_ADMIN_CUENTAS, {"q": "ana.perez"})
        self.assertContains(lista, CORREO_COMPRADOR)
        url = url_desactivar_cuenta(self.comprador)
        self.assertContains(lista, f'href="{url}"')
        respuesta = self.client.post(url, {"motivo": MotivoDesactivacion.SUPLANTACION}, follow=True)
        self.assertContains(respuesta, f"La cuenta {CORREO_COMPRADOR} quedó desactivada")
        self.comprador.refresh_from_db()
        self.assertFalse(self.comprador.activo)
        # La sesión abierta se pierde en la siguiente petición
        self.assertRedirects(sesion_comprador.get(URL_MI_CUENTA), f"{URL_INGRESAR}?next={URL_MI_CUENTA}")
        # Y no puede volver a iniciar sesión (mensaje de E1, sin revelar el estado de la cuenta)
        nuevo = Client()
        intento = nuevo.post(URL_INGRESAR, {"username": CORREO_COMPRADOR, "password": "Clave-Segura-2026"})
        self.assertContains(intento, "Correo o contraseña incorrectos")
        self.assertFalse(get_user(intento.wsgi_request).is_authenticated)

    def test_los_productos_de_una_cuenta_desactivada_salen_del_catalogo(self):
        emprendedor, producto = emprendedor_con_producto()
        self.client.post(url_desactivar_cuenta(emprendedor), {"motivo": MOTIVO})
        anonimo = Client()
        self.assertNotContains(anonimo.get(URL_CATALOGO), "Arepa de queso")
        detalle = anonimo.get(reverse("catalogo:detalle", kwargs={"codigo": producto.codigo}))
        self.assertEqual(detalle.status_code, 404)

    def test_no_se_puede_escribir_a_una_cuenta_desactivada(self):
        emprendedor, producto = emprendedor_con_producto()
        conversacion, _ = contacto.iniciar_conversacion(self.comprador, producto)
        contacto.enviar_mensaje(conversacion, self.comprador, "Hola, ¿tienes arepas?")
        self.client.post(url_desactivar_cuenta(emprendedor), {"motivo": MOTIVO})
        sesion_comprador = Client()
        entrar(sesion_comprador, CORREO_COMPRADOR)
        url = reverse("contacto:conversacion", kwargs={"codigo": conversacion.codigo})
        pagina = sesion_comprador.get(url)
        self.assertContains(pagina, "Esta cuenta fue desactivada")
        self.assertNotContains(pagina, 'name="contenido"')
        sesion_comprador.post(url, {"contenido": "¿Sigues ahí?"})
        self.assertEqual(Mensaje.objects.count(), 1)

    def test_reactivar_una_cuenta_le_devuelve_el_acceso(self):
        self.client.post(url_desactivar_cuenta(self.comprador), {"motivo": MOTIVO})
        respuesta = self.client.post(url_reactivar_cuenta(self.comprador), follow=True)
        self.assertContains(respuesta, f"La cuenta {CORREO_COMPRADOR} volvió a estar activa")
        self.assertTrue(Client().login(correo_institucional=CORREO_COMPRADOR, password="Clave-Segura-2026"))

    def test_no_se_desactiva_la_propia_cuenta_ni_la_de_otro_administrador(self):
        otro_admin = crear_administrador("otra.admin@amigo.edu.co")
        lista = self.client.get(URL_ADMIN_CUENTAS).content.decode()
        for cuenta in [self.admin, otro_admin]:
            with self.subTest(cuenta=cuenta.correo_institucional):
                self.assertNotIn(url_desactivar_cuenta(cuenta), lista)
                respuesta = self.client.post(url_desactivar_cuenta(cuenta), {"motivo": MOTIVO}, follow=True)
                self.assertContains(respuesta, "no se puede desactivar")
                cuenta.refresh_from_db()
                self.assertTrue(cuenta.activo)


class HU22SinPermisosTests(TestCase):
    def setUp(self):
        crear_administrador()
        self.emprendedor, self.producto = emprendedor_con_producto()
        self.comprador = crear_usuario(correo=CORREO_COMPRADOR)
        emprendedor_con_producto(CORREO_EMPRENDEDOR_B, "Pulsera")
        self.rutas = [
            URL_ADMIN,
            URL_ADMIN_PRODUCTOS,
            URL_ADMIN_CUENTAS,
            url_desactivar_producto(self.producto),
            url_desactivar_cuenta(self.comprador),
            url_reactivar_cuenta(self.comprador),
        ]

    def test_cp_22_3_sin_permisos_de_administrador_se_deniega_el_acceso(self):
        """CP-22.3 · Esc. 3: quien no es administrador recibe acceso denegado y nada cambia."""
        for correo in [CORREO_COMPRADOR, CORREO_EMPRENDEDOR_A, CORREO_EMPRENDEDOR_B]:
            self.client.logout()
            entrar(self.client, correo)
            for ruta in self.rutas:
                with self.subTest(correo=correo, ruta=ruta):
                    self.assertEqual(self.client.get(ruta).status_code, 403)
                    self.assertEqual(self.client.post(ruta, {"motivo": MOTIVO}).status_code, 403)
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).estado, EstadoProducto.DISPONIBLE)
        self.comprador.refresh_from_db()
        self.assertTrue(self.comprador.activo)
        self.assertFalse(Desactivacion.objects.exists())

    def test_sin_sesion_se_pide_iniciar_sesion(self):
        for ruta in self.rutas:
            with self.subTest(ruta=ruta):
                self.assertRedirects(self.client.get(ruta), f"{URL_INGRESAR}?next={ruta}")
