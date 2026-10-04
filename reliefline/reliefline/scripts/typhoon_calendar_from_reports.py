"""
The typhoon calendar, built ONLY from the real relief reports (2026-10-03, on
request). It replaces scripts/typhoon_calendar_2021_2026.py, a researched
36-storm list (news/PIA/DROMIC searches) that is no longer used.

Every storm named in a report's "Name of Typhoon" column becomes one
`typhoon_calendar` row (see _storms.py - "Luis & Maymay & Neneng & Pilandok"
is four storms; "Habagat" is not a storm). Dates come from the reports too:
  start_date = earliest report start date naming that storm (any LGU)
  end_date   = latest report end date naming that storm
  key_date   = start_date (Stage 2 counts each storm in this month)
  (all three overridden per storm by STORM_DATES - see below)
A combined report gives all of its storms the same dates - the reports don't
say when each storm hit - EXCEPT where STORM_DATES below gives a storm its
own dates (2026-10-03, on request: the four 2026 storms are counted as
separate storms in their own months).

What this means for the model (app/ml/train.py): Stage 2's storm frequency
and the P(relief) denominator count only storms that appear in at least one
LGU's relief report - storms that brought no relief anywhere are not in the
calendar, so P(relief) here is "relief events per reported storm".

Each storm also gets a disaster_events row (scope='province', status='ended',
is_reference=True), as the old calendar did, kept out of staff event pickers.

Called by scripts/load_relief_events.py (sync before loading, prune after);
run this file on its own to print the derived calendar.
"""
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _storms import date_range, storm_names

import real_calasiao_typhoons_2021_2026 as calasiao
import real_sta_barbara_typhoons_2021_2026 as sta_barbara
import real_urdaneta_typhoons_2021_2026 as urdaneta

SOURCES = [("Calasiao", calasiao), ("Santa Barbara", sta_barbara), ("Urdaneta City", urdaneta)]

CLASSIFICATION = "Not stated in relief reports"
IMPACT = "relief report"

# Per-storm dates for storms the reports only date as part of a combined
# report: typhoon_key -> (start, end, key_date, source). key_date decides the
# month Stage 2 counts the storm in. Chosen 2026-10-03 ("use best
# estimates"): Maymay and Pilandok from the news sources the earlier
# researched calendar cited; Luis and Neneng are ESTIMATES from PAGASA's
# naming order (names are given in order of formation: Kiyapo Jul 22 <
# Luis < Maymay Aug 4 < Neneng < Pilandok Aug 30). Replace with official
# PAGASA dates when available.
STORM_DATES = {
    "luis_2026": ("2026-08-01", "2026-08-03", "2026-08-01",
                  "ESTIMATE - named between Kiyapo (Jul 22) and Maymay (Aug 4); "
                  "counted in August, could have been late July"),
    "maymay_2026": ("2026-08-04", "2026-08-06", "2026-08-06",
                    "GMA News, Aug 6 2026 (as cited by the earlier researched calendar)"),
    "neneng_2026": ("2026-08-15", "2026-08-17", "2026-08-15",
                    "ESTIMATE - named between Maymay (Aug 4) and Pilandok (Aug 30), so August"),
    "pilandok_2026": ("2026-08-30", "2026-09-03", "2026-09-01",
                      "Manila Times/Rappler: TD Aug 30, tropical storm Sep 1, exited PAR Sep 3 "
                      "(as cited by the earlier researched calendar)"),
}


def derive():
    """{typhoon_key: {"name", "year", "start", "end", "key", "named_in": [...],
    "date_source"}} - dates from the reports, unless STORM_DATES overrides."""
    storms = {}
    for lgu, module in SOURCES:
        for key, raw in module._FILES.items():
            first = next(csv.DictReader(io.StringIO(raw)))
            start, end = date_range(first["Date ng Typhoon"])
            year = int(start[:4])
            for name in storm_names(first["Name of Typhoon"]):
                k = f"{name.lower()}_{year}"
                s = storms.setdefault(k, {"name": name, "year": year, "start": start, "end": end,
                                          "named_in": []})
                s["start"] = min(s["start"], start)
                s["end"] = max(s["end"], end)
                s["named_in"].append(f"{lgu} {first['Date ng Typhoon'].strip()}")
    for k, s in storms.items():
        if k in STORM_DATES:
            s["start"], s["end"], s["key"], s["date_source"] = STORM_DATES[k]
        else:
            s["key"], s["date_source"] = s["start"], "relief reports"
    return storms


