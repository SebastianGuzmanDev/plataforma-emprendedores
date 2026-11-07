# Épica 2 · Perfil y productos

**Proyecto:** Plataforma de Emprendedores (MVP) · Universidad Católica Luis Amigó
**Fuentes:** Entregable 1 (HU-04 a HU-06, RF-05 a RF-08, RNF), Entregable 2 (CU-04 a CU-06, diagramas A2, ES1 y S3, modelo de dominio, reglas RN-05 a RN-09, decisión D5) y *Manual de Identidad Visual* versión 02.
**Estado:** aprobada con los cambios CC-02 (reactivación), CC-03 (nombre del emprendimiento) y CC-04 (plataforma **Emprendi Amigos**); ver la sección 8 y el [registro de cambios](../registro-de-cambios.md). La Épica 3 agrega a este módulo la miniatura de cada producto (CC-06).

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Emprendedor |
| Qué cubre | Publicar y mantener el portafolio |
| Historias | HU-04 Crear el perfil de mi emprendimiento (Must, 2 h) · HU-05 Publicar un producto (Must, 3 h) · HU-06 Editar, desactivar y marcar agotado un producto (Must, 2 h) |
| Casos de uso | CU-04, CU-05 y CU-06 (actor Emprendedor) |
| RF | RF-05, RF-06, RF-07 y RF-08 (todos Must) |
| RNF de la épica | RNF-05 (asociado a HU-06) y los transversales que aplican: RNF-03, RNF-04, RNF-06, RNF-08, RNF-09 (Should, aquí se verifican los 300 productos) y RNF-11 (Could, texto alternativo en las fotos) |
| Reglas de negocio | RN-05, RN-06, RN-07, RN-08 y RN-09 |
| Diagramas que implementa | A2 (actividades), ES1 (estados de Producto), S3 (secuencia de la publicación); clases `Categoria`, `Emprendimiento`, `Producto` y `EstadoProducto` |

**RNF que no aplican a esta épica:** RNF-01 y RNF-02 (catálogo y chat, E3 y E4), RNF-07 (entorno desplegado, Sprint 4) y RNF-10 (mensajes, E4).

### 1.1 Escenarios que mencionan "el catálogo"

HU-04, HU-05 y HU-06 terminan con frases como "queda visible en el catálogo" o "deja de aparecer en el catálogo". La pantalla pública del catálogo es la HU-07 de la Épica 3. Para no adelantar esa épica, E2 entrega dos cosas:

1. **El contrato del catálogo (RN-09):** las consultas `Producto.objects.visibles_en_catalogo()` y `Emprendimiento.objects.visibles_en_catalogo()`. El catálogo de E3 se construirá sobre ellas. Las pruebas de E2 verifican cada escenario contra este contrato.
2. **La vista previa del emprendedor** (`/emprendimiento/vista-previa/`). Aplica la misma regla y la misma tarjeta de producto que usará el catálogo, para revisar a mano lo que verá un comprador.

Cuando exista el catálogo, los casos CP-07.x de la Épica 3 repetirán la verificación en la pantalla pública.

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E2 |
|---|---|---|
| Capa de presentación | `apps/perfil_productos/forms.py`, `views.py`, `templates/perfil_productos/` | Formularios de perfil y producto, panel del emprendedor, confirmación de la desactivación y vista previa |
| **Módulo Perfil y productos** | `reglas.py` (RN-07), `servicios.py` (CU-04 a CU-06, nombres de S3), `models.py` (máquina de estados ES1 y contrato RN-09) | Publicar, editar, marcar agotado y desactivar; solo el dueño (RN-08) |
| Capa de acceso a datos | `models.py` (ORM) | `Categoria`, `Emprendimiento`, `Producto` y restricciones `CHECK` (precio ≥ 0, estado válido) |
| Almacenamiento de fotos (D5) | `MEDIA_ROOT`, separado de la base de datos | Fotos normalizadas de hasta 5 MB |
| Módulo Cuentas y acceso (E1) | `rol_requerido(Rol.EMPRENDEDOR)` | Todas las pantallas de E2 exigen el rol Emprendedor |

