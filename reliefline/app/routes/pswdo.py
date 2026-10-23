# PSWDO pages: dashboard, warehouses, stock requests, transfers, deliveries, GIS map.

import calendar
import csv
import io
import json
import os
import re
from math import radians, sin, cos, sqrt, atan2

from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from datetime import date, datetime

from app.utils.timezone import ph_now, ph_today
from app.utils.stock_labels import stock_log_label
from werkzeug.utils import secure_filename
from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.barangay import Barangay
from app.models.barangay_inventory import BarangayInventory, food_pack_on_hand
from app.models.warehouse import WarehouseInventory, WarehouseStockLog
from app.models.food_pack_batch import FoodPackBatch, FoodPackComponent, FoodPackBatchItem
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.utils.filters import arg_date, date_range, in_range, iso
from app.models.disaster_event import DisasterEvent, event_categories_from_form
from app.models.barangay_status import BarangayDisasterStatus
from app.utils.disaster_events import (
    resolve_effective_event,
    blocking_event_for_province, relevant_active_events_query,
)
from app.models.activity_log import ActivityLog
from app.models.logistics import WarehouseTransfer
from app.models.relief_request_batch import ReliefRequestBatch
from app.models.barangay_report import BarangayReport
from app.models.user import User
from app.utils.settings import get_setting
from app.ml import predict as ml_predict
from app.utils import weather as weather_service

pswdo_bp = Blueprint("pswdo", __name__)

TARGET_LGUS = ["Urdaneta City", "Santa Barbara", "Calasiao"]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

WAREHOUSE_HEALTHY_DEFAULT = 0.70
WAREHOUSE_MODERATE_DEFAULT = 0.30


# The 'Healthy' warehouse level set by the System Admin (default 70% full).
# A warehouse at or above this level shows as 'Healthy'.
def _healthy_threshold():
    return get_setting("warehouse_healthy_threshold", WAREHOUSE_HEALTHY_DEFAULT, cast=float)


# The 'Moderate' warehouse level set by the System Admin (default 30% full).
# Between this and 'Healthy' shows as 'Moderate'; below it shows as 'Low'.
def _moderate_threshold():
    return get_setting("warehouse_moderate_threshold", WAREHOUSE_MODERATE_DEFAULT, cast=float)

PRIORITY_BY_STATUS = {
    "high_priority": {"label": "Critical", "tier": "critical", "detail": "Immediate action required", "rank": 4},
    "needs_assistance": {"label": "High", "tier": "high", "detail": "Needs attention", "rank": 3},
    "monitoring": {"label": "Medium", "tier": "medium", "detail": "Monitor", "rank": 2},
    "normal": {"label": "Low", "tier": "low", "detail": "Stable", "rank": 1},
}
DEFAULT_PRIORITY = {"label": "Unrated", "tier": "unrated", "detail": "No status on record", "rank": 0}


_STOCK_TIER = {
    "critical": {"label": "Critical", "tier": "critical", "rank": 4},
    "high":     {"label": "High",     "tier": "high",     "rank": 3},
    "medium":   {"label": "Medium",   "tier": "medium",   "rank": 2},
    "low":      {"label": "Low",      "tier": "low",      "rank": 1},
    "unrated":  {"label": "Unrated",  "tier": "unrated",  "rank": 0},
}


# Rates whether a barangay's own food packs can cover its reported need
# (Low, Medium, High or Critical concern). Used for the map colors and priority lists.
def _stock_adequacy(need, on_hand):
    if on_hand is None:
        return _STOCK_TIER["unrated"], None
    if need <= 0:
        return _STOCK_TIER["low"], 0.0
    if on_hand == 0:
        return _STOCK_TIER["critical"], None
    ratio = need / on_hand
    if ratio <= 0.50:
        key = "low"
    elif ratio <= 0.80:
        key = "medium"
    elif ratio < 1.00:
        key = "high"
    else:
        key = "critical"
    return _STOCK_TIER[key], round(ratio * 100, 1)


DISPATCH_STATUS_LABELS = {
    "preparing": "Preparing",
    "loaded": "Loaded",
    "dispatched": "Dispatched",
    "in_transit": "In Transit",
    "delivered": "Delivered",
}

DISPATCH_STEPS = ["approved", "preparing", "loaded", "dispatched", "in_transit", "delivered"]
STEP_LABELS = {
    "approved": "Approved", "preparing": "Preparing", "loaded": "Loaded",
    "dispatched": "Dispatched", "in_transit": "In Transit", "delivered": "Delivered",
}

ROUTE_PROGRESS_BY_STATUS = {
    "preparing": 0, "loaded": 10, "dispatched": 35,
    "in_transit": 65, "delivered": 100,
}

NOTIFICATION_META = {
    "allocation_approved": {"icon": "check-circle", "color": "#1e8449", "category": "relief_requests", "category_label": "Stock Requests"},
    "allocation_rejected": {"icon": "x-circle", "color": "#c0392b", "category": "relief_requests", "category_label": "Stock Requests"},
    "relief_request_submitted": {"icon": "clipboard", "color": "#3867d6", "category": "relief_requests", "category_label": "Stock Requests"},
    "distribution_status": {"icon": "truck", "color": "#2c5aa0", "category": "distribution", "category_label": "Deliveries"},
    "distribution_delivered": {"icon": "check-circle", "color": "#1e8449", "category": "distribution", "category_label": "Deliveries"},
    "warehouse_transfer_completed": {"icon": "rotate-ccw", "color": "#6c5ce7", "category": "warehouse", "category_label": "Warehouse"},
    "damage_report_submitted": {"icon": "clipboard", "color": "#3867d6", "category": "barangay_reports", "category_label": "Barangay Reports"},
    "damage_report_returned": {"icon": "x-circle", "color": "#c0392b", "category": "barangay_reports", "category_label": "Barangay Reports"},
    "barangay_relief_approved": {"icon": "check-circle", "color": "#1e8449", "category": "barangay_reports", "category_label": "Barangay Reports"},
    "barangay_relief_declined": {"icon": "x-circle", "color": "#c0392b", "category": "barangay_reports", "category_label": "Barangay Reports"},
    "barangay_report_verified": {"icon": "check-circle", "color": "#2c5aa0", "category": "barangay_reports", "category_label": "Barangay Reports"},
    "distribution_receipt_confirmed": {"icon": "check-circle", "color": "#1e8449", "category": "distribution", "category_label": "Deliveries"},
    "disaster_event_declared": {"icon": "cloud-lightning", "color": "#c0392b", "category": "disaster_events", "category_label": "Disaster Events"},
    "disaster_event_ended": {"icon": "check-circle", "color": "#1e8449", "category": "disaster_events", "category_label": "Disaster Events"},
    "direct_allocation": {"icon": "package", "color": "#6c5ce7", "category": "relief_requests", "category_label": "Stock Requests"},
    "cswdo_proactive_allocation": {"icon": "package", "color": "#6c5ce7", "category": "distribution", "category_label": "Deliveries"},
}
DEFAULT_NOTIFICATION_META = {"icon": "bell", "color": "#8a94a6", "category": "other", "category_label": "Other"}


# The icon, color and category of a notification type (used in notification lists).
@pswdo_bp.app_template_global()
def notif_meta(action_type):
    return NOTIFICATION_META.get(action_type, DEFAULT_NOTIFICATION_META)

PSWDO_EXCLUDED_NOTIFICATION_TYPES = {
    "damage_report_submitted", "damage_report_returned",
    "barangay_relief_approved", "barangay_relief_declined",
    "barangay_report_verified",
    "cswdo_proactive_allocation",
}
PSWDO_NOTIFICATION_TYPES = [k for k in NOTIFICATION_META if k not in PSWDO_EXCLUDED_NOTIFICATION_TYPES]


# Link to the stock request a notification is about.
def _batch_link(log):
    if log.batch_id:
        return url_for("pswdo.relief_request_detail", batch_id=log.batch_id)
    return url_for("pswdo.relief_requests")


# Finds the stock transfer linked to a stock request notification.
def _batch_transfer_id(log):
    if not log.batch_id:
        return None
    t = WarehouseTransfer.query.filter_by(batch_id=log.batch_id).order_by(
        WarehouseTransfer.transfer_id.desc()
    ).first()
    return t.transfer_id if t else None


NOTIFICATION_LINK_BUILDERS = {
    "allocation_approved": _batch_link,
    "allocation_rejected": _batch_link,
    "relief_request_submitted": _batch_link,
    "distribution_status": lambda log: url_for("pswdo.transfers"),
    "distribution_delivered": lambda log: url_for("pswdo.transfers"),
    "warehouse_transfer_completed": lambda log: (
        url_for("pswdo.transfer_detail", transfer_id=_batch_transfer_id(log)) if _batch_transfer_id(log)
        else (url_for("pswdo.warehouse_detail", office_id=log.office_id) if log.office_id else None)
    ),
    "disaster_event_declared": lambda log: url_for("pswdo.dashboard"),
    "disaster_event_ended": lambda log: url_for("pswdo.dashboard"),
    "direct_allocation": lambda log: url_for("pswdo.transfers"),
}


# Gets one notification ready for display: icon, color, category and where clicking it goes.
def _notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = NOTIFICATION_LINK_BUILDERS.get(log.action_type)
    return {
        "log": log,
        "icon": meta["icon"],
        "color": meta["color"],
        "category": meta["category"],
        "category_label": meta["category_label"],
        "link": link_fn(log) if link_fn else None,
    }


# The priority label and color for a barangay's disaster status (e.g. 'High Priority' = red).
def _priority_info(status_key):
    return PRIORITY_BY_STATUS.get(status_key, DEFAULT_PRIORITY)


GIS_LGU_FILES = {
    "Urdaneta City": "Municipality/bgysubmuns-municity-105546000.0.1.json",
    "Santa Barbara": "Municipality/bgysubmuns-municity-105538000.0.1.json",
    "Calasiao": "Municipality/bgysubmuns-municity-105517000.0.1.json",
}

PROVINCE_TOPOJSON_FILE = "Province/municities-provdist-105500000.topo.0.1.json"
TARGET_LGU_OUTLINES_FILE = "Province/target-lgu-outlines.json"

_geojson_cache = {}


_EMPTY_FEATURE_COLLECTION = {"type": "FeatureCollection", "features": []}


# Loads a map boundary file from app/static/geo.
# It is kept in memory until the file changes, so the map loads faster.
def _load_geojson_file(filename):
    path = os.path.join(current_app.root_path, "static", "geo", filename)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return _EMPTY_FEATURE_COLLECTION
    cached = _geojson_cache.get(filename)
    if cached is None or cached[0] != mtime:
        with open(path) as f:
            _geojson_cache[filename] = (mtime, json.load(f))
    return _geojson_cache[filename][1]


# Decodes the compressed province map file into real map coordinates.
def _decode_topojson_arcs(transform, arcs):
    if not transform:
        return arcs
    scale_x, scale_y = transform["scale"]
    translate_x, translate_y = transform["translate"]
    decoded = []
    for arc in arcs:
        x = y = 0
        coords = []
        for dx, dy in arc:
            x += dx
            y += dy
            coords.append([x * scale_x + translate_x, y * scale_y + translate_y])
        decoded.append(coords)
    return decoded


# Gets one line segment of a map boundary, in the right direction.
def _topojson_arc_coords(decoded_arcs, index):
    if index >= 0:
        return decoded_arcs[index]
    return list(reversed(decoded_arcs[~index]))


# Joins map line segments into one closed boundary.
def _topojson_ring(decoded_arcs, arc_indices):
    ring = []
    for i, idx in enumerate(arc_indices):
        coords = _topojson_arc_coords(decoded_arcs, idx)
        ring.extend(coords if i == 0 else coords[1:])
    return ring


# Converts one compressed map shape into the normal map format.
def _topojson_geometry_to_geojson(decoded_arcs, geometry):
    gtype = geometry["type"]
    if gtype == "Polygon":
        coords = [_topojson_ring(decoded_arcs, ring) for ring in geometry["arcs"]]
    elif gtype == "MultiPolygon":
        coords = [[_topojson_ring(decoded_arcs, ring) for ring in poly] for poly in geometry["arcs"]]
    else:
        return None
    return {"type": gtype, "coordinates": coords}


# Loads the compressed Pangasinan province map file (kept in memory until it changes).
def _load_topojson_file(filename):
    path = os.path.join(current_app.root_path, "static", "geo", filename)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return _EMPTY_FEATURE_COLLECTION
    cache_key = ("topo", filename)
    cached = _geojson_cache.get(cache_key)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    with open(path, encoding="utf-8") as f:
        topology = json.load(f)
    decoded_arcs = _decode_topojson_arcs(topology.get("transform"), topology["arcs"])
    object_name = next(iter(topology["objects"]))
    features = []
    for geom in topology["objects"][object_name]["geometries"]:
        geometry = _topojson_geometry_to_geojson(decoded_arcs, geom)
        if geometry is None:
            continue
        features.append({"type": "Feature", "properties": geom.get("properties", {}), "geometry": geometry})
    result = {"type": "FeatureCollection", "features": features}
    _geojson_cache[cache_key] = (mtime, result)
    return result


