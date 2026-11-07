# Épica 7 · Administración

**Proyecto:** Emprendi Amigos (MVP) · Universidad Católica Luis Amigó
**Fuentes:**
- **Entregable 1:** HU-22, RF-24 y RF-03 (el rol de administrador se asigna internamente).
- **Entregable 2:**
  - Caso de uso CU-22, y CU-02 flujo 2b ("cuenta desactivada por el administrador").
  - Regla RN-19; decisiones D4 y D6.
  - Transiciones de ES1 hacia *Desactivado* por el administrador.
  - Clases `Usuario` (atributo `activo`) y `Producto`.
  - Anexo A (CP-22.1 a CP-22.3) y punto abierto B.2 (canal de notificación).
- *Manual de Identidad Visual*, versión 02.

**Estado:** entregada para revisión. Es la última épica del alcance: con ella están implementadas las 22 historias del MVP.

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Administración |
| Qué cubre | Desactivar cuentas o contenido inapropiado, "como control mínimo para que la plataforma sea confiable" |
| Historia | HU-22 Desactivar contenido o cuentas inapropiadas (Could, 3 h) |
| Caso de uso | CU-22 (actor Administrador) |
| RF | RF-24 (Could) |
| RNF de la épica | D4 exige negar el acceso a quien no es administrador (HU-22 Esc. 3). También aplican RNF-05, RNF-03, RNF-06 y RNF-11 |
| Reglas de negocio | RN-19: solo el administrador desactiva productos o cuentas; una cuenta desactivada pierde el acceso |
| Diagramas | ES1: *Disponible → Desactivado* y *Agotado → Desactivado* "o lo desactiva el administrador". CU-22 no tiene diagrama dinámico propio |

En el Entregable 1 esta historia quedó sin sprint, dentro de la holgura del riesgo R1. Se construye ahora porque E1 a E6 ya están terminadas.

**Lo que E1 ya dejó listo:**
- El atributo `activo` de `Usuario`, del que depende `is_active`. Django rechaza el inicio de sesión de una cuenta inactiva y la saca de la sesión abierta.
- El comando `promover_administrador` (RF-03).
- Un panel de administración provisional, que esta épica reemplaza.

**RNF que no aplican:**
- RNF-01, RNF-02 y RNF-10: son del catálogo y del chat.
- RNF-07: requiere el entorno desplegado.

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E7 |
|---|---|---|
| **Módulo Administración** ("desactivación de productos y cuentas que incumplen las reglas") | `apps/administracion/servicios.py` | `desactivar_producto`, `desactivar_cuenta` y `reactivar_cuenta`. Cada una verifica que quien actúa sea administrador (RN-19), además de la vista (D4, defensa en profundidad). Incluye los avisos para el dueño (`avisos_de`, `avisos_pendientes`, `marcar_avisos_vistos`) y las búsquedas del administrador |
| Capa de acceso a datos | `Desactivacion` y `MotivoDesactivacion` (CC-11) | Registro de cada desactivación. La base de datos exige que sea de un producto o de una cuenta, nunca de ambos, y con un motivo válido |
| Clase `Producto` (E2) y contrato con el Catálogo (E3) | `visibles_en_catalogo()` y `es_visible_en_catalogo` | RN-09 + RN-19: también se ocultan los productos de una cuenta desactivada (CC-12) |
| Clase `Usuario` (E1) | `activo` y el código aleatorio `codigo` | Pierde el acceso. Ninguna URL lleva el id secuencial de una cuenta |
| Módulo Contacto (E4) | `enviar_mensaje()` | No se escribe a una cuenta desactivada (CC-12) |
| Capa de presentación | `views.py`, `templates/administracion/`, aviso en `base.html` | Panel con historial, productos, cuentas, formularios de desactivación y avisos del dueño |

### 2.1 Modelo de dominio → código

