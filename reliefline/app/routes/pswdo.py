import calendar
import csv
import io
import json
import os
import re
from math import radians, sin, cos, sqrt, atan2

from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
from werkzeug.utils import secure_filename
from app.extensions import db
from app.utils.decorators import role_required
from app.models.office import Office
from app.models.barangay import Barangay
from app.models.warehouse import WarehouseInventory, WarehouseStockLog
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.activity_log import ActivityLog, DailyOpsStat
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


def _healthy_threshold():
    # Admin-editable via System Settings — see app.utils.settings.SETTINGS_SCHEMA.
    return get_setting("warehouse_healthy_threshold", WAREHOUSE_HEALTHY_DEFAULT, cast=float)


def _moderate_threshold():
    return get_setting("warehouse_moderate_threshold", WAREHOUSE_MODERATE_DEFAULT, cast=float)

# Priority is derived from BarangayDisasterStatus for the active event —
# there is no priority/urgency column in the schema, so this maps the
# existing 4-tier status enum onto the labels the UI shows.
PRIORITY_BY_STATUS = {
    "high_priority": {"label": "Critical", "tier": "critical", "detail": "Immediate action required", "rank": 4},
    "needs_assistance": {"label": "High", "tier": "high", "detail": "Needs attention", "rank": 3},
    "monitoring": {"label": "Medium", "tier": "medium", "detail": "Monitor", "rank": 2},
    "normal": {"label": "Low", "tier": "low", "detail": "Stable", "rank": 1},
}
DEFAULT_PRIORITY = {"label": "Unrated", "tier": "unrated", "detail": "No status on record", "rank": 0}

DISPATCH_STATUS_LABELS = {
    "preparing": "Preparing",
    "loaded": "Loaded",
    "dispatched": "Dispatched",
    "in_transit": "In Transit",
    "delivered": "Delivered",
    "delayed": "Delayed",
}

# Sequential happy-path stages for the detail-page stepper (delayed is a side-branch flag, not a step)
DISPATCH_STEPS = ["approved", "preparing", "loaded", "dispatched", "in_transit", "delivered"]
STEP_LABELS = {
    "approved": "Approved", "preparing": "Preparing", "loaded": "Loaded",
    "dispatched": "Dispatched", "in_transit": "In Transit", "delivered": "Delivered",
}

# Route-map placeholder progress, 0 = at warehouse, 100 = at destination
ROUTE_PROGRESS_BY_STATUS = {
    "preparing": 0, "loaded": 10, "dispatched": 35,
    "in_transit": 65, "delivered": 100, "delayed": 50,
}

# Every ActivityLog.action_type actually written anywhere in this app (see the
# ActivityLog(...) call sites) — the Notifications page and dashboard mini
# panel both render off of this, so a new action_type must be added here too.
NOTIFICATION_META = {
    "allocation_approved": {"icon": "check-circle", "color": "#1e8449", "category": "relief_requests", "category_label": "Relief Requests"},
    "allocation_rejected": {"icon": "x-circle", "color": "#c0392b", "category": "relief_requests", "category_label": "Relief Requests"},
    "relief_request_submitted": {"icon": "clipboard", "color": "#3867d6", "category": "relief_requests", "category_label": "Relief Requests"},
    "distribution_status": {"icon": "truck", "color": "#2c5aa0", "category": "distribution", "category_label": "Distribution"},
    "distribution_delivered": {"icon": "check-circle", "color": "#1e8449", "category": "distribution", "category_label": "Distribution"},
    "warehouse_transfer_completed": {"icon": "rotate-ccw", "color": "#6c5ce7", "category": "warehouse", "category_label": "Warehouse"},
    "damage_report_submitted": {"icon": "clipboard", "color": "#3867d6", "category": "damage_reports", "category_label": "Damage Reports"},
    "damage_report_verified": {"icon": "check-circle", "color": "#1e8449", "category": "damage_reports", "category_label": "Damage Reports"},
    "damage_report_returned": {"icon": "x-circle", "color": "#c0392b", "category": "damage_reports", "category_label": "Damage Reports"},
    "distribution_receipt_confirmed": {"icon": "check-circle", "color": "#1e8449", "category": "distribution", "category_label": "Distribution"},
    "disaster_event_declared": {"icon": "cloud-lightning", "color": "#c0392b", "category": "disaster_events", "category_label": "Disaster Events"},
    "disaster_event_ended": {"icon": "check-circle", "color": "#1e8449", "category": "disaster_events", "category_label": "Disaster Events"},
    "direct_allocation": {"icon": "package", "color": "#6c5ce7", "category": "relief_requests", "category_label": "Relief Requests"},
    # Tier 1 (barangay -> CSWDO) — CSWDO + barangay feeds only, never PSWDO's.
    "barangay_relief_approved": {"icon": "check-circle", "color": "#1e8449", "category": "relief_requests", "category_label": "Relief Requests"},
    "barangay_relief_declined": {"icon": "x-circle", "color": "#c0392b", "category": "relief_requests", "category_label": "Relief Requests"},
}
DEFAULT_NOTIFICATION_META = {"icon": "bell", "color": "#8a94a6", "category": "other", "category_label": "Other"}

# Damage report review is entirely a CSWDO/MSWDO responsibility per the
# manuscript — PSWDO has no damage-report page of its own to click through
# to (see BarangayReport's own docstring: "reviewed/verified by the CSWDO/
# MSWDO office"). Rather than show these as dead-end, non-clickable entries,
# PSWDO's own notification feed excludes them outright; NOTIFICATION_META
# itself stays the shared source of truth since CSWDO's and Barangay's own
# notification feeds still need these 3 action_types.
PSWDO_EXCLUDED_NOTIFICATION_TYPES = {
    "damage_report_submitted", "damage_report_verified", "damage_report_returned",
    "barangay_relief_approved", "barangay_relief_declined",
}
PSWDO_NOTIFICATION_TYPES = [k for k in NOTIFICATION_META if k not in PSWDO_EXCLUDED_NOTIFICATION_TYPES]

def _batch_link(log):
    """Stock Request notifications resolve to that batch's detail page."""
    if log.batch_id:
        return url_for("pswdo.relief_request_detail", batch_id=log.batch_id)
    return url_for("pswdo.relief_requests")


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


def _priority_info(status_key):
    return PRIORITY_BY_STATUS.get(status_key, DEFAULT_PRIORITY)


# --- GIS map: real PSGC boundary data (faeldon/philippines-json-maps), scoped to
# exactly what the manuscript covers — barangay-level for the 3 target LGUs, with
# the rest of the province shown only as neutral geographic context (no disaster
# data is tracked for those areas, so none is shown for them).
GIS_LGU_FILES = {
    "Urdaneta City": "urdaneta_barangays.json",
    "Santa Barbara": "santabarbara_barangays.json",
    "Calasiao": "calasiao_barangays.json",
}

_geojson_cache = {}


def _load_geojson_file(filename):
    # Keyed on the file's mtime, not just its name — a boundary-data fix
    # edited on disk (e.g. the Santa Barbara/Calasiao/Urdaneta polygon
    # corrections) used to keep serving the stale in-memory copy for the
    # rest of that server process's life until someone thought to restart
    # it. Re-reading on mtime change costs one cheap stat() per request and
    # means a saved edit is just live, no restart required.
    path = os.path.join(current_app.root_path, "static", "geo", filename)
    mtime = os.path.getmtime(path)
    cached = _geojson_cache.get(filename)
    if cached is None or cached[0] != mtime:
        with open(path) as f:
            _geojson_cache[filename] = (mtime, json.load(f))
    return _geojson_cache[filename][1]


