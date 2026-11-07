# Épica 4 · Contacto por chat

**Proyecto:** Emprendi Amigos (MVP) · Universidad Católica Luis Amigó
**Fuentes:** Entregable 1 (HU-11 a HU-14, RF-13 a RF-16, RNF-02, RNF-10, riesgo R3), Entregable 2 (CU-11 a CU-14, diagramas A3, S5 y C1, clases `Conversacion` y `Mensaje`, reglas RN-16 a RN-18, decisión D3) y *Manual de Identidad Visual* versión 02.
**Estado:** aprobada el 07/11/2026, junto con CC-08 (el registro conserva el producto de origen). Queda pendiente aplicar el protocolo de RNF-02 con personas (sección 4.2).

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Ambos (comprador y emprendedor) |
| Qué cubre | Conversar para organizar la entrega |
| Historias | HU-11 Iniciar una conversación (Must, 3 h) · HU-12 Intercambiar mensajes con historial (Must, 4 h) · HU-13 Ver mis conversaciones (Must, 2 h) · HU-14 Ver cuántos mensajes tengo sin leer (Should, 2 h) |
| Casos de uso | CU-11 (incluye CU-02), CU-12, CU-13 y CU-14 |
| RF | RF-13, RF-14 y RF-15 (Must) y RF-16 (Should) |
| RNF de la épica | **RNF-10** (persistencia, asociado a HU-12), **RNF-02** (usabilidad, se completa con E3 y E4) y los transversales que aplican: RNF-03, RNF-05, RNF-06, RNF-09 y RNF-11 |
| Reglas de negocio | RN-16 (mensaje vacío; historial; asíncrono), RN-17 (orden por mensaje más reciente) y RN-18 (sin contacto con un producto propio) |
| Diagramas que implementa | S5 (contacto e intercambio de mensajes), C1 (colaboración equivalente), la parte del chat de A3, y las clases `Conversacion` y `Mensaje` |

**Riesgo R3** ("el chat resulta más complejo de lo estimado"): no se activó el Plan B (botón de WhatsApp). El chat se construyó como lo define D3: asíncrono, sin tiempo real, con el historial en la base de datos.

**RNF que no aplican:** RNF-01 (catálogo, E3) y RNF-07 (entorno desplegado).

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E4 |
|---|---|---|
| **Módulo Contacto por chat** | `apps/contacto/servicios.py` | `iniciar_conversacion`, `enviar_mensaje` y `obtener_mensajes` con los nombres de S5 y C1; `conversaciones_de` (HU-13) y `mensajes_sin_leer` (HU-14) |
| | `apps/contacto/reglas.py` | RN-16: mensaje no vacío y de hasta 1000 caracteres |
| Capa de presentación | `views.py`, `templates/contacto/`, `context_processors.py` | Lista de conversaciones, conversación con historial, botón "Actualizar" e indicador en el encabezado |
| Capa de acceso a datos | `models.py` | `Conversacion` y `Mensaje` con restricciones: una conversación por comprador y producto, nadie conversa consigo mismo y ningún mensaje vacío |
| Base de datos | Tablas `contacto_conversacion` y `contacto_mensaje` | RNF-10: el historial no depende de la sesión |
| Módulo Catálogo (E3) | Botón "Contactar" del detalle | Ahora envía un POST a `contacto:iniciar` |

### 2.1 Modelo de dominio → código

| Clase del diagrama | Código | Nota |
|---|---|---|
| `Conversacion` — comprador 1, emprendedor 1, producto (origen) 1 | `comprador`, `emprendedor`, `producto`, `creada`, `codigo` | `codigo` es un UUID para las rutas; `creada` sirve para ordenar las conversaciones sin mensajes |
| `Conversacion.abrir()`, `ultimoMensaje()` | `servicios.obtener_mensajes()`, `Conversacion.ultimo_mensaje()` | |
| `Mensaje(contenido, fechaEnvio, leido)` y autor | `contenido` (≤ 1000), `fecha_envio`, `leido`, `autor` | |
| `Mensaje.enviar()`, `marcarLeido()` | `servicios.enviar_mensaje()`, `Mensaje.marcar_leido()` | |

