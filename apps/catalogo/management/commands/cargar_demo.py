"""
Datos de demostración para el catálogo (mitiga el riesgo R4: demo sin contenido) y para
medir RNF-01 con 100 productos.

    python manage.py cargar_demo                         # 10 emprendimientos, 100 productos
    python manage.py cargar_demo --limpiar --productos 300
    python manage.py cargar_demo --limpiar --productos 100 --solo-disponibles   # medición de RNF-01

Todas las cuentas usan correos «demo.…@amigo.edu.co» y la contraseña indicada. Solo
funciona con DEBUG activo, salvo que se use --forzar (nunca con datos reales).
"""
import io
import random
from decimal import Decimal
import unicodedata

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.administracion import servicios as administracion
from apps.administracion.models import Desactivacion, MotivoDesactivacion
from apps.contacto import servicios as contacto
from apps.finanzas import servicios as finanzas
from apps.finanzas.models import CategoriaGasto
from apps.finanzas.reglas import mes_anterior
from apps.cuentas.models import Rol, Usuario
from apps.inventario import servicios as inventario
from apps.cuentas.servicios import registrar_usuario
from apps.perfil_productos import servicios
from apps.perfil_productos.models import ESTADOS_VISIBLES_EN_CATALOGO, Categoria, Emprendimiento

PREFIJO = "demo."
DOMINIO = "amigo.edu.co"

EMPRENDIMIENTOS = [
    ("Arepas Doña Rosa", "Comida", "Arepas rellenas hechas en casa con queso campesino."),
    ("Tejidos Juana", "Artesanías", "Pulseras, mochilas y llaveros tejidos a mano."),
    ("Dulce Campus", "Comida", "Postres caseros: brownies, galletas y tortas por porción."),
    ("Pixel Arcade", "Videojuegos", "Juegos indie hechos por estudiantes y accesorios gamer."),
    ("Juegos de Mesa Amigó", "Ocio", "Alquiler y venta de juegos de mesa y cartas."),
    ("Café del Bloque", "Comida", "Café de origen colombiano y bebidas frías."),
    ("Barro y Color", "Artesanías", "Cerámica pintada a mano: tazas, materas y aretes."),
    ("Stickers U", "Otros", "Stickers, separadores y agendas con diseños propios."),
    ("Snacks Saludables", "Comida", "Frutas picadas, granola y wraps."),
    ("Retro Cartuchos", "Videojuegos", "Reparación de controles y juegos retro."),
]
PRODUCTOS = {
    "Comida": ["Arepa de queso", "Arepa mixta", "Empanada", "Brownie", "Galletas de avena", "Café tinto",
               "Capuchino", "Jugo de mango", "Wrap de pollo", "Pandebono", "Buñuelo", "Torta de chocolate"],
    "Artesanías": ["Pulsera tejida", "Mochila wayuu", "Llavero tejido", "Taza pintada", "Aretes de barro", "Matera"],
    "Videojuegos": ["Juego indie digital", "Control reparado", "Cartucho retro", "Soporte para control"],
    "Ocio": ["Alquiler de Catan", "Juego de cartas UNO", "Rompecabezas 1000 piezas", "Dominó"],
    "Otros": ["Paquete de stickers", "Agenda 2027", "Separadores de libro", "Camiseta estampada"],
}
INSUMOS = {
    "Comida": [("Harina de maíz (kg)", "5", 18000), ("Queso campesino (lb)", "3", 21000), ("Azúcar (kg)", "2", 7000)],
    "Artesanías": [("Hilo encerado (rollos)", "4", 16000), ("Arcilla (kg)", "2,5", 12500)],
    "Videojuegos": [("Repuestos de joystick", "6", 30000)],
    "Ocio": [("Fundas para cartas", "10", 15000)],
    "Otros": [("Papel adhesivo (pliegos)", "20", 24000), ("Tinta (cartuchos)", "2", 60000)],
}
COLORES = [(232, 200, 150), (210, 180, 140), (190, 220, 210), (240, 210, 160), (200, 210, 235), (235, 200, 210)]


FUENTES_CON_TILDES = [
    "DejaVuSans.ttf",  # Linux
    "arial.ttf",  # Windows
    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
    "/Library/Fonts/Arial.ttf",
]


def fuente_y_texto(texto, tamano=72):
    """Usa una fuente del sistema con tildes; si no hay, la de Pillow con el texto sin tildes."""
    for ruta in FUENTES_CON_TILDES:
        try:
            return ImageFont.truetype(ruta, tamano), texto
        except OSError:
            continue
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    try:
        return ImageFont.load_default(size=tamano), sin_tildes
    except TypeError:  # Pillow sin FreeType
        return ImageFont.load_default(), sin_tildes


