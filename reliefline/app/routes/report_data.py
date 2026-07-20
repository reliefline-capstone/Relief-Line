"""
Data-builder functions for the Reports feature. Each builder pulls real rows
from the same tables/helpers the rest of the app already uses (no synthetic
report numbers) and returns a plain {columns, rows, ...} dict, so a single
generic template/PDF/Excel renderer can present any of the 7 report types
without a per-type template.
"""
from datetime import date, datetime, timedelta

from app.extensions import db
from app.models.barangay import Barangay
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus

from app.routes.pswdo import (
    TARGET_LGUS, DISPATCH_STATUS_LABELS, PRIORITY_BY_STATUS,
    _load_warehouses, _lgu_burn_rate, _stock_recommendations,
    _relief_summary, _full_stock_movements,
)
from app.routes.prediction import _barangay_snapshot
from app.utils.roles import ROLE_LABELS

REPORT_TYPES = {
    "relief_requests": {
        "title": "Relief Request Report",
        "description": "All relief requests submitted by municipalities with approval status.",
        "icon": "clipboard",
    },
    "distribution": {
        "title": "Distribution Report",
        "description": "Complete history of all food pack deliveries per warehouse and destination.",
        "icon": "truck",
    },
    "warehouse_inventory": {
        "title": "Warehouse Inventory Report",
        "description": "Current inventory levels, remaining capacity, and low-stock items per warehouse.",
        "icon": "building",
    },
    "stock_movement": {
        "title": "Stock Movement Report",
        "description": "All incoming, outgoing stock movements and inter-warehouse transfers.",
        "icon": "package",
    },
    "municipality_summary": {
        "title": "Municipality Summary Report",
        "description": "Relief operations summary per municipality — families, requests, delivery status.",
        "icon": "map",
    },
    "typhoon_summary": {
        "title": "Typhoon Event Summary",
        "description": "Full operational summary for a single typhoon event from start to close.",
        "icon": "cloud-lightning",
    },
    "analytics": {
        "title": "Analytics Report",
        "description": "Demand forecast, burn rate analysis, warehouse forecast, and system recommendations.",
        "icon": "trending-up",
    },
}

STATUS_LABELS = {
    "pending": "Pending",
    "approved": "Approved",
    "released": "Released",
    "partially_approved": "Partially Approved",
    "rejected": "Rejected",
}


def _fmt_date(d):
    return d.strftime("%b %d, %Y") if d else "—"


def resolve_filters(args):
    """Shared filter parsing for the Reports listing page and every report type."""
    event_id = args.get("event_id", type=int)
    event = DisasterEvent.query.get(event_id) if event_id else None
    if not event:
        event = DisasterEvent.query.filter_by(status="active").order_by(
            DisasterEvent.start_date.desc()
        ).first()

    municipality = args.get("municipality", "all")
    if municipality not in TARGET_LGUS:
        municipality = "all"

    days = args.get("days", 30, type=int)
    if days not in (7, 30, 90):
        days = 30

    lgus = [municipality] if municipality != "all" else list(TARGET_LGUS)

    return {
        "event": event,
        "event_id": event.event_id if event else None,
        "municipality": municipality,
        "lgus": lgus,
        "days": days,
        "start_date": date.today() - timedelta(days=days),
    }


def _build_relief_requests(filters):
    q = AllocationRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(filters["lgus"]),
        AllocationRecord.allocation_date >= filters["start_date"],
    )
    if filters["event_id"]:
        q = q.filter(AllocationRecord.event_id == filters["event_id"])
    records = q.order_by(AllocationRecord.allocation_date.desc()).all()

    rows = []
    for i, r in enumerate(records, start=1):
        rows.append([
            i,
            r.barangay.city_municipality,
            f"RR-{r.allocation_date.year}-{r.allocation_id:03d}",
            _fmt_date(r.allocation_date),
            f"{r.predicted_quantity or 0:,}",
            f"{r.allocated_quantity:,}" if r.status in ("approved", "released") else "—",
            STATUS_LABELS.get(r.display_status, r.display_status.replace("_", " ").title()),
        ])
    return {
        "columns": ["#", "Municipality", "Request ID", "Date", "Requested Packs", "Approved Packs", "Status"],
        "rows": rows,
    }


