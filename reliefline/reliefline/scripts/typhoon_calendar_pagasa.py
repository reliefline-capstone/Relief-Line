"""
The typhoon calendar: the 33 tropical cyclones affecting / relevant to
Pangasinan, 2021-2026, from the user-supplied table "Typhoon Events
Affecting / Relevant to Pangasinan, 2021-2026" (final.pdf, a corrected
research working table prepared 2026-10-03, dates and classifications
checked against PAGASA tropical cyclone preliminary reports, PAGASA's
August 2026 monthly review and Provincial Government of Pangasinan posts).
Adopted 2026-10-05 on request: "use this as a basis for how many typhoons
per month recently every year has". It replaces
scripts/typhoon_calendar_from_reports.py (24 storms, only the ones named in
a relief report).

What this means for the model (app/ml/train.py):
  * Stage 2's monthly frequency (climatology_by_month) counts all 33 storms
    in the month they STARTED (key_date = start_date).
  * P(relief) = relief events with packs / 33, i.e. relief operations per
    storm on this list. The 9 storms no relief report names (Jolina 2021,
    Florita 2022, Neneng 2022, Falcon 2023, Goring 2023, Marce 2024, Isang
    2025, Ramil 2025, Obet 2026) count as storms that brought no relief
    operation. The list itself notes that being listed does not prove a
    direct impact on Pangasinan - which is exactly what P(relief) absorbs.

Every storm a relief report names (scripts/_storms.py) must be on this
list - derive() raises if one isn't, so a new report can't silently link to
a storm the frequency count doesn't know. The reports still record which
LGU reports name each storm (research_notes).

Each storm also gets a disaster_events row (scope='province', status='ended',
is_reference=True), kept out of staff event pickers.

Called by scripts/load_relief_events.py (sync before loading, prune after);
run this file on its own to print the calendar and its monthly counts.
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

REPORT_SOURCES = [("Calasiao", calasiao), ("Santa Barbara", sta_barbara), ("Urdaneta City", urdaneta)]

SOURCE = "final.pdf (PAGASA-checked working table, 2026-10-03)"

# (name, start, end, peak classification) - transcribed from final.pdf.
STORMS = [
    ("Fabian",   "2021-07-16", "2021-07-24", "Typhoon"),
    ("Jolina",   "2021-09-05", "2021-09-08", "Typhoon"),
    ("Maring",   "2021-10-07", "2021-10-13", "Severe Tropical Storm"),
    ("Florita",  "2022-08-20", "2022-08-26", "Severe Tropical Storm"),
    ("Karding",  "2022-09-21", "2022-09-29", "Super Typhoon"),
    ("Neneng",   "2022-10-13", "2022-10-20", "Typhoon"),
    ("Paeng",    "2022-10-26", "2022-11-03", "Typhoon"),
    ("Egay",     "2023-07-20", "2023-07-29", "Super Typhoon"),
    ("Falcon",   "2023-07-26", "2023-08-11", "Typhoon"),
    ("Goring",   "2023-08-22", "2023-09-03", "Super Typhoon"),
    ("Carina",   "2024-07-19", "2024-07-28", "Super Typhoon"),
    ("Enteng",   "2024-09-01", "2024-09-08", "Super Typhoon"),
    ("Kristine", "2024-10-20", "2024-10-28", "Typhoon"),
    ("Leon",     "2024-10-23", "2024-11-01", "Super Typhoon"),
    ("Marce",    "2024-11-03", "2024-11-12", "Typhoon"),
    ("Nika",     "2024-11-08", "2024-11-15", "Typhoon"),
    ("Ofel",     "2024-11-10", "2024-11-16", "Super Typhoon"),
    ("Pepito",   "2024-11-07", "2024-11-20", "Super Typhoon"),
    ("Crising",  "2025-07-16", "2025-07-23", "Typhoon"),
    ("Dante",    "2025-07-22", "2025-07-26", "Tropical Storm"),
    ("Emong",    "2025-07-22", "2025-08-01", "Typhoon"),
    ("Isang",    "2025-08-21", "2025-08-26", "Typhoon"),
    ("Mirasol",  "2025-09-16", "2025-09-20", "Severe Tropical Storm"),
    ("Nando",    "2025-09-17", "2025-09-25", "Super Typhoon"),
    ("Opong",    "2025-09-23", "2025-09-29", "Typhoon"),
    ("Paolo",    "2025-10-01", "2025-10-06", "Typhoon"),
    ("Ramil",    "2025-10-16", "2025-10-23", "Severe Tropical Storm"),
    ("Uwan",     "2025-11-03", "2025-11-13", "Super Typhoon"),
    ("Luis",     "2026-08-01", "2026-08-03", "Tropical Depression"),
    ("Maymay",   "2026-08-04", "2026-08-06", "Tropical Storm"),
    ("Neneng",   "2026-08-18", "2026-08-20", "Tropical Depression"),
    ("Obet",     "2026-08-24", "2026-08-24", "Typhoon"),
    ("Pilandok", "2026-08-30", "2026-09-03", "Tropical Storm"),
]


def _report_mentions():
    """{typhoon_key: ["<LGU> <report dates>", ...]} for every storm a relief
    report names."""
    mentions = {}
    for lgu, module in REPORT_SOURCES:
        for raw in module._FILES.values():
            first = next(csv.DictReader(io.StringIO(raw)))
            year = int(date_range(first["Date ng Typhoon"])[0][:4])
            for name in storm_names(first["Name of Typhoon"]):
                mentions.setdefault(f"{name.lower()}_{year}", []).append(
                    f"{lgu} {first['Date ng Typhoon'].strip()}")
    return mentions


def derive():
    """{typhoon_key: {"name", "year", "start", "end", "key", "classification",
    "named_in": [...]}} for all 33 listed storms. Raises if a relief report
    names a storm that isn't listed."""
    storms = {}
    for name, start, end, cls in STORMS:
        year = int(start[:4])
        storms[f"{name.lower()}_{year}"] = {"name": name, "year": year, "start": start, "end": end,
                                            "key": start, "classification": cls, "named_in": []}
    mentions = _report_mentions()
    unlisted = sorted(set(mentions) - set(storms))
    if unlisted:
        raise KeyError(f"relief reports name storms not in the PAGASA list: {unlisted} - "
                       f"add them to STORMS in scripts/typhoon_calendar_pagasa.py")
    for k, where in mentions.items():
        storms[k]["named_in"] = where
    return storms


