# Finds which disaster events are active and who they cover.

from sqlalchemy import and_, or_

from app.models.disaster_event import DisasterEvent
from app.models.event_barangay import EventBarangay


# Finds the active disaster event for a municipality.
# A local (municipal) event is used first; if none, the province-wide event is used.
def resolve_effective_event(city_municipality):
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


# Checks if a disaster event applies to a barangay.
# Province-wide events cover every barangay; local events cover only the barangays that were ticked.
def event_covers_barangay(applicable_barangay_ids, barangay_id):
    return applicable_barangay_ids is None or barangay_id in applicable_barangay_ids


# Finds the active province-wide event, if any.
# Only one province-wide event can be active at a time.
def blocking_event_for_province():
    return DisasterEvent.query.filter_by(status="active", scope="province").first()


# Finds an active event that stops a municipality from declaring a new one
# (either a province-wide event, or the municipality's own local event).
def blocking_event_for_municipality(city_municipality):
    return DisasterEvent.query.filter(
        DisasterEvent.status == "active",
        or_(
            DisasterEvent.scope == "province",
            and_(DisasterEvent.scope == "municipality",
                 DisasterEvent.city_municipality == city_municipality),
        ),
    ).first()


# Lists every active event that covers a barangay (its local event and/or the province-wide one).
# These are the events a barangay can choose when filing a report.
def events_covering_barangay(city_municipality, barangay_id):
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


# Lists the active events that affect the given municipalities, newest first.
def relevant_active_events_query(lgus):
    return DisasterEvent.query.filter(
        DisasterEvent.status == "active",
        or_(
            DisasterEvent.scope == "province",
            and_(DisasterEvent.scope == "municipality",
                 DisasterEvent.city_municipality.in_(lgus)),
        ),
    ).order_by(DisasterEvent.start_date.desc())