### 2.2 Diagramas S5 y C1 implementados

| Mensaje del diagrama | Código |
|---|---|
| 1: presionarContactar(producto) → 1.1: `iniciarConversacion(producto)` | POST `/mensajes/iniciar/<producto>/` → `servicios.iniciar_conversacion()` |
| alt "no hay sesión iniciada" → pedir iniciar sesión | `login_required`; en el detalle, el botón lleva a iniciar sesión y regresa al producto |
| 1.2: obtenerEmprendedor() · 1.3: crear(comprador, emprendedor, producto) | `producto.emprendimiento.propietario` y `Conversacion.objects.get_or_create(...)` |
| 2.1: `enviarMensaje(conversacion, contenido)` · alt "mensaje vacío" | `servicios.enviar_mensaje()` → `MensajeVacio`, y el formulario muestra "Escribe un mensaje antes de enviarlo." |
| 2.2: [texto no vacío] crear(texto, autor) · guardar Mensaje(leido = falso) | `Mensaje.objects.create(...)` con `leido=False` |
| 3: abrirConversacion() · 3.1: `obtenerMensajes(conversacion)` | GET `/mensajes/<código>/` → `servicios.obtener_mensajes()`, que además marca como leídos los de la otra persona (HU-14) |
| Nota: "mensajería asíncrona: la otra persona ve la respuesta al actualizar la vista" | Botón **Actualizar** y el aviso "Los mensajes no llegan en tiempo real…" |

### 2.3 Rutas

| Ruta | Método | HU / RF |
|---|---|---|
| `/mensajes/` | GET | HU-13 · RF-15 (y HU-14: "N sin leer" por conversación) |
| `/mensajes/iniciar/<código del producto>/` | POST (GET regresa al producto) | HU-11 · RF-13 |
| `/mensajes/<código de la conversación>/` | GET (historial) y POST (enviar) | HU-12 · RF-14 |

Todas exigen sesión. Solo los dos participantes abren una conversación: cualquier otra cuenta recibe 403. El encabezado muestra "Mensajes" con un contador de mensajes sin leer (HU-14).

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-13 | Iniciar una conversación con el emprendedor desde un producto | "Contactar" en el detalle crea la conversación o reabre la que ya existía con ese producto. Sin sesión pide iniciarla. En un producto propio no hay botón y el servidor rechaza el intento (RN-18) | CP-11.1 a CP-11.5 |
| RF-14 | Enviar y recibir mensajes con historial | Formulario de mensaje (1 a 1000 caracteres), historial en orden de envío, burbujas "Tú" y de la otra persona, botón "Actualizar" | CP-12.1 a CP-12.5 |
| RF-15 | Ver la lista de conversaciones | Ordenada por el mensaje más reciente (RN-17), con la otra persona, el producto, el último mensaje y su hora; mensaje si no hay conversaciones | CP-13.1 a CP-13.3 |
| RF-16 | Ver la cantidad de mensajes sin leer | Contador en el encabezado en todas las páginas y "N sin leer" en cada conversación; al abrirla, baja a 0 | CP-14.1, CP-14.2 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E4 | Prueba |
|---|---|---|---|
| **RNF-10 Persistencia** | Must | Los mensajes se guardan en la base de datos, no en la sesión; el historial sigue igual al cerrar sesión y volver a entrar | CP-12.3 |
| **RNF-02 Usabilidad** | Must | Recorrido corto: 4 acciones para encontrar el producto y 16 para abrir el chat, incluso creando la cuenta. El registro conserva el producto de origen y vuelve a él (sección 4) | CP-RNF02 |
| RNF-05 Privacidad | Must | Solo los participantes leen o escriben; un tercero recibe 403 y no puede marcar mensajes como leídos; los códigos de las rutas no son secuenciales; las páginas no quedan en caché | CP-RNF05 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad 1.3 sobre los mensajes. El emprendedor **no ve el correo** del comprador: lo identifica como "Comprador" con un código de 4 caracteres. El modelo guarda solo los datos del diagrama de clases | CP-RNF06 |
| RNF-03 Compatibilidad | Must | Lista y conversación verificadas a 360, 768 y 1280 px | CP-RNF03 |
| RNF-09 Escalabilidad | Should | La lista hace el mismo número de consultas con 3 o con 40 conversaciones | CP-RNF09 |
| RNF-11 Accesibilidad | Could | Campo de mensaje con etiqueta; contador con texto para lectores de pantalla ("3 mensajes sin leer"); el historial es una lista ordenada con nombre | CP-RNF11 |

