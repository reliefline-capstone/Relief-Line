"""
REAL records given to the team: Urdaneta City CSWDO barangay disaster reports
for four 2025 events. Per barangay: families / persons affected and the family
food packs (FFP) served. This is the first per-barangay ground truth we hold
and is used three ways (see scripts/seed_monthly_history.py):

  1. it REPLACES the synthetic history for Urdaneta in those four months
     (data_source='real') - the model trains on it;
  2. it sets Urdaneta's flood susceptibility (relative share of households
     affected across the four events);
  3. it calibrates the synthetic generator (reach, packs per household, the
     per-barangay cap) so the other LGUs / years look like the real thing.

Events (report date -> the month the relief belongs to):
  dante_emong  TS Dante, TD Emong + enhanced SW monsoon  "as of Aug 1, 2025"  -> Jul 2025
  mirasol_nando  Mirasol & Nando + SW monsoon            "Sep 26, 2025"       -> Sep 2025
  paolo        Tropical Cyclone Paolo (Matmo)            "Oct 4, 2025"        -> Oct 2025
  uwan         Super Typhoon Uwan (Fung-wong)            "Nov 25, 2025"       -> Nov 2025

How "packs served" was read from each report (assumptions stated, not hidden):
  * Dante/Emong report has no pack counts, only LGU assistance at Php 500 per
    affected family, printed as "Provided family food packs" -> 1 pack per
    affected family (= families).
  * Mirasol/Nando, Paolo, Uwan: the number in the Remarks ("500 family food
    packs served", "300 families served", "467 families served & one ... house
    given 10,000") -> that number. Paolo: "500 by LGU and 70 by DSWD" -> 570;
    "500 ... and 54 FFP's by DSWD" -> 554; San Vicente "500 from DSWD" -> 500.
  * No remark -> 0 served (e.g. Bactad East, Sep). The Uwan remarks add up to
    the report's own 950 total, which supports reading them as packs.

Data-quality notes kept from the source:
  * Tulong (Dante/Emong): source prints Php 74,500 for 148 families (a Php 500
    rate gives 74,000); packs are taken as 148.
  * Cabuloan (Mirasol/Nando): 5,010 persons for 202 families looks like a typo,
    but the report's own grand total (27,974) includes it, so it is kept.
    Persons are not used by the model - only families and packs.
  * Barangays with an empty row (no report for that event) are stored as
    "not reported" (None) and load as 0 packs.

Run this file to print the integrity check against each report's grand total.
"""
import statistics
import unicodedata

# name -> (families affected, persons affected, packs served)
DANTE_EMONG = {
    "Anonas": (112, 448, 112), "Bactad East": (45, 138, 45), "Bayaoas": (130, 520, 130),
    "Bolaoen": (50, 128, 50), "Cabuloan": (112, 336, 112), "Camanang": (45, 109, 45),
    "Camantiles": (65, 163, 65), "Casantaan": (60, 185, 60), "Catablan": (161, 623, 161),
    "Cayambanan": (106, 318, 106), "Consolacion": (45, 152, 45), "Dilan Paurido": (236, 704, 236),
    "Labit Proper": (81, 289, 81), "Labit West": (93, 287, 93), "Macalong": (57, 221, 57),
    "Mabanogbog": (162, 555, 162), "Nancamaliran East": (40, 122, 40), "Nancalobasaan": (51, 166, 51),
    "Nancayasan": (99, 297, 99), "Pedro T. Orata": (61, 183, 61), "Palina East": (70, 188, 70),
    "Palina West": (99, 303, 99), "Pinmaludpod": (120, 365, 120), "Poblacion": (57, 79, 57),
    "Sta. Lucia": (84, 306, 84), "San Jose": (199, 598, 199), "San Vicente": (76, 279, 76),
    "Tiposu": (40, 160, 40), "Tulong": (148, 441, 148),
}

