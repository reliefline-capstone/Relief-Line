"""
REAL records given to the team: Urdaneta City CSWDO per-barangay disaster
reports for 14 typhoon reports, 2021-2026, all in the same clean tabulated
CSV format (updated dataset delivered 2026-10-03).

This single module replaces the two earlier Urdaneta sources:
  * real_urdaneta_typhoons_2021_2025.py - the same 10 non-2025-season reports,
    but with "Total Number of Families/Individuals" figures that the updated
    dataset revised (e.g. Sugcong 85 -> 321 families for Maymay);
  * real_urdaneta_reports_2025.py - Dante/Emong, Mirasol/Nando, Paolo, Uwan,
    whose pack counts had to be read out of free-text Remarks and which had no
    population snapshot. The updated dataset gives all four as clean CSVs with
    Food Packs Given and population columns, so no extraction is needed.

Combined reports spanning more than one calendar typhoon:
  Nika + Ofel + Pepito   (Nov 2024) -> nika_2024, ofel_2024, pepito_2024
  Kristine + Leon        (Oct 2024) -> kristine_2024, leon_2024
  Dante & Emong          (Jul 2025) -> dante_2025, emong_2025
  Mirasol & Nando        (Sep 2025) -> mirasol_2025, nando_2025
  Fabian + Habagat       (Jul 2021) -> fabian_2021 ("Habagat" is enhanced
                                        monsoon alongside Fabian, not itself
                                        a named calendar typhoon)
  Enteng + Habagat       (Sep 2024) -> enteng_2024 (same habagat pattern)
One relief_events row per report, one relief_event_typhoons row per named
calendar typhoon it maps to (see scripts/apply_relief_schema.py) - frequency
and P(relief) are counted off the calendar/linkage independently, so a
combined report never needs (and the source data can't support) a per-storm
pack split.

Data-quality notes kept from the source (not corrected - figures are as given):
  * Cabuloan (Mirasol & Nando): 5,010 individuals for 202 families looks like
    a typo; kept. Individuals are not used by the model.
  * Paolo: Bactad East reports 693 affected families against 601 total
    families, and several barangays got more packs than affected families
    (e.g. Consolacion 500 packs / 303 families). The model uses packs, so
    these are kept as reported.

Run this file to print a structural sanity check per report.
"""
import csv
import io

from _barangay_names import strip_accents_and_punct


def normalize(name):
    """Folds Urdaneta's report spellings onto the barangays table:
    'Dilan-Paurido' -> 'dilan paurido', 'Pedro T. Orata' -> 'dr pedro t orata',
    'Tiposu' -> 'tipuso', 'Sta. Lucia' -> 'santa lucia'."""
    s = strip_accents_and_punct(name)
    return {
        "pedro t orata": "dr pedro t orata", "tiposu": "tipuso", "sta lucia": "santa lucia",
    }.get(s, s)