---

## 4. RNF-02: un comprador nuevo encuentra un producto y abre el chat en 3 minutos o menos

### 4.1 Recorrido automatizado

`scripts/flujo_comprador.mjs` recorre el camino más largo: un teléfono de 360 px, sin sesión y **sin cuenta**.

| Tramo | Acciones | Resultado |
|---|---|---|
| Portada → "Ver el catálogo" → buscar "arepa" → abrir el producto | 4 | Producto encontrado en 0,5 s de máquina |
| "Contactar" → crear la cuenta (correo, rol, contraseña ×2, aviso) → iniciar sesión → regresa al mismo producto → "Contactar" | 12 | Chat abierto en 1,3 s de máquina |
| **Total** | **16** | El comprador **vuelve al producto** tras registrarse; el mensaje se envía y se ve |

Para lograrlo, esta épica ajustó el registro de la Épica 1 (sección 6): antes, quien se registraba desde "Contactar" perdía el producto y tenía que buscarlo otra vez.

### 4.2 Protocolo con personas (criterio de aceptación de RNF-02)

El tiempo de una máquina no mide la usabilidad. Según el plan de pruebas (Entregable 2, 4.1.5), se hace con 3 a 5 usuarios del prototipo:

1. **Participantes:** de 3 a 5 personas de la comunidad que no hayan usado la plataforma.
2. **Preparación:** `cargar_demo --limpiar`. Cada persona recibe un correo `@amigo.edu.co` de prueba y una contraseña, en un papel.
3. **Tarea, leída en voz alta:** "Estás en la universidad y te provoca una arepa. Encuentra una y escríbele al vendedor para preguntarle si la tiene hoy". La persona empieza en la portada, sin sesión, en su propio teléfono.
4. **Medición:** cronómetro desde que la persona toca la pantalla hasta que aparece la conversación ("Escribe tu primer mensaje…"). Se anotan las dudas, sin ayudar.
5. **Criterio:** **cada** participante abre el chat en **3:00 o menos**, incluido el registro.

| Participante | Tiempo hasta abrir el chat | ¿≤ 3:00? | Dudas o tropiezos observados |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 (opcional) | | | |
| 5 (opcional) | | | |

---

## 5. Identidad visual aplicada

| Componente | Aplicación |
|---|---|
| Mensajes propios | Burbuja azul con texto blanco (4.89:1) |
| Mensajes de la otra persona | Burbuja blanca con borde gris y texto negro |
| Contador de no leídos | Naranja con texto negro (8.9:1) y texto oculto para lectores de pantalla |
| Conversación con mensajes sin leer | Borde izquierdo naranja e insignia "N sin leer" |

**Capturas:**

| Vista | Archivo |
|---|---|
| Mis mensajes a 1280 y 360 px | [e4-mensajes-1280.png](capturas/e4-mensajes-1280.png) · [e4-mensajes-360.png](capturas/e4-mensajes-360.png) |
| Conversación a 360 px | [e4-conversacion-360.png](capturas/e4-conversacion-360.png) |
| Comprador nuevo: chat abierto y mensaje enviado (RNF-02) | [chat-abierto-360.png](capturas/chat-abierto-360.png) · [mensaje-enviado-360.png](capturas/mensaje-enviado-360.png) |

---

## 6. Cambios sobre las épicas anteriores

