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
from app.models.logistics import Vehicle, Driver, WarehouseTransfer
from app.models.user import User

pswdo_bp = Blueprint("pswdo", __name__)

TARGET_LGUS = ["Urdaneta City", "Santa Barbara", "Calasiao"]

WAREHOUSE_HEALTHY = 0.70
WAREHOUSE_MODERATE = 0.30

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
    "distribution_status": {"icon": "truck", "color": "#2c5aa0", "category": "distribution", "category_label": "Distribution"},
    "distribution_delivered": {"icon": "check-circle", "color": "#1e8449", "category": "distribution", "category_label": "Distribution"},
    "warehouse_transfer_completed": {"icon": "rotate-ccw", "color": "#6c5ce7", "category": "warehouse", "category_label": "Warehouse"},
}
DEFAULT_NOTIFICATION_META = {"icon": "bell", "color": "#8a94a6", "category": "other", "category_label": "Other"}

NOTIFICATION_LINKS = {
    "relief_requests": lambda log: url_for("pswdo.relief_requests", municipality=log.barangay.city_municipality) if log.barangay else url_for("pswdo.relief_requests"),
    "distribution": lambda log: url_for("pswdo.distribution", q=log.barangay.city_municipality) if log.barangay else url_for("pswdo.distribution"),
    "warehouse": lambda log: url_for("pswdo.warehouse_stock_movements"),
}


def _notification_view(log):
    meta = NOTIFICATION_META.get(log.action_type, DEFAULT_NOTIFICATION_META)
    link_fn = NOTIFICATION_LINKS.get(meta["category"])
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
    if filename not in _geojson_cache:
        path = os.path.join(current_app.root_path, "static", "geo", filename)
        with open(path) as f:
            _geojson_cache[filename] = json.load(f)
    return _geojson_cache[filename]


def _bbox_center(geometry):
    """Bounding-box midpoint — stable for marker placement even on concave
    polygons, where a naive vertex-average centroid could land oddly."""
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
            return _bbox_center(feature["geometry"])
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
        else:
            props = {"name": name, "has_data": False, "status": None, "priority_tier": "unrated"}
        features.append({"type": "Feature", "properties": props, "geometry": feature["geometry"]})

    return {"type": "FeatureCollection", "features": features}


def _target_barangay_centroid(lgu, barangay_name):
    raw = _load_geojson_file(GIS_LGU_FILES[lgu])
    for feature in raw["features"]:
        if feature["properties"]["name"] == barangay_name:
            return _bbox_center(feature["geometry"])
    return None


def _relief_summary(barangay_ids, event_id):
    """Food-pack requested/approved/released rollup for a set of barangays,
    built entirely from AllocationRecord + DistributionRecord — no invented
    fields (this backs the GIS map's Relief Statistics card)."""
    empty = {"requested": 0, "approved": 0, "released": 0, "remaining": 0, "progress_pct": 0}
    if not barangay_ids:
        return empty

    alloc_query = AllocationRecord.query.filter(AllocationRecord.barangay_id.in_(barangay_ids))
    if event_id:
        alloc_query = alloc_query.filter(AllocationRecord.event_id == event_id)
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

        if pct >= WAREHOUSE_HEALTHY * 100:
            health = "Healthy"
        elif pct >= WAREHOUSE_MODERATE * 100:
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
                })

    if type_filter in ("all", "received"):
        log_q = WarehouseStockLog.query.filter(
            WarehouseStockLog.office_id.in_(office_ids),
            WarehouseStockLog.delta > 0
        )
        if filter_date:
            log_q = log_q.filter(db.func.date(WarehouseStockLog.created_at) == filter_date)
        for log in log_q.order_by(WarehouseStockLog.created_at.desc()).all():
            movements.append({
                "office_id": log.office_id,
                "office_name": log.office.office_name,
                "direction": "Received",
                "qty": log.delta,
                "context": log.reason or f"{log.item_name} stock update",
                "when": log.created_at.date(),
                "sort_at": log.created_at,
            })

    movements.sort(key=lambda m: m["sort_at"], reverse=True)
    return movements


def _recent_stock_movements(office_ids, limit=6):
    # Over-fetch on each side before merging — otherwise a same-day tie between
    # a release and a transfer can get the transfer truncated before the merge
    # even sees it (list.sort() is stable, so pre-limited insertion order wins).
    return _full_stock_movements(office_ids)[:limit]


