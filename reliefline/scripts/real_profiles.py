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
  Santa Barbara   - Crising/Dante/Emong (Jul 2025), all 29 barangays.

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
# Maymay (Aug 2026) report - see scripts/real_urdaneta_typhoons_2021_2026.py
# (updated dataset 2026-10-03).
_URDANETA_INDIVIDUALS_2026 = {
    "Anonas": 6285, "Bactad East": 2231, "Bayaoas": 5864, "Bolaoen": 1604,
    "Cabaruan": 2389, "Cabuloan": 3564, "Camanang": 5397, "Camantiles": 6564,
    "Casantaan": 1479, "Catablan": 6107, "Cayambanan": 4408, "Consolacion": 1830,
    "Dilan Paurido": 7186, "Dr. Pedro T. Orata": 3458, "Labit Proper": 3939,
    "Labit West": 2751, "Mabanogbog": 3564, "Macalong": 1756, "Nancalobasaan": 3364,
    "Nancamaliran East": 5284, "Nancamaliran West": 5981, "Nancayasan": 8175,
    "Oltama": 1422, "Palina East": 5190, "Palina West": 3443, "Pinmaludpod": 8324,
    "Poblacion": 7301, "San Jose": 5730, "San Vicente": 9532, "Santa Lucia": 3401,
    "Santo Domingo": 3423, "Sugcong": 1160, "Tipuso": 2262, "Tulong": 1567,
}
_URDANETA_FAMILIES_2026 = {
    "Anonas": 1540, "Bactad East": 611, "Bayaoas": 1635, "Bolaoen": 432,
    "Cabaruan": 624, "Cabuloan": 915, "Camanang": 1335, "Camantiles": 1732,
    "Casantaan": 456, "Catablan": 1695, "Cayambanan": 1267, "Consolacion": 480,
    "Dilan Paurido": 1983, "Dr. Pedro T. Orata": 670, "Labit Proper": 968,
    "Labit West": 726, "Mabanogbog": 975, "Macalong": 495, "Nancalobasaan": 860,
    "Nancamaliran East": 1502, "Nancamaliran West": 1595, "Nancayasan": 2397,
    "Oltama": 399, "Palina East": 1425, "Palina West": 948, "Pinmaludpod": 2171,
    "Poblacion": 1958, "San Jose": 1554, "San Vicente": 2624, "Santa Lucia": 940,
    "Santo Domingo": 954, "Sugcong": 321, "Tipuso": 558, "Tulong": 400,
}
for _name, _pop in _URDANETA_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["population"] = _pop
for _name, _hh in _URDANETA_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["num_households"] = _hh


# --- Calasiao --------------------------------------------------------------
# Maymay (Aug 2026) report - see scripts/real_calasiao_typhoons_2021_2026.py
# (updated dataset 2026-10-03).
_CALASIAO_INDIVIDUALS_2026 = {
    "Ambonao": 7131, "Ambuetel": 3081, "Banaoang": 5088, "Bued": 5908, "Buenlag": 8206,
    "Cabilocaan": 3262, "Dinalaoan": 4167, "Doyong": 4052, "Gabon": 2782, "Lasip": 3139,
    "Longos": 3101, "Lumbang": 2784, "Macabito": 4494, "Malabago": 4477, "Mancup": 3793,
    "Nagsaing": 6066, "Nalsian": 6203, "Poblacion East": 1691, "Poblacion West": 506,
    "Quesban": 3205, "San Miguel": 7890, "San Vicente": 2122, "Songkoy": 3001,
    "Talibaew": 4722,
}
_CALASIAO_FAMILIES_2026 = {
    "Ambonao": 1739, "Ambuetel": 752, "Banaoang": 1241, "Bued": 1441, "Buenlag": 2001,
    "Cabilocaan": 796, "Dinalaoan": 1016, "Doyong": 988, "Gabon": 679, "Lasip": 766,
    "Longos": 756, "Lumbang": 679, "Macabito": 1096, "Malabago": 1092, "Mancup": 925,
    "Nagsaing": 1480, "Nalsian": 1513, "Poblacion East": 412, "Poblacion West": 123,
    "Quesban": 782, "San Miguel": 1924, "San Vicente": 518, "Songkoy": 732,
    "Talibaew": 1152,
}
for _name, _pop in _CALASIAO_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["population"] = _pop
for _name, _hh in _CALASIAO_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["num_households"] = _hh


# --- Santa Barbara -------------------------------------------------------
# Crising/Dante/Emong (Jul 2025) report, all 29 barangays - see
# scripts/real_sta_barbara_typhoons_2021_2025.py (updated dataset 2026-10-03).
_STA_BARBARA_INDIVIDUALS_2025 = {
    "Alibago": 1789, "Balingueo": 3922, "Banaoang": 4551, "Banzal": 1747, "Botao": 3484,
    "Cablong": 3102, "Carusocan": 1981, "Dalongue": 2278, "Erfe": 675,
    "Gueguesangen": 1872, "Leet": 6891, "Malanay": 2914, "Maningding": 4940,
    "Maronong": 3523, "Maticmatic": 4992, "Minien East": 3373, "Minien West": 5284,
    "Nilombot": 2632, "Patayac": 2834, "Payas": 4021, "Poblacion Norte": 3671,
    "Poblacion Sur": 1504, "Primicias": 1932, "Sapang": 2354, "Sonquil": 3401,
    "Tebag East": 354, "Tebag West": 2678, "Tuliao": 6128, "Ventinilla": 3656,
}
_STA_BARBARA_FAMILIES_2025 = {
    "Alibago": 480, "Balingueo": 1053, "Banaoang": 1222, "Banzal": 469, "Botao": 935,
    "Cablong": 833, "Carusocan": 532, "Dalongue": 612, "Erfe": 181, "Gueguesangen": 503,
    "Leet": 1850, "Malanay": 782, "Maningding": 1326, "Maronong": 946,
    "Maticmatic": 1340, "Minien East": 906, "Minien West": 1419, "Nilombot": 707,
    "Patayac": 761, "Payas": 1079, "Poblacion Norte": 986, "Poblacion Sur": 404,
    "Primicias": 519, "Sapang": 632, "Sonquil": 913, "Tebag East": 95,
    "Tebag West": 719, "Tuliao": 1645, "Ventinilla": 981,
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
