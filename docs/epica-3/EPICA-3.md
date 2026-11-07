# Épica 3 · Catálogo

**Proyecto:** Emprendi Amigos (MVP) · Universidad Católica Luis Amigó
**Fuentes:** Entregable 1 (HU-07 a HU-10, RF-09 a RF-12, RNF-01), Entregable 2 (CU-07 a CU-10, diagramas A3 y S4, ES1, reglas RN-09 y RN-18, supuesto S-4) y *Manual de Identidad Visual* versión 02.
**Estado:** entregada para revisión. No se ha iniciado la Épica 4.

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Comprador |
| Qué cubre | Ver, filtrar por tipo de producto y buscar |
| Historias | HU-07 Ver el catálogo (Must, 2 h) · HU-08 Filtrar por categoría (Must, 2 h) · HU-09 Ver el detalle de un producto y su emprendimiento (Must, 2 h) · HU-10 Buscar por palabra clave (Should, 1 h) |
| Casos de uso | CU-07, CU-08 «extend» CU-07, CU-09 y CU-10 «extend» CU-07 (actor Comprador) |
| RF | RF-09, RF-10 y RF-12 (Must) y RF-11 (Should) |
| RNF de la épica | **RNF-01** (asociado a HU-07) y los transversales que aplican: RNF-03, RNF-06 (sin datos personales en páginas públicas), RNF-09 (300 productos) y RNF-11 |
| Reglas de negocio | RN-09 (catálogo sin desactivados, agotados con etiqueta) y RN-18 (sin "Contactar" en un producto propio) |
| Diagramas que implementa | S4 (secuencia del catálogo con filtro), la parte del catálogo y el detalle de A3, y el estado *Desactivado* de ES1 (aviso por enlace directo) |

**RNF que no aplican todavía:** RNF-02 (encontrar un producto y abrir el chat en 3 minutos o menos) necesita el chat de la Épica 4 y se medirá allí con usuarios. RNF-07 y RNF-10 tampoco aplican a esta épica.

Según el supuesto S-4 del Entregable 2, el catálogo, el filtro, la búsqueda y el detalle **no exigen sesión**; solo contactar la exige.

### 1.1 El botón "Contactar"

HU-09 Esc. 1 exige que el detalle muestre el botón "Contactar". La conversación es de la Épica 4 (HU-11 y HU-12). Por eso, en esta épica el botón sigue A3 hasta donde corresponde a E3:

- **Producto propio:** no aparece el botón (RN-18). En su lugar se ve "Este producto es tuyo. Editarlo".
- **Sin sesión:** lleva a iniciar sesión y luego regresa al producto (A3: "pedir iniciar sesión", y el flujo continúa con CU-02).
- **Con sesión:** abre una página provisional "Contactar a …", con los horarios y la zona de entrega del emprendimiento. La Épica 4 la reemplaza por la conversación.

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E3 |
|---|---|---|
| **Módulo Catálogo** | `apps/catalogo/servicios.py` | `listar_productos()` y `filtrar_por_categoria()` con los nombres de S4, y `buscar_por_palabra()` (CU-10) |
| | `apps/catalogo/busqueda.py` | Comparación sin mayúsculas, tildes ni diéresis (función pura) |
| Capa de presentación | `apps/catalogo/views.py`, `templates/catalogo/` | Listado con fichas de categoría, buscador, paginación, detalle y aviso de "no disponible" |
| Módulo Perfil y productos (E2) | `Producto.objects.visibles_en_catalogo()` y la tarjeta `_tarjeta_producto.html` | Contrato RN-09 y la misma tarjeta que ve el emprendedor en su vista previa |
| Almacenamiento de fotos | Miniatura de 600 px por producto (**CC-06**) | Tarjetas livianas para cumplir RNF-01 |
| Datos de demostración | `python manage.py cargar_demo` | Contenido para la demo y para medir RNF-01 (riesgo R4) |

### 2.1 Diagrama S4 implementado

| Mensaje de S4 | Código |
|---|---|
| `listarProductos()` → consultar productos no desactivados | `servicios.listar_productos()` → `visibles_en_catalogo()`: disponibles primero y luego los más recientes |
| alt "no hay productos activos" → mensaje de catálogo vacío | "Todavía no hay productos en el catálogo." |
| opt `filtrarPorCategoria(categoria)` → consultar productos de la categoría | `servicios.filtrar_por_categoria()` (S-1: la categoría es la del emprendimiento) |
| alt "la categoría no tiene productos" → mensaje de que no hay resultados | "No hay productos en la categoría …" |

