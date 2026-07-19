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
    var MIN_ZOOM = 9, MAX_ZOOM = 14;

    var map = L.map(mapEl, {
        zoomControl: false,
        attributionControl: true,
        minZoom: MIN_ZOOM,
        maxZoom: MAX_ZOOM,
        scrollWheelZoom: false,
    }).setView([15.98, 120.45], 11);

    L.control.attribution({ prefix: false }).addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: MAX_ZOOM,
    }).addTo(map);

    function goToFullMap(municipality, barangayId) {
        var params = new URLSearchParams();
        if (municipality) params.set('municipality', municipality);
        if (barangayId) params.set('barangay_id', barangayId);
        var qs = params.toString();
        window.location.href = '/pswdo/gis-map' + (qs ? '?' + qs : '');
    }

    var provinceLayer = L.geoJSON(null, {
        style: function (feature) {
            var isTarget = feature.properties.is_target;
            return {
                color: isTarget ? '#8a94a6' : '#c3cad6',
                weight: isTarget ? 1.5 : 1,
                fillColor: '#f4f6fa',
                fillOpacity: isTarget ? 0 : 0.3,
                dashArray: isTarget ? null : '3,3',
            };
        },
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.is_target) {
                layer.bindTooltip('Click to view ' + p.lgu);
                layer.on('click', function () { goToFullMap(p.lgu); });
            }
        },
    }).addTo(map);

    var barangayLayer = L.geoJSON(null, {
        style: function (feature) {
            var p = feature.properties;
            var color = TIER_COLORS[p.priority_tier] || TIER_COLORS.unrated;
            return { color: '#fff', weight: 1, fillColor: color, fillOpacity: 0.65 };
        },
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.has_data) {
                layer.bindTooltip('<strong>' + p.name + '</strong><br>' + p.priority_label, { sticky: true });
                layer.on('click', function () { goToFullMap(p.lgu, p.barangay_id); });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);
    var routeLayer = L.layerGroup().addTo(map);

    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouses.forEach(function (w) {
            var color = w.health === 'Healthy' ? '#27ae60' : (w.health === 'Moderate' ? '#f1c40f' : '#e74c3c');
            L.circleMarker([w.lat, w.lng], {
                radius: 6, color: '#0f2547', weight: 2, fillColor: color, fillOpacity: 0.9,
            }).bindTooltip(w.name).addTo(warehouseLayer);
        });
    }

    function renderRoutes(lines) {
        routeLayer.clearLayers();
        lines.forEach(function (line) {
            L.polyline([line.from, line.to], {
                color: '#3867d6', weight: 2, dashArray: '6,6', opacity: 0.8,
            }).addTo(routeLayer);
        });
    }

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

    fetch('/pswdo/gis-map/data').then(function (r) { return r.json(); }).then(function (data) {
        provinceLayer.addData(data.province_context);
        barangayLayer.addData(data.target_barangays);
        renderWarehouses(data.warehouses);
        renderRoutes(data.in_transit_lines);

        var bounds = L.geoJSON(data.target_barangays).getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
        updateZoomPct();
    });
});
