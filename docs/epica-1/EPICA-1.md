# Épica 1 · Cuentas y acceso

**Proyecto:** Plataforma de Emprendedores (MVP) · Universidad Católica Luis Amigó
**Fuentes:** Entregable 1 (épicas, RF, RNF, HU y criterios Given-When-Then), Entregable 2 (casos de uso CU-01 a CU-03, diagramas A1, S1 y S2, modelo de dominio, reglas RN-01 a RN-04, arquitectura y plan de pruebas) y *Manual de Identidad Visual* versión 02.
**Estado:** entregada para revisión. No se ha iniciado la Épica 2.

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Transversal: lo usan los tres actores |
| Qué cubre | Registro, inicio de sesión y roles |
| Historias | HU-01 Registrarme eligiendo mi rol (Must, 2 h) · HU-02 Iniciar y cerrar sesión (Must, 1 h) · HU-03 Recuperar mi contraseña (Should, 1 h) |
| Casos de uso | CU-01, CU-02 y CU-03 (actores Comprador, Emprendedor y Usuario abstracto) |
| RF | RF-01 (Must), RF-02 (Must), RF-03 (Must), RF-04 (Should) |
| RNF de la épica | RNF-06 (asociado a HU-01) y los transversales que aplican a cuentas: RNF-03, RNF-04, RNF-05, RNF-08, RNF-09 (Should) y RNF-11 (Could) |
| Reglas de negocio | RN-01, RN-02, RN-03, RN-04 y RN-19 (acceso de cuentas desactivadas, preparado para E7) |
| Diagramas que implementa | A1 (actividades), S1 (secuencia del registro), S2 (secuencia de inicio y cierre de sesión), clase `Usuario` y enumeración `Rol` |

**RNF que no aplican a esta épica** (se verifican cuando exista su funcionalidad): RNF-01 (catálogo, E3), RNF-02 (catálogo y chat, E3 y E4), RNF-07 (disponibilidad del entorno desplegado, Sprint 4) y RNF-10 (mensajes, E4).

HU-03 es *Should* y en el Entregable 1 quedó "sin sprint (holgura)". Se incluye porque pertenece a la Épica 1 y Django ya trae el mecanismo de enlace firmado, de modo que su costo fue bajo. Si el equipo prefiere mantenerla fuera del núcleo, basta con quitar sus cuatro rutas en `apps/cuentas/urls.py`.

---

## 2. Desglose por componentes clave

Los componentes son los de la arquitectura de alto nivel (Entregable 2, figura 9 y tabla 2.2.2). Cada uno se corresponde con archivos concretos.

| Componente (Entregable 2) | Implementación | Responsabilidad en E1 |
|---|---|---|
| Navegador web | Plantillas responsive desde 360 px | Interfaz para los tres actores (RNF-03) |
| Capa de presentación | `apps/cuentas/forms.py`, `views.py`, `templates/` | Formularios de registro, ingreso y recuperación; mensajes de error de cada escenario |
| **Módulo Cuentas y acceso** | `apps/cuentas/reglas.py`, `servicios.py`, `decorators.py`, `middleware.py` | Reglas RN-01 a RN-03, caso de uso de registro, control de acceso por rol, páginas privadas sin caché |
| Capa de acceso a datos | `apps/cuentas/models.py` (ORM de Django) | Clase `Usuario` y enumeración `Rol` del modelo de dominio |
| Base de datos | SQLite (desarrollo) con restricciones `CHECK` y `UNIQUE` | Cuentas, sesiones y evidencia del consentimiento |
| Servicio de correo | `EMAIL_BACKEND` (consola en desarrollo, SMTP en producción) | Enlace de recuperación de contraseña (D6) |
| Repositorio Git y entorno de pruebas | `README.md`, `config/settings/prod.py`, historial de commits | RNF-08 y despliegue desde `main` (D8) |

### 2.1 Clase `Usuario` (modelo de dominio → código)