| Épica | Cambio | Motivo | Pruebas afectadas |
|---|---|---|---|
| E3 | La página provisional `/catalogo/productos/<código>/contactar/` se elimina; el botón "Contactar" del detalle envía un POST a `contacto:iniciar` | Era el lugar reservado para HU-11 | `test_hu09_detalle.py`: las 4 pruebas del botón ahora verifican el formulario nuevo; la del acceso sin sesión pasó a E4 (CP-11.2) |
| E1 | El registro conserva la página de origen (`?next=`), solo si es de este mismo sitio, y al terminar lleva a iniciar sesión con ese destino | RNF-02: quien se registraba desde "Contactar" perdía el producto | Ninguna: las de E1 siguen igual; se agregan 3 en `test_rnf02.py` |
| E1 y E2 | Aviso de privacidad 1.3 (mensajes) | Ley 1581: nuevos datos y finalidad | La prueba de E2 que fijaba "1.2" ahora lee la versión vigente |
| Todas | El encabezado agrega "Mensajes" con el contador | HU-14 | Ninguna |
| E3 | `cargar_demo` crea también 3 conversaciones de demostración (`--conversaciones`) | Probar E4 con contenido (R4) | 1 prueba nueva |

---

## 7. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E4-01 | Una conversación por comprador y producto: volver a pulsar "Contactar" la reabre | Evita hilos duplicados; HU-11 Esc. 1 se cumple la primera vez |
| DT-E4-02 | La conversación se crea al pulsar "Contactar" (S5), pero al emprendedor solo le aparece cuando tiene algún mensaje | No recibe conversaciones vacías si el comprador se arrepiente |
| DT-E4-03 | El emprendedor ve "Comprador XXXX" y no el correo | RNF-06, datos mínimos: para acordar la entrega basta el chat |
| DT-E4-04 | Asíncrono con el botón "Actualizar"; sin recarga automática | D3 y HU-12 Esc. 2 ("al actualizarla"); una recarga automática borraría lo que la persona está escribiendo |
| DT-E4-05 | Al abrir una conversación se marcan como leídos los mensajes de la otra persona | HU-14 Esc. 2 |
| DT-E4-06 | Mensajes de hasta 1000 caracteres; el campo de texto recibe el foco al abrir la conversación | Es la acción principal de la pantalla |
| DT-E4-07 | "Contactar" es un formulario POST con CSRF; un GET a esa ruta regresa al producto | Crear datos solo por POST; tras iniciar sesión el navegador vuelve sin crear nada (A3) |
| DT-E4-08 | El contador del encabezado se calcula en cada página con sesión (1 consulta); sin sesión no consulta | HU-14 Esc. 1: "cuando entro a la plataforma" |
| DT-E4-09 | Cualquier cuenta que no sea la dueña del producto puede contactar, incluso otro emprendedor | Decisión del 07/11/2026 (punto B.2) |

### 7.1 Puntos para considerar más adelante

1. **Avisos por correo de mensajes nuevos:** fuera del alcance (D6 limita el correo a la recuperación de contraseña). Si los emprendedores no revisan la plataforma, sería la primera mejora.
2. **Conservación y borrado de conversaciones:** el Entregable 1 no lo define. Hoy se conservan mientras existan las cuentas, y el aviso de privacidad explica cómo pedir su eliminación.
3. **Mensajes inapropiados:** HU-22 (E7) modera cuentas y productos, no mensajes. Al desactivar una cuenta, esa persona pierde el acceso y deja de escribir.

### 7.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E4-contacto-por-chat` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí (273 pruebas: 90 de E1, 78 de E2, 55 de E3 y 50 de E4) |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en las épicas anteriores |

---

## 8. Batería de pruebas de validación

### 8.1 Cómo ejecutarla

```bash
git pull
pip install -r requirements.txt
python manage.py migrate                 # crea contacto_conversacion y contacto_mensaje
python manage.py test -v 2
python manage.py cargar_demo --limpiar   # 100 productos y 3 conversaciones
python manage.py runserver
```

Cuentas de demostración (contraseña `Clave-Segura-2026`): `demo.comprador@amigo.edu.co` (tiene 3 conversaciones) y `demo.emprendedor02@amigo.edu.co` (Tejidos Juana, con mensajes sin leer). Para probar con dos personas a la vez, usa una ventana normal y otra privada.

