"""
Builds a realistic training dataset for the food-pack demand model
(app.ml.train) while real PSWDO/CSWDO records are still pending.

What it does
------------
1. Upserts the full, real barangay roster for the three target LGUs —
   Urdaneta City (34), Santa Barbara (29), Calasiao (24) — taken from the
   PSGC boundary files in app/static/geo. Existing barangays keep their
   barangay_id (so every FK — users, allocations, statuses — stays intact);
   only their profile numbers are refreshed. The 10 placeholder Santa
   Barbara names are renamed to real ones.
2. Gives every barangay a *coherent* synthetic profile: population, a
   per-barangay household size (so num_households is NOT a fixed ratio of
   population and the two carry independent signal), poverty incidence,
   disaster risk index and past-calamity frequency — all deterministic from
   the barangay name, so re-runs are stable. Any barangay figure we have an
   official record for (see scripts/real_profiles.py — currently Urdaneta
   City population and household counts, PSA 2024) overrides the synthetic
   value; fields with no real dataset yet stay synthetic.
3. Creates six past (ended) typhoon events spanning 2023-2025 and, for each,
   a BarangayDisasterStatus + a released AllocationRecord for a large subset
   of barangays. The allocation quantity comes from an explicit generative
   model (see `synthetic_allocation`): a fraction of households is affected,
   only a fraction of THOSE need food packs, and the pack count tracks that
   need (~one per family) — so a mid-size barangay in a moderate event lands
   around 100-300 packs, not thousands. `affected_families` on the status row
   is the raw affected count (larger, but never more than the barangay's
   household total). Real allocations will differ; retraining via
   scripts/train_model.py is all that's needed.

Idempotent: re-running only fills gaps. Delete the six SYNTHETIC_EVENTS rows
(and their allocations/statuses) to fully reseed the historical set.

Usage:
    .venv/bin/python scripts/seed_training_data.py
"""
import json
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ — sibling modules

from real_profiles import real_profile

from app.utils.timezone import ph_now, ph_today

from app import create_app
from app.extensions import db
from app.models.barangay import Barangay
from app.models.office import Office
from app.models.user import User
from app.models.disaster_event import DisasterEvent
from app.models.barangay_status import BarangayDisasterStatus
from app.models.allocation import AllocationRecord
from app.models.validation import DistributionRecord
from app.models.relief_request_batch import ReliefRequestBatch
from app.ml.train import historical_allocation_for

app = create_app()

GEO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static", "geo")
GEO_FILES = {
    "Urdaneta City": "urdaneta_barangays.json",
    "Santa Barbara": "santabarbara_barangays.json",
    "Calasiao": "calasiao_barangays.json",
}

# Placeholder Santa Barbara names currently in the DB (barangay_id 11-20),
# in id order -> the real barangays they should become. Renaming keeps the
# barangay_id (and every FK to it) intact.
SANTA_BARBARA_RENAMES = {
    "Abot": "Alibago",
    "Ban-ao": "Balingueo",
    "Batayang": "Sonquil",  # not "Banaoang" — that name already exists in Calasiao
    "Bungallon": "Banzal",
    "Calepaan": "Botao",
    "Carosucan Norte": "Cablong",
    "Carosucan Sur": "Carusocan",
    "Coliling": "Dalongue",
    "Hacienda": "Erfe",
    "Mapolopolo": "Gueguesangen",
}

# Six past typhoon events with a severity multiplier each. Severity is the
# only per-event driver the model can't see (it has no event feature), so it
# is kept in a modest band — the six static predictors stay dominant.
SYNTHETIC_EVENTS = [
    ("Typhoon Egay (2023)",        date(2023, 8, 19),  date(2023, 8, 26),  "Typhoon",            0.88),
    ("Typhoon Kabayan (2023)",     date(2023, 11, 4),  date(2023, 11, 10), "Severe Tropical Storm", 0.97),
    ("Typhoon Carina (2024)",      date(2024, 7, 23),  date(2024, 7, 30),  "Typhoon",            1.12),
    ("Super Typhoon Julian (2024)", date(2024, 9, 13), date(2024, 9, 22),  "Super Typhoon",      1.20),
    ("Tropical Storm Dante (2025)", date(2025, 6, 17), date(2025, 6, 21),  "Tropical Storm",     0.86),
    ("Typhoon Ramil (2025)",       date(2025, 10, 1),  date(2025, 10, 8),  "Typhoon",            1.05),
]