def _bbox_center(geometry):
    """Bounding-box midpoint — used only as a fallback when a polygon is too
    degenerate for _polygon_centroid to compute an area."""
    lons, lats = [], []

    def collect(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                collect(c)

    collect(geometry["coordinates"])
    return ((min(lats) + max(lats)) / 2, (min(lons) + max(lons)) / 2)


def _ring_signed_area_centroid(ring):
    """Shoelace-formula signed area and centroid of a single [lon, lat] ring."""
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


def _polygon_centroid(geometry):
    """Area-weighted centroid of a Polygon/MultiPolygon's exterior ring(s) —
    correct for concave, bay-wrapping coastal shapes (e.g. Alaminos) where a
    bounding-box midpoint can land in open water. Falls back to the bbox
    center only if every ring turns out to be degenerate (zero area)."""
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


def _normalize_muni_name(name):
    """Collapse both PSGC naming conventions ("City of Urdaneta" from the
    province boundary file vs. "Urdaneta City" used elsewhere in the app) to
    the same bare name so lookups between the two match."""
    name = name.strip()
    lowered = name.lower()
    if lowered.startswith("city of "):
        name = name[len("city of "):]
    elif lowered.endswith(" city"):
        name = name[: -len(" city")]
    return name.strip()


def _haversine_km(point_a, point_b):
    """Great-circle distance in km — used only for an approximate warehouse
    distance estimate, not a claim of real road distance/travel time."""
    lat1, lon1 = point_a
    lat2, lon2 = point_b
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


def _municipality_centroid(area_covered):
    """Approximate lat/lng for an office's LGU, from the province boundary file.
    Used only to place warehouse markers — not a claim of a precise address."""
    province = _load_geojson_file("pangasinan_municipalities.json")
    target = _normalize_muni_name(area_covered).lower()
    for feature in province["features"]:
        if _normalize_muni_name(feature["properties"]["name"]).lower() == target:
            return _polygon_centroid(feature["geometry"])
    return None


def _target_barangay_geojson(lgu, event_id):
    """Barangay polygons for one target LGU, merged with real disaster-status
    data for the given event. Barangays with no matching DB record (a known
    data-quality gap for Santa Barbara — see conversation notes) render as
    'no_data' rather than being silently guessed at."""
    raw = _load_geojson_file(GIS_LGU_FILES[lgu])
    db_barangays = {b.barangay_name: b for b in Barangay.query.filter_by(city_municipality=lgu).all()}

    statuses = {}
    if event_id:
        rows = BarangayDisasterStatus.query.join(Barangay).filter(
            BarangayDisasterStatus.event_id == event_id,
            Barangay.city_municipality == lgu
        ).all()
        statuses = {r.barangay_id: r for r in rows}

    features = []
    for feature in raw["features"]:
        name = feature["properties"]["name"]
        barangay = db_barangays.get(name)
        if barangay:
            status_row = statuses.get(barangay.barangay_id)
            status_key = status_row.status if status_row else "normal"
            priority = _priority_info(status_key)
            props = {
                "name": name,
                "barangay_id": barangay.barangay_id,
                "has_data": True,
                "status": status_key,
                "priority_label": priority["label"],
                "priority_tier": priority["tier"],
                "affected_families": status_row.affected_families if status_row else 0,
                "population": barangay.population,
                "num_households": barangay.num_households,
                "poverty_incidence": float(barangay.poverty_incidence) if barangay.poverty_incidence is not None else None,
                "disaster_risk_index": float(barangay.disaster_risk_index) if barangay.disaster_risk_index is not None else None,
                "past_calamity_freq": barangay.past_calamity_freq,
            }
            # Current calculated food-pack figure — the map's hover detail.
            # Real submitted request if this barangay has one for the event,
            # else the Linear Regression model's live estimate — see
            # _current_packs_needed for why (never a manual barangay guess).
            packs_needed, packs_source = _current_packs_needed(barangay, event_id)
            props["food_packs_current"] = packs_needed
            props["food_packs_source"] = packs_source
        else:
            props = {"name": name, "has_data": False, "status": None, "priority_tier": "unrated"}
        features.append({"type": "Feature", "properties": props, "geometry": feature["geometry"]})

    return {"type": "FeatureCollection", "features": features}


def _target_barangay_centroid(lgu, barangay_name):
    raw = _load_geojson_file(GIS_LGU_FILES[lgu])
    for feature in raw["features"]:
        if feature["properties"]["name"] == barangay_name:
            return _polygon_centroid(feature["geometry"])
    return None


def _relief_summary(barangay_ids, event_id):
    """Food-pack requested/approved/released rollup for a set of barangays,
    built entirely from AllocationRecord + DistributionRecord — no invented
    fields (this backs the GIS map's Relief Statistics card)."""
    empty = {"requested": 0, "approved": 0, "released": 0, "remaining": 0, "progress_pct": 0}
    if not barangay_ids:
        return empty

    # Scoped to the current relief context: the active event's allocations, or —
    # when no event is active — only standing/direct allocations (event_id IS
    # NULL). Historical allocations from past ended events are NOT current need
    # and must never be summed in here (a barangay with several past typhoons on
    # record would otherwise show a "requested" figure in the tens of thousands).
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


def _current_packs_needed(barangay, event_id, relief=None):
    """The food-pack figure the system currently calculates for one barangay:
    the real submitted request for the given event if one exists (an actual
    request always beats a model guess — same rule the manuscript's Chapter 2
    Predictive Model discussion frames as "decision support rather than an
    automatic final allocation"), otherwise the Linear Regression model's live
    estimate from the barangay's latest profile data. This is the same
    "packs needed" figure the Predictive Analytics dashboard shows (see
    app.routes.prediction._barangay_snapshot) — reused here so the GIS map's
    hover detail and that dashboard never disagree. relief can be passed in
    when the caller already has it (e.g. _target_barangay_geojson) to avoid
    querying AllocationRecord/DistributionRecord twice for the same barangay.
    Returns (quantity, source) where source is "request" or "model".
    """
    if relief is None:
        relief = _relief_summary([barangay.barangay_id], event_id)
    if relief["requested"] > 0:
        return relief["requested"], "request"
    return (ml_predict.predict_quantity(barangay) or 0), "model"


def _load_warehouses():
    """ALL warehouses (province-wide infrastructure, PSWDO-managed) with current food-pack stock."""
    all_offices = Office.query.filter(
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

        if pct >= _healthy_threshold() * 100:
            health = "Healthy"
        elif pct >= _moderate_threshold() * 100:
            health = "Moderate"
        else:
            health = "Low"

        warehouses.append({
            "office": office, "food_pack_qty": qty, "capacity": capacity,
            "pct": pct, "health": health
        })
        total_food_packs += qty

    return all_offices, warehouses, total_food_packs


def _stock_recommendations(warehouses):
    """Threshold-based redistribution suggestions, food_pack only. Shared by the
    dashboard's compact panel and the full Warehouse Inventory page."""
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


def _lgu_burn_rate(office, active_events):
    """Packs/day burn rate for a warehouse's own LGU, same 3-day-per-pack basis
    as the dashboard's province-wide burn rate. Returns None when the warehouse
    isn't tied to one of the target LGUs or there's no active-event demand data."""
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


def _item_status(qty, min_level):
    """Status relative to an item's own reorder point (min_stock_level) — distinct
    from _load_warehouses()'s food-pack health, which is relative to max capacity."""
    if min_level <= 0:
        return "Healthy" if qty > 0 else "Low"
    pct = qty / min_level
    if pct >= 1.0:
        return "Healthy"
    elif pct >= 0.5:
        return "Moderate"
    return "Low"


def _slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "item"


def _parse_stock_source(form):
    """Shared by warehouse_inventory_add and warehouse_inventory_update — one
    dispatch point for turning the "Source" field on either modal into
    (source_type, donor_name, error). A donation entry needs a named donor/
    agency so the tracking is actually useful (per the manuscript's "tracks
    incoming relief supplies including special donations from external
    agencies"); anything else defaults to a routine "standard" restock."""
    source_type = form.get("source_type", "standard").strip()
    if source_type not in ("standard", "donation"):
        source_type = "standard"

    donor_name = None
    if source_type == "donation":
        donor_name = form.get("donor_name", "").strip() or None
        if not donor_name:
            return None, None, "Enter the donor or agency name for a donation entry."

    return source_type, donor_name, None


def _full_stock_movements(office_ids, type_filter="all", date_str=""):
    """Structured movement ledger (releases, completed transfers, manual stock
    adjustments) for warehouses in office_ids — real data, not free-text logs.
    type_filter: all | released | transferred_out | transferred_in | received"""
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
                # distribution_date has no time component — submitted_at is the closest
                # real timestamp on this row, used only to interleave with other sources.
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

    if type_filter in ("all", "received"):
        log_q = WarehouseStockLog.query.filter(
            WarehouseStockLog.office_id.in_(office_ids),
            WarehouseStockLog.delta > 0
        )
        if filter_date:
            log_q = log_q.filter(db.func.date(WarehouseStockLog.created_at) == filter_date)
        for log in log_q.order_by(WarehouseStockLog.created_at.desc()).all():
            base_context = log.reason or f"{log.item_name} stock update"
            if log.is_donation:
                context = f"Donated by {log.donor_name}" + (f" — {log.reason}" if log.reason else "")
            else:
                context = base_context
            movements.append({
                "office_id": log.office_id,
                "office_name": log.office.office_name,
                "direction": "Received — Donation" if log.is_donation else "Received",
                "qty": log.delta,
                "context": context,
                "when": log.created_at.date(),
                "sort_at": log.created_at,
                "is_donation": log.is_donation,
            })

    movements.sort(key=lambda m: m["sort_at"], reverse=True)
    return movements


def _recent_stock_movements(office_ids, limit=6):
    # Over-fetch on each side before merging — otherwise a same-day tie between
    # a release and a transfer can get the transfer truncated before the merge
    # even sees it (list.sort() is stable, so pre-limited insertion order wins).
    return _full_stock_movements(office_ids)[:limit]


def _resolve_dashboard_period():
    """Reads ?period=monthly|yearly&month=&year= off the dashboard request and
    turns it into a (period_start, period_end) date range, or (None, None)
    when no period is selected — the caller's cue to fall back to today's
    live/current-state view (the dashboard's original behavior).

    Deliberately does NOT touch warehouse stock — WarehouseInventory only ever
    stores today's on-hand quantity, never a historical daily balance, so
    "stock as of a past month" isn't data this system actually has. Food Packs
    Available / Low Stock Items stay live regardless of the period picked."""
    period = request.args.get("period")
    if period not in ("monthly", "yearly"):
        return None, None, None

    # Falls back to the current year/month rather than bailing out to Live —
    # switching the Monthly/Yearly tab resubmits the form without the field
    # that only the other tab renders (e.g. "month" doesn't exist while
    # Yearly is showing), and that toggle shouldn't silently drop the filter.
    year = request.args.get("year", type=int) or date.today().year

    if period == "yearly":
        return period, date(year, 1, 1), date(year, 12, 31)

    month = request.args.get("month", type=int)
    if not month or not (1 <= month <= 12):
        month = date.today().month
    last_day = calendar.monthrange(year, month)[1]
    return period, date(year, month, 1), date(year, month, last_day)


def _dashboard_period_years():
    """Selectable years for the dashboard filter — spans every DisasterEvent
    on record through the current year, so a past-dated seed event is never
    out of the dropdown's reach."""
    earliest = db.session.query(db.func.min(DisasterEvent.start_date)).scalar()
    start_year = earliest.year if earliest else date.today().year
    return list(range(date.today().year, start_year - 1, -1))


@pswdo_bp.route("/dashboard")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard():
    today = date.today()
    now = datetime.now()

    period, period_start, period_end = _resolve_dashboard_period()
    is_filtered = period is not None
    # Reflect _resolve_dashboard_period()'s own defaulting (e.g. a bare tab
    # switch with no month yet) so the filter bar's selects show what's
    # actually driving the KPIs below, not just the raw querystring.
    selected_month = period_start.month if is_filtered else None
    selected_year = period_start.year if is_filtered else None

    if is_filtered:
        # Historical view: any event whose date range overlaps the selected
        # month/year, regardless of its current status (an event that has
        # since ended still "happened" in the month being viewed).
        active_events = DisasterEvent.query.filter(
            DisasterEvent.start_date <= period_end,
            db.or_(DisasterEvent.end_date.is_(None), DisasterEvent.end_date >= period_start)
        ).order_by(DisasterEvent.start_date.desc()).all()
    else:
        # Live view: only what's active right now — the dashboard's original behavior.
        active_events = DisasterEvent.query.filter_by(status="active").order_by(
            DisasterEvent.start_date.desc()
        ).all()
    primary_event = active_events[0] if active_events else None

    all_offices, warehouses, total_food_packs = _load_warehouses()
    # Dashboard's "Warehouse Status" widget only — highest capacity % first,
    # lowest (i.e. the warehouses most in need of attention) at the bottom,
    # per how the widget is meant to read top-to-bottom.
    warehouses.sort(key=lambda w: w["pct"], reverse=True)

    # CSWDO offices only — scope for relief operations (3 target LGUs)
    cswdo_offices = [o for o in all_offices if o.office_type == "cswdo"]
    office_ids = [o.office_id for o in cswdo_offices]

    # Pending Stock Requests — the municipal-warehouse replenishment requests
    # PSWDO decides on (the ONLY request type it acts on).
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

    # Affected families + municipalities (3 target LGUs only)
    total_affected_families = 0
    affected_municipalities = set()
    if active_events:
        event_ids = [e.event_id for e in active_events]
        affected_statuses = BarangayDisasterStatus.query.filter(
            BarangayDisasterStatus.event_id.in_(event_ids),
            BarangayDisasterStatus.status != "normal"
        ).all()
        total_affected_families = sum(s.affected_families for s in affected_statuses)
        affected_municipalities = {s.barangay.city_municipality for s in affected_statuses}

    # Burn rate — based on affected families in the 3 target LGUs,
    # against TOTAL province-wide food pack stock (PSWDO can redistribute)
    burn_rate = round(total_affected_families / 3, 0) if total_affected_families > 0 else 0
    days_remaining = round(total_food_packs / burn_rate, 1) if burn_rate > 0 else None
    estimated_need = int(burn_rate * 3) if burn_rate > 0 else 0  # 3-day estimated need
    remaining_after_3days = max(total_food_packs - estimated_need, 0)

    # Low stock — item-level only, all warehouses
    all_inventory = WarehouseInventory.query.filter(
        WarehouseInventory.office_id.in_([o.office_id for o in all_offices])
    ).all()

    # Reorder-point based, same as the Inventory Management page's status column —
    # a flexible item catalog can't use a fixed per-type capacity table (that only
    # ever covered food_pack/hygiene_kit/kitchen_kit).
    low_stock_items = [
        item for item in all_inventory
        if _item_status(item.quantity_available, item.min_stock_level) == "Low"
    ]

    # System Recommendations — simple threshold-based logic, food_pack only
    recommendations = _stock_recommendations(warehouses)

    # Today's Distribution Progress (3 target LGUs, TODAY's actual active event —
    # deliberately independent of the month/year filter above, which only
    # scopes the historical KPI cards, never this always-live "today" panel).
    today_active_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    # Scoped to the active event when one exists; otherwise every approved/
    # released allocation counts (direct allocations and standing requests
    # can both happen with no declared event — see direct_allocation).
    today_query = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status.in_(["approved", "released"]),
        AllocationRecord.source != "barangay_request",
    )
    if today_active_event:
        today_query = today_query.filter(AllocationRecord.event_id == today_active_event.event_id)
    today_allocations = today_query.all()

    total_allocated_today = sum(a.allocated_quantity for a in today_allocations)

    today_distributions = DistributionRecord.query.filter_by(distribution_date=today).all()
    total_released_today = sum(d.quantity_released for d in today_distributions)
    packs_remaining = max(total_allocated_today - total_released_today, 0)
    completion_pct = round((total_released_today / total_allocated_today) * 100, 0) if total_allocated_today > 0 else 0

    municipalities_served = len(set(
        d.barangay.city_municipality for d in today_distributions if d.barangay
    ))

    vehicle_stats = DailyOpsStat.query.filter(
        DailyOpsStat.office_id.in_(office_ids),
        DailyOpsStat.stat_date == today
    ).all()
    vehicles_active = sum(v.vehicles_active for v in vehicle_stats)

    by_municipality = []
    for lgu in TARGET_LGUS:
        lgu_allocated = sum(a.allocated_quantity for a in today_allocations if a.barangay.city_municipality == lgu)
        lgu_released = sum(d.quantity_released for d in today_distributions if d.barangay and d.barangay.city_municipality == lgu)
        if lgu_allocated > 0:
            by_municipality.append({"lgu": lgu, "released": lgu_released, "allocated": lgu_allocated})

    # Recent activity feed — "Recent Activities" is the general audit trail,
    # "Notifications" below it is only the unread subset needing attention.
    # Both restricted to NOTIFICATION_META's known operational action_types —
    # System Administration rows (logins, user/office/barangay management)
    # belong on the System Admin's own System Activity page, not here.
    known_types = PSWDO_NOTIFICATION_TYPES
    recent_activities = ActivityLog.query.filter(ActivityLog.action_type.in_(known_types)).order_by(
        ActivityLog.created_at.desc()
    ).limit(4).all()
    notifications = ActivityLog.query.filter(
        ActivityLog.action_type.in_(known_types), ActivityLog.is_read.is_(False)
    ).order_by(ActivityLog.created_at.desc()).limit(3).all()

    return render_template(
        "pswdo/dashboard.html",
        active_events=active_events,
        primary_event=primary_event,
        today_active_event=today_active_event,
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
        low_stock_items=low_stock_items,
        burn_rate=burn_rate,
        days_remaining=days_remaining,
        estimated_need=estimated_need,
        remaining_after_3days=remaining_after_3days,
        recommendations=recommendations,
        completion_pct=completion_pct,
        municipalities_served=municipalities_served,
        total_released_today=total_released_today,
        packs_remaining=packs_remaining,
        vehicles_active=vehicles_active,
        by_municipality=by_municipality,
        recent_activities=recent_activities,
        notifications=notifications,
        weather_cities=TARGET_LGUS,
        now=now
    )


@pswdo_bp.route("/dashboard/weather")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard_weather():
    """JSON feed for the dashboard's live weather. Fetched client-side (see
    static/js/weather_widget.js) so a slow/unreachable upstream never blocks
    the dashboard's own page load.

    Defaults to all three target LGUs, for the dashboard's Weather & Typhoon
    Watch detail panel. The greeting header instead passes
    ?cities=Lingayen — the PSWDO's own seat (see app.utils.weather.LGU_COORDS)
    — so the header shows conditions where PSWDO staff actually are, distinct
    from the target-LGU breakdown in the panel below.
    """
    requested = request.args.get("cities")
    if requested:
        cities = [c.strip() for c in requested.split(",") if c.strip() in weather_service.LGU_COORDS]
        if cities:
            return weather_service.get_dashboard_snapshot(cities)
    return weather_service.get_dashboard_snapshot(TARGET_LGUS)


@pswdo_bp.route("/disaster-events/declare", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def declare_disaster_event():
    """Opens a new active DisasterEvent — the one action that was previously
    only possible by editing the database directly (see scripts/seed_demo_data.py;
    no route ever constructed a DisasterEvent before this one). Meant to be
    triggered off the live Weather & Typhoon Watch panel (app/utils/weather.py)
    once PSWDO decides a real detected system warrants an official response,
    though the form works with any manually-entered name too.

    Only one event may be active at a time — every dashboard's "primary_event"
    logic already assumes a single current event, so a second concurrent one
    would make "the" active typhoon ambiguous everywhere it's used.
    """
    existing = DisasterEvent.query.filter_by(status="active").first()
    if existing:
        flash(f"“{existing.event_name}” is already active. End it before declaring a new event.", "error")
        return redirect(url_for("pswdo.dashboard"))

    event_name = request.form.get("event_name", "").strip()
    if not event_name:
        flash("Event name is required to declare a disaster event.", "error")
        return redirect(url_for("pswdo.dashboard"))

    # The system is scoped to typhoon-related response (manuscript: other
    # disaster types are "future implementations"). The per-barangay hazard
    # sub-classification lives on BarangayReport.disaster_type instead.
    event_type = "typhoon"

    start_date_raw = request.form.get("start_date", "")
    try:
        start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date() if start_date_raw else date.today()
    except ValueError:
        start_date = date.today()

    weather_condition = request.form.get("weather_condition", "").strip() or None

    event = DisasterEvent(
        event_name=event_name, event_type=event_type, status="active",
        weather_condition=weather_condition, start_date=start_date,
        created_by=current_user.user_id,
    )
    db.session.add(event)
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="disaster_event_declared",
        description=f"Declared {event_name} as the active disaster event.",
    ))
    db.session.commit()

    flash(f"{event_name} has been declared as the active disaster event.", "success")
    return redirect(url_for("pswdo.dashboard"))