| Elemento | Código | Nota |
|---|---|---|
| `Rol.ADMINISTRADOR` | Ya existía (E1) | Se asigna con `python manage.py promover_administrador <correo>` (RF-03) |
| `Usuario.activo` | Ya existía (E1) | `desactivar_cuenta` lo pone en falso y `reactivar_cuenta` lo devuelve a verdadero |
| `EstadoProducto.DESACTIVADO` (ES1) | `perfil_productos.servicios.desactivar_producto()` | Es la misma transición que usa el emprendedor y sigue siendo definitiva |
| **Nuevo (CC-11):** `Desactivacion(administrador, producto \| cuenta, motivo, detalle, fecha, vista_en, reactivada_en)` | `apps/administracion/models.py` | Es a la vez la notificación al dueño (`vista_en`) y la trazabilidad de la decisión |
| **Nuevo (CC-11):** `MotivoDesactivacion` | Seis motivos | Contenido ofensivo o discriminatorio; producto no permitido en la universidad; información engañosa o fraudulenta; expone datos personales de otras personas; suplantación de identidad; otro incumplimiento |
| `Usuario.codigo` (CC-12) | UUID aleatorio | Migración en tres pasos para que las cuentas existentes reciban códigos distintos |

### 2.2 Caso de uso CU-22 implementado

| Paso del caso de uso | Código |
|---|---|
| Precondición: "quien actúa es administrador" | `rol_requerido(Rol.ADMINISTRADOR)` en todas las vistas de moderación y `_exigir_administrador()` en los servicios |
| 1: desactivar el producto que incumple las reglas | En **Administración → Productos** (búsqueda por producto o emprendimiento) o con el botón "Desactivar por incumplir las reglas" del detalle del producto. Se elige el motivo (obligatorio) y un detalle opcional de hasta 300 caracteres |
| 2: "deja de mostrarse y se notifica a su dueño" | ES1 → *Desactivado*: sale del listado, y su enlace directo muestra "Este producto ya no está disponible" (HU-09). El dueño ve un aviso en todas las páginas hasta abrir **Avisos de la administración**, donde aparecen el motivo, el detalle y la fecha. En su panel, el producto aparece como "Desactivado por la administración" |
| 1 (cuenta): desactivar la cuenta | En **Administración → Cuentas** (búsqueda por correo). La persona pierde el acceso: no puede iniciar sesión y su sesión abierta termina en la siguiente petición (CU-02 2b) |
| 1a: sin permisos de administrador → acceso denegado | 403 para comprador y emprendedor, tanto en GET como en POST, sin cambiar nada. Sin sesión, se pide iniciar sesión |

### 2.3 Rutas

| Ruta | Método | Para |
|---|---|---|
| `/administracion/` | GET | Panel: cifras e historial de desactivaciones |
| `/administracion/productos/?q=` | GET | Productos que hoy están en el catálogo (20 por página) |
| `/administracion/productos/<código>/desactivar/` | GET, POST | HU-22 Esc. 1 |
| `/administracion/cuentas/?q=` | GET | Cuentas, con su rol y estado |
| `/administracion/cuentas/<código>/desactivar/` | GET, POST | HU-22 Esc. 2 |
| `/administracion/cuentas/<código>/reactivar/` | POST | Corregir un error (CC-12) |
| `/administracion/avisos/` | GET | El emprendedor ve los avisos de sus productos (CC-11) |

En el menú aparece **Administración** solo para el administrador, y "Mi cuenta" enlaza al panel. Para el resto de las personas, las rutas de moderación responden 403.

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-24 | Desactivar cuentas o contenido inapropiado (administrador) | Desactivación de productos (ES1) y de cuentas, con motivo obligatorio, aviso al dueño del producto e historial. Es exclusiva del administrador | CP-22.1 a CP-22.9 |
| RF-03 (complemento) | El rol de administrador se asigna internamente | Comando `promover_administrador` (E1). El registro sigue sin ofrecer ese rol | Pruebas de E1 |

### 3.2 Requerimientos no funcionales y decisiones