### 2.1 Modelo de dominio → código

| Clase del diagrama | Código | Nota |
|---|---|---|
| `Categoria(nombre)` | `Categoria.nombre` | Se crean con una migración: Comida, Artesanías, Videojuegos, Ocio y Otros |
| `Emprendimiento(nombre, descripcion, horarios, zonaEntrega)` | `nombre` (80, CC-03), `descripcion` (500), `horarios` (120), `zona_entrega` (120), `categoria`, `propietario` | Usuario 1 — 0..1 Emprendimiento (S-2): `OneToOneField` |
| `Producto(nombre, foto, precioReferencia, estado)` | `nombre` (80), `foto`, `precio_referencia` (pesos enteros), `estado`, `codigo` | `codigo` es un UUID para las rutas. `existencias` y `umbralStockBajo` se agregan en E5 |
| `EstadoProducto` | `DISPONIBLE`, `AGOTADO`, `DESACTIVADO` | Estado inicial: `DISPONIBLE` |
| Operaciones `crearPerfil()`, `editarPerfil()`, `publicar()`, `editar()`, `marcarAgotado()`, `marcarDisponible()` (CC-02), `desactivar()` | `servicios.guardar_perfil`, `publicar_producto`, `editar_producto`, `marcar_agotado`, `marcar_disponible`, `desactivar_producto` | Las transiciones se validan en el modelo |

### 2.2 Diagrama de estados ES1 implementado (versión 2, con CC-02)

| Origen | Evento | Destino | Dónde |
|---|---|---|---|
| (inicio) | Publicar producto | Disponible | `publicar_producto` |
| Disponible o Agotado | Editar (por ejemplo, el precio) | El mismo estado | `Producto.validar_edicion` |
| Disponible | Marcar agotado | Agotado | `Producto.marcar_agotado` |
| Agotado | Marcar disponible (CC-02) | Disponible | `Producto.marcar_disponible` |
| Disponible o Agotado | Desactivar | Desactivado | `Producto.desactivar` (con confirmación) |
| Desactivado | Cualquier acción | — | Se rechaza con un mensaje (`TransicionNoPermitida`) |

*Desactivado* sigue siendo definitivo: así el dueño no puede deshacer una desactivación del administrador (HU-22). El diagrama actualizado está en [`docs/diagramas/ES1-producto-v2.puml`](../diagramas/ES1-producto-v2.puml) y reemplaza la figura 7 del Entregable 2.

La salida de inventario que deja las existencias en 0 (HU-16) usará `marcar_agotado` cuando se construya E5.

### 2.3 Flujo (A2 y S3)

1. **Perfil (A2):** si falta algún campo obligatorio, se rechaza el envío y se señala el campo. Si están todos, se crea el perfil y queda visible.
2. **Publicación (A2 y S3):** sin perfil, se envía al emprendedor a crearlo (RN-05). Con perfil, se valida primero el tamaño de la foto y luego el precio. Si todo es válido, se guarda la foto y después el producto con estado *Disponible*. Al final el emprendedor ve el producto publicado en su panel.

### 2.4 Rutas

| Ruta | Método | HU / RF |
|---|---|---|
| `/emprendimiento/` | GET | Panel: perfil y portafolio |
| `/emprendimiento/perfil/` | GET, POST | HU-04 · RF-05 |
| `/emprendimiento/vista-previa/` | GET | HU-04 a HU-06 (lo que verá el comprador) |
| `/emprendimiento/productos/nuevo/` | GET, POST | HU-05 · RF-06 |
| `/emprendimiento/productos/<código>/editar/` | GET, POST | HU-06 · RF-07 |
| `/emprendimiento/productos/<código>/agotado/` | POST | HU-06 · RF-08 |
| `/emprendimiento/productos/<código>/disponible/` | POST | CC-02 · RF-08 |
| `/emprendimiento/productos/<código>/desactivar/` | GET (confirmar), POST | HU-06 · RF-08 |

