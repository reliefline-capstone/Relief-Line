// The small map on the PSWDO dashboard.
// Shows the 3 municipalities (or their barangays) colored by need, plus the warehouses.
document.addEventListener('DOMContentLoaded', function () {
    var mapEl = document.getElementById('dashboard-mini-map');
    if (!mapEl) return;

    var TIER_COLORS = {
        critical: '#e74c3c',
        high: '#e67e22',
        medium: '#f1c40f',
        low: '#27ae60',
        unrated: '#d8dee8',
    };
    var TIER_BORDER_COLORS = {
        critical: '#922b21',
        high: '#9c5310',
        medium: '#9a7d0a',
        low: '#1e8449',
        unrated: '#5d6d7e',
    };
    var MIN_ZOOM = 9, MAX_ZOOM = 14;

    var IS_MUNI_ONLY = window.RELIEFLINE_DASHBOARD_ROLE !== 'cswdo_admin';
    var currentMuniData = null;

    var map = L.map(mapEl, {
        zoomControl: false,
        attributionControl: false,
        minZoom: MIN_ZOOM,
        maxZoom: MAX_ZOOM,
        scrollWheelZoom: false,
        zoomAnimation: false,
    }).setView([15.98, 120.45], 11);

    L.control.attribution({ prefix: false }).addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: MAX_ZOOM,
    }).addTo(map);

    // Opens the full GIS Map page zoomed to the clicked municipality or barangay.
    function goToFullMap(municipality, barangayId) {
        var params = new URLSearchParams();
        if (municipality) params.set('municipality', municipality);
        if (barangayId) params.set('barangay_id', barangayId);
        var qs = params.toString();
        var base = window.RELIEFLINE_GIS_MAP_URL || '/pswdo/gis-map';
        window.location.href = base + (qs ? '?' + qs : '');
    }

    var provinceLayer = L.geoJSON(null, {
        // Colors each municipality on the small map (by need level, or grey for other towns).
        style: function (feature) {
            var isTarget = feature.properties.is_target;
            if (isTarget && IS_MUNI_ONLY) {
                var muni = currentMuniData ? currentMuniData.find(function (m) { return m.lgu === feature.properties.lgu; }) : null;
                var tier = muni ? muni.status_tier : 'unrated';
                return {
                    color: TIER_BORDER_COLORS[tier],
                    weight: 2,
                    fillColor: TIER_COLORS[tier],
                    fillOpacity: 0.55,
                };
            }
            if (isTarget) {
                return { color: '#0f2547', weight: 3, fillColor: '#2c5aa0', fillOpacity: 0.12 };
            }
            return { color: '#6b7280', weight: 1.2, fillColor: '#c3c7d1', fillOpacity: 0.5 };
        },
        // Adds the hover label (name, predicted demand) and the click action to each municipality.
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.is_target) {
                var muni = currentMuniData ? currentMuniData.find(function (m) { return m.lgu === p.lgu; }) : null;
                var demandLine = muni ? ('<br>Predicted Demand: ' + (muni.predicted_demand || 0).toLocaleString() + ' packs<br>Demand Level: ' + muni.status_label) : '';
                layer.bindTooltip('<strong>' + p.lgu + '</strong>' + demandLine + '<br><em>Click to view</em>');
                layer.on('click', function () { goToFullMap(p.lgu); });
            }
        },
    }).addTo(map);

    var barangayLayer = L.geoJSON(null, {
        // Colors each barangay by its priority level.
        style: function (feature) {
            var p = feature.properties;
            var color = TIER_COLORS[p.priority_tier] || TIER_COLORS.unrated;
            return { color: '#fff', weight: 1, fillColor: color, fillOpacity: 0.65 };
        },
        // Adds the hover label to each barangay (name, priority, food packs requested or estimated).
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.has_data) {
                var sourceLabel = p.food_packs_source === 'request' ? 'requested' : 'estimated';
                layer.bindTooltip(
                    '<strong>' + p.name + '</strong><br>' + p.priority_label +
                    '<br>' + (p.food_packs_current || 0).toLocaleString() + ' food packs ' + sourceLabel,
                    { sticky: true }
                );
                layer.on('click', function () { goToFullMap(p.lgu, p.barangay_id); });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);

    // Draws a dot for each warehouse, colored by stock health
    // (green = Healthy, yellow = Moderate, red = Low).
    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouses.forEach(function (w) {
            var color = w.health === 'Healthy' ? '#27ae60' : (w.health === 'Moderate' ? '#f1c40f' : '#e74c3c');
            L.circleMarker([w.lat, w.lng], {
                radius: 6, color: '#0f2547', weight: 2, fillColor: color, fillOpacity: 0.9,
            }).bindTooltip(w.name).addTo(warehouseLayer);
        });
    }

    // Shows the current zoom level as a percentage.
    function updateZoomPct() {
        var pct = Math.round(((map.getZoom() - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM)) * 100);
        var el = document.getElementById('dashboard-map-zoom-pct');
        if (el) el.textContent = pct + '%';
    }
    map.on('zoomend', updateZoomPct);

    var zoomInBtn = document.getElementById('dashboard-map-zoom-in');
    var zoomOutBtn = document.getElementById('dashboard-map-zoom-out');
    if (zoomInBtn) zoomInBtn.addEventListener('click', function () { map.zoomIn(); });
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', function () { map.zoomOut(); });

    var eventId = window.RELIEFLINE_DASHBOARD_EVENT_ID;
    var dataUrl = '/pswdo/gis-map/data' + (eventId ? '?event_id=' + eventId : '');

    fetch(dataUrl).then(function (r) { return r.json(); }).then(function (data) {
        currentMuniData = data.municipalities;
        provinceLayer.addData(data.province_context);
        if (!IS_MUNI_ONLY) barangayLayer.addData(data.target_barangays);
        renderWarehouses(data.warehouses);

        var bounds = L.geoJSON(data.target_barangays).getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
        updateZoomPct();
    });
});