# Labels of pre-existing demo allocations (Typhoon Inday etc., event_id 1-3)
# are rewritten from the same generative model so the training set follows a
# single coherent function; their linked distribution / status rows are kept
# in sync. These event names are left untouched otherwise.
LEGACY_EVENT_SEVERITY = {
    "Typhoon Inday": 1.15,
    "Tropical Storm Basyang": 0.9,
    "Tropical Storm Ada": 0.84,
}

MIN_EVENTS_PER_BARANGAY = 3  # so every barangay carries a real historical_allocation


def geo_names(lgu):
    with open(os.path.join(GEO_DIR, GEO_FILES[lgu])) as f:
        data = json.load(f)
    return sorted(ft["properties"]["name"] for ft in data["features"])


def profile_for(name, lgu):
    """Deterministic, plausible barangay profile.

    num_households is population / household-size with an independent
    multiplicative factor on top, so it correlates with population the way a
    real household count does (r ~ 0.85) without being a fixed ratio the
    least-squares solver can't separate."""
    rng = random.Random(f"profile|{lgu}|{name}")
    population = int(rng.uniform(1000, 6200))
    avg_household_size = rng.uniform(3.8, 5.6)
    independent_factor = rng.uniform(0.80, 1.22)
    num_households = max(int(round(population / avg_household_size * independent_factor)), 60)
    poverty_incidence = round(rng.uniform(12.0, 47.0), 2)
    disaster_risk_index = round(rng.uniform(3.6, 9.1), 2)
    past_calamity_freq = rng.randint(1, 9)
    profile = {
        "population": population,
        "num_households": num_households,
        "poverty_incidence": poverty_incidence,
        "disaster_risk_index": disaster_risk_index,
        "past_calamity_freq": past_calamity_freq,
    }
    # Overlay any official figure on record (see scripts/real_profiles.py).
    # Synthetic values survive only for fields with no real dataset yet.
    profile.update(real_profile(lgu, name))
    return profile


def _affected_rate(b, severity):
    """Fraction of a barangay's households actually affected in an event.
    Driven by exposure/vulnerability, lifted by event severity. Clipped to a
    realistic 5%-60% — a whole barangay is very rarely 100% affected."""
    base = (0.055
            + 0.026 * float(b.disaster_risk_index)
            + 0.0016 * float(b.poverty_incidence)
            + 0.011 * b.past_calamity_freq)
    return max(0.05, min(base * (0.75 + 0.35 * severity), 0.60))


def _pack_need_rate(b):
    """Of the AFFECTED households, the share that actually needs a food pack —
    displaced, house damaged, or no means to cook. Not every affected family
    needs relief goods; higher-risk barangays see more displacement."""
    return max(0.20, min(0.24 + 0.028 * float(b.disaster_risk_index)
                         + 0.001 * float(b.poverty_incidence), 0.68))


PACKS_PER_FAMILY = 1.1  # ~one food pack per family, small operational buffer


def affected_families_for(b, severity, rng):
    """Realistic count of affected families for a BarangayDisasterStatus row —
    a few dozen to a few hundred, never more than the barangay has."""
    fam = _affected_rate(b, severity) * b.num_households * rng.uniform(0.9, 1.1)
    return max(0, min(int(round(fam)), b.num_households))


