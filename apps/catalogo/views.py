"""
Vistas del módulo E3 · Catálogo (capa de presentación). Supuesto S-4 del Entregable 2:
catálogo, filtro, búsqueda y detalle no exigen sesión; contactar sí (A3).
"""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.perfil_productos.models import Producto

from . import servicios
from .busqueda import LONGITUD_MAXIMA_CONSULTA


def _parametros(**valores):
    limpios = {clave: valor for clave, valor in valores.items() if valor}
    return f"?{urlencode(limpios)}" if limpios else ""


def listado(request):
    """HU-07 · CU-07, con las extensiones CU-08 (filtro) y CU-10 (búsqueda). Diagrama S4."""
    categorias = servicios.categorias()
    categoria = servicios.categoria_por_slug(categorias, request.GET.get("categoria", "").strip())
    consulta = request.GET.get("q", "").strip()[:LONGITUD_MAXIMA_CONSULTA]

    productos = servicios.listar_productos()
    if categoria:
        productos = servicios.filtrar_por_categoria(productos, categoria)
    if consulta:
        productos = servicios.buscar_por_palabra(productos, consulta)

    paginador = Paginator(productos, settings.CATALOGO_PRODUCTOS_POR_PAGINA)
    pagina = paginador.get_page(request.GET.get("pagina"))
    slug = categoria.slug if categoria else ""
    return render(
        request,
        "catalogo/listado.html",
        {
            "productos": pagina.object_list,
            "pagina": pagina,
            "total": paginador.count,
            "categorias": [
                {"categoria": c, "url": _parametros(categoria=c.slug, q=consulta), "actual": c == categoria}
                for c in categorias
            ],
            "url_todas": _parametros(q=consulta) or request.path,
            "categoria": categoria,
            "consulta": consulta,
            "hay_filtros": bool(categoria or consulta),
            "url_anterior": _parametros(categoria=slug, q=consulta, pagina=pagina.previous_page_number())
            if pagina.has_previous() else "",
            "url_siguiente": _parametros(categoria=slug, q=consulta, pagina=pagina.next_page_number())
            if pagina.has_next() else "",
        },
    )


def _producto_publico(codigo):
    return get_object_or_404(Producto.objects.select_related("emprendimiento__categoria"), codigo=codigo)


def detalle(request, codigo):
    """HU-09 · CU-09: detalle del producto y su emprendimiento; aviso si está desactivado."""
    producto = _producto_publico(codigo)
    if not producto.es_visible_en_catalogo:
        return render(request, "catalogo/no_disponible.html", status=404)
    es_propio = request.user.is_authenticated and producto.emprendimiento.propietario_id == request.user.pk
    return render(
        request,
        "catalogo/detalle.html",
        {"producto": producto, "emprendimiento": producto.emprendimiento, "es_propio": es_propio},
    )


@login_required
def contactar(request, codigo):
    """
    A3 · «Presionar Contactar» con sesión iniciada. La conversación (HU-11 a HU-14) se
    construye en la Épica 4; por ahora se muestra cómo encontrar al emprendedor.
    """
    producto = _producto_publico(codigo)
    if not producto.es_visible_en_catalogo:
        return render(request, "catalogo/no_disponible.html", status=404)
    if producto.emprendimiento.propietario_id == request.user.pk:  # RN-18
        return redirect("catalogo:detalle", codigo=producto.codigo)
    return render(request, "catalogo/contactar.html", {"producto": producto, "emprendimiento": producto.emprendimiento})
