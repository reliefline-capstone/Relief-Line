"""
REAL sample record given to the team: "Municipality of Sta. Barbara,
Pangasinan - Relief Distribution Status" (scanned 24 Sep 2026). Family Food
Packs (FFP) delivered to barangays after the late-August 2026 habagat
flooding (Pangasinan was placed under a state of calamity on 31 Aug 2026;
Sta. Barbara was one of the LGUs that declared it).

Two funding sources delivered in lots between 19 Aug and 2 Sep 2026:
  * DSWD - 21 barangays
  * LGU  - 19 lots (Maticmatic appears twice; Maticmatic 20 and Minien West 17
           are evacuation-center packs)

This is what was DISTRIBUTED (supply), not a measurement of what was needed,
so the generator uses it to calibrate scale and shape only (see
scripts/seed_monthly_history.py, calibration_report). Transcribed as printed;
names are matched to the barangays table accent-insensitively.
"""
import unicodedata

MONTH = "2026-08"

DSWD = {
    "Alibago": 497, "Balingueo": 300, "Banaoang": 350, "Banzal": 250,
    "Cablong": 257, "Dalongue": 729, "Erfe": 100, "Gueguesangen": 350,
    "Leet": 517, "Malanay": 300, "Maningding": 412, "Minien East": 275,
    "Minien West": 8, "Nilombot": 250, "Payas": 350, "Población Norte": 100,
    "Población Sur": 275, "Sapang": 400, "Sonquil": 1037, "Tuliao": 800,
    "Ventinilla": 1000,
}

# (barangay, packs) - a list, not a dict: Maticmatic has two LGU lots.
LGU = [
    ("Maningding", 600), ("Tuliao", 800), ("Leet", 500), ("Banaoang", 303),
    ("Tebag West", 400), ("Payas", 50), ("Alibago", 200),
    ("Población Norte", 350), ("Sapang", 200), ("Cablong", 250),
    ("Ventinilla", 100), ("Nilombot", 300), ("Banzal", 300),
    ("Maticmatic", 400), ("Carusuçan", 200), ("Maticmatic", 20),
    ("Minien West", 17), ("Erfe", 150), ("Malanay", 374),
]


def normalize(name):
    """Accent-insensitive key: 'Población Norte' -> 'poblacion norte',
    'Carusuçan' -> 'carusucan'. The barangays table spells the latter
    'Carusocan', so that one is aliased explicitly."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower().strip()
    return {"carusucan": "carusocan"}.get(s, s)


def combined_totals():
    """{normalized barangay name: packs} summed across DSWD and LGU lots."""
    totals = {}
    for name, qty in DSWD.items():
        totals[normalize(name)] = totals.get(normalize(name), 0) + qty
    for name, qty in LGU:
        totals[normalize(name)] = totals.get(normalize(name), 0) + qty
    return totals


if __name__ == "__main__":
    t = combined_totals()
    vals = sorted(t.values())
    print("DSWD total:", sum(DSWD.values()), "| LGU total:", sum(q for _n, q in LGU))
    print("barangays reached:", len(t), "| total packs:", sum(vals))
    print("per-barangay min/median/max:", vals[0], vals[len(vals) // 2], vals[-1])