@pswdo_bp.route("/disaster-events/<int:event_id>/end", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def end_disaster_event(event_id):
    """Closes out an active DisasterEvent — the counterpart to
    declare_disaster_event above. Existing allocation/distribution/damage-report
    history tied to this event is untouched; it simply stops being "the"
    active event so a new one can be declared."""
    event = DisasterEvent.query.get_or_404(event_id)
    if event.status != "active":
        flash(f"{event.event_name} is not currently active.", "error")
        return redirect(url_for("pswdo.dashboard"))

    event.status = "ended"
    event.end_date = date.today()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="disaster_event_ended",
        description=f"Marked {event.event_name} as ended.",
    ))
    db.session.commit()

    flash(f"{event.event_name} has been marked as ended.", "success")
    return redirect(url_for("pswdo.dashboard"))


@pswdo_bp.route("/warehouse-inventory")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory():
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]
    # Warehouse Overview table — highest capacity % first, lowest (i.e. the
    # warehouses most in need of attention) at the bottom, same ordering as
    # the dashboard's "Warehouse Status" widget.
    warehouses.sort(key=lambda w: w["pct"], reverse=True)

    for w in warehouses:
        burn = _lgu_burn_rate(w["office"], active_events)
        w["days_remaining"] = round(w["food_pack_qty"] / burn, 0) if burn else None

    low_stock_count = len([w for w in warehouses if w["health"] == "Low"])
    recommendations = _stock_recommendations(warehouses)

    today = date.today()
    transfers_today_count = WarehouseTransfer.query.filter(
        WarehouseTransfer.status == "completed",
        db.func.date(WarehouseTransfer.completed_at) == today
    ).count()

    recent_movements = _recent_stock_movements(office_ids, limit=6)

    # Warehouse map markers — same municipality-centroid approximation used by
    # the GIS Map / dashboard mini-map (see _municipality_centroid), not a
    # claim of the warehouse's precise street address.
    warehouse_map_points = []
    for w in warehouses:
        centroid = _municipality_centroid(w["office"].area_covered)
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

    # office_type="pswdo" marks it as province-managed warehouse infrastructure,
    # so it's picked up by _load_warehouses() regardless of which LGU it's in —
    # same pattern as the existing "PSWDO Warehouse" seed offices.
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


