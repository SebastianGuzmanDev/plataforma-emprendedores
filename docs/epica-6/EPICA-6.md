# Épica 6 · Finanzas

**Proyecto:** Emprendi Amigos (MVP) · Universidad Católica Luis Amigó
**Fuentes:**
- **Entregable 1:** HU-19 a HU-21 y RF-21 a RF-23.
- **Entregable 2:**
  - Casos de uso CU-19 a CU-21.
  - Clases `Ingreso`, `Gasto` y `ResumenFinanciero` (derivada).
  - Reglas RN-13 a RN-15 y supuestos S-3, S-5 y S-7.
  - Decisión D4, valores límite de 4.1.4, Anexo A (CP-19.1 a CP-21.3) y punto abierto B.2.
- *Manual de Identidad Visual*, versión 02.

**Estado:** **aprobada** (07/11/2026), con CC-10.

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Emprendedor |
| Qué cubre | Ingresos y gastos, incluida la materia prima |
| Historias | HU-19 Registrar un ingreso (Should, 2 h). HU-20 Registrar un gasto (Should, 2 h). HU-21 Ver el resumen financiero de un periodo (Should, 3 h) |
| Casos de uso | CU-19, CU-20 y CU-21 (actor Emprendedor) |
| RF | RF-21, RF-22 y RF-23 (todos Should) |
| RNF de la épica | RNF-05 (Must), citado en HU-19 Esc. 3. También aplican RNF-03, RNF-06 y RNF-11 |
| Reglas de negocio | RN-13 (monto mayor a 0; el gasto lleva categoría), RN-14 (cada usuario ve solo sus datos financieros) y RN-15 (el resumen cuenta solo el mes elegido; sin movimientos, todo en 0) |
| Diagramas | El Entregable 2 no define un diagrama dinámico para HU-18 a HU-21. Quedan cubiertas por la plantilla del caso de uso, el modelo de dominio y sus casos de prueba (sección 3.1 del Entregable 2) |

En el Entregable 1 estas historias quedaron sin sprint, dentro de la holgura del riesgo R1. Se construyen ahora porque E1 a E5 ya están terminadas.

**RNF que no aplican:**
- RNF-01, RNF-02 y RNF-10: son del catálogo y del chat.
- RNF-07: requiere el entorno desplegado.

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E6 |
|---|---|---|
| **Módulo Finanzas** ("ingresos, gastos y resumen por periodo, con acceso solo al dueño de los datos") | `apps/finanzas/servicios.py` | `registrar_ingreso` (CU-19), `registrar_gasto` (CU-20) y `resumen_financiero(usuario, año, mes)` (CU-21) |
| | `apps/finanzas/reglas.py` | RN-13 (`interpretar_monto`) y RN-15 (`interpretar_periodo` y límites del mes) |
| Capa de acceso a datos | `Ingreso`, `Gasto` | Restricciones en la base de datos: monto > 0 y categoría válida. Índice por propietario y fecha |
| Capa de presentación | `views.py`, `templates/finanzas/` | Resumen del mes; formularios de ingreso y gasto; confirmación para eliminar un registro equivocado |
| Módulo Inventario (E5) | `registrar_insumo(..., registrar_como_gasto)` | CC-10: el insumo puede quedar también como gasto de *Materia prima* |

### 2.1 Modelo de dominio → código

| Elemento del modelo | Código | Nota |
|---|---|---|
| `Ingreso` (monto y fecha), asociado a `Usuario` | `Ingreso(propietario, monto, fecha)` | S-3: pertenece al usuario emprendedor, no al emprendimiento. S-5: tiene fecha para agruparse por mes |
| `Gasto` (monto, categoría y fecha) | `Gasto(propietario, monto, categoria, fecha)` | La categoría es obligatoria (RN-13). Las seis categorías vienen de CC-10 |
| `ResumenFinanciero` (derivado) | `servicios.ResumenFinanciero` (*dataclass*), sin tabla | S-7: se calcula a partir de `Ingreso` y `Gasto`. Contiene periodo, total de ingresos, total de gastos, balance, gastos por categoría y movimientos del mes |

