# Emprendi Amigos · Universidad Católica Luis Amigó

MVP web donde los emprendedores de la comunidad universitaria publican su portafolio y llevan el control de su inventario y sus finanzas, y donde compradores (estudiantes, docentes, personal administrativo y directivos) encuentran lo que se vende en el campus.

Proyecto del curso **Ingeniería de Software** · Jerónimo Álvarez Calvachi y Sebastián Guzmán Ortiz.

| Épica | Módulo | Estado |
|---|---|---|
| E1 Cuentas y acceso (HU-01 a HU-03) | `apps/cuentas` | Entregada ([documento](docs/epica-1/EPICA-1.md)) |
| E2 Perfil y productos (HU-04 a HU-06) | `apps/perfil_productos` | **Entregada, en revisión** ([documento](docs/epica-2/EPICA-2.md)) |
| E3 Catálogo (HU-07 a HU-10) | — | Pendiente |
| E4 Contacto por chat (HU-11 a HU-14) | — | Pendiente |
| E5 Inventario (HU-15 a HU-18) | — | Pendiente |
| E6 Finanzas (HU-19 a HU-21) | — | Pendiente |
| E7 Administración (HU-22) | — | Pendiente |

## Tecnología

- Python 3.10 o superior y **Django 5.2 LTS** (soporte de seguridad hasta abril de 2028).
- Monolito modular de tres capas (presentación, lógica de negocio y acceso a datos), con un módulo por épica, como define la sección 2.2 del Entregable 2.
- SQLite en desarrollo y pruebas. Contraseñas con hash **Argon2id**.
- Fotos de productos validadas y normalizadas con **Pillow** (sin metadatos EXIF), guardadas en `media/` (separado de la base de datos).
- Interfaz con plantillas de Django y CSS propio basado en el *Manual de Identidad Visual* de la universidad (`static/css/marca.css`).

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abre <http://127.0.0.1:8000>. En desarrollo, los correos de recuperación de contraseña se imprimen en la terminal del servidor y las fotos de productos se guardan en `media/`.

Para asignar el rol de administrador a una cuenta ya registrada (RF-03: se asigna internamente):

```bash
python manage.py promover_administrador correo@amigo.edu.co
```

## Cómo probarlo

```bash
python manage.py test -v 2
```

Resultado esperado: `Ran 164 tests` y `OK` (90 de E1 y 74 de E2). Las baterías completas (automáticas y manuales) con sus criterios de aprobación están en [docs/epica-1/EPICA-1.md](docs/epica-1/EPICA-1.md#6-batería-de-pruebas-de-validación) y [docs/epica-2/EPICA-2.md](docs/epica-2/EPICA-2.md#7-batería-de-pruebas-de-validación).

Verificación de la configuración de producción (RNF-04):

```bash
DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
DJANGO_ALLOWED_HOSTS=emprendedores.amigo.edu.co \
python manage.py check --deploy --settings=config.settings.prod
```

Verificación visual responsive (opcional, requiere Node.js y el servidor corriendo):

```bash
npm install --no-save playwright@1.49.1 && npx playwright install
node scripts/verificar_interfaz.mjs chromium   # también: firefox, webkit
```

Para incluir las pantallas del emprendedor, define `EMPRENDEDOR_CORREO` y `EMPRENDEDOR_CONTRASENA` de una cuenta emprendedora con perfil.

Los cambios aprobados sobre los Entregables se registran en [docs/registro-de-cambios.md](docs/registro-de-cambios.md).

## Estructura

```
config/                 Configuración (base, dev, prod) y rutas
apps/cuentas/           E1 · Cuentas y acceso
  models.py             Capa de datos: Usuario y Rol
  reglas.py             Reglas de negocio RN-01 a RN-03 (funciones puras)
  servicios.py          Lógica de negocio: caso de uso de registro (CU-01)
  forms.py, views.py    Capa de presentación
  decorators.py         rol_requerido(): control de acceso por rol para E2 a E7
  middleware.py         Sin caché para páginas vistas con sesión (RNF-05)
  tests/                Pruebas unitarias y de integración por HU y RNF
apps/perfil_productos/  E2 · Perfil y productos
  models.py             Categoria, Emprendimiento, Producto y estados (diagrama ES1)
  reglas.py             RN-07: precio y foto (validación y normalización)
  servicios.py          Casos de uso CU-04 a CU-06 (secuencia S3)
  models.visibles_en_catalogo()  Contrato RN-09 que usará el Catálogo (E3)
templates/              Plantillas comunes, aviso de privacidad y páginas de error
static/css/marca.css    Tokens de color y tipografía del manual de identidad
static/img/             Logotipo institucional (vector) y elemento gráfico
docs/                   Documentación por épica
scripts/                Verificación visual con Playwright
```

## Cómo contribuir

Se sigue la estrategia de la sección 4.2 del Entregable 2 (Gitflow sin rama `develop`):

1. Crea una rama por historia desde `main`: `git checkout -b feature/HU-04-perfil-emprendimiento`.
2. Haz commits pequeños que mencionen la historia: `HU-04: validar campos obligatorios del perfil`.
3. Escribe primero las pruebas de los escenarios Given-When-Then; integra solo con la suite en verde.
4. Abre la solicitud de integración hacia `main`; la otra persona del equipo revisa y ejecuta los escenarios.
5. Etiqueta el cierre de cada sprint (`sprint-1` … `sprint-4`) y la entrega final (`v1.0`).

Configuración de producción: copia `.env.example`, define las variables y usa `config.settings.prod`.