MIRASOL_NANDO = {
    "Anonas": (653, 2080, 300), "Bactad East": (30, 112, 0), "Bayaoas": (408, 955, 298),
    "Bolaoen": (100, 301, 80), "Cabuloan": (202, 5010, 100), "Camanang": (258, 439, 170),
    "Camantiles": (218, 454, 160), "Casantaan": (156, 253, 150), "Catablan": (651, 1979, 467),
    "Cayambanan": (103, 223, 100), "Consolacion": (123, 253, 100), "Dilan-Paurido": (448, 1350, 250),
    "Labit Proper": (125, 305, 100), "Labit West": (353, 981, 277), "Mabanogbog": (235, 598, 100),
    "Macalong": (160, 284, 140), "Nancalobasaan": (270, 618, 202), "Nancamaliran East": (99, 200, 80),
    "Nancamaliran West": (120, 266, 100), "Nancayasan": (310, 742, 220), "Palina East": (253, 560, 100),
    "Palina West": (398, 1002, 220), "Pedro T. Orata": (120, 250, 100), "Pinmaludpod": (697, 1991, 340),
    "Poblacion": (143, 231, 119), "San Jose": (681, 2010, 520), "San Vicente": (528, 1972, 126),
    "Santa Lucia": (402, 1011, 282), "Santo Domingo": (253, 533, 200), "Tiposu": (89, 155, 80),
    "Tulong": (352, 856, 250),
}

PAOLO = {
    "Anonas": (755, 1113, 500), "Bactad East": (693, 1126, 500), "Bayaoas": (870, 1222, 570),
    "Bolaoen": (236, 700, 200), "Cabuloan": (226, 655, 200), "Camanang": (356, 1115, 300),
    "Camantiles": (423, 1106, 300), "Casantaan": (348, 1026, 300), "Catablan": (633, 1989, 500),
    "Cayambanan": (340, 989, 300), "Consolacion": (303, 1003, 500), "Dilan-Paurido": (500, 1402, 500),
    "Labit Proper": (303, 758, 300), "Labit West": (415, 1015, 300), "Mabanogbog": (398, 1102, 300),
    "Macalong": (202, 565, 200), "Nancalobasaan": (554, 1204, 554), "Nancamaliran East": (305, 789, 300),
    "Nancamaliran West": (500, 1316, 500), "Nancayasan": (500, 1326, 500), "Palina East": (405, 1056, 300),
    "Palina West": (500, 1153, 500), "Pedro T. Orata": (303, 706, 300), "Pinmaludpod": (500, 1416, 500),
    "Poblacion": (788, 1986, 500), "San Jose": (658, 1289, 500), "San Vicente": (567, 1681, 500),
    "Santa Lucia": (455, 1056, 500), "Santo Domingo": (389, 1022, 500), "Tiposu": (298, 1181, 500),
    "Tulong": (289, 860, 200),
}

UWAN = {
    "Anonas": (114, 348, 100), "Bactad East": (19, 57, 10), "Bayaoas": (139, 415, 100),
    "Cabaruan": (51, 150, 40), "Cabuloan": (21, 64, 20), "Camanang": (61, 191, 50),
    "Camantiles": (65, 201, 50), "Casantaan": (12, 38, 10), "Catablan": (142, 403, 100),
    "Cayambanan": (38, 116, 25), "Consolacion": (23, 71, 20), "Dilan-Paurido": (67, 202, 25),
    "Labit Proper": (16, 53, 10), "Labit West": (14, 44, 10), "Mabanogbog": (20, 58, 20),
    "Macalong": (15, 50, 10), "Nancalobasaan": (55, 166, 30), "Nancamaliran East": (41, 123, 20),
    "Nancamaliran West": (2, 14, 0), "Nancayasan": (43, 131, 0), "Oltama": (31, 92, 10),
    "Palina East": (16, 47, 10), "Palina West": (33, 104, 30), "Pinmaludpod": (61, 184, 50),
    "Poblacion": (22, 67, 10), "San Jose": (88, 263, 50), "San Vicente": (122, 359, 100),
    "Sugcong": (13, 41, 10), "Tiposu": (11, 35, 10), "Tulong": (25, 75, 20),
}

