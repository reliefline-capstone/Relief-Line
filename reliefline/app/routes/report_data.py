# Collects the data for every PDF/Excel report.

import os
import re
from datetime import date, timedelta

from flask import current_app

from app.utils.timezone import ph_now, ph_today
from app.utils.stock_labels import stock_log_label

from app.extensions import db
from app.models.barangay import Barangay
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.barangay_report import BarangayReport

from app.routes.pswdo import (
    TARGET_LGUS, DISPATCH_STATUS_LABELS, PRIORITY_BY_STATUS,
    _load_warehouses, _lgu_burn_rate, _stock_recommendations,
    _relief_summary, _full_stock_movements,
)
from app.routes.prediction import _barangay_snapshot
from app.utils.roles import ROLE_LABELS


# The official name forms of a municipality (e.g. 'Urdaneta City' -> 'City of Urdaneta').
def lgu_names(lgu):
    name = (lgu or "").strip()
    lowered = name.lower()
    if lowered.endswith(" city"):
        return f"City of {name[:-5]}", "City"
    if lowered.startswith("city of "):
        return name, "City"
    return f"Municipality of {name}", "Municipal"


PROVINCE_SEAL = "img/province-seal.png"
LGU_LOGOS = {
    "Urdaneta City": "img/lgu/urdaneta.png",
    "Santa Barbara": "img/lgu/santa-barbara.png",
    "Calasiao": "img/lgu/calasiao.png",
}


# Which official seals go on the left and right of the letterhead.
def _seals(lgu=None):
    logo = LGU_LOGOS.get(lgu) if lgu else None
    if logo:
        return {"logo_left": logo, "logo_right": PROVINCE_SEAL}
    return {"logo_left": PROVINCE_SEAL, "logo_right": None}


# Turns a name into a simple file-name form (e.g. 'Santa Barbara' -> 'santa-barbara').
def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


# Finds a barangay's own seal image, if one exists in the app's files.
def barangay_logo(barangay):
    rel = f"img/barangay/{_slug(barangay.city_municipality)}/{_slug(barangay.barangay_name)}.png"
    return rel if os.path.exists(os.path.join(current_app.static_folder, *rel.split("/"))) else None


# The seals for a barangay letterhead (barangay seal + municipal seal).
def _barangay_seals(barangay):
    logo = barangay_logo(barangay)
    if logo:
        return {"logo_left": logo, "logo_right": LGU_LOGOS.get(barangay.city_municipality) or PROVINCE_SEAL}
    return _seals(barangay.city_municipality)


# The blank 'Prepared By' signature line.
def _preparer(user, fallback_position):
    return {"label": "Prepared By", "name": "", "position": "Signature over Printed Name"}


# Builds the report letterhead: 'Republic of the Philippines', province, municipality/barangay,
# the office name, seals and signature lines.
def build_letterhead(user=None, barangay=None):
    lines = ["Republic of the Philippines", "Province of Pangasinan"]
    if barangay is not None:
        lgu_line, _ = lgu_names(barangay.city_municipality)
        lines += [lgu_line, f"Barangay {barangay.barangay_name}"]
        return {
            "lines": lines,
            "office": "Office of the Punong Barangay",
            "place": f"Brgy. {barangay.barangay_name}, {barangay.city_municipality}",
            **_barangay_seals(barangay),
            "signatories": [
                _preparer(user, "Barangay Secretary"),
                {"label": "Approved By", "name": "", "position": "Punong Barangay"},
            ],
        }
    office = getattr(user, "office", None) if user else None
    if user and user.role == "cswdo_admin" and office and office.area_covered:
        lgu_line, kind = lgu_names(office.area_covered)
        lines.append(lgu_line)
        return {
            "lines": lines,
            "office": f"{kind} Social Welfare and Development Office",
            "place": office.area_covered,
            **_seals(office.area_covered),
            "signatories": [
                _preparer(user, f"{kind} Social Welfare Staff"),
                {"label": "Noted By", "name": "", "position": f"{kind} Social Welfare and Development Officer"},
                {"label": "Approved By", "name": "", "position": f"{kind} Mayor"},
            ],
        }
    return {
        "lines": lines,
        "office": "Provincial Social Welfare and Development Office",
        "place": "Province of Pangasinan",
        **_seals(),
        "signatories": [
            _preparer(user, "PSWDO Staff"),
            {"label": "Noted By", "name": "", "position": "Provincial Social Welfare and Development Officer"},
            {"label": "Approved By", "name": "", "position": "Provincial Governor"},
        ],
    }


