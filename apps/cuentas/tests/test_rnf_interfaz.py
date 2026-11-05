"""
Interfaz de la Épica 1:
- RNF-03 · Compatibilidad (Must): interfaz responsive desde 360 px.
- RNF-11 · Accesibilidad (Could): WCAG 2.1 AA, contraste 4.5:1 y texto alternativo.
- Manual de Identidad Visual: solo se usan los colores institucionales.

La verificación visual a 360 px en los cuatro navegadores se completa con
`scripts/verificar_interfaz.mjs` y con la prueba manual CP-RNF03.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .utilidades import CONTRASENA_VALIDA, CORREO_COMPRADOR, crear_usuario

CSS_DIR = Path(settings.BASE_DIR) / "static" / "css"
PLANTILLAS = [Path(settings.BASE_DIR) / "templates", Path(settings.BASE_DIR) / "apps"]

# Manual de Identidad Visual, pág. 07 (Composición del color) y pág. 06 (blanco como
# fondo principal). El negro aparece en las aplicaciones sobre fondo negro (pág. 13).
PALETA_INSTITUCIONAL = {"#007b99", "#f39200", "#848585", "#ffffff", "#000000"}

PAGINAS_PUBLICAS = [
    "inicio",
    "aviso_privacidad",
    "cuentas:registro",
    "cuentas:ingresar",
    "cuentas:recuperar",
    "cuentas:recuperar_enviado",
]


class _AnalizadorHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imagenes, self.campos, self.etiquetas, self.metas = [], [], set(), []

    def handle_starttag(self, etiqueta, atributos):
        attrs = dict(atributos)
        if etiqueta == "img":
            self.imagenes.append(attrs)
        elif etiqueta in ("input", "select", "textarea") and attrs.get("type") not in ("hidden", "submit"):
            self.campos.append(attrs)
        elif etiqueta == "label" and attrs.get("for"):
            self.etiquetas.add(attrs["for"])
        elif etiqueta == "meta":
            self.metas.append(attrs)


def analizar(html):
    analizador = _AnalizadorHTML()
    analizador.feed(html)
    return analizador


def luminancia(hex_color):
    canales = [int(hex_color[i: i + 2], 16) / 255 for i in (1, 3, 5)]
    lineal = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]


def contraste(color_a, color_b):
    claro, oscuro = sorted([luminancia(color_a), luminancia(color_b)], reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def tokens_css():
    texto = (CSS_DIR / "marca.css").read_text(encoding="utf-8")
    return {nombre: valor.lower() for nombre, valor in re.findall(r"(--ula-[a-z]+)\s*:\s*(#[0-9a-fA-F]{6})", texto)}


class PaginasAccesiblesTests(TestCase):
    def paginas(self):
        for nombre in PAGINAS_PUBLICAS:
            yield nombre, self.client.get(reverse(nombre)).content.decode()
        crear_usuario()
        self.client.login(correo_institucional=CORREO_COMPRADOR, password=CONTRASENA_VALIDA)
        yield "cuentas:mi_cuenta", self.client.get(reverse("cuentas:mi_cuenta")).content.decode()

    def test_rnf03_todas_las_paginas_declaran_viewport_movil(self):
        for nombre, html in self.paginas():
            with self.subTest(pagina=nombre):
                viewport = [m for m in analizar(html).metas if m.get("name") == "viewport"]
                self.assertEqual(len(viewport), 1)
                self.assertIn("width=device-width", viewport[0]["content"])

    def test_rnf11_todas_las_imagenes_tienen_texto_alternativo(self):
        for nombre, html in self.paginas():
            for imagen in analizar(html).imagenes:
                with self.subTest(pagina=nombre, imagen=imagen.get("src")):
                    self.assertIn("alt", imagen)
                    decorativa = imagen.get("aria-hidden") == "true"
                    self.assertTrue(decorativa or imagen["alt"].strip())

    def test_rnf11_cada_campo_tiene_una_etiqueta_asociada(self):
        for nombre, html in self.paginas():
            analisis = analizar(html)
            for campo in analisis.campos:
                with self.subTest(pagina=nombre, campo=campo.get("name")):
                    self.assertIn(campo.get("id"), analisis.etiquetas)

    def test_las_paginas_estan_en_espanol(self):
        for nombre, html in self.paginas():
            with self.subTest(pagina=nombre):
                self.assertRegex(html, r'<html lang="es')

    def test_el_encabezado_usa_el_logotipo_institucional_vectorial(self):
        html = self.client.get(reverse("inicio")).content.decode()
        self.assertRegex(html, r'<img[^>]+src="[^"]*img/logo-ucla\.svg"[^>]+alt="Universidad Católica Luis Amigó"')


class IdentidadVisualTests(SimpleTestCase):
    def test_los_tokens_de_color_son_los_del_manual(self):
        tokens = tokens_css()
        self.assertEqual(tokens["--ula-azul"], "#007b99")
        self.assertEqual(tokens["--ula-naranja"], "#f39200")
        self.assertEqual(tokens["--ula-gris"], "#848585")
        self.assertEqual(tokens["--ula-blanco"], "#ffffff")

    def test_ninguna_hoja_de_estilo_ni_plantilla_usa_colores_fuera_de_la_paleta(self):
        archivos = list(CSS_DIR.glob("*.css"))
        for raiz in PLANTILLAS:
            archivos += list(raiz.rglob("*.html"))
        for archivo in archivos:
            texto = archivo.read_text(encoding="utf-8")
            with self.subTest(archivo=archivo.name):
                self.assertNotRegex(texto, r"\b(rgba?|hsla?)\(", "Usa los tokens HEX de la paleta")
                for color in re.findall(r"#[0-9a-fA-F]{3,8}\b", texto):
                    self.assertIn(color.lower(), PALETA_INSTITUCIONAL, f"{color} en {archivo.name}")

    def test_rnf11_las_combinaciones_de_texto_cumplen_contraste_4_5(self):
        t = tokens_css()
        combinaciones = {
            "texto negro sobre blanco": (t["--ula-negro"], t["--ula-blanco"]),
            "azul (títulos, enlaces) sobre blanco": (t["--ula-azul"], t["--ula-blanco"]),
            "blanco sobre azul (botones, panel)": (t["--ula-blanco"], t["--ula-azul"]),
            "negro sobre naranja (insignias)": (t["--ula-negro"], t["--ula-naranja"]),
        }
        for nombre, (texto, fondo) in combinaciones.items():
            with self.subTest(combinacion=nombre):
                self.assertGreaterEqual(contraste(texto, fondo), 4.5)

    def test_rnf11_los_bordes_de_los_campos_cumplen_contraste_3(self):
        """WCAG 1.4.11: los límites de los controles necesitan 3:1."""
        t = tokens_css()
        self.assertGreaterEqual(contraste(t["--ula-gris"], t["--ula-blanco"]), 3)

    def test_rnf11_naranja_y_gris_no_se_usan_como_color_de_texto_sobre_blanco(self):
        """El naranja (2.35:1) y el gris (3.7:1) no alcanzan 4.5:1 sobre blanco."""
        t = tokens_css()
        self.assertLess(contraste(t["--ula-naranja"], t["--ula-blanco"]), 4.5)
        self.assertLess(contraste(t["--ula-gris"], t["--ula-blanco"]), 4.5)
        estilos = (CSS_DIR / "app.css").read_text(encoding="utf-8")
        for regla in re.findall(r"(?<![-\w])color\s*:\s*var\((--[a-z-]+)\)", estilos):
            with self.subTest(token=regla):
                self.assertNotIn(regla, {"--ula-naranja", "--ula-gris", "--color-acento", "--color-borde"})