Los dos modelos guardan además un `codigo` aleatorio (UUID) que se usa en las URL de eliminación. Así los registros no se pueden enumerar.

### 2.2 Casos de uso implementados

| Paso del caso de uso | Código |
|---|---|
| CU-19 · 1–2: registrar un ingreso con monto válido; se guarda y se suma al total | `IngresoForm` → `registrar_ingreso()` → redirige al resumen del mes del ingreso, que muestra el total actualizado |
| CU-19 · 1a: monto cero o negativo → rechazo | `interpretar_monto()`: entero mayor a 0. La base de datos también lo impide |
| CU-19 · 1b: ingresos de otro usuario → acceso denegado | Todas las consultas parten de `request.user`. Eliminar un registro ajeno responde 403 |
| CU-20 · 1–2: gasto con monto y categoría | `GastoForm` → `registrar_gasto()` |
| CU-20 · 1a: gasto sin categoría → rechazo | La categoría es obligatoria y de la lista cerrada, en el formulario y en la base de datos |
| CU-20 · postcondición "incluye los gastos de materia prima" | Categoría *Materia prima* y CC-10 desde Inventario |
| CU-21 · 1–2: abrir el resumen de un mes | `/finanzas/?mes=AAAA-MM`, con selector de mes y enlaces al mes anterior y al siguiente |
| CU-21 · 2a: periodo sin movimientos → todo en 0 | Las sumas vacías se convierten en 0. Aparece el mensaje "No registraste movimientos en este mes" |
| CU-21 · 2b: no se muestran otros meses | Filtro `fecha ≥ día 1 del mes` y `fecha < día 1 del mes siguiente` (intervalo semiabierto, sin errores en el último día) |

### 2.3 Rutas

| Ruta | Método | HU / RF |
|---|---|---|
| `/finanzas/?mes=AAAA-MM` | GET | HU-21 · RF-23. Sin `mes`, o con un valor inválido, muestra el mes actual |
| `/finanzas/ingresos/nuevo/` | GET, POST | HU-19 · RF-21 |
| `/finanzas/gastos/nuevo/` | GET, POST | HU-20 · RF-22 |
| `/finanzas/<ingreso\|gasto>/<código>/eliminar/` | GET (confirmación), POST | Corregir un registro equivocado (DT-E6-05) |

- Todas las rutas exigen el rol Emprendedor y no dependen de tener el perfil público creado (S-3).
- El panel "Mi emprendimiento" tiene el botón **Finanzas**.
- Ninguna cifra financiera aparece en el catálogo ni en páginas públicas.

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-21 | Registrar ingresos | Monto en pesos (acepta «25000», «25.000» y «$ 25.000») y fecha (hoy por defecto; se admiten días anteriores, pero no fechas futuras). El total del mes se actualiza | CP-19.1, CP-19.2 y pruebas de la fecha |
| RF-22 | Registrar gastos | Monto, categoría obligatoria de la lista cerrada y fecha | CP-20.1, CP-20.2 y CP-RN13 |
| RF-23 | Ver el resumen financiero por periodo | Ingresos, gastos y balance del mes (ganancia o pérdida), gastos por categoría y movimientos del mes. Se navega entre meses | CP-21.1 a CP-21.3 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E6 | Prueba |
|---|---|---|---|
| **RNF-05 Privacidad** (RN-14, D4) | Must | El resumen se calcula siempre con el usuario de la sesión. Otro emprendedor no ve las cifras ajenas y recibe 403 al intentar eliminar un registro ajeno. Un comprador recibe 403. Sin sesión, se pide iniciar sesión. Las respuestas llevan `Cache-Control: no-store` | CP-19.3 y CP-RNF05 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad 1.5: "Tus finanzas… Solo tú puedes ver tus finanzas". Solo se guardan los datos del modelo de dominio: no hay descripción libre que pueda contener datos de terceros | CP-RNF06 |
| RNF-03 Compatibilidad | Must | Resumen, formularios, confirmación y errores verificados a 360, 768 y 1280 px. Las tres cifras se apilan en el teléfono. Los navegadores sin selector de mes muestran un campo de texto que indica el formato `AAAA-MM` | CP-RNF03 |
| RNF-11 Accesibilidad | Could | Todos los campos tienen etiqueta y la categoría se agrupa en un `fieldset`. La pérdida se comunica con texto ("Pérdida") y el signo "−", no solo con el color. "Eliminar" incluye texto oculto que dice qué registro elimina. Las barras de categoría son decorativas: el monto y el porcentaje van escritos | CP-RNF11 |

