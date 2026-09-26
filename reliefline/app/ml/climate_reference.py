"""
Real-world reference data behind the time-series forecaster: climate normals,
ENSO history and the calendar of storms/monsoon floods that actually affected
Pangasinan (2021-2025). The synthetic history in
scripts/seed_monthly_history.py is generated FROM this module, so the
seasonal shape and the timing of the demand spikes are grounded in real
events, not invented ones.

What is verified vs. judged (kept explicit on purpose, for the panel):

  VERIFIED (looked up, source noted)
    * RAINFALL_NORMAL_MM / RAINY_DAYS - PAGASA Dagupan station, 1991-2020
      normals (Wikipedia "Dagupan" climate table, transcribed from PAGASA).
    * Climate type / seasons - Dagupan is Type I: dry Nov-May, wet Jun-Oct,
      heaviest rain Jul-Aug (City Government of Dagupan, "Climate").
    * ONI - NOAA CPC Oceanic Nino Index, ERSSTv6 table (2021-2025).
    * PAGASA: 20.2 tropical cyclones per year enter the PAR (1991-2020),
      ~70% of them Jul-Oct.
    * EVENTS - dates, names and the fact that Pangasinan was affected are
      from NDRRMC/ReliefWeb/Wikipedia/PIA reports (per-event note below).

  MEASURED (real per-barangay records)
    * Urdaneta City CSWDO reports for the four 2025 events (Dante/Emong+habagat
      Jul, Mirasol/Nando Sep, Paolo Oct, Uwan Nov) - scripts/real_urdaneta_
      reports_2025.py. They showed the impact of one storm differs a lot by
      LGU (Paolo was Urdaneta's worst event, Jul 2025 among its mildest), so
      severity below is PER LGU where a report exists.

  JUDGED (a modelling decision, not a measurement)
    * severity (1-5) - a relative impact class. `severity` is the default for
      every LGU, judged from reported provincial impact (state of calamity,
      evacuations, flooding in Calasiao / Sta. Barbara...); `lgu_severity`
      overrides it for an LGU with a real report (severity_for()). Class 5 is
      anchored to the Aug 2026 Sta. Barbara relief-distribution sheet; classes
      1-4 are anchored to the Urdaneta 2025 reports (see scripts/
      seed_monthly_history.py, calibration_report).
    * TC_CLIMO monthly split - the annual total and the Jul-Oct share match
      PAGASA, but the month-by-month split is approximate.

Storms whose reports did NOT mention Pangasinan (e.g. Yagi/Enteng Sep 2024,
Koinu/Jenny Oct 2023) are deliberately left out.
"""
from datetime import date

# PAGASA Dagupan normals 1991-2020, mm per month (Jan..Dec). Annual 2,516.7.
RAINFALL_NORMAL_MM = [5.7, 9.5, 23.0, 69.5, 218.2, 335.5, 532.7, 619.5, 401.6, 226.6, 54.9, 20.0]
RAINY_DAYS = [2, 2, 3, 4, 11, 16, 20, 21, 19, 9, 5, 3]

# Type I climate (Dagupan / Pangasinan): dry Nov-May, wet Jun-Oct.
WET_SEASON_MONTHS = {6, 7, 8, 9, 10}
# Peak typhoon / habagat months (PAGASA: ~70% of TCs Jul-Oct). Extra weight
# in the forecast, per the team's "give more weight to the rainy season".
PEAK_MONTHS = {7, 8, 9, 10}

# Approximate tropical cyclones entering the PAR per month (sums to ~20.9;
# PAGASA annual mean is 20.2, Jul-Oct share ~67-70%).
TC_CLIMO = [0.5, 0.3, 0.4, 0.6, 0.9, 1.7, 3.3, 4.0, 3.7, 3.0, 1.7, 0.8]

# NOAA CPC ONI (ERSSTv6). Each row is the 3-month season CENTRED on the month,
# so index 0 = DJF = January ... index 11 = NDJ = December.
ONI = {
    2021: [-1.0, -0.9, -0.7, -0.6, -0.4, -0.3, -0.3, -0.5, -0.6, -0.8, -0.9, -0.8],
    2022: [-0.8, -0.7, -0.8, -0.9, -0.8, -0.7, -0.7, -0.8, -0.9, -0.9, -0.8, -0.7],
    2023: [-0.5, -0.3, -0.1, 0.2, 0.5, 0.7, 1.0, 1.3, 1.5, 1.7, 1.9, 2.0],
    2024: [1.8, 1.5, 1.2, 0.8, 0.4, 0.2, 0.1, 0.0, -0.1, -0.2, -0.3, -0.4],
    2025: [-0.5, -0.2, -0.1, 0.0, 0.0, 0.0, -0.1, -0.3, -0.4, -0.6, -0.6, -0.6],
}


def oni_for(year, month):
    """ONI for a calendar month; the latest known value is carried forward
    for any month past the table (ENSO is highly persistent month to month -
    update ONI above as new NOAA values are published)."""
    if year in ONI:
        return ONI[year][month - 1]
    last_year = max(ONI)
    return ONI[last_year][-1] if year > last_year else ONI[min(ONI)][month - 1]