| Atributo del diagrama | Campo en el código | Nota |
|---|---|---|
| `correoInstitucional : String` | `correo_institucional` | Único sin distinguir mayúsculas; se guarda en minúsculas |
| `contrasenaCifrada : String` | `password` | Hash Argon2id con sal por usuario (nombre que exige Django) |
| `rol : Rol` | `rol` | `COMPRADOR`, `EMPRENDEDOR` o `ADMINISTRADOR` (restricción `CHECK`) |
| `avisoPrivacidadAceptado : Boolean` | `aviso_privacidad_aceptado` | La base de datos impide guardarlo en falso (restricción `CHECK`) |
| `activo : Boolean` | `activo` | Si es falso, la cuenta no entra y la sesión abierta se corta |
| — | `aviso_privacidad_version`, `aviso_privacidad_fecha` | Prueba de la autorización (supuesto S-E1-3) |
| — | `last_login` | Dato técnico de Django; invalida enlaces de recuperación ya usados |

Operaciones del diagrama: `registrarse()` → `servicios.registrar_usuario`; `iniciarSesion()` / `cerrarSesion()` → `IngresoView` / `SalidaView`; `recuperarContrasena()` → `RecuperarView` y `RestablecerView`; `desactivar()` → campo `activo` (lo usará E7).

### 2.2 Flujo implementado (diagramas A1, S1 y S2)

1. **Registro (A1, S1):** la persona completa correo, rol, contraseña y decide sobre el aviso. El sistema valida correo institucional (RN-01), correo repetido (RN-01), aviso aceptado (RN-02) y rol autorregistrable (RN-03). Muestra todos los errores a la vez, lo que cumple cualquier orden de validación (supuesto S-8 del Entregable 2). Si todo es válido crea la cuenta y envía a la persona a **Iniciar sesión**, como indica A1.
2. **Inicio de sesión (S2):** valida credenciales y que la cuenta esté activa. Ante cualquier fallo muestra el mismo mensaje. Al entrar, renueva el identificador de sesión.
3. **Cierre de sesión (S2):** termina la sesión y las páginas privadas redirigen a Iniciar sesión.
4. **Recuperación (CU-03):** siempre responde con el mismo mensaje neutro; solo las cuentas activas registradas reciben el enlace, que vence en 1 hora y sirve una sola vez.

### 2.3 Rutas