---

## 4. Identidad visual aplicada

| Componente | Aplicación |
|---|---|
| Cifras de ingresos y gastos | Tarjetas blancas con borde gris; valor grande en azul `#007b99` con la tipografía de títulos |
| Balance con ganancia o en cero | Tarjeta azul institucional con texto blanco (4.89:1) |
| Balance con pérdida | Borde naranja `#f39200`, ícono "!" y texto negro: es el mismo patrón de alerta de E1 a E5, y no se usa rojo porque no está en la paleta |
| Gastos por categoría | Barras azules sobre una pista con borde gris |
| Movimientos del mes | Franja izquierda azul para ingresos y naranja para gastos. El tipo también va escrito ("Ingreso" o "Gasto") |
| Casilla de CC-10 | Casilla grande (24 px) con `accent-color` azul |

**Capturas** (con `cargar_demo`):

| Vista | Archivo |
|---|---|
| Resumen del mes a 360 px | [e6-finanzas-360.png](capturas/e6-finanzas-360.png) |
| Resumen del mes a 768 px | [e6-resumen-768.png](capturas/e6-resumen-768.png) |
| Mes con pérdida (balance negativo) | [e6-perdida-768.png](capturas/e6-perdida-768.png) |
| Mes sin movimientos (CP-21.2) | [e6-mes-sin-movimientos-768.png](capturas/e6-mes-sin-movimientos-768.png) |
| Registrar un ingreso | [e6-nuevo-ingreso-768.png](capturas/e6-nuevo-ingreso-768.png) |
| Gasto con monto 0 y sin categoría (CP-19.2 y CP-20.2) | [e6-gasto-errores-360.png](capturas/e6-gasto-errores-360.png) |
| Confirmación de eliminar | [e6-eliminar-360.png](capturas/e6-eliminar-360.png) |
| Insumo con la casilla de CC-10 | [e6-cc10-insumo-768.png](capturas/e6-cc10-insumo-768.png) |

---

## 5. Cambios sobre las épicas anteriores

| Épica | Cambio | Motivo | Pruebas afectadas |
|---|---|---|---|
| E5 | El formulario de insumos tiene la casilla "Registrar también este costo como un gasto de materia prima de hoy en Finanzas", marcada por defecto. El insumo y el gasto se guardan juntos en una transacción | **CC-10** (punto B.2) | 3 pruebas nuevas. Las de HU-18 no cambian, porque no envían la casilla |
| E2 | El panel "Mi emprendimiento" muestra el botón **Finanzas** aunque todavía no exista el perfil | Navegación y supuesto S-3 | 1 prueba nueva |
| Todas | Aviso de privacidad 1.5 (ingresos, gastos y resumen) | Ley 1581 | La prueba de E5 que fijaba "1.4" ahora lee la versión vigente |
| E3 | `cargar_demo` crea ingresos y gastos del mes actual y de los dos anteriores, y registra los insumos de la demo también como gasto | Probar E6 con contenido (riesgo R4) | 1 prueba nueva |

---