# Real storms / monsoon episodes that affected Pangasinan. severity: 1-5.
# `end` may fall in the following month - the generator spills part of the
# relief into it (deliveries run ~2 weeks after an event, per the Aug 2026
# Sta. Barbara sheet).
EVENTS = [
    {"key": "fabian_2021", "name": "Habagat enhanced by Typhoon In-fa (Fabian)", "start": date(2021, 7, 20), "end": date(2021, 7, 23), "severity": 3,
     "note": "Heavy monsoon rain over Central Luzon/Pangasinan/Ilocos; 2 swept away in Aguilar, Pangasinan; 202,213 people (50,676 families) affected nationally (NDRRMC via Wikipedia)."},
    {"key": "maring_2021", "name": "Severe Tropical Storm Nyatoh (Maring)", "start": date(2021, 10, 11), "end": date(2021, 10, 12), "severity": 3,
     "note": "Widespread flooding in Pangasinan and La Union, ~1,100 evacuated (Inquirer)."},
    {"key": "karding_2022", "name": "Super Typhoon Noru (Karding)", "start": date(2022, 9, 25), "end": date(2022, 9, 26), "severity": 2,
     "note": "Landfall Polillo/Aurora, crossed Central Luzon and exited near Zambales/Pangasinan; 1.07M people affected nationally."},
    {"key": "egay_2023", "name": "Super Typhoon Doksuri (Egay) + habagat", "start": date(2023, 7, 25), "end": date(2023, 7, 27), "severity": 3,
     "note": "Flooding/roof damage in Pangasinan incl. Calasiao, Lingayen, Binmaley; Ilocos hardest hit; 2.9M affected nationally."},
    {"key": "goring_2023", "name": "Habagat enhanced by Typhoon Saola (Goring) + Haikui", "start": date(2023, 8, 27), "end": date(2023, 9, 1), "severity": 2,
     "note": "Enhanced southwest monsoon; Pangasinan and Ilocos reported flooding/water damage; 1.09M affected nationally."},
    {"key": "carina_2024", "name": "Super Typhoon Gaemi (Carina) + habagat", "start": date(2024, 7, 22), "end": date(2024, 7, 26), "severity": 4,
     "note": "Pangasinan initial damage P222.5M infrastructure / P24.5M agriculture (Inquirer/ReliefWeb); 4.8M affected nationally."},
    {"key": "julian_2024", "name": "Super Typhoon Krathon (Julian)", "start": date(2024, 10, 1), "end": date(2024, 10, 3), "severity": 1,
     "note": "Pangasinan under Signal No. 1 only; brunt on Batanes/Babuyan; 380,778 affected nationally."},
    {"key": "kristine_2024", "name": "Severe Tropical Storm Trami (Kristine)", "start": date(2024, 10, 22), "end": date(2024, 10, 25), "severity": 2,
     "note": "Storm surge inundated six barangays in Lingayen, Pangasinan; Central Luzon 1.09M affected."},
    {"key": "pepito_2024", "name": "Super Typhoon Man-yi (Pepito)", "start": date(2024, 11, 16), "end": date(2024, 11, 17), "severity": 2,
     "note": "Landfall Catanduanes then Aurora; Pangasinan among affected provinces; 4.24M affected nationally."},
    {"key": "crising_2025", "name": "Habagat + TS Wipha (Crising) + TS Dante + TS Co-may (Emong)", "start": date(2025, 7, 15), "end": date(2025, 7, 26), "severity": 5,
     "lgu_severity": {"Urdaneta City": 2},
     "note": "Co-may made landfall over Pangasinan; Calasiao residents used rafts; 1,700+ homes damaged in Mangaldan. Urdaneta CSWDO report (as of Aug 1): only 2,704 families affected - a mild event there."},
    {"key": "nando_2025", "name": "Habagat + TC Mirasol + Super Typhoon Ragasa (Nando)", "start": date(2025, 9, 20), "end": date(2025, 9, 26), "severity": 3,
     "lgu_severity": {"Urdaneta City": 3},
     "note": "Pangasinan/Ilocos/La Union under wind signals with enhanced habagat. Urdaneta CSWDO report (Sep 26): 8,938 families affected, 5,731 packs served."},
    {"key": "paolo_2025", "name": "Typhoon Matmo (Paolo)", "start": date(2025, 10, 1), "end": date(2025, 10, 4), "severity": 3,
     "lgu_severity": {"Urdaneta City": 4},
     "note": "Landfall Dinapigue, Isabela Oct 3; Pangasinan and Ilocos affected. Urdaneta CSWDO report (Oct 4): 14,012 families affected, 12,424 packs served - Urdaneta's worst event of 2025."},
    {"key": "uwan_2025", "name": "Super Typhoon Fung-wong (Uwan)", "start": date(2025, 11, 9), "end": date(2025, 11, 10), "severity": 2,
     "lgu_severity": {"Urdaneta City": 1},
     "note": "Landfall Dinalungan, Aurora Nov 9; Pangasinan placed under a state of calamity. Urdaneta CSWDO report (Nov 25): only 1,380 families affected, 950 packs served."},
]

def severity_for(event, lgu):
    """Severity class (1-5) of `event` in `lgu`: the LGU's own override where a
    real report exists, else the event's default."""
    return event.get("lgu_severity", {}).get(lgu, event["severity"])


# Dry-season / non-typhoon baseline: small localized incidents (fire, flash
# flood, evacuation) that need a few relief packs in an ordinary month.
BASELINE_INCIDENT_PROB = 0.03
BASELINE_INCIDENT_PACKS = (20, 80)

HISTORY_START = date(2021, 1, 1)
HISTORY_END = date(2025, 12, 1)   # last month of the synthetic history