REPORT_TYPES = {
    "relief_requests": {
        "title": "Barangay Reports",
        "description": "All barangay reports submitted, with impact figures, model estimate, and allocation status.",
        "icon": "clipboard",
    },
    "distribution": {
        "title": "Deliveries Report",
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
        "description": "Relief operations summary per municipality - families, requests, delivery status.",
        "icon": "map",
    },
    "typhoon_summary": {
        "title": "Typhoon Event Summary",
        "description": "Full operational summary for a single typhoon event from start to close.",
        "icon": "cloud-lightning",
    },
    "analytics": {
        "title": "Predictive Analytics Report",
        "description": "Demand forecast, burn rate analysis, warehouse forecast, and system recommendations.",
        "icon": "trending-up",
    },
}


# Formats a date for reports (e.g. October 23, 2026).
def _fmt_date(d):
    return d.strftime("%b %d, %Y") if d else "-"


# Reads the report period filter (last 7, 30 or 90 days, or all time).
def _parse_days(raw):
    if raw is None or raw == "all":
        return "all"
    try:
        days = int(raw)
    except (TypeError, ValueError):
        return "all"
    return days if days in (7, 30, 90) else "all"


# Reads all report filters (event, municipality, period) and works out the date range.
def resolve_filters(args):
    event_id = args.get("event_id", type=int)
    event = DisasterEvent.query.get(event_id) if event_id else None

    municipality = args.get("municipality", "all")
    if municipality not in TARGET_LGUS:
        municipality = "all"

    days = _parse_days(args.get("days"))

    lgus = [municipality] if municipality != "all" else list(TARGET_LGUS)

    return {
        "event": event,
        "event_id": event.event_id if event else None,
        "municipality": municipality,
        "lgus": lgus,
        "days": days,
        "start_date": ph_today() - timedelta(days=days) if days != "all" else date.min,
    }


# Collects the data for the Relief Requests report (requests, quantities, statuses).
def _build_relief_requests(filters):
    q = BarangayReport.query.join(Barangay).filter(
        Barangay.city_municipality.in_(filters["lgus"]),
        BarangayReport.status != "draft",
        BarangayReport.submitted_at >= filters["start_date"],
    )
    if filters["event_id"]:
        q = q.filter(BarangayReport.event_id == filters["event_id"])
    records = q.order_by(BarangayReport.submitted_at.desc()).all()

    rows = []
    for i, rep in enumerate(records, start=1):
        alloc = rep.allocation
        rows.append([
            i,
            rep.barangay.city_municipality,
            rep.ref,
            rep.barangay.barangay_name,
            rep.event.event_name if rep.event else "-",
            BARANGAY_REPORT_STATUS_LABELS.get(rep.status, rep.status.title()),
            rep.submitted_by_name,
            f"{rep.affected_families:,}",
            f"{rep.totally_damaged_houses:,}",
            f"{alloc.allocated_quantity:,}" if alloc else "-",
            _fmt_date(rep.reviewed_at or rep.submitted_at),
        ])
    return {
        "columns": [
            "#", "Municipality", "Report ID", "Barangay", "Typhoon Event", "Status",
            "Submitted By", "Affected Families", "Totally Damaged Houses",
            "Allocated Packs", "Last Updated",
        ],
        "rows": rows,
    }


# Collects the data for the Distribution report (deliveries to barangays).
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
            fulfilling.office_name if fulfilling else "-",
            f"{d.quantity_released:,}",
            _fmt_date(d.distribution_date),
            DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
        ])
    return {
        "columns": ["#", "Distribution ID", "Municipality", "Warehouse", "Packs", "Date", "Status"],
        "rows": rows,
    }


# Collects the data for the Warehouse Inventory report (stock in each warehouse).
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
            f"{int(days_left)} days" if days_left is not None else "-",
        ])
    return {
        "columns": ["#", "Warehouse", "Municipality", "Food Packs", "Capacity", "% Capacity", "Health", "Days Remaining"],
        "rows": rows,
    }


# Collects the data for the Stock Movement report (stock in and out).
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


# Collects the data for the Municipality Summary report
# (affected families and food packs per municipality).
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


# Collects the data for the Typhoon Event Summary report
# (key numbers for one disaster event).
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


# Collects the data for the Analytics report (each barangay's status and relief received).
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
    notes = [f"{rec['title']} - {rec['detail']}" for rec in _stock_recommendations(warehouses)]
    if not notes:
        notes = ["No stock-transfer recommendations at this time - warehouse levels are healthy."]

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