Todas exigen el rol Emprendedor. Un comprador o un administrador reciben 403; sin sesión, se pide iniciarla.

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-05 | Crear el perfil del emprendimiento (nombre —CC-03—, descripción, categoría, horarios y zona de entrega) | `PerfilForm` con los cinco campos obligatorios (RN-06); un perfil por emprendedor; el mismo formulario edita | CP-04.1 a CP-04.5 |
| RF-06 | Publicar un producto con foto (hasta 5 MB) y precio de referencia | `ProductoForm` + `publicar_producto`. La foto se valida por tamaño y por contenido real (JPG, PNG o WebP). El precio se acepta como `5000`, `5.000` o `$ 5.000` y se rechaza si es negativo o tiene letras | CP-05.1 a CP-05.5 |
| RF-07 | Editar un producto | `editar_producto`: nombre, precio y, de forma opcional, una foto nueva (la anterior se borra del almacenamiento). Con CC-02 también se editan los agotados | CP-06.1, CP-06.7 |
| RF-08 | Desactivar un producto, marcarlo como agotado o (CC-02) volver a marcarlo disponible | `marcar_agotado`, `marcar_disponible` y `desactivar_producto`, según ES1 v2 y solo por POST; la desactivación pide confirmación | CP-06.2, CP-06.3, CP-06.5, CP-06.6 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E2 | Prueba |
|---|---|---|---|
| RNF-03 Compatibilidad | Must | Panel, formularios, vista previa y tarjetas responsive; verificado a 360, 768 y 1280 px sin desplazamiento horizontal | CP-RNF03 |
| RNF-04 Seguridad | Must | CSRF en todos los formularios; cambios de estado solo por POST; se valida el contenido real de la foto (un HTML o SVG disfrazado de `.jpg` se rechaza) y se guarda siempre como JPEG con nombre aleatorio | CP-05.4, CP-06.5 |
| RNF-05 Privacidad | Must | El emprendedor se identifica por la sesión; un producto ajeno responde 403 y no cambia; panel y vista previa muestran solo lo propio; las rutas usan un código no secuencial | CP-06.4, CP-RNF05 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad versión 1.2: incluye el perfil (con su nombre) y los productos y su publicación en el catálogo. Antes de guardar cada foto se borran sus metadatos EXIF, incluida la ubicación GPS. El formulario del perfil avisa que será público. Una prueba falla si se agrega un dato no previsto en el modelo | CP-RNF06 |
| RNF-08 Mantenibilidad | Must | Módulo propio `apps/perfil_productos`, commits por historia, documento de la épica y README actualizados | CP-RNF08 |
| RNF-09 Escalabilidad | Should | Con 100 usuarios y 300 productos, el contrato del catálogo responde completo y el panel usa el mismo número de consultas con 10 o con más de 100 productos | CP-RNF09 |
| RNF-11 Accesibilidad | Could | Cada foto tiene como texto alternativo el nombre del producto; los estados se leen como texto y no solo por color; cada campo tiene etiqueta; los botones repetidos nombran su producto para los lectores de pantalla | CP-RNF11 |

---

## 4. Identidad visual aplicada

Los componentes nuevos usan solo los tokens de `static/css/marca.css`. La prueba de paleta de E1 revisa también las plantillas y estilos de E2.

| Componente | Aplicación |
|---|---|
| Estado *Disponible* | Texto y borde azul sobre blanco (4.89:1) |
| Estado *Agotado* | Fondo naranja con texto negro (8.9:1): el naranja comunica la alerta sin usarse como color de texto |
| Estado *Desactivado* | Borde punteado negro |
| Fichas de categoría y tarjetas de producto | Borde gris (3.7:1, cumple 3:1 para controles) y azul al seleccionar |
| Títulos | Línea con punto final, como en el manual |

