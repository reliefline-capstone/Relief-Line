"""
REAL records given to the team: Calasiao disaster reports for the 2025
southwest-monsoon typhoons. Second per-barangay ground truth after Urdaneta
(scripts/real_urdaneta_reports_2025.py) and loaded the same way by
scripts/seed_monthly_history.py: Calasiao's history for the two event months
is REPLACED by these figures (data_source='real') and the SARIMAX model trains
on them.

Two reports:
  crising_2025  "Calasiao_Crising&EmongAUG2025" - Table 1, all 24 barangays.
                Habagat + TS Crising + TS Emong, report dated August 2025;
                the relief belongs to Jul 2025 (same event as Urdaneta's
                Dante/Emong report). It has ONLY affected families / persons /
                4Ps - no assistance table.
  nando_2025    "Nando & Opong" report - Tables 1, 2.1-2.3, 3, 4 (files
                T1..T4). 19 of 24 barangays reported. Booked to Sep 2025, the
                Nando event month (Opong, the following storm, is in the same
                report and is not split out).

How "packs served" was read (assumptions stated, not hidden):
  * Nando/Opong Table 4 (assistance provided) gives DSWD family food packs
    (FFP), LGU FPs and Province FPs per barangay -> packs = the three summed.
    Barangays reported as affected but absent from Table 4 (Bued, Doyong,
    Quesban, Songkoy) are stored as 0 served, like Bactad East in Urdaneta.
  * Crising/Emong has NO pack figures. The packs are ESTIMATED as
    affected families x CRISING_PACKS_PER_FAMILY, the packs-per-affected-family
    ratio measured on Calasiao's own Nando/Opong report (see nando_ratio()).
    This is an assumption, not a measurement: the model would otherwise train
    on synthetic data for the very month the team holds real records for.
    Those rows are flagged data_source='real' like the rest - treat the
    Jul 2025 Calasiao figures as "real families, estimated packs".

Data-quality notes kept from the source:
  * Table 1 (Nando) "Total" row prints 2,008 families / 76,011 individuals /
    706 4Ps. The rows sum to 20,008 families (a dropped digit: 2,008 -> 20,008)
    and 76,011 individuals (matches); the 4Ps rows sum to 642, not 706. The
    row values are used, the printed total is not.
  * Table 4 lists Lasip twice (rows 13 and 15, both 1,280 LGU FPs) and skips
    row 11; the printed LGU total (7,540) counts both. 2,560 packs for 1,380
    affected families is implausible, so the duplicate is treated as a
    copy-paste error and counted ONCE (LASIP_DUPLICATE_COUNTED = False).
    Flip the flag if the LGU confirms two lots.
  * The Table 2.x file names and the caption image disagree (image: 2.2 = Latter
    Day Saints, 2.3 = Sports Complex; files: T2.2 = Sports Complex 263 fam / 833
    persons, T2.3 = Latter Day Saints 18 / 81). The file contents are kept.
    The age tables match their sites' totals except 2.1 (124 vs 114 persons).
  * Barangay names differ from the barangays table ("Cabiloocan" vs
    "Cabilocaan", "Pob. East" vs "Poblacion East"); see normalize().

Displaced / damaged-house / age-bracket tables have no home in the schema
(barangay_reports deliberately excludes evacuee headcounts) and the forecaster
does not use them, so they are kept here as reference data only and are not
loaded into the database.

Run this file to print the integrity checks.
"""
import unicodedata

# ---------------------------------------------------------------- Crising / Emong
# name -> (families affected, individuals affected, 4Ps)   [Table 1]
CRISING_EMONG = {
    "Ambonao": (1030, 5162, 23), "Ambuetel": (969, 3876, 9), "Banaoang": (1149, 4596, 75),
    "Bued": (1500, 6074, 75), "Buenlag": (2156, 8624, 250), "Cabiloocan": (509, 2545, 14),
    "Dinalaoan": (1268, 6340, 26), "Doyong": (1700, 4352, 198), "Gabon": (759, 3795, 59),
    "Lasip": (1380, 4131, 74), "Longos": (1205, 4820, 31), "Lumbang": (790, 2032, 40),
    "Macabito": (1015, 4606, 19), "Malabago": (1822, 4952, 0), "Mancup": (1300, 5196, 16),
    "Nagsaing": (2109, 10530, 31), "Nalsian": (2253, 5686, 85), "Poblacion East": (843, 3375, 50),
    "Poblacion West": (450, 900, 8), "Quesban": (603, 1807, 25), "San Miguel": (1300, 5263, 30),
    "San Vicente": (520, 2080, 0), "Songkoy": (826, 3304, 11), "Talibaew": (1900, 9358, 124),
}
CRISING_TOTALS = (29356, 113404, 1273)   # the report's own Total row

