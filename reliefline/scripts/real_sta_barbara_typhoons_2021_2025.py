"""
REAL records given to the team: Santa Barbara per-barangay disaster reports
for 7 typhoons/combined events, 2021-2025 - additional real data alongside
the already-loaded Aug-2026 DSWD+LGU distribution sheet
(scripts/sample_sta_barbara_aug2026.py). Unlike Calasiao, many barangays here
are explicitly reported as unaffected ("No Typhoon"/"None" rows, 0 across the
board) rather than simply absent - these are CONFIRMED zeros (kept as 0, not
NULL/"not reported").

One file (Crising/Dante/Emong, Jul 2025) is a single relief report covering
THREE calendar typhoons at once - it maps to three typhoon_keys
(crising_2025, dante_2025, emong_2025) via one relief_events row and three
relief_event_typhoons rows, not a per-storm split the source data can't
support (see app/ml/train.py's p_relief()/climatology_by_month() - frequency
is counted off the calendar independently of how a report groups events).

Data-quality fixes applied at transcription time (source value -> corrected
value), matching same-year figures in the other Sta. Barbara files:
  * Karding (2022-09-25): Banaoang Total Individuals 4777 -> 4477 (matches
    Paeng/Maring/Egay 2022-2023 Banaoang figure); Tuliao Total Individuals
    6244 -> 6424 (matches Egay/Fabian... see next). Both look like a digit
    transposition in the same source file.
  * Fabian (2021-07-22): Banaoang Total Individuals 4777 -> 4477; Tuliao
    Total Individuals 6244 -> 6424. Same transposition pattern as Karding,
    likely from the same transcriber.

Dates normalized to ISO at transcription time (each source file used a
different format - DD/MM/YYYY, MM/DD/YYYY or YYYY-MM-DD - resolved against
scripts/typhoon_calendar_2021_2026.py's key_date/start_date where a raw date
was ambiguous on its own, e.g. Maring's "11/10/2021" -> 2021-10-11 matches
the calendar's key_date).

Run this file to print a structural sanity check per report.
"""
import csv
import io

from _barangay_names import strip_accents_and_punct