### 8.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 273 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Recorrido de RNF-02 | `node scripts/flujo_comprador.mjs` (con `cargar_demo` y `runserver`) | Termina en "Recorrido de RNF-02 sin tropiezos" |
| G5 Casos manuales | Tabla 8.3, incluido el protocolo de la sección 4.2 | Todos cumplen su criterio |

- **APROBADA:** G1 a G5 pasan.
- **APROBADA CON AJUSTES:** solo falla un caso Should o Could (CP-14.x, CP-RNF09, CP-RNF11), o algún participante supera los 3 minutos por una causa de interfaz que se pueda corregir y quede registrada.
- **NO APROBADA:** falla G1 a G4, o cualquier caso Must (HU-11, HU-12, HU-13, RNF-05, RNF-06 o RNF-10).

### 8.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-11.1 a CP-14.2 son los del Anexo A del Entregable 2.

#### HU-11 · Iniciar una conversación (Must · RF-13)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-11.1 | Conversación nueva | A+M | Con `demo.comprador`, abrir un producto y pulsar **Contactar** | Se abre la conversación con el emprendimiento correcto, el producto arriba y "Escribe tu primer mensaje…" | **Aprueba** si se abre con el emprendedor del producto |
| CP-11.2 | Contactar sin sesión | A+M | Sin sesión, pulsar **Contactar** | Pide iniciar sesión y después regresa al producto | **Aprueba** si no se crea nada sin sesión |
| CP-11.3 | Producto propio (RN-18) | A+M | Con `demo.emprendedor01`, abrir uno de sus productos | No aparece **Contactar**; un POST forzado responde "No puedes contactarte a ti mismo" | **Aprueba** si no hay forma de contactarse a sí mismo |
| CP-11.4 | Otro emprendedor | A | Un emprendedor contacta el producto de otro | Se crea la conversación | **Aprueba** si se permite (DT-E4-09) |
| CP-11.5 | Volver a contactar | A+M | Pulsar **Contactar** dos veces en el mismo producto | Se abre la misma conversación, sin duplicados | **Aprueba** si en "Mis mensajes" aparece una sola |

#### HU-12 · Intercambiar mensajes con historial (Must · RF-14, RNF-10)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-12.1 | Enviar mensaje | A+M | Escribir "¿La tienes hoy?" y pulsar **Enviar** | Aparece como burbuja azul "Tú" con su hora | **Aprueba** si queda registrado |
| CP-12.2 | Recibir respuesta | A+M | Ventana A (comprador) y ventana privada B (emprendedor): B abre "Mensajes", responde; A pulsa **Actualizar** | A ve la respuesta debajo de su mensaje | **Aprueba** si se ve al actualizar |
| CP-12.3 | Historial persistente (RNF-10) | A+M | Cerrar sesión, volver a entrar y abrir la conversación | Todos los mensajes siguen ahí, en orden | **Aprueba** si no se pierde ninguno |
| CP-12.4 | Mensaje vacío (RN-16) | A+M | Pulsar **Enviar** vacío o solo con espacios | "Escribe un mensaje antes de enviarlo." y no se agrega nada | **Aprueba** si no se envía |
| CP-12.5 | Mensaje largo y contenido especial | A | Más de 1000 caracteres; texto con `<b>` y saltos de línea | Se rechaza el largo; el HTML se muestra como texto y los saltos se respetan | **Aprueba** si la suite pasa |

#### HU-13 · Ver mis conversaciones (Must · RF-15)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-13.1 | Lista ordenada (RN-17) | A+M | Con `demo.comprador`, abrir "Mensajes"; escribir en la última conversación de la lista y volver | Ordenadas por el mensaje más reciente: la que acabas de escribir sube al primer lugar | **Aprueba** si el orden sigue al último mensaje |
| CP-13.2 | Lista vacía | A+M | Con una cuenta nueva, abrir "Mensajes" | "Todavía no tienes conversaciones." y botón "Explorar el catálogo" | **Aprueba** si muestra el mensaje |
| CP-13.3 | Lo que ve el emprendedor | A+M | Con `demo.emprendedor02`, abrir "Mensajes" y la conversación | La otra persona aparece como "Comprador XXXX"; en ninguna parte se ve su correo | **Aprueba** si el correo no aparece (también con Ctrl+U) |