**Capturas** (Chromium, `scripts/verificar_interfaz.mjs` con una cuenta emprendedora de demostración):

| Vista | Archivo |
|---|---|
| Panel del emprendedor a 1280 y 360 px | [e2-panel-1280.png](capturas/e2-panel-1280.png) · [e2-panel-360.png](capturas/e2-panel-360.png) |
| Edición del perfil (fichas de categoría) | [e2-perfil-1280.png](capturas/e2-perfil-1280.png) |
| Publicación con errores a 360 px (HU-05) | [e2-publicar-errores-360.png](capturas/e2-publicar-errores-360.png) |
| Vista previa del comprador a 1280 y 360 px | [e2-vista-previa-1280.png](capturas/e2-vista-previa-1280.png) · [e2-vista-previa-360.png](capturas/e2-vista-previa-360.png) |

---

## 5. Cambios sobre la Épica 1

| Cambio | Motivo | Pruebas de E1 afectadas |
|---|---|---|
| El panel provisional `/cuentas/panel/emprendedor/` se reemplaza por `/emprendimiento/` | E1 lo había dejado como punto de entrada de E2 | `test_roles.py`: solo cambia la constante de la ruta; los casos (200 para emprendedor, 403 para comprador, inicio de sesión sin cuenta) son los mismos |
| Aviso de privacidad versión 1.1 | Nuevos datos (perfil, productos y fotos) y nueva finalidad (publicación en el catálogo), según la Ley 1581 | `test_rnf_legal.py`: la versión esperada se lee del ajuste en lugar de estar fija en "1.0" |
| Mi cuenta avisa a quien aceptó una versión anterior del aviso | Informar al titular del cambio | Ninguna (prueba nueva en E2) |
| Encabezado con el enlace "Mi emprendimiento" para emprendedores | Navegación | Ninguna |

---

## 6. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E2-01 | Validar la foto por contenido real (Pillow) y no solo por extensión | Evita que se suban archivos maliciosos con nombre `.jpg` (RNF-04) |
| DT-E2-02 | Normalizar la foto: orientación correcta, sin EXIF, lado mayor de 1600 px, JPEG con calidad 85 y nombre aleatorio | Quita la ubicación GPS y otros datos ocultos (RNF-06) y mantiene liviano el catálogo de E3 (RNF-01). El límite de 5 MB se aplica a la foto que sube el usuario |
| DT-E2-03 | Precio en pesos enteros; se aceptan `5000`, `5.000` y `$ 5.000` | El peso colombiano no usa centavos en la práctica; el punto es el separador de miles habitual |
| DT-E2-04 | Código UUID en las rutas de productos | Las rutas no revelan cuántos productos hay ni permiten recorrerlos en orden; el control real sigue siendo el de dueño (RN-08) |
| DT-E2-05 | Producto ajeno → 403 "acceso denegado"; código inexistente → 404 | HU-06 Esc. 4 dice "me deniega el acceso" |
| DT-E2-06 | Confirmación antes de desactivar | Según ES1, la desactivación no tiene vuelta atrás |
| DT-E2-07 | Contrato del catálogo y vista previa en lugar de la pantalla pública | Cumple los escenarios sin adelantar HU-07 (E3); ver 1.1 |

| # | Supuesto (el Entregable 1 no lo define) | Decisión |
|---|---|---|
| S-E2-1 | Lista de categorías | Comida, Artesanías, Videojuegos y Ocio (nombradas en el alcance) más "Otros" por el "etc.". **Confirmado (CC-05)** |
| S-E2-2 | Precio de 0 (punto abierto B.2) | Se acepta, porque RN-07 solo exige "no negativo". **Confirmado (CC-05)** |
| S-E2-3 | Formatos de foto | JPG, PNG y WebP; GIF y SVG no |
| S-E2-4 | Longitudes máximas | Descripción 500, horarios 120, zona 120 y nombre del producto 80 caracteres |
| S-E2-5 | Fotos en producción | `MEDIA_ROOT` configurable con `DJANGO_MEDIA_ROOT`; en el Sprint 4 se define quién las sirve (servidor web o almacenamiento de objetos) y un límite del cuerpo de la petición de unos 6 MB en el servidor web |

