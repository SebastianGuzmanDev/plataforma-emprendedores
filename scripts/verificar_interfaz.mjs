/**
 * Verificación automática de la interfaz (RNF-03 y manual de identidad visual).
 *
 * Revisa, en cada página y en cada ancho (360, 768 y 1280 px):
 *   1. que no haya desplazamiento horizontal (la página cabe en la pantalla);
 *   2. que el logotipo institucional mida al menos 190 px de ancho (5 cm, pág. 10);
 *   3. que todo control interactivo mida al menos 24 × 24 px (WCAG 2.5.8).
 * Además guarda capturas en scripts/capturas/<navegador>/.
 *
 * Uso (con el servidor corriendo en otra terminal: python manage.py runserver):
 *   npm install --no-save playwright@1.49.1 && npx playwright install
 *   node scripts/verificar_interfaz.mjs                     # chromium
 *   node scripts/verificar_interfaz.mjs firefox             # o webkit (motor de Safari)
 *   BASE_URL=http://127.0.0.1:8000 node scripts/verificar_interfaz.mjs chromium
 *
 * Pantallas del emprendedor (E2): define una cuenta emprendedora con perfil y productos
 *   EMPRENDEDOR_CORREO=... EMPRENDEDOR_CONTRASENA=... node scripts/verificar_interfaz.mjs
 */
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const playwright = require("playwright");

const navegador = process.argv[2] || "chromium";
const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8000";
const ANCHOS = [360, 768, 1280];
const PAGINAS = [
  ["inicio", "/"],
  ["registro", "/cuentas/registro/"],
  ["ingresar", "/cuentas/ingresar/"],
  ["recuperar", "/cuentas/recuperar/"],
  ["aviso-privacidad", "/privacidad/"],
  ["e3-catalogo", "/catalogo/"],
  ["e3-catalogo-filtro", "/catalogo/?categoria=comida&q=arepa"],
  ["e3-catalogo-sin-resultados", "/catalogo/?q=zzzz"],
];
const PAGINAS_EMPRENDEDOR = [
  ["e2-panel", "/emprendimiento/"],
  ["e2-perfil", "/emprendimiento/perfil/"],
  ["e2-publicar", "/emprendimiento/productos/nuevo/"],
  ["e2-vista-previa", "/emprendimiento/vista-previa/"],
];
const carpeta = new URL(`./capturas/${navegador}/`, import.meta.url);
mkdirSync(carpeta, { recursive: true });

const fallos = [];
const browser = await playwright[navegador].launch();

// Desplaza la página para que carguen las imágenes diferidas antes de la captura.
async function cargarPerezosas(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += window.innerHeight) {
      window.scrollTo(0, y);
      await new Promise((resolver) => setTimeout(resolver, 60));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForLoadState("networkidle");
}

async function revisar(page, nombre, ancho) {
  const r = await page.evaluate(() => {
    const logo = document.querySelector(".encabezado__logo img");
    const pequenos = [...document.querySelectorAll("a, button, input, select, textarea")]
      .filter((el) => el.offsetParent !== null && !el.closest(".saltar"))
      .map((el) => [el, el.getBoundingClientRect()])
      .filter(([el, b]) => el.tagName !== "A" || el.closest("nav, .acciones") ? b.width < 24 || b.height < 24 : false)
      .map(([el]) => el.outerHTML.slice(0, 80));
    return {
      desborde: document.documentElement.scrollWidth - window.innerWidth,
      logo: logo ? logo.getBoundingClientRect().width : 0,
      pequenos,
    };
  });
  await cargarPerezosas(page);
  const id = `${nombre} @ ${ancho}px`;
  if (r.desborde > 0) fallos.push(`${id}: desplazamiento horizontal de ${r.desborde}px`);
  if (r.logo < 189) fallos.push(`${id}: logotipo de ${r.logo.toFixed(0)}px (< 190px)`);
  r.pequenos.forEach((html) => fallos.push(`${id}: control menor a 24px → ${html}`));
  console.log(`${r.desborde > 0 || r.logo < 189 || r.pequenos.length ? "✗" : "✓"} ${id}  (logo ${r.logo.toFixed(0)}px)`);
}

for (const ancho of ANCHOS) {
  const page = await browser.newPage({ viewport: { width: ancho, height: 800 } });
  for (const [nombre, ruta] of PAGINAS) {
    await page.goto(BASE_URL + ruta);
    await revisar(page, nombre, ancho);
    await page.screenshot({ path: new URL(`${nombre}-${ancho}.png`, carpeta).pathname, fullPage: true });
  }
  // Detalle de un producto (HU-09): se abre desde la primera tarjeta del catálogo
  await page.goto(BASE_URL + "/catalogo/");
  const enlace = await page.$(".tarjeta-producto__enlace");
  if (enlace) {
    await Promise.all([page.waitForNavigation(), enlace.click()]);
    await revisar(page, "e3-detalle", ancho);
    await page.screenshot({ path: new URL(`e3-detalle-${ancho}.png`, carpeta).pathname, fullPage: true });
  }
  // Estado con errores del registro (HU-01, escenarios 3 y 4)
  await page.goto(BASE_URL + "/cuentas/registro/");
  await page.fill("#id_correo_institucional", "ana@gmail.com");
  await page.click("button[type=submit]");
  await page.waitForLoadState();
  await revisar(page, "registro-con-errores", ancho);
  await page.screenshot({ path: new URL(`registro-errores-${ancho}.png`, carpeta).pathname, fullPage: true });
  await page.close();

  if (process.env.EMPRENDEDOR_CORREO) {
    const contexto = await browser.newContext({ viewport: { width: ancho, height: 800 } });
    const privada = await contexto.newPage();
    await privada.goto(BASE_URL + "/cuentas/ingresar/");
    await privada.fill("#id_username", process.env.EMPRENDEDOR_CORREO);
    await privada.fill("#id_password", process.env.EMPRENDEDOR_CONTRASENA || "");
    await Promise.all([privada.waitForNavigation(), privada.click("form.formulario button[type=submit]")]);
    for (const [nombre, ruta] of PAGINAS_EMPRENDEDOR) {
      await privada.goto(BASE_URL + ruta);
      await revisar(privada, nombre, ancho);
      await privada.screenshot({ path: new URL(`${nombre}-${ancho}.png`, carpeta).pathname, fullPage: true });
    }
    // Estado con errores de la publicación (HU-05, escenario 3) y del perfil (HU-04, escenario 2)
    await privada.goto(BASE_URL + "/emprendimiento/productos/nuevo/");
    await privada.fill("#id_nombre", "Arepa de prueba");
    await privada.fill("#id_precio_referencia", "12a");
    await Promise.all([privada.waitForNavigation(), privada.click("form.formulario button[type=submit]")]);
    await revisar(privada, "e2-publicar-con-errores", ancho);
    await privada.screenshot({ path: new URL(`e2-publicar-errores-${ancho}.png`, carpeta).pathname, fullPage: true });
    await contexto.close();
  }
}
await browser.close();

if (fallos.length) {
  console.error(`\n${fallos.length} problema(s):\n- ${fallos.join("\n- ")}`);
  process.exit(1);
}
const vistas = ANCHOS.length * (PAGINAS.length + 2 + (process.env.EMPRENDEDOR_CORREO ? PAGINAS_EMPRENDEDOR.length + 1 : 0));
console.log(`\nInterfaz verificada en ${navegador}: ${vistas} vistas sin problemas.`);
