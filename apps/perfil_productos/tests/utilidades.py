"""Datos y ayudas compartidas por las pruebas de la Épica 2."""
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.cuentas.models import Rol
from apps.cuentas.tests.utilidades import CONTRASENA_VALIDA, crear_usuario
from apps.perfil_productos.models import Categoria, Emprendimiento, EstadoProducto, Producto

CORREO_EMPRENDEDOR_A = "rosa.arepas@amigo.edu.co"
CORREO_EMPRENDEDOR_B = "juan.artesanias@amigo.edu.co"
CORREO_COMPRADOR = "ana.perez@amigo.edu.co"
MB = 1024 * 1024


class MediaTemporalMixin:
    """Guarda las fotos de cada clase de prueba en una carpeta temporal que luego se borra."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="media-pruebas-")
        cls._ajuste_media = override_settings(MEDIA_ROOT=cls._media)
        cls._ajuste_media.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._ajuste_media.disable()
        shutil.rmtree(cls._media, ignore_errors=True)


def imagen(nombre="foto.jpg", formato="JPEG", ancho=800, alto=600, tamano_total=None, exif_gps=False):
    """Imagen válida en memoria. `tamano_total` rellena el archivo hasta ese número de bytes."""
    lienzo = Image.new("RGBA" if formato == "PNG" else "RGB", (ancho, alto), (0, 123, 153))
    extra = {}
    if exif_gps:
        exif = Image.Exif()
        exif[0x010F] = "CamaraPrueba"
        exif[0x8825] = {1: "N", 2: (6.0, 15.0, 0.0), 3: "W", 4: (75.0, 34.0, 0.0)}
        extra["exif"] = exif
    salida = io.BytesIO()
    lienzo.save(salida, formato, **extra)
    datos = salida.getvalue()
    if tamano_total is not None:
        datos += b"\0" * (tamano_total - len(datos))
    tipo = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "GIF": "image/gif"}[formato]
    return SimpleUploadedFile(nombre, datos, content_type=tipo)


def archivo_no_imagen(nombre="documento.jpg", contenido=b"esto no es una imagen"):
    return SimpleUploadedFile(nombre, contenido, content_type="image/jpeg")


def crear_emprendedor(correo=CORREO_EMPRENDEDOR_A):
    return crear_usuario(correo=correo, rol=Rol.EMPRENDEDOR)


def crear_perfil(usuario, categoria="Comida", **cambios):
    datos = {
        "descripcion": "Arepas rellenas hechas en casa.",
        "horarios": "Lunes a viernes, 10:00 a 14:00",
        "zona_entrega": "Bloque 3, frente a la cafetería",
    }
    datos.update(cambios)
    return Emprendimiento.objects.create(
        propietario=usuario, categoria=Categoria.objects.get(nombre=categoria), **datos
    )


def crear_producto(emprendimiento, nombre="Arepa de queso", precio=5000, estado=EstadoProducto.DISPONIBLE):
    return Producto.objects.create(
        emprendimiento=emprendimiento,
        nombre=nombre,
        precio_referencia=precio,
        estado=estado,
        foto="productos/prueba.jpg",
    )


def entrar(cliente, correo):
    assert cliente.login(correo_institucional=correo, password=CONTRASENA_VALIDA)