def _build_distribution(filters):
    q = DistributionRecord.query.join(Barangay).filter(
        Barangay.city_municipality.in_(filters["lgus"]),
        DistributionRecord.distribution_date >= filters["start_date"],
    )
    if filters["event_id"]:
        q = q.join(AllocationRecord, DistributionRecord.allocation_id == AllocationRecord.allocation_id).filter(
            AllocationRecord.event_id == filters["event_id"]
        )
    records = q.order_by(DistributionRecord.distribution_date.desc()).all()

    rows = []
    for i, d in enumerate(records, start=1):
        fulfilling = d.allocation.fulfilling_office or d.allocation.office
        rows.append([
            i,
            f"D-{d.distribution_date.year}-{d.distribution_id:03d}",
            d.barangay.city_municipality,
            fulfilling.office_name if fulfilling else "—",
            f"{d.quantity_released:,}",
            d.vehicle.vehicle_name if d.vehicle else "Unassigned",
            d.driver.name if d.driver else "—",
            _fmt_date(d.distribution_date),
            DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
        ])
    return {
        "columns": ["#", "Distribution ID", "Municipality", "Warehouse", "Packs", "Vehicle", "Driver", "Date", "Status"],
        "rows": rows,
    }


def _build_warehouse_inventory(filters):
    active_events = DisasterEvent.query.filter_by(status="active").order_by(
        DisasterEvent.start_date.desc()
    ).all()
    all_offices, warehouses, total_food_packs = _load_warehouses()
    if filters["municipality"] != "all":
        warehouses = [
            w for w in warehouses
            if w["office"].office_type == "pswdo" or w["office"].area_covered == filters["municipality"]
        ]

    rows = []
    for i, w in enumerate(warehouses, start=1):
        burn = _lgu_burn_rate(w["office"], active_events)
        days_left = round(w["food_pack_qty"] / burn, 0) if burn else None
        rows.append([
            i,
            w["office"].office_name,
            w["office"].area_covered,
            f"{w['food_pack_qty']:,}",
            f"{w['capacity']:,}",
            f"{w['pct']:.0f}%",
            w["health"],
            f"{int(days_left)} days" if days_left is not None else "—",
        ])
    return {
        "columns": ["#", "Warehouse", "Municipality", "Food Packs", "Capacity", "% Capacity", "Health", "Days Remaining"],
        "rows": rows,
    }


def _build_stock_movement(filters):
    all_offices, _, _ = _load_warehouses()
    if filters["municipality"] != "all":
        office_ids = [
            o.office_id for o in all_offices
            if o.office_type == "pswdo" or o.area_covered == filters["municipality"]
        ]
    else:
        office_ids = [o.office_id for o in all_offices]

    movements = [m for m in _full_stock_movements(office_ids) if m["when"] and m["when"] >= filters["start_date"]]

    rows = []
    for i, m in enumerate(movements, start=1):
        rows.append([
            i, m["office_name"], m["direction"], f"{m['qty']:+,}", m["context"], _fmt_date(m["when"]),
        ])
    return {
        "columns": ["#", "Warehouse", "Direction", "Quantity", "Context", "Date"],
        "rows": rows,
    }


def _build_municipality_summary(filters):
    rows = []
    for i, lgu in enumerate(filters["lgus"], start=1):
        barangay_ids = [b.barangay_id for b in Barangay.query.filter_by(city_municipality=lgu).all()]
        summary = _relief_summary(barangay_ids, filters["event_id"])

        affected_families = 0
        if filters["event_id"]:
            affected_families = db.session.query(db.func.sum(BarangayDisasterStatus.affected_families)).filter(
                BarangayDisasterStatus.barangay_id.in_(barangay_ids),
                BarangayDisasterStatus.event_id == filters["event_id"],
            ).scalar() or 0

        requests_submitted = AllocationRecord.query.filter(
            AllocationRecord.barangay_id.in_(barangay_ids),
            AllocationRecord.allocation_date >= filters["start_date"],
        ).count()
        pct_delivered = round((summary["released"] / summary["requested"]) * 100) if summary["requested"] else 0

        rows.append([
            i, lgu, f"{affected_families:,}", requests_submitted,
            f"{summary['requested']:,}", f"{summary['released']:,}", f"{pct_delivered}%",
        ])
    return {
        "columns": ["#", "Municipality", "Affected Families", "Requests Submitted", "Packs Requested", "Packs Delivered", "% Delivered"],
        "rows": rows,
    }