@pswdo_bp.route("/warehouse-inventory/<int:office_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_detail(office_id):
    office = Office.query.get_or_404(office_id)
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    food_pack_item = WarehouseInventory.query.filter_by(office_id=office_id, item_type="food_pack").first()
    food_pack_qty = food_pack_item.quantity_available if food_pack_item else 0
    capacity = office.capacity_food_pack or 20000
    pct = round((food_pack_qty / capacity) * 100, 0) if capacity > 0 else 0

    if pct >= _healthy_threshold() * 100:
        health = "Healthy"
    elif pct >= _moderate_threshold() * 100:
        health = "Moderate"
    else:
        health = "Low"

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


@pswdo_bp.route("/warehouse-inventory/<int:office_id>/edit", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_edit(office_id):
    office = Office.query.get_or_404(office_id)
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


@pswdo_bp.route("/warehouse-inventory/<int:office_id>/inventory")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_items(office_id):
    office = Office.query.get_or_404(office_id)
    search_query = request.args.get("q", "").strip()

    items_q = WarehouseInventory.query.filter_by(office_id=office_id)
    if search_query:
        items_q = items_q.filter(WarehouseInventory.item_name.ilike(f"%{search_query}%"))
    items = items_q.order_by(WarehouseInventory.item_name).all()

    rows = [
        {"item": item, "status": _item_status(item.quantity_available, item.min_stock_level)}
        for item in items
    ]

    return render_template(
        "pswdo/warehouse_items.html",
        office=office, rows=rows, search_query=search_query,
    )


@pswdo_bp.route("/warehouse-inventory/<int:office_id>/inventory/add", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_add(office_id):
    office = Office.query.get_or_404(office_id)
    item_name = request.form.get("item_name", "").strip()
    unit = request.form.get("unit", "").strip() or "units"
    quantity = request.form.get("quantity", type=int)
    min_stock_level = request.form.get("min_stock_level", type=int) or 0

    if not item_name or quantity is None or quantity < 0:
        flash("Enter a valid item name and quantity.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    source_type, donor_name, source_error = _parse_stock_source(request.form)
    if source_error:
        flash(source_error, "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    item_type = _slugify(item_name)
    if WarehouseInventory.query.filter_by(office_id=office_id, item_type=item_type).first():
        flash(f"{item_name} already exists for this warehouse — use Update instead.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    item = WarehouseInventory(
        office_id=office_id, item_type=item_type, item_name=item_name, unit=unit,
        quantity_available=quantity, min_stock_level=min_stock_level,
        updated_by=current_user.user_id,
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


@pswdo_bp.route("/warehouse-inventory/inventory/<int:inventory_id>/update", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_update(inventory_id):
    item = WarehouseInventory.query.get_or_404(inventory_id)
    new_quantity = request.form.get("quantity", type=int)
    unit = request.form.get("unit", "").strip()
    reason = request.form.get("reason", "").strip() or None

    if new_quantity is None or new_quantity < 0:
        flash("Enter a valid quantity.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))

    # Only a net *increase* is ever a "received" event with a source worth
    # tagging — a decrease is a manual correction (e.g. recount, spoilage),
    # not incoming stock, so donation/standard source doesn't apply to it.
    delta = new_quantity - item.quantity_available
    source_type, donor_name = "standard", None
    if delta > 0:
        source_type, donor_name, source_error = _parse_stock_source(request.form)
        if source_error:
            flash(source_error, "error")
            return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))

    item.quantity_available = new_quantity
    if unit:
        item.unit = unit
    item.updated_by = current_user.user_id

    if delta != 0:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type=item.item_type, item_name=item.item_name,
            delta=delta, reason=reason, source_type=source_type, donor_name=donor_name,
            updated_by=current_user.user_id,
        ))

    db.session.commit()
    flash(f"Updated {item.item_name} stock.", "success")
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=item.office_id))


@pswdo_bp.route("/warehouse-inventory/inventory/<int:inventory_id>/delete", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory_delete(inventory_id):
    item = WarehouseInventory.query.get_or_404(inventory_id)
    office_id = item.office_id

    if item.item_type == "food_pack":
        flash("Food Packs can't be removed — it's required for allocation and prediction.", "error")
        return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))

    db.session.delete(item)
    db.session.commit()
    flash(f"{item.item_name} removed.", "success")
    return redirect(url_for("pswdo.warehouse_inventory_items", office_id=office_id))


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
            f"{pct}%" if pct is not None else "—",
            _item_status(item.quantity_available, item.min_stock_level),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={office.office_name.replace(' ', '_')}_inventory.csv"},
    )


