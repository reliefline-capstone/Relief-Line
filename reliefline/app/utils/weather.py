"""
Live weather, short-range forecast, and typhoon (tropical cyclone) monitoring
for the three target LGUs (Urdaneta City, Santa Barbara, Calasiao) named in
the manuscript's Scope and Limitations section.

This is a situational-awareness add-on layered on top of the manuscript's
core deliverables (Linear Regression allocation prediction + geospatial
mapping) — it does not feed the predictive model or change any of its six
predictor variables. It exists so PSWDO/CSWDO/barangay users can see current
conditions and an approaching tropical cyclone *before* someone manually logs
a DisasterEvent, the same way DisasterEvent.weather_condition already lets
them record conditions *after* the fact.

Two free, no-API-key data sources are used deliberately, so nobody has to
sign up for or manage a paid API key on a student capstone:

  - Open-Meteo (https://open-meteo.com) for current conditions + a 4-day
    forecast. Free for non-commercial use, no key required.
  - GDACS (https://gdacs.org), the UN/EU-run Global Disaster Alert and
    Coordination System, for active tropical cyclone monitoring worldwide.
    Also free, no key required. PAGASA has no public REST API, so GDACS's
    globally-sourced (NOAA-fed) tropical cyclone feed is used instead and
    filtered down to storms near/within the Philippine Area of
    Responsibility (PAR).

Both calls are wrapped in short timeouts + a small in-process TTL cache so a
slow or unreachable upstream (no internet in a sandboxed environment, an
outage, etc.) degrades to an "unavailable" flag rather than ever blocking a
dashboard page load. Routes should treat every field here as optional.
"""
import time
from datetime import datetime

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GDACS_EVENTS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"
REQUEST_TIMEOUT = 8  # seconds — generous since this is fetched client-side, off the page's own load path
REQUEST_RETRIES = 2  # one retry absorbs the occasional transient blip (seen in practice when
                      # 3 sequential per-city calls share one flaky connection) without a user-visible failure
CACHE_TTL = 900  # 15 minutes — plenty fresh for a relief-planning dashboard

# Approximate town-center coordinates for the three target LGUs (manuscript
# Scope and Limitations). Good enough for a city-level weather snapshot;
# per-barangay granularity isn't needed for pre-positioning/allocation
# decisions, which already operate at the city/municipality level upward.
LGU_COORDS = {
    "Urdaneta City": (15.9762, 120.5713),
    "Santa Barbara": (15.8961, 120.4991),
    "Calasiao": (16.0089, 120.4520),
    # Not one of the three target LGUs — this is the PSWDO's own seat (see
    # Appendix A: "Building, Solis Street, Poblacion Lingayen, Pangasinan").
    # Used only for the PSWDO dashboard's header ("conditions where we are"),
    # separate from the target-LGU breakdown in the dashboard's detail panel.
    "Lingayen": (16.0219, 120.2325),
}

# Philippine Area of Responsibility, loosely boxed — generous on purpose so a
# storm approaching from the Pacific still shows up a little before PAGASA
# would formally name it. Matches the manuscript's "Typhoon-Related Disaster
# Response" scope (typhoon + its direct effects: flash floods, storm surge,
# strong winds).
PAR_BOUNDS = {"lat_min": 4.0, "lat_max": 26.0, "lon_min": 114.0, "lon_max": 136.0}

# WMO weather codes (used by Open-Meteo) collapsed into the small icon set
# app.utils.icons actually has. Keep this mapping's icon names in sync with
# both app/utils/icons.py and the WEATHER_ICONS table duplicated in
# static/js/weather_widget.js (the browser can't read icons.py directly).
_WMO_CODE_MAP = {
    0: ("Clear sky", "sun"),
    1: ("Mainly clear", "sun"),
    2: ("Partly cloudy", "cloud"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "cloud"),
    48: ("Depositing rime fog", "cloud"),
    51: ("Light drizzle", "cloud-drizzle"),
    53: ("Drizzle", "cloud-drizzle"),
    55: ("Dense drizzle", "cloud-drizzle"),
    56: ("Freezing drizzle", "cloud-drizzle"),
    57: ("Dense freezing drizzle", "cloud-drizzle"),
    61: ("Light rain", "cloud-rain"),
    63: ("Rain", "cloud-rain"),
    65: ("Heavy rain", "cloud-rain"),
    66: ("Freezing rain", "cloud-rain"),
    67: ("Heavy freezing rain", "cloud-rain"),
    71: ("Light snow", "cloud-snow"),
    73: ("Snow", "cloud-snow"),
    75: ("Heavy snow", "cloud-snow"),
    77: ("Snow grains", "cloud-snow"),
    80: ("Light rain showers", "cloud-rain"),
    81: ("Rain showers", "cloud-rain"),
    82: ("Violent rain showers", "cloud-rain"),
    85: ("Light snow showers", "cloud-snow"),
    86: ("Heavy snow showers", "cloud-snow"),
    95: ("Thunderstorm", "cloud-lightning"),
    96: ("Thunderstorm w/ hail", "cloud-lightning"),
    99: ("Thunderstorm w/ heavy hail", "cloud-lightning"),
}

_weather_cache = {}  # city -> (fetched_at_epoch, payload)
_typhoon_cache = {"fetched_at": 0, "payload": None}