### 2.2 Rutas

| Ruta | Acceso | HU / RF |
|---|---|---|
| `/catalogo/` | Público | HU-07 · RF-09 |
| `/catalogo/?categoria=comida` | Público | HU-08 · RF-10 |
| `/catalogo/?q=arepa` (combinable con `categoria` y `pagina`) | Público | HU-10 · RF-11 |
| `/catalogo/productos/<código>/` | Público | HU-09 · RF-12 |
| `/catalogo/productos/<código>/contactar/` | Con sesión | A3, página provisional hasta E4 |

El encabezado tiene el enlace "Catálogo" para todos y la portada tiene el botón "Ver el catálogo".

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-09 | Listar los productos activos | Tarjetas con foto, nombre, emprendimiento, categoría, precio y estado; agotados con etiqueta y al final; desactivados ocultos; 24 por página | CP-07.1 a CP-07.5 |
| RF-10 | Filtrar los productos por categoría | Fichas "Todas", "Artesanías", "Comida", "Ocio", "Otros" y "Videojuegos" con la actual marcada (`aria-current`); "Limpiar filtros" | CP-08.1 a CP-08.4 |
| RF-11 | Buscar productos por palabra clave | Busca en el nombre del producto, sin distinguir mayúsculas ni tildes; si hay varias palabras, todas deben aparecer; se combina con el filtro | CP-10.1 a CP-10.4 |
| RF-12 | Ver el detalle de un producto y de su emprendimiento | Foto completa, precio, estado, nombre, categoría, descripción, horarios y zona del emprendimiento, y el botón "Contactar" según A3; aviso si el producto fue desactivado | CP-09.1 a CP-09.4 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E3 | Prueba |
|---|---|---|---|
| **RNF-01 Rendimiento** | Must | Paginación de 24 productos; tarjetas con miniaturas de 600 px (CC-06); las 4 primeras imágenes cargan de inmediato y el resto al desplazarse; la página hace 3 consultas sin importar cuántos productos haya. Medido en Chromium con **100 productos visibles**, sin caché y con la red limitada (tabla 3.3) | CP-RNF01 |
| RNF-03 Compatibilidad | Must | Catálogo, filtro, búsqueda y detalle verificados a 360, 768 y 1280 px sin desplazamiento horizontal | CP-RNF03 |
| RNF-06 Cumplimiento legal | Must | Las páginas públicas no muestran correos ni otros datos personales del emprendedor | CP-RNF06 |
| RNF-09 Escalabilidad | Should | Con 300 productos, el listado, el filtro, la búsqueda y la paginación responden correctamente | CP-RNF09 |
| RNF-11 Accesibilidad | Could | Buscador con etiqueta y `role="search"`; categorías como enlaces con `aria-current`; toda la tarjeta es clicable sin anidar enlaces y muestra el foco; texto alternativo en cada foto; total de resultados anunciado con `role="status"` | CP-RNF11 |

### 3.3 Medición de RNF-01

`scripts/medir_catalogo.mjs`, con 100 productos visibles (`cargar_demo --solo-disponibles`), sin caché y mediana de 3 cargas. Los perfiles de red son los de Chrome DevTools: "4G" = 9 Mbit/s y 60 ms; "4G lento" = 1,6 Mbit/s y 150 ms.

| Perfil | Ancho | Carga completa (`load`) | LCP | Transferido |
|---|---|---|---|---|
| 4G | 360 px | 230 ms | 224 ms | 88 KB |
| 4G | 1280 px | 232 ms | 228 ms | 205 KB |
| 4G lento (referencia) | 360 px | 703 ms | 724 ms | 88 KB |
| 4G lento (referencia) | 1280 px | 696 ms | 728 ms | 130 KB |

**Resultado:** cumple con amplio margen (límite: 3000 ms).

**Limitaciones de la medición:**
- Las fotos de demostración son imágenes generadas, más livianas que fotos reales.
- Se usó el servidor de desarrollo y no el de producción.

Conviene repetir la medición en el entorno desplegado y con las fotos reales de los emprendedores piloto (R4).

---

## 4. Identidad visual aplicada

| Componente | Aplicación |
|---|---|
| Fichas de categoría | Borde gris (3.7:1, sirve para controles) y texto azul; la ficha seleccionada va en azul con texto blanco (4.89:1) |
| Buscador | Campo con borde gris y botón primario azul |
| Tarjeta de producto | La misma de E2: nombre en azul, precio en negro, estados *Disponible* (azul) y *Agotado* (naranja con texto negro) |
| Detalle | Título con línea y punto final, como en el manual; botón "Contactar" primario azul |

