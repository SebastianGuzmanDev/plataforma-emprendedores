"""
Pruebas UNITARIAS de las reglas de la Épica 2 (RN-05 a RN-09) y del diagrama de
estados ES1 de la entidad Producto (Entregable 2, sección 1.3).
"""
import io

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from PIL import Image

from apps.perfil_productos.models import EstadoProducto, Producto, TransicionNoPermitida
from apps.perfil_productos.reglas import LIMITE_FOTO_BYTES, interpretar_precio, procesar_foto, validar_foto

from .utilidades import MB, archivo_no_imagen, crear_emprendedor, crear_perfil, crear_producto, imagen


class ReglaPrecioTests(SimpleTestCase):
    """RN-07: el precio de referencia no es negativo ni contiene letras (valores límite del plan, 4.1.4)."""

    def test_rn07_acepta_numeros_no_negativos(self):
        for texto, esperado in [
            ("5000", 5000),
            ("5.000", 5000),
            ("$ 5.000", 5000),
            ("$5000", 5000),
            (" 12500 ", 12500),
            ("1.250.000", 1250000),
            ("0", 0),
        ]:
            with self.subTest(texto=texto):
                self.assertEqual(interpretar_precio(texto), esperado)

    def test_rn07_rechaza_negativos_letras_y_formatos_ambiguos(self):
        for texto in ["-1000", "abc", "12a", "12,5", "5.00", "1.2345", "", "   ", "5 000", "$", None, "99999999999"]:
            with self.subTest(texto=texto):
                self.assertIsNone(interpretar_precio(texto))


class ReglaFotoTests(SimpleTestCase):
    """RN-07: la foto del producto pesa hasta 5 MB."""

    def test_el_limite_es_de_5_megabytes(self):
        self.assertEqual(LIMITE_FOTO_BYTES, 5 * MB)

    def test_rn07_foto_de_exactamente_5_mb_es_valida(self):
        validar_foto(imagen(tamano_total=5 * MB))

    def test_rn07_foto_de_un_byte_mas_de_5_mb_se_rechaza(self):
        with self.assertRaisesMessage(ValidationError, "el límite es 5 MB"):
            validar_foto(imagen(tamano_total=5 * MB + 1))

    def test_rn07_foto_de_6_mb_se_rechaza_indicando_el_limite(self):
        with self.assertRaisesMessage(ValidationError, "La foto pesa 6,0 MB y el límite es 5 MB"):
            validar_foto(imagen(tamano_total=6 * MB))

    def test_acepta_jpg_png_y_webp(self):
        for formato, nombre in [("JPEG", "a.jpg"), ("PNG", "a.png"), ("WEBP", "a.webp")]:
            with self.subTest(formato=formato):
                validar_foto(imagen(nombre=nombre, formato=formato))

    def test_rechaza_archivos_que_no_son_imagenes_aunque_digan_jpg(self):
        for archivo in [archivo_no_imagen(), archivo_no_imagen("x.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>")]:
            with self.subTest(archivo=archivo.name):
                with self.assertRaisesMessage(ValidationError, "no es una imagen JPG, PNG o WebP"):
                    validar_foto(archivo)

    def test_rechaza_formatos_no_admitidos(self):
        with self.assertRaisesMessage(ValidationError, "no es una imagen JPG, PNG o WebP"):
            validar_foto(imagen(nombre="a.gif", formato="GIF"))


class ProcesamientoFotoTests(SimpleTestCase):
    """RNF-06 (datos mínimos) y RNF-01 (carga del catálogo): la foto publicada se normaliza."""

    def abrir(self, contenido):
        return Image.open(io.BytesIO(contenido.read()))

    def test_elimina_los_metadatos_exif_incluida_la_ubicacion_gps(self):
        resultado = self.abrir(procesar_foto(imagen(exif_gps=True)))
        self.assertEqual(dict(resultado.getexif()), {})

    def test_limita_el_lado_mayor_a_1600_px_sin_deformar(self):
        resultado = self.abrir(procesar_foto(imagen(ancho=4000, alto=3000)))
        self.assertEqual(resultado.size, (1600, 1200))

    def test_guarda_siempre_jpeg_con_nombre_aleatorio(self):
        primera = procesar_foto(imagen(nombre="Foto de Rosa Pérez.png", formato="PNG"))
        segunda = procesar_foto(imagen(nombre="Foto de Rosa Pérez.png", formato="PNG"))
        self.assertRegex(primera.name, r"^[0-9a-f]{32}\.jpg$")
        self.assertNotEqual(primera.name, segunda.name)
        self.assertEqual(self.abrir(primera).format, "JPEG")


class DiagramaEstadosProductoTests(TestCase):
    """ES1 con CC-02: Disponible ⇄ Agotado; ambos → Desactivado, que es definitivo."""

    def setUp(self):
        self.producto = crear_producto(crear_perfil(crear_emprendedor()))

    def test_es1_al_publicar_el_estado_inicial_es_disponible(self):
        self.assertEqual(Producto._meta.get_field("estado").default, EstadoProducto.DISPONIBLE)
        self.assertEqual(self.producto.estado, EstadoProducto.DISPONIBLE)

    def test_es1_disponible_pasa_a_agotado(self):
        self.producto.marcar_agotado()
        self.assertEqual(self.producto.estado, EstadoProducto.AGOTADO)

    def test_es1_disponible_y_agotado_pasan_a_desactivado(self):
        self.producto.desactivar()
        self.assertEqual(self.producto.estado, EstadoProducto.DESACTIVADO)
        otro = crear_producto(self.producto.emprendimiento, estado=EstadoProducto.AGOTADO)
        otro.desactivar()
        self.assertEqual(otro.estado, EstadoProducto.DESACTIVADO)

    def test_es1_desactivado_no_tiene_transiciones_de_salida(self):
        self.producto.desactivar()
        for accion in (
            self.producto.marcar_agotado,
            self.producto.marcar_disponible,
            self.producto.desactivar,
            self.producto.validar_edicion,
        ):
            with self.subTest(accion=accion.__name__):
                with self.assertRaises(TransicionNoPermitida):
                    accion()

    def test_cc02_agotado_vuelve_a_disponible(self):
        self.producto.marcar_agotado()
        self.producto.marcar_disponible()
        self.assertEqual(self.producto.estado, EstadoProducto.DISPONIBLE)

    def test_cc02_un_producto_disponible_no_se_marca_disponible_otra_vez(self):
        with self.assertRaisesMessage(TransicionNoPermitida, "ya está disponible"):
            self.producto.marcar_disponible()

    def test_cc02_un_producto_agotado_no_se_vuelve_a_agotar(self):
        self.producto.marcar_agotado()
        with self.assertRaises(TransicionNoPermitida):
            self.producto.marcar_agotado()

    def test_cc02_disponibles_y_agotados_se_pueden_editar(self):
        self.producto.validar_edicion()  # Disponible: no lanza
        self.producto.marcar_agotado()
        self.producto.validar_edicion()  # Agotado: no lanza

    def test_cc02_un_desactivado_no_se_reactiva(self):
        self.producto.desactivar()
        with self.assertRaisesMessage(TransicionNoPermitida, "no se puede reactivar"):
            self.producto.marcar_disponible()
