document.addEventListener('DOMContentLoaded', function () {
    var TIER_COLORS = {
        critical: '#e74c3c',
        high: '#e67e22',
        medium: '#f1c40f',
        low: '#27ae60',
        unrated: '#d8dee8',
    };
    var TIER_RANK = { critical: 4, high: 3, medium: 2, low: 1, unrated: 0 };

    var map = L.map('gis-map', { zoomControl: true }).setView([15.98, 120.45], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Drill-down state: overview -> municipality -> barangay-list -> barangay-detail
    var state = { level: 'overview', lgu: null, barangayId: null, barangayName: null };
    var currentData = null;

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function fmt(n) { return (n || 0).toLocaleString(); }

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
                layer.bindTooltip('Click to view ' + escapeHtml(p.lgu));
                layer.on('click', function () { setLevel('municipality', p.lgu); });
                layer.on('mouseover', function () { layer.setStyle({ weight: 2.5 }); });
                layer.on('mouseout', function () { layer.setStyle({ weight: 1.5 }); });
            } else {
                layer.bindTooltip(escapeHtml(p.name));
            }
        },
    }).addTo(map);

    var barangayLayer = L.geoJSON(null, {
        style: function (feature) {
            var p = feature.properties;
            var color = TIER_COLORS[p.priority_tier] || TIER_COLORS.unrated;
            var isSelected = state.level === 'barangay-detail' && state.barangayId === p.barangay_id;
            return {
                color: isSelected ? '#3867d6' : '#fff',
                weight: isSelected ? 3 : 1,
                fillColor: color,
                fillOpacity: 0.65,
            };
        },
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.has_data) {
                layer.bindTooltip('<strong>' + escapeHtml(p.name) + '</strong><br>' + escapeHtml(p.priority_label), { sticky: true });
                layer.on('click', function () { setLevel('barangay-detail', p.lgu, p.barangay_id, p.name); });
            } else {
                layer.bindTooltip(escapeHtml(p.name) + ' — no data on record', { sticky: true });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);
    var routeLayer = L.layerGroup().addTo(map);

    function warehouseCode(name) {
        var m = name.match(/warehouse\s+([a-z0-9]+)/i);
        if (m) return 'WH-' + m[1].toUpperCase();
        return name.split(' ').map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase();
    }

    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouses.forEach(function (w) {
            var healthClass = (w.health || 'low').toLowerCase();
            var icon = L.divIcon({
                className: 'gis-wh-marker gis-wh-' + healthClass,
                html: '<span>' + escapeHtml(warehouseCode(w.name)) + '</span>',
                iconSize: [60, 26],
                iconAnchor: [30, 13],
            });
            var marker = L.marker([w.lat, w.lng], { icon: icon });
            marker.bindPopup(
                '<strong>' + escapeHtml(w.name) + '</strong>' +
                '<span>' + escapeHtml(w.area_covered) + '</span>' +
                '<span>' + fmt(w.food_pack_qty) + ' / ' + fmt(w.capacity) + ' packs (' + w.pct.toFixed(0) + '%)</span>'
            );
            marker.addTo(warehouseLayer);
        });
    }

    function renderRoutes(lines) {
        routeLayer.clearLayers();
        lines.forEach(function (line) {
            L.polyline([line.from, line.to], {
                color: '#3867d6', weight: 2, dashArray: '6,6', opacity: 0.8,
            }).bindTooltip('In transit to ' + escapeHtml(line.barangay)).addTo(routeLayer);
        });
    }

    function renderStats(stats) {
        return '' +
            '<section class="stat-cards gis-stat-cards">' +
            '<div class="stat-card">' +
            '<div class="stat-icon orange">' + ICON.mapPin + '</div>' +
            '<span class="stat-value">' + fmt(stats.affected_barangays) + '</span>' +
            '<span class="stat-label">Affected Barangays</span>' +
            '<span class="stat-sub">of ' + fmt(stats.total_barangays) + ' tracked</span>' +
            '</div>' +
            '<div class="stat-card">' +
            '<div class="stat-icon purple">' + ICON.users + '</div>' +
            '<span class="stat-value">' + fmt(stats.total_affected_families) + '</span>' +
            '<span class="stat-label">Affected Families</span>' +
            '</div>' +
            '<div class="stat-card">' +
            '<div class="stat-icon green">' + ICON.package + '</div>' +
            '<span class="stat-value">' + fmt(stats.total_food_packs) + '</span>' +
            '<span class="stat-label">Packs Available</span>' +
            '</div>' +
            '</section>';
    }

    // Minimal inline icon set matching app/utils/icons.py, kept local since this
    // panel is assembled client-side (server-rendered {{ icon() }} can't reach it).
    var ICON = {
        mapPin: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e67e22" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        users: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        package: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#20bf6b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 9.4L7.5 4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
        arrow: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
        clipboard: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
        download: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    };

    function tierBadge(tier, label) {
        return '<span class="badge-priority badge-priority-' + tier + '"><i class="priority-dot"></i> ' + escapeHtml(label) + '</span>';
    }

    function renderOverviewPanel() {
        var html = renderStats(currentData.stats);

        html += '<section class="panel"><div class="panel-header"><h3>Municipalities</h3></div><div class="gis-muni-list">';
        currentData.municipalities.forEach(function (m) {
            html += '<div class="gis-priority-row gis-clickable" data-nav="municipality" data-lgu="' + escapeHtml(m.lgu) + '">' +
                '<div><strong>' + escapeHtml(m.lgu) + '</strong><span>' + fmt(m.affected_barangays) + ' of ' + fmt(m.total_barangays) + ' barangays affected</span></div>' +
                '<div class="gis-priority-row-right">' + tierBadge(m.status_tier, m.status_label) + '</div>' +
                '</div>';
        });
        html += '</div></section>';

        html += '<section class="panel"><div class="panel-header"><h3>Priority Barangays</h3></div><div>';
        if (!currentData.priority_barangays.length) {
            html += '<p class="empty-note">No priority barangays right now.</p>';
        } else {
            currentData.priority_barangays.forEach(function (p) {
                html += '<div class="gis-priority-row gis-clickable" data-nav="barangay-detail" data-lgu="' + escapeHtml(p.lgu) + '" data-barangay-id="' + p.barangay_id + '" data-barangay-name="' + escapeHtml(p.name) + '">' +
                    '<div><strong>' + escapeHtml(p.name) + '</strong><span>' + escapeHtml(p.lgu) + '</span></div>' +
                    '<div class="gis-priority-row-right"><strong>' + fmt(p.affected_families) + ' families</strong>' + tierBadge(p.priority_tier, p.priority_label) + '</div>' +
                    '</div>';
            });
        }
        html += '</div></section>';
        return html;
    }

    function reliefRows(relief) {
        return '' +
            '<div class="dd-summary-row"><span>Food Packs Requested</span><strong>' + fmt(relief.requested) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Food Packs Approved</span><strong>' + fmt(relief.approved) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Food Packs Released</span><strong class="text-green">' + fmt(relief.released) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Remaining Need</span><strong class="text-red">' + fmt(relief.remaining) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Delivery Progress</span><strong>' + relief.progress_pct + '%</strong></div>';
    }

    function renderMunicipalityPanel(lgu) {
        var m = currentData.municipalities.find(function (x) { return x.lgu === lgu; });
        if (!m) return '<p class="empty-note">Municipality not found.</p>';

        var html = '<section class="panel">';
        html += '<div class="panel-header"><h3>' + escapeHtml(m.lgu) + '</h3>' + tierBadge(m.status_tier, m.status_label) + '</div>';
        html += '<span class="rd-sub" style="display:block; margin-top:-10px; margin-bottom:14px;">Province of Pangasinan</span>';
        if (currentData.event) {
            html += '<div class="dd-summary-row"><span>Active Event</span><strong>' + escapeHtml(currentData.event.event_name) +
                (currentData.event.weather_condition ? ' · ' + escapeHtml(currentData.event.weather_condition) : '') + '</strong></div>';
        }
        html += '<div class="dd-summary-row"><span>Affected Barangays</span><strong>' + fmt(m.affected_barangays) + ' / ' + fmt(m.total_barangays) + '</strong></div>';
        html += '<div class="dd-summary-row"><span>Affected Families</span><strong>' + fmt(m.total_affected_families) + '</strong></div>';
        html += '<div class="dd-summary-row"><span>Total Population (tracked barangays)</span><strong>' + fmt(m.total_population) + '</strong></div>';
        html += '</section>';

        html += '<section class="panel"><div class="panel-header"><h3>Relief Statistics</h3></div>' + reliefRows(m.relief) + '</section>';

        html += '<section class="panel"><div class="panel-header"><h3>Warehouse Information</h3></div>';
        if (m.warehouse) {
            html += '<div class="dd-summary-row"><span>Assigned Warehouse</span><strong>' + escapeHtml(m.warehouse.name) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Approx. Distance</span><strong>' + (m.warehouse.distance_km != null ? (m.warehouse.distance_km < 0.5 ? 'Same municipality' : '~' + m.warehouse.distance_km + ' km') : '—') + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Current Stock</span><strong>' + (m.warehouse.food_pack_qty != null ? fmt(m.warehouse.food_pack_qty) + ' / ' + fmt(m.warehouse.capacity) + ' packs' : '—') + '</strong></div>';
        } else {
            html += '<p class="empty-note">No warehouse data available.</p>';
        }
        html += '</section>';

        html += '<section class="panel"><div class="panel-header"><h3>Distribution Status</h3></div>';
        if (m.current_distribution) {
            var d = m.current_distribution;
            html += '<div class="dd-summary-row"><span>Current Distribution</span><strong>D-' + d.distribution_id + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Truck</span><strong>' + escapeHtml(d.vehicle) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Driver</span><strong>' + escapeHtml(d.driver) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>ETA</span><strong>' + escapeHtml(d.eta) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Status</span><span class="badge-status badge-status-' + d.status + '">' + escapeHtml(d.status_label) + '</span></div>';
        } else {
            html += '<p class="empty-note">No active distribution route right now.</p>';
        }
        html += '</section>';

        html += '<section class="panel">';
        html += '<button type="button" class="btn-decision btn-partial dd-full-width" data-external="distribution" data-lgu="' + escapeHtml(m.lgu) + '">' + ICON.arrow + ' View Distribution</button>';
        html += '<button type="button" class="btn-outline dd-full-width" data-external="relief" data-lgu="' + escapeHtml(m.lgu) + '" style="justify-content:center; margin-top:10px;">' + ICON.clipboard + ' View Relief Request</button>';
        html += '<button type="button" class="btn-decision dd-full-width gis-btn-dark" data-nav="barangay-list" data-lgu="' + escapeHtml(m.lgu) + '" style="margin-top:10px;">' + ICON.mapPin + ' View Barangays</button>';
        html += '<button type="button" class="btn-outline dd-full-width" data-external="report" data-lgu="' + escapeHtml(m.lgu) + '" style="justify-content:center; margin-top:10px;">' + ICON.download + ' Generate Report</button>';
        html += '</section>';

        return html;
    }

    function renderBarangayListPanel(lgu) {
        var statusFilter = document.getElementById('filter-status').value;
        var features = currentData.target_barangays.features.filter(function (f) {
            return f.properties.lgu === lgu && (!statusFilter || f.properties.status === statusFilter);
        });
        var withData = features.filter(function (f) { return f.properties.has_data; });
        var affected = withData.filter(function (f) { return f.properties.status !== 'normal'; });

        withData.sort(function (a, b) {
            var ra = TIER_RANK[a.properties.priority_tier] || 0;
            var rb = TIER_RANK[b.properties.priority_tier] || 0;
            if (rb !== ra) return rb - ra;
            return b.properties.affected_families - a.properties.affected_families;
        });

        var html = '<section class="panel">';
        html += '<div class="panel-header"><h3>' + escapeHtml(lgu) + '</h3></div>';
        html += '<span class="rd-sub" style="display:block; margin-bottom:14px;">' + fmt(affected.length) + ' of ' + fmt(withData.length) + ' barangays affected</span>';
        html += '<div class="gis-barangay-list">';
        if (!withData.length) {
            html += '<p class="empty-note">No barangays match the current filters.</p>';
        } else {
            withData.forEach(function (f) {
                var p = f.properties;
                html += '<div class="gis-priority-row gis-clickable" data-nav="barangay-detail" data-lgu="' + escapeHtml(lgu) + '" data-barangay-id="' + p.barangay_id + '" data-barangay-name="' + escapeHtml(p.name) + '">' +
                    '<div><strong>' + escapeHtml(p.name) + '</strong><span>' + fmt(p.affected_families) + ' families</span></div>' +
                    '<div class="gis-priority-row-right">' + tierBadge(p.priority_tier, p.priority_label) + '</div>' +
                    '</div>';
            });
        }
        html += '</div></section>';
        return html;
    }

    function renderBarangayDetailLoading() {
        return '<section class="panel"><p class="empty-note">Loading barangay details…</p></section>';
    }

    function renderBarangayDetail(b) {
        var eventId = document.getElementById('filter-event').value;
        var html = '<section class="panel">';
        html += '<div class="panel-header"><h3>' + escapeHtml(b.name) + '</h3>' + tierBadge(b.priority_tier, b.priority_label) + '</div>';
        html += '<span class="rd-sub" style="display:block; margin-top:-10px; margin-bottom:14px;">Barangay · ' + escapeHtml(b.lgu) + '</span>';
        html += '<div class="dd-kv-list">';
        html += '<div><span>Affected Families</span><strong>' + fmt(b.affected_families) + '</strong></div>';
        html += '<div><span>Population</span><strong>' + fmt(b.population) + '</strong></div>';
        html += '<div><span>Households</span><strong>' + fmt(b.num_households) + '</strong></div>';
        html += '<div><span>Poverty Incidence</span><strong>' + (b.poverty_incidence != null ? b.poverty_incidence + '%' : '—') + '</strong></div>';
        html += '<div><span>Disaster Risk Index</span><strong>' + (b.disaster_risk_index != null ? b.disaster_risk_index : '—') + '</strong></div>';
        html += '<div><span>Past Calamity Frequency</span><strong>' + fmt(b.past_calamity_freq) + '</strong></div>';
        html += '</div></section>';

        html += '<section class="panel"><div class="panel-header"><h3>Relief Statistics</h3></div>' + reliefRows(b.relief) + '</section>';

        html += '<section class="panel"><div class="panel-header"><h3>Distribution History</h3></div>';
        if (!b.distribution_history.length) {
            html += '<p class="empty-note">No distribution records for this barangay yet.</p>';
        } else {
            html += '<table class="wh-table"><thead><tr><th>DATE</th><th>PACKS</th><th>STATUS</th></tr></thead><tbody>';
            b.distribution_history.forEach(function (d) {
                html += '<tr><td>' + escapeHtml(d.date) + '</td><td>' + fmt(d.packs) + '</td>' +
                    '<td><span class="badge-status badge-status-' + d.status + '">' + escapeHtml(d.status_label) + '</span></td></tr>';
            });
            html += '</tbody></table>';
        }
        html += '</section>';

        html += '<section class="panel">';
        html += '<button type="button" class="btn-decision btn-partial dd-full-width" data-external="distribution" data-lgu="' + escapeHtml(b.lgu) + '">' + ICON.arrow + ' View Distribution</button>';
        html += '<button type="button" class="btn-outline dd-full-width" data-external="relief" data-lgu="' + escapeHtml(b.lgu) + '" style="justify-content:center; margin-top:10px;">' + ICON.clipboard + ' View Relief Request</button>';
        html += '</section>';
        return html;
    }

    function renderPanel() {
        var panel = document.getElementById('gis-info-panel');
        if (!currentData) { panel.innerHTML = '<p class="empty-note">Loading…</p>'; return; }

        if (state.level === 'overview') {
            panel.innerHTML = renderOverviewPanel();
        } else if (state.level === 'municipality') {
            panel.innerHTML = renderMunicipalityPanel(state.lgu);
        } else if (state.level === 'barangay-list') {
            panel.innerHTML = renderBarangayListPanel(state.lgu);
        } else if (state.level === 'barangay-detail') {
            panel.innerHTML = renderBarangayDetailLoading();
            var eventId = document.getElementById('filter-event').value;
            var url = '/pswdo/gis-map/barangay/' + state.barangayId + (eventId ? '?event_id=' + eventId : '');
            var requestedBarangayId = state.barangayId;
            fetch(url).then(function (r) { return r.json(); }).then(function (b) {
                if (state.level === 'barangay-detail' && state.barangayId === requestedBarangayId) {
                    panel.innerHTML = renderBarangayDetail(b);
                }
            });
        }
    }

    function renderBreadcrumb() {
        var el = document.getElementById('gis-breadcrumb');
        var parts = [];
        parts.push({ label: 'Province', nav: 'overview' });
        if (state.lgu) {
            parts.push({ label: state.lgu, nav: 'municipality', lgu: state.lgu });
        }
        if (state.level === 'barangay-list' || state.level === 'barangay-detail') {
            parts.push({ label: 'Barangays', nav: 'barangay-list', lgu: state.lgu });
        }
        if (state.level === 'barangay-detail') {
            parts.push({ label: state.barangayName, nav: 'barangay-detail', lgu: state.lgu, barangayId: state.barangayId, barangayName: state.barangayName });
        }

        el.innerHTML = parts.map(function (p, i) {
            var isLast = i === parts.length - 1;
            if (isLast) return '<span class="gis-crumb-current">' + escapeHtml(p.label) + '</span>';
            var attrs = 'data-nav="' + p.nav + '"';
            if (p.lgu) attrs += ' data-lgu="' + escapeHtml(p.lgu) + '"';
            return '<span class="gis-crumb-link" ' + attrs + '>' + escapeHtml(p.label) + '</span><span class="gis-crumb-sep">/</span>';
        }).join('');
    }

    function allTargetBounds() {
        if (!currentData || !currentData.target_barangays.features.length) return null;
        return L.geoJSON(currentData.target_barangays).getBounds();
    }

    function focusMap() {
        if (!currentData) return;
        if (state.level === 'overview') {
            var b = allTargetBounds();
            if (b && b.isValid()) map.fitBounds(b.pad(0.05));
            return;
        }
        var feats = currentData.target_barangays.features.filter(function (f) { return f.properties.lgu === state.lgu; });
        if (!feats.length) return;
        var bounds = L.geoJSON({ type: 'FeatureCollection', features: feats }).getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.1));
    }

    function renderRoutesTable() {
        var routes = currentData ? currentData.routes_table : [];
        if (state.lgu) {
            routes = routes.filter(function (r) { return r.to_municipality === state.lgu; });
        }
        document.getElementById('routes-count').textContent = routes.length;
        var body = document.getElementById('routes-table-body');
        if (!routes.length) {
            body.innerHTML = '<tr><td colspan="7" class="empty-note" style="text-align:center; padding:24px;">No active distribution routes right now.</td></tr>';
            return;
        }
        body.innerHTML = routes.map(function (r) {
            return '<tr>' +
                '<td>D-' + r.distribution_id + '</td>' +
                '<td>' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_barangay) + ' / ' + escapeHtml(r.to_municipality) + '</td>' +
                '<td>' + escapeHtml(r.vehicle) + '</td>' +
                '<td>' + escapeHtml(r.driver) + '</td>' +
                '<td>' + fmt(r.packs) + '</td>' +
                '<td><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></td>' +
                '<td>' + escapeHtml(r.eta) + '</td>' +
                '</tr>';
        }).join('');
    }

    function applyClientFilters() {
        if (!currentData) return;
        var lgu = document.getElementById('filter-lgu').value;
        var status = document.getElementById('filter-status').value;

        var filtered = currentData.target_barangays.features.filter(function (f) {
            if (lgu && f.properties.lgu !== lgu) return false;
            if (status && f.properties.status !== status) return false;
            return true;
        });
        barangayLayer.clearLayers();
        barangayLayer.addData({ type: 'FeatureCollection', features: filtered });
    }

    function setLevel(level, lgu, barangayId, barangayName) {
        state.level = level;
        state.lgu = lgu || null;
        state.barangayId = barangayId || null;
        state.barangayName = barangayName || null;
        document.getElementById('filter-lgu').value = state.lgu || '';
        applyClientFilters();
        focusMap();
        renderBreadcrumb();
        renderPanel();
        renderRoutesTable();
    }

    // Deep-link support so links from other pages (e.g. the Dashboard's mini
    // map) can land directly on a municipality or barangay instead of overview.
    var pendingNav = (function () {
        var params = new URLSearchParams(window.location.search);
        var municipality = params.get('municipality');
        var barangayId = params.get('barangay_id');
        if (!municipality && !barangayId) return null;
        return { municipality: municipality, barangayId: barangayId ? parseInt(barangayId, 10) : null };
    })();

    function loadData() {
        var eventId = document.getElementById('filter-event').value;
        var url = '/pswdo/gis-map/data' + (eventId ? '?event_id=' + eventId : '');
        fetch(url).then(function (r) { return r.json(); }).then(function (data) {
            currentData = data;
            provinceLayer.clearLayers();
            provinceLayer.addData(data.province_context);
            renderWarehouses(data.warehouses);
            renderRoutes(data.in_transit_lines);

            if (pendingNav) {
                var nav = pendingNav;
                pendingNav = null;
                var feature = nav.barangayId ? data.target_barangays.features.find(function (f) { return f.properties.barangay_id === nav.barangayId; }) : null;
                if (feature) {
                    setLevel('barangay-detail', feature.properties.lgu, feature.properties.barangay_id, feature.properties.name);
                    return;
                }
                if (nav.municipality) {
                    setLevel('municipality', nav.municipality);
                    return;
                }
            }

            applyClientFilters();
            focusMap();
            renderBreadcrumb();
            renderPanel();
            renderRoutesTable();
        });
    }

    // Delegated click handling for breadcrumb + info panel (both are re-rendered
    // via innerHTML, so listeners are attached once on stable ancestors).
    function handleActionClick(e) {
        var navEl = e.target.closest('[data-nav]');
        if (navEl) {
            var level = navEl.getAttribute('data-nav');
            var lgu = navEl.getAttribute('data-lgu');
            var barangayId = navEl.getAttribute('data-barangay-id');
            var barangayName = navEl.getAttribute('data-barangay-name');
            setLevel(level, lgu, barangayId ? parseInt(barangayId, 10) : null, barangayName);
            return;
        }
        var extEl = e.target.closest('[data-external]');
        if (extEl) {
            var lguVal = extEl.getAttribute('data-lgu');
            var kind = extEl.getAttribute('data-external');
            var eventId = document.getElementById('filter-event').value;
            if (kind === 'distribution') {
                window.location.href = '/pswdo/distribution?q=' + encodeURIComponent(lguVal);
            } else if (kind === 'relief') {
                window.location.href = '/pswdo/relief-requests?municipality=' + encodeURIComponent(lguVal);
            } else if (kind === 'report') {
                window.location.href = '/pswdo/gis-map/municipality/' + encodeURIComponent(lguVal) + '/report.csv' + (eventId ? '?event_id=' + eventId : '');
            }
        }
    }
    document.getElementById('gis-breadcrumb').addEventListener('click', handleActionClick);
    document.getElementById('gis-info-panel').addEventListener('click', handleActionClick);

    document.getElementById('filter-event').addEventListener('change', loadData);
    document.getElementById('filter-lgu').addEventListener('change', function () {
        var lgu = this.value;
        setLevel(lgu ? 'municipality' : 'overview', lgu || null);
    });
    document.getElementById('filter-status').addEventListener('change', function () {
        applyClientFilters();
        if (state.level === 'barangay-list') renderPanel();
    });
    document.getElementById('btn-refresh').addEventListener('click', loadData);

    loadData();
});
