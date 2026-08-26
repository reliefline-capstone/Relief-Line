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

    // Same PSWDO-vs-CSWDO/MSWDO split as gis_map.js: PSWDO's dashboard
    // preview sees municipality-level demand only, no barangay boundaries.
    var IS_MUNI_ONLY = window.RELIEFLINE_DASHBOARD_ROLE !== 'cswdo_admin';
    var currentMuniData = null;

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
        // Set per-template (pswdo/dashboard.html vs cswdo/dashboard.html) so
        // each role lands on its own GIS Map page/sidebar, not the other's.
        var base = window.RELIEFLINE_GIS_MAP_URL || '/pswdo/gis-map';
        window.location.href = base + (qs ? '?' + qs : '');
    }

    var provinceLayer = L.geoJSON(null, {
        style: function (feature) {
            // Matches gis_map.js's full-map styling — is_target is already
            // scoped server-side (app.routes.pswdo._gis_scope_lgus), so this
            // bold border marks exactly what this account can see.
            var isTarget = feature.properties.is_target;
            if (isTarget && IS_MUNI_ONLY) {
                // PSWDO preview: color each target LGU by its own real
                // demand tier, same as the full GIS Map page, so this
                // preview answers "which municipality needs attention"
                // without waiting for the full page to load.
                var muni = currentMuniData ? currentMuniData.find(function (m) { return m.lgu === feature.properties.lgu; }) : null;
                return {
                    color: '#55606b',
                    weight: 1.5,
                    fillColor: TIER_COLORS[muni ? muni.status_tier : 'unrated'],
                    fillOpacity: 0.55,
                };
            }
            return {
                color: isTarget ? '#0f2547' : '#5b86b8',
                weight: isTarget ? 3 : 1,
                fillColor: isTarget ? '#2c5aa0' : '#bcd4f0',
                fillOpacity: isTarget ? 0.12 : 0.45,
            };
        },
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
        style: function (feature) {
            var p = feature.properties;
            var color = TIER_COLORS[p.priority_tier] || TIER_COLORS.unrated;
            return { color: '#fff', weight: 1, fillColor: color, fillOpacity: 0.65 };
        },
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

    // When the dashboard's month/year filter resolves to a historical event,
    // the template sets this so the mini-map reflects that period's status
    // instead of whatever's active right now.
    var eventId = window.RELIEFLINE_DASHBOARD_EVENT_ID;
    var dataUrl = '/pswdo/gis-map/data' + (eventId ? '?event_id=' + eventId : '');

    fetch(dataUrl).then(function (r) { return r.json(); }).then(function (data) {
        currentMuniData = data.municipalities;
        provinceLayer.addData(data.province_context);
        if (!IS_MUNI_ONLY) barangayLayer.addData(data.target_barangays);
        renderWarehouses(data.warehouses);
        renderRoutes(data.in_transit_lines);

        var bounds = L.geoJSON(data.target_barangays).getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
        updateZoomPct();
    });
});
