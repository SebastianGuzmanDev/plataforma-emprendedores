"""
RNF aplicables a la Épica 3:
- RNF-01 Rendimiento (Must): el catálogo carga en 3 s o menos con 100 productos.
  Aquí se mide la parte del servidor; la carga completa en el navegador se mide con
  scripts/medir_catalogo.mjs (CP-RNF01).
- RNF-09 Escalabilidad (Should): 300 productos registrados.
- RNF-03 y RNF-11: viewport, etiquetas y texto alternativo en el catálogo y el detalle.
- RNF-06: las páginas públicas no exponen correos.
"""
import time
from html.parser import HTMLParser

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from .utilidades import (
    CORREO_EMPRENDEDOR_A,
    CORREO_EMPRENDEDOR_B,
    URL_CATALOGO,
    cargar_productos,
    emprendimientos_de_prueba,
    url_detalle,
)


def consultas(cliente, url, **parametros):
    with CaptureQueriesContext(connection) as contexto:
        respuesta = cliente.get(url, parametros)
    assert respuesta.status_code == 200
    return len(contexto.captured_queries)


class RendimientoTests(TestCase):
    def setUp(self):
        self.comida, self.artesanias = emprendimientos_de_prueba()

    def test_rnf01_con_100_productos_el_servidor_responde_muy_por_debajo_de_3_segundos(self):
        cargar_productos(100, self.comida)
        inicio = time.perf_counter()
        respuesta = self.client.get(URL_CATALOGO)
        duracion = time.perf_counter() - inicio
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "100 productos")
        self.assertLess(duracion, 1.0, f"El servidor tardó {duracion:.2f} s")

    def test_rnf01_las_consultas_no_crecen_con_la_cantidad_de_productos(self):
        cargar_productos(5, self.comida, prefijo="Pocos")
        pocos = consultas(self.client, URL_CATALOGO)
        cargar_productos(95, self.artesanias, prefijo="Muchos")
        muchos = consultas(self.client, URL_CATALOGO)
        self.assertEqual(pocos, muchos)
        self.assertLessEqual(muchos, 4)
        self.assertLessEqual(consultas(self.client, URL_CATALOGO, q="muchos", categoria="artesanias"), muchos)

    def test_rnf09_con_300_productos_el_catalogo_filtra_y_busca_correctamente(self):
        cargar_productos(150, self.comida, prefijo="Arepa")
        cargar_productos(150, self.artesanias, prefijo="Pulsera")
        self.assertContains(self.client.get(URL_CATALOGO), "300 productos")
        self.assertContains(self.client.get(URL_CATALOGO, {"categoria": "artesanias"}), "150 productos en Artesanías")
        self.assertContains(self.client.get(URL_CATALOGO, {"q": "pulsera 149"}), "1 producto para «pulsera 149»")
        self.assertEqual(self.client.get(URL_CATALOGO, {"pagina": 13}).status_code, 200)


class _Analizador(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imagenes, self.campos, self.etiquetas, self.viewport = [], [], set(), False

    def handle_starttag(self, etiqueta, atributos):
        attrs = dict(atributos)
        if etiqueta == "img":
            self.imagenes.append(attrs)
        elif etiqueta in ("input", "select", "textarea") and attrs.get("type") not in ("hidden", "submit"):
            self.campos.append(attrs)
        elif etiqueta == "label" and attrs.get("for"):
            self.etiquetas.add(attrs["for"])
        elif etiqueta == "meta" and attrs.get("name") == "viewport":
            self.viewport = "width=device-width" in attrs.get("content", "")


class InterfazPublicaTests(TestCase):
    def setUp(self):
        comida, _ = emprendimientos_de_prueba()
        self.producto = cargar_productos(3, comida)[0]
        self.paginas = {
            "catalogo": URL_CATALOGO,
            "catalogo filtrado": f"{URL_CATALOGO}?categoria=comida&q=producto",
            "sin resultados": f"{URL_CATALOGO}?q=zzz",
            "detalle": url_detalle(self.producto),
        }

    def analizar(self, url):
        analizador = _Analizador()
        analizador.feed(self.client.get(url).content.decode())
        return analizador

    def test_rnf03_viewport_y_rnf11_etiquetas_y_textos_alternativos(self):
        for nombre, url in self.paginas.items():
            pagina = self.analizar(url)
            with self.subTest(pagina=nombre):
                self.assertTrue(pagina.viewport)
                for campo in pagina.campos:
                    self.assertIn(campo.get("id"), pagina.etiquetas, campo)
                for imagen in pagina.imagenes:
                    decorativa = imagen.get("aria-hidden") == "true"
                    self.assertTrue(decorativa or imagen.get("alt", "").strip(), imagen)

    def test_rnf06_las_paginas_publicas_no_muestran_correos(self):
        for nombre, url in self.paginas.items():
            html = self.client.get(url).content.decode()
            with self.subTest(pagina=nombre):
                self.assertNotIn(CORREO_EMPRENDEDOR_A, html)
                self.assertNotIn(CORREO_EMPRENDEDOR_B, html)

    def test_el_buscador_es_un_formulario_get_con_etiqueta(self):
        html = self.client.get(URL_CATALOGO).content.decode()
        self.assertIn('role="search"', html)
        self.assertIn('<label for="id_q"', html)
        self.assertIn('type="search"', html)