def _get_json(url, params=None):
    """requests.get(...).json() with a couple of immediate retries — cheap
    insurance against the occasional one-off timeout/connection blip that
    would otherwise fail a single city while its neighbors (fetched moments
    apart in the same request) succeed. Raises on the final attempt so the
    caller's existing except block still handles a genuinely-down upstream."""
    last_error = None
    for attempt in range(REQUEST_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
    raise last_error


def _describe_code(code):
    return _WMO_CODE_MAP.get(int(code), ("Unknown", "cloud")) if code is not None else ("Unknown", "cloud")


def _day_label(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return d.strftime("%a")


def get_weather(city, force_refresh=False):
    """Current conditions + next-4-days forecast for one of LGU_COORDS's
    cities. Returns a dict; on any failure (bad city name, network error,
    timeout, malformed response) returns {"available": False, "city": city}
    rather than raising, so a dashboard can always render *something*."""
    if city not in LGU_COORDS:
        return {"available": False, "city": city, "error": "unknown_city"}

    cached = _weather_cache.get(city)
    if not force_refresh and cached and (time.time() - cached[0]) < CACHE_TTL:
        return cached[1]

    lat, lon = LGU_COORDS[city]
    try:
        data = _get_json(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                           "precipitation,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "Asia/Manila",
                "forecast_days": 5,
                "wind_speed_unit": "kmh",
            },
        )

        current = data.get("current", {})
        label, icon = _describe_code(current.get("weather_code"))

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        rain_pct = daily.get("precipitation_probability_max", [])

        # Skip index 0 (today, already covered by "current") — next 4 days.
        forecast = []
        for i in range(1, min(len(dates), 5)):
            f_label, f_icon = _describe_code(codes[i]) if i < len(codes) else ("Unknown", "cloud")
            forecast.append({
                "day": _day_label(dates[i]),
                "date": dates[i],
                "label": f_label,
                "icon": f_icon,
                "high": round(highs[i]) if i < len(highs) and highs[i] is not None else None,
                "low": round(lows[i]) if i < len(lows) and lows[i] is not None else None,
                "rain_chance": rain_pct[i] if i < len(rain_pct) and rain_pct[i] is not None else None,
            })

        payload = {
            "available": True,
            "city": city,
            "current": {
                "temperature": round(current.get("temperature_2m")) if current.get("temperature_2m") is not None else None,
                "feels_like": round(current.get("apparent_temperature")) if current.get("apparent_temperature") is not None else None,
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": round(current.get("wind_speed_10m")) if current.get("wind_speed_10m") is not None else None,
                "precipitation": current.get("precipitation"),
                "label": label,
                "icon": icon,
            },
            "forecast": forecast,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "source": "Open-Meteo",
        }
        _weather_cache[city] = (time.time(), payload)
        return payload
    except (requests.RequestException, ValueError, KeyError, TypeError):
        # Serve a stale cached reading rather than nothing, if one exists.
        if cached:
            return cached[1]
        return {"available": False, "city": city, "error": "fetch_failed"}


def _in_par(lon, lat):
    return (PAR_BOUNDS["lat_min"] <= lat <= PAR_BOUNDS["lat_max"]
            and PAR_BOUNDS["lon_min"] <= lon <= PAR_BOUNDS["lon_max"])


def _mentions_philippines(feature_props):
    text = " ".join([
        feature_props.get("country") or "",
        " ".join(c.get("countryname", "") for c in feature_props.get("affectedcountries") or []),
    ]).lower()
    return "philippin" in text


def get_typhoon_watch(force_refresh=False):
    """Active tropical cyclones worldwide (from GDACS), filtered to ones
    near/within the Philippine Area of Responsibility or explicitly naming
    the Philippines as an affected country. Returns:

        {"available": True, "active": bool, "storms": [...], "fetched_at": ...}

    or {"available": False} if GDACS couldn't be reached. "active" is False
    (not missing) when GDACS is reachable but no PAR-relevant storm exists —
    that's the normal, good-news case, distinct from "we couldn't check"."""
    cached = _typhoon_cache["payload"]
    if not force_refresh and cached and (time.time() - _typhoon_cache["fetched_at"]) < CACHE_TTL:
        return cached

    try:
        data = _get_json(GDACS_EVENTS_URL)

        storms = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if props.get("eventtype") != "TC":
                continue
            coords = (feature.get("geometry") or {}).get("coordinates")
            lon, lat = (coords[0], coords[1]) if coords and len(coords) >= 2 else (None, None)
            near_par = (lon is not None and lat is not None and _in_par(lon, lat)) or _mentions_philippines(props)
            if not near_par:
                continue
            severity = props.get("severitydata", {})
            storms.append({
                "name": props.get("eventname") or props.get("name"),
                "alert_level": props.get("alertlevel"),
                "severity_text": severity.get("severitytext"),
                "max_wind_kmh": severity.get("severity"),
                "from_date": props.get("fromdate"),
                "to_date": props.get("todate"),
                "country": props.get("country") or None,
                "report_url": (props.get("url") or {}).get("report"),
                "lat": lat,
                "lon": lon,
            })

        payload = {
            "available": True,
            "active": len(storms) > 0,
            "storms": storms,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "source": "GDACS",
        }
        _typhoon_cache["fetched_at"] = time.time()
        _typhoon_cache["payload"] = payload
        return payload
    except (requests.RequestException, ValueError, KeyError, TypeError):
        if cached:
            return cached
        return {"available": False}


def get_dashboard_snapshot(cities):
    """Convenience bundle for a dashboard route: weather for each requested
    city plus the shared typhoon watch. `cities` is a list of LGU names from
    LGU_COORDS; unknown names are skipped rather than raising."""
    return {
        "cities": [get_weather(c) for c in cities if c in LGU_COORDS],
        "typhoon_watch": get_typhoon_watch(),
    }
