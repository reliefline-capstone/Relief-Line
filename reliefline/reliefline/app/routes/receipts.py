"""Delivery receipts - one printable, read-only page per food-pack delivery, so
everyone on the chain can see exactly what was handed over: who sent it, who
received it, how many packs, what condition, and what was inside them with each
item's expiration date.

Two kinds of delivery:
  * transfer     - PSWDO depot -> CSWDO warehouse (WarehouseTransfer)
  * distribution - CSWDO warehouse -> barangay (DistributionRecord)

Visible to the sending and receiving side of each delivery (plus PSWDO/system
admins, who oversee everything). Nothing here writes to the database.
"""
from datetime import date as _date
import json

from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from app.models.food_pack_batch import FoodPackComponent
from app.models.logistics import WarehouseTransfer
from app.models.validation import DistributionRecord
from app.routes.pswdo import _shelf_status, NEAR_EXPIRY_DAYS
from app.utils.timezone import ph_now

receipts_bp = Blueprint("receipts", __name__)

RECEIPT_ROLES = ("pswdo_admin", "cswdo_admin", "barangay_user", "system_admin")


def _lots_for_display(raw):
    """Turns a stored batch_lots JSON (see pswdo._deduct_food_pack_batches)
    into what the receipt shows: [{qty, received, earliest, status, items:
    [{name, qty_label, expires, status}]}]. Empty list for deliveries
    dispatched before batch details were recorded."""
    if not raw:
        return []
    components = {c.component_id: c for c in FoodPackComponent.query.all()}
    lots = []
    for lot in json.loads(raw):
        items = []
        for cid, name, iso, *rest in (lot.get("items") or []):
            comp = components.get(cid)
            exp = _date.fromisoformat(iso)
            items.append({
                "name": comp.name if comp else name,
                "qty_label": (rest[0] if rest and rest[0] else None) or (comp.quantity_label if comp else ""),
                "expires": exp,
                "status": _shelf_status(exp),
            })
        items.sort(key=lambda i: i["expires"])
        earliest = items[0]["expires"] if items else None
        lots.append({
            "qty": lot["qty"],
            "received": _date.fromisoformat(lot["received"]),
            "earliest": earliest,
            "status": _shelf_status(earliest) if earliest else None,
            "items": items,
        })
    return sorted(lots, key=lambda l: (l["earliest"] is None, l["earliest"] or _date.max))


@receipts_bp.route("/transfer/<int:transfer_id>")
@login_required
def transfer_receipt(transfer_id):
    if current_user.role not in RECEIPT_ROLES or current_user.role == "barangay_user":
        abort(403)
    t = WarehouseTransfer.query.get_or_404(transfer_id)
    if current_user.role == "cswdo_admin":
        office = current_user.office
        if not office or office.office_id not in (t.to_office_id, t.from_office_id):
            abort(403)
    if t.item_type != "food_pack":
        abort(404)

    received = t.status == "completed"
    return render_template(
        "receipts/receipt.html",
        kind="transfer", ref=t.ref,
        title="Stock Transfer Receipt",
        source_line=(f"Replenishment for {t.batch.ref}" if t.batch else (t.note or "Pre-positioning")),
        sender=t.from_office.office_name, recipient=t.to_office.office_name,
        dispatched_at=t.issued_at, dispatched_by=t.issued_by_user.name if t.issued_by_user else None,
        expected=t.expected_arrival,
        received=received, received_at=t.received_at, received_by=t.received_by,
        condition=(t.receipt_condition or "complete") if received else None,
        released=t.quantity, received_count=t.received_count if received else None,
        damaged=t.damaged_count if received else 0,
        usable=t.good_count if received else None,
        short=t.shortage_count if received else 0,
        note=t.receipt_note, remarks=t.note,
        lots=_lots_for_display(t.batch_lots), attachments=[], distribution_id=None,
        replaces=None, replacements=[],
        near_expiry_days=NEAR_EXPIRY_DAYS, generated_at=ph_now(),
    )


@receipts_bp.route("/distribution/<int:distribution_id>")
@login_required
def distribution_receipt(distribution_id):
    if current_user.role not in RECEIPT_ROLES:
        abort(403)
    rec = DistributionRecord.query.get_or_404(distribution_id)
    alloc = rec.allocation
    fulfilling = alloc.fulfilling_office if alloc else None
    if current_user.role == "barangay_user":
        if current_user.barangay_id != rec.barangay_id:
            abort(403)
    elif current_user.role == "cswdo_admin":
        office = current_user.office
        if not office or not fulfilling or fulfilling.office_id != office.office_id:
            abort(403)

    ref = f"D-{rec.distribution_date.year}-{rec.distribution_id:03d}"
    confirmed = rec.is_validated
    if alloc and alloc.barangay_report_id:
        source_line = "Barangay relief request"
    elif alloc and alloc.source == "cswdo_direct":
        source_line = "Proactive allocation (no barangay request)"
    else:
        source_line = "Allocation"
    if alloc and alloc.event:
        source_line += f" - {alloc.event.event_name}"

    def _ref(r):
        return f"D-{r.distribution_date.year}-{r.distribution_id:03d}"

    return render_template(
        "receipts/receipt.html",
        kind="distribution", ref=ref,
        title="Relief Delivery Receipt",
        source_line=source_line,
        sender=fulfilling.office_name if fulfilling else "Dispatching office",
        recipient=f"Brgy. {rec.barangay.barangay_name}, {rec.barangay.city_municipality}",
        dispatched_at=rec.issued_at, dispatched_by=rec.issued_by_user.name if rec.issued_by_user else None,
        expected=None,
        received=confirmed, received_at=None, received_by=rec.received_by,
        received_on=rec.distribution_date if confirmed else None, received_time=rec.time_received,
        condition=(rec.condition or "complete") if confirmed else None,
        released=rec.quantity_released or 0,
        received_count=rec.received_count if confirmed else None,
        damaged=rec.damaged_count if confirmed else 0,
        usable=rec.good_count if confirmed else None,
        short=rec.shortage_count if confirmed else 0,
        note=None, remarks=rec.issuance_note or (alloc.remarks if alloc else None),
        lots=_lots_for_display(rec.batch_lots),
        attachments=rec.validation_file.split(",") if (confirmed and rec.validation_file) else [],
        distribution_id=rec.distribution_id,
        replaces=_ref(rec.replaces) if rec.replaces else None,
        replacements=[{"ref": _ref(r), "qty": r.quantity_released or 0} for r in rec.replacements],
        near_expiry_days=NEAR_EXPIRY_DAYS, generated_at=ph_now(),
    )
