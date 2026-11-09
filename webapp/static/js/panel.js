(async function () {
  const {api, escapeHtml: esc, hectares, number, readPortalState, writePortalState, toast} = window.CHCP;
  if (!window.L) return;
  const params = new URLSearchParams(window.location.search);
  const stored = readPortalState();
  let territoryId = params.get('territory') || stored.territoryId || 'cuenca:chcp';
  let summary = null;
  let currentResult = null;
  let config = null;
  const allowedTabs = new Set(['summary','coverage','structure','corridors','interpretation','temporal','concordance','official','eri']);
  const legacyTabAliases = {evaluation:'interpretation', evidence:'coverage', fragmentation:'structure', connectivity:'structure'};
  const requestedTab = new URLSearchParams(window.location.search).get('tab');
  let activeTab = allowedTabs.has(requestedTab) ? requestedTab : (legacyTabAliases[requestedTab] || 'summary');
  let searchTimer;
  let searchItems = [];
  let activeSearchIndex = -1;
  const map = L.map('panel-map', {preferCanvas:true});
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {attribution:'Esri Light Gray Canvas',maxZoom:16}).addTo(map);
  let territoryLayer;
  let resultMapLayers = [];
  let territoryReference = null;
  let corridorReferenceLayer = null;
  let criticalPointReferenceLayer = null;
  let panelPreviewLayer = null;
  let panelPreviewRequest = 0;
  let selectedOfficialSource = '2021_general';

  const officialCoverageProducts = [
    ['1992_historico','Cobertura histórica 1992'],
    ['2000_historico','Cobertura histórica 2000'],
    ['2012_binario','Bosque / no bosque 2012'],
    ['2012_detallado','Uso y cobertura 2012'],
    ['2019_general','Cobertura general 2019'],
    ['2021_general','Cobertura general oficial 2021'],
    ['2021_detallado','Uso y cobertura detallada 2021'],
    ['2023_general','Diagnóstico general 2023'],
  ];

  const mapThemeLabels = {
    summary:'Resumen territorial', coverage:'Cobertura y cambio forestal', structure:'Parches y red estructural',
    corridors:'Corredores publicados y rutas potenciales', interpretation:'Señales y prioridad territorial',
    temporal:'Comparación temporal', concordance:'Concordancia de fuentes',
    official:'Coberturas de Panamá', eri:'ERI complementario',
  };

  function resultLayersVisibleFor(...tabs) { return tabs.includes(activeTab); }

  function clearPanelPreview() {
    panelPreviewRequest += 1;
    if (panelPreviewLayer && map.hasLayer(panelPreviewLayer)) map.removeLayer(panelPreviewLayer);
    panelPreviewLayer = null;
    const legend = document.getElementById('panel-map-legend');
    if (legend) legend.innerHTML = '';
  }

  async function loadOfficialPreview() {
    const requestId = ++panelPreviewRequest;
    const button = document.getElementById('panel-show-official');
    if (button) { button.disabled = true; button.textContent = 'Preparando…'; }
    try {
      const response = await api('/api/v1/layers/preview', {
        method:'POST',
        body:JSON.stringify({source:selectedOfficialSource, area:{mode:'draw',geometry:summary.geometry}}),
      });
      if (requestId !== panelPreviewRequest) return;
      clearPanelPreview();
      panelPreviewRequest = requestId;
      panelPreviewLayer = L.tileLayer(response.layer.tile_url, {opacity:Number(document.getElementById('panel-map-opacity').value)/100,attribution:'SINIA–MiAMBIENTE · Google Earth Engine',maxZoom:18,updateWhenIdle:true,keepBuffer:1}).addTo(map);
      const legend = document.getElementById('panel-map-legend');
      legend.innerHTML = `<b>${esc(response.layer.legend)}</b>${(response.layer.classes || []).map(item => `<span><i style="background:${esc(item.color)}"></i>${esc(item.etiqueta)}</span>`).join('')}<small>${esc(response.layer.limitation || '')}</small>`;
      toast(`${response.layer.legend} está visible.`, 'success');
    } catch (error) {
      if (requestId === panelPreviewRequest) toast(`No se pudo mostrar la cobertura: ${error.message}`, 'error');
    } finally {
      if (button && requestId === panelPreviewRequest) { button.disabled = false; button.textContent = 'Mostrar capa'; }
    }
  }

  function renderThemeLayerControls() {
    const container = document.getElementById('panel-theme-layers');
    const title = document.getElementById('panel-layer-title');
    if (!container || !title) return;
    title.textContent = ({coverage:'Cobertura y cambio',structure:'Parches y red estructural',corridors:'Corredores y conectividad',interpretation:'Señales territoriales',eri:'Resiliencia ecológica'}[activeTab] || 'Capas del análisis');
    if (activeTab === 'coverage' || activeTab === 'official') {
      container.innerHTML = `<label class="panel-layer-select"><span>Producto</span><select id="panel-official-product">${officialCoverageProducts.map(([value,label]) => `<option value="${value}" ${value === selectedOfficialSource ? 'selected' : ''}>${label}</option>`).join('')}</select></label><button type="button" id="panel-show-official">Mostrar capa</button>`;
      document.getElementById('panel-official-product').addEventListener('change', event => { selectedOfficialSource = event.target.value; });
      document.getElementById('panel-show-official').addEventListener('click', loadOfficialPreview);
    } else {
      container.innerHTML = activeTab === 'corridors'
        ? '<p><i class="swatch published"></i><b>Publicados</b><small>Corredores estratégicos y puntos críticos.</small></p><p><i class="swatch modelled"></i><b>Potenciales</b><small>Solo si existe una red calculada.</small></p>'
        : activeTab === 'coverage'
          ? '<p><i class="swatch loss"></i><b>Pérdida y degradación</b><small>Se muestra desde el resultado territorial activo.</small></p>'
          : '<p><i class="swatch context"></i><b>Contexto territorial</b><small>Las capas calculadas aparecen cuando existe un resultado compatible.</small></p>';
    }
  }

  function clearResultMapLayers() {
    resultMapLayers.forEach(layer => map.removeLayer(layer));
    resultMapLayers = [];
  }

  function addGeoJsonResult(geojson, style) {
    if (!geojson?.features?.length) return;
    const layer = L.geoJSON(geojson, {style});
    if (document.getElementById('panel-layer-results')?.checked !== false) layer.addTo(map);
    resultMapLayers.push(layer);
  }

  function renderCurrentResultMap() {
    clearResultMapLayers();
    if (!currentResult?.result) return;
    const result = currentResult.result;
    if (currentResult.kind === 'integrated_ecological_analysis') {
      const evaluation = result.evaluation || {};
      const structure = result.structure || {};
      const selected = result.selected_components || ['ecological','fragmentation','connectivity'];
      const tile = evaluation.maps?.coincidence?.tile_url;
      if (tile && resultLayersVisibleFor('summary','interpretation','coverage')) { const layer = L.tileLayer(tile, {opacity:.78,attribution:'Google Earth Engine'}); if (document.getElementById('panel-layer-results')?.checked !== false) layer.addTo(map); resultMapLayers.push(layer); }
      if ((selected.includes('fragmentation') || selected.includes('connectivity')) && resultLayersVisibleFor('structure','corridors')) addGeoJsonResult(structure.parches_geojson, {color:'#237A4B',weight:.7,fillColor:'#237A4B',fillOpacity:.25});
      if (selected.includes('connectivity') && resultLayersVisibleFor('structure','corridors')) {
        addGeoJsonResult(structure.conexiones_geojson, {color:'#225ea8',weight:2,opacity:.85});
        addGeoJsonResult(structure.ruta_corredor_geojson, {color:'#f28e2b',weight:4,opacity:.95});
      }
    } else if (currentResult.kind === 'ecological_evaluation') {
      const tile = result.maps?.coincidence?.tile_url;
      if (tile && resultLayersVisibleFor('summary','interpretation','coverage')) { const layer = L.tileLayer(tile, {opacity:.78,attribution:'Google Earth Engine'}); if (document.getElementById('panel-layer-results')?.checked !== false) layer.addTo(map); resultMapLayers.push(layer); }
      const structure = result.structural_reference_2021;
      if (resultLayersVisibleFor('structure','corridors')) addGeoJsonResult(structure?.parches_geojson, {color:'#237A4B',weight:.7,fillColor:'#237A4B',fillOpacity:.25});
      if (resultLayersVisibleFor('structure','corridors')) {
        addGeoJsonResult(structure?.conexiones_geojson, {color:'#225ea8',weight:2,opacity:.85});
        addGeoJsonResult(structure?.ruta_corredor_geojson, {color:'#f28e2b',weight:4,opacity:.95});
      }
    } else if (currentResult.kind === 'structural_connectivity') {
      if (resultLayersVisibleFor('summary','coverage','structure','corridors')) addGeoJsonResult(result.parches_geojson, {color:'#237A4B',weight:.7,fillColor:'#237A4B',fillOpacity:.3});
      if (resultLayersVisibleFor('structure','corridors')) {
        addGeoJsonResult(result.conexiones_geojson, {color:'#225ea8',weight:2,opacity:.85});
        addGeoJsonResult(result.conexiones_potenciales_geojson, {color:'#d0442c',weight:2,dashArray:'7 5'});
        addGeoJsonResult(result.ruta_corredor_geojson, {color:'#f28e2b',weight:4,opacity:.95});
      }
    } else if (currentResult.kind === 'official_coverage_2021' || currentResult.kind === 'official_coverage_2023') {
      const tile = result.map?.tile_url;
      if (tile && resultLayersVisibleFor('summary','coverage','official')) { const layer = L.tileLayer(tile, {opacity:.72,attribution:'Google Earth Engine'}); if (document.getElementById('panel-layer-results')?.checked !== false) layer.addTo(map); resultMapLayers.push(layer); }
    }
  }

  function renderReferenceLayers() {
    if (corridorReferenceLayer && map.hasLayer(corridorReferenceLayer)) map.removeLayer(corridorReferenceLayer);
    if (criticalPointReferenceLayer && map.hasLayer(criticalPointReferenceLayer)) map.removeLayer(criticalPointReferenceLayer);
    if (!territoryReference || activeTab !== 'corridors' || document.getElementById('panel-layer-context')?.checked === false) return;
    if (!corridorReferenceLayer) corridorReferenceLayer = L.geoJSON(territoryReference.corridors, {style:{color:'#527b24',weight:2,fillColor:'#9bc53d',fillOpacity:.22}});
    if (!criticalPointReferenceLayer) criticalPointReferenceLayer = L.geoJSON(territoryReference.critical_points, {pointToLayer:(_feature,latlng)=>L.circleMarker(latlng,{radius:6,color:'#8f1f17',weight:2,fillColor:'#f04438',fillOpacity:.9})});
    corridorReferenceLayer.addTo(map);
    criticalPointReferenceLayer.addTo(map);
  }

  function renderActiveMapLayers() {
    document.getElementById('panel-map-theme').textContent = mapThemeLabels[activeTab] || 'Contexto territorial';
    document.getElementById('panel-layer-context-label').textContent = activeTab === 'corridors' ? 'Corredores y puntos publicados' : 'Contexto publicado';
    if (activeTab !== 'coverage' && activeTab !== 'official') clearPanelPreview();
    renderThemeLayerControls();
    renderCurrentResultMap();
    renderReferenceLayers();
    requestAnimationFrame(() => map.invalidateSize());
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
  function metric(label,value,note='') {
    const text = label.toLowerCase();
    const tone = /bosque|regeneración|cobertura forestal/.test(text) ? 'forest' : /agua/.test(text) ? 'water' : /pérdida|deforestación|degradación|brecha|aislado/.test(text) ? 'alert' : 'info';
    return `<article class="metric-card" data-tone="${tone}"><span>${esc(label)}</span><b>${esc(value)}</b><small>${esc(note)}</small></article>`;
  }
  function panelBarChart(title, rows, note='') {
    const maximum = Math.max(1, ...rows.map(row => Number(row.value) || 0));
    return `<div class="panel-chart"><div class="panel-chart-head"><h3>${esc(title)}</h3><span>${esc(rows[0]?.unit || '')}</span></div><div class="panel-bars">${rows.map(row => `<div class="panel-bar"><span>${esc(row.label)}</span><div class="panel-bar-track" aria-hidden="true"><div class="panel-bar-fill" style="width:${Math.max(2,(Number(row.value)||0)/maximum*100)}%;--bar:${row.color || '#073f8c'}"></div></div><b>${esc(row.formatted ?? row.value)}</b></div>`).join('')}</div>${note ? `<p class="panel-chart-note">${esc(note)}</p>` : ''}</div>`;
  }
  function panelWidget(title, question, body, information='') {
    return `<section class="panel-widget"><header><div><span>${esc(question)}</span><h2>${esc(title)}</h2></div>${information ? `<button type="button" class="panel-info-button" aria-expanded="false" aria-label="Metodología y limitaciones">i</button>` : ''}</header><div class="panel-widget-body">${body}</div>${information ? `<div class="panel-widget-info" hidden>${esc(information)}</div>` : ''}</section>`;
  }
  function resultDownloads() {
    if (!currentResult?.result_id) return `<div class="panel-empty-guidance"><b>Informe todavía no disponible</b><span>Ejecute un análisis para generar el PDF y el paquete de datos a partir de un resultado científico identificado.</span></div>`;
    const resultId = encodeURIComponent(currentResult.result_id);
    return `<div class="result-download-actions"><a class="btn btn-p" href="/api/v1/results/${resultId}/report.pdf">Generar informe técnico (PDF)</a><a class="btn btn-s" href="/api/v1/results/${resultId}/download.zip">Descargar datos</a></div>`;
  }
  function period(sourceKey) {
    const source = config?.sources?.[sourceKey];
    if (!source) return 'Referencia fija';
    if (!source.years?.length) return source.version || 'Referencia fija';
    return `${source.years[0]} → ${source.years[source.years.length - 1]}`;
  }
  function moduleShowcase(key) {
    const open = `<a class="btn btn-s showcase-action" href="/platform?territory=${encodeURIComponent(territoryId)}">Crear análisis científico</a>`;
    if (key === 'evaluation') return `<div class="showcase-head"><span>Preevaluación territorial</span><h2>Cinco señales que orientan una revisión</h2><p>Combina indicios sin afirmar que fueron confirmados en campo.</p></div><div class="showcase-source-grid">${metric('JRC TMF','Estado 2025','Deforestación, degradación y regeneración')}${metric('Hansen','2001 → 2025','Pérdida arbórea; la preevaluación usa la señal posterior a 2020')}${metric('ESRI LULC',period('esri_lulc'),'Salida de la clase Trees')}${metric('Sentinel-2 NDVI','2017 → 2025','Disminución del vigor vegetal')}${metric('GEDI','Referencia fija','Altura del dosel')}</div>${panelBarChart('Peso máximo por señal',[{label:'JRC TMF',value:2,formatted:'2.0 pts',color:'#166b51'},{label:'Hansen',value:1.5,formatted:'1.5 pts',color:'#c43d2b'},{label:'ESRI',value:1.5,formatted:'1.5 pts',color:'#276c98'},{label:'GEDI',value:1,formatted:'1.0 pt',color:'#68439a'},{label:'NDVI',value:.5,formatted:'0.5 pts',color:'#6f8f14'}],'Pesos metodológicos originales; esta gráfica no representa un resultado calculado para el territorio.')} ${open}`;
    if (key === 'coverage') return `<div class="showcase-head"><span>Cobertura y uso del suelo</span><h2>Ocho productos oficiales en su contexto espacial</h2><p>Seleccione una cobertura en el control del mapa. La capa y su leyenda se muestran sin ejecutar fragmentación ni conectividad.</p></div><div class="coverage-category-grid"><article style="--cat:#237A4B"><i></i><b>Referencias generales</b><small>2019, 2021 y diagnóstico 2023; cada producto conserva su definición.</small></article><article style="--cat:#4D9221"><i></i><b>Uso y cobertura detallada</b><small>2012 y 2021; la leyenda 2021 sigue parcialmente documentada.</small></article><article style="--cat:#388FC4"><i></i><b>Historia territorial</b><small>1992, 2000 y bosque/no bosque 2012. No forman una serie homogénea.</small></article></div><div class="panel-empty-guidance"><b>Estadísticas territoriales no disponibles en la sesión</b><span>El mapa puede consultarse ahora. Las cifras solo aparecen si existe un resultado almacenado y compatible; no se sustituyen por valores nacionales de ejemplo.</span></div>${open}`;
    if (key === 'fragmentation') return `<div class="showcase-head"><span>Fragmentación</span><h2>Cómo se describe la estructura del bosque</h2><p>Usa la cobertura institucional 2021 para delimitar parches dentro del área seleccionada.</p></div><div class="showcase-source-grid">${metric('Superficie forestal','ha','dentro del área')}${metric('Número de parches','conteo','con área mínima configurable')}${metric('Tamaño medio','ha por parche','sin mezclar contexto exterior')}${metric('Densidad y borde','parches/100 ha · m/ha','métricas estructurales')}</div>${open}`;
    if (key === 'connectivity') return `<div class="showcase-head"><span>Conectividad estructural</span><h2>Relaciones potenciales entre parches</h2><p>No demuestra movimiento de fauna; muestra proximidad geométrica bajo un umbral común.</p></div><div class="showcase-source-grid">${metric('Componentes','red','grupos conectados')}${metric('Parches aislados','conteo y %','según distancia máxima')}${metric('Conexiones','aristas','distancia entre bordes')}${metric('Brechas y rutas','potenciales','contexto de corredores')}</div>${open}`;
    if (key === 'corridors') return `<div class="showcase-head"><span>Corredores publicados</span><h2>Contexto estratégico disponible desde el Panel</h2><p>La intersección y la distancia a los corredores se muestran con la información territorial cargada. La red modelada es un resultado diferente y no se confunde con los corredores oficiales.</p></div><div class="showcase-source-grid">${metric('Intersección','área y %','superposición territorial')}${metric('Proximidad','metros','distancia geométrica')}${metric('Puntos críticos','referencias','información publicada')}${metric('Ruta potencial','resultado modelado','solo cuando se solicita conectividad')}</div>${open}`;
    if (key === 'evidence') return `<div class="showcase-head"><span>Fuentes complementarias</span><h2>Capas para interpretar, no para mezclar</h2><p>Cada producto conserva su definición, resolución y período.</p></div><div class="source-period-list"><article><b>Hansen Global Forest Change</b><strong>2001 → 2025</strong><small>Pérdida de cobertura arbórea</small></article><article><b>Sentinel-2 NDVI</b><strong>2017 → 2025</strong><small>Composición anual de vigor vegetal</small></article><article><b>GEDI</b><strong>Referencia fija</strong><small>Altura del dosel, no serie anual</small></article><article><b>ESA WorldCover</b><strong>2021</strong><small>Cobertura global de referencia</small></article></div>${open}`;
    if (key === 'temporal') return `<div class="showcase-head"><span>Comparación temporal</span><h2>Primer año frente al último disponible</h2><p>El portal usa parámetros equivalentes en ambos períodos y no convierte una selección visual en recálculo científico.</p></div><div class="source-period-list"><article><b>JRC TMF</b><strong>${esc(period('jrc_tmf'))}</strong><small>Cobertura, parches y red para ambos años</small></article><article><b>ESRI LULC</b><strong>${esc(period('esri_lulc'))}</strong><small>Metodología independiente de JRC</small></article></div>${open}`;
    if (key === 'concordance') return `<div class="showcase-head"><span>Concordancia</span><h2>JRC TMF y ESRI sin fusionarlos</h2><p>Compara coincidencias y discrepancias durante el período común 2017–2025; no produce una cobertura “verdadera” combinada.</p></div>${open}`;
    if (key === 'official') return `<div class="showcase-head"><span>Coberturas de Panamá</span><h2>Categorías institucionales disponibles</h2><p>La referencia 2021 y el diagnóstico 2023 se presentan por separado. No se afirma cambio entre ambos.</p></div><div class="coverage-category-grid"><article style="--cat:#237A4B"><i></i><b>Bosques y Otras Tierras Boscosas</b><small>Categoría amplia; no distingue bosque maduro, secundario o manglar.</small></article><article style="--cat:#D8C49C"><i></i><b>Otras Tierras</b><small>No se desagrega en cultivos, pastos o urbano.</small></article><article style="--cat:#388FC4"><i></i><b>Aguas Continentales</b><small>Categoría hídrica institucional.</small></article></div>${open}`;
    if (key === 'eri') return `<div class="showcase-head"><span>ERI complementario</span><h2>Índice de Resiliencia Ecológica</h2><p>Es independiente de la prioridad territorial y no se presenta como una serie anual.</p></div><div class="showcase-source-grid">${metric('Integridad estructural','35 %','peso original')}${metric('Conectividad local','25 %','peso original')}${metric('Estabilidad topográfica','20 %','peso original')}${metric('Proximidad riparia','20 %','peso original')}</div>${open}`;
    return `<div class="showcase-head"><span>Geoportal CHCP</span><h2>Resultados territoriales y contexto espacial</h2><p>Las pestañas reúnen resultados disponibles y capas verificables. La metodología detallada se consulta en su sección propia.</p></div>`;
  }
  function resultTab(key) {
    if (currentResult?.kind === 'integrated_ecological_analysis') {
      const evaluation = currentResult.result?.evaluation || {};
      const structure = currentResult.result?.structure || {};
      const metrics = evaluation.metrics || {};
      const landscape = structure.metricas_clase || {};
      const network = structure.metricas_red || {};
      const selected = currentResult.result?.selected_components || ['ecological','fragmentation','connectivity'];
      if (key === 'evaluation') { const priority=evaluation.priority || 'No disponible'; const color={Alta:'#9f261a',Media:'#8a5700',Preventiva:'#145f8c',Baja:'#176b45'}[priority] || '#073f8c'; const signalRows=Object.entries(evaluation.contributions || {}).map(([source,value])=>({label:source.toUpperCase(),value,formatted:`${number(value,1)} pts`,color:{tmf:'#166b51',hansen:'#c43d2b',esri:'#276c98',gedi:'#68439a',ndvi:'#6f8f14'}[source]})); return `<div class="priority-banner" style="--priority-color:${color}"><span>Prioridad territorial</span><b>${esc(priority)}</b><small>${number(evaluation.score || 0,1)} de ${number(evaluation.maximum_score || 0,1)} puntos</small></div><div class="metric-grid">${metric('Prioridad de visita',evaluation.visit_priority?.prioridad_visita || '—',evaluation.visit_priority?.combinacion_territorial || '')}${metric('Consistencia',evaluation.consistency?.nivel || '—',(evaluation.consistency?.fuentes_deterioro || []).join(', '))}${Object.entries(evaluation.signals || {}).map(([source,active]) => metric(source.toUpperCase(),active ? 'Señal activa' : 'Sin señal',`${number(evaluation.contributions?.[source] || 0,1)} puntos`)).join('')}</div>${panelBarChart('Aportes al índice de indicios',signalRows,'Valores calculados para el territorio; el máximo metodológico es 6.5 puntos.')}`; }
      if (key === 'coverage' || key === 'evidence') return `<div class="metric-grid">${metric('Bosque oficial 2021',hectares(landscape.area_total_bosque_ha || 0),`${number(landscape.porcentaje_paisaje_bosque || 0,1)} % del área`)}${metric('Deforestación JRC',hectares(metrics.tmf_deforestacion || 0),'Estado 2025')}${metric('Degradación JRC',hectares(metrics.tmf_degradacion || 0),'Estado 2025')}${metric('Pérdida Hansen',hectares(metrics.hansen_post || 0),'Posterior a 2020')}</div>`;
      if (key === 'fragmentation') return selected.includes('fragmentation') ? `<div class="metric-grid">${metric('Parches',number(landscape.numero_parches || 0,0),`${number(landscape.area_media_parche_ha || 0,2)} ha de media`)}${metric('Densidad',number(landscape.densidad_parches_por_100ha || 0,2),'parches / 100 ha')}${metric('Borde',number(landscape.densidad_borde_m_ha || 0,2),'m / ha')}</div>` : moduleShowcase('fragmentation');
      if (key === 'connectivity' || key === 'corridors') return selected.includes('connectivity') ? `<div class="metric-grid">${metric('Componentes',number(network.numero_componentes || 0,0),'red estructural')}${metric('Aislados',number(network.numero_parches_aislados || 0,0),`${number(network.porcentaje_parches_aislados || 0,1)} %`)}${metric('Conexiones',number(network.numero_aristas || 0,0),`umbral ${number(network.umbral_m || 0,0)} m`)}${metric('Brechas',number(network.numero_brechas_potenciales || 0,0),'potenciales')}</div><p class="method-note">La estructura complementa la preevaluación y no modifica su puntaje.</p>` : moduleShowcase('connectivity');
      if (key === 'eri') return moduleShowcase('eri');
      return moduleShowcase(key);
    }
    if (currentResult?.kind === 'ecological_evaluation') {
      const result = currentResult.result || {};
      const metrics = result.metrics || {};
      if (key === 'evaluation') { const priority=result.priority || 'No disponible'; const color={Alta:'#9f261a',Media:'#8a5700',Preventiva:'#145f8c',Baja:'#176b45'}[priority] || '#073f8c'; const signalRows=Object.entries(result.contributions || {}).map(([source,value])=>({label:source.toUpperCase(),value,formatted:`${number(value,1)} pts`,color:{tmf:'#166b51',hansen:'#c43d2b',esri:'#276c98',gedi:'#68439a',ndvi:'#6f8f14'}[source]})); return `<div class="priority-banner" style="--priority-color:${color}"><span>Prioridad territorial</span><b>${esc(priority)}</b><small>${number(result.score || 0,1)} de ${number(result.maximum_score || 0,1)} puntos</small></div><div class="metric-grid">${metric('Prioridad de visita',result.visit_priority?.prioridad_visita || '—',result.visit_priority?.combinacion_territorial || '')}${metric('Consistencia',result.consistency?.nivel || '—',(result.consistency?.fuentes_deterioro || []).join(', '))}${Object.entries(result.signals || {}).map(([source,active]) => metric(source.toUpperCase(),active ? 'Señal activa' : 'Sin señal',`${number(result.contributions?.[source] || 0,1)} puntos`)).join('')}</div>${panelBarChart('Aportes al índice de indicios',signalRows,'Valores calculados para el territorio; no son probabilidades.')}<p class="method-note">${esc(result.visit_priority?.lectura_integrada || '')}</p>`; }
      if (key === 'coverage' || key === 'evidence') return `<div class="metric-grid">${metric('Deforestación JRC',hectares(metrics.tmf_deforestacion || 0),'Estado 2025')}${metric('Degradación JRC',hectares(metrics.tmf_degradacion || 0),'Estado 2025')}${metric('Regeneración JRC',hectares(metrics.tmf_recuperacion || 0),'Estado 2025')}${metric('Pérdida Hansen',hectares(metrics.hansen_post || 0),'Posterior al 31/12/2020')}${metric('Salida de árboles ESRI',hectares(metrics.esri_salida || 0),'2017–2024')}${metric('Disminución NDVI',hectares(metrics.ndvi_disminucion || 0),'2020–2025')}</div>`;
      if (key === 'corridors') return `<div class="metric-grid">${metric('Intersección',result.visit_priority?.intersecta_corredor ? 'Sí' : 'No',`${number(result.visit_priority?.porcentaje_aoi_en_corredores || 0,1)} % del área`)}${metric('Valor estratégico',result.visit_priority?.valor_corredor || '—',`Aporte ${number(result.visit_priority?.aporte_corredor || 0,2)}`)}</div><p class="method-note">La intersección aumenta el valor estratégico de visita, pero no demuestra conectividad funcional.</p>`;
      if (key === 'fragmentation' || key === 'connectivity' || key === 'temporal' || key === 'concordance' || key === 'eri') return moduleShowcase(key);
    }
    if (currentResult?.kind === 'official_coverage_2021' || currentResult?.kind === 'official_coverage_2023') {
      const result = currentResult.result || {};
      if (key === 'official' || key === 'coverage') { const rows=(result.statistics?.classes || []); return `<div class="review-note"><b>${esc(result.source)} · ${esc(result.year)}.</b> Se conservan las categorías amplias de la fuente; no se inventan usos más detallados.</div><div class="metric-grid">${rows.map(row => metric(row.label,hectares(row.area_ha),`${number(row.percentage,1)} %`)).join('')}</div>${panelBarChart('Superficie por categoría',rows.map((row,index)=>({label:row.label,value:row.area_ha,formatted:hectares(row.area_ha),color:['#176b45','#9a7a3e','#1976a8'][index]})),'Porcentajes calculados sobre el área clasificada válida.')}`; }
      return moduleShowcase(key);
    }
    if (currentResult?.kind === 'structural_connectivity') {
      const result = currentResult.result || {};
      const landscape = result.metricas_clase || {};
      const network = result.metricas_red || {};
      if (key === 'fragmentation' || key === 'coverage') return `<div class="metric-grid">${metric('Superficie forestal',hectares(landscape.area_total_bosque_ha || 0),`${number(landscape.porcentaje_paisaje_bosque || 0,1)} %`)}${metric('Parches',number(landscape.numero_parches || 0,0),`${number(landscape.area_media_parche_ha || 0,2)} ha de media`)}${metric('Densidad',number(landscape.densidad_parches_por_100ha || 0,2),'parches / 100 ha')}${metric('Borde',number(landscape.densidad_borde_m_ha || 0,2),'m / ha')}</div>`;
      if (key === 'connectivity' || key === 'corridors') return `<div class="metric-grid">${metric('Componentes',number(network.numero_componentes || 0,0),'red estructural')}${metric('Aislados',number(network.numero_parches_aislados || 0,0),`${number(network.porcentaje_parches_aislados || 0,1)} %`)}${metric('Conexiones',number(network.numero_aristas || 0,0),`umbral ${number(network.umbral_m || 0,0)} m`)}${metric('Brechas',number(network.numero_brechas_potenciales || 0,0),'potenciales')}${metric('Ruta a corredor',result.conexion_corredor?.conecta ? 'Identificada' : 'No identificada',result.conexion_corredor?.corredor_nombre || '')}</div><p class="method-note">${esc(result.comparability_warning || '')}</p>`;
      if (key === 'official' && result.scenario === 'diagnostic_2023') return `<p class="method-note">${esc(result.source_adaptation || '')}</p>${resultTab('fragmentation')}`;
      return moduleShowcase(key);
    }
    if (currentResult?.kind === 'complementary_evidence') {
      if (key !== 'evidence' && key !== 'coverage') return moduleShowcase(key);
      const source = currentResult.result || {};
      const cards = Object.entries(source.statistics || {}).filter(([,value]) => !Array.isArray(value) && typeof value !== 'object').map(([label,value]) => metric(label.replaceAll('_',' '), typeof value === 'number' ? number(value,3) : value ?? 'Sin datos', source.source)).join('');
      return `<div class="metric-grid">${cards || metric('Estado','Sin observaciones válidas',source.source || '')}</div><p class="method-note">${esc(source.method || '')}</p><ul class="warning-list">${(source.limitations || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul>`;
    }
    const p = temporalParts();
    if (!p) return moduleShowcase(key);
    if (key === 'coverage' || key === 'temporal') return `<div class="metric-grid">${metric(`Bosque ${p.yi}`,hectares(p.initial.bosque_ha),`${number(p.initial.porcentaje_bosque,1)} %`)}${metric(`Bosque ${p.yf}`,hectares(p.final.bosque_ha),`${number(p.final.porcentaje_bosque,1)} %`)}${metric('Cambio neto',hectares(p.comparison.cambio_neto_bosque_ha),`${p.yi}–${p.yf}`)}${metric('Pérdida detectada',hectares(p.comparison.perdida_bosque_ha),currentResult.result.fuente?.nombre || '')}</div>`;
    if (key === 'fragmentation') return `<div class="metric-grid">${metric(`Parches ${p.yi}`,number(p.ri?.numero_parches,0),'Misma área y parámetros')}${metric(`Parches ${p.yf}`,number(p.rf?.numero_parches,0),'Misma área y parámetros')}${metric('Área media final',hectares(p.rf?.area_media_parche_ha || 0),`Año ${p.yf}`)}${metric('Densidad final',number(p.rf?.densidad_parches_100ha,2),'parches / 100 ha')}</div>`;
    if (key === 'connectivity') return `<div class="metric-grid">${metric(`Componentes ${p.yi}`,number(p.ri?.numero_componentes,0),'Conectividad estructural')}${metric(`Componentes ${p.yf}`,number(p.rf?.numero_componentes,0),'Conectividad estructural')}${metric('Parches aislados final',number(p.rf?.parches_aislados,0),`Umbral ${number(p.result.parametros?.distancia_maxima_m || 0,0)} m`)}${metric('Aristas finales',number(p.rf?.numero_aristas,0),'Proximidad entre bordes')}</div><p class="method-note">Estas relaciones no demuestran desplazamiento de fauna.</p>`;
    if (key === 'concordance' && p.root.mode === 'integrated') return `<div class="metric-grid">${metric('Concordancia de estado',`${number(p.root.concordance?.estado?.concordancia_pct,1)} %`,'JRC y ESRI')}${metric('Diferencia final',hectares(p.root.concordance?.diferencia_superficie_forestal_final_ha || 0),'JRC menos ESRI')}</div>`;
    if (key === 'eri') return moduleShowcase('eri');
    return moduleShowcase(key);
  }
  function renderTab() {
    const view = document.getElementById('territory-tab-view');
    if (!summary) { view.innerHTML = '<div class="panel-skeleton">Cargando territorio…</div>'; return; }
    if (activeTab === 'summary') {
      const summaryBody = `<div class="panel-summary-copy"><p>${currentResult ? `El Panel presenta el resultado territorial disponible para <b>${esc(resultPeriodLabel(currentResult))}</b> y conserva el mapa visible para mantener el contexto espacial.` : 'Este territorio todavía no tiene un resultado científico almacenado en esta sesión. Puede consultar su superficie, corredores publicados y coberturas oficiales sin generar cifras ficticias.'}</p><div class="metric-grid">${metric('Superficie territorial',hectares(summary.area_ha),'Área del territorio seleccionado')}${metric('Corredores presentes',number(summary.corridors.count,0),'Referencias publicadas que intersectan')}${metric('Puntos críticos',number(summary.critical_points,0),'Referencias publicadas dentro')}${metric('Resultado territorial',currentResult ? 'Disponible' : 'Pendiente',currentResult ? resultPeriodLabel(currentResult) : 'No se recalcula al abrir el Panel')}</div>${currentResult ? `<div class="panel-next-step"><div><span>Resultado activo</span><b>Explore Cobertura, estructura y prioridad</b><small>Las pestañas reutilizan el cálculo almacenado.</small></div><a class="btn btn-p" href="/platform?territory=${encodeURIComponent(territoryId)}">Abrir en Plataforma</a></div>` : `<div class="panel-next-step"><div><span>Exploración disponible</span><b>Consulte las capas oficiales desde Cobertura</b><small>Un análisis nuevo solo es necesario para obtener métricas específicas del territorio.</small></div><button class="btn btn-p" type="button" data-open-coverage>Ver coberturas</button></div>`}</div>`;
      view.innerHTML = panelWidget(summary.territory.nombre, '¿Qué se observó en el territorio?', summaryBody, 'El resumen combina contexto territorial precalculado y, cuando existe, el último resultado compatible almacenado. No ejecuta Earth Engine al abrirse.');
      view.querySelector('[data-open-coverage]')?.addEventListener('click', () => setActiveTab('coverage'));
    } else if (activeTab === 'structure') {
      const fragmentation = currentResult ? resultTab('fragmentation') : moduleShowcase('fragmentation');
      const connectivity = currentResult ? resultTab('connectivity') : moduleShowcase('connectivity');
      view.innerHTML = `${panelWidget('Fragmentación del bosque','¿Cómo se distribuyen los parches?',fragmentation,'Las métricas describen estructura espacial y dependen de una cobertura, área mínima y proyección documentadas.')}${panelWidget('Conectividad estructural','¿Qué parches mantienen relaciones potenciales?',connectivity,'La red usa distancia geométrica entre parches. No demuestra movimiento observado de fauna.')}`;
    } else if (activeTab === 'corridors') {
      const context = summary.corridor_analysis || {};
      const modelContext = currentResult ? resultTab('connectivity') : moduleShowcase('corridors');
      const corridorBody = `<div class="panel-summary-copy"><div class="metric-grid">${metric('Área en corredores',hectares(context.area_en_corredores_ha || 0),`${number(context.porcentaje_aoi_en_corredores || 0,1)} % del territorio`)}${metric('Distancia al más cercano',context.distancia_corredor_mas_cercano_m == null ? '—' : `${number(context.distancia_corredor_mas_cercano_m,0)} m`,'Distancia geométrica')}</div><p>${summary.corridors.count ? `${summary.corridors.count} referencia(s) espacial(es) intersectan el territorio.` : 'No se identificaron intersecciones.'}</p>${summary.corridors.names.length ? `<ul>${summary.corridors.names.map((name) => `<li>${esc(name)}</li>`).join('')}</ul>` : ''}<p class="method-note">Fuente: ${esc(context.fuente || summary.metadata.corridor_source)}. La superposición no demuestra conectividad funcional.</p>${modelContext}</div>`;
      view.innerHTML = panelWidget('Corredores publicados y relación estructural','¿Qué parte del territorio coincide con corredores?',corridorBody,'Los corredores publicados, los puntos críticos y las rutas estructurales potenciales son productos distintos y se presentan por separado.');
    } else if (activeTab === 'interpretation') {
      const interpretation = currentResult ? resultTab('evaluation') : moduleShowcase('evaluation');
      view.innerHTML = `${panelWidget('Prioridad e interpretación','¿Por qué conviene revisar el territorio?',interpretation,'La prioridad territorial suma hasta 6.5 puntos. El valor estratégico de corredor es complementario y no altera las señales satelitales.')}${panelWidget('Informe y datos','¿Cómo conservar y compartir el resultado?',resultDownloads(),'El PDF y el ZIP reutilizan el resultado almacenado; no vuelven a ejecutar el análisis científico.')}`;
    } else {
      const labels = {coverage:['Cobertura y cambio','¿Qué cobertura existe y cómo cambia?'],eri:['ERI complementario','¿Qué indica la resiliencia ecológica?'],temporal:['Comparación temporal','¿Qué cambió entre dos años comparables?'],concordance:['Concordancia JRC + ESRI','¿Dónde coinciden o discrepan las fuentes?'],official:['Coberturas de Panamá','¿Qué muestran las referencias institucionales?']};
      const [title,question] = labels[activeTab] || ['Resultados territoriales','¿Qué muestra este módulo?'];
      view.innerHTML = panelWidget(title,question,currentResult ? resultTab(activeTab) : moduleShowcase(activeTab),'La fuente, el año y las limitaciones se conservan en cada resultado; productos no comparables no se fusionan.');
    }
    view.querySelectorAll('.panel-info-button').forEach((button) => button.addEventListener('click', () => { const info=button.closest('.panel-widget')?.querySelector('.panel-widget-info'); if (!info) return; info.hidden=!info.hidden; button.setAttribute('aria-expanded',String(!info.hidden)); }));
    renderActiveMapLayers();
  }
  function renderSummary() {
    document.getElementById('panel-territory-name').textContent = summary.territory.nombre;
    document.getElementById('panel-territory-group').textContent = `${summary.territory.tipo === 'cuenca' ? 'Cuenca principal' : summary.territory.grupo || 'CHCP · subcuenca'} · preevaluación territorial de referencia 2025`;
    document.getElementById('panel-custom-analysis').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
    document.getElementById('territory-kpis').innerHTML = [
      ['Superficie', hectares(summary.area_ha), `${number(summary.area_km2,2)} km²`],
      ['Resultado activo', currentResult ? 'Disponible' : 'Exploración territorial', currentResult ? resultPeriodLabel(currentResult) : `${number(summary.corridors.count,0)} corredor(es) · ${number(summary.critical_points,0)} punto(s) crítico(s)`],
    ].map(([label,value,note]) => `<article><span>${esc(label)}</span><b>${esc(value)}</b><small>${esc(note)}</small></article>`).join('');
    document.getElementById('territory-facts').innerHTML = `<b>${esc(summary.territory.nombre)}</b><span>${hectares(summary.area_ha)}</span><small>${esc(summary.scientific_indicators.message)}</small>`;
    if (territoryLayer) map.removeLayer(territoryLayer);
    territoryLayer = L.geoJSON(summary.geometry, {style:{color:'#0a4393',weight:3,fillColor:'#77cc09',fillOpacity:.12}});
    if (document.getElementById('panel-layer-territory').checked) territoryLayer.addTo(map);
    map.fitBounds(territoryLayer.getBounds(), {padding:[24,24],maxZoom:13});
    renderTab();
  }
  function resultPeriodLabel(result) {
    if (result.kind === 'ecological_evaluation') return 'Preevaluación territorial · períodos fijos';
    if (result.kind === 'integrated_ecological_analysis') return 'Preevaluación + estructura oficial 2021';
    if (result.kind === 'official_coverage_2021') return 'Cartografía institucional · 2021';
    if (result.kind === 'official_coverage_2023') return 'Cartografía oficial · 2023';
    if (result.kind === 'structural_connectivity') return `${result.result.authority} · ${result.result.reference_year}`;
    if (result.kind === 'complementary_evidence') return String(result.result.period?.year || [result.result.period?.initial,result.result.period?.final].filter(Boolean).join('–') || 'Referencia fija');
    return `${result.result.anio_inicial}–${result.result.anio_final}`;
  }
  async function selectTerritory(item) {
    territoryId = item.id;
    writePortalState({territoryId:item.id,territoryName:item.nombre,territoryType:item.tipo});
    currentResult = null;
    history.replaceState({},'',`/panel?territory=${encodeURIComponent(item.id)}&tab=${encodeURIComponent(activeTab)}`);
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
      const period = resultPeriodLabel(currentResult);
      const resultId = encodeURIComponent(currentResult.result_id);
      provenance.innerHTML = `<b>Resultado disponible</b><span>${esc(currentResult.area.label)} · ${esc(period)}</span><small>Procesado ${esc(new Date(currentResult.created_utc).toLocaleString('es-PA'))} · ID ${esc(currentResult.result_id.slice(0,8))}</small><span class="result-provenance-actions"><a href="/api/v1/results/${resultId}/report.pdf">Informe PDF</a><a href="/api/v1/results/${resultId}/download.zip">Datos</a></span>`;
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
  function setActiveTab(tab) {
    if (!allowedTabs.has(tab)) return;
    activeTab = tab;
    document.querySelectorAll('[data-territory-tab]').forEach((item) => item.setAttribute('aria-selected',String(item.dataset.territoryTab === tab)));
    const more = document.getElementById('panel-more-analysis');
    more.value = Array.from(more.options).some(option => option.value === tab) ? tab : '';
    const url = new URL(window.location.href);
    url.searchParams.set('territory',territoryId);
    url.searchParams.set('tab',tab);
    history.replaceState({},'',url);
    renderTab();
  }
  document.querySelectorAll('[data-territory-tab]').forEach((button) => button.addEventListener('click', () => setActiveTab(button.dataset.territoryTab)));
  document.querySelectorAll('[data-territory-tab]').forEach((button) => button.setAttribute('aria-selected', String(button.dataset.territoryTab === activeTab)));
  if (Array.from(document.getElementById('panel-more-analysis').options).some(option => option.value === activeTab)) document.getElementById('panel-more-analysis').value = activeTab;
  document.getElementById('panel-more-analysis').addEventListener('change', (event) => { if (event.target.value) setActiveTab(event.target.value); });
  document.getElementById('panel-draw').addEventListener('click', () => window.location.assign('/platform?draw=1'));
  document.getElementById('panel-custom-analysis').href = `/platform?territory=${encodeURIComponent(territoryId)}`;
  document.getElementById('panel-layer-territory').addEventListener('change', (event) => {
    if (!territoryLayer) return;
    if (event.target.checked && !map.hasLayer(territoryLayer)) territoryLayer.addTo(map);
    if (!event.target.checked && map.hasLayer(territoryLayer)) map.removeLayer(territoryLayer);
  });
  document.getElementById('panel-layer-results').addEventListener('change', (event) => {
    resultMapLayers.forEach(layer => {
      if (event.target.checked && !map.hasLayer(layer)) layer.addTo(map);
      if (!event.target.checked && map.hasLayer(layer)) map.removeLayer(layer);
    });
  });
  document.getElementById('panel-layer-context').addEventListener('change', renderReferenceLayers);
  document.getElementById('panel-fit-territory').addEventListener('click', () => {
    if (territoryLayer) map.fitBounds(territoryLayer.getBounds(), {padding:[24,24],maxZoom:13});
  });
  document.getElementById('panel-analyze').addEventListener('click', () => {
    if (territoryLayer) map.fitBounds(territoryLayer.getBounds(), {padding:[24,24],maxZoom:13});
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.querySelector('.panel-map-shell')?.scrollIntoView({behavior:reducedMotion ? 'auto' : 'smooth',block:'start'});
    requestAnimationFrame(() => map.invalidateSize());
  });
  document.getElementById('panel-map-opacity').addEventListener('input', (event) => {
    const opacity = Number(event.target.value) / 100;
    document.getElementById('panel-map-opacity-value').textContent = `${event.target.value} %`;
    resultMapLayers.forEach(layer => {
      if (typeof layer.setOpacity === 'function') layer.setOpacity(opacity);
      else if (typeof layer.setStyle === 'function') layer.setStyle({opacity,fillOpacity:opacity * .45});
    });
    if (panelPreviewLayer?.setOpacity) panelPreviewLayer.setOpacity(opacity);
  });
  window.addEventListener('storage', async (event) => { if (event.key === 'chcp.portal-state.v1') await loadSummary(); });
  [config, territoryReference] = await Promise.all([api('/api/v1/config'), api('/api/v1/territory')]);
  await loadSummary();
})();
