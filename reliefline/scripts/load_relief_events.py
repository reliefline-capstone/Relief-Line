"""
Master loader: imports every real relief-data module and upserts them into
relief_events / relief_event_typhoons / barangay_relief_records (see
scripts/apply_relief_schema.py). Replaces seed_monthly_history.py's
load_real()/load_real_sample() - there is no synthetic fallback anymore.

Sources loaded (4 modules):
  real_calasiao_typhoons_2021_2026   - 14 reports, has population snapshots
                                        (updated dataset 2026-10-03; replaced
                                        the old 25-typhoon version and
                                        real_calasiao_reports_2025)
  real_sta_barbara_typhoons_2021_2025 - 7 reports, NEW, has population snapshots
  real_urdaneta_typhoons_2021_2026   - 14 reports, has population snapshots
                                        (updated dataset 2026-10-03; replaced
                                        real_urdaneta_typhoons_2021_2025 and
                                        real_urdaneta_reports_2025 - see
                                        _drop_retired_sources below)
  sample_sta_barbara_aug2026         - 1 distribution sheet, EXISTING, packs
                                        only (no affected-families figure and
                                        no population snapshot) - mapped to
                                        BOTH maymay_2026 and pilandok_2026 as a
                                        combined relief_event: the delivery
                                        window (19 Aug - 2 Sep 2026) plausibly
                                        reflects cumulative relief for both
                                        storms and the sheet gives no way to
                                        split it by event. This is a judgement
                                        call, documented here rather than
                                        silently picked - revisit if a cleaner
                                        per-storm Sta. Barbara sheet turns up.

Run: .venv/Scripts/python.exe -m scripts.load_relief_events
Then: bash scripts/sync_db_dump.sh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import bindparam, text

from app import create_app
from app.extensions import db

import real_calasiao_typhoons_2021_2026 as calasiao_new
import real_sta_barbara_typhoons_2021_2025 as sta_barbara_new
import real_urdaneta_typhoons_2021_2026 as urdaneta_new
import sample_sta_barbara_aug2026 as sta_barbara_aug2026


def _barangay_index():
    """{(city_municipality, normalized_name): barangay_id}"""
    from _barangay_names import strip_accents_and_punct
    rows = db.session.execute(text(
        "SELECT barangay_id, barangay_name, city_municipality, population, num_households "
        "FROM barangays")).fetchall()
    idx = {}
    pop = {}
    for bid, name, lgu, population, households in rows:
        idx[(lgu, strip_accents_and_punct(name))] = bid
        pop[bid] = (population, households)
    return idx, pop


def _find_barangay(idx, lgu, raw_name, normalize_fn):
    from _barangay_names import strip_accents_and_punct
    key = (lgu, normalize_fn(raw_name) if normalize_fn else strip_accents_and_punct(raw_name))
    bid = idx.get(key)
    if bid is None:
        raise KeyError(f"no barangay match for {lgu!r} / {raw_name!r} (normalized {key[1]!r})")
    return bid


def _upsert_relief_event(lgu, label, report_date, source_file, is_raw, notes, typhoon_keys):
    existing = db.session.execute(text(
        "SELECT relief_event_id FROM relief_events "
        "WHERE city_municipality = :lgu AND label = :label"
    ), {"lgu": lgu, "label": label}).scalar()
    if existing:
        relief_event_id = existing
        db.session.execute(text(
            "UPDATE relief_events SET report_date = :rd, source_file = :sf, "
            "is_raw_report_extraction = :raw, notes = :notes WHERE relief_event_id = :id"
        ), {"rd": report_date, "sf": source_file, "raw": int(is_raw), "notes": notes,
            "id": relief_event_id})
        db.session.execute(text("DELETE FROM barangay_relief_records WHERE relief_event_id = :id"),
                            {"id": relief_event_id})
        db.session.execute(text("DELETE FROM relief_event_typhoons WHERE relief_event_id = :id"),
                            {"id": relief_event_id})
    else:
        db.session.execute(text(
            "INSERT INTO relief_events (city_municipality, label, report_date, source_file, "
            "is_raw_report_extraction, notes) VALUES (:lgu, :label, :rd, :sf, :raw, :notes)"
        ), {"lgu": lgu, "label": label, "rd": report_date, "sf": source_file,
            "raw": int(is_raw), "notes": notes})
        relief_event_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    for key in typhoon_keys:
        exists = db.session.execute(text(
            "SELECT 1 FROM typhoon_calendar WHERE typhoon_key = :k"), {"k": key}).scalar()
        if not exists:
            raise KeyError(f"typhoon_key {key!r} not found in typhoon_calendar - "
                            f"run scripts/typhoon_calendar_2021_2026.py first")
        db.session.execute(text(
            "INSERT INTO relief_event_typhoons (relief_event_id, typhoon_key) VALUES (:id, :k)"
        ), {"id": relief_event_id, "k": key})
    return relief_event_id


def _insert_records(relief_event_id, records):
    """records: list of (barangay_id, affected_families, affected_individuals,
    food_packs_given, total_families, total_individuals) - any of the numeric
    fields may be None (not reported)."""
    for bid, fam, ind, packs, tf, ti in records:
        db.session.execute(text(
            "INSERT INTO barangay_relief_records "
            "(relief_event_id, barangay_id, affected_families, affected_individuals, "
            " food_packs_given, total_families_snapshot, total_individuals_snapshot) "
            "VALUES (:eid, :bid, :fam, :ind, :packs, :tf, :ti)"
        ), {"eid": relief_event_id, "bid": bid, "fam": fam, "ind": ind, "packs": packs,
            "tf": tf, "ti": ti})


def _drop_events_not_in(lgu, source_file, labels):
    """A module that is re-delivered with fewer reports (e.g. Calasiao's
    2026-10-03 update dropped 13 typhoons) must not leave its old events
    behind - remove this module's events for this LGU that it no longer has."""
    ids = [r[0] for r in db.session.execute(text(
        "SELECT relief_event_id FROM relief_events "
        "WHERE city_municipality = :lgu AND source_file = :sf AND label NOT IN :labels"
    ).bindparams(bindparam("labels", expanding=True)),
        {"lgu": lgu, "sf": source_file, "labels": list(labels)})]
    for eid in ids:
        for table in ("barangay_relief_records", "relief_event_typhoons", "relief_events"):
            db.session.execute(text(f"DELETE FROM {table} WHERE relief_event_id = :id"), {"id": eid})
    if ids:
        print(f"  {lgu}: dropped {len(ids)} events no longer in {source_file}")