def synthetic_allocation(b, severity, prior, rng):
    """Generative model for a released food-pack allocation.

        affected_households = num_households * affected_rate(risk, poverty, freq, severity)
        families_needing_packs = affected_households * pack_need_rate(risk, poverty)
        allocation = severity * families_needing_packs * PACKS_PER_FAMILY
                   + 0.20 * prior_allocation + noise

    So the figure tracks *families that actually need relief goods*, not the
    raw affected count — a barangay of 500 households in a moderate event lands
    around 80-150 packs, not thousands.
    """
    affected_households = b.num_households * _affected_rate(b, severity)
    families_needing = affected_households * _pack_need_rate(b)
    base = severity * families_needing * PACKS_PER_FAMILY
    noise = rng.gauss(0.0, 0.06 * base)
    value = base + 0.20 * prior + noise
    return max(int(round(value)), 0)


def status_tier(affected_families, num_households):
    ratio = affected_families / num_households if num_households else 0
    if ratio >= 0.45:
        return "high_priority"
    if ratio >= 0.28:
        return "needs_assistance"
    if ratio >= 0.13:
        return "monitoring"
    return "normal"


def run():
    with app.app_context():
        pswdo_admin = (User.query.filter_by(role="pswdo_admin").first()
                       or User.query.filter_by(role="system_admin").first())
        cswdo_office_by_lgu = {o.area_covered: o for o in Office.query.filter_by(office_type="cswdo").all()}

        # --- 1. rename placeholder Santa Barbara barangays -------------------
        renamed = 0
        for old, new in SANTA_BARBARA_RENAMES.items():
            row = Barangay.query.filter_by(barangay_name=old, city_municipality="Santa Barbara").first()
            if row and not Barangay.query.filter_by(barangay_name=new, city_municipality="Santa Barbara").first():
                row.barangay_name = new
                renamed += 1
        db.session.flush()
        if renamed:
            print(f"Renamed {renamed} placeholder Santa Barbara barangay(s) to real names.")

        # --- 2. upsert the full real roster + refresh profiles --------------
        all_barangays = []
        added = 0
        for lgu in GEO_FILES:
            for name in geo_names(lgu):
                row = Barangay.query.filter_by(barangay_name=name, city_municipality=lgu).first()
                prof = profile_for(name, lgu)
                if row is None:
                    row = Barangay(barangay_name=name, city_municipality=lgu, **prof)
                    db.session.add(row)
                    added += 1
                else:
                    for k, v in prof.items():
                        setattr(row, k, v)
                all_barangays.append(row)
        db.session.flush()
        print(f"Roster: {len(all_barangays)} barangays ({added} newly added, profiles refreshed).")

        # --- 2b. baseline barangay food-pack stock ------------------------
        # Every barangay carries some on-hand stock so the CSWDO/MSWDO-facing
        # views (Barangay Report review, Predictive Analytics, GIS map) have a
        # real figure to weigh an allocation against. A barangay that later
        # hands everything out drops to a genuine 0; only a barangay with NO
        # inventory row at all reads as "none reported".
        from app.models.barangay_inventory import BarangayInventory
        BASELINE_BARANGAY_STOCK = 100
        stocked = 0
        for b in all_barangays:
            inv = BarangayInventory.query.filter_by(
                barangay_id=b.barangay_id, item_type="food_pack"
            ).first()
            if inv is None:
                db.session.add(BarangayInventory(
                    barangay_id=b.barangay_id, item_type="food_pack",
                    item_name="Food Packs", unit="packs",
                    quantity_available=BASELINE_BARANGAY_STOCK,
                ))
                stocked += 1
            elif (inv.quantity_available or 0) == 0:
                inv.quantity_available = BASELINE_BARANGAY_STOCK
                stocked += 1
        db.session.flush()
        print(f"Barangay stock: {stocked} barangays set to a {BASELINE_BARANGAY_STOCK}-pack baseline.")

        # --- 3. decide which barangays each event hits ---------------------
        # Deterministic per barangay+event; then top up so every barangay is
        # in at least MIN_EVENTS_PER_BARANGAY events.
        event_names = [e[0] for e in SYNTHETIC_EVENTS]
        hits = {b.barangay_id: [] for b in all_barangays}
        for ev_name, *_ in SYNTHETIC_EVENTS:
            for b in all_barangays:
                rng = random.Random(f"hit|{b.city_municipality}|{b.barangay_name}|{ev_name}")
                if rng.random() < 0.75:
                    hits[b.barangay_id].append(ev_name)
        for b in all_barangays:
            missing = MIN_EVENTS_PER_BARANGAY - len(hits[b.barangay_id])
            for ev_name in event_names:
                if missing <= 0:
                    break
                if ev_name not in hits[b.barangay_id]:
                    hits[b.barangay_id].append(ev_name)
                    missing -= 1

        # --- 4. create events + statuses + allocations (chronological) -----
        # The synthetic historical events carry ONLY training data (no
        # distributions), so their allocations + statuses are dropped and
        # rebuilt every run — that keeps a retune of the generative model a
        # one-command operation.
        barangay_by_id = {b.barangay_id: b for b in all_barangays}
        syn_events = DisasterEvent.query.filter(
            DisasterEvent.event_name.in_([e[0] for e in SYNTHETIC_EVENTS])
        ).all()
        syn_event_ids = [e.event_id for e in syn_events]
        if syn_event_ids:
            AllocationRecord.query.filter(
                AllocationRecord.event_id.in_(syn_event_ids)
            ).delete(synchronize_session=False)
            BarangayDisasterStatus.query.filter(
                BarangayDisasterStatus.event_id.in_(syn_event_ids)
            ).delete(synchronize_session=False)
            db.session.flush()

        created_events = 0
        created_allocs = 0
        for ev_name, start, end, weather, severity in SYNTHETIC_EVENTS:
            event = DisasterEvent.query.filter_by(event_name=ev_name).first()
            if event is None:
                event = DisasterEvent(
                    event_name=ev_name, event_type="typhoon", status="ended",
                    weather_condition=weather, start_date=start, end_date=end,
                    created_by=pswdo_admin.user_id if pswdo_admin else None,
                )
                db.session.add(event)
                db.session.flush()
                created_events += 1

            for b in all_barangays:
                if ev_name not in hits[b.barangay_id]:
                    continue

                rng = random.Random(f"alloc|{b.city_municipality}|{b.barangay_name}|{ev_name}")
                prior = historical_allocation_for(b.barangay_id, before_date=start)
                qty = synthetic_allocation(b, severity, prior, rng)
                affected_families = affected_families_for(b, severity, rng)

                office = cswdo_office_by_lgu.get(b.city_municipality)
                db.session.add(AllocationRecord(
                    barangay_id=b.barangay_id,
                    office_id=office.office_id if office else None,
                    predicted_quantity=qty,
                    allocated_quantity=qty,
                    historical_allocation=prior,
                    allocation_date=start,
                    event_id=event.event_id,
                    disaster_event=ev_name,
                    status="released",
                    created_by=pswdo_admin.user_id if pswdo_admin else None,
                    decided_by=pswdo_admin.user_id if pswdo_admin else None,
                ))
                created_allocs += 1

                if not BarangayDisasterStatus.query.filter_by(
                    barangay_id=b.barangay_id, event_id=event.event_id
                ).first():
                    db.session.add(BarangayDisasterStatus(
                        barangay_id=b.barangay_id, event_id=event.event_id,
                        status=status_tier(affected_families, b.num_households),
                        affected_families=affected_families,
                        updated_by=pswdo_admin.user_id if pswdo_admin else None,
                    ))
            db.session.flush()

        # --- 5. rewrite pre-existing demo allocation labels coherently -----
        # (Typhoon Inday / Basyang / Ada — event_id 1-3). Keeps the training
        # set on one generative function; syncs the linked distribution and
        # status rows so the demo pages still add up.
        rewritten = 0
        legacy_events = DisasterEvent.query.filter(
            DisasterEvent.event_name.in_(list(LEGACY_EVENT_SEVERITY))
        ).order_by(DisasterEvent.start_date).all()
        for event in legacy_events:
            severity = LEGACY_EVENT_SEVERITY[event.event_name]
            allocs = AllocationRecord.query.filter_by(event_id=event.event_id).all()
            for a in allocs:
                b = barangay_by_id.get(a.barangay_id)
                if b is None:
                    continue
                rng = random.Random(f"legacy|{a.allocation_id}|{event.event_name}")
                prior = historical_allocation_for(a.barangay_id, before_date=event.start_date)
                qty = synthetic_allocation(b, severity, prior, rng)
                a.predicted_quantity = qty
                a.historical_allocation = prior
                if (a.allocated_quantity or 0) > 0 or a.status in ("approved", "released"):
                    a.allocated_quantity = qty
                for d in a.distribution_records:
                    d.quantity_released = a.allocated_quantity or qty
                bds = BarangayDisasterStatus.query.filter_by(
                    barangay_id=a.barangay_id, event_id=event.event_id
                ).first()
                if bds:
                    fam = affected_families_for(b, severity, rng)
                    bds.affected_families = fam
                    bds.status = status_tier(fam, b.num_households)
                rewritten += 1
        db.session.flush()

        # --- 6b. backfill barangay_reports for the new request flow -------
        # Every existing damage report now needs a `requested_food_packs`
        # figure (the barangay's own ask) and a computed `flood_level`.
        from app.models.barangay_report import BarangayReport
        from app.routes.barangay import _compute_severity
        from app.ml import predict as ml_predict
        report_fix = 0
        for rep in BarangayReport.query.all():
            b = barangay_by_id.get(rep.barangay_id) or Barangay.query.get(rep.barangay_id)
            if b is None:
                continue
            rng = random.Random(f"report|{rep.report_id}")
            if not rep.requested_food_packs:
                est = ml_predict.predict_quantity(b) or 0
                rep.requested_food_packs = max(int(round(est * rng.uniform(0.8, 1.25))), 20)
                report_fix += 1
            rep.flood_level = _compute_severity(
                affected_families=rep.affected_families or 0,
                affected_individuals=rep.affected_individuals or 0,
                totally_damaged_houses=rep.totally_damaged_houses or 0,
                partially_damaged_houses=rep.partially_damaged_houses or 0,
                roofs_damaged=rep.roofs_damaged or 0,
            )
        db.session.flush()

        # --- 6. seed a few CSWDO warehouse stock-in logs ------------------
        # So the new Municipal Warehouse movements page isn't empty. One
        # provincial-supply receipt + one donation per CSWDO office, dated
        # around the active event. Idempotent on (office, reason).
        from app.models.warehouse import WarehouseInventory, WarehouseStockLog
        from datetime import datetime, timedelta
        stock_logs = 0
        for lgu, office in cswdo_office_by_lgu.items():
            seeds = [
                ("food_pack", "Food Packs", "packs", 3000, "standard", None, "Provincial supply top-up", 14),
                ("food_pack", "Food Packs", "packs", 800, "donation", "Philippine Red Cross", "Donation drop-off", 6),
                ("hygiene_kit", "Hygiene Kits", "kits", 250, "standard", None, "Provincial supply", 10),
            ]
            for item_type, item_name, unit, delta, src, donor, reason, days_ago in seeds:
                if WarehouseStockLog.query.filter_by(office_id=office.office_id, reason=reason).first():
                    continue
                inv = WarehouseInventory.query.filter_by(
                    office_id=office.office_id, item_type=item_type
                ).first()
                if inv is None:
                    inv = WarehouseInventory(
                        office_id=office.office_id, item_type=item_type, item_name=item_name,
                        unit=unit, quantity_available=0, min_stock_level=0,
                    )
                    db.session.add(inv)
                inv.quantity_available = (inv.quantity_available or 0) + delta
                db.session.add(WarehouseStockLog(
                    office_id=office.office_id, item_type=item_type, item_name=item_name,
                    delta=delta, reason=reason, source_type=src, donor_name=donor,
                    updated_by=pswdo_admin.user_id if pswdo_admin else None,
                    created_at=ph_now() - timedelta(days=days_ago),
                ))
                stock_logs += 1
        db.session.flush()

        db.session.flush()

        # --- 7. demo barangay Relief Requests for the ACTIVE event ---------
        # A handful of Tier-1 (barangay -> CSWDO) requests across every state so
        # the CSWDO inbox / Deliveries pages and barangay Inventory aren't empty.
        from app.models.validation import DistributionRecord
        from app.models.barangay_inventory import BarangayInventory, BarangayStockLog
        active = DisasterEvent.query.filter_by(status="active").order_by(
            DisasterEvent.start_date.desc()
        ).first()
        brgy_requests = 0
        _have_demo = AllocationRecord.query.filter_by(source="barangay_request").filter(
            AllocationRecord.event_id == (active.event_id if active else None)
        ).count()
        if active and _have_demo < 3:
            today = ph_today()
            # (barangay_name, lgu, hazard, families, requested, outcome)
            plan = [
                ("Poblacion", "Urdaneta City", "Flooding", 210, 260, "pending"),
                ("Nancayasan", "Urdaneta City", "Strong Winds", 90, 120, "approved"),
                ("San Vicente", "Urdaneta City", "Combined", 140, 180, "fulfilled"),
                ("Maningding", "Santa Barbara", "Flooding", 120, 150, "approved"),
                ("Nalsian", "Calasiao", "Storm Surge", 160, 200, "fulfilled"),
                ("Longos", "Calasiao", "Strong Winds", 70, 90, "declined"),
            ]
            cswdo_admin_by_office = {u.office_id: u for u in User.query.filter_by(role="cswdo_admin").all()}
            for name, lgu, hazard, fam, requested, outcome in plan:
                b = Barangay.query.filter_by(barangay_name=name, city_municipality=lgu).first()
                if not b or BarangayReport.query.filter_by(barangay_id=b.barangay_id, event_id=active.event_id).first():
                    continue
                office = cswdo_office_by_lgu.get(lgu)
                cadmin = cswdo_admin_by_office.get(office.office_id) if office else None
                rep = BarangayReport(
                    barangay_id=b.barangay_id, event_id=active.event_id,
                    submitted_by_name="Barangay Captain", submitted_by_designation="Barangay Captain",
                    submitted_at=ph_now(),
                    incident_date=active.start_date,
                    affected_families=fam, affected_individuals=fam * 4,
                    totally_damaged_houses=max(fam // 30, 1), partially_damaged_houses=fam // 8,
                    roofs_damaged=(fam // 6 if hazard in ("Strong Winds", "Combined") else 0),
                    requested_food_packs=requested,
                    status="pending",
                )
                rep.flood_level = _compute_severity(
                    affected_families=fam, totally_damaged_houses=rep.totally_damaged_houses,
                    partially_damaged_houses=rep.partially_damaged_houses, roofs_damaged=rep.roofs_damaged,
                )
                db.session.add(rep)
                db.session.flush()
                brgy_requests += 1
                if outcome == "pending":
                    continue
                if outcome == "declined":
                    rep.status = "declined"
                    rep.review_remarks = "Barangay stock still adequate from a prior delivery."
                    continue

                qty = int(round(requested * 0.85))
                alloc = AllocationRecord(
                    barangay_id=b.barangay_id, office_id=office.office_id,
                    predicted_quantity=requested, allocated_quantity=qty,
                    historical_allocation=historical_allocation_for(b.barangay_id),
                    allocation_date=today, event_id=active.event_id,
                    status="approved", fulfilling_office_id=office.office_id,
                    source="barangay_request", barangay_report_id=rep.report_id,
                    created_by=cadmin.user_id if cadmin else None,
                    decided_by=cadmin.user_id if cadmin else None,
                )
                db.session.add(alloc)
                db.session.flush()
                fpv = WarehouseInventory.query.filter_by(office_id=office.office_id, item_type="food_pack").first()
                if fpv:
                    fpv.quantity_available = max((fpv.quantity_available or 0) - qty, 0)
                dist = DistributionRecord(
                    barangay_id=b.barangay_id, allocation_id=alloc.allocation_id,
                    quantity_released=qty, distribution_date=today,
                    dispatch_status=("dispatched" if outcome == "approved" else "delivered"),
                    submitted_by=cadmin.user_id if cadmin else None,
                )
                if outcome != "approved":
                    dist.status = "confirmed"
                    dist.received_by = "Barangay Captain"
                    dist.condition = "complete"
                    dist.validation_type = "signature"
                    dist.issued_by = cadmin.user_id if cadmin else None
                    dist.issued_at = ph_now()
                    rep.status = "fulfilled"
                    binv = BarangayInventory.query.filter_by(barangay_id=b.barangay_id, item_type="food_pack").first()
                    if binv is None:
                        binv = BarangayInventory(barangay_id=b.barangay_id, item_type="food_pack",
                                                 item_name="Food Packs", unit="packs", quantity_available=0)
                        db.session.add(binv)
                    binv.quantity_available += qty
                    db.session.add(BarangayStockLog(
                        barangay_id=b.barangay_id, item_type="food_pack", item_name="Food Packs",
                        delta=qty, source_type="delivery", distribution_id=dist.distribution_id,
                        reason="Received relief delivery",
                    ))
                else:
                    dist.issued_by = cadmin.user_id if cadmin else None
                    dist.issued_at = ph_now()
                db.session.add(dist)
                db.session.flush()

        # --- 8. demo Stock Requests (CSWDO -> PSWDO, Tier 2) --------------
        from app.models.logistics import WarehouseTransfer
        stock_reqs = 0
        depot = Office.query.filter_by(office_name="PSWDO Warehouse").first()
        if depot and ReliefRequestBatch.query.filter(
            ReliefRequestBatch.submitted_at.isnot(None)
        ).count() < 2:
            cadmin_by_office = {u.office_id: u for u in User.query.filter_by(role="cswdo_admin").all()}
            plan = [
                ("Urdaneta City", 2500, "pending", 0),
                ("Calasiao", 1800, "approved", 1500),   # approved + transfer in transit
            ]
            for lgu, requested, outcome, approved in plan:
                office = cswdo_office_by_lgu.get(lgu)
                if not office:
                    continue
                cadmin = cadmin_by_office.get(office.office_id)
                batch = ReliefRequestBatch(
                    office_id=office.office_id, event_id=active.event_id if active else None,
                    requested_food_packs=requested, priority="high",
                    reason="Barangay relief requests this week have drawn the municipal warehouse below projected demand.",
                    created_by=cadmin.user_id if cadmin else None,
                    created_at=ph_now(), submitted_at=ph_now(),
                    status="pending",
                )
                db.session.add(batch)
                db.session.flush()
                stock_reqs += 1
                if outcome == "approved":
                    src = WarehouseInventory.query.filter_by(office_id=depot.office_id, item_type="food_pack").first()
                    if src:
                        src.quantity_available = max((src.quantity_available or 0) - approved, 0)
                    batch.status = "approved"
                    batch.approved_food_packs = approved
                    batch.fulfilling_office_id = depot.office_id
                    pswdo_u = pswdo_admin
                    batch.decided_by = pswdo_u.user_id if pswdo_u else None
                    batch.decided_at = ph_now()
                    db.session.add(WarehouseTransfer(
                        from_office_id=depot.office_id, to_office_id=office.office_id,
                        item_type="food_pack", quantity=approved, batch_id=batch.batch_id,
                        status="pending", dispatch_status="in_transit",
                        issued_by=pswdo_u.user_id if pswdo_u else None, issued_at=ph_now(),
                        requested_by=cadmin.user_id if cadmin else None,
                        note="Truck 1", expected_arrival=ph_today(),
                    ))
        db.session.flush()

        db.session.commit()
        print(f"Created {created_events} historical event(s) and {created_allocs} released allocation(s).")
        print(f"Seeded {stock_logs} CSWDO warehouse stock-in log(s), {brgy_requests} demo barangay relief request(s), {stock_reqs} demo stock request(s).")
        print(f"Rewrote {rewritten} pre-existing demo allocation label(s) to match the generative model.")
        print(f"Total AllocationRecords now: {AllocationRecord.query.count()}")
        print("\nNext: .venv/bin/python scripts/train_model.py")


if __name__ == "__main__":
    run()