**Capturas** (Chromium, `scripts/verificar_interfaz.mjs` con `cargar_demo`):

| Vista | Archivo |
|---|---|
| Catálogo a 1280 px (100 productos, página 1 de 5) | [e3-catalogo-1280.png](capturas/e3-catalogo-1280.png) |
| Filtro "Comida" con búsqueda "arepa" a 360 px | [e3-catalogo-filtro-360.png](capturas/e3-catalogo-filtro-360.png) |
| Búsqueda sin resultados a 360 px | [e3-catalogo-sin-resultados-360.png](capturas/e3-catalogo-sin-resultados-360.png) |
| Detalle a 1280 y 360 px | [e3-detalle-1280.png](capturas/e3-detalle-1280.png) · [e3-detalle-360.png](capturas/e3-detalle-360.png) |

---

## 5. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E3-01 | La búsqueda compara solo el **nombre del producto** | RF-11 dice "buscar productos por palabra clave". Incluir el nombre del emprendimiento hacía que "arepa" trajera también el café de "Arepas Doña Rosa" |
| DT-E3-02 | La búsqueda se resuelve en Python sobre los productos visibles | Funciona igual en SQLite y en PostgreSQL. A la escala de RNF-09 (300 productos) tarda milisegundos. Si el catálogo creciera mucho, se cambiaría por una columna normalizada o por `unaccent` de PostgreSQL |
| DT-E3-03 | 24 productos por página | Mantiene liviana la primera carga (RNF-01) y cabe en filas de 2, 3 o 4 columnas |
| DT-E3-04 | Disponibles primero y luego los más recientes | El comprador ve primero lo que puede pedir; los agotados siguen visibles (RN-09) |
| DT-E3-05 | La categoría va en la URL como texto legible (`?categoria=artesanias`) | Enlaces que se pueden compartir; una categoría inexistente muestra todo el catálogo |
| DT-E3-06 | Un producto desactivado abierto por enlace directo responde 404 con el aviso "Este producto ya no está disponible" | HU-09 Esc. 2 y estado *Desactivado* de ES1; no muestra precio ni datos |
| DT-E3-07 | Página provisional al contactar con sesión | Cumple HU-09 y A3 sin adelantar la Épica 4 |
| DT-E3-08 | **CC-06**: miniatura de 600 px por producto, generada al publicar o cambiar la foto y creada con una migración para los productos que ya existían | Las tarjetas pesan unos 10 a 50 KB en lugar de cientos; el detalle usa la foto completa |
| DT-E3-09 | `cargar_demo` solo funciona con DEBUG activo o con `--forzar`, y solo crea cuentas `demo.…@amigo.edu.co` | Evita mezclar datos de demostración con datos reales; `--limpiar` borra solo las cuentas de demostración |

### 5.1 Puntos para decidir antes de la Épica 4

1. **¿Un emprendedor puede contactar a otro emprendedor?** HU-11 habla del comprador, y el punto B.2 sigue abierto. Hoy el botón aparece para cualquier cuenta que no sea la dueña del producto. Recomiendo mantenerlo así: un emprendedor también es parte de la comunidad y puede comprar.
2. **Búsqueda por emprendimiento.** Si quieren buscar también por el nombre del emprendimiento, se puede agregar como resultado secundario (unos 30 minutos).
3. **CC-06** (miniaturas) es un cambio de diseño, sin cambio de requerimiento, y quedó en el registro de cambios. Necesita su visto bueno junto con esta épica.

### 5.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E3-catalogo` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí (223 pruebas: 90 de E1, 78 de E2 y 55 de E3) |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en E1 y E2 |

---

## 6. Batería de pruebas de validación

### 6.1 Cómo ejecutarla

```bash
git pull
pip install -r requirements.txt
python manage.py migrate                      # aplica 0004_miniatura (CC-06)
python manage.py test -v 2
python manage.py cargar_demo --limpiar        # 10 emprendimientos y 100 productos
python manage.py runserver
```

Cuentas de demostración (contraseña `Clave-Segura-2026`): `demo.comprador@amigo.edu.co` y `demo.emprendedor01@amigo.edu.co` a `demo.emprendedor10@amigo.edu.co`.

