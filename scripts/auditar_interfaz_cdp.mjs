import { spawn } from 'node:child_process';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const chrome = process.argv[2];
const url = process.argv[3];
const outputDir = resolve(process.argv[4] || 'docs/capturas');
const port = Number(process.argv[5] || 9333);

if (!chrome || !url) {
  throw new Error('Uso: node auditar_interfaz_cdp.mjs <chrome> <url> [salida] [puerto]');
}

await mkdir(outputDir, { recursive: true });
const profile = await mkdtemp(join(tmpdir(), 'chcp-cdp-'));
const browser = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--disable-default-apps',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--window-size=1920,1080', url,
], { stdio: ['ignore', 'ignore', 'pipe'] });

const sleep = (ms) => new Promise((resolvePromise) => setTimeout(resolvePromise, ms));

async function waitForJson(endpoint, attempts = 80) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(endpoint);
      if (response.ok) return await response.json();
    } catch (error) {
      lastError = error;
    }
    await sleep(125);
  }
  throw lastError || new Error(`No respondió ${endpoint}`);
}

class Cdp {
  constructor(socket) {
    this.socket = socket;
    this.sequence = 0;
    this.pending = new Map();
    this.events = [];
    socket.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve: resolvePending, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(message.error.message));
        else resolvePending(message.result || {});
      } else if (message.method) {
        this.events.push(message);
      }
    });
  }

  send(method, params = {}) {
    const id = ++this.sequence;
    return new Promise((resolvePending, reject) => {
      this.pending.set(id, { resolve: resolvePending, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', {
      expression, awaitPromise: true, returnByValue: true,
    });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || 'Fallo al evaluar JavaScript');
    return result.result?.value;
  }
}

async function capture(cdp, filename) {
  const screenshot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const path = join(outputDir, filename);
  await writeFile(path, Buffer.from(screenshot.data, 'base64'));
  return path;
}