def foto_demo(nombre, indice):
    """Imagen de 1200 × 900 con el nombre del producto (no es una foto real)."""
    fondo = COLORES[indice % len(COLORES)]
    trazo = tuple(max(0, canal - 90) for canal in fondo)
    imagen = Image.new("RGB", (1200, 900), fondo)
    dibujo = ImageDraw.Draw(imagen)
    dibujo.ellipse((390, 140, 810, 560), outline=trazo, width=60)
    fuente, texto = fuente_y_texto(nombre)
    dibujo.text((600, 700), texto, fill=trazo, font=fuente, anchor="mm")
    salida = io.BytesIO()
    imagen.save(salida, "JPEG", quality=85)
    return SimpleUploadedFile("demo.jpg", salida.getvalue(), content_type="image/jpeg")


class Command(BaseCommand):
    help = "Carga emprendimientos y productos de demostración (correos demo.…@amigo.edu.co)."

    def add_arguments(self, parser):
        parser.add_argument("--emprendimientos", type=int, default=10)
        parser.add_argument("--productos", type=int, default=100, help="Total de productos a crear")
        parser.add_argument("--conversaciones", type=int, default=3,
                            help="Conversaciones del comprador de demostración con mensajes sin leer (E4)")
        parser.add_argument("--contrasena", default="Clave-Segura-2026")
        parser.add_argument("--limpiar", action="store_true", help="Borra antes los datos de demostración")
        parser.add_argument("--solo-disponibles", action="store_true",
                            help="Todos los productos quedan Disponibles (para medir RNF-01 con 100 visibles)")
        parser.add_argument("--forzar", action="store_true", help="Permite ejecutarlo con DEBUG desactivado")

    def handle(self, *args, emprendimientos, productos, contrasena, limpiar, forzar, solo_disponibles,
               conversaciones, **opciones):
        if not settings.DEBUG and not forzar:
            raise CommandError("DEBUG está desactivado. Usa --forzar solo en un entorno de pruebas sin datos reales.")
        if emprendimientos < 1 or productos < 0:
            raise CommandError("Indica al menos 1 emprendimiento y 0 o más productos.")
        aleatorio = random.Random(2026)  # mismos datos en cada carga
        with transaction.atomic():
            if limpiar:
                borrados, _ = Usuario.objects.filter(correo_institucional__startswith=PREFIJO).delete()
                self.stdout.write(f"Datos de demostración anteriores borrados ({borrados} registros).")
            comprador = f"{PREFIJO}comprador@{DOMINIO}"
            cuenta_comprador = Usuario.objects.filter(correo_institucional=comprador).first() or registrar_usuario(
                correo=comprador, contrasena=contrasena, rol=Rol.COMPRADOR, acepta_aviso=True
            )

            creados = []
            for i in range(emprendimientos):
                nombre, categoria, descripcion = EMPRENDIMIENTOS[i % len(EMPRENDIMIENTOS)]
                correo = f"{PREFIJO}emprendedor{i + 1:02d}@{DOMINIO}"
                usuario = Usuario.objects.filter(correo_institucional=correo).first() or registrar_usuario(
                    correo=correo, contrasena=contrasena, rol=Rol.EMPRENDEDOR, acepta_aviso=True
                )
                perfil, _ = Emprendimiento.objects.get_or_create(
                    propietario=usuario,
                    defaults={
                        "nombre": nombre if i < len(EMPRENDIMIENTOS) else f"{nombre} {i + 1}",
                        "categoria": Categoria.objects.get(nombre=categoria),
                        "descripcion": descripcion,
                        "horarios": aleatorio.choice(["Lunes a viernes, 10:00 a 14:00", "Martes y jueves, 8:00 a 12:00",
                                                      "Lunes a sábado, 7:00 a 11:00"]),
                        "zona_entrega": aleatorio.choice(["Bloque 3, frente a la cafetería", "Biblioteca, primer piso",
                                                          "Portería principal", "Plazoleta central"]),
                    },
                )
                creados.append((usuario, perfil))

            for i in range(productos):
                usuario, perfil = creados[i % len(creados)]
                nombre = aleatorio.choice(PRODUCTOS[perfil.categoria.nombre])
                producto = servicios.publicar_producto(
                    usuario, nombre=nombre, foto=foto_demo(nombre, i), precio=aleatorio.randrange(10, 400) * 100
                )
                suerte = 1 if solo_disponibles else aleatorio.random()
                if suerte < 0.10:
                    servicios.marcar_agotado(producto)
                    inventario.registrar_existencias(producto, 0)
                elif suerte < 0.15:
                    servicios.desactivar_producto(producto)
                elif suerte < 0.80:  # E5: la mayoría lleva inventario; algunos con stock bajo
                    inventario.registrar_existencias(producto, aleatorio.randrange(1, 31))
                    if aleatorio.random() < 0.4:
                        inventario.definir_umbral(producto, 5)

            for usuario, perfil in creados:
                if not usuario.insumos.exists():
                    for nombre, cantidad, costo in INSUMOS[perfil.categoria.nombre]:
                        inventario.registrar_insumo(
                            usuario, nombre=nombre, cantidad=Decimal(cantidad.replace(",", ".")), costo=costo,
                            registrar_como_gasto=True,  # CC-10
                        )

            # E6: ingresos y gastos del mes actual y de los dos anteriores (nunca con fecha futura).
            hoy = timezone.localdate()
            meses = [hoy.replace(day=1)]
            for _ in range(2):
                meses.append(mes_anterior(meses[-1]))
            otras_categorias = [c for c in CategoriaGasto.values if c != CategoriaGasto.MATERIA_PRIMA]
            for usuario, _perfil in creados:
                if usuario.ingresos.exists():
                    continue
                for inicio in meses:
                    ultimo_dia = hoy.day if inicio.month == hoy.month and inicio.year == hoy.year else 28
                    for _ in range(aleatorio.randrange(4, 9)):
                        finanzas.registrar_ingreso(
                            usuario, monto=aleatorio.randrange(8, 61) * 1000,
                            fecha=inicio.replace(day=aleatorio.randrange(1, ultimo_dia + 1)),
                        )
                    for _ in range(aleatorio.randrange(2, 5)):
                        finanzas.registrar_gasto(
                            usuario, monto=aleatorio.randrange(3, 41) * 1000,
                            # en el mes actual la materia prima sale de los insumos (CC-10)
                            categoria=aleatorio.choice(
                                otras_categorias if inicio == meses[0] else CategoriaGasto.values
                            ),
                            fecha=inicio.replace(day=aleatorio.randrange(1, ultimo_dia + 1)),
                        )

            # E4: el comprador escribe a varios emprendimientos; los emprendedores tienen mensajes sin leer.
            charlas = 0
            for usuario, perfil in creados[1:] + creados[:1]:
                if charlas >= conversaciones:
                    break
                producto = perfil.productos.filter(estado="DISPONIBLE").first()
                if producto is None:
                    continue
                conversacion, nueva = contacto.iniciar_conversacion(cuenta_comprador, producto)
                if not nueva:
                    continue
                contacto.enviar_mensaje(conversacion, cuenta_comprador, f"Hola, ¿tienes «{producto.nombre}» disponible hoy?")
                if charlas == 0:
                    contacto.enviar_mensaje(conversacion, usuario, f"¡Hola! Sí, hasta las 2 p. m. Te lo entrego en {perfil.zona_entrega.lower()}.")
                    contacto.enviar_mensaje(conversacion, cuenta_comprador, "Perfecto, paso a las 12. ¡Gracias!")
                charlas += 1

            # E7: cuenta de administración (RF-03: el rol se asigna internamente) y una desactivación
            # de ejemplo con su aviso pendiente para demo.emprendedor02. No se hace con --solo-disponibles.
            correo_admin = f"{PREFIJO}administrador@{DOMINIO}"
            administrador = Usuario.objects.filter(correo_institucional=correo_admin).first()
            if administrador is None:
                administrador = registrar_usuario(
                    correo=correo_admin, contrasena=contrasena, rol=Rol.COMPRADOR, acepta_aviso=True
                )
                administrador.rol = Rol.ADMINISTRADOR
                administrador.save(update_fields=["rol"])
            if not solo_disponibles and len(creados) > 1:
                _, perfil = creados[1]
                if not Desactivacion.objects.filter(producto__emprendimiento=perfil).exists():
                    producto = perfil.productos.filter(estado__in=ESTADOS_VISIBLES_EN_CATALOGO).order_by("-id").first()
                    if producto is not None:
                        administracion.desactivar_producto(
                            administrador, producto, motivo=MotivoDesactivacion.ENGANOSO,
                            detalle="La foto no corresponde al producto que se ofrece.",
                        )

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {len(creados)} emprendimientos, {productos} productos y {charlas} conversaciones de demostración."
        ))
        self.stdout.write(f"Comprador: {comprador} · Administrador: {PREFIJO}administrador@{DOMINIO} · "
                          f"Emprendedores: {PREFIJO}emprendedor01@{DOMINIO} … "
                          f"· Contraseña: {contrasena}")