| Ruta | Acceso | HU / RF |
|---|---|---|
| `/cuentas/registro/` | Público | HU-01 · RF-01, RF-03 |
| `/cuentas/ingresar/` | Público | HU-02 · RF-02 |
| `/cuentas/salir/` | Con sesión, solo POST | HU-02 · RF-02 |
| `/cuentas/mi-cuenta/` | Con sesión | HU-02 · RNF-05 |
| `/cuentas/panel/emprendedor/` | Rol Emprendedor | RF-03 (punto de entrada de E2) |
| `/cuentas/panel/administracion/` | Rol Administrador | RF-03 (punto de entrada de E7) |
| `/cuentas/recuperar/` y `/cuentas/recuperar/enviado/` | Público | HU-03 · RF-04 |
| `/cuentas/restablecer/<uid>/<token>/` y `/cuentas/restablecer/completo/` | Enlace firmado | HU-03 · RF-04 |
| `/privacidad/` | Público | RNF-06 |

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-01 | Registrar usuarios con correo institucional y aceptación del aviso de privacidad | `RegistroForm` + `servicios.registrar_usuario`; dominio configurable en `DOMINIOS_INSTITUCIONALES`; casilla obligatoria y restricción en base de datos | CP-01.1 a CP-01.4 |
| RF-02 | Iniciar y cerrar sesión | `IngresoView` (mensaje único, renovación de sesión) y `SalidaView` (solo POST con CSRF) | CP-02.1 a CP-02.4 |
| RF-03 | Asignar el rol al registrarse; el de administrador se asigna internamente | El formulario solo ofrece Comprador y Emprendedor y rechaza valores manipulados; `promover_administrador` asigna el rol de administrador; `rol_requerido()` protege las pantallas por rol | CP-01.5, CP-ROL.1, CP-ROL.2 |
| RF-04 | Recuperar la contraseña mediante un enlace enviado al correo | `RecuperarView` con mensaje neutro; enlace firmado de un solo uso que vence en 1 hora | CP-03.1 a CP-03.3 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E1 | Prueba |
|---|---|---|---|
| RNF-03 Compatibilidad | Must | Diseño móvil primero, `meta viewport`, sin anchos fijos; verificado a 360, 768 y 1280 px sin desplazamiento horizontal | CP-RNF03 |
| RNF-04 Seguridad | Must | Argon2id con sal; en producción: redirección a HTTPS, HSTS de 1 año, cookies `Secure` y `HttpOnly`, `SameSite=Lax`, CSRF en todos los formularios y `X-Frame-Options: DENY`; `check --deploy` sin observaciones | CP-RNF04.1 a CP-RNF04.3 |
| RNF-05 Privacidad | Must | El usuario se identifica por la sesión, nunca por un identificador en la URL; las páginas vistas con sesión se envían con `Cache-Control: no-store, private`; las pantallas de otro rol responden 403 | CP-RNF05, CP-ROL.1 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad según la Ley 1581 de 2012 (responsable, datos, finalidad, derechos, canal y plazos); casilla sin marcar por defecto; se guardan la versión y la fecha de aceptación; solo se piden correo, contraseña y rol. Una prueba falla si alguien agrega un dato personal no previsto en la matriz (riesgo R5) | CP-RNF06 |
| RNF-08 Mantenibilidad | Must | Repositorio Git con commits que nombran la historia, README con descripción, ejecución y contribución, módulo separado por épica | CP-RNF08 |
| RNF-09 Escalabilidad | Should | Registro e ingreso funcionan con 100 usuarios registrados (los 300 productos se prueban en E2) | CP-RNF09 |
| RNF-11 Accesibilidad | Could | Contrastes medidos ≥ 4.5:1 en texto y ≥ 3:1 en bordes; texto alternativo en el logotipo; cada campo con etiqueta; errores enlazados con `aria-describedby` y `aria-invalid`; foco visible; enlace "Saltar al contenido"; controles de 24 px o más | CP-RNF11 |

---

## 4. Identidad visual aplicada

| Lineamiento del manual | Página | Aplicación |
|---|---|---|
| Colores digitales: azul `#007b99`, naranja `#f39200`, gris `#848585` | 07 | Únicos valores de color, definidos solo en `static/css/marca.css`; una prueba rechaza cualquier otro color en CSS o plantillas |
| Blanco como fondo principal | 06 | Fondo de todas las páginas |
| Aplicación principal del logotipo, sin deformar, girar, pixelar ni cambiar colores | 12, 23 a 25 | SVG vectorial extraído del propio manual (sin rasterizar), con proporción original |
| Tamaño mínimo de 5 cm | 10 | Ancho mínimo de 190 px, verificado en los tres anchos de pantalla |
| Área de reserva | 08 | Espacio libre alrededor del logotipo; el nombre de la plataforma va separado por un filete |
| Ubicación en la parte superior | 26 | Esquina superior izquierda |
| Elemento gráfico (tilde y "O"), de uso libre para el diseñador | 05, 22 | Bloque diagonal naranja y arco naranja en los paneles azules; ícono de la pestaña |
| Títulos con línea y punto final | Todas | Clase `.titulo-linea` |
| Tipografías Ingra Cd Book y Azo Sans Medium | 11 | Primeras en la pila de fuentes; si la licencia no está instalada se usan fuentes del sistema (supuesto S-E1-6) |

**Capturas** (Chromium, generadas con `scripts/verificar_interfaz.mjs`):