PSWDO_REPORT_TYPES = ("warehouse_inventory", "stock_movement", "analytics")


# Builds any PSWDO/CSWDO report by its type:
# title, letterhead, table columns and rows, and notes.
def build_report(report_type, filters, user=None):
    if report_type not in REPORT_TYPES:
        return None
    info = REPORT_TYPES[report_type]
    data = BUILDERS[report_type](filters)
    if report_type == "warehouse_inventory":
        coverage = "Current Snapshot"
    elif filters["days"] == "all":
        coverage = "All Time"
    else:
        coverage = f"Last {filters['days']} Days"

    return {
        "report_type": report_type,
        "title": info["title"],
        "description": info["description"],
        "columns": data["columns"],
        "rows": data["rows"],
        "record_count": len(data["rows"]),
        "notes": data.get("notes"),
        "coverage": coverage,
        "event_name": filters["event"].event_name if filters["event"] else "All Events",
        "municipality_label": filters["municipality"] if filters["municipality"] != "all" else "All Municipalities",
        "date_generated": ph_now(),
        "prepared_by": user.name if user else "PSWDO Officer",
        "prepared_by_role": ROLE_LABELS.get(user.role, user.role) if user else "PSWDO Officer",
        "letterhead": build_letterhead(user),
    }


BARANGAY_REPORT_TYPES = {
    "damage_reports": {
        "title": "Barangay Report History",
        "description": "All barangay reports this barangay has submitted, with review status.",
        "icon": "clipboard",
    },
    "relief_deliveries": {
        "title": "Relief Delivery Report",
        "description": "Complete history of food pack deliveries received by this barangay.",
        "icon": "truck",
    },
    "stock_movements": {
        "title": "Stock Movement History",
        "description": "Every food pack movement in this barangay's inventory - received, distributed, adjusted, expired.",
        "icon": "package",
    },
}

BARANGAY_STOCK_SOURCE_LABELS = {
    "delivery": "Received",
    "distribution": "Distributed",
    "adjustment": "Adjustment",
    "damaged_return": "Damaged - Returned to Warehouse",
    "expired": "Expired Food Packs",
}

BARANGAY_REPORT_STATUS_LABELS = {
    "draft": "Draft",
    "pending": "Submitted",
    "returned": "Returned",
    "verified": "Verified",
    "approved": "Approved",
    "declined": "Declined",
    "fulfilled": "Fulfilled",
}


# Reads the barangay report filters (event and period).
def resolve_barangay_filters(args):
    event_id = args.get("event_id", type=int)
    event = DisasterEvent.query.get(event_id) if event_id else None

    days = _parse_days(args.get("days"))

    return {
        "event": event,
        "event_id": event.event_id if event else None,
        "days": days,
        "start_date": ph_today() - timedelta(days=days) if days != "all" else date.min,
    }


# Collects the data for the barangay's Reports report (its situation reports).
def _build_barangay_damage_reports(barangay, filters):
    q = BarangayReport.query.filter(
        BarangayReport.barangay_id == barangay.barangay_id,
        BarangayReport.status != "draft",
        BarangayReport.created_at >= filters["start_date"],
    )
    if filters["event_id"]:
        q = q.filter(BarangayReport.event_id == filters["event_id"])
    records = q.order_by(BarangayReport.created_at.desc()).all()

    rows = []
    for i, r in enumerate(records, start=1):
        rows.append([
            i, r.ref, r.event.event_name if r.event else "-", _fmt_date(r.submitted_at),
            f"{r.affected_families:,}", f"{r.affected_individuals:,}",
            BARANGAY_REPORT_STATUS_LABELS.get(r.status, r.status.title()),
        ])
    return {
        "columns": ["#", "Report ID", "Typhoon Event", "Date Submitted", "Affected Families", "Affected Individuals", "Status"],
        "rows": rows,
    }


# Collects the data for the barangay's Relief Deliveries report (deliveries received).
def _build_barangay_relief_deliveries(barangay, filters):
    q = DistributionRecord.query.filter(
        DistributionRecord.barangay_id == barangay.barangay_id,
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
            i, f"D-{d.distribution_date.year}-{d.distribution_id:03d}",
            fulfilling.office_name if fulfilling else "-", f"{d.quantity_released:,}",
            _fmt_date(d.distribution_date), DISPATCH_STATUS_LABELS.get(d.dispatch_status, d.dispatch_status),
            d.received_by or "-",
        ])
    return {
        "columns": ["#", "Distribution ID", "Warehouse", "Food Packs", "Date", "Status", "Received By"],
        "rows": rows,
    }


