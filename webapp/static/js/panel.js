(async function () {
  const {api, escapeHtml: esc, hectares, number, readPortalState, writePortalState, toast} = window.CHCP;
  if (!window.L) return;
  const params = new URLSearchParams(window.location.search);
  const stored = readPortalState();
  let territoryId = params.get('territory') || stored.territoryId || 'cuenca:chcp';
  let summary = null;
  let activeTab = 'summary';
  let searchTimer;
  let searchItems = [];
  let activeSearchIndex = -1;
  const map = L.map('panel-map', {preferCanvas:true});
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {attribution:'Esri Light Gray Canvas',maxZoom:16}).addTo(map);
  let territoryLayer;

  function notCalculated(title) {
    return `<div class="not-calculated"><span>No calculado</span><h3>${esc(title)}</h3><p>Este panel no inventa valores precalculados. Ejecute un análisis para obtener un resultado científico con fuente, años y parámetros documentados.</p><a class="btn btn-p" href="/platform?territory=${encodeURIComponent(territoryId)}">Configurar análisis</a></div>`;
  }
  function renderTab() {
    const view = document.getElementById('territory-tab-view');
    if (!summary) { view.innerHTML = '<div class="panel-skeleton">Cargando territorio…</div>'; return; }
    if (activeTab === 'summary') {
      view.innerHTML = `<div class="panel-summary-copy"><h2>Consulta territorial inmediata</h2><p>El área y las intersecciones con referencias locales se calculan sin ejecutar Earth Engine. Los indicadores forestales permanecen como «No calculado» hasta iniciar un análisis.</p><dl><dt>Fuente territorial</dt><dd>${esc(summary.metadata.source)}</dd><dt>Sistema de referencia</dt><dd>${esc(summary.metadata.crs)}</dd><dt>Área</dt><dd>Calculada en ${esc(summary.metadata.area_crs)}</dd></dl></div>`;
    } else if (activeTab === 'corridors') {
      view.innerHTML = `<div class="panel-summary-copy"><h2>Corredores publicados</h2><p>${summary.corridors.count ? `${summary.corridors.count} referencia(s) espacial(es) intersectan el territorio.` : 'No se identificaron intersecciones con los corredores locales publicados.'}</p>${summary.corridors.names.length ? `<ul>${summary.corridors.names.map((name) => `<li>${esc(name)}</li>`).join('')}</ul>` : ''}<p class="method-note">La intersección geométrica no demuestra conectividad funcional para una especie.</p></div>`;
    } else {
      const labels = {coverage:'Cobertura forestal',fragmentation:'Fragmentación',connectivity:'Conectividad estructural',eri:'ERI complementario',temporal:'Comparación temporal',concordance:'Concordancia JRC + ESRI'};
      view.innerHTML = notCalculated(labels[activeTab]);
    }
  }
  function renderSummary() {
    document.getElementById('panel-territory-name').textContent = summary.territory.nombre;
    document.getElementById('panel-territory-group').textContent = summary.territory.tipo === 'cuenca' ? 'Cuenca principal · consulta territorial' : `${summary.territory.grupo || 'CHCP'} · subcuenca`;
    document.getElementById('panel-analyze').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
    document.getElementById('territory-kpis').innerHTML = [
      ['Superficie', hectares(summary.area_ha), `${number(summary.area_km2,2)} km²`],
      ['Corredores presentes', number(summary.corridors.count,0), 'Referencias con intersección'],
      ['Puntos críticos', number(summary.critical_points,0), 'Puntos publicados dentro'],
      ['Indicadores científicos', 'No calculado', 'Requiere fuente y período'],
    ].map(([label,value,note]) => `<article><span>${esc(label)}</span><b>${esc(value)}</b><small>${esc(note)}</small></article>`).join('');
    document.getElementById('territory-facts').innerHTML = `<b>${esc(summary.territory.nombre)}</b><span>${hectares(summary.area_ha)}</span><small>${esc(summary.scientific_indicators.message)}</small>`;
    if (territoryLayer) map.removeLayer(territoryLayer);
    territoryLayer = L.geoJSON(summary.geometry, {style:{color:'#0a4393',weight:3,fillColor:'#77cc09',fillOpacity:.12}}).addTo(map);
    map.fitBounds(territoryLayer.getBounds(), {padding:[24,24],maxZoom:13});
    renderTab();
  }
  async function selectTerritory(item) {
    territoryId = item.id;
    writePortalState({territoryId:item.id,territoryName:item.nombre,territoryType:item.tipo});
    history.replaceState({},'',`/panel?territory=${encodeURIComponent(item.id)}`);
    await loadSummary();
  }
  async function loadSummary() {
    try { summary = await api(`/api/v1/territories/${encodeURIComponent(territoryId)}/summary`); renderSummary(); }
    catch (error) { toast(error.message,'error'); }
  }
  const search = document.getElementById('panel-search');
  const results = document.getElementById('panel-search-results');
  function closeSearch() {
    results.hidden = true;
    search.setAttribute('aria-expanded','false');
    search.removeAttribute('aria-activedescendant');
    activeSearchIndex = -1;
  }
  function activateSearch(index) {
    const buttons = Array.from(results.querySelectorAll('[data-index]'));
    if (!buttons.length) return;
    activeSearchIndex = (index + buttons.length) % buttons.length;
    buttons.forEach((button,itemIndex) => button.setAttribute('aria-selected',String(itemIndex === activeSearchIndex)));
    const button = buttons[activeSearchIndex];
    button.id = `panel-search-option-${activeSearchIndex}`;
    search.setAttribute('aria-activedescendant',button.id);
    button.scrollIntoView({block:'nearest'});
  }
  function chooseSearch(index) {
    const item = searchItems[index];
    if (!item) return;
    closeSearch();
    search.value = '';
    selectTerritory(item);
  }
  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
      if (search.value.trim().length < 2) { results.hidden = true; return; }
      const response = await api(`/api/v1/territories/search?q=${encodeURIComponent(search.value.trim())}`);
      searchItems = response.results;
      activeSearchIndex = -1;
      results.innerHTML = searchItems.length ? searchItems.map((item,index) => `<button type="button" role="option" data-index="${index}" aria-selected="false"><span>${esc(item.nombre)}</span><small>${esc(item.tipo)}</small></button>`).join('') : '<div class="territory-no-results">No hay coincidencias.</div>';
      results.hidden = false;
      search.setAttribute('aria-expanded','true');
      results.querySelectorAll('[data-index]').forEach((button) => button.addEventListener('click', () => chooseSearch(Number(button.dataset.index))));
    },180);
  });
  search.addEventListener('keydown',(event) => {
    if (event.key === 'ArrowDown') { event.preventDefault(); activateSearch(activeSearchIndex + 1); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); activateSearch(activeSearchIndex - 1); }
    else if (event.key === 'Enter' && activeSearchIndex >= 0) { event.preventDefault(); chooseSearch(activeSearchIndex); }
    else if (event.key === 'Escape') closeSearch();
  });
  document.querySelectorAll('[data-territory-tab]').forEach((button) => button.addEventListener('click', () => {
    activeTab = button.dataset.territoryTab;
    document.querySelectorAll('[data-territory-tab]').forEach((item) => item.setAttribute('aria-selected',String(item===button)));
    renderTab();
  }));
  document.getElementById('panel-draw').addEventListener('click', () => window.location.assign('/platform?draw=1'));
  await loadSummary();
})();