| Vista | Archivo |
|---|---|
| Inicio a 1280 px y a 360 px | [inicio-1280.png](capturas/inicio-1280.png) · [inicio-360.png](capturas/inicio-360.png) |
| Registro a 1280 px | [registro-1280.png](capturas/registro-1280.png) |
| Registro con errores a 360 px (HU-01, escenarios 3 y 4) | [registro-errores-360.png](capturas/registro-errores-360.png) |
| Iniciar sesión a 1280 px | [ingresar-1280.png](capturas/ingresar-1280.png) |
| Mi cuenta a 360 px | [mi-cuenta-360.png](capturas/mi-cuenta-360.png) |
| Acceso denegado por rol (403) | [403-1280.png](capturas/403-1280.png) |

**Accesibilidad y paleta.** El naranja sobre blanco tiene contraste 2.35:1 y el gris 3.7:1, por debajo de 4.5:1. Por eso nunca se usan como color de texto: el naranja queda como acento y el gris como color de bordes (cumple 3:1). Los errores se señalan con un marcador naranja, un ícono "!" y texto en negro, de modo que no dependen solo del color (WCAG 1.4.1).

---

## 5. Decisiones técnicas y supuestos

El Entregable 2 dejó la tecnología para el Sprint 1 (S-9). Estas son las decisiones tomadas; ninguna cambia el alcance, las prioridades ni los criterios de aceptación.

| # | Decisión | Justificación |
|---|---|---|
| DT-01 | Python + **Django 5.2 LTS**, plantillas en servidor | Encaja con el monolito modular (D1) y un módulo por épica (D2). Trae autenticación, sesiones, CSRF, hash de contraseñas, enlaces de recuperación y pruebas unitarias y de integración, lo que ahorra horas frente al déficit de capacidad (R1). Tiene soporte hasta 2028 |
| DT-02 | Hash **Argon2id** | Algoritmo recomendado por OWASP; cumple RNF-04 ("contraseñas almacenadas cifradas") con un hash irreversible, más seguro que un cifrado reversible |
| DT-03 | Mensaje único en el ingreso; mensaje explícito en el registro con correo repetido | El ingreso no revela si una cuenta existe. El registro sí informa que el correo existe porque así lo exige HU-01, Escenario 2 |
| DT-04 | Tras registrarse, la persona inicia sesión manualmente | Sigue el diagrama A1 (crear cuenta → ingresar correo y contraseña) |
| DT-05 | Cerrar sesión solo con POST | Impide que un enlace externo cierre la sesión de alguien |
| DT-06 | Rol de administrador con el comando `promover_administrador` | RF-03: se asigna internamente y sobre una cuenta que ya aceptó el aviso |
| DT-07 | `rol_requerido()` y middleware sin caché | Las épicas 2 a 7 los reutilizan sin repetir controles de acceso |
| DT-08 | SQLite en desarrollo y pruebas | Cero configuración para el equipo; cambiar a PostgreSQL al desplegar es un ajuste de `DATABASES` en `prod.py` (se decide en el Sprint 4) |

| # | Supuesto (el Entregable 1 no lo define) | Decisión |
|---|---|---|
| S-E1-1 | Dominio del correo institucional | `@amigo.edu.co`, tomado del correo de contacto del manual. Se configura con `DOMINIOS_INSTITUCIONALES` sin cambiar código |
| S-E1-2 | Política de contraseñas | Mínimo 8 caracteres, no común, no solo numérica y distinta del correo |
| S-E1-3 | Prueba del consentimiento | Se guardan la versión del aviso y la fecha de aceptación (Ley 1581, art. 9: la autorización debe poder consultarse después) |
| S-E1-4 | Vigencia del enlace de recuperación | 1 hora y un solo uso |
| S-E1-5 | Duración de la sesión | 12 horas |
| S-E1-6 | Tipografías corporativas | Son licenciadas; no se incluyen archivos de fuente. Si la universidad provee la licencia web, se agregan con `@font-face` sin cambiar el resto |
| S-E1-7 | Nombre del producto | "Plataforma de Emprendedores" como nombre descriptivo provisional, configurable en `NOMBRE_PLATAFORMA` |

### 5.1 Puntos que necesitan validación del equipo