_FILES = {
    # Combined report: three calendar typhoons in one relief distribution.
    "crising_dante_emong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Crising/Dante/Emong,2025-07-22,269,1213,231,360,1489
Sta. Barbara,Balingueo,Crising/Dante/Emong,2025-07-22,717,3133,617,960,3845
Sta. Barbara,Banaoang,Crising/Dante/Emong,2025-07-22,784,4098,674,1050,5030
Sta. Barbara,Banzal,Crising/Dante/Emong,2025-07-22,246,1329,212,330,1631
Sta. Barbara,Botao,No Typhoon,,0,0,0,730,3608
Sta. Barbara,Cablong,No Typhoon,,0,0,0,550,2691
Sta. Barbara,Carusocan,No Typhoon,,0,0,0,390,1915
Sta. Barbara,Dalongue,Crising/Dante/Emong,2025-07-22,336,1749,289,450,2147
Sta. Barbara,Erfe,Crising/Dante/Emong,2025-07-22,119,609,102,160,747
Sta. Barbara,Gueguesangen,Crising/Dante/Emong,2025-07-22,284,1491,244,380,1830
Sta. Barbara,Leet,Crising/Dante/Emong,2025-07-22,739,3763,636,990,4618
Sta. Barbara,Malanay,Crising/Dante/Emong,2025-07-22,448,2261,385,600,2775
Sta. Barbara,Maningding,Crising/Dante/Emong,2025-07-22,784,4071,674,1050,4996
Sta. Barbara,Maronong,Crising/Dante/Emong,2025-07-22,560,2919,482,750,3582
Sta. Barbara,Maticmatic,Crising/Dante/Emong,2025-07-22,769,4043,661,1030,4962
Sta. Barbara,Minien East,No Typhoon,,0,0,0,690,3327
Sta. Barbara,Minien West,No Typhoon,,0,0,0,1090,5152
Sta. Barbara,Nilombot,Crising/Dante/Emong,2025-07-22,388,2031,334,520,2492
Sta. Barbara,Patayac,No Typhoon,,0,0,0,630,2984
Sta. Barbara,Payas,Crising/Dante/Emong,2025-07-22,612,3190,526,820,3915
Sta. Barbara,Poblacion Norte,Crising/Dante/Emong,2025-07-22,291,1514,250,390,1858
Sta. Barbara,Poblacion Sur,Crising/Dante/Emong,2025-07-22,340,1439,292,455,1766
Sta. Barbara,Primicias,Crising/Dante/Emong,2025-07-22,352,1482,303,472,1819
Sta. Barbara,Sapang,Crising/Dante/Emong,2025-07-22,396,1886,341,531,2315
Sta. Barbara,Sonquil,Crising/Dante/Emong,2025-07-22,576,2666,495,771,3272
Sta. Barbara,Tebag East,No Typhoon,,0,0,0,118,439
Sta. Barbara,Tebag West,Crising/Dante/Emong,2025-07-22,442,2068,380,592,2538
Sta. Barbara,Tuliao,Crising/Dante/Emong,2025-07-22,1122,5234,965,1503,6424
Sta. Barbara,Ventinilla,No Typhoon,,0,0,0,833,3485
""",
    "enteng_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Enteng,2024-08-31,150,600,129,360,1489
Sta. Barbara,Balingueo,None,,0,0,0,960,3845
Sta. Barbara,Banaoang,Enteng,2024-08-31,220,880,189,1050,5030
Sta. Barbara,Banzal,Enteng,2024-08-31,103,412,89,330,1631
Sta. Barbara,Botao,None,,0,0,0,730,3608
Sta. Barbara,Cablong,None,,0,0,0,550,2691
Sta. Barbara,Carusocan,None,,0,0,0,390,1915
Sta. Barbara,Dalongue,Enteng,2024-08-31,275,1100,236,450,2147
Sta. Barbara,Erfe,None,,0,0,0,160,747
Sta. Barbara,Gueguesangen,None,,0,0,0,380,1830
Sta. Barbara,Leet,Enteng,2024-08-31,190,760,163,990,4618
Sta. Barbara,Malanay,Enteng,2024-08-31,154,616,132,600,2775
Sta. Barbara,Maningding,Enteng,2024-08-31,255,1020,219,1050,4996
Sta. Barbara,Maronong,Enteng,2024-08-31,161,644,138,750,3582
Sta. Barbara,Maticmatic,Enteng,2024-08-31,224,896,193,1030,4962
Sta. Barbara,Minien East,None,,0,0,0,690,3327
Sta. Barbara,Minien West,None,,0,0,0,1090,5152
Sta. Barbara,Nilombot,Enteng,2024-08-31,139,556,120,520,2492
Sta. Barbara,Patayac,None,,0,0,0,630,2984
Sta. Barbara,Payas,Enteng,2024-08-31,197,788,169,820,3915
Sta. Barbara,Poblacion Norte,Enteng,2024-08-31,91,364,78,390,1858
Sta. Barbara,Poblacion Sur,Enteng,2024-08-31,98,392,84,455,1766
Sta. Barbara,Primicias,Enteng,2024-08-31,112,448,96,472,1819
Sta. Barbara,Sapang,Enteng,2024-08-31,121,484,104,531,2315
Sta. Barbara,Sonquil,Enteng,2024-08-31,376,1504,323,771,3272
Sta. Barbara,Tebag East,None,,0,0,0,118,439
Sta. Barbara,Tebag West,None,,0,0,0,592,2538
Sta. Barbara,Tuliao,Enteng,2024-08-31,259,1036,223,1503,6424
Sta. Barbara,Ventinilla,Enteng,2024-08-31,262,1048,225,833,3485
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Egay,2023-07-26,112,487,96,393,1564
Sta. Barbara,Balingueo,Egay,2023-07-26,248,1126,219,885,3911
Sta. Barbara,Banaoang,Egay,2023-07-26,302,1378,267,1066,4477
Sta. Barbara,Banzal,Egay,2023-07-26,126,536,111,422,1571
Sta. Barbara,Botao,Egay,2023-07-26,224,1073,198,788,3401
Sta. Barbara,Cablong,Egay,2023-07-26,205,1018,183,671,3058
Sta. Barbara,Carusocan,Egay,2023-07-26,145,641,128,479,1876
Sta. Barbara,Dalongue,Egay,2023-07-26,139,679,123,470,2030
Sta. Barbara,Erfe,Egay,2023-07-26,42,176,37,179,652
Sta. Barbara,Gueguesangen,Egay,2023-07-26,132,641,116,443,1831
Sta. Barbara,Leet,Egay,2023-07-26,495,2428,438,1724,7275
Sta. Barbara,Malanay,Egay,2023-07-26,187,913,164,638,2764
Sta. Barbara,Maningding,Egay,2023-07-26,356,1742,315,1188,4890
Sta. Barbara,Maronong,Egay,2023-07-26,235,1141,208,802,3304
Sta. Barbara,Maticmatic,Egay,2023-07-26,343,1789,305,1165,5116
Sta. Barbara,Minien East,Egay,2023-07-26,218,1097,192,759,3260
Sta. Barbara,Minien West,Egay,2023-07-26,379,1846,337,1264,5230
Sta. Barbara,Nilombot,Egay,2023-07-26,174,862,154,577,2434
Sta. Barbara,Patayac,Egay,2023-07-26,207,1005,183,704,2880
Sta. Barbara,Payas,Egay,2023-07-26,271,1438,242,858,3928
Sta. Barbara,Poblacion Norte,Egay,2023-07-26,326,1571,290,1059,4677
Sta. Barbara,Poblacion Sur,Egay,2023-07-26,137,614,121,455,1766
Sta. Barbara,Primicias,Egay,2023-07-26,125,574,111,472,1819
Sta. Barbara,Sapang,Egay,2023-07-26,166,815,148,531,2315
Sta. Barbara,Sonquil,Egay,2023-07-26,238,1197,212,771,3272
Sta. Barbara,Tebag East,Egay,2023-07-26,34,143,30,118,439
Sta. Barbara,Tebag West,Egay,2023-07-26,172,851,153,592,2538
Sta. Barbara,Tuliao,Egay,2023-07-26,498,2264,441,1503,6424
Sta. Barbara,Ventinilla,Egay,2023-07-26,258,1249,230,833,3485
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Paeng,2022-10-30,71,274,58,393,1564
Sta. Barbara,Balingueo,Paeng,2022-10-30,195,849,168,885,3911
Sta. Barbara,Banaoang,Paeng,2022-10-30,213,895,192,1066,4477
Sta. Barbara,Banzal,Paeng,2022-10-30,106,401,100,422,1571
Sta. Barbara,Botao,Paeng,2022-10-30,134,596,110,788,3401
Sta. Barbara,Cablong,Paeng,2022-10-30,154,681,132,671,3058
Sta. Barbara,Carusocan,Paeng,2022-10-30,134,517,121,479,1876
Sta. Barbara,Dalongue,Paeng,2022-10-30,113,488,106,470,2030
Sta. Barbara,Erfe,Paeng,2022-10-30,27,100,22,179,652
Sta. Barbara,Gueguesangen,Paeng,2022-10-30,84,358,72,443,1831
Sta. Barbara,Leet,Paeng,2022-10-30,448,1834,403,1724,7275
Sta. Barbara,Malanay,Paeng,2022-10-30,134,572,126,638,2764
Sta. Barbara,Maningding,Paeng,2022-10-30,285,1173,234,1188,4890
Sta. Barbara,Maronong,Paeng,2022-10-30,160,669,138,802,3304
Sta. Barbara,Maticmatic,Paeng,2022-10-30,315,1425,284,1165,5116
Sta. Barbara,Minien East,Paeng,2022-10-30,137,571,129,759,3260
Sta. Barbara,Minien West,Paeng,2022-10-30,316,1288,259,1264,5230
Sta. Barbara,Nilombot,Paeng,2022-10-30,127,536,109,577,2434
Sta. Barbara,Patayac,Paeng,2022-10-30,113,469,102,704,2880
Sta. Barbara,Payas,Paeng,2022-10-30,180,849,169,858,3928
Sta. Barbara,Poblacion Norte,Paeng,2022-10-30,244,1045,200,1059,4677
Sta. Barbara,Poblacion Sur,Paeng,2022-10-30,86,329,74,455,1766
Sta. Barbara,Primicias,Paeng,2022-10-30,80,308,72,472,1819
Sta. Barbara,Sapang,Paeng,2022-10-30,117,518,110,531,2315
Sta. Barbara,Sonquil,Paeng,2022-10-30,216,944,177,771,3272
Sta. Barbara,Tebag East,Paeng,2022-10-30,17,61,15,118,439
Sta. Barbara,Tebag West,Paeng,2022-10-30,118,498,106,592,2538
Sta. Barbara,Tuliao,Paeng,2022-10-30,451,1928,424,1503,6424
Sta. Barbara,Ventinilla,Paeng,2022-10-30,200,849,164,833,3485
""",
    # Data-quality fix applied: Banaoang Total Individuals 4777->4477, Tuliao
    # Total Individuals 6244->6424 (see module docstring).
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Karding,2022-09-26,11,48,8,393,1564
Sta. Barbara,Balingueo,Karding,2022-09-26,16,81,12,885,3911
Sta. Barbara,Banaoang,Karding,2022-09-26,39,196,31,1066,4477
Sta. Barbara,Banzal,Karding,2022-09-26,10,46,8,422,1571
Sta. Barbara,Botao,Karding,2022-09-26,25,119,22,788,3401
Sta. Barbara,Cablong,Karding,2022-09-26,27,141,19,671,3058
Sta. Barbara,Carusocan,Karding,2022-09-26,9,42,7,479,1876
Sta. Barbara,Dalongue,Karding,2022-09-26,17,91,14,470,2030
Sta. Barbara,Erfe,Karding,2022-09-26,4,16,3,179,652
Sta. Barbara,Gueguesangen,Karding,2022-09-26,12,57,11,443,1831
Sta. Barbara,Leet,Karding,2022-09-26,78,394,55,1724,7275
Sta. Barbara,Malanay,Karding,2022-09-26,20,108,15,638,2764
Sta. Barbara,Maningding,Karding,2022-09-26,43,195,34,1188,4890
Sta. Barbara,Maronong,Karding,2022-09-26,18,85,15,802,3304
Sta. Barbara,Maticmatic,Karding,2022-09-26,48,253,43,1165,5116
Sta. Barbara,Minien East,Karding,2022-09-26,21,112,15,759,3260
Sta. Barbara,Minien West,Karding,2022-09-26,46,210,34,1264,5230
Sta. Barbara,Nilombot,Karding,2022-09-26,13,63,10,577,2434
Sta. Barbara,Patayac,Karding,2022-09-26,22,108,19,704,2880
Sta. Barbara,Payas,Karding,2022-09-26,31,177,28,858,3928
Sta. Barbara,Poblacion Norte,Karding,2022-09-26,43,210,30,1059,4677
Sta. Barbara,Poblacion Sur,Karding,2022-09-26,8,36,6,455,1766
Sta. Barbara,Primicias,Karding,2022-09-26,11,51,9,472,1819
Sta. Barbara,Sapang,Karding,2022-09-26,17,92,14,531,2315
Sta. Barbara,Sonquil,Karding,2022-09-26,28,131,25,771,3272
Sta. Barbara,Tebag East,Karding,2022-09-26,2,8,1,118,439
Sta. Barbara,Tebag West,Karding,2022-09-26,16,82,12,592,2538
Sta. Barbara,Tuliao,Karding,2022-09-26,68,362,54,1503,6424
Sta. Barbara,Ventinilla,Karding,2022-09-26,27,124,23,833,3485
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Maring,2021-10-11,179,834,147,393,1564
Sta. Barbara,Balingueo,Maring,2021-10-11,402,2086,362,885,3911
Sta. Barbara,Banaoang,Maring,2021-10-11,484,2388,411,1066,4477
Sta. Barbara,Banzal,Maring,2021-10-11,192,838,169,422,1571
Sta. Barbara,Botao,Maring,2021-10-11,358,1814,286,788,3401
Sta. Barbara,Cablong,Maring,2021-10-11,305,1631,274,671,3058
Sta. Barbara,Carusocan,Maring,2021-10-11,218,1001,183,479,1876
Sta. Barbara,Dalongue,Maring,2021-10-11,214,1083,186,470,2030
Sta. Barbara,Erfe,Maring,2021-10-11,81,348,65,179,652
Sta. Barbara,Gueguesangen,Maring,2021-10-11,201,977,181,443,1831
Sta. Barbara,Leet,Maring,2021-10-11,783,3881,673,1724,7275
Sta. Barbara,Malanay,Maring,2021-10-11,290,1474,241,638,2764
Sta. Barbara,Maningding,Maring,2021-10-11,540,2609,475,1188,4890
Sta. Barbara,Maronong,Maring,2021-10-11,365,1763,310,802,3304
Sta. Barbara,Maticmatic,Maring,2021-10-11,529,2729,476,1165,5116
Sta. Barbara,Minien East,Maring,2021-10-11,345,1739,283,759,3260
Sta. Barbara,Minien West,Maring,2021-10-11,574,2790,499,1264,5230
Sta. Barbara,Nilombot,Maring,2021-10-11,262,1298,220,577,2434
Sta. Barbara,Patayac,Maring,2021-10-11,320,1536,285,704,2880
Sta. Barbara,Payas,Maring,2021-10-11,390,2095,335,858,3928
Sta. Barbara,Poblacion Norte,Maring,2021-10-11,481,2495,399,1059,4677
Sta. Barbara,Poblacion Sur,Maring,2021-10-11,207,942,186,455,1766
Sta. Barbara,Primicias,Maring,2021-10-11,215,970,187,472,1819
Sta. Barbara,Sapang,Maring,2021-10-11,241,1235,205,531,2315
Sta. Barbara,Sonquil,Maring,2021-10-11,350,1745,308,771,3272
Sta. Barbara,Tebag East,Maring,2021-10-11,54,234,43,118,439
Sta. Barbara,Tebag West,Maring,2021-10-11,269,1354,231,592,2538
Sta. Barbara,Tuliao,Maring,2021-10-11,683,3427,615,1503,6424
Sta. Barbara,Ventinilla,Maring,2021-10-11,379,1859,318,833,3485
""",
    # Data-quality fix applied: Banaoang Total Individuals 4777->4477, Tuliao
    # Total Individuals 6244->6424 (see module docstring).
    "fabian_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Fabian,2021-07-22,39,171,28,393,1564
Sta. Barbara,Balingueo,Fabian,2021-07-22,72,366,55,885,3911
Sta. Barbara,Banaoang,Fabian,2021-07-22,131,659,106,1066,4477
Sta. Barbara,Banzal,Fabian,2021-07-22,38,176,32,422,1571
Sta. Barbara,Botao,Fabian,2021-07-22,86,410,77,788,3401
Sta. Barbara,Cablong,Fabian,2021-07-22,88,461,63,671,3058
Sta. Barbara,Carusocan,Fabian,2021-07-22,37,173,28,479,1876
Sta. Barbara,Dalongue,Fabian,2021-07-22,66,354,53,470,2030
Sta. Barbara,Erfe,Fabian,2021-07-22,15,61,13,179,652
Sta. Barbara,Gueguesangen,Fabian,2021-07-22,46,219,41,443,1831
Sta. Barbara,Leet,Fabian,2021-07-22,266,1345,192,1724,7275
Sta. Barbara,Malanay,Fabian,2021-07-22,72,388,55,638,2764
Sta. Barbara,Maningding,Fabian,2021-07-22,151,686,122,1188,4890
Sta. Barbara,Maronong,Fabian,2021-07-22,77,364,66,802,3304
Sta. Barbara,Maticmatic,Fabian,2021-07-22,169,889,152,1165,5116
Sta. Barbara,Minien East,Fabian,2021-07-22,90,481,65,759,3260
Sta. Barbara,Minien West,Fabian,2021-07-22,172,786,132,1264,5230
Sta. Barbara,Nilombot,Fabian,2021-07-22,52,252,42,577,2434
Sta. Barbara,Patayac,Fabian,2021-07-22,77,377,66,704,2880
Sta. Barbara,Payas,Fabian,2021-07-22,105,598,94,858,3928
Sta. Barbara,Poblacion Norte,Fabian,2021-07-22,159,775,114,1059,4677
Sta. Barbara,Poblacion Sur,Fabian,2021-07-22,37,165,28,455,1766
Sta. Barbara,Primicias,Fabian,2021-07-22,47,216,38,472,1819
Sta. Barbara,Sapang,Fabian,2021-07-22,60,326,51,531,2315
Sta. Barbara,Sonquil,Fabian,2021-07-22,102,478,92,771,3272
Sta. Barbara,Tebag East,Fabian,2021-07-22,9,38,6,118,439
Sta. Barbara,Tebag West,Fabian,2021-07-22,62,318,47,592,2538
Sta. Barbara,Tuliao,Fabian,2021-07-22,239,1271,194,1503,6424
Sta. Barbara,Ventinilla,Fabian,2021-07-22,99,456,85,833,3485
""",
}

