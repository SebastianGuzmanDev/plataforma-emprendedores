"""
HU-10 · RF-11 · Búsqueda por palabra clave sin distinguir mayúsculas ni tildes.

«café», «CAFÉ» y «cafe» son equivalentes (Entregable 2, plan de pruebas 4.1.4). Todas
las palabras de la consulta deben aparecer en alguno de los textos del producto.
"""
import unicodedata

LONGITUD_MAXIMA_CONSULTA = 80


def normalizar_texto(texto):
    """Minúsculas, sin tildes ni diéresis (ñ → n) y con espacios simples."""
    if not texto:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    sin_marcas = "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))
    return " ".join(sin_marcas.casefold().split())


def coincide(textos, consulta):
    """True si cada palabra de la consulta aparece en los textos. Una consulta vacía no filtra."""
    palabras = normalizar_texto(consulta).split()
    if not palabras:
        return True
    if isinstance(textos, str):
        textos = [textos]
    contenido = " ".join(normalizar_texto(texto) for texto in textos)
    return all(palabra in contenido for palabra in palabras)
