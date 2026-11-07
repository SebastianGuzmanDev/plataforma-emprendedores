"""
CC-06 · Miniaturas para el catálogo (cambio de diseño para cumplir RNF-01).

El catálogo muestra muchas tarjetas a la vez: cada una usa una miniatura de hasta
600 px en lugar de la foto de 1600 px. El detalle sigue usando la foto completa.
"""
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from apps.perfil_productos.models import Producto

from .utilidades import CORREO_EMPRENDEDOR_A, MediaTemporalMixin, crear_emprendedor, crear_perfil, crear_producto, entrar, imagen


class MiniaturasTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.emprendimiento = crear_perfil(crear_emprendedor())
        entrar(self.client, CORREO_EMPRENDEDOR_A)

    def publicar(self, **cambios):
        datos = {"nombre": "Arepa de queso", "precio_referencia": "5000", "foto": imagen(ancho=3000, alto=2000)}
        datos.update(cambios)
        self.client.post(reverse("emprendimiento:publicar"), datos)
        return Producto.objects.latest("id")

    def ruta(self, archivo):
        return Path(settings.MEDIA_ROOT) / archivo.name

    def test_al_publicar_se_genera_una_miniatura_jpeg_de_hasta_600_px(self):
        producto = self.publicar()
        self.assertTrue(producto.miniatura)
        with Image.open(self.ruta(producto.miniatura)) as miniatura:
            self.assertEqual(miniatura.format, "JPEG")
            self.assertEqual(max(miniatura.size), 600)
            self.assertEqual(dict(miniatura.getexif()), {})
        with Image.open(self.ruta(producto.foto)) as foto:
            self.assertEqual(max(foto.size), 1600)
        self.assertLess(self.ruta(producto.miniatura).stat().st_size, self.ruta(producto.foto).stat().st_size)
        self.assertEqual(producto.url_miniatura, producto.miniatura.url)

    def test_al_cambiar_la_foto_se_reemplaza_tambien_la_miniatura(self):
        producto = self.publicar()
        miniatura_anterior = self.ruta(producto.miniatura)
        self.client.post(
            reverse("emprendimiento:editar", kwargs={"codigo": producto.codigo}),
            {"nombre": "Arepa de queso", "precio_referencia": "5000", "foto": imagen()},
        )
        producto.refresh_from_db()
        self.assertFalse(miniatura_anterior.exists())
        self.assertTrue(self.ruta(producto.miniatura).is_file())

    def test_sin_miniatura_se_usa_la_foto_completa(self):
        producto = crear_producto(self.emprendimiento)
        self.assertFalse(producto.miniatura)
        self.assertEqual(producto.url_miniatura, producto.foto.url)

    def test_la_vista_previa_usa_la_miniatura(self):
        producto = self.publicar()
        self.assertContains(self.client.get(reverse("emprendimiento:vista_previa")), f'src="{producto.miniatura.url}"')