# typhoon_key(s) matching scripts/typhoon_calendar_2021_2026.py
_TYPHOON_KEYS = {
    "crising_dante_emong_2025": ["crising_2025", "dante_2025", "emong_2025"],
    "enteng_2024": ["enteng_2024"],
    "egay_2023": ["egay_2023"],
    "paeng_2022": ["paeng_2022"],
    "karding_2022": ["karding_2022"],
    "maring_2021": ["maring_2021"],
    "fabian_2021": ["fabian_2021"],
}


def normalize(name):
    return strip_accents_and_punct(name)


def parse(report_key):
    reader = csv.DictReader(io.StringIO(_FILES[report_key]))
    rows = []
    for r in reader:
        if r["Name of Typhoon"] in ("No Typhoon", "None"):
            continue  # confirmed zero - real, but nothing to attribute to the storm(s)
        rows.append({
            "barangay": r["Barangay"],
            "date": r["Date ng Typhoon"],
            "affected_families": int(r["Affected Families"]),
            "affected_individuals": int(r["Affected Individuals"]),
            "food_packs_given": int(r["Food Packs Given"]),
            "total_families": int(r["Total Number of Families"]),
            "total_individuals": int(r["Total Number of Individuals"]),
        })
    return rows


def all_barangay_rows(report_key):
    """Every barangay including confirmed-zero ones, for the structural
    check and for population-snapshot backfill (real_profiles.py needs every
    barangay's Total Number of Families, not just the affected ones)."""
    reader = csv.DictReader(io.StringIO(_FILES[report_key]))
    return [{
        "barangay": r["Barangay"],
        "total_families": int(r["Total Number of Families"]),
        "total_individuals": int(r["Total Number of Individuals"]),
        "affected": r["Name of Typhoon"] not in ("No Typhoon", "None"),
    } for r in reader]


REPORTS = [
    {"key": key, "typhoon_keys": _TYPHOON_KEYS[key], "rows": parse(key), "all_rows": all_barangay_rows(key)}
    for key in _FILES
]


if __name__ == "__main__":
    ok = True
    for rep in REPORTS:
        rows, all_rows = rep["rows"], rep["all_rows"]
        fam = sum(r["affected_families"] for r in rows)
        packs = sum(r["food_packs_given"] for r in rows)
        good = len(all_rows) == 29
        ok &= good
        print(f"{rep['key']:<26} 29 brgy={len(all_rows) == 29!s:<6} affected={len(rows):>2}/29 "
              f"families={fam:>6,} packs={packs:>6,}  {'OK' if good else 'MISMATCH'}")
    print("\nAll 7 Sta. Barbara reports structurally OK." if ok else "\nMISMATCH - recheck transcription.")