1. **¿Los estudiantes usan `@amigo.edu.co` o un subdominio?** Si hay otro dominio, se agrega a `DOMINIOS_INSTITUCIONALES`.
2. **Verificación de propiedad del correo.** Ningún requerimiento pide confirmar que quien se registra es dueño del correo. Hoy alguien podría registrar el correo institucional de otra persona. Se recomienda evaluarlo como solicitud de cambio (CC-01): agregaría un RF y unas 2 h.
3. **Correo de contacto de privacidad** (`CORREO_CONTACTO_PRIVACIDAD`): hoy tiene un valor provisional.
4. **Una persona con los dos roles** (punto abierto B.2 del Entregable 2): E1 implementa un rol por cuenta, como dice RF-03.

### 5.2 Definición de Hecho

| Condición (Entregable 1) | Estado |
|---|---|
| El código está en la rama principal | Sí (`main` del repositorio local) |
| Todos los escenarios Given-When-Then pasan | Sí (88 pruebas automáticas en verde) |
| No hay errores bloqueantes | Sí |
| La función está desplegada en el entorno de pruebas | **Pendiente**: el equipo aún no tiene entorno de pruebas. La configuración de producción está lista y pasa `check --deploy` |

---

## 6. Batería de pruebas de validación

### 6.1 Cómo ejecutarla

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test apps.cuentas -v 2                # pruebas automáticas
python manage.py runserver                             # para las pruebas manuales
```

Datos de prueba para los pasos manuales: correos `@amigo.edu.co` inventados (por ejemplo `prueba1@amigo.edu.co`) y la contraseña `Clave-Segura-2026`.

### 6.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test apps.cuentas -v 2` | `Ran 88 tests` y `OK` (0 fallos, 0 errores) |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` con `DJANGO_SECRET_KEY` y `DJANGO_ALLOWED_HOSTS` (ver README) | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Casos manuales | Tabla 6.3, columna "Manual" | Todos cumplen su criterio |

**Decisión sobre la entrega:**

- **APROBADA:** G1, G2 y G3 pasan, y todos los casos de la tabla 6.3 cumplen su criterio.
- **APROBADA CON AJUSTES:** G1 a G3 pasan y solo falla algún caso *Should* o *Could* (CP-03.x, CP-RNF09, CP-RNF11). Los fallos se registran como defectos no bloqueantes y se corrigen antes de iniciar la Épica 2.
- **NO APROBADA:** falla G1, G2 o G3, o falla cualquier caso *Must*.

### 6.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual, **A+M** = ambos. Los ID CP-hh.n son los del Anexo A del Entregable 2. Los ID nuevos (CP-01.5, CP-02.4, CP-03.3, CP-ROL y CP-RNF) completan la cobertura de RF-03 y de los RNF.

#### HU-01 · Registrarme eligiendo mi rol (Must · RF-01, RF-03, RNF-06)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-01.1 | Registro exitoso | A+M | 1. Abrir `/cuentas/registro/`. 2. Correo `prueba1@amigo.edu.co`, rol **Emprendedor**, contraseña y confirmación `Clave-Segura-2026`. 3. Marcar la casilla del aviso. 4. Pulsar **Crear cuenta**. 5. Iniciar sesión con esos datos. | Redirige a **Inicia sesión** con "Tu cuenta fue creada con el rol emprendedor". Tras ingresar, **Mi cuenta** muestra el correo y el rol Emprendedor | **Aprueba** si se crea la cuenta con el rol elegido y se puede ingresar. **No aprueba** si no se crea, el rol es otro o el ingreso falla |
| CP-01.2 | Correo repetido | A+M | 1. Repetir CP-01.1 con `prueba1@amigo.edu.co`. 2. Repetir con `PRUEBA1@AMIGO.EDU.CO`. | En ambos casos: "Ya existe una cuenta con este correo…" y no se crea otra cuenta | **Aprueba** si rechaza las dos variantes. **No aprueba** si alguna crea una segunda cuenta |
| CP-01.3 | Sin consentimiento | A+M | 1. Completar el formulario con un correo nuevo sin marcar la casilla. 2. Enviar. | "Debes aceptar el aviso de privacidad para crear tu cuenta." La cuenta no existe (intentar ingresar falla) | **Aprueba** si no se crea la cuenta y se pide aceptar el aviso. **No aprueba** en otro caso |
| CP-01.4 | Correo no institucional | A+M | 1. Usar `ana@gmail.com` con el resto de datos válidos. 2. Enviar. | "Usa tu correo institucional (@amigo.edu.co)." No se crea la cuenta | **Aprueba** si rechaza y pide el correo institucional. **No aprueba** si acepta el correo |
| CP-01.5 | El rol de administrador no se puede elegir | A+M | 1. Ver que el formulario solo ofrece Comprador y Emprendedor. 2. Con las herramientas de desarrollo del navegador, cambiar el `value` de una opción a `ADMINISTRADOR` y enviar. | Solo aparecen dos opciones. El envío manipulado muestra "Elige tu rol: comprador o emprendedor." y no crea la cuenta | **Aprueba** si no existe forma de registrarse como administrador. **No aprueba** si se crea una cuenta administradora |
| CP-01.6 | Política de contraseña | A | Contraseñas `12345678`, `password` y `anaperez`; confirmación distinta | Se rechazan; "Las contraseñas no coinciden" cuando difieren | **Aprueba** si ninguna se acepta |

#### HU-02 · Iniciar y cerrar sesión (Must · RF-02)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-02.1 | Acceso correcto | A+M | 1. Abrir `/cuentas/ingresar/`. 2. Ingresar el correo de CP-01.1 (también en mayúsculas) y su contraseña. | Entra a **Mi cuenta**; el encabezado muestra la insignia del rol y **Cerrar sesión** | **Aprueba** si accede con el correo en cualquier combinación de mayúsculas. **No aprueba** si no accede |
| CP-02.2 | Credenciales incorrectas | A+M | 1. Correo correcto con contraseña `Incorrecta-2026`. 2. Correo inexistente `nadie@amigo.edu.co`. | En ambos casos el mismo mensaje: "Correo o contraseña incorrectos…" y sin acceso | **Aprueba** si no hay acceso y el mensaje es idéntico en los dos casos. **No aprueba** si accede o si el mensaje revela que el correo no existe |
| CP-02.3 | Cierre de sesión | A+M | 1. Con sesión, pulsar **Cerrar sesión**. 2. Abrir `/cuentas/mi-cuenta/`. 3. Pulsar **Atrás** en el navegador. | Mensaje "Cerraste sesión…". Mi cuenta redirige a Iniciar sesión. Atrás no muestra los datos de la cuenta | **Aprueba** si ninguna página privada queda disponible. **No aprueba** si algún dato privado se ve tras cerrar sesión |
| CP-02.4 | Cuenta desactivada (CU-02, flujo 2b) | A | Desactivar una cuenta y luego intentar ingresar; desactivarla con una sesión abierta | No ingresa (mensaje genérico) y la sesión abierta se corta | **Aprueba** si en ambos casos pierde el acceso |
| CP-02.5 | Sesión segura | A | Ingresar y comparar el identificador de sesión; ingresar con `?next=https://sitio-externo.com` | El identificador cambia al ingresar; el destino externo se ignora | **Aprueba** si se cumplen ambas condiciones |

