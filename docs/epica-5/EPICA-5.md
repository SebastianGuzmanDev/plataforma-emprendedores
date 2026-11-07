# Épica 5 · Inventario

**Proyecto:** Emprendi Amigos (MVP) · Universidad Católica Luis Amigó
**Fuentes:** Entregable 1 (HU-15 a HU-18, RF-17 a RF-20), Entregable 2 (CU-15 a CU-18, diagramas A4, S6, C2 y ES1, atributos `existencias` y `umbralStockBajo` de `Producto`, clases `MovimientoInventario` e `Insumo`, reglas RN-10 a RN-12, supuestos S-3 y S-6, punto abierto B.2) y *Manual de Identidad Visual* versión 02.
**Estado:** **aprobada** (07/11/2026), con CC-09. Los puntos de la sección 6.1 se resolvieron en la Épica 6 (CC-10).

---

## 1. Alcance de la épica

| Elemento | Contenido (sin cambios respecto al Entregable 1) |
|---|---|
| Módulo | Emprendedor |
| Qué cubre | Existencias e insumos |
| Historias | HU-15 Registrar las existencias de un producto (Should, 2 h) · HU-16 Actualizar existencias con entradas y salidas (Should, 2 h) · HU-17 Recibir alerta de stock bajo (Could, 1 h) · HU-18 Registrar insumos (Could, 2 h) |
| Casos de uso | CU-15, CU-16, CU-17 «extend» CU-16 y CU-18 (actor Emprendedor) |
| RF | RF-17 y RF-18 (Should) y RF-19 y RF-20 (Could) |
| RNF de la épica | RNF-05 (cada usuario accede solo a sus datos) y los transversales que aplican: RNF-03, RNF-06 y RNF-11 |
| Reglas de negocio | RN-10 (existencias), RN-11 (alerta por umbral) y RN-12 (insumo) |
| Diagramas que implementa | A4 (actividades), S6 (secuencia de una salida), C2 (colaboración) y la transición *Disponible → Agotado* por existencias en 0 de ES1 |

En el Entregable 1 estas historias quedaron sin sprint, sujetas a la holgura del riesgo R1. Se construyen ahora porque el núcleo (E1 a E4) ya está terminado.

**RNF que no aplican:** RNF-01, RNF-02 y RNF-10 (catálogo y chat) y RNF-07 (entorno desplegado).

---

## 2. Desglose por componentes clave

| Componente (Entregable 2) | Implementación | Responsabilidad en E5 |
|---|---|---|
| **Módulo Inventario** | `apps/inventario/servicios.py` | `registrar_movimiento(producto, tipo, cantidad)` con el nombre de S6; `registrar_existencias` (HU-15), `definir_umbral` (HU-17) y `registrar_insumo` (HU-18) |
| | `apps/inventario/reglas.py` | RN-10 (enteros no negativos; al menos 1 unidad por movimiento) y RN-12 (cantidad de insumo mayor que 0) |
| Clase `Producto` (módulo E2) | `existencias`, `umbral_stock_bajo` y las operaciones de C2 | `obtener_existencias()`, `descontar(cantidad)`, `reponer(cantidad)` y `tiene_stock_bajo()` |
| Capa de acceso a datos | `MovimientoInventario`, `Insumo` | Restricciones: cantidad del movimiento > 0, existencias ≥ 0, cantidad del insumo > 0 y costo ≥ 0 |
| Capa de presentación | `views.py`, `templates/inventario/` | Panel de inventario, página de inventario por producto e insumos; alerta en el panel del emprendedor |

### 2.1 Modelo de dominio → código

| Elemento del diagrama | Código | Nota |
|---|---|---|
| `Producto.existencias : Entero` | `existencias` (entero ≥ 0 o vacío) | Vacío = el emprendedor aún no lleva inventario de ese producto (HU-15) |
| `Producto.umbralStockBajo : Entero` | `umbral_stock_bajo` (entero ≥ 1 o vacío) | S-6: el umbral es de cada producto |
| `Producto.registrarMovimiento(tipo, cantidad)` | `servicios.registrar_movimiento()` | El diagrama S6 lo ubica en el módulo Inventario |
| `Producto.tieneStockBajo() : Boolean` | `Producto.tiene_stock_bajo()` | C2: `existencias < umbral` |
| `MovimientoInventario(tipo, cantidad, fecha)` | `MovimientoInventario` | Historial de entradas y salidas |
| `TipoMovimiento` | `ENTRADA`, `SALIDA` | |
| `Insumo(nombre, cantidad : Decimal, costo : Decimal)` asociado a `Usuario` | `Insumo(propietario, nombre, cantidad, costo)` | S-3: pertenece al usuario emprendedor, no al emprendimiento |