@pswdo_bp.route("/warehouse-inventory/transfer", methods=["GET", "POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_transfer_page():
    all_offices, warehouses, total_food_packs = _load_warehouses()

    if request.method == "POST":
        from_office_id = request.form.get("from_office_id", type=int)
        to_office_id = request.form.get("to_office_id", type=int)
        quantity = request.form.get("quantity", type=int)
        reason = request.form.get("reason", "").strip() or None

        if not from_office_id or not to_office_id or from_office_id == to_office_id or not quantity or quantity <= 0:
            flash("Select two different warehouses and a valid quantity.", "error")
            return redirect(url_for("pswdo.warehouse_stock_transfer_page"))

        source_inventory = WarehouseInventory.query.filter_by(
            office_id=from_office_id, item_type="food_pack"
        ).first()
        if not source_inventory or source_inventory.quantity_available < quantity:
            flash("Source warehouse does not have enough food pack stock for this transfer.", "error")
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

        source_inventory.quantity_available -= quantity
        dest_inventory.quantity_available += quantity

        from_office = Office.query.get(from_office_id)
        to_office = Office.query.get(to_office_id)

        db.session.add(WarehouseTransfer(
            from_office_id=from_office_id, to_office_id=to_office_id,
            item_type="food_pack", quantity=quantity,
            status="completed", requested_by=current_user.user_id,
            completed_at=datetime.utcnow(),
        ))
        db.session.add(ActivityLog(
            actor_id=current_user.user_id, action_type="warehouse_transfer_completed",
            description=(
                f"Transferred {quantity:,} food packs from {from_office.office_name} to {to_office.office_name}"
                + (f" — {reason}" if reason else "")
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


@pswdo_bp.route("/warehouse-inventory/movements")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_movements():
    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]

    office_filter = request.args.get("office_id", type=int)
    type_filter = request.args.get("type", "all")
    date_filter = request.args.get("date", "")

    scoped_ids = [office_filter] if office_filter else office_ids
    movements = _full_stock_movements(scoped_ids, type_filter, date_filter)

    return render_template(
        "pswdo/warehouse_movements.html",
        warehouses=warehouses,
        movements=movements,
        office_filter=office_filter,
        type_filter=type_filter,
        date_filter=date_filter,
        default_office_id=warehouses[0]["office"].office_id if warehouses else None,
    )


@pswdo_bp.route("/warehouse-inventory/movements/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_stock_movements_export():
    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]

    office_filter = request.args.get("office_id", type=int)
    type_filter = request.args.get("type", "all")
    date_filter = request.args.get("date", "")
    scoped_ids = [office_filter] if office_filter else office_ids
    movements = _full_stock_movements(scoped_ids, type_filter, date_filter)

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


@pswdo_bp.route("/warehouse-inventory/reports")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_reports():
    # Deferred import — report_data imports helpers back from this module,
    # so this must be a call-time import to avoid a circular import.
    from app.models.report import ReportLog
    from app.routes.report_data import REPORT_TYPES, resolve_filters

    filters = resolve_filters(request.args)
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

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

    reports_generated = ReportLog.query.filter(ReportLog.generated_at >= filters["start_date"]).count()
    approved_requests = approved_q.count()
    packs_distributed = sum(d.quantity_released for d in delivered_q.all())
    completed_deliveries = delivered_q.count()

    query_params = {"event_id": filters["event_id"], "municipality": filters["municipality"], "days": filters["days"]}
    report_cards = [
        {"slug": slug, **info, "generate_url": url_for("reports.view", report_type=slug, **query_params)}
        for slug, info in REPORT_TYPES.items()
    ]

    recent_logs = ReportLog.query.order_by(ReportLog.generated_at.desc()).limit(10).all()
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
        f"{filters['start_date'].strftime('%b %d')} - {date.today().strftime('%b %d, %Y')}"
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


def _gis_scope_lgus():
    """LGUs the current user's GIS map may show any data for.

    PSWDO/system_admin coordinate all 3 target LGUs (their actual scope per
    the manuscript). A CSWDO/MSWDO admin is restricted to their own office's
    area_covered only — the manuscript's generalized-workflow note ("operational
    procedures unique to a specific city or municipality... are not
    accommodated") reflects a per-office operational boundary, and nothing in
    the manuscript gives one city/municipal office visibility into another's
    barangay-level demand, warehouse stock, or distribution routes. A CSWDO
    admin with no office on record (shouldn't happen in practice) gets an
    empty scope rather than falling back to full access.
    """
    if current_user.role == "cswdo_admin":
        office = current_user.office
        if office and office.area_covered in TARGET_LGUS:
            return [office.area_covered]
        return []
    return list(TARGET_LGUS)


def _gis_config():
    """Client-side config for the GIS map shell (both the PSWDO and CSWDO page
    templates) — resolves the role-specific "View Distribution" / "View Relief
    Request" destinations once, server-side, instead of hardcoding PSWDO-only
    routes in gis_map.js. CSWDO has no distribution/dispatch page of its own
    (that stays a PSWDO responsibility per the manuscript), so distributionUrl
    is None for them and gis_map.js hides that action entirely."""
    is_pswdo = current_user.role in ("pswdo_admin", "system_admin")
    scope = _gis_scope_lgus()
    return {
        "role": current_user.role,
        "reliefRequestsUrl": url_for("pswdo.relief_requests") if is_pswdo else url_for("cswdo.relief_requests"),
        "distributionUrl": url_for("pswdo.distribution") if is_pswdo else None,
        "defaultLgu": scope[0] if len(scope) == 1 else None,
    }


@pswdo_bp.route("/gis-map")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map():
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    return render_template(
        "pswdo/gis_map.html",
        active_events=active_events,
        target_lgus=_gis_scope_lgus(),
        gis_config=_gis_config(),
    )


@pswdo_bp.route("/gis-map/data")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_data():
    event_id = _resolve_event_id(request.args.get("event_id", type=int))
    scope_lgus = _gis_scope_lgus()
    full_scope = set(scope_lgus) == set(TARGET_LGUS)

    # Barangay-level layer — the only areas the manuscript's predictive/status
    # model actually covers. Everything else on the map is neutral context.
    # Scoped to scope_lgus, not TARGET_LGUS — a CSWDO/MSWDO admin only ever
    # gets their own municipality's barangays back from this endpoint.
    target_features = []
    for lgu in scope_lgus:
        fc = _target_barangay_geojson(lgu, event_id)
        for feature in fc["features"]:
            feature["properties"]["lgu"] = lgu
            target_features.append(feature)
    target_barangays_geojson = {"type": "FeatureCollection", "features": target_features}

    # Province context — geographic orientation only, no disaster data implied.
    # is_target (which drives the bordered/clickable styling and the hover
    # detail) is restricted to scope_lgus — for a CSWDO admin, the OTHER two
    # target LGUs render exactly like any other non-target municipality:
    # plain background, no click-through, no data.
    province_geojson = _load_geojson_file("pangasinan_municipalities.json")
    target_by_normalized = {_normalize_muni_name(l).lower(): l for l in TARGET_LGUS}
    province_features = []
    for feature in province_geojson["features"]:
        name = feature["properties"]["name"]
        matched_lgu = target_by_normalized.get(_normalize_muni_name(name).lower())
        in_scope = matched_lgu is not None and matched_lgu in scope_lgus
        province_features.append({
            "type": "Feature",
            "properties": {"name": name, "is_target": in_scope, "lgu": matched_lgu if in_scope else None},
            "geometry": feature["geometry"],
        })
    province_context_geojson = {"type": "FeatureCollection", "features": province_features}

    # Warehouses — real Office + WarehouseInventory data, placed at their LGU's
    # approximate centroid (not a precise street address). Full scope (PSWDO)
    # keeps every warehouse, provincial depots included. A CSWDO admin only
    # ever sees their own municipal office's stock — not another city/town's,
    # and not the provincial depots either, since that province-wide stock
    # visibility is a PSWDO-only responsibility per the manuscript and isn't
    # exposed to CSWDO anywhere else in the system.
    all_offices, warehouses, total_food_packs = _load_warehouses()
    warehouse_markers = []
    for w in warehouses:
        if not full_scope and w["office"].area_covered not in scope_lgus:
            continue
        centroid = _municipality_centroid(w["office"].area_covered)
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
            # PSWDO-only addition (gated on full_scope, the same flag this
            # function already uses to distinguish PSWDO's province-wide view
            # from CSWDO's single-LGU one) — real WarehouseInventory rows for
            # this office, item_type != "food_pack" (that one's covered by
            # food_pack_qty/capacity above). Any such row is, by definition,
            # a relief-supply stock-monitoring line item (see
            # app.models.warehouse.WarehouseInventory's own docstring) — not
            # general inventory — so all of them are relief-relevant here.
            # CSWDO's payload shape is completely unchanged by this branch.
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

    # Schematic in-transit indicators — a straight line between known warehouse
    # and barangay centroids, NOT a real road route (excluded by manuscript scope).
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
        from_point = _municipality_centroid(office.area_covered)
        to_point = _target_barangay_centroid(d.barangay.city_municipality, d.barangay.barangay_name)
        if from_point and to_point:
            in_transit_lines.append({
                "from": from_point, "to": to_point,
                "barangay": d.barangay.barangay_name,
            })

    # Side-panel stats — real counts scoped to scope_lgus only.
    barangay_props = [f["properties"] for f in target_features if f["properties"]["has_data"]]
    affected = [p for p in barangay_props if p["status"] != "normal"]
    total_affected_families = sum(p["affected_families"] for p in affected)
    priority_barangays = sorted(
        affected,
        key=lambda p: (_priority_info(p["status"])["rank"], p["affected_families"]),
        reverse=True,
    )[:5]

    # Active distribution routes table — real DistributionRecord + logistics data.
    active_routes = DistributionRecord.query.join(Barangay).join(AllocationRecord).filter(
        Barangay.city_municipality.in_(scope_lgus),
        DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"])
    ).order_by(DistributionRecord.distribution_date.desc()).limit(10).all()

    routes_table = []
    for d in active_routes:
        allocation = d.allocation
        office = allocation.fulfilling_office if allocation else None
        # Same municipality-centroid approximations used above for
        # in_transit_lines — real coordinates (not a road route), just
        # enough for the client to hand off to OSRM for the actual routing.
        # None when a centroid can't be resolved; the frontend simply won't
        # offer route visualization for that row rather than guessing.
        from_point = _municipality_centroid(office.area_covered) if office else None
        to_point = _target_barangay_centroid(d.barangay.city_municipality, d.barangay.barangay_name)
        routes_table.append({
            "distribution_id": d.distribution_id,
            "from_office": office.office_name if office else "—",
            "from_lat": from_point[0] if from_point else None,
            "from_lng": from_point[1] if from_point else None,
            "to_barangay": d.barangay.barangay_name,
            "to_municipality": d.barangay.city_municipality,
            "to_lat": to_point[0] if to_point else None,
            "to_lng": to_point[1] if to_point else None,
            "packs": d.quantity_released,
            "status": d.dispatch_status,
            "status_label": DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
            "eta": d.expected_arrival_time.strftime("%I:%M %p") if d.expected_arrival_time else "—",
        })

    # Per-municipality rollups — backs the GIS map's drill-down "Municipality
    # Information" panel. Built entirely from data already computed above plus
    # real AllocationRecord/DistributionRecord aggregates (no invented fields).
    municipalities = []
    for lgu in scope_lgus:
        lgu_props = [f["properties"] for f in target_features if f["properties"]["lgu"] == lgu and f["properties"]["has_data"]]
        lgu_affected = [p for p in lgu_props if p["status"] != "normal"]
        barangay_ids = [p["barangay_id"] for p in lgu_props]
        worst_rank = max((_priority_info(p["status"])["rank"] for p in lgu_props), default=0)
        worst_tier = next((v for v in PRIORITY_BY_STATUS.values() if v["rank"] == worst_rank), DEFAULT_PRIORITY)

        current_route = DistributionRecord.query.join(Barangay).filter(
            Barangay.city_municipality == lgu,
            DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"])
        ).order_by(DistributionRecord.distribution_date.desc()).first()
        current_distribution = None
        if current_route:
            current_distribution = {
                "distribution_id": current_route.distribution_id,
                "eta": current_route.expected_arrival_time.strftime("%I:%M %p") if current_route.expected_arrival_time else "—",
                "status": current_route.dispatch_status,
                "status_label": DISPATCH_STATUS_LABELS.get(current_route.dispatch_status, current_route.dispatch_status),
            }

        # "Assigned" warehouse — prefer the office actually fulfilling this
        # municipality's requests (real AllocationRecord.fulfilling_office_id
        # relationship) over a geographic guess; only fall back to nearest-by-
        # distance when no fulfillment history exists yet.
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

        relief = _relief_summary(barangay_ids, event_id)
        # Predicted demand — sum of each tracked barangay's food_packs_current
        # (real submitted request where one exists, else the Linear
        # Regression model's live estimate; see _current_packs_needed). Same
        # methodology Predictive Analytics already reports per barangay,
        # rolled up here for PSWDO's municipality-level oversight view so it
        # never disagrees with that page or the barangay hover detail.
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


def _resolve_event_id(event_id):
    if event_id:
        return event_id
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    return primary_event.event_id if primary_event else None


@pswdo_bp.route("/gis-map/barangay/<int:barangay_id>")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_barangay_detail(barangay_id):
    barangay = Barangay.query.get_or_404(barangay_id)
    if barangay.city_municipality not in _gis_scope_lgus():
        abort(404)

    event_id = _resolve_event_id(request.args.get("event_id", type=int))

    status_row = None
    if event_id:
        status_row = BarangayDisasterStatus.query.filter_by(
            barangay_id=barangay_id, event_id=event_id
        ).first()
    status_key = status_row.status if status_row else "normal"
    priority = _priority_info(status_key)

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
        "poverty_incidence": float(barangay.poverty_incidence) if barangay.poverty_incidence is not None else None,
        "disaster_risk_index": float(barangay.disaster_risk_index) if barangay.disaster_risk_index is not None else None,
        "past_calamity_freq": barangay.past_calamity_freq,
        "status": status_key,
        "priority_label": priority["label"],
        "priority_tier": priority["tier"],
        "affected_families": status_row.affected_families if status_row else 0,
        "relief": relief,
        "distribution_history": distribution_history,
    }


@pswdo_bp.route("/gis-map/municipality/<lgu>/report.csv")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_municipality_report(lgu):
    if lgu not in _gis_scope_lgus():
        abort(404)

    event_id = _resolve_event_id(request.args.get("event_id", type=int))
    fc = _target_barangay_geojson(lgu, event_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Barangay", "Status", "Affected Families", "Population", "Households",
        "Poverty Incidence (%)", "Disaster Risk Index",
        "Food Packs Requested", "Food Packs Approved", "Food Packs Released",
    ])
    for feature in fc["features"]:
        p = feature["properties"]
        if not p["has_data"]:
            writer.writerow([p["name"], "No data on record", "", "", "", "", "", "", "", ""])
            continue
        relief = _relief_summary([p["barangay_id"]], event_id)
        writer.writerow([
            p["name"], p["priority_label"], p["affected_families"], p["population"],
            p["num_households"], p["poverty_incidence"], p["disaster_risk_index"],
            relief["requested"], relief["approved"], relief["released"],
        ])

    filename = lgu.lower().replace(" ", "_")
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=gis_report_{filename}.csv"},
    )


# ---------------------------------------------------------------------------
# Stock Requests (PSWDO decides) — CSWDO municipal-warehouse replenishment.
# The only request type PSWDO acts on. Approving one performs a WarehouseTransfer
# from a provincial depot into the CSWDO warehouse; PSWDO monitors that leg.
# ---------------------------------------------------------------------------

RR_STATUS_LABELS = {
    "draft": "Draft", "pending": "Under Review", "approved": "Approved",
    "partially_approved": "Partially Approved", "declined": "Declined", "fulfilled": "Fulfilled",
}


def _stock_request_rows(status_filter="all", municipality_filter="all", search=""):
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
        if search and search.lower() not in b.ref.lower() and search.lower() not in lgu.lower():
            continue
        rows.append(b)
    return rows


def _municipal_demand_for(office, event):
    """Sum of the barangay-level model outputs for an office's LGU — the exact
    figure PSWDO sees (aggregation traceability). Real active-event barangay
    request where one exists, else the model estimate."""
    lgu = office.area_covered if office else None
    if not lgu:
        return [], 0
    event_id = event.event_id if event else None
    rows = []
    for b in Barangay.query.filter_by(city_municipality=lgu).order_by(Barangay.barangay_name).all():
        req = None
        if event_id:
            rep = BarangayReport.query.filter_by(barangay_id=b.barangay_id, event_id=event_id).filter(
                BarangayReport.status.in_(("pending", "approved", "fulfilled"))
            ).first()
            req = rep.requested_food_packs if rep else None
        model = ml_predict.predict_quantity(b) or 0
        demand = req if (req and req > 0) else model
        rows.append({"barangay": b, "model": model, "requested": req, "demand": demand})
    return rows, sum(r["demand"] for r in rows)


@pswdo_bp.route("/relief-requests")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_requests():
    status_filter = request.args.get("status", "all")
    municipality_filter = request.args.get("municipality", "all")
    search_query = request.args.get("q", "").strip()
    rows = _stock_request_rows(status_filter, municipality_filter, search_query)

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
        target_lgus=TARGET_LGUS, status_labels=RR_STATUS_LABELS, priority_labels={"high": "High", "medium": "Medium", "low": "Low"},
        depots=depots, page=page, total_pages=total_pages,
    )