## 6. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E6-01 | El periodo del resumen es el **mes calendario** | HU-21 Esc. 1 y 3 hablan de "un mes" y "varios meses"; S-5 dice que HU-21 filtra por mes |
| DT-E6-02 | **CC-10 (a):** el gasto tiene seis categorías fijas: Materia prima, Empaques, Transporte, Publicidad, Herramientas y equipos, y Otros | Resuelve el punto B.2. Una lista cerrada permite totales comparables por categoría. "Otros" cubre el resto |
| DT-E6-03 | **CC-10 (b):** un insumo puede registrarse también como gasto de *Materia prima* (casilla marcada por defecto). Un insumo de costo 0 no genera gasto | Resuelve el punto B.2 y evita anotar la misma compra dos veces. Se puede desmarcar si la compra ya se anotó como gasto |
| DT-E6-04 | Montos en pesos enteros mayores a 0, con la misma interpretación que el precio de E2 | RN-13. En Colombia no se usan centavos en el día a día |
| DT-E6-05 | Un registro equivocado se puede **eliminar** con confirmación; no se edita | Ninguna historia pide editar. Sin esta opción, un error de digitación dejaría el resumen incorrecto para siempre. Es la forma mínima de corregir |
| DT-E6-06 | La fecha propone el día de hoy, admite días anteriores y rechaza fechas futuras o anteriores al año 2000 | El resumen debe reflejar lo que ya ocurrió (HU-21: "saber si mi negocio deja ganancia") |
| DT-E6-07 | Una salida de inventario ("vendí") **no** crea un ingreso automático | El precio del producto es solo de referencia (RF-06): el monto real lo acuerdan las partes por chat. Un ingreso automático sería inexacto |
| DT-E6-08 | El ingreso no tiene un campo de descripción | El modelo de dominio define solo monto y fecha (RNF-06, datos mínimos) |
| DT-E6-09 | El balance es ingresos − gastos y se muestra con la palabra "Ganancia", "Pérdida" o "Sin ganancia ni pérdida" | HU-21: "para saber si mi negocio deja ganancia" |

### 6.1 Puntos para la Épica 7

1. **Administración (HU-22):** el administrador desactiva contenido o cuentas inapropiadas. Las finanzas y el inventario **no** se exponen al administrador. RN-14 dice "cada usuario accede solo a sus propios datos, incluidos los financieros", y la Épica 7 lo respetará.
2. **Exportar el resumen** (por ejemplo a CSV): no lo pide ninguna historia. Queda como mejora futura.

### 6.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E6-finanzas` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí. Son 354 pruebas: 90 de E1, 78 de E2, 57 de E3, 50 de E4, 43 de E5 y 36 de E6 |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en las épicas anteriores |

---

## 7. Batería de pruebas de validación

### 7.1 Cómo ejecutarla

```bash
git pull
pip install -r requirements.txt
python manage.py migrate                 # tablas de ingresos y gastos
python manage.py test -v 2
python manage.py cargar_demo --limpiar   # con ingresos y gastos de tres meses
python manage.py runserver
```

Cuenta de demostración: `demo.emprendedor01@amigo.edu.co`, contraseña `Clave-Segura-2026`. Entra a "Mi emprendimiento" y pulsa **Finanzas**.

### 7.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 354 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Casos manuales | Tabla 7.3 | Todos cumplen su criterio |

- **APROBADA:** pasan G1 a G4.
- **APROBADA CON AJUSTES:** solo falla un caso de CC-10, de eliminar o de CP-RNF11, o se pide cambiar alguna decisión de la sección 6 (por ejemplo, las categorías).
- **NO APROBADA:** falla G1, G2 o G3, o cualquier caso de HU-19, HU-20, HU-21, RNF-05, RNF-06 o RNF-03.

### 7.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-19.1 a CP-21.3 son los del Anexo A del Entregable 2; los demás completan la cobertura.

