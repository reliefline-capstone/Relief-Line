// Weather & Typhoon Watch widget on the dashboards.
// Loads the weather and typhoon alerts from the server and shows them, with Declare/End Event buttons.
(function () {
    "use strict";

    var REFRESH_MS = 15 * 60 * 1000;

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

    // Builds a weather icon (sun, cloud, rain...).
    function svgIcon(name, size) {
        var paths = WEATHER_ICONS[name] || WEATHER_ICONS.cloud;
        size = size || 20;
        return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size +
            '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
            'stroke-linecap="round" stroke-linejoin="round">' + paths + '</svg>';
    }

    // Makes text safe to show on the page.
    function escapeHtml(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    // Builds the weather card for one municipality: current conditions and the next days' forecast.
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

    // Builds the Typhoon Watch section: active storms near the Philippines, or 'no active storms'.
    function renderTyphoonWatch(watch) {
        if (!watch || !watch.available) {
            return (
                '<div class="typhoon-watch typhoon-watch-unknown">' +
                svgIcon("alert-triangle", 16) +
                '<span>Typhoon monitoring is temporarily unavailable - check PAGASA directly for the latest bulletin.</span>' +
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

        return '<div class="typhoon-watch typhoon-watch-active">' + storms + '</div>';
    }

    // Builds the 'Declare Event' or 'End Event' button (only for users allowed to declare events).
    function eventActionHtml(container, opts) {
        opts = opts || {};
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
            '<button type="button" class="weather-declare-btn" data-declare-open ' +
            'data-prefill-name="' + escapeHtml(opts.prefillName || "") + '" ' +
            'data-prefill-condition="' + escapeHtml(opts.prefillCondition || "") + '">' +
            svgIcon("cloud-lightning", 14) + ' Declare Disaster Event' +
            "</button>"
        );
    }

    // Makes the Declare / End Event buttons work.
    function wireEventActions(container) {
        var endForm = container.querySelector(".weather-end-form");
        if (endForm) {
            endForm.addEventListener("submit", function (e) {
                e.preventDefault();
                openEndEventModal(endForm, container.dataset.activeEventName || "this event");
            });
        }
        var declareBtn = container.querySelector(".weather-declare-btn");
        if (declareBtn) {
            declareBtn.addEventListener("click", function () {
                openDeclareModal(declareBtn.dataset.prefillName || "", declareBtn.dataset.prefillCondition || "");
            });
        }
    }

    // Asks for confirmation before ending an event.
    function openEndEventModal(form, name) {
        var modal = document.getElementById("end-event-modal");
        if (!modal) return;
        var nameEl = document.getElementById("end-event-name");
        if (nameEl) nameEl.textContent = name;
        modal.hidden = false;
        var confirmBtn = document.getElementById("end-event-confirm-btn");
        if (confirmBtn) {
            // Ends the event once the user confirms.
            confirmBtn.onclick = function () {
                modal.hidden = true;
                form.submit();
            };
        }
    }

    // Opens the Declare Event form, pre-filled with the storm's name from the typhoon alert.
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

    // Builds the whole weather widget: header, municipality weather cards and typhoon watch.
    function renderWidget(container, data) {
        var watch = data.typhoon_watch;
        var firstStorm = (watch && watch.available && watch.active && watch.storms[0]) || {};
        var citiesHtml = (data.cities || []).map(renderCity).join("");
        var typhoonHtml = renderTyphoonWatch(watch);
        var stamp = (watch && watch.fetched_at) || "";

        container.innerHTML = (
            '<div class="weather-widget-header">' +
            '<span class="weather-widget-title">' + svgIcon("cloud", 16) + ' Weather &amp; Typhoon Watch</span>' +
            '<div class="weather-widget-actions">' +
            eventActionHtml(container, { prefillName: firstStorm.name, prefillCondition: firstStorm.severity_text }) +
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

    // Shows a message when the weather can't be loaded.
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

    // Loads the weather data from the server and shows it (also used by the Refresh button).
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

    // Builds the small weather display in the page header (temperature and conditions).
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

        container.innerHTML = '<div class="weather-header-conditions">' + conditionsHtml + '</div>';
    }

    // Shows 'Live conditions unavailable' in the header.
    function renderHeaderError(container) {
        container.innerHTML = '<span class="weather-header-loading">Live conditions unavailable</span>';
    }

    // Loads the header weather from the server.
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

    // Builds the forecast box (the next days' weather for the municipality).
    function renderForecastBox(container, data) {
        var city = (data.cities || [])[0];
        if (!city || !city.available || !city.forecast || !city.forecast.length) {
            container.innerHTML = '<span class="banner-forecast-error">' + svgIcon("cloud", 14) + ' Forecast unavailable' +
                (city ? " - " + escapeHtml(city.city) : "") + '</span>';
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

    // Shows 'Forecast unavailable' in the forecast box.
    function renderForecastError(container) {
        container.innerHTML = '<span class="banner-forecast-error">' + svgIcon("cloud", 14) + ' Forecast unavailable</span>';
    }

    // Loads the forecast from the server.
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
