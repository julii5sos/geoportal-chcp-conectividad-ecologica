/** Captura determinista de una app Streamlit ya iniciada mediante Chrome CDP. */

import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const [, , url, archivo, textoEsperado = "Conectividad Panamá"] = process.argv;
if (!url || !archivo) {
  throw new Error("Uso: node capturar_streamlit_cdp.mjs URL ARCHIVO [TEXTO_ESPERADO]");
}

const puertoCdp = process.env.CHROME_CDP_PORT || "9222";
const ancho = Number(process.env.CDP_WIDTH || 1600);
const alto = Number(process.env.CDP_HEIGHT || 1100);
const baseCdp = `http://127.0.0.1:${puertoCdp}`;
const destino = resolve(archivo);

const objetivo = await (
  await fetch(`${baseCdp}/json/new?${encodeURIComponent(url)}`, { method: "PUT" })
).json();
const socket = new WebSocket(objetivo.webSocketDebuggerUrl);
await new Promise((resolver, rechazar) => {
  socket.addEventListener("open", resolver, { once: true });
  socket.addEventListener("error", rechazar, { once: true });
});

let secuencia = 0;
const pendientes = new Map();
socket.addEventListener("message", (evento) => {
  const mensaje = JSON.parse(evento.data);
  if (!mensaje.id || !pendientes.has(mensaje.id)) return;
  const promesa = pendientes.get(mensaje.id);
  pendientes.delete(mensaje.id);
  if (mensaje.error) promesa.rechazar(new Error(mensaje.error.message));
  else promesa.resolver(mensaje.result);
});

function enviar(method, params = {}) {
  return new Promise((resolver, rechazar) => {
    const id = ++secuencia;
    pendientes.set(id, { resolver, rechazar });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function esperar(ms) {
  await new Promise((resolver) => setTimeout(resolver, ms));
}

async function evaluar(expression) {
  const respuesta = await enviar("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  return respuesta.result.value;
}

await enviar("Page.enable");
await enviar("Runtime.enable");
await enviar("Emulation.setDeviceMetricsOverride", {
  width: ancho,
  height: alto,
  deviceScaleFactor: 1,
  mobile: false,
});
await enviar("Page.navigate", { url });

const limite = Date.now() + 45_000;
let texto = "";
while (Date.now() < limite) {
  texto = await evaluar("document.body?.innerText || ''");
  const cargando = await evaluar(
    "Boolean(document.querySelector('[data-testid=\"stSkeleton\"]'))",
  );
  if (texto.includes(textoEsperado) && !cargando) break;
  await esperar(500);
}
if (!texto.includes(textoEsperado)) {
  throw new Error(`La página no mostró el texto esperado: ${textoEsperado}`);
}

await evaluar("document.fonts?.ready || Promise.resolve()");
await esperar(5_000);
const selectorClick = process.env.CDP_CLICK_SELECTOR;
if (selectorClick) {
  const encontrado = await evaluar(`(() => {
    const elemento = document.querySelector(${JSON.stringify(selectorClick)});
    if (!elemento) return false;
    elemento.click();
    return true;
  })()`);
  if (!encontrado) throw new Error(`No se encontró el selector para la captura: ${selectorClick}`);
  await esperar(Number(process.env.CDP_AFTER_CLICK_MS || 1_000));
}
const captura = await enviar("Page.captureScreenshot", {
  format: "png",
  fromSurface: true,
  captureBeyondViewport: false,
});
await mkdir(dirname(destino), { recursive: true });
await writeFile(destino, Buffer.from(captura.data, "base64"));

const diagnostico = await evaluar(`({
  title: document.title,
  width: innerWidth,
  height: innerHeight,
  scrollWidth: document.documentElement.scrollWidth,
  scrollHeight: document.documentElement.scrollHeight,
  text: document.body.innerText.slice(0, 1200),
  boxes: Object.fromEntries([
    ['headerStreamlit', '[data-testid="stHeader"]'],
    ['contenedor', '.block-container'],
    ['navegacion', '.ref-nav'],
    ['mapaCabecera', '.mapa-cabecera'],
    ['hero', '.ref-hero'],
    ['sidebar', '[data-testid="stSidebar"]']
  ].map(([name, selector]) => {
    const element = document.querySelector(selector);
    if (!element) return [name, null];
    const box = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return [name, {x: box.x, y: box.y, width: box.width, height: box.height,
      paddingTop: style.paddingTop, marginTop: style.marginTop, position: style.position}];
  }))
})`);
console.log(JSON.stringify({ archivo: destino, ...diagnostico }, null, 2));

socket.close();
await fetch(`${baseCdp}/json/close/${objetivo.id}`);
