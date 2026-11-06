(async function () {
  const {api, toast} = window.CHCP;
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
})();

