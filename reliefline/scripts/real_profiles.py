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

  Urdaneta City   - Luis/Maymay/Neneng/Pilandok (2026), all 34 barangays.
  Calasiao        - Luis/Maymay/Neneng/Pilandok (Aug 2026), all 24 barangays.
  Santa Barbara   - Luis/Maymay/Neneng/Pilandok (Aug 2026), all 29 barangays.

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
# Luis & Maymay & Neneng & Pilandok (2026) report - see
# scripts/real_urdaneta_typhoons_2021_2026.py (dataset 2026-10-03).
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
    "Anonas": 1726, "Bactad East": 705, "Bayaoas": 1810, "Bolaoen": 450,
    "Cabaruan": 696, "Cabuloan": 1140, "Camanang": 1460, "Camantiles": 1858,
    "Casantaan": 428, "Catablan": 1805, "Cayambanan": 1407, "Consolacion": 433,
    "Dilan Paurido": 2079, "Dr. Pedro T. Orata": 1327, "Labit Proper": 1014,
    "Labit West": 789, "Mabanogbog": 1079, "Macalong": 484, "Nancalobasaan": 1008,
    "Nancamaliran East": 1300, "Nancamaliran West": 1707, "Nancayasan": 2420,
    "Oltama": 392, "Palina East": 1273, "Palina West": 985, "Pinmaludpod": 2320,
    "Poblacion": 2194, "San Jose": 1832, "San Vicente": 2974, "Santa Lucia": 875,
    "Santo Domingo": 931, "Sugcong": 322, "Tipuso": 616, "Tulong": 444,
}
for _name, _pop in _URDANETA_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["population"] = _pop
for _name, _hh in _URDANETA_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["num_households"] = _hh


# --- Calasiao --------------------------------------------------------------
# Luis & Maymay & Neneng & Pilandok (Aug 2026) report - see
# scripts/real_calasiao_typhoons_2021_2026.py (complete dataset 2026-10-03).
_CALASIAO_INDIVIDUALS_2026 = {
    "Ambonao": 7046, "Ambuetel": 3031, "Banaoang": 5069, "Bued": 5904, "Buenlag": 8231,
    "Cabilocaan": 3167, "Dinalaoan": 4149, "Doyong": 4020, "Gabon": 2861, "Lasip": 3223,
    "Longos": 3069, "Lumbang": 2642, "Macabito": 4461, "Malabago": 4427, "Mancup": 3735,
    "Nagsaing": 6064, "Nalsian": 6429, "Poblacion East": 1684, "Poblacion West": 609,
    "Quesban": 3200, "San Miguel": 7842, "San Vicente": 2117, "Songkoy": 2949,
    "Talibaew": 4757,
}
_CALASIAO_FAMILIES_2026 = {
    "Ambonao": 1895, "Ambuetel": 776, "Banaoang": 1327, "Bued": 1649, "Buenlag": 2087,
    "Cabilocaan": 876, "Dinalaoan": 1123, "Doyong": 1046, "Gabon": 757, "Lasip": 875,
    "Longos": 838, "Lumbang": 705, "Macabito": 1179, "Malabago": 1159, "Mancup": 1026,
    "Nagsaing": 1503, "Nalsian": 1797, "Poblacion East": 438, "Poblacion West": 162,
    "Quesban": 927, "San Miguel": 2150, "San Vicente": 549, "Songkoy": 786,
    "Talibaew": 1339,
}
for _name, _pop in _CALASIAO_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["population"] = _pop
for _name, _hh in _CALASIAO_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Calasiao", _name), {})["num_households"] = _hh


# --- Santa Barbara -------------------------------------------------------
# Luis & Maymay & Neneng & Pilandok (Aug 2026) report, all 29 barangays - see
# scripts/real_sta_barbara_typhoons_2021_2026.py (dataset 2026-10-03).
_STA_BARBARA_INDIVIDUALS_2026 = {
    "Alibago": 1744, "Balingueo": 3920, "Banaoang": 4536, "Banzal": 1712,
    "Botao": 3467, "Cablong": 3093, "Carusocan": 1960, "Dalongue": 2228, "Erfe": 670,
    "Gueguesangen": 1864, "Leet": 6968, "Malanay": 2884, "Maningding": 4930,
    "Maronong": 3479, "Maticmatic": 5017, "Minien East": 3350, "Minien West": 5273,
    "Nilombot": 2592, "Patayac": 2843, "Payas": 4002, "Poblacion Norte": 3872,
    "Poblacion Sur": 1556, "Primicias": 1909, "Sapang": 2346, "Sonquil": 3375,
    "Tebag East": 371, "Tebag West": 2650, "Tuliao": 6187, "Ventinilla": 3622,
}
_STA_BARBARA_FAMILIES_2026 = {
    "Alibago": 452, "Balingueo": 1110, "Banaoang": 1214, "Banzal": 461, "Botao": 1001,
    "Cablong": 868, "Carusocan": 504, "Dalongue": 680, "Erfe": 218,
    "Gueguesangen": 497, "Leet": 1842, "Malanay": 771, "Maningding": 1419,
    "Maronong": 982, "Maticmatic": 1280, "Minien East": 969, "Minien West": 1634,
    "Nilombot": 706, "Patayac": 814, "Payas": 1077, "Poblacion Norte": 914,
    "Poblacion Sur": 531, "Primicias": 614, "Sapang": 644, "Sonquil": 893,
    "Tebag East": 116, "Tebag West": 765, "Tuliao": 1715, "Ventinilla": 972,
}
for _name, _pop in _STA_BARBARA_INDIVIDUALS_2026.items():
    REAL_PROFILES.setdefault(("Santa Barbara", _name), {})["population"] = _pop
for _name, _hh in _STA_BARBARA_FAMILIES_2026.items():
    REAL_PROFILES.setdefault(("Santa Barbara", _name), {})["num_households"] = _hh


def real_profile(city_municipality, barangay_name):
    """Real predictor values on record for one barangay, or {} if none.

    The keys are a subset of the model's column-backed predictors; the caller
    overlays them on top of a synthetic profile so unknown fields stay
    synthetic."""
    return dict(REAL_PROFILES.get((city_municipality, barangay_name), {}))