# ---------------------------------------------------------------- Nando / Opong
# name -> (families affected, individuals affected, 4Ps)   [T1]
NANDO_OPONG = {
    "Bued": (720, 2880, 0), "Longos": (1250, 3123, 50), "Lumbang": (790, 3160, 40),
    "Banaoang": (2200, 8800, 0), "Buenlag": (800, 3659, 154), "Mancup": (1300, 6143, 7),
    "Doyong": (850, 3413, 7), "Talibaew": (1900, 7600, 110), "Pob. East": (790, 3160, 50),
    "Malabago": (1822, 4952, 140), "Lasip": (1380, 4131, 0), "Pob. West": (511, 814, 0),
    "San Miguel": (469, 2345, 24), "Quesban": (590, 2069, 15), "Dinalaoan": (750, 3750, 0),
    "Gabon": (700, 3500, 3), "San Vicente": (600, 2863, 30), "Songkoy": (280, 420, 12),
    "Nalsian": (2306, 9229, 0),
}
NANDO_PRINTED_TOTAL = (2008, 76011, 706)   # families/4Ps figures don't match the rows - see docstring

# [T4] name -> (DSWD FFPs, LGU FPs, Province FPs)
NANDO_ASSISTANCE = {
    "Mancup": (1300, 0, 0), "Talibaew": (1850, 0, 0), "Longos": (1230, 0, 0),
    "Banaoang": (2200, 0, 0), "San Vicente": (700, 0, 0), "Gabon": (600, 0, 0),
    "Buenlag": (0, 1320, 0), "Pob. East": (0, 500, 0), "Malabago": (0, 1250, 0),
    "Dinalaoan": (0, 1000, 0), "Lumbang": (0, 200, 400), "Lasip": (0, 1280, 0),
    "Pob. West": (0, 160, 0), "San Miguel": (0, 550, 0), "Nalsian": (2600, 0, 0),
}
LASIP_DUPLICATE_COUNTED = False          # see docstring
NANDO_PRINTED_ASSISTANCE_TOTAL = (10480, 7540, 400)   # printed LGU total counts Lasip twice

# ------------------------------------------------- reference only (not loaded)
# [T2.1-2.3] site -> (families, individuals)
EVACUATION_SITES = {
    "Designated ECs (Malabago BH 16/42, Talibaew ES 5/17, Longos ES 20/45, Mancup BH & ES 7/20)": (46, 114),
    "Calasiao Sports Complex (file T2.2)": (263, 833),
    "Latter Day Saints Church (file T2.3)": (18, 81),
}
DAMAGED_HOUSES = {"Doyong": {"totally": 0, "partially": 1, "remarks": "For further validation"}}
# [2.1-2.3 age tables] bracket -> (M, F), in the same order as the sites above
AGE_BRACKETS = {
    "2.1": {"Infant (0-11mos.)": (2, 0), "Toddler (1-3)": (1, 2), "Pre-schooler (4-5)": (1, 5),
            "School age (6-12)": (11, 8), "Teenage (13-19)": (10, 7), "Adult (20-59)": (35, 33),
            "Older person (60+)": (4, 5)},
    "2.2": {"Infant (0-11mos.)": (8, 5), "Toddler (1-3)": (20, 23), "Pre-schooler (4-5)": (42, 29),
            "School age (6-12)": (61, 56), "Teenage (13-19)": (60, 57), "Adult (20-59)": (208, 200),
            "Older person (60+)": (27, 37)},
    "2.3": {"Infant (0-11mos.)": (0, 1), "Toddler (1-3)": (1, 0), "Pre-schooler (4-5)": (1, 3),
            "School age (6-12)": (12, 5), "Teenage (13-19)": (5, 5), "Adult (20-59)": (23, 19),
            "Older person (60+)": (2, 3)},
}


