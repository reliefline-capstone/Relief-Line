"""
REAL records given to the team: Urdaneta City CSWDO per-barangay disaster
reports for 14 typhoon reports, 2021-2026, all 34 barangays per file, in the
same 14-report structure as Calasiao's and Sta. Barbara's sets.

Current version = the Urdaneta set delivered 2026-10-03 (second delivery that
day). It REPLACES this module's earlier 2026-10-03 version:
  * Maymay (2026, 3 packs) -> combined "Luis & Maymay & Neneng & Pilandok"
    report (1,768 packs);
  * Ramil (2025) is not in the new set - dropped (as Calasiao/Sta. Barbara
    have no Ramil report either);
  * NEW: Carina + Habagat (Jul 2024);
  * older reports re-delivered with revised figures (Maring 2021 2 -> 2,611
    packs, Fabian 2021 37 -> 623, Egay 2023 580 -> 682, Enteng 2024 53 ->
    162, Nika/Ofel/Pepito 82 -> 74; the 2025 reports are unchanged) and new
    "Total Number of Families" snapshots (2021-2023 = one snapshot, e.g.
    Anonas 1,385; 2024-2026 = another, Anonas 1,726).
Before that, real_urdaneta_typhoons_2021_2025.py and
real_urdaneta_reports_2025.py were replaced - see git history.

Each report links to every storm its "Name of Typhoon" column names (see
_storms.py; the typhoon calendar is built from these reports - see
scripts/typhoon_calendar_from_reports.py). Combined reports:
  Luis & Maymay & Neneng & Pilandok (2026) -> luis_2026, maymay_2026,
                                     neneng_2026, pilandok_2026
  Mirasol & Nando        (Sep 2025) -> mirasol_2025, nando_2025
  Dante & Emong          (Jul 2025) -> dante_2025, emong_2025
  Nika + Ofel + Pepito   (Nov 2024) -> nika_2024, ofel_2024, pepito_2024
  Kristine + Leon        (Oct 2024) -> kristine_2024, leon_2024
  Fabian / Enteng / Carina + Habagat -> the named storm only ("Habagat" is the
                                     enhanced monsoon, not a calendar typhoon)
One relief_events row per report, one relief_event_typhoons row per named
calendar typhoon it maps to (see scripts/apply_relief_schema.py) - frequency
and P(relief) are counted off the calendar/linkage independently, so a
combined report never needs (and the source data can't support) a per-storm
pack split.

Data-quality notes kept from the source (not corrected - figures are as given):
  * Luis & Maymay & Neneng & Pilandok is dated 2026-10-01 to 2026-10-15
    (file "OCT2026"), while the same storms are dated Aug 2026 in Calasiao's
    and Sta. Barbara's reports and in the typhoon calendar; the range also
    ends after the delivery date (2026-10-03). Kept as given - the date only
    orders snapshots/backtests.
  * Cabuloan (Mirasol & Nando): 5,010 individuals for 202 families looks like
    a typo; kept. Individuals are not used by the model.
  * Paolo: several barangays got more packs than affected families (e.g.
    Consolacion 500 packs / 303 families, Tiposu 500 / 298). The model uses
    packs, so these are kept as reported.
  * Uwan: Nancayasan reports 43 affected families but 0 packs.

Run this file to print a structural sanity check per report.
"""
import csv
import io

from _barangay_names import strip_accents_and_punct
from _storms import storm_keys


def normalize(name):
    """Folds Urdaneta's report spellings onto the barangays table:
    'Dilan-Paurido' -> 'dilan paurido', 'Pedro T. Orata' -> 'dr pedro t orata',
    'Tiposu' -> 'tipuso', 'Sta. Lucia' -> 'santa lucia'."""
    s = strip_accents_and_punct(name)
    return {
        "pedro t orata": "dr pedro t orata", "tiposu": "tipuso", "sta lucia": "santa lucia",
    }.get(s, s)


_HEADER = ("Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,"
           "Affected Individuals,Food Packs Given,Total Number of Families,"
           "Total Number of Individuals\n")