| RNF o decisión | Prioridad | Cómo se cumple en E7 | Prueba |
|---|---|---|---|
| **D4**: negar el acceso a quien no es administrador | Must | Las rutas de moderación responden 403 a comprador y emprendedor (GET y POST). Los servicios repiten la verificación | CP-22.3 |
| **RNF-05 Privacidad** (RN-14) | Must | El administrador **no** ve mensajes, inventario ni finanzas de nadie (403). Cada emprendedor ve solo sus avisos. Las páginas de administración llevan `no-store`. Ninguna URL lleva el id de una cuenta | CP-RNF05 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad 1.6, con la sección "La administración": qué ve el administrador, qué no ve y cómo se informa una desactivación. La lista de cuentas muestra solo correo, rol y estado; el registro guarda solo lo necesario | CP-RNF06 |
| D6: correo solo para recuperar la contraseña | — | El aviso al dueño es interno a la plataforma (CC-11) | CP-22.1 |
| RNF-03 Compatibilidad | Must | Panel, listas, formularios (con y sin errores), avisos y conversación verificados a 360, 768 y 1280 px. 102 vistas sin problemas | CP-RNF03 |
| RNF-11 Accesibilidad | Could | Los motivos están en un `fieldset` con etiquetas y tienen un área táctil de al menos 24 px. El aviso usa `role="status"` y texto, no solo color. "Desactivar" y "Reactivar" incluyen texto oculto con el nombre o correo afectado | CP-RNF11 |

---

## 4. Identidad visual aplicada

| Componente | Aplicación |
|---|---|
| Insignia del rol "Administrador" | Naranja con texto negro, igual que los demás roles |
| Aviso al dueño | Borde naranja, ícono "!" y texto negro (8.9:1), el mismo patrón de alerta de E1 a E6. El enlace "Ver el motivo" va en negrita negra |
| Advertencia antes de desactivar | Recuadro con borde naranja y "!" que explica qué pasará (definitivo para productos; reactivable para cuentas) |
| Motivos | Opciones de bloque con borde gris; la elegida queda con borde azul |
| Historial | Franja izquierda azul; un aviso nuevo para el dueño lleva franja naranja y la etiqueta "Nuevo" |
| Cuenta desactivada | Borde punteado y etiqueta "Desactivada" con texto negro |

**Capturas** (con `cargar_demo`):

| Vista | Archivo |
|---|---|
| Aviso al dueño en todas las páginas (360 px) | [e7-aviso-dueno-360.png](capturas/e7-aviso-dueno-360.png) |
| Avisos de la administración (360 px) | [e7-avisos-360.png](capturas/e7-avisos-360.png) |
| Panel del emprendedor con el producto desactivado por la administración | [e7-panel-emprendedor-360.png](capturas/e7-panel-emprendedor-360.png) |
| Panel del administrador con el historial | [e7-panel-admin-1280.png](capturas/e7-panel-admin-1280.png) |
| Productos del catálogo para moderar (360 px) | [e7-productos-360.png](capturas/e7-productos-360.png) |
| Desactivar un producto sin motivo (error) | [e7-desactivar-producto-errores-360.png](capturas/e7-desactivar-producto-errores-360.png) |
| Desactivar una cuenta | [e7-desactivar-cuenta-1280.png](capturas/e7-desactivar-cuenta-1280.png) |
| Cuenta desactivada en la lista | [e7-cuenta-desactivada-1280.png](capturas/e7-cuenta-desactivada-1280.png) |
| Cuenta reactivada | [e7-cuenta-reactivada-1280.png](capturas/e7-cuenta-reactivada-1280.png) |
| Conversación con una cuenta desactivada (360 px) | [e7-conversacion-cuenta-desactivada-360.png](capturas/e7-conversacion-cuenta-desactivada-360.png) |

---

## 5. Cambios sobre las épicas anteriores

