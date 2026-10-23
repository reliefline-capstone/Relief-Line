# Gets weather and typhoon alerts from online weather services.

import time
from datetime import datetime

from app.utils.timezone import ph_now

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GDACS_EVENTS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"
REQUEST_TIMEOUT = 8
REQUEST_RETRIES = 2
CACHE_TTL = 900

LGU_COORDS = {
    "Urdaneta City": (15.9762, 120.5713),
    "Santa Barbara": (15.8961, 120.4991),
    "Calasiao": (16.0089, 120.4520),
    "Lingayen": (16.0219, 120.2325),
}

PAR_BOUNDS = {"lat_min": 4.0, "lat_max": 26.0, "lon_min": 114.0, "lon_max": 136.0}

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

_weather_cache = {}
_typhoon_cache = {"fetched_at": 0, "payload": None}


# Downloads data from an online weather service.
# If it fails, it tries again a few times before giving up.
def _get_json(url, params=None):
    last_error = None
    for attempt in range(REQUEST_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
    raise last_error


# Turns a weather code number into words and an icon (e.g. 61 = 'Light rain').
def _describe_code(code):
    return _WMO_CODE_MAP.get(int(code), ("Unknown", "cloud")) if code is not None else ("Unknown", "cloud")


# Turns a date into a short day name (e.g. 'Mon'), for the forecast.
def _day_label(iso_date):
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return d.strftime("%a")


# Gets the current weather and the next days' forecast for one municipality (from Open-Meteo).
# The result is saved for 15 minutes so the weather site isn't asked on every page load.
def get_weather(city, force_refresh=False):
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
            "fetched_at": ph_now().isoformat(timespec="seconds"),
            "source": "Open-Meteo",
        }
        _weather_cache[city] = (time.time(), payload)
        return payload
    except (requests.RequestException, ValueError, KeyError, TypeError):
        if cached:
            return cached[1]
        return {"available": False, "city": city, "error": "fetch_failed"}


# Checks if a storm is inside the Philippine Area of Responsibility (PAR),
# the area PAGASA monitors.
def _in_par(lon, lat):
    return (PAR_BOUNDS["lat_min"] <= lat <= PAR_BOUNDS["lat_max"]
            and PAR_BOUNDS["lon_min"] <= lon <= PAR_BOUNDS["lon_max"])


# Checks if a storm alert lists the Philippines as an affected country.
def _mentions_philippines(feature_props):
    text = " ".join([
        feature_props.get("country") or "",
        " ".join(c.get("countryname", "") for c in feature_props.get("affectedcountries") or []),
    ]).lower()
    return "philippin" in text


# Gets the active tropical storms near the Philippines (from GDACS) for the Typhoon Watch panel.
# The result is saved for 15 minutes.
def get_typhoon_watch(force_refresh=False):
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
            "fetched_at": ph_now().isoformat(timespec="seconds"),
            "source": "GDACS",
        }
        _typhoon_cache["fetched_at"] = time.time()
        _typhoon_cache["payload"] = payload
        return payload
    except (requests.RequestException, ValueError, KeyError, TypeError):
        if cached:
            return cached
        return {"available": False}


# Collects the weather for the given municipalities plus the typhoon watch,
# all in one package for the dashboard weather widget.
def get_dashboard_snapshot(cities):
    return {
        "cities": [get_weather(c) for c in cities if c in LGU_COORDS],
        "typhoon_watch": get_typhoon_watch(),
    }
