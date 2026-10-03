"""
REAL records given to the team: Calasiao per-barangay disaster reports for 14
typhoon reports, 2021-2026, all 24 barangays per file, in the same clean
tabulated CSV format as Urdaneta's.

Current version = the "complete and most updated" Calasiao set delivered
2026-10-03 (second delivery that day). It has the same 14-report structure as
Urdaneta's set and REPLACES this module's earlier 2026-10-03 version:
  * Maymay (2026) -> combined "Luis & Maymay & Neneng & Pilandok" report
    (old Maymay-only sheet had 5 packs; the combined one has 27,520);
  * separate Nika / Ofel / Pepito and Kristine / Leon 2024 sheets -> one
    combined report each (as in Urdaneta's set);
  * NEW: Paolo (Oct 2025), Uwan (Nov 2025), Fabian + Habagat (Jul 2021).
Before that, the old 25-typhoon version of this module (a much larger scale)
and real_calasiao_reports_2025.py were replaced - see git history.

Each report links to every storm its "Name of Typhoon" column names (see
_storms.py; the typhoon calendar is built from these reports - see
scripts/typhoon_calendar_from_reports.py). Combined reports:
  Luis & Maymay & Neneng & Pilandok (2026) -> luis_2026, maymay_2026,
                                     neneng_2026, pilandok_2026
  Nando & Opong     (Sep 2025) -> nando_2025, opong_2025
  Crising & Emong   (Jul 2025) -> crising_2025, emong_2025
  Nika & Ofel & Pepito (Nov 2024) -> nika_2024, ofel_2024, pepito_2024
  Kristine & Leon   (Oct 2024) -> kristine_2024, leon_2024

Data-quality notes kept from the source (not corrected - figures are as given):
  * Uwan's source file is named "FEB2025" but its rows are dated 2025-11-10
    (Uwan = Nov 2025); the row date is used.
  * Luis & Maymay & Neneng & Pilandok 2026: Affected Families exceeds Total
    Number of Families in most barangays (e.g. Buenlag 4,617 vs 2,087) -
    plausibly the same families counted once per storm across the four.
  * Crising & Emong: several barangays got roughly 2 packs per affected
    family (e.g. Mancup 2,600 packs / 1,300 families) - plausibly two
    distributions (one per storm).
  * Crising & Emong / Nando & Opong: "Total Number of Families" differs from
    the other reports for some barangays (e.g. Banaoang 1,220 / 2,200 vs
    1,327) - kept as each report's own snapshot.

Run this file to print a structural sanity check per report.
"""
import csv
import io

from _barangay_names import strip_accents_and_punct
from _storms import storm_keys


def normalize(name):
    """Older Calasiao sheets spell 'Cabiloocan'; the barangays table spells
    it 'Cabilocaan'."""
    s = strip_accents_and_punct(name)
    return {"cabiloocan": "cabilocaan"}.get(s, s)


_HEADER = ("Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,"
           "Affected Individuals,Food Packs Given,Total Number of Families,"
           "Total Number of Individuals\n")

