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
| CC-06 | 07/11/2026 | Miniatura de 600 px por producto para las tarjetas del catálogo, generada junto con la foto | Diseño (sin cambio de requerimiento) | Clase `Producto` (atributo `miniatura`), S3 ("guardar(foto)" guarda foto y miniatura), D5, migración `0004_miniatura` | ≈ 0,5 | **Aplicada en E3; pendiente de visto bueno** con la aprobación de la épica |

## Texto actualizado de los artefactos

**RF-05 (CC-03):** Crear el perfil del emprendimiento (nombre, descripción, categoría, horarios y zona de entrega).

**RN-06 (CC-03):** Son obligatorios nombre, descripción, categoría, horarios y zona de entrega.

**RF-08 (CC-02):** Desactivar un producto, marcarlo como agotado o volver a marcarlo como disponible.

**HU-06, escenarios nuevos (CC-02):**

> **Escenario 5: Volver a estar disponible. Dado que** tengo un producto agotado, **cuando** lo marco como disponible, **entonces** el catálogo lo muestra con el estado "Disponible".
>
> **Escenario 6: Editar un producto agotado. Dado que** tengo un producto agotado, **cuando** cambio su precio y guardo, **entonces** el catálogo muestra el precio nuevo y el producto sigue agotado.

**HU-04, escenario 2 (CC-03):** el nombre se suma a los campos obligatorios que se señalan si están vacíos.

**ES1 (CC-02):** nueva transición *Agotado → Disponible* ("marcar disponible") y actividad interna "editar" en *Agotado*. *Desactivado* conserva su carácter definitivo. Fuente actualizada: `docs/diagramas/ES1-producto-v2.puml`.

**Clase `Emprendimiento` (CC-03):** nuevo atributo `-nombre : String`.

## Efecto sobre la capacidad (riesgo R1)

CC-02 a CC-04 suman cerca de 1,25 h. El Entregable 1 exige compensar las horas nuevas con una historia de menor prioridad (línea de corte por prioridad). Se propone descontarlas de la holgura de HU-10 (Should, búsqueda), que sigue sin sprint asignado.
