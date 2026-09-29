"""
Real per-barangay reference data that replaces synthetic seed values.

This is the single source of truth for any barangay profile figure we have an
official record for. `seed_training_data.profile_for()` generates a synthetic
profile for every barangay, then overlays whatever real values live here on
top - so a field we have is real, and a field we don't yet have stays
synthetic until its own official dataset is added here.

Add a municipality by dropping its dict into REAL_PROFILES keyed by the exact
`(city_municipality, barangay_name)` used in the database. Every inner dict may
carry any subset of the model's column-backed predictors: population,
num_households. (poverty_incidence, disaster_risk_index and
past_calamity_freq were dropped from the Barangay model 2026-09-29 - display
-only fields the demand model never actually used.)
Missing keys simply fall through to the synthetic value.

----------------------------------------------------------------------------
Sources - all three LGUs now sourced the SAME way (2026-09-28)
----------------------------------------------------------------------------
`population` / `num_households` are each barangay's "Total Number of
Individuals" / "Total Number of Families" from its most recent real relief
record (barangay_relief_records.total_individuals_snapshot/
total_families_snapshot - see scripts/real_<lgu>_typhoons_*.py), NOT a PSA
census count, for all three LGUs including Urdaneta:

  Urdaneta City   - Maymay (Aug 2026), all 34 barangays.
  Calasiao        - Maymay (Aug 2026), all 24 barangays.
  Santa Barbara   - mostly Crising/Dante/Emong (Jul 2025); a handful of
                    barangays not covered by it fall back to their next most
                    recent report (Egay 2023 or Enteng 2024).

Urdaneta previously used real PSA 2024 census figures here instead (city
totals then: population 145,935, households 40,015). Switched to match
Calasiao/Sta. Barbara's approach on request, after an informal check found
the two sources perform about the same for the share model (LOTO-CV MAE
0.0306 PSA-independent vs 0.0307 relief-report - see conversation log, not
committed here) and this keeps one consistent, explainable source across all
three LGUs (this exact "Family count used" figure is also what
app.ml.predict.share_breakdown shows on the Predictive Analytics page, so
"Households (current)" and "Family count used" are now the same number
everywhere, instead of silently disagreeing for Urdaneta only). The PSA
figures are not lost - they're in this file's git history if ever needed
again.

`num_households` here means "families" in the relief report's own sense
(the sheet's own column header), which is NOT the same definition as a PSA
household count (see the barangay-by-barangay mismatch this replaced -
e.g. old PSA Anonas households 1,625 vs relief-report families 2,232 - two
independently-collected figures that were never reconciled with each other).
"""

# (city_municipality, barangay_name) -> {predictor: real value}
REAL_PROFILES = {}


# --- Urdaneta City --------------------------------------------------------
# Maymay (Aug 2026) report - see scripts/real_urdaneta_typhoons_2021_2025.py.
_URDANETA_INDIVIDUALS_2026 = {
    "Anonas": 9153, "Bactad East": 3036, "Bayaoas": 9357, "Bolaoen": 1693,
    "Cabaruan": 1343, "Cabuloan": 3474, "Camanang": 4204, "Camantiles": 4584,
    "Casantaan": 2672, "Catablan": 10233, "Cayambanan": 3737, "Consolacion": 2511,
    "Dilan Paurido": 8087, "Dr. Pedro T. Orata": 2102, "Labit Proper": 2817,
    "Labit West": 4146, "Mabanogbog": 4715, "Macalong": 2350, "Nancalobasaan": 4686,
    "Nancamaliran East": 2817, "Nancamaliran West": 1839, "Nancayasan": 5036,
    "Oltama": 818, "Palina East": 3460, "Palina West": 5139, "Pinmaludpod": 7387,
    "Poblacion": 3985, "San Jose": 9503, "San Vicente": 7883, "Santa Lucia": 3956,
    "Santo Domingo": 2044, "Sugcong": 350, "Tipuso": 1971, "Tulong": 4847,
}
_URDANETA_FAMILIES_2026 = {
    "Anonas": 2232, "Bactad East": 741, "Bayaoas": 2282, "Bolaoen": 413,
    "Cabaruan": 328, "Cabuloan": 847, "Camanang": 1025, "Camantiles": 1118,
    "Casantaan": 652, "Catablan": 2496, "Cayambanan": 912, "Consolacion": 612,
    "Dilan Paurido": 1973, "Dr. Pedro T. Orata": 513, "Labit Proper": 687,
    "Labit West": 1011, "Mabanogbog": 1150, "Macalong": 573, "Nancalobasaan": 1143,
    "Nancamaliran East": 687, "Nancamaliran West": 449, "Nancayasan": 1228,
    "Oltama": 199, "Palina East": 844, "Palina West": 1253, "Pinmaludpod": 1802,
    "Poblacion": 972, "San Jose": 2318, "San Vicente": 1923, "Santa Lucia": 965,
    "Santo Domingo": 498, "Sugcong": 85, "Tipuso": 481, "Tulong": 1182,
}
for _name, _pop in _URDANETA_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["population"] = _pop
for _name, _hh in _URDANETA_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["num_households"] = _hh