def normalize(name):
    """Accent/punctuation-insensitive key folding this report's spellings onto
    the barangays table: 'Pob. East' / 'Poblacion East' -> 'poblacion east',
    'Cabiloocan' -> 'cabilocaan'."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    for ch in ".,'-":
        s = s.replace(ch, " ")
    s = " ".join(s.split())
    if s.startswith("pob "):
        s = "poblacion " + s[4:]
    return {"cabiloocan": "cabilocaan"}.get(s, s)


def nando_packs():
    """{barangay name: packs served} from Table 4 (DSWD + LGU + Province)."""
    out = {n: sum(v) for n, v in NANDO_ASSISTANCE.items()}
    if LASIP_DUPLICATE_COUNTED:
        out["Lasip"] += 1280
    return out


def nando_ratio():
    """Packs served per affected family over the barangays Nando/Opong reported."""
    return sum(nando_packs().values()) / sum(v[0] for v in NANDO_OPONG.values())


# Estimated packs-per-family for the Crising/Emong report (no pack figures in
# the source). Rounded from nando_ratio() so it does not silently move.
CRISING_PACKS_PER_FAMILY = 0.86


def crising_rows():
    """{name: (families, persons, packs)} - packs ESTIMATED, see docstring."""
    return {n: (f, p, int(round(f * CRISING_PACKS_PER_FAMILY)))
            for n, (f, p, _4ps) in CRISING_EMONG.items()}


def nando_rows():
    """{name: (families, persons, packs)} - packs measured (Table 4)."""
    packs = nando_packs()
    return {n: (f, p, packs.get(n, 0)) for n, (f, p, _4ps) in NANDO_OPONG.items()}


# key matches app.ml.climate_reference.EVENTS; month = history month the relief
# is booked to. `packs_estimated` marks the report with no pack figures.
REPORTS = [
    {"key": "crising_2025", "short": "Crising/Emong + habagat", "month": "2025-07-01",
     "title": "Habagat, TS Crising and TS Emong (report dated Aug 2025)",
     "rows": crising_rows(), "packs_estimated": True},
    {"key": "nando_2025", "short": "Nando/Opong", "month": "2025-09-01",
     "title": "Typhoons Nando and Opong (Sep 2025)",
     "rows": nando_rows(), "packs_estimated": False},
]


def by_key(report):
    """{normalized barangay name: (families, persons, packs)}"""
    return {normalize(n): v for n, v in report["rows"].items()}


def totals_of(report):
    rows = report["rows"].values()
    return sum(r[0] for r in rows), sum(r[1] for r in rows), sum(r[2] for r in rows)


if __name__ == "__main__":
    f, p, q = (sum(v[i] for v in CRISING_EMONG.values()) for i in range(3))
    print(f"Crising/Emong Table 1: {len(CRISING_EMONG)} barangays, rows sum {f:,} fam / {p:,} ind / {q:,} 4Ps"
          f" vs printed {CRISING_TOTALS} -> {'OK' if (f, p, q) == CRISING_TOTALS else 'MISMATCH'}")
    f, p, q = (sum(v[i] for v in NANDO_OPONG.values()) for i in range(3))
    print(f"Nando/Opong T1: {len(NANDO_OPONG)} barangays, rows sum {f:,} fam / {p:,} ind / {q:,} 4Ps"
          f" vs printed {NANDO_PRINTED_TOTAL}")
    cols = [sum(v[i] for v in NANDO_ASSISTANCE.values()) for i in range(3)]
    print(f"Nando/Opong T4 (Lasip once): DSWD {cols[0]:,} LGU {cols[1]:,} Prov {cols[2]:,} | printed "
          f"{NANDO_PRINTED_ASSISTANCE_TOTAL} (LGU matches only with Lasip twice: {cols[1] + 1280:,})")
    print(f"Packs served (used): {sum(nando_packs().values()):,}; per affected family {nando_ratio():.3f}"
          f" (Crising estimate uses {CRISING_PACKS_PER_FAMILY})")
    print("T2 evacuee sums:", tuple(sum(v[i] for v in EVACUATION_SITES.values()) for i in (0, 1)))
    for site, t in AGE_BRACKETS.items():
        print(f"  age table {site}: {sum(m + f_ for m, f_ in t.values())} persons")
    for r in REPORTS:
        print(f"{r['short']}: families/persons/packs = {totals_of(r)}")