# key matches app.ml.climate_reference.EVENTS; month = the history month the
# relief is booked to. `totals` are the report's own GRAND TOTAL row (families,
# persons, packs served or None where the report gives no served total).
REPORTS = [
    {"key": "crising_2025", "short": "Dante/Emong + habagat", "month": "2025-07-01",
     "title": "TS Dante, TD Emong and enhanced southwest monsoon (as of Aug 1, 2025)",
     "rows": DANTE_EMONG, "totals": (2704, 8663, None)},
    {"key": "nando_2025", "short": "Mirasol/Nando + habagat", "month": "2025-09-01",
     "title": "Southwest monsoon with TC Mirasol and Nando (Sep 26, 2025)",
     "rows": MIRASOL_NANDO, "totals": (8938, 27974, None)},
    {"key": "paolo_2025", "short": "Paolo", "month": "2025-10-01",
     "title": "Tropical Cyclone Paolo (Oct 4, 2025)",
     "rows": PAOLO, "totals": (14012, 34927, None)},
    {"key": "uwan_2025", "short": "Uwan", "month": "2025-11-01",
     "title": "Super Typhoon Uwan (Nov 25, 2025)",
     "rows": UWAN, "totals": (1380, 4162, 950)},
]


def normalize(name):
    """Accent/punctuation-insensitive key that also folds the spelling
    variants across the four reports and the barangays table:
    'Dilan-Paurido' / 'DILAN PAURIDO' -> 'dilan paurido',
    'Pedro T. Orata' -> 'dr pedro t orata', 'Tiposu' -> 'tipuso',
    'Sta. Lucia' -> 'santa lucia'."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    for ch in ".,'-":
        s = s.replace(ch, " ")
    s = " ".join(s.split())
    return {
        "pedro t orata": "dr pedro t orata", "tiposu": "tipuso", "sta lucia": "santa lucia",
    }.get(s, s)


def by_key(report):
    """{normalized barangay name: (families, persons, packs)}"""
    return {normalize(n): v for n, v in report["rows"].items()}


def totals_of(report):
    rows = report["rows"].values()
    return sum(r[0] for r in rows), sum(r[1] for r in rows), sum(r[2] for r in rows)


def stats_of(report, n_barangays=34):
    """Shape numbers used to calibrate the generator."""
    vals = sorted(v[2] for v in report["rows"].values() if v[2] > 0)
    fam, _p, packs = totals_of(report)
    return {
        "reported": len(report["rows"]), "served": len(vals), "reach": len(vals) / n_barangays,
        "families": fam, "packs": packs,
        "packs_per_family": packs / fam if fam else 0,
        "median": statistics.median(vals) if vals else 0,
        "p90": vals[int(len(vals) * 0.9) - 1] if vals else 0,
        "max": vals[-1] if vals else 0,
    }


if __name__ == "__main__":
    ok = True
    print(f"{'event':<26}{'families':>9}{'(report)':>9}{'persons':>9}{'(report)':>9}{'packs':>8}{'(report)':>9}  check")
    for r in REPORTS:
        fam, per, packs = totals_of(r)
        tf, tp, tk = r["totals"]
        good = fam == tf and per == tp and (tk is None or packs == tk)
        ok &= good
        print(f"{r['short']:<26}{fam:>9,}{tf:>9,}{per:>9,}{tp:>9,}{packs:>8,}{(tk if tk is not None else 0):>9,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print("\nShape of each real event (Urdaneta City, 34 barangays)")
    print(f"{'event':<26}{'reached':>8}{'packs/fam':>10}{'median':>8}{'p90':>7}{'max':>6}")
    for r in REPORTS:
        s = stats_of(r)
        print(f"{r['short']:<26}{s['served']:>4}/34{s['packs_per_family']:>10.2f}{s['median']:>8.0f}{s['p90']:>7.0f}{s['max']:>6}")
    print("\nAll four reports match their own grand totals." if ok else "\nMISMATCH - recheck the transcription.")