| Épica | Cambio | Motivo | Pruebas afectadas |
|---|---|---|---|
| E1 | El panel provisional `cuentas:panel_administracion` se reemplaza por `administracion:panel`. "Mi cuenta" enlaza al nuevo panel y el menú muestra **Administración** al administrador | E7 implementa la moderación | `test_roles.py` apunta a la nueva ruta y su criterio no cambia: solo el administrador entra |
| E1 | `Usuario` recibe `codigo` (UUID aleatorio, migración `0002`) | CC-12: E1 prohíbe ids de usuario en las URL | La lista de campos de `test_rnf_legal.py` incluye `codigo` (identificador técnico, no dato personal) |
| E2/E3 | `visibles_en_catalogo()` y `es_visible_en_catalogo` también ocultan los productos de cuentas desactivadas. "Este producto ya no está disponible" dice "Se retiró del catálogo" en lugar de "El emprendedor lo retiró" | RN-19 (CC-12); el texto anterior era falso cuando lo retira el administrador | Ninguna. La prueba de consultas constantes del panel (RNF-09) detectó una consulta extra, que se corrigió precargando al propietario |
| E2 | El panel del emprendedor marca los productos "Desactivado por la administración", con enlace al motivo | CC-11 | 1 prueba nueva |
| E4 | No se envían mensajes a una cuenta desactivada; la conversación lo explica y conserva el historial | CC-12 | 1 prueba nueva |
| E6 | Las fechas de "Eliminar" y de los movimientos se escriben en minúscula ("7 de noviembre") | Coherencia con E1 | Ninguna |
| Todas | Aviso de privacidad 1.6 | Ley 1581 | La prueba de E6 que fijaba "1.5" ahora lee la versión vigente |
| E3 | `cargar_demo` crea `demo.administrador@amigo.edu.co` y una desactivación de ejemplo con aviso pendiente para `demo.emprendedor02` | Probar E7 con contenido (riesgo R4) | 1 prueba nueva |

---

## 6. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E7-01 | **CC-11:** el dueño recibe un aviso dentro de la plataforma, que no desaparece hasta que lo abre | Resuelve el punto B.2 ("canal por el que se notifica"). D6 limita el correo a la recuperación de contraseña |
| DT-E7-02 | El motivo es obligatorio y sale de una lista cerrada de seis; el detalle es opcional (300 caracteres) | El Entregable 1 habla de "incumplir las reglas": el dueño debe saber cuál. La lista permite revisar decisiones comparables |
| DT-E7-03 | No se desactiva la propia cuenta ni la de otro administrador desde la plataforma | Evita dejar la plataforma sin administración. El rol se gestiona internamente (RF-03) |
| DT-E7-04 | **CC-12:** una cuenta desactivada por error se puede reactivar; un producto desactivado sigue siendo definitivo | ES1 define *Desactivado* como estado final del producto. Para las cuentas no hay diagrama, y sin esta opción un error del administrador solo se corregiría por consola |
| DT-E7-05 | Al desactivar una cuenta, sus productos se ocultan sin cambiar de estado | Si se reactiva la cuenta, vuelven tal como estaban. Un comprador no contacta a quien no puede responder |
| DT-E7-06 | El administrador no ve mensajes, inventario ni finanzas | RN-14 ("cada usuario accede solo a sus propios datos, incluidos los financieros") y minimización de datos (RNF-06). Para moderar le basta lo público: el catálogo y, de las cuentas, el correo, el rol y el estado |
| DT-E7-07 | Se mantiene el mensaje genérico de E1 al intentar entrar con una cuenta desactivada | Es una decisión aprobada en E1 y la historia no pide otra cosa. Dejo la alternativa como propuesta **CC-13** (sección 6.1) |
| DT-E7-08 | Cada desactivación guarda quién la hizo y cuándo | Trazabilidad: la decisión se puede revisar si el dueño reclama |

### 6.1 Pendientes de decisión (fuera del código)

1. **CC-13 (propuesta):** a quien escribe la contraseña correcta de una cuenta desactivada, decirle "Tu cuenta fue desactivada por la administración. Si crees que es un error, escribe a …".
   - **Ventaja:** la persona no cree que olvidó su contraseña.
   - **Riesgo:** casi nulo, porque solo lo ve quien conoce la contraseña.
   - Requiere cambiar `IngresoForm` y el *backend* de autenticación de E1. Falta tu decisión.
2. **CC-01 (propuesta desde E1):** verificar que quien se registra es dueño del correo institucional.
3. **Correo de contacto:** `CORREO_CONTACTO_PRIVACIDAD` sigue como `privacidad@por-definir.amigo.edu.co`. Se debe definir antes del despliegue (aparece en el aviso de privacidad y en los avisos de la administración).
4. **Despliegue en un entorno de pruebas** (RNF-07) y protocolo de RNF-02 con personas.

### 6.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E7-administracion` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí. Son 390 pruebas: 90 de E1, 78 de E2, 58 de E3, 50 de E4, 43 de E5, 36 de E6 y 35 de E7 |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en las épicas anteriores |

