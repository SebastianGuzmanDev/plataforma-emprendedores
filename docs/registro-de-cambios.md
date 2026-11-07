# Registro de cambios

Proceso de la sección 4.2.2 del Entregable 2: registrar, evaluar el impacto, decidir, aplicar en una rama actualizando los artefactos y cerrar cuando pasan las pruebas. Línea base de requerimientos: Entregable 1. Línea base del diseño: Entregable 2.

| ID | Fecha | Cambio | Tipo | Elementos afectados | Horas | Decisión |
|---|---|---|---|---|---|---|
| CC-00 | Entregable 1 | Línea base: 22 HU, 24 RF, 11 RNF y 46 h de desarrollo | Línea base | Todos | — | Aprobada |
| CC-01 | 05/11/2026 | Verificar que quien se registra es dueño del correo institucional (enlace de confirmación) | Requerimiento | RF-01, HU-01, CU-01, A1, S1, CP-01.x | ≈ 2 | **Propuesta, pendiente de decisión** |
| CC-02 | 06/11/2026 | Reactivación: un producto *Agotado* puede volver a *Disponible* y también se puede editar. *Desactivado* sigue siendo definitivo | Diseño (ES1) y requerimiento (RF-08) | RF-08, HU-06 (escenarios nuevos), CU-06, ES1 (`docs/diagramas/ES1-producto-v2.puml`), RN-08, CP-06.5 a CP-06.7 | ≈ 0,5 | **Aprobada** y aplicada |
| CC-03 | 06/11/2026 | Nombre obligatorio en el perfil del emprendimiento (hasta 80 caracteres) | Requerimiento | RF-05, HU-04, CU-04, A2, clase `Emprendimiento`, RN-06, aviso de privacidad (versión 1.2), CP-04.1 a CP-04.5 | ≈ 0,5 | **Aprobada** y aplicada |
| CC-04 | 06/11/2026 | La plataforma se llama **Emprendi Amigos** (antes "Plataforma de Emprendedores", nombre provisional S-E1-7) | Presentación | Encabezado, títulos, correo de recuperación, README | ≈ 0,25 | **Aprobada** y aplicada |
| CC-05 | 06/11/2026 | Confirmar los supuestos S-E2-1 (categoría "Otros") y S-E2-2 (precio de 0 permitido) | Supuestos de diseño | Anexo B del Entregable 2 | 0 | **Aprobada** (sin cambios de código) |
| CC-06 | 07/11/2026 | Miniatura de 600 px por producto para las tarjetas del catálogo, generada junto con la foto | Diseño (sin cambio de requerimiento) | Clase `Producto` (atributo `miniatura`), S3 ("guardar(foto)" guarda foto y miniatura), D5, migración `0004_miniatura` | ≈ 0,5 | **Aprobada** (07/11/2026) y aplicada en E3 |
| CC-07 | 07/11/2026 | Confirmar el punto B.2: cualquier cuenta que no sea la dueña del producto puede contactar, incluso otro emprendedor; la búsqueda se mantiene solo por el nombre del producto (RF-11) | Supuestos de diseño | HU-11, CU-11, CU-10 | 0 | **Aprobada** (sin cambios de código) |
| CC-08 | 07/11/2026 | El registro conserva la página de origen: quien se registra desde "Contactar" vuelve al producto después de iniciar sesión | Diseño (flujos A1 y A3, para RNF-02) | CU-01, A1, A3, plantillas de registro e ingreso, `test_rnf02.py` | ≈ 0,5 | **Aprobada** (07/11/2026) y aplicada en E4 |
| CC-09 | 07/11/2026 | Coherencia entre inventario y estado (punto B.2): una entrada sobre un producto *Agotado* lo vuelve *Disponible*; registrar 0 existencias lo deja *Agotado*; "Marcar disponible" no se permite con existencias en 0 | Diseño (ES1) y requerimiento (RF-18) | RF-18, HU-16, CU-16, A4, ES1 (`docs/diagramas/ES1-producto-v2.puml`), CP-15.3, CP-16.5, CP-16.6 | ≈ 0,5 | **Aprobada** con la Épica 5 y aplicada |
| CC-10 | 07/11/2026 | Punto B.2 sobre finanzas: (a) los gastos se clasifican en una lista cerrada de seis categorías: Materia prima, Empaques, Transporte, Publicidad, Herramientas y equipos, y Otros; (b) al registrar un insumo, una casilla marcada por defecto lo registra también como gasto de *Materia prima* con la fecha del día, para no anotarlo dos veces (un insumo de costo 0 no genera gasto, RN-13) | Diseño (sin cambio de RF) | HU-18, HU-20, CU-18, CU-20 (postcondición "incluye los gastos de materia prima"), clase `Gasto` (atributo `categoria`), formulario de insumos, aviso de privacidad (versión 1.5) | ≈ 0,5 | **Aplicada en E6; pendiente de visto bueno** con la aprobación de la épica |

## Texto actualizado de los artefactos

**RF-05 (CC-03):** Crear el perfil del emprendimiento (nombre, descripción, categoría, horarios y zona de entrega).

**RN-06 (CC-03):** Son obligatorios nombre, descripción, categoría, horarios y zona de entrega.

**RF-08 (CC-02):** Desactivar un producto, marcarlo como agotado o volver a marcarlo como disponible.

**HU-06, escenarios nuevos (CC-02):**

> **Escenario 5: Volver a estar disponible. Dado que** tengo un producto agotado, **cuando** lo marco como disponible, **entonces** el catálogo lo muestra con el estado "Disponible".
>
> **Escenario 6: Editar un producto agotado. Dado que** tengo un producto agotado, **cuando** cambio su precio y guardo, **entonces** el catálogo muestra el precio nuevo y el producto sigue agotado.

**HU-04, escenario 2 (CC-03):** el nombre se suma a los campos obligatorios que se señalan si están vacíos.

**HU-16, escenario nuevo (CC-09):**

> **Escenario 4: Reponer un producto agotado. Dado que** tengo un producto agotado, **cuando** registro una entrada válida, **entonces** las existencias se actualizan y el producto vuelve a "Disponible".

**HU-18, escenario nuevo (CC-10):**

> **Escenario 3: Registrar el insumo también como gasto. Dado que** registro un insumo con costo mayor a 0 y dejo marcada la casilla "Registrar también este costo como un gasto de materia prima", **cuando** lo guardo, **entonces** el insumo queda registrado y el resumen financiero del mes suma un gasto de *Materia prima* por ese costo.

**HU-20 (CC-10):** las categorías del gasto son Materia prima, Empaques, Transporte, Publicidad, Herramientas y equipos, y Otros.

**ES1 (CC-02):** nueva transición *Agotado → Disponible* ("marcar disponible") y actividad interna "editar" en *Agotado*. *Desactivado* conserva su carácter definitivo. Fuente actualizada: `docs/diagramas/ES1-producto-v2.puml`.

**Clase `Emprendimiento` (CC-03):** nuevo atributo `-nombre : String`.

## Efecto sobre la capacidad (riesgo R1)

CC-02 a CC-04 suman cerca de 1,25 h. El Entregable 1 exige compensar las horas nuevas con una historia de menor prioridad (línea de corte por prioridad). Se propone descontarlas de la holgura de HU-10 (Should, búsqueda), que sigue sin sprint asignado.

CC-09 y CC-10 suman cerca de 1 h más. Se descuentan de la misma holgura: las épicas E5 y E6 ya estaban sin sprint asignado (holgura del riesgo R1), así que no desplazan ninguna historia Must.
