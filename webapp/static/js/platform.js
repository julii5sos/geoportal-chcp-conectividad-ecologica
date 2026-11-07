(async function () {
  const { $, $$, escapeHtml: esc, number, hectares, api, toast, readPortalState, writePortalState } = window.CHCP;
  if (!window.L) return;

  const state = {
    config: null,
    territory: null,
    sourceCatalog: null,
    resultOpacity: .76,
    result: null,
    eri: null,
    resultLayers: new Map(),
    activeLayers: new Set(['basin']),
    areaLayer: null,
    drawnGeometry: null,
    drawing: false,
    drawingPoints: [],
    drawingMarkers: [],
    drawingLine: null,
    territoryId: null,
    requestSequence: 0,
    wizardStep: 0,
    wizard: {
      analyses: ['coverage', 'fragmentation', 'connectivity'],
      areaMode: 'draw',
      subbasin: '',
      source: 'jrc_tmf',
      initialYear: 2020,
      finalYear: 2025,
      maximumDistance: 500,
      minimumPatchArea: 0,
    },
  };

  const map = L.map('smap', { zoomControl: true, attributionControl: true, preferCanvas: true, doubleClickZoom: true });
  L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map);
  const baseMaps = {
    imagery: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: 'Esri World Imagery', maxZoom: 19 }),
    light: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', { attribution: 'Esri Light Gray Canvas', maxZoom: 16 }),
    osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OpenStreetMap', maxZoom: 19 }),
  };
  let currentBase = 'imagery';
  baseMaps[currentBase].addTo(map);
  map.setView([9.1, -79.7], 9);
  map.on('mousemove', (event) => { $('#coords').textContent = `lat ${event.latlng.lat.toFixed(4)} · lon ${event.latlng.lng.toFixed(4)}`; });

  function symColor(group, key, fallback) {
    return state.config?.symbology?.[group]?.[key]?.color || fallback;
  }

  function setBusy(on, title = 'Procesando') {
    const busy = $('#busy');
    busy.hidden = !on;
    if (!on) return;
    $('#busy-title').textContent = title;
    $('#busy-steps').innerHTML = ['Validando el área', 'Consultando Earth Engine', 'Calculando parches y red', 'Preparando resultados'].map((step, index) => `<li class="${index === 0 ? 'now' : ''}">${index === 0 ? '●' : '○'} ${step}</li>`).join('');
    $('#busy-bar').style.width = '16%';
    let index = 0;
    clearInterval(setBusy._timer);
    setBusy._timer = setInterval(() => {
      index = Math.min(3, index + 1);
      $('#busy-steps').innerHTML = ['Validando el área', 'Consultando Earth Engine', 'Calculando parches y red', 'Preparando resultados'].map((step, item) => `<li class="${item < index ? 'done' : item === index ? 'now' : ''}">${item < index ? '✓' : item === index ? '●' : '○'} ${step}</li>`).join('');
      $('#busy-bar').style.width = `${20 + index * 23}%`;
    }, 3500);
  }
  function stopBusy() { clearInterval(setBusy._timer); setBusy(false); }

  function layerStyle(key) {
    const styles = {
      basin: { color: '#0a4393', weight: 3, fillColor: '#0a4393', fillOpacity: .04 },
      subbasins: { color: '#77cc09', weight: 1, fillOpacity: 0 },
      area: { color: '#42d4f4', weight: 3, fillColor: '#42d4f4', fillOpacity: .06 },
      stable: { color: '#216e39', weight: .6, fillColor: '#2e7d32', fillOpacity: .65 },
      loss: { color: '#b42318', weight: .7, fillColor: '#e76f51', fillOpacity: .82 },
      gain: { color: '#147d64', weight: .7, fillColor: '#43aa8b', fillOpacity: .78 },
      noforest: { color: '#8a94a6', weight: .4, fillColor: '#d6deeb', fillOpacity: .3 },
      patchesInitial: { color: '#0f5f4f', weight: .6, fillColor: '#1f8a70', fillOpacity: .42 },
      patchesFinal: { color: '#062a5e', weight: .7, fillColor: '#3a7ca5', fillOpacity: .42 },
      connectionsInitial: { color: '#fabc20', weight: 2, opacity: .8 },
      connectionsFinal: { color: '#7a5195', weight: 2.2, opacity: .9 },
      corridors: { color: '#345a01', weight: 1.4, fillColor: '#a1d303', fillOpacity: .22 },
      criticalPoints: { color: '#b42318', weight: 2, fillColor: '#f04438', fillOpacity: .9, radius: 5 },
    };
    return styles[key] || styles.area;
  }

  function addResultLayer(key, name, geojson, color, active = false) {
    if (!geojson?.features?.length) return;
    const layer = L.geoJSON(geojson, {
      style: () => layerStyle(key),
      onEachFeature: (feature, item) => {
        const properties = feature.properties || {};
        const rows = Object.entries(properties).slice(0, 6).map(([label, value]) => `<b>${esc(label)}</b>: ${esc(value)}`).join('<br>');
        if (rows) item.bindTooltip(rows, { sticky: true, className: 'tt' });
      },
    });
    state.resultLayers.set(key, { key, name, layer, color });
    if (active) { layer.addTo(map); state.activeLayers.add(key); }
  }

  function addTileResultLayer(key, name, descriptor, active = false) {
    if (!descriptor?.tile_url) return;
    const classes = descriptor.classes || [];
    const layer = L.tileLayer(descriptor.tile_url, {
      opacity: state.resultOpacity,
      attribution: 'Google Earth Engine',
      maxZoom: 18,
    });
    state.resultLayers.set(key, {
      key,
      name,
      layer,
      color: classes[0]?.color || '#0a4393',
      legend: classes.map((item) => ({name: item.etiqueta, color: item.color})),
    });
    if (active) { layer.addTo(map); state.activeLayers.add(key); }
  }

  function clearResultLayers() {
    state.resultLayers.forEach(({layer}) => { if (map.hasLayer(layer)) map.removeLayer(layer); });
    state.resultLayers.clear();
    state.activeLayers = new Set(['basin']);
  }

  function toggleLayer(key, active) {
    const entry = state.resultLayers.get(key);
    if (!entry) return;
    if (active && !map.hasLayer(entry.layer)) entry.layer.addTo(map);
    if (!active && map.hasLayer(entry.layer)) map.removeLayer(entry.layer);
    active ? state.activeLayers.add(key) : state.activeLayers.delete(key);
    renderLegend();
  }

  function group(title, content, open = true) {
    return `<div class="lg ${open ? 'open' : ''}"><button type="button"><span>${title}</span><span class="cnt"></span><i class="chev"></i></button><div class="lg-items">${content}</div></div>`;
  }
  function layerRow(key, name, color, enabled = true, note = '') {
    const checked = state.activeLayers.has(key);
    return `<div class="ly ${enabled ? '' : 'layer-disabled'}"><div class="ly-h"><span class="tg"><input type="checkbox" data-layer="${key}" ${checked ? 'checked' : ''} ${enabled ? '' : 'disabled'} aria-label="Mostrar ${esc(name)}"><span></span></span><i class="layer-color" style="background:${color}"></i><label class="nm">${esc(name)}${note ? `<small>${esc(note)}</small>` : ''}</label></div></div>`;
  }

  function renderLayers() {
    const basinRows = layerRow('basin', 'Límite de la CHCP', '#0a4393', true, 'GeoJSON local') + layerRow('subbasins', 'Subcuencas del Canal', '#77cc09', true, `${state.territory?.subbasins?.features?.length || 0} unidades`);
    const corridorRows = layerRow('corridors', 'Corredores estratégicos publicados', '#a1d303', true, `${state.territory?.corridors?.features?.length || 0} polígonos`) + layerRow('criticalPoints', 'Puntos críticos publicados', '#f04438', true, `${state.territory?.critical_points?.features?.length || 0} puntos`);
    const temporalRows = state.resultLayers.size
      ? Array.from(state.resultLayers.values()).map((item) => layerRow(item.key, item.name, item.color, true, 'Resultado calculado')).join('')
      : layerRow('pending', 'Ejecute un análisis para habilitar resultados', '#d6deeb', false);
    const source = state.config?.sources?.[state.wizard.source];
    const sourceInfo = source ? `<div class="source-note"><b>${esc(source.nombre)}</b><br>${source.anio_inicial}–${source.anio_final} · ${source.resolucion_m} m<br>${esc(source.definicion_bosque)}</div>` : '';
    const complementaryRows = (state.sourceCatalog?.sources || [])
      .filter((item) => item.categoria.startsWith('B'))
      .map((item) => layerRow(`catalog-${item.clave}`, item.nombre_oficial, '#9aa7b8', false, item.estado_html))
      .join('');
    $('#panel-layers').innerHTML = group('Límites', basinRows) + group('Corredores publicados', corridorRows, false) + group('Cobertura y transiciones', temporalRows) + group('Fuente activa', sourceInfo, false) + (complementaryRows ? group('Fuentes complementarias', complementaryRows, false) : '') + group('ERI complementario', state.eri ? layerRow('eriTiles', 'Índice ERI indicativo', '#76b72a', state.resultLayers.has('eriTiles')) : layerRow('eriPending', 'Calcule el ERI desde Resultados', '#d6deeb', false), false);
    $$('#panel-layers .lg>button').forEach((button) => button.addEventListener('click', () => button.parentElement.classList.toggle('open')));
    $$('[data-layer]', $('#panel-layers')).forEach((input) => input.addEventListener('change', () => {
      const key = input.dataset.layer;
      if (key === 'basin') input.checked ? basinLayer.addTo(map) : map.removeLayer(basinLayer);
      else if (key === 'subbasins') input.checked ? subbasinLayer.addTo(map) : map.removeLayer(subbasinLayer);
      else if (key === 'corridors') input.checked ? corridorLayer.addTo(map) : map.removeLayer(corridorLayer);
      else if (key === 'criticalPoints') input.checked ? criticalPointLayer.addTo(map) : map.removeLayer(criticalPointLayer);
      else toggleLayer(key, input.checked);
      input.checked ? state.activeLayers.add(key) : state.activeLayers.delete(key);
      renderLegend();
    }));
  }

  function renderLegend() {
    const items = Array.from(state.activeLayers).map((key) => state.resultLayers.get(key)).filter(Boolean);
    const legend = $('#map-legend');
    if (!items.length) { legend.hidden = true; return; }
    legend.hidden = false;
    legend.innerHTML = `<span class="eyebrow">Capas visibles</span>${items.map((item) => item.legend?.length
      ? `<div class="legend-layer"><b>${esc(item.name)}</b>${item.legend.map((entry) => `<div class="legend-item"><i style="background:${entry.color}"></i>${esc(entry.name)}</div>`).join('')}</div>`
      : `<div class="legend-item"><i style="background:${item.color}"></i>${esc(item.name)}</div>`).join('')}`;
  }

  let basinLayer;
  let subbasinLayer;
  let corridorLayer;
  let criticalPointLayer;
  async function prepareCorridorFromMap(feature, layer) {
    const name = feature.properties?.nombre || 'Corredor publicado';
    try {
      const response = await api(`/api/v1/territories/search?q=${encodeURIComponent(name)}`);
      const item = (response.results || []).find((candidate) => candidate.tipo === 'corredor' && candidate.nombre === name);
      if (!item) throw new Error('El corredor no tiene un identificador territorial disponible.');
      state.territoryId = item.id;
      state.wizard.areaMode = 'draw';
      state.wizard.subbasin = '';
      state.drawnGeometry = feature.geometry;
      if (state.areaLayer) map.removeLayer(state.areaLayer);
      state.areaLayer = L.geoJSON(feature.geometry, {style: layerStyle('area')}).addTo(map);
      map.fitBounds(layer.getBounds(), {padding:[35,35],maxZoom:13});
      $('#selected-territory-id').textContent = `Territorio preparado: ${name}`;
      writePortalState({territoryId:item.id,territoryName:name,territoryType:'corredor'});
      updateAreaLabel();
      toast(`${name} quedó preparado para el análisis.`, 'success');
    } catch (error) {
      toast(`No se pudo preparar el corredor: ${error.message}`, 'error');
    }
  }
  function renderTerritory() {
    basinLayer = L.geoJSON(state.territory.basin, { style: layerStyle('basin') }).addTo(map);
    subbasinLayer = L.geoJSON(state.territory.subbasins, { style: layerStyle('subbasins'), onEachFeature: (feature, layer) => layer.bindTooltip(feature.properties?.nombre || 'Subcuenca') });
    corridorLayer = L.geoJSON(state.territory.corridors, {
      style: layerStyle('corridors'),
      onEachFeature: (feature, layer) => {
        layer.bindTooltip(`${feature.properties?.nombre || 'Corredor publicado'} · clic para analizar`);
        layer.on('click', () => prepareCorridorFromMap(feature, layer));
      },
    });
    criticalPointLayer = L.geoJSON(state.territory.critical_points, {
      pointToLayer: (feature, latlng) => L.circleMarker(latlng, layerStyle('criticalPoints')),
      onEachFeature: (feature, layer) => layer.bindTooltip(feature.properties?.nombre || feature.properties?.titulo || 'Punto crítico publicado'),
    });
    map.fitBounds(basinLayer.getBounds(), { padding: [18, 18] });
  }

  function renderBasemaps() {
    const choices = [
      ['imagery', 'Imagen satelital', 'linear-gradient(#365240 55%,#243d2c 55%)'],
      ['light', 'Mapa claro', 'linear-gradient(#e6ebf3 55%,#fff 55%)'],
      ['osm', 'OpenStreetMap', 'linear-gradient(#d9e9d2 55%,#f3ead8 55%)'],
    ];
    $('#basemap-list').innerHTML = choices.map(([key, name, background]) => `<button type="button" data-base="${key}" aria-pressed="${key === currentBase}"><i style="background:${background}"></i>${name}</button>`).join('');
    $$('[data-base]', $('#basemap-list')).forEach((button) => button.addEventListener('click', () => {
      if (button.dataset.base === currentBase) return;
      map.removeLayer(baseMaps[currentBase]);
      currentBase = button.dataset.base;
      baseMaps[currentBase].addTo(map);
      baseMaps[currentBase].bringToBack();
      renderBasemaps();
    }));
  }

  function selectYears(sourceKey, initialSelect, finalSelect) {
    const source = state.config.sources[sourceKey];
    const years = source.years;
    if (!years.includes(state.wizard.initialYear)) state.wizard.initialYear = Math.max(source.anio_inicial, source.anio_final - 5);
    if (!years.includes(state.wizard.finalYear)) state.wizard.finalYear = source.anio_final;
    if (state.wizard.initialYear >= state.wizard.finalYear) state.wizard.initialYear = years[Math.max(0, years.length - 2)];
    initialSelect.innerHTML = years.slice(0, -1).map((year) => `<option value="${year}" ${year === state.wizard.initialYear ? 'selected' : ''}>${year}</option>`).join('');
    finalSelect.innerHTML = years.slice(1).map((year) => `<option value="${year}" ${year === state.wizard.finalYear ? 'selected' : ''}>${year}</option>`).join('');
  }

  function renderQuickFilters() {
    const sourceSelect = $('#quick-source');
    sourceSelect.innerHTML = Object.values(state.config.sources).map((source) => `<option value="${source.clave}" ${source.clave === state.wizard.source ? 'selected' : ''}>${esc(source.nombre)}</option>`).join('');
    selectYears(state.wizard.source, $('#quick-initial-year'), $('#quick-final-year'));
    $('#quick-distance').value = String(state.wizard.maximumDistance);
    $('#layer-opacity').value = String(Math.round(state.resultOpacity * 100));
    $('#layer-opacity-value').textContent = `${Math.round(state.resultOpacity * 100)} %`;
    sourceSelect.onchange = () => { state.wizard.source = sourceSelect.value; selectYears(state.wizard.source, $('#quick-initial-year'), $('#quick-final-year')); renderLayers(); persistWizard(); };
    $('#quick-initial-year').onchange = (event) => { state.wizard.initialYear = Number(event.target.value); persistWizard(); };
    $('#quick-final-year').onchange = (event) => { state.wizard.finalYear = Number(event.target.value); persistWizard(); };
    $('#quick-distance').onchange = (event) => { state.wizard.maximumDistance = Number(event.target.value); persistWizard(); };
    $('#layer-opacity').oninput = (event) => {
      state.resultOpacity = Number(event.target.value) / 100;
      $('#layer-opacity-value').textContent = `${event.target.value} %`;
      state.resultLayers.forEach(({layer}) => {
        if (typeof layer.setOpacity === 'function') layer.setOpacity(state.resultOpacity);
        else if (typeof layer.setStyle === 'function') layer.setStyle({opacity:state.resultOpacity,fillOpacity:state.resultOpacity * .65});
      });
      writePortalState({resultOpacity:state.resultOpacity});
    };
    const evidenceSource = $('#evidence-source');
    const refreshEvidence = () => {
      const fixed = ['gedi','worldcover'].includes(evidenceSource.value);
      $('#evidence-years').hidden = fixed;
      $('#evidence-note').textContent = fixed ? 'Producto de referencia fija; no se fabrica una serie anual.' : evidenceSource.value === 'hansen_gfc' ? 'Pérdida anual 2001–2025; no equivale automáticamente a deforestación.' : 'Mediana anual con máscara SCL y respaldo del año anterior donde falten observaciones.';
      if (evidenceSource.value === 'sentinel_ndvi') { $('#evidence-initial').min='2017'; $('#evidence-final').max='2026'; }
      else { $('#evidence-initial').min='2001'; $('#evidence-final').max='2025'; }
    };
    evidenceSource.onchange = refreshEvidence;
    refreshEvidence();
    $('#run-evidence').onclick = runEvidence;
  }

  async function runEvidence() {
    if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { toast('Dibuje un polígono o seleccione un territorio antes de calcular.', 'error'); return; }
    const source = $('#evidence-source').value;
    const payload = {source, area:currentAreaRequest(), initial_year:Number($('#evidence-initial').value), final_year:Number($('#evidence-final').value), parameters:{tree_cover_threshold:30}, territory_id:state.territoryId};
    if (['gedi','worldcover'].includes(source)) { payload.initial_year = null; payload.final_year = null; }
    const sequence = ++state.requestSequence;
    writePortalState({analysisStatus:'processing',analysisTerritoryId:state.territoryId,analysisLabel:`${source} · evidencia complementaria`,analysisError:null});
    setBusy(true, 'Calculando evidencia complementaria');
    $('#run-evidence').disabled = true;
    try {
      const response = await api('/api/v1/evidence', {method:'POST', body:JSON.stringify(payload)});
      if (sequence !== state.requestSequence) {
        writePortalState({resultId:response.result_id,resultTerritoryId:payload.territory_id,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:payload.territory_id,analysisError:null});
        return;
      }
      state.result = response;
      renderEvidenceResult(response);
      $('#download-result').disabled = false;
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(response.cache_hit ? 'Se reutilizó la misma evidencia en caché.' : 'Evidencia calculada.');
    } catch (error) {
      writePortalState({analysisStatus:'error',analysisTerritoryId:payload.territory_id,analysisError:error.message});
      toast(error.message, 'error');
    }
    finally { stopBusy(); $('#run-evidence').disabled = false; }
  }

  function renderEvidenceResult(response) {
    clearResultLayers();
    const result = response.result;
    Object.entries(result.maps || {}).forEach(([key, descriptor], index) => addTileResultLayer(`evidence-${key}`, descriptor.legend || key, descriptor, index === 0));
    if (state.areaLayer) map.removeLayer(state.areaLayer);
    state.areaLayer = L.geoJSON(response.area.geometry, {style:layerStyle('area')}).addTo(map);
    map.fitBounds(state.areaLayer.getBounds(), {padding:[35,35],maxZoom:14});
    const statistics = Object.entries(result.statistics || {}).filter(([,value]) => !Array.isArray(value) && typeof value !== 'object');
    const annual = result.statistics?.annual_loss_ha;
    const cards = statistics.map(([key,value]) => metric(key.replaceAll('_',' '), typeof value === 'number' ? number(value,3) : value ?? 'Sin datos', result.source)).join('');
    const chart = annual?.length ? `<div class="chart-card"><h3>Pérdida anual (ha)</h3>${barChart(annual.map(item => ({label:item.year,value:item.value,formatted:hectares(item.value),color:'#e76f51'})))}</div>` : '';
    $('#results-title').textContent = result.source;
    $('#results-subtitle').textContent = `${response.area.label} · evidencia independiente`;
    $('#results-body').innerHTML = `<div class="metric-grid">${cards || metric('Estado','Sin observaciones válidas',result.source)}</div>${chart}<div class="res-sec"><h3>Metodología y límites</h3>${result.method ? `<p>${esc(result.method)}</p>` : ''}<ul class="warning-list">${(result.limitations || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul></div><a class="btn btn-s download-link" href="/api/v1/results/${response.result_id}/download.zip">Descargar resultado y metadatos</a>`;
    $('#results-panel').classList.remove('closed');
    $('#results-reopen').hidden = true;
    renderLayers(); renderLegend();
    setTimeout(() => map.invalidateSize(),220);
  }

  function currentAreaRequest() {
    if (state.wizard.areaMode === 'draw') return {mode: 'draw', geometry: state.drawnGeometry};
    if (state.wizard.areaMode === 'subbasin') return {mode: 'subbasin', subbasin: state.wizard.subbasin};
    return {mode: 'basin'};
  }

  function areaLabel() {
    if (state.wizard.areaMode === 'draw') return state.drawnGeometry ? 'Polígono dibujado' : 'Polígono pendiente';
    if (state.wizard.areaMode === 'subbasin') return state.wizard.subbasin ? `Subcuenca ${state.wizard.subbasin}` : 'Subcuenca pendiente';
    return 'Toda la CHCP';
  }

  function updateAreaLabel() { $('#filter-area-label').textContent = areaLabel(); }

  function persistWizard() {
    writePortalState({
      source: state.wizard.source,
      initialYear: state.wizard.initialYear,
      finalYear: state.wizard.finalYear,
      maximumDistance: state.wizard.maximumDistance,
      minimumPatchArea: state.wizard.minimumPatchArea,
      areaMode: state.wizard.areaMode,
      subbasin: state.wizard.subbasin,
    });
  }

  function startDrawing() {
    closeWizard();
    state.drawing = true;
    state.drawingPoints = [];
    state.drawingMarkers.forEach((marker) => map.removeLayer(marker));
    state.drawingMarkers = [];
    if (state.drawingLine) map.removeLayer(state.drawingLine);
    state.drawingLine = null;
    map.doubleClickZoom.disable();
    map.getContainer().classList.add('drawing');
    $('#drawbar').hidden = false;
    $('#draw-count').textContent = '0 vértices';
    toast('Haga clic en el mapa para añadir vértices y luego pulse Terminar.');
  }

  function updateDrawing() {
    if (state.drawingLine) map.removeLayer(state.drawingLine);
    if (state.drawingPoints.length > 1) state.drawingLine = L.polyline(state.drawingPoints, {color: '#d0442c', weight: 2, dashArray: '5 4'}).addTo(map);
    $('#draw-count').textContent = `${state.drawingPoints.length} vértice${state.drawingPoints.length === 1 ? '' : 's'}`;
  }

  map.on('click', (event) => {
    if (!state.drawing) return;
    state.drawingPoints.push(event.latlng);
    state.drawingMarkers.push(L.circleMarker(event.latlng, {radius: 5, color: '#fff', weight: 2, fillColor: '#d0442c', fillOpacity: 1}).addTo(map));
    updateDrawing();
  });

  function stopDrawing(reopen = true) {
    state.drawing = false;
    map.doubleClickZoom.enable();
    map.getContainer().classList.remove('drawing');
    $('#drawbar').hidden = true;
    state.drawingMarkers.forEach((marker) => map.removeLayer(marker));
    state.drawingMarkers = [];
    if (state.drawingLine) map.removeLayer(state.drawingLine);
    state.drawingLine = null;
    if (reopen) openWizard(1);
  }

  $('#draw-undo').addEventListener('click', () => { const marker = state.drawingMarkers.pop(); if (marker) map.removeLayer(marker); state.drawingPoints.pop(); updateDrawing(); });
  $('#draw-cancel').addEventListener('click', () => stopDrawing(true));
  $('#draw-finish').addEventListener('click', () => {
    if (state.drawingPoints.length < 3) { toast('El polígono necesita al menos tres vértices.', 'error'); return; }
    const coordinates = state.drawingPoints.map((point) => [point.lng, point.lat]);
    coordinates.push(coordinates[0]);
    state.drawnGeometry = {type: 'Polygon', coordinates: [coordinates]};
    if (state.areaLayer) map.removeLayer(state.areaLayer);
    state.areaLayer = L.geoJSON(state.drawnGeometry, {style: layerStyle('area')}).addTo(map);
    map.fitBounds(state.areaLayer.getBounds(), {padding: [40, 40], maxZoom: 15});
    state.wizard.areaMode = 'draw';
    state.territoryId = null;
    updateAreaLabel();
    stopDrawing(true);
  });

  const modal = $('#analysis-modal');
  const steps = ['Análisis', 'Área', 'Parámetros', 'Revisión'];
  function openWizard(step = 0) { state.wizardStep = step; modal.hidden = false; renderWizard(); $('#wizard-next').focus(); }
  function closeWizard() { modal.hidden = true; $('#open-analysis').focus(); }
  $('#open-analysis').addEventListener('click', () => openWizard(0));
  $('#modal-close').addEventListener('click', closeWizard);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeWizard(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !modal.hidden) closeWizard(); });

  function renderWizard() {
    $('#wizard-steps').innerHTML = steps.map((label, index) => `<li class="${index === state.wizardStep ? 'cur' : index < state.wizardStep ? 'ok' : ''}"><i>${index < state.wizardStep ? '✓' : index + 1}</i><span>${label}</span></li>`).join('');
    $('#wizard-back').disabled = state.wizardStep === 0;
    $('#wizard-next').textContent = state.wizardStep === 3 ? 'Ejecutar análisis' : 'Siguiente';
    $('#wizard-error').textContent = '';
    const body = $('#wizard-body');
    if (state.wizardStep === 0) renderAnalysisStep(body);
    else if (state.wizardStep === 1) renderAreaStep(body);
    else if (state.wizardStep === 2) renderParameterStep(body);
    else renderReviewStep(body);
  }

  function renderAnalysisStep(body) {
    const allSelected = state.wizard.analyses.length === 3;
    const options = state.config.analyses.map((item) => `<label class="opt"><input type="checkbox" data-analysis="${item.key}" ${state.wizard.analyses.includes(item.key) ? 'checked' : ''}><span class="layer-color" style="background:${item.key === 'coverage' ? '#1f8a70' : item.key === 'fragmentation' ? '#e76f51' : '#7a5195'}"></span><div><b>${esc(item.name)}</b><span>${esc(item.description)}</span></div></label>`).join('');
    body.innerHTML = `<h3>¿Qué quiere analizar?</h3><p class="sub">El motor recalcula cada período con parámetros equivalentes.</p><div class="wizard-analysis-grid"><label class="opt integral"><input type="checkbox" id="analysis-integral" ${allSelected ? 'checked' : ''}><span class="layer-color" style="background:#0a4393"></span><div><b>Análisis integral</b><span>Cobertura, fragmentación y conectividad en una sola ejecución.</span></div></label>${options}</div>`;
    $('#analysis-integral').onchange = (event) => { state.wizard.analyses = event.target.checked ? ['coverage', 'fragmentation', 'connectivity'] : ['coverage']; renderWizard(); };
    $$('[data-analysis]', body).forEach((input) => input.onchange = () => {
      const selected = $$('[data-analysis]:checked', body).map((item) => item.dataset.analysis);
      state.wizard.analyses = selected.length ? selected : ['coverage'];
      $('#analysis-integral').checked = state.wizard.analyses.length === 3;
    });
  }

  function renderAreaStep(body) {
    const subbasins = state.territory.subbasins.features.map((feature) => feature.properties?.nombre).filter(Boolean).sort((a, b) => a.localeCompare(b, 'es'));
    body.innerHTML = `<h3>Seleccione el área</h3><p class="sub">El dibujo es la primera opción. Las partes exteriores se recortan automáticamente a la CHCP.</p><div class="area-choice">
      <label class="opt"><input type="radio" name="area-mode" value="draw" ${state.wizard.areaMode === 'draw' ? 'checked' : ''}><span class="layer-color" style="background:#d0442c"></span><div><b>Dibujar un polígono</b><span>${state.drawnGeometry ? 'Polígono listo para analizar.' : 'Defina vértices directamente en el mapa.'}</span></div></label>
      <button class="btn btn-s" id="wizard-draw" type="button">${state.drawnGeometry ? 'Dibujar de nuevo' : 'Dibujar en el mapa'}</button>
      <label class="opt"><input type="radio" name="area-mode" value="subbasin" ${state.wizard.areaMode === 'subbasin' ? 'checked' : ''}><span class="layer-color" style="background:#77cc09"></span><div><b>Seleccionar una subcuenca</b><span>Utiliza los límites GeoJSON locales incluidos en el proyecto.</span></div></label>
      <label for="wizard-subbasin">Subcuenca</label><select id="wizard-subbasin" ${state.wizard.areaMode === 'subbasin' ? '' : 'disabled'}><option value="">Seleccione…</option>${subbasins.map((name) => `<option ${name === state.wizard.subbasin ? 'selected' : ''}>${esc(name)}</option>`).join('')}</select>
      <label class="opt"><input type="radio" name="area-mode" value="basin" ${state.wizard.areaMode === 'basin' ? 'checked' : ''}><span class="layer-color" style="background:#0a4393"></span><div><b>Toda la CHCP</b><span>Alternativa regional; puede requerir más tiempo de procesamiento.</span></div></label>
    </div>`;
    $('#wizard-draw').onclick = startDrawing;
    $$('input[name="area-mode"]', body).forEach((input) => input.onchange = () => { state.wizard.areaMode = input.value; renderWizard(); updateAreaLabel(); });
    $('#wizard-subbasin').onchange = (event) => { state.wizard.subbasin = event.target.value; updateAreaLabel(); };
  }

  function renderParameterStep(body) {
    const sources = Object.values(state.config.sources);
    body.innerHTML = `<h3>Fuente, período y parámetros</h3><p class="sub">JRC y ESRI se calculan independientemente. La modalidad integrada compara sus resultados sin fusionarlos.</p><div class="fld"><label for="wizard-source">Fuente temporal</label><select id="wizard-source">${sources.map((source) => `<option value="${source.clave}" ${source.clave === state.wizard.source ? 'selected' : ''}>${esc(source.nombre)} · ${source.resolucion_m} m</option>`).join('')}</select></div><div class="parameter-grid"><div class="fld"><label for="wizard-initial">Año inicial</label><select id="wizard-initial"></select></div><div class="fld"><label for="wizard-final">Año final</label><select id="wizard-final"></select></div><div class="fld"><label for="wizard-distance">Distancia máxima</label><select id="wizard-distance">${[100,250,500,750,1000,1500,2000].map((value) => `<option value="${value}" ${value === state.wizard.maximumDistance ? 'selected' : ''}>${value} m</option>`).join('')}</select></div><div class="fld"><label for="wizard-min-area">Área mínima de parche</label><input id="wizard-min-area" type="number" min="0" max="500" step="0.1" value="${state.wizard.minimumPatchArea}"><span class="hint">Hectáreas; se aplica igual en ambos años.</span></div></div><div class="source-note" id="wizard-source-note"></div>`;
    const sourceSelect = $('#wizard-source');
    const initial = $('#wizard-initial');
    const final = $('#wizard-final');
    const updateSource = () => {
      state.wizard.source = sourceSelect.value;
      selectYears(state.wizard.source, initial, final);
      const source = state.config.sources[state.wizard.source];
      $('#wizard-source-note').innerHTML = `<b>${esc(source.definicion_bosque)}</b><br>${esc(source.limitacion)}`;
    };
    updateSource();
    sourceSelect.onchange = updateSource;
    initial.onchange = (event) => { state.wizard.initialYear = Number(event.target.value); };
    final.onchange = (event) => { state.wizard.finalYear = Number(event.target.value); };
    $('#wizard-distance').onchange = (event) => { state.wizard.maximumDistance = Number(event.target.value); };
    $('#wizard-min-area').oninput = (event) => { state.wizard.minimumPatchArea = Math.max(0, Number(event.target.value) || 0); };
  }

  function renderReviewStep(body) {
    const source = state.config.sources[state.wizard.source];
    const names = state.wizard.analyses.map((key) => state.config.analyses.find((item) => item.key === key)?.name).filter(Boolean).join(', ');
    body.innerHTML = `<h3>Revise antes de ejecutar</h3><dl class="rev"><dt>Análisis</dt><dd>${esc(names)}</dd><dt>Área</dt><dd>${esc(areaLabel())}</dd><dt>Fuente</dt><dd>${esc(source.nombre)}</dd><dt>Período</dt><dd>${state.wizard.initialYear}–${state.wizard.finalYear}</dd><dt>Resolución nominal</dt><dd>${source.resolucion_m} m</dd><dt>Distancia entre parches</dt><dd>${number(state.wizard.maximumDistance, 0)} m</dd><dt>Área mínima</dt><dd>${number(state.wizard.minimumPatchArea, 1)} ha</dd></dl><div class="review-note">El resultado es indicativo. El ERI se calcula por separado y no altera las métricas temporales.</div>`;
  }

  $('#wizard-back').addEventListener('click', () => { if (state.wizardStep > 0) { state.wizardStep -= 1; renderWizard(); } });
  $('#wizard-next').addEventListener('click', () => {
    if (state.wizardStep === 1) {
      if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { $('#wizard-error').textContent = 'Dibuje un polígono antes de continuar.'; return; }
      if (state.wizard.areaMode === 'subbasin' && !state.wizard.subbasin) { $('#wizard-error').textContent = 'Seleccione una subcuenca.'; return; }
    }
    if (state.wizardStep === 2 && state.wizard.initialYear >= state.wizard.finalYear) { $('#wizard-error').textContent = 'El año inicial debe ser anterior al final.'; return; }
    if (state.wizardStep < 3) { state.wizardStep += 1; renderWizard(); return; }
    closeWizard();
    runAnalysis();
  });

  function analysisPayload() {
    return {
      analyses: state.wizard.analyses,
      area: currentAreaRequest(),
      source: state.wizard.source,
      initial_year: state.wizard.initialYear,
      final_year: state.wizard.finalYear,
      maximum_distance_m: state.wizard.maximumDistance,
      minimum_patch_area_ha: state.wizard.minimumPatchArea,
      territory_id: state.territoryId,
    };
  }

  function selectionFingerprint() {
    return JSON.stringify(analysisPayload());
  }

  async function runAnalysis() {
    persistWizard();
    const requestSequence = ++state.requestSequence;
    const payload = analysisPayload();
    const fingerprint = JSON.stringify(payload);
    writePortalState({analysisStatus:'processing',analysisTerritoryId:payload.territory_id,analysisLabel:`${payload.source} · ${payload.initial_year}–${payload.final_year}`,analysisError:null});
    setBusy(true, 'Calculando análisis científico');
    $('#open-analysis').disabled = true;
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 420000);
      const response = await api('/api/v1/analyses', {method: 'POST', body: JSON.stringify(payload), signal: controller.signal});
      clearTimeout(timer);
      if (requestSequence !== state.requestSequence || fingerprint !== selectionFingerprint()) {
        writePortalState({resultId:response.result_id,resultTerritoryId:payload.territory_id,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:payload.territory_id,analysisError:null});
        toast('El análisis terminó, pero la selección cambió. El resultado se guardó sin reemplazar la vista activa.');
        return;
      }
      state.result = response;
      state.eri = null;
      renderAnalysisResult(response);
      $('#download-result').disabled = false;
      writePortalState({
        resultId: response.result_id,
        resultTerritoryId: state.territoryId,
        resultCreatedUtc: response.created_utc,
        resultSource: state.wizard.source,
        resultInitialYear: state.wizard.initialYear,
        resultFinalYear: state.wizard.finalYear,
        analysisStatus: 'available',
        analysisTerritoryId: payload.territory_id,
        analysisError: null,
      });
      toast(response.cache_hit ? 'Se reutilizó un resultado idéntico en caché.' : 'Análisis completado.');
    } catch (error) {
      const suffix = error.supportId ? ` Código de soporte: ${error.supportId}.` : '';
      writePortalState({analysisStatus:'error',analysisTerritoryId:payload.territory_id,analysisError:`${error.message}${suffix}`});
      toast(`${error.name === 'AbortError' ? 'El análisis superó el tiempo de espera.' : error.message}${suffix}`, 'error');
    } finally {
      stopBusy();
      $('#open-analysis').disabled = false;
    }
  }

  function renderAnalysisMap(response) {
    clearResultLayers();
    const result = response.result;
    const yi = String(result.anio_inicial);
    const yf = String(result.anio_final);
    if (result.mode === 'integrated') {
      const concordance = result.concordance || {};
      addTileResultLayer('concordanceState', `Concordancia de cobertura ${yf}`, concordance.maps?.state, true);
      addTileResultLayer('concordanceChange', `Concordancia de cambios ${yi}–${yf}`, concordance.maps?.change, false);
      const jrc = result.sources?.jrc_tmf;
      const esri = result.sources?.esri_lulc;
      addResultLayer('jrcLoss', 'Pérdida según JRC', jrc?.transiciones?.perdida_bosque?.geojson, '#D94438', false);
      addResultLayer('jrcGain', 'Ganancia según JRC', jrc?.transiciones?.ganancia_bosque?.geojson, '#76B852', false);
      addResultLayer('esriLoss', 'Pérdida según ESRI', esri?.transiciones?.perdida_bosque?.geojson, '#F07A52', false);
      addResultLayer('esriGain', 'Ganancia según ESRI', esri?.transiciones?.ganancia_bosque?.geojson, '#9BCB68', false);
    } else {
    addResultLayer('stable', 'Bosque estable', result.transiciones?.bosque_estable?.geojson, symColor('transiciones_forestales','bosque_estable','#187A45'), false);
    addResultLayer('loss', 'Pérdida de bosque', result.transiciones?.perdida_bosque?.geojson, symColor('transiciones_forestales','perdida_bosque','#D94438'), true);
    addResultLayer('gain', 'Ganancia de clase bosque', result.transiciones?.ganancia_bosque?.geojson, symColor('transiciones_forestales','ganancia_bosque','#76B852'), true);
    addResultLayer('patchesInitial', `Parches ${yi}`, result.periodos?.[yi]?.analisis?.parches_geojson, '#1f8a70', false);
    addResultLayer('patchesFinal', `Parches ${yf}`, result.periodos?.[yf]?.analisis?.parches_geojson, '#3a7ca5', true);
    addResultLayer('connectionsInitial', `Conexiones ${yi}`, result.periodos?.[yi]?.analisis?.conexiones_geojson, '#fabc20', false);
    addResultLayer('connectionsFinal', `Conexiones ${yf}`, result.periodos?.[yf]?.analisis?.conexiones_geojson, '#7a5195', false);
    }
    if (state.areaLayer) map.removeLayer(state.areaLayer);
    state.areaLayer = L.geoJSON(response.area.geometry, {style: layerStyle('area')}).addTo(map);
    map.fitBounds(state.areaLayer.getBounds(), {padding: [35, 35], maxZoom: 14});
    renderLayers();
    renderLegend();
  }

  function metric(label, value, note = '') { return `<div class="metric-card"><span>${esc(label)}</span><b>${esc(value)}</b>${note ? `<small>${esc(note)}</small>` : ''}</div>`; }
  function barChart(rows) {
    const maximum = Math.max(1, ...rows.map((row) => Math.abs(Number(row.value || 0))));
    return `<div class="bar-chart">${rows.map((row) => `<div class="bar-row"><span>${esc(row.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(1, Math.abs(Number(row.value || 0)) / maximum * 100)}%;background:${row.color}"></div></div><span class="bar-value">${esc(row.formatted)}</span></div>`).join('')}</div>`;
  }

  function resultViews(response) {
    const result = response.result;
    if (result.mode === 'integrated') return integratedResultViews(response);
    const yi = String(result.anio_inicial);
    const yf = String(result.anio_final);
    const stats = result.estadisticas_cobertura;
    const initial = stats.periodos[yi];
    const final = stats.periodos[yf];
    const comparison = stats.comparacion;
    const ri = result.periodos[yi].resumen;
    const rf = result.periodos[yf].resumen;
    const interpretation = result.interpretacion_ecologica;
    const summary = `<div class="metric-grid">${metric(`Bosque ${yi}`, hectares(initial.bosque_ha), `${number(initial.porcentaje_bosque,1)} % del área válida`)}${metric(`Bosque ${yf}`, hectares(final.bosque_ha), `${number(final.porcentaje_bosque,1)} % del área válida`)}${metric('Cambio neto', hectares(comparison.cambio_neto_bosque_ha), `${number(comparison.cambio_neto_puntos_porcentuales,2)} puntos porcentuales`)}${metric('Pérdida', hectares(comparison.perdida_bosque_ha), 'Máscara válida común')}${metric(`Parches ${yi}`, number(ri.numero_parches,0), `${number(ri.area_media_parche_ha,2)} ha de media`)}${metric(`Parches ${yf}`, number(rf.numero_parches,0), `${number(rf.area_media_parche_ha,2)} ha de media`)}${metric(`Aislados ${yi}`, `${number(ri.porcentaje_parches_aislados,1)} %`, `${number(ri.numero_componentes,0)} componentes`)}${metric(`Aislados ${yf}`, `${number(rf.porcentaje_parches_aislados,1)} %`, `${number(rf.numero_componentes,0)} componentes`)}</div><div class="interpretation"><b>Lectura principal.</b> ${esc(interpretation.cobertura)}</div><ul class="warning-list">${response.warnings.map((warning) => `<li>${esc(warning)}</li>`).join('')}</ul>`;
    const charts = `<div class="chart-card"><h3>Cobertura forestal</h3>${barChart([{label: yi, value: initial.bosque_ha, formatted: hectares(initial.bosque_ha), color:'#1f8a70'},{label:yf,value:final.bosque_ha,formatted:hectares(final.bosque_ha),color:'#3a7ca5'}])}</div><div class="chart-card"><h3>Transiciones</h3>${barChart([{label:'Estable',value:comparison.bosque_estable_ha,formatted:hectares(comparison.bosque_estable_ha),color:'#2e7d32'},{label:'Pérdida',value:comparison.perdida_bosque_ha,formatted:hectares(comparison.perdida_bosque_ha),color:'#e76f51'},{label:'Ganancia',value:comparison.ganancia_bosque_ha,formatted:hectares(comparison.ganancia_bosque_ha),color:'#43aa8b'}])}</div><div class="chart-card"><h3>Fragmentación</h3>${barChart([{label:`Parches ${yi}`,value:ri.numero_parches,formatted:number(ri.numero_parches,0),color:'#1f8a70'},{label:`Parches ${yf}`,value:rf.numero_parches,formatted:number(rf.numero_parches,0),color:'#3a7ca5'}])}</div><div class="chart-card"><h3>Conectividad estructural</h3>${barChart([{label:`Aristas ${yi}`,value:ri.numero_aristas,formatted:number(ri.numero_aristas,0),color:'#fabc20'},{label:`Aristas ${yf}`,value:rf.numero_aristas,formatted:number(rf.numero_aristas,0),color:'#7a5195'}])}</div>`;
    const interpretationHtml = `<div class="interpretation"><b>Cobertura.</b> ${esc(interpretation.cobertura)}</div><div class="interpretation"><b>Fragmentación.</b> ${esc(interpretation.fragmentacion)}</div><div class="interpretation"><b>Conectividad.</b> ${esc(interpretation.conectividad)}</div>${interpretation.contradicciones.map((item) => `<div class="review-note">${esc(item)}</div>`).join('')}<div class="res-sec"><h3>Limitaciones</h3><ul class="warning-list">${interpretation.limitaciones.map((item) => `<li>${esc(item)}</li>`).join('')}</ul></div>`;
    const eri = `<div id="eri-content" class="empty-result"><h3>ERI complementario</h3><p>Se calcula de forma independiente y conserva los pesos originales. No modifica cobertura, fragmentación ni conectividad.</p><button class="btn btn-p" id="calculate-eri" type="button">Calcular ERI para esta área</button></div>`;
    return {summary, charts, interpretation: interpretationHtml, eri};
  }

  function integratedResultViews(response) {
    const result = response.result;
    const yi = String(result.anio_inicial);
    const yf = String(result.anio_final);
    const jrc = result.sources.jrc_tmf;
    const esri = result.sources.esri_lulc;
    const jrcStats = jrc.estadisticas_cobertura;
    const esriStats = esri.estadisticas_cobertura;
    const jrcFinal = jrcStats.periodos[yf];
    const esriFinal = esriStats.periodos[yf];
    const jrcChange = jrcStats.comparacion;
    const esriChange = esriStats.comparacion;
    const jrcFragments = jrc.periodos[yf].resumen;
    const esriFragments = esri.periodos[yf].resumen;
    const concordance = result.concordance;
    const summary = `<div class="metric-grid">${metric(`Bosque JRC ${yf}`, hectares(jrcFinal.bosque_ha), `${number(jrcFinal.porcentaje_bosque,1)} % válido`)}${metric(`Bosque ESRI ${yf}`, hectares(esriFinal.bosque_ha), `${number(esriFinal.porcentaje_bosque,1)} % válido`)}${metric('Diferencia final', hectares(concordance.diferencia_superficie_forestal_final_ha), 'JRC menos ESRI')}${metric('Concordancia de estado', `${number(concordance.estado.concordancia_pct,1)} %`, 'Sobre área válida común')}${metric('Pérdida JRC', hectares(jrcChange.perdida_bosque_ha), `${yi}–${yf}`)}${metric('Pérdida ESRI', hectares(esriChange.perdida_bosque_ha), `${yi}–${yf}`)}${metric('Parches JRC', number(jrcFragments.numero_parches,0), `Año ${yf}`)}${metric('Parches ESRI', number(esriFragments.numero_parches,0), `Año ${yf}`)}</div><div class="interpretation"><b>Lectura comparativa.</b> La concordancia identifica coincidencias y discrepancias entre productos. No crea una cobertura definitiva ni sustituye validación de campo.</div><ul class="warning-list">${response.warnings.map((warning) => `<li>${esc(warning)}</li>`).join('')}</ul>`;
    const charts = `<div class="chart-card"><h3>Superficie forestal final</h3>${barChart([{label:'JRC TMF',value:jrcFinal.bosque_ha,formatted:hectares(jrcFinal.bosque_ha),color:'#1F8A70'},{label:'ESRI LULC',value:esriFinal.bosque_ha,formatted:hectares(esriFinal.bosque_ha),color:'#3A7CA5'}])}</div><div class="chart-card"><h3>Pérdida detectada</h3>${barChart([{label:'JRC TMF',value:jrcChange.perdida_bosque_ha,formatted:hectares(jrcChange.perdida_bosque_ha),color:'#D94438'},{label:'ESRI LULC',value:esriChange.perdida_bosque_ha,formatted:hectares(esriChange.perdida_bosque_ha),color:'#F07A52'}])}</div><div class="chart-card"><h3>Ganancia de clase bosque</h3>${barChart([{label:'JRC TMF',value:jrcChange.ganancia_bosque_ha,formatted:hectares(jrcChange.ganancia_bosque_ha),color:'#76B852'},{label:'ESRI LULC',value:esriChange.ganancia_bosque_ha,formatted:hectares(esriChange.ganancia_bosque_ha),color:'#9BCB68'}])}</div><div class="chart-card"><h3>Parches del año final</h3>${barChart([{label:'JRC TMF',value:jrcFragments.numero_parches,formatted:number(jrcFragments.numero_parches,0),color:'#1F8A70'},{label:'ESRI LULC',value:esriFragments.numero_parches,formatted:number(esriFragments.numero_parches,0),color:'#3A7CA5'}])}</div>`;
    const stateAreas = concordance.estado.areas_ha;
    const changeAreas = concordance.cambio.areas_ha;
    const concordanceHtml = `<div class="chart-card"><h3>Concordancia de cobertura ${yf}</h3>${barChart([{label:'Bosque ambas',value:stateAreas.bosque_ambas,formatted:hectares(stateAreas.bosque_ambas),color:'#187A45'},{label:'No bosque ambas',value:stateAreas.no_bosque_ambas,formatted:hectares(stateAreas.no_bosque_ambas),color:'#D7C2A1'},{label:'Solo JRC',value:stateAreas.bosque_solo_jrc,formatted:hectares(stateAreas.bosque_solo_jrc),color:'#6B5FB5'},{label:'Solo ESRI',value:stateAreas.bosque_solo_esri,formatted:hectares(stateAreas.bosque_solo_esri),color:'#2F8FB3'}])}</div><div class="chart-card"><h3>Eventos coincidentes ${yi}–${yf}</h3>${barChart([{label:'Pérdida ambas',value:changeAreas.perdida_ambas,formatted:hectares(changeAreas.perdida_ambas),color:'#8B1E1E'},{label:'Ganancia ambas',value:changeAreas.ganancia_ambas,formatted:hectares(changeAreas.ganancia_ambas),color:'#3D7E3A'},{label:'Pérdida solo JRC',value:changeAreas.perdida_solo_jrc,formatted:hectares(changeAreas.perdida_solo_jrc),color:'#D94438'},{label:'Pérdida solo ESRI',value:changeAreas.perdida_solo_esri,formatted:hectares(changeAreas.perdida_solo_esri),color:'#F07A52'}])}</div><div class="review-note">La agregación de ESRI a 30 m usa moda sobre la malla JRC. No se emplea interpolación bilineal para clases.</div>`;
    const interpretation = `<div class="interpretation"><b>JRC TMF.</b> ${esc(jrc.interpretacion_ecologica.cobertura)}</div><div class="interpretation"><b>ESRI LULC.</b> ${esc(esri.interpretacion_ecologica.cobertura)}</div><div class="review-note">${esc(result.metadata.scientific_scope)}</div><ul class="warning-list">${result.warnings.map((warning) => `<li>${esc(warning)}</li>`).join('')}</ul>`;
    const eri = `<div id="eri-content" class="empty-result"><h3>ERI complementario</h3><p>Se calcula por separado y no interviene en la concordancia JRC–ESRI.</p><button class="btn btn-p" id="calculate-eri" type="button">Calcular ERI para esta área</button></div>`;
    return {summary, charts, concordance: concordanceHtml, interpretation, eri};
  }

  function renderAnalysisResult(response) {
    if (response.kind === 'complementary_evidence') { renderEvidenceResult(response); return; }
    renderAnalysisMap(response);
    const views = resultViews(response);
    $('#results-title').textContent = 'Resultado del análisis';
    $('#results-subtitle').textContent = `${response.area.label} · ${response.result.anio_inicial}–${response.result.anio_final}`;
    const tabs = ['summary','charts',...(views.concordance ? ['concordance'] : []),'interpretation','eri'];
    const labels = {summary:'Lectura',charts:'Gráficas',concordance:'Concordancia',interpretation:'Interpretación',eri:'ERI'};
    $('#results-body').innerHTML = `<div class="result-tabs" role="tablist">${tabs.map((key,index) => `<button role="tab" data-result-tab="${key}" aria-selected="${index === 0}">${labels[key]}</button>`).join('')}</div>${tabs.map((key,index) => `<div class="result-view" id="view-${key}" ${index ? 'hidden' : ''}>${views[key]}</div>`).join('')}<a class="btn btn-s download-link" href="/api/v1/results/${response.result_id}/download.zip">Descargar resultados y metadatos</a>`;
    const panel = $('#results-panel');
    panel.classList.remove('closed');
    $('#results-reopen').hidden = true;
    $$('[data-result-tab]', panel).forEach((button) => button.addEventListener('click', () => {
      $$('[data-result-tab]', panel).forEach((item) => item.setAttribute('aria-selected', String(item === button)));
      tabs.forEach((key) => { $(`#view-${key}`).hidden = button.dataset.resultTab !== key; });
    }));
    $('#calculate-eri').addEventListener('click', calculateEri);
    setTimeout(() => map.invalidateSize(), 220);
  }

  async function calculateEri() {
    const container = $('#eri-content');
    container.innerHTML = '<h3>Calculando ERI…</h3><p>Dynamic World, GEDI, Copernicus DEM y MERIT Hydro.</p>';
    try {
      state.eri = await api('/api/v1/eri', {method: 'POST', body: JSON.stringify({area: currentAreaRequest()})});
      const result = state.eri.result;
      const components = Object.entries(result.componentes).map(([key,value]) => ({label: key.replaceAll('_',' '), value, formatted:number(value,2), color: key === 'integridad_estructural' ? '#0a4393' : key === 'conectividad' ? '#2a9d8f' : key === 'estabilidad_topografica' ? '#fabc20' : '#3a7ca5'}));
      container.className = 'result-view';
      container.innerHTML = `<div class="eri-score"><div class="eri-ring" style="--eri-value:${result.valor * 100};--eri-color:${result.color}"><b>${number(result.valor,2)}</b></div><div><h3>${esc(result.clase)}</h3><p>${esc(result.lectura)}</p><span class="status-pill">Complementario</span></div></div><div class="chart-card"><h3>Componentes del ERI</h3>${barChart(components)}</div><div class="interpretation">${esc(result.nota_conectividad)}</div><ul class="warning-list">${state.eri.warnings.map((warning) => `<li>${esc(warning)}</li>`).join('')}</ul>`;
      if (result.tile_url) {
        const layer = L.tileLayer(result.tile_url, {opacity: .72, attribution: 'Google Earth Engine'});
        state.resultLayers.set('eriTiles', {key:'eriTiles',name:'ERI indicativo',layer,color:'#76b72a'});
        renderLayers();
      }
    } catch (error) {
      container.className = 'empty-result';
      container.innerHTML = `<h3>ERI no disponible</h3><p>${esc(error.message)}</p><button class="btn btn-s" id="retry-eri" type="button">Intentar nuevamente</button>`;
      $('#retry-eri').addEventListener('click', calculateEri);
    }
  }

  $('#results-close').addEventListener('click', () => { $('#results-panel').classList.add('closed'); $('#results-reopen').hidden = false; setTimeout(() => map.invalidateSize(), 220); });
  $('#results-reopen').addEventListener('click', () => { $('#results-panel').classList.remove('closed'); $('#results-reopen').hidden = true; setTimeout(() => map.invalidateSize(), 220); });
  $('#download-result').addEventListener('click', () => { if (state.result) window.location.assign(`/api/v1/results/${state.result.result_id}/download.zip`); });
  $('#left-toggle').addEventListener('click', () => {
    const container = $('#v-plataforma');
    const collapsed = container.classList.toggle('left-collapsed');
    $('#left-toggle').textContent = collapsed ? '›' : '‹';
    $('#left-toggle').setAttribute('aria-label', collapsed ? 'Mostrar panel de controles' : 'Ocultar panel de controles');
    setTimeout(() => map.invalidateSize(), 220);
  });

  $$('.side-tabs [role="tab"]').forEach((button) => button.addEventListener('click', () => {
    $$('.side-tabs [role="tab"]').forEach((item) => item.setAttribute('aria-selected', String(item === button)));
    ['layers','filters','basemaps'].forEach((key) => { $(`#panel-${key}`).hidden = button.dataset.panel !== key; });
  }));

  async function applyPreparedTerritory() {
    const params = new URLSearchParams(window.location.search);
    const stored = readPortalState();
    const requested = params.get('territory') || stored.territoryId;
    if (requested) {
      try {
        const summary = await api(`/api/v1/territories/${encodeURIComponent(requested)}/summary`);
        state.territoryId = requested;
        $('#selected-territory-id').textContent = `Territorio preparado: ${summary.territory.nombre}`;
        if (summary.territory.tipo === 'subcuenca') {
          state.wizard.areaMode = 'subbasin';
          state.wizard.subbasin = summary.territory.nombre;
        } else if (summary.territory.tipo === 'corredor') {
          state.wizard.areaMode = 'draw';
          state.wizard.subbasin = '';
          state.drawnGeometry = summary.geometry;
        } else {
          state.wizard.areaMode = 'basin';
          state.wizard.subbasin = '';
        }
        if (state.areaLayer) map.removeLayer(state.areaLayer);
        state.areaLayer = L.geoJSON(summary.geometry, {style: layerStyle('area')}).addTo(map);
        map.fitBounds(state.areaLayer.getBounds(), {padding:[35,35],maxZoom:13});
        updateAreaLabel();
      } catch (error) {
        toast(`No se pudo preparar el territorio guardado: ${error.message}`, 'error');
      }
    }
    if (params.get('draw') === '1') startDrawing();
  }

  async function restoreResult() {
    const params = new URLSearchParams(window.location.search);
    const stored = readPortalState();
    const identifier = params.get('result') || stored.resultId;
    if (!identifier) return;
    try {
      const response = await api(`/api/v1/results/${encodeURIComponent(identifier)}`);
      state.result = response;
      renderAnalysisResult(response);
      $('#download-result').disabled = false;
    } catch (error) {
      if (error.status !== 404) toast(`No se pudo recuperar el resultado: ${error.message}`, 'error');
    }
  }

  try {
    const stored = readPortalState();
    state.wizard.source = stored.source || state.wizard.source;
    state.wizard.initialYear = Number(stored.initialYear || state.wizard.initialYear);
    state.wizard.finalYear = Number(stored.finalYear || state.wizard.finalYear);
    state.wizard.maximumDistance = Number(stored.maximumDistance || state.wizard.maximumDistance);
    state.wizard.minimumPatchArea = Number(stored.minimumPatchArea || state.wizard.minimumPatchArea);
    state.resultOpacity = Math.max(.2, Math.min(1, Number(stored.resultOpacity || state.resultOpacity)));
    [state.config, state.territory, state.sourceCatalog] = await Promise.all([api('/api/v1/config'), api('/api/v1/territory'), api('/api/v1/catalog/sources')]);
    if (!state.config.sources[state.wizard.source]) state.wizard.source = 'jrc_tmf';
    renderTerritory();
    renderBasemaps();
    renderQuickFilters();
    renderLayers();
    updateAreaLabel();
    await applyPreparedTerritory();
    await restoreResult();
  } catch (error) {
    toast(`No se pudo iniciar el geoportal: ${error.message}`, 'error');
    $('#open-analysis').disabled = true;
  }
})();

