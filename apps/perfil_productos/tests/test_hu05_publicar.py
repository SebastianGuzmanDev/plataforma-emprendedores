"""
HU-05 · Publicar un producto (Must) · RF-06 · CU-05 · diagramas A2 y S3.
"""
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.perfil_productos.models import EstadoProducto, Producto

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    MB,
    MediaTemporalMixin,
    archivo_no_imagen,
    crear_emprendedor,
    crear_perfil,
    entrar,
    imagen,
)

URL_PUBLICAR = reverse("emprendimiento:publicar")
URL_PANEL = reverse("emprendimiento:panel")
URL_VISTA_PREVIA = reverse("emprendimiento:vista_previa")


def datos_producto(**cambios):
    datos = {"nombre": "Arepa de queso", "precio_referencia": "5000", "foto": imagen()}
    for campo, valor in cambios.items():
        if valor is None:
            datos.pop(campo, None)
        else:
            datos[campo] = valor
    return datos


class HU05PublicarTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.emprendimiento = crear_perfil(crear_emprendedor())
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def test_cp_05_1_publicacion_exitosa_aparece_en_el_catalogo_como_disponible(self):
        """CP-05.1 · Esc. 1: nombre, foto y precio válidos → aparece en el catálogo con estado Disponible."""
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(precio_referencia="5.000"), follow=True)
        self.assertRedirects(respuesta, URL_PANEL)
        self.assertContains(respuesta, "Publicaste «Arepa de queso»")
        producto = Producto.objects.get()
        self.assertEqual(producto.emprendimiento, self.emprendimiento)
        self.assertEqual(producto.estado, EstadoProducto.DISPONIBLE)
        self.assertEqual(producto.precio_referencia, 5000)
        self.assertIn(producto, Producto.objects.visibles_en_catalogo())
        self.assertTrue((Path(settings.MEDIA_ROOT) / producto.foto.name).is_file())
        vista = self.client.get(URL_VISTA_PREVIA)
        self.assertContains(vista, "Arepa de queso")
        self.assertContains(vista, "$ 5.000")
        self.assertContains(vista, "Disponible")
        self.assertContains(vista, f'src="{producto.foto.url}"')

    def test_cp_05_2_foto_mayor_a_5_mb_se_rechaza_e_indica_el_limite(self):
        """CP-05.2 · Esc. 2: una foto de más de 5 MB se rechaza indicando el límite."""
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(foto=imagen(tamano_total=6 * MB)))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "el límite es 5 MB")
        self.assertFalse(Producto.objects.exists())

    def test_cp_05_2_foto_de_exactamente_5_mb_se_acepta(self):
        self.client.post(URL_PUBLICAR, datos_producto(foto=imagen(tamano_total=5 * MB)))
        self.assertEqual(Producto.objects.count(), 1)

    def test_cp_05_3_precio_negativo_o_con_letras_se_rechaza(self):
        """CP-05.3 · Esc. 3: un precio negativo o con letras se rechaza."""
        for precio in ["-1000", "abc", "12a"]:
            with self.subTest(precio=precio):
                respuesta = self.client.post(URL_PUBLICAR, datos_producto(precio_referencia=precio))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "Escribe el precio solo con números")
                self.assertFalse(Producto.objects.exists())

    def test_la_foto_es_obligatoria(self):
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(foto=None))
        self.assertContains(respuesta, "Agrega una foto del producto.")
        self.assertFalse(Producto.objects.exists())

    def test_el_nombre_es_obligatorio(self):
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(nombre="  "))
        self.assertContains(respuesta, "Escribe el nombre del producto.")
        self.assertFalse(Producto.objects.exists())

    def test_un_archivo_que_no_es_imagen_se_rechaza(self):
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(foto=archivo_no_imagen()))
        self.assertContains(respuesta, "no es una imagen JPG, PNG o WebP")
        self.assertFalse(Producto.objects.exists())

    def test_los_datos_validos_se_conservan_al_mostrar_un_error(self):
        respuesta = self.client.post(URL_PUBLICAR, datos_producto(precio_referencia="abc"))
        self.assertContains(respuesta, 'value="Arepa de queso"')

    def test_el_formulario_indica_los_formatos_y_el_limite(self):
        respuesta = self.client.get(URL_PUBLICAR)
        self.assertContains(respuesta, "JPG, PNG o WebP de hasta 5 MB")
        self.assertContains(respuesta, 'enctype="multipart/form-data"')
        self.assertContains(respuesta, 'accept="image/jpeg,image/png,image/webp"')


class HU05SinPerfilTests(MediaTemporalMixin, TestCase):
    """RN-05: el emprendedor necesita su perfil para publicar productos (precondición de CU-05)."""

    def test_sin_perfil_se_envia_a_crear_el_perfil(self):
        crear_emprendedor()
        entrar(self.client, CORREO_EMPRENDEDOR_A)
        mensaje = "Antes de publicar productos, crea el perfil de tu emprendimiento"
        formulario = self.client.get(URL_PUBLICAR, follow=True)
        self.assertRedirects(formulario, reverse("emprendimiento:perfil"))
        self.assertContains(formulario, mensaje)
        envio = self.client.post(URL_PUBLICAR, datos_producto(), follow=True)
        self.assertRedirects(envio, reverse("emprendimiento:perfil"))
        self.assertFalse(Producto.objects.exists())