def load_new_module(module, lgu):
    idx, _pop = _barangay_index()
    normalize_fn = getattr(module, "normalize", None)
    labels = []
    for rep in module.REPORTS:
        # Build a readable label from the typhoon key(s), e.g. "maymay_2026"
        # -> "Maymay (2026)", "nika_2024"+"ofel_2024"+"pepito_2024" -> "Nika +
        # Ofel + Pepito (2024)" - not the raw report/typhoon key.
        rows = rep["rows"]
        report_date = rows[0]["date"].split(" to ")[0] if rows and rows[0].get("date") else None
        label_pretty = " + ".join(k.rsplit("_", 1)[0].title() for k in rep["typhoon_keys"])
        year = rep["typhoon_keys"][0].rsplit("_", 1)[1]
        eid = _upsert_relief_event(
            lgu=lgu, label=f"{label_pretty} ({year})", report_date=report_date,
            source_file=module.__name__, is_raw=False, notes=None,
            typhoon_keys=rep["typhoon_keys"])
        records = []
        for r in rows:
            bid = _find_barangay(idx, lgu, r["barangay"], normalize_fn)
            records.append((bid, r["affected_families"], r["affected_individuals"],
                             r["food_packs_given"], r.get("total_families"), r.get("total_individuals")))
        _insert_records(eid, records)
        labels.append(f"{label_pretty} ({year})")
        print(f"  {lgu}: {label_pretty} ({year}) -> {len(records)} barangay rows")
    _drop_events_not_in(lgu, module.__name__, labels)


# Source modules superseded by a newer dataset: their relief_events (and the
# rows hanging off them) are dropped before reloading, since the replacement
# module labels the same reports differently (e.g. "Dante/Emong + habagat
# (2025)" -> "Dante + Emong (2025)") and the label-keyed upsert would
# otherwise leave the old copies behind as duplicates.
_RETIRED_SOURCES = ("real_urdaneta_reports_2025", "real_calasiao_reports_2025")


def _drop_retired_sources():
    ids = [r[0] for r in db.session.execute(text(
        "SELECT relief_event_id FROM relief_events WHERE source_file IN :sources"
    ).bindparams(bindparam("sources", expanding=True)), {"sources": list(_RETIRED_SOURCES)})]
    for eid in ids:
        for table in ("barangay_relief_records", "relief_event_typhoons", "relief_events"):
            db.session.execute(text(f"DELETE FROM {table} WHERE relief_event_id = :id"), {"id": eid})
    if ids:
        print(f"  dropped {len(ids)} relief events from retired sources {_RETIRED_SOURCES}")


def load_sta_barbara_aug2026():
    idx, _pop = _barangay_index()
    lgu = "Santa Barbara"
    totals = sta_barbara_aug2026.combined_totals()
    eid = _upsert_relief_event(
        lgu=lgu, label="Aug 2026 DSWD+LGU distribution sheet", report_date="2026-08-19",
        source_file="sample_sta_barbara_aug2026", is_raw=True,
        notes="Supply distributed, not measured need; no affected-families figure or population "
              "snapshot in this source. Mapped to Maymay+Pilandok jointly - delivery window "
              "(19 Aug-2 Sep 2026) can't be cleanly split between the two storms from this sheet.",
        typhoon_keys=["maymay_2026", "pilandok_2026"])
    records = []
    for norm_name, packs in totals.items():
        bid = idx.get((lgu, norm_name))
        if bid is None:
            raise KeyError(f"no barangay match for {lgu!r} / {norm_name!r}")
        records.append((bid, None, None, packs, None, None))
    _insert_records(eid, records)
    print(f"  {lgu}: Aug 2026 sheet -> {len(records)} barangay rows (packs only)")


def load_all():
    _drop_retired_sources()
    print("Loading real relief-event modules...")
    load_new_module(calasiao_new, "Calasiao")
    load_new_module(sta_barbara_new, "Santa Barbara")
    load_new_module(urdaneta_new, "Urdaneta City")
    load_sta_barbara_aug2026()
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        load_all()
        n_events = db.session.execute(text("SELECT COUNT(*) FROM relief_events")).scalar()
        n_records = db.session.execute(text("SELECT COUNT(*) FROM barangay_relief_records")).scalar()
        per_lgu = db.session.execute(text(
            "SELECT city_municipality, COUNT(*) FROM relief_events GROUP BY city_municipality"
        )).fetchall()
        print(f"\nrelief_events: {n_events} rows, barangay_relief_records: {n_records} rows")
        for lgu, n in per_lgu:
            print(f"  {lgu}: {n} relief events")
