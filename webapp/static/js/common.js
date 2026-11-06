(function () {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const number = (value, digits = 1) => new Intl.NumberFormat('es-PA', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(Number(value || 0));
  const hectares = (value, digits = 1) => `${number(value, digits)} ha`;

  async function api(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: {'Content-Type': 'application/json', ...(options.headers || {})},
    });
    const type = response.headers.get('content-type') || '';
    const body = type.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const error = new Error(body?.error || `La solicitud falló (${response.status}).`);
      error.status = response.status;
      error.details = body?.details;
      error.supportId = body?.support_id;
      throw error;
    }
    return body;
  }

  function toast(message, kind = 'info') {
    let element = $('.toast');
    if (!element) {
      element = document.createElement('div');
      element.className = 'toast';
      element.setAttribute('role', kind === 'error' ? 'alert' : 'status');
      document.body.appendChild(element);
    }
    element.textContent = message;
    element.dataset.kind = kind;
    element.hidden = false;
    clearTimeout(element._timer);
    element._timer = setTimeout(() => { element.hidden = true; }, 4500);
  }

  const burger = $('#burger');
  const links = $('#links');
  burger?.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
  });

  window.CHCP = {$, $$, escapeHtml, number, hectares, api, toast};
})();