@pswdo_bp.route("/relief-requests/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_relief_requests():
    rows = _stock_request_rows(
        request.args.get("status", "all"), request.args.get("municipality", "all"),
        request.args.get("q", "").strip(),
    )
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


def _get_target_scoped_request(allocation_id):
    req = AllocationRecord.query.get_or_404(allocation_id)
    if req.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return req


@pswdo_bp.route("/relief-requests/<int:batch_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_request_detail(batch_id):
    batch = ReliefRequestBatch.query.get_or_404(batch_id)
    if not batch.office or batch.office.office_type != "cswdo":
        abort(404)
    breakdown, predicted_demand = _municipal_demand_for(batch.office, batch.event)

    fp = WarehouseInventory.query.filter_by(office_id=batch.office_id, item_type="food_pack").first()
    cswdo_on_hand = fp.quantity_available if fp else 0
    _, warehouses, _ = _load_warehouses()
    depots = [w for w in warehouses if w["office"].office_type == "pswdo" and w["food_pack_qty"] > 0]
    transfer = batch.transfer

    return render_template(
        "pswdo/relief_request_detail.html",
        batch=batch, breakdown=breakdown, predicted_demand=predicted_demand,
        cswdo_on_hand=cswdo_on_hand, shortfall=max(predicted_demand - cswdo_on_hand, 0),
        depots=depots, transfer=transfer,
        status_labels=RR_STATUS_LABELS, priority_labels={"high": "High", "medium": "Medium", "low": "Low"},
        dispatch_labels={"preparing": "Preparing", "in_transit": "In Transit", "delivered": "Delivered"},
    )


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

    src.quantity_available -= quantity
    src.updated_by = current_user.user_id
    transfer = WarehouseTransfer(
        from_office_id=depot.office_id, to_office_id=batch.office_id,
        item_type="food_pack", quantity=quantity, batch_id=batch.batch_id,
        status="pending", dispatch_status="preparing",
        requested_by=current_user.user_id,
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
    batch.decided_at = datetime.utcnow()
    batch.decision_remarks = remarks

    label = "Partially approved" if quantity < batch.requested_food_packs else "Approved"
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="allocation_approved",
        description=f"{label} stock request {batch.ref} — {quantity:,} food packs to "
                    f"{batch.office.office_name} from {depot.office_name}",
        office_id=batch.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"{label}: {quantity:,} food packs transferring to {batch.office.area_covered}.", "success")
    return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))


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
    batch.decided_at = datetime.utcnow()
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="allocation_rejected",
        description=f"Declined stock request {batch.ref} from {batch.office.office_name}: {reason}",
        office_id=batch.office_id, batch_id=batch.batch_id,
    ))
    db.session.commit()
    flash(f"Stock request {batch.ref} declined.", "success")
    return redirect(url_for("pswdo.relief_request_detail", batch_id=batch_id))


