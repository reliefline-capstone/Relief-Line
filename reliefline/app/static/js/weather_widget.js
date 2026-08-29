/**
 * Weather & Typhoon Watch widget — fetches app.utils.weather's JSON snapshot
 * (served per-role at /pswdo/dashboard/weather, /cswdo/dashboard/weather,
 * /barangay/dashboard/weather) and renders it client-side.
 *
 * Fetched client-side on purpose: a slow or unreachable upstream (Open-Meteo
 * / GDACS) must never delay the dashboard's own server-rendered page load.
 * The container starts in a loading state and this script fills it in.
 *
 * Every host page must include a container like:
 *   <div class="weather-widget" data-weather-widget data-endpoint="{{ url_for('pswdo.dashboard_weather') }}"></div>
 *
 * A second, optional container renders a compact one-line summary — meant
 * for the dashboard's greeting banner, where a "condition + typhoon status"
 * glance belongs beside the clock rather than the full multi-day card:
 *   <div class="banner-weather-live" data-weather-header data-endpoint="..."></div>
 *
 * A third, optional container renders a compact multi-day forecast strip —
 * sits in the greeting banner where a manually-logged DisasterEvent badge
 * used to (that badge is a *record your office logged*, not live weather —
 * see app/models/disaster_event.py — so it doesn't belong next to a weather
 * widget; each dashboard shows it elsewhere if at all):
 *   <div class="banner-forecast-box" data-weather-forecast data-endpoint="..."></div>
 *
 * All containers fetch independently (they all hit the same 15-minute
 * server-side cache, so a second request in the same window is instant —
 * simpler than plumbing shared state between unrelated DOM regions).
 *
 * Icon paths are duplicated from app/utils/icons.py (the browser can't read
 * that file) — keep both in sync when adding a weather icon.
 */