### 2.2 Diagramas A4, S6 y C2 implementados

| Paso del diagrama | Código |
|---|---|
| A4: «Seleccionar un producto publicado» | El panel de inventario lista los productos *Disponible* y *Agotado*; uno desactivado no admite movimientos |
| A4: «¿La cantidad es válida?» → rechazar | `MovimientoForm`: entero de al menos 1 unidad |
| S6/C2 1.1: `registrarMovimiento(producto, SALIDA, cantidad)` · 1.2: `obtenerExistencias()` | `servicios.registrar_movimiento()` → `producto.obtener_existencias()` |
| S6 alt «la salida es mayor a las existencias» → salida rechazada | `producto.descontar()` es una sola actualización atómica con la condición `existencias ≥ cantidad`: aunque lleguen dos salidas a la vez, nunca quedan existencias negativas |
| C2 1.4: `crear(SALIDA, cantidad)` | `MovimientoInventario.objects.create(...)` |
| S6 opt «las existencias quedan en 0» → AGOTADO · C2 1.5 `marcarAgotado()` | `producto.marcar_agotado()` (ES1) |
| S6 opt «hay umbral definido y las existencias bajan de él» → alerta · C2 1.6 `tieneStockBajo()` | Mensaje "Stock bajo: quedan N unidades…" y etiqueta **Stock bajo** en el inventario y en el panel del emprendedor |

### 2.3 Rutas

| Ruta | Método | HU / RF |
|---|---|---|
| `/inventario/` | GET | Panel: existencias de los productos e insumos |
| `/inventario/productos/<código>/` | GET | Inventario del producto e historial de movimientos |
| `/inventario/productos/<código>/existencias/` | POST | HU-15 · RF-17 |
| `/inventario/productos/<código>/movimiento/` | POST | HU-16 · RF-18 (y la alerta de HU-17) |
| `/inventario/productos/<código>/umbral/` | POST | HU-17 · RF-19 |
| `/inventario/insumos/nuevo/` | GET, POST | HU-18 · RF-20 |

Todas exigen el rol Emprendedor y operan solo sobre sus productos e insumos. El panel "Mi emprendimiento" tiene el botón **Inventario** y muestra, junto a cada producto, sus existencias y la etiqueta *Stock bajo*. El catálogo público no muestra existencias.

---

## 3. Cumplimiento de los requerimientos

### 3.1 Requerimientos funcionales

| RF | Requerimiento | Cómo se cumple | Prueba |
|---|---|---|---|
| RF-17 | Registrar las existencias de un producto | Cantidad entera de 0 o más, una sola vez por producto (después se usan entradas y salidas); queda como primera entrada en el historial; si es 0, el producto pasa a *Agotado* (RN-10) | CP-15.1 a CP-15.4 |
| RF-18 | Actualizar las existencias con entradas y salidas | Entrada o salida de al menos 1 unidad; una salida mayor a las existencias se rechaza; si quedan en 0, el producto pasa a *Agotado*; historial con fecha | CP-16.1 a CP-16.6 |
| RF-19 | Recibir una alerta de stock bajo | Umbral por producto; alerta al quedar `existencias < umbral` (en el umbral no alerta) y etiqueta persistente mientras dure | CP-17.1 a CP-17.4 |
| RF-20 | Registrar insumos (materia prima) con su costo | Nombre, cantidad decimal mayor que 0 (admite «2,5») y costo total en pesos; lista y costo total acumulado | CP-18.1 a CP-18.3 |

### 3.2 Requerimientos no funcionales

| RNF | Prioridad | Cómo se cumple en E5 | Prueba |
|---|---|---|---|
| **RNF-05 Privacidad** | Must | El inventario y los insumos se consultan siempre filtrados por el usuario de la sesión; el inventario de otro emprendedor responde 403 y no cambia; un comprador recibe 403; el catálogo público no muestra existencias | CP-RNF05 |
| RNF-06 Cumplimiento legal | Must | Aviso de privacidad 1.4: el inventario y los insumos son datos privados del emprendedor. Solo se guardan los datos del modelo de dominio | CP-RNF06 |
| RNF-03 Compatibilidad | Must | Panel, inventario por producto e insumos verificados a 360, 768 y 1280 px | CP-RNF03 |
| RNF-11 Accesibilidad | Could | Etiquetas en todos los campos (sin identificadores repetidos entre formularios); la alerta se comunica con texto y no solo con color | CP-RNF11 |

---

## 4. Identidad visual aplicada