@pswdo_bp.route("/dashboard")
@login_required
@role_required("pswdo_admin", "system_admin")
def dashboard():
    today = date.today()
    now = datetime.now()

    # Active typhoon/disaster events
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    primary_event = active_events[0] if active_events else None

    all_offices, warehouses, total_food_packs = _load_warehouses()

    # CSWDO offices only — scope for relief operations (3 target LGUs)
    cswdo_offices = [o for o in all_offices if o.office_type == "cswdo"]
    office_ids = [o.office_id for o in cswdo_offices]

    # Pending allocation requests (a rejected request keeps status="pending" but
    # carries rejection_reason, so it must be excluded here — see AllocationRecord.display_status)
    pending_requests = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).order_by(AllocationRecord.allocation_date.desc()).limit(6).all()

    pending_requests_count = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).count()

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

    # Today's Distribution Progress (3 target LGUs, active event)
    today_allocations = []
    if primary_event:
        today_allocations = AllocationRecord.query.join(Barangay).filter(
            Barangay.city_municipality.in_(TARGET_LGUS),
            AllocationRecord.status.in_(["approved", "released"]),
            AllocationRecord.event_id == primary_event.event_id
        ).all()

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
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(4).all()
    notifications = ActivityLog.query.filter(ActivityLog.is_read.is_(False)).order_by(
        ActivityLog.created_at.desc()
    ).limit(3).all()

    return render_template(
        "pswdo/dashboard.html",
        active_events=active_events,
        primary_event=primary_event,
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
        now=now
    )