#### HU-19 · Registrar un ingreso (Should · RF-21 · RNF-05)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-19.1 | Registro de venta exitoso | A+M | En Finanzas, anotar el valor de "Ingresos". Pulsar "Registrar ingreso", escribir `25.000`, dejar la fecha de hoy y pulsar "Registrar ingreso" | "Registraste un ingreso de $ 25.000 el dd/mm/aaaa." Vuelve al resumen del mes; "Ingresos" aumentó $ 25.000 y el movimiento aparece en la lista | **Aprueba** si queda guardado y se suma al total. **No aprueba** si el total no cambia |
| CP-19.2 | Monto cero o negativo | A+M | Probar `0`, `-5000` y `abc` | "Escribe un monto mayor a 0…" en el campo; el total no cambia | **Aprueba** si los tres se rechazan |
| CP-19.3 | Ingresos de otro usuario | A+M | Con `demo.emprendedor01`, abrir "Eliminar" de un ingreso y copiar la URL. Cerrar sesión, entrar con `demo.emprendedor02` y abrir esa URL. Revisar también su resumen | 403 "No tienes permiso…". El resumen de emprendedor02 muestra solo sus cifras | **Aprueba** si se deniega el acceso. **No aprueba** si se ve o se elimina el ingreso ajeno |
| CP-19.4 | Fecha | A+M | Elegir mañana; dejar la fecha vacía; elegir ayer | Mañana: "La fecha no puede ser futura…". Vacía: "Indica la fecha…". Ayer: se guarda con esa fecha | **Aprueba** si se cumple |

#### HU-20 · Registrar un gasto (Should · RF-22)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-20.1 | Gasto con categoría | A+M | "Registrar gasto": `12.000`, *Materia prima*, fecha de hoy | "Registraste un gasto de $ 12.000 en Materia prima…". "Gastos" y "Gastos por categoría" se actualizan | **Aprueba** si queda guardado con su categoría |
| CP-20.2 | Gasto sin categoría | A+M | Escribir el monto sin elegir categoría y enviar | "Elige la categoría del gasto." y nada se guarda | **Aprueba** si se rechaza |
| CP-RN13 | Monto del gasto | A | Gasto con monto `0` | "Escribe un monto mayor a 0…" | **Aprueba** si la suite pasa |

#### HU-21 · Ver el resumen financiero de un periodo (Should · RF-23)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-21.1 | Resumen del mes | A+M | Con ingresos de $ 80.000 y gastos de $ 30.000 + $ 5.000 en un mes, abrir ese mes | Ingresos $ 80.000, Gastos $ 35.000 y Balance $ 45.000 "Ganancia". Gastos por categoría y movimientos del mes | **Aprueba** si las tres cifras son correctas |
| CP-21.2 | Periodo sin movimientos | A+M | Elegir en "Ver otro mes" uno sin registros (por ejemplo, agosto) | Las tres cifras en `$ 0` y "No registraste movimientos en este mes" | **Aprueba** si todo aparece en 0 |
| CP-21.3 | Otros meses | A+M | Con movimientos en octubre, noviembre y diciembre, abrir noviembre y luego "← Mes anterior" | Noviembre no muestra los de octubre ni los de diciembre, y viceversa | **Aprueba** si no se mezclan los meses |
| CP-21.4 | Pérdida | A+M | Registrar en un mes un gasto mayor que sus ingresos | Balance "−$ …" con "!" y "Pérdida", en una tarjeta con borde naranja | **Aprueba** si la pérdida se entiende sin depender del color |
| CP-21.5 | Navegación de meses | A | Abrir `?mes=2026-01`; abrir `?mes=2026-13` o `?mes=abc` | Enlaces a 2025-12 y 2026-02. Un mes inválido muestra el mes actual | **Aprueba** si la suite pasa |

#### Corrección y CC-10

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-E6.1 | Eliminar un registro equivocado | A+M | Pulsar "Eliminar" en un ingreso y luego "Sí, eliminar" | Confirmación "¿Eliminar el ingreso de $ …?", después "Eliminaste el ingreso…". El total se corrige | **Aprueba** si pide confirmación y corrige el total |
| CP-CC10.1 | Insumo también como gasto | A+M | En Inventario → "Registrar insumo": `Queso (lb)`, `3`, `21.000`, casilla marcada | "…También quedó como gasto de materia prima en Finanzas." El resumen del mes suma $ 21.000 en *Materia prima* | **Aprueba** si se crean ambos registros |
| CP-CC10.2 | Insumo sin gasto | A+M | Igual que el anterior, pero desmarcando la casilla; y otro insumo de costo `0` con la casilla marcada | Se registra solo el insumo; los gastos no cambian | **Aprueba** si no se crea ningún gasto |

