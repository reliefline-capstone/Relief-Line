// The GIS Map page: the interactive map of municipalities, barangays, warehouses and delivery routes.
// It also builds the side panel, the search box and the routes table.
document.addEventListener('DOMContentLoaded', function () {
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
    var TIER_RANK = { critical: 4, high: 3, medium: 2, low: 1, unrated: 0 };
    var TIER_BORDER_COLORS_DARK = {
        critical: '#f5a49b',
        high: '#f8c27a',
        medium: '#f7e08a',
        low: '#9ee8bb',
        unrated: '#c3cad6',
    };
    // True if dark mode is on (map colors change to match).
    function isDark() { return document.documentElement.getAttribute('data-theme') === 'dark'; }

    var map = L.map('gis-map', {
        zoomControl: false,
        zoomAnimation: true,
        zoomSnap: 0,
        zoomDelta: 0.5,
        wheelPxPerZoomLevel: 110,
        wheelDebounceTime: 10,
    }).setView([15.98, 120.45], 11);
    map.createPane('barangayPane').style.zIndex = 410;
    map.createPane('routePane').style.zIndex = 420;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    L.control.zoom({ position: 'bottomleft' }).addTo(map);

    var state = { level: 'overview', lgu: null, barangayId: null, barangayName: null, showBreakdown: false };
    var currentData = null;

    // Makes text safe to show on the page (so names with symbols can't break the layout).
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    // Formats a number with commas (e.g. 12,345).
    function fmt(n) { return (n || 0).toLocaleString(); }

    var GIS_CONFIG = window.RELIEFLINE_GIS_CONFIG || { role: null, barangayReportsUrl: null, defaultLgu: null };

    var IS_MUNI_ONLY = GIS_CONFIG.role !== 'cswdo_admin';

    // Colors each municipality on the map: the 3 target municipalities by status,
    // other towns in grey, and the selected one highlighted.
    function provinceStyle(feature) {
        var isTarget = feature.properties.is_target;
        if (!isTarget) {
            var dark = isDark();
            if (state.lgu && state.lgu === feature.properties.name) {
                return dark
                    ? { color: '#e4e6ee', weight: 3, fillColor: '#5b6275', fillOpacity: 0.55 }
                    : { color: '#374151', weight: 3, fillColor: '#9aa0ae', fillOpacity: 0.7 };
            }
            return dark
                ? { color: '#9aa3b5', weight: 1.2, fillColor: '#3a3f52', fillOpacity: 0.35 }
                : { color: '#6b7280', weight: 1.2, fillColor: '#c3c7d1', fillOpacity: 0.5 };
        }
        var isSelected = state.lgu === feature.properties.lgu;
        var fillColor = '#5347ce';
        var borderColor = isDark() ? '#9ee8bb' : '#145a32';
        if (IS_MUNI_ONLY) {
            var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === feature.properties.lgu; }) : null;
            var tier = muni ? muni.status_tier : 'unrated';
            fillColor = TIER_COLORS[tier];
            borderColor = (isDark() ? TIER_BORDER_COLORS_DARK : TIER_BORDER_COLORS)[tier];
        }
        return {
            color: borderColor,
            weight: isSelected ? 4 : 2.5,
            fillColor: fillColor,
            fillOpacity: IS_MUNI_ONLY ? (isSelected ? 0.65 : 0.45) : 0,
            className: 'gis-target-muni',
        };
    }

    var muniLabelLayer = L.layerGroup().addTo(map);

    var provinceLayer = L.geoJSON(null, {
        style: provinceStyle,
        // Adds the name label, the hover info and the click action to each municipality.
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            var labelBounds = layer.getBounds();
            if (labelBounds.isValid()) {
                var labelMarker = L.marker(labelBounds.getCenter(), {
                    icon: L.divIcon({
                        className: p.is_target ? 'gis-muni-label gis-muni-label-target' : 'gis-muni-label',
                        html: escapeHtml(p.is_target ? p.lgu : p.name),
                        iconSize: null,
                    }),
                    interactive: !!p.is_target,
                    keyboard: false,
                }).addTo(muniLabelLayer);
                if (p.is_target) {
                    labelMarker.on('click', function () { toggleMunicipality(p.lgu); });
                }
            }
            if (p.is_target) {
                var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === p.lgu; }) : null;
                var demandLine = muni ? (
                    '<br>Predicted Demand: ' + fmt(muni.predicted_demand) + ' packs' +
                    '<br>Demand Level: ' + escapeHtml(muni.status_label)
                ) : '';
                layer.bindTooltip('<strong>' + escapeHtml(p.lgu) + '</strong>' + demandLine + '<br><em>Click to view</em>', { sticky: true });
                layer.on('click', function () { toggleMunicipality(p.lgu); });
                layer.on('mouseover', function () {
                    layer.setStyle({
                        weight: state.lgu === p.lgu ? 4.5 : 3.2,
                        fillOpacity: IS_MUNI_ONLY ? (state.lgu === p.lgu ? 0.8 : 0.65) : 0,
                    });
                });
                layer.on('mouseout', function () { layer.setStyle(provinceStyle(feature)); });
            } else if (!IS_MUNI_ONLY) {
                layer.options.interactive = false;
            } else {
                layer.bindTooltip(
                    '<strong>' + escapeHtml(p.name) + '</strong>' +
                    '<span class="gis-neutral-tt-note">Outside current detailed data coverage' +
                    '<br><em>Click to view</em></span>',
                    { className: 'gis-neutral-tooltip', sticky: true }
                );
                layer.on('click', function () { toggleMunicipality(p.name); });
                layer.on('mouseover', function () {
                    layer.setStyle(isDark()
                        ? { weight: 2, color: '#e4e6ee', fillColor: '#5b6275', fillOpacity: 0.55 }
                        : { weight: 2, color: '#4b5563', fillColor: '#9aa0ac', fillOpacity: 0.65 });
                });
                layer.on('mouseout', function () { layer.setStyle(provinceStyle(feature)); });
            }
        },
    }).addTo(map);

    var barangayLabelLayer = L.layerGroup().addTo(map);
    var barangayLabels = [];

    // Area of a map shape (used to decide where to put labels).
    function ringArea(ring) {
        var s = 0;
        for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            s += (ring[j][0] * ring[i][1]) - (ring[i][0] * ring[j][1]);
        }
        return s / 2;
    }
    // True if a point is inside a map shape.
    function pointInRing(pt, ring) {
        var inside = false;
        for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
            if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) inside = !inside;
        }
        return inside;
    }
    // Finds a good spot inside a barangay's shape to put its name label.
    function polygonLabelPoint(geometry) {
        var polys = geometry.type === 'MultiPolygon' ? geometry.coordinates : [geometry.coordinates];
        var best = null, bestArea = 0;
        polys.forEach(function (poly) {
            var a = Math.abs(ringArea(poly[0]));
            if (a > bestArea) { bestArea = a; best = poly[0]; }
        });
        if (!best) return null;
        var A = ringArea(best), cx = 0, cy = 0;
        for (var i = 0, j = best.length - 1; i < best.length; j = i++) {
            var f = best[j][0] * best[i][1] - best[i][0] * best[j][1];
            cx += (best[j][0] + best[i][0]) * f;
            cy += (best[j][1] + best[i][1]) * f;
        }
        var pt = A ? [cx / (6 * A), cy / (6 * A)] : best[0];
        if (!pointInRing(pt, best)) {
            var xs = [];
            for (var k = 0, m = best.length - 1; k < best.length; m = k++) {
                var y1 = best[m][1], y2 = best[k][1];
                if ((y1 > pt[1]) !== (y2 > pt[1])) {
                    xs.push(best[m][0] + (pt[1] - y1) * (best[k][0] - best[m][0]) / (y2 - y1));
                }
            }
            xs.sort(function (p1, p2) { return p1 - p2; });
            var bestW = -1;
            for (var q = 0; q + 1 < xs.length; q += 2) {
                if (xs[q + 1] - xs[q] > bestW) { bestW = xs[q + 1] - xs[q]; pt = [(xs[q] + xs[q + 1]) / 2, pt[1]]; }
            }
        }
        return [pt[1], pt[0]];
    }

    // The biggest part of a map shape (for barangays made of several pieces).
    function largestRing(geometry) {
        var polys = geometry.type === 'MultiPolygon' ? geometry.coordinates : [geometry.coordinates];
        var best = null, bestArea = 0;
        polys.forEach(function (poly) {
            var a = Math.abs(ringArea(poly[0]));
            if (a > bestArea) { bestArea = a; best = poly[0]; }
        });
        return best;
    }

    // Creates the barangay name labels on the map.
    function rebuildBarangayLabels(features) {
        barangayLabelLayer.clearLayers();
        barangayLabels = [];
        features.forEach(function (f) {
            var at = polygonLabelPoint(f.geometry);
            if (!at) return;
            var marker = L.marker(at, {
                icon: L.divIcon({ className: 'gis-brgy-label', html: '<span>' + escapeHtml(f.properties.name) + '</span>', iconSize: null }),
                interactive: false,
                keyboard: false,
            }).addTo(barangayLabelLayer);
            barangayLabels.push({
                marker: marker, name: f.properties.name, id: f.properties.barangay_id,
                bounds: L.geoJSON(f).getBounds(), home: L.latLng(at), ring: largestRing(f.geometry),
            });
        });
        updateBarangayLabelVisibility();
    }

    // Hides barangay labels that would overlap other labels,
    // so the map stays readable at every zoom level.
    function updateBarangayLabelVisibility() {
        if (!barangayLabels.length) return;
        var cbox = map.getContainer().getBoundingClientRect();
        var taken = [];
        document.querySelectorAll('.gis-muni-label-target').forEach(function (e) {
            var r = e.getBoundingClientRect();
            if (r.width) taken.push({ l: r.left - cbox.left, t: r.top - cbox.top, r: r.right - cbox.left, b: r.bottom - cbox.top });
        });
        var selectedId = state.level === 'barangay-detail' ? state.barangayId : null;
        barangayLabels.map(function (entry) {
            var sw = map.latLngToContainerPoint(entry.bounds.getSouthWest());
            var ne = map.latLngToContainerPoint(entry.bounds.getNorthEast());
            var area = Math.abs(ne.x - sw.x) * Math.abs(sw.y - ne.y);
            return { entry: entry, area: entry.id === selectedId ? Infinity : area };
        }).sort(function (x, y) { return y.area - x.area; }).forEach(function (item) {
            var entry = item.entry, el = entry.marker.getElement();
            if (!el) return;
            if (!entry.size) {
                el.style.display = '';
                var span = el.querySelector('span') || el;
                if (span.offsetWidth) entry.size = { w: span.offsetWidth + 4, h: span.offsetHeight || 13 };
            }
            var w = entry.size ? entry.size.w : entry.name.length * 5.6 + 8;
            var h = entry.size ? entry.size.h : 13;
            var home = map.latLngToContainerPoint(entry.home);
            // The space a label takes on the screen.
            function boxAt(p) { return { l: p.x - w / 2, t: p.y - h / 2, r: p.x + w / 2, b: p.y + h / 2 }; }
            // True if a label would overlap a label already shown.
            function clashes(box) {
                return taken.some(function (t) {
                    return !(box.r <= t.l || t.r <= box.l || box.b <= t.t || t.b <= box.t);
                });
            }
            var offsets = [[0, 0], [0, -h], [0, h], [-w / 2, 0], [w / 2, 0], [0, -2 * h], [0, 2 * h],
                           [-w / 2, -h], [w / 2, -h], [-w / 2, h], [w / 2, h]];
            var placed = null;
            for (var i = 0; i < offsets.length && !placed; i++) {
                var p = L.point(home.x + offsets[i][0], home.y + offsets[i][1]);
                var ll = i === 0 ? entry.home : map.containerPointToLatLng(p);
                if (i > 0 && (!entry.ring || !pointInRing([ll.lng, ll.lat], entry.ring))) continue;
                if (entry.id === selectedId || !clashes(boxAt(p))) placed = { p: p, ll: ll };
            }
            if (placed) {
                entry.marker.setLatLng(placed.ll);
                el.style.display = '';
                taken.push(boxAt(placed.p));
            } else {
                entry.marker.setLatLng(entry.home);
                el.style.display = 'none';
            }
        });
    }
    barangayLabelLayer.on('add', updateBarangayLabelVisibility);
    map.on('zoomend moveend', updateBarangayLabelVisibility);

    window.addEventListener('rl-themechange', function () {
        provinceLayer.setStyle(provinceStyle);
        if (typeof barangayLayer !== 'undefined') barangayLayer.eachLayer(function (l) { barangayLayer.resetStyle(l); });
    });

    var barangayLayer = L.geoJSON(null, {
        pane: 'barangayPane',
        // Colors each barangay by its priority level (and outlines the selected barangay).
        style: function (feature) {
            var p = feature.properties;
            var color = TIER_COLORS[p.priority_tier] || TIER_COLORS.unrated;
            var isSelected = state.level === 'barangay-detail' && state.barangayId === p.barangay_id;
            return {
                color: isSelected ? '#3867d6' : '#fff',
                weight: isSelected ? 3 : 1,
                fillColor: color,
                fillOpacity: 0.75,
            };
        },
        // Adds the hover info (status, stock, food packs) and the click action to each barangay.
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            if (p.has_data) {
                var sourceLabel = p.food_packs_source === 'request' ? 'allocated' : 'estimated';
                var stockLine = p.barangay_on_hand == null
                    ? '<br>Barangay stock: none reported'
                    : '<br>Barangay stock: ' + fmt(p.barangay_on_hand) + ' packs';
                var adequacyLine = p.stock_ratio_pct == null
                    ? (p.barangay_on_hand === 0 ? '<br>Need vs stock: ' + fmt(p.stock_need) + ' vs 0 - critical' : '')
                    : '<br>Need vs stock: ' + fmt(p.stock_need) + ' / ' + fmt(p.barangay_on_hand) + ' (' + p.stock_ratio_pct + '%)';
                layer.bindTooltip(
                    '<strong>' + escapeHtml(p.name) + '</strong><br>Stock adequacy: ' + escapeHtml(p.priority_label) +
                    adequacyLine + stockLine +
                    '<br>' + fmt(p.food_packs_current) + ' food packs ' + sourceLabel,
                    { sticky: true }
                );
                layer.on('click', function () { toggleBarangay(p.lgu, p.barangay_id, p.name); });
            } else {
                layer.bindTooltip(escapeHtml(p.name) + ' - no data on record', { sticky: true });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);
    var searchMarkerLayer = L.layerGroup().addTo(map);
    var osrmRouteLayer = L.layerGroup().addTo(map);

    var WH_ICON_ZOOM_BREAKPOINTS = [
        { minZoom: 13, size: 30 },
        { minZoom: 11, size: 24 },
        { minZoom: 9, size: 18 },
        { minZoom: 0, size: 14 },
    ];
    // The warehouse icon size for the current zoom level (bigger when zoomed in).
    function warehouseIconSize() {
        var zoom = map.getZoom();
        for (var i = 0; i < WH_ICON_ZOOM_BREAKPOINTS.length; i++) {
            if (zoom >= WH_ICON_ZOOM_BREAKPOINTS[i].minZoom) return WH_ICON_ZOOM_BREAKPOINTS[i].size;
        }
        return 14;
    }
    // Builds a warehouse icon colored by stock health (Healthy, Moderate, Low).
    function buildWarehouseIcon(healthClass) {
        var size = warehouseIconSize();
        var half = size / 2;
        return L.divIcon({
            className: 'gis-wh-marker gis-wh-' + healthClass,
            html: '<span class="gis-wh-marker-pin">' + ICON.warehouse + '</span>',
            iconSize: [size, size],
            iconAnchor: [half, half],
        });
    }
    var warehouseMarkers = [];
    map.on('zoomend', function () {
        warehouseMarkers.forEach(function (entry) {
            entry.marker.setIcon(buildWarehouseIcon(entry.healthClass));
        });
    });

    // Draws the warehouse icons on the map with their hover info (stock and % full).
    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouseMarkers = [];
        warehouses.forEach(function (w) {
            var healthClass = (w.health || 'low').toLowerCase();
            var marker = L.marker([w.lat, w.lng], { icon: buildWarehouseIcon(healthClass), title: w.name });
            warehouseMarkers.push({ marker: marker, healthClass: healthClass });
            var popupHtml =
                '<strong>' + escapeHtml(w.name) + '</strong>' +
                '<span>' + escapeHtml(w.area_covered) + '</span>' +
                '<div class="gis-wh-popup-stock">' +
                '<span class="gis-wh-popup-qty">' + fmt(w.food_pack_qty) + ' <small>/ ' + fmt(w.capacity) + ' packs (' + w.pct.toFixed(0) + '%)</small></span>' +
                '<span class="badge-health badge-' + healthClass + '">' + escapeHtml(w.health || 'No data available') + '</span>' +
                '</div>';
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

    var searchResultsEl = document.getElementById('gis-search-results');
    var searchInputEl = document.getElementById('gis-search-input');
    var searchClearEl = document.getElementById('gis-search-clear');

    // Shows the search box's clear (x) button only when something is typed.
    function updateSearchClearVisibility() {
        searchClearEl.hidden = !searchInputEl.value;
    }

    // Clears the map search box and its results.
    function clearSearch() {
        searchInputEl.value = '';
        searchMarkerLayer.clearLayers();
        hideSearchResults();
        updateSearchClearVisibility();
        searchInputEl.focus();
    }

    // Hides the search results list.
    function hideSearchResults() {
        searchResultsEl.hidden = true;
        searchResultsEl.innerHTML = '';
    }

    // Everything that can be searched on the map (municipalities and barangays).
    function searchCandidates() {
        if (IS_MUNI_ONLY) {
            return currentData.province_context.features.map(function (f) {
                var name = f.properties.is_target ? f.properties.lgu : f.properties.name;
                return {
                    name: name,
                    sub: 'Municipality &middot; ' + (f.properties.is_target ? 'has data' : 'no data'),
                    // Opens the chosen municipality from the search results.
                    pick: function () { setLevel('municipality', name); },
                };
            });
        }
        return currentData.target_barangays.features.map(function (f) {
            var pr = f.properties;
            return {
                name: pr.name,
                sub: 'Barangay &middot; ' + escapeHtml(pr.lgu),
                // Opens the chosen barangay from the search results.
                pick: function () { setLevel('barangay-detail', pr.lgu, pr.barangay_id, pr.name); },
            };
        });
    }

    // Searches the map while the user types and lists the matches.
    function runSearch() {
        var q = (searchInputEl.value || '').trim();
        if (!q) { hideSearchResults(); return []; }
        searchResultsEl.hidden = false;
        if (!currentData) {
            searchResultsEl.innerHTML = '<div class="gis-search-empty">Loading…</div>';
            return [];
        }
        var needle = q.toLowerCase();
        var found = searchCandidates().filter(function (m) {
            return m.name.toLowerCase().indexOf(needle) !== -1;
        }).sort(function (x, y) {
            var xs = x.name.toLowerCase().indexOf(needle) === 0 ? 0 : 1;
            var ys = y.name.toLowerCase().indexOf(needle) === 0 ? 0 : 1;
            return xs - ys || x.name.localeCompare(y.name);
        });
        if (!found.length) {
            searchResultsEl.innerHTML = '<div class="gis-search-empty">No ' + (IS_MUNI_ONLY ? 'municipality' : 'barangay') + ' found.</div>';
            return found;
        }
        searchResultsEl.innerHTML = found.map(function (m, i) {
            return '<div class="gis-search-result" data-idx="' + i + '"><strong>' + escapeHtml(m.name) + '</strong>' +
                '<span class="gis-search-result-sub">' + m.sub + '</span></div>';
        }).join('');
        searchResultsEl.querySelectorAll('.gis-search-result').forEach(function (el, i) {
            el.addEventListener('click', function () { selectSearchResult(found[i]); });
        });
        return found;
    }

    // Goes to the chosen search result on the map.
    function selectSearchResult(m) {
        searchMarkerLayer.clearLayers();
        hideSearchResults();
        searchInputEl.value = m.name;
        updateSearchClearVisibility();
        m.pick();
    }

    var activeRouteRowId = null;

    // Removes the delivery route shown on the map.
    function clearRouteDetail() {
        activeRouteRowId = null;
        osrmRouteLayer.clearLayers();
        var detailEl = document.getElementById('gis-route-detail');
        if (detailEl) { detailEl.hidden = true; detailEl.innerHTML = ''; }
        document.querySelectorAll('#routes-table-body tr.gis-route-row-active').forEach(function (el) {
            el.classList.remove('gis-route-row-active');
        });
    }

    // Shows the delivery route's details box (with a close button).
    function showRouteDetail(html) {
        var detailEl = document.getElementById('gis-route-detail');
        if (!detailEl) return;
        detailEl.hidden = false;
        detailEl.innerHTML = '<button type="button" class="gis-route-detail-close" title="Close route" aria-label="Close route">' + ICON.close + '</button>' + html;
    }

    // The dot that marks where a delivery route starts (the warehouse).
    function routeDotIcon(fillColor) {
        return L.divIcon({
            className: 'gis-route-dot',
            html: '<span style="background:' + fillColor + '"></span>',
            iconSize: [14, 14],
            iconAnchor: [7, 7],
        });
    }

    // The pin that marks where a delivery route ends (the barangay).
    function routePinIcon(fillColor) {
        return L.divIcon({
            className: 'gis-route-pin',
            html: '<svg width="30" height="38" viewBox="0 0 24 30" xmlns="http://www.w3.org/2000/svg">' +
                '<path d="M12 1C6.2 1 1.5 5.6 1.5 11.3 1.5 19 12 29 12 29s10.5-10 10.5-17.7C22.5 5.6 17.8 1 12 1z" fill="' + fillColor + '" stroke="#ffffff" stroke-width="1.6" stroke-linejoin="round"/>' +
                '<circle cx="12" cy="11.3" r="4" fill="#ffffff"/></svg>',
            iconSize: [30, 38],
            iconAnchor: [15, 38],
            tooltipAnchor: [0, -34],
        });
    }

    var ROUTE_COLOR = '#5347ce';

    // Draws the start dot and end pin of a delivery route.
    function addRouteEndpoints(r) {
        L.marker([r.from_lat, r.from_lng], { icon: routeDotIcon(ROUTE_COLOR), keyboard: false })
            .bindTooltip(escapeHtml(r.from_office)).addTo(osrmRouteLayer);
        return L.marker([r.to_lat, r.to_lng], { icon: routePinIcon('#e74c3c'), keyboard: false, zIndexOffset: 1000 })
            .addTo(osrmRouteLayer);
    }

    // Zooms the map so the whole route is visible (leaving room for open panels).
    function fitRouteBounds(bounds) {
        var infoWrap = document.getElementById('gis-floating-info');
        var panelOpen = infoWrap && !infoWrap.classList.contains('is-collapsed');
        var bottomPad = 40;
        var dock = document.getElementById('gis-routes-panel');
        if (dock && !dock.hidden) {
            var mapBox = map.getContainer().getBoundingClientRect();
            bottomPad = Math.max(40, Math.round(mapBox.bottom - dock.getBoundingClientRect().top) + 16);
        }
        map.fitBounds(bounds, {
            paddingTopLeft: [40, 90],
            paddingBottomRight: [panelOpen ? 390 : 40, bottomPad],
        });
    }

    // Adds the label on the route's destination pin (destination and distance).
    function pinSummary(pin, r, line2) {
        pin.bindTooltip('<strong>' + escapeHtml(r.to_label) + '</strong><br>' + line2,
            { permanent: true, direction: 'top', className: 'gis-route-tt' });
    }

    // Builds the route details: delivery number, from/to, distance and estimated travel time.
    function detailHtml(r, distanceLabel, distanceValue, timeValue) {
        return '<strong>D-' + r.distribution_id + ' &middot; ' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_label) + '</strong>' +
            '<div class="gis-route-detail-grid">' +
            '<div><span>' + distanceLabel + '</span><strong>' + distanceValue + '</strong></div>' +
            '<div><span>Est. Travel Time</span><strong>' + timeValue + '</strong></div>' +
            '<div><span>Packs</span><strong>' + fmt(r.packs) + '</strong></div>' +
            '<div><span>Status</span><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></div>' +
            '</div>';
    }

    // Gets the actual road route for a delivery from the free OSRM map service and draws it.
    // If the service is unavailable, a straight line and straight-line distance are shown instead.
    function loadOsrmRoute(r, rowEl) {
        osrmRouteLayer.clearLayers();
        document.querySelectorAll('#routes-table-body tr.gis-route-row-active').forEach(function (el) {
            el.classList.remove('gis-route-row-active');
        });
        rowEl.classList.add('gis-route-row-active');
        activeRouteRowId = r.distribution_id;

        if (r.from_lat == null || r.to_lat == null) {
            showRouteDetail('<strong>D-' + r.distribution_id + '</strong>' +
                '<span>Route unavailable - no coordinates on record for this warehouse or barangay.</span>');
            return;
        }

        showRouteDetail('<strong>D-' + r.distribution_id + '</strong><span>Loading route…</span>');
        var url = 'https://router.project-osrm.org/route/v1/driving/' +
            r.from_lng + ',' + r.from_lat + ';' + r.to_lng + ',' + r.to_lat +
            '?overview=full&geometries=geojson';
        var controller = ('AbortController' in window) ? new AbortController() : null;
        var timer = controller ? setTimeout(function () { controller.abort(); }, 10000) : null;
        fetch(url, controller ? { signal: controller.signal } : undefined)
            .then(function (resp) { if (!resp.ok) throw new Error('routing failed'); return resp.json(); })
            .then(function (data) {
                if (timer) clearTimeout(timer);
                if (activeRouteRowId !== r.distribution_id) return;
                if (!data.routes || !data.routes.length) throw new Error('no route');
                var route = data.routes[0];
                L.geoJSON(route.geometry, {
                    pane: 'routePane',
                    style: { color: '#ffffff', weight: 9, opacity: 0.95 },
                }).addTo(osrmRouteLayer);
                var line = L.geoJSON(route.geometry, {
                    pane: 'routePane',
                    style: { color: ROUTE_COLOR, weight: 5, opacity: 1 },
                }).addTo(osrmRouteLayer);
                var pin = addRouteEndpoints(r);

                var km = (route.distance / 1000).toFixed(1);
                var mins = Math.round(route.duration / 60);
                pinSummary(pin, r, km + ' km &middot; ' + mins + ' min');
                showRouteDetail(detailHtml(r, 'Distance', km + ' km', mins + ' min'));
                fitRouteBounds(line.getBounds());
            })
            .catch(function () {
                if (timer) clearTimeout(timer);
                if (activeRouteRowId !== r.distribution_id) return;
                var from = [r.from_lat, r.from_lng], to = [r.to_lat, r.to_lng];
                L.polyline([from, to], { pane: 'routePane', color: '#ffffff', weight: 8, opacity: 0.95 }).addTo(osrmRouteLayer);
                var straight = L.polyline([from, to], { pane: 'routePane', color: ROUTE_COLOR, weight: 4, opacity: 1, dashArray: '8 8' }).addTo(osrmRouteLayer);
                var pin = addRouteEndpoints(r);
                var km = (map.distance(from, to) / 1000).toFixed(1);
                pinSummary(pin, r, '~' + km + ' km straight line');
                showRouteDetail(detailHtml(r, 'Straight-line distance', '~' + km + ' km', 'n/a') +
                    '<span class="gis-route-note">Road route unavailable right now - showing a straight line between the two points instead. Click the row twice to retry.</span>');
                fitRouteBounds(straight.getBounds());
                rowEl.setAttribute('data-route-failed', '1');
            });
    }

    // Builds the summary number cards at the top of the side panel.
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

    var ICON = {
        mapPin: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e67e22" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        users: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        package: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#20bf6b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 9.4L7.5 4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
        arrow: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
        clipboard: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
        download: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        warehouse: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6.01"/><line x1="15" y1="6" x2="15" y2="6.01"/><line x1="9" y1="10" x2="9" y2="10.01"/><line x1="15" y1="10" x2="15" y2="10.01"/><line x1="9" y1="14" x2="9" y2="14.01"/><line x1="15" y1="14" x2="15" y2="14.01"/><line x1="9" y1="18" x2="9" y2="18.01"/></svg>',
        building: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="1"/><line x1="9" y1="7" x2="9" y2="7.01"/><line x1="15" y1="7" x2="15" y2="7.01"/><line x1="9" y1="11" x2="9" y2="11.01"/><line x1="15" y1="11" x2="15" y2="11.01"/><line x1="9" y1="15" x2="9" y2="15.01"/><line x1="15" y1="15" x2="15" y2="15.01"/><path d="M9 21v-3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/></svg>',
        search: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        chevronRight: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
        close: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        camera: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
        chevronLeft: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
    };

    // Builds a colored priority badge (e.g. 'High').
    function tierBadge(tier, label) {
        return '<span class="badge-priority badge-priority-' + tier + '"><i class="priority-dot"></i> ' + escapeHtml(label) + '</span>';
    }

    // Builds the 'View Barangay Reports' button (CSWDO/MSWDO only).
    function barangayReportsButtonHtml(lgu, barangayName) {
        if (!GIS_CONFIG.barangayReportsUrl) return '';
        return '<button type="button" class="btn-outline dd-full-width" data-external="barangay-reports" data-lgu="' + escapeHtml(lgu) + '"' +
            (barangayName ? ' data-barangay="' + escapeHtml(barangayName) + '"' : '') +
            ' style="justify-content:center; margin-top:10px;">' + ICON.clipboard + ' View Barangay Reports</button>';
    }

    // Builds the 'View Family Distributions' button (CSWDO/MSWDO only).
    function barangayDistributionsButtonHtml(barangayId) {
        if (!GIS_CONFIG.barangayDistributionsUrl || !barangayId) return '';
        return '<button type="button" class="btn-outline dd-full-width" data-external="barangay-distributions" data-barangay-id="' + barangayId + '"' +
            ' style="justify-content:center; margin-top:10px;">' + ICON.camera + ' View Family Distributions</button>';
    }

    // Builds the province overview side panel: summary numbers and each municipality's status.
    function renderOverviewPanel() {
        var html = renderStats(currentData.stats);

        var statusFilterEl = document.getElementById('filter-status');
        var statusFilter = statusFilterEl ? statusFilterEl.value : '';
        var visibleMunicipalities = statusFilter
            ? currentData.municipalities.filter(function (m) { return m.status_tier === statusFilter; })
            : currentData.municipalities;

        var muniColors = ['blue', 'purple', 'green', 'orange'];
        html += '<section class="panel"><div class="panel-header gis-muni-header">' +
            '<h3>Municipalities</h3>' +
            '<div class="gis-muni-search"><input type="text" id="gis-muni-search" placeholder="Search municipality…" autocomplete="off">' + ICON.search + '</div>' +
            '</div><div class="gis-muni-list">';
        if (!visibleMunicipalities.length) {
            html += '<p class="empty-note">No municipalities match the current filter.</p>';
        }
        visibleMunicipalities.forEach(function (m, idx) {
            html += '<div class="gis-priority-row gis-clickable" data-nav="municipality" data-lgu="' + escapeHtml(m.lgu) + '" data-muni-name="' + escapeHtml(m.lgu.toLowerCase()) + '">' +
                '<div class="gis-muni-row-icon ' + muniColors[idx % muniColors.length] + '">' + ICON.building + '</div>' +
                '<div><strong>' + escapeHtml(m.lgu) + '</strong><span>' + fmt(m.affected_barangays) + '/' + fmt(m.total_barangays) + ' barangays affected</span></div>' +
                '<div class="gis-priority-row-right">' + tierBadge(m.status_tier, m.status_label) + '</div>' +
                '<span class="gis-row-chevron">' + ICON.chevronRight + '</span>' +
                '</div>';
        });
        if (IS_MUNI_ONLY && !statusFilter) {
            currentData.province_context.features
                .filter(function (f) { return !f.properties.is_target; })
                .map(function (f) { return f.properties.name; })
                .sort(function (x, y) { return x.localeCompare(y); })
                .forEach(function (name) {
                    html += '<div class="gis-priority-row gis-clickable gis-muni-nodata" data-nav="municipality" data-lgu="' + escapeHtml(name) + '" data-muni-name="' + escapeHtml(name.toLowerCase()) + '">' +
                        '<div class="gis-muni-row-icon gray">' + ICON.building + '</div>' +
                        '<div><strong>' + escapeHtml(name) + '</strong><span>No data available</span></div>' +
                        '<div class="gis-priority-row-right">' + tierBadge('unrated', 'No data') + '</div>' +
                        '<span class="gis-row-chevron">' + ICON.chevronRight + '</span>' +
                        '</div>';
                });
        }
        html += '<p class="empty-note" id="gis-muni-search-empty" hidden>No municipality matches your search.</p>';
        html += '</div></section>';

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

    // Builds the food packs requested / approved / released lines.
    function reliefRows(relief) {
        return '' +
            '<div class="dd-summary-row"><span>Food Packs Requested</span><strong>' + fmt(relief.requested) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Food Packs Approved</span><strong>' + fmt(relief.approved) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Food Packs Released</span><strong class="text-green">' + fmt(relief.released) + '</strong></div>' +
            '<div class="dd-summary-row"><span>Remaining Need</span><strong class="text-red">' + fmt(relief.remaining) + '</strong></div>';
    }

    // Builds the side panel for one municipality: status, affected families,
    // food packs, warehouse stock and its barangays.
    function renderMunicipalityPanel(lgu) {
        var m = currentData.municipalities.find(function (x) { return x.lgu === lgu; });
        if (!m) {
            var known = currentData.province_context.features.some(function (f) { return f.properties.name === lgu; });
            if (!known) return '<p class="empty-note">Municipality not found.</p>';
            return '<section class="panel">' +
                '<div class="panel-header"><h3>' + escapeHtml(lgu) + '</h3>' + tierBadge('unrated', 'No data') + '</div>' +
                '<span class="rd-sub" style="display:block; margin-top:-10px; margin-bottom:14px;">Province of Pangasinan</span>' +
                '<p class="empty-note">No barangay data is tracked for this municipality yet, so there are no relief statistics, demand or allocation figures to show.</p>' +
                '</section>';
        }

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
                html += '<p class="empty-note">Per-barangay food-pack demand - not shown on the map by default.</p>';
            }
            html += '</section>';
        }

        html += '<section class="panel"><div class="panel-header"><h3>Warehouse Information</h3></div>';
        if (m.warehouse) {
            html += '<div class="dd-summary-row"><span>Assigned Warehouse</span><strong>' + escapeHtml(m.warehouse.name) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Current Stock</span><strong>' + (m.warehouse.food_pack_qty != null ? fmt(m.warehouse.food_pack_qty) + ' / ' + fmt(m.warehouse.capacity) + ' packs' : '-') + '</strong></div>';
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

        if (!IS_MUNI_ONLY) {
            html += '<section class="panel">';
            html += barangayReportsButtonHtml(m.lgu);
            html += '<button type="button" class="btn-decision dd-full-width gis-btn-dark" data-nav="barangay-list" data-lgu="' + escapeHtml(m.lgu) + '" style="margin-top:10px;">' + ICON.mapPin + ' View Barangays</button>';
            html += '<button type="button" class="btn-outline dd-full-width" data-external="report" data-lgu="' + escapeHtml(m.lgu) + '" style="justify-content:center; margin-top:10px;">' + ICON.download + ' Generate Report</button>';
            html += '</section>';
        }

        return html;
    }

    // Builds the list of barangays in a municipality (filtered by status if chosen).
    function renderBarangayListPanel(lgu) {
        var statusFilter = document.getElementById('filter-status').value;
        var features = currentData.target_barangays.features.filter(function (f) {
            return f.properties.lgu === lgu && (!statusFilter || f.properties.priority_tier === statusFilter);
        });
        var withData = features.filter(function (f) { return f.properties.has_data; });
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

    // Shows 'Loading barangay details...' while the details are fetched.
    function renderBarangayDetailLoading() {
        return '<section class="panel"><p class="empty-note">Loading barangay details…</p></section>';
    }

    // Builds the side panel for one barangay: status, report, stock and food packs.
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
                ? (b.barangay_on_hand === 0 && b.stock_need > 0 ? fmt(b.stock_need) + ' / 0 - critical' : '-')
                : fmt(b.stock_need) + ' / ' + fmt(b.barangay_on_hand) + ' (' + b.stock_ratio_pct + '%)') +
            '</strong></div>';
        html += '<div><span>Population</span><strong>' + fmt(b.population) + '</strong></div>';
        html += '<div><span>Households</span><strong>' + fmt(b.num_households) + '</strong></div>';
        html += '</div></section>';

        html += '<section class="panel"><div class="panel-header"><h3>Relief Statistics</h3></div>' + reliefRows(b.relief) + '</section>';

        html += '<section class="panel"><div class="panel-header"><h3>Distribution History</h3></div>';
        if (!b.distribution_history.length) {
            html += '<p class="empty-note">No distribution records for this barangay yet.</p>';
        } else {
            html += '<table class="wh-table"><thead><tr><th>DATE</th><th>PACKS</th><th>STATUS</th></tr></thead><tbody>';
            b.distribution_history.forEach(function (d, i) {
                html += '<tr' + (i >= 3 ? ' class="gis-dist-extra" hidden' : '') + '><td>' + escapeHtml(d.date) + '</td><td>' + fmt(d.packs) + '</td>' +
                    '<td><span class="badge-status badge-status-' + d.status + '">' + escapeHtml(d.status_label) + '</span></td></tr>';
            });
            html += '</tbody></table>';
            if (GIS_CONFIG.deliveriesUrl) {
                html += '<button type="button" class="btn-outline dd-full-width" data-external="barangay-deliveries" data-barangay-id="' + state.barangayId + '"' +
                    ' style="justify-content:center; margin-top:10px;">View All</button>';
            } else if (b.distribution_history.length > 3) {
                html += '<button type="button" class="btn-outline dd-full-width" data-gis-dist-expand' +
                    ' style="justify-content:center; margin-top:10px;">View All (' + b.distribution_history.length + ')</button>';
            }
        }
        html += '</section>';

        html += '<section class="panel">';
        html += barangayReportsButtonHtml(b.lgu, b.name);
        html += barangayDistributionsButtonHtml(state.barangayId);
        html += '</section>';
        return html;
    }

    // Shows the right side panel for the current view (province, municipality or barangay).
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

    // Builds the 'Province > Municipality > Barangay' path at the top of the map.
    function renderBreadcrumb() {
        var el = document.getElementById('gis-breadcrumb');
        var parts = [];
        if (!(GIS_CONFIG.role === 'cswdo_admin' && state.lgu)) {
            parts.push({ label: 'Province', nav: 'overview', disabled: true });
        }
        if (state.lgu) {
            parts.push({ label: state.lgu, nav: 'municipality', lgu: state.lgu });
        }
        if (state.level === 'barangay-list' || state.level === 'barangay-detail') {
            parts.push({ label: 'Barangays', nav: 'barangay-list', lgu: state.lgu });
        }
        if (state.level === 'barangay-detail') {
            parts.push({ label: state.barangayName, nav: 'barangay-detail', lgu: state.lgu, barangayId: state.barangayId, barangayName: state.barangayName });
        }

        var backBtn = '';
        var back = null;
        if (state.level === 'municipality' && GIS_CONFIG.role !== 'cswdo_admin') {
            back = { nav: 'overview' };
        } else if (state.level === 'barangay-list') {
            back = { nav: 'municipality', lgu: state.lgu };
        } else if (state.level === 'barangay-detail') {
            back = { nav: 'barangay-list', lgu: state.lgu };
        }
        if (back) {
            backBtn = '<button type="button" class="gis-back-btn" title="Back" aria-label="Back" data-nav="' + back.nav + '"' +
                (back.lgu ? ' data-lgu="' + escapeHtml(back.lgu) + '"' : '') + '>' + ICON.chevronLeft + '</button>';
        }

        el.innerHTML = backBtn + parts.map(function (p, i) {
            var isLast = i === parts.length - 1;
            var sep = isLast ? '' : '<span class="gis-crumb-sep">/</span>';
            if (isLast) return '<span class="gis-crumb-current">' + escapeHtml(p.label) + '</span>' + sep;
            if (p.disabled) return '<span class="gis-crumb-static">' + escapeHtml(p.label) + '</span>' + sep;
            var attrs = 'data-nav="' + p.nav + '"';
            if (p.lgu) attrs += ' data-lgu="' + escapeHtml(p.lgu) + '"';
            return '<span class="gis-crumb-link" ' + attrs + '>' + escapeHtml(p.label) + '</span>' + sep;
        }).join('');
    }

    // Zooms the map to the current view.
    function focusMap() {
        if (!currentData) return;
        if (state.level === 'overview') {
            var b = provinceLayer.getBounds();
            if (b && b.isValid()) map.fitBounds(b.pad(0.02));
            return;
        }
        var feats = currentData.target_barangays.features.filter(function (f) { return f.properties.lgu === state.lgu; });
        var bounds;
        if (feats.length) {
            bounds = L.geoJSON({ type: 'FeatureCollection', features: feats }).getBounds();
        } else {
            var muniFeature = currentData.province_context.features.find(function (f) { return f.properties.lgu === state.lgu || f.properties.name === state.lgu; });
            if (!muniFeature) return;
            bounds = L.geoJSON(muniFeature).getBounds();
        }
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
    }

    var routesById = {};

    // Builds the delivery routes table under the map (only the chosen municipality's routes if one is open).
    function renderRoutesTable() {
        clearRouteDetail();
        var routes = currentData ? currentData.routes_table : [];
        if (state.lgu) {
            routes = routes.filter(function (r) { return r.to_municipality === state.lgu; });
        }
        var brgyName = state.level === 'barangay-detail' ? state.barangayName : null;
        if (brgyName) {
            routes = routes.filter(function (r) { return r.to_barangay_id === state.barangayId; });
        }
        routesById = {};
        routes.forEach(function (r) { routesById[r.distribution_id] = r; });
        document.getElementById('routes-count').textContent = routes.length;
        var routesPill = document.getElementById('routes-count-pill');
        if (routesPill) routesPill.textContent = routes.length;
        var body = document.getElementById('routes-table-body');
        if (!routes.length) {
            var emptyMsg = brgyName
                ? 'No active distribution routes to ' + escapeHtml(brgyName) + ' right now.'
                : 'No active distribution routes right now.';
            body.innerHTML = '<tr><td colspan="5" class="empty-note" style="text-align:center; padding:24px;">' + emptyMsg + '</td></tr>';
            return;
        }
        body.innerHTML = routes.map(function (r) {
            return '<tr class="gis-route-row" data-distribution-id="' + r.distribution_id + '" title="Click to view route on map">' +
                '<td>D-' + r.distribution_id + '</td>' +
                '<td>' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_label) + '</td>' +
                '<td>' + fmt(r.packs) + '</td>' +
                '<td><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></td>' +
                '<td>' + escapeHtml(r.eta) + '</td>' +
                '</tr>';
        }).join('');
    }

    // Applies the status filter: only barangays with the chosen status stay on the map.
    function applyClientFilters() {
        if (!currentData) return;
        barangayLayer.clearLayers();
        barangayLabelLayer.clearLayers();
        barangayLabels = [];
        if (IS_MUNI_ONLY) return;

        var lgu = document.getElementById('filter-lgu').value;
        var status = document.getElementById('filter-status').value;

        var filtered = currentData.target_barangays.features.filter(function (f) {
            if (lgu && f.properties.lgu !== lgu) return false;
            if (status && f.properties.priority_tier !== status) return false;
            return true;
        });
        barangayLayer.addData({ type: 'FeatureCollection', features: filtered });
        if (state.level === 'barangay-detail' && state.barangayId) {
            barangayLayer.eachLayer(function (layer) {
                if (layer.feature && layer.feature.properties.barangay_id === state.barangayId) layer.bringToFront();
            });
        }
        rebuildBarangayLabels(filtered);
    }

    // Switches the view (province, municipality, or barangay),
    // then refreshes the map, side panel, path and routes table.
    function setLevel(level, lgu, barangayId, barangayName) {
        if (IS_MUNI_ONLY && (level === 'barangay-list' || level === 'barangay-detail')) {
            level = 'municipality';
        }
        state.level = level;
        state.lgu = lgu || null;
        state.barangayId = barangayId || null;
        state.barangayName = barangayName || null;
        state.showBreakdown = false;
        if (state.level !== 'overview' && panelWrap && panelWrap.classList.contains('is-collapsed')) {
            setPanelOpen(true);
        }
        var lguSelect = document.getElementById('filter-lgu');
        if (lguSelect.value !== (state.lgu || '')) {
            lguSelect.value = state.lgu || '';
            lguSelect.dispatchEvent(new Event('change'));
        }
        var brgySelect = document.getElementById('filter-barangay');
        if (brgySelect) {
            var wantBrgy = (state.level === 'barangay-detail' && state.barangayId) ? String(state.barangayId) : '';
            if (brgySelect.value !== wantBrgy) {
                brgySelect.value = wantBrgy;
                brgySelect.dispatchEvent(new Event('change'));
            }
        }
        provinceLayer.setStyle(provinceStyle);
        applyClientFilters();
        focusMap();
        renderBreadcrumb();
        renderPanel();
        renderRoutesTable();
        var onPhone = window.innerWidth < 700;
        if (IS_MUNI_ONLY && !onPhone && state.level !== 'overview' && routesPanel && routesPanel.hidden) {
            setRoutesOpen(true);
        }
        if (onPhone && state.level !== 'overview' && routesPanel && !routesPanel.hidden) {
            setRoutesOpen(false);
        }
        var floatingCard = document.querySelector('.gis-floating-card');
        if (floatingCard) floatingCard.scrollTop = 0;
    }

    // Opens a municipality when clicked, or goes back if it's already open.
    function toggleMunicipality(lgu) {
        if (state.level === 'municipality' && state.lgu === lgu) {
            if (!GIS_CONFIG.defaultLgu) setLevel('overview');
            return;
        }
        setLevel('municipality', lgu);
    }
    // Opens a barangay when clicked, or goes back if it's already open.
    function toggleBarangay(lgu, barangayId, barangayName) {
        if (state.level === 'barangay-detail' && state.barangayId === barangayId) {
            setLevel('municipality', lgu);
            return;
        }
        setLevel('barangay-detail', lgu, barangayId, barangayName);
    }

    var pendingNav = (function () {
        var params = new URLSearchParams(window.location.search);
        var municipality = params.get('municipality') || GIS_CONFIG.defaultLgu;
        var barangayId = params.get('barangay_id');
        if (!municipality && !barangayId) return null;
        return { municipality: municipality, barangayId: barangayId ? parseInt(barangayId, 10) : null };
    })();

    // Loads the map data from the server for the chosen disaster event, then draws everything.
    function loadData() {
        var eventId = document.getElementById('filter-event').value;
        var url = '/pswdo/gis-map/data' + (eventId ? '?event_id=' + eventId : '');
        fetch(url).then(function (r) { return r.json(); }).then(function (data) {
            currentData = data;
            provinceLayer.clearLayers();
            muniLabelLayer.clearLayers();
            provinceLayer.addData(data.province_context);
            renderWarehouses(data.warehouses);

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

    // Handles button clicks inside the side panel (breakdowns, links to other pages, etc.).
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
        var expandEl = e.target.closest('[data-gis-dist-expand]');
        if (expandEl) {
            expandEl.closest('section').querySelectorAll('.gis-dist-extra').forEach(function (tr) { tr.hidden = false; });
            expandEl.remove();
            return;
        }
        var extEl = e.target.closest('[data-external]');
        if (extEl) {
            var lguVal = extEl.getAttribute('data-lgu');
            var kind = extEl.getAttribute('data-external');
            var eventId = document.getElementById('filter-event').value;
            if (kind === 'barangay-reports' && GIS_CONFIG.barangayReportsUrl) {
                var brgy = extEl.getAttribute('data-barangay');
                window.location.href = GIS_CONFIG.barangayReportsUrl + (brgy ? '?tab=all&q=' + encodeURIComponent(brgy) : '');
            } else if (kind === 'barangay-deliveries' && GIS_CONFIG.deliveriesUrl) {
                window.location.href = GIS_CONFIG.deliveriesUrl + '?barangay_id=' + encodeURIComponent(extEl.getAttribute('data-barangay-id'));
            } else if (kind === 'barangay-distributions' && GIS_CONFIG.barangayDistributionsUrl) {
                window.location.href = GIS_CONFIG.barangayDistributionsUrl + '?barangay_id=' + encodeURIComponent(extEl.getAttribute('data-barangay-id'));
            } else if (kind === 'report') {
                window.location.href = '/pswdo/gis-map/municipality/' + encodeURIComponent(lguVal) + '/report.csv' + (eventId ? '?event_id=' + eventId : '');
            }
        }
    }
    document.getElementById('gis-breadcrumb').addEventListener('click', handleActionClick);
    document.getElementById('gis-info-panel').addEventListener('click', handleActionClick);

    var routesPanel = document.getElementById('gis-routes-panel');
    var routesToggle = document.getElementById('gis-routes-toggle');
    var routesMin = document.getElementById('gis-routes-min');
    var routesMapPanel = document.querySelector('.gis-map-panel');
    // Makes room at the bottom of the map for the routes panel when it is open.
    function syncDockSpace() {
        if (!routesMapPanel) return;
        var open = !routesPanel.hidden;
        routesMapPanel.classList.toggle('gis-dock-open', open);
        routesMapPanel.style.setProperty('--dock-h', open ? routesPanel.offsetHeight + 'px' : '0px');
    }
    // Opens or closes the delivery routes panel.
    function setRoutesOpen(open) {
        routesPanel.hidden = !open;
        routesToggle.hidden = open;
        syncDockSpace();
    }
    if (routesPanel && routesToggle && routesMin) {
        if ('ResizeObserver' in window) new ResizeObserver(syncDockSpace).observe(routesPanel);
        setRoutesOpen(window.innerWidth >= 1360);
        routesToggle.addEventListener('click', function () { setRoutesOpen(true); });
        routesMin.addEventListener('click', function () { setRoutesOpen(false); });
    }

    var panelWrap = document.getElementById('gis-floating-info');
    var panelCloseBtn = document.getElementById('gis-panel-close');
    var panelOpenBtn = document.getElementById('gis-panel-open');
    // Opens or closes the side info panel.
    function setPanelOpen(open) {
        panelWrap.classList.toggle('is-collapsed', !open);
        panelCloseBtn.hidden = !open;
        panelOpenBtn.hidden = open;
    }
    if (panelWrap && panelCloseBtn && panelOpenBtn) {
        panelCloseBtn.addEventListener('click', function () { setPanelOpen(false); });
        panelOpenBtn.addEventListener('click', function () { setPanelOpen(true); });
    }

    document.getElementById('gis-info-panel').addEventListener('input', function (e) {
        if (e.target.id !== 'gis-muni-search') return;
        var q = e.target.value.trim().toLowerCase();
        var shown = 0;
        document.querySelectorAll('.gis-muni-list [data-muni-name]').forEach(function (row) {
            var match = !q.length || row.getAttribute('data-muni-name').indexOf(q) !== -1;
            row.hidden = !match;
            if (match) shown++;
        });
        var emptyEl = document.getElementById('gis-muni-search-empty');
        if (emptyEl) emptyEl.hidden = shown > 0;
    });

    document.getElementById('filter-event').addEventListener('change', loadData);
    var barangayFilterEl = document.getElementById('filter-barangay');
    if (barangayFilterEl) {
        barangayFilterEl.addEventListener('change', function () {
            var current = (state.level === 'barangay-detail' && state.barangayId) ? String(state.barangayId) : '';
            if (this.value === current) return;
            var lgu = state.lgu || GIS_CONFIG.defaultLgu;
            if (!this.value) setLevel('municipality', lgu);
            else setLevel('barangay-detail', lgu, parseInt(this.value, 10), this.options[this.selectedIndex].text);
        });
    }
    document.getElementById('filter-lgu').addEventListener('change', function () {
        var lgu = this.value;
        if (lgu === (state.lgu || '')) return;
        setLevel(lgu ? 'municipality' : 'overview', lgu || null);
    });
    document.getElementById('filter-status').addEventListener('change', function () {
        applyClientFilters();
        if (state.level === 'barangay-list' || state.level === 'overview') renderPanel();
    });
    var refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) refreshBtn.addEventListener('click', loadData);

    // Shows or hides a map layer (e.g. warehouses, labels) with its checkbox.
    function wireLayerToggle(checkboxId, layers) {
        var cb = document.getElementById(checkboxId);
        if (!cb) return;
        cb.addEventListener('change', function () {
            layers.forEach(function (layer) {
                if (cb.checked) { map.addLayer(layer); } else { map.removeLayer(layer); }
            });
        });
    }
    wireLayerToggle('layer-toggle-municipality', [provinceLayer, muniLabelLayer]);
    wireLayerToggle('layer-toggle-barangay', [barangayLayer, barangayLabelLayer]);
    wireLayerToggle('layer-toggle-warehouse', [warehouseLayer]);

    var resetBtn = document.getElementById('btn-reset-map');
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            searchMarkerLayer.clearLayers();
            searchInputEl.value = '';
            updateSearchClearVisibility();
            hideSearchResults();
            clearRouteDetail();
            if (GIS_CONFIG.defaultLgu) setLevel('municipality', GIS_CONFIG.defaultLgu);
            else setLevel('overview');
        });
    }

    document.getElementById('gis-search-btn').addEventListener('click', runSearch);
    searchInputEl.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        var found = runSearch();
        if (found.length) selectSearchResult(found[0]);
    });
    searchInputEl.addEventListener('input', function () {
        updateSearchClearVisibility();
        runSearch();
    });
    searchClearEl.addEventListener('click', clearSearch);
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.gis-search-bar') && !e.target.closest('.gis-search-results')) {
            hideSearchResults();
        }
    });

    document.getElementById('gis-route-detail').addEventListener('click', function (e) {
        if (e.target.closest('.gis-route-detail-close')) clearRouteDetail();
    });
    document.getElementById('routes-table-body').addEventListener('click', function (e) {
        var row = e.target.closest('tr[data-distribution-id]');
        if (!row) return;
        var r = routesById[row.getAttribute('data-distribution-id')];
        if (!r) return;
        if (row.classList.contains('gis-route-row-active') && !row.hasAttribute('data-route-failed')) {
            clearRouteDetail();
            return;
        }
        row.removeAttribute('data-route-failed');
        loadOsrmRoute(r, row);
        var panelEl = document.querySelector('.gis-map-panel');
        if (panelEl && panelEl.scrollIntoView) panelEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    var legendToggle = document.getElementById('gis-legend-toggle');
    var legendBox = document.getElementById('gis-legend-box');
    if (legendToggle && legendBox) {
        legendToggle.addEventListener('click', function () { legendBox.classList.toggle('is-open'); });
    }

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