_FILES = {
    "luis_maymay_neneng_pilandok_2026": _HEADER + """City of Urdaneta,Anonas,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,142,439,142,1726,6285
City of Urdaneta,Bactad East,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,14,38,9,705,2231
City of Urdaneta,Bayaoas,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,47,130,27,1810,5864
City of Urdaneta,Bolaoen,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,14,42,8,450,1604
City of Urdaneta,Cabaruan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,21,61,16,696,2389
City of Urdaneta,Cabuloan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,30,81,19,1140,3564
City of Urdaneta,Camanang,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,46,152,34,1460,5397
City of Urdaneta,Camantiles,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,140,412,140,1858,6564
City of Urdaneta,Casantaan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,9,20,6,428,1479
City of Urdaneta,Catablan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,43,142,27,1805,6107
City of Urdaneta,Cayambanan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,30,89,19,1407,4408
City of Urdaneta,Consolacion,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,13,33,10,433,1830
City of Urdaneta,Dilan-Paurido,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,50,135,31,2079,7186
City of Urdaneta,Labit Proper,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,29,86,24,1014,3939
City of Urdaneta,Labit West,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,20,61,12,789,2751
City of Urdaneta,Mabanogbog,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,68,231,68,1079,3564
City of Urdaneta,Macalong,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,13,38,10,484,1756
City of Urdaneta,Nancalobasaan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,71,193,71,1008,3364
City of Urdaneta,Nancamaliran East,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,42,122,31,1300,5284
City of Urdaneta,Nancamaliran West,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,35,112,22,1707,5981
City of Urdaneta,Nancayasan,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,166,548,166,2420,8175
City of Urdaneta,Oltama,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,9,27,6,392,1422
City of Urdaneta,Palina East,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,39,131,26,1273,5190
City of Urdaneta,Palina West,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,29,83,21,985,3443
City of Urdaneta,Pedro T. Orata,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,29,91,21,1327,3458
City of Urdaneta,Pinmaludpod,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,199,677,199,2320,8324
City of Urdaneta,Poblacion,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,160,543,160,2194,7301
City of Urdaneta,San Jose,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,157,488,157,1832,5730
City of Urdaneta,San Vicente,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,191,660,191,2974,9532
City of Urdaneta,Santa Lucia,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,29,73,24,875,3401
City of Urdaneta,Santo Domingo,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,26,86,21,931,3423
City of Urdaneta,Sugcong,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,8,22,6,322,1160
City of Urdaneta,Tiposu,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,20,60,13,616,2262
City of Urdaneta,Tulong,Luis & Maymay & Neneng & Pilandok,2026-10-01 to 2026-10-15,31,86,31,444,1567
""",
    "uwan_2025": _HEADER + """City of Urdaneta,Anonas,Uwan,2025-11-03 to 2025-11-25,114,348,100,1726,6285
City of Urdaneta,Bactad East,Uwan,2025-11-03 to 2025-11-25,19,57,10,705,2231
City of Urdaneta,Bayaoas,Uwan,2025-11-03 to 2025-11-25,139,415,100,1810,5864
City of Urdaneta,Bolaoen,Uwan,2025-11-03 to 2025-11-25,0,0,0,450,1604
City of Urdaneta,Cabaruan,Uwan,2025-11-03 to 2025-11-25,51,150,40,696,2389
City of Urdaneta,Cabuloan,Uwan,2025-11-03 to 2025-11-25,21,64,20,1140,3564
City of Urdaneta,Camanang,Uwan,2025-11-03 to 2025-11-25,61,191,50,1460,5397
City of Urdaneta,Camantiles,Uwan,2025-11-03 to 2025-11-25,65,201,50,1858,6564
City of Urdaneta,Casantaan,Uwan,2025-11-03 to 2025-11-25,12,38,10,428,1479
City of Urdaneta,Catablan,Uwan,2025-11-03 to 2025-11-25,142,403,100,1805,6107
City of Urdaneta,Cayambanan,Uwan,2025-11-03 to 2025-11-25,38,116,25,1407,4408
City of Urdaneta,Consolacion,Uwan,2025-11-03 to 2025-11-25,23,71,20,433,1830
City of Urdaneta,Dilan-Paurido,Uwan,2025-11-03 to 2025-11-25,67,202,25,2079,7186
City of Urdaneta,Labit Proper,Uwan,2025-11-03 to 2025-11-25,16,53,10,1014,3939
City of Urdaneta,Labit West,Uwan,2025-11-03 to 2025-11-25,14,44,10,789,2751
City of Urdaneta,Mabanogbog,Uwan,2025-11-03 to 2025-11-25,20,58,20,1079,3564
City of Urdaneta,Macalong,Uwan,2025-11-03 to 2025-11-25,15,50,10,484,1756
City of Urdaneta,Nancalobasaan,Uwan,2025-11-03 to 2025-11-25,55,166,30,1008,3364
City of Urdaneta,Nancamaliran East,Uwan,2025-11-03 to 2025-11-25,41,123,20,1300,5284
City of Urdaneta,Nancamaliran West,Uwan,2025-11-03 to 2025-11-25,2,14,0,1707,5981
City of Urdaneta,Nancayasan,Uwan,2025-11-03 to 2025-11-25,43,131,0,2420,8175
City of Urdaneta,Oltama,Uwan,2025-11-03 to 2025-11-25,31,92,10,392,1422
City of Urdaneta,Palina East,Uwan,2025-11-03 to 2025-11-25,16,47,10,1273,5190
City of Urdaneta,Palina West,Uwan,2025-11-03 to 2025-11-25,33,104,30,985,3443
City of Urdaneta,Pedro T. Orata,Uwan,2025-11-03 to 2025-11-25,0,0,0,1327,3458
City of Urdaneta,Pinmaludpod,Uwan,2025-11-03 to 2025-11-25,61,184,50,2320,8324
City of Urdaneta,Poblacion,Uwan,2025-11-03 to 2025-11-25,22,67,10,2194,7301
City of Urdaneta,San Jose,Uwan,2025-11-03 to 2025-11-25,88,263,50,1832,5730
City of Urdaneta,San Vicente,Uwan,2025-11-03 to 2025-11-25,122,359,100,2974,9532
City of Urdaneta,Santa Lucia,Uwan,2025-11-03 to 2025-11-25,0,0,0,875,3401
City of Urdaneta,Santo Domingo,Uwan,2025-11-03 to 2025-11-25,0,0,0,931,3423
City of Urdaneta,Sugcong,Uwan,2025-11-03 to 2025-11-25,13,41,10,322,1160
City of Urdaneta,Tiposu,Uwan,2025-11-03 to 2025-11-25,11,35,10,616,2262
City of Urdaneta,Tulong,Uwan,2025-11-03 to 2025-11-25,25,75,20,444,1567
""",
    "paolo_2025": _HEADER + """City of Urdaneta,Anonas,Paolo,2025-10-01 to 2025-10-04,755,1113,500,1726,6285
City of Urdaneta,Bactad East,Paolo,2025-10-01 to 2025-10-04,693,1126,500,705,2231
City of Urdaneta,Bayaoas,Paolo,2025-10-01 to 2025-10-04,870,1222,570,1810,5864
City of Urdaneta,Bolaoen,Paolo,2025-10-01 to 2025-10-04,236,700,200,450,1604
City of Urdaneta,Cabaruan,Paolo,2025-10-01 to 2025-10-04,0,0,0,696,2389
City of Urdaneta,Cabuloan,Paolo,2025-10-01 to 2025-10-04,226,655,200,1140,3564
City of Urdaneta,Camanang,Paolo,2025-10-01 to 2025-10-04,356,1115,300,1460,5397
City of Urdaneta,Camantiles,Paolo,2025-10-01 to 2025-10-04,423,1106,300,1858,6564
City of Urdaneta,Casantaan,Paolo,2025-10-01 to 2025-10-04,348,1026,300,428,1479
City of Urdaneta,Catablan,Paolo,2025-10-01 to 2025-10-04,633,1989,500,1805,6107
City of Urdaneta,Cayambanan,Paolo,2025-10-01 to 2025-10-04,340,989,300,1407,4408
City of Urdaneta,Consolacion,Paolo,2025-10-01 to 2025-10-04,303,1003,500,433,1830
City of Urdaneta,Dilan-Paurido,Paolo,2025-10-01 to 2025-10-04,500,1402,500,2079,7186
City of Urdaneta,Labit Proper,Paolo,2025-10-01 to 2025-10-04,303,758,300,1014,3939
City of Urdaneta,Labit West,Paolo,2025-10-01 to 2025-10-04,415,1015,300,789,2751
City of Urdaneta,Mabanogbog,Paolo,2025-10-01 to 2025-10-04,398,1102,300,1079,3564
City of Urdaneta,Macalong,Paolo,2025-10-01 to 2025-10-04,202,565,200,484,1756
City of Urdaneta,Nancalobasaan,Paolo,2025-10-01 to 2025-10-04,554,1204,554,1008,3364
City of Urdaneta,Nancamaliran East,Paolo,2025-10-01 to 2025-10-04,305,789,300,1300,5284
City of Urdaneta,Nancamaliran West,Paolo,2025-10-01 to 2025-10-04,500,1316,500,1707,5981
City of Urdaneta,Nancayasan,Paolo,2025-10-01 to 2025-10-04,500,1326,500,2420,8175
City of Urdaneta,Oltama,Paolo,2025-10-01 to 2025-10-04,0,0,0,392,1422
City of Urdaneta,Palina East,Paolo,2025-10-01 to 2025-10-04,405,1056,300,1273,5190
City of Urdaneta,Palina West,Paolo,2025-10-01 to 2025-10-04,500,1153,500,985,3443
City of Urdaneta,Pedro T. Orata,Paolo,2025-10-01 to 2025-10-04,303,706,300,1327,3458
City of Urdaneta,Pinmaludpod,Paolo,2025-10-01 to 2025-10-04,500,1416,500,2320,8324
City of Urdaneta,Poblacion,Paolo,2025-10-01 to 2025-10-04,788,1986,500,2194,7301
City of Urdaneta,San Jose,Paolo,2025-10-01 to 2025-10-04,658,1289,500,1832,5730
City of Urdaneta,San Vicente,Paolo,2025-10-01 to 2025-10-04,567,1681,567,2974,9532
City of Urdaneta,Santa Lucia,Paolo,2025-10-01 to 2025-10-04,455,1056,500,875,3401
City of Urdaneta,Santo Domingo,Paolo,2025-10-01 to 2025-10-04,389,1022,500,931,3423
City of Urdaneta,Sugcong,Paolo,2025-10-01 to 2025-10-04,0,0,0,322,1160
City of Urdaneta,Tiposu,Paolo,2025-10-01 to 2025-10-04,298,1181,500,616,2262
City of Urdaneta,Tulong,Paolo,2025-10-01 to 2025-10-04,289,860,200,444,1567
""",
    "mirasol_nando_2025": _HEADER + """City of Urdaneta,Anonas,Mirasol & Nando,2025-09-16 to 2025-09-26,653,2080,300,1726,6285
City of Urdaneta,Bactad East,Mirasol & Nando,2025-09-16 to 2025-09-26,30,112,0,705,2231
City of Urdaneta,Bayaoas,Mirasol & Nando,2025-09-16 to 2025-09-26,408,955,298,1810,5864
City of Urdaneta,Bolaoen,Mirasol & Nando,2025-09-16 to 2025-09-26,100,301,80,450,1604
City of Urdaneta,Cabaruan,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,696,2389
City of Urdaneta,Cabuloan,Mirasol & Nando,2025-09-16 to 2025-09-26,202,5010,100,1140,3564
City of Urdaneta,Camanang,Mirasol & Nando,2025-09-16 to 2025-09-26,258,439,170,1460,5397
City of Urdaneta,Camantiles,Mirasol & Nando,2025-09-16 to 2025-09-26,218,454,160,1858,6564
City of Urdaneta,Casantaan,Mirasol & Nando,2025-09-16 to 2025-09-26,156,253,150,428,1479
City of Urdaneta,Catablan,Mirasol & Nando,2025-09-16 to 2025-09-26,651,1979,467,1805,6107
City of Urdaneta,Cayambanan,Mirasol & Nando,2025-09-16 to 2025-09-26,103,223,100,1407,4408
City of Urdaneta,Consolacion,Mirasol & Nando,2025-09-16 to 2025-09-26,123,253,100,433,1830
City of Urdaneta,Dilan-Paurido,Mirasol & Nando,2025-09-16 to 2025-09-26,448,1350,250,2079,7186
City of Urdaneta,Labit Proper,Mirasol & Nando,2025-09-16 to 2025-09-26,125,305,100,1014,3939
City of Urdaneta,Labit West,Mirasol & Nando,2025-09-16 to 2025-09-26,353,981,277,789,2751
City of Urdaneta,Mabanogbog,Mirasol & Nando,2025-09-16 to 2025-09-26,235,598,100,1079,3564
City of Urdaneta,Macalong,Mirasol & Nando,2025-09-16 to 2025-09-26,160,284,140,484,1756
City of Urdaneta,Nancalobasaan,Mirasol & Nando,2025-09-16 to 2025-09-26,270,618,202,1008,3364
City of Urdaneta,Nancamaliran East,Mirasol & Nando,2025-09-16 to 2025-09-26,99,200,80,1300,5284
City of Urdaneta,Nancamaliran West,Mirasol & Nando,2025-09-16 to 2025-09-26,120,266,100,1707,5981
City of Urdaneta,Nancayasan,Mirasol & Nando,2025-09-16 to 2025-09-26,310,742,220,2420,8175
City of Urdaneta,Oltama,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,392,1422
City of Urdaneta,Palina East,Mirasol & Nando,2025-09-16 to 2025-09-26,253,560,100,1273,5190
City of Urdaneta,Palina West,Mirasol & Nando,2025-09-16 to 2025-09-26,398,1002,220,985,3443
City of Urdaneta,Pedro T. Orata,Mirasol & Nando,2025-09-16 to 2025-09-26,120,250,100,1327,3458
City of Urdaneta,Pinmaludpod,Mirasol & Nando,2025-09-16 to 2025-09-26,697,1991,340,2320,8324
City of Urdaneta,Poblacion,Mirasol & Nando,2025-09-16 to 2025-09-26,143,231,119,2194,7301
City of Urdaneta,San Jose,Mirasol & Nando,2025-09-16 to 2025-09-26,681,2010,520,1832,5730
City of Urdaneta,San Vicente,Mirasol & Nando,2025-09-16 to 2025-09-26,528,1972,126,2974,9532
City of Urdaneta,Santa Lucia,Mirasol & Nando,2025-09-16 to 2025-09-26,402,1011,282,875,3401
City of Urdaneta,Santo Domingo,Mirasol & Nando,2025-09-16 to 2025-09-26,253,533,200,931,3423
City of Urdaneta,Sugcong,Mirasol & Nando,2025-09-16 to 2025-09-26,0,0,0,322,1160
City of Urdaneta,Tiposu,Mirasol & Nando,2025-09-16 to 2025-09-26,89,155,80,616,2262
City of Urdaneta,Tulong,Mirasol & Nando,2025-09-16 to 2025-09-26,352,856,250,444,1567
""",
    "dante_emong_2025": _HEADER + """City of Urdaneta,Anonas,Dante & Emong,2025-07-22 to 2025-08-01,112,448,112,1726,6285
City of Urdaneta,Bactad East,Dante & Emong,2025-07-22 to 2025-08-01,45,138,45,705,2231
City of Urdaneta,Bayaoas,Dante & Emong,2025-07-22 to 2025-08-01,130,520,130,1810,5864
City of Urdaneta,Bolaoen,Dante & Emong,2025-07-22 to 2025-08-01,50,128,50,450,1604
City of Urdaneta,Cabaruan,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,696,2389
City of Urdaneta,Cabuloan,Dante & Emong,2025-07-22 to 2025-08-01,112,336,112,1140,3564
City of Urdaneta,Camanang,Dante & Emong,2025-07-22 to 2025-08-01,45,109,45,1460,5397
City of Urdaneta,Camantiles,Dante & Emong,2025-07-22 to 2025-08-01,65,163,65,1858,6564
City of Urdaneta,Casantaan,Dante & Emong,2025-07-22 to 2025-08-01,60,185,60,428,1479
City of Urdaneta,Catablan,Dante & Emong,2025-07-22 to 2025-08-01,161,623,161,1805,6107
City of Urdaneta,Cayambanan,Dante & Emong,2025-07-22 to 2025-08-01,106,318,106,1407,4408
City of Urdaneta,Consolacion,Dante & Emong,2025-07-22 to 2025-08-01,45,152,45,433,1830
City of Urdaneta,Dilan-Paurido,Dante & Emong,2025-07-22 to 2025-08-01,236,704,236,2079,7186
City of Urdaneta,Labit Proper,Dante & Emong,2025-07-22 to 2025-08-01,81,289,81,1014,3939
City of Urdaneta,Labit West,Dante & Emong,2025-07-22 to 2025-08-01,93,287,93,789,2751
City of Urdaneta,Mabanogbog,Dante & Emong,2025-07-22 to 2025-08-01,162,555,162,1079,3564
City of Urdaneta,Macalong,Dante & Emong,2025-07-22 to 2025-08-01,57,221,57,484,1756
City of Urdaneta,Nancalobasaan,Dante & Emong,2025-07-22 to 2025-08-01,51,166,51,1008,3364
City of Urdaneta,Nancamaliran East,Dante & Emong,2025-07-22 to 2025-08-01,40,122,40,1300,5284
City of Urdaneta,Nancamaliran West,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,1707,5981
City of Urdaneta,Nancayasan,Dante & Emong,2025-07-22 to 2025-08-01,99,297,99,2420,8175
City of Urdaneta,Oltama,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,392,1422
City of Urdaneta,Palina East,Dante & Emong,2025-07-22 to 2025-08-01,70,188,70,1273,5190
City of Urdaneta,Palina West,Dante & Emong,2025-07-22 to 2025-08-01,99,303,99,985,3443
City of Urdaneta,Pedro T. Orata,Dante & Emong,2025-07-22 to 2025-08-01,61,183,61,1327,3458
City of Urdaneta,Pinmaludpod,Dante & Emong,2025-07-22 to 2025-08-01,120,365,120,2320,8324
City of Urdaneta,Poblacion,Dante & Emong,2025-07-22 to 2025-08-01,57,79,57,2194,7301
City of Urdaneta,San Jose,Dante & Emong,2025-07-22 to 2025-08-01,199,598,199,1832,5730
City of Urdaneta,San Vicente,Dante & Emong,2025-07-22 to 2025-08-01,76,279,76,2974,9532
City of Urdaneta,Santa Lucia,Dante & Emong,2025-07-22 to 2025-08-01,84,306,84,875,3401
City of Urdaneta,Santo Domingo,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,931,3423
City of Urdaneta,Sugcong,Dante & Emong,2025-07-22 to 2025-08-01,0,0,0,322,1160
City of Urdaneta,Tiposu,Dante & Emong,2025-07-22 to 2025-08-01,40,160,40,616,2262
City of Urdaneta,Tulong,Dante & Emong,2025-07-22 to 2025-08-01,148,441,148,444,1567
""",
    "nika_ofel_pepito_2024": _HEADER + """City of Urdaneta,Anonas,Nika + Ofel + Pepito,2024-11-16,5,19,5,1726,6285
City of Urdaneta,Bactad East,Nika + Ofel + Pepito,2024-11-16,1,3,1,705,2231
City of Urdaneta,Bayaoas,Nika + Ofel + Pepito,2024-11-16,2,6,2,1810,5864
City of Urdaneta,Bolaoen,Nika + Ofel + Pepito,2024-11-16,1,4,1,450,1604
City of Urdaneta,Cabaruan,Nika + Ofel + Pepito,2024-11-16,1,4,1,696,2389
City of Urdaneta,Cabuloan,Nika + Ofel + Pepito,2024-11-16,2,7,1,1140,3564
City of Urdaneta,Camanang,Nika + Ofel + Pepito,2024-11-16,2,7,1,1460,5397
City of Urdaneta,Camantiles,Nika + Ofel + Pepito,2024-11-16,5,16,5,1858,6564
City of Urdaneta,Casantaan,Nika + Ofel + Pepito,2024-11-16,1,4,1,428,1479
City of Urdaneta,Catablan,Nika + Ofel + Pepito,2024-11-16,2,8,1,1805,6107
City of Urdaneta,Cayambanan,Nika + Ofel + Pepito,2024-11-16,2,7,2,1407,4408
City of Urdaneta,Consolacion,Nika + Ofel + Pepito,2024-11-16,1,3,1,433,1830
City of Urdaneta,Dilan-Paurido,Nika + Ofel + Pepito,2024-11-16,2,8,1,2079,7186
City of Urdaneta,Labit Proper,Nika + Ofel + Pepito,2024-11-16,2,6,1,1014,3939
City of Urdaneta,Labit West,Nika + Ofel + Pepito,2024-11-16,1,4,1,789,2751
City of Urdaneta,Mabanogbog,Nika + Ofel + Pepito,2024-11-16,3,9,3,1079,3564
City of Urdaneta,Macalong,Nika + Ofel + Pepito,2024-11-16,1,3,1,484,1756
City of Urdaneta,Nancalobasaan,Nika + Ofel + Pepito,2024-11-16,3,11,3,1008,3364
City of Urdaneta,Nancamaliran East,Nika + Ofel + Pepito,2024-11-16,2,7,2,1300,5284
City of Urdaneta,Nancamaliran West,Nika + Ofel + Pepito,2024-11-16,2,7,1,1707,5981
City of Urdaneta,Nancayasan,Nika + Ofel + Pepito,2024-11-16,5,15,5,2420,8175
City of Urdaneta,Oltama,Nika + Ofel + Pepito,2024-11-16,1,3,1,392,1422
City of Urdaneta,Palina East,Nika + Ofel + Pepito,2024-11-16,2,6,2,1273,5190
City of Urdaneta,Palina West,Nika + Ofel + Pepito,2024-11-16,2,7,2,985,3443
City of Urdaneta,Pedro T. Orata,Nika + Ofel + Pepito,2024-11-16,2,6,1,1327,3458
City of Urdaneta,Pinmaludpod,Nika + Ofel + Pepito,2024-11-16,6,17,6,2320,8324
City of Urdaneta,Poblacion,Nika + Ofel + Pepito,2024-11-16,6,19,6,2194,7301
City of Urdaneta,San Jose,Nika + Ofel + Pepito,2024-11-16,4,15,4,1832,5730
City of Urdaneta,San Vicente,Nika + Ofel + Pepito,2024-11-16,6,21,6,2974,9532
City of Urdaneta,Santa Lucia,Nika + Ofel + Pepito,2024-11-16,2,8,1,875,3401
City of Urdaneta,Santo Domingo,Nika + Ofel + Pepito,2024-11-16,2,7,1,931,3423
City of Urdaneta,Sugcong,Nika + Ofel + Pepito,2024-11-16,1,4,1,322,1160
City of Urdaneta,Tiposu,Nika + Ofel + Pepito,2024-11-16,1,4,1,616,2262
City of Urdaneta,Tulong,Nika + Ofel + Pepito,2024-11-16,2,7,2,444,1567
""",
    "kristine_leon_2024": _HEADER + """City of Urdaneta,Anonas,Kristine + Leon,2024-10-24,0,0,0,1726,6285
City of Urdaneta,Bactad East,Kristine + Leon,2024-10-24,0,0,0,705,2231
City of Urdaneta,Bayaoas,Kristine + Leon,2024-10-24,0,0,0,1810,5864
City of Urdaneta,Bolaoen,Kristine + Leon,2024-10-24,0,0,0,450,1604
City of Urdaneta,Cabaruan,Kristine + Leon,2024-10-24,0,0,0,696,2389
City of Urdaneta,Cabuloan,Kristine + Leon,2024-10-24,0,0,0,1140,3564
City of Urdaneta,Camanang,Kristine + Leon,2024-10-24,0,0,0,1460,5397
City of Urdaneta,Camantiles,Kristine + Leon,2024-10-24,0,0,0,1858,6564
City of Urdaneta,Casantaan,Kristine + Leon,2024-10-24,0,0,0,428,1479
City of Urdaneta,Catablan,Kristine + Leon,2024-10-24,0,0,0,1805,6107
City of Urdaneta,Cayambanan,Kristine + Leon,2024-10-24,0,0,0,1407,4408
City of Urdaneta,Consolacion,Kristine + Leon,2024-10-24,0,0,0,433,1830
City of Urdaneta,Dilan-Paurido,Kristine + Leon,2024-10-24,0,0,0,2079,7186
City of Urdaneta,Labit Proper,Kristine + Leon,2024-10-24,0,0,0,1014,3939
City of Urdaneta,Labit West,Kristine + Leon,2024-10-24,0,0,0,789,2751
City of Urdaneta,Mabanogbog,Kristine + Leon,2024-10-24,0,0,0,1079,3564
City of Urdaneta,Macalong,Kristine + Leon,2024-10-24,0,0,0,484,1756
City of Urdaneta,Nancalobasaan,Kristine + Leon,2024-10-24,0,0,0,1008,3364
City of Urdaneta,Nancamaliran East,Kristine + Leon,2024-10-24,0,0,0,1300,5284
City of Urdaneta,Nancamaliran West,Kristine + Leon,2024-10-24,0,0,0,1707,5981
City of Urdaneta,Nancayasan,Kristine + Leon,2024-10-24,1,3,1,2420,8175
City of Urdaneta,Oltama,Kristine + Leon,2024-10-24,0,0,0,392,1422
City of Urdaneta,Palina East,Kristine + Leon,2024-10-24,0,0,0,1273,5190
City of Urdaneta,Palina West,Kristine + Leon,2024-10-24,0,0,0,985,3443
City of Urdaneta,Pedro T. Orata,Kristine + Leon,2024-10-24,0,0,0,1327,3458
City of Urdaneta,Pinmaludpod,Kristine + Leon,2024-10-24,1,3,1,2320,8324
City of Urdaneta,Poblacion,Kristine + Leon,2024-10-24,0,0,0,2194,7301
City of Urdaneta,San Jose,Kristine + Leon,2024-10-24,0,0,0,1832,5730
City of Urdaneta,San Vicente,Kristine + Leon,2024-10-24,0,0,0,2974,9532
City of Urdaneta,Santa Lucia,Kristine + Leon,2024-10-24,0,0,0,875,3401
City of Urdaneta,Santo Domingo,Kristine + Leon,2024-10-24,0,0,0,931,3423
City of Urdaneta,Sugcong,Kristine + Leon,2024-10-24,0,0,0,322,1160
City of Urdaneta,Tiposu,Kristine + Leon,2024-10-24,0,0,0,616,2262
City of Urdaneta,Tulong,Kristine + Leon,2024-10-24,0,0,0,444,1567
""",
    "enteng_habagat_2024": _HEADER + """City of Urdaneta,Anonas,Enteng + Habagat,2024-09-05 to 2024-09-06,13,46,13,1726,6285
City of Urdaneta,Bactad East,Enteng + Habagat,2024-09-05 to 2024-09-06,2,6,1,705,2231
City of Urdaneta,Bayaoas,Enteng + Habagat,2024-09-05 to 2024-09-06,4,16,2,1810,5864
City of Urdaneta,Bolaoen,Enteng + Habagat,2024-09-05 to 2024-09-06,2,8,1,450,1604
City of Urdaneta,Cabaruan,Enteng + Habagat,2024-09-05 to 2024-09-06,2,8,1,696,2389
City of Urdaneta,Cabuloan,Enteng + Habagat,2024-09-05 to 2024-09-06,3,10,2,1140,3564
City of Urdaneta,Camanang,Enteng + Habagat,2024-09-05 to 2024-09-06,4,14,3,1460,5397
City of Urdaneta,Camantiles,Enteng + Habagat,2024-09-05 to 2024-09-06,14,45,14,1858,6564
City of Urdaneta,Casantaan,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,1,428,1479
City of Urdaneta,Catablan,Enteng + Habagat,2024-09-05 to 2024-09-06,4,16,3,1805,6107
City of Urdaneta,Cayambanan,Enteng + Habagat,2024-09-05 to 2024-09-06,3,12,2,1407,4408
City of Urdaneta,Consolacion,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,433,1830
City of Urdaneta,Dilan-Paurido,Enteng + Habagat,2024-09-05 to 2024-09-06,4,14,3,2079,7186
City of Urdaneta,Labit Proper,Enteng + Habagat,2024-09-05 to 2024-09-06,3,12,2,1014,3939
City of Urdaneta,Labit West,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,789,2751
City of Urdaneta,Mabanogbog,Enteng + Habagat,2024-09-05 to 2024-09-06,6,21,6,1079,3564
City of Urdaneta,Macalong,Enteng + Habagat,2024-09-05 to 2024-09-06,2,8,2,484,1756
City of Urdaneta,Nancalobasaan,Enteng + Habagat,2024-09-05 to 2024-09-06,8,32,8,1008,3364
City of Urdaneta,Nancamaliran East,Enteng + Habagat,2024-09-05 to 2024-09-06,3,12,2,1300,5284
City of Urdaneta,Nancamaliran West,Enteng + Habagat,2024-09-05 to 2024-09-06,3,10,2,1707,5981
City of Urdaneta,Nancayasan,Enteng + Habagat,2024-09-05 to 2024-09-06,14,52,14,2420,8175
City of Urdaneta,Oltama,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,392,1422
City of Urdaneta,Palina East,Enteng + Habagat,2024-09-05 to 2024-09-06,4,16,2,1273,5190
City of Urdaneta,Palina West,Enteng + Habagat,2024-09-05 to 2024-09-06,3,12,3,985,3443
City of Urdaneta,Pedro T. Orata,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,2,1327,3458
City of Urdaneta,Pinmaludpod,Enteng + Habagat,2024-09-05 to 2024-09-06,12,45,12,2320,8324
City of Urdaneta,Poblacion,Enteng + Habagat,2024-09-05 to 2024-09-06,16,57,16,2194,7301
City of Urdaneta,San Jose,Enteng + Habagat,2024-09-05 to 2024-09-06,11,36,11,1832,5730
City of Urdaneta,San Vicente,Enteng + Habagat,2024-09-05 to 2024-09-06,17,59,17,2974,9532
City of Urdaneta,Santa Lucia,Enteng + Habagat,2024-09-05 to 2024-09-06,3,11,2,875,3401
City of Urdaneta,Santo Domingo,Enteng + Habagat,2024-09-05 to 2024-09-06,2,8,2,931,3423
City of Urdaneta,Sugcong,Enteng + Habagat,2024-09-05 to 2024-09-06,2,7,1,322,1160
City of Urdaneta,Tiposu,Enteng + Habagat,2024-09-05 to 2024-09-06,2,8,2,616,2262
City of Urdaneta,Tulong,Enteng + Habagat,2024-09-05 to 2024-09-06,4,14,4,444,1567
""",
    "carina_habagat_2024": _HEADER + """City of Urdaneta,Anonas,Carina + Habagat,2024-07-23 to 2024-07-28,2,8,2,1726,6285
City of Urdaneta,Bactad East,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,705,2231
City of Urdaneta,Bayaoas,Carina + Habagat,2024-07-23 to 2024-07-28,1,5,1,1810,5864
City of Urdaneta,Bolaoen,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,450,1604
City of Urdaneta,Cabaruan,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,696,2389
City of Urdaneta,Cabuloan,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1140,3564
City of Urdaneta,Camanang,Carina + Habagat,2024-07-23 to 2024-07-28,1,4,1,1460,5397
City of Urdaneta,Camantiles,Carina + Habagat,2024-07-23 to 2024-07-28,2,7,2,1858,6564
City of Urdaneta,Casantaan,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,428,1479
City of Urdaneta,Catablan,Carina + Habagat,2024-07-23 to 2024-07-28,1,5,1,1805,6107
City of Urdaneta,Cayambanan,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1407,4408
City of Urdaneta,Consolacion,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,433,1830
City of Urdaneta,Dilan-Paurido,Carina + Habagat,2024-07-23 to 2024-07-28,1,4,1,2079,7186
City of Urdaneta,Labit Proper,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1014,3939
City of Urdaneta,Labit West,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,789,2751
City of Urdaneta,Mabanogbog,Carina + Habagat,2024-07-23 to 2024-07-28,1,4,1,1079,3564
City of Urdaneta,Macalong,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,484,1756
City of Urdaneta,Nancalobasaan,Carina + Habagat,2024-07-23 to 2024-07-28,1,5,1,1008,3364
City of Urdaneta,Nancamaliran East,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1300,5284
City of Urdaneta,Nancamaliran West,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1707,5981
City of Urdaneta,Nancayasan,Carina + Habagat,2024-07-23 to 2024-07-28,2,8,2,2420,8175
City of Urdaneta,Oltama,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,392,1422
City of Urdaneta,Palina East,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1273,5190
City of Urdaneta,Palina West,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,985,3443
City of Urdaneta,Pedro T. Orata,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,1327,3458
City of Urdaneta,Pinmaludpod,Carina + Habagat,2024-07-23 to 2024-07-28,2,9,2,2320,8324
City of Urdaneta,Poblacion,Carina + Habagat,2024-07-23 to 2024-07-28,2,8,2,2194,7301
City of Urdaneta,San Jose,Carina + Habagat,2024-07-23 to 2024-07-28,2,7,2,1832,5730
City of Urdaneta,San Vicente,Carina + Habagat,2024-07-23 to 2024-07-28,2,8,2,2974,9532
City of Urdaneta,Santa Lucia,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,875,3401
City of Urdaneta,Santo Domingo,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,931,3423
City of Urdaneta,Sugcong,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,322,1160
City of Urdaneta,Tiposu,Carina + Habagat,2024-07-23 to 2024-07-28,0,0,0,616,2262
City of Urdaneta,Tulong,Carina + Habagat,2024-07-23 to 2024-07-28,1,4,1,444,1567
""",
    "egay_2023": _HEADER + """City of Urdaneta,Anonas,Egay,2023-07-26,42,182,42,1385,6221
City of Urdaneta,Bactad East,Egay,2023-07-26,6,28,3,550,2175
City of Urdaneta,Bayaoas,Egay,2023-07-26,12,54,7,1471,5789
City of Urdaneta,Bolaoen,Egay,2023-07-26,5,23,3,389,1506
City of Urdaneta,Cabaruan,Egay,2023-07-26,6,27,5,561,2353
City of Urdaneta,Cabuloan,Egay,2023-07-26,9,36,7,823,3506
City of Urdaneta,Camanang,Egay,2023-07-26,12,49,10,1201,5109
City of Urdaneta,Camantiles,Egay,2023-07-26,49,244,49,1558,6605
City of Urdaneta,Casantaan,Egay,2023-07-26,4,17,3,410,1549
City of Urdaneta,Catablan,Egay,2023-07-26,13,53,10,1525,6082
City of Urdaneta,Cayambanan,Egay,2023-07-26,9,40,8,1140,4440
City of Urdaneta,Consolacion,Egay,2023-07-26,5,20,3,432,1750
City of Urdaneta,Dilan-Paurido,Egay,2023-07-26,21,88,18,1784,7391
City of Urdaneta,Labit Proper,Egay,2023-07-26,10,41,7,871,3855
City of Urdaneta,Labit West,Egay,2023-07-26,9,43,7,653,2708
City of Urdaneta,Mabanogbog,Egay,2023-07-26,32,158,32,877,3470
City of Urdaneta,Macalong,Egay,2023-07-26,5,25,3,445,1553
City of Urdaneta,Nancalobasaan,Egay,2023-07-26,27,136,27,774,3315
City of Urdaneta,Nancamaliran East,Egay,2023-07-26,14,63,12,1351,5542
City of Urdaneta,Nancamaliran West,Egay,2023-07-26,13,57,10,1435,5748
City of Urdaneta,Nancayasan,Egay,2023-07-26,82,426,82,2156,8742
City of Urdaneta,Oltama,Egay,2023-07-26,4,15,2,359,1487
City of Urdaneta,Palina East,Egay,2023-07-26,12,54,9,1282,5144
City of Urdaneta,Palina West,Egay,2023-07-26,8,33,5,853,3386
City of Urdaneta,Pedro T. Orata,Egay,2023-07-26,7,27,4,603,2393
City of Urdaneta,Pinmaludpod,Egay,2023-07-26,77,377,77,1953,8166
City of Urdaneta,Poblacion,Egay,2023-07-26,60,320,60,1761,7285
City of Urdaneta,San Jose,Egay,2023-07-26,50,218,50,1398,5850
City of Urdaneta,San Vicente,Egay,2023-07-26,95,460,95,2360,9778
City of Urdaneta,Santa Lucia,Egay,2023-07-26,8,38,6,846,3273
City of Urdaneta,Santo Domingo,Egay,2023-07-26,10,47,7,858,3610
City of Urdaneta,Sugcong,Egay,2023-07-26,3,12,2,289,1168
City of Urdaneta,Tiposu,Egay,2023-07-26,5,19,3,502,2190
City of Urdaneta,Tulong,Egay,2023-07-26,14,60,14,360,1438
""",
    "paeng_2022": _HEADER + """City of Urdaneta,Anonas,Paeng,2022-10-29,0,0,0,1385,6221
City of Urdaneta,Bactad East,Paeng,2022-10-29,0,0,0,550,2175
City of Urdaneta,Bayaoas,Paeng,2022-10-29,0,0,0,1471,5789
City of Urdaneta,Bolaoen,Paeng,2022-10-29,0,0,0,389,1506
City of Urdaneta,Cabaruan,Paeng,2022-10-29,0,0,0,561,2353
City of Urdaneta,Cabuloan,Paeng,2022-10-29,0,0,0,823,3506
City of Urdaneta,Camanang,Paeng,2022-10-29,0,0,0,1201,5109
City of Urdaneta,Camantiles,Paeng,2022-10-29,0,0,0,1558,6605
City of Urdaneta,Casantaan,Paeng,2022-10-29,0,0,0,410,1549
City of Urdaneta,Catablan,Paeng,2022-10-29,0,0,0,1525,6082
City of Urdaneta,Cayambanan,Paeng,2022-10-29,0,0,0,1140,4440
City of Urdaneta,Consolacion,Paeng,2022-10-29,0,0,0,432,1750
City of Urdaneta,Dilan-Paurido,Paeng,2022-10-29,0,0,0,1784,7391
City of Urdaneta,Labit Proper,Paeng,2022-10-29,0,0,0,871,3855
City of Urdaneta,Labit West,Paeng,2022-10-29,0,0,0,653,2708
City of Urdaneta,Mabanogbog,Paeng,2022-10-29,0,0,0,877,3470
City of Urdaneta,Macalong,Paeng,2022-10-29,0,0,0,445,1553
City of Urdaneta,Nancalobasaan,Paeng,2022-10-29,0,0,0,774,3315
City of Urdaneta,Nancamaliran East,Paeng,2022-10-29,0,0,0,1351,5542
City of Urdaneta,Nancamaliran West,Paeng,2022-10-29,0,0,0,1435,5748
City of Urdaneta,Nancayasan,Paeng,2022-10-29,0,0,0,2156,8742
City of Urdaneta,Oltama,Paeng,2022-10-29,0,0,0,359,1487
City of Urdaneta,Palina East,Paeng,2022-10-29,0,0,0,1282,5144
City of Urdaneta,Palina West,Paeng,2022-10-29,0,0,0,853,3386
City of Urdaneta,Pedro T. Orata,Paeng,2022-10-29,0,0,0,603,2393
City of Urdaneta,Pinmaludpod,Paeng,2022-10-29,1,2,1,1953,8166
City of Urdaneta,Poblacion,Paeng,2022-10-29,0,0,0,1761,7285
City of Urdaneta,San Jose,Paeng,2022-10-29,0,0,0,1398,5850
City of Urdaneta,San Vicente,Paeng,2022-10-29,0,0,0,2360,9778
City of Urdaneta,Santa Lucia,Paeng,2022-10-29,0,0,0,846,3273
City of Urdaneta,Santo Domingo,Paeng,2022-10-29,0,0,0,858,3610
City of Urdaneta,Sugcong,Paeng,2022-10-29,0,0,0,289,1168
City of Urdaneta,Tiposu,Paeng,2022-10-29,0,0,0,502,2190
City of Urdaneta,Tulong,Paeng,2022-10-29,0,0,0,360,1438
""",
    "karding_2022": _HEADER + """City of Urdaneta,Anonas,Karding,2022-09-25,0,0,0,1385,6221
City of Urdaneta,Bactad East,Karding,2022-09-25,0,0,0,550,2175
City of Urdaneta,Bayaoas,Karding,2022-09-25,0,0,0,1471,5789
City of Urdaneta,Bolaoen,Karding,2022-09-25,0,0,0,389,1506
City of Urdaneta,Cabaruan,Karding,2022-09-25,0,0,0,561,2353
City of Urdaneta,Cabuloan,Karding,2022-09-25,0,0,0,823,3506
City of Urdaneta,Camanang,Karding,2022-09-25,0,0,0,1201,5109
City of Urdaneta,Camantiles,Karding,2022-09-25,0,0,0,1558,6605
City of Urdaneta,Casantaan,Karding,2022-09-25,0,0,0,410,1549
City of Urdaneta,Catablan,Karding,2022-09-25,0,0,0,1525,6082
City of Urdaneta,Cayambanan,Karding,2022-09-25,0,0,0,1140,4440
City of Urdaneta,Consolacion,Karding,2022-09-25,0,0,0,432,1750
City of Urdaneta,Dilan-Paurido,Karding,2022-09-25,0,0,0,1784,7391
City of Urdaneta,Labit Proper,Karding,2022-09-25,0,0,0,871,3855
City of Urdaneta,Labit West,Karding,2022-09-25,0,0,0,653,2708
City of Urdaneta,Mabanogbog,Karding,2022-09-25,0,0,0,877,3470
City of Urdaneta,Macalong,Karding,2022-09-25,0,0,0,445,1553
City of Urdaneta,Nancalobasaan,Karding,2022-09-25,0,0,0,774,3315
City of Urdaneta,Nancamaliran East,Karding,2022-09-25,0,0,0,1351,5542
City of Urdaneta,Nancamaliran West,Karding,2022-09-25,0,0,0,1435,5748
City of Urdaneta,Nancayasan,Karding,2022-09-25,0,0,0,2156,8742
City of Urdaneta,Oltama,Karding,2022-09-25,0,0,0,359,1487
City of Urdaneta,Palina East,Karding,2022-09-25,0,0,0,1282,5144
City of Urdaneta,Palina West,Karding,2022-09-25,0,0,0,853,3386
City of Urdaneta,Pedro T. Orata,Karding,2022-09-25,0,0,0,603,2393
City of Urdaneta,Pinmaludpod,Karding,2022-09-25,0,0,0,1953,8166
City of Urdaneta,Poblacion,Karding,2022-09-25,1,4,1,1761,7285
City of Urdaneta,San Jose,Karding,2022-09-25,0,0,0,1398,5850
City of Urdaneta,San Vicente,Karding,2022-09-25,1,3,1,2360,9778
City of Urdaneta,Santa Lucia,Karding,2022-09-25,0,0,0,846,3273
City of Urdaneta,Santo Domingo,Karding,2022-09-25,0,0,0,858,3610
City of Urdaneta,Sugcong,Karding,2022-09-25,0,0,0,289,1168
City of Urdaneta,Tiposu,Karding,2022-09-25,0,0,0,502,2190
City of Urdaneta,Tulong,Karding,2022-09-25,0,0,0,360,1438
""",
    "maring_2021": _HEADER + """City of Urdaneta,Anonas,Maring,2021-10-11,203,1041,203,1385,6221
City of Urdaneta,Bactad East,Maring,2021-10-11,21,100,15,550,2175
City of Urdaneta,Bayaoas,Maring,2021-10-11,55,230,31,1471,5789
City of Urdaneta,Bolaoen,Maring,2021-10-11,14,63,9,389,1506
City of Urdaneta,Cabaruan,Maring,2021-10-11,24,124,17,561,2353
City of Urdaneta,Cabuloan,Maring,2021-10-11,26,122,22,823,3506
City of Urdaneta,Camanang,Maring,2021-10-11,44,205,36,1201,5109
City of Urdaneta,Camantiles,Maring,2021-10-11,195,1022,195,1558,6605
City of Urdaneta,Casantaan,Maring,2021-10-11,16,79,11,410,1549
City of Urdaneta,Catablan,Maring,2021-10-11,63,333,39,1525,6082
City of Urdaneta,Cayambanan,Maring,2021-10-11,47,223,29,1140,4440
City of Urdaneta,Consolacion,Maring,2021-10-11,19,83,11,432,1750
City of Urdaneta,Dilan-Paurido,Maring,2021-10-11,67,311,41,1784,7391
City of Urdaneta,Labit Proper,Maring,2021-10-11,38,185,27,871,3855
City of Urdaneta,Labit West,Maring,2021-10-11,23,108,17,653,2708
City of Urdaneta,Mabanogbog,Maring,2021-10-11,94,516,94,877,3470
City of Urdaneta,Macalong,Maring,2021-10-11,18,86,11,445,1553
City of Urdaneta,Nancalobasaan,Maring,2021-10-11,120,663,120,774,3315
City of Urdaneta,Nancamaliran East,Maring,2021-10-11,53,255,36,1351,5542
City of Urdaneta,Nancamaliran West,Maring,2021-10-11,62,291,49,1435,5748
City of Urdaneta,Nancayasan,Maring,2021-10-11,293,1446,293,2156,8742
City of Urdaneta,Oltama,Maring,2021-10-11,15,70,12,359,1487
City of Urdaneta,Palina East,Maring,2021-10-11,43,206,36,1282,5144
City of Urdaneta,Palina West,Maring,2021-10-11,31,154,24,853,3386
City of Urdaneta,Pedro T. Orata,Maring,2021-10-11,24,125,17,603,2393
City of Urdaneta,Pinmaludpod,Maring,2021-10-11,312,1515,312,1953,8166
City of Urdaneta,Poblacion,Maring,2021-10-11,251,1338,251,1761,7285
City of Urdaneta,San Jose,Maring,2021-10-11,177,771,177,1398,5850
City of Urdaneta,San Vicente,Maring,2021-10-11,367,1953,367,2360,9778
City of Urdaneta,Santa Lucia,Maring,2021-10-11,25,136,16,846,3273
City of Urdaneta,Santo Domingo,Maring,2021-10-11,30,129,22,858,3610
City of Urdaneta,Sugcong,Maring,2021-10-11,11,53,9,289,1168
City of Urdaneta,Tiposu,Maring,2021-10-11,24,105,16,502,2190
City of Urdaneta,Tulong,Maring,2021-10-11,46,214,46,360,1438
""",
    "fabian_habagat_2021": _HEADER + """City of Urdaneta,Anonas,Fabian + Habagat,2021-07-23 to 2021-07-24,45,163,45,1385,6221
City of Urdaneta,Bactad East,Fabian + Habagat,2021-07-23 to 2021-07-24,5,17,3,550,2175
City of Urdaneta,Bayaoas,Fabian + Habagat,2021-07-23 to 2021-07-24,15,55,10,1471,5789
City of Urdaneta,Bolaoen,Fabian + Habagat,2021-07-23 to 2021-07-24,4,13,2,389,1506
City of Urdaneta,Cabaruan,Fabian + Habagat,2021-07-23 to 2021-07-24,5,20,4,561,2353
City of Urdaneta,Cabuloan,Fabian + Habagat,2021-07-23 to 2021-07-24,8,30,5,823,3506
City of Urdaneta,Camanang,Fabian + Habagat,2021-07-23 to 2021-07-24,11,46,7,1201,5109
City of Urdaneta,Camantiles,Fabian + Habagat,2021-07-23 to 2021-07-24,60,256,60,1558,6605
City of Urdaneta,Casantaan,Fabian + Habagat,2021-07-23 to 2021-07-24,4,14,3,410,1549
City of Urdaneta,Catablan,Fabian + Habagat,2021-07-23 to 2021-07-24,14,51,11,1525,6082
City of Urdaneta,Cayambanan,Fabian + Habagat,2021-07-23 to 2021-07-24,11,39,7,1140,4440
City of Urdaneta,Consolacion,Fabian + Habagat,2021-07-23 to 2021-07-24,5,17,4,432,1750
City of Urdaneta,Dilan-Paurido,Fabian + Habagat,2021-07-23 to 2021-07-24,15,54,12,1784,7391
City of Urdaneta,Labit Proper,Fabian + Habagat,2021-07-23 to 2021-07-24,8,25,6,871,3855
City of Urdaneta,Labit West,Fabian + Habagat,2021-07-23 to 2021-07-24,7,22,5,653,2708
City of Urdaneta,Mabanogbog,Fabian + Habagat,2021-07-23 to 2021-07-24,22,94,22,877,3470
City of Urdaneta,Macalong,Fabian + Habagat,2021-07-23 to 2021-07-24,4,14,3,445,1553
City of Urdaneta,Nancalobasaan,Fabian + Habagat,2021-07-23 to 2021-07-24,30,129,30,774,3315
City of Urdaneta,Nancamaliran East,Fabian + Habagat,2021-07-23 to 2021-07-24,11,38,8,1351,5542
City of Urdaneta,Nancamaliran West,Fabian + Habagat,2021-07-23 to 2021-07-24,15,61,9,1435,5748
City of Urdaneta,Nancayasan,Fabian + Habagat,2021-07-23 to 2021-07-24,75,305,75,2156,8742
City of Urdaneta,Oltama,Fabian + Habagat,2021-07-23 to 2021-07-24,5,18,4,359,1487
City of Urdaneta,Palina East,Fabian + Habagat,2021-07-23 to 2021-07-24,13,55,8,1282,5144
City of Urdaneta,Palina West,Fabian + Habagat,2021-07-23 to 2021-07-24,8,27,6,853,3386
City of Urdaneta,Pedro T. Orata,Fabian + Habagat,2021-07-23 to 2021-07-24,7,23,6,603,2393
City of Urdaneta,Pinmaludpod,Fabian + Habagat,2021-07-23 to 2021-07-24,67,237,67,1953,8166
City of Urdaneta,Poblacion,Fabian + Habagat,2021-07-23 to 2021-07-24,45,171,45,1761,7285
City of Urdaneta,San Jose,Fabian + Habagat,2021-07-23 to 2021-07-24,46,156,46,1398,5850
City of Urdaneta,San Vicente,Fabian + Habagat,2021-07-23 to 2021-07-24,77,325,77,2360,9778
City of Urdaneta,Santa Lucia,Fabian + Habagat,2021-07-23 to 2021-07-24,9,31,8,846,3273
City of Urdaneta,Santo Domingo,Fabian + Habagat,2021-07-23 to 2021-07-24,7,29,5,858,3610
City of Urdaneta,Sugcong,Fabian + Habagat,2021-07-23 to 2021-07-24,3,10,2,289,1168
City of Urdaneta,Tiposu,Fabian + Habagat,2021-07-23 to 2021-07-24,5,20,4,502,2190
City of Urdaneta,Tulong,Fabian + Habagat,2021-07-23 to 2021-07-24,14,55,14,360,1438
""",
}