### 6.1 Puntos que necesitaban decisión del equipo (resueltos el 06/11/2026)

Los puntos 1 a 3 se aprobaron como CC-02 y CC-03 (sección 8). El punto 4 queda informado: Mi cuenta avisa a quien aceptó una versión anterior del aviso, que ahora es la 1.2.

1. **Reactivación (punto abierto B.2 y nota de ES1).** Hoy un producto agotado no puede volver a *Disponible*, así que quien vende comida a diario tendría que publicarlo de nuevo cada día. Recomiendo aprobar la transición *Agotado → Disponible* como solicitud de cambio (CC-02, unos 30 minutos más actualizar ES1). La desactivación debería seguir siendo definitiva, para que no se pueda deshacer una desactivación del administrador (HU-22).
2. **Editar un producto agotado.** ES1 solo modela la edición en *Disponible*, y así quedó implementado. Si se aprueba el punto 1, se resuelve en el mismo cambio.
3. **Nombre del emprendimiento.** RF-05 y el modelo de dominio no lo incluyen, por eso la vista previa titula "Emprendimiento de comida". Recomiendo agregarlo (CC-03, unos 30 minutos) antes de construir el catálogo de E3.
4. **Aviso 1.1 y cuentas existentes.** Las cuentas que aceptaron la versión 1.0 ven el aviso de actualización en Mi cuenta. Si ya hay emprendedores piloto registrados (R4), conviene pedirles que lo revisen.

### 6.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E2-perfil-y-productos` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí (164 pruebas: 90 de E1 y 74 de E2, con CC-02 a CC-04) |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en E1: aún no hay entorno de pruebas |

---

## 7. Batería de pruebas de validación

### 7.1 Cómo ejecutarla

```bash
pip install -r requirements.txt        # E2 agrega Pillow
python manage.py migrate               # crea las tablas y las 5 categorías
python manage.py test -v 2             # E1 + E2
python manage.py runserver
```

Para los pasos manuales: registra una cuenta **Emprendedor** (por ejemplo `emprende1@amigo.edu.co`) y otra **Emprendedor** (`emprende2@amigo.edu.co`), con la contraseña `Clave-Segura-2026`. Usa una foto JPG de tu teléfono (idealmente con ubicación activada) y otra de más de 5 MB.

### 7.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 164 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` (ver README) | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Casos manuales | Tabla 7.3, columna "Tipo" con M | Todos cumplen su criterio |

- **APROBADA:** G1 a G4 pasan.
- **APROBADA CON AJUSTES:** solo falla CP-RNF09 o CP-RNF11 (Should y Could), o se pide alguno de los cambios de 6.1. Los cambios se registran en el registro de cambios y se aplican antes de E3.
- **NO APROBADA:** falla G1, G2 o G3, o falla cualquier otro caso (todas las historias de E2 son Must).

### 7.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-04.x a CP-06.4 son los del Anexo A del Entregable 2; los demás completan la cobertura.

