"""
The verified Pangasinan typhoon calendar, 2021-2026 (36 events) - the
authoritative source for Stage 2's climatological monthly frequency and the
P(relief) denominator (see app/ml/train.py). Supersedes
app.ml.climate_reference.EVENTS, which anchored the now-deleted synthetic
generator.

`pangasinan_impact_confirmed` is a RESEARCH-CONFIDENCE flag only (did a news/
DROMIC search turn up a source naming Pangasinan for this storm), NOT ground
truth of whether relief was distributed. Real barangay relief records already
contradict it for many "not confirmed" entries (e.g. Kiko, Jolina, Fabian,
Florita, Karding, Neneng, Paeng, Dodong, Goring, Carina, Butchoy, Enteng,
Kristine, Leon, Marce, Nika, Ofel, Pepito all have real Calasiao and/or
Urdaneta relief reports despite being marked "not confirmed in sources
reviewed" here). app.ml.train.p_relief() deliberately computes P(relief) from
real barangay_relief_records coverage, never from this column.

Run this file to load the 36 rows into `typhoon_calendar` and create their
matching `disaster_events` rows (scope='province', status='ended',
is_reference=True - see scripts/apply_relief_schema.py's docstring for why
is_reference exists).
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _d(s):
    return date.fromisoformat(s) if s else None


# key, name, classification, start, end, key_date, year, impact_confirmed, notes
EVENTS = [
    ("fabian_2021", "Fabian", "Typhoon", "2021-07-16", "2021-07-24", None, 2021,
     "not confirmed", "No PH landfall (passed offshore); check DROMIC for habagat-only effects in Pangasinan"),
    ("jolina_2021", "Jolina", "Typhoon", "2021-09-06", "2021-09-08", "2021-09-07", 2021,
     "not confirmed", "DROMIC tracked mainly Visayas/Batangas/Cavite/Bataan landfalls; no Pangasinan mention found"),
    ("kiko_2021", "Kiko", "Super Typhoon", "2021-09-07", "2021-09-12", "2021-09-11", 2021,
     "not confirmed", "Landfall Batanes; DROMIC noted Regions I-II-III-CAR affected in general but no Pangasinan-specific figure found yet"),
    ("maring_2021", "Maring", "Severe Tropical Storm", "2021-10-07", "2021-10-13", "2021-10-11", 2021,
     "confirmed", "PIA: \"Pangasinan braces for Typhoon Maring\"; DSWD Field Office I (Ilocos Region incl. Pangasinan) distributed 27518 relief packs to Maring-affected families"),

    ("florita_2022", "Florita", "Severe Tropical Storm", "2022-08-21", "2022-08-24", "2022-08-23", 2022,
     "not confirmed", "Landfall Isabela; no Pangasinan-specific report found yet"),
    ("karding_2022", "Karding", "Super Typhoon", "2022-09-22", "2022-09-26", "2022-09-25", 2022,
     "not confirmed", "Landfalls Polillo/Aurora; PAGASA-DOST final report reviewed did not single out Pangasinan"),
    ("neneng_2022", "Neneng", "Typhoon", "2022-10-13", "2022-10-17", "2022-10-16", 2022,
     "not confirmed", "Landfall Calayan Cagayan; no Pangasinan-specific report found yet"),
    ("paeng_2022", "Paeng", "Severe Tropical Storm", "2022-10-26", "2022-10-31", "2022-10-29", 2022,
     "not confirmed", "NDRRMC reports centered on Bicol/Quezon/Mindanao; no Pangasinan-specific figure found (needs DROMIC check)"),

    ("dodong_2023", "Dodong", "Severe Tropical Storm", "2023-07-13", "2023-07-18", None, 2023,
     "not confirmed", "Landfall Aurora; enhanced monsoon across Luzon generally; no Pangasinan-specific figure found yet"),
    ("egay_2023", "Egay", "Typhoon", "2023-07-21", "2023-07-27", "2023-07-26", 2023,
     "confirmed (combined Egay+Falcon+habagat event)", "PNA: DSWD aid reached Urbiztondo, Alcala, Basista, Mangatarem, Pangasinan; 112756 families affected province-wide"),
    ("falcon_2023", "Falcon", "Typhoon", "2023-07-29", "2023-08-01", None, 2023,
     "confirmed (combined Egay+Falcon+habagat event)", "Same PNA report as Egay - combined effect of both systems plus habagat on Pangasinan"),
    ("goring_2023", "Goring", "Super Typhoon", "2023-08-23", "2023-08-30", None, 2023,
     "not confirmed", "Looped east of Luzon/crossed Babuyan Islands; no Pangasinan-specific figure found yet"),

    ("carina_2024", "Carina", "Typhoon (offshore; became Typhoon Gaemi outside PAR)", "2024-07-19", "2024-07-20", None, 2024,
     "not directly confirmed", "No PH landfall; combined with Butchoy+habagat caused Luzon-wide flooding (NDRRMC: 3.6M+ affected) but no Pangasinan-specific figure found yet"),
    ("butchoy_2024", "Butchoy", "Tropical Depression", "2024-07-19", "2024-07-20", None, 2024,
     "not directly confirmed", "Formed and exited PAR within ~1 day as TD (04W), later became TS Prapiroon outside PAR; DSWD DROMIC monitored combined Butchoy+Carina+habagat effects through Aug 10 but no Pangasinan-specific figure found yet"),
    ("enteng_2024", "Enteng", "Typhoon", "2024-08-31", "2024-09-09", "2024-09-02", 2024,
     "not confirmed", "Landfall Casiguran Aurora; no Pangasinan-specific figure found yet"),
    ("kristine_2024", "Kristine", "Severe Tropical Storm", "2024-10-19", "2024-10-29", "2024-10-24", 2024,
     "not confirmed", "Landfall Divilacan Isabela; UNICEF/NDRRMC reports centered on Bicol/Isabela/CAR; no Pangasinan-specific figure found yet"),
    ("leon_2024", "Leon", "Super Typhoon", "2024-10-24", "2024-11-01", None, 2024,
     "not confirmed", "Storm surge flooding Cagayan/Batanes; no Pangasinan-specific figure found yet"),
    ("marce_2024", "Marce", "Super Typhoon", "2024-11-03", "2024-11-12", "2024-11-07", 2024,
     "not confirmed", "Landfalls Cagayan; no Pangasinan-specific figure found yet"),
    ("nika_2024", "Nika", "Typhoon", "2024-11-09", "2024-11-15", "2024-11-10", 2024,
     "not confirmed", "Landfall Dilasag Aurora; NDRRMC combined Nika+Ofel+Pepito report: 3.9M affected nationwide, but figure not broken down to Pangasinan in sources reviewed"),
    ("ofel_2024", "Ofel", "Super Typhoon", "2024-11-12", "2024-11-16", "2024-11-14", 2024,
     "not confirmed", "Landfall Baggao Cagayan; see Nika note above (combined NDRRMC figure only)"),
    ("pepito_2024", "Pepito", "Super Typhoon", "2024-11-09", "2024-11-20", "2024-11-16", 2024,
     "not confirmed", "Landfalls Catanduanes/Aurora; see Nika note above (combined NDRRMC figure only)"),

    ("bising_2025", "Bising", "Typhoon", "2025-07-04", "2025-07-11", None, 2025,
     "not confirmed", "NDRRMC/PIA report centered on Central Luzon (13006 affected in 14 barangays); no Pangasinan-specific figure found yet"),
    ("crising_2025", "Crising", "Severe Tropical Storm", "2025-07-16", "2025-07-22", "2025-07-18", 2025,
     "confirmed", "PIA: combined Crising+habagat flooded Calasiao (Marusay River overflowed 17 barangays); Sta. Barbara placed under state of calamity; 585178 individuals affected province-wide (July 24 2025 report)"),
    ("dante_2025", "Dante", "Tropical Storm", "2025-07-22", "2025-07-26", None, 2025,
     "not confirmed", "Tracked mostly offshore north of Luzon; minor reported PH impact"),
    ("emong_2025", "Emong", "Severe Tropical Storm", "2025-07-22", "2025-08-03", "2025-07-24", 2025,
     "confirmed", "Direct landfall Agno, Pangasinan - strongest typhoon to hit Pangasinan in 16 years; 49000+ affected, 25 dead; Alaminos also affected"),
    ("isang_2025", "Isang", "Typhoon", "2025-08-22", "2025-08-26", "2025-08-22", 2025,
     "not confirmed", "Landfall Casiguran Aurora; combined with habagat affected Central Luzon/Metro Manila; no Pangasinan-specific figure found yet"),
    ("mirasol_2025", "Mirasol", "Severe Tropical Storm", "2025-09-16", "2025-09-20", "2025-09-17", 2025,
     "not confirmed", "Landfall Casiguran Aurora; weakened over Cordillera; no Pangasinan-specific figure found yet"),
    ("nando_2025", "Nando", "Super Typhoon", "2025-09-17", "2025-09-25", "2025-09-22", 2025,
     "confirmed", "PIA: \"Pangasinan speeds up relief for Super Typhoon Nando-affected families\" (province-wide relief operations confirmed; barangay breakdown not in this source)"),
    ("paolo_2025", "Paolo", "Typhoon", "2025-10-01", "2025-10-06", "2025-10-03", 2025,
     "partial (province-wide alert only)", "PNA: Pangasinan placed on red alert; Signal No. 2 in 29 northern towns/cities (San Fabian, Sison, Pozorrubio, Dagupan, Bolinao, etc.) - Calasiao/Sta. Barbara/Urdaneta not specifically named in this source"),
    ("ramil_2025", "Ramil", "Severe Tropical Storm", "2025-10-16", "2025-10-23", "2025-10-18", 2025,
     "not confirmed", "Exited PAR without PH landfall per PAGASA/Rappler; no Pangasinan-specific figure found yet"),
    ("uwan_2025", "Uwan", "Super Typhoon", "2025-11-07", "2025-11-13", "2025-11-09", 2025,
     "partial (province-wide figure only)", "PNA: 12270 families / 47679 individuals affected across 255 barangays in 25 municipalities + 1 city in Pangasinan (Nov 10 2025); PIA also reported evacuation advisories - list of specific municipalities not itemized in sources reviewed"),

    ("ester_2026", "Ester", "Tropical Depression", "2026-06-03", "2026-06-06", None, 2026,
     "not confirmed", "Enhanced habagat rains in Luzon generally; no Pangasinan-specific figure found yet"),
    ("gardo_2026", "Gardo", "Tropical Storm", "2026-06-22", "2026-06-27", "2026-06-25", 2026,
     "not confirmed", "Exited PAR Jun 26 but habagat persisted in Luzon; no Pangasinan-specific figure found yet"),
    ("kiyapo_2026", "Kiyapo", "Typhoon", "2026-07-22", "2026-07-25", None, 2026,
     "not confirmed", "Moved away from Luzon; monsoon rain persisted; no Pangasinan-specific figure found yet"),
    ("maymay_2026", "Maymay", "Tropical Storm", "2026-08-04", "2026-08-06", "2026-08-06", 2026,
     "confirmed", "GMA News (Aug 6 2026): 6500+ families affected; Calasiao Brgy. Lasip flooded above knee level; Sta. Barbara (Sinucalan River) also monitored; 40+ barangays flooded province-wide"),
    ("pilandok_2026", "Pilandok", "Tropical Storm", "2026-08-30", "2026-09-03", "2026-09-01", 2026,
     "confirmed (province-wide rainfall warning)", "Manila Times/Rappler: formed as TD Aug 30, became TS Sept 1 (international name Krovanh), exited PAR Sept 3; PAGASA orange rainfall warning (up to 200mm) explicitly named Pangasinan among affected provinces"),
]

assert len(EVENTS) == 36, f"expected 36 calendar events, got {len(EVENTS)}"


def load():
    from sqlalchemy import text
    from app.extensions import db

    for key, name, classification, start, end, key_date, year, confirmed, notes in EVENTS:
        # One DisasterEvent per calendar typhoon, flagged is_reference so the
        # staff's live event pickers (which query DisasterEvent unfiltered in
        # a few places) don't show 36 years-old calendar rows as if they were
        # something a CSWDO/PSWDO admin could act on today.
        event_id = db.session.execute(text(
            "SELECT event_id FROM disaster_events WHERE event_name = :n AND is_reference = 1"
        ), {"n": f"{name} ({year})"}).scalar()
        if event_id is None:
            db.session.execute(text(
                "INSERT INTO disaster_events "
                "(event_name, event_type, status, weather_condition, start_date, end_date, "
                " scope, city_municipality, is_reference) "
                "VALUES (:n, 'typhoon', 'ended', :cls, :s, :e, 'province', NULL, 1)"
            ), {"n": f"{name} ({year})", "cls": classification, "s": start, "e": end or start})
            event_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar()

        db.session.execute(text(
            "INSERT INTO typhoon_calendar "
            "(typhoon_key, typhoon_name, classification, start_date, end_date, key_date, year, "
            " pangasinan_impact_confirmed, research_notes, disaster_event_id) "
            "VALUES (:k, :n, :cls, :s, :e, :kd, :y, :conf, :notes, :eid) "
            "ON DUPLICATE KEY UPDATE "
            "typhoon_name=:n, classification=:cls, start_date=:s, end_date=:e, key_date=:kd, "
            "year=:y, pangasinan_impact_confirmed=:conf, research_notes=:notes, disaster_event_id=:eid"
        ), {"k": key, "n": name, "cls": classification, "s": start, "e": end, "kd": key_date,
            "y": year, "conf": confirmed, "notes": notes, "eid": event_id})
    db.session.commit()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        load()
        from sqlalchemy import text
        from app.extensions import db
        n = db.session.execute(text("SELECT COUNT(*) FROM typhoon_calendar")).scalar()
        m = db.session.execute(text(
            "SELECT COUNT(*) FROM disaster_events WHERE is_reference = 1")).scalar()
        print(f"typhoon_calendar: {n} rows, disaster_events(is_reference=1): {m} rows")
