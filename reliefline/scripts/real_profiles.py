"""
Real per-barangay reference data that replaces synthetic seed values.

This is the single source of truth for any barangay profile figure we have an
official record for. `seed_training_data.profile_for()` generates a synthetic
profile for every barangay, then overlays whatever real values live here on
top — so a field we have (e.g. Urdaneta population) is real, and a field we
don't yet have (e.g. poverty incidence, disaster risk index) stays synthetic
until its own official dataset is added here.

Add a municipality by dropping its dict into REAL_PROFILES keyed by the exact
`(city_municipality, barangay_name)` used in the database. Every inner dict may
carry any subset of the model's column-backed predictors:
    population, num_households, poverty_incidence,
    disaster_risk_index, past_calamity_freq
Missing keys simply fall through to the synthetic value.

----------------------------------------------------------------------------
Sources
----------------------------------------------------------------------------
Urdaneta City
  * population     — Philippine Statistics Authority (PSA), "Total Population,
                     Urdaneta City", as of 01 July 2024. City total: 145,935.
  * num_households — PSA household count per barangay. City total: 40,015.
"""

# (city_municipality, barangay_name) -> {predictor: real value}
REAL_PROFILES = {}


# --- Urdaneta City ----------------------------------------------------------
_URDANETA_POPULATION_2024 = {
    "Anonas": 6285,
    "Bactad East": 2231,
    "Bayaoas": 5864,
    "Bolaoen": 1604,
    "Cabaruan": 2389,
    "Cabuloan": 3564,
    "Camanang": 5397,
    "Camantiles": 6564,
    "Casantaan": 1479,
    "Catablan": 6107,
    "Cayambanan": 4408,
    "Consolacion": 1830,
    "Dilan Paurido": 7186,
    "Dr. Pedro T. Orata": 3458,
    "Labit Proper": 3939,
    "Labit West": 2751,
    "Mabanogbog": 3564,
    "Macalong": 1756,
    "Nancalobasaan": 3364,
    "Nancamaliran East": 5284,
    "Nancamaliran West": 5981,
    "Nancayasan": 8175,
    "Oltama": 1422,
    "Palina East": 5190,
    "Palina West": 3443,
    "Pinmaludpod": 8324,
    "Poblacion": 7301,
    "San Jose": 5730,
    "San Vicente": 9532,
    "Santa Lucia": 3401,
    "Santo Domingo": 3423,
    "Sugcong": 1160,
    "Tipuso": 2262,
    "Tulong": 1567,
}

_URDANETA_HOUSEHOLDS_2024 = {
    "Anonas": 1625,
    "Bactad East": 704,
    "Bayaoas": 1658,
    "Bolaoen": 448,
    "Cabaruan": 692,
    "Cabuloan": 1060,
    "Camanang": 1282,
    "Camantiles": 1735,
    "Casantaan": 412,
    "Catablan": 1734,
    "Cayambanan": 1407,
    "Consolacion": 413,
    "Dilan Paurido": 1827,
    "Dr. Pedro T. Orata": 1322,
    "Labit Proper": 1009,
    "Labit West": 785,
    "Mabanogbog": 1004,
    "Macalong": 477,
    "Nancalobasaan": 1006,
    "Nancamaliran East": 1190,
    "Nancamaliran West": 1706,
    "Nancayasan": 2258,
    "Oltama": 367,
    "Palina East": 1265,
    "Palina West": 976,
    "Pinmaludpod": 2148,
    "Poblacion": 1767,
    "San Jose": 1756,
    "San Vicente": 2891,
    "Santa Lucia": 802,
    "Santo Domingo": 915,
    "Sugcong": 321,
    "Tipuso": 615,
    "Tulong": 438,
}

for _name, _pop in _URDANETA_POPULATION_2024.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["population"] = _pop
for _name, _hh in _URDANETA_HOUSEHOLDS_2024.items():
    REAL_PROFILES.setdefault(("Urdaneta City", _name), {})["num_households"] = _hh


def real_profile(city_municipality, barangay_name):
    """Real predictor values on record for one barangay, or {} if none.

    The keys are a subset of the model's column-backed predictors; the caller
    overlays them on top of a synthetic profile so unknown fields stay
    synthetic."""
    return dict(REAL_PROFILES.get((city_municipality, barangay_name), {}))
