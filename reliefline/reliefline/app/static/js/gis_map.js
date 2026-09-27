document.addEventListener('DOMContentLoaded', function () {
    var TIER_COLORS = {
        critical: '#e74c3c',
        high: '#e67e22',
        medium: '#f1c40f',
        low: '#27ae60',
        unrated: '#d8dee8',
    };
    // A darker shade of each TIER_COLORS hue, for the study-area polygon
    // border (gis_map.js provinceStyle) - the fill shows the status color
    // itself, the border is that same status "inked in" a shade darker, so
    // a critical (red) study area reads as a distinct dark-red outline, not
    // the same fixed purple every status used to get.
    var TIER_BORDER_COLORS = {
        critical: '#922b21',
        high: '#9c5310',
        medium: '#9a7d0a',
        low: '#1e8449',
        unrated: '#5d6d7e',
    };
    var TIER_RANK = { critical: 4, high: 3, medium: 2, low: 1, unrated: 0 };

    // zoomAnimation: false - .dashboard-layout applies a CSS `zoom` scale
    // (base.css, --ui-scale) to this whole page. Leaflet's animated zoom
    // transitions position markers/layers with a CSS transform computed in
    // its own pixel space, and that math doesn't account for an ancestor's
    // `zoom` scale - each zoom step compounds a small offset, which is
    // exactly the "warehouse pin drifts off its real spot" symptom reported
    // on this page. Disabling the animation makes every zoom step reproject
    // markers from their actual lat/lng instead of transforming the old
    // frame, so they stay pinned to the right spot at any zoom level.
    var map = L.map('gis-map', { zoomControl: false, zoomAnimation: false }).setView([15.98, 120.45], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Bottom-right instead of Leaflet's default top-left (which now sits
    // under the search bar overlay anyway) - restyled in gis_map.css to
    // match the app's own button/panel language instead of Leaflet's stock
    // look. Leaflet stacks same-corner controls itself, so this shares the
    // corner with the attribution control with no manual offset needed.
    L.control.zoom({ position: 'bottomleft' }).addTo(map);

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
    // both the PSWDO and CSWDO page templates) - role-specific destinations
    // and, for a single-LGU scope (CSWDO/MSWDO), the municipality to land on
    // by default instead of an overview that only ever has one entry.
    var GIS_CONFIG = window.RELIEFLINE_GIS_CONFIG || { role: null, barangayReportsUrl: null, defaultLgu: null };

    // PSWDO (province-wide oversight) sees municipality-level aggregates
    // only - no barangay boundaries, no barangay drill-down. That level of
    // operational detail is CSWDO/MSWDO's job (they only ever have one
    // municipality in scope anyway). system_admin gets the same province-wide
    // view PSWDO does.
    var IS_MUNI_ONLY = GIS_CONFIG.role !== 'cswdo_admin';

    // is_target is already restricted server-side to this user's own scope
    // (app.routes.pswdo._gis_scope_lgus) - a three-tier visual hierarchy:
    //   1. Other municipalities - light grey, thin border, muted fill.
    //      Real PSGC boundaries now (not placeholder shapes), shown at
    //      every drill-down level, never hidden - see TARGET_LGUS in
    //      app.routes.pswdo for why only 3 LGUs get further detail.
    //   2. Study area (Urdaneta City / Santa Barbara / Calasiao), not the
    //      one currently open - same purple border as every study area
    //      (that border is what marks "this is one of the 3", consistently),
    //      filled with that LGU's own real demand tier color (PSWDO/
    //      system_admin only - same Critical/High/Medium/Low/Unrated scale
    //      as the legend and every badge elsewhere) so the map itself
    //      answers "which study area needs attention right now" at a
    //      glance. Recomputed fresh from currentData every render.
    //   3. The study area currently open (state.lgu) - strongest border/
    //      fill of the three, plus the zoom-in and side-panel detail that
    //      setLevel() already drives.
    // CSWDO/MSWDO (single-LGU scope) keeps a flat purple fill instead -
    // that account's own dashboard already covers its one town's status,
    // so this map doesn't need to repeat it as a color.
    function provinceStyle(feature) {
        var isTarget = feature.properties.is_target;
        if (!isTarget) {
            if (state.lgu && state.lgu === feature.properties.name) {
                return { color: '#374151', weight: 3, fillColor: '#9aa0ae', fillOpacity: 0.7 };
            }
            return { color: '#6b7280', weight: 1.2, fillColor: '#c3c7d1', fillOpacity: 0.5 };
        }
        // className is set once when the layer/path DOM element is first
        // created (Leaflet doesn't re-apply it on a later setStyle() -
        // setLevel() below only ever calls setStyle(), never recreates the
        // layer) - so it has to stay the same string across selected/
        // unselected, and "strongest" instead comes entirely from the
        // color/weight/fillOpacity numbers below, which setStyle() DOES
        // update live.
        var isSelected = state.lgu === feature.properties.lgu;
        var fillColor = '#5347ce';
        var borderColor = isSelected ? '#3d2eb0' : '#5347ce';
        if (IS_MUNI_ONLY) {
            var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === feature.properties.lgu; }) : null;
            var tier = muni ? muni.status_tier : 'unrated';
            fillColor = TIER_COLORS[tier];
            // Border is that same status color, darker - not the fixed
            // purple every status used to get - so a critical (red) study
            // area outlines in dark red, a low (green) one in dark green, etc.
            borderColor = TIER_BORDER_COLORS[tier];
        }
        return {
            color: borderColor,
            weight: isSelected ? 4 : 2.5,
            fillColor: fillColor,
            // CSWDO/MSWDO: no fill at all on the municipality shape - the
            // barangay layer drawn on top of it IS the status colouring, and
            // a translucent purple fill underneath tinted every status
            // colour (green "Low" came out teal, not the legend's green).
            fillOpacity: IS_MUNI_ONLY ? (isSelected ? 0.65 : 0.45) : 0,
            className: 'gis-target-muni',
        };
    }

    // Always-on municipality/city name labels - separate from the hover
    // tooltips below (which carry demand data for in-scope LGUs and a
    // "no data" note for everyone else) so every one of the province's 48
    // LGUs reads its name at a glance without hovering. Plain divIcon
    // markers, not interactive, so clicks/hover still reach the polygon
    // underneath rather than the label.
    var muniLabelLayer = L.layerGroup().addTo(map);

    var provinceLayer = L.geoJSON(null, {
        style: provinceStyle,
        onEachFeature: function (feature, layer) {
            var p = feature.properties;
            var labelBounds = layer.getBounds();
            if (labelBounds.isValid()) {
                // Study-area labels are also a click target for setLevel(),
                // not just decoration - Calasiao/Santa Barbara's own
                // polygons can be a tiny sliver at whole-province zoom (much
                // smaller than Urdaneta City's), easy to miss with a click;
                // the label sits at a fixed, always-legible spot regardless
                // of how small the real shape renders, so it's a far more
                // reliable place to click "this municipality" than the
                // shape itself at that zoom level.
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
                    labelMarker.on('click', function () { setLevel('municipality', p.lgu); });
                }
            }
            if (p.is_target) {
                // currentData is already assigned before addData() runs (see
                // loadData()), so the per-LGU relief rollup - the closest
                // real figure to "predicted demand" this dataset has - is
                // available here to enrich the hover tooltip.
                var muni = currentData ? currentData.municipalities.find(function (m) { return m.lgu === p.lgu; }) : null;
                var demandLine = muni ? (
                    '<br>Predicted Demand: ' + fmt(muni.predicted_demand) + ' packs' +
                    '<br>Demand Level: ' + escapeHtml(muni.status_label)
                ) : '';
                layer.bindTooltip('<strong>' + escapeHtml(p.lgu) + '</strong>' + demandLine + '<br><em>Click to view</em>', { sticky: true });
                layer.on('click', function () { setLevel('municipality', p.lgu); });
                // Hover deepens the fill (a real, visible color change - no
                // shadow/glow filter involved anywhere on this layer any
                // more) plus a slightly thicker border. mouseout resets via
                // provinceStyle(feature) itself, not hardcoded numbers, so
                // it's always exactly back to this LGU's real current
                // tier/selection style - never stale if either changes
                // while the cursor happens to be sitting on it.
                layer.on('mouseover', function () {
                    layer.setStyle({
                        weight: state.lgu === p.lgu ? 4.5 : 3.2,
                        fillOpacity: IS_MUNI_ONLY ? (state.lgu === p.lgu ? 0.8 : 0.65) : 0,
                    });
                });
                layer.on('mouseout', function () { layer.setStyle(provinceStyle(feature)); });
            } else {
                // Outside current detailed coverage - hover or click both
                // answer with just the name plus why nothing else shows, as
                // a small, auto-dismissing tooltip rather than a modal-style
                // popup with its own close button. Deliberately stops
                // there: no stock/request/prediction figures, because none
                // exist for this municipality (see
                // app.routes.pswdo.TARGET_LGUS) and inventing any would
                // misrepresent real coverage.
                layer.bindTooltip(
                    '<strong>' + escapeHtml(p.name) + '</strong>' +
                    '<span class="gis-neutral-tt-note">Outside current detailed data coverage' +
                    (IS_MUNI_ONLY ? '<br><em>Click to view</em>' : '') + '</span>',
                    { className: 'gis-neutral-tooltip', sticky: true }
                );
                // PSWDO/system_admin (province-wide oversight) can open any
                // municipality - it just lands on an empty-state panel, see
                // renderMunicipalityPanel. A CSWDO/MSWDO account's other
                // LGUs stay inert, as before.
                layer.on('click', function (e) {
                    if (IS_MUNI_ONLY) setLevel('municipality', p.name);
                    else layer.openTooltip(e.latlng);
                });
                // Fill darkens too on hover, not just the border - a weight/
                // color-only change was easy to miss on a shape this small
                // at province zoom; the fill covers the whole shape, so its
                // change reads immediately as "this one, right here".
                layer.on('mouseover', function () { layer.setStyle({ weight: 2, color: '#4b5563', fillColor: '#9aa0ac', fillOpacity: 0.65 }); });
                // mouseout resets via provinceStyle so a currently-selected
                // no-data municipality keeps its selected look.
                layer.on('mouseout', function () { layer.setStyle(provinceStyle(feature)); });
            }
        },
    }).addTo(map);

    // Barangay name labels (CSWDO/MSWDO layout - PSWDO has no barangay layer).
    // Plain text divIcons like the municipality labels, one per barangay
    // currently drawn (so the Status filter thins them out along with the
    // shapes), each placed at a point that's actually INSIDE its polygon - a
    // bounding-box centre can land outside a concave barangay. Whether a
    // label is shown depends on zoom: it only appears once its polygon is
    // wide enough on screen to hold the name, so 34 names don't pile up on
    // top of each other (and on tiny barangays) at the municipality view -
    // zooming in reveals the rest.
    var barangayLabelLayer = L.layerGroup().addTo(map);
    var barangayLabels = [];

    function ringArea(ring) {
        var s = 0;
        for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            s += (ring[j][0] * ring[i][1]) - (ring[i][0] * ring[j][1]);
        }
        return s / 2;
    }
    function pointInRing(pt, ring) {
        var inside = false;
        for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
            var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
            if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) inside = !inside;
        }
        return inside;
    }
    // [lat, lng] label spot for a Polygon/MultiPolygon: the area-weighted
    // centroid of its largest outer ring, or - if that falls outside the
    // shape - the middle of the widest horizontal chord through the
    // centroid's latitude.
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
            barangayLabels.push({ marker: marker, name: f.properties.name, bounds: L.geoJSON(f).getBounds() });
        });
        updateBarangayLabelVisibility();
    }

    function updateBarangayLabelVisibility() {
        if (!barangayLabels.length) return;
        var cbox = map.getContainer().getBoundingClientRect();
        var taken = [];
        // The municipality's own name label (and anything else already on
        // screen at that spot) is an obstacle too.
        document.querySelectorAll('.gis-muni-label-target').forEach(function (e) {
            var r = e.getBoundingClientRect();
            if (r.width) taken.push({ l: r.left - cbox.left, t: r.top - cbox.top, r: r.right - cbox.left, b: r.bottom - cbox.top });
        });
        // Biggest barangays claim their spot first; a smaller one whose label
        // would land on top of an already-placed label stays hidden until
        // there's room for it (zooming in makes room - every barangay shows
        // by one zoom level closer).
        barangayLabels.map(function (entry) {
            var sw = map.latLngToContainerPoint(entry.bounds.getSouthWest());
            var ne = map.latLngToContainerPoint(entry.bounds.getNorthEast());
            return { entry: entry, area: Math.abs(ne.x - sw.x) * Math.abs(sw.y - ne.y) };
        }).sort(function (x, y) { return y.area - x.area; }).forEach(function (item) {
            var entry = item.entry, el = entry.marker.getElement();
            if (!el) return;
            var pt = map.latLngToContainerPoint(entry.marker.getLatLng());
            var w = entry.name.length * 5.6 + 8, h = 13;
            var box = { l: pt.x - w / 2, t: pt.y - h / 2, r: pt.x + w / 2, b: pt.y + h / 2 };
            var clash = taken.some(function (t) {
                return !(box.r <= t.l || t.r <= box.l || box.b <= t.t || t.b <= box.t);
            });
            el.style.display = clash ? 'none' : '';
            if (!clash) taken.push(box);
        });
    }
    barangayLabelLayer.on('add', updateBarangayLabelVisibility);
    map.on('zoomend moveend', updateBarangayLabelVisibility);

    var barangayLayer = L.geoJSON(null, {
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
                layer.on('click', function () { setLevel('barangay-detail', p.lgu, p.barangay_id, p.name); });
            } else {
                layer.bindTooltip(escapeHtml(p.name) + ' - no data on record', { sticky: true });
            }
        },
    }).addTo(map);

    var warehouseLayer = L.layerGroup().addTo(map);
    // Search result pin layer - kept separate from every other layer so a
    // search never disturbs municipality/warehouse/route rendering.
    var searchMarkerLayer = L.layerGroup().addTo(map);
    // The actual road-routed polyline (OSRM) for whichever Active
    // Distribution Routes row a user clicks into - routes stay hidden
    // otherwise, no in-transit line renders automatically for every
    // delivery, only for the one the user actually asked to see.
    var osrmRouteLayer = L.layerGroup().addTo(map);

    // Warehouse marker pixel size shrinks in steps as the map zooms out.
    // Markers are always placed at their real, fixed [lat, lng] (see
    // renderWarehouses below) - that never changes with zoom. What DOES
    // change with zoom, for every map (this isn't Leaflet-specific), is how
    // many screen pixels separate two markers that are a fixed real-world
    // distance apart: Calasiao and Santa Barbara's warehouses are only
    // ~8km apart, so at a zoomed-out view their fixed-size 30px icons can
    // visually touch or overlap even though neither one has actually
    // moved. Shrinking the icon at lower zoom keeps them visually distinct
    // instead of reading as "the pin jumped".
    var WH_ICON_ZOOM_BREAKPOINTS = [
        { minZoom: 13, size: 30 },
        { minZoom: 11, size: 24 },
        { minZoom: 9, size: 18 },
        { minZoom: 0, size: 14 },
    ];
    function warehouseIconSize() {
        var zoom = map.getZoom();
        for (var i = 0; i < WH_ICON_ZOOM_BREAKPOINTS.length; i++) {
            if (zoom >= WH_ICON_ZOOM_BREAKPOINTS[i].minZoom) return WH_ICON_ZOOM_BREAKPOINTS[i].size;
        }
        return 14;
    }
    // iconAnchor is always exactly half of iconSize (recomputed here every
    // time, never hardcoded) so the anchor point - the marker's actual
    // [lat, lng] - stays under the icon's visual center at every size.
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
    // (marker, healthClass) pairs currently on the map, so a zoomend can
    // re-run buildWarehouseIcon() on each without re-fetching/re-placing
    // any of them - only the icon's pixel size changes, never the marker's
    // underlying latlng.
    var warehouseMarkers = [];
    map.on('zoomend', function () {
        warehouseMarkers.forEach(function (entry) {
            entry.marker.setIcon(buildWarehouseIcon(entry.healthClass));
        });
    });

    function renderWarehouses(warehouses) {
        warehouseLayer.clearLayers();
        warehouseMarkers = [];
        warehouses.forEach(function (w) {
            var healthClass = (w.health || 'low').toLowerCase();
            // A plain building icon, colored by stock health, instead of a
            // 2-3 letter abbreviation of the warehouse's name - "C"/"SB"/
            // "UC" read as unexplained codes to anyone who hasn't memorized
            // which warehouse each stands for. The full name is still one
            // click away in the popup below.
            var marker = L.marker([w.lat, w.lng], { icon: buildWarehouseIcon(healthClass), title: w.name });
            warehouseMarkers.push({ marker: marker, healthClass: healthClass });
            // Food packs are the one figure every warehouse popup leads
            // with, everywhere in the app - the badge next to it is the
            // same badge-health used on the Dashboard/Warehouse Inventory,
            // so "is this warehouse okay" reads the same way here too.
            var popupHtml =
                '<strong>' + escapeHtml(w.name) + '</strong>' +
                '<span>' + escapeHtml(w.area_covered) + '</span>' +
                '<div class="gis-wh-popup-stock">' +
                '<span class="gis-wh-popup-qty">' + fmt(w.food_pack_qty) + ' <small>/ ' + fmt(w.capacity) + ' packs (' + w.pct.toFixed(0) + '%)</small></span>' +
                '<span class="badge-health badge-' + healthClass + '">' + escapeHtml(w.health || 'No data available') + '</span>' +
                '</div>';
            // PSWDO only (CSWDO/MSWDO keeps the popup exactly as it was) -
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

    // ---- Search box ------------------------------------------------
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

    // The search box finds things IN THIS MAP'S SCOPE and opens the one you
    // pick, the same as clicking it on the map - not an arbitrary street/place
    // lookup. PSWDO/system_admin: MUNICIPALITIES (all 48 in the province map,
    // with or without data). CSWDO/MSWDO: BARANGAYS of their own
    // municipality (the only ones on their map). Matched locally against the
    // already-loaded map data, so it's instant and needs no network.
    function searchCandidates() {
        if (IS_MUNI_ONLY) {
            return currentData.province_context.features.map(function (f) {
                var name = f.properties.is_target ? f.properties.lgu : f.properties.name;
                return {
                    name: name,
                    sub: 'Municipality &middot; ' + (f.properties.is_target ? 'has data' : 'no data'),
                    pick: function () { setLevel('municipality', name); },
                };
            });
        }
        return currentData.target_barangays.features.map(function (f) {
            var pr = f.properties;
            return {
                name: pr.name,
                sub: 'Barangay &middot; ' + escapeHtml(pr.lgu),
                pick: function () { setLevel('barangay-detail', pr.lgu, pr.barangay_id, pr.name); },
            };
        });
    }

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

    function selectSearchResult(m) {
        searchMarkerLayer.clearLayers();
        hideSearchResults();
        searchInputEl.value = m.name;
        updateSearchClearVisibility();
        m.pick();
    }

    // ---- OSRM route visualization (Active Distribution Routes) ------
    // Free public demo router, no API key. Draws the actual road path
    // (distinct solid teal line) plus a popup with real distance/duration
    // from OSRM itself - separate from the schematic dashed lines above.
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
        // Close button on the selected route's strip: puts the route away
        // (line, pin, highlighted row) - see the delegated click listener
        // near the routes table wiring below, since this markup is replaced
        // on every showRouteDetail() call.
        detailEl.innerHTML = '<button type="button" class="gis-route-detail-close" title="Close route" aria-label="Close route">' + ICON.close + '</button>' + html;
    }

    // Small colored dot marker for a route's start/end point - see the
    // comment at its call site in loadOsrmRoute for why this is a plain
    // L.marker (marker pane) instead of L.circleMarker (SVG).
    function routeDotIcon(fillColor) {
        return L.divIcon({
            className: 'gis-route-dot',
            html: '<span style="background:' + fillColor + '"></span>',
            iconSize: [14, 14],
            iconAnchor: [7, 7],
        });
    }

    // Location-pin marker for a route's destination. Anchored at the pin's
    // TIP (bottom centre), not its centre like routeDotIcon, so the tip sits
    // exactly on the destination's real [lat, lng] and the pin's body rises
    // above it - a plain marker-pane element, for the same reason as the dots.
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

    // Start dot + destination pin for a route. Plain L.marker dots, not
    // L.circleMarker (SVG) - after the fitBounds() jump, Leaflet's SVG
    // renderer's own internal positioning can end up visibly offset from
    // marker-pane elements (like the warehouse icon under them) even though
    // both come from the exact same [lat, lng] - a real, reproducible
    // Leaflet quirk under this page's CSS zoom scale (base.css --ui-scale),
    // not a coordinate error. Marker-pane elements sidestep it entirely and
    // land exactly on the warehouse icon's own real position. The
    // destination is a location pin, drawn above the warehouse icon that can
    // sit on the very same point (a PSWDO route ends at the receiving
    // municipality's own warehouse). Returns the pin so the caller can put
    // the distance/time summary on it.
    // One colour for the whole route (line, straight-line fallback, start dot)
    // - the app's own indigo instead of the earlier teal, which blended into
    // the green "Low" study-area fills and the blue water it usually crosses.
    var ROUTE_COLOR = '#5347ce';

    function addRouteEndpoints(r) {
        L.marker([r.from_lat, r.from_lng], { icon: routeDotIcon(ROUTE_COLOR), keyboard: false })
            .bindTooltip(escapeHtml(r.from_office)).addTo(osrmRouteLayer);
        return L.marker([r.to_lat, r.to_lng], { icon: routePinIcon('#e74c3c'), keyboard: false, zIndexOffset: 1000 })
            .addTo(osrmRouteLayer);
    }

    // Pads the fit away from the overlays on the map itself - the toolbar
    // row along the top (and the tall destination pin under it), and the
    // info card on the right while it's open - so the route's end never
    // lands hidden underneath them.
    function fitRouteBounds(bounds) {
        var infoWrap = document.getElementById('gis-floating-info');
        var panelOpen = infoWrap && !infoWrap.classList.contains('is-collapsed');
        // ...and the routes dock along the bottom, when it's open (PSWDO
        // layout) - it's taller while a route's detail strip is showing, so
        // this is measured, not a fixed number.
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

    // The summary sits on the map itself (a permanent tooltip over the
    // destination pin), not only in the table's detail strip below the map -
    // the table can be scrolled well out of sight of the route it just drew.
    function pinSummary(pin, r, line2) {
        pin.bindTooltip('<strong>' + escapeHtml(r.to_label) + '</strong><br>' + line2,
            { permanent: true, direction: 'top', className: 'gis-route-tt' });
    }

    function detailHtml(r, distanceLabel, distanceValue, timeValue) {
        return '<strong>D-' + r.distribution_id + ' &middot; ' + escapeHtml(r.from_office) + ' &rarr; ' + escapeHtml(r.to_label) + '</strong>' +
            '<div class="gis-route-detail-grid">' +
            '<div><span>' + distanceLabel + '</span><strong>' + distanceValue + '</strong></div>' +
            '<div><span>Est. Travel Time</span><strong>' + timeValue + '</strong></div>' +
            '<div><span>Packs</span><strong>' + fmt(r.packs) + '</strong></div>' +
            '<div><span>Status</span><span class="badge-status badge-status-' + r.status + '">' + escapeHtml(r.status_label) + '</span></div>' +
            '</div>';
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
                '<span>Route unavailable - no coordinates on record for this warehouse or barangay.</span>');
            return;
        }

        showRouteDetail('<strong>D-' + r.distribution_id + '</strong><span>Loading route…</span>');
        var url = 'https://router.project-osrm.org/route/v1/driving/' +
            r.from_lng + ',' + r.from_lat + ';' + r.to_lng + ',' + r.to_lat +
            '?overview=full&geometries=geojson';
        // The public OSRM demo server can hang as easily as it can fail
        // outright - without a timeout the row would sit on "Loading route…"
        // indefinitely instead of falling through to the straight-line view.
        var controller = ('AbortController' in window) ? new AbortController() : null;
        var timer = controller ? setTimeout(function () { controller.abort(); }, 10000) : null;
        fetch(url, controller ? { signal: controller.signal } : undefined)
            .then(function (resp) { if (!resp.ok) throw new Error('routing failed'); return resp.json(); })
            .then(function (data) {
                if (timer) clearTimeout(timer);
                if (activeRouteRowId !== r.distribution_id) return; // a newer click superseded this one
                if (!data.routes || !data.routes.length) throw new Error('no route');
                var route = data.routes[0];
                // A white "casing" drawn first, wider than the route line
                // itself, then the solid teal line on top - keeps the route
                // clearly visible/highlighted against ANY background it
                // crosses (a solid study-area fill, another municipality,
                // busy basemap detail), not just readable against a plain
                // map. Same technique real map products use for a route
                // that has to stay legible over arbitrary terrain.
                L.geoJSON(route.geometry, {
                    style: { color: '#ffffff', weight: 9, opacity: 0.95 },
                }).addTo(osrmRouteLayer);
                var line = L.geoJSON(route.geometry, {
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
                // Road routing didn't come back (server down, slow, or no
                // road path) - still show WHERE the delivery is going with
                // a straight line between the two real endpoints, clearly
                // labelled as not a road route, rather than an empty map.
                var from = [r.from_lat, r.from_lng], to = [r.to_lat, r.to_lng];
                L.polyline([from, to], { color: '#ffffff', weight: 8, opacity: 0.95 }).addTo(osrmRouteLayer);
                var straight = L.polyline([from, to], { color: ROUTE_COLOR, weight: 4, opacity: 1, dashArray: '8 8' }).addTo(osrmRouteLayer);
                var pin = addRouteEndpoints(r);
                var km = (map.distance(from, to) / 1000).toFixed(1);
                pinSummary(pin, r, '~' + km + ' km straight line');
                showRouteDetail(detailHtml(r, 'Straight-line distance', '~' + km + ' km', 'n/a') +
                    '<span class="gis-route-note">Road route unavailable right now - showing a straight line between the two points instead. Click the row twice to retry.</span>');
                fitRouteBounds(straight.getBounds());
                rowEl.setAttribute('data-route-failed', '1');
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
        warehouse: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6.01"/><line x1="15" y1="6" x2="15" y2="6.01"/><line x1="9" y1="10" x2="9" y2="10.01"/><line x1="15" y1="10" x2="15" y2="10.01"/><line x1="9" y1="14" x2="9" y2="14.01"/><line x1="15" y1="14" x2="15" y2="14.01"/><line x1="9" y1="18" x2="9" y2="18.01"/></svg>',
        building: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="1"/><line x1="9" y1="7" x2="9" y2="7.01"/><line x1="15" y1="7" x2="15" y2="7.01"/><line x1="9" y1="11" x2="9" y2="11.01"/><line x1="15" y1="11" x2="15" y2="11.01"/><line x1="9" y1="15" x2="9" y2="15.01"/><line x1="15" y1="15" x2="15" y2="15.01"/><path d="M9 21v-3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/></svg>',
        search: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        chevronRight: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
        close: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        chevronLeft: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
    };

    function tierBadge(tier, label) {
        return '<span class="badge-priority badge-priority-' + tier + '"><i class="priority-dot"></i> ' + escapeHtml(label) + '</span>';
    }

    // Used by renderMunicipalityPanel and renderBarangayDetail. Scoped to the
    // role it belongs to (see app.routes.pswdo._gis_config) - the button is
    // simply omitted for the other role rather than linking somewhere it
    // would 403 or make no sense: reviewing barangay reports is entirely a
    // CSWDO/MSWDO responsibility, PSWDO has no barangay-report page.
    function barangayReportsButtonHtml(lgu, barangayName) {
        if (!GIS_CONFIG.barangayReportsUrl) return '';
        return '<button type="button" class="btn-outline dd-full-width" data-external="barangay-reports" data-lgu="' + escapeHtml(lgu) + '"' +
            (barangayName ? ' data-barangay="' + escapeHtml(barangayName) + '"' : '') +
            ' style="justify-content:center; margin-top:10px;">' + ICON.clipboard + ' View Barangay Reports</button>';
    }

    function renderOverviewPanel() {
        var html = renderStats(currentData.stats);

        // Top filter bar's Status select doubles as this list's own filter
        // for PSWDO/system_admin (which has no barangay layer of its own to
        // filter - see applyClientFilters) - same tier values either way.
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
        // Every other municipality on the province map - not part of the
        // predictive/status model, so no barangay data behind them (and no
        // drill-down beyond an empty-state panel, see renderMunicipalityPanel).
        // Only when no Status filter is applied, since they have no status.
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

        // Barangay-level priority listing is CSWDO/MSWDO operational detail
        // - PSWDO's oversight view stops at the "Municipalities" list above,
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
                html += '<p class="empty-note">Per-barangay food-pack demand - not shown on the map by default.</p>';
            }
            html += '</section>';
        }

        html += '<section class="panel"><div class="panel-header"><h3>Warehouse Information</h3></div>';
        if (m.warehouse) {
            html += '<div class="dd-summary-row"><span>Assigned Warehouse</span><strong>' + escapeHtml(m.warehouse.name) + '</strong></div>';
            html += '<div class="dd-summary-row"><span>Approx. Distance</span><strong>' + (m.warehouse.distance_km != null ? (m.warehouse.distance_km < 0.5 ? 'Same municipality' : '~' + m.warehouse.distance_km + ' km') : '-') + '</strong></div>';
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
                ? (b.barangay_on_hand === 0 && b.stock_need > 0 ? fmt(b.stock_need) + ' / 0 - critical' : '-')
                : fmt(b.stock_need) + ' / ' + fmt(b.barangay_on_hand) + ' (' + b.stock_ratio_pct + '%)') +
            '</strong></div>';
        html += '<div><span>Population</span><strong>' + fmt(b.population) + '</strong></div>';
        html += '<div><span>Households</span><strong>' + fmt(b.num_households) + '</strong></div>';
        html += '<div><span>Poverty Incidence</span><strong>' + (b.poverty_incidence != null ? b.poverty_incidence + '%' : '-') + '</strong></div>';
        html += '<div><span>Disaster Risk Index</span><strong>' + (b.disaster_risk_index != null ? b.disaster_risk_index : '-') + '</strong></div>';
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
        // "Province" is province-wide oversight - a PSWDO/system_admin
        // concern only (see IS_MUNI_ONLY above). A CSWDO/MSWDO account is
        // already locked to its own single LGU server-side, so this crumb
        // stays as a plain, non-clickable label for them instead of a link
        // back to a province overview they have no business opening.
        // ...so for that account the crumb trail starts at its own
        // municipality instead: "Province" would only be a dead label.
        if (!(GIS_CONFIG.role === 'cswdo_admin' && state.lgu)) {
            // Plain text for everyone now - the back button (left of the trail)
            // is the way up a level, so "Province" isn't a link any more.
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

        // Back button: one level up from wherever you are (municipality ->
        // province overview, barangay list -> municipality, barangay detail
        // -> barangay list), so you don't have to aim for the "Province"
        // crumb. Not shown at the top level, or for a CSWDO/MSWDO account at
        // its own municipality (its "Province" crumb is disabled, there's no
        // province overview for it to go back to). Reuses the same data-nav
        // attributes the crumbs use, so handleActionClick needs no changes.
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

    function focusMap() {
        if (!currentData) return;
        if (state.level === 'overview') {
            // Whole province (every municipality in province_context, not
            // just the 3 target LGUs, and not the target LGUs' barangays -
            // those sit in a narrow N-S sliver, so fitting to them alone
            // stretched the map's east-west extent to match the
            // container's wide aspect ratio and left far-off municipalities
            // e.g. Alaminos, San Carlos) out of frame instead of the
            // intended province-wide overview. Applies to PSWDO and
            // CSWDO/MSWDO alike - the geographic overview is the same
            // regardless of how much of it has detailed data.
            var b = provinceLayer.getBounds();
            if (b && b.isValid()) map.fitBounds(b.pad(0.02));
            return;
        }
        var feats = currentData.target_barangays.features.filter(function (f) { return f.properties.lgu === state.lgu; });
        var bounds;
        if (feats.length) {
            bounds = L.geoJSON({ type: 'FeatureCollection', features: feats }).getBounds();
        } else {
            // No barangay-level boundaries loaded for this LGU yet (barangay
            // drill-down isn't wired up) - fall back to the municipality's
            // own real PSGC boundary from province_context, which is always
            // present, so "zoom to the selected study area" still works on
            // its own instead of silently doing nothing.
            var muniFeature = currentData.province_context.features.find(function (f) { return f.properties.lgu === state.lgu || f.properties.name === state.lgu; });
            if (!muniFeature) return;
            bounds = L.geoJSON(muniFeature).getBounds();
        }
        if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
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
        var routesPill = document.getElementById('routes-count-pill');
        if (routesPill) routesPill.textContent = routes.length;
        var body = document.getElementById('routes-table-body');
        if (!routes.length) {
            body.innerHTML = '<tr><td colspan="5" class="empty-note" style="text-align:center; padding:24px;">No active distribution routes right now.</td></tr>';
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
        rebuildBarangayLabels(filtered);
    }

    function setLevel(level, lgu, barangayId, barangayName) {
        // Municipality-level view never drills further than 'municipality' -
        // no barangay boundary layer is even populated to select from.
        if (IS_MUNI_ONLY && (level === 'barangay-list' || level === 'barangay-detail')) {
            level = 'municipality';
        }
        state.level = level;
        state.lgu = lgu || null;
        state.barangayId = barangayId || null;
        state.barangayName = barangayName || null;
        state.showBreakdown = false;
        // Picking a municipality (map, list, search box or filter) while the
        // info card is closed brings it back on its own - otherwise the
        // selection happens with nothing showing what was selected, and the
        // hamburger has to be pressed as a second step. Going back to the
        // province overview (Reset) doesn't reopen it: closing it was a
        // deliberate choice and nothing new was picked.
        if (state.level !== 'overview' && panelWrap && panelWrap.classList.contains('is-collapsed')) {
            setPanelOpen(true);
        }
        // Keep the Municipality dropdown showing what's actually selected
        // when the selection came from somewhere else (map, list, search
        // box, Reset). Setting .value alone updates the hidden native
        // <select> but not the visible custom-select trigger (see
        // custom_select.js) - it only re-renders its label on a 'change'
        // event, so one is dispatched; the listener below ignores it since
        // the value already matches state.lgu.
        var lguSelect = document.getElementById('filter-lgu');
        if (lguSelect.value !== (state.lgu || '')) {
            lguSelect.value = state.lgu || '';
            lguSelect.dispatchEvent(new Event('change'));
        }
        // Same for the Barangay filter (CSWDO/MSWDO layout only): it shows the
        // barangay currently open, or "All Barangays" at the municipality
        // level, whichever way the selection was made.
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
        // Same as the info card above: picking any municipality while the
        // Active Distribution panel is minimised brings it back - including
        // ones with nothing in transit, where it shows its "No active
        // distribution routes" note, so it's clear there's simply nothing
        // there rather than the panel having failed to open.
        // PSWDO only: a CSWDO/MSWDO account is always "in" a municipality, so
        // every barangay click would re-open a panel it had just minimised.
        var onPhone = window.innerWidth < 700;
        if (IS_MUNI_ONLY && !onPhone && state.level !== 'overview' && routesPanel && routesPanel.hidden) {
            setRoutesOpen(true);
        }
        // On a phone the info card and the routes panel are both bottom
        // sheets, so only one shows at a time (see gis_map.css): opening a
        // municipality's card puts the routes panel back to its pill.
        if (onPhone && state.level !== 'overview' && routesPanel && !routesPanel.hidden) {
            setRoutesOpen(false);
        }
        // #gis-info-panel's content just got fully replaced, but its
        // scrollable ancestor (.gis-floating-card, now that the info panel
        // floats on the map instead of a plain sidebar) keeps whatever
        // scrollTop it had from the PREVIOUS level's content - a browser
        // never resets a container's scroll position just because its
        // children changed. Left alone, drilling into a municipality right
        // after scrolling the overview list would render the new panel
        // already scrolled past its own header.
        var floatingCard = document.querySelector('.gis-floating-card');
        if (floatingCard) floatingCard.scrollTop = 0;
    }

    // Deep-link support so links from other pages (e.g. the Dashboard's mini
    // map) can land directly on a municipality or barangay instead of overview.
    // Falls back to GIS_CONFIG.defaultLgu when there's no explicit query param
    // - a CSWDO/MSWDO admin's scope is a single municipality, so there's no
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
            if (kind === 'barangay-reports' && GIS_CONFIG.barangayReportsUrl) {
                var brgy = extEl.getAttribute('data-barangay');
                window.location.href = GIS_CONFIG.barangayReportsUrl + (brgy ? '?tab=all&q=' + encodeURIComponent(brgy) : '');
            } else if (kind === 'report') {
                window.location.href = '/pswdo/gis-map/municipality/' + encodeURIComponent(lguVal) + '/report.csv' + (eventId ? '?event_id=' + eventId : '');
            }
        }
    }
    document.getElementById('gis-breadcrumb').addEventListener('click', handleActionClick);
    document.getElementById('gis-info-panel').addEventListener('click', handleActionClick);

    // Active Distribution Routes dock (PSWDO layout): a panel on the map
    // itself that minimises to a pill button. Open by default where there's
    // room beside the legend and the info card; on a narrow window it would
    // cover most of the map, so it starts as the pill there instead.
    var routesPanel = document.getElementById('gis-routes-panel');
    var routesToggle = document.getElementById('gis-routes-toggle');
    var routesMin = document.getElementById('gis-routes-min');
    // The map panel carries whether the dock is open and how tall it is (as
    // --dock-h), so the CSS can stack the info card ABOVE it on windows too
    // narrow for the two to sit side by side, instead of one covering the other.
    var routesMapPanel = document.querySelector('.gis-map-panel');
    function syncDockSpace() {
        if (!routesMapPanel) return;
        var open = !routesPanel.hidden;
        routesMapPanel.classList.toggle('gis-dock-open', open);
        routesMapPanel.style.setProperty('--dock-h', open ? routesPanel.offsetHeight + 'px' : '0px');
    }
    function setRoutesOpen(open) {
        routesPanel.hidden = !open;
        routesToggle.hidden = open;
        syncDockSpace();
    }
    if (routesPanel && routesToggle && routesMin) {
        // Its height changes as rows load and while a route's detail strip is
        // showing - keep the reserved space in step.
        if ('ResizeObserver' in window) new ResizeObserver(syncDockSpace).observe(routesPanel);
        setRoutesOpen(window.innerWidth >= 1360);
        routesToggle.addEventListener('click', function () { setRoutesOpen(true); });
        routesMin.addEventListener('click', function () { setRoutesOpen(false); });
    }

    // Floating panel close (X) / reopen (hamburger) - PSWDO layout only;
    // the CSWDO page keeps its plain sidebar and has neither button.
    var panelWrap = document.getElementById('gis-floating-info');
    var panelCloseBtn = document.getElementById('gis-panel-close');
    var panelOpenBtn = document.getElementById('gis-panel-open');
    function setPanelOpen(open) {
        panelWrap.classList.toggle('is-collapsed', !open);
        panelCloseBtn.hidden = !open;
        panelOpenBtn.hidden = open;
    }
    if (panelWrap && panelCloseBtn && panelOpenBtn) {
        panelCloseBtn.addEventListener('click', function () { setPanelOpen(false); });
        panelOpenBtn.addEventListener('click', function () { setPanelOpen(true); });
    }

    // #gis-muni-search is re-created on every renderOverviewPanel() call, so
    // this listens on the panel itself (delegation, same pattern as
    // handleActionClick above) instead of being re-wired per render.
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
            if (this.value === current) return; // setLevel's own sync event
            var lgu = state.lgu || GIS_CONFIG.defaultLgu;
            if (!this.value) setLevel('municipality', lgu);
            else setLevel('barangay-detail', lgu, parseInt(this.value, 10), this.options[this.selectedIndex].text);
        });
    }
    document.getElementById('filter-lgu').addEventListener('change', function () {
        var lgu = this.value;
        if (lgu === (state.lgu || '')) return; // already showing this one (setLevel's own sync event)
        setLevel(lgu ? 'municipality' : 'overview', lgu || null);
    });
    document.getElementById('filter-status').addEventListener('change', function () {
        applyClientFilters();
        if (state.level === 'barangay-list' || state.level === 'overview') renderPanel();
    });
    var refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) refreshBtn.addEventListener('click', loadData);

    // Map Layers checkboxes (legend box) - each just shows/hides a real
    // Leaflet layer group already on the map, nothing re-fetched. Municipality
    // Boundary also toggles the name-label layer with it, since a label with
    // no boundary underneath it reads as a stray floating word.
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

    // Reset: back to the starting view - the province overview for PSWDO; for
    // a CSWDO/MSWDO account (single-LGU scope, no real province overview) its
    // own municipality, which is where that account lands to begin with.
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

    // Search: button click or Enter key; results dismiss on outside click.
    document.getElementById('gis-search-btn').addEventListener('click', runSearch);
    searchInputEl.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        // Enter opens the best (first) match instead of just re-listing.
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

    // Active Distribution Routes: click a row to draw its real OSRM route.
    document.getElementById('gis-route-detail').addEventListener('click', function (e) {
        if (e.target.closest('.gis-route-detail-close')) clearRouteDetail();
    });
    document.getElementById('routes-table-body').addEventListener('click', function (e) {
        var row = e.target.closest('tr[data-distribution-id]');
        if (!row) return;
        var r = routesById[row.getAttribute('data-distribution-id')];
        if (!r) return;
        // Clicking the row that's already showing its route puts it away
        // again (a way to clear the map without hunting for another
        // control). A row that fell back to the straight line re-tries the
        // road route instead, so a transient OSRM failure isn't sticky.
        if (row.classList.contains('gis-route-row-active') && !row.hasAttribute('data-route-failed')) {
            clearRouteDetail();
            return;
        }
        row.removeAttribute('data-route-failed');
        loadOsrmRoute(r, row);
        // CSWDO's routes table still sits below its map - bring the map
        // into view, or the route it just drew is somewhere off-screen
        // above. (On the PSWDO page the table is on the map already.)
        var panelEl = document.querySelector('.gis-map-panel');
        if (panelEl && panelEl.scrollIntoView) panelEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    // Legend toggle - the legend is always on show on a desktop-sized window,
    // but on a phone it would cover most of the map, so there it starts hidden
    // behind this button (the button itself is display:none on desktop).
    var legendToggle = document.getElementById('gis-legend-toggle');
    var legendBox = document.getElementById('gis-legend-box');
    if (legendToggle && legendBox) {
        legendToggle.addEventListener('click', function () { legendBox.classList.toggle('is-open'); });
    }

    // Fullscreen toggle - expands the whole map panel (search bar, map,
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