#### HU-03 · Recuperar mi contraseña (Should · RF-04)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-03.1 | Correo registrado | A+M | 1. En Iniciar sesión, pulsar "¿Olvidaste tu contraseña?". 2. Escribir el correo de CP-01.1 y enviar. 3. Copiar el enlace que aparece en la terminal del servidor y abrirlo. 4. Definir `Nueva-Clave-Amigo-26`. 5. Ingresar con la nueva; luego intentar con la anterior. 6. Abrir el mismo enlace otra vez. | Mensaje neutro; correo con asunto "Restablece tu contraseña…"; "Contraseña actualizada"; ingresa con la nueva y no con la anterior; el enlace reutilizado muestra "El enlace no es válido o ya venció" | **Aprueba** si se cumplen todos. **No aprueba** si no llega el enlace, la contraseña no cambia o el enlace sirve dos veces |
| CP-03.2 | Correo desconocido | A+M | Solicitar la recuperación para `nadie@amigo.edu.co` | La misma página y el mismo mensaje que en CP-03.1; en la terminal no aparece ningún correo | **Aprueba** si la respuesta no permite saber si la cuenta existe. **No aprueba** si muestra un mensaje distinto |
| CP-03.3 | Vencimiento del enlace | A | Usar un enlace 1 hora y 1 minuto después de emitido | "El enlace no es válido o ya venció" | **Aprueba** si el enlace vencido no sirve |

