(async function () {
  const {api, toast, escapeHtml: esc, writePortalState} = window.CHCP;
  const element = document.getElementById('home-map');
  if (!element || !window.L) return;
  const map = L.map(element, {zoomControl: true, attributionControl: true, preferCanvas: true});
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri Light Gray Canvas', maxZoom: 16,
  }).addTo(map);
  try {
    const territory = await api('/api/v1/territory');
    const basin = L.geoJSON(territory.basin, {style: {color: '#0a4393', weight: 3, fillColor: '#0a4393', fillOpacity: .08}}).addTo(map);
    L.geoJSON(territory.subbasins, {style: {color: '#77cc09', weight: 1, fillOpacity: 0}, onEachFeature: (feature, layer) => layer.bindTooltip(feature.properties?.nombre || 'Subcuenca')}).addTo(map);
    map.fitBounds(basin.getBounds(), {padding: [16, 16]});
  } catch (error) {
    map.setView([9.1, -79.7], 9);
    toast('No se pudo cargar el límite territorial.', 'error');
  }

  const input = document.getElementById('territory-query');
  const results = document.getElementById('territory-results');
  const status = document.getElementById('territory-search-status');
  const spinner = document.getElementById('territory-search-spinner');
  let choices = [];
  let active = -1;
  let timer;

  function closeResults() {
    results.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    active = -1;
  }
  function choose(item) {
    writePortalState({territoryId: item.id, territoryName: item.nombre, territoryType: item.tipo});
    window.location.assign(`/panel?territory=${encodeURIComponent(item.id)}`);
  }
  function renderChoices() {
    if (!choices.length) {
      results.innerHTML = '<div class="territory-no-results">No hay coincidencias. Pruebe con una parte del nombre, por ejemplo «Río» o «Lago».</div>';
      status.textContent = 'No se encontraron territorios reales con ese texto.';
    } else {
      results.innerHTML = choices.map((item, index) => `<button id="territory-option-${index}" type="button" role="option" aria-selected="${index === active}" data-index="${index}"><span>${esc(item.nombre)}</span><small>${esc(item.tipo === 'cuenca' ? 'Cuenca principal' : item.grupo || 'Subcuenca')}</small></button>`).join('');
      status.textContent = `${choices.length} coincidencia${choices.length === 1 ? '' : 's'}. Use las flechas y Enter para seleccionar.`;
      results.querySelectorAll('[data-index]').forEach((button) => button.addEventListener('click', () => choose(choices[Number(button.dataset.index)])));
    }
    results.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }
  async function search() {
    const query = input.value.trim();
    if (query.length < 2) { closeResults(); status.textContent = 'Escriba al menos dos caracteres.'; return; }
    spinner.hidden = false;
    status.textContent = 'Buscando territorios…';
    try {
      const response = await api(`/api/v1/territories/search?q=${encodeURIComponent(query)}`);
      choices = response.results;
      active = choices.length ? 0 : -1;
      renderChoices();
    } catch (error) {
      closeResults();
      status.textContent = 'No fue posible consultar el catálogo territorial.';
    } finally { spinner.hidden = true; }
  }
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(search, 180); });
  input.addEventListener('keydown', (event) => {
    if (results.hidden || !choices.length) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      active = (active + (event.key === 'ArrowDown' ? 1 : -1) + choices.length) % choices.length;
      renderChoices();
      input.setAttribute('aria-activedescendant', `territory-option-${active}`);
    } else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); choose(choices[active]); }
    else if (event.key === 'Escape') closeResults();
  });
  document.addEventListener('click', (event) => { if (!document.getElementById('territory-search').contains(event.target)) closeResults(); });
})();

