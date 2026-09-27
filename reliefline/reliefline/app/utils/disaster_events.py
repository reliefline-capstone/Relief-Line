"""Scope-aware resolution for the "current active event" a given town should
follow, now that a CSWDO can declare its own scope="municipality" event
alongside PSWDO's traditional scope="province" one (see
app.routes.cswdo.declare_disaster_event / app.routes.pswdo.declare_disaster_event).

Precedence: a town's own active municipality-scoped event always wins over
the province-wide one - the most specific declare governs that town. A town
with no local event just falls back to the active province event, which is
exactly how the whole app behaved before this module existed.
"""
from sqlalchemy import and_, or_

from app.models.disaster_event import DisasterEvent
from app.models.event_barangay import EventBarangay


def resolve_effective_event(city_municipality):
    """(event, applicable_barangay_ids) for this town.

    applicable_barangay_ids is a set of barangay_ids when the effective event
    is municipality-scoped (only those barangays are covered), or None when
    it's the province event (implicitly covers every barangay in town, same
    as legacy behavior) or when there's no active event at all.
    """
    local = DisasterEvent.query.filter_by(
        status="active", scope="municipality", city_municipality=city_municipality,
    ).order_by(DisasterEvent.start_date.desc()).first()
    if local:
        ids = {eb.barangay_id for eb in EventBarangay.query.filter_by(event_id=local.event_id).all()}
        return local, ids

    province = DisasterEvent.query.filter_by(
        status="active", scope="province",
    ).order_by(DisasterEvent.start_date.desc()).first()
    if province:
        return province, None

    return None, None


def event_covers_barangay(applicable_barangay_ids, barangay_id):
    """True if a barangay is within the effective event's coverage -
    applicable_barangay_ids is the second element resolve_effective_event
    returned (None means "covers every barangay in town")."""
    return applicable_barangay_ids is None or barangay_id in applicable_barangay_ids


def blocking_event_for_province():
    """The active province-scope event, if any - PSWDO's declare-guard.
    A CSWDO's local event never blocks PSWDO from declaring."""
    return DisasterEvent.query.filter_by(status="active", scope="province").first()


def blocking_event_for_municipality(city_municipality):
    """The active event (province OR this town's own municipality one) that
    would block a CSWDO in this town from declaring a new local event."""
    return DisasterEvent.query.filter(
        DisasterEvent.status == "active",
        or_(
            DisasterEvent.scope == "province",
            and_(DisasterEvent.scope == "municipality",
                 DisasterEvent.city_municipality == city_municipality),
        ),
    ).first()


def events_covering_barangay(city_municipality, barangay_id):
    """Active events that specifically cover this ONE barangay - unlike
    relevant_active_events_query (a town-wide picker for CSWDO/PSWDO views,
    where per-barangay coverage doesn't matter), this checks the local
    event's actual EventBarangay membership so a barangay left unchecked out
    of its town's local declare never sees it as a choice. Used for the
    barangay report form's event picker (a barangay covered by both its
    town's local event and the province one gets to choose between them)."""
    events = []
    local = DisasterEvent.query.filter_by(
        status="active", scope="municipality", city_municipality=city_municipality,
    ).order_by(DisasterEvent.start_date.desc()).first()
    if local:
        ids = {eb.barangay_id for eb in EventBarangay.query.filter_by(event_id=local.event_id).all()}
        if barangay_id in ids:
            events.append(local)

    province = DisasterEvent.query.filter_by(status="active", scope="province").first()
    if province:
        events.append(province)

    return events


def relevant_active_events_query(lgus):
    """Active events an event-picker dropdown should offer a viewer scoped to
    these LGUs: the province-wide event, plus any municipality-scoped event
    for a town in `lgus` (a single-element list for a cswdo_admin, or every
    target LGU for pswdo_admin/system_admin)."""
    return DisasterEvent.query.filter(
        DisasterEvent.status == "active",
        or_(
            DisasterEvent.scope == "province",
            and_(DisasterEvent.scope == "municipality",
                 DisasterEvent.city_municipality.in_(lgus)),
        ),
    ).order_by(DisasterEvent.start_date.desc())
