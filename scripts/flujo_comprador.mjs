/**
 * CP-RNF02 · Recorrido de un comprador NUEVO (sin cuenta) hasta abrir el chat.
 *
 * RNF-02: «Un comprador nuevo encuentra un producto y abre el chat en 3 min o menos».
 * Este script recorre el camino más largo, en un teléfono de 360 px y sin sesión:
 *   portada → «Ver el catálogo» → buscar «arepa» → abrir el producto → «Contactar»
 *   → crear la cuenta → iniciar sesión → regresar al producto → «Contactar» → chat abierto.
 * Informa cuántas acciones necesita (clics y campos) y si se pierde el producto en el
 * camino. El tiempo de una máquina no reemplaza la prueba con personas del protocolo
 * de docs/epica-4/EPICA-4.md, pero demuestra que el recorrido no tiene tropiezos.
 *
 * Uso (con datos de demostración y el servidor corriendo):
 *   python manage.py cargar_demo --limpiar && python manage.py runserver
 *   node scripts/flujo_comprador.mjs
 * Crea una cuenta «demo.rnf02.…@amigo.edu.co»; `cargar_demo --limpiar` la borra.
 */
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8000";
const CONTRASENA = "Clave-Segura-2026";
const correo = `demo.rnf02.${Date.now()}@amigo.edu.co`;
const carpeta = new URL("./capturas/rnf02/", import.meta.url);
mkdirSync(carpeta, { recursive: true });

const browser = await chromium.launch();
const pagina = await browser.newPage({ viewport: { width: 360, height: 800 } });
let acciones = 0;
const paso = async (descripcion, accion) => {
  acciones += 1;
  await accion();
  console.log(`  ${String(acciones).padStart(2)}. ${descripcion}`);
};
const navegar = (accion) => Promise.all([pagina.waitForNavigation(), accion()]);

const inicio = Date.now();
await pagina.goto(`${BASE_URL}/`);
await paso("Pulsa «Ver el catálogo»", () => navegar(() => pagina.getByRole("link", { name: "Ver el catálogo" }).click()));
await paso("Escribe «arepa» en el buscador", () => pagina.fill("#id_q", "arepa"));
await paso("Pulsa «Buscar»", () => navegar(() => pagina.click(".buscador button")));
await paso("Abre el primer producto", () => navegar(() => pagina.locator(".tarjeta-producto__enlace").first().click()));
const producto = pagina.url();
const encontrado = Date.now();
await paso("Pulsa «Contactar» (pide iniciar sesión)", () => navegar(() => pagina.getByRole("link", { name: "Contactar" }).click()));
await paso("Pulsa «Crea una con tu correo institucional»", () =>
  navegar(() => pagina.getByRole("link", { name: "Crea una con tu correo institucional" }).click())
);
await paso("Escribe su correo", () => pagina.fill("#id_correo_institucional", correo));
await paso("Elige «Comprador»", () => pagina.check("#id_rol_0"));
await paso("Escribe la contraseña", () => pagina.fill("#id_contrasena", CONTRASENA));
await paso("Confirma la contraseña", () => pagina.fill("#id_contrasena_confirmacion", CONTRASENA));
await paso("Acepta el aviso de privacidad", () => pagina.check("#id_acepta_aviso"));
await paso("Pulsa «Crear cuenta»", () => navegar(() => pagina.getByRole("button", { name: "Crear cuenta" }).click()));
await paso("Escribe su correo para ingresar", () => pagina.fill("#id_username", correo));
await paso("Escribe su contraseña", () => pagina.fill("#id_password", CONTRASENA));
await paso("Pulsa «Iniciar sesión»", () => navegar(() => pagina.click("form.formulario button[type=submit]")));
const regresoAlProducto = pagina.url() === producto;
await paso("Pulsa «Contactar»", () => navegar(() => pagina.getByRole("button", { name: "Contactar" }).click()));
const chatAbierto = await pagina.getByText("Escribe tu primer mensaje").isVisible();
const fin = Date.now();
await pagina.screenshot({ path: new URL("chat-abierto-360.png", carpeta).pathname, fullPage: true });
await pagina.fill("#id_contenido", "Hola, ¿la tienes disponible hoy?");
await navegar(() => pagina.getByRole("button", { name: "Enviar" }).click());
const mensajeVisible = await pagina.getByText("Hola, ¿la tienes disponible hoy?").isVisible();
await pagina.screenshot({ path: new URL("mensaje-enviado-360.png", carpeta).pathname, fullPage: true });
await browser.close();

const segundos = (ms) => (ms / 1000).toFixed(1);
console.log(`\nProducto encontrado en ${segundos(encontrado - inicio)} s (4 acciones).`);
console.log(`Chat abierto en ${segundos(fin - inicio)} s de máquina con ${acciones} acciones, incluida la creación de la cuenta.`);
console.log(`Regresó al mismo producto después de registrarse: ${regresoAlProducto ? "sí" : "NO"}.`);
console.log(`Chat abierto: ${chatAbierto ? "sí" : "NO"} · Mensaje enviado y visible: ${mensajeVisible ? "sí" : "NO"}.`);
const ok = regresoAlProducto && chatAbierto && mensajeVisible && fin - inicio < 180_000;
console.log(ok ? "\nRecorrido de RNF-02 sin tropiezos." : "\nEl recorrido de RNF-02 tiene un problema.");
process.exit(ok ? 0 : 1);