def _build_typhoon_summary(filters):
    event = filters["event"]
    if not event:
        return {
            "columns": ["Metric", "Value"], "rows": [],
            "notes": ["No disaster event on record for the selected filters."],
        }

    barangay_ids = [b.barangay_id for b in Barangay.query.filter(Barangay.city_municipality.in_(filters["lgus"])).all()]
    statuses = BarangayDisasterStatus.query.filter(
        BarangayDisasterStatus.event_id == event.event_id,
        BarangayDisasterStatus.barangay_id.in_(barangay_ids),
    ).all()
    affected_barangays = len([s for s in statuses if s.status != "normal"])
    affected_families = sum(s.affected_families for s in statuses)

    summary = _relief_summary(barangay_ids, event.event_id)
    requests_submitted = AllocationRecord.query.filter(
        AllocationRecord.event_id == event.event_id,
        AllocationRecord.barangay_id.in_(barangay_ids),
    ).count()
    delivered_count = DistributionRecord.query.join(AllocationRecord).filter(
        AllocationRecord.event_id == event.event_id,
        DistributionRecord.dispatch_status == "delivered",
        AllocationRecord.barangay_id.in_(barangay_ids),
    ).count()
    warehouses_involved = db.session.query(AllocationRecord.fulfilling_office_id).filter(
        AllocationRecord.event_id == event.event_id,
        AllocationRecord.fulfilling_office_id.isnot(None),
        AllocationRecord.barangay_id.in_(barangay_ids),
    ).distinct().count()

    rows = [
        ["Event Name", event.event_name],
        ["Type", event.event_type.title()],
        ["Status", event.status.title()],
        ["Start Date", _fmt_date(event.start_date)],
        ["End Date", _fmt_date(event.end_date) if event.end_date else "Ongoing"],
        ["Barangays Affected", str(affected_barangays)],
        ["Affected Families", f"{affected_families:,}"],
        ["Requests Submitted", str(requests_submitted)],
        ["Packs Requested", f"{summary['requested']:,}"],
        ["Packs Approved", f"{summary['approved']:,}"],
        ["Packs Released / Delivered", f"{summary['released']:,}"],
        ["Completed Deliveries", str(delivered_count)],
        ["Warehouses Involved", str(warehouses_involved)],
    ]
    return {"columns": ["Metric", "Value"], "rows": rows}


def _build_analytics(filters):
    barangays = Barangay.query.filter(Barangay.city_municipality.in_(filters["lgus"])).order_by(
        Barangay.city_municipality, Barangay.barangay_name
    ).all()
    status_map = {}
    if filters["event_id"]:
        status_rows = BarangayDisasterStatus.query.filter_by(event_id=filters["event_id"]).all()
        status_map = {r.barangay_id: r for r in status_rows}

    snapshots = [_barangay_snapshot(b, status_map.get(b.barangay_id), filters["event_id"]) for b in barangays]

    rows = []
    for i, lgu in enumerate(filters["lgus"], start=1):
        lgu_snaps = [s for s in snapshots if s["lgu"] == lgu]
        packs_needed = sum(s["packs_needed"] for s in lgu_snaps)
        delivered = sum(s["released"] for s in lgu_snaps)
        remaining = max(packs_needed - delivered, 0)
        pct_done = round((delivered / packs_needed) * 100) if packs_needed else 0
        worst_rank = max((s["priority_rank"] for s in lgu_snaps), default=0)
        worst_label = next((v["label"] for v in PRIORITY_BY_STATUS.values() if v["rank"] == worst_rank), "Unrated")
        rows.append([i, lgu, f"{packs_needed:,}", f"{delivered:,}", f"{remaining:,}", f"{pct_done}%", worst_label])

    _, warehouses, _ = _load_warehouses()
    notes = [f"{rec['title']} — {rec['detail']}" for rec in _stock_recommendations(warehouses)]
    if not notes:
        notes = ["No stock-transfer recommendations at this time — warehouse levels are healthy."]

    return {
        "columns": ["#", "Municipality", "Packs Needed", "Delivered", "Remaining", "% Done", "Priority"],
        "rows": rows,
        "notes": notes,
    }


BUILDERS = {
    "relief_requests": _build_relief_requests,
    "distribution": _build_distribution,
    "warehouse_inventory": _build_warehouse_inventory,
    "stock_movement": _build_stock_movement,
    "municipality_summary": _build_municipality_summary,
    "typhoon_summary": _build_typhoon_summary,
    "analytics": _build_analytics,
}


def build_report(report_type, filters, user=None):
    if report_type not in REPORT_TYPES:
        return None
    info = REPORT_TYPES[report_type]
    data = BUILDERS[report_type](filters)
    coverage = "Current Snapshot" if report_type == "warehouse_inventory" else f"Last {filters['days']} Days"

    return {
        "report_type": report_type,
        "title": info["title"],
        "description": info["description"],
        "columns": data["columns"],
        "rows": data["rows"],
        "record_count": len(data["rows"]),
        "notes": data.get("notes"),
        "coverage": coverage,
        "event_name": filters["event"].event_name if filters["event"] else "No active event",
        "municipality_label": filters["municipality"] if filters["municipality"] != "all" else "All Municipalities",
        "date_generated": datetime.now(),
        "prepared_by": user.name if user else "PSWDO Officer",
        "prepared_by_role": ROLE_LABELS.get(user.role, user.role) if user else "PSWDO Officer",
    }