let cdp;
try {
  const targets = await waitForJson(`http://127.0.0.1:${port}/json/list`);
  const target = targets.find((item) => item.type === 'page');
  if (!target?.webSocketDebuggerUrl) throw new Error('Chrome no expuso una pestaña inspeccionable.');

  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolveSocket, reject) => {
    socket.addEventListener('open', resolveSocket, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  cdp = new Cdp(socket);
  await Promise.all([
    cdp.send('Page.enable'), cdp.send('Runtime.enable'), cdp.send('Network.enable'), cdp.send('Log.enable'),
  ]);
  await sleep(9000);

  const snapshotExpression = `(() => {
    const visible = (node) => Boolean(node && !node.hidden && getComputedStyle(node).display !== 'none' && getComputedStyle(node).visibility !== 'hidden');
    const selectedResultTab = document.querySelector('[data-result-tab][aria-selected="true"]');
    return {
      title: document.title,
      viewport: { width: innerWidth, height: innerHeight, deviceScaleFactor: devicePixelRatio },
      document: { scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight },
      overflowX: document.documentElement.scrollWidth > innerWidth,
      columns: {
        left: visible(document.querySelector('#left-panel')),
        map: visible(document.querySelector('#smap')),
        results: visible(document.querySelector('#results-panel')),
      },
      resultsTitle: document.querySelector('#results-title')?.textContent?.trim(),
      resultsSubtitle: document.querySelector('#results-subtitle')?.textContent?.trim(),
      selectedResultTab: selectedResultTab?.dataset.resultTab || null,
      resultTabs: [...document.querySelectorAll('[data-result-tab]')].map((node) => node.textContent.trim()),
      toggles: document.querySelectorAll('input[type="checkbox"]').length,
      activeToggles: document.querySelectorAll('input[type="checkbox"]:checked').length,
      mapPaths: document.querySelectorAll('.leaflet-overlay-pane path').length,
      scale: document.querySelector('.leaflet-control-scale-line')?.textContent?.trim() || null,
      charts: [...document.querySelectorAll('.chart-card')].filter(visible).map((node) => node.innerText.trim()),
      metrics: [...document.querySelectorAll('.metric-card')].filter(visible).map((node) => node.innerText.trim()),
      interpretations: [...document.querySelectorAll('.interpretation')].filter(visible).map((node) => node.innerText.trim()),
      pdfHref: document.querySelector('a[href*="report.pdf"]')?.getAttribute('href') || null,
      downloadHref: document.querySelector('a[href*="download.zip"]')?.getAttribute('href') || null,
    };
  })()`;

  const initial = await cdp.evaluate(snapshotExpression);
  const initialScreenshot = await capture(cdp, 'auditoria_cdp_resumen.png');
  const analyticalBeforeTabs = cdp.events.filter((event) => event.method === 'Network.requestWillBeSent' && /\/api\/v1\/(analyses|evaluations|structural-connectivity|eri)/.test(event.params.request.url)).length;

  const forestClick = await cdp.evaluate(`(() => {
    const button = document.querySelector('[data-result-tab="forest"]');
    if (!button) return false;
    button.click();
    return true;
  })()`);
  await sleep(500);
  const forest = await cdp.evaluate(snapshotExpression);
  const forestScreenshot = await capture(cdp, 'auditoria_cdp_dinamica_bosque.png');

  const connectivityClick = await cdp.evaluate(`(() => {
    const button = document.querySelector('[data-result-tab="connectivity"]');
    if (!button) return false;
    button.click();
    return true;
  })()`);
  await sleep(500);
  const connectivity = await cdp.evaluate(snapshotExpression);
  const connectivityScreenshot = await capture(cdp, 'auditoria_cdp_conectividad.png');

  const toggleDisabled = await cdp.evaluate(`(() => {
    const input = document.querySelector('input[data-layer="corridors"]');
    if (!input) return { found: false };
    const before = { checked: input.checked };
    input.click();
    return { found: true, before, after: { checked: input.checked } };
  })()`);
  await sleep(800);
  const corridorsDisabledScreenshot = await capture(cdp, 'auditoria_cdp_corredores_apagados.png');
  const toggleRestored = await cdp.evaluate(`(() => {
    const input = document.querySelector('input[data-layer="corridors"]');
    if (!input) return { found: false };
    const before = { checked: input.checked };
    input.click();
    return { found: true, before, after: { checked: input.checked } };
  })()`);
  await sleep(800);
  const corridorsRestoredScreenshot = await capture(cdp, 'auditoria_cdp_corredores_encendidos.png');

  const leftTabs = await cdp.evaluate(`(() => {
    const result = {};
    for (const name of ['filters', 'basemaps', 'layers']) {
      const button = document.querySelector('.side-tabs [data-panel="' + name + '"]');
      button?.click();
      result[name] = {
        selected: button?.getAttribute('aria-selected'),
        visible: !document.querySelector('#panel-' + name)?.hidden,
      };
    }
    return result;
  })()`);

  const wizard = await cdp.evaluate(`(() => {
    document.querySelector('#open-analysis')?.click();
    const modal = document.querySelector('#analysis-modal');
    const result = {
      visible: Boolean(modal && !modal.hidden),
      title: document.querySelector('#analysis-title')?.textContent?.trim(),
      stepLabels: [...document.querySelectorAll('#wizard-steps li')].map((node) => node.textContent.trim()),
      options: [...document.querySelectorAll('input[name="analysis-component"]')].map((node) => node.value),
    };
    document.querySelector('#modal-close')?.click();
    return result;
  })()`);

  const analyticalAfterTabs = cdp.events.filter((event) => event.method === 'Network.requestWillBeSent' && /\/api\/v1\/(analyses|evaluations|structural-connectivity|eri)/.test(event.params.request.url)).length;
  const failedRequests = cdp.events.filter((event) => event.method === 'Network.loadingFailed').map((event) => ({
    url: event.params.url || null, errorText: event.params.errorText, canceled: event.params.canceled || false,
  }));
  const badResponses = cdp.events.filter((event) => event.method === 'Network.responseReceived' && event.params.response.status >= 400).map((event) => ({
    status: event.params.response.status, url: event.params.response.url,
  }));
  const consoleMessages = cdp.events.filter((event) => event.method === 'Runtime.consoleAPICalled').map((event) => ({
    type: event.params.type, text: event.params.args.map((arg) => arg.value ?? arg.description ?? '').join(' '),
  }));
  const exceptions = cdp.events.filter((event) => event.method === 'Runtime.exceptionThrown').map((event) => event.params.exceptionDetails?.text || 'Excepción JavaScript');

  const responsive = [];
  for (const [width, height] of [[1920,1080],[1440,900],[1366,768],[1024,768],[536,800],[375,667]]) {
    await cdp.send('Emulation.setDeviceMetricsOverride', {width, height, deviceScaleFactor: 1, mobile: false});
    await cdp.evaluate(`(() => { window.dispatchEvent(new Event('resize')); return true; })()`);
    await sleep(350);
    const layout = await cdp.evaluate(`(() => ({
      viewport: {width: innerWidth, height: innerHeight},
      document: {width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight},
      overflowX: document.documentElement.scrollWidth > innerWidth + 1,
      columnsVisible: ['left-panel','smap','results-panel'].filter((id) => {
        const node = document.getElementById(id); return node && getComputedStyle(node).display !== 'none';
      }),
    }))()`);
    const screenshot = await capture(cdp, `auditoria_responsive_${width}x${height}.png`);
    responsive.push({width, height, ...layout, screenshot});
  }

  const report = {
    url, initial, interactions: {
      forestClick, forest, connectivityClick, connectivity, toggleDisabled, toggleRestored, leftTabs, wizard,
      analyticalRequestsTriggeredByTabs: analyticalAfterTabs - analyticalBeforeTabs,
    },
    diagnostics: { failedRequests, badResponses, consoleMessages, exceptions },
    responsive,
    screenshots: {
      initialScreenshot, forestScreenshot, connectivityScreenshot,
      corridorsDisabledScreenshot, corridorsRestoredScreenshot,
    },
  };
  await writeFile(join(outputDir, 'auditoria_cdp_resultado.json'), JSON.stringify(report, null, 2), 'utf8');
  console.log(JSON.stringify(report, null, 2));
  socket.close();
} finally {
  browser.kill();
  await sleep(250);
  await rm(profile, { recursive: true, force: true });
}