(function () {
    "use strict";

    var REFRESH_MS = 15 * 60 * 1000; // matches the server's 15-minute cache TTL

    var WEATHER_ICONS = {
        "sun": '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
        "cloud": '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>',
        "cloud-drizzle": '<path d="M8 19v1"/><path d="M8 14v1"/><path d="M16 19v1"/><path d="M16 14v1"/><path d="M12 21v1"/><path d="M12 16v1"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>',
        "cloud-rain": '<line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>',
        "cloud-snow": '<path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25"/><line x1="8" y1="16" x2="8.01" y2="16"/><line x1="8" y1="20" x2="8.01" y2="20"/><line x1="12" y1="18" x2="12.01" y2="18"/><line x1="12" y1="22" x2="12.01" y2="22"/><line x1="16" y1="16" x2="16.01" y2="16"/><line x1="16" y1="20" x2="16.01" y2="20"/>',
        "cloud-lightning": '<path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/><polyline points="13 11 9 17 15 17 11 23"/>',
        "wind": '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>',
        "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "droplet": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>'
    };

    function svgIcon(name, size) {
        var paths = WEATHER_ICONS[name] || WEATHER_ICONS.cloud;
        size = size || 20;
        return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size +
            '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
            'stroke-linecap="round" stroke-linejoin="round">' + paths + '</svg>';
    }

    function escapeHtml(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    function renderCity(city) {
        if (!city || !city.available) {
            return (
                '<div class="weather-city weather-city-unavailable">' +
                '<span class="weather-city-name">' + escapeHtml(city ? city.city : "") + '</span>' +
                '<span class="weather-unavailable-note">' + svgIcon("cloud", 14) + ' Weather data unavailable right now</span>' +
                "</div>"
            );
        }
        var c = city.current;
        var forecastHtml = (city.forecast || []).map(function (f) {
            return (
                '<div class="weather-forecast-day">' +
                '<span class="wf-day">' + escapeHtml(f.day) + '</span>' +
                '<span class="wf-icon">' + svgIcon(f.icon, 16) + '</span>' +
                '<span class="wf-temps"><strong>' + (f.high != null ? f.high + "°" : "--") + '</strong> / ' + (f.low != null ? f.low + "°" : "--") + '</span>' +
                (f.rain_chance != null ? '<span class="wf-rain">' + f.rain_chance + '% rain</span>' : "") +
                "</div>"
            );
        }).join("");

        return (
            '<div class="weather-city">' +
            '<div class="weather-city-current">' +
            '<span class="weather-city-icon">' + svgIcon(c.icon, 28) + '</span>' +
            '<div class="weather-city-main">' +
            '<span class="weather-city-name">' + escapeHtml(city.city) + '</span>' +
            '<span class="weather-city-temp">' + (c.temperature != null ? c.temperature + "°C" : "--") + '</span>' +
            '<span class="weather-city-label">' + escapeHtml(c.label) +
            (c.feels_like != null ? " · feels like " + c.feels_like + "°C" : "") + '</span>' +
            '</div>' +
            '<div class="weather-city-extra">' +
            (c.wind_speed != null ? '<span>' + svgIcon("wind", 12) + ' ' + c.wind_speed + ' km/h</span>' : "") +
            (c.humidity != null ? '<span>' + svgIcon("droplet", 12) + ' ' + c.humidity + '%</span>' : "") +
            '</div>' +
            '</div>' +
            '<div class="weather-forecast-strip">' + forecastHtml + '</div>' +
            '</div>'
        );
    }

    function renderTyphoonWatch(watch, declareOpts) {
        declareOpts = declareOpts || {};
        if (!watch || !watch.available) {
            return (
                '<div class="typhoon-watch typhoon-watch-unknown">' +
                svgIcon("alert-triangle", 16) +
                '<span>Typhoon monitoring is temporarily unavailable — check PAGASA directly for the latest bulletin.</span>' +
                "</div>"
            );
        }
        if (!watch.active) {
            return (
                '<div class="typhoon-watch typhoon-watch-clear">' +
                svgIcon("check-circle", 16) +
                '<span>No active tropical cyclone in or near the Philippine Area of Responsibility.</span>' +
                "</div>"
            );
        }
        var storms = watch.storms.map(function (s) {
            var level = (s.alert_level || "Green").toLowerCase();
            return (
                '<div class="typhoon-storm typhoon-alert-' + escapeHtml(level) + '">' +
                svgIcon("alert-triangle", 14) +
                '<div>' +
                '<strong>' + escapeHtml(s.name || "Unnamed system") + '</strong>' +
                '<span class="typhoon-storm-meta">' + escapeHtml(s.severity_text || "") + '</span>' +
                (s.report_url ? '<a href="' + escapeHtml(s.report_url) + '" target="_blank" rel="noopener">View GDACS report →</a>' : "") +
                '</div>' +
                "</div>"
            );
        }).join("");

        // Live-detected system + PSWDO viewing + nothing already declared —
        // the one moment this data should turn into an action, not just a
        // reading. Pre-fills the modal from the first detected storm so
        // declaring it is a one-click confirm rather than retyping what's
        // already on screen.
        var cta = "";
        if (declareOpts.canDeclare && !declareOpts.hasActiveEvent) {
            var first = watch.storms[0] || {};
            cta = (
                '<button type="button" class="weather-declare-cta-btn" ' +
                'data-prefill-name="' + escapeHtml(first.name || "") + '" ' +
                'data-prefill-condition="' + escapeHtml(first.severity_text || "") + '">' +
                svgIcon("cloud-lightning", 13) + ' Declare as Disaster Event' +
                "</button>"
            );
        }
        return '<div class="typhoon-watch typhoon-watch-active">' + storms + cta + '</div>';
    }

    // --- Declare/End Disaster Event header action ---------------------------
    // PSWDO-only (gated by data-can-declare-events on the panel container —
    // see app.routes.pswdo.declare_disaster_event / end_disaster_event).
    // Only one of Declare/End ever renders: the app treats a single active
    // DisasterEvent as the current one everywhere, so both being available
    // at once would be misleading.

    function eventActionHtml(container) {
        if (container.dataset.canDeclareEvents !== "true") return "";
        var activeEventId = container.dataset.activeEventId;
        if (activeEventId) {
            return (
                '<form method="POST" action="' + escapeHtml(container.dataset.endUrl || "") + '" class="weather-end-form">' +
                '<button type="submit" class="weather-end-btn">' + svgIcon("check-circle", 14) + ' End Disaster Event</button>' +
                "</form>"
            );
        }
        return (
            '<button type="button" class="weather-declare-btn" data-declare-open>' +
            svgIcon("cloud-lightning", 14) + ' Declare Disaster Event' +
            "</button>"
        );
    }

    function wireEventActions(container) {
        var endForm = container.querySelector(".weather-end-form");
        if (endForm) {
            endForm.addEventListener("submit", function (e) {
                // Native confirm() dialogs look out of place next to the rest of
                // the app's own modal styling, so this opens the styled
                // #end-event-modal instead and only actually submits the form
                // once the user confirms there.
                e.preventDefault();
                openEndEventModal(endForm, container.dataset.activeEventName || "this event");
            });
        }
        var declareBtn = container.querySelector(".weather-declare-btn");
        if (declareBtn) {
            declareBtn.addEventListener("click", function () { openDeclareModal("", ""); });
        }
        container.querySelectorAll(".weather-declare-cta-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                openDeclareModal(btn.dataset.prefillName, btn.dataset.prefillCondition);
            });
        });
    }

    function openEndEventModal(form, name) {
        var modal = document.getElementById("end-event-modal");
        if (!modal) return;
        var nameEl = document.getElementById("end-event-name");
        if (nameEl) nameEl.textContent = name;
        modal.hidden = false;
        var confirmBtn = document.getElementById("end-event-confirm-btn");
        if (confirmBtn) {
            // Reassigning .onclick (rather than addEventListener) each time
            // keeps this to a single handler bound to the current form,
            // even if the widget re-renders and wires up a new one.
            confirmBtn.onclick = function () {
                modal.hidden = true;
                // form.submit() bypasses the 'submit' event entirely (unlike a
                // real button click), so this doesn't re-trigger the listener
                // above and reopen the modal.
                form.submit();
            };
        }
    }

    function openDeclareModal(name, condition) {
        var modal = document.getElementById("declare-event-modal");
        if (!modal) return;
        var nameInput = document.getElementById("declare-event-name");
        var condInput = document.getElementById("declare-weather-condition");
        if (nameInput) nameInput.value = name || "";
        if (condInput) condInput.value = condition || "";
        modal.hidden = false;
        if (nameInput) nameInput.focus();
    }

    function renderWidget(container, data) {
        var canDeclare = container.dataset.canDeclareEvents === "true";
        var hasActiveEvent = !!container.dataset.activeEventId;
        var citiesHtml = (data.cities || []).map(renderCity).join("");
        var typhoonHtml = renderTyphoonWatch(data.typhoon_watch, { canDeclare: canDeclare, hasActiveEvent: hasActiveEvent });
        var stamp = (data.typhoon_watch && data.typhoon_watch.fetched_at) || "";

        container.innerHTML = (
            '<div class="weather-widget-header">' +
            '<span class="weather-widget-title">' + svgIcon("cloud", 16) + ' Weather &amp; Typhoon Watch</span>' +
            '<div class="weather-widget-actions">' + eventActionHtml(container) +
            '<button type="button" class="weather-refresh-btn" aria-label="Refresh weather">↻ Refresh</button></div>' +
            "</div>" +
            typhoonHtml +
            '<div class="weather-cities">' + (citiesHtml || '<p class="weather-empty">No location configured.</p>') + '</div>' +
            '<p class="weather-attribution">Weather via Open-Meteo · Typhoon monitoring via GDACS' +
            (stamp ? " · updated " + escapeHtml(stamp.replace("T", " ")) : "") + '</p>'
        );

        var btn = container.querySelector(".weather-refresh-btn");
        if (btn) {
            btn.addEventListener("click", function () { loadWidget(container, true); });
        }
        wireEventActions(container);
    }

    function renderError(container) {
        container.innerHTML = (
            '<div class="weather-widget-header">' +
            '<span class="weather-widget-title">' + svgIcon("cloud", 16) + ' Weather &amp; Typhoon Watch</span>' +
            '<div class="weather-widget-actions">' + eventActionHtml(container) +
            '<button type="button" class="weather-refresh-btn" aria-label="Retry">↻ Retry</button></div>' +
            "</div>" +
            '<p class="weather-empty">Couldn\'t load live weather right now. This does not affect any other part of the dashboard.</p>'
        );
        var btn = container.querySelector(".weather-refresh-btn");
        if (btn) {
            btn.addEventListener("click", function () { loadWidget(container, true); });
        }
        wireEventActions(container);
    }

    function loadWidget(container, isManualRefresh) {
        var endpoint = container.getAttribute("data-endpoint");
        if (!endpoint) return;
        if (isManualRefresh) {
            container.classList.add("is-refreshing");
        }
        fetch(endpoint, { headers: { "Accept": "application/json" } })
            .then(function (res) {
                if (!res.ok) throw new Error("bad status " + res.status);
                return res.json();
            })
            .then(function (data) {
                renderWidget(container, data);
            })
            .catch(function () {
                renderError(container);
            })
            .finally(function () {
                container.classList.remove("is-refreshing");
            });
    }

    // --- Compact header chip (greeting banner) -----------------------------
    // A one-line "conditions + typhoon status" glance, distinct from the
    // full multi-city panel above. Uses the first city in the endpoint's
    // response — the viewer's own LGU for CSWDO/barangay, or the first of
    // the three target LGUs for PSWDO's province-wide view.

    function renderHeaderChip(container, data) {
        var city = (data.cities || [])[0];
        var conditionsHtml;
        if (city && city.available) {
            var c = city.current;
            conditionsHtml = (
                svgIcon(c.icon, 16) +
                '<span class="weather-header-city">' + escapeHtml(city.city) + '</span>' +
                '<span class="weather-header-temp">' + (c.temperature != null ? c.temperature + "°C" : "--") + '</span>' +
                '<span class="weather-header-cond">' + escapeHtml(c.label) + '</span>'
            );
        } else {
            conditionsHtml = svgIcon("cloud", 16) + '<span class="weather-header-cond">Weather unavailable</span>';
        }

        var watch = data.typhoon_watch;
        var typhoonHtml;
        if (!watch || !watch.available) {
            typhoonHtml = '<span class="weather-header-typhoon is-unknown">' + svgIcon("alert-triangle", 12) + ' Typhoon status unavailable</span>';
        } else if (watch.active) {
            var first = watch.storms[0] || {};
            var more = watch.storms.length > 1 ? " (+" + (watch.storms.length - 1) + " more)" : "";
            typhoonHtml = (
                '<span class="weather-header-typhoon is-alert">' + svgIcon("alert-triangle", 12) +
                ' Tropical Cyclone Watch: ' + escapeHtml(first.name || "Unnamed system") + escapeHtml(more) + '</span>'
            );
        } else {
            typhoonHtml = '<span class="weather-header-typhoon is-clear">' + svgIcon("check-circle", 12) + ' No active cyclone in the PAR</span>';
        }

        container.innerHTML = (
            '<div class="weather-header-conditions">' + conditionsHtml + '</div>' + typhoonHtml
        );
    }

    function renderHeaderError(container) {
        container.innerHTML = '<span class="weather-header-loading">Live conditions unavailable</span>';
    }

    function loadHeader(container) {
        var endpoint = container.getAttribute("data-endpoint");
        if (!endpoint) return;
        fetch(endpoint, { headers: { "Accept": "application/json" } })
            .then(function (res) {
                if (!res.ok) throw new Error("bad status " + res.status);
                return res.json();
            })
            .then(function (data) { renderHeaderChip(container, data); })
            .catch(function () { renderHeaderError(container); });
    }

    // --- Compact forecast strip (greeting banner, badge slot) --------------
    // Same multi-day data as the detail panel's per-city cards, just laid
    // out for the banner's dark background and tighter width.

    function renderForecastBox(container, data) {
        var city = (data.cities || [])[0];
        if (!city || !city.available || !city.forecast || !city.forecast.length) {
            container.innerHTML = '<span class="banner-forecast-error">' + svgIcon("cloud", 14) + ' Forecast unavailable' +
                (city ? " — " + escapeHtml(city.city) : "") + '</span>';
            return;
        }
        var daysHtml = city.forecast.map(function (f) {
            return (
                '<div class="banner-forecast-day">' +
                '<span class="bf-day">' + escapeHtml(f.day) + '</span>' +
                '<span class="bf-icon">' + svgIcon(f.icon, 16) + '</span>' +
                '<span class="bf-temps">' + (f.high != null ? f.high + "°" : "--") +
                '<span class="bf-low"> / ' + (f.low != null ? f.low + "°" : "--") + '</span></span>' +
                "</div>"
            );
        }).join("");
        container.innerHTML = (
            '<span class="banner-forecast-label">' + escapeHtml(city.city) + ' · 4-Day Forecast</span>' +
            '<div class="banner-forecast-strip">' + daysHtml + "</div>"
        );
    }

    function renderForecastError(container) {
        container.innerHTML = '<span class="banner-forecast-error">' + svgIcon("cloud", 14) + ' Forecast unavailable</span>';
    }

    function loadForecast(container) {
        var endpoint = container.getAttribute("data-endpoint");
        if (!endpoint) return;
        fetch(endpoint, { headers: { "Accept": "application/json" } })
            .then(function (res) {
                if (!res.ok) throw new Error("bad status " + res.status);
                return res.json();
            })
            .then(function (data) { renderForecastBox(container, data); })
            .catch(function () { renderForecastError(container); });
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-weather-widget]").forEach(function (container) {
            loadWidget(container, false);
            setInterval(function () { loadWidget(container, false); }, REFRESH_MS);
        });
        document.querySelectorAll("[data-weather-header]").forEach(function (container) {
            loadHeader(container);
            setInterval(function () { loadHeader(container); }, REFRESH_MS);
        });
        document.querySelectorAll("[data-weather-forecast]").forEach(function (container) {
            loadForecast(container);
            setInterval(function () { loadForecast(container); }, REFRESH_MS);
        });
    });
})();