@pswdo_bp.route("/warehouse-inventory")
@login_required
@role_required("pswdo_admin", "system_admin")
def warehouse_inventory():
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()

    all_offices, warehouses, total_food_packs = _load_warehouses()
    office_ids = [o.office_id for o in all_offices]

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

    return render_template(
        "pswdo/warehouse_inventory.html",
        warehouses=warehouses,
        total_food_packs=total_food_packs,
        low_stock_count=low_stock_count,
        recommendations=recommendations,
        transfers_today_count=transfers_today_count,
        recent_movements=recent_movements,
        default_office_id=warehouses[0]["office"].office_id if warehouses else None,
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
    # same pattern as the existing "Warehouse A"/"Warehouse C" seed offices.
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

    if pct >= WAREHOUSE_HEALTHY * 100:
        health = "Healthy"
    elif pct >= WAREHOUSE_MODERATE * 100:
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
            delta=quantity, reason="Initial stock", updated_by=current_user.user_id,
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

    delta = new_quantity - item.quantity_available
    item.quantity_available = new_quantity
    if unit:
        item.unit = unit
    item.updated_by = current_user.user_id

    if delta != 0:
        db.session.add(WarehouseStockLog(
            office_id=item.office_id, item_type=item.item_type, item_name=item.item_name,
            delta=delta, reason=reason, updated_by=current_user.user_id,
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

    coverage_range = f"{filters['start_date'].strftime('%b %d')} - {date.today().strftime('%b %d, %Y')}"

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
        target_lgus=TARGET_LGUS,
    )


@pswdo_bp.route("/gis-map/data")
@login_required
@role_required("pswdo_admin", "cswdo_admin", "system_admin")
def gis_map_data():
    event_id = _resolve_event_id(request.args.get("event_id", type=int))

    # Barangay-level layer — the only areas the manuscript's predictive/status
    # model actually covers. Everything else on the map is neutral context.
    target_features = []
    for lgu in TARGET_LGUS:
        fc = _target_barangay_geojson(lgu, event_id)
        for feature in fc["features"]:
            feature["properties"]["lgu"] = lgu
            target_features.append(feature)
    target_barangays_geojson = {"type": "FeatureCollection", "features": target_features}

    # Province context — geographic orientation only, no disaster data implied.
    province_geojson = _load_geojson_file("pangasinan_municipalities.json")
    target_by_normalized = {_normalize_muni_name(l).lower(): l for l in TARGET_LGUS}
    province_features = []
    for feature in province_geojson["features"]:
        name = feature["properties"]["name"]
        matched_lgu = target_by_normalized.get(_normalize_muni_name(name).lower())
        province_features.append({
            "type": "Feature",
            "properties": {"name": name, "is_target": matched_lgu is not None, "lgu": matched_lgu},
            "geometry": feature["geometry"],
        })
    province_context_geojson = {"type": "FeatureCollection", "features": province_features}

    # Warehouses — real Office + WarehouseInventory data, placed at their LGU's
    # approximate centroid (not a precise street address).
    all_offices, warehouses, total_food_packs = _load_warehouses()
    warehouse_markers = []
    for w in warehouses:
        centroid = _municipality_centroid(w["office"].area_covered)
        if not centroid:
            continue
        warehouse_markers.append({
            "name": w["office"].office_name,
            "area_covered": w["office"].area_covered,
            "lat": centroid[0], "lng": centroid[1],
            "health": w["health"], "pct": w["pct"],
            "food_pack_qty": w["food_pack_qty"], "capacity": w["capacity"],
        })

    # Schematic in-transit indicators — a straight line between known warehouse
    # and barangay centroids, NOT a real road route (excluded by manuscript scope).
    in_transit_lines = []
    in_transit_records = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS),
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

    # Side-panel stats — real counts scoped to the 3 target LGUs only.
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
        Barangay.city_municipality.in_(TARGET_LGUS),
        DistributionRecord.dispatch_status.in_(["preparing", "loaded", "dispatched", "in_transit"])
    ).order_by(DistributionRecord.distribution_date.desc()).limit(10).all()

    routes_table = []
    for d in active_routes:
        allocation = d.allocation
        office = allocation.fulfilling_office if allocation else None
        routes_table.append({
            "distribution_id": d.distribution_id,
            "from_office": office.office_name if office else "—",
            "to_barangay": d.barangay.barangay_name,
            "to_municipality": d.barangay.city_municipality,
            "vehicle": d.vehicle.vehicle_name if d.vehicle else "—",
            "driver": d.driver.name if d.driver else "—",
            "packs": d.quantity_released,
            "status": d.dispatch_status,
            "status_label": DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
            "eta": d.expected_arrival_time.strftime("%I:%M %p") if d.expected_arrival_time else "—",
        })

    # Per-municipality rollups — backs the GIS map's drill-down "Municipality
    # Information" panel. Built entirely from data already computed above plus
    # real AllocationRecord/DistributionRecord aggregates (no invented fields).
    municipalities = []
    for lgu in TARGET_LGUS:
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
                "vehicle": current_route.vehicle.vehicle_name if current_route.vehicle else "—",
                "driver": current_route.driver.name if current_route.driver else "—",
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

        municipalities.append({
            "lgu": lgu,
            "total_barangays": len(lgu_props),
            "affected_barangays": len(lgu_affected),
            "total_affected_families": sum(p["affected_families"] for p in lgu_affected),
            "total_population": sum(p["population"] for p in lgu_props),
            "status_label": worst_tier["label"],
            "status_tier": worst_tier["tier"],
            "relief": _relief_summary(barangay_ids, event_id),
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
    if barangay.city_municipality not in TARGET_LGUS:
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
@role_required("pswdo_admin", "system_admin")
def gis_map_municipality_report(lgu):
    if lgu not in TARGET_LGUS:
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


def _filtered_relief_requests():
    """Shared filter/sort logic for the relief requests page and its CSV export."""
    status_filter = request.args.get("status", "all")
    municipality_filter = request.args.get("municipality", "all")
    priority_filter = request.args.get("priority", "all")
    date_filter = request.args.get("date", "")
    search_query = request.args.get("q", "").strip()

    active_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS)
    )

    total_count = base_query.count()
    pending_count = base_query.filter(
        AllocationRecord.status == "pending",
        AllocationRecord.rejection_reason.is_(None)
    ).count()
    approved_count = base_query.filter(AllocationRecord.status == "approved").count()
    released_count = base_query.filter(AllocationRecord.status == "released").count()

    query = base_query
    if status_filter != "all":
        query = query.filter(AllocationRecord.status == status_filter)
    if municipality_filter != "all":
        query = query.filter(Barangay.city_municipality == municipality_filter)
    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(AllocationRecord.allocation_date == parsed_date)
        except ValueError:
            pass
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Barangay.city_municipality.ilike(like),
                Barangay.barangay_name.ilike(like),
            )
        )

    matching_requests = query.order_by(AllocationRecord.allocation_date.desc()).all()

    # Priority lookup, scoped to the active event (falls back to "Unrated" otherwise)
    status_map = {}
    if active_event:
        statuses = BarangayDisasterStatus.query.filter_by(event_id=active_event.event_id).all()
        status_map = {s.barangay_id: s.status for s in statuses}

    enriched = []
    for req in matching_requests:
        priority = _priority_info(status_map.get(req.barangay_id))
        enriched.append((req, priority))

    if priority_filter != "all":
        enriched = [pair for pair in enriched if pair[1]["tier"] == priority_filter]

    enriched.sort(key=lambda pair: (pair[1]["rank"], pair[0].allocation_date), reverse=True)

    return {
        "enriched": enriched,
        "active_event": active_event,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "released_count": released_count,
        "total_count": total_count,
        "status_filter": status_filter,
        "municipality_filter": municipality_filter,
        "priority_filter": priority_filter,
        "date_filter": date_filter,
        "search_query": search_query,
    }


