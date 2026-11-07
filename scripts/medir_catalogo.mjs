/**
 * CP-RNF01 · Medición de RNF-01: «El catálogo carga en 3 s o menos con 100 productos».
 *
 * Abre /catalogo/ en Chromium sin caché, con la red limitada como en Chrome DevTools, y
 * mide el tiempo hasta el evento `load` (todo lo necesario para ver la página) y el
 * Largest Contentful Paint. Repite 3 veces y usa la mediana.
 *
 * Criterio de aprobación: mediana de `load` ≤ 3000 ms con el perfil «4G» en 360 px y
 * en 1280 px. El perfil «4G lento» se informa como referencia.
 *
 * Uso (con 100 productos cargados y el servidor corriendo):
 *   python manage.py cargar_demo --limpiar --productos 100 --solo-disponibles
 *   python manage.py runserver
 *   node scripts/medir_catalogo.mjs
 */
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:8000";
const LIMITE_MS = 3000;
const REPETICIONES = 3;
const PERFILES = {
  "4G": { latency: 60, downloadThroughput: (9_000 * 1024) / 8, uploadThroughput: (1_500 * 1024) / 8 },
  "4G lento (referencia)": { latency: 150, downloadThroughput: (1_600 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 },
};
const ANCHOS = [360, 1280];

const mediana = (valores) => [...valores].sort((a, b) => a - b)[Math.floor(valores.length / 2)];

async function medir(browser, ancho, red) {
  const contexto = await browser.newContext({ viewport: { width: ancho, height: 800 } });
  const pagina = await contexto.newPage();
  const cdp = await contexto.newCDPSession(pagina);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  await cdp.send("Network.emulateNetworkConditions", { offline: false, ...red });
  await pagina.addInitScript(() => {
    window.__lcp = 0;
    new PerformanceObserver((lista) => {
      for (const entrada of lista.getEntries()) window.__lcp = entrada.startTime;
    }).observe({ type: "largest-contentful-paint", buffered: true });
  });
  await pagina.goto(`${BASE_URL}/catalogo/`, { waitUntil: "load" });
  await pagina.waitForTimeout(600); // el navegador reporta el LCP poco después del load
  const datos = await pagina.evaluate(() => {
    const nav = performance.getEntriesByType("navigation")[0];
    const recursos = performance.getEntriesByType("resource");
    const bytes = recursos.reduce((total, r) => total + (r.transferSize || 0), nav.transferSize || 0);
    return {
      load: nav.loadEventEnd,
      lcp: window.__lcp,
      bytes,
      total: document.querySelector(".resultados__total")?.textContent.trim().replace(/\s+/g, " "),
      tarjetas: document.querySelectorAll(".tarjeta-producto").length,
    };
  });
  await contexto.close();
  return datos;
}

const browser = await chromium.launch();
let aprobado = true;
for (const [nombre, red] of Object.entries(PERFILES)) {
  for (const ancho of ANCHOS) {
    const corridas = [];
    for (let i = 0; i < REPETICIONES; i++) corridas.push(await medir(browser, ancho, red));
    const load = mediana(corridas.map((c) => c.load));
    const lcps = corridas.map((c) => c.lcp).filter((valor) => valor > 0);
    const lcp = lcps.length ? `${Math.round(mediana(lcps))} ms` : "n/d";
    const kb = Math.round(mediana(corridas.map((c) => c.bytes)) / 1024);
    const cumple = load <= LIMITE_MS;
    if (nombre === "4G" && !cumple) aprobado = false;
    console.log(
      `${cumple ? "✓" : "✗"} ${nombre.padEnd(22)} ${String(ancho).padStart(4)} px · load ${Math.round(load)} ms · ` +
        `LCP ${lcp} · ${kb} KB · ${corridas[0].tarjetas} tarjetas · «${corridas[0].total}»`
    );
  }
}
await browser.close();
console.log(aprobado ? `\nRNF-01 cumplido: el catálogo carga en ${LIMITE_MS} ms o menos con el perfil 4G.` : "\nRNF-01 NO cumplido.");
process.exit(aprobado ? 0 : 1);