| Componente | Aplicación |
|---|---|
| Existencias del producto | Cifra grande en azul con la tipografía de títulos |
| Etiqueta *Stock bajo* y aviso de alerta | Naranja con texto negro (8.9:1) |
| Tipo de movimiento | Fichas seleccionables "Entrada: preparé o repuse" y "Salida: vendí o retiré" |

**Capturas** (con `cargar_demo`):

| Vista | Archivo |
|---|---|
| Panel de inventario e insumos a 1280 px | [e5-inventario-1280.png](capturas/e5-inventario-1280.png) |
| Inventario de un producto a 360 px | [e5-producto-360.png](capturas/e5-producto-360.png) |
| Alerta de stock bajo tras una salida (HU-17) | [e5-alerta-stock-bajo-1280.png](capturas/e5-alerta-stock-bajo-1280.png) |
| Registrar un insumo a 360 px | [e5-nuevo-insumo-360.png](capturas/e5-nuevo-insumo-360.png) |

---

## 5. Cambios sobre las épicas anteriores

| Épica | Cambio | Motivo | Pruebas afectadas |
|---|---|---|---|
| E2 | `Producto` recibe `existencias` y `umbral_stock_bajo`, más las operaciones de C2 (migración `0005`) | Atributos del modelo de dominio | La lista de campos de `test_rnf.py` (E2) los incluye; esa prueba ya lo anticipaba |
| E2 | "Marcar disponible" no se permite si el inventario está en 0 | Coherencia (CC-09): un producto sin existencias no puede ofrecerse | Prueba nueva en E5 |
| E2 | El panel del emprendedor muestra las existencias, la etiqueta *Stock bajo* y el botón **Inventario** | Navegación y HU-17 | Ninguna |
| Todas | Aviso de privacidad 1.4 (inventario e insumos) y estilo de aviso de alerta | Ley 1581 | La prueba de E4 que fijaba "1.3" ahora lee la versión vigente |
| E3 | `cargar_demo` crea existencias coherentes con el estado, umbrales e insumos | Probar E5 con contenido (R4) | 1 prueba nueva |

---

## 6. Decisiones técnicas y supuestos

| # | Decisión | Justificación |
|---|---|---|
| DT-E5-01 | Existencias vacías hasta que el emprendedor las registre | El inventario es opcional (Should): un producto sin inventario no debe aparecer como agotado |
| DT-E5-02 | Las existencias iniciales se registran una sola vez y quedan como la primera entrada; después solo hay entradas y salidas | Precondición de CU-16; el historial siempre explica las existencias actuales |
| DT-E5-03 | La salida se descuenta con una actualización atómica condicionada en la base de datos, y la base impide existencias negativas | RN-10 incluso con dos salidas simultáneas |
| DT-E5-04 | La alerta usa `existencias < umbral`; en el umbral no alerta | C2 1.6 y HU-17 ("bajan de ese umbral"); resuelve el punto B.2 sobre el umbral exacto |
| DT-E5-05 | **CC-09**: una entrada sobre un producto *Agotado* lo vuelve *Disponible*; registrar 0 existencias lo deja *Agotado*; "Marcar disponible" no se permite con 0 existencias | Resuelve el punto B.2 ("si una entrada vuelve a dejar Disponible un producto agotado") de forma coherente con CC-02 |
| DT-E5-06 | Insumo: cantidad decimal (hasta 3 decimales, con coma o punto) y costo total en pesos enteros; la unidad va en el nombre | El diagrama define `cantidad : Decimal` sin atributo de unidad; RN-12 exige "cantidad distinta de 0" (se interpreta como mayor que 0) |
| DT-E5-07 | Los insumos pertenecen al usuario y no requieren perfil de emprendimiento | Supuesto S-3 |
| DT-E5-08 | El catálogo no muestra existencias | Ninguna historia lo pide y es información comercial del emprendedor (RNF-05) |

### 6.1 Puntos para la Épica 6

1. **Insumos y gastos de materia prima** (punto B.2): hoy son registros independientes. En la Épica 6 se puede ofrecer "registrar también como gasto" al crear un insumo, para no anotarlo dos veces. Lo propongo como decisión de E6.
2. **Ventas e ingresos:** una salida "vendí" podría sugerir el ingreso correspondiente. Fuera del alcance de E5; se evaluará en E6.
3. **Editar o consumir insumos:** HU-18 solo pide registrarlos. Llevar su consumo sería una historia nueva.

### 6.2 Definición de Hecho