---

## 7. Batería de pruebas de validación

### 7.1 Cómo ejecutarla

```bash
git pull
pip install -r requirements.txt
python manage.py migrate                 # código de cuenta y tabla de desactivaciones
python manage.py test -v 2
python manage.py cargar_demo --limpiar   # incluye la cuenta de administración
python manage.py runserver
```

Cuentas de demostración (contraseña `Clave-Segura-2026`):

| Cuenta | Para qué sirve |
|---|---|
| `demo.administrador@amigo.edu.co` | Administrador |
| `demo.emprendedor02@amigo.edu.co` | Tiene un producto desactivado y un aviso pendiente |
| `demo.comprador@amigo.edu.co` | Comprador con conversaciones |

### 7.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 390 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Casos manuales | Tabla 7.3 | Todos cumplen su criterio |

- **APROBADA:** pasan G1 a G4.
- **APROBADA CON AJUSTES:** solo falla un caso de CP-22.4 a CP-22.9 o CP-RNF11, o se pide cambiar alguna decisión de la sección 6 (por ejemplo, los motivos o la reactivación).
- **NO APROBADA:** falla G1, G2 o G3, o cualquier caso de CP-22.1, CP-22.2, CP-22.3, RNF-05, RNF-06 o RNF-03.

### 7.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-22.1 a CP-22.3 son los del Anexo A del Entregable 2; los demás completan la cobertura.

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-22.1 | Producto desactivado (Esc. 1) | A+M | Con el administrador: Administración → Revisar productos → buscar un producto → "Desactivar" → elegir motivo y detalle → "Desactivar producto". Cerrar sesión y buscarlo en el catálogo y por su enlace. Entrar con su dueño | "«…» quedó desactivado: ya no aparece en el catálogo y se le notificó a su dueño." No aparece en el catálogo; el enlace dice "Este producto ya no está disponible". El dueño ve "La administración desactivó 1 de tus productos… Ver el motivo", y en Avisos aparecen el motivo, el detalle y la fecha. Al abrirlos, el aviso desaparece | **Aprueba** si deja de mostrarse **y** el dueño es notificado. **No aprueba** si sigue visible o el dueño no recibe el aviso |
| CP-22.2 | Cuenta desactivada (Esc. 2) | A+M | Abrir sesión con `demo.comprador` en otra ventana. Con el administrador, desactivar esa cuenta. En la otra ventana, recargar "Mi cuenta" e intentar entrar de nuevo | "La cuenta … quedó desactivada…". La sesión abierta pasa a "Ingresar". El nuevo intento muestra "Correo o contraseña incorrectos…" | **Aprueba** si el usuario pierde el acceso, incluida la sesión abierta |
| CP-22.3 | Sin permisos de administrador (Esc. 3) | A+M | Con `demo.comprador` y con `demo.emprendedor01`, abrir `/administracion/`, `/administracion/cuentas/` y la URL de "Desactivar" copiada por el administrador | 403 "No tienes permiso para ver esta página"; nada cambia | **Aprueba** si se deniega el acceso a ambos |
| CP-22.4 | Motivo obligatorio | A+M | Enviar "Desactivar producto" sin elegir motivo, y con un detalle de más de 300 caracteres | "Elige el motivo de la desactivación." y "El detalle admite hasta 300 caracteres." El producto sigue en el catálogo | **Aprueba** si no se desactiva |
| CP-22.5 | Productos de una cuenta desactivada | A+M | Desactivar la cuenta de un emprendedor con productos y buscarlos en el catálogo | No aparecen; su enlace muestra "no está disponible" | **Aprueba** si se ocultan |
| CP-22.6 | Reactivar una cuenta | A+M | En Cuentas, pulsar "Reactivar" en la cuenta desactivada; entrar con ella | "La cuenta … volvió a estar activa." Puede iniciar sesión y sus productos vuelven al catálogo | **Aprueba** si recupera el acceso |
| CP-22.7 | Cuenta propia u otro administrador | A+M | En Cuentas, ver la fila del administrador (dice "Cuenta de administración" y no tiene botón). Abrir a mano la URL de desactivar de otro administrador | "…no se puede desactivar desde aquí." La cuenta sigue activa | **Aprueba** si no se desactiva |
| CP-22.8 | Chat con una cuenta desactivada | A+M | Desactivar `demo.emprendedor03` y abrir, con `demo.comprador`, su conversación con "Dulce Campus" | "Esta cuenta fue desactivada por la administración…"; no hay campo para escribir; el historial se ve | **Aprueba** si no se puede enviar |
| CP-22.9 | Desde el detalle e historial | A+M | Con el administrador, abrir el detalle de un producto del catálogo; después ver el panel | Botón "Desactivar por incumplir las reglas" (un comprador no lo ve). El historial muestra qué se desactivó, el motivo, la fecha y quién lo hizo | **Aprueba** si se cumple |
| CP-RNF05 | Privacidad (Must) | A+M | Con el administrador, abrir `/finanzas/`, `/inventario/`, una conversación ajena y `/administracion/avisos/`. Con `demo.emprendedor01`, abrir `/administracion/avisos/` | 403 para el administrador en los cuatro. emprendedor01 ve "No tienes avisos de la administración" (no ve los de emprendedor02) | **Aprueba** si nadie ve datos privados ajenos |
| CP-RNF06 | Ley 1581 (Must) | A+M | Abrir `/privacidad/` | Versión 1.6 con la sección "La administración": qué ve, "no puede ver tus mensajes, tu inventario ni tus finanzas" y "te lo informamos en la plataforma con el motivo" | **Aprueba** si está |
| CP-RNF03 | Responsive (Must) | A+M | Panel, productos, cuentas, desactivar (con y sin errores) y avisos a 360 px en Chrome, Edge, Firefox y Safari (opcional: `ADMIN_CORREO=… node scripts/verificar_interfaz.mjs`) | Sin desplazamiento horizontal; motivos y botones de al menos 24 px | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF11 | Accesibilidad (Could) | A+M | Desactivar un producto solo con el teclado (Tab y flechas en los motivos). Escuchar el aviso del dueño con un lector de pantalla | Foco visible. El aviso se anuncia como estado con su texto completo | **Aprueba** si se completa sin mouse y se entiende sin ver |