_FILES = {
    "maymay_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Maymay,2026-08-05,0,0,0,1540,6285
City of Urdaneta,Bactad East,Maymay,2026-08-05,0,0,0,611,2231
City of Urdaneta,Bayaoas,Maymay,2026-08-05,0,0,0,1635,5864
City of Urdaneta,Bolaoen,Maymay,2026-08-05,0,0,0,432,1604
City of Urdaneta,Cabaruan,Maymay,2026-08-05,0,0,0,624,2389
City of Urdaneta,Cabuloan,Maymay,2026-08-05,2,6,2,915,3564
City of Urdaneta,Camanang,Maymay,2026-08-05,0,0,0,1335,5397
City of Urdaneta,Camantiles,Maymay,2026-08-05,0,0,0,1732,6564
City of Urdaneta,Casantaan,Maymay,2026-08-05,0,0,0,456,1479
City of Urdaneta,Catablan,Maymay,2026-08-05,0,0,0,1695,6107
City of Urdaneta,Cayambanan,Maymay,2026-08-05,0,0,0,1267,4408
City of Urdaneta,Consolacion,Maymay,2026-08-05,0,0,0,480,1830
City of Urdaneta,Dilan-Paurido,Maymay,2026-08-05,0,0,0,1983,7186
City of Urdaneta,Labit Proper,Maymay,2026-08-05,0,0,0,968,3939
City of Urdaneta,Labit West,Maymay,2026-08-05,0,0,0,726,2751
City of Urdaneta,Mabanogbog,Maymay,2026-08-05,0,0,0,975,3564
City of Urdaneta,Macalong,Maymay,2026-08-05,0,0,0,495,1756
City of Urdaneta,Nancalobasaan,Maymay,2026-08-05,0,0,0,860,3364
City of Urdaneta,Nancamaliran East,Maymay,2026-08-05,0,0,0,1502,5284
City of Urdaneta,Nancamaliran West,Maymay,2026-08-05,0,0,0,1595,5981
City of Urdaneta,Nancayasan,Maymay,2026-08-05,1,3,1,2397,8175
City of Urdaneta,Oltama,Maymay,2026-08-05,0,0,0,399,1422
City of Urdaneta,Palina East,Maymay,2026-08-05,0,0,0,1425,5190
City of Urdaneta,Palina West,Maymay,2026-08-05,0,0,0,948,3443
City of Urdaneta,Pedro T. Orata,Maymay,2026-08-05,0,0,0,670,3458
City of Urdaneta,Pinmaludpod,Maymay,2026-08-05,0,0,0,2171,8324
City of Urdaneta,Poblacion,Maymay,2026-08-05,0,0,0,1958,7301
City of Urdaneta,San Jose,Maymay,2026-08-05,0,0,0,1554,5730
City of Urdaneta,San Vicente,Maymay,2026-08-05,0,0,0,2624,9532
City of Urdaneta,Santa Lucia,Maymay,2026-08-05,0,0,0,940,3401
City of Urdaneta,Santo Domingo,Maymay,2026-08-05,0,0,0,954,3423
City of Urdaneta,Sugcong,Maymay,2026-08-05,0,0,0,321,1160
City of Urdaneta,Tiposu,Maymay,2026-08-05,0,0,0,558,2262
City of Urdaneta,Tulong,Maymay,2026-08-05,0,0,0,400,1567
""",
    "uwan_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Uwan,2025-11-03 to 2025-11-25,114,348,100,1513,6285
City of Urdaneta,Bactad East,Uwan,2025-11-03 to 2025-11-25,19,57,10,601,2231
City of Urdaneta,Bayaoas,Uwan,2025-11-03 to 2025-11-25,139,415,100,1607,5864
City of Urdaneta,Bolaoen,Uwan,2025-11-03 to 2025-11-25,0,0,0,425,1604
City of Urdaneta,Cabaruan,Uwan,2025-11-03 to 2025-11-25,51,150,40,613,2389
City of Urdaneta,Cabuloan,Uwan,2025-11-03 to 2025-11-25,21,64,20,899,3564
City of Urdaneta,Camanang,Uwan,2025-11-03 to 2025-11-25,61,191,50,1312,5397
City of Urdaneta,Camantiles,Uwan,2025-11-03 to 2025-11-25,65,201,50,1702,6564
City of Urdaneta,Casantaan,Uwan,2025-11-03 to 2025-11-25,12,38,10,448,1479
City of Urdaneta,Catablan,Uwan,2025-11-03 to 2025-11-25,142,403,100,1666,6107
City of Urdaneta,Cayambanan,Uwan,2025-11-03 to 2025-11-25,38,116,25,1245,4408
City of Urdaneta,Consolacion,Uwan,2025-11-03 to 2025-11-25,23,71,20,472,1830
City of Urdaneta,Dilan-Paurido,Uwan,2025-11-03 to 2025-11-25,67,202,25,1949,7186
City of Urdaneta,Labit Proper,Uwan,2025-11-03 to 2025-11-25,16,53,10,951,3939
City of Urdaneta,Labit West,Uwan,2025-11-03 to 2025-11-25,14,44,10,713,2751
City of Urdaneta,Mabanogbog,Uwan,2025-11-03 to 2025-11-25,20,58,20,958,3564
City of Urdaneta,Macalong,Uwan,2025-11-03 to 2025-11-25,15,50,10,486,1756
City of Urdaneta,Nancalobasaan,Uwan,2025-11-03 to 2025-11-25,55,166,30,845,3364
City of Urdaneta,Nancamaliran East,Uwan,2025-11-03 to 2025-11-25,41,123,20,1476,5284
City of Urdaneta,Nancamaliran West,Uwan,2025-11-03 to 2025-11-25,2,14,0,1567,5981
City of Urdaneta,Nancayasan,Uwan,2025-11-03 to 2025-11-25,43,131,0,2355,8175
City of Urdaneta,Oltama,Uwan,2025-11-03 to 2025-11-25,31,92,10,392,1422
City of Urdaneta,Palina East,Uwan,2025-11-03 to 2025-11-25,16,47,10,1400,5190
City of Urdaneta,Palina West,Uwan,2025-11-03 to 2025-11-25,33,104,30,932,3443
City of Urdaneta,Pedro T. Orata,Uwan,2025-11-03 to 2025-11-25,0,0,0,659,3458
City of Urdaneta,Pinmaludpod,Uwan,2025-11-03 to 2025-11-25,61,184,50,2133,8324
City of Urdaneta,Poblacion,Uwan,2025-11-03 to 2025-11-25,22,67,10,1923,7301
City of Urdaneta,San Jose,Uwan,2025-11-03 to 2025-11-25,88,263,50,1527,5730
City of Urdaneta,San Vicente,Uwan,2025-11-03 to 2025-11-25,122,359,100,2578,9532
City of Urdaneta,Santa Lucia,Uwan,2025-11-03 to 2025-11-25,0,0,0,924,3401
City of Urdaneta,Santo Domingo,Uwan,2025-11-03 to 2025-11-25,0,0,0,937,3423
City of Urdaneta,Sugcong,Uwan,2025-11-03 to 2025-11-25,13,41,10,316,1160
City of Urdaneta,Tiposu,Uwan,2025-11-03 to 2025-11-25,11,35,10,548,2262
City of Urdaneta,Tulong,Uwan,2025-11-03 to 2025-11-25,25,75,20,393,1567
""",
    "ramil_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Ramil,2025-10-17 to 2025-10-19,2,6,2,1513,6285
City of Urdaneta,Bactad East,Ramil,2025-10-17 to 2025-10-19,1,4,1,601,2231
City of Urdaneta,Bayaoas,Ramil,2025-10-17 to 2025-10-19,2,6,2,1607,5864
City of Urdaneta,Bolaoen,Ramil,2025-10-17 to 2025-10-19,1,3,1,425,1604
City of Urdaneta,Cabaruan,Ramil,2025-10-17 to 2025-10-19,0,0,0,613,2389
City of Urdaneta,Cabuloan,Ramil,2025-10-17 to 2025-10-19,1,3,1,899,3564
City of Urdaneta,Camanang,Ramil,2025-10-17 to 2025-10-19,2,6,1,1312,5397
City of Urdaneta,Camantiles,Ramil,2025-10-17 to 2025-10-19,2,6,2,1702,6564
City of Urdaneta,Casantaan,Ramil,2025-10-17 to 2025-10-19,1,3,1,448,1479
City of Urdaneta,Catablan,Ramil,2025-10-17 to 2025-10-19,3,9,2,1666,6107
City of Urdaneta,Cayambanan,Ramil,2025-10-17 to 2025-10-19,1,3,1,1245,4408
City of Urdaneta,Consolacion,Ramil,2025-10-17 to 2025-10-19,1,3,1,472,1830
City of Urdaneta,Dilan-Paurido,Ramil,2025-10-17 to 2025-10-19,2,7,2,1949,7186
City of Urdaneta,Labit Proper,Ramil,2025-10-17 to 2025-10-19,1,3,1,951,3939
City of Urdaneta,Labit West,Ramil,2025-10-17 to 2025-10-19,1,3,1,713,2751
City of Urdaneta,Mabanogbog,Ramil,2025-10-17 to 2025-10-19,1,3,1,958,3564
City of Urdaneta,Macalong,Ramil,2025-10-17 to 2025-10-19,1,3,1,486,1756
City of Urdaneta,Nancalobasaan,Ramil,2025-10-17 to 2025-10-19,1,3,1,845,3364
City of Urdaneta,Nancamaliran East,Ramil,2025-10-17 to 2025-10-19,1,3,1,1476,5284
City of Urdaneta,Nancamaliran West,Ramil,2025-10-17 to 2025-10-19,1,3,1,1567,5981
City of Urdaneta,Nancayasan,Ramil,2025-10-17 to 2025-10-19,1,3,1,2355,8175
City of Urdaneta,Oltama,Ramil,2025-10-17 to 2025-10-19,0,0,0,392,1422
City of Urdaneta,Palina East,Ramil,2025-10-17 to 2025-10-19,1,3,1,1400,5190
City of Urdaneta,Palina West,Ramil,2025-10-17 to 2025-10-19,2,6,2,932,3443
City of Urdaneta,Pedro T. Orata,Ramil,2025-10-17 to 2025-10-19,1,3,1,659,3458
City of Urdaneta,Pinmaludpod,Ramil,2025-10-17 to 2025-10-19,3,11,3,2133,8324
City of Urdaneta,Poblacion,Ramil,2025-10-17 to 2025-10-19,1,3,1,1923,7301
City of Urdaneta,San Jose,Ramil,2025-10-17 to 2025-10-19,3,9,2,1527,5730
City of Urdaneta,San Vicente,Ramil,2025-10-17 to 2025-10-19,2,6,1,2578,9532
City of Urdaneta,Santa Lucia,Ramil,2025-10-17 to 2025-10-19,1,3,1,924,3401
City of Urdaneta,Santo Domingo,Ramil,2025-10-17 to 2025-10-19,1,3,1,937,3423
City of Urdaneta,Sugcong,Ramil,2025-10-17 to 2025-10-19,0,0,0,316,1160
City of Urdaneta,Tiposu,Ramil,2025-10-17 to 2025-10-19,0,0,0,548,2262
City of Urdaneta,Tulong,Ramil,2025-10-17 to 2025-10-19,2,6,2,393,1567
""",
    "paolo_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Paolo,2025-10-01 to 2025-10-04,755,1113,500,1513,6285
City of Urdaneta,Bactad East,Paolo,2025-10-01 to 2025-10-04,693,1126,500,601,2231
City of Urdaneta,Bayaoas,Paolo,2025-10-01 to 2025-10-04,870,1222,570,1607,5864
City of Urdaneta,Bolaoen,Paolo,2025-10-01 to 2025-10-04,236,700,200,425,1604
City of Urdaneta,Cabaruan,Paolo,2025-10-01 to 2025-10-04,0,0,0,613,2389
City of Urdaneta,Cabuloan,Paolo,2025-10-01 to 2025-10-04,226,655,200,899,3564
City of Urdaneta,Camanang,Paolo,2025-10-01 to 2025-10-04,356,1115,300,1312,5397
City of Urdaneta,Camantiles,Paolo,2025-10-01 to 2025-10-04,423,1106,300,1702,6564
City of Urdaneta,Casantaan,Paolo,2025-10-01 to 2025-10-04,348,1026,300,448,1479
City of Urdaneta,Catablan,Paolo,2025-10-01 to 2025-10-04,633,1989,500,1666,6107
City of Urdaneta,Cayambanan,Paolo,2025-10-01 to 2025-10-04,340,989,300,1245,4408
City of Urdaneta,Consolacion,Paolo,2025-10-01 to 2025-10-04,303,1003,500,472,1830
City of Urdaneta,Dilan-Paurido,Paolo,2025-10-01 to 2025-10-04,500,1402,500,1949,7186
City of Urdaneta,Labit Proper,Paolo,2025-10-01 to 2025-10-04,303,758,300,951,3939
City of Urdaneta,Labit West,Paolo,2025-10-01 to 2025-10-04,415,1015,300,713,2751
City of Urdaneta,Mabanogbog,Paolo,2025-10-01 to 2025-10-04,398,1102,300,958,3564
City of Urdaneta,Macalong,Paolo,2025-10-01 to 2025-10-04,202,565,200,486,1756
City of Urdaneta,Nancalobasaan,Paolo,2025-10-01 to 2025-10-04,554,1204,554,845,3364
City of Urdaneta,Nancamaliran East,Paolo,2025-10-01 to 2025-10-04,305,789,300,1476,5284
City of Urdaneta,Nancamaliran West,Paolo,2025-10-01 to 2025-10-04,500,1316,500,1567,5981
City of Urdaneta,Nancayasan,Paolo,2025-10-01 to 2025-10-04,500,1326,500,2355,8175
City of Urdaneta,Oltama,Paolo,2025-10-01 to 2025-10-04,0,0,0,392,1422
City of Urdaneta,Palina East,Paolo,2025-10-01 to 2025-10-04,405,1056,300,1400,5190
City of Urdaneta,Palina West,Paolo,2025-10-01 to 2025-10-04,500,1153,500,932,3443
City of Urdaneta,Pedro T. Orata,Paolo,2025-10-01 to 2025-10-04,303,706,300,659,3458
City of Urdaneta,Pinmaludpod,Paolo,2025-10-01 to 2025-10-04,500,1416,500,2133,8324
City of Urdaneta,Poblacion,Paolo,2025-10-01 to 2025-10-04,788,1986,500,1923,7301
City of Urdaneta,San Jose,Paolo,2025-10-01 to 2025-10-04,658,1289,500,1527,5730
City of Urdaneta,San Vicente,Paolo,2025-10-01 to 2025-10-04,567,1681,567,2578,9532
City of Urdaneta,Santa Lucia,Paolo,2025-10-01 to 2025-10-04,455,1056,500,924,3401
City of Urdaneta,Santo Domingo,Paolo,2025-10-01 to 2025-10-04,389,1022,500,937,3423
City of Urdaneta,Sugcong,Paolo,2025-10-01 to 2025-10-04,0,0,0,316,1160
City of Urdaneta,Tiposu,Paolo,2025-10-01 to 2025-10-04,298,1181,500,548,2262
City of Urdaneta,Tulong,Paolo,2025-10-01 to 2025-10-04,289,860,200,393,1567
""",
    "mirasol_nando_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Mirasol & Nando,2025-09-16 to 2025-09-26,653,2080,300,1513,6285
City of Urdaneta,Bactad East,Mirasol & Nando,2025-09-16 to 2025-09-26,30,112,0,601,2231
City of Urdaneta,Bayaoas,Mirasol & Nando,2025-09-16 to 2025-09-26,408,955,298,1607,5864
City of Urdaneta,Bolaoen,Mirasol & Nando,2025-09-16 to 2025-09-26,100,301,80,425,1604
City of Urdaneta,Cabaruan,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,613,2389
City of Urdaneta,Cabuloan,Mirasol & Nando,2025-09-16 to 2025-09-26,202,5010,100,899,3564
City of Urdaneta,Camanang,Mirasol & Nando,2025-09-16 to 2025-09-26,258,439,170,1312,5397
City of Urdaneta,Camantiles,Mirasol & Nando,2025-09-16 to 2025-09-26,218,454,160,1702,6564
City of Urdaneta,Casantaan,Mirasol & Nando,2025-09-16 to 2025-09-26,156,253,150,448,1479
City of Urdaneta,Catablan,Mirasol & Nando,2025-09-16 to 2025-09-26,651,1979,467,1666,6107
City of Urdaneta,Cayambanan,Mirasol & Nando,2025-09-16 to 2025-09-26,103,223,100,1245,4408
City of Urdaneta,Consolacion,Mirasol & Nando,2025-09-16 to 2025-09-26,123,253,100,472,1830
City of Urdaneta,Dilan-Paurido,Mirasol & Nando,2025-09-16 to 2025-09-26,448,1350,250,1949,7186
City of Urdaneta,Labit Proper,Mirasol & Nando,2025-09-16 to 2025-09-26,125,305,100,951,3939
City of Urdaneta,Labit West,Mirasol & Nando,2025-09-16 to 2025-09-26,353,981,277,713,2751
City of Urdaneta,Mabanogbog,Mirasol & Nando,2025-09-16 to 2025-09-26,235,598,100,958,3564
City of Urdaneta,Macalong,Mirasol & Nando,2025-09-16 to 2025-09-26,160,284,140,486,1756
City of Urdaneta,Nancalobasaan,Mirasol & Nando,2025-09-16 to 2025-09-26,270,618,202,845,3364
City of Urdaneta,Nancamaliran East,Mirasol & Nando,2025-09-16 to 2025-09-26,99,200,80,1476,5284
City of Urdaneta,Nancamaliran West,Mirasol & Nando,2025-09-16 to 2025-09-26,120,266,100,1567,5981
City of Urdaneta,Nancayasan,Mirasol & Nando,2025-09-16 to 2025-09-26,310,742,220,2355,8175
City of Urdaneta,Oltama,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,392,1422
City of Urdaneta,Palina East,Mirasol & Nando,2025-09-16 to 2025-09-26,253,560,100,1400,5190
City of Urdaneta,Palina West,Mirasol & Nando,2025-09-16 to 2025-09-26,398,1002,220,932,3443
City of Urdaneta,Pedro T. Orata,Mirasol & Nando,2025-09-16 to 2025-09-26,120,250,100,659,3458
City of Urdaneta,Pinmaludpod,Mirasol & Nando,2025-09-16 to 2025-09-26,697,1991,340,2133,8324
City of Urdaneta,Poblacion,Mirasol & Nando,2025-09-16 to 2025-09-26,143,231,119,1923,7301
City of Urdaneta,San Jose,Mirasol & Nando,2025-09-16 to 2025-09-26,681,2010,520,1527,5730
City of Urdaneta,San Vicente,Mirasol & Nando,2025-09-16 to 2025-09-26,528,1972,126,2578,9532
City of Urdaneta,Santa Lucia,Mirasol & Nando,2025-09-16 to 2025-09-26,402,1011,282,924,3401
City of Urdaneta,Santo Domingo,Mirasol & Nando,2025-09-16 to 2025-09-26,253,533,200,937,3423
City of Urdaneta,Sugcong,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,316,1160
City of Urdaneta,Tiposu,Mirasol & Nando,2025-09-16 to 2025-09-26,89,155,80,548,2262
City of Urdaneta,Tulong,Mirasol & Nando,2025-09-16 to 2025-09-26,352,856,250,393,1567
""",
    "dante_emong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Dante & Emong,2025-07-22 to 2025-08-01,112,448,112,1513,6285
City of Urdaneta,Bactad East,Dante & Emong,2025-07-22 to 2025-08-01,45,138,45,601,2231
City of Urdaneta,Bayaoas,Dante & Emong,2025-07-22 to 2025-08-01,130,520,130,1607,5864
City of Urdaneta,Bolaoen,Dante & Emong,2025-07-22 to 2025-08-01,50,128,50,425,1604
City of Urdaneta,Cabaruan,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,613,2389
City of Urdaneta,Cabuloan,Dante & Emong,2025-07-22 to 2025-08-01,112,336,112,899,3564
City of Urdaneta,Camanang,Dante & Emong,2025-07-22 to 2025-08-01,45,109,45,1312,5397
City of Urdaneta,Camantiles,Dante & Emong,2025-07-22 to 2025-08-01,65,163,65,1702,6564
City of Urdaneta,Casantaan,Dante & Emong,2025-07-22 to 2025-08-01,60,185,60,448,1479
City of Urdaneta,Catablan,Dante & Emong,2025-07-22 to 2025-08-01,161,623,161,1666,6107
City of Urdaneta,Cayambanan,Dante & Emong,2025-07-22 to 2025-08-01,106,318,106,1245,4408
City of Urdaneta,Consolacion,Dante & Emong,2025-07-22 to 2025-08-01,45,152,45,472,1830
City of Urdaneta,Dilan-Paurido,Dante & Emong,2025-07-22 to 2025-08-01,236,704,236,1949,7186
City of Urdaneta,Labit Proper,Dante & Emong,2025-07-22 to 2025-08-01,81,289,81,951,3939
City of Urdaneta,Labit West,Dante & Emong,2025-07-22 to 2025-08-01,93,287,93,713,2751
City of Urdaneta,Mabanogbog,Dante & Emong,2025-07-22 to 2025-08-01,162,555,162,958,3564
City of Urdaneta,Macalong,Dante & Emong,2025-07-22 to 2025-08-01,57,221,57,486,1756
City of Urdaneta,Nancalobasaan,Dante & Emong,2025-07-22 to 2025-08-01,51,166,51,845,3364
City of Urdaneta,Nancamaliran East,Dante & Emong,2025-07-22 to 2025-08-01,40,122,40,1476,5284
City of Urdaneta,Nancamaliran West,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,1567,5981
City of Urdaneta,Nancayasan,Dante & Emong,2025-07-22 to 2025-08-01,99,297,99,2355,8175
City of Urdaneta,Oltama,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,392,1422
City of Urdaneta,Palina East,Dante & Emong,2025-07-22 to 2025-08-01,70,188,70,1400,5190
City of Urdaneta,Palina West,Dante & Emong,2025-07-22 to 2025-08-01,99,303,99,932,3443
City of Urdaneta,Pedro T. Orata,Dante & Emong,2025-07-22 to 2025-08-01,61,183,61,659,3458
City of Urdaneta,Pinmaludpod,Dante & Emong,2025-07-22 to 2025-08-01,120,365,120,2133,8324
City of Urdaneta,Poblacion,Dante & Emong,2025-07-22 to 2025-08-01,57,79,57,1923,7301
City of Urdaneta,San Jose,Dante & Emong,2025-07-22 to 2025-08-01,199,598,199,1527,5730
City of Urdaneta,San Vicente,Dante & Emong,2025-07-22 to 2025-08-01,76,279,76,2578,9532
City of Urdaneta,Santa Lucia,Dante & Emong,2025-07-22 to 2025-08-01,84,306,84,924,3401
City of Urdaneta,Santo Domingo,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,937,3423
City of Urdaneta,Sugcong,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,316,1160
City of Urdaneta,Tiposu,Dante & Emong,2025-07-22 to 2025-08-01,40,160,40,548,2262
City of Urdaneta,Tulong,Dante & Emong,2025-07-22 to 2025-08-01,148,441,148,393,1567
""",
    "nika_ofel_pepito_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Nika + Ofel + Pepito,2024-11-16,6,23,5,1726,6285
City of Urdaneta,Bactad East,Nika + Ofel + Pepito,2024-11-16,2,8,2,705,2231
City of Urdaneta,Bayaoas,Nika + Ofel + Pepito,2024-11-16,6,23,5,1810,5864
City of Urdaneta,Bolaoen,Nika + Ofel + Pepito,2024-11-16,1,4,1,450,1604
City of Urdaneta,Cabaruan,Nika + Ofel + Pepito,2024-11-16,1,3,1,696,2389
City of Urdaneta,Cabuloan,Nika + Ofel + Pepito,2024-11-16,2,9,2,1140,3564
City of Urdaneta,Camanang,Nika + Ofel + Pepito,2024-11-16,3,10,2,1460,5397
City of Urdaneta,Camantiles,Nika + Ofel + Pepito,2024-11-16,3,11,3,1858,6564
City of Urdaneta,Casantaan,Nika + Ofel + Pepito,2024-11-16,2,7,1,428,1479
City of Urdaneta,Catablan,Nika + Ofel + Pepito,2024-11-16,7,25,5,1805,6107
City of Urdaneta,Cayambanan,Nika + Ofel + Pepito,2024-11-16,3,9,3,1407,4408
City of Urdaneta,Consolacion,Nika + Ofel + Pepito,2024-11-16,2,6,1,433,1830
City of Urdaneta,Dilan-Paurido,Nika + Ofel + Pepito,2024-11-16,6,20,4,2079,7186
City of Urdaneta,Labit Proper,Nika + Ofel + Pepito,2024-11-16,2,7,2,1014,3939
City of Urdaneta,Labit West,Nika + Ofel + Pepito,2024-11-16,3,10,2,789,2751
City of Urdaneta,Mabanogbog,Nika + Ofel + Pepito,2024-11-16,3,12,2,1079,3564
City of Urdaneta,Macalong,Nika + Ofel + Pepito,2024-11-16,2,6,2,484,1756
City of Urdaneta,Nancalobasaan,Nika + Ofel + Pepito,2024-11-16,3,12,3,1008,3364
City of Urdaneta,Nancamaliran East,Nika + Ofel + Pepito,2024-11-16,2,7,1,1300,5284
City of Urdaneta,Nancamaliran West,Nika + Ofel + Pepito,2024-11-16,1,5,1,1707,5981
City of Urdaneta,Nancayasan,Nika + Ofel + Pepito,2024-11-16,4,13,3,2420,8175
City of Urdaneta,Oltama,Nika + Ofel + Pepito,2024-11-16,1,2,1,392,1422
City of Urdaneta,Palina East,Nika + Ofel + Pepito,2024-11-16,2,9,2,1273,5190
City of Urdaneta,Palina West,Nika + Ofel + Pepito,2024-11-16,4,13,4,985,3443
City of Urdaneta,Pedro T. Orata,Nika + Ofel + Pepito,2024-11-16,1,5,1,1327,3458
City of Urdaneta,Pinmaludpod,Nika + Ofel + Pepito,2024-11-16,5,18,3,2320,8324
City of Urdaneta,Poblacion,Nika + Ofel + Pepito,2024-11-16,3,10,3,2194,7301
City of Urdaneta,San Jose,Nika + Ofel + Pepito,2024-11-16,7,24,6,1832,5730
City of Urdaneta,San Vicente,Nika + Ofel + Pepito,2024-11-16,5,20,4,2974,9532
City of Urdaneta,Santa Lucia,Nika + Ofel + Pepito,2024-11-16,3,10,3,875,3401
City of Urdaneta,Santo Domingo,Nika + Ofel + Pepito,2024-11-16,1,5,1,931,3423
City of Urdaneta,Sugcong,Nika + Ofel + Pepito,2024-11-16,0,1,0,322,1160
City of Urdaneta,Tiposu,Nika + Ofel + Pepito,2024-11-16,1,5,1,616,2262
City of Urdaneta,Tulong,Nika + Ofel + Pepito,2024-11-16,3,12,2,444,1567
""",
    "kristine_leon_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Kristine + Leon,2024-10-24,0,1,0,1726,6285
City of Urdaneta,Bactad East,Kristine + Leon,2024-10-24,0,0,0,705,2231
City of Urdaneta,Bayaoas,Kristine + Leon,2024-10-24,0,1,0,1810,5864
City of Urdaneta,Bolaoen,Kristine + Leon,2024-10-24,0,0,0,450,1604
City of Urdaneta,Cabaruan,Kristine + Leon,2024-10-24,0,0,0,696,2389
City of Urdaneta,Cabuloan,Kristine + Leon,2024-10-24,0,0,0,1140,3564
City of Urdaneta,Camanang,Kristine + Leon,2024-10-24,0,0,0,1460,5397
City of Urdaneta,Camantiles,Kristine + Leon,2024-10-24,0,0,0,1858,6564
City of Urdaneta,Casantaan,Kristine + Leon,2024-10-24,0,0,0,428,1479
City of Urdaneta,Catablan,Kristine + Leon,2024-10-24,1,1,1,1805,6107
City of Urdaneta,Cayambanan,Kristine + Leon,2024-10-24,0,0,0,1407,4408
City of Urdaneta,Consolacion,Kristine + Leon,2024-10-24,0,0,0,433,1830
City of Urdaneta,Dilan-Paurido,Kristine + Leon,2024-10-24,0,1,0,2079,7186
City of Urdaneta,Labit Proper,Kristine + Leon,2024-10-24,0,0,0,1014,3939
City of Urdaneta,Labit West,Kristine + Leon,2024-10-24,0,0,0,789,2751
City of Urdaneta,Mabanogbog,Kristine + Leon,2024-10-24,0,0,0,1079,3564
City of Urdaneta,Macalong,Kristine + Leon,2024-10-24,0,0,0,484,1756
City of Urdaneta,Nancalobasaan,Kristine + Leon,2024-10-24,0,0,0,1008,3364
City of Urdaneta,Nancamaliran East,Kristine + Leon,2024-10-24,0,0,0,1300,5284
City of Urdaneta,Nancamaliran West,Kristine + Leon,2024-10-24,0,0,0,1707,5981
City of Urdaneta,Nancayasan,Kristine + Leon,2024-10-24,0,0,0,2420,8175
City of Urdaneta,Oltama,Kristine + Leon,2024-10-24,0,0,0,392,1422
City of Urdaneta,Palina East,Kristine + Leon,2024-10-24,0,0,0,1273,5190
City of Urdaneta,Palina West,Kristine + Leon,2024-10-24,0,0,0,985,3443
City of Urdaneta,Pedro T. Orata,Kristine + Leon,2024-10-24,0,0,0,1327,3458
City of Urdaneta,Pinmaludpod,Kristine + Leon,2024-10-24,0,0,0,2320,8324
City of Urdaneta,Poblacion,Kristine + Leon,2024-10-24,0,0,0,2194,7301
City of Urdaneta,San Jose,Kristine + Leon,2024-10-24,1,1,1,1832,5730
City of Urdaneta,San Vicente,Kristine + Leon,2024-10-24,0,1,0,2974,9532
City of Urdaneta,Santa Lucia,Kristine + Leon,2024-10-24,0,0,0,875,3401
City of Urdaneta,Santo Domingo,Kristine + Leon,2024-10-24,0,0,0,931,3423
City of Urdaneta,Sugcong,Kristine + Leon,2024-10-24,0,0,0,322,1160
City of Urdaneta,Tiposu,Kristine + Leon,2024-10-24,0,0,0,616,2262
City of Urdaneta,Tulong,Kristine + Leon,2024-10-24,0,0,0,444,1567
""",
    "enteng_habagat_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Enteng + Habagat,2024-09-05 to 2024-09-06,4,13,4,1726,6285
City of Urdaneta,Bactad East,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,705,2231
City of Urdaneta,Bayaoas,Enteng + Habagat,2024-09-05 to 2024-09-06,5,18,4,1810,5864
City of Urdaneta,Bolaoen,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,450,1604
City of Urdaneta,Cabaruan,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,696,2389
City of Urdaneta,Cabuloan,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1140,3564
City of Urdaneta,Camanang,Enteng + Habagat,2024-09-05 to 2024-09-06,2,6,1,1460,5397
City of Urdaneta,Camantiles,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1858,6564
City of Urdaneta,Casantaan,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,428,1479
City of Urdaneta,Catablan,Enteng + Habagat,2024-09-05 to 2024-09-06,5,16,4,1805,6107
City of Urdaneta,Cayambanan,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1407,4408
City of Urdaneta,Consolacion,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,433,1830
City of Urdaneta,Dilan-Paurido,Enteng + Habagat,2024-09-05 to 2024-09-06,4,14,4,2079,7186
City of Urdaneta,Labit Proper,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1014,3939
City of Urdaneta,Labit West,Enteng + Habagat,2024-09-05 to 2024-09-06,2,6,2,789,2751
City of Urdaneta,Mabanogbog,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,1,1079,3564
City of Urdaneta,Macalong,Enteng + Habagat,2024-09-05 to 2024-09-06,1,4,1,484,1756
City of Urdaneta,Nancalobasaan,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,1,1008,3364
City of Urdaneta,Nancamaliran East,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1300,5284
City of Urdaneta,Nancamaliran West,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,1707,5981
City of Urdaneta,Nancayasan,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,2420,8175
City of Urdaneta,Oltama,Enteng + Habagat,2024-09-05 to 2024-09-06,0,0,0,392,1422
City of Urdaneta,Palina East,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,1,1273,5190
City of Urdaneta,Palina West,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,985,3443
City of Urdaneta,Pedro T. Orata,Enteng + Habagat,2024-09-05 to 2024-09-06,1,4,1,1327,3458
City of Urdaneta,Pinmaludpod,Enteng + Habagat,2024-09-05 to 2024-09-06,3,10,3,2320,8324
City of Urdaneta,Poblacion,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,2194,7301
City of Urdaneta,San Jose,Enteng + Habagat,2024-09-05 to 2024-09-06,5,15,3,1832,5730
City of Urdaneta,San Vicente,Enteng + Habagat,2024-09-05 to 2024-09-06,3,8,3,2974,9532
City of Urdaneta,Santa Lucia,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,875,3401
City of Urdaneta,Santo Domingo,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,931,3423
City of Urdaneta,Sugcong,Enteng + Habagat,2024-09-05 to 2024-09-06,0,0,0,322,1160
City of Urdaneta,Tiposu,Enteng + Habagat,2024-09-05 to 2024-09-06,1,3,1,616,2262
City of Urdaneta,Tulong,Enteng + Habagat,2024-09-05 to 2024-09-06,2,6,1,444,1567
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Egay,2023-07-26,46,219,29,1460,6221
City of Urdaneta,Bactad East,Egay,2023-07-26,15,73,14,580,2175
City of Urdaneta,Bayaoas,Egay,2023-07-26,47,224,43,1551,5789
City of Urdaneta,Bolaoen,Egay,2023-07-26,9,40,6,410,1506
City of Urdaneta,Cabaruan,Egay,2023-07-26,7,32,6,591,2353
City of Urdaneta,Cabuloan,Egay,2023-07-26,18,83,15,868,3506
City of Urdaneta,Camanang,Egay,2023-07-26,21,101,15,1266,5109
City of Urdaneta,Camantiles,Egay,2023-07-26,23,110,22,1643,6605
City of Urdaneta,Casantaan,Egay,2023-07-26,14,64,11,432,1549
City of Urdaneta,Catablan,Egay,2023-07-26,52,245,36,1608,6082
City of Urdaneta,Cayambanan,Egay,2023-07-26,19,89,15,1202,4440
City of Urdaneta,Consolacion,Egay,2023-07-26,13,60,12,455,1750
City of Urdaneta,Dilan-Paurido,Egay,2023-07-26,41,193,28,1881,7391
City of Urdaneta,Labit Proper,Egay,2023-07-26,14,67,10,918,3855
City of Urdaneta,Labit West,Egay,2023-07-26,21,99,21,688,2708
City of Urdaneta,Mabanogbog,Egay,2023-07-26,24,113,21,925,3470
City of Urdaneta,Macalong,Egay,2023-07-26,12,56,9,469,1553
City of Urdaneta,Nancalobasaan,Egay,2023-07-26,24,112,19,816,3315
City of Urdaneta,Nancamaliran East,Egay,2023-07-26,14,67,9,1424,5542
City of Urdaneta,Nancamaliran West,Egay,2023-07-26,9,44,6,1513,5748
City of Urdaneta,Nancayasan,Egay,2023-07-26,25,120,18,2273,8742
City of Urdaneta,Oltama,Egay,2023-07-26,4,20,3,379,1487
City of Urdaneta,Palina East,Egay,2023-07-26,17,83,12,1352,5144
City of Urdaneta,Palina West,Egay,2023-07-26,26,123,18,899,3386
City of Urdaneta,Pedro T. Orata,Egay,2023-07-26,11,50,7,636,2393
City of Urdaneta,Pinmaludpod,Egay,2023-07-26,37,177,32,2059,8166
City of Urdaneta,Poblacion,Egay,2023-07-26,20,95,14,1857,7285
City of Urdaneta,San Jose,Egay,2023-07-26,48,227,46,1474,5850
City of Urdaneta,San Vicente,Egay,2023-07-26,40,189,38,2488,9778
City of Urdaneta,Santa Lucia,Egay,2023-07-26,20,95,13,892,3273
City of Urdaneta,Santo Domingo,Egay,2023-07-26,10,49,7,905,3610
City of Urdaneta,Sugcong,Egay,2023-07-26,2,8,2,305,1168
City of Urdaneta,Tiposu,Egay,2023-07-26,10,47,7,562,2190
City of Urdaneta,Tulong,Egay,2023-07-26,25,116,16,380,1438
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Paeng,2022-10-29,0,0,0,1435,6221
City of Urdaneta,Bactad East,Paeng,2022-10-29,0,0,0,570,2175
City of Urdaneta,Bayaoas,Paeng,2022-10-29,0,0,0,1524,5789
City of Urdaneta,Bolaoen,Paeng,2022-10-29,0,0,0,403,1506
City of Urdaneta,Cabaruan,Paeng,2022-10-29,0,0,0,581,2353
City of Urdaneta,Cabuloan,Paeng,2022-10-29,0,0,0,853,3506
City of Urdaneta,Camanang,Paeng,2022-10-29,0,0,0,1244,5109
City of Urdaneta,Camantiles,Paeng,2022-10-29,0,0,0,1614,6605
City of Urdaneta,Casantaan,Paeng,2022-10-29,0,0,0,425,1549
City of Urdaneta,Catablan,Paeng,2022-10-29,1,1,1,1580,6082
City of Urdaneta,Cayambanan,Paeng,2022-10-29,0,0,0,1181,4440
City of Urdaneta,Consolacion,Paeng,2022-10-29,0,0,0,448,1750
City of Urdaneta,Dilan-Paurido,Paeng,2022-10-29,0,0,0,1848,7391
City of Urdaneta,Labit Proper,Paeng,2022-10-29,0,0,0,902,3855
City of Urdaneta,Labit West,Paeng,2022-10-29,0,0,0,676,2708
City of Urdaneta,Mabanogbog,Paeng,2022-10-29,0,0,0,908,3470
City of Urdaneta,Macalong,Paeng,2022-10-29,0,0,0,461,1553
City of Urdaneta,Nancalobasaan,Paeng,2022-10-29,0,0,0,802,3315
City of Urdaneta,Nancamaliran East,Paeng,2022-10-29,0,0,0,1400,5542
City of Urdaneta,Nancamaliran West,Paeng,2022-10-29,0,0,0,1487,5748
City of Urdaneta,Nancayasan,Paeng,2022-10-29,0,0,0,2233,8742
City of Urdaneta,Oltama,Paeng,2022-10-29,0,0,0,372,1487
City of Urdaneta,Palina East,Paeng,2022-10-29,0,0,0,1328,5144
City of Urdaneta,Palina West,Paeng,2022-10-29,0,0,0,884,3386
City of Urdaneta,Pedro T. Orata,Paeng,2022-10-29,0,0,0,625,2393
City of Urdaneta,Pinmaludpod,Paeng,2022-10-29,0,0,0,2023,8166
City of Urdaneta,Poblacion,Paeng,2022-10-29,0,0,0,1824,7285
City of Urdaneta,San Jose,Paeng,2022-10-29,0,1,0,1448,5850
City of Urdaneta,San Vicente,Paeng,2022-10-29,0,0,0,2445,9778
City of Urdaneta,Santa Lucia,Paeng,2022-10-29,0,0,0,876,3273
City of Urdaneta,Santo Domingo,Paeng,2022-10-29,0,0,0,889,3610
City of Urdaneta,Sugcong,Paeng,2022-10-29,0,0,0,299,1168
City of Urdaneta,Tiposu,Paeng,2022-10-29,0,0,0,533,2190
City of Urdaneta,Tulong,Paeng,2022-10-29,0,0,0,373,1438
""",
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Karding,2022-09-25,0,1,0,1435,6221
City of Urdaneta,Bactad East,Karding,2022-09-25,0,0,0,570,2175
City of Urdaneta,Bayaoas,Karding,2022-09-25,0,1,0,1524,5789
City of Urdaneta,Bolaoen,Karding,2022-09-25,0,0,0,403,1506
City of Urdaneta,Cabaruan,Karding,2022-09-25,0,0,0,581,2353
City of Urdaneta,Cabuloan,Karding,2022-09-25,0,0,0,853,3506
City of Urdaneta,Camanang,Karding,2022-09-25,0,0,0,1244,5109
City of Urdaneta,Camantiles,Karding,2022-09-25,0,0,0,1614,6605
City of Urdaneta,Casantaan,Karding,2022-09-25,0,0,0,425,1549
City of Urdaneta,Catablan,Karding,2022-09-25,1,1,1,1580,6082
City of Urdaneta,Cayambanan,Karding,2022-09-25,0,0,0,1181,4440
City of Urdaneta,Consolacion,Karding,2022-09-25,0,0,0,448,1750
City of Urdaneta,Dilan-Paurido,Karding,2022-09-25,0,1,0,1848,7391
City of Urdaneta,Labit Proper,Karding,2022-09-25,0,0,0,902,3855
City of Urdaneta,Labit West,Karding,2022-09-25,0,0,0,676,2708
City of Urdaneta,Mabanogbog,Karding,2022-09-25,0,0,0,908,3470
City of Urdaneta,Macalong,Karding,2022-09-25,0,0,0,461,1553
City of Urdaneta,Nancalobasaan,Karding,2022-09-25,0,0,0,802,3315
City of Urdaneta,Nancamaliran East,Karding,2022-09-25,0,0,0,1400,5542
City of Urdaneta,Nancamaliran West,Karding,2022-09-25,0,0,0,1487,5748
City of Urdaneta,Nancayasan,Karding,2022-09-25,0,0,0,2233,8742
City of Urdaneta,Oltama,Karding,2022-09-25,0,0,0,372,1487
City of Urdaneta,Palina East,Karding,2022-09-25,0,0,0,1328,5144
City of Urdaneta,Palina West,Karding,2022-09-25,0,0,0,884,3386
City of Urdaneta,Pedro T. Orata,Karding,2022-09-25,0,0,0,625,2393
City of Urdaneta,Pinmaludpod,Karding,2022-09-25,0,1,0,2023,8166
City of Urdaneta,Poblacion,Karding,2022-09-25,0,0,0,1824,7285
City of Urdaneta,San Jose,Karding,2022-09-25,1,1,1,1448,5850
City of Urdaneta,San Vicente,Karding,2022-09-25,0,1,0,2445,9778
City of Urdaneta,Santa Lucia,Karding,2022-09-25,0,0,0,876,3273
City of Urdaneta,Santo Domingo,Karding,2022-09-25,0,0,0,889,3610
City of Urdaneta,Sugcong,Karding,2022-09-25,0,0,0,299,1168
City of Urdaneta,Tiposu,Karding,2022-09-25,0,0,0,533,2190
City of Urdaneta,Tulong,Karding,2022-09-25,0,0,0,373,1438
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Maring,2021-10-11,0,0,0,1410,6221
City of Urdaneta,Bactad East,Maring,2021-10-11,0,0,0,560,2175
City of Urdaneta,Bayaoas,Maring,2021-10-11,0,0,0,1497,5789
City of Urdaneta,Bolaoen,Maring,2021-10-11,0,0,0,396,1506
City of Urdaneta,Cabaruan,Maring,2021-10-11,0,0,0,571,2353
City of Urdaneta,Cabuloan,Maring,2021-10-11,0,0,0,838,3506
City of Urdaneta,Camanang,Maring,2021-10-11,0,0,0,1222,5109
City of Urdaneta,Camantiles,Maring,2021-10-11,0,0,0,1586,6605
City of Urdaneta,Casantaan,Maring,2021-10-11,0,0,0,417,1549
City of Urdaneta,Catablan,Maring,2021-10-11,1,3,1,1552,6082
City of Urdaneta,Cayambanan,Maring,2021-10-11,0,0,0,1160,4440
City of Urdaneta,Consolacion,Maring,2021-10-11,0,0,0,440,1750
City of Urdaneta,Dilan-Paurido,Maring,2021-10-11,0,0,0,1816,7391
City of Urdaneta,Labit Proper,Maring,2021-10-11,0,0,0,887,3855
City of Urdaneta,Labit West,Maring,2021-10-11,0,0,0,665,2708
City of Urdaneta,Mabanogbog,Maring,2021-10-11,0,0,0,893,3470
City of Urdaneta,Macalong,Maring,2021-10-11,0,0,0,453,1553
City of Urdaneta,Nancalobasaan,Maring,2021-10-11,0,0,0,788,3315
City of Urdaneta,Nancamaliran East,Maring,2021-10-11,0,0,0,1375,5542
City of Urdaneta,Nancamaliran West,Maring,2021-10-11,0,0,0,1461,5748
City of Urdaneta,Nancayasan,Maring,2021-10-11,0,0,0,2194,8742
City of Urdaneta,Oltama,Maring,2021-10-11,0,0,0,365,1487
City of Urdaneta,Palina East,Maring,2021-10-11,0,0,0,1305,5144
City of Urdaneta,Palina West,Maring,2021-10-11,0,0,0,868,3386
City of Urdaneta,Pedro T. Orata,Maring,2021-10-11,0,0,0,614,2393
City of Urdaneta,Pinmaludpod,Maring,2021-10-11,0,0,0,1988,8166
City of Urdaneta,Poblacion,Maring,2021-10-11,0,0,0,1792,7285
City of Urdaneta,San Jose,Maring,2021-10-11,1,3,1,1423,5850
City of Urdaneta,San Vicente,Maring,2021-10-11,0,0,0,2402,9778
City of Urdaneta,Santa Lucia,Maring,2021-10-11,0,0,0,861,3273
City of Urdaneta,Santo Domingo,Maring,2021-10-11,0,0,0,873,3610
City of Urdaneta,Sugcong,Maring,2021-10-11,0,0,0,294,1168
City of Urdaneta,Tiposu,Maring,2021-10-11,0,0,0,533,2190
City of Urdaneta,Tulong,Maring,2021-10-11,0,0,0,366,1438
""",
    "fabian_habagat_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Fabian + Habagat,2021-07-23 to 2021-07-24,3,8,3,1410,6221
City of Urdaneta,Bactad East,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,560,2175
City of Urdaneta,Bayaoas,Fabian + Habagat,2021-07-23 to 2021-07-24,2,6,1,1497,5789
City of Urdaneta,Bolaoen,Fabian + Habagat,2021-07-23 to 2021-07-24,0,0,0,396,1506
City of Urdaneta,Cabaruan,Fabian + Habagat,2021-07-23 to 2021-07-24,0,0,0,571,2353
City of Urdaneta,Cabuloan,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,838,3506
City of Urdaneta,Camanang,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1222,5109
City of Urdaneta,Camantiles,Fabian + Habagat,2021-07-23 to 2021-07-24,2,7,1,1586,6605
City of Urdaneta,Casantaan,Fabian + Habagat,2021-07-23 to 2021-07-24,1,4,1,417,1549
City of Urdaneta,Catablan,Fabian + Habagat,2021-07-23 to 2021-07-24,3,10,2,1552,6082
City of Urdaneta,Cayambanan,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1160,4440
City of Urdaneta,Consolacion,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,440,1750
City of Urdaneta,Dilan-Paurido,Fabian + Habagat,2021-07-23 to 2021-07-24,2,6,1,1816,7391
City of Urdaneta,Labit Proper,Fabian + Habagat,2021-07-23 to 2021-07-24,1,4,1,887,3855
City of Urdaneta,Labit West,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,665,2708
City of Urdaneta,Mabanogbog,Fabian + Habagat,2021-07-23 to 2021-07-24,2,7,2,893,3470
City of Urdaneta,Macalong,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,453,1553
City of Urdaneta,Nancalobasaan,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,788,3315
City of Urdaneta,Nancamaliran East,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1375,5542
City of Urdaneta,Nancamaliran West,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1461,5748
City of Urdaneta,Nancayasan,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,2194,8742
City of Urdaneta,Oltama,Fabian + Habagat,2021-07-23 to 2021-07-24,0,0,0,365,1487
City of Urdaneta,Palina East,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1305,5144
City of Urdaneta,Palina West,Fabian + Habagat,2021-07-23 to 2021-07-24,2,6,1,868,3386
City of Urdaneta,Pedro T. Orata,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,614,2393
City of Urdaneta,Pinmaludpod,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1988,8166
City of Urdaneta,Poblacion,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,1792,7285
City of Urdaneta,San Jose,Fabian + Habagat,2021-07-23 to 2021-07-24,3,11,2,1423,5850
City of Urdaneta,San Vicente,Fabian + Habagat,2021-07-23 to 2021-07-24,2,6,2,2402,9778
City of Urdaneta,Santa Lucia,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,861,3273
City of Urdaneta,Santo Domingo,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,873,3610
City of Urdaneta,Sugcong,Fabian + Habagat,2021-07-23 to 2021-07-24,0,0,0,294,1168
City of Urdaneta,Tiposu,Fabian + Habagat,2021-07-23 to 2021-07-24,1,3,1,533,2190
City of Urdaneta,Tulong,Fabian + Habagat,2021-07-23 to 2021-07-24,2,7,2,366,1438
""",
}

# typhoon_key(s) matching scripts/typhoon_calendar_2021_2026.py
_TYPHOON_KEYS = {
    "maymay_2026": ["maymay_2026"],
    "uwan_2025": ["uwan_2025"],
    "ramil_2025": ["ramil_2025"],
    "paolo_2025": ["paolo_2025"],
    "mirasol_nando_2025": ["mirasol_2025", "nando_2025"],
    "dante_emong_2025": ["dante_2025", "emong_2025"],
    "nika_ofel_pepito_2024": ["nika_2024", "ofel_2024", "pepito_2024"],
    "kristine_leon_2024": ["kristine_2024", "leon_2024"],
    "enteng_habagat_2024": ["enteng_2024"],
    "egay_2023": ["egay_2023"],
    "paeng_2022": ["paeng_2022"],
    "karding_2022": ["karding_2022"],
    "maring_2021": ["maring_2021"],
    "fabian_habagat_2021": ["fabian_2021"],
}


def parse(report_key):
    reader = csv.DictReader(io.StringIO(_FILES[report_key]))
    return [{
        "barangay": r["Barangay"],
        "date": r["Date ng Typhoon"],
        "affected_families": int(r["Affected Families"]),
        "affected_individuals": int(r["Affected Individuals"]),
        "food_packs_given": int(r["Food Packs Given"]),
        "total_families": int(r["Total Number of Families"]),
        "total_individuals": int(r["Total Number of Individuals"]),
    } for r in reader]


REPORTS = [
    {"key": key, "typhoon_keys": _TYPHOON_KEYS[key], "rows": parse(key)}
    for key in _FILES
]


if __name__ == "__main__":
    ok = True
    for rep in REPORTS:
        rows = rep["rows"]
        fam = sum(r["affected_families"] for r in rows)
        packs = sum(r["food_packs_given"] for r in rows)
        good = len(rows) == 34 and len({normalize(r["barangay"]) for r in rows}) == 34
        ok &= good
        print(f"{rep['key']:<24} 34 brgy={good!s:<6} families={fam:>6,} packs={packs:>6,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Urdaneta reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