# --- Calasiao --------------------------------------------------------------
# Maymay (Aug 2026) report - see scripts/real_calasiao_typhoons_2021_2026.py.
_CALASIAO_INDIVIDUALS_2026 = {
    "Ambonao": 5291, "Ambuetel": 3973, "Banaoang": 4711, "Bued": 6226, "Buenlag": 8840,
    "Cabilocaan": 2609, "Dinalaoan": 6498, "Doyong": 4461, "Gabon": 3890, "Lasip": 4234,
    "Longos": 4940, "Lumbang": 2083, "Macabito": 4721, "Malabago": 5076, "Mancup": 5326,
    "Nagsaing": 10793, "Nalsian": 5828, "Poblacion East": 3459, "Poblacion West": 922,
    "Quesban": 1852, "San Miguel": 5395, "San Vicente": 2132, "Songkoy": 3387, "Talibaew": 9592,
}
_CALASIAO_FAMILIES_2026 = {
    "Ambonao": 1056, "Ambuetel": 993, "Banaoang": 1178, "Bued": 1537, "Buenlag": 2210,
    "Cabilocaan": 522, "Dinalaoan": 1300, "Doyong": 1742, "Gabon": 778, "Lasip": 1414,
    "Longos": 1235, "Lumbang": 810, "Macabito": 1040, "Malabago": 1868, "Mancup": 1332,
    "Nagsaing": 2162, "Nalsian": 2309, "Poblacion East": 864, "Poblacion West": 461,
    "Quesban": 618, "San Miguel": 1332, "San Vicente": 533, "Songkoy": 847, "Talibaew": 1947,
}
for _name, _pop in _CALASIAO_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["population"] = _pop
for _name, _hh in _CALASIAO_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["num_households"] = _hh


# --- Santa Barbara -------------------------------------------------------
# Mostly the Crising/Dante/Emong (Jul 2025) report; a handful of barangays
# not covered by it fall back to their next most recent report (Egay 2023 or
# Enteng 2024 - see scripts/real_sta_barbara_typhoons_2021_2025.py).
_STA_BARBARA_INDIVIDUALS_2025 = {
    "Alibago": 1489, "Balingueo": 3845, "Banaoang": 5030, "Banzal": 1631, "Botao": 3401,
    "Cablong": 3058, "Carusocan": 1876, "Dalongue": 2147, "Erfe": 747, "Gueguesangen": 1830,
    "Leet": 4618, "Malanay": 2775, "Maningding": 4996, "Maronong": 3582, "Maticmatic": 4962,
    "Minien East": 3260, "Minien West": 5230, "Nilombot": 2492, "Patayac": 2880, "Payas": 3915,
    "Poblacion Norte": 1858, "Poblacion Sur": 1766, "Primicias": 1819, "Sapang": 2315,
    "Sonquil": 3272, "Tebag East": 439, "Tebag West": 2538, "Tuliao": 6424, "Ventinilla": 3485,
}
_STA_BARBARA_FAMILIES_2025 = {
    "Alibago": 360, "Balingueo": 960, "Banaoang": 1050, "Banzal": 330, "Botao": 788,
    "Cablong": 671, "Carusocan": 479, "Dalongue": 450, "Erfe": 160, "Gueguesangen": 380,
    "Leet": 990, "Malanay": 600, "Maningding": 1050, "Maronong": 750, "Maticmatic": 1030,
    "Minien East": 759, "Minien West": 1264, "Nilombot": 520, "Patayac": 704, "Payas": 820,
    "Poblacion Norte": 390, "Poblacion Sur": 455, "Primicias": 472, "Sapang": 531,
    "Sonquil": 771, "Tebag East": 118, "Tebag West": 592, "Tuliao": 1503, "Ventinilla": 833,
}
for _name, _pop in _STA_BARBARA_INDIVIDUALS_2025.items():
    REAL_PROFILES.setdefault(("Santa Barbara", _name), {})["population"] = _pop
for _name, _hh in _STA_BARBARA_FAMILIES_2025.items():
    REAL_PROFILES.setdefault(("Santa Barbara", _name), {})["num_households"] = _hh


def real_profile(city_municipality, barangay_name):
    """Real predictor values on record for one barangay, or {} if none.

    The keys are a subset of the model's column-backed predictors; the caller
    overlays them on top of a synthetic profile so unknown fields stay
    synthetic."""
    return dict(REAL_PROFILES.get((city_municipality, barangay_name), {}))
