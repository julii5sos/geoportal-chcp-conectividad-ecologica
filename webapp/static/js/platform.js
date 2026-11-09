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
    activeLayers: new Set(['basin', 'corridors', 'criticalPoints']),
    preview: {
      ndviYear: 2025,
      jrcYear: 2025,
      hansenYear: 2025,
      esriYear: 2025,
      officialSource: '2023_general',
      loading: new Set(),
    },
    areaLayer: null,
    drawnGeometry: null,
    drawing: false,
    drawingPoints: [],
    drawingMarkers: [],
    drawingLine: null,
    territoryId: null,
    requestSequence: 0,
    lastAnalysisFingerprint: null,
    wizardStep: 0,
    wizard: {
      mode: 'custom',
      selectedComponents: ['ecological'],
      areaMode: 'draw',
      subbasin: '',
      source: 'jrc_tmf',
      initialYear: 2020,
      finalYear: 2025,
      maximumDistance: 500,
      minimumPatchArea: 0,
      evidenceSource: 'hansen_gfc',
      officialCoverageYear: 2021,
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

  function setBusy(on, title = 'Procesando', steps = null) {
    const busy = $('#busy');
    busy.hidden = !on;
    if (!on) return;
    const activeSteps = steps || ['Validando el área', 'Consultando cobertura', 'Preparando parches', 'Construyendo red', 'Preparando resultados'];
    setBusy._steps = activeSteps;
    $('#busy-title').textContent = title;
    $('#busy-steps').innerHTML = activeSteps.map((step, index) => `<li class="${index === 0 ? 'now' : ''}">${index === 0 ? '●' : '○'} ${step}</li>`).join('');
    $('#busy-bar').style.width = `${Math.round(100 / activeSteps.length)}%`;
    let index = 0;
    clearInterval(setBusy._timer);
    setBusy._timer = setInterval(() => {
      index = Math.min(activeSteps.length - 1, index + 1);
      $('#busy-steps').innerHTML = activeSteps.map((step, item) => `<li class="${item < index ? 'done' : item === index ? 'now' : ''}">${item < index ? '✓' : item === index ? '●' : '○'} ${step}</li>`).join('');
      $('#busy-bar').style.width = `${Math.round((index + 1) / activeSteps.length * 100)}%`;
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
      structuralPatches: { color: '#237A4B', weight: .8, fillColor: '#237A4B', fillOpacity: .34 },
      structuralConnections: { color: '#225ea8', weight: 2.2, opacity: .85 },
      structuralGaps: { color: '#d0442c', weight: 2.2, dashArray: '7 5', opacity: .9 },
      structuralRoute: { color: '#f28e2b', weight: 4, opacity: .95 },
      comparisonPatches2021: { color: '#237A4B', weight: .8, fillColor: '#237A4B', fillOpacity: .36 },
      comparisonPatches2023: { color: '#7a5195', weight: .8, fillColor: '#7a5195', fillOpacity: .34 },
      comparisonConnections2021: { color: '#225ea8', weight: 2.2, opacity: .9 },
      comparisonConnections2023: { color: '#f28e2b', weight: 2.2, opacity: .9 },
      comparisonRoute2021: { color: '#0a4393', weight: 4, opacity: .95 },
      comparisonRoute2023: { color: '#d0442c', weight: 4, opacity: .95 },
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
      updateWhenIdle: true,
      keepBuffer: 1,
    });
    state.resultLayers.set(key, {
      key,
      name,
      layer,
      color: classes[0]?.color || '#0a4393',
      legend: classes.map((item) => ({name: item.etiqueta || item.label || `Clase ${item.value}`, color: item.color})),
    });
    if (active) { layer.addTo(map); state.activeLayers.add(key); }
  }

  function previewAreaRequest() {
    if (state.drawnGeometry) return {mode: 'draw', geometry: state.drawnGeometry};
    if (state.wizard.areaMode === 'subbasin' && state.wizard.subbasin) {
      return {mode: 'subbasin', subbasin: state.wizard.subbasin};
    }
    return {mode: 'basin'};
  }

  async function loadPreview(key, source, year = null) {
    const previous = state.resultLayers.get(key);
    if (previous?.layer && map.hasLayer(previous.layer)) map.removeLayer(previous.layer);
    state.resultLayers.delete(key);
    state.activeLayers.delete(key);
    state.preview.loading.add(key);
    renderLayers();
    try {
      const response = await api('/api/v1/layers/preview', {
        method: 'POST',
        body: JSON.stringify({source, year, area: previewAreaRequest()}),
      });
      addTileResultLayer(key, response.layer.legend, response.layer, true);
      toast(`${response.layer.legend} está visible en el mapa.`, 'success');
    } catch (error) {
      toast(`No se pudo preparar la capa: ${error.message}`, 'error');
    } finally {
      state.preview.loading.delete(key);
      renderLayers();
      renderLegend();
    }
  }

  function removePreview(key) {
    const entry = state.resultLayers.get(key);
    if (entry?.layer && map.hasLayer(entry.layer)) map.removeLayer(entry.layer);
    state.resultLayers.delete(key);
    state.activeLayers.delete(key);
    renderLayers();
    renderLegend();
  }

  function clearResultLayers() {
    state.resultLayers.forEach(({layer}) => { if (map.hasLayer(layer)) map.removeLayer(layer); });
    state.resultLayers.clear();
    state.activeLayers = new Set(['basin', 'corridors', 'criticalPoints']);
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
    const corridorRows = layerRow('corridors', 'Corredores publicados', '#a1d303', true, `${state.territory?.corridors?.features?.length || 0} polígonos`) + layerRow('criticalPoints', 'Puntos críticos publicados', '#f04438', true, `${state.territory?.critical_points?.features?.length || 0} puntos`);
    const calculatedLayers = Array.from(state.resultLayers.values()).filter((item) => !item.key.startsWith('preview-'));
    const temporalRows = calculatedLayers.length
      ? calculatedLayers.map((item) => layerRow(item.key, item.name, item.color, true, 'Resultado calculado')).join('')
      : layerRow('pending', 'Ejecute un análisis para habilitar resultados', '#d6deeb', false);
    const ndviChecked = state.activeLayers.has('preview-ndvi');
    const officialChecked = state.activeLayers.has('preview-official');
    const ndviYears = Array.from({length: 9}, (_, index) => 2017 + index).map((year) => `<option ${year === state.preview.ndviYear ? 'selected' : ''}>${year}</option>`).join('');
    const yearOptions = (initial, final, selected) => Array.from({length: final - initial + 1}, (_, index) => initial + index).map((year) => `<option ${year === selected ? 'selected' : ''}>${year}</option>`).join('');
    const officialProducts = [
      ['1992_historico','Cobertura histórica 1992'],
      ['2000_historico','Cobertura histórica 2000'],
      ['2012_binario','Bosque / no bosque 2012'],
      ['2012_detallado','Uso y cobertura 2012'],
      ['2019_general','Cobertura general 2019'],
      ['2021_general','Cobertura general oficial 2021'],
      ['2021_detallado','Uso y cobertura detallada 2021'],
      ['2023_general','Diagnóstico general 2023'],
    ].map(([value,label]) => `<option value="${value}" ${value === state.preview.officialSource ? 'selected' : ''}>${label}</option>`).join('');
    const vegetationRows = `<div class="layer-source-control ${state.preview.loading.has('preview-ndvi') ? 'is-loading' : ''}"><div class="ly-h"><span class="tg"><input type="checkbox" data-preview="ndvi" ${ndviChecked ? 'checked' : ''} ${state.preview.loading.has('preview-ndvi') ? 'disabled' : ''} aria-label="Mostrar Sentinel-2 NDVI"><span></span></span><i class="layer-color ndvi-ramp"></i><label class="nm">Sentinel-2 · NDVI<small>Vigor de la vegetación; vista anual sin estadísticas</small></label></div><label class="layer-source-select">Año<select data-preview-year ${state.preview.loading.has('preview-ndvi') ? 'disabled' : ''}>${ndviYears}</select></label></div>`;
    const satelliteControl = (key, source, name, note, color, yearField = null, initial = null, final = null) => {
      const layerKey = `preview-${key}`;
      const checked = state.activeLayers.has(layerKey);
      const loading = state.preview.loading.has(layerKey);
      const year = yearField ? state.preview[yearField] : null;
      const selector = yearField ? `<label class="layer-source-select">Año<select data-sat-year="${key}" ${loading ? 'disabled' : ''}>${yearOptions(initial, final, year)}</select></label>` : '';
      return `<div class="layer-source-control ${loading ? 'is-loading' : ''}"><div class="ly-h"><span class="tg"><input type="checkbox" data-sat-preview="${key}" data-source="${source}" ${checked ? 'checked' : ''} ${loading ? 'disabled' : ''} aria-label="Mostrar ${esc(name)}"><span></span></span><i class="layer-color" style="background:${color}"></i><label class="nm">${esc(name)}<small>${esc(note)}</small></label></div>${selector}</div>`;
    };
    const satelliteRows = satelliteControl('jrc', 'jrc_tmf', 'JRC Tropical Moist Forest', 'Estado anual del bosque húmedo tropical', '#005a32', 'jrcYear', 1990, 2025)
      + satelliteControl('hansen', 'hansen_gfc', 'Hansen Global Forest Change', 'Pérdida de cobertura arbórea por año', '#b42318', 'hansenYear', 2001, 2025)
      + satelliteControl('esri', 'esri_lulc', 'ESRI Land Use / Land Cover', 'Cobertura anual de 10 m', '#397d49', 'esriYear', 2017, 2025)
      + vegetationRows
      + satelliteControl('gedi', 'gedi', 'GEDI · altura del dosel', 'Referencia estructural fija con cobertura parcial', '#225ea8');
    const officialRows = `<div class="layer-source-control ${state.preview.loading.has('preview-official') ? 'is-loading' : ''}"><div class="ly-h"><span class="tg"><input type="checkbox" data-preview="official" ${officialChecked ? 'checked' : ''} ${state.preview.loading.has('preview-official') ? 'disabled' : ''} aria-label="Mostrar cobertura oficial"><span></span></span><i class="layer-color official-ramp"></i><label class="nm">Coberturas oficiales de Panamá<small>Productos independientes; no forman una serie comparable por defecto</small></label></div><label class="layer-source-select">Producto<select data-preview-product ${state.preview.loading.has('preview-official') ? 'disabled' : ''}>${officialProducts}</select></label></div><div class="source-note"><small>Activar una capa solo cambia el mapa. Fragmentación y conectividad se ejecutan desde Realizar análisis.</small></div>`;
    const comparisonAction = `<div class="source-note structural-comparison-action"><b>Escenarios estructurales 2021 y 2023</b><small>Dos diagnósticos paralelos; no se interpreta como cambio causal.</small><button class="btn btn-s" id="compare-structural" type="button">Comparar conectividad 2021–2023</button></div>`;
    $('#panel-layers').innerHTML = group('Resultados del análisis', temporalRows, true) + group('Señales satelitales', satelliteRows, true) + group('Conectividad y riesgos', corridorRows + comparisonAction, true) + group('Coberturas oficiales', officialRows, true) + group('Límites territoriales', basinRows, false) + group('ERI complementario', state.eri ? layerRow('eriTiles', 'Índice ERI indicativo', '#76b72a', state.resultLayers.has('eriTiles')) : layerRow('eriPending', 'Se habilita después de un resultado', '#d6deeb', false), false);
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
    $('#compare-structural')?.addEventListener('click', runStructuralComparison);
    $('[data-preview="ndvi"]', $('#panel-layers'))?.addEventListener('change', (event) => {
      if (event.target.checked) loadPreview('preview-ndvi', 'sentinel_ndvi', state.preview.ndviYear);
      else removePreview('preview-ndvi');
    });
    $('[data-preview="official"]', $('#panel-layers'))?.addEventListener('change', (event) => {
      if (event.target.checked) loadPreview('preview-official', state.preview.officialSource);
      else removePreview('preview-official');
    });
    $$('[data-sat-preview]', $('#panel-layers')).forEach((input) => input.addEventListener('change', (event) => {
      const key = event.target.dataset.satPreview;
      const source = event.target.dataset.source;
      const field = key === 'jrc' ? 'jrcYear' : key === 'hansen' ? 'hansenYear' : key === 'esri' ? 'esriYear' : null;
      if (event.target.checked) loadPreview(`preview-${key}`, source, field ? state.preview[field] : null);
      else removePreview(`preview-${key}`);
    }));
    $$('[data-sat-year]', $('#panel-layers')).forEach((select) => select.addEventListener('change', (event) => {
      const key = event.target.dataset.satYear;
      const field = key === 'jrc' ? 'jrcYear' : key === 'hansen' ? 'hansenYear' : 'esriYear';
      const source = key === 'jrc' ? 'jrc_tmf' : key === 'hansen' ? 'hansen_gfc' : 'esri_lulc';
      state.preview[field] = Number(event.target.value);
      if (state.activeLayers.has(`preview-${key}`)) loadPreview(`preview-${key}`, source, state.preview[field]);
    }));
    $('[data-preview-year]', $('#panel-layers'))?.addEventListener('change', (event) => {
      state.preview.ndviYear = Number(event.target.value);
      if (state.activeLayers.has('preview-ndvi')) loadPreview('preview-ndvi', 'sentinel_ndvi', state.preview.ndviYear);
    });
    $('[data-preview-product]', $('#panel-layers'))?.addEventListener('change', (event) => {
      state.preview.officialSource = event.target.value;
      if (state.activeLayers.has('preview-official')) loadPreview('preview-official', state.preview.officialSource);
    });
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
      const summary = await api(`/api/v1/territories/${encodeURIComponent(item.id)}/summary`);
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
      renderPreparedTerritory(summary);
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
    }).addTo(map);
    criticalPointLayer = L.geoJSON(state.territory.critical_points, {
      pointToLayer: (feature, latlng) => L.circleMarker(latlng, layerStyle('criticalPoints')),
      onEachFeature: (feature, layer) => layer.bindTooltip(feature.properties?.nombre || feature.properties?.titulo || 'Punto crítico publicado'),
    }).addTo(map);
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
    $('#quick-distance').value = String(state.wizard.maximumDistance);
    $('#layer-opacity').value = String(Math.round(state.resultOpacity * 100));
    $('#layer-opacity-value').textContent = `${Math.round(state.resultOpacity * 100)} %`;
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
  }

  async function runStructuralConnectivity(scenario, scope = 'connectivity') {
    if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { toast('Dibuje un polígono o seleccione un territorio antes de calcular.', 'error'); return; }
    $('#open-analysis').disabled = true;
    setBusy(true, scope === 'fragmentation' ? 'Calculando fragmentación oficial 2021' : scenario === 'official_2021' ? 'Calculando conectividad oficial 2021' : 'Calculando escenario diagnóstico 2023', ['Validando el área', 'Consultando cobertura oficial', 'Preparando parches', 'Construyendo red', 'Preparando resultados']);
    try {
      const response = await api('/api/v1/structural-connectivity', {method:'POST', body:JSON.stringify({area:currentAreaRequest(), scenario, maximum_distance_m:state.wizard.maximumDistance, minimum_patch_area_ha:state.wizard.minimumPatchArea, territory_id:state.territoryId})});
      state.result = response;
      state.lastAnalysisFingerprint = selectionFingerprint();
      renderStructuralConnectivity(response, scope);
      $('#download-result').disabled = false;
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(response.cache_hit ? 'Se reutilizó la estructura ya calculada.' : scope === 'fragmentation' ? 'Fragmentación calculada.' : 'Conectividad estructural calculada.');
    } catch (error) { toast(error.message, 'error'); }
    finally { stopBusy(); $('#open-analysis').disabled = false; }
  }

  async function runStructuralComparison() {
    if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) {
      toast('Dibuje un polígono o seleccione un territorio antes de comparar.', 'error');
      return;
    }
    $('#open-analysis').disabled = true;
    setBusy(true, 'Comparando escenarios estructurales 2021 y 2023', [
      'Validando el área y los parámetros comunes',
      'Preparando estructura oficial 2021',
      'Preparando escenario diagnóstico 2023',
      'Construyendo las dos redes',
      'Presentando diagnósticos paralelos',
    ]);
    try {
      const response = await api('/api/v1/structural-comparison', {
        method:'POST',
        body:JSON.stringify({
          area:currentAreaRequest(),
          maximum_distance_m:state.wizard.maximumDistance,
          minimum_patch_area_ha:state.wizard.minimumPatchArea,
          territory_id:state.territoryId,
        }),
      });
      state.result = response;
      state.lastAnalysisFingerprint = null;
      renderStructuralComparison(response);
      $('#download-result').disabled = false;
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(response.cache_hit ? 'Se reutilizó la comparación estructural.' : 'Comparación estructural completada.');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      stopBusy();
      $('#open-analysis').disabled = false;
    }
  }

  async function runOfficialCoverage() {
    if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { toast('Dibuje un polígono o seleccione un territorio antes de consultar.', 'error'); return; }
    const year = state.wizard.officialCoverageYear;
    $('#open-analysis').disabled = true;
    setBusy(true, `Consultando cobertura ${year}`, ['Validando el área', `Consultando la fuente ${year}`, 'Calculando superficies por categoría', 'Preparando resultados']);
    try {
      const response = await api(`/api/v1/official-coverages/${year}`, {method:'POST', body:JSON.stringify({area:currentAreaRequest(), territory_id:state.territoryId})});
      state.result = response;
      state.lastAnalysisFingerprint = null;
      renderOfficialCoverage(response);
      $('#download-result').disabled = false;
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(year === 2021 ? 'Cobertura institucional 2021 consultada.' : 'Cobertura diagnóstica 2023 consultada por código.');
    } catch (error) { toast(error.message, 'error'); }
    finally { stopBusy(); $('#open-analysis').disabled = false; }
  }

  async function runEvidence() {
    if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { toast('Dibuje un polígono o seleccione un territorio antes de calcular.', 'error'); return; }
    const source = state.wizard.evidenceSource;
    const payload = {source, area:currentAreaRequest(), initial_year:state.wizard.initialYear, final_year:state.wizard.finalYear, parameters:{tree_cover_threshold:30}, territory_id:state.territoryId};
    if (['gedi','worldcover'].includes(source)) { payload.initial_year = null; payload.final_year = null; }
    const sequence = ++state.requestSequence;
    writePortalState({analysisStatus:'processing',analysisTerritoryId:state.territoryId,analysisLabel:`${source} · evidencia complementaria`,analysisError:null});
    setBusy(true, 'Calculando evidencia complementaria', ['Validando el área', 'Consultando la fuente seleccionada', 'Calculando estadísticas', 'Preparando resultados']);
    $('#open-analysis').disabled = true;
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
    finally { stopBusy(); $('#open-analysis').disabled = false; }
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
    const components = [
      ['ecological','Preevaluación territorial','#0a4393','Calcula primero las cinco señales y el índice territorial. No prepara parches.'],
      ['fragmentation','Fragmentación','#1f8a70','Mide superficie forestal, número, tamaño, densidad y bordes de los parches oficiales 2021.'],
      ['connectivity','Conectividad','#225ea8','Construye la red estructural, componentes, aislamiento, brechas y ruta potencial hacia corredores.'],
    ];
    const integral = state.wizard.mode === 'integral';
    body.innerHTML = `<h3>¿Qué quiere analizar?</h3><p class="sub">Puede combinar uno o varios componentes. Cada resultado conserva su fórmula y fuente.</p><div class="wizard-analysis-grid">${components.map(([key,name,color,note]) => `<label class="opt"><input type="checkbox" name="analysis-component" value="${key}" ${state.wizard.selectedComponents.includes(key) ? 'checked' : ''} ${integral ? 'disabled' : ''}><span class="layer-color" style="background:${color}"></span><div><b>${name}</b><span>${note}</span></div></label>`).join('')}</div><div class="analysis-or"><span>o ejecute los tres componentes</span></div><label class="opt integral"><input type="checkbox" id="analysis-integral" ${integral ? 'checked' : ''}><span class="layer-color" style="background:#7a5195"></span><div><b>Análisis integral</b><span>Selecciona preevaluación, fragmentación y conectividad. Es exclusivo para evitar combinaciones duplicadas.</span></div></label><div class="review-note">La comparación temporal, las coberturas oficiales y las fuentes complementarias se consultan desde el Panel territorial.</div>`;
    $$('input[name="analysis-component"]', body).forEach((input) => input.onchange = () => {
      state.wizard.mode = 'custom';
      state.wizard.selectedComponents = $$('input[name="analysis-component"]:checked', body).map((item) => item.value);
    });
    $('#analysis-integral').onchange = (event) => {
      state.wizard.mode = event.target.checked ? 'integral' : 'custom';
      state.wizard.selectedComponents = event.target.checked ? ['ecological','fragmentation','connectivity'] : ['ecological'];
      renderAnalysisStep(body);
    };
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
    const selected = state.wizard.selectedComponents;
    const needsStructure = selected.includes('fragmentation') || selected.includes('connectivity');
    if (!needsStructure) {
      body.innerHTML = `<h3>Períodos científicos fijos</h3><p class="sub">Esta primera etapa calcula solamente las cinco señales y el índice original.</p><dl class="rev"><dt>JRC TMF</dt><dd>Estado 2025</dd><dt>Hansen</dt><dd>Pérdida posterior al 31/12/2020</dd><dt>ESRI</dt><dd>Transición Trees 2017–2024</dd><dt>Sentinel-2 NDVI</dt><dd>2020–2025</dd><dt>GEDI</dt><dd>Altura de dosel como contexto</dd></dl><div class="review-note">No se preparan parches en esta modalidad. El mapa de coincidencia orienta dónde revisar y no suma puntos.</div>`;
      return;
    }
    if (needsStructure) {
      const selectedNames = selected.map((key) => ({ecological:'preevaluación territorial',fragmentation:'fragmentación',connectivity:'conectividad'}[key])).join(', ');
      body.innerHTML = `<h3>Parámetros estructurales</h3><p class="sub">Componentes seleccionados: ${esc(selectedNames)}.</p><div class="source-note"><b>SINIA–MiAMBIENTE · Bosques y Otras Tierras Boscosas</b><br>Referencia oficial 2021. No se considera equivalente a JRC o ESRI.</div><div class="parameter-grid"><div class="fld"><label for="wizard-distance">Distancia máxima</label><select id="wizard-distance">${[100,250,500,750,1000,1500,2000].map((value) => `<option value="${value}" ${value === state.wizard.maximumDistance ? 'selected' : ''}>${value} m</option>`).join('')}</select></div><div class="fld"><label for="wizard-min-area">Área mínima de parche</label><input id="wizard-min-area" type="number" min="0" max="500" step="0.1" value="${state.wizard.minimumPatchArea}"><span class="hint">Hectáreas. Cero conserva todos los parches identificados.</span></div></div>`;
      $('#wizard-distance').onchange = (event) => { state.wizard.maximumDistance = Number(event.target.value); };
      $('#wizard-min-area').oninput = (event) => { state.wizard.minimumPatchArea = Math.max(0, Number(event.target.value) || 0); };
      return;
    }
  }

  function renderReviewStep(body) {
    const selected = state.wizard.selectedComponents;
    const names = selected.map((key) => ({ecological:'Preevaluación territorial',fragmentation:'Fragmentación',connectivity:'Conectividad'}[key]));
    const needsStructure = selected.includes('fragmentation') || selected.includes('connectivity');
    if (!needsStructure) {
      body.innerHTML = `<h3>Revise antes de ejecutar</h3><dl class="rev"><dt>Modo</dt><dd>Preevaluación territorial</dd><dt>Área</dt><dd>${esc(areaLabel())}</dd><dt>Resultado inmediato</dt><dd>Cinco señales, índice de indicios, consistencia y prioridad territorial</dd><dt>Parches y red</dt><dd>No se calculan en esta modalidad</dd></dl><div class="review-note">Resultado indicativo; requiere interpretación y verificación de campo.</div>`;
      return;
    }
    if (needsStructure) {
      body.innerHTML = `<h3>Revise antes de ejecutar</h3><dl class="rev"><dt>Componentes</dt><dd>${esc(names.join(', '))}</dd><dt>Área</dt><dd>${esc(areaLabel())}</dd><dt>Fuente estructural</dt><dd>SINIA–MiAMBIENTE 2021</dd><dt>Distancia</dt><dd>${number(state.wizard.maximumDistance,0)} m</dd><dt>Área mínima</dt><dd>${number(state.wizard.minimumPatchArea,1)} ha</dd></dl><div class="review-note">La conectividad es estructural potencial y no demuestra desplazamiento de fauna.</div>`;
      return;
    }
  }

  $('#wizard-back').addEventListener('click', () => { if (state.wizardStep > 0) { state.wizardStep -= 1; renderWizard(); } });
  $('#wizard-next').addEventListener('click', () => {
    if (state.wizardStep === 0 && !state.wizard.selectedComponents.length) {
      $('#wizard-error').textContent = 'Seleccione al menos un componente.';
      return;
    }
    if (state.wizardStep === 1) {
      if (state.wizard.areaMode === 'draw' && !state.drawnGeometry) { $('#wizard-error').textContent = 'Dibuje un polígono antes de continuar.'; return; }
      if (state.wizard.areaMode === 'subbasin' && !state.wizard.subbasin) { $('#wizard-error').textContent = 'Seleccione una subcuenca.'; return; }
    }
    if (state.wizardStep < 3) { state.wizardStep += 1; renderWizard(); return; }
    closeWizard();
    runAnalysis();
  });

  function analysisPayload() {
    return {
      analyses: state.wizard.selectedComponents,
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
    const fingerprint = selectionFingerprint();
    if (state.result && state.lastAnalysisFingerprint === fingerprint) {
      toast('Este resultado ya corresponde al área y los parámetros seleccionados. No fue necesario recalcular.');
      return;
    }
    const selected = state.wizard.selectedComponents;
    const ecological = selected.includes('ecological');
    const fragmentation = selected.includes('fragmentation');
    const connectivity = selected.includes('connectivity');
    if (selected.length === 1 && ecological) { await runEcologicalEvaluation(); return; }
    if (!ecological && selected.length === 1 && fragmentation) { await runStructuralConnectivity('official_2021', 'fragmentation'); return; }
    if (!ecological && connectivity) { await runStructuralConnectivity('official_2021', 'connectivity'); return; }
    if (!ecological && fragmentation && connectivity) { await runStructuralConnectivity('official_2021', 'connectivity'); return; }
    await runIntegratedEvaluation(selected);
  }

  async function runEcologicalEvaluation() {
    const sequence = ++state.requestSequence;
    setBusy(true, 'Calculando preevaluación territorial', ['Validando el área', 'Consultando las cinco señales', 'Calculando el índice territorial', 'Preparando resultados']);
    $('#open-analysis').disabled = true;
    try {
      const response = await api('/api/v1/evaluations/ecological', {method:'POST', body:JSON.stringify({area:currentAreaRequest(), territory_id:state.territoryId})});
      if (sequence !== state.requestSequence) return;
      state.result = response;
      state.lastAnalysisFingerprint = selectionFingerprint();
      state.eri = null;
      renderEcologicalEvaluation(response);
      $('#download-result').disabled = false;
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(response.cache_hit ? 'Se reutilizó la misma preevaluación.' : 'Preevaluación territorial completada.');
    } catch (error) { toast(error.message, 'error'); }
    finally { stopBusy(); $('#open-analysis').disabled = false; }
  }

  async function runIntegratedEvaluation(selectedComponents = ['ecological','fragmentation','connectivity']) {
    const sequence = ++state.requestSequence;
    $('#open-analysis').disabled = true;
    try {
      setBusy(true, 'Etapa 1 de 2 · Preevaluación territorial', ['Validando el área', 'Consultando las cinco señales', 'Calculando el índice territorial', 'Mostrando el primer resultado']);
      const ecological = await api('/api/v1/evaluations/ecological', {method:'POST', body:JSON.stringify({area:currentAreaRequest(), territory_id:state.territoryId})});
      if (sequence !== state.requestSequence) return;
      state.result = ecological;
      renderEcologicalEvaluation(ecological);
      $('#download-result').disabled = false;
      // La preevaluación es un resultado científico completo por sí mismo. Se
      // sincroniza de inmediato con el Panel antes de iniciar la estructura,
      // para no perderla si la cobertura institucional no está disponible.
      writePortalState({resultId:ecological.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:ecological.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast('Preevaluación lista. Continúa la estructura oficial 2021.');

      setBusy(true, 'Etapa 2 de 2 · Estructura oficial 2021', ['Reutilizando la preevaluación', 'Consultando cobertura oficial', 'Preparando parches', 'Construyendo red', 'Integrando resultados']);
      const response = await api('/api/v1/evaluations/integrated', {method:'POST', body:JSON.stringify({area:currentAreaRequest(), maximum_distance_m:state.wizard.maximumDistance, minimum_patch_area_ha:state.wizard.minimumPatchArea, selected_components:selectedComponents, territory_id:state.territoryId})});
      if (sequence !== state.requestSequence) return;
      state.result = response;
      state.lastAnalysisFingerprint = selectionFingerprint();
      state.eri = null;
      renderIntegratedEvaluation(response);
      writePortalState({resultId:response.result_id,resultTerritoryId:state.territoryId,resultCreatedUtc:response.created_utc,analysisStatus:'available',analysisTerritoryId:state.territoryId,analysisError:null});
      toast(response.cache_hit ? 'Se reutilizó el análisis integral.' : 'Análisis integral completado.');
    } catch (error) {
      toast(error.message, 'error');
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

  function metric(label, value, note = '') {
    const normalized = String(label).toLowerCase();
    const tone = /pérdida|deforest|degrad|aislad|brecha/.test(normalized) ? 'loss'
      : /bosque|regener|cobertura/.test(normalized) ? 'forest'
      : /conex|componente|red|corredor/.test(normalized) ? 'network'
      : /prioridad|visita/.test(normalized) ? 'priority' : 'neutral';
    return `<div class="metric-card" data-tone="${tone}"><span>${esc(label)}</span><b>${esc(value)}</b>${note ? `<small>${esc(note)}</small>` : ''}</div>`;
  }
  function barChart(rows) {
    const maximum = Math.max(1, ...rows.map((row) => Math.abs(Number(row.value || 0))));
    return `<div class="bar-chart">${rows.map((row) => `<div class="bar-row"><span>${esc(row.label)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(1, Math.abs(Number(row.value || 0)) / maximum * 100)}%;background:${row.color}"></div></div><span class="bar-value">${esc(row.formatted)}</span></div>`).join('')}</div>`;
  }

  const scientificTabLabels = {
    summary: 'Resumen', forest: 'Dinámica del bosque',
    connectivity: 'Fragmentación y conectividad', coverages: 'Coberturas oficiales',
  };

  function mountScientificViews(views, initial = 'summary') {
    const normalized = {...views};
    if (normalized.corridors) {
      normalized.connectivity = `${normalized.connectivity || ''}<section class="embedded-science"><h3>Corredores y contexto territorial</h3>${normalized.corridors}</section>`;
    }
    if (normalized.report) {
      normalized.summary = `${normalized.summary || ''}<details class="scientific-details"><summary>Interpretación, limitaciones e informe</summary><div>${normalized.report}</div></details>`;
    }
    const order = ['summary','forest','connectivity','coverages'];
    const entries = order.filter((key) => Boolean(normalized[key])).map((key) => [key, normalized[key]]);
    const active = entries.some(([key]) => key === initial) ? initial : entries[0]?.[0];
    const navigation = $('#results-navigation');
    navigation.hidden = false;
    navigation.innerHTML = `<div class="result-tabs scientific-result-tabs" role="tablist" aria-label="Secciones del resultado">${entries.map(([key]) => `<button role="tab" data-result-tab="${key}" aria-selected="${key === active}">${scientificTabLabels[key] || key}</button>`).join('')}</div>`;
    $('#results-body').innerHTML = entries.map(([key, content]) => `<section class="result-view scientific-result-view" id="view-${key}" role="tabpanel" ${key === active ? '' : 'hidden'}>${content}</section>`).join('');
    const panel = $('#results-panel');
    panel.classList.remove('closed');
    $('#results-reopen').hidden = true;
    $$('[data-result-tab]', panel).forEach((button) => button.addEventListener('click', () => {
      $$('[data-result-tab]', panel).forEach((item) => item.setAttribute('aria-selected', String(item === button)));
      entries.forEach(([key]) => { $(`#view-${key}`).hidden = button.dataset.resultTab !== key; });
    }));
  }

  function corridorResultView(response) {
    const context = response.corridor_context || {};
    const corridors = context.corredores || [];
    const cards = `${metric('Área en corredores',hectares(context.area_en_corredores_ha || 0),`${number(context.porcentaje_aoi_en_corredores || 0,1)} % del territorio`)}${metric('Corredores intersectados',number(corridors.length,0),context.intersecta ? 'Intersección publicada' : 'Sin intersección')}${metric('Distancia al más cercano',context.distancia_corredor_mas_cercano_m == null ? 'No disponible' : `${number(context.distancia_corredor_mas_cercano_m,0)} m`,'Distancia geométrica')}${metric('Corredor Mesoamericano',context.intersecta_mesoamericano ? 'Intersecta' : 'No intersecta',context.fuente || 'Contexto publicado')}`;
    const list = corridors.length ? `<div class="scientific-table-wrap"><table class="scientific-table"><thead><tr><th>Corredor</th><th>Categoría</th><th>Intersección</th></tr></thead><tbody>${corridors.map((item) => `<tr><td>${esc(item.nombre || 'Sin nombre')}</td><td>${esc(item.categoria_etiqueta || item.categoria || '—')}</td><td>${hectares(item.interseccion_ha || 0)}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty-result"><h3>Sin intersecciones publicadas</h3><p>El análisis mantiene la distancia al corredor más cercano cuando está disponible.</p></div>';
    return `<div class="metric-grid">${cards}</div>${list}<div class="interpretation technical"><b>Alcance.</b> Los corredores publicados aportan contexto territorial. Las conexiones modeladas son relaciones estructurales potenciales y no demuestran desplazamiento de fauna.</div>`;
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
    if (response.kind === 'complementary_evidence') renderEvidenceResult(response);
    else if (response.kind === 'ecological_evaluation') renderEcologicalEvaluation(response);
    else if (response.kind === 'integrated_ecological_analysis') renderIntegratedEvaluation(response);
    else if (response.kind === 'official_coverage_2021' || response.kind === 'official_coverage_2023') renderOfficialCoverage(response);
    else if (response.kind === 'structural_connectivity') renderStructuralConnectivity(response);
    else if (response.kind === 'structural_comparison_2021_2023') renderStructuralComparison(response);
    else {
      renderAnalysisMap(response);
      const views = resultViews(response);
      $('#results-title').textContent = 'Resultado del análisis';
      $('#results-subtitle').textContent = `${response.area.label} · ${response.result.anio_inicial}–${response.result.anio_final}`;
      const tabs = ['summary','charts',...(views.concordance ? ['concordance'] : []),'interpretation','eri'];
      const labels = {summary:'Lectura',charts:'Gráficas',concordance:'Concordancia',interpretation:'Interpretación',eri:'ERI'};
      $('#results-body').innerHTML = `<div class="result-tabs" role="tablist">${tabs.map((key,index) => `<button role="tab" data-result-tab="${key}" aria-selected="${index === 0}">${labels[key]}</button>`).join('')}</div>${tabs.map((key,index) => `<div class="result-view" id="view-${key}" ${index ? 'hidden' : ''}>${views[key]}</div>`).join('')}`;
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
    appendResultDownloads(response);
  }

  function appendResultDownloads(response) {
    const body = $('#results-body');
    if (!body || !response.result_id || body.querySelector('.result-download-actions')) return;
    body.querySelectorAll('.download-link').forEach((link) => link.remove());
    const id = encodeURIComponent(response.result_id);
    body.insertAdjacentHTML('beforeend', `<div class="result-download-actions"><a class="btn btn-p" href="/api/v1/results/${id}/report.pdf">Generar informe técnico (PDF)</a><a class="btn btn-s" href="/api/v1/results/${id}/download.zip">Descargar datos y metadatos</a></div>`);
  }

  function structuralInterpretation(landscape = {}, network = {}) {
    const patches = Number(landscape.numero_parches || 0);
    const components = Number(network.numero_componentes || 0);
    const isolated = Number(network.numero_parches_aislados || 0);
    const mainShare = Number(network.porcentaje_nodos_componente_mayor || 0);
    if (!patches) return 'La cobertura oficial no identificó parches forestales válidos dentro del área. Revise la cobertura, el recorte y los datos sin interpretar este resultado como ausencia comprobada de bosque.';
    if (patches === 1) return 'La cobertura oficial forma un solo parche dentro del área. Esta lectura describe continuidad geométrica a la resolución del producto y no conectividad funcional para una especie.';
    if (components <= 1) return `Los ${number(patches,0)} parches pertenecen a una sola red con el umbral elegido. La relación es estructural y depende de la distancia máxima configurada.`;
    return `Los ${number(patches,0)} parches se distribuyen en ${number(components,0)} componentes; ${number(isolated,0)} están aislados y la red principal reúne ${number(mainShare,1)} % de los parches. Conviene revisar las separaciones sin asumir movimiento de fauna.`;
  }

  function patchDistributionRows(result = {}) {
    const features = result.parches_geojson?.features || [];
    const bins = [
      {label:'< 1 ha', min:0, max:1, value:0, color:'#9ccf7c'},
      {label:'1–5 ha', min:1, max:5, value:0, color:'#62a95c'},
      {label:'5–25 ha', min:5, max:25, value:0, color:'#31834d'},
      {label:'≥ 25 ha', min:25, max:Infinity, value:0, color:'#176b45'},
    ];
    features.forEach((feature) => {
      const props = feature.properties || {};
      const area = Number(props.area_ha ?? props.superficie_ha ?? props.area ?? NaN);
      if (!Number.isFinite(area)) return;
      const bin = bins.find((item) => area >= item.min && area < item.max);
      if (bin) bin.value += 1;
    });
    return bins.map((item) => ({...item, formatted:`${number(item.value,0)} parches`}));
  }

  function structuralCharts(result = {}, includeNetwork = true) {
    const landscape = result.metricas_clase || {};
    const network = result.metricas_red || {};
    const sizeRows = patchDistributionRows(result);
    const charts = [];
    if (sizeRows.some((row) => row.value > 0)) {
      charts.push(`<div class="chart-card"><h3>Distribución de tamaños de parche</h3>${barChart(sizeRows)}<p class="chart-note">Conteo de los parches transferidos con el resultado. Si la API generaliza o limita geometrías, consulte la descarga para el detalle completo.</p></div>`);
    }
    if (includeNetwork) {
      const total = Number(landscape.numero_parches || 0);
      const isolated = Math.min(total, Number(network.numero_parches_aislados || 0));
      const connected = Math.max(0, total - isolated);
      charts.push(`<div class="chart-card"><h3>Condición de los parches al umbral elegido</h3>${barChart([
        {label:'En red',value:connected,formatted:`${number(connected,0)} parches`,color:'#225ea8'},
        {label:'Aislados',value:isolated,formatted:`${number(isolated,0)} parches`,color:'#d0442c'},
      ])}<p class="chart-note">El aislamiento depende del umbral de ${number(network.umbral_m || 0,0)} m entre bordes.</p></div>`);
    }
    return charts.join('');
  }

  function prepareResultArea(response) {
    if (state.areaLayer) map.removeLayer(state.areaLayer);
    state.areaLayer = L.geoJSON(response.area.geometry, {style:layerStyle('area')}).addTo(map);
    const bounds = state.areaLayer.getBounds();
    const fitSelectedArea = () => {
      if (!bounds.isValid()) return;
      map.invalidateSize({pan:false});
      map.fitBounds(bounds, {padding:[35,35],maxZoom:14,animate:false});
    };
    fitSelectedArea();
    // El panel derecho cambia de tamaño al montar los resultados. Leaflet debe
    // recalcular su lienzo después de ese cambio para conservar el encuadre del
    // territorio seleccionado al restaurar un resultado desde la URL.
    window.setTimeout(fitSelectedArea, 320);
  }

  function renderEcologicalEvaluation(response) {
    clearResultLayers();
    const result = response.result;
    addTileResultLayer('ecologicalCoincidence', 'Sectores que requieren revisión', result.maps?.coincidence, true);
    addTileResultLayer('ecologicalJrc', 'Estado forestal JRC TMF 2025', result.maps?.jrc_state, false);
    const structure = result.structural_reference_2021;
    if (structure) {
      addResultLayer('structuralPatches', 'Parches oficiales 2021', structure.parches_geojson, '#237A4B', false);
      addResultLayer('structuralConnections', 'Conexiones modeladas 2021', structure.conexiones_geojson, '#225ea8', false);
      addResultLayer('structuralGaps', 'Brechas potenciales 2021', structure.conexiones_potenciales_geojson, '#d0442c', false);
      addResultLayer('structuralRoute', 'Ruta potencial hacia corredor', structure.ruta_corredor_geojson, '#f28e2b', false);
    }
    prepareResultArea(response);
    const labels = {tmf:'JRC TMF',hansen:'Hansen GFC',esri:'ESRI LULC',gedi:'GEDI',ndvi:'Sentinel-2 NDVI'};
    const colors = {tmf:'#005a32',hansen:'#d62828',esri:'#3a7ca5',gedi:'#7a5195',ndvi:'#e9a23b'};
    const signalRows = Object.entries(result.signals).map(([key,active]) => ({label:labels[key],value:active ? result.contributions[key] : 0,formatted:active ? `Activa · +${number(result.contributions[key],1)}` : 'Sin señal',color:active ? colors[key] : '#c9d2df'}));
    const metrics = result.metrics;
    const signalCards = Object.entries(result.signals).map(([key,active]) => metric(labels[key], active ? 'Señal activa' : 'Sin señal', `${number(result.contributions[key],1)} de ${number(result.weights[key],1)} puntos`)).join('');
    const priorityColor = {Alta:'#b42318',Media:'#e9a23b',Preventiva:'#3a7ca5',Baja:'#1f8a70'}[result.priority] || '#0a4393';
    $('#results-title').textContent = 'Preevaluación territorial';
    $('#results-subtitle').textContent = `${response.area.label} · diagnóstico multifuente`;
    const summaryView = `<div class="priority-banner" style="border-left-color:${priorityColor}"><span>Prioridad territorial</span><b>${esc(result.priority)}</b><small>${number(result.score,1)} de ${number(result.maximum_score,1)} puntos</small></div><div class="metric-grid">${metric('Prioridad de visita',result.visit_priority.prioridad_visita || result.visit_priority.prioridad || '—',result.visit_priority.combinacion_territorial || '')}${metric('Consistencia de fuentes',result.consistency.nivel || '—',(result.consistency.fuentes_deterioro || []).join(', '))}</div><div class="interpretation"><b>Lectura integrada.</b> ${esc(result.visit_priority.lectura_integrada || result.consistency.detalle || '')}</div>`;
    const forestView = `<div class="metric-grid">${metric('Deforestación JRC',hectares(metrics.tmf_deforestacion),'2025')}${metric('Degradación JRC',hectares(metrics.tmf_degradacion),'2025')}${metric('Regeneración JRC',hectares(metrics.tmf_recuperacion),'2025')}${metric('Pérdida Hansen',hectares(metrics.hansen_post),'posterior a 2020')}</div><div class="chart-card"><h3>Aportes reales al índice de indicios</h3>${barChart(signalRows)}<p class="chart-note">Las barras representan aportes al índice, no categorías mutuamente excluyentes de superficie.</p></div><div class="res-sec"><h3>Señales por fuente</h3><div class="metric-grid">${signalCards}</div></div>`;
    const connectivityView = structure ? `<div class="metric-grid">${metric('Bosque oficial 2021',hectares(structure.metricas_clase.area_total_bosque_ha),`${number(structure.metricas_clase.porcentaje_paisaje_bosque,1)} % del territorio`)}${metric('Parches',number(structure.metricas_clase.numero_parches,0),`${number(structure.metricas_clase.area_media_parche_ha,2)} ha de media`)}${metric('Componentes',number(structure.metricas_red.numero_componentes,0),`${number(structure.metricas_red.numero_parches_aislados,0)} aislados`)}${metric('Conexiones',number(structure.metricas_red.numero_aristas,0),`umbral ${number(structure.metricas_red.umbral_m,0)} m`)}</div>${structuralCharts(structure,true)}<div class="interpretation"><b>Qué significa.</b> ${esc(structuralInterpretation(structure.metricas_clase,structure.metricas_red))}</div>` : `<div class="empty-result"><h3>No calculado</h3><p>La preevaluación territorial ya está disponible. Para preparar parches y red seleccione Fragmentación, Conectividad o Análisis integral.</p><button class="btn btn-p" type="button" data-open-analysis>Completar análisis estructural</button></div>`;
    const coverageView = `<div class="empty-result"><h3>Coberturas oficiales disponibles</h3><p>Active en el panel izquierdo la cartografía SINIA/MiAMBIENTE que desea explorar. Las capas se muestran sin recalcular este resultado y conservan sus leyendas y años reales.</p></div>`;
    const reportView = `<div class="res-sec"><h3>Limitaciones y verificación</h3><ul class="warning-list">${response.warnings.map(item => `<li>${esc(item)}</li>`).join('')}</ul></div><div id="eri-content" class="empty-result"><h3>ERI complementario</h3><p>Se calcula por separado y no altera el índice de indicios.</p><button class="btn btn-s" id="calculate-eri" type="button">Calcular ERI complementario</button></div>`;
    mountScientificViews({summary:summaryView,forest:forestView,connectivity:connectivityView,corridors:corridorResultView(response),coverages:coverageView,report:reportView});
    $('#calculate-eri')?.addEventListener('click', calculateEri);
    renderLayers(); renderLegend(); setTimeout(() => map.invalidateSize(),220);
  }

  function renderIntegratedEvaluation(response) {
    const evaluation = response.result.evaluation;
    const structure = response.result.structure;
    const selected = response.result.selected_components || ['ecological','fragmentation','connectivity'];
    const showFragmentation = selected.includes('fragmentation');
    const showConnectivity = selected.includes('connectivity');
    renderEcologicalEvaluation({...response, result:evaluation});
    addResultLayer('structuralPatches', 'Parches oficiales 2021', structure.parches_geojson, '#237A4B', showFragmentation || showConnectivity);
    if (showConnectivity) {
      addResultLayer('structuralConnections', 'Conexiones modeladas 2021', structure.conexiones_geojson, '#225ea8', true);
      addResultLayer('structuralGaps', 'Brechas potenciales 2021', structure.conexiones_potenciales_geojson, '#d0442c', false);
      addResultLayer('structuralRoute', 'Ruta potencial hacia corredor', structure.ruta_corredor_geojson, '#f28e2b', true);
    }
    const landscape = structure.metricas_clase || {};
    const network = structure.metricas_red || {};
    $('#results-title').textContent = selected.length === 3 ? 'Análisis integral' : 'Análisis combinado';
    $('#results-subtitle').textContent = `${response.area.label} · señales y estructura oficial 2021`;
    const fragmentationCards = showFragmentation ? `${metric('Bosque oficial 2021',hectares(landscape.area_total_bosque_ha || 0),`${number(landscape.porcentaje_paisaje_bosque || 0,1)} % del área`)}${metric('Parches',number(landscape.numero_parches || 0,0),`${number(landscape.area_media_parche_ha || 0,2)} ha de media`)}${metric('Densidad',number(landscape.densidad_parches_por_100ha || 0,2),'parches / 100 ha')}` : '';
    const connectivityCards = showConnectivity ? `${metric('Componentes',number(network.numero_componentes || 0,0),`${number(network.numero_parches_aislados || 0,0)} aislados`)}${metric('Conexiones',number(network.numero_aristas || 0,0),`umbral ${number(network.umbral_m || 0,0)} m`)}${metric('Brechas',number(network.numero_brechas_potenciales || 0,0),'potenciales')}${metric('Ruta a corredor',structure.conexion_corredor?.conecta ? 'Identificada' : 'No identificada',structure.conexion_corredor?.corredor_nombre || '')}` : '';
    const connectivityView = $('#view-connectivity');
    if (connectivityView) connectivityView.innerHTML = `<div class="res-sec"><h3>${showFragmentation && showConnectivity ? 'Fragmentación y conectividad' : showFragmentation ? 'Fragmentación' : 'Conectividad'}</h3><div class="metric-grid">${fragmentationCards}${connectivityCards}</div>${structuralCharts(structure, showConnectivity)}<div class="interpretation"><b>Qué significa.</b> ${esc(structuralInterpretation(landscape, network))}</div><p class="method-note">Los indicadores estructurales complementan la prioridad territorial; no suman puntos ni demuestran movimiento de fauna.</p></div>`;
    renderLayers(); renderLegend();
  }

  function renderOfficialCoverage(response) {
    clearResultLayers();
    const result = response.result;
    const year = result.year;
    addTileResultLayer(`officialCoverage${year}`, `Cobertura ${year} · categorías`, result.map, true);
    prepareResultArea(response);
    const rows = result.statistics.classes || [];
    const validArea = result.statistics.valid_area_ha ?? result.statistics.total_classified_ha;
    const validPct = result.statistics.valid_coverage_pct ?? (result.statistics.aoi_area_ha ? validArea / result.statistics.aoi_area_ha * 100 : 0);
    $('#results-title').textContent = year === 2021 ? 'Cobertura institucional 2021' : 'Cobertura diagnóstica 2023';
    $('#results-subtitle').textContent = `${response.area.label} · categorías amplias de Panamá`;
    const summaryView = `<div class="review-note"><b>${esc(result.source)}.</b> La leyenda conserva exactamente las categorías disponibles; no se desagrega «Otras Tierras» en usos que el producto no identifica.</div><div class="metric-grid">${metric('Área del AOI',hectares(result.statistics.aoi_area_ha),'denominador territorial')}${metric('Área clasificada',hectares(validArea),`${number(validPct,1)} % del AOI`)}${metric('Sin clasificar',hectares(result.statistics.unclassified_or_nodata_ha),'fuera del denominador por categorías')}</div>`;
    const coverageView = `<div class="chart-card"><h3>Superficie por categoría</h3>${barChart(rows.map((row,index) => ({label:row.label,value:row.area_ha,formatted:hectares(row.area_ha),color:result.map.classes[index]?.color || '#3a7ca5'})))}</div><div class="metric-grid">${rows.map(row => metric(row.label,hectares(row.area_ha),`${number(row.percentage,1)} % del área clasificada`)).join('')}</div>`;
    const reportView = `<div class="res-sec"><h3>Uso permitido y límites</h3><ul class="warning-list">${result.prohibited_interpretations.map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>`;
    mountScientificViews({summary:summaryView,coverages:coverageView,corridors:corridorResultView(response),report:reportView},'coverages');
    renderLayers(); renderLegend(); setTimeout(() => map.invalidateSize(),220);
  }

  function renderStructuralConnectivity(response, scope = 'connectivity') {
    clearResultLayers();
    const result = response.result;
    const year = result.reference_year;
    addResultLayer('structuralPatches', `Parches ${year}`, result.parches_geojson, '#237A4B', true);
    addResultLayer('structuralConnections', `Conexiones modeladas ${year}`, result.conexiones_geojson, '#225ea8', scope === 'connectivity');
    addResultLayer('structuralGaps', `Brechas potenciales ${year}`, result.conexiones_potenciales_geojson, '#d0442c', false);
    addResultLayer('structuralRoute', 'Ruta potencial hacia corredor', result.ruta_corredor_geojson, '#f28e2b', scope === 'connectivity');
    prepareResultArea(response);
    const landscape = result.metricas_clase || {};
    const network = result.metricas_red || {};
    $('#results-title').textContent = scope === 'fragmentation' ? 'Fragmentación oficial 2021' : result.scenario === 'official_2021' ? 'Conectividad oficial 2021' : 'Conectividad diagnóstica 2023';
    $('#results-subtitle').textContent = `${response.area.label} · ${result.authority}`;
    const fragmentationCards = `${metric('Bosque/tierras boscosas',hectares(landscape.area_total_bosque_ha || 0),`${number(landscape.porcentaje_paisaje_bosque || 0,1)} % del AOI`)}${metric('Parches',number(landscape.numero_parches || 0,0),`${number(landscape.area_media_parche_ha || 0,2)} ha de media`)}${metric('Densidad',number(landscape.densidad_parches_por_100ha || 0,2),'parches / 100 ha')}${metric('Densidad de borde',number(landscape.densidad_borde_m_ha || 0,2),'m / ha')}`;
    const connectivityCards = `${metric('Componentes',number(network.numero_componentes || 0,0),`${number(network.numero_parches_aislados || 0,0)} parches aislados`)}${metric('Conexiones',number(network.numero_aristas || 0,0),`umbral ${number(network.umbral_m || 0,0)} m`)}${metric('Brechas potenciales',number(network.numero_brechas_potenciales || 0,0),'separaciones para revisar')}${metric('Contexto exterior',`${number(result.context_radius_m || 0,0)} m`,'no suma superficie al AOI')}`;
    const summaryView = `<div class="metric-grid">${fragmentationCards}${scope === 'connectivity' ? connectivityCards : ''}</div><div class="interpretation"><b>Qué significa.</b> ${esc(structuralInterpretation(landscape, network))}</div>`;
    const connectivityView = `${structuralCharts(result, scope === 'connectivity')}<div class="interpretation technical"><b>Método.</b> ${esc(result.source_adaptation)} ${scope === 'connectivity' ? esc(result.metodo) : 'Los parches se delimitan sobre la cobertura oficial y las superficies se recortan al área objetivo.'}</div>`;
    const reportView = `<div class="res-sec"><h3>Advertencias científicas</h3><ul class="warning-list">${response.warnings.map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>`;
    mountScientificViews({summary:summaryView,connectivity:connectivityView,corridors:corridorResultView(response),report:reportView},'connectivity');
    renderLayers(); renderLegend(); setTimeout(() => map.invalidateSize(),220);
  }

  function renderStructuralComparison(response) {
    clearResultLayers();
    const scenarios = response.result.scenarios || {};
    const reference = scenarios['2021'] || {};
    const diagnostic = scenarios['2023'] || {};
    addResultLayer('comparisonPatches2021', 'Parches estructurales 2021', reference.parches_geojson, '#237A4B', true);
    addResultLayer('comparisonPatches2023', 'Parches diagnósticos 2023', diagnostic.parches_geojson, '#7a5195', false);
    addResultLayer('comparisonConnections2021', 'Conexiones estructurales modeladas 2021', reference.conexiones_geojson, '#225ea8', false);
    addResultLayer('comparisonConnections2023', 'Conexiones estructurales modeladas 2023', diagnostic.conexiones_geojson, '#f28e2b', false);
    addResultLayer('comparisonRoute2021', 'Ruta potencial 2021', reference.ruta_corredor_geojson, '#0a4393', false);
    addResultLayer('comparisonRoute2023', 'Ruta potencial 2023', diagnostic.ruta_corredor_geojson, '#d0442c', false);
    prepareResultArea(response);

    const landscape21 = reference.metricas_clase || {};
    const landscape23 = diagnostic.metricas_clase || {};
    const network21 = reference.metricas_red || {};
    const network23 = diagnostic.metricas_red || {};
    $('#results-title').textContent = 'Escenarios estructurales 2021 y 2023';
    $('#results-subtitle').textContent = `${response.area.label} · diagnósticos paralelos con parámetros equivalentes`;
    const summaryView = `<div class="review-note"><b>Comparación exploratoria.</b> ${esc(response.result.interpretation)}</div><div class="metric-grid">${metric('Bosque 2021',hectares(landscape21.area_total_bosque_ha || 0),`${number(landscape21.porcentaje_paisaje_bosque || 0,1)} % del AOI`)}${metric('Bosque 2023',hectares(landscape23.area_total_bosque_ha || 0),`${number(landscape23.porcentaje_paisaje_bosque || 0,1)} % del AOI`)}${metric('Parches 2021',number(landscape21.numero_parches || 0,0),`${number(landscape21.area_media_parche_ha || 0,2)} ha de media`)}${metric('Parches 2023',number(landscape23.numero_parches || 0,0),`${number(landscape23.area_media_parche_ha || 0,2)} ha de media`)}</div><div class="interpretation"><b>Lectura permitida.</b> Los valores describen la estructura que produce cada cartografía con el mismo umbral. No se publica diferencia de pérdida o ganancia porque la equivalencia temática y geométrica no ha sido demostrada.</div>`;
    const comparisonCharts = `<div class="chart-card"><h3>Superficie forestal por escenario</h3>${barChart([{label:'Referencia 2021',value:landscape21.area_total_bosque_ha,formatted:hectares(landscape21.area_total_bosque_ha || 0),color:'#237A4B'},{label:'Diagnóstico 2023',value:landscape23.area_total_bosque_ha,formatted:hectares(landscape23.area_total_bosque_ha || 0),color:'#7a5195'}])}<p class="chart-note">Barras paralelas; no representan pérdida o ganancia.</p></div><div class="chart-card"><h3>Número de parches</h3>${barChart([{label:'2021',value:landscape21.numero_parches,formatted:`${number(landscape21.numero_parches || 0,0)} parches`,color:'#237A4B'},{label:'2023',value:landscape23.numero_parches,formatted:`${number(landscape23.numero_parches || 0,0)} parches`,color:'#7a5195'}])}</div><div class="chart-card"><h3>Componentes de red</h3>${barChart([{label:'2021',value:network21.numero_componentes,formatted:number(network21.numero_componentes || 0,0),color:'#225ea8'},{label:'2023',value:network23.numero_componentes,formatted:number(network23.numero_componentes || 0,0),color:'#f28e2b'}])}</div><div class="chart-card"><h3>Conexiones modeladas</h3>${barChart([{label:'2021',value:network21.numero_aristas,formatted:number(network21.numero_aristas || 0,0),color:'#225ea8'},{label:'2023',value:network23.numero_aristas,formatted:number(network23.numero_aristas || 0,0),color:'#f28e2b'}])}<p class="chart-note">Umbral común: ${number(response.result.parameters?.maximum_distance_m || 0,0)} m.</p></div>`;
    const connectivityView = `<div class="metric-grid">${metric('Componentes 2021',number(network21.numero_componentes || 0,0),`${number(network21.numero_parches_aislados || 0,0)} aislados`)}${metric('Componentes 2023',number(network23.numero_componentes || 0,0),`${number(network23.numero_parches_aislados || 0,0)} aislados`)}${metric('Conexiones 2021',number(network21.numero_aristas || 0,0),'relaciones estructurales')}${metric('Conexiones 2023',number(network23.numero_aristas || 0,0),'relaciones estructurales')}</div>${comparisonCharts}<div class="interpretation technical"><b>Fuentes.</b> 2021 usa el vector institucional filtrado por categoría; 2023 usa la clase 1 del ráster diagnóstico a 10 m con vecindad de ocho píxeles.</div>`;
    const reportView = `<div class="res-sec"><h3>Advertencias científicas</h3><ul class="warning-list">${response.warnings.map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>`;
    mountScientificViews({summary:summaryView,connectivity:connectivityView,corridors:corridorResultView(response),report:reportView},'connectivity');
    renderLayers(); renderLegend(); setTimeout(() => map.invalidateSize(),220);
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

  $('#results-close').addEventListener('click', () => { window.location.assign('/methodology'); });
  $('#results-reopen').addEventListener('click', () => { $('#results-panel').classList.remove('closed'); $('#results-reopen').hidden = true; setTimeout(() => map.invalidateSize(), 220); });
  $('#download-result').addEventListener('click', () => { if (state.result) window.location.assign(`/api/v1/results/${state.result.result_id}/download.zip`); });
  $('#results-body').addEventListener('click', (event) => {
    if (event.target.closest('[data-open-analysis]')) $('#open-analysis').click();
  });
  $('#reset-platform').addEventListener('click', () => {
    clearResultLayers();
    if (state.areaLayer) { map.removeLayer(state.areaLayer); state.areaLayer = null; }
    state.result = null;
    state.lastAnalysisFingerprint = null;
    state.eri = null;
    state.drawnGeometry = null;
    state.territoryId = null;
    state.wizard = {...state.wizard,selectedComponents:['ecological'],areaMode:'draw',subbasin:'',source:'jrc_tmf',initialYear:2020,finalYear:2025,maximumDistance:500,minimumPatchArea:0};
    localStorage.removeItem('chcp.portal-state.v1');
    $('#results-title').textContent = 'Territorio preparado';
    $('#results-subtitle').textContent = 'Los resultados reales aparecerán aquí sin ocultar el mapa.';
    $('#results-navigation').hidden = true;
    $('#results-navigation').innerHTML = '';
    $('#results-body').innerHTML = '<div class="empty-result scientific-empty"><h3>No calculado</h3><p>Seleccione el área y ejecute una preevaluación, fragmentación, conectividad o análisis integral. Las capas de exploración pueden activarse sin recalcular.</p><button class="btn btn-p" type="button" data-open-analysis>Realizar análisis</button></div>';
    $('#download-result').disabled = true;
    renderQuickFilters(); renderLayers(); renderLegend(); updateAreaLabel();
    if (basinLayer) { basinLayer.addTo(map); map.fitBounds(basinLayer.getBounds(),{padding:[18,18]}); }
    toast('La vista cartográfica fue restablecida.');
  });
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

  function renderPreparedTerritory(summary) {
    if (state.result) return;
    const territory = summary.territory || {};
    const corridors = summary.corridors || {};
    const navigation = $('#results-navigation');
    navigation.hidden = true;
    navigation.innerHTML = '';
    $('#results-title').textContent = territory.nombre || 'Territorio preparado';
    $('#results-subtitle').textContent = `${territory.tipo === 'subcuenca' ? 'Subcuenca de la CHCP' : territory.grupo || 'Contexto territorial'} · listo para explorar`;
    $('#results-body').innerHTML = `<section class="result-view scientific-result-view prepared-territory">
      <div class="prepared-status"><span>Territorio seleccionado</span><b>${esc(territory.nombre || 'Área preparada')}</b><small>El mapa y las capas exploratorias están disponibles sin ejecutar Earth Engine.</small></div>
      <div class="metric-grid">${metric('Superficie territorial',hectares(summary.area_ha || 0),'calculada localmente')}${metric('Corredores intersectados',number(corridors.count || 0,0),(corridors.names || []).join(', ') || 'contexto publicado')}${metric('Puntos críticos',number(summary.critical_points || 0,0),'publicados dentro del territorio')}${metric('Indicadores científicos','No calculados','requieren una ruta de análisis')}</div>
      <div class="interpretation technical"><b>Qué puede hacer ahora.</b> Active coberturas, corredores o NDVI desde el panel izquierdo para explorar el territorio. Use «Realizar análisis» únicamente cuando necesite indicadores científicos nuevos.</div>
      <button class="btn btn-p" type="button" data-open-analysis>Realizar análisis</button>
    </section>`;
  }

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
        renderPreparedTerritory(summary);
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