def sync():
    """Upsert every derived storm into typhoon_calendar (+ its reference
    disaster_events row). Does not commit."""
    from sqlalchemy import text
    from app.extensions import db

    for key, s in sorted(derive().items(), key=lambda kv: kv[1]["start"]):
        label = f"{s['name']} ({s['year']})"
        event_id = db.session.execute(text(
            "SELECT event_id FROM disaster_events WHERE event_name = :n AND is_reference = 1"
        ), {"n": label}).scalar()
        if event_id is None:
            db.session.execute(text(
                "INSERT INTO disaster_events "
                "(event_name, event_type, status, weather_condition, start_date, end_date, "
                " scope, city_municipality, is_reference) "
                "VALUES (:n, 'typhoon', 'ended', :cls, :s, :e, 'province', NULL, 1)"
            ), {"n": label, "cls": CLASSIFICATION, "s": s["start"], "e": s["end"]})
            event_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        else:
            db.session.execute(text(
                "UPDATE disaster_events SET weather_condition = :cls, start_date = :s, end_date = :e "
                "WHERE event_id = :id"
            ), {"cls": CLASSIFICATION, "s": s["start"], "e": s["end"], "id": event_id})

        notes = ("Named in relief reports: " + "; ".join(s["named_in"])
                 + f". Dates: {s['date_source']}")
        db.session.execute(text(
            "INSERT INTO typhoon_calendar "
            "(typhoon_key, typhoon_name, classification, start_date, end_date, key_date, year, "
            " pangasinan_impact_confirmed, research_notes, disaster_event_id) "
            "VALUES (:k, :n, :cls, :s, :e, :kd, :y, :conf, :notes, :eid) "
            "ON DUPLICATE KEY UPDATE "
            "typhoon_name=:n, classification=:cls, start_date=:s, end_date=:e, key_date=:kd, "
            "year=:y, pangasinan_impact_confirmed=:conf, research_notes=:notes, disaster_event_id=:eid"
        ), {"k": key, "n": s["name"], "cls": CLASSIFICATION, "s": s["start"], "e": s["end"], "kd": s["key"],
            "y": s["year"], "conf": IMPACT, "notes": notes, "eid": event_id})


def prune():
    """Remove calendar storms no relief report names (e.g. the old researched
    list's Jolina, Kiko, Ramil...), with their reference disaster_events
    rows. Run AFTER the relief events are reloaded, so nothing still links to
    them; refuses (raises) if something does. Does not commit."""
    from sqlalchemy import bindparam, text
    from app.extensions import db

    keep = list(derive())
    stale = db.session.execute(text(
        "SELECT typhoon_key, disaster_event_id FROM typhoon_calendar WHERE typhoon_key NOT IN :keep"
    ).bindparams(bindparam("keep", expanding=True)), {"keep": keep}).fetchall()
    if not stale:
        return 0
    keys = [r[0] for r in stale]
    linked = db.session.execute(text(
        "SELECT DISTINCT typhoon_key FROM relief_event_typhoons WHERE typhoon_key IN :keys"
    ).bindparams(bindparam("keys", expanding=True)), {"keys": keys}).scalars().all()
    if linked:
        raise RuntimeError(f"calendar storms still linked to relief events, not pruned: {linked}")
    db.session.execute(text("DELETE FROM typhoon_calendar WHERE typhoon_key IN :keys")
                       .bindparams(bindparam("keys", expanding=True)), {"keys": keys})
    event_ids = [r[1] for r in stale if r[1] is not None]
    if event_ids:
        db.session.execute(text(
            "DELETE FROM disaster_events WHERE is_reference = 1 AND event_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True)), {"ids": event_ids})
    return len(keys)


if __name__ == "__main__":
    storms = derive()
    for key, s in sorted(storms.items(), key=lambda kv: kv[1]["start"]):
        print(f"{key:<16} {s['start']} to {s['end']}  named in {len(s['named_in'])} report(s)")
    print(f"\n{len(storms)} storms named in the relief reports.")