#### RF-03 · Roles

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-ROL.1 | Acceso por rol | A+M | 1. Como comprador, abrir `/cuentas/panel/emprendedor/` y `/cuentas/panel/administracion/`. 2. Como emprendedor, abrir ambos. 3. Sin sesión, abrir ambos. | Comprador: 403 "No tienes permiso…" en ambos. Emprendedor: abre su panel y recibe 403 en administración. Sin sesión: redirige a Iniciar sesión | **Aprueba** si cada rol solo ve lo suyo. **No aprueba** si algún rol abre un panel ajeno |
| CP-ROL.2 | Asignación interna del administrador | A+M | 1. `python manage.py promover_administrador prueba1@amigo.edu.co`. 2. Ingresar con esa cuenta. 3. Probar con un correo inexistente. | "… ahora es administrador"; Mi cuenta muestra Administrador y abre el panel de administración. Con el correo inexistente el comando falla sin crear cuentas | **Aprueba** si el rol solo cambia por esta vía interna |

#### Requerimientos no funcionales

| ID | RNF | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RNF03 | RNF-03 (Must) | A+M | 1. Abrir inicio, registro (vacío y con errores), ingresar, recuperar y aviso en **Chrome, Edge, Firefox y Safari** con el modo de dispositivo a **360 px** de ancho. 2. Opcional: `node scripts/verificar_interfaz.mjs` con `chromium`, `firefox` y `webkit`. | Sin barra de desplazamiento horizontal; todo el texto legible; todos los controles se pueden usar; logotipo completo | **Aprueba** si se cumple en los 4 navegadores (y el script termina con "sin problemas"). **No aprueba** si algún navegador corta contenido o exige desplazamiento horizontal |
| CP-RNF04.1 | RNF-04 (Must) · contraseña cifrada | A+M | 1. Registrar una cuenta. 2. `python manage.py shell -c "from apps.cuentas.models import Usuario; print(Usuario.objects.last().password[:40])"` 3. Buscar la contraseña en `db.sqlite3`. | El valor empieza por `argon2$argon2id$`; la contraseña no aparece en la base de datos | **Aprueba** si solo existe el hash. **No aprueba** si la contraseña es legible en algún lugar |
| CP-RNF04.2 | RNF-04 (Must) · HTTPS | A+M | 1. Ejecutar G2. 2. Cuando exista el entorno desplegado: `curl -I http://<dominio>/` y `curl -I https://<dominio>/` | G2 sin observaciones; HTTP responde 301 hacia `https://`; HTTPS envía `Strict-Transport-Security` | **Aprueba** si G2 pasa (y, una vez desplegado, se cumple el paso 2). **No aprueba** si G2 reporta problemas |
| CP-RNF04.3 | RNF-04 (Must) · formularios y cookies | A | Enviar el registro sin token CSRF; revisar cookie de sesión y cabeceras | 403 sin token; cookie `HttpOnly`; `X-Frame-Options: DENY` | **Aprueba** si se cumplen las tres |
| CP-RNF05 | RNF-05 (Must) | A+M | 1. Ingresar con la cuenta A y abrir Mi cuenta. 2. En otra ventana privada, ingresar con B. 3. Revisar en las herramientas de desarrollo la cabecera `Cache-Control` de Mi cuenta. | Cada ventana muestra solo los datos de su cuenta; ninguna ruta acepta el identificador de otra persona; la cabecera incluye `no-store` y `private` | **Aprueba** si nadie ve datos de otra cuenta. **No aprueba** si hay alguna forma de verlos |
| CP-RNF06 | RNF-06 (Must) | A+M | 1. Abrir `/privacidad/` desde el registro y desde el pie de página. 2. Ver que la casilla del registro viene sin marcar. 3. Tras registrarse, revisar Mi cuenta. | El aviso incluye responsable, datos que se recolectan, finalidad, derechos (conocer, actualizar, rectificar, revocar), canal y plazos de respuesta. Mi cuenta muestra la versión y la fecha de aceptación. El registro solo pide correo, rol y contraseña | **Aprueba** si se cumplen los tres puntos. **No aprueba** si falta una sección, la casilla viene marcada o se pide un dato no previsto |
| CP-RNF08 | RNF-08 (Must) | M | 1. `git log --oneline`. 2. Abrir `README.md`. | Commits pequeños que nombran la historia (por ejemplo, "HU-01: …"); README con descripción, cómo ejecutar, cómo probar y cómo contribuir | **Aprueba** si existen ambos. **No aprueba** si falta el README o los commits no son descriptivos |
| CP-RNF09 | RNF-09 (Should) | A | Con 100 usuarios cargados, registrar uno más, ingresar y probar un correo repetido | Todo funciona igual | **Aprueba** si las tres operaciones responden correctamente |
| CP-RNF11 | RNF-11 (Could) | A+M | 1. Completar el registro usando solo el teclado (Tab, Espacio, Enter). 2. Provocar errores y escuchar o revisar el anuncio (lector de pantalla opcional). | Foco visible en cada control; los errores aparecen en un resumen con enlaces a cada campo; contrastes ≥ 4.5:1 (verificados por la suite) | **Aprueba** si el registro se completa solo con el teclado y los errores son perceptibles sin depender del color |
| CP-ID | Manual de identidad (requisito de la entrega) | A+M | Revisar encabezado, botones y paneles en 360 y 1280 px | Logotipo oficial vectorial arriba a la izquierda, sin deformar y de 190 px o más; solo azul, naranja, gris, blanco y negro; naranja y gris nunca como texto sobre blanco | **Aprueba** si se cumple y la suite no reporta colores fuera de la paleta |