_FILES = {
    "luis_maymay_neneng_pilandok_2026": _HEADER + """Calasiao,Ambonao,Luis & Maymay & Neneng & Pilandok,2026-08-01,2663,10634,1225,1895,7046
Calasiao,Ambuetel,Luis & Maymay & Neneng & Pilandok,2026-08-01,604,2501,165,776,3031
Calasiao,Banaoang,Luis & Maymay & Neneng & Pilandok,2026-08-01,3055,12450,2030,1327,5069
Calasiao,Bued,Luis & Maymay & Neneng & Pilandok,2026-08-01,2613,10145,1440,1649,5904
Calasiao,Buenlag,Luis & Maymay & Neneng & Pilandok,2026-08-01,4617,19278,2875,2087,8231
Calasiao,Cabilocaan,Luis & Maymay & Neneng & Pilandok,2026-08-01,1075,4201,445,876,3167
Calasiao,Dinalaoan,Luis & Maymay & Neneng & Pilandok,2026-08-01,2283,9074,1580,1123,4149
Calasiao,Doyong,Luis & Maymay & Neneng & Pilandok,2026-08-01,2033,8323,1145,1046,4020
Calasiao,Gabon,Luis & Maymay & Neneng & Pilandok,2026-08-01,1404,5674,835,757,2861
Calasiao,Lasip,Luis & Maymay & Neneng & Pilandok,2026-08-01,2172,8611,1705,875,3223
Calasiao,Longos,Luis & Maymay & Neneng & Pilandok,2026-08-01,2230,8805,1655,838,3069
Calasiao,Lumbang,Luis & Maymay & Neneng & Pilandok,2026-08-01,1813,7282,1405,705,2642
Calasiao,Macabito,Luis & Maymay & Neneng & Pilandok,2026-08-01,812,3282,220,1179,4461
Calasiao,Malabago,Luis & Maymay & Neneng & Pilandok,2026-08-01,2045,8332,1145,1159,4427
Calasiao,Mancup,Luis & Maymay & Neneng & Pilandok,2026-08-01,2454,9646,1905,1026,3735
Calasiao,Nagsaing,Luis & Maymay & Neneng & Pilandok,2026-08-01,1304,5537,375,1503,6064
Calasiao,Nalsian,Luis & Maymay & Neneng & Pilandok,2026-08-01,2687,10425,1245,1797,6429
Calasiao,Poblacion East,Luis & Maymay & Neneng & Pilandok,2026-08-01,930,3808,570,438,1684
Calasiao,Poblacion West,Luis & Maymay & Neneng & Pilandok,2026-08-01,170,683,60,162,609
Calasiao,Quesban,Luis & Maymay & Neneng & Pilandok,2026-08-01,1220,4609,580,927,3200
Calasiao,San Miguel,Luis & Maymay & Neneng & Pilandok,2026-08-01,2057,8097,705,2150,7842
Calasiao,San Vicente,Luis & Maymay & Neneng & Pilandok,2026-08-01,625,2561,255,549,2117
Calasiao,Songkoy,Luis & Maymay & Neneng & Pilandok,2026-08-01,1317,5292,695,786,2949
Calasiao,Talibaew,Luis & Maymay & Neneng & Pilandok,2026-08-01,3683,14217,3260,1339,4757
""",
    "uwan_2025": _HEADER + """Calasiao,Ambonao,Uwan,2025-11-10,96,468,50,1895,7046
Calasiao,Ambuetel,Uwan,2025-11-10,23,112,5,776,3031
Calasiao,Banaoang,Uwan,2025-11-10,110,548,100,1327,5069
Calasiao,Bued,Uwan,2025-11-10,95,446,55,1649,5904
Calasiao,Buenlag,Uwan,2025-11-10,166,850,130,2087,8231
Calasiao,Cabilocaan,Uwan,2025-11-10,40,186,20,876,3167
Calasiao,Dinalaoan,Uwan,2025-11-10,83,400,55,1123,4149
Calasiao,Doyong,Uwan,2025-11-10,74,367,50,1046,4020
Calasiao,Gabon,Uwan,2025-11-10,51,250,35,757,2861
Calasiao,Lasip,Uwan,2025-11-10,79,379,75,875,3223
Calasiao,Longos,Uwan,2025-11-10,81,388,70,838,3069
Calasiao,Lumbang,Uwan,2025-11-10,66,321,60,705,2642
Calasiao,Macabito,Uwan,2025-11-10,30,145,10,1179,4461
Calasiao,Malabago,Uwan,2025-11-10,74,367,50,1159,4427
Calasiao,Mancup,Uwan,2025-11-10,89,425,80,1026,3735
Calasiao,Nagsaing,Uwan,2025-11-10,48,246,15,1503,6064
Calasiao,Nalsian,Uwan,2025-11-10,97,458,60,1797,6429
Calasiao,Poblacion East,Uwan,2025-11-10,34,168,30,438,1684
Calasiao,Poblacion West,Uwan,2025-11-10,7,31,5,162,609
Calasiao,Quesban,Uwan,2025-11-10,45,203,25,927,3200
Calasiao,San Miguel,Uwan,2025-11-10,75,357,25,2150,7842
Calasiao,San Vicente,Uwan,2025-11-10,23,113,10,549,2117
Calasiao,Songkoy,Uwan,2025-11-10,48,233,30,786,2949
Calasiao,Talibaew,Uwan,2025-11-10,133,624,120,1339,4757
""",
    "paolo_2025": _HEADER + """Calasiao,Ambonao,Paolo,2025-10-03,29,117,25,1895,7046
Calasiao,Ambuetel,Paolo,2025-10-03,6,20,5,776,3031
Calasiao,Banaoang,Paolo,2025-10-03,24,99,20,1327,5069
Calasiao,Bued,Paolo,2025-10-03,23,88,20,1649,5904
Calasiao,Buenlag,Paolo,2025-10-03,48,182,45,2087,8231
Calasiao,Cabilocaan,Paolo,2025-10-03,10,38,10,876,3167
Calasiao,Dinalaoan,Paolo,2025-10-03,22,87,20,1123,4149
Calasiao,Doyong,Paolo,2025-10-03,17,63,15,1046,4020
Calasiao,Gabon,Paolo,2025-10-03,13,48,10,757,2861
Calasiao,Lasip,Paolo,2025-10-03,25,103,25,875,3223
Calasiao,Longos,Paolo,2025-10-03,15,61,15,838,3069
Calasiao,Lumbang,Paolo,2025-10-03,16,64,15,705,2642
Calasiao,Macabito,Paolo,2025-10-03,7,30,5,1179,4461
Calasiao,Malabago,Paolo,2025-10-03,23,97,20,1159,4427
Calasiao,Mancup,Paolo,2025-10-03,24,84,20,1026,3735
Calasiao,Nagsaing,Paolo,2025-10-03,16,66,15,1503,6064
Calasiao,Nalsian,Paolo,2025-10-03,19,68,15,1797,6429
Calasiao,Poblacion East,Paolo,2025-10-03,10,38,10,438,1684
Calasiao,Poblacion West,Paolo,2025-10-03,2,5,0,162,609
Calasiao,Quesban,Paolo,2025-10-03,11,39,10,927,3200
Calasiao,San Miguel,Paolo,2025-10-03,19,80,15,2150,7842
Calasiao,San Vicente,Paolo,2025-10-03,7,23,5,549,2117
Calasiao,Songkoy,Paolo,2025-10-03,9,33,5,786,2949
Calasiao,Talibaew,Paolo,2025-10-03,25,107,25,1339,4757
""",
    "nando_opong_2025": _HEADER + """Calasiao,Ambonao,Nando & Opong,2025-09-22,0,0,0,1695,7046
Calasiao,Ambuetel,Nando & Opong,2025-09-22,0,0,0,729,3031
Calasiao,Banaoang,Nando & Opong,2025-09-22,2200,8800,2200,2200,5069
Calasiao,Bued,Nando & Opong,2025-09-22,720,2880,0,1421,5904
Calasiao,Buenlag,Nando & Opong,2025-09-22,800,3659,1320,1980,8231
Calasiao,Cabilocaan,Nando & Opong,2025-09-22,0,0,0,762,3167
Calasiao,Dinalaoan,Nando & Opong,2025-09-22,750,3750,1000,998,4149
Calasiao,Doyong,Nando & Opong,2025-09-22,850,3413,0,967,4020
Calasiao,Gabon,Nando & Opong,2025-09-22,700,3500,600,700,2861
Calasiao,Lasip,Nando & Opong,2025-09-22,1380,4131,1280,1380,3223
Calasiao,Longos,Nando & Opong,2025-09-22,1250,3123,1230,1250,3069
Calasiao,Lumbang,Nando & Opong,2025-09-22,790,3160,600,790,2642
Calasiao,Macabito,Nando & Opong,2025-09-22,0,0,0,1073,4461
Calasiao,Malabago,Nando & Opong,2025-09-22,1822,4952,1250,1822,4427
Calasiao,Mancup,Nando & Opong,2025-09-22,1300,6143,1300,1300,3735
Calasiao,Nagsaing,Nando & Opong,2025-09-22,0,0,0,1459,6064
Calasiao,Nalsian,Nando & Opong,2025-09-22,2306,9229,2600,2306,6429
Calasiao,Poblacion East,Nando & Opong,2025-09-22,790,3160,500,790,1684
Calasiao,Poblacion West,Nando & Opong,2025-09-22,511,814,160,511,609
Calasiao,Quesban,Nando & Opong,2025-09-22,590,2069,0,770,3200
Calasiao,San Miguel,Nando & Opong,2025-09-22,469,2345,550,1887,7842
Calasiao,San Vicente,Nando & Opong,2025-09-22,600,2863,700,600,2117
Calasiao,Songkoy,Nando & Opong,2025-09-22,280,420,0,710,2949
Calasiao,Talibaew,Nando & Opong,2025-09-22,1900,7600,1850,1900,4757
""",
    "crising_emong_2025": _HEADER + """Calasiao,Ambonao,Crising & Emong,2025-07-18,1030,5162,1030,1695,7046
Calasiao,Ambuetel,Crising & Emong,2025-07-18,969,3876,1769,969,3031
Calasiao,Banaoang,Crising & Emong,2025-07-18,1149,4596,1499,1220,5069
Calasiao,Bued,Crising & Emong,2025-07-18,1500,6074,1500,1500,5904
Calasiao,Buenlag,Crising & Emong,2025-07-18,2156,8624,2156,2156,8231
Calasiao,Cabilocaan,Crising & Emong,2025-07-18,509,2545,509,762,3167
Calasiao,Dinalaoan,Crising & Emong,2025-07-18,1268,6340,1268,1268,4149
Calasiao,Doyong,Crising & Emong,2025-07-18,1700,4352,1700,1700,4020
Calasiao,Gabon,Crising & Emong,2025-07-18,759,3795,904,759,2861
Calasiao,Lasip,Crising & Emong,2025-07-18,1380,4131,1382,1380,3223
Calasiao,Longos,Crising & Emong,2025-07-18,1205,4820,1229,1205,3069
Calasiao,Lumbang,Crising & Emong,2025-07-18,790,2032,1419,790,2642
Calasiao,Macabito,Crising & Emong,2025-07-18,1015,4606,1015,1073,4461
Calasiao,Malabago,Crising & Emong,2025-07-18,1822,4952,3322,1822,4427
Calasiao,Mancup,Crising & Emong,2025-07-18,1300,5196,2600,1300,3735
Calasiao,Nagsaing,Crising & Emong,2025-07-18,2109,10530,2109,2109,6064
Calasiao,Nalsian,Crising & Emong,2025-07-18,2253,5686,3998,2253,6429
Calasiao,Poblacion East,Crising & Emong,2025-07-18,843,3375,843,843,1684
Calasiao,Poblacion West,Crising & Emong,2025-07-18,450,900,900,450,609
Calasiao,Quesban,Crising & Emong,2025-07-18,603,1807,1206,770,3200
Calasiao,San Miguel,Crising & Emong,2025-07-18,1300,5263,1300,1887,7842
Calasiao,San Vicente,Crising & Emong,2025-07-18,520,2080,920,520,2117
Calasiao,Songkoy,Crising & Emong,2025-07-18,826,3304,1625,826,2949
Calasiao,Talibaew,Crising & Emong,2025-07-18,1900,9358,2900,1900,4757
""",
    "nika_ofel_pepito_2024": _HEADER + """Calasiao,Ambonao,Nika & Ofel & Pepito,2024-11-10,23,77,20,1895,7046
Calasiao,Ambuetel,Nika & Ofel & Pepito,2024-11-10,6,19,5,776,3031
Calasiao,Banaoang,Nika & Ofel & Pepito,2024-11-10,26,90,25,1327,5069
Calasiao,Bued,Nika & Ofel & Pepito,2024-11-10,22,73,20,1649,5904
Calasiao,Buenlag,Nika & Ofel & Pepito,2024-11-10,38,137,35,2087,8231
Calasiao,Cabilocaan,Nika & Ofel & Pepito,2024-11-10,10,31,10,876,3167
Calasiao,Dinalaoan,Nika & Ofel & Pepito,2024-11-10,19,65,15,1123,4149
Calasiao,Doyong,Nika & Ofel & Pepito,2024-11-10,17,60,15,1046,4020
Calasiao,Gabon,Nika & Ofel & Pepito,2024-11-10,12,41,10,757,2861
Calasiao,Lasip,Nika & Ofel & Pepito,2024-11-10,19,63,15,875,3223
Calasiao,Longos,Nika & Ofel & Pepito,2024-11-10,19,64,15,838,3069
Calasiao,Lumbang,Nika & Ofel & Pepito,2024-11-10,16,53,15,705,2642
Calasiao,Macabito,Nika & Ofel & Pepito,2024-11-10,8,25,5,1179,4461
Calasiao,Malabago,Nika & Ofel & Pepito,2024-11-10,18,61,15,1159,4427
Calasiao,Mancup,Nika & Ofel & Pepito,2024-11-10,21,70,20,1026,3735
Calasiao,Nagsaing,Nika & Ofel & Pepito,2024-11-10,12,41,10,1503,6064
Calasiao,Nalsian,Nika & Ofel & Pepito,2024-11-10,23,75,20,1797,6429
Calasiao,Poblacion East,Nika & Ofel & Pepito,2024-11-10,8,28,5,438,1684
Calasiao,Poblacion West,Nika & Ofel & Pepito,2024-11-10,2,5,0,162,609
Calasiao,Quesban,Nika & Ofel & Pepito,2024-11-10,11,34,10,927,3200
Calasiao,San Miguel,Nika & Ofel & Pepito,2024-11-10,18,59,15,2150,7842
Calasiao,San Vicente,Nika & Ofel & Pepito,2024-11-10,6,19,5,549,2117
Calasiao,Songkoy,Nika & Ofel & Pepito,2024-11-10,12,39,10,786,2949
Calasiao,Talibaew,Nika & Ofel & Pepito,2024-11-10,31,102,30,1339,4757
""",
    "kristine_leon_2024": _HEADER + """Calasiao,Ambonao,Kristine & Leon,2024-10-23,12,52,9,1895,7046
Calasiao,Ambuetel,Kristine & Leon,2024-10-23,3,13,1,776,3031
Calasiao,Banaoang,Kristine & Leon,2024-10-23,14,61,14,1327,5069
Calasiao,Bued,Kristine & Leon,2024-10-23,12,50,10,1649,5904
Calasiao,Buenlag,Kristine & Leon,2024-10-23,21,95,21,2087,8231
Calasiao,Cabilocaan,Kristine & Leon,2024-10-23,6,22,4,876,3167
Calasiao,Dinalaoan,Kristine & Leon,2024-10-23,11,45,11,1123,4149
Calasiao,Doyong,Kristine & Leon,2024-10-23,10,42,10,1046,4020
Calasiao,Gabon,Kristine & Leon,2024-10-23,7,29,7,757,2861
Calasiao,Lasip,Kristine & Leon,2024-10-23,10,42,10,875,3223
Calasiao,Longos,Kristine & Leon,2024-10-23,10,43,10,838,3069
Calasiao,Lumbang,Kristine & Leon,2024-10-23,9,37,9,705,2642
Calasiao,Macabito,Kristine & Leon,2024-10-23,4,16,2,1179,4461
Calasiao,Malabago,Kristine & Leon,2024-10-23,10,42,10,1159,4427
Calasiao,Mancup,Kristine & Leon,2024-10-23,11,47,11,1026,3735
Calasiao,Nagsaing,Kristine & Leon,2024-10-23,6,27,3,1503,6064
Calasiao,Nalsian,Kristine & Leon,2024-10-23,12,51,11,1797,6429
Calasiao,Poblacion East,Kristine & Leon,2024-10-23,5,19,5,438,1684
Calasiao,Poblacion West,Kristine & Leon,2024-10-23,2,5,1,162,609
Calasiao,Quesban,Kristine & Leon,2024-10-23,6,23,5,927,3200
Calasiao,San Miguel,Kristine & Leon,2024-10-23,10,40,7,2150,7842
Calasiao,San Vicente,Kristine & Leon,2024-10-23,4,14,2,549,2117
Calasiao,Songkoy,Kristine & Leon,2024-10-23,7,27,7,786,2949
Calasiao,Talibaew,Kristine & Leon,2024-10-23,17,70,17,1339,4757
""",
    "enteng_habagat_2024": _HEADER + """Calasiao,Ambonao,Enteng + Habagat,2024-09-04,381,1329,215,1895,7046
Calasiao,Ambuetel,Enteng + Habagat,2024-09-04,87,313,30,776,3031
Calasiao,Banaoang,Enteng + Habagat,2024-09-04,437,1555,365,1327,5069
Calasiao,Bued,Enteng + Habagat,2024-09-04,374,1270,215,1649,5904
Calasiao,Buenlag,Enteng + Habagat,2024-09-04,660,2404,475,2087,8231
Calasiao,Cabilocaan,Enteng + Habagat,2024-09-04,154,526,75,876,3167
Calasiao,Dinalaoan,Enteng + Habagat,2024-09-04,327,1135,240,1123,4149
Calasiao,Doyong,Enteng + Habagat,2024-09-04,291,1039,220,1046,4020
Calasiao,Gabon,Enteng + Habagat,2024-09-04,201,709,135,757,2861
Calasiao,Lasip,Enteng + Habagat,2024-09-04,311,1077,295,875,3223
Calasiao,Longos,Enteng + Habagat,2024-09-04,319,1101,290,838,3069
Calasiao,Lumbang,Enteng + Habagat,2024-09-04,260,911,255,705,2642
Calasiao,Macabito,Enteng + Habagat,2024-09-04,117,411,35,1179,4461
Calasiao,Malabago,Enteng + Habagat,2024-09-04,293,1041,190,1159,4427
Calasiao,Mancup,Enteng + Habagat,2024-09-04,351,1207,305,1026,3735
Calasiao,Nagsaing,Enteng + Habagat,2024-09-04,187,690,70,1503,6064
Calasiao,Nalsian,Enteng + Habagat,2024-09-04,384,1304,205,1797,6429
Calasiao,Poblacion East,Enteng + Habagat,2024-09-04,134,476,105,438,1684
Calasiao,Poblacion West,Enteng + Habagat,2024-09-04,25,86,10,162,609
Calasiao,Quesban,Enteng + Habagat,2024-09-04,175,578,85,927,3200
Calasiao,San Miguel,Enteng + Habagat,2024-09-04,295,1014,120,2150,7842
Calasiao,San Vicente,Enteng + Habagat,2024-09-04,90,320,40,549,2117
Calasiao,Songkoy,Enteng + Habagat,2024-09-04,189,662,125,786,2949
Calasiao,Talibaew,Enteng + Habagat,2024-09-04,527,1780,500,1339,4757
""",
    "carina_habagat_2024": _HEADER + """Calasiao,Ambonao,Carina + Habagat,2024-07-22,47,163,45,1895,7046
Calasiao,Ambuetel,Carina + Habagat,2024-07-22,11,39,5,776,3031
Calasiao,Banaoang,Carina + Habagat,2024-07-22,54,190,50,1327,5069
Calasiao,Bued,Carina + Habagat,2024-07-22,46,155,45,1649,5904
Calasiao,Buenlag,Carina + Habagat,2024-07-22,81,293,80,2087,8231
Calasiao,Cabilocaan,Carina + Habagat,2024-07-22,20,65,15,876,3167
Calasiao,Dinalaoan,Carina + Habagat,2024-07-22,40,138,40,1123,4149
Calasiao,Doyong,Carina + Habagat,2024-07-22,36,127,35,1046,4020
Calasiao,Gabon,Carina + Habagat,2024-07-22,25,87,25,757,2861
Calasiao,Lasip,Carina + Habagat,2024-07-22,38,131,35,875,3223
Calasiao,Longos,Carina + Habagat,2024-07-22,39,134,35,838,3069
Calasiao,Lumbang,Carina + Habagat,2024-07-22,32,111,30,705,2642
Calasiao,Macabito,Carina + Habagat,2024-07-22,15,51,10,1179,4461
Calasiao,Malabago,Carina + Habagat,2024-07-22,36,127,35,1159,4427
Calasiao,Mancup,Carina + Habagat,2024-07-22,43,147,40,1026,3735
Calasiao,Nagsaing,Carina + Habagat,2024-07-22,24,85,15,1503,6064
Calasiao,Nalsian,Carina + Habagat,2024-07-22,47,159,40,1797,6429
Calasiao,Poblacion East,Carina + Habagat,2024-07-22,17,59,15,438,1684
Calasiao,Poblacion West,Carina + Habagat,2024-07-22,4,11,0,162,609
Calasiao,Quesban,Carina + Habagat,2024-07-22,22,71,20,927,3200
Calasiao,San Miguel,Carina + Habagat,2024-07-22,36,124,25,2150,7842
Calasiao,San Vicente,Carina + Habagat,2024-07-22,12,40,10,549,2117
Calasiao,Songkoy,Carina + Habagat,2024-07-22,24,82,20,786,2949
Calasiao,Talibaew,Carina + Habagat,2024-07-22,64,217,60,1339,4757
""",
    "egay_habagat_2023": _HEADER + """Calasiao,Ambonao,Egay + Habagat,2023-07-26,722,3978,80,1566,6879
Calasiao,Ambuetel,Egay + Habagat,2023-07-26,165,933,10,644,2933
Calasiao,Banaoang,Egay + Habagat,2023-07-26,841,4743,145,1113,5032
Calasiao,Bued,Egay + Habagat,2023-07-26,774,3921,90,1489,5896
Calasiao,Buenlag,Egay + Habagat,2023-07-26,1604,7776,250,2211,8281
Calasiao,Cabilocaan,Egay + Habagat,2023-07-26,312,1545,30,775,2985
Calasiao,Dinalaoan,Egay + Habagat,2023-07-26,639,3457,110,958,4114
Calasiao,Doyong,Egay + Habagat,2023-07-26,627,3217,100,983,3957
Calasiao,Gabon,Egay + Habagat,2023-07-26,405,2295,60,666,3026
Calasiao,Lasip,Egay + Habagat,2023-07-26,612,3228,110,752,3398
Calasiao,Longos,Egay + Habagat,2023-07-26,654,2855,135,749,3006
Calasiao,Lumbang,Egay + Habagat,2023-07-26,488,2260,90,578,2379
Calasiao,Macabito,Egay + Habagat,2023-07-26,224,1242,15,992,4395
Calasiao,Malabago,Egay + Habagat,2023-07-26,597,3169,75,1031,4329
Calasiao,Mancup,Egay + Habagat,2023-07-26,621,3439,105,791,3621
Calasiao,Nagsaing,Egay + Habagat,2023-07-26,396,2166,35,1389,6060
Calasiao,Nalsian,Egay + Habagat,2023-07-26,850,4328,110,1734,6906
Calasiao,Poblacion East,Egay + Habagat,2023-07-26,288,1483,50,412,1671
Calasiao,Poblacion West,Egay + Habagat,2023-07-26,83,394,10,240,883
Calasiao,Quesban,Egay + Habagat,2023-07-26,357,1771,35,825,3191
Calasiao,San Miguel,Egay + Habagat,2023-07-26,622,3119,50,1980,7747
Calasiao,San Vicente,Egay + Habagat,2023-07-26,182,988,20,485,2107
Calasiao,Songkoy,Egay + Habagat,2023-07-26,375,1981,50,681,2848
Calasiao,Talibaew,Egay + Habagat,2023-07-26,1065,4585,235,1181,4827
""",
    "paeng_2022": _HEADER + """Calasiao,Ambonao,Paeng,2022-10-29,0,0,0,1566,6879
Calasiao,Ambuetel,Paeng,2022-10-29,0,0,0,644,2933
Calasiao,Banaoang,Paeng,2022-10-29,1,5,1,1113,5032
Calasiao,Bued,Paeng,2022-10-29,0,0,0,1489,5896
Calasiao,Buenlag,Paeng,2022-10-29,1,5,1,2211,8281
Calasiao,Cabilocaan,Paeng,2022-10-29,0,0,0,775,2985
Calasiao,Dinalaoan,Paeng,2022-10-29,1,4,1,958,4114
Calasiao,Doyong,Paeng,2022-10-29,1,4,1,983,3957
Calasiao,Gabon,Paeng,2022-10-29,1,4,1,666,3026
Calasiao,Lasip,Paeng,2022-10-29,1,4,1,752,3398
Calasiao,Longos,Paeng,2022-10-29,1,4,1,749,3006
Calasiao,Lumbang,Paeng,2022-10-29,1,4,1,578,2379
Calasiao,Macabito,Paeng,2022-10-29,0,0,0,992,4395
Calasiao,Malabago,Paeng,2022-10-29,1,4,0,1031,4329
Calasiao,Mancup,Paeng,2022-10-29,1,4,1,791,3621
Calasiao,Nagsaing,Paeng,2022-10-29,0,0,0,1389,6060
Calasiao,Nalsian,Paeng,2022-10-29,0,0,0,1734,6906
Calasiao,Poblacion East,Paeng,2022-10-29,1,4,1,412,1671
Calasiao,Poblacion West,Paeng,2022-10-29,0,0,0,240,883
Calasiao,Quesban,Paeng,2022-10-29,0,0,0,825,3191
Calasiao,San Miguel,Paeng,2022-10-29,0,0,0,1980,7747
Calasiao,San Vicente,Paeng,2022-10-29,0,0,0,485,2107
Calasiao,Songkoy,Paeng,2022-10-29,0,0,0,681,2848
Calasiao,Talibaew,Paeng,2022-10-29,1,4,1,1181,4827
""",
    "karding_2022": _HEADER + """Calasiao,Ambonao,Karding,2022-09-25,0,0,0,1566,6879
Calasiao,Ambuetel,Karding,2022-09-25,0,0,0,644,2933
Calasiao,Banaoang,Karding,2022-09-25,1,5,0,1113,5032
Calasiao,Bued,Karding,2022-09-25,0,0,0,1489,5896
Calasiao,Buenlag,Karding,2022-09-25,1,5,1,2211,8281
Calasiao,Cabilocaan,Karding,2022-09-25,0,0,0,775,2985
Calasiao,Dinalaoan,Karding,2022-09-25,0,0,0,958,4114
Calasiao,Doyong,Karding,2022-09-25,0,0,0,983,3957
Calasiao,Gabon,Karding,2022-09-25,0,0,0,666,3026
Calasiao,Lasip,Karding,2022-09-25,1,5,1,752,3398
Calasiao,Longos,Karding,2022-09-25,1,5,1,749,3006
Calasiao,Lumbang,Karding,2022-09-25,1,5,1,578,2379
Calasiao,Macabito,Karding,2022-09-25,0,0,0,992,4395
Calasiao,Malabago,Karding,2022-09-25,0,0,0,1031,4329
Calasiao,Mancup,Karding,2022-09-25,1,5,1,791,3621
Calasiao,Nagsaing,Karding,2022-09-25,0,0,0,1389,6060
Calasiao,Nalsian,Karding,2022-09-25,0,0,0,1734,6906
Calasiao,Poblacion East,Karding,2022-09-25,1,5,1,412,1671
Calasiao,Poblacion West,Karding,2022-09-25,0,0,0,240,883
Calasiao,Quesban,Karding,2022-09-25,0,0,0,825,3191
Calasiao,San Miguel,Karding,2022-09-25,0,0,0,1980,7747
Calasiao,San Vicente,Karding,2022-09-25,0,0,0,485,2107
Calasiao,Songkoy,Karding,2022-09-25,0,0,0,681,2848
Calasiao,Talibaew,Karding,2022-09-25,1,5,1,1181,4827
""",
    "maring_2021": _HEADER + """Calasiao,Ambonao,Maring,2021-10-11,528,2770,305,1566,6879
Calasiao,Ambuetel,Maring,2021-10-11,121,650,45,644,2933
Calasiao,Banaoang,Maring,2021-10-11,615,3301,460,1113,5032
Calasiao,Bued,Maring,2021-10-11,567,2734,305,1489,5896
Calasiao,Buenlag,Maring,2021-10-11,1173,5422,995,2211,8281
Calasiao,Cabilocaan,Maring,2021-10-11,229,1078,115,775,2985
Calasiao,Dinalaoan,Maring,2021-10-11,468,2408,355,958,4114
Calasiao,Doyong,Maring,2021-10-11,459,2242,310,983,3957
Calasiao,Gabon,Maring,2021-10-11,297,1598,205,666,3026
Calasiao,Lasip,Maring,2021-10-11,448,2403,405,752,3398
Calasiao,Longos,Maring,2021-10-11,479,2334,460,749,3006
Calasiao,Lumbang,Maring,2021-10-11,357,1776,305,578,2379
Calasiao,Macabito,Maring,2021-10-11,165,866,50,992,4395
Calasiao,Malabago,Maring,2021-10-11,437,2208,275,1031,4329
Calasiao,Mancup,Maring,2021-10-11,454,2462,405,791,3621
Calasiao,Nagsaing,Maring,2021-10-11,290,1508,115,1389,6060
Calasiao,Nalsian,Maring,2021-10-11,622,3016,380,1734,6906
Calasiao,Poblacion East,Maring,2021-10-11,211,1034,165,412,1671
Calasiao,Poblacion West,Maring,2021-10-11,61,275,25,240,883
Calasiao,Quesban,Maring,2021-10-11,261,1234,125,825,3191
Calasiao,San Miguel,Maring,2021-10-11,455,2174,160,1980,7747
Calasiao,San Vicente,Maring,2021-10-11,133,688,55,485,2107
Calasiao,Songkoy,Maring,2021-10-11,274,1380,170,681,2848
Calasiao,Talibaew,Maring,2021-10-11,780,3859,730,1181,4827
""",
    "fabian_habagat_2021": _HEADER + """Calasiao,Ambonao,Fabian + Habagat,2021-07-22,20,96,20,1566,6879
Calasiao,Ambuetel,Fabian + Habagat,2021-07-22,5,23,5,644,2933
Calasiao,Banaoang,Fabian + Habagat,2021-07-22,23,114,20,1113,5032
Calasiao,Bued,Fabian + Habagat,2021-07-22,21,95,20,1489,5896
Calasiao,Buenlag,Fabian + Habagat,2021-07-22,42,187,40,2211,8281
Calasiao,Cabilocaan,Fabian + Habagat,2021-07-22,9,38,5,775,2985
Calasiao,Dinalaoan,Fabian + Habagat,2021-07-22,17,83,15,958,4114
Calasiao,Doyong,Fabian + Habagat,2021-07-22,17,78,15,983,3957
Calasiao,Gabon,Fabian + Habagat,2021-07-22,11,55,10,666,3026
Calasiao,Lasip,Fabian + Habagat,2021-07-22,17,84,15,752,3398
Calasiao,Longos,Fabian + Habagat,2021-07-22,18,81,15,749,3006
Calasiao,Lumbang,Fabian + Habagat,2021-07-22,13,61,10,578,2379
Calasiao,Macabito,Fabian + Habagat,2021-07-22,7,31,5,992,4395
Calasiao,Malabago,Fabian + Habagat,2021-07-22,16,76,15,1031,4329
Calasiao,Mancup,Fabian + Habagat,2021-07-22,17,85,15,791,3621
Calasiao,Nagsaing,Fabian + Habagat,2021-07-22,11,52,10,1389,6060
Calasiao,Nalsian,Fabian + Habagat,2021-07-22,23,104,20,1734,6906
Calasiao,Poblacion East,Fabian + Habagat,2021-07-22,8,36,5,412,1671
Calasiao,Poblacion West,Fabian + Habagat,2021-07-22,3,10,0,240,883
Calasiao,Quesban,Fabian + Habagat,2021-07-22,10,43,10,825,3191
Calasiao,San Miguel,Fabian + Habagat,2021-07-22,17,76,15,1980,7747
Calasiao,San Vicente,Fabian + Habagat,2021-07-22,6,25,5,485,2107
Calasiao,Songkoy,Fabian + Habagat,2021-07-22,11,49,10,681,2848
Calasiao,Talibaew,Fabian + Habagat,2021-07-22,28,133,25,1181,4827
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
        good = len(rows) == 24 and len({normalize(r["barangay"]) for r in rows}) == 24
        ok &= good
        print(f"{rep['key']:<34} 24 brgy={good!s:<6} families={fam:>6,} packs={packs:>6,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Calasiao reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
