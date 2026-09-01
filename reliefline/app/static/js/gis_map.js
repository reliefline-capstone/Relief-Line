document.addEventListener('DOMContentLoaded', function () {
    var TIER_COLORS = {
        critical: '#e74c3c',
        high: '#e67e22',
        medium: '#f1c40f',
        low: '#27ae60',
        unrated: '#d8dee8',
    };
    var TIER_RANK = { critical: 4, high: 3, medium: 2, low: 1, unrated: 0 };

    var map = L.map('gis-map', { zoomControl: false }).setView([15.98, 120.45], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Bottom-right instead of Leaflet's default top-left (which now sits
    // under the search bar overlay anyway) — restyled in gis_map.css to
    // match the app's own button/panel language instead of Leaflet's stock
    // look. Leaflet stacks same-corner controls itself, so this shares the
    // corner with the attribution control with no manual offset needed.
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Drill-down state: overview -> municipality -> barangay-list -> barangay-detail
    var state = { level: 'overview', lgu: null, barangayId: null, barangayName: null, showBreakdown: false };
    var currentData = null;

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function fmt(n) { return (n || 0).toLocaleString(); }

    // Config rendered server-side by app.routes.pswdo._gis_config() (shared by
    // both the PSWDO and CSWDO page templates) — role-specific destinations
    // and, for a single-LGU scope (CSWDO/MSWDO), the municipality to land on
    // by default instead of an overview that only ever has one entry.
    var GIS_CONFIG = window.RELIEFLINE_GIS_CONFIG || { role: null, barangayReportsUrl: null, distributionUrl: null, defaultLgu: null };

    // PSWDO (province-wide oversight) sees municipality-level aggregates
    // only — no barangay boundaries, no barangay drill-down. That level of
    // operational detail is CSWDO/MSWDO's job (they only ever have one
    // municipality in scope anyway). system_admin gets the same province-wide
    // view PSWDO does.
    var IS_MUNI_ONLY = GIS_CONFIG.role !== 'cswdo_admin';

    // is_target is already restricted server-side to this user's own scope
    // (app.routes.pswdo._gis_scope_lgus) — a bold solid border marks exactly
    // the municipality/ies this account is allowed to see data for.
    // Neighboring municipalities' boundaries only carry a handful of
    // vertices each (coarse province-wide context data, not surveyed to the
    // same precision as the 3 target LGUs' barangay-derived shapes) — fine
    // as a faint backdrop at the whole-province overview, but blocky enough
    // up close that once the user drills into one LGU, a neighboring shape
    // can read as a stray rectangle "box" over the view. So they're hidden
    // past the overview level, leaving only the clicked LGU's own accurate
    // boundary on screen — see setLevel(), which re-applies this style.
    function provinceStyle(feature) {
        var isTarget = feature.properties.is_target;
        if (state.level !== 'overview' && !isTarget) {
            return { color: 'transparent', weight: 0, opacity: 0, fillOpacity: 0 };
        }
        if (isTarget && IS_MUNI_ONLY) {
            // PSWDO's municipality-level view: fill each target LGU by its
            // own real demand tier (same Critical/High/Medium/Low/Unrated
            // scale as the legend and every badge elsewhere) instead of a
            // flat color, so the map itself answers "which municipality
            // needs attention" at a glance — updates automatically whenever
            // the underlying barangay status/allocation data changes, since
            // this is computed fresh from currentData on every render.
            var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === feature.properties.lgu; }) : null;
            var demandColor = TIER_COLORS[muni ? muni.status_tier : 'unrated'];
            var isSelected = state.lgu === feature.properties.lgu;
            return {
                color: isSelected ? '#0f2547' : '#55606b',
                weight: isSelected ? 3 : 1.5,
                fillColor: demandColor,
                fillOpacity: isSelected ? 0.6 : 0.45,
            };
        }
        return {
            // Every non-target (or CSWDO-scope) municipality gets the same
            // on-brand blue fill so the whole province reads as one shaded
            // region against neighboring provinces (Nueva Ecija, Tarlac, La
            // Union, Benguet) — target LGUs stand out further on top of that
            // with a bolder navy border and a touch more fill.
            //
            // Non-target municipalities have no real barangay-level source
            // data (out of this project's scope — see Scope and Limitations),
            // so pangasinan_municipalities.json carries only crude, low-point
            // placeholder shapes for them — some render as an obvious
            // near-rectangle. Rather than inventing a more accurate boundary
            // (explicitly against project rules), the border is dropped
            // entirely for non-target munis: a soft fill with no hard edge
            // never draws attention to how few points a shape actually has,
            // while target LGUs (real, accurate boundaries) keep their
            // border as before.
            color: isTarget ? '#0f2547' : 'transparent',
            weight: isTarget ? 3 : 0,
            fillColor: isTarget ? '#2c5aa0' : '#bcd4f0',
            fillOpacity: isTarget ? 0.12 : 0.4,
        };
    }

    var provinceLayer = L.geoJSON(null, {
        style: provinceStyle,
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.is_target) {
                // currentData is already assigned before addData() runs (see
                // loadData()), so the per-LGU relief rollup — the closest
                // real figure to "predicted demand" this dataset has — is
                // available here to enrich the hover tooltip.
                var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === p.lgu; }) : null;
                var demandLine = muni ? (
                    '<br>Predicted Demand: ' + fmt(muni.predicted_demand) + ' packs' +
                    '<br>Demand Level: ' + escapeHtml(muni.status_label)
                ) : '';
                layer.bindTooltip('<strong>' + escapeHtml(p.lgu) + '</strong>' + demandLine + '<br><em>Click to view</em>', { sticky: true });
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
                var sourceLabel = p.food_packs_source === 'request' ? 'allocated' : 'estimated';
                var stockLine = p.barangay_on_hand == null
                    ? '<br>Barangay stock: none reported'
                    : '<br>Barangay stock: ' + fmt(p.barangay_on_hand) + ' packs';
                var adequacyLine = p.stock_ratio_pct == null
                    ? (p.barangay_on_hand === 0 ? '<br>Need vs stock: ' + fmt(p.stock_need) + ' vs 0 — critical' : '')
                    : '<br>Need vs stock: ' + fmt(p.stock_need) + ' / ' + fmt(p.barangay_on_hand) + ' (' + p.stock_ratio_pct + '%)';
                layer.bindTooltip(
                    '<strong>' + escapeHtml(p.name) + '</strong><br>Stock adequacy: ' + escapeHtml(p.priority_label) +
                    adequacyLine + stockLine +
                    '<br>' + fmt(p.food_packs_current) + ' food packs ' + sourceLabel,
                    { sticky: true }
                );
                layer.on('click', function () { setLevel('barangay-detail', p.lgu, p.barangay_id, p.name); });
            } else {
                layer.bindTooltip(escapeHtml(p.name) + ' — no data on record', { sticky: true });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);
    var routeLayer = L.layerGroup().addTo(map);
    // Nominatim search result pin — separate from every other layer so a
    // search never disturbs municipality/warehouse/route rendering.
    var searchMarkerLayer = L.layerGroup().addTo(map);
    // The actual road-routed polyline drawn from clicking a row in Active
    // Distribution Routes (OSRM) — visually distinct (solid, teal) from the
    // existing schematic dashed "in transit" lines in routeLayer above,
    // which stay exactly as they were.
    var osrmRouteLayer = L.layerGroup().addTo(map);

    function warehouseCode(w) {
        var m = w.name.match(/warehouse\s+([a-z0-9]+)/i);
        if (m) return 'WH-' + m[1].toUpperCase();
        // Generic names like "PSWDO Warehouse" and "PSWDO Warehouse -
        // Alaminos" both reduce to the same "PW" initials — the dash isn't
        // a word character, so the regex above never sees "Alaminos" at
        // all. Falling back to the office's own area instead (already on
        // every warehouse marker) is what actually tells two such
        // warehouses apart on the map.
        if (w.area_covered) {
            return w.area_covered.split(' ').map(function (word) { return word[0]; }).slice(0, 3).join('').toUpperCase();
        }
        return w.name.split(' ').map(function (word) { return word[0]; }).slice(0, 2).join('').toUpperCase();
    }

    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouses.forEach(function (w) {
            var healthClass = (w.health || 'low').toLowerCase();
            var icon = L.divIcon({
                className: 'gis-wh-marker gis-wh-' + healthClass,
                html: '<span>' + escapeHtml(warehouseCode(w)) + '</span>',
                iconSize: [60, 26],
                iconAnchor: [30, 13],
            });
            var marker = L.marker([w.lat, w.lng], { icon: icon });
            // Food packs are the one figure every warehouse popup leads
            // with, everywhere in the app — the badge next to it is the
            // same badge-health used on the Dashboard/Warehouse Inventory,
            // so "is this warehouse okay" reads the same way here too.
            var popupHtml =
                '<strong>' + escapeHtml(w.name) + '</strong>' +
                '<span>' + escapeHtml(w.area_covered) + '</span>' +
                '<div class="gis-wh-popup-stock">' +
                '<span class="gis-wh-popup-qty">' + fmt(w.food_pack_qty) + ' <small>/ ' + fmt(w.capacity) + ' packs (' + w.pct.toFixed(0) + '%)</small></span>' +
                '<span class="badge-health badge-' + healthClass + '">' + escapeHtml(w.health || 'No data available') + '</span>' +
                '</div>';
            // PSWDO only (CSWDO/MSWDO keeps the popup exactly as it was) —
            // every other relief item this office has on record, never
            // fabricated ("No data available" when there's genuinely
            // nothing), kept visually separate from the food-pack figure
            // above rather than just another plain text line among others,
            // so the whole popup reads as "relief supplies", not a generic
            // office info card.
            if (IS_MUNI_ONLY) {
                popupHtml += '<div class="gis-wh-popup-divider"></div>';
                popupHtml += '<span class="gis-wh-popup-label">Other Relief Items</span>';
                popupHtml += '<span class="gis-wh-relief-items">';
                if (w.other_relief_items && w.other_relief_items.length) {
                    popupHtml += escapeHtml(w.other_relief_items.map(function (i) {
                        return i.name + ' (' + fmt(i.qty) + ' ' + i.unit + ')';
                    }).join(', '));
                } else {
                    popupHtml += 'No data available';
                }
                popupHtml += '</span>';
            }
            marker.bindPopup(popupHtml);
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

    // ---- Nominatim location search ----------------------------------
    // Free, no API key. Query is biased toward Pangasinan (appended, not
    // hard-bounded, so a warehouse/place name still resolves even if
    // Nominatim's data ties it to a slightly different admin boundary).
    var searchResultsEl = document.getElementById('gis-search-results');
    var searchInputEl = document.getElementById('gis-search-input');
    var searchClearEl = document.getElementById('gis-search-clear');

    function updateSearchClearVisibility() {
        searchClearEl.hidden = !searchInputEl.value;
    }

    function clearSearch() {
        searchInputEl.value = '';
        searchMarkerLayer.clearLayers();
        hideSearchResults();
        updateSearchClearVisibility();
        searchInputEl.focus();
    }

    function hideSearchResults() {
        searchResultsEl.hidden = true;
        searchResultsEl.innerHTML = '';
    }

    function runSearch() {
        var q = (searchInputEl.value || '').trim();
        if (!q) { hideSearchResults(); return; }
        searchResultsEl.hidden = false;
        searchResultsEl.innerHTML = '<div class="gis-search-empty">Searching…</div>';
        var url = 'https://nominatim.openstreetmap.org/search?format=json&limit=6&q=' +
            encodeURIComponent(q + ', Pangasinan, Philippines');
        fetch(url, { headers: { 'Accept': 'application/json' } })
            .then(function (r) { if (!r.ok) throw new Error('search failed'); return r.json(); })
            .then(function (results) {
                if (!results.length) {
                    searchResultsEl.innerHTML = '<div class="gis-search-empty">No results found.</div>';
                    return;
                }
                searchResultsEl.innerHTML = results.map(function (r, i) {
                    return '<div class="gis-search-result" data-idx="' + i + '">' + escapeHtml(r.display_name) + '</div>';
                }).join('');
                searchResultsEl.querySelectorAll('.gis-search-result').forEach(function (el, i) {
                    el.addEventListener('click', function () { selectSearchResult(results[i]); });
                });
            })
            .catch(function () {
                // Never breaks the rest of the dashboard — this is a graceful,
                // visible failure state, not a thrown error.
                searchResultsEl.innerHTML = '<div class="gis-search-empty">Search is unavailable right now. Try again in a moment.</div>';
            });
    }

    function selectSearchResult(r) {
        searchMarkerLayer.clearLayers();
        var lat = parseFloat(r.lat), lng = parseFloat(r.lon);
        L.marker([lat, lng]).addTo(searchMarkerLayer).bindPopup(escapeHtml(r.display_name)).openPopup();
        map.setView([lat, lng], 15);
        hideSearchResults();
        searchInputEl.value = r.display_name;
        updateSearchClearVisibility();
    }

    // ---- OSRM route visualization (Active Distribution Routes) ------
    // Free public demo router, no API key. Draws the actual road path
    // (distinct solid teal line) plus a popup with real distance/duration
    // from OSRM itself — separate from the schematic dashed lines above.
    var activeRouteRowId = null;

    function clearRouteDetail() {
        activeRouteRowId = null;
        osrmRouteLayer.clearLayers();
        var detailEl = document.getElementById('gis-route-detail');
        if (detailEl) { detailEl.hidden = true; detailEl.innerHTML = ''; }
        document.querySelectorAll('#routes-table-body tr.gis-route-row-active').forEach(function (el) {
            el.classList.remove('gis-route-row-active');
        });
    }

    function showRouteDetail(html) {
        var detailEl = document.getElementById('gis-route-detail');
        if (!detailEl) return;
        detailEl.hidden = false;
        detailEl.innerHTML = html;
    }

    function loadOsrmRoute(r, rowEl) {
        osrmRouteLayer.clearLayers();
        document.querySelectorAll('#routes-table-body tr.gis-route-row-active').forEach(function (el) {
            el.classList.remove('gis-route-row-active');
        });
        rowEl.classList.add('gis-route-row-active');
        activeRouteRowId = r.distribution_id;

        if (r.from_lat == null || r.to_lat == null) {
            showRouteDetail('<strong>D-' + r.distribution_id + '</strong>' +
                '<span>Route unavailable — no coordinates on record for this warehouse or barangay.</span>');
            return;
        }

        showRouteDetail('<strong>D-' + r.distribution_id + '</strong><span>Loading route…</span>');
        var url = 'https://router.project-osrm.org/route/v1/driving/' +
            r.from_lng + ',' + r.from_lat + ';' + r.to_lng + ',' + r.to_lat +
            '?overview=full&geometries=geojson';
        fetch(url).then(function (resp) { if (!resp.ok) throw new Error('routing failed'); return resp.json(); })
            .then(function (data) {
                if (activeRouteRowId !== r.distribution_id) return; // a newer click superseded this one
                if (!data.routes || !data.routes.length) throw new Error('no route');
                var route = data.routes[0];
                var line = L.geoJSON(route.geometry, {
                    style: { color: '#16a085', weight: 5, opacity: 0.85 },
                }).addTo(osrmRouteLayer);
                L.circleMarker([r.from_lat, r.from_lng], { radius: 6, color: '#0f2547', weight: 2, fillColor: '#16a085', fillOpacity: 1 })
                    .bindTooltip(escapeHtml(r.from_office)).addTo(osrmRouteLayer);
                L.circleMarker([r.to_lat, r.to_lng], { radius: 6, color: '#0f2547', weight: 2, fillColor: '#e74c3c', fillOpacity: 1 })
                    .bindTooltip(escapeHtml(r.to_barangay)).addTo(osrmRouteLayer);
                map.fitBounds(line.getBounds().pad(0.15));

                var km = (route.distance / 1000).toFixed(1);
                var mins = Math.round(route.duration / 60);
                showRouteDetail(
                    '<strong>D-' + r.distribution_id + ' &middot; ' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_barangay) + '</strong>' +
                    '<div class="gis-route-detail-grid">' +
                    '<div><span>Distance</span><strong>' + km + ' km</strong></div>' +
                    '<div><span>Est. Travel Time</span><strong>' + mins + ' min</strong></div>' +
                    '<div><span>Packs</span><strong>' + fmt(r.packs) + '</strong></div>' +
                    '<div><span>Status</span><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></div>' +
                    '</div>'
                );
            })
            .catch(function () {
                if (activeRouteRowId !== r.distribution_id) return;
                showRouteDetail('<strong>D-' + r.distribution_id + '</strong>' +
                    '<span>Could not load the route right now. The rest of the map is unaffected — try again in a moment.</span>');
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

    // Shared by renderMunicipalityPanel and renderBarangayDetail. Each action is
    // scoped to the role it belongs to (see app.routes.pswdo._gis_config) — the
    // button is simply omitted for the other role rather than linking somewhere
    // it would 403 or make no sense:
    //   - Distribution / dispatch stays a PSWDO responsibility.
    //   - Reviewing barangay reports is entirely a CSWDO/MSWDO responsibility;
    //     PSWDO has no barangay-report page.
    function distributionButtonHtml(lgu) {
        if (!GIS_CONFIG.distributionUrl) return '';
        return '<button type="button" class="btn-decision btn-partial dd-full-width" data-external="distribution" data-lgu="' + escapeHtml(lgu) + '">' + ICON.arrow + ' View Distribution</button>';
    }
    function barangayReportsButtonHtml(lgu, barangayName) {
        if (!GIS_CONFIG.barangayReportsUrl) return '';
        return '<button type="button" class="btn-outline dd-full-width" data-external="barangay-reports" data-lgu="' + escapeHtml(lgu) + '"' +
            (barangayName ? ' data-barangay="' + escapeHtml(barangayName) + '"' : '') +
            ' style="justify-content:center; margin-top:10px;">' + ICON.clipboard + ' View Barangay Reports</button>';
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

        // Barangay-level priority listing is CSWDO/MSWDO operational detail
        // — PSWDO's oversight view stops at the "Municipalities" list above,
        // which already answers "which LGU has the highest demand."
        if (!IS_MUNI_ONLY) {
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
        }
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

        html += '<section class="panel"><div class="panel-header"><h3>Demand &amp; Allocation</h3></div>';
        html += '<div class="dd-summary-row"><span>Predicted Demand</span><strong>' + fmt(m.predicted_demand) + '</strong></div>';
        html += '<div class="dd-summary-row"><span>Available Allocation</span><strong>' + fmt(m.relief.approved) + '</strong></div>';
        html += '<div class="dd-summary-row"><span>Shortage</span><strong class="' + (m.shortage > 0 ? 'text-red' : 'text-green') + '">' + fmt(m.shortage) + '</strong></div>';
        html += '<div class="dd-summary-row"><span>Allocation Status</span><span class="badge-status badge-status-' + (m.shortage > 0 ? 'pending' : 'released') + '">' + escapeHtml(m.allocation_status) + '</span></div>';
        html += '</section>';

        if (IS_MUNI_ONLY) {
            html += '<section class="panel">';
            html += '<div class="panel-header"><h3>Barangay Breakdown</h3>' +
                '<button type="button" class="btn-outline" id="btn-toggle-breakdown">' + (state.showBreakdown ? 'Hide' : 'View Barangay Breakdown') + '</button></div>';
            if (state.showBreakdown) {
                var lguBarangays = currentData.target_barangays.features
                    .filter(function (f) { return f.properties.lgu === lgu && f.properties.has_data; })
                    .map(function (f) { return f.properties; })
                    .sort(function (a, b) { return b.food_packs_current - a.food_packs_current; });
                if (!lguBarangays.length) {
                    html += '<p class="empty-note">No barangay data on record.</p>';
                } else {
                    html += '<div class="gis-barangay-list">';
                    lguBarangays.forEach(function (p) {
                        html += '<div class="gis-priority-row">' +
                            '<div><strong>' + escapeHtml(p.name) + '</strong><span>' + (p.food_packs_source === 'request' ? 'allocated' : 'model estimate') + '</span></div>' +
                            '<div class="gis-priority-row-right"><strong>' + fmt(p.food_packs_current) + ' packs</strong>' + tierBadge(p.priority_tier, p.priority_label) + '</div>' +
                            '</div>';
                    });
                    html += '</div>';
                }
            } else {
                html += '<p class="empty-note">Per-barangay food-pack demand — not shown on the map by default.</p>';
            }
            html += '</section>';
        }

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
            html += '<div class="dd-summary-row"><span>ETA</span><strong>' + escapeHtml(d.eta) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Status</span><span class="badge-status badge-status-' + d.status + '">' + escapeHtml(d.status_label) + '</span></div>';
        } else {
            html += '<p class="empty-note">No active distribution route right now.</p>';
        }
        html += '</section>';

        html += '<section class="panel">';
        html += distributionButtonHtml(m.lgu);
        html += barangayReportsButtonHtml(m.lgu);
        if (!IS_MUNI_ONLY) {
            html += '<button type="button" class="btn-decision dd-full-width gis-btn-dark" data-nav="barangay-list" data-lgu="' + escapeHtml(m.lgu) + '" style="margin-top:10px;">' + ICON.mapPin + ' View Barangays</button>';
        }
        html += '<button type="button" class="btn-outline dd-full-width" data-external="report" data-lgu="' + escapeHtml(m.lgu) + '" style="justify-content:center; margin-top:10px;">' + ICON.download + ' Generate Report</button>';
        html += '</section>';

        return html;
    }

    function renderBarangayListPanel(lgu) {
        var statusFilter = document.getElementById('filter-status').value;
        var features = currentData.target_barangays.features.filter(function (f) {
            return f.properties.lgu === lgu && (!statusFilter || f.properties.priority_tier === statusFilter);
        });
        var withData = features.filter(function (f) { return f.properties.has_data; });
        // "affected" = the barangay filed a report for this event (same basis as
        // the dashboards), not the graded status tier.
        var affected = withData.filter(function (f) { return f.properties.is_affected; });

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
        html += '<div><span>Affected Individuals</span><strong>' + fmt(b.affected_individuals) + '</strong></div>';
        html += '<div><span>Barangay Stock on Hand</span><strong>' +
            (b.barangay_on_hand == null ? 'None reported' : fmt(b.barangay_on_hand) + ' packs') + '</strong></div>';
        html += '<div><span>Need vs Stock</span><strong>' +
            (b.stock_ratio_pct == null
                ? (b.barangay_on_hand === 0 && b.stock_need > 0 ? fmt(b.stock_need) + ' / 0 — critical' : '—')
                : fmt(b.stock_need) + ' / ' + fmt(b.barangay_on_hand) + ' (' + b.stock_ratio_pct + '%)') +
            '</strong></div>';
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
        html += distributionButtonHtml(b.lgu);
        html += barangayReportsButtonHtml(b.lgu, b.name);
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
        // "Province" is province-wide oversight — a PSWDO/system_admin
        // concern only (see IS_MUNI_ONLY above). A CSWDO/MSWDO account is
        // already locked to its own single LGU server-side, so this crumb
        // stays as a plain, non-clickable label for them instead of a link
        // back to a province overview they have no business opening.
        parts.push({ label: 'Province', nav: 'overview', disabled: GIS_CONFIG.role === 'cswdo_admin' });
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
            var sep = isLast ? '' : '<span class="gis-crumb-sep">/</span>';
            if (isLast || p.disabled) return '<span class="gis-crumb-current">' + escapeHtml(p.label) + '</span>' + sep;
            var attrs = 'data-nav="' + p.nav + '"';
            if (p.lgu) attrs += ' data-lgu="' + escapeHtml(p.lgu) + '"';
            return '<span class="gis-crumb-link" ' + attrs + '>' + escapeHtml(p.label) + '</span>' + sep;
        }).join('');
    }

    function focusMap() {
        if (!currentData) return;
        if (state.level === 'overview') {
            if (IS_MUNI_ONLY) {
                // PSWDO overview: fit to just the 3 target MUNICIPALITY
                // polygons (province_context, is_target features) — not the
                // whole province, and not barangay polygons (those sit in a
                // narrow N-S sliver and stretched the map's aspect ratio
                // when tried before; see the CSWDO branch below for that
                // history). CSWDO/MSWDO is untouched — still fits the whole
                // province_context exactly as before.
                var targetFeats = currentData.province_context.features.filter(function (f) { return f.properties.is_target; });
                if (targetFeats.length) {
                    var tb = L.geoJSON({ type: 'FeatureCollection', features: targetFeats }).getBounds();
                    if (tb.isValid()) { map.fitBounds(tb.pad(0.08)); return; }
                }
                // Fall back to the whole-province fit below if, for some
                // reason, no target features came back.
            }
            // Whole province, not just the target LGUs' barangays — those sit
            // in a narrow N-S sliver, so fitting to them alone stretched the
            // map's east-west extent to match the container's wide aspect
            // ratio and left far-off municipalities (e.g. Alaminos, San
            // Carlos) misleadingly in frame instead of the intended overview.
            var b = provinceLayer.getBounds();
            if (b && b.isValid()) map.fitBounds(b.pad(0.02));
            return;
        }
        var feats = currentData.target_barangays.features.filter(function (f) { return f.properties.lgu === state.lgu; });
        if (!feats.length) return;
        var bounds = L.geoJSON({ type: 'FeatureCollection', features: feats }).getBounds();
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.1));
    }

    var routesById = {};

    function renderRoutesTable() {
        clearRouteDetail();
        var routes = currentData ? currentData.routes_table : [];
        if (state.lgu) {
            routes = routes.filter(function (r) { return r.to_municipality === state.lgu; });
        }
        routesById = {};
        routes.forEach(function (r) { routesById[r.distribution_id] = r; });
        document.getElementById('routes-count').textContent = routes.length;
        var body = document.getElementById('routes-table-body');
        if (!routes.length) {
            body.innerHTML = '<tr><td colspan="5" class="empty-note" style="text-align:center; padding:24px;">No active distribution routes right now.</td></tr>';
            return;
        }
        body.innerHTML = routes.map(function (r) {
            return '<tr class="gis-route-row" data-distribution-id="' + r.distribution_id + '" title="Click to view route on map">' +
                '<td>D-' + r.distribution_id + '</td>' +
                '<td>' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_barangay) + ' / ' + escapeHtml(r.to_municipality) + '</td>' +
                '<td>' + fmt(r.packs) + '</td>' +
                '<td><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></td>' +
                '<td>' + escapeHtml(r.eta) + '</td>' +
                '</tr>';
        }).join('');
    }

    function applyClientFilters() {
        if (!currentData) return;
        barangayLayer.clearLayers();
        if (IS_MUNI_ONLY) return;

        var lgu = document.getElementById('filter-lgu').value;
        var status = document.getElementById('filter-status').value;

        var filtered = currentData.target_barangays.features.filter(function (f) {
            if (lgu && f.properties.lgu !== lgu) return false;
            if (status && f.properties.priority_tier !== status) return false;
            return true;
        });
        barangayLayer.addData({ type: 'FeatureCollection', features: filtered });
    }

    function setLevel(level, lgu, barangayId, barangayName) {
        // Municipality-level view never drills further than 'municipality' —
        // no barangay boundary layer is even populated to select from.
        if (IS_MUNI_ONLY && (level === 'barangay-list' || level === 'barangay-detail')) {
            level = 'municipality';
        }
        state.level = level;
        state.lgu = lgu || null;
        state.barangayId = barangayId || null;
        state.barangayName = barangayName || null;
        state.showBreakdown = false;
        document.getElementById('filter-lgu').value = state.lgu || '';
        provinceLayer.setStyle(provinceStyle);
        applyClientFilters();
        focusMap();
        renderBreadcrumb();
        renderPanel();
        renderRoutesTable();
    }

    // Deep-link support so links from other pages (e.g. the Dashboard's mini
    // map) can land directly on a municipality or barangay instead of overview.
    // Falls back to GIS_CONFIG.defaultLgu when there's no explicit query param
    // — a CSWDO/MSWDO admin's scope is a single municipality, so there's no
    // real "overview" for them to land on; they go straight to their town.
    var pendingNav = (function () {
        var params = new URLSearchParams(window.location.search);
        var municipality = params.get('municipality') || GIS_CONFIG.defaultLgu;
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
        if (e.target.closest('#btn-toggle-breakdown')) {
            state.showBreakdown = !state.showBreakdown;
            renderPanel();
            return;
        }
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
            if (kind === 'distribution' && GIS_CONFIG.distributionUrl) {
                window.location.href = GIS_CONFIG.distributionUrl + '?q=' + encodeURIComponent(lguVal);
            } else if (kind === 'barangay-reports' && GIS_CONFIG.barangayReportsUrl) {
                var brgy = extEl.getAttribute('data-barangay');
                window.location.href = GIS_CONFIG.barangayReportsUrl + (brgy ? '?tab=all&q=' + encodeURIComponent(brgy) : '');
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
    var refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) refreshBtn.addEventListener('click', loadData);

    // Only present on the PSWDO template — CSWDO/MSWDO's single-LGU scope
    // has no real "province overview" to reset back to.
    var resetBtn = document.getElementById('btn-reset-map');
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            searchMarkerLayer.clearLayers();
            searchInputEl.value = '';
            updateSearchClearVisibility();
            hideSearchResults();
            clearRouteDetail();
            setLevel('overview');
        });
    }

    // Search: button click or Enter key; results dismiss on outside click.
    document.getElementById('gis-search-btn').addEventListener('click', runSearch);
    searchInputEl.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); runSearch(); }
    });
    searchInputEl.addEventListener('input', updateSearchClearVisibility);
    searchClearEl.addEventListener('click', clearSearch);
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.gis-search-bar') && !e.target.closest('.gis-search-results')) {
            hideSearchResults();
        }
    });

    // Active Distribution Routes: click a row to draw its real OSRM route.
    document.getElementById('routes-table-body').addEventListener('click', function (e) {
        var row = e.target.closest('tr[data-distribution-id]');
        if (!row) return;
        var r = routesById[row.getAttribute('data-distribution-id')];
        if (r) loadOsrmRoute(r, row);
    });

    // Fullscreen toggle — expands the whole map panel (search bar, map,
    // legend included) via the browser's native Fullscreen API, no extra
    // library. Leaflet needs an explicit invalidateSize() nudge after the
    // container's size changes, or tiles render wrong until the next pan.
    var fullscreenBtn = document.getElementById('gis-fullscreen-btn');
    var mapPanelEl = document.querySelector('.gis-map-panel');
    if (fullscreenBtn && mapPanelEl) {
        fullscreenBtn.addEventListener('click', function () {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else if (mapPanelEl.requestFullscreen) {
                mapPanelEl.requestFullscreen();
            }
        });
        document.addEventListener('fullscreenchange', function () {
            var isFull = !!document.fullscreenElement;
            mapPanelEl.classList.toggle('gis-map-panel-fullscreen', isFull);
            fullscreenBtn.title = isFull ? 'Exit fullscreen' : 'Toggle fullscreen';
            setTimeout(function () { map.invalidateSize(); }, 100);
        });
    }

    loadData();
});