### 6.4 Trazabilidad de las pruebas automáticas

| Archivo | Pruebas | Casos que cubre |
|---|---|---|
| `tests/test_reglas.py` | 16 | RN-01, RN-02, RN-03; CP-01.3 y CP-01.4 a nivel unitario; CP-01.6 |
| `tests/test_hu01_registro.py` | 13 | CP-01.1 a CP-01.5 |
| `tests/test_hu02_sesion.py` | 10 | CP-02.1 a CP-02.5 |
| `tests/test_hu03_recuperacion.py` | 6 | CP-03.1 a CP-03.3 |
| `tests/test_roles.py` | 7 | CP-ROL.1, CP-ROL.2 |
| `tests/test_rnf_seguridad.py` | 12 | CP-RNF04.1 a CP-RNF04.3 |
| `tests/test_rnf_privacidad.py` | 4 | CP-RNF05 |
| `tests/test_rnf_legal.py` | 8 | CP-RNF06 |
| `tests/test_rnf_interfaz.py` | 10 | CP-RNF03 (viewport), CP-RNF11, CP-ID |
| `tests/test_rnf_escalabilidad.py` | 2 | CP-RNF09 |
| **Total** | **88** | |

Antes de entregar, la suite se probó contra tres defectos introducidos a propósito: aceptar cualquier dominio de correo, usar un color fuera de la paleta y quitar la protección de caché junto con Argon2. Cada defecto hizo fallar entre 2 y 8 pruebas, y la suite volvió a quedar en verde al revertirlos.