| Condición | Estado |
|---|---|
| El código está en la rama principal | Sí, al integrar `feature/E5-inventario` en `main` |
| Todos los escenarios Given-When-Then pasan | Sí (317 pruebas: 90 de E1, 78 de E2, 56 de E3, 50 de E4 y 43 de E5) |
| No hay errores bloqueantes | Sí |
| Desplegada en el entorno de pruebas | **Pendiente**, igual que en las épicas anteriores |

---

## 7. Batería de pruebas de validación

### 7.1 Cómo ejecutarla

```bash
git pull
pip install -r requirements.txt
python manage.py migrate                 # existencias y umbral en Producto; tablas de inventario
python manage.py test -v 2
python manage.py cargar_demo --limpiar   # con inventario, umbrales e insumos
python manage.py runserver
```

Cuenta de demostración: `demo.emprendedor01@amigo.edu.co`, contraseña `Clave-Segura-2026`. Entra a "Mi emprendimiento" → **Inventario**.

### 7.2 Criterio global de aprobación

| Puerta | Comando o acción | Resultado exigido |
|---|---|---|
| G1 Suite automática | `python manage.py test -v 2` | `Ran 317 tests` y `OK` |
| G2 Seguridad de producción | `check --deploy --settings=config.settings.prod` | `System check identified no issues (0 silenced).` |
| G3 Modelo y migraciones | `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| G4 Casos manuales | Tabla 7.3 | Todos cumplen su criterio |

- **APROBADA:** G1 a G4 pasan.
- **APROBADA CON AJUSTES:** solo falla un caso de HU-17 o HU-18 (Could) o CP-RNF11, o se pide cambiar alguna decisión de la sección 6 (por ejemplo, CC-09).
- **NO APROBADA:** falla G1, G2 o G3, o cualquier caso de HU-15, HU-16, RNF-05, RNF-06 o RNF-03.

### 7.3 Casos de prueba

Tipo: **A** = automático (incluido en G1), **M** = manual. CP-15.1 a CP-18.2 son los del Anexo A del Entregable 2; los demás completan la cobertura.

#### HU-15 · Registrar las existencias (Should · RF-17)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-15.1 | Registro exitoso | A+M | En Inventario, "Gestionar" un producto con "Sin registrar"; escribir `25` y pulsar "Registrar existencias" | "Registraste 25 unidades…"; la cifra muestra 25; el historial muestra "Entrada de 25" | **Aprueba** si quedan guardadas |
| CP-15.2 | Cantidad inválida | A+M | Probar `-1`, `2.5`, `2,5` y `abc` | "Escribe una cantidad en unidades enteras…"; sigue "Sin registrar" | **Aprueba** si las cuatro se rechazan |
| CP-15.3 | Registrar 0 | A | Registrar `0` | El producto queda en 0 y *Agotado* (RN-10) | **Aprueba** si se cumple |
| CP-15.4 | Registrar dos veces | A | Volver a enviar existencias a un producto que ya las tiene | "…ya tiene existencias registradas: usa entradas y salidas…"; no cambian | **Aprueba** si no se sobrescriben |

#### HU-16 · Entradas y salidas (Should · RF-18)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-16.1 | Movimiento registrado | A+M | Con existencias 5: "Entrada" de 3 y luego "Salida" de 2 | "Entrada de 3 unidades registrada. Existencias: 8." y después 6; el historial muestra ambos movimientos | **Aprueba** si las existencias se actualizan en consecuencia |
| CP-16.2 | Salida mayor a las existencias | A+M | Con 5, "Salida" de 6 | "No puedes sacar 6 unidades: solo hay 5."; siguen en 5; no se agrega movimiento | **Aprueba** si se rechaza |
| CP-16.3 | Existencias en 0 | A+M | Con 5, "Salida" de 5; revisar el catálogo | "…quedó agotado…"; el catálogo lo muestra como **Agotado** | **Aprueba** si pasa a Agotado |
| CP-16.4 | Cantidad inválida | A+M | Cantidad `0`, `-2`, `1.5` o vacía; o sin elegir el tipo | "Escribe una cantidad entera de al menos 1 unidad." o "Elige si es una entrada o una salida." | **Aprueba** si no se registra nada |
| CP-16.5 | Reponer un agotado (CC-09) | A+M | Con el producto agotado en 0, registrar una "Entrada" de 4 | "…volvió a estar disponible en el catálogo"; existencias 4 y *Disponible* | **Aprueba** si vuelve a Disponible |
| CP-16.6 | Coherencia con el estado | A+M | Con existencias en 0, ir a "Mi emprendimiento" y pulsar "Marcar disponible" | "…registra una entrada de inventario para volver a ofrecerlo"; sigue *Agotado* | **Aprueba** si no se permite |

#### HU-17 · Alerta de stock bajo (Could · RF-19)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-17.1 | Alerta por umbral | A+M | Umbral 5 con existencias 10; "Salida" de 6 | Aviso naranja "Stock bajo: quedan 4 unidades… (umbral: 5)"; etiqueta **Stock bajo** en Inventario y en "Mi emprendimiento" | **Aprueba** si aparece la alerta |
| CP-17.2 | Sin alerta | A+M | Umbral 5; dejar las existencias en 6 | Ni aviso ni etiqueta | **Aprueba** si no hay alerta |
| CP-17.3 | En el umbral exacto | A | Existencias 10 y umbral 10 | Sin alerta (C2: `existencias < umbral`) | **Aprueba** si la suite pasa |
| CP-17.4 | Definir y quitar el umbral | A+M | Guardar `3`; luego dejarlo vacío; probar `0` y `2.5` | "Te avisaremos cuando queden menos de 3 unidades."; "Quitaste el umbral…"; `0` y `2.5` se rechazan | **Aprueba** si se cumple |

#### HU-18 · Registrar insumos (Could · RF-20)

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-18.1 | Insumo con costo | A+M | "Registrar insumo": `Harina de maíz (kg)`, cantidad `2,5`, costo `12.000` | "Registraste el insumo…"; aparece en la lista con "Cantidad: 2,5 · Costo: $ 12.000" y el costo total se actualiza | **Aprueba** si queda guardado |
| CP-18.2 | Datos inválidos | A+M | Costo vacío; cantidad `0`; nombre vacío | "Escribe el costo…", "La cantidad debe ser mayor que 0…", "Escribe el nombre del insumo." | **Aprueba** si no se guarda ninguno |
| CP-18.3 | Costo total | A | Dos insumos de $ 15.000 y $ 8.000 | "Costo total de los insumos registrados: $ 23.000" | **Aprueba** si la suma es correcta |

#### RNF

| ID | Escenario | Tipo | Pasos | Resultado esperado | Aprueba si / No aprueba si |
|---|---|---|---|---|---|
| CP-RNF05 | Privacidad (Must) | A+M | Con `demo.emprendedor02`, abrir la URL del inventario de un producto de `demo.emprendedor01`; con `demo.comprador`, abrir `/inventario/` | 403 en ambos casos; los insumos y existencias ajenos no aparecen; el detalle público de un producto no muestra existencias | **Aprueba** si nadie ve ni cambia el inventario ajeno |
| CP-RNF06 | Ley 1581 (Must) | A+M | Abrir `/privacidad/` | Versión 1.4 con "Tu inventario…" y "Solo tú puedes ver tu inventario" | **Aprueba** si está |
| CP-RNF03 | Responsive (Must) | A+M | Inventario, inventario por producto e insumo a 360 px en Chrome, Edge, Firefox y Safari (opcional: `EMPRENDEDOR_CORREO=… node scripts/verificar_interfaz.mjs`) | Sin desplazamiento horizontal; fichas y botones usables con el dedo | **Aprueba** si se cumple en los 4 navegadores |
| CP-RNF11 | Accesibilidad (Could) | A+M | Registrar un movimiento solo con el teclado | Foco visible; la alerta se lee como texto ("Stock bajo: …") | **Aprueba** si se completa sin mouse |

### 7.4 Trazabilidad de las pruebas automáticas

| Archivo (`apps/inventario/tests/`) | Pruebas | Casos que cubre |
|---|---|---|
| `test_reglas.py` | 10 | RN-10, RN-11 y RN-12 con los valores límite del plan 4.1.4; operaciones de C2; existencias negativas impedidas por la base de datos |
| `test_hu15_hu16_existencias.py` | 15 | CP-15.1 a CP-15.4, CP-16.1 a CP-16.6 |
| `test_hu17_hu18.py` | 9 | CP-17.1 a CP-17.4, CP-18.1 a CP-18.3 |
| `test_rnf.py` | 9 | CP-RNF05, CP-RNF06, CP-RNF03, CP-RNF11 |
| **Total E5** | **43** | (más las 274 de E1 a E4 = 317) |

Antes de entregar, la suite se probó contra cuatro defectos introducidos a propósito, y todos se detectaron:

- una salida que llega a 0 no agota el producto: 3 fallos;
- alertar también en el umbral exacto: 2 fallos;
- el panel muestra los insumos de todos: 1 fallo;
- una entrada no devuelve el producto a *Disponible*: 1 fallo.

Al revertir los cambios, la suite volvió a pasar completa.