#### HU-14 · Ver cuántos mensajes tengo sin leer (Should · RF-16)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-14.1 | Cantidad sin leer | A+M | Con `demo.emprendedor02`, entrar a la plataforma | "Mensajes" con el contador naranja (p. ej. "2") y "2 sin leer" en la conversación | **Aprueba** si el número coincide con los mensajes no leídos |
| CP-14.2 | Lectura | A+M | Abrir la conversación y volver al inicio | El contador desaparece (0) | **Aprueba** si baja a 0 |

#### RNF

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RNF02 | Usabilidad (Must) | A+M | G4 y el protocolo de la sección 4.2 con 3 a 5 personas | Recorrido sin tropiezos; cada persona abre el chat en 3:00 o menos | **Aprueba** si todos los participantes cumplen. **No aprueba** si alguno supera 3:00 por un problema de la interfaz |
| CP-RNF05 | Privacidad (Must) | A+M | Copiar la URL de una conversación de `demo.comprador` y abrirla con `demo.emprendedor05` | "No tienes permiso…" (403); no ve ni puede escribir mensajes | **Aprueba** si un tercero no accede |
| CP-RNF06 | Ley 1581 (Must) | A+M | Abrir `/privacidad/` | Versión 1.3 con "Los mensajes que envías…", quién los ve y que el emprendedor no ve tu correo | **Aprueba** si están los tres puntos |
| CP-RNF03 | Responsive (Must) | A+M | "Mensajes" y una conversación a 360 px en Chrome, Edge, Firefox y Safari (opcional: `COMPRADOR_CORREO=… node scripts/verificar_interfaz.mjs`) | Sin desplazamiento horizontal; burbujas legibles; botón Enviar alcanzable | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF09 | Muchas conversaciones (Should) | A | 40 conversaciones | La lista hace las mismas consultas que con 3 | **Aprueba** si la suite pasa |
| CP-RNF11 | Accesibilidad (Could) | A+M | Con el teclado: abrir "Mensajes", entrar a una conversación, escribir y enviar | Foco visible; con lector de pantalla, el contador se lee "N mensajes sin leer" | **Aprueba** si se completa sin mouse |

### 8.4 Trazabilidad de las pruebas automáticas

| Archivo (`apps/contacto/tests/`) | Pruebas | Casos que cubre |
|---|---|---|
| `test_reglas.py` | 13 | RN-16, RN-17, RN-18; nombres de S5 (`iniciar_conversacion`, `enviar_mensaje`, `obtener_mensajes`) |
| `test_hu11_iniciar.py` | 8 | CP-11.1 a CP-11.5 |
| `test_hu12_mensajes.py` | 7 | CP-12.1 a CP-12.5 (CP-12.3 = RNF-10) |
| `test_hu13_hu14_lista.py` | 9 | CP-13.1 a CP-13.3, CP-14.1, CP-14.2 |
| `test_rnf.py` | 10 | CP-RNF05, CP-RNF06, CP-RNF03, CP-RNF09, CP-RNF11 |
| `test_rnf02.py` | 3 | CP-RNF02 (el registro conserva el producto) |
| **Total E4** | **50** | (más las 223 de E1 a E3, con los ajustes de la sección 6 = 273) |

Antes de entregar, la suite se probó contra cuatro defectos introducidos a propósito, y todos se detectaron:

- permitir que cualquier cuenta participe en una conversación: 2 fallos;
- aceptar mensajes vacíos: 5 fallos;
- no marcar como leído al abrir: 2 fallos;
- ordenar por la fecha de creación y no por el último mensaje: 2 fallos.

En este último caso, la prueba de integración CP-13.1 al principio pasó por coincidencia. Se reforzó para que el orden de creación y el del último mensaje sean distintos, y ahora también lo detecta. Al revertir los defectos, las 273 pruebas volvieron a pasar.