### 6.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 223 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` (ver README) | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Rendimiento (RNF-01) | `cargar_demo --limpiar --productos 100 --solo-disponibles` + `runserver` + `node scripts/medir_catalogo.mjs` | Termina con "RNF-01 cumplido" (mediana ≤ 3000 ms con 4G en 360 y 1280 px) |
| G5 Casos manuales | Tabla 6.3, casos con M | Todos cumplen su criterio |

- **APROBADA:** G1 a G5 pasan.
- **APROBADA CON AJUSTES:** solo falla un caso Should o Could (CP-10.x, CP-RNF09, CP-RNF11), o se pide alguno de los puntos de 5.1.
- **NO APROBADA:** falla G1 a G4, o cualquier caso Must (HU-07, HU-08, HU-09, RNF-01, RNF-03 o RNF-06).

### 6.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-07.1 a CP-10.3 son los del Anexo A del Entregable 2; los demás completan la cobertura.

#### HU-07 · Ver el catálogo (Must · RF-09, RNF-01)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-07.1 | Con productos activos | A+M | Sin iniciar sesión, pulsar "Catálogo" en el encabezado | Tarjetas con foto, nombre, emprendimiento, categoría, precio y estado; total "N productos" | **Aprueba** si se ven los productos activos y se abre sin sesión |
| CP-07.2 | Sin productos | A+M | Con la base vacía (o tras desactivar todo), abrir el catálogo | "Todavía no hay productos en el catálogo." | **Aprueba** si muestra el mensaje |
| CP-07.3 | Desactivados | A+M | Desactivar un producto desde el panel del emprendedor y buscarlo en el catálogo | No aparece | **Aprueba** si ningún desactivado aparece |
| CP-07.4 | Agotados y orden | A+M | Marcar un producto como agotado y revisar el catálogo | Se ve con la etiqueta **Agotado**, después de los disponibles | **Aprueba** si se cumple |
| CP-07.5 | Paginación | A+M | Con 100 productos, ir a la página siguiente y probar `?pagina=abc` | 24 por página, "Página 1 de 5", "Anterior" y "Siguiente"; una página inválida no da error | **Aprueba** si se recorren las 5 páginas |

#### HU-08 · Filtrar por categoría (Must · RF-10)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-08.1 | Filtro con resultados | A+M | Pulsar la ficha "Artesanías" | Solo productos de emprendimientos de Artesanías; la ficha queda marcada; "N productos en Artesanías" | **Aprueba** si no aparece ninguna otra categoría |
| CP-08.2 | Filtro sin resultados | A+M | Elegir una categoría sin productos (en la demo, desactiva los de "Otros") | "No hay productos en la categoría …" | **Aprueba** si muestra el mensaje |
| CP-08.3 | Limpiar filtros | A+M | Con un filtro activo, pulsar "Todas" o "Limpiar filtros" | Vuelve el catálogo completo | **Aprueba** si regresa el total original |
| CP-08.4 | Categoría inexistente | A | Abrir `/catalogo/?categoria=no-existe` | Catálogo completo, sin ficha de categoría marcada | **Aprueba** si no hay error |

#### HU-09 · Ver el detalle (Must · RF-12)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-09.1 | Detalle completo | A+M | Pulsar cualquier tarjeta | Foto completa, nombre, precio, estado, nombre del emprendimiento, categoría, descripción, horarios, zona de entrega y botón **Contactar**; ningún correo visible | **Aprueba** si están todos los datos |
| CP-09.2 | Desactivado por enlace directo | A+M | Copiar la URL de un producto, desactivarlo desde el panel y abrir la URL | "Este producto ya no está disponible" y botón "Ir al catálogo"; sin precio | **Aprueba** si se ve el aviso |
| CP-09.3 | Contactar sin sesión (A3) | A+M | Sin sesión, pulsar "Contactar" e iniciar sesión | Pide iniciar sesión y luego regresa al mismo producto | **Aprueba** si vuelve al producto |
| CP-09.4 | Producto propio (RN-18) | A+M | Con `demo.emprendedor01`, abrir uno de sus productos | No aparece "Contactar"; aparece "Este producto es tuyo. Editarlo" | **Aprueba** si no hay botón |
| CP-09.5 | Contactar con sesión | A+M | Con `demo.comprador`, pulsar "Contactar" | Página provisional "Contactar a …" con horarios y zona (la conversación llega en E4) | **Aprueba** si abre la página del emprendimiento correcto |