# Finds the middle of the box around a map shape.
def _bbox_center(geometry):
    lons, lats = [], []

    # Collects all the points of a map shape.
    def collect(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                collect(c)

    collect(geometry["coordinates"])
    return ((min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2)


# Computes the area and center point of a map boundary.
def _ring_signed_area_centroid(ring):
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5
    if area == 0:
        return 0.0, None, None
    return area, cx / (6 * area), cy / (6 * area)


# Finds the center point of a municipality or barangay on the map.
def _polygon_centroid(geometry):
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]

    total_area = 0.0
    weighted_lon = 0.0
    weighted_lat = 0.0
    for poly in polygons:
        area, cx, cy = _ring_signed_area_centroid(poly[0])
        area = abs(area)
        if area == 0:
            continue
        total_area += area
        weighted_lon += cx * area
        weighted_lat += cy * area

    if total_area == 0:
        return _bbox_center(geometry)
    return (weighted_lat / total_area, weighted_lon / total_area)


# Cleans a municipality name so names can be matched (removes 'City of' and ' City').
def _normalize_muni_name(name):
    name = name.strip()
    lowered = name.lower()
    if lowered.startswith("city of "):
        name = name[len("city of "):]
    elif lowered.endswith(" city"):
        name = name[: -len(" city")]
    return name.strip()


# Straight-line distance in kilometers between two places on the map.
def _haversine_km(point_a, point_b):
    lat1, lon1 = point_a
    lat2, lon2 = point_b
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


# The center point of a municipality on the map.
def _municipality_centroid(area_covered):
    province = _load_topojson_file(PROVINCE_TOPOJSON_FILE)
    target = _normalize_muni_name(area_covered).lower()
    for feature in province["features"]:
        if _normalize_muni_name(feature["properties"]["adm3_en"]).lower() == target:
            return _polygon_centroid(feature["geometry"])
    return None


WAREHOUSE_COORDS = {
    "Lingayen": (16.018148620092937, 120.22850482048867),
    "Province of Pangasinan": (16.018148620092937, 120.22850482048867),
    "Urdaneta City": (15.976373250682347, 120.56670137845737),
    "Santa Barbara": (15.998539153802154, 120.42154479771158),
    "Calasiao": (16.008967715946202, 120.35641917730929),
}


# The map location of a warehouse (its saved location, or its municipality's center).
def _warehouse_centroid(area_covered):
    coords = WAREHOUSE_COORDS.get(area_covered)
    if coords:
        return coords
    coords = weather_service.LGU_COORDS.get(area_covered)
    if coords:
        return coords
    return _municipality_centroid(area_covered)


# Builds the barangay shapes for the GIS map, each with its disaster status,
# report, affected families, stock and food pack numbers.
def _target_barangay_geojson(lgu, event_id):
    raw = _load_geojson_file(GIS_LGU_FILES[lgu])
    db_barangays = {b.barangay_name: b for b in Barangay.query.filter_by(city_municipality=lgu).all()}

    statuses = {}
    reports = {}
    if event_id:
        rows = BarangayDisasterStatus.query.join(Barangay).filter(
            BarangayDisasterStatus.event_id == event_id,
            Barangay.city_municipality == lgu
        ).all()
        statuses = {r.barangay_id: r for r in rows}

        report_rows = BarangayReport.query.join(Barangay).filter(
            BarangayReport.event_id == event_id,
            Barangay.city_municipality == lgu,
            BarangayReport.status != "draft",
        ).order_by(
            BarangayReport.submitted_at.desc(), BarangayReport.created_at.desc()
        ).all()
        for r in report_rows:
            reports.setdefault(r.barangay_id, r)

    features = []
    for feature in raw["features"]:
        name = feature["properties"]["adm4_en"]
        barangay = db_barangays.get(name)
        if barangay:
            status_row = statuses.get(barangay.barangay_id)
            status_key = status_row.status if status_row else "normal"
            report_row = reports.get(barangay.barangay_id)
            on_hand = food_pack_on_hand(barangay.barangay_id)
            stock_need = (report_row.requested_food_packs or 0) if report_row else 0
            adeq, ratio_pct = _stock_adequacy(stock_need, on_hand)
            props = {
                "name": name,
                "barangay_id": barangay.barangay_id,
                "has_data": True,
                "status": status_key,
                "priority_label": adeq["label"],
                "priority_tier": adeq["tier"],
                "stock_need": stock_need,
                "stock_ratio_pct": ratio_pct,
                "is_affected": report_row is not None,
                "affected_families": (report_row.affected_families or 0) if report_row else 0,
                "affected_individuals": (report_row.affected_individuals or 0) if report_row else 0,
                "population": barangay.population,
                "num_households": barangay.num_households,
                "barangay_on_hand": on_hand,
            }
            packs_needed, packs_source = _current_packs_needed(barangay, event_id)
            props["food_packs_current"] = packs_needed
            props["food_packs_source"] = packs_source
        else:
            props = {"name": name, "has_data": False, "status": None,
                     "priority_tier": "unrated", "priority_label": "Unrated",
                     "stock_need": 0, "stock_ratio_pct": None, "barangay_on_hand": None,
                     "is_affected": False, "affected_families": 0}
        features.append({"type": "Feature", "properties": props, "geometry": feature["geometry"]})

    return {"type": "FeatureCollection", "features": features}


# The center point of a barangay on the map.
def _target_barangay_centroid(lgu, barangay_name):
    raw = _load_geojson_file(GIS_LGU_FILES[lgu])
    for feature in raw["features"]:
        if feature["properties"]["adm4_en"] == barangay_name:
            return _polygon_centroid(feature["geometry"])
    return None


# Totals of food packs requested, approved and released for a group of barangays in one event,
# plus how many remain and the % done.
def _relief_summary(barangay_ids, event_id):
    empty = {"requested": 0, "approved": 0, "released": 0, "remaining": 0, "progress_pct": 0}
    if not barangay_ids:
        return empty

    alloc_query = AllocationRecord.query.filter(AllocationRecord.barangay_id.in_(barangay_ids))
    if event_id:
        alloc_query = alloc_query.filter(AllocationRecord.event_id == event_id)
    else:
        alloc_query = alloc_query.filter(AllocationRecord.event_id.is_(None))
    allocations = alloc_query.all()
    if not allocations:
        return empty

    requested = sum(a.predicted_quantity or 0 for a in allocations)
    approved = sum(a.allocated_quantity or 0 for a in allocations if a.status in ("approved", "released"))

    allocation_ids = [a.allocation_id for a in allocations]
    released = int(db.session.query(db.func.sum(DistributionRecord.quantity_released)).filter(
        DistributionRecord.allocation_id.in_(allocation_ids),
        DistributionRecord.dispatch_status == "delivered"
    ).scalar() or 0)

    remaining = max(requested - released, 0)
    progress_pct = int(round((released / requested) * 100)) if requested else 0

    return {
        "requested": requested, "approved": approved, "released": released,
        "remaining": remaining, "progress_pct": progress_pct,
    }


# How many food packs a barangay needs now:
# what it actually requested if there is a request, otherwise the forecast estimate.
def _current_packs_needed(barangay, event_id, relief=None):
    if relief is None:
        relief = _relief_summary([barangay.barangay_id], event_id)
    if relief["requested"] > 0:
        return relief["requested"], "request"
    return (ml_predict.predict_quantity(barangay) or 0), "model"


# Loads all active warehouses (PSWDO depots and the 3 municipal warehouses)
# with their food pack stock, % full and health status (Healthy, Moderate, Low).
def _load_warehouses():
    all_offices = Office.query.filter(
        Office.is_active.is_(True),
        db.or_(
            Office.office_type == "pswdo",
            db.and_(Office.office_type == "cswdo", Office.area_covered.in_(TARGET_LGUS))
        )
    ).all()

    warehouses = []
    total_food_packs = 0
    for office in all_offices:
        food_pack = WarehouseInventory.query.filter_by(
            office_id=office.office_id, item_type="food_pack"
        ).first()
        qty = food_pack.quantity_available if food_pack else 0
        capacity = office.capacity_food_pack or 20000
        pct = round((qty / capacity) * 100, 0) if capacity > 0 else 0
        health = _food_pack_health(qty, capacity)

        warehouses.append({
            "office": office, "food_pack_qty": qty, "capacity": capacity,
            "pct": pct, "health": health
        })
        total_food_packs += qty

    return all_offices, warehouses, total_food_packs


# Blocks changes unless the warehouse is a PSWDO warehouse
# (PSWDO can view municipal warehouses but not edit them).
def _require_pswdo_managed_office(office):
    if office.office_type != "pswdo":
        abort(403)


# Suggests moving stock from the fullest healthy warehouse to the lowest one.
def _stock_recommendations(warehouses):
    recommendations = []
    healthy_wh = [w for w in warehouses if w["health"] == "Healthy"]
    low_wh = [w for w in warehouses if w["health"] == "Low"]

    if low_wh and healthy_wh:
        source = max(healthy_wh, key=lambda w: w["food_pack_qty"])
        target = min(low_wh, key=lambda w: w["pct"])
        transfer_qty = min(2000, source["food_pack_qty"])
        recommendations.append({
            "type": "info",
            "title": f"Transfer {transfer_qty:,} packs → {target['office'].area_covered}",
            "detail": f"From {source['office'].office_name} · High Priority"
        })

    for w in warehouses:
        if w["pct"] < 15:
            recommendations.append({
                "type": "warning",
                "title": "Increase food pack procurement",
                "detail": f"{w['office'].office_name} stock: {w['pct']:.0f}% only"
            })

    for w in warehouses:
        if w["office"].office_type == "cswdo" and w["health"] == "Low":
            recommendations.append({
                "type": "critical",
                "title": f"Prioritize {w['office'].area_covered} next dispatch",
                "detail": "Critical stock level"
            })

    return recommendations


# Suggests restocking a municipal warehouse when the forecast says its stock
# will run out within the chosen number of months.
def _forecast_recommendations(warehouses, horizon_months=6, audience="pswdo"):
    recs = []
    for w in warehouses:
        office = w["office"]
        lgu = office.area_covered
        if office.office_type != "cswdo" or lgu not in TARGET_LGUS:
            continue
        f = ml_predict.forecast_lgu(lgu, horizon_months)
        if not f or not f["months"]:
            continue
        stock = int(w["food_pack_qty"])
        stockpile, expected = int(f["horizon_p90"]), int(f["horizon_total"])
        if stock >= stockpile:
            continue

        # The month when the stock is expected to run out.
        def runout(key):
            m = next((m for m in f["months"] if m[key] > stock), None)
            return f"{MONTH_NAMES[m['month'] - 1]} {m['year']}" if m else None

        shortfall = stockpile - stock
        action = (f"Request at least {shortfall:,} more packs" if audience == "cswdo"
                  else f"Transfer or procure about {shortfall:,} packs for {lgu}")
        run_e, run_p = runout("cum_expected"), runout("cum_p90")
        if run_e:
            rec_type, title = "critical", f"{lgu} stock may run out in {run_e}"
            summary = (f"{stock:,} packs on hand vs {expected:,} expected over the next {horizon_months} months "
                       f"(recommended stockpile {stockpile:,}).")
        else:
            rec_type, title = "warning", f"{lgu} stock is {shortfall:,} packs short of the recommended stockpile"
            summary = (f"{stock:,} packs on hand covers the expected {expected:,} packs over the next "
                       f"{horizon_months} months, but a bad season would run out{' in ' + run_p if run_p else ''}.")
        recs.append({"type": rec_type, "lgu": lgu, "title": title, "summary": summary,
                     "detail": f"{summary} {action} to reach {stockpile:,}."})
    recs.sort(key=lambda r: 0 if r["type"] == "critical" else 1)
    return recs


# Lists barangays expected to run short of food packs (forecast need minus stock on hand
# and packs already on the way), biggest shortage first.
def _barangay_shortages(lgu, horizon_months):
    f = ml_predict.forecast_lgu(lgu, horizon_months)
    shares = ml_predict.share_breakdown(lgu)
    if not f or not shares:
        return []
    on_hand = dict(BarangayInventory.query.with_entities(
        BarangayInventory.barangay_id, BarangayInventory.quantity_available
    ).filter(
        BarangayInventory.barangay_id.in_([r["barangay_id"] for r in shares]),
        BarangayInventory.item_type == "food_pack",
    ).all())
    incoming = dict(db.session.query(
        DistributionRecord.barangay_id, db.func.sum(DistributionRecord.quantity_released)
    ).filter(
        DistributionRecord.barangay_id.in_([r["barangay_id"] for r in shares]),
        DistributionRecord.status == "pending",
    ).group_by(DistributionRecord.barangay_id).all())
    rows = []
    for r in shares:
        expected = sum(max(int(round(m["projected_packs"] * r["share"])), 0) for m in f["months"])
        stockpile = max(int(round(f["horizon_p90"] * r["share"])), expected)
        stock = on_hand.get(r["barangay_id"])
        coming = int(incoming.get(r["barangay_id"]) or 0)
        have = (stock or 0) + coming
        if have < stockpile:
            rows.append({"barangay_id": r["barangay_id"], "name": r["name"], "on_hand": stock or 0,
                         "incoming": coming, "no_record": stock is None,
                         "expected": expected, "stockpile": stockpile,
                         "short": stockpile - have, "short_expected": have < expected})
    rows.sort(key=lambda x: x["short"], reverse=True)
    return rows


# Suggests which barangays to send food packs to ahead of time (pre-positioning),
# based on their expected shortage.
def _barangay_recommendations(warehouses, lgus, horizon_months=6, audience="pswdo", top=5):
    municipal = {w["office"].area_covered: int(w["food_pack_qty"])
                 for w in warehouses if w["office"].office_type == "cswdo"}
    recs = []
    for lgu in lgus:
        rows = _barangay_shortages(lgu, horizon_months)
        if not rows:
            continue
        # Text describing a barangay's stock (on hand, and on the way).
        def _stock_txt(r):
            base = "no stock on record" if r["no_record"] else f"{r['on_hand']:,} on hand"
            return base + (f", {r['incoming']:,} on the way" if r["incoming"] else "")
        listed = ", ".join(f"{r['name']} ({r['short']:,} short, {_stock_txt(r)})" for r in rows[:top])
        more = f" and {len(rows) - top} more" if len(rows) > top else ""
        total_short = sum(r["short"] for r in rows)
        stock = municipal.get(lgu)
        stock_note = f" {lgu}'s municipal warehouse has {stock:,} packs." if stock is not None else ""
        if audience != "cswdo":
            action = f"Follow up with {lgu} CSWDO/MSWDO on pre-positioning packs in these barangays."
        elif stock is not None and stock < total_short:
            action = (f"That covers only part of the gap - allocate the biggest gaps first and request "
                      f"about {total_short - stock:,} more packs from PSWDO.")
        else:
            action = "Allocate from the municipal warehouse, biggest gap first."
        recs.append({
            "type": "critical" if any(r["short_expected"] for r in rows) else "warning",
            "lgu": lgu, "barangays": rows, "total_short": total_short, "horizon_months": horizon_months,
            "title": f"{len(rows)} barangay{'s' if len(rows) != 1 else ''} in {lgu} need food packs",
            "detail": f"Most in need: {listed}{more}. Together they are {total_short:,} packs short of their "
                      f"{horizon_months}-month recommended stockpile.{stock_note} {action}",
        })
    recs.sort(key=lambda r: 0 if r["type"] == "critical" else 1)
    return recs


# Rough estimate of food packs used per day in a municipality during an active event
# (affected families divided by 3). Used for 'days of supply left'.
def _lgu_burn_rate(office, active_events):
    if office.area_covered not in TARGET_LGUS or not active_events:
        return None
    event_ids = [e.event_id for e in active_events]
    affected = db.session.query(db.func.sum(BarangayDisasterStatus.affected_families)).join(
        Barangay, Barangay.barangay_id == BarangayDisasterStatus.barangay_id
    ).filter(
        BarangayDisasterStatus.event_id.in_(event_ids),
        BarangayDisasterStatus.status != "normal",
        Barangay.city_municipality == office.area_covered
    ).scalar() or 0
    return (affected / 3) if affected > 0 else None


# Rates a stock item against its minimum level (reorder point):
# Healthy (at or above), Moderate (at least half), or Low.
def _item_status(qty, min_level):
    if min_level <= 0:
        return "Healthy" if qty > 0 else "Low"
    pct = qty / min_level
    if pct >= 1.0:
        return "Healthy"
    elif pct >= 0.5:
        return "Moderate"
    return "Low"


ITEM_TYPE_LABELS = {"food_pack": "Food Packs"}


# Applies the item type and stock status filters on the inventory list.
def _inventory_row_filters(rows, office_id):
    type_filter = request.args.get("item_type", "all")
    status_filter = request.args.get("stock_status", "all")
    item_types = sorted({
        t for (t,) in db.session.query(WarehouseInventory.item_type).filter_by(office_id=office_id).distinct() if t
    })
    if type_filter != "all":
        rows = [r for r in rows if r["item"].item_type == type_filter]
    if status_filter != "all":
        rows = [r for r in rows if r["status"] == status_filter]
    return rows, {
        "type_filter": type_filter, "stock_status_filter": status_filter,
        "item_type_options": [(t, ITEM_TYPE_LABELS.get(t, t.replace("_", " ").title())) for t in item_types],
    }


# Rates a warehouse's food packs by how full the warehouse is:
# Healthy, Moderate or Low (using the System Admin's levels).
def _food_pack_health(qty, capacity):
    cap = capacity or 20000
    pct = (qty / cap * 100) if cap > 0 else 0
    if pct >= _healthy_threshold() * 100:
        return "Healthy"
    if pct >= _moderate_threshold() * 100:
        return "Moderate"
    return "Low"


NEAR_EXPIRY_DAYS = 30


# Tells if a batch is fresh, near expiry (30 days or less left), or expired.
def _shelf_status(expiration_date):
    days_left = (expiration_date - ph_today()).days
    if days_left < 0:
        return "expired"
    if days_left <= NEAR_EXPIRY_DAYS:
        return "near_expiry"
    return "fresh"


# Keeps a warehouse's food pack batches matching its actual stock count,
# and moves batches that have expired out of usable stock into 'Expired' stock.
def _sync_food_pack_batches(office_id):
    fp = WarehouseInventory.query.filter_by(office_id=office_id, item_type="food_pack").first()
    on_hand = fp.quantity_available if fp else 0

    active_batches = _batch_take_order(FoodPackBatch.query.filter_by(office_id=office_id, status="active").all())

    batch_total = sum(b.quantity_remaining for b in active_batches)
    excess = batch_total - on_hand
    if excess > 0:
        for b in active_batches:
            if excess <= 0:
                break
            trim = min(b.quantity_remaining, excess)
            b.quantity_remaining -= trim
            excess -= trim
        active_batches = [b for b in active_batches if b.quantity_remaining > 0]
    elif excess < 0:
        active_batches.append(_create_food_pack_batch(office_id, -excess, ph_today()))

    today = ph_today()
    expired_batches = [b for b in active_batches if b.expiration_date < today and b.quantity_remaining > 0]
    if not expired_batches:
        db.session.commit()
        return

    expired_qty = sum(b.quantity_remaining for b in expired_batches)
    if fp:
        fp.quantity_available = max((fp.quantity_available or 0) - expired_qty, 0)

    expired_item = WarehouseInventory.query.filter_by(office_id=office_id, item_type="food_pack_expired").first()
    if expired_item is None:
        expired_item = WarehouseInventory(
            office_id=office_id, item_type="food_pack_expired",
            item_name="Food Packs (Expired)", unit="packs", quantity_available=0,
        )
        db.session.add(expired_item)
    expired_item.quantity_available = (expired_item.quantity_available or 0) + expired_qty

    db.session.add(WarehouseStockLog(
        office_id=office_id, item_type="food_pack", item_name="Food Packs",
        delta=-expired_qty, source_type="expired",
        reason=f"{expired_qty:,} food packs passed their expiration date",
    ))
    db.session.add(WarehouseStockLog(
        office_id=office_id, item_type="food_pack_expired", item_name="Food Packs (Expired)",
        delta=expired_qty, source_type="expired",
        reason=f"{expired_qty:,} food packs moved to Expired after passing their expiration date",
    ))

    for b in expired_batches:
        b.status = "expired"
        b.expired_at = ph_now()

    db.session.commit()


# Reads and checks an expiration date typed in a form (it can't be in the past).
def _parse_expiration_date(raw, label="This item"):
    from datetime import datetime
    try:
        d = datetime.strptime((raw or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, f"Enter a valid expiration date for {label}."
    if d < ph_today():
        return None, f"The expiration date for {label} can't be in the past."
    return d, None


# Reads an item's expiration date, only if the user said the item expires.
def _parse_item_expiration(form, label="this item"):
    if form.get("expires", "no") != "yes":
        return None, None
    return _parse_expiration_date(form.get("expiration_date"), label)


# Reads the food pack contents from the form (each item and its expiration date)
# and checks the dates are valid.
def _parse_food_pack_contents(form):
    from datetime import datetime
    today = ph_today()
    specs = []

    # Reads and checks one expiration date.
    def _date(raw, label):
        try:
            d = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None, f"Enter a valid expiration date for {label}."
        if d < today:
            return None, f"The expiration date for {label} can't be in the past."
        return d, None

    for c in FoodPackComponent.query.order_by(FoodPackComponent.sort_order).all():
        if not form.get(f"inc_{c.component_id}"):
            continue
        raw = (form.get(f"exp_{c.component_id}") or "").strip()
        d = None
        if raw:
            d, err = _date(raw, c.name)
            if err:
                return [], err
        qty = (form.get(f"qty_{c.component_id}") or "").strip()[:50] or None
        specs.append((c.component_id, None, d, qty if qty != c.quantity_label else None))

    names = form.getlist("other_name")
    dates = form.getlist("other_date")
    qtys = form.getlist("other_qty")
    for i, name in enumerate(names):
        name = name.strip()
        raw = (dates[i] if i < len(dates) else "").strip()
        qty = (qtys[i] if i < len(qtys) else "").strip()[:50] or None
        if not name and not raw:
            continue
        if not name:
            return [], "Enter a name for each 'Others' item that has a date."
        if len(name) > 100:
            return [], "'Others' item names can be at most 100 characters."
        d, err = _date(raw, name)
        if err:
            return [], err
        specs.append((None, name, d, qty))

    if not specs:
        return [], "Select at least one item that's in this batch."
    return specs, None


# Fills in any missing expiration dates using each item's normal shelf life
# (e.g. rice lasts about 180 days).
def _resolve_batch_item_specs(received_date, item_specs):
    from datetime import timedelta
    components = {c.component_id: c for c in FoodPackComponent.query.all()}
    if item_specs is None:
        item_specs = [(cid, None, None, None) for cid in components]
    rows = []
    for component_id, custom_name, d, *rest in item_specs:
        if d is None:
            c = components.get(component_id)
            d = received_date + timedelta(days=c.shelf_life_days if c else 180)
        rows.append((component_id, custom_name, d, rest[0] if rest else None))
    return rows


# Creates a new food pack batch in a warehouse with its items.
# The batch expires on the date of its earliest-expiring item.
def _create_food_pack_batch(office_id, quantity, received_date, updated_by=None, item_specs=None):
    from datetime import timedelta
    rows = _resolve_batch_item_specs(received_date, item_specs)
    batch = FoodPackBatch(
        office_id=office_id, quantity_remaining=quantity,
        received_date=received_date,
        expiration_date=min((d for _, _, d, _ in rows), default=received_date + timedelta(days=180)),
        updated_by=updated_by,
    )
    db.session.add(batch)
    db.session.flush()
    for component_id, custom_name, d, qty_label in rows:
        db.session.add(FoodPackBatchItem(
            batch_id=batch.batch_id, component_id=component_id,
            custom_name=custom_name, quantity_label=qty_label, expiration_date=d,
        ))
    return batch


# Sorts batches so the ones expiring soonest are used first.
def _batch_take_order(batches):
    today = ph_today()
    return sorted(batches, key=lambda b: (b.expiration_date < today, b.expiration_date, b.received_date, b.batch_id))


# Takes packs out of batches, soonest-to-expire first (first expire, first out),
# and records which batches were used so the details travel with the delivery.
def _take_from_batches(batches, quantity):
    lots = []
    remaining = quantity
    for b in _batch_take_order([b for b in batches if b.quantity_remaining > 0]):
        if remaining <= 0:
            break
        take = min(b.quantity_remaining, remaining)
        b.quantity_remaining -= take
        remaining -= take
        lots.append({
            "received": b.received_date.isoformat(), "qty": take,
            "items": [[i.component_id, i.custom_name, i.expiration_date.isoformat(), i.quantity_label] for i in b.items],
        })
    if remaining > 0:
        lots.append({"received": ph_today().isoformat(), "qty": remaining, "items": None})
    return lots


# Reads which batches the user picked by hand when sending out stock,
# and checks the numbers add up.
def _batch_picks_from_form(office_id, quantity):
    if request.form.get("batch_mode") != "manual":
        return None, None
    picks = {}
    for key, raw in request.form.items():
        if not key.startswith("batch_qty_"):
            continue
        try:
            batch_id, qty = int(key[len("batch_qty_"):]), int(raw or 0)
        except ValueError:
            return None, "Enter whole numbers for the packs taken from each batch."
        if qty < 0:
            return None, "Packs taken from a batch can't be negative."
        if qty:
            picks[batch_id] = qty
    if not picks:
        return None, "Choose at least one batch, or switch back to automatic (nearest expiry first)."
    batches = {b.batch_id: b for b in FoodPackBatch.query.filter(
        FoodPackBatch.batch_id.in_(picks), FoodPackBatch.office_id == office_id,
        FoodPackBatch.status == "active",
    ).all()}
    if set(batches) != set(picks):
        return None, "A selected batch isn't available in this warehouse any more - reload and choose again."
    for batch_id, qty in picks.items():
        b = batches[batch_id]
        if qty > b.quantity_remaining:
            return None, (f"The batch received {b.received_date.strftime('%b %d, %Y')} only has "
                          f"{b.quantity_remaining:,} packs left.")
    total = sum(picks.values())
    if total != quantity:
        return None, f"The packs chosen from batches ({total:,}) must add up to the quantity ({quantity:,})."
    return picks, None


# Removes the packs being sent out from the warehouse's batches
# (automatically, or from the batches the user picked).
def _deduct_food_pack_batches(office_id, quantity, picks=None):
    if not quantity or quantity <= 0:
        return None
    batches = FoodPackBatch.query.filter_by(office_id=office_id, status="active").filter(
        FoodPackBatch.quantity_remaining > 0
    ).all()
    if not picks:
        return json.dumps(_take_from_batches(batches, quantity))
    lots = []
    for b in batches:
        if b.batch_id in picks:
            lots += _take_from_batches([b], picks[b.batch_id])
    return json.dumps(lots)


# Lists the warehouse's batches that still have packs to send out.
def _pickable_food_pack_batches(office_id):
    return _batch_take_order(FoodPackBatch.query.filter_by(office_id=office_id, status="active").filter(
        FoodPackBatch.quantity_remaining > 0
    ).all())


# Reads the batch details that travelled with a delivery,
# so the receiving office gets batches with the same expiration dates.
def _lots_from_json(raw, limit, fallback_date=None):
    from datetime import date as _date
    out = []
    remaining = limit
    for lot in (json.loads(raw) if raw else []):
        if remaining <= 0:
            break
        qty = min(int(lot["qty"]), remaining)
        remaining -= qty
        items = lot.get("items")
        specs = [(cid, name, _date.fromisoformat(d), (rest[0] if rest else None)) for cid, name, d, *rest in items] if items else None
        out.append((_date.fromisoformat(lot["received"]), qty, specs))
    if remaining > 0:
        out.append((fallback_date or ph_today(), remaining, None))
    return out


# Repacking: replaces the expired items in a batch with fresh ones
# and works out the new expiration dates.
def _refreshed_batch_items(batch, refresh_date):
    from datetime import timedelta
    from types import SimpleNamespace
    plan = []
    replaced_components = []
    for item in batch.items:
        component = item.component
        if _shelf_status(item.expiration_date) == "expired":
            if component:
                plan.append((component.component_id, None, refresh_date + timedelta(days=component.shelf_life_days), item.quantity_label))
                replaced_components.append(component)
            else:
                replaced_components.append(SimpleNamespace(name=f"{item.custom_name} (removed)"))
        else:
            plan.append((item.component_id, item.custom_name, item.expiration_date, item.quantity_label))
    return plan, replaced_components


# A batch's expiration date = the date of its earliest-expiring item.
def _plan_expiration(plan):
    from datetime import timedelta
    return min((exp for _, _, exp, _ in plan), default=ph_today() + timedelta(days=180))


# Turns an item name into a simple code (e.g. 'Hygiene Kit' -> 'hygiene_kit').
def _slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "item"


# Reads where new stock came from (regular supply, donation, or DSWD)
# and the donor name, which is required for donations.
def _parse_stock_source(form, allowed=("standard", "donation", "dswd")):
    source_type = form.get("source_type", "standard").strip()
    if source_type not in allowed:
        source_type = "standard"

    donor_name = None
    if source_type == "donation":
        donor_name = form.get("donor_name", "").strip() or None
        if not donor_name:
            return None, None, "Enter the donor or agency name for a donation entry."

    return source_type, donor_name, None


# Builds the complete stock movement history for warehouses:
# restocks, donations, transfers, deliveries to barangays, expired and damaged stock.
def _full_stock_movements(office_ids, type_filter="all", date_str=""):
    movements = []
    filter_date = None
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            filter_date = None

    if type_filter in ("all", "released"):
        release_q = DistributionRecord.query.join(AllocationRecord).filter(
            AllocationRecord.fulfilling_office_id.in_(office_ids)
        )
        if filter_date:
            release_q = release_q.filter(DistributionRecord.distribution_date == filter_date)
        for d in release_q.order_by(DistributionRecord.distribution_date.desc()).all():
            office = d.allocation.fulfilling_office
            movements.append({
                "office_id": office.office_id if office else None,
                "office_name": office.office_name if office else "Unknown",
                "direction": "Released",
                "qty": -d.quantity_released,
                "context": d.barangay.city_municipality if d.barangay else "",
                "when": d.distribution_date,
                "sort_at": d.submitted_at or datetime.combine(d.distribution_date, datetime.min.time()),
                "is_donation": False,
            })

    if type_filter in ("all", "transferred_out", "transferred_in"):
        transfer_q = WarehouseTransfer.query.filter(
            WarehouseTransfer.status == "completed",
            db.or_(
                WarehouseTransfer.from_office_id.in_(office_ids),
                WarehouseTransfer.to_office_id.in_(office_ids)
            )
        )
        if filter_date:
            transfer_q = transfer_q.filter(db.func.date(WarehouseTransfer.completed_at) == filter_date)
        for t in transfer_q.order_by(WarehouseTransfer.completed_at.desc()).all():
            completed_date = t.completed_at.date() if t.completed_at else None
            if type_filter in ("all", "transferred_out") and t.from_office_id in office_ids:
                movements.append({
                    "office_id": t.from_office_id,
                    "office_name": t.from_office.office_name,
                    "direction": "Transferred Out",
                    "qty": -t.quantity,
                    "context": f"To {t.to_office.office_name}",
                    "when": completed_date,
                    "sort_at": t.completed_at or datetime.min,
                    "is_donation": False,
                })
            if type_filter in ("all", "transferred_in") and t.to_office_id in office_ids:
                movements.append({
                    "office_id": t.to_office_id,
                    "office_name": t.to_office.office_name,
                    "direction": "Transferred In",
                    "qty": t.quantity,
                    "context": f"From {t.from_office.office_name}",
                    "when": completed_date,
                    "sort_at": t.completed_at or datetime.min,
                    "is_donation": False,
                })

    if type_filter in ("all", "received", "returned_damaged"):
        log_q = WarehouseStockLog.query.filter(
            WarehouseStockLog.office_id.in_(office_ids),
            WarehouseStockLog.delta > 0
        )
        if type_filter == "received":
            log_q = log_q.filter(WarehouseStockLog.source_type.notin_(("returned_damaged", "expired")))
        elif type_filter == "returned_damaged":
            log_q = log_q.filter(WarehouseStockLog.source_type == "returned_damaged")
        if filter_date:
            log_q = log_q.filter(db.func.date(WarehouseStockLog.created_at) == filter_date)
        for log in log_q.order_by(WarehouseStockLog.created_at.desc(), WarehouseStockLog.log_id.desc()).all():
            base_context = log.reason or f"{log.item_name} stock update"
            if log.is_donation:
                context = f"Donated by {log.donor_name}" + (f" - {log.reason}" if log.reason else "")
            else:
                context = base_context
            direction = (stock_log_label(log.item_type, log.delta, log.source_type, log.reason)
                         or (f"Received - {log.source_label}" if log.source_label else "Received"))
            movements.append({
                "office_id": log.office_id,
                "office_name": log.office.office_name,
                "direction": direction,
                "qty": log.delta,
                "context": context,
                "when": log.created_at.date(),
                "sort_at": log.created_at,
                "is_donation": log.is_donation,
            })

    if type_filter == "all":
        removed_q = WarehouseStockLog.query.filter(
            WarehouseStockLog.office_id.in_(office_ids),
            WarehouseStockLog.item_type == "food_pack",
            WarehouseStockLog.source_type == "expired",
            WarehouseStockLog.delta < 0,
        )
        if filter_date:
            removed_q = removed_q.filter(db.func.date(WarehouseStockLog.created_at) == filter_date)
        for log in removed_q.all():
            movements.append({
                "office_id": log.office_id,
                "office_name": log.office.office_name,
                "direction": stock_log_label(log.item_type, log.delta, log.source_type, log.reason),
                "qty": log.delta,
                "context": f"{-log.delta:,} food packs removed from usable stock after passing their expiration date",
                "when": log.created_at.date(),
                "sort_at": log.created_at,
                "is_donation": False,
            })

    if type_filter in ("all", "damaged_resolved"):
        resolved_q = WarehouseStockLog.query.filter(
            WarehouseStockLog.office_id.in_(office_ids),
            WarehouseStockLog.item_type.in_(("food_pack_damaged", "food_pack_expired")),
            WarehouseStockLog.delta < 0,
        )
        if filter_date:
            resolved_q = resolved_q.filter(db.func.date(WarehouseStockLog.created_at) == filter_date)
        for log in resolved_q.order_by(WarehouseStockLog.created_at.desc(), WarehouseStockLog.log_id.desc()).all():
            direction = stock_log_label(log.item_type, log.delta, log.source_type, log.reason)
            movements.append({
                "office_id": log.office_id,
                "office_name": log.office.office_name,
                "direction": direction,
                "qty": log.delta,
                "context": log.reason or f"{log.item_name} stock update",
                "when": log.created_at.date(),
                "sort_at": log.created_at,
                "is_donation": False,
            })

    movements.sort(key=lambda m: m["sort_at"], reverse=True)
    return movements


# The latest few stock movements, for the dashboard and warehouse pages.
def _recent_stock_movements(office_ids, limit=6):
    return _full_stock_movements(office_ids)[:limit]


# Reads the dashboard's month/year filter (or none = current status).
def _resolve_dashboard_period():
    period = request.args.get("period")
    if period not in ("monthly", "yearly"):
        return None, None, None

    year = request.args.get("year", type=int) or ph_today().year

    if period == "yearly":
        return period, date(year, 1, 1), date(year, 12, 31)

    month = request.args.get("month", type=int)
    if not month or not (1 <= month <= 12):
        month = ph_today().month
    last_day = calendar.monthrange(year, month)[1]
    return period, date(year, month, 1), date(year, month, last_day)


# The years shown in the dashboard's year filter (from the first event until now).
def _dashboard_period_years():
    earliest = db.session.query(db.func.min(DisasterEvent.start_date)).scalar()
    start_year = earliest.year if earliest else ph_today().year
    return list(range(ph_today().year, start_year - 1, -1))


# Page: /pswdo/dashboard - PSWDO main dashboard: active disaster events, stock in every warehouse, pending stock requests,
# deliveries, recent stock movements and weather. Can be filtered by month or year.
@pswdo_bp.route("/dashboard")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard():
    now = ph_now()

    period, period_start, period_end = _resolve_dashboard_period()
    is_filtered = period is not None
    selected_month = period_start.month if is_filtered else None
    selected_year = period_start.year if is_filtered else None

    if is_filtered:
        active_events = DisasterEvent.query.filter(
            DisasterEvent.scope == "province",
            DisasterEvent.start_date <= period_end,
            db.or_(DisasterEvent.end_date.is_(None), DisasterEvent.end_date >= period_start)
        ).order_by(DisasterEvent.start_date.desc()).all()
    else:
        active_events = DisasterEvent.query.filter_by(status="active", scope="province").order_by(
            DisasterEvent.start_date.desc()
        ).all()
    primary_event = active_events[0] if active_events else None

    all_offices, warehouses, total_food_packs = _load_warehouses()
    warehouses.sort(key=lambda w: w["pct"], reverse=True)

    pending_q = ReliefRequestBatch.query.filter(
        ReliefRequestBatch.submitted_at.isnot(None),
        ReliefRequestBatch.status == "pending",
    )
    if is_filtered:
        pending_q = pending_q.filter(
            ReliefRequestBatch.submitted_at >= period_start,
            ReliefRequestBatch.submitted_at <= period_end,
        )
    pending_requests = pending_q.order_by(ReliefRequestBatch.submitted_at.desc()).limit(6).all()
    pending_requests_count = pending_q.count()

    total_affected_families = 0
    affected_municipalities = set()
    if active_events:
        event_ids = [e.event_id for e in active_events]
        event_reports = BarangayReport.query.join(
            Barangay, Barangay.barangay_id == BarangayReport.barangay_id
        ).filter(
            BarangayReport.event_id.in_(event_ids),
            BarangayReport.status.notin_(("draft", "declined")),
            Barangay.city_municipality.in_(TARGET_LGUS),
        ).all()
        total_affected_families = sum((r.affected_families or 0) for r in event_reports)
        affected_municipalities = {r.barangay.city_municipality for r in event_reports}

    projected_demand = stockpile_12mo = 0
    for lgu in TARGET_LGUS:
        forecast = ml_predict.forecast_lgu(lgu, 12)
        if forecast:
            projected_demand += forecast["months"][0]["projected_packs"] if forecast["months"] else 0
            stockpile_12mo += forecast["horizon_p90"]

    low_stock_warehouses = sorted(
        w["office"].office_name for w in warehouses if w["health"] == "Low"
    )

    recommendations = (_forecast_recommendations(warehouses)
                       + _barangay_recommendations(warehouses, TARGET_LGUS)
                       + _stock_recommendations(warehouses))

    known_types = PSWDO_NOTIFICATION_TYPES
    recent_activities = ActivityLog.query.filter(ActivityLog.action_type.in_(known_types)).order_by(
        ActivityLog.created_at.desc()
    ).limit(4).all()

    return render_template(
        "pswdo/dashboard.html",
        active_events=active_events,
        primary_event=primary_event,
        period=period,
        is_filtered=is_filtered,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_month_name=MONTH_NAMES[selected_month - 1] if selected_month else None,
        month_names=MONTH_NAMES,
        available_years=_dashboard_period_years(),
        map_event_id=primary_event.event_id if (is_filtered and primary_event) else None,
        warehouses=warehouses,
        total_food_packs=total_food_packs,
        pending_requests=pending_requests,
        pending_requests_count=pending_requests_count,
        total_affected_families=total_affected_families,
        affected_municipalities_count=len(affected_municipalities),
        total_target_lgus=len(TARGET_LGUS),
        low_stock_warehouses=low_stock_warehouses,
        projected_demand=projected_demand,
        stockpile_12mo=stockpile_12mo,
        recommendations=recommendations,
        recent_activities=recent_activities,
        weather_cities=TARGET_LGUS,
        now=now
    )


# Page: /pswdo/dashboard/weather - Sends the weather and typhoon data that the dashboard weather widget shows.
@pswdo_bp.route("/dashboard/weather")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard_weather():
    requested = request.args.get("cities")
    if requested:
        cities = [c.strip() for c in requested.split(",") if c.strip() in weather_service.LGU_COORDS]
        if cities:
            return weather_service.get_dashboard_snapshot(cities)
    return weather_service.get_dashboard_snapshot(TARGET_LGUS)


# Action: /pswdo/disaster-events/declare - Declares a new province-wide disaster event (e.g. a typhoon).
# Only one province-wide event can be active at a time.
@pswdo_bp.route("/disaster-events/declare", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def declare_disaster_event():
    existing = blocking_event_for_province()
    if existing:
        flash(f"“{existing.event_name}” is already active. End it before declaring a new event.", "error")
        return redirect(url_for("pswdo.dashboard"))

    event_name = request.form.get("event_name", "").strip()
    if not event_name:
        flash("Event name is required to declare a disaster event.", "error")
        return redirect(url_for("pswdo.dashboard"))

    event_type = "typhoon"

    start_date_raw = request.form.get("start_date", "")
    try:
        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date() if start_date_raw else ph_today()
    except ValueError:
        start_date = ph_today()

    weather_condition = event_categories_from_form(request.form)

    event = DisasterEvent(
        event_name=event_name, event_type=event_type, status="active",
        weather_condition=weather_condition, start_date=start_date,
        created_by=current_user.user_id, scope="province",
    )
    db.session.add(event)
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="disaster_event_declared",
        description=f"Declared {event_name} as the active disaster event.",
    ))
    db.session.commit()

    flash(f"{event_name} has been declared as the active disaster event.", "success")
    return redirect(url_for("pswdo.dashboard"))


# Action: /pswdo/disaster-events/<int:event_id>/end - Ends an active disaster event and records the end date.
@pswdo_bp.route("/disaster-events/<int:event_id>/end", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def end_disaster_event(event_id):
    event = DisasterEvent.query.get_or_404(event_id)
    if event.status != "active":
        flash(f"{event.event_name} is not currently active.", "error")
        return redirect(url_for("pswdo.dashboard"))

    event.status = "ended"
    event.end_date = ph_today()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="disaster_event_ended",
        description=f"Marked {event.event_name} as ended.",
    ))
    db.session.commit()

    flash(f"{event.event_name} has been marked as ended.", "success")
    return redirect(url_for("pswdo.dashboard"))


# Page: /pswdo/warehouse-inventory - Warehouse Inventory overview: every warehouse with its food packs, % full,
# health and estimated days of supply left.
@pswdo_bp.route("/warehouse-inventory")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory():
    active_events = DisasterEvent.query.filter_by(status="active", scope="province").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]
    warehouses.sort(key=lambda w: w["pct"], reverse=True)

    for w in warehouses:
        burn = _lgu_burn_rate(w["office"], active_events)
        w["days_remaining"] = round(w["food_pack_qty"] / burn, 0) if burn else None

    low_stock_count = len([w for w in warehouses if w["health"] == "Low"])
    recommendations = _stock_recommendations(warehouses)

    today = ph_today()
    transfers_today_count = WarehouseTransfer.query.filter(
        WarehouseTransfer.status == "completed",
        db.func.date(WarehouseTransfer.completed_at) == today
    ).count()

    recent_movements = _recent_stock_movements(office_ids, limit=6)

    warehouse_map_points = []
    for w in warehouses:
        centroid = _warehouse_centroid(w["office"].area_covered)
        if not centroid:
            continue
        warehouse_map_points.append({
            "name": w["office"].office_name,
            "area_covered": w["office"].area_covered,
            "lat": centroid[0], "lng": centroid[1],
            "health": w["health"], "pct": w["pct"],
            "food_pack_qty": w["food_pack_qty"], "capacity": w["capacity"],
            "office_id": w["office"].office_id,
        })

    return render_template(
        "pswdo/warehouse_inventory.html",
        warehouses=warehouses,
        total_food_packs=total_food_packs,
        low_stock_count=low_stock_count,
        recommendations=recommendations,
        transfers_today_count=transfers_today_count,
        recent_movements=recent_movements,
        default_office_id=warehouses[0]["office"].office_id if warehouses else None,
        warehouse_map_points=warehouse_map_points,
    )