# Collects the data for the barangay's Stock Movements report.
def _build_barangay_stock_movements(barangay, filters):
    from app.models.barangay_inventory import BarangayStockLog

    q = BarangayStockLog.query.filter(
        BarangayStockLog.barangay_id == barangay.barangay_id,
        BarangayStockLog.created_at >= filters["start_date"],
    )
    event = filters["event"]
    if event:
        q = q.filter(db.func.date(BarangayStockLog.created_at) >= event.start_date)
        if event.end_date:
            q = q.filter(db.func.date(BarangayStockLog.created_at) <= event.end_date)
    logs = q.order_by(BarangayStockLog.created_at.desc(), BarangayStockLog.log_id.desc()).all()
    return _barangay_stock_movement_table(logs)


# Builds the rows of the barangay stock movement table.
def _barangay_stock_movement_table(logs):
    rows = []
    for i, l in enumerate(logs, start=1):
        label = (stock_log_label(l.item_type, l.delta, l.source_type, l.reason)
                 or BARANGAY_STOCK_SOURCE_LABELS.get(l.source_type, l.source_type.title()))
        details = l.reason or "-"
        if l.family and l.family.family_name not in details:
            details = f"{details} · {l.family.family_name}" if l.reason else l.family.family_name
        rows.append([
            i, l.created_at.strftime("%b %d, %Y %I:%M %p") if l.created_at else "-",
            label, l.item_name, f"{l.delta:+,}", details,
            f"{len(l.proof_photo_list)} photo{'s' if len(l.proof_photo_list) != 1 else ''}" if l.proof_photo_list else "-",
            l.updated_by_user.name if l.updated_by_user else "-",
        ])

    return {
        "columns": ["#", "Date", "Movement", "Item", "Quantity", "Details", "Photo Proof", "Recorded By"],
        "rows": rows,
    }


BARANGAY_BUILDERS = {
    "damage_reports": _build_barangay_damage_reports,
    "relief_deliveries": _build_barangay_relief_deliveries,
    "stock_movements": _build_barangay_stock_movements,
}


# Builds any barangay report by its type:
# title, letterhead, table columns and rows, and notes.
def build_barangay_report(report_type, barangay, filters, user=None):
    if report_type not in BARANGAY_REPORT_TYPES:
        return None
    info = BARANGAY_REPORT_TYPES[report_type]
    data = BARANGAY_BUILDERS[report_type](barangay, filters)
    coverage = "All Time" if filters["days"] == "all" else f"Last {filters['days']} Days"

    return {
        "report_type": report_type,
        "title": info["title"],
        "description": info["description"],
        "columns": data["columns"],
        "rows": data["rows"],
        "record_count": len(data["rows"]),
        "notes": data.get("notes"),
        "coverage": coverage,
        "event_name": filters["event"].event_name if filters["event"] else "All Events",
        "municipality_label": f"Brgy. {barangay.barangay_name}, {barangay.city_municipality}",
        "date_generated": ph_now(),
        "prepared_by": user.name if user else "Barangay User",
        "prepared_by_role": ROLE_LABELS.get(user.role, user.role) if user else "Barangay User",
        "letterhead": build_letterhead(user, barangay=barangay),
    }


# Builds the barangay stock movement Excel export (with the filters used).
def build_barangay_movement_export(barangay, logs, type_label, date_from, date_to, user=None):
    info = BARANGAY_REPORT_TYPES["stock_movements"]
    data = _barangay_stock_movement_table(logs)
    if date_from or date_to:
        coverage = f"{_fmt_date(date_from) if date_from else 'Start'} to {_fmt_date(date_to) if date_to else 'Present'}"
    else:
        coverage = "All Time"
    return {
        "report_type": "stock_movements",
        "title": info["title"],
        "description": info["description"],
        "columns": data["columns"],
        "rows": data["rows"],
        "record_count": len(data["rows"]),
        "notes": data.get("notes"),
        "coverage": coverage,
        "event_label": "Movement Type",
        "event_name": type_label,
        "municipality_label": f"Brgy. {barangay.barangay_name}, {barangay.city_municipality}",
        "date_generated": ph_now(),
        "prepared_by": user.name if user else "Barangay User",
        "prepared_by_role": ROLE_LABELS.get(user.role, user.role) if user else "Barangay User",
        "letterhead": build_letterhead(user, barangay=barangay),
    }