@pswdo_bp.route("/relief-requests")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_requests():
    ctx = _filtered_relief_requests()
    enriched = ctx["enriched"]

    per_page = 10
    total_filtered = len(enriched)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    page_items = enriched[start:start + per_page]

    return render_template(
        "pswdo/relief_requests.html",
        active_event=ctx["active_event"],
        pending_count=ctx["pending_count"],
        approved_count=ctx["approved_count"],
        released_count=ctx["released_count"],
        total_count=ctx["total_count"],
        total_filtered=total_filtered,
        status_filter=ctx["status_filter"],
        municipality_filter=ctx["municipality_filter"],
        priority_filter=ctx["priority_filter"],
        date_filter=ctx["date_filter"],
        search_query=ctx["search_query"],
        target_lgus=TARGET_LGUS,
        requests=page_items,
        page=page,
        total_pages=total_pages,
    )


@pswdo_bp.route("/relief-requests/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_relief_requests():
    ctx = _filtered_relief_requests()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Municipality", "Barangay", "Request ID", "Typhoon Event",
        "Requested Packs", "Priority", "Date", "Status"
    ])
    for req, priority in ctx["enriched"]:
        writer.writerow([
            req.barangay.city_municipality,
            req.barangay.barangay_name,
            f"RR-{req.allocation_date.year}-{req.allocation_id:03d}",
            req.event.event_name if req.event else (req.disaster_event or ""),
            req.predicted_quantity,
            priority["label"],
            req.allocation_date.isoformat(),
            req.status,
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=relief_requests.csv"},
    )


def _urgency_score(barangay, status_key, predicted_quantity, municipal_available):
    """
    0-100 score, weighted from real fields since there's no urgency column in the
    schema: disaster status tier (40%), barangay disaster_risk_index (20%),
    poverty_incidence (15%), past_calamity_freq (10%), and the requested-vs-available
    stock gap at the municipal office (15%).
    """
    rank = _priority_info(status_key)["rank"]  # 0-4
    status_component = (rank / 4) * 40
    risk_component = min(float(barangay.disaster_risk_index or 0) / 10, 1) * 20
    poverty_component = min(float(barangay.poverty_incidence or 0) / 100, 1) * 15
    calamity_component = min((barangay.past_calamity_freq or 0) / 10, 1) * 10

    if predicted_quantity > 0:
        gap = max(0, (predicted_quantity - municipal_available) / predicted_quantity)
    else:
        gap = 0
    stock_component = gap * 15

    return round(status_component + risk_component + poverty_component + calamity_component + stock_component)


def _get_target_scoped_request(allocation_id):
    req = AllocationRecord.query.get_or_404(allocation_id)
    if req.barangay.city_municipality not in TARGET_LGUS:
        abort(404)
    return req


@pswdo_bp.route("/relief-requests/<int:allocation_id>")
@login_required
@role_required("pswdo_admin", "system_admin")
def relief_request_detail(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    status_key = None
    affected_families = 0
    if req.event_id:
        bs = BarangayDisasterStatus.query.filter_by(
            barangay_id=req.barangay_id, event_id=req.event_id
        ).first()
        if bs:
            status_key = bs.status
            affected_families = bs.affected_families

    priority = _priority_info(status_key)

    affected_barangays_count = 0
    if req.event_id:
        affected_barangays_count = BarangayDisasterStatus.query.join(Barangay).filter(
            BarangayDisasterStatus.event_id == req.event_id,
            BarangayDisasterStatus.status != "normal",
            Barangay.city_municipality == req.barangay.city_municipality,
        ).count()

    # The requesting municipality's own office stock, for the inventory-gap comparison
    municipal_office = req.office
    municipal_inventory = None
    if municipal_office:
        municipal_inventory = WarehouseInventory.query.filter_by(
            office_id=municipal_office.office_id, item_type="food_pack"
        ).first()
    municipal_available = municipal_inventory.quantity_available if municipal_inventory else 0
    municipal_capacity = municipal_office.capacity_food_pack if municipal_office else 20000

    _, warehouses, total_food_packs = _load_warehouses()

    urgency_score = _urgency_score(req.barangay, status_key, req.predicted_quantity, municipal_available)
    suggested_allocation = min(req.predicted_quantity, total_food_packs)
    enough_stock = total_food_packs >= req.predicted_quantity

    # Fixed 2-day SLA heuristic off the real allocation_date, purely for the deadline hint
    deadline_label, deadline_state = None, None
    if req.display_status == "pending":
        days_left = (req.allocation_date + timedelta(days=2) - date.today()).days
        if days_left < 0:
            deadline_label, deadline_state = "Overdue", "overdue"
        elif days_left == 0:
            deadline_label, deadline_state = "Today", "today"
        else:
            deadline_label, deadline_state = f"In {days_left} day{'s' if days_left != 1 else ''}", "upcoming"

    fulfillable_warehouses = [w for w in warehouses if w["food_pack_qty"] > 0]

    return render_template(
        "pswdo/relief_request_detail.html",
        req=req,
        priority=priority,
        affected_families=affected_families,
        affected_barangays_count=affected_barangays_count,
        municipal_office=municipal_office,
        municipal_available=municipal_available,
        municipal_capacity=municipal_capacity,
        total_food_packs=total_food_packs,
        urgency_score=urgency_score,
        suggested_allocation=suggested_allocation,
        enough_stock=enough_stock,
        deadline_label=deadline_label,
        deadline_state=deadline_state,
        fulfillable_warehouses=fulfillable_warehouses,
    )


@pswdo_bp.route("/relief-requests/<int:allocation_id>/approve", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def approve_relief_request(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    if req.display_status != "pending":
        flash("This request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    office_id = request.form.get("fulfilling_office_id", type=int)
    quantity = request.form.get("quantity", type=int)
    expected_delivery = request.form.get("expected_delivery_date", "")
    remarks = request.form.get("remarks", "").strip()

    office = Office.query.get(office_id) if office_id else None
    if not office:
        flash("Select a warehouse to fulfill this request.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    if not quantity or quantity <= 0 or quantity > req.predicted_quantity:
        flash(f"Quantity must be between 1 and {req.predicted_quantity:,}.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    inventory = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
    available = inventory.quantity_available if inventory else 0
    if quantity > available:
        flash(f"{office.office_name} only has {available:,} food packs available.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    req.status = "approved"
    req.allocated_quantity = quantity
    req.fulfilling_office_id = office.office_id
    req.remarks = remarks or None
    req.rejection_reason = None
    req.decided_by = current_user.user_id
    if expected_delivery:
        try:
            req.expected_delivery_date = datetime.strptime(expected_delivery, "%Y-%m-%d").date()
        except ValueError:
            pass

    inventory.quantity_available -= quantity

    label = "Partially approved" if quantity < req.predicted_quantity else "Approved"
    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="allocation_approved",
        description=f"{label} {quantity:,} food packs for {req.barangay.city_municipality} from {office.office_name}",
        office_id=office.office_id,
        barangay_id=req.barangay_id,
    ))

    db.session.commit()
    flash(f"{label}: {quantity:,} food packs allocated to {req.barangay.city_municipality}.", "success")
    return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))


@pswdo_bp.route("/relief-requests/<int:allocation_id>/reject", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def reject_relief_request(allocation_id):
    req = _get_target_scoped_request(allocation_id)

    if req.display_status != "pending":
        flash("This request has already been decided.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("A reason is required to reject a request.", "error")
        return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))

    req.rejection_reason = reason
    req.decided_by = current_user.user_id
    db.session.add(ActivityLog(
        actor_id=current_user.user_id,
        action_type="allocation_rejected",
        description=f"Rejected relief request from {req.barangay.city_municipality}: {reason}",
        office_id=req.office_id,
        barangay_id=req.barangay_id,
    ))
    db.session.commit()
    flash(f"Request from {req.barangay.city_municipality} has been rejected.", "success")
    return redirect(url_for("pswdo.relief_request_detail", allocation_id=allocation_id))


def _filtered_distributions():
    """Shared filter logic for the distribution page and its CSV export."""
    today = date.today()
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    primary_event = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).first()

    base_query = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(TARGET_LGUS)
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


@pswdo_bp.route("/distribution")
@login_required
@role_required("pswdo_admin", "system_admin")
def distribution():
    ctx = _filtered_distributions()
    return render_template(
        "pswdo/distribution.html",
        dispatch_labels=DISPATCH_STATUS_LABELS,
        **ctx,
    )


@pswdo_bp.route("/distribution/export")
@login_required
@role_required("pswdo_admin", "system_admin")
def export_distribution():
    ctx = _filtered_distributions()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Distribution ID", "Request ID", "Municipality", "Warehouse",
        "Packs", "Vehicle", "Driver", "Date", "Status"
    ])
    for rec in ctx["records"]:
        fulfilling = rec.allocation.fulfilling_office or rec.allocation.office
        writer.writerow([
            f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}",
            f"RR-{rec.allocation.allocation_date.year}-{rec.allocation.allocation_id:03d}",
            rec.barangay.city_municipality,
            fulfilling.office_name if fulfilling else "",
            rec.quantity_released,
            rec.vehicle.vehicle_name if rec.vehicle else "Unassigned",
            rec.driver.name if rec.driver else "",
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

    vehicles = Vehicle.query.order_by(Vehicle.vehicle_name).all()
    drivers = Driver.query.order_by(Driver.name).all()

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
        vehicles=vehicles,
        drivers=drivers,
        dispatch_steps=DISPATCH_STEPS,
        step_labels=STEP_LABELS,
        current_index=current_index,
        route_progress=route_progress,
        dispatch_labels=DISPATCH_STATUS_LABELS,
        requested_by_label=_person_label(alloc.submitted_by, alloc.office),
        approved_by_label=_person_label(alloc.decided_by_user, alloc.fulfilling_office or alloc.office),
        attachments=attachments,
    )


@pswdo_bp.route("/distribution/<int:distribution_id>/assign-vehicle", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def assign_distribution_vehicle(distribution_id):
    rec = _get_target_scoped_distribution(distribution_id)

    vehicle_id = request.form.get("vehicle_id", type=int)
    driver_id = request.form.get("driver_id", type=int)
    plate_number = request.form.get("plate_number", "").strip()
    capacity = request.form.get("capacity_packs", type=int)

    vehicle = Vehicle.query.get(vehicle_id) if vehicle_id else None
    driver = Driver.query.get(driver_id) if driver_id else None
    if not vehicle or not driver:
        flash("Select a vehicle and a driver.", "error")
        return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))

    if plate_number:
        vehicle.plate_number = plate_number
    if capacity:
        vehicle.capacity_packs = capacity

    rec.vehicle_id = vehicle.vehicle_id
    rec.driver_id = driver.driver_id
    db.session.commit()
    flash(f"Assigned {vehicle.vehicle_name} with driver {driver.name}.", "success")
    return redirect(url_for("pswdo.distribution_detail", distribution_id=distribution_id))


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

    if target == "dispatched" and not (rec.vehicle_id and rec.driver_id):
        flash("Assign a vehicle and driver before dispatching.", "error")
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
    status_filter = request.args.get("status", "all")

    query = ActivityLog.query
    if category_filter != "all":
        action_types = [k for k, v in NOTIFICATION_META.items() if v["category"] == category_filter]
        query = query.filter(ActivityLog.action_type.in_(action_types))
    if status_filter == "unread":
        query = query.filter(ActivityLog.is_read.is_(False))

    unread_count = ActivityLog.query.filter(ActivityLog.is_read.is_(False)).count()
    total_count = ActivityLog.query.count()

    per_page = 15
    all_matching = query.order_by(ActivityLog.created_at.desc()).all()
    total_filtered = len(all_matching)
    total_pages = max((total_filtered + per_page - 1) // per_page, 1)
    page = max(request.args.get("page", 1, type=int), 1)
    page = min(page, total_pages)
    page_items = [_notification_view(log) for log in all_matching[(page - 1) * per_page: page * per_page]]

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
        status_filter=status_filter,
        categories=categories,
        page=page,
        total_pages=total_pages,
    )


@pswdo_bp.route("/notifications/<int:log_id>/read", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def mark_notification_read(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    log.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("pswdo.notifications"))


@pswdo_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@role_required("pswdo_admin", "system_admin")
def mark_all_notifications_read():
    ActivityLog.query.filter(ActivityLog.is_read.is_(False)).update({"is_read": True})
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