@pswdo_bp.route("/allocations/direct", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def direct_allocation():
    """PSWDO pre-positioning stock into a CSWDO warehouse proactively, ahead of
    any Stock Request (manuscript's pre-positioning phase). Creates a monitored
    WarehouseTransfer, not a barangay allocation — PSWDO never allocates to a
    barangay directly (that is CSWDO's job)."""
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

    src.quantity_available -= quantity
    src.updated_by = current_user.user_id
    transfer = WarehouseTransfer(
        from_office_id=depot.office_id, to_office_id=to_office.office_id,
        item_type="food_pack", quantity=quantity, batch_id=None,
        status="pending", dispatch_status="in_transit",
        issued_by=current_user.user_id, issued_at=datetime.utcnow(),
        note=request.form.get("remarks", "").strip() or "Proactive pre-positioning",
        requested_by=current_user.user_id,
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


# ---------------------------------------------------------------------------
# Stock Transfers monitor — PSWDO -> CSWDO warehouse legs (Stock-Request
# fulfilments + proactive pre-positioning). PSWDO monitors the trip; the CSWDO
# warehouse confirms receipt (which credits the stock). This is the ONLY
# delivery monitoring PSWDO does — barangay deliveries are CSWDO's.
# ---------------------------------------------------------------------------

TRANSFER_STATUS_LABELS = {"preparing": "Preparing", "in_transit": "In Transit", "delivered": "Delivered"}
TRANSFER_STEPS = ["preparing", "in_transit", "delivered"]


def _cswdo_office_ids():
    return [o.office_id for o in Office.query.filter(
        Office.office_type == "cswdo", Office.area_covered.in_(TARGET_LGUS)
    ).all()]


@pswdo_bp.route("/transfers")
@login_required
@role_required("pswdo_admin", "system_admin")
def transfers():
    status_filter = request.args.get("status", "all")
    cswdo_ids = _cswdo_office_ids()
    q = WarehouseTransfer.query.filter(WarehouseTransfer.to_office_id.in_(cswdo_ids))
    all_t = q.order_by(WarehouseTransfer.requested_at.desc()).all()
    # Instant depot->depot redistributions never get a dispatch_status; exclude.
    monitored = [t for t in all_t if t.dispatch_status is not None or t.batch_id is not None]

    rows = monitored
    if status_filter == "active":
        rows = [t for t in rows if t.status != "completed"]
    elif status_filter == "completed":
        rows = [t for t in rows if t.status == "completed"]

    return render_template(
        "pswdo/transfers.html",
        rows=rows, status_filter=status_filter,
        labels=TRANSFER_STATUS_LABELS,
        active_count=sum(1 for t in monitored if t.status != "completed"),
        completed_count=sum(1 for t in monitored if t.status == "completed"),
        in_transit_packs=sum(t.quantity for t in monitored if t.dispatch_status == "in_transit"),
    )


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


@pswdo_bp.route("/transfers/<int:transfer_id>/issue", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def transfer_issue(transfer_id):
    t = WarehouseTransfer.query.get_or_404(transfer_id)
    if t.to_office_id not in _cswdo_office_ids() or t.dispatch_status != "preparing":
        flash("This transfer can't be dispatched right now.", "error")
        return redirect(url_for("pswdo.transfer_detail", transfer_id=transfer_id))
    t.issued_by = current_user.user_id
    t.issued_at = datetime.utcnow()
    t.dispatch_status = "in_transit"
    t.note = request.form.get("note", "").strip() or t.note
    ea = request.form.get("expected_arrival", "")
    if ea:
        try:
            t.expected_arrival = datetime.strptime(ea, "%Y-%m-%d").date()
        except ValueError:
            pass
    db.session.add(ActivityLog(
        actor_id=current_user.user_id, action_type="distribution_status",
        description=f"{t.ref} dispatched — {t.quantity:,} food packs en route to {t.to_office.office_name}",
        office_id=t.to_office_id, batch_id=t.batch_id,
    ))
    db.session.commit()
    flash(f"{t.ref} dispatched. Awaiting {t.to_office.area_covered}'s receipt confirmation.", "success")
    return redirect(url_for("pswdo.transfer_detail", transfer_id=transfer_id))


# ---------------------------------------------------------------------------
# Recommendations — PSWDO's read-only decision-support view. It does NOT run
# the model (manuscript: the provincial level "draws from city and municipality
# demand projections rather than generating a separate prediction model"). Each
# line carries its numbers so the reasoning is explainable (Molnar, 2022).
# ---------------------------------------------------------------------------

@pswdo_bp.route("/recommendations")
@login_required
@role_required("pswdo_admin", "system_admin")
def recommendations_page():
    active_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()
    _, warehouses, total_food_packs = _load_warehouses()
    depots = [w for w in warehouses if w["office"].office_type == "pswdo"]
    healthiest = max(depots, key=lambda w: w["food_pack_qty"], default=None)

    municipalities = []
    total_demand = total_shortfall = 0
    for lgu in TARGET_LGUS:
        office = Office.query.filter_by(office_type="cswdo", area_covered=lgu).first()
        breakdown, demand = _municipal_demand_for(office, active_event)
        fp = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first() if office else None
        on_hand = fp.quantity_available if fp else 0
        shortfall = max(demand - on_hand, 0)
        total_demand += demand
        total_shortfall += shortfall
        # any open stock request for this municipality?
        open_req = ReliefRequestBatch.query.filter(
            ReliefRequestBatch.office_id == (office.office_id if office else 0),
            ReliefRequestBatch.status.in_(("pending", "approved", "partially_approved")),
        ).order_by(ReliefRequestBatch.submitted_at.desc()).first() if office else None
        municipalities.append({
            "lgu": lgu, "office": office, "demand": demand, "on_hand": on_hand,
            "shortfall": shortfall, "coverage_pct": round(min(on_hand / demand * 100, 100)) if demand else 100,
            "barangay_count": len(breakdown), "open_request": open_req,
        })

    recs = []
    for m in sorted(municipalities, key=lambda x: x["shortfall"], reverse=True):
        if m["shortfall"] <= 0:
            continue
        src = healthiest["office"].office_name if healthiest else "a provincial depot"
        if m["open_request"] and m["open_request"].status == "pending":
            action = f"Stock request {m['open_request'].ref} is pending — approve up to {m['shortfall']:,} packs."
            link = url_for("pswdo.relief_request_detail", batch_id=m["open_request"].batch_id)
        elif m["open_request"]:
            action = f"Stock request {m['open_request'].ref} already approved — monitor the transfer."
            link = url_for("pswdo.relief_request_detail", batch_id=m["open_request"].batch_id)
        else:
            action = f"No request on file yet. Consider pre-positioning ~{m['shortfall']:,} packs from {src}."
            link = url_for("pswdo.relief_requests")
        recs.append({
            "type": "critical" if m["coverage_pct"] < 50 else "warning",
            "title": f"{m['lgu']}: {m['demand']:,} predicted demand vs {m['on_hand']:,} on hand → short {m['shortfall']:,}",
            "detail": action, "link": link,
        })
    for w in depots:
        if w["health"] == "Low":
            recs.append({
                "type": "warning",
                "title": f"{w['office'].office_name} stock low — {w['pct']:.0f}% of capacity ({w['food_pack_qty']:,} packs)",
                "detail": "Replenish this depot before it can't cover municipal requests.",
                "link": url_for("pswdo.warehouse_inventory"),
            })
    if not recs:
        recs.append({"type": "info", "title": "All municipal warehouses are covered",
                     "detail": f"Predicted demand {total_demand:,} packs is met by current municipal stock.", "link": None})

    return render_template(
        "pswdo/recommendations.html",
        active_event=active_event, municipalities=municipalities, recommendations=recs,
        total_demand=total_demand, total_shortfall=total_shortfall,
        total_food_packs=total_food_packs,
    )


def _filtered_distributions():
    """Shared filter logic for the distribution page and its CSV export."""
    today = date.today()
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = DistributionRecord.query.join(Barangay).join(AllocationRecord).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.source != "barangay_request",
    )
    today_query = base_query.filter(DistributionRecord.distribution_date == today)

    total_today = today_query.count()
    preparing_count = today_query.filter(DistributionRecord.dispatch_status == "preparing").count()
    in_transit_count = today_query.filter(DistributionRecord.dispatch_status == "in_transit").count()
    delivered_today = today_query.filter(DistributionRecord.dispatch_status == "delivered").all()
    delivered_count = len(delivered_today)
    delayed_count = today_query.filter(DistributionRecord.dispatch_status == "delayed").count()
    packs_released = sum(d.quantity_released for d in delivered_today)

    query = base_query
    if status_filter != "all":
        query = query.filter(DistributionRecord.dispatch_status == status_filter)
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(Barangay.city_municipality.ilike(like))

    records = query.order_by(DistributionRecord.distribution_date.desc()).all()

    return {
        "primary_event": primary_event,
        "today": today,
        "total_today": total_today,
        "preparing_count": preparing_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "delayed_count": delayed_count,
        "packs_released": packs_released,
        "status_filter": status_filter,
        "search_query": search_query,
        "records": records,
    }


def _eligible_for_distribution():
    """Approved relief requests with no DistributionRecord yet — the pool
    "New Distribution" can schedule from. Once scheduled, an allocation drops
    out of this list (see create_distribution) since dispatch-status changes
    happen afterward via the existing distribution detail actions, not by
    creating a second DistributionRecord.

    Each row is enriched with the fulfilling warehouse's CURRENT stock (not
    just what was available at approval time) so the New Distribution modal
    can double-check availability up front, before the user even submits —
    create_distribution() re-checks the same thing server-side regardless,
    since stock can still move between page load and submit."""
    allocations = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "approved",
        AllocationRecord.source != "barangay_request",
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


@pswdo_bp.route("/distribution")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution():
    ctx = _filtered_distributions()
    eligible_allocations = _eligible_for_distribution()

    # Municipality counts for the New Distribution wizard's first step —
    # ordered by TARGET_LGUS so the tile order stays stable across loads.
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
        today_str=date.today().isoformat(),
        **ctx,
    )


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

    # Re-check stock at schedule time, not just at approval time — the
    # fulfilling warehouse's stock can move (other releases, transfers) in
    # the gap between a request being approved and actually being scheduled.
    office = allocation.fulfilling_office
    inventory = WarehouseInventory.query.filter_by(
        office_id=office.office_id, item_type="food_pack"
    ).first() if office else None
    available = inventory.quantity_available if inventory else 0
    if not office or available < allocation.allocated_quantity:
        flash(
            f"Cannot schedule — {office.office_name if office else 'the fulfilling warehouse'} now has only "
            f"{available:,} food packs available, but this request needs {allocation.allocated_quantity:,}. "
            f"Transfer more stock in or re-approve with a lower quantity first.",
            "error"
        )
        return redirect(url_for("pswdo.distribution"))

    distribution_date = date.today()
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
            f"{allocation.barangay.city_municipality} — {allocation.allocated_quantity:,} food packs"
        ),
        office_id=allocation.fulfilling_office_id,
        barangay_id=allocation.barangay_id,
        distribution_id=rec.distribution_id,
    ))
    db.session.commit()

    flash(f"Distribution scheduled for {allocation.barangay.barangay_name}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=rec.distribution_id))


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


def _person_label(user, office):
    if not user:
        return "—"
    prefix = OFFICE_TYPE_PREFIX.get(office.office_type) if office else None
    return f"{prefix} - {user.name}" if prefix else user.name


def _get_target_scoped_distribution(distribution_id):
    rec = DistributionRecord.query.get_or_404(distribution_id)
    if rec.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return rec


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


@pswdo_bp.route("/distribution/<int:distribution_id>/advance", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def advance_distribution(distribution_id):
    """Handles the simple one-click transitions: preparing -> loaded -> dispatched -> in_transit."""
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
        rec.departure_time = datetime.now().time()

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


@pswdo_bp.route("/distribution/completed")
@login_required
@role_required("pswdo_admin", "system_admin")
def completed_deliveries():
    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
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


@pswdo_bp.route("/notifications")
@login_required
@role_required("pswdo_admin", "system_admin")
def notifications():
    category_filter = request.args.get("category", "all")

    # Restricted to PSWDO_NOTIFICATION_TYPES (NOTIFICATION_META minus damage
    # reports) — otherwise two kinds of rows leak into this feed: System
    # Administration rows (logins, user/office/barangay management — see
    # app.utils.log_admin_activity), which are is_read=True by design so they
    # wouldn't inflate the unread badge but still showed up in the list
    # itself as uncategorized "Other" entries; and damage_report_* rows,
    # which showed up correctly categorized but as dead-end, non-clickable
    # entries since PSWDO has no damage-report page — that review is
    # entirely CSWDO/MSWDO's job. Both belong elsewhere, not here.
    known_types = PSWDO_NOTIFICATION_TYPES
    base_scope = ActivityLog.action_type.in_(known_types)

    query = ActivityLog.query.filter(base_scope)
    if category_filter != "all":
        action_types = [k for k, v in NOTIFICATION_META.items() if v["category"] == category_filter]
        query = query.filter(ActivityLog.action_type.in_(action_types))

    unread_count = ActivityLog.query.filter(base_scope, ActivityLog.is_read.is_(False)).count()
    total_count = ActivityLog.query.filter(base_scope).count()

    per_page = 15
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

    # Opening the Notifications page is itself the "read" action — no per-item
    # or "Mark all as read" click needed. Unread rows still show highlighted on
    # this render (via was_unread) so the user sees what's new before it clears.
    if unread_count:
        ActivityLog.query.filter(
            base_scope, ActivityLog.is_read.is_(False)
        ).update({"is_read": True}, synchronize_session=False)
        db.session.commit()

    categories = [
        {"value": "all", "label": "All"},
        {"value": "relief_requests", "label": "Relief Requests"},
        {"value": "distribution", "label": "Distribution"},
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
    )


@pswdo_bp.route("/notifications/<int:log_id>/view")
@login_required
@role_required("pswdo_admin", "system_admin")
def view_notification(log_id):
    """The Notifications page's "View" link routes through here instead of
    linking to item.link directly, so opening a notification is what marks
    it read — no separate "Mark as read" click required."""
    log = ActivityLog.query.get_or_404(log_id)
    log.is_read = True
    db.session.commit()
    destination = _notification_view(log)["link"]
    return redirect(destination or url_for("pswdo.notifications"))


@pswdo_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def mark_all_notifications_read():
    known_types = PSWDO_NOTIFICATION_TYPES
    ActivityLog.query.filter(
        ActivityLog.action_type.in_(known_types), ActivityLog.is_read.is_(False)
    ).update({"is_read": True}, synchronize_session=False)
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for("pswdo.notifications"))


@pswdo_bp.route("/settings/profile")
@login_required
@role_required("pswdo_admin", "system_admin")
def profile_settings():
    return render_template("pswdo/profile_settings.html")


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