def sync():
    """Upsert every listed storm into typhoon_calendar (+ its reference
    disaster_events row). Does not commit."""
    from sqlalchemy import text
    from app.extensions import db

    for key, s in sorted(derive().items(), key=lambda kv: (kv[1]["start"], kv[0])):
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
            ), {"n": label, "cls": s["classification"], "s": s["start"], "e": s["end"]})
            event_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        else:
            db.session.execute(text(
                "UPDATE disaster_events SET weather_condition = :cls, start_date = :s, end_date = :e "
                "WHERE event_id = :id"
            ), {"cls": s["classification"], "s": s["start"], "e": s["end"], "id": event_id})

        impact = "relief report" if s["named_in"] else "listed, no relief report"
        notes = (f"Source: {SOURCE}. "
                 + ("Named in relief reports: " + "; ".join(s["named_in"]) + "."
                    if s["named_in"] else "Not named in any LGU relief report."))
        db.session.execute(text(
            "INSERT INTO typhoon_calendar "
            "(typhoon_key, typhoon_name, classification, start_date, end_date, key_date, year, "
            " pangasinan_impact_confirmed, research_notes, disaster_event_id) "
            "VALUES (:k, :n, :cls, :s, :e, :kd, :y, :conf, :notes, :eid) "
            "ON DUPLICATE KEY UPDATE "
            "typhoon_name=:n, classification=:cls, start_date=:s, end_date=:e, key_date=:kd, "
            "year=:y, pangasinan_impact_confirmed=:conf, research_notes=:notes, disaster_event_id=:eid"
        ), {"k": key, "n": s["name"], "cls": s["classification"], "s": s["start"], "e": s["end"],
            "kd": s["key"], "y": s["year"], "conf": impact, "notes": notes, "eid": event_id})


def prune():
    """Remove calendar storms not on the list, with their reference
    disaster_events rows. Run AFTER the relief events are reloaded, so
    nothing still links to them; refuses (raises) if something does. Does
    not commit."""
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
    from collections import Counter

    storms = derive()
    for key, s in sorted(storms.items(), key=lambda kv: (kv[1]["start"], kv[0])):
        tag = f"named in {len(s['named_in'])} report(s)" if s["named_in"] else "no relief report"
        print(f"{key:<16} {s['start']} to {s['end']}  {s['classification']:<22} {tag}")
    by_month = Counter(int(s["start"][5:7]) for s in storms.values())
    print(f"\n{len(storms)} storms; by start month: "
          + ", ".join(f"{m}: {by_month[m]}" for m in sorted(by_month)))