#### HU-10 · Buscar por palabra clave (Should · RF-11)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-10.1 | Coincidencia | A+M | Buscar `arepa` | Solo productos cuyo nombre contiene "arepa"; "N productos para «arepa»" | **Aprueba** si todos los resultados coinciden |
| CP-10.2 | Sin coincidencias | A+M | Buscar `zzzz` | "No encontramos productos para «zzzz»." | **Aprueba** si muestra el mensaje |
| CP-10.3 | Mayúsculas y tildes | A+M | Buscar `café`, `CAFÉ` y `cafe` | Los tres dan los mismos resultados | **Aprueba** si son idénticos |
| CP-10.4 | Búsqueda con filtro | A+M | Con la ficha "Comida" activa, buscar `arepa`; luego buscar `pulsera` | Combina ambos; "No encontramos productos para «pulsera» en la categoría Comida." | **Aprueba** si respeta los dos criterios |

#### RNF y cambios

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RNF01 | Rendimiento (Must) | A+M | G4 (`medir_catalogo.mjs`); además, en Chrome DevTools → Network → "Fast 4G" con caché desactivada, recargar `/catalogo/` con 100 productos | Mediana ≤ 3000 ms; en DevTools, el evento "Load" ≤ 3 s | **Aprueba** si ambas mediciones están por debajo de 3 s. En el servidor, la suite verifica además que responde en menos de 1 s y con un número fijo de consultas |
| CP-RNF03 | Responsive (Must) | A+M | Catálogo, filtro, búsqueda sin resultados y detalle a 360 px en Chrome, Edge, Firefox y Safari | Sin desplazamiento horizontal; fichas y buscador usables con el dedo | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF06 | Datos personales (Must) | A+M | Revisar el código fuente (Ctrl+U) del catálogo y del detalle | No aparece ningún correo `@amigo.edu.co` | **Aprueba** si no hay correos |
| CP-RNF09 | 300 productos (Should) | A+M | `cargar_demo --limpiar --productos 300` y recorrer el catálogo | 13 páginas; filtro y búsqueda correctos | **Aprueba** si todo responde |
| CP-RNF11 | Accesibilidad (Could) | A+M | Con el teclado: Tab hasta el buscador, buscar, elegir una ficha y abrir un producto con Enter | Foco visible en cada paso; la tarjeta enfocada se resalta completa | **Aprueba** si se completa sin mouse |
| CP-CC06 | Miniaturas (diseño) | A | Publicar y cambiar la foto de un producto | Se genera una miniatura JPEG de 600 px sin EXIF; al cambiar la foto se borra la anterior; el catálogo y la vista previa usan la miniatura | **Aprueba** si la suite pasa |
| CP-DEMO | Datos de demostración | A+M | `cargar_demo --limpiar`, luego otra vez con `--limpiar` | Se crean y reemplazan solo las cuentas `demo.…`; con DEBUG desactivado y sin `--forzar` se niega | **Aprueba** si no toca otras cuentas |

### 6.4 Trazabilidad de las pruebas automáticas

| Archivo | Pruebas | Casos que cubre |
|---|---|---|
| `apps/catalogo/tests/test_busqueda.py` | 9 | CP-10.3 (unitario), normalización |
| `apps/catalogo/tests/test_hu07_catalogo.py` | 11 | CP-07.1 a CP-07.5, S4 `listarProductos()` |
| `apps/catalogo/tests/test_hu08_filtro.py` | 6 | CP-08.1 a CP-08.4, S4 `filtrarPorCategoria()` |
| `apps/catalogo/tests/test_hu09_detalle.py` | 10 | CP-09.1 a CP-09.5, RN-18 |
| `apps/catalogo/tests/test_hu10_busqueda.py` | 9 | CP-10.1 a CP-10.4 |
| `apps/catalogo/tests/test_rnf.py` | 6 | CP-RNF01 (servidor), CP-RNF03, CP-RNF06, CP-RNF09, CP-RNF11 |
| `apps/catalogo/tests/test_cargar_demo.py` | 4 | CP-DEMO |
| `apps/perfil_productos/tests/test_miniaturas.py` | 4 | CP-CC06 |
| **Total nuevo** | **59** | (más 164 de E1 y E2 = 223) |

Antes de entregar, la suite se probó contra cuatro defectos introducidos a propósito, y todos se detectaron:

- listar también los desactivados: 4 fallos;
- buscar distinguiendo tildes: 8 fallos;
- mostrar "Contactar" en el producto propio: 1 fallo;
- quitar `select_related`, lo que genera consultas N+1: 1 fallo.

Al revertir los cambios, las 223 pruebas volvieron a pasar.