# Action: /pswdo/warehouse-inventory/create - Adds a new PSWDO warehouse (name, location and capacity).
@pswdo_bp.route("/warehouse-inventory/create", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_create():
    office_name = request.form.get("office_name", "").strip()
    area_covered = request.form.get("area_covered", "").strip()
    capacity_food_pack = request.form.get("capacity_food_pack", type=int) or 20000

    if not office_name or not area_covered:
        flash("Enter a warehouse name and location.", "error")
        return redirect(url_for("pswdo.warehouse_inventory"))

    if Office.query.filter_by(office_name=office_name).first():
        flash(f"A warehouse named '{office_name}' already exists.", "error")
        return redirect(url_for("pswdo.warehouse_inventory"))

    office = Office(
        office_name=office_name, office_type="pswdo", area_covered=area_covered,
        capacity_food_pack=capacity_food_pack,
        full_address=request.form.get("full_address", "").strip() or None,
        manager_name=request.form.get("manager_name", "").strip() or None,
        contact_number=request.form.get("contact_number", "").strip() or None,
        email=request.form.get("email", "").strip() or None,
    )
    db.session.add(office)
    db.session.flush()

    db.session.add(WarehouseInventory(
        office_id=office.office_id, item_type="food_pack", item_name="Food Packs",
        unit="packs", quantity_available=0, min_stock_level=0,
        updated_by=current_user.user_id,
    ))
    db.session.commit()

    flash(f"{office_name} added.", "success")
    return redirect(url_for("pswdo.warehouse_detail", office_id=office.office_id))


# Page: /pswdo/warehouse-inventory/warehouses - List of all warehouses.
@pswdo_bp.route("/warehouse-inventory/warehouses")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_list():
    all_offices, warehouses, total_food_packs = _load_warehouses()
    return render_template(
        "pswdo/warehouse_list.html",
        warehouses=warehouses,
        total_food_packs=total_food_packs,
    )


# Page: /pswdo/warehouse-inventory/<int:office_id> - One warehouse's details: stock, capacity, food pack batches with expiration dates,
# and recent stock movements.
@pswdo_bp.route("/warehouse-inventory/<int:office_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_detail(office_id):
    office = Office.query.get_or_404(office_id)
    _sync_food_pack_batches(office_id)
    active_events = DisasterEvent.query.filter_by(status="active", scope="province").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    food_pack_item = WarehouseInventory.query.filter_by(office_id=office_id, item_type="food_pack").first()
    food_pack_qty = food_pack_item.quantity_available if food_pack_item else 0
    capacity = office.capacity_food_pack or 20000
    pct = round((food_pack_qty / capacity) * 100, 0) if capacity > 0 else 0
    health = _food_pack_health(food_pack_qty, capacity)

    burn = _lgu_burn_rate(office, active_events)
    days_remaining = round(food_pack_qty / burn, 0) if burn else None

    items = WarehouseInventory.query.filter_by(office_id=office_id).order_by(
        WarehouseInventory.item_name
    ).all()
    inventory_summary = [
        {"item": item, "status": _item_status(item.quantity_available, item.min_stock_level)}
        for item in items
    ]

    movements = _recent_stock_movements([office_id], limit=6)

    return render_template(
        "pswdo/warehouse_detail.html",
        office=office, food_pack_qty=food_pack_qty, capacity=capacity, pct=pct, health=health,
        burn=burn, days_remaining=days_remaining, inventory_summary=inventory_summary,
        movements=movements,
    )


# Action: /pswdo/warehouse-inventory/<int:office_id>/edit - Saves a PSWDO warehouse's details (address, manager, contact, capacity).
@pswdo_bp.route("/warehouse-inventory/<int:office_id>/edit", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_edit(office_id):
    office = Office.query.get_or_404(office_id)
    _require_pswdo_managed_office(office)
    office.full_address = request.form.get("full_address", "").strip() or None
    office.manager_name = request.form.get("manager_name", "").strip() or None
    office.contact_number = request.form.get("contact_number", "").strip() or None
    office.email = request.form.get("email", "").strip() or None

    capacity = request.form.get("capacity_food_pack", type=int)
    if capacity and capacity > 0:
        office.capacity_food_pack = capacity

    db.session.commit()
    flash("Warehouse information updated.", "success")
    return redirect(url_for("pswdo.warehouse_detail", office_id=office_id))


# Page: /pswdo/warehouse-inventory/<int:office_id>/inventory - Inventory Management page for one warehouse: every stock item with its quantity,
# minimum level and status (Healthy, Moderate, Low).
@pswdo_bp.route("/warehouse-inventory/<int:office_id>/inventory")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_items(office_id):
    office = Office.query.get_or_404(office_id)
    _sync_food_pack_batches(office_id)
    search_query = request.args.get("q", "").strip()

    items_q = WarehouseInventory.query.filter_by(office_id=office_id)
    if search_query:
        items_q = items_q.filter(WarehouseInventory.item_name.ilike(f"%{search_query}%"))
    items = items_q.order_by(WarehouseInventory.item_name).all()

    rows = [
        {"item": item, "status": _item_status(item.quantity_available, item.min_stock_level)}
        for item in items
    ]
    rows, item_filters = _inventory_row_filters(rows, office_id)

    batches = FoodPackBatch.query.filter(
        FoodPackBatch.office_id == office_id, FoodPackBatch.quantity_remaining > 0
    ).order_by(FoodPackBatch.expiration_date).all()
    batch_rows = [{"batch": b, "shelf_status": _shelf_status(b.expiration_date)} for b in batches]

    return render_template(
        "pswdo/warehouse_items.html",
        office=office, rows=rows, search_query=search_query, **item_filters,
        batch_rows=batch_rows, near_expiry_days=NEAR_EXPIRY_DAYS, shelf_status_fn=_shelf_status,
        food_pack_components=FoodPackComponent.query.order_by(FoodPackComponent.sort_order).all(),
    )


# Action: /pswdo/warehouse-inventory/<int:office_id>/inventory/add - Adds a new stock item to a PSWDO warehouse, with its source (supply/donation/DSWD)
# and, for food packs, the contents and expiration dates.
@pswdo_bp.route("/warehouse-inventory/<int:office_id>/inventory/add", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_add(office_id):
    office = Office.query.get_or_404(office_id)
    _require_pswdo_managed_office(office)
    item_name = request.form.get("item_name", "").strip()
    unit = "packs"
    quantity = request.form.get("quantity", type=int)
    min_stock_level = request.form.get("min_stock_level", type=int) or 0

    if not item_name or quantity is None or quantity < 0:
        flash("Enter a valid item name and quantity.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    source_type, donor_name, source_error = _parse_stock_source(request.form)
    if source_error:
        flash(source_error, "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    expiration_date, expiry_error = _parse_item_expiration(request.form, item_name)
    if expiry_error:
        flash(expiry_error, "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    item_type = _slugify(item_name)
    if WarehouseInventory.query.filter_by(office_id=office_id, item_type=item_type).first():
        flash(f"{item_name} already exists for this warehouse - use Update instead.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    item = WarehouseInventory(
        office_id=office_id, item_type=item_type, item_name=item_name, unit=unit,
        quantity_available=quantity, min_stock_level=min_stock_level,
        expiration_date=expiration_date, updated_by=current_user.user_id,
    )
    db.session.add(item)

    if quantity > 0:
        db.session.add(WarehouseStockLog(
            office_id=office_id, item_type=item_type, item_name=item_name,
            delta=quantity, reason="Initial stock", source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))

    db.session.commit()
    flash(f"Added {item_name} to {office.office_name}.", "success")
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))


# Action: /pswdo/warehouse-inventory/inventory/<int:inventory_id>/update - Adds or removes stock for an item, with a reason and source.
# The change is saved in the stock history; stock can't go below zero.
@pswdo_bp.route("/warehouse-inventory/inventory/<int:inventory_id>/update", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_update(inventory_id):
    item = WarehouseInventory.query.get_or_404(inventory_id)
    _require_pswdo_managed_office(item.office)
    delta = request.form.get("delta", type=int)
    unit = request.form.get("unit", "").strip()
    reason = request.form.get("reason", "").strip() or None
    min_stock_level = request.form.get("min_stock_level", type=int)

    if delta is None:
        flash("Enter a quantity to add or remove.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))
    new_quantity = item.quantity_available + delta
    if new_quantity < 0:
        flash(
            f"That would take {item.item_name} below zero - current stock is "
            f"{item.quantity_available:,}.", "error"
        )
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))
    if min_stock_level is not None and min_stock_level < 0:
        flash("Min stock level can't be negative.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))

    source_type, donor_name = "standard", None
    if delta > 0:
        source_type, donor_name, source_error = _parse_stock_source(request.form)
        if source_error:
            flash(source_error, "error")
            return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))
    elif request.form.get("source_type", "").strip() == "donation":
        flash("A donation adds stock - enter a positive quantity to record it.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))

    expiry_specs = None
    new_expiration = None
    if item.item_type == "food_pack" and delta > 0:
        expiry_specs, expiry_error = _parse_food_pack_contents(request.form)
        if expiry_error:
            flash(expiry_error, "error")
            return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))
    elif item.expiration_date and delta > 0 and request.form.get("expiration_date", "").strip():
        new_expiration, expiry_error = _parse_expiration_date(request.form.get("expiration_date"), item.item_name)
        if expiry_error:
            flash(expiry_error, "error")
            return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))

    # Save the new stock quantity.
    item.quantity_available = new_quantity
    if unit:
        item.unit = unit
    if min_stock_level is not None:
        item.min_stock_level = min_stock_level
    if new_expiration:
        item.expiration_date = new_expiration
    item.updated_by = current_user.user_id

    if item.item_type == "food_pack" and delta > 0:
        _create_food_pack_batch(item.office_id, delta, ph_today(), current_user.user_id, expiry_specs)

    if delta != 0:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type=item.item_type, item_name=item.item_name,
            delta=delta, reason=reason, source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))

    db.session.commit()
    flash(f"Updated {item.item_name} stock.", "success")
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))