#### HU-04 · Crear el perfil de mi emprendimiento (Must · RF-05)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-04.1 | Perfil válido | A+M | 1. Ingresar como `emprende1`. 2. "Mi emprendimiento" → "Crear perfil". 3. Completar nombre ("Arepas Doña Rosa"), descripción, categoría Comida, horarios y zona. 4. "Publicar perfil". 5. "Ver como comprador". | "El perfil de tu emprendimiento quedó publicado…"; la vista previa se titula con el nombre y muestra los demás datos | **Aprueba** si el perfil se crea y se ve en la vista previa. **No aprueba** en otro caso |
| CP-04.2 | Campo obligatorio vacío | A+M | Repetir dejando vacío, uno a la vez, cada campo (también con solo espacios) | Mensaje específico junto al campo ("Escribe el nombre…", "Escribe la descripción…", "Elige la categoría…", "Indica tus horarios…", "Indica la zona de entrega.") y en el resumen; no se crea el perfil | **Aprueba** si cada campo vacío se señala por su nombre. **No aprueba** si se guarda o el error no indica el campo |
| CP-04.3 | Edición del perfil | A+M | "Editar perfil", cambiar a Artesanías y otra descripción; guardar; abrir la vista previa | "Guardamos los cambios de tu perfil"; la vista previa muestra lo nuevo y ya no lo anterior; sigue habiendo un solo perfil | **Aprueba** si se actualiza sin duplicarse |
| CP-04.4 | Acceso por rol | A | Comprador y usuario sin sesión intentan abrir `/emprendimiento/perfil/` | 403 y pedir inicio de sesión, respectivamente | **Aprueba** si ninguno crea un perfil |
| CP-04.5 | Nombre del emprendimiento (CC-03) | A+M | Escribir un nombre de más de 80 caracteres; revisar el panel y la vista previa | "El nombre puede tener hasta 80 caracteres…"; el panel y el título de la vista previa muestran el nombre y ya no "Emprendimiento de comida" | **Aprueba** si se cumple |

#### HU-05 · Publicar un producto (Must · RF-06)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-05.1 | Publicación exitosa | A+M | "Publicar producto": nombre "Arepa de queso", una foto JPG y precio `5.000`. Publicar y abrir "Ver como comprador". | "Publicaste «Arepa de queso»…"; en la vista previa aparece con foto, "$ 5.000" y la etiqueta **Disponible** | **Aprueba** si aparece como Disponible con el precio correcto |
| CP-05.2 | Foto mayor a 5 MB | A+M | Publicar con una foto de más de 5 MB | "La foto pesa X MB y el límite es 5 MB."; no se publica. Una foto de exactamente 5 MB sí se acepta (A) | **Aprueba** si se rechaza indicando el límite |
| CP-05.3 | Precio inválido | A+M | Precios `-1000`, `abc` y `12a` | "Escribe el precio solo con números, sin signos negativos ni letras…"; no se publica y se conserva el nombre escrito | **Aprueba** si los tres se rechazan |
| CP-05.4 | Archivo que no es imagen | A+M | Renombrar un PDF o TXT como `foto.jpg` y subirlo | "El archivo no es una imagen JPG, PNG o WebP." | **Aprueba** si se rechaza |
| CP-05.5 | Sin perfil (RN-05) | A+M | Con `emprende2` (aún sin perfil), abrir `/emprendimiento/productos/nuevo/` | Redirige a crear el perfil con "Antes de publicar productos, crea el perfil de tu emprendimiento." | **Aprueba** si no se puede publicar sin perfil |
| CP-05.6 | Foto sin metadatos | A+M | Descargar la foto publicada (clic derecho → abrir imagen) y revisar sus propiedades o pasarla por un visor EXIF | No conserva ubicación GPS, modelo del teléfono ni fecha; mide como máximo 1600 px de lado | **Aprueba** si no queda ningún metadato |