def parse(report_key):
    reader = csv.DictReader(io.StringIO(_FILES[report_key]))
    return [{
        "barangay": r["Barangay"],
        "storm": r["Name of Typhoon"],
        "date": r["Date ng Typhoon"],
        "affected_families": int(r["Affected Families"]),
        "affected_individuals": int(r["Affected Individuals"]),
        "food_packs_given": int(r["Food Packs Given"]),
        "total_families": int(r["Total Number of Families"]),
        "total_individuals": int(r["Total Number of Individuals"]),
    } for r in reader]


def _report(key):
    rows = parse(key)
    # Calendar keys come from the report's own storm names - see _storms.py.
    return {"key": key, "rows": rows,
            "typhoon_keys": storm_keys(rows[0]["storm"], rows[0]["date"][:4])}


REPORTS = [_report(key) for key in _FILES]


if __name__ == "__main__":
    ok = True
    for rep in REPORTS:
        rows = rep["rows"]
        fam = sum(r["affected_families"] for r in rows)
        packs = sum(r["food_packs_given"] for r in rows)
        good = len(rows) == 34 and len({normalize(r["barangay"]) for r in rows}) == 34
        ok &= good
        print(f"{rep['key']:<34} 34 brgy={good!s:<6} families={fam:>6,} packs={packs:>6,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Urdaneta reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