# Action: /pswdo/warehouse-inventory/expired-batch/<int:batch_id>/resolve - Handles an expired food pack batch:
# either dispose of the packs, or repack them with fresh items and put them back in stock.
@pswdo_bp.route("/warehouse-inventory/expired-batch/<int:batch_id>/resolve", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_resolve_expired_batch(batch_id):
    batch = FoodPackBatch.query.get_or_404(batch_id)
    _require_pswdo_managed_office(batch.office)
    if batch.status != "expired":
        abort(403)
    office_id = batch.office_id

    quantity = request.form.get("quantity", type=int)
    resolution = request.form.get("resolution", "")
    if not quantity or quantity <= 0:
        flash("Enter how many expired packs this covers.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))
    if quantity > batch.quantity_remaining:
        flash(f"Only {batch.quantity_remaining:,} expired packs are on record for that batch.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))
    if resolution not in ("disposed", "fixed"):
        flash("Select Disposed or Fixed.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    expired_item = WarehouseInventory.query.filter_by(
        office_id=office_id, item_type="food_pack_expired"
    ).first()
    if expired_item is None or expired_item.quantity_available < quantity:
        flash("Expired stock record is out of sync - reload and try again.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    plan, replaced_components = _refreshed_batch_items(batch, ph_today())

    batch.quantity_remaining -= quantity
    expired_item.quantity_available -= quantity
    expired_item.updated_by = current_user.user_id

    if resolution == "disposed":
        db.session.add(WarehouseStockLog(
            office_id=office_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs disposed / written off",
            updated_by=current_user.user_id,
        ))
        flash(f"{quantity:,} expired packs marked disposed.", "success")
    else:
        replaced_names = ", ".join(c.name for c in replaced_components)
        db.session.add(WarehouseStockLog(
            office_id=office_id, item_type="food_pack_expired", item_name=expired_item.item_name,
            delta=-quantity, source_type="expired",
            reason=f"{quantity:,} expired packs resolved - {replaced_names} replaced with fresh stock",
            updated_by=current_user.user_id,
        ))
        fp = WarehouseInventory.query.filter_by(office_id=office_id, item_type="food_pack").first()
        if fp is None:
            fp = WarehouseInventory(
                office_id=office_id, item_type="food_pack",
                item_name="Food Packs", unit="packs", quantity_available=0,
            )
            db.session.add(fp)
        fp.quantity_available = (fp.quantity_available or 0) + quantity
        fp.updated_by = current_user.user_id
        db.session.add(WarehouseStockLog(
            office_id=office_id, item_type="food_pack", item_name="Food Packs",
            delta=quantity, source_type="expired",
            reason=f"{quantity:,} packs returned to usable stock after replacing {replaced_names}",
            updated_by=current_user.user_id,
        ))

        new_batch = FoodPackBatch(
            office_id=office_id, quantity_remaining=quantity,
            received_date=ph_today(),
            expiration_date=_plan_expiration(plan),
            status="active", updated_by=current_user.user_id,
        )
        db.session.add(new_batch)
        db.session.flush()
        for component_id, custom_name, exp, qty_label in plan:
            db.session.add(FoodPackBatchItem(
                batch_id=new_batch.batch_id, component_id=component_id,
                custom_name=custom_name, quantity_label=qty_label, expiration_date=exp,
            ))

        flash(f"{quantity:,} expired packs marked fixed - {replaced_names} replaced, "
              f"returned to Food Packs stock.", "success")

    db.session.commit()
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))


# Action: /pswdo/warehouse-inventory/inventory/<int:inventory_id>/delete - Removes a stock item from a warehouse.
# Food Packs can't be removed because forecasts and allocations depend on them.
@pswdo_bp.route("/warehouse-inventory/inventory/<int:inventory_id>/delete", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_delete(inventory_id):
    item = WarehouseInventory.query.get_or_404(inventory_id)
    _require_pswdo_managed_office(item.office)
    office_id = item.office_id

    if item.item_type == "food_pack":
        flash("Food Packs can't be removed - it's required for allocation and prediction.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    db.session.delete(item)
    db.session.commit()
    flash(f"{item.item_name} removed.", "success")
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))


# Download: /pswdo/warehouse-inventory/<int:office_id>/inventory/export - Downloads one warehouse's inventory as a CSV (spreadsheet) file.
@pswdo_bp.route("/warehouse-inventory/<int:office_id>/inventory/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_export(office_id):
    office = Office.query.get_or_404(office_id)
    items = WarehouseInventory.query.filter_by(office_id=office_id).order_by(
        WarehouseInventory.item_name
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Item", "Current Qty", "Unit", "Min Level", "Stock vs Min", "Status"])
    for item in items:
        pct = round((item.quantity_available / item.min_stock_level) * 100) if item.min_stock_level > 0 else None
        writer.writerow([
            item.item_name, item.quantity_available, item.unit, item.min_stock_level,
            f"{pct}%" if pct is not None else "-",
            _item_status(item.quantity_available, item.min_stock_level),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={office.office_name.replace(' ', '_')}_inventory.csv"},
    )


# Page: /pswdo/warehouse-inventory/transfer - Stock Transfer page: moves food packs from one PSWDO warehouse to another.
# Both warehouses' stock and history are updated.
@pswdo_bp.route("/warehouse-inventory/transfer", methods=["GET", "POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_transfer_page():
    _, all_warehouses, _ = _load_warehouses()
    warehouses = [w for w in all_warehouses if w["office"].office_type == "pswdo"]

    if request.method == "POST":
        from_office_id = request.form.get("from_office_id", type=int)
        to_office_id = request.form.get("to_office_id", type=int)
        quantity = request.form.get("quantity", type=int)
        reason = request.form.get("reason", "").strip() or None

        if not from_office_id or not to_office_id or from_office_id == to_office_id or not quantity or quantity <= 0:
            flash("Select two different warehouses and a valid quantity.", "error")
            return redirect(url_for("pswdo.warehouse_stock_transfer_page"))

        from_office = Office.query.get(from_office_id)
        to_office = Office.query.get(to_office_id)
        if not from_office or not to_office \
                or from_office.office_type != "pswdo" or to_office.office_type != "pswdo":
            flash("Warehouse-to-warehouse transfers are for PSWDO depots only - use Relief Requests "
                  "or Direct Allocation to send stock to a CSWDO warehouse.", "error")
            return redirect(url_for("pswdo.warehouse_stock_transfer_page"))

        source_inventory = WarehouseInventory.query.filter_by(
            office_id=from_office_id, item_type="food_pack"
        ).first()
        if not source_inventory or source_inventory.quantity_available < quantity:
            flash("Source warehouse does not have enough food pack stock for this transfer.", "error")
            return redirect(url_for("pswdo.warehouse_stock_transfer_page"))
        picks, err = _batch_picks_from_form(from_office_id, quantity)
        if err:
            flash(err, "error")
            return redirect(url_for("pswdo.warehouse_stock_transfer_page"))

        dest_inventory = WarehouseInventory.query.filter_by(
            office_id=to_office_id, item_type="food_pack"
        ).first()
        if not dest_inventory:
            dest_inventory = WarehouseInventory(
                office_id=to_office_id, item_type="food_pack",
                item_name="Food Packs", unit="packs", quantity_available=0,
            )
            db.session.add(dest_inventory)

        # Move the packs: out of the sending warehouse...
        source_inventory.quantity_available -= quantity
        # ...and into the receiving warehouse.
        dest_inventory.quantity_available += quantity
        for received_date, qty, specs in _lots_from_json(
                _deduct_food_pack_batches(from_office_id, quantity, picks), quantity, ph_today()):
            _create_food_pack_batch(to_office_id, qty, received_date, current_user.user_id, specs)

        db.session.add(WarehouseTransfer(
            from_office_id=from_office_id, to_office_id=to_office_id,
            item_type="food_pack", quantity=quantity,
            status="completed", requested_by=current_user.user_id,
            completed_at=ph_now(),
        ))
        db.session.add(ActivityLog(
            actor_id=current_user.user_id, action_type="warehouse_transfer_completed",
            description=(
                f"Transferred {quantity:,} food packs from {from_office.office_name} to {to_office.office_name}"
                + (f" - {reason}" if reason else "")
            ),
            office_id=to_office_id,
        ))
        db.session.commit()

        return redirect(url_for(
            "pswdo.warehouse_stock_transfer_page",
            success=1, qty=quantity, from_name=from_office.office_name, to_name=to_office.office_name,
        ))

    recommendations = _stock_recommendations(warehouses)
    success_ctx = None
    if request.args.get("success"):
        success_ctx = {
            "qty": request.args.get("qty", type=int),
            "from_name": request.args.get("from_name"),
            "to_name": request.args.get("to_name"),
        }

    return render_template(
        "pswdo/warehouse_transfer.html",
        warehouses=warehouses,
        recommendations=recommendations,
        success=success_ctx,
        default_office_id=warehouses[0]["office"].office_id if warehouses else None,
    )


# Applies the warehouse, movement type, date and search filters to the stock history.
def _movement_filters(office_ids):
    office_filter = request.args.get("office_id", type=int)
    if office_filter not in office_ids:
        office_filter = None
    type_filter = request.args.get("type", "all")
    date_from, date_to = date_range(request.args)
    legacy = arg_date(request.args, "date")
    if legacy and not (date_from or date_to):
        date_from = date_to = legacy
    search_query = request.args.get("q", "").strip()
    scoped_ids = [office_filter] if office_filter else office_ids
    movements = [m for m in _full_stock_movements(scoped_ids, type_filter, "")
                 if in_range(m["when"], date_from, date_to)]
    if search_query:
        needle = search_query.lower()
        movements = [m for m in movements if needle in " ".join(
            str(m.get(k) or "") for k in ("office_name", "direction", "context")).lower()]
    return movements, {
        "office_filter": office_filter, "type_filter": type_filter, "search_query": search_query,
        "date_from": iso(date_from), "date_to": iso(date_to),
    }


# Page: /pswdo/warehouse-inventory/movements - Stock Movement History page: every stock movement across all warehouses, with filters.
@pswdo_bp.route("/warehouse-inventory/movements")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_movements():
    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]

    movements, filters = _movement_filters(office_ids)

    return render_template(
        "pswdo/warehouse_movements.html",
        warehouses=warehouses,
        movements=movements,
        **filters,
        default_office_id=warehouses[0]["office"].office_id if warehouses else None,
    )


# Download: /pswdo/warehouse-inventory/movements/export - Downloads the stock movement history as a CSV (spreadsheet) file.
@pswdo_bp.route("/warehouse-inventory/movements/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_movements_export():
    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]

    movements, _ = _movement_filters(office_ids)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Warehouse", "Activity", "Context", "Quantity"])
    for m in movements:
        writer.writerow([
            m["when"].isoformat() if m["when"] else "",
            m["office_name"], m["direction"], m["context"], m["qty"],
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_movements.csv"},
    )


# Page: /pswdo/warehouse-inventory/reports - Warehouse Reports page: summary numbers (approved, released, delivered)
# and the list of PDF/Excel reports that can be generated.
@pswdo_bp.route("/warehouse-inventory/reports")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_reports():
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES, PSWDO_REPORT_TYPES, resolve_filters

    filters = resolve_filters(request.args)
    active_events = DisasterEvent.query.filter_by(is_reference=False).order_by(DisasterEvent.start_date.desc()).all()

    barangay_ids = [b.barangay_id for b in Barangay.query.filter(
        Barangay.city_municipality.in_(filters["lgus"])
    ).all()]

    approved_q = AllocationRecord.query.filter(
        AllocationRecord.status.in_(("approved", "released")),
        AllocationRecord.allocation_date >= filters["start_date"],
        AllocationRecord.barangay_id.in_(barangay_ids),
    )
    delivered_q = DistributionRecord.query.filter(
        DistributionRecord.dispatch_status == "delivered",
        DistributionRecord.distribution_date >= filters["start_date"],
        DistributionRecord.barangay_id.in_(barangay_ids),
    )
    if filters["event_id"]:
        approved_q = approved_q.filter(AllocationRecord.event_id == filters["event_id"])
        delivered_q = delivered_q.join(AllocationRecord).filter(AllocationRecord.event_id == filters["event_id"])

    reports_generated = ReportLog.query.filter(
        ReportLog.report_type.in_(PSWDO_REPORT_TYPES),
        ReportLog.generated_at >= filters["start_date"],
    ).count()
    approved_requests = approved_q.count()
    packs_distributed = sum(d.quantity_released for d in delivered_q.all())
    completed_deliveries = delivered_q.count()

    query_params = {"event_id": filters["event_id"] or "", "municipality": filters["municipality"], "days": filters["days"]}
    report_cards = [
        {"slug": slug, **REPORT_TYPES[slug], "generate_url": url_for("reports.view", report_type=slug, **query_params)}
        for slug in PSWDO_REPORT_TYPES
    ]

    recent_logs = ReportLog.query.filter(
        ReportLog.report_type.in_(PSWDO_REPORT_TYPES)
    ).order_by(ReportLog.generated_at.desc()).limit(10).all()
    recent_reports = []
    for log in recent_logs:
        stored = json.loads(log.filters_json) if log.filters_json else {}
        recent_reports.append({
            "log": log,
            "title": REPORT_TYPES.get(log.report_type, {}).get("title", log.report_type),
            "view_url": url_for("reports.view", report_type=log.report_type, **stored),
            "download_url": url_for("reports.download", report_id=log.report_id),
        })

    coverage_range = "All Time" if filters["days"] == "all" else (
        f"{filters['start_date'].strftime('%b %d')} - {ph_today().strftime('%b %d, %Y')}"
    )

    return render_template(
        "pswdo/warehouse_reports.html",
        active_events=active_events,
        target_lgus=TARGET_LGUS,
        filters=filters,
        coverage_range=coverage_range,
        reports_generated=reports_generated,
        approved_requests=approved_requests,
        packs_distributed=packs_distributed,
        completed_deliveries=completed_deliveries,
        report_cards=report_cards,
        recent_reports=recent_reports,
        download_all_url=url_for("reports.download_all"),
    )


# Which municipalities the user may see on the map
# (CSWDO/MSWDO: only their own; PSWDO: all 3).
def _gis_scope_lgus():
    if current_user.role == "cswdo_admin":
        office = current_user.office
        if office and office.area_covered in TARGET_LGUS:
            return [office.area_covered]
        return []
    return list(TARGET_LGUS)


# Settings passed to the GIS map page (user role, links to other pages, default municipality).
def _gis_config():
    is_pswdo = current_user.role in ("pswdo_admin", "system_admin")
    scope = _gis_scope_lgus()
    return {
        "role": current_user.role,
        "barangayReportsUrl": None if is_pswdo else url_for("cswdo.damage_assessment"),
        "barangayDistributionsUrl": None if is_pswdo else url_for("cswdo.barangay_distribution_history"),
        "deliveriesUrl": None if is_pswdo else url_for("cswdo.deliveries"),
        "defaultLgu": scope[0] if len(scope) == 1 else None,
    }


# Names of the other Pangasinan municipalities, shown in grey on the map for context.
def _other_municipality_names():
    if current_user.role == "cswdo_admin":
        return []
    targets = {_normalize_muni_name(l).lower() for l in TARGET_LGUS}
    names = {
        f["properties"]["adm3_en"]
        for f in _load_topojson_file(PROVINCE_TOPOJSON_FILE)["features"]
        if _normalize_muni_name(f["properties"]["adm3_en"]).lower() not in targets
    }
    return sorted(names)


# Page: /pswdo/gis-map - GIS Map page: an interactive map of the barangays with their disaster status,
# stock adequacy, warehouses and delivery routes.
@pswdo_bp.route("/gis-map")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map():
    scope_lgus = _gis_scope_lgus()
    active_events = relevant_active_events_query(scope_lgus).all()
    return render_template(
        "pswdo/gis_map.html",
        active_events=active_events,
        target_lgus=scope_lgus,
        other_municipalities=_other_municipality_names(),
        gis_config=_gis_config(),
    )


# Page: /pswdo/gis-map/data - Sends all the GIS map data at once: municipality and barangay shapes with their status,
# warehouses, delivery routes and summary numbers.
@pswdo_bp.route("/gis-map/data")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_data():
    explicit_event_id = request.args.get("event_id", type=int)
    scope_lgus = _gis_scope_lgus()
    full_scope = set(scope_lgus) == set(TARGET_LGUS)

    lgu_event_ids = {lgu: _resolve_event_id(explicit_event_id, lgu) for lgu in scope_lgus}

    target_features = []
    for lgu in scope_lgus:
        event_id = lgu_event_ids[lgu]
        fc = _target_barangay_geojson(lgu, event_id)
        for feature in fc["features"]:
            feature["properties"]["lgu"] = lgu
            target_features.append(feature)
    target_barangays_geojson = {"type": "FeatureCollection", "features": target_features}

    province_geojson = _load_topojson_file(PROVINCE_TOPOJSON_FILE)
    target_by_normalized = {_normalize_muni_name(l).lower(): l for l in TARGET_LGUS}
    target_outlines = {
        f["properties"]["lgu"]: f["geometry"]
        for f in _load_geojson_file(TARGET_LGU_OUTLINES_FILE)["features"]
    }
    province_features = []
    for feature in province_geojson["features"]:
        name = feature["properties"]["adm3_en"]
        matched_lgu = target_by_normalized.get(_normalize_muni_name(name).lower())
        in_scope = matched_lgu is not None and matched_lgu in scope_lgus
        province_features.append({
            "type": "Feature",
            "properties": {"name": name, "is_target": in_scope, "lgu": matched_lgu if in_scope else None},
            "geometry": target_outlines.get(matched_lgu) or feature["geometry"],
        })
    province_context_geojson = {"type": "FeatureCollection", "features": province_features}

    all_offices, warehouses, total_food_packs = _load_warehouses()
    warehouse_markers = []
    for w in warehouses:
        if not full_scope and w["office"].area_covered not in scope_lgus:
            continue
        centroid = _warehouse_centroid(w["office"].area_covered)
        if not centroid:
            continue
        marker = {
            "name": w["office"].office_name,
            "area_covered": w["office"].area_covered,
            "lat": centroid[0], "lng": centroid[1],
            "health": w["health"], "pct": w["pct"],
            "food_pack_qty": w["food_pack_qty"], "capacity": w["capacity"],
        }
        if full_scope:
            other_items = WarehouseInventory.query.filter(
                WarehouseInventory.office_id == w["office"].office_id,
                WarehouseInventory.item_type != "food_pack",
            ).all()
            marker["other_relief_items"] = [{
                "name": i.item_name, "qty": i.quantity_available, "unit": i.unit,
            } for i in other_items]
        warehouse_markers.append(marker)
    if not full_scope:
        total_food_packs = sum(w["food_pack_qty"] for w in warehouse_markers)

    in_transit_lines = []
    in_transit_records = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(scope_lgus),
        DistributionRecord.dispatch_status == "in_transit"
    ).all()
    for d in in_transit_records:
        allocation = d.allocation
        office = allocation.fulfilling_office if allocation else None
        if not office:
            continue
        from_point = _warehouse_centroid(office.area_covered)
        to_point = _target_barangay_centroid(d.barangay.city_municipality, d.barangay.barangay_name)
        if from_point and to_point:
            in_transit_lines.append({
                "from": from_point, "to": to_point,
                "barangay": d.barangay.barangay_name,
            })

    barangay_props = [f["properties"] for f in target_features if f["properties"]["has_data"]]
    affected = [p for p in barangay_props if p["is_affected"]]
    total_affected_families = sum(p["affected_families"] for p in affected)
    priority_barangays = sorted(
        affected,
        key=lambda p: (_STOCK_TIER.get(p["priority_tier"], _STOCK_TIER["unrated"])["rank"],
                       p["stock_need"]),
        reverse=True,
    )[:5]

    active_routes_query = DistributionRecord.query.join(Barangay).join(
        AllocationRecord, DistributionRecord.allocation_id == AllocationRecord.allocation_id
    ).filter(
        Barangay.city_municipality.in_(scope_lgus),
        DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"])
    )
    is_pswdo_view = current_user.role in ("pswdo_admin", "system_admin")
    if is_pswdo_view:
        active_routes_query = active_routes_query.join(
            Office, AllocationRecord.fulfilling_office_id == Office.office_id
        ).filter(Office.office_type == "pswdo")
    active_routes = active_routes_query.order_by(DistributionRecord.distribution_date.desc()).limit(10).all()

    routes_table = []
    for d in active_routes:
        allocation = d.allocation
        office = allocation.fulfilling_office if allocation else None
        from_point = _warehouse_centroid(office.area_covered) if office else None
        if is_pswdo_view:
            to_point = _warehouse_centroid(d.barangay.city_municipality)
            to_label = d.barangay.city_municipality
        else:
            to_point = _target_barangay_centroid(d.barangay.city_municipality, d.barangay.barangay_name)
            to_label = f"{d.barangay.barangay_name} / {d.barangay.city_municipality}"
        routes_table.append({
            "distribution_id": d.distribution_id,
            "from_office": office.office_name if office else "-",
            "from_lat": from_point[0] if from_point else None,
            "from_lng": from_point[1] if from_point else None,
            "to_barangay": d.barangay.barangay_name,
            "to_barangay_id": d.barangay.barangay_id,
            "to_municipality": d.barangay.city_municipality,
            "to_label": to_label,
            "to_lat": to_point[0] if to_point else None,
            "to_lng": to_point[1] if to_point else None,
            "packs": d.quantity_released,
            "status": d.dispatch_status,
            "status_label": DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
            "eta": d.expected_arrival_time.strftime("%I:%M %p") if d.expected_arrival_time else "-",
        })

    municipalities = []
    for lgu in scope_lgus:
        lgu_props = [f["properties"] for f in target_features if f["properties"]["lgu"] == lgu and f["properties"]["has_data"]]
        lgu_affected = [p for p in lgu_props if p["is_affected"]]
        barangay_ids = [p["barangay_id"] for p in lgu_props]
        worst_rank = max((_STOCK_TIER.get(p["priority_tier"], _STOCK_TIER["unrated"])["rank"] for p in lgu_props), default=0)
        worst_tier = next((v for v in _STOCK_TIER.values() if v["rank"] == worst_rank), _STOCK_TIER["unrated"])

        current_route = DistributionRecord.query.join(Barangay).filter(
            Barangay.city_municipality == lgu,
            DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"])
        ).order_by(DistributionRecord.distribution_date.desc()).first()
        current_distribution = None
        if current_route:
            current_distribution = {
                "distribution_id": current_route.distribution_id,
                "eta": current_route.expected_arrival_time.strftime("%I:%M %p") if current_route.expected_arrival_time else "-",
                "status": current_route.dispatch_status,
                "status_label": DISPATCH_STATUS_LABELS.get(current_route.dispatch_status, current_route.dispatch_status),
            }

        fulfilling_office = None
        if current_route and current_route.allocation:
            fulfilling_office = current_route.allocation.fulfilling_office
        if not fulfilling_office:
            last_alloc = AllocationRecord.query.join(Barangay).filter(
                Barangay.city_municipality == lgu,
                AllocationRecord.fulfilling_office_id.isnot(None)
            ).order_by(AllocationRecord.allocation_date.desc()).first()
            if last_alloc:
                fulfilling_office = last_alloc.fulfilling_office

        warehouse_info = None
        muni_centroid = _municipality_centroid(lgu)
        if fulfilling_office:
            wh_match = next((w for w in warehouse_markers if w["name"] == fulfilling_office.office_name), None)
            distance_km = round(_haversine_km(muni_centroid, (wh_match["lat"], wh_match["lng"])), 1) if (wh_match and muni_centroid) else None
            warehouse_info = {
                "name": fulfilling_office.office_name,
                "distance_km": distance_km,
                "food_pack_qty": wh_match["food_pack_qty"] if wh_match else None,
                "capacity": wh_match["capacity"] if wh_match else fulfilling_office.capacity_food_pack,
            }
        elif muni_centroid and warehouse_markers:
            closest = min(warehouse_markers, key=lambda w: _haversine_km(muni_centroid, (w["lat"], w["lng"])))
            warehouse_info = {
                "name": closest["name"],
                "distance_km": round(_haversine_km(muni_centroid, (closest["lat"], closest["lng"])), 1),
                "food_pack_qty": closest["food_pack_qty"],
                "capacity": closest["capacity"],
            }

        relief = _relief_summary(barangay_ids, lgu_event_ids[lgu])
        predicted_demand = sum(p["food_packs_current"] for p in lgu_props)
        shortage = max(predicted_demand - relief["approved"], 0)

        municipalities.append({
            "lgu": lgu,
            "total_barangays": len(lgu_props),
            "affected_barangays": len(lgu_affected),
            "total_affected_families": sum(p["affected_families"] for p in lgu_affected),
            "total_population": sum(p["population"] for p in lgu_props),
            "status_label": worst_tier["label"],
            "status_tier": worst_tier["tier"],
            "relief": relief,
            "predicted_demand": predicted_demand,
            "shortage": shortage,
            "allocation_status": "Fulfilled" if shortage == 0 and relief["requested"] > 0 else "For Allocation",
            "warehouse": warehouse_info,
            "current_distribution": current_distribution,
        })

    if len(scope_lgus) == 1:
        event_id = lgu_event_ids[scope_lgus[0]]
    else:
        province_event = blocking_event_for_province()
        event_id = province_event.event_id if province_event else None
    event = DisasterEvent.query.get(event_id) if event_id else None

    return {
        "event_id": event_id,
        "event": {
            "event_name": event.event_name,
            "event_type": event.event_type,
            "status": event.status,
            "weather_condition": event.weather_condition,
        } if event else None,
        "target_barangays": target_barangays_geojson,
        "province_context": province_context_geojson,
        "warehouses": warehouse_markers,
        "in_transit_lines": in_transit_lines,
        "stats": {
            "affected_barangays": len(affected),
            "total_barangays": len(barangay_props),
            "total_affected_families": total_affected_families,
            "total_food_packs": total_food_packs,
        },
        "priority_barangays": priority_barangays,
        "routes_table": routes_table,
        "municipalities": municipalities,
    }


# Picks which disaster event the map shows: the one the user chose,
# otherwise the active event.
def _resolve_event_id(event_id, lgu=None):
    if event_id:
        return event_id
    if lgu:
        event, _ = resolve_effective_event(lgu)
    else:
        event = blocking_event_for_province()
    return event.event_id if event else None


# Page: /pswdo/gis-map/barangay/<int:barangay_id> - Sends one barangay's full details when it is clicked on the map
# (status, report, stock, food packs requested/approved/released).
@pswdo_bp.route("/gis-map/barangay/<int:barangay_id>")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_barangay_detail(barangay_id):
    barangay = Barangay.query.get_or_404(barangay_id)
    if barangay.city_municipality not in _gis_scope_lgus():
        abort(404)

    event_id = _resolve_event_id(request.args.get("event_id", type=int), barangay.city_municipality)

    status_row = None
    report_row = None
    if event_id:
        status_row = BarangayDisasterStatus.query.filter_by(
            barangay_id=barangay_id, event_id=event_id
        ).first()
        report_row = BarangayReport.query.filter(
            BarangayReport.barangay_id == barangay_id,
            BarangayReport.event_id == event_id,
            BarangayReport.status != "draft",
        ).order_by(
            BarangayReport.submitted_at.desc(), BarangayReport.created_at.desc()
        ).first()
    status_key = status_row.status if status_row else "normal"
    on_hand = food_pack_on_hand(barangay_id)
    stock_need = (report_row.requested_food_packs or 0) if report_row else 0
    adeq, ratio_pct = _stock_adequacy(stock_need, on_hand)

    relief = _relief_summary([barangay_id], event_id)

    allocation_ids = [a.allocation_id for a in AllocationRecord.query.filter_by(barangay_id=barangay_id).all()]
    history = []
    if allocation_ids:
        history = DistributionRecord.query.filter(
            DistributionRecord.allocation_id.in_(allocation_ids)
        ).order_by(DistributionRecord.distribution_date.desc()).limit(10).all()

    distribution_history = [{
        "distribution_id": d.distribution_id,
        "date": d.distribution_date.strftime("%b %d, %Y"),
        "packs": d.quantity_released,
        "status": d.dispatch_status,
        "status_label": DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
    } for d in history]

    return {
        "barangay_id": barangay.barangay_id,
        "name": barangay.barangay_name,
        "lgu": barangay.city_municipality,
        "population": barangay.population,
        "num_households": barangay.num_households,
        "status": status_key,
        "priority_label": adeq["label"],
        "priority_tier": adeq["tier"],
        "stock_need": stock_need,
        "stock_ratio_pct": ratio_pct,
        "is_affected": report_row is not None,
        "affected_families": (report_row.affected_families or 0) if report_row else 0,
        "affected_individuals": (report_row.affected_individuals or 0) if report_row else 0,
        "barangay_on_hand": on_hand,
        "relief": relief,
        "distribution_history": distribution_history,
    }


# Download: /pswdo/gis-map/municipality/<lgu>/report.csv - Downloads a CSV report of every barangay in a municipality
# (status, need, stock, affected families, food packs).
@pswdo_bp.route("/gis-map/municipality/<lgu>/report.csv")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_municipality_report(lgu):
    if lgu not in _gis_scope_lgus():
        abort(404)

    event_id = _resolve_event_id(request.args.get("event_id", type=int), lgu)
    fc = _target_barangay_geojson(lgu, event_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Barangay", "Stock Adequacy", "Need (families)", "Barangay Stock",
        "Need/Stock %", "Affected Families", "Population", "Households",
        "Food Packs Requested", "Food Packs Approved", "Food Packs Released",
    ])
    for feature in fc["features"]:
        p = feature["properties"]
        if not p["has_data"]:
            writer.writerow([p["name"], "No stock on record"] + [""] * 9)
            continue
        relief = _relief_summary([p["barangay_id"]], event_id)
        writer.writerow([
            p["name"], p["priority_label"], p["stock_need"],
            "" if p["barangay_on_hand"] is None else p["barangay_on_hand"],
            "" if p["stock_ratio_pct"] is None else p["stock_ratio_pct"],
            p["affected_families"], p["population"],
            p["num_households"],
            relief["requested"], relief["approved"], relief["released"],
        ])

    filename = lgu.lower().replace(" ", "_")
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=gis_report_{filename}.csv"},
    )


RR_STATUS_LABELS = {
    "draft": "Draft", "pending": "Under Review", "approved": "Approved",
    "partially_approved": "Partially Approved", "declined": "Declined", "fulfilled": "Fulfilled",
}


# Reads the stock request filters (status, municipality, search, priority, event, dates).
def _stock_request_filters(args):
    # Reads one date from the filter.
    def as_date(key):
        try:
            return datetime.strptime(args.get(key, ""), "%Y-%m-%d").date()
        except ValueError:
            return None
    return {
        "status": args.get("status", "all"),
        "municipality": args.get("municipality", "all"),
        "q": args.get("q", "").strip(),
        "priority": args.get("priority", "all"),
        "event_id": args.get("event_id", type=int),
        "date_from": as_date("date_from"),
        "date_to": as_date("date_to"),
    }


# Lists the submitted stock requests that match the filters, newest first.
def _stock_request_rows(status_filter="all", municipality_filter="all", search="",
                        priority="all", event_id=None, date_from=None, date_to=None):
    q = ReliefRequestBatch.query.filter(ReliefRequestBatch.submitted_at.isnot(None))
    batches = q.order_by(ReliefRequestBatch.submitted_at.desc()).all()
    rows = []
    for b in batches:
        lgu = b.office.area_covered if b.office else ""
        if municipality_filter != "all" and lgu != municipality_filter:
            continue
        if status_filter == "approved":
            if b.display_status not in ("approved", "partially_approved"):
                continue
        elif status_filter != "all" and b.display_status != status_filter:
            continue
        if priority != "all" and b.priority != priority:
            continue
        if event_id and b.event_id != event_id:
            continue
        submitted = b.submitted_at.date()
        if (date_from and submitted < date_from) or (date_to and submitted > date_to):
            continue
        if search and search.lower() not in b.ref.lower() and search.lower() not in lgu.lower():
            continue
        rows.append(b)
    return rows


# Page: /pswdo/relief-requests - Stock Requests page: requests for food packs sent by the CSWDO/MSWDO offices.
# PSWDO reviews them here (pending, approved, fulfilled, declined), 12 per page.
@pswdo_bp.route("/relief-requests")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_requests():
    f = _stock_request_filters(request.args)
    status_filter, municipality_filter, search_query = f["status"], f["municipality"], f["q"]
    rows = _stock_request_rows(status_filter, municipality_filter, search_query,
                               f["priority"], f["event_id"], f["date_from"], f["date_to"])

    all_submitted = ReliefRequestBatch.query.filter(ReliefRequestBatch.submitted_at.isnot(None)).all()
    counts = {
        "pending": sum(1 for b in all_submitted if b.display_status == "pending"),
        "approved": sum(1 for b in all_submitted if b.display_status in ("approved", "partially_approved")),
        "fulfilled": sum(1 for b in all_submitted if b.display_status == "fulfilled"),
        "declined": sum(1 for b in all_submitted if b.display_status == "declined"),
    }
    per_page = 12
    total_filtered = len(rows)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = min(max(request.args.get("page", 1, type=int), 1), total_pages)
    page_rows = rows[(page - 1) * per_page: page * per_page]

    _, warehouses, _ = _load_warehouses()
    depots = [w for w in warehouses if w["office"].office_type == "pswdo" and w["food_pack_qty"] > 0]
    cswdo_offices = sorted(
        (w for w in warehouses if w["office"].office_type == "cswdo"),
        key=lambda w: w["office"].area_covered,
    )

    return render_template(
        "pswdo/relief_requests.html",
        rows=page_rows, counts=counts, total_count=len(all_submitted), total_filtered=total_filtered,
        cswdo_offices=cswdo_offices,
        status_filter=status_filter, municipality_filter=municipality_filter, search_query=search_query,
        priority_filter=f["priority"], event_filter=f["event_id"],
        date_from=f["date_from"].isoformat() if f["date_from"] else "",
        date_to=f["date_to"].isoformat() if f["date_to"] else "",
        events=DisasterEvent.query.order_by(DisasterEvent.start_date.desc()).all(),
        target_lgus=TARGET_LGUS, status_labels=RR_STATUS_LABELS, priority_labels={"high": "High", "medium": "Medium", "low": "Low"},
        depots=depots, page=page, total_pages=total_pages, per_page=per_page,
    )


# Download: /pswdo/relief-requests/export - Downloads the stock requests list as a CSV (spreadsheet) file.
@pswdo_bp.route("/relief-requests/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_relief_requests():
    f = _stock_request_filters(request.args)
    rows = _stock_request_rows(f["status"], f["municipality"], f["q"],
                               f["priority"], f["event_id"], f["date_from"], f["date_to"])
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Request ID", "Municipality", "Event", "Requested", "Approved", "Status", "Submitted"])
    for b in rows:
        writer.writerow([
            b.ref, b.office.area_covered if b.office else "", b.event.event_name if b.event else "",
            b.requested_food_packs, b.approved_food_packs,
            RR_STATUS_LABELS.get(b.display_status, b.display_status),
            b.submitted_at.strftime("%Y-%m-%d") if b.submitted_at else "",
        ])
    return Response(buffer.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=stock_requests.csv"})


# Finds an allocation, but only if it belongs to one of the 3 target municipalities.
def _get_target_scoped_request(allocation_id):
    req = AllocationRecord.query.get_or_404(allocation_id)
    if req.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return req


# Page: /pswdo/relief-requests/<int:batch_id> - One stock request's full details: what was asked, why, attachments,
# the municipality's current stock, and which PSWDO depots can supply it.
@pswdo_bp.route("/relief-requests/<int:batch_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_request_detail(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    if not batch.office or batch.office.office_type != "cswdo":
        abort(404)

    fp = WarehouseInventory.query.filter_by(office_id=batch.office_id, item_type="food_pack").first()
    cswdo_on_hand = fp.quantity_available if fp else 0
    _, warehouses, _ = _load_warehouses()
    depots = [w for w in warehouses if w["office"].office_type == "pswdo" and w["food_pack_qty"] > 0]
    transfer = batch.transfer

    return render_template(
        "pswdo/relief_request_detail.html",
        batch=batch, cswdo_on_hand=cswdo_on_hand,
        depots=depots, transfer=transfer,
        status_labels=RR_STATUS_LABELS, priority_labels={"high": "High", "medium": "Medium", "low": "Low"},
        dispatch_labels={"preparing": "Preparing", "in_transit": "In Transit", "delivered": "Delivered"},
    )


# Action: /pswdo/relief-requests/<int:batch_id>/approve - Approves a stock request: takes the packs out of the chosen provincial depot
# and creates a transfer to the municipal warehouse (the municipality confirms receipt later).
@pswdo_bp.route("/relief-requests/<int:batch_id>/approve", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def approve_relief_request(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    if batch.display_status != "pending":
        flash("This stock request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))

    depot_id = request.form.get("fulfilling_office_id", type=int)
    quantity = request.form.get("quantity", type=int)
    remarks = request.form.get("remarks", "").strip() or None
    depot = Office.query.get(depot_id) if depot_id else None
    if not depot or depot.office_type != "pswdo":
        flash("Select a provincial depot to transfer from.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))
    if not quantity or quantity <= 0 or quantity > batch.requested_food_packs:
        flash(f"Quantity must be between 1 and {batch.requested_food_packs:,}.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))

    src = WarehouseInventory.query.filter_by(office_id=depot.office_id, item_type="food_pack").first()
    available = src.quantity_available if src else 0
    if quantity > available:
        flash(f"{depot.office_name} only has {available:,} food packs available.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))
    picks, err = _batch_picks_from_form(depot.office_id, quantity)
    if err:
        flash(err, "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))

    # Take the approved packs out of the provincial depot's stock.
    src.quantity_available -= quantity
    src.updated_by = current_user.user_id
    transfer = WarehouseTransfer(
        from_office_id=depot.office_id, to_office_id=batch.office_id,
        item_type="food_pack", quantity=quantity, batch_id=batch.batch_id,
        status="pending", dispatch_status="preparing",
        requested_by=current_user.user_id,
        batch_lots=_deduct_food_pack_batches(depot.office_id, quantity, picks),
    )
    db.session.add(transfer)
    db.session.add(WarehouseStockLog(
        office_id=depot.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity, reason=f"Replenishment to {batch.office.office_name} ({batch.ref})",
        source_type="standard", updated_by=current_user.user_id,
    ))

    batch.status = "partially_approved" if quantity < batch.requested_food_packs else "approved"
    batch.approved_food_packs = quantity
    batch.fulfilling_office_id = depot.office_id
    batch.decided_by = current_user.user_id
    batch.decided_at = ph_now()
    batch.decision_remarks = remarks

    label = "Partially approved" if quantity < batch.requested_food_packs else "Approved"
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="allocation_approved",
        description=f"{label} stock request {batch.ref} - {quantity:,} food packs to "
                    f"{batch.office.office_name} from {depot.office_name}",
        office_id=batch.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"{label}: {quantity:,} food packs transferring to {batch.office.area_covered}.", "success")
    return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))


# Action: /pswdo/relief-requests/<int:batch_id>/reject - Declines a stock request. A reason is required so the municipality knows why.
@pswdo_bp.route("/relief-requests/<int:batch_id>/reject", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def reject_relief_request(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    if batch.display_status != "pending":
        flash("This stock request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))
    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("A reason is required to decline a stock request.", "error")
        return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))
    batch.status = "declined"
    batch.decision_remarks = reason
    batch.decided_by = current_user.user_id
    batch.decided_at = ph_now()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="allocation_rejected",
        description=f"Declined stock request {batch.ref} from {batch.office.office_name}: {reason}",
        office_id=batch.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"Stock request {batch.ref} declined.", "success")
    return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))


# Action: /pswdo/allocations/direct - Sends food packs from a PSWDO depot to a municipal warehouse without waiting for a request
# (e.g. to pre-position stock before a typhoon).
@pswdo_bp.route("/allocations/direct", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def direct_allocation():
    to_office_id = request.form.get("to_office_id", type=int)
    to_office = Office.query.get(to_office_id) if to_office_id else None
    if not to_office or to_office.office_type != "cswdo" or to_office.area_covered not in TARGET_LGUS:
        flash("Select a target municipal warehouse.", "error")
        return redirect(url_for("pswdo.relief_requests"))
    depot_id = request.form.get("fulfilling_office_id", type=int)
    depot = Office.query.get(depot_id) if depot_id else None
    if not depot or depot.office_type != "pswdo":
        flash("Select a provincial depot to transfer from.", "error")
        return redirect(url_for("pswdo.relief_requests"))
    quantity = request.form.get("quantity", type=int)
    if not quantity or quantity <= 0:
        flash("Enter a quantity greater than zero.", "error")
        return redirect(url_for("pswdo.relief_requests"))

    src = WarehouseInventory.query.filter_by(office_id=depot.office_id, item_type="food_pack").first()
    available = src.quantity_available if src else 0
    if quantity > available:
        flash(f"{depot.office_name} only has {available:,} food packs available.", "error")
        return redirect(url_for("pswdo.relief_requests"))
    picks, err = _batch_picks_from_form(depot.office_id, quantity)
    if err:
        flash(err, "error")
        return redirect(url_for("pswdo.relief_requests"))

    # Take the packs out of the provincial depot's stock.
    src.quantity_available -= quantity
    src.updated_by = current_user.user_id
    transfer = WarehouseTransfer(
        from_office_id=depot.office_id, to_office_id=to_office.office_id,
        item_type="food_pack", quantity=quantity, batch_id=None,
        status="pending", dispatch_status="in_transit",
        issued_by=current_user.user_id, issued_at=ph_now(),
        note=request.form.get("remarks", "").strip() or "Proactive pre-positioning",
        requested_by=current_user.user_id,
        batch_lots=_deduct_food_pack_batches(depot.office_id, quantity, picks),
    )
    db.session.add(transfer)
    db.session.add(WarehouseStockLog(
        office_id=depot.office_id, item_type="food_pack", item_name="Food Packs",
        delta=-quantity, reason=f"Pre-positioning to {to_office.office_name}",
        source_type="standard", updated_by=current_user.user_id,
    ))
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="direct_allocation",
        description=f"Pre-positioned {quantity:,} food packs to {to_office.office_name} from {depot.office_name}",
        office_id=to_office.office_id,
    ))
    db.session.commit()
    flash(f"{quantity:,} food packs pre-positioned to {to_office.area_covered}.", "success")
    return redirect(url_for("pswdo.transfers"))


TRANSFER_STATUS_LABELS = {"preparing": "Preparing", "in_transit": "In Transit", "delivered": "Delivered"}
TRANSFER_STEPS = ["preparing", "in_transit", "delivered"]


# The IDs of the 3 target municipal (CSWDO/MSWDO) offices.
def _cswdo_office_ids():
    return [o.office_id for o in Office.query.filter(
        Office.office_type == "cswdo", Office.area_covered.in_(TARGET_LGUS)
    ).all()]


# Page: /pswdo/transfers - Transfers page: stock being moved from PSWDO depots to the municipal warehouses,
# with search and filters by status, destination and date.
@pswdo_bp.route("/transfers")
@login_required
@role_required("pswdo_admin", "system_admin")
def transfers():
    status_filter = request.args.get("status", "all")
    cswdo_ids = _cswdo_office_ids()
    q = WarehouseTransfer.query.filter(WarehouseTransfer.to_office_id.in_(cswdo_ids))
    all_t = q.order_by(WarehouseTransfer.requested_at.desc()).all()
    monitored = [t for t in all_t if t.dispatch_status is not None or t.batch_id is not None]

    search_query = request.args.get("q", "").strip()
    destination_filter = request.args.get("destination", "all")
    type_filter = request.args.get("type", "all")
    date_from, date_to = date_range(request.args)

    rows = monitored
    if status_filter == "active":
        rows = [t for t in rows if t.status != "completed"]
    elif status_filter == "completed":
        rows = [t for t in rows if t.status == "completed"]
    elif status_filter in TRANSFER_STATUS_LABELS:
        rows = [t for t in rows if t.dispatch_status == status_filter]
    if destination_filter != "all":
        rows = [t for t in rows if t.to_office and t.to_office.area_covered == destination_filter]
    if type_filter == "replenishment":
        rows = [t for t in rows if t.batch_id]
    elif type_filter == "preposition":
        rows = [t for t in rows if not t.batch_id]
    rows = [t for t in rows if in_range(t.requested_at, date_from, date_to)]
    if search_query:
        needle = search_query.lower()
        rows = [t for t in rows if needle in t.ref.lower() or (t.batch and needle in t.batch.ref.lower())]

    return render_template(
        "pswdo/transfers.html",
        rows=rows, status_filter=status_filter,
        search_query=search_query, destination_filter=destination_filter, type_filter=type_filter,
        date_from=iso(date_from), date_to=iso(date_to), target_lgus=TARGET_LGUS,
        labels=TRANSFER_STATUS_LABELS,
        active_count=sum(1 for t in monitored if t.status != "completed"),
        completed_count=sum(1 for t in monitored if t.status == "completed"),
        in_transit_packs=sum(t.quantity for t in monitored if t.dispatch_status == "in_transit"),
    )


# Page: /pswdo/transfers/<int:transfer_id> - One transfer's details and its delivery progress (preparing, in transit, received).
@pswdo_bp.route("/transfers/<int:transfer_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def transfer_detail(transfer_id):
    t = WarehouseTransfer.query.get_or_404(transfer_id)
    if t.to_office_id not in _cswdo_office_ids():
        abort(404)
    idx = TRANSFER_STEPS.index(t.dispatch_status) if t.dispatch_status in TRANSFER_STEPS else 0
    return render_template(
        "pswdo/transfer_detail.html",
        t=t, steps=TRANSFER_STEPS, labels=TRANSFER_STATUS_LABELS, current_index=idx,
        can_issue=(t.dispatch_status == "preparing" and not t.issued_at),
    )


# Action: /pswdo/transfers/<int:transfer_id>/issue - Dispatches a transfer: marks it 'In Transit' and saves the expected arrival date.
@pswdo_bp.route("/transfers/<int:transfer_id>/issue", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def transfer_issue(transfer_id):
    t = WarehouseTransfer.query.get_or_404(transfer_id)
    if t.to_office_id not in _cswdo_office_ids() or t.dispatch_status != "preparing":
        flash("This transfer can't be dispatched right now.", "error")
        return redirect(url_for("pswdo.transfer_detail", transfer_id=transfer_id))
    t.issued_by = current_user.user_id
    t.issued_at = ph_now()
    t.dispatch_status = "in_transit"
    ea = request.form.get("expected_arrival", "")
    if ea:
        try:
            t.expected_arrival = datetime.strptime(ea, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_status",
        description=f"{t.ref} dispatched - {t.quantity:,} food packs en route to {t.to_office.office_name}",
        office_id=t.to_office_id, batch_id=t.batch_id,
    ))
    db.session.commit()
    flash(f"{t.ref} dispatched. Awaiting {t.to_office.area_covered}'s receipt confirmation.", "success")
    return redirect(url_for("pswdo.transfer_detail", transfer_id=transfer_id))


# Page: /pswdo/recommendations - Recommendations page: for each municipality, how much stock it should have
# for the next 3/6/9/12 months (from the forecast), how much is short, and what to do next.
@pswdo_bp.route("/recommendations")
@login_required
@role_required("pswdo_admin", "system_admin")
def recommendations_page():
    active_event = blocking_event_for_province()
    _, warehouses, total_food_packs = _load_warehouses()
    depots = [w for w in warehouses if w["office"].office_type == "pswdo"]
    healthiest = max(depots, key=lambda w: w["food_pack_qty"], default=None)

    horizon_months = request.args.get("months", 12, type=int)
    if horizon_months not in (3, 6, 9, 12):
        horizon_months = 12

    municipalities = []
    total_demand = total_shortage = total_stockpile = 0
    for lgu in TARGET_LGUS:
        office = Office.query.filter_by(office_type="cswdo", area_covered=lgu).first()
        forecast = ml_predict.forecast_lgu(lgu, horizon_months)
        demand = forecast["months"][0]["projected_packs"] if forecast else 0
        stockpile_total = forecast["horizon_p90"] if forecast else 0
        expected_total = forecast["horizon_total"] if forecast else 0
        lgu_barangays = Barangay.query.filter_by(city_municipality=lgu).all()
        barangay_count = len(lgu_barangays)
        fp = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first() if office else None
        on_hand = fp.quantity_available if fp else 0
        shortage = max(demand - on_hand, 0)
        total_demand += demand
        total_shortage += shortage
        total_stockpile += stockpile_total
        open_req = ReliefRequestBatch.query.filter(
            ReliefRequestBatch.office_id == (office.office_id if office else 0),
            ReliefRequestBatch.status.in_(("pending", "approved", "partially_approved")),
        ).order_by(ReliefRequestBatch.submitted_at.desc()).first() if office else None

        barangay_rows = []
        for b in lgu_barangays:
            bf = ml_predict.forecast_barangay(b, horizon_months)
            barangay_rows.append({
                "name": b.barangay_name,
                "this_month": bf["months"][0]["projected_packs"] if bf and bf["months"] else 0,
                "stockpile": bf["horizon_p90"] if bf else 0,
            })
        barangay_rows.sort(key=lambda r: r["this_month"], reverse=True)

        municipalities.append({
            "lgu": lgu, "office": office, "demand": demand, "on_hand": on_hand,
            "shortage": shortage, "coverage_pct": round(min(on_hand / demand * 100, 100)) if demand else 100,
            "barangay_count": barangay_count, "open_request": open_req,
            "stockpile_total": stockpile_total, "expected_total": expected_total,
            "forecast_months": forecast["months"] if forecast else [],
            "barangays": barangay_rows,
        })

    src = healthiest["office"].office_name if healthiest else "a provincial depot"

    # The suggested next step for a municipality
    # (approve its pending request, monitor the transfer, or pre-position stock).
    def _action(m, qty):
        if m["open_request"] and m["open_request"].status == "pending":
            return (f"Stock request {m['open_request'].ref} is pending - approve up to {qty:,} packs.",
                    url_for("pswdo.relief_request_detail", batch_id=m["open_request"].batch_id))
        if m["open_request"]:
            return (f"Stock request {m['open_request'].ref} already approved - monitor the transfer.",
                    url_for("pswdo.relief_request_detail", batch_id=m["open_request"].batch_id))
        return (f"No request on file yet. Consider pre-positioning ~{qty:,} packs from {src} "
                f"now, toward a {horizon_months}-month stockpile target of {m['stockpile_total']:,} packs.",
                url_for("pswdo.relief_requests"))

    recs = []
    for m in sorted(municipalities, key=lambda x: x["shortage"], reverse=True):
        if m["shortage"] <= 0:
            continue
        action, link = _action(m, m["shortage"])
        recs.append({
            "type": "critical" if m["coverage_pct"] < 50 else "warning",
            "title": f"{m['lgu']}: {m['demand']:,} projected this month vs {m['on_hand']:,} on hand → short {m['shortage']:,}",
            "detail": action, "link": link,
        })
    by_lgu = {m["lgu"]: m for m in municipalities}
    for fr in _forecast_recommendations(warehouses, horizon_months):
        m = by_lgu.get(fr["lgu"])
        if not m or m["shortage"] > 0:
            continue
        action, link = _action(m, max(m["stockpile_total"] - m["on_hand"], 0))
        recs.append({"type": fr["type"], "title": fr["title"],
                     "detail": fr["summary"] + " " + action, "link": link})
    for br in _barangay_recommendations(warehouses, TARGET_LGUS, horizon_months):
        recs.append({"type": br["type"], "title": br["title"], "detail": br["detail"],
                     "link": url_for("pswdo.relief_requests")})
    for w in depots:
        if w["health"] == "Low":
            recs.append({
                "type": "warning",
                "title": f"{w['office'].office_name} stock low - {w['pct']:.0f}% of capacity ({w['food_pack_qty']:,} packs)",
                "detail": "Replenish this depot before it can't cover municipal requests.",
                "link": url_for("pswdo.warehouse_inventory"),
            })
    if not recs:
        recs.append({"type": "info", "title": "All municipal warehouses are covered",
                     "detail": f"Projected demand {total_demand:,} packs this month is met by current municipal stock.", "link": None})

    return render_template(
        "pswdo/recommendations.html",
        active_event=active_event, municipalities=municipalities, recommendations=recs,
        total_demand=total_demand, total_shortage=total_shortage,
        total_stockpile=total_stockpile, horizon_months=horizon_months,
        total_food_packs=total_food_packs,
        model_available=ml_predict.is_model_available(),
    )


# Lists the food pack deliveries that match the page filters (status, municipality, dates, search),
# with counts per status.
def _filtered_distributions():
    today = ph_today()
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()
    municipality_filter = request.args.get("municipality", "all")
    date_from, date_to = date_range(request.args)

    primary_event = DisasterEvent.query.filter_by(status="active", scope="province").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = DistributionRecord.query.join(Barangay).join(
        AllocationRecord, DistributionRecord.allocation_id == AllocationRecord.allocation_id
    ).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.source.notin_(("barangay_request", "cswdo_direct")),
    )
    today_query = base_query.filter(DistributionRecord.distribution_date == today)

    total_today = today_query.count()
    preparing_count = today_query.filter(DistributionRecord.dispatch_status == "preparing").count()
    in_transit_count = today_query.filter(DistributionRecord.dispatch_status == "in_transit").count()
    delivered_today = today_query.filter(DistributionRecord.dispatch_status == "delivered").all()
    delivered_count = len(delivered_today)
    packs_released = sum(d.quantity_released for d in delivered_today)

    query = base_query
    if status_filter != "all":
        query = query.filter(DistributionRecord.dispatch_status == status_filter)
    if municipality_filter != "all":
        query = query.filter(Barangay.city_municipality == municipality_filter)
    if date_from:
        query = query.filter(DistributionRecord.distribution_date >= date_from)
    if date_to:
        query = query.filter(DistributionRecord.distribution_date <= date_to)

    records = query.order_by(DistributionRecord.distribution_date.desc()).all()
    if search_query:
        needle = search_query.lower()
        records = [r for r in records if needle in r.barangay.city_municipality.lower()
                   or needle in f"d-{r.distribution_date.year}-{r.distribution_id:03d}"]

    return {
        "primary_event": primary_event,
        "today": today,
        "total_today": total_today,
        "preparing_count": preparing_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "packs_released": packs_released,
        "status_filter": status_filter,
        "search_query": search_query,
        "municipality_filter": municipality_filter,
        "date_from": iso(date_from),
        "date_to": iso(date_to),
        "target_lgus": TARGET_LGUS,
        "records": records,
    }


# Approved allocations that don't have a delivery yet (ready to be scheduled),
# with the supplying warehouse's stock.
def _eligible_for_distribution():
    allocations = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "approved",
        AllocationRecord.source.notin_(("barangay_request", "cswdo_direct")),
        ~AllocationRecord.distribution_records.any(),
    ).order_by(AllocationRecord.allocation_date.desc()).all()

    office_ids = {a.fulfilling_office_id for a in allocations if a.fulfilling_office_id}
    stock_by_office = {}
    if office_ids:
        rows = WarehouseInventory.query.filter(
            WarehouseInventory.office_id.in_(office_ids),
            WarehouseInventory.item_type == "food_pack",
        ).all()
        stock_by_office = {r.office_id: r.quantity_available for r in rows}

    enriched = []
    for a in allocations:
        available = stock_by_office.get(a.fulfilling_office_id, 0)
        enriched.append({
            "allocation": a,
            "municipality": a.barangay.city_municipality,
            "available_stock": available,
            "stock_ok": available >= a.allocated_quantity,
        })
    return enriched


# Page: /pswdo/distribution - Distribution page: food pack deliveries from PSWDO to barangays and their status.
@pswdo_bp.route("/distribution")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution():
    ctx = _filtered_distributions()
    eligible_allocations = _eligible_for_distribution()

    municipality_counts = {}
    for lgu in TARGET_LGUS:
        count = sum(1 for row in eligible_allocations if row["municipality"] == lgu)
        if count:
            municipality_counts[lgu] = count

    return render_template(
        "pswdo/distribution.html",
        dispatch_labels=DISPATCH_STATUS_LABELS,
        eligible_allocations=eligible_allocations,
        municipality_counts=municipality_counts,
        today_str=ph_today().isoformat(),
        **ctx,
    )


# Action: /pswdo/distribution/create - Schedules a new delivery for an approved allocation.
@pswdo_bp.route("/distribution/create", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def create_distribution():
    allocation_id = request.form.get("allocation_id", type=int)
    allocation = _get_target_scoped_request(allocation_id) if allocation_id else None

    if not allocation:
        flash("Select a relief request to schedule.", "error")
        return redirect(url_for("pswdo.distribution"))
    if allocation.status != "approved":
        flash("Only approved relief requests can be scheduled for distribution.", "error")
        return redirect(url_for("pswdo.distribution"))
    if allocation.distribution_records:
        flash("A distribution has already been scheduled for this request.", "error")
        return redirect(url_for("pswdo.distribution"))

    office = allocation.fulfilling_office
    inventory = WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack"
    ).first() if office else None
    available = inventory.quantity_available if inventory else 0
    if not office or available < allocation.allocated_quantity:
        flash(
            f"Cannot schedule - {office.office_name if office else 'the fulfilling warehouse'} now has only "
            f"{available:,} food packs available, but this request needs {allocation.allocated_quantity:,}. "
            f"Transfer more stock in or re-approve with a lower quantity first.",
            "error"
        )
        return redirect(url_for("pswdo.distribution"))

    distribution_date = ph_today()
    date_str = request.form.get("distribution_date", "")
    if date_str:
        try:
            distribution_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    rec = DistributionRecord(
        barangay_id=allocation.barangay_id,
        allocation_id=allocation.allocation_id,
        quantity_released=allocation.allocated_quantity,
        distribution_date=distribution_date,
        dispatch_status="preparing",
        submitted_by=current_user.user_id,
    )
    db.session.add(rec)
    db.session.flush()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="distribution_status",
        description=(
            f"New distribution scheduled for {allocation.barangay.barangay_name}, "
            f"{allocation.barangay.city_municipality} - {allocation.allocated_quantity:,} food packs"
        ),
        office_id=allocation.fulfilling_office_id,
        barangay_id=allocation.barangay_id,
        distribution_id=rec.distribution_id,
    ))
    db.session.commit()

    flash(f"Distribution scheduled for {allocation.barangay.barangay_name}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=rec.distribution_id))


# Download: /pswdo/distribution/export - Downloads the deliveries list as a CSV (spreadsheet) file.
@pswdo_bp.route("/distribution/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_distribution():
    ctx = _filtered_distributions()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Distribution ID", "Request ID", "Municipality", "Warehouse",
        "Packs", "Date", "Status"
    ])
    for rec in ctx["records"]:
        fulfilling = rec.allocation.fulfilling_office or rec.allocation.office
        writer.writerow([
            f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}",
            f"RR-{rec.allocation.allocation_date.year}-{rec.allocation.allocation_id:03d}",
            rec.barangay.city_municipality,
            fulfilling.office_name if fulfilling else "",
            rec.quantity_released,
            rec.distribution_date.isoformat(),
            DISPATCH_STATUS_LABELS.get(rec.dispatch_status, rec.dispatch_status),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=distribution.csv"},
    )


OFFICE_TYPE_PREFIX = {"cswdo": "MSWDO", "pswdo": "PSWDO"}


# Shows a person's name with their office, e.g. 'PSWDO - Juan Dela Cruz'.
def _person_label(user, office):
    if not user:
        return "-"
    prefix = OFFICE_TYPE_PREFIX.get(office.office_type) if office else None
    return f"{prefix} - {user.name}" if prefix else user.name


# Finds a delivery, but only if it is in one of the 3 target municipalities.
def _get_target_scoped_distribution(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    if rec.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return rec


# Page: /pswdo/distribution/<int:distribution_id> - One delivery's details and progress steps (preparing, loaded, dispatched, in transit, delivered).
@pswdo_bp.route("/distribution/<int:distribution_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution_detail(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)
    alloc = rec.allocation

    status_key = None
    if alloc.event_id:
        bs = BarangayDisasterStatus.query.filter_by(
            barangay_id=alloc.barangay_id, event_id=alloc.event_id
        ).first()
        if bs:
            status_key = bs.status
    priority = _priority_info(status_key)

    fulfilling_office = alloc.fulfilling_office or alloc.office
    inventory = None
    if fulfilling_office:
        inventory = WarehouseInventory.query.filter_by(
            office_id=fulfilling_office.office_id, item_type="food_pack"
        ).first()
    available_stock = inventory.quantity_available if inventory else 0
    stock_after_release = max(available_stock - rec.quantity_released, 0) if rec.dispatch_status not in ("delivered",) else available_stock

    current_index = DISPATCH_STEPS.index(rec.dispatch_status) if rec.dispatch_status in DISPATCH_STEPS else 1
    route_progress = ROUTE_PROGRESS_BY_STATUS.get(rec.dispatch_status, 0)

    attachments = rec.validation_file.split(",") if rec.validation_file else []

    return render_template(
        "pswdo/distribution_detail.html",
        rec=rec,
        alloc=alloc,
        priority=priority,
        fulfilling_office=fulfilling_office,
        available_stock=available_stock,
        stock_after_release=stock_after_release,
        dispatch_steps=DISPATCH_STEPS,
        step_labels=STEP_LABELS,
        current_index=current_index,
        route_progress=route_progress,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        requested_by_label=_person_label(alloc.submitted_by, alloc.office),
        approved_by_label=_person_label(alloc.decided_by_user, alloc.fulfilling_office or alloc.office),
        attachments=attachments,
    )


# Action: /pswdo/distribution/<int:distribution_id>/advance - Moves a delivery to its next step: Preparing -> Loaded -> Dispatched -> In Transit.
@pswdo_bp.route("/distribution/<int:distribution_id>/advance", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def advance_distribution(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)
    target = request.form.get("target")

    valid_transitions = {
        "preparing": "loaded",
        "loaded": "dispatched",
        "dispatched": "in_transit",
    }
    expected_next = valid_transitions.get(rec.dispatch_status)
    if target != expected_next:
        flash("That status change is no longer valid.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    rec.dispatch_status = target
    if target == "dispatched" and not rec.departure_time:
        rec.departure_time = ph_now().time()

    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="distribution_status",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} marked {DISPATCH_STATUS_LABELS[target]}",
        office_id=rec.allocation.fulfilling_office_id,
        barangay_id=rec.barangay_id,
        distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash(f"Status updated to {DISPATCH_STATUS_LABELS[target]}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


ALLOWED_PROOF_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "zip"}


# Action: /pswdo/distribution/<int:distribution_id>/confirm-delivery - Confirms a delivery arrived: who received it, when, travel time,
# and its condition (complete, partial or damaged).
@pswdo_bp.route("/distribution/<int:distribution_id>/confirm-delivery", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def confirm_delivery(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)

    if rec.dispatch_status != "in_transit":
        flash("Delivery can only be confirmed once a distribution is In Transit.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    received_by = request.form.get("received_by", "").strip()
    condition = request.form.get("condition", "")
    time_received = request.form.get("time_received", "").strip()
    travel_time = request.form.get("travel_time", "").strip()

    if not received_by or condition not in ("complete", "partial", "damaged"):
        flash("Received By and Condition are required.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    rec.received_by = received_by
    rec.condition = condition
    rec.travel_time = travel_time or None
    if time_received:
        for fmt in ("%H:%M", "%I:%M %p"):
            try:
                rec.time_received = datetime.strptime(time_received, fmt).time()
                break
            except ValueError:
                continue

    saved_names = []
    files = request.files.getlist("proof_files")
    if files and any(f.filename for f in files):
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "distributions", str(rec.distribution_id))
        os.makedirs(upload_dir, exist_ok=True)
        for f in files:
            if not f.filename:
                continue
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_PROOF_EXTENSIONS:
                continue
            safe_name = secure_filename(f.filename)
            f.save(os.path.join(upload_dir, safe_name))
            saved_names.append(safe_name)

    if saved_names:
        rec.validation_file = ",".join(saved_names)
        rec.validation_type = "photo"

    rec.dispatch_status = "delivered"
    rec.status = "confirmed"
    rec.submitted_by = current_user.user_id

    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="distribution_delivered",
        description=f"D-{rec.distribution_date.year}-{rec.distribution_id:03d} delivered to {rec.barangay.city_municipality}, received by {received_by}",
        office_id=rec.allocation.fulfilling_office_id,
        barangay_id=rec.barangay_id,
        distribution_id=rec.distribution_id,
    ))
    db.session.commit()
    flash("Delivery confirmed.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


# Page: /pswdo/distribution/completed - Completed Deliveries page: all delivered food packs, with totals.
@pswdo_bp.route("/distribution/completed")
@login_required
@role_required("pswdo_admin", "system_admin")
def completed_deliveries():
    primary_event = DisasterEvent.query.filter_by(status="active", scope="province").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    delivered = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        DistributionRecord.dispatch_status == "delivered"
    ).order_by(DistributionRecord.distribution_date.desc()).all()

    total_delivered = len(delivered)
    packs_delivered = sum(d.quantity_released for d in delivered)
    municipalities_served = len({d.barangay.city_municipality for d in delivered})

    return render_template(
        "pswdo/completed_deliveries.html",
        primary_event=primary_event,
        delivered=delivered,
        total_delivered=total_delivered,
        packs_delivered=packs_delivered,
        municipalities_served=municipalities_served,
    )


# Page: /pswdo/notifications - PSWDO Notifications page: province-wide updates (requests, transfers, deliveries, events),
# filterable by category.
@pswdo_bp.route("/notifications")
@login_required
@role_required("pswdo_admin", "system_admin")
def notifications():
    category_filter = request.args.get("category", "all")

    known_types = PSWDO_NOTIFICATION_TYPES
    base_scope = ActivityLog.action_type.in_(known_types)

    query = ActivityLog.query.filter(base_scope)
    if category_filter != "all":
        action_types = [k for k, v in NOTIFICATION_META.items() if v["category"] == category_filter]
        query = query.filter(ActivityLog.action_type.in_(action_types))

    unread_count = ActivityLog.query.filter(base_scope, ActivityLog.is_read.is_(False)).count()
    total_count = ActivityLog.query.filter(base_scope).count()

    per_page = 10
    all_matching = query.order_by(ActivityLog.created_at.desc()).all()
    total_filtered = len(all_matching)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    page_items = []
    for log in all_matching[(page - 1) * per_page: page * per_page]:
        view = _notification_view(log)
        view["was_unread"] = not log.is_read
        page_items.append(view)

    if unread_count:
        ActivityLog.query.filter(
            base_scope, ActivityLog.is_read.is_(False)
        ).update({"is_read": True}, synchronize_session=False)
        db.session.commit()

    categories = [
        {"value": "all", "label": "All"},
        {"value": "relief_requests", "label": "Stock Requests"},
        {"value": "distribution", "label": "Deliveries"},
        {"value": "warehouse", "label": "Warehouse"},
    ]

    return render_template(
        "pswdo/notifications.html",
        items=page_items,
        unread_count=unread_count,
        total_count=total_count,
        total_filtered=total_filtered,
        category_filter=category_filter,
        categories=categories,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
    )


# Page: /pswdo/notifications/<int:log_id>/view - Marks a notification as read and opens the page it is about.
@pswdo_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("pswdo_admin", "system_admin")
def view_notification(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    log.is_read = True
    db.session.commit()
    destination = _notification_view(log)["link"]
    return redirect(destination or url_for("pswdo.notifications"))


# Page: /pswdo/settings/profile - PSWDO user's Profile Settings page.
@pswdo_bp.route("/settings/profile")
@login_required
@role_required("pswdo_admin", "system_admin")
def profile_settings():
    return render_template("pswdo/profile_settings.html")


# Action: /pswdo/settings/profile - Saves the user's own name and email (the email must not be used by another account).
@pswdo_bp.route("/settings/profile", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def update_profile_info():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("pswdo.profile_settings"))

    email_taken = User.query.filter(
        User.email == email, User.user_id != current_user.user_id
    ).first()
    if email_taken:
        flash(f"{email} is already in use by another account.", "error")
        return redirect(url_for("pswdo.profile_settings"))

    current_user.name = name
    current_user.email = email
    db.session.commit()
    flash("Profile information updated.", "success")
    return redirect(url_for("pswdo.profile_settings"))


# Action: /pswdo/settings/password - Changes the user's own password.
# The current password must be correct and the new one at least 8 characters.
@pswdo_bp.route("/settings/password", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "error")
    elif len(new_password) < 8:
        flash("New password must be at least 8 characters long.", "error")
    elif new_password != confirm_password:
        flash("New password and confirmation do not match.", "error")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("pswdo.profile_settings"))