#### RNF

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RNF05 | Privacidad (Must) | A+M | Con `demo.comprador`, abrir `/finanzas/`, `/finanzas/ingresos/nuevo/` y `/finanzas/gastos/nuevo/`. Sin sesión, abrir `/finanzas/`. Cerrar sesión y usar "Atrás" | 403 para el comprador. Sin sesión, redirección a "Ingresar". "Atrás" no muestra las cifras desde la caché | **Aprueba** si nadie más que el dueño ve sus finanzas |
| CP-RNF06 | Ley 1581 (Must) | A+M | Abrir `/privacidad/`. En "Mi cuenta", con una cuenta que aceptó una versión anterior | Versión 1.5 con "Tus finanzas…" y "Solo tú puedes ver tus finanzas". Mi cuenta avisa que el aviso cambió | **Aprueba** si están ambos |
| CP-RNF03 | Responsive (Must) | A+M | Finanzas, registrar ingreso o gasto y eliminar a 360 px en Chrome, Edge, Firefox y Safari (opcional: `EMPRENDEDOR_CORREO=… node scripts/verificar_interfaz.mjs`) | Sin desplazamiento horizontal; las cifras apiladas; las fichas de categoría usables con el dedo. Si el navegador no muestra un selector de mes, "Ver otro mes" acepta `2026-10` escrito | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF11 | Accesibilidad (Could) | A+M | Registrar un gasto solo con el teclado (Tab, flechas en las categorías, Enter). Revisar con un lector de pantalla el balance y un "Eliminar" | Foco visible. El balance se lee "Balance −$ … Pérdida (ingresos menos gastos)" y "Eliminar el gasto de $ … del …" | **Aprueba** si se completa sin mouse y se entiende sin ver |

### 7.4 Trazabilidad de las pruebas automáticas

| Archivo | Pruebas | Casos que cubre |
|---|---|---|
| `apps/finanzas/tests/test_reglas.py` | 10 | RN-13 y RN-15 con los valores límite del plan 4.1.4 (monto 0 y negativo); balance negativo; RN-14 en el servicio; orden de movimientos |
| `apps/finanzas/tests/test_hu19_hu20.py` | 8 | CP-19.1, CP-19.2, CP-19.4, CP-20.1, CP-20.2, CP-RN13 y CP-E6.1 |
| `apps/finanzas/tests/test_hu21_resumen.py` | 7 | CP-21.1 a CP-21.5 y el selector de mes accesible |
| `apps/finanzas/tests/test_rnf.py` | 11 | CP-19.3, CP-RNF05, CP-RNF06 (aviso 1.5 y datos mínimos), CP-CC10.1, CP-CC10.2, CP-RNF03 y CP-RNF11, y el botón **Finanzas** del panel |
| **Total E6** | **36** | Más 1 prueba nueva de `cargar_demo` en E3. Suite completa: 354 |

Antes de entregar, la suite se probó contra diez defectos introducidos a propósito. **Los diez se detectaron**, y al revertir los cambios la suite volvió a pasar completa:

| Defecto introducido | Pruebas que fallaron |
|---|---|
| M1 · aceptar un monto de 0 (RN-13) | 3 |
| M2 · el resumen no filtra por propietario (RN-14) | 2 |
| M3 · el mes incluye el día 1 del mes siguiente (RN-15) | 2 |
| M4 · eliminar sin verificar el dueño | 1 (CP-19.3) |
| M5 · gasto sin categoría permitido | 1 (CP-20.2) |
| M6 · CC-10 ignora la casilla | 1 |
| M7 · el balance suma en vez de restar | 4 |
| M8 · se permite una fecha futura | 1 |
| M9 · un comprador entra a Finanzas | 1 |
| M10 · la pérdida se muestra sin signo | 1 |
