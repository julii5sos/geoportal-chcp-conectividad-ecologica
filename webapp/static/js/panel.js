(async function () {
  const {api, escapeHtml: esc, hectares, number, readPortalState, writePortalState, toast} = window.CHCP;
  if (!window.L) return;
  const params = new URLSearchParams(window.location.search);
  const stored = readPortalState();
  let territoryId = params.get('territory') || stored.territoryId || 'cuenca:chcp';
  let summary = null;
  let currentResult = null;
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
  function temporalParts() {
    if (!currentResult?.result) return null;
    const root = currentResult.result;
    const result = root.mode === 'integrated' ? root.sources?.jrc_tmf : root;
    if (!result?.estadisticas_cobertura) return null;
    const yi = String(result.anio_inicial);
    const yf = String(result.anio_final);
    return {root, result, yi, yf, stats:result.estadisticas_cobertura, initial:result.estadisticas_cobertura.periodos[yi], final:result.estadisticas_cobertura.periodos[yf], comparison:result.estadisticas_cobertura.comparacion, ri:result.periodos?.[yi]?.resumen, rf:result.periodos?.[yf]?.resumen};
  }
  function metric(label,value,note='') { return `<article class="metric-card"><span>${esc(label)}</span><b>${esc(value)}</b><small>${esc(note)}</small></article>`; }
  function resultTab(key) {
    if (currentResult?.kind === 'complementary_evidence') {
      if (key !== 'evidence' && key !== 'coverage') return notCalculated(key);
      const source = currentResult.result || {};
      const cards = Object.entries(source.statistics || {}).filter(([,value]) => !Array.isArray(value) && typeof value !== 'object').map(([label,value]) => metric(label.replaceAll('_',' '), typeof value === 'number' ? number(value,3) : value ?? 'Sin datos', source.source)).join('');
      return `<div class="metric-grid">${cards || metric('Estado','Sin observaciones válidas',source.source || '')}</div><p class="method-note">${esc(source.method || '')}</p><ul class="warning-list">${(source.limitations || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul>`;
    }
    const p = temporalParts();
    if (!p) return notCalculated(key);
    if (key === 'coverage' || key === 'temporal') return `<div class="metric-grid">${metric(`Bosque ${p.yi}`,hectares(p.initial.bosque_ha),`${number(p.initial.porcentaje_bosque,1)} %`)}${metric(`Bosque ${p.yf}`,hectares(p.final.bosque_ha),`${number(p.final.porcentaje_bosque,1)} %`)}${metric('Cambio neto',hectares(p.comparison.cambio_neto_bosque_ha),`${p.yi}–${p.yf}`)}${metric('Pérdida detectada',hectares(p.comparison.perdida_bosque_ha),currentResult.result.fuente?.nombre || '')}</div>`;
    if (key === 'fragmentation') return `<div class="metric-grid">${metric(`Parches ${p.yi}`,number(p.ri?.numero_parches,0),'Misma área y parámetros')}${metric(`Parches ${p.yf}`,number(p.rf?.numero_parches,0),'Misma área y parámetros')}${metric('Área media final',hectares(p.rf?.area_media_parche_ha || 0),`Año ${p.yf}`)}${metric('Densidad final',number(p.rf?.densidad_parches_100ha,2),'parches / 100 ha')}</div>`;
    if (key === 'connectivity') return `<div class="metric-grid">${metric(`Componentes ${p.yi}`,number(p.ri?.numero_componentes,0),'Conectividad estructural')}${metric(`Componentes ${p.yf}`,number(p.rf?.numero_componentes,0),'Conectividad estructural')}${metric('Parches aislados final',number(p.rf?.parches_aislados,0),`Umbral ${number(p.result.parametros?.distancia_maxima_m || 0,0)} m`)}${metric('Aristas finales',number(p.rf?.numero_aristas,0),'Proximidad entre bordes')}</div><p class="method-note">Estas relaciones no demuestran desplazamiento de fauna.</p>`;
    if (key === 'concordance' && p.root.mode === 'integrated') return `<div class="metric-grid">${metric('Concordancia de estado',`${number(p.root.concordance?.estado?.concordancia_pct,1)} %`,'JRC y ESRI')}${metric('Diferencia final',hectares(p.root.concordance?.diferencia_superficie_forestal_final_ha || 0),'JRC menos ESRI')}</div>`;
    if (key === 'eri') return notCalculated('ERI complementario');
    return notCalculated(key);
  }
  function renderTab() {
    const view = document.getElementById('territory-tab-view');
    if (!summary) { view.innerHTML = '<div class="panel-skeleton">Cargando territorio…</div>'; return; }
    if (activeTab === 'summary') {
      view.innerHTML = `<div class="panel-summary-copy"><h2>Consulta territorial inmediata</h2><p>El área y las intersecciones con referencias locales se calculan sin ejecutar Earth Engine. Los indicadores forestales permanecen como «No calculado» hasta iniciar un análisis.</p><dl><dt>Fuente territorial</dt><dd>${esc(summary.metadata.source)}</dd><dt>Sistema de referencia</dt><dd>${esc(summary.metadata.crs)}</dd><dt>Área</dt><dd>Calculada en ${esc(summary.metadata.area_crs)}</dd></dl></div>`;
    } else if (activeTab === 'corridors') {
      const context = summary.corridor_analysis || {};
      const calculated = currentResult ? resultTab('connectivity') : notCalculated('Fragmentación y conectividad dentro del corredor');
      view.innerHTML = `<div class="panel-summary-copy"><h2>Corredores publicados</h2><div class="metric-grid">${metric('Área en corredores',hectares(context.area_en_corredores_ha || 0),`${number(context.porcentaje_aoi_en_corredores || 0,1)} % del territorio`)}${metric('Distancia al más cercano',context.distancia_corredor_mas_cercano_m == null ? '—' : `${number(context.distancia_corredor_mas_cercano_m,0)} m`,'Distancia geométrica')}</div><p>${summary.corridors.count ? `${summary.corridors.count} referencia(s) espacial(es) intersectan el territorio.` : 'No se identificaron intersecciones.'}</p>${summary.corridors.names.length ? `<ul>${summary.corridors.names.map((name) => `<li>${esc(name)}</li>`).join('')}</ul>` : ''}<p class="method-note">Fuente: ${esc(context.fuente || summary.metadata.corridor_source)}. La superposición no demuestra conectividad funcional.</p><h3>Métricas modeladas</h3>${calculated}</div>`;
    } else {
      const labels = {coverage:'Cobertura forestal',evidence:'Vegetación y estructura',fragmentation:'Fragmentación',connectivity:'Conectividad estructural',eri:'ERI complementario',temporal:'Comparación temporal',concordance:'Concordancia JRC + ESRI'};
      view.innerHTML = currentResult ? resultTab(activeTab) : notCalculated(labels[activeTab]);
    }
  }
  function renderSummary() {
    document.getElementById('panel-territory-name').textContent = summary.territory.nombre;
    document.getElementById('panel-territory-group').textContent = summary.territory.tipo === 'cuenca' ? 'Cuenca principal · consulta territorial' : `${summary.territory.grupo || 'CHCP'} · subcuenca`;
    document.getElementById('panel-analyze').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
    document.getElementById('panel-custom-analysis').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
    document.getElementById('territory-kpis').innerHTML = [
      ['Superficie', hectares(summary.area_ha), `${number(summary.area_km2,2)} km²`],
      ['Corredores presentes', number(summary.corridors.count,0), 'Referencias con intersección'],
      ['Puntos críticos', number(summary.critical_points,0), 'Puntos publicados dentro'],
      ['Indicadores científicos', currentResult ? 'Disponible' : 'No calculado', currentResult ? (currentResult.kind === 'complementary_evidence' ? currentResult.result.source : `${currentResult.result.anio_inicial}–${currentResult.result.anio_final}`) : 'Requiere fuente y período'],
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
    currentResult = null;
    history.replaceState({},'',`/panel?territory=${encodeURIComponent(item.id)}`);
    await loadSummary();
  }
  async function loadAvailableResult() {
    const state = readPortalState();
    const provenance = document.getElementById('result-provenance');
    if (state.analysisTerritoryId === territoryId && state.analysisStatus === 'processing') {
      currentResult = null;
      provenance.hidden = false;
      provenance.innerHTML = `<b>Procesando</b><span>${esc(state.analysisLabel || 'Análisis científico')}</span><small>Los valores anteriores no se mostrarán como si pertenecieran al cálculo activo.</small><a href="/platform?territory=${encodeURIComponent(territoryId)}">Ver progreso</a>`;
      return;
    }
    if (state.analysisTerritoryId === territoryId && state.analysisStatus === 'error') {
      currentResult = null;
      provenance.hidden = false;
      provenance.innerHTML = `<b>Error de procesamiento</b><span>${esc(state.analysisError || 'No se pudo completar el análisis.')}</span><small>Revise los parámetros o intente nuevamente.</small><a href="/platform?territory=${encodeURIComponent(territoryId)}">Revisar</a>`;
      return;
    }
    const currentParams = new URLSearchParams(window.location.search);
    const requestedId = currentParams.get('result') || (state.resultTerritoryId === territoryId ? state.resultId : null);
    try {
      if (requestedId) currentResult = await api(`/api/v1/results/${encodeURIComponent(requestedId)}`);
      else {
        const latest = await api(`/api/v1/territories/${encodeURIComponent(territoryId)}/results/latest`);
        currentResult = latest.result || null;
      }
    } catch (error) {
      if (error.status !== 404) toast(error.message,'error');
      currentResult = null;
    }
    provenance.hidden = !currentResult;
    if (currentResult) {
      const period = currentResult.kind === 'complementary_evidence' ? (currentResult.result.period?.year || [currentResult.result.period?.initial,currentResult.result.period?.final].filter(Boolean).join('–') || 'Referencia fija') : `${currentResult.result.anio_inicial}–${currentResult.result.anio_final}`;
      provenance.innerHTML = `<b>Resultado disponible</b><span>${esc(currentResult.area.label)} · ${esc(period)}</span><small>Procesado ${esc(new Date(currentResult.created_utc).toLocaleString('es-PA'))} · ID ${esc(currentResult.result_id.slice(0,8))}</small><a href="/api/v1/results/${encodeURIComponent(currentResult.result_id)}/download.zip">Descargar</a>`;
    }
  }
  async function loadSummary() {
    try { summary = await api(`/api/v1/territories/${encodeURIComponent(territoryId)}/summary`); await loadAvailableResult(); renderSummary(); }
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
  document.getElementById('panel-custom-analysis').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
  window.addEventListener('storage', async (event) => { if (event.key === 'chcp.portal-state.v1') await loadSummary(); });
  await loadSummary();
})();