#### HU-06 · Editar, desactivar y marcar agotado (Must · RF-07, RF-08, RNF-05)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-06.1 | Cambio de precio | A+M | En el panel, "Editar" la arepa; cambiar el precio a `7.500` sin subir foto; guardar; ver la vista previa | "Guardamos los cambios…"; la vista previa muestra "$ 7.500" y conserva la foto | **Aprueba** si el precio nuevo se ve y el anterior no |
| CP-06.2 | Marcar como agotado | A+M | "Marcar agotado" en un producto disponible; ver la vista previa | "…quedó marcado como agotado…"; en la vista previa sigue visible con la etiqueta **Agotado** | **Aprueba** si sigue visible con la etiqueta |
| CP-06.3 | Desactivación | A+M | "Desactivar" → confirmar "Sí, desactivar"; ver la vista previa | Pide confirmación ("no se puede deshacer"); "…quedó desactivado y ya no aparece en el catálogo"; la vista previa ya no lo muestra; el panel lo lista en "Desactivados" sin acciones | **Aprueba** si desaparece de la vista previa |
| CP-06.4 | Producto ajeno | A+M | 1. Con `emprende1`, copiar la URL de "Editar" de un producto. 2. Cerrar sesión, ingresar con `emprende2` (con perfil) y abrir esa URL. 3. Probar también la de "Desactivar". | "No tienes permiso para ver esta página" (403); el producto de `emprende1` no cambia | **Aprueba** si se deniega en todos los casos. **No aprueba** si `emprende2` ve o modifica algo |
| CP-06.5 | Reglas de ES1 v2 | A | Volver a agotar un agotado; marcar disponible uno disponible; editar, agotar o reactivar un desactivado; enviar un cambio de estado por GET | Se informa que no está permitido y el estado no cambia; GET responde 405 | **Aprueba** si ninguna transición fuera de ES1 v2 ocurre |
| CP-06.6 | Volver a estar disponible (CC-02) | A+M | En un producto agotado, pulsar "Marcar disponible"; ver la vista previa | "…volvió a estar disponible en el catálogo"; la vista previa lo muestra como **Disponible** | **Aprueba** si regresa a Disponible |
| CP-06.7 | Editar un agotado (CC-02) | A+M | En un producto agotado, "Editar" y cambiar el precio | Se guarda el precio y el producto sigue **Agotado** | **Aprueba** si cambia el precio y no el estado |
| CP-06.8 | Desactivado definitivo (CC-02) | A+M | Revisar en el panel un producto desactivado | Aparece en "Desactivados" sin botones; intentar reactivarlo (A) responde "no se puede reactivar" | **Aprueba** si no hay forma de reactivarlo |

#### RN-09 y RNF

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RN09 | Contrato del catálogo | A | Productos en los tres estados de dos emprendimientos | El catálogo incluye Disponible y Agotado, oculta Desactivado; cada producto lleva la categoría de su emprendimiento; una sola consulta | **Aprueba** si la suite pasa |
| CP-RNF03 | Responsive (Must) | A+M | Panel, perfil, publicar (con errores) y vista previa a 360 px en Chrome, Edge, Firefox y Safari; opcional `EMPRENDEDOR_CORREO=… EMPRENDEDOR_CONTRASENA=… node scripts/verificar_interfaz.mjs` | Sin desplazamiento horizontal; botones y fichas usables con el dedo | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF05 | Privacidad (Must) | A+M | Como comprador, abrir `/emprendimiento/`; como `emprende2`, revisar su panel y su vista previa | 403 para el comprador; `emprende2` no ve productos de `emprende1` | **Aprueba** si nadie ve ni modifica lo ajeno |
| CP-RNF06 | Ley 1581 (Must) | A+M | Abrir `/privacidad/`; en Mi cuenta de una cuenta registrada antes del cambio | Aviso versión 1.2 con el perfil (nombre incluido), los productos, su publicación en el catálogo y la eliminación de la ubicación GPS; aviso de actualización en Mi cuenta | **Aprueba** si están ambos |
| CP-CC04 | Nombre de la plataforma (CC-04) | A+M | Revisar el encabezado, el título de la pestaña y el correo de recuperación (en la terminal) | Dicen "Emprendi Amigos" y no "Plataforma de Emprendedores" | **Aprueba** si se cumple en los tres |
| CP-RNF08 | Repositorio (Must) | M | `git log --oneline` y README | Commits que nombran HU-04, HU-05 y HU-06; README con E2 y la dependencia Pillow | **Aprueba** si existen ambos |
| CP-RNF09 | 300 productos (Should) | A | 100 usuarios, 30 emprendimientos y 300 productos | El catálogo devuelve los 270 visibles; el panel hace las mismas consultas con 10 o con más de 100 productos | **Aprueba** si la suite pasa |
| CP-RNF11 | Accesibilidad (Could) | A+M | Publicar y mantener un producto solo con el teclado; revisar el texto alternativo de las fotos | Se completa sin mouse; cada foto tiene como `alt` el nombre del producto; los estados se leen como texto | **Aprueba** si se cumple |