### 7.4 Trazabilidad de las pruebas automáticas

| Archivo (`apps/administracion/tests/`) | Pruebas | Casos que cubre |
|---|---|---|
| `test_servicios.py` | 13 | RN-19 en la capa de lógica (solo el administrador; ES1 desde *Agotado*; no repetir; cuenta propia y otro administrador; reactivar; productos ocultos sin cambiar de estado; avisos vistos y solo del dueño) |
| `test_hu22.py` | 12 | CP-22.1 a CP-22.9 por la interfaz |
| `test_rnf.py` | 10 | CP-RNF05, CP-RNF06 (aviso 1.6 y datos mínimos), historial, CP-RNF03, CP-RNF11 y el enlace "Administración" solo para el administrador |
| **Total E7** | **35** | Más 1 prueba nueva de `cargar_demo` en E3. Suite completa: 390 |

Antes de entregar, la suite se probó contra doce defectos introducidos a propósito. **Los doce se detectaron**, y al revertir los cambios la suite volvió a pasar completa:

| Defecto introducido | Pruebas que fallaron |
|---|---|
| M1 · el servicio no exige administrador (RN-19) | 1 |
| M2 · vistas de administración abiertas a cualquier sesión (CP-22.3) | 2 |
| M3 · el catálogo muestra productos de cuentas desactivadas | 2 |
| M4 · el detalle muestra productos de cuentas desactivadas | 2 |
| M5 · una cuenta desactivada conserva la sesión (CP-22.2) | 3 (incluidas 2 de E1) |
| M6 · el aviso nunca queda pendiente (Esc. 1) | 4 |
| M7 · avisos de todos los dueños (RN-14) | 2 |
| M8 · se puede desactivar a otro administrador | 1 |
| M9 · se puede escribir a una cuenta desactivada | 1 |
| M10 · el motivo es opcional | 1 |
| M11 · ver los avisos no los marca como vistos | 1 |
| M12 · reactivar sin exigir administrador | 1 |