### 7.4 Trazabilidad de las pruebas automáticas

| Archivo (`apps/perfil_productos/tests/`) | Pruebas | Casos que cubre |
|---|---|---|
| `test_reglas.py` | 21 | RN-07 (precio y foto, valores límite del plan 4.1.4), CP-05.6, ES1 v2 |
| `test_hu04_perfil.py` | 13 | CP-04.1 a CP-04.5, categorías iniciales |
| `test_hu05_publicar.py` | 10 | CP-05.1 a CP-05.5 |
| `test_hu06_mantener.py` | 15 | CP-06.1 a CP-06.8 |
| `test_catalogo_contrato.py` | 4 | CP-RN09 |
| `test_rnf.py` | 11 | CP-RNF03, CP-RNF05, CP-RNF06, CP-RNF09, CP-RNF11 |
| **Total E2** | **74** | (más las 90 de E1, que incluyen las 2 de CP-CC04 = 164) |

Antes de entregar, la suite se probó contra cuatro defectos introducidos a propósito, y todos se detectaron:

- quitar el control de dueño: 6 fallos;
- mostrar los productos desactivados en el catálogo: 5 fallos;
- tratar el límite de foto como "menor que 5 MB" y conservar el EXIF: 3 fallos;
- permitir editar productos agotados: 2 fallos.

Al revertir los cambios, las 155 pruebas volvieron a pasar.

---

## 8. Cambios aprobados el 06/11/2026

| CC | Qué cambió en el código | Pruebas |
|---|---|---|
| CC-02 Reactivación | `Producto.marcar_disponible()` (*Agotado → Disponible*), ruta `/productos/<código>/disponible/` (solo POST y solo el dueño), botón "Marcar disponible" en el panel. `validar_edicion` permite editar agotados. *Desactivado* sigue siendo definitivo | CP-06.5 a CP-06.8 y 5 pruebas unitarias de ES1 v2 |
| CC-03 Nombre del emprendimiento | Campo `Emprendimiento.nombre` obligatorio (80 caracteres) en el formulario, el panel y el título de la vista previa. La migración `0003` asigna "Mi emprendimiento" a los perfiles existentes. Aviso de privacidad 1.2 | CP-04.1, CP-04.2, CP-04.5 y CP-RNF06 |
| CC-04 Emprendi Amigos | `NOMBRE_PLATAFORMA = "Emprendi Amigos"` en el encabezado, los títulos y el correo de recuperación | CP-CC04 (2 pruebas en `apps/cuentas/tests/test_rnf_interfaz.py`) |
| CC-05 Supuestos confirmados | Sin cambios: se mantienen la categoría "Otros" y el precio 0 | — |

Para comprobar las pruebas nuevas se introdujeron dos defectos a propósito, y ambos se detectaron:

- permitir reactivar un producto desactivado: 5 fallos;
- quitar el nombre del formulario de perfil: 15 fallos.

Al revertirlos, las 164 pruebas volvieron a pasar.

**Artefactos de los Entregables por actualizar** (Word, fuera del repositorio): RF-05, RF-08 y RN-06 en la matriz, los escenarios nuevos de HU-06, la figura 7 (ES1, fuente en `docs/diagramas/ES1-producto-v2.puml`), el atributo `nombre` en la clase `Emprendimiento` y el registro de cambios de la sección 4.2.2. El texto exacto está en [`docs/registro-de-cambios.md`](../registro-de-cambios.md).
