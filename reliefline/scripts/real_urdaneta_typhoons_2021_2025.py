"""
REAL records given to the team: Urdaneta City CSWDO per-barangay disaster
reports for 10 more typhoons, 2021-2026 - additional real data alongside the
four 2025 events already covered by scripts/real_urdaneta_reports_2025.py
(Dante/Emong, Mirasol/Nando, Paolo, Uwan - none of which overlap with these
10). All 10 are the clean tabulated CSV format (unlike that module's four
2025 events, which needed pack counts parsed from free-text Remarks - no
extraction needed here).

Three files are combined reports spanning more than one calendar typhoon:
  Nika + Ofel + Pepito   (Nov 2024) -> nika_2024, ofel_2024, pepito_2024
  Kristine + Leon        (Oct 2024) -> kristine_2024, leon_2024
  Fabian + Habagat       (Jul 2021) -> fabian_2021 ("Habagat" is enhanced
                                        monsoon alongside Fabian, not itself
                                        a named calendar typhoon)
  Enteng + Habagat       (Sep 2024) -> enteng_2024 (same habagat pattern)
One relief_events row per report, one relief_event_typhoons row per named
calendar typhoon it maps to (see scripts/apply_relief_schema.py) - frequency
and P(relief) are counted off the calendar/linkage independently, so a
combined report never needs (and the source data can't support) a per-storm
pack split.

Uses the same barangay-name normalize() as real_urdaneta_reports_2025.py
(imported, not re-derived) since the spelling variants are identical across
Urdaneta's own reports (Dilan-Paurido/Dilan Paurido, Pedro T. Orata/Dr. Pedro
T. Orata, Tiposu/Tipuso, Sta. Lucia/Santa Lucia).

Run this file to print a structural sanity check per report.
"""
import csv
import io

from real_urdaneta_reports_2025 import normalize  # noqa: F401 - re-exported for the loader

_FILES = {
    "maymay_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Maymay,2026-08-05,0,0,0,2232,9153
City of Urdaneta,Bactad East,Maymay,2026-08-05,0,0,0,741,3036
City of Urdaneta,Bayaoas,Maymay,2026-08-05,0,0,0,2282,9357
City of Urdaneta,Bolaoen,Maymay,2026-08-05,0,0,0,413,1693
City of Urdaneta,Cabaruan,Maymay,2026-08-05,0,0,0,328,1343
City of Urdaneta,Cabuloan,Maymay,2026-08-05,2,6,2,847,3474
City of Urdaneta,Camanang,Maymay,2026-08-05,0,0,0,1025,4204
City of Urdaneta,Camantiles,Maymay,2026-08-05,0,0,0,1118,4584
City of Urdaneta,Casantaan,Maymay,2026-08-05,0,0,0,652,2672
City of Urdaneta,Catablan,Maymay,2026-08-05,0,0,0,2496,10233
City of Urdaneta,Cayambanan,Maymay,2026-08-05,0,0,0,912,3737
City of Urdaneta,Consolacion,Maymay,2026-08-05,0,0,0,612,2511
City of Urdaneta,Dilan-Paurido,Maymay,2026-08-05,0,0,0,1973,8087
City of Urdaneta,Labit Proper,Maymay,2026-08-05,0,0,0,687,2817
City of Urdaneta,Labit West,Maymay,2026-08-05,0,0,0,1011,4146
City of Urdaneta,Mabanogbog,Maymay,2026-08-05,0,0,0,1150,4715
City of Urdaneta,Macalong,Maymay,2026-08-05,0,0,0,573,2350
City of Urdaneta,Nancalobasaan,Maymay,2026-08-05,0,0,0,1143,4686
City of Urdaneta,Nancamaliran East,Maymay,2026-08-05,0,0,0,687,2817
City of Urdaneta,Nancamaliran West,Maymay,2026-08-05,0,0,0,449,1839
City of Urdaneta,Nancayasan,Maymay,2026-08-05,1,3,1,1228,5036
City of Urdaneta,Oltama,Maymay,2026-08-05,0,0,0,199,818
City of Urdaneta,Palina East,Maymay,2026-08-05,0,0,0,844,3460
City of Urdaneta,Palina West,Maymay,2026-08-05,0,0,0,1253,5139
City of Urdaneta,Pedro T. Orata,Maymay,2026-08-05,0,0,0,513,2102
City of Urdaneta,Pinmaludpod,Maymay,2026-08-05,0,0,0,1802,7387
City of Urdaneta,Poblacion,Maymay,2026-08-05,0,0,0,972,3985
City of Urdaneta,San Jose,Maymay,2026-08-05,0,0,0,2318,9503
City of Urdaneta,San Vicente,Maymay,2026-08-05,0,0,0,1923,7883
City of Urdaneta,Santa Lucia,Maymay,2026-08-05,0,0,0,965,3956
City of Urdaneta,Santo Domingo,Maymay,2026-08-05,0,0,0,498,2044
City of Urdaneta,Sugcong,Maymay,2026-08-05,0,0,0,85,350
City of Urdaneta,Tiposu,Maymay,2026-08-05,0,0,0,481,1971
City of Urdaneta,Tulong,Maymay,2026-08-05,0,0,0,1182,4847
""",
    "ramil_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Ramil,2025-10-18,2,6,2,2232,9153
City of Urdaneta,Bactad East,Ramil,2025-10-18,1,4,1,741,3036
City of Urdaneta,Bayaoas,Ramil,2025-10-18,2,6,2,2282,9357
City of Urdaneta,Bolaoen,Ramil,2025-10-18,1,3,1,413,1693
City of Urdaneta,Cabaruan,Ramil,2025-10-18,0,0,0,328,1343
City of Urdaneta,Cabuloan,Ramil,2025-10-18,1,3,1,847,3474
City of Urdaneta,Camanang,Ramil,2025-10-18,2,6,1,1025,4204
City of Urdaneta,Camantiles,Ramil,2025-10-18,2,6,2,1118,4584
City of Urdaneta,Casantaan,Ramil,2025-10-18,1,3,1,652,2672
City of Urdaneta,Catablan,Ramil,2025-10-18,3,9,2,2496,10233
City of Urdaneta,Cayambanan,Ramil,2025-10-18,1,3,1,912,3737
City of Urdaneta,Consolacion,Ramil,2025-10-18,1,3,1,612,2511
City of Urdaneta,Dilan-Paurido,Ramil,2025-10-18,2,7,2,1973,8087
City of Urdaneta,Labit Proper,Ramil,2025-10-18,1,3,1,687,2817
City of Urdaneta,Labit West,Ramil,2025-10-18,1,3,1,1011,4146
City of Urdaneta,Mabanogbog,Ramil,2025-10-18,1,3,1,1150,4715
City of Urdaneta,Macalong,Ramil,2025-10-18,1,3,1,573,2350
City of Urdaneta,Nancalobasaan,Ramil,2025-10-18,1,3,1,1143,4686
City of Urdaneta,Nancamaliran East,Ramil,2025-10-18,1,3,1,687,2817
City of Urdaneta,Nancamaliran West,Ramil,2025-10-18,1,3,1,449,1839
City of Urdaneta,Nancayasan,Ramil,2025-10-18,1,3,1,1228,5036
City of Urdaneta,Oltama,Ramil,2025-10-18,0,0,0,199,818
City of Urdaneta,Palina East,Ramil,2025-10-18,1,3,1,844,3460
City of Urdaneta,Palina West,Ramil,2025-10-18,2,6,2,1253,5139
City of Urdaneta,Pedro T. Orata,Ramil,2025-10-18,1,3,1,513,2102
City of Urdaneta,Pinmaludpod,Ramil,2025-10-18,3,11,3,1802,7387
City of Urdaneta,Poblacion,Ramil,2025-10-18,1,3,1,972,3985
City of Urdaneta,San Jose,Ramil,2025-10-18,3,9,2,2318,9503
City of Urdaneta,San Vicente,Ramil,2025-10-18,2,6,1,1923,7883
City of Urdaneta,Santa Lucia,Ramil,2025-10-18,1,3,1,965,3956
City of Urdaneta,Santo Domingo,Ramil,2025-10-18,1,3,1,498,2044
City of Urdaneta,Sugcong,Ramil,2025-10-18,0,0,0,85,350
City of Urdaneta,Tiposu,Ramil,2025-10-18,0,0,0,481,1971
City of Urdaneta,Tulong,Ramil,2025-10-18,2,6,2,1182,4847
""",
    "nika_ofel_pepito_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Nika + Ofel + Pepito,2024-11-16,6,23,5,2232,9153
City of Urdaneta,Bactad East,Nika + Ofel + Pepito,2024-11-16,2,8,2,741,3036
City of Urdaneta,Bayaoas,Nika + Ofel + Pepito,2024-11-16,6,23,5,2282,9357
City of Urdaneta,Bolaoen,Nika + Ofel + Pepito,2024-11-16,1,4,1,413,1693
City of Urdaneta,Cabaruan,Nika + Ofel + Pepito,2024-11-16,1,3,1,328,1343
City of Urdaneta,Cabuloan,Nika + Ofel + Pepito,2024-11-16,2,9,2,847,3474
City of Urdaneta,Camanang,Nika + Ofel + Pepito,2024-11-16,3,10,2,1025,4204
City of Urdaneta,Camantiles,Nika + Ofel + Pepito,2024-11-16,3,11,3,1118,4584
City of Urdaneta,Casantaan,Nika + Ofel + Pepito,2024-11-16,2,7,1,652,2672
City of Urdaneta,Catablan,Nika + Ofel + Pepito,2024-11-16,7,25,5,2496,10233
City of Urdaneta,Cayambanan,Nika + Ofel + Pepito,2024-11-16,3,9,3,912,3737
City of Urdaneta,Consolacion,Nika + Ofel + Pepito,2024-11-16,2,6,1,612,2511
City of Urdaneta,Dilan-Paurido,Nika + Ofel + Pepito,2024-11-16,6,20,4,1973,8087
City of Urdaneta,Labit Proper,Nika + Ofel + Pepito,2024-11-16,2,7,2,687,2817
City of Urdaneta,Labit West,Nika + Ofel + Pepito,2024-11-16,3,10,2,1011,4146
City of Urdaneta,Mabanogbog,Nika + Ofel + Pepito,2024-11-16,3,12,2,1150,4715
City of Urdaneta,Macalong,Nika + Ofel + Pepito,2024-11-16,2,6,2,573,2350
City of Urdaneta,Nancalobasaan,Nika + Ofel + Pepito,2024-11-16,3,12,3,1143,4686
City of Urdaneta,Nancamaliran East,Nika + Ofel + Pepito,2024-11-16,2,7,1,687,2817
City of Urdaneta,Nancamaliran West,Nika + Ofel + Pepito,2024-11-16,1,5,1,449,1839
City of Urdaneta,Nancayasan,Nika + Ofel + Pepito,2024-11-16,4,13,3,1228,5036
City of Urdaneta,Oltama,Nika + Ofel + Pepito,2024-11-16,1,2,1,199,818
City of Urdaneta,Palina East,Nika + Ofel + Pepito,2024-11-16,2,9,2,844,3460
City of Urdaneta,Palina West,Nika + Ofel + Pepito,2024-11-16,4,13,4,1253,5139
City of Urdaneta,Pedro T. Orata,Nika + Ofel + Pepito,2024-11-16,1,5,1,513,2102
City of Urdaneta,Pinmaludpod,Nika + Ofel + Pepito,2024-11-16,5,18,3,1802,7387
City of Urdaneta,Poblacion,Nika + Ofel + Pepito,2024-11-16,3,10,3,972,3985
City of Urdaneta,San Jose,Nika + Ofel + Pepito,2024-11-16,7,24,6,2318,9503
City of Urdaneta,San Vicente,Nika + Ofel + Pepito,2024-11-16,5,20,4,1923,7883
City of Urdaneta,Santa Lucia,Nika + Ofel + Pepito,2024-11-16,3,10,3,965,3956
City of Urdaneta,Santo Domingo,Nika + Ofel + Pepito,2024-11-16,1,5,1,498,2044
City of Urdaneta,Sugcong,Nika + Ofel + Pepito,2024-11-16,0,1,0,85,350
City of Urdaneta,Tiposu,Nika + Ofel + Pepito,2024-11-16,1,5,1,481,1971
City of Urdaneta,Tulong,Nika + Ofel + Pepito,2024-11-16,3,12,2,1182,4847
""",
    "kristine_leon_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Kristine + Leon,2024-10-24,0,1,0,2232,9153
City of Urdaneta,Bactad East,Kristine + Leon,2024-10-24,0,0,0,741,3036
City of Urdaneta,Bayaoas,Kristine + Leon,2024-10-24,0,1,0,2282,9357
City of Urdaneta,Bolaoen,Kristine + Leon,2024-10-24,0,0,0,413,1693
City of Urdaneta,Cabaruan,Kristine + Leon,2024-10-24,0,0,0,328,1343
City of Urdaneta,Cabuloan,Kristine + Leon,2024-10-24,0,0,0,847,3474
City of Urdaneta,Camanang,Kristine + Leon,2024-10-24,0,0,0,1025,4204
City of Urdaneta,Camantiles,Kristine + Leon,2024-10-24,0,0,0,1118,4584
City of Urdaneta,Casantaan,Kristine + Leon,2024-10-24,0,0,0,652,2672
City of Urdaneta,Catablan,Kristine + Leon,2024-10-24,1,1,1,2496,10233
City of Urdaneta,Cayambanan,Kristine + Leon,2024-10-24,0,0,0,912,3737
City of Urdaneta,Consolacion,Kristine + Leon,2024-10-24,0,0,0,612,2511
City of Urdaneta,Dilan-Paurido,Kristine + Leon,2024-10-24,0,1,0,1973,8087
City of Urdaneta,Labit Proper,Kristine + Leon,2024-10-24,0,0,0,687,2817
City of Urdaneta,Labit West,Kristine + Leon,2024-10-24,0,0,0,1011,4146
City of Urdaneta,Mabanogbog,Kristine + Leon,2024-10-24,0,0,0,1150,4715
City of Urdaneta,Macalong,Kristine + Leon,2024-10-24,0,0,0,573,2350
City of Urdaneta,Nancalobasaan,Kristine + Leon,2024-10-24,0,0,0,1143,4686
City of Urdaneta,Nancamaliran East,Kristine + Leon,2024-10-24,0,0,0,687,2817
City of Urdaneta,Nancamaliran West,Kristine + Leon,2024-10-24,0,0,0,449,1839
City of Urdaneta,Nancayasan,Kristine + Leon,2024-10-24,0,0,0,1228,5036
City of Urdaneta,Oltama,Kristine + Leon,2024-10-24,0,0,0,199,818
City of Urdaneta,Palina East,Kristine + Leon,2024-10-24,0,0,0,844,3460
City of Urdaneta,Palina West,Kristine + Leon,2024-10-24,0,0,0,1253,5139
City of Urdaneta,Pedro T. Orata,Kristine + Leon,2024-10-24,0,0,0,513,2102
City of Urdaneta,Pinmaludpod,Kristine + Leon,2024-10-24,0,0,0,1802,7387
City of Urdaneta,Poblacion,Kristine + Leon,2024-10-24,0,0,0,972,3985
City of Urdaneta,San Jose,Kristine + Leon,2024-10-24,1,1,1,2318,9503
City of Urdaneta,San Vicente,Kristine + Leon,2024-10-24,0,1,0,1923,7883
City of Urdaneta,Santa Lucia,Kristine + Leon,2024-10-24,0,0,0,965,3956
City of Urdaneta,Santo Domingo,Kristine + Leon,2024-10-24,0,0,0,498,2044
City of Urdaneta,Sugcong,Kristine + Leon,2024-10-24,0,0,0,85,350
City of Urdaneta,Tiposu,Kristine + Leon,2024-10-24,0,0,0,481,1971
City of Urdaneta,Tulong,Kristine + Leon,2024-10-24,0,0,0,1182,4847
""",
    "enteng_habagat_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Enteng + Habagat,2024-09-05,4,13,4,2232,9153
City of Urdaneta,Bactad East,Enteng + Habagat,2024-09-05,1,3,1,741,3036
City of Urdaneta,Bayaoas,Enteng + Habagat,2024-09-05,5,18,4,2282,9357
City of Urdaneta,Bolaoen,Enteng + Habagat,2024-09-05,1,3,1,413,1693
City of Urdaneta,Cabaruan,Enteng + Habagat,2024-09-05,1,3,1,328,1343
City of Urdaneta,Cabuloan,Enteng + Habagat,2024-09-05,1,3,1,847,3474
City of Urdaneta,Camanang,Enteng + Habagat,2024-09-05,2,6,1,1025,4204
City of Urdaneta,Camantiles,Enteng + Habagat,2024-09-05,1,3,1,1118,4584
City of Urdaneta,Casantaan,Enteng + Habagat,2024-09-05,1,3,1,652,2672
City of Urdaneta,Catablan,Enteng + Habagat,2024-09-05,5,16,4,2496,10233
City of Urdaneta,Cayambanan,Enteng + Habagat,2024-09-05,1,3,1,912,3737
City of Urdaneta,Consolacion,Enteng + Habagat,2024-09-05,1,3,1,612,2511
City of Urdaneta,Dilan-Paurido,Enteng + Habagat,2024-09-05,4,14,4,1973,8087
City of Urdaneta,Labit Proper,Enteng + Habagat,2024-09-05,1,3,1,687,2817
City of Urdaneta,Labit West,Enteng + Habagat,2024-09-05,2,6,2,1011,4146
City of Urdaneta,Mabanogbog,Enteng + Habagat,2024-09-05,2,7,1,1150,4715
City of Urdaneta,Macalong,Enteng + Habagat,2024-09-05,1,4,1,573,2350
City of Urdaneta,Nancalobasaan,Enteng + Habagat,2024-09-05,2,7,1,1143,4686
City of Urdaneta,Nancamaliran East,Enteng + Habagat,2024-09-05,1,3,1,687,2817
City of Urdaneta,Nancamaliran West,Enteng + Habagat,2024-09-05,1,3,1,449,1839
City of Urdaneta,Nancayasan,Enteng + Habagat,2024-09-05,2,7,2,1228,5036
City of Urdaneta,Oltama,Enteng + Habagat,2024-09-05,0,0,0,199,818
City of Urdaneta,Palina East,Enteng + Habagat,2024-09-05,2,7,1,844,3460
City of Urdaneta,Palina West,Enteng + Habagat,2024-09-05,2,7,2,1253,5139
City of Urdaneta,Pedro T. Orata,Enteng + Habagat,2024-09-05,1,4,1,513,2102
City of Urdaneta,Pinmaludpod,Enteng + Habagat,2024-09-05,3,10,3,1802,7387
City of Urdaneta,Poblacion,Enteng + Habagat,2024-09-05,1,3,1,972,3985
City of Urdaneta,San Jose,Enteng + Habagat,2024-09-05,5,15,3,2318,9503
City of Urdaneta,San Vicente,Enteng + Habagat,2024-09-05,3,8,3,1923,7883
City of Urdaneta,Santa Lucia,Enteng + Habagat,2024-09-05,1,3,1,965,3956
City of Urdaneta,Santo Domingo,Enteng + Habagat,2024-09-05,1,3,1,498,2044
City of Urdaneta,Sugcong,Enteng + Habagat,2024-09-05,0,0,0,85,350
City of Urdaneta,Tiposu,Enteng + Habagat,2024-09-05,1,3,1,481,1971
City of Urdaneta,Tulong,Enteng + Habagat,2024-09-05,2,6,1,1182,4847
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Egay,2023-07-26,46,219,29,2212,9068
City of Urdaneta,Bactad East,Egay,2023-07-26,15,73,14,734,3008
City of Urdaneta,Bayaoas,Egay,2023-07-26,47,224,43,2261,9270
City of Urdaneta,Bolaoen,Egay,2023-07-26,9,40,6,409,1678
City of Urdaneta,Cabaruan,Egay,2023-07-26,7,32,6,324,1331
City of Urdaneta,Cabuloan,Egay,2023-07-26,18,83,15,839,3442
City of Urdaneta,Camanang,Egay,2023-07-26,21,101,15,1016,4165
City of Urdaneta,Camantiles,Egay,2023-07-26,23,110,22,1108,4541
City of Urdaneta,Casantaan,Egay,2023-07-26,14,64,11,645,2647
City of Urdaneta,Catablan,Egay,2023-07-26,52,245,36,2473,10138
City of Urdaneta,Cayambanan,Egay,2023-07-26,19,89,15,903,3702
City of Urdaneta,Consolacion,Egay,2023-07-26,13,60,12,607,2487
City of Urdaneta,Dilan-Paurido,Egay,2023-07-26,41,193,28,1954,8012
City of Urdaneta,Labit Proper,Egay,2023-07-26,14,67,10,681,2791
City of Urdaneta,Labit West,Egay,2023-07-26,21,99,21,1002,4107
City of Urdaneta,Mabanogbog,Egay,2023-07-26,24,113,21,1139,4671
City of Urdaneta,Macalong,Egay,2023-07-26,12,56,9,568,2328
City of Urdaneta,Nancalobasaan,Egay,2023-07-26,24,112,19,1132,4642
City of Urdaneta,Nancamaliran East,Egay,2023-07-26,14,67,9,681,2791
City of Urdaneta,Nancamaliran West,Egay,2023-07-26,9,44,6,444,1822
City of Urdaneta,Nancayasan,Egay,2023-07-26,25,120,18,1217,4989
City of Urdaneta,Oltama,Egay,2023-07-26,4,20,3,197,810
City of Urdaneta,Palina East,Egay,2023-07-26,17,83,12,836,3428
City of Urdaneta,Palina West,Egay,2023-07-26,26,123,18,1242,5091
City of Urdaneta,Pedro T. Orata,Egay,2023-07-26,11,50,7,508,2083
City of Urdaneta,Pinmaludpod,Egay,2023-07-26,37,177,32,1785,7318
City of Urdaneta,Poblacion,Egay,2023-07-26,20,95,14,963,3948
City of Urdaneta,San Jose,Egay,2023-07-26,48,227,46,2296,9415
City of Urdaneta,San Vicente,Egay,2023-07-26,40,189,38,1905,7810
City of Urdaneta,Santa Lucia,Egay,2023-07-26,20,95,13,956,3919
City of Urdaneta,Santo Domingo,Egay,2023-07-26,10,49,7,494,2025
City of Urdaneta,Sugcong,Egay,2023-07-26,2,8,2,85,347
City of Urdaneta,Tiposu,Egay,2023-07-26,10,47,7,476,1952
City of Urdaneta,Tulong,Egay,2023-07-26,25,116,16,1171,4801
""",
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Karding,2022-09-25,0,1,0,2212,9068
City of Urdaneta,Bactad East,Karding,2022-09-25,0,0,0,734,3008
City of Urdaneta,Bayaoas,Karding,2022-09-25,0,1,0,2261,9270
City of Urdaneta,Bolaoen,Karding,2022-09-25,0,0,0,409,1678
City of Urdaneta,Cabaruan,Karding,2022-09-25,0,0,0,324,1331
City of Urdaneta,Cabuloan,Karding,2022-09-25,0,0,0,839,3442
City of Urdaneta,Camanang,Karding,2022-09-25,0,0,0,1016,4165
City of Urdaneta,Camantiles,Karding,2022-09-25,0,0,0,1108,4541
City of Urdaneta,Casantaan,Karding,2022-09-25,0,0,0,645,2647
City of Urdaneta,Catablan,Karding,2022-09-25,1,1,1,2473,10138
City of Urdaneta,Cayambanan,Karding,2022-09-25,0,0,0,903,3702
City of Urdaneta,Consolacion,Karding,2022-09-25,0,0,0,607,2487
City of Urdaneta,Dilan-Paurido,Karding,2022-09-25,0,1,0,1954,8012
City of Urdaneta,Labit Proper,Karding,2022-09-25,0,0,0,681,2791
City of Urdaneta,Labit West,Karding,2022-09-25,0,0,0,1002,4107
City of Urdaneta,Mabanogbog,Karding,2022-09-25,0,0,0,1139,4671
City of Urdaneta,Macalong,Karding,2022-09-25,0,0,0,568,2328
City of Urdaneta,Nancalobasaan,Karding,2022-09-25,0,0,0,1132,4642
City of Urdaneta,Nancamaliran East,Karding,2022-09-25,0,0,0,681,2791
City of Urdaneta,Nancamaliran West,Karding,2022-09-25,0,0,0,444,1822
City of Urdaneta,Nancayasan,Karding,2022-09-25,0,0,0,1217,4989
City of Urdaneta,Oltama,Karding,2022-09-25,0,0,0,197,810
City of Urdaneta,Palina East,Karding,2022-09-25,0,0,0,836,3428
City of Urdaneta,Palina West,Karding,2022-09-25,0,0,0,1242,5091
City of Urdaneta,Pedro T. Orata,Karding,2022-09-25,0,0,0,508,2083
City of Urdaneta,Pinmaludpod,Karding,2022-09-25,0,1,0,1785,7318
City of Urdaneta,Poblacion,Karding,2022-09-25,0,0,0,963,3948
City of Urdaneta,San Jose,Karding,2022-09-25,1,1,1,2296,9415
City of Urdaneta,San Vicente,Karding,2022-09-25,0,1,0,1905,7810
City of Urdaneta,Santa Lucia,Karding,2022-09-25,0,0,0,956,3919
City of Urdaneta,Santo Domingo,Karding,2022-09-25,0,0,0,494,2025
City of Urdaneta,Sugcong,Karding,2022-09-25,0,0,0,85,347
City of Urdaneta,Tiposu,Karding,2022-09-25,0,0,0,476,1952
City of Urdaneta,Tulong,Karding,2022-09-25,0,0,0,1171,4801
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Paeng,2022-10-29,0,0,0,2212,9068
City of Urdaneta,Bactad East,Paeng,2022-10-29,0,0,0,734,3008
City of Urdaneta,Bayaoas,Paeng,2022-10-29,0,0,0,2261,9270
City of Urdaneta,Bolaoen,Paeng,2022-10-29,0,0,0,409,1678
City of Urdaneta,Cabaruan,Paeng,2022-10-29,0,0,0,324,1331
City of Urdaneta,Cabuloan,Paeng,2022-10-29,0,0,0,839,3442
City of Urdaneta,Camanang,Paeng,2022-10-29,0,0,0,1016,4165
City of Urdaneta,Camantiles,Paeng,2022-10-29,0,0,0,1108,4541
City of Urdaneta,Casantaan,Paeng,2022-10-29,0,0,0,645,2647
City of Urdaneta,Catablan,Paeng,2022-10-29,1,1,1,2473,10138
City of Urdaneta,Cayambanan,Paeng,2022-10-29,0,0,0,903,3702
City of Urdaneta,Consolacion,Paeng,2022-10-29,0,0,0,607,2487
City of Urdaneta,Dilan-Paurido,Paeng,2022-10-29,0,0,0,1954,8012
City of Urdaneta,Labit Proper,Paeng,2022-10-29,0,0,0,681,2791
City of Urdaneta,Labit West,Paeng,2022-10-29,0,0,0,1002,4107
City of Urdaneta,Mabanogbog,Paeng,2022-10-29,0,0,0,1139,4671
City of Urdaneta,Macalong,Paeng,2022-10-29,0,0,0,568,2328
City of Urdaneta,Nancalobasaan,Paeng,2022-10-29,0,0,0,1132,4642
City of Urdaneta,Nancamaliran East,Paeng,2022-10-29,0,0,0,681,2791
City of Urdaneta,Nancamaliran West,Paeng,2022-10-29,0,0,0,444,1822
City of Urdaneta,Nancayasan,Paeng,2022-10-29,0,0,0,1217,4989
City of Urdaneta,Oltama,Paeng,2022-10-29,0,0,0,197,810
City of Urdaneta,Palina East,Paeng,2022-10-29,0,0,0,836,3428
City of Urdaneta,Palina West,Paeng,2022-10-29,0,0,0,1242,5091
City of Urdaneta,Pedro T. Orata,Paeng,2022-10-29,0,0,0,508,2083
City of Urdaneta,Pinmaludpod,Paeng,2022-10-29,0,0,0,1785,7318
City of Urdaneta,Poblacion,Paeng,2022-10-29,0,0,0,963,3948
City of Urdaneta,San Jose,Paeng,2022-10-29,0,1,0,2296,9415
City of Urdaneta,San Vicente,Paeng,2022-10-29,0,0,0,1905,7810
City of Urdaneta,Santa Lucia,Paeng,2022-10-29,0,0,0,956,3919
City of Urdaneta,Santo Domingo,Paeng,2022-10-29,0,0,0,494,2025
City of Urdaneta,Sugcong,Paeng,2022-10-29,0,0,0,85,347
City of Urdaneta,Tiposu,Paeng,2022-10-29,0,0,0,476,1952
City of Urdaneta,Tulong,Paeng,2022-10-29,0,0,0,1171,4801
""",
    "fabian_habagat_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Fabian + Habagat,2021-07-23,6,29,5,2212,9068
City of Urdaneta,Bactad East,Fabian + Habagat,2021-07-23,0,0,0,734,3008
City of Urdaneta,Bayaoas,Fabian + Habagat,2021-07-23,6,30,4,2261,9270
City of Urdaneta,Bolaoen,Fabian + Habagat,2021-07-23,0,0,0,409,1678
City of Urdaneta,Cabaruan,Fabian + Habagat,2021-07-23,0,0,0,324,1331
City of Urdaneta,Cabuloan,Fabian + Habagat,2021-07-23,0,0,0,839,3442
City of Urdaneta,Camanang,Fabian + Habagat,2021-07-23,0,0,0,1016,4165
City of Urdaneta,Camantiles,Fabian + Habagat,2021-07-23,0,0,0,1108,4541
City of Urdaneta,Casantaan,Fabian + Habagat,2021-07-23,0,0,0,645,2647
City of Urdaneta,Catablan,Fabian + Habagat,2021-07-23,7,33,4,2473,10138
City of Urdaneta,Cayambanan,Fabian + Habagat,2021-07-23,0,0,0,903,3702
City of Urdaneta,Consolacion,Fabian + Habagat,2021-07-23,0,0,0,607,2487
City of Urdaneta,Dilan-Paurido,Fabian + Habagat,2021-07-23,6,26,4,1954,8012
City of Urdaneta,Labit Proper,Fabian + Habagat,2021-07-23,0,0,0,681,2791
City of Urdaneta,Labit West,Fabian + Habagat,2021-07-23,0,0,0,1002,4107
City of Urdaneta,Mabanogbog,Fabian + Habagat,2021-07-23,0,0,0,1139,4671
City of Urdaneta,Macalong,Fabian + Habagat,2021-07-23,0,0,0,568,2328
City of Urdaneta,Nancalobasaan,Fabian + Habagat,2021-07-23,0,0,0,1132,4642
City of Urdaneta,Nancamaliran East,Fabian + Habagat,2021-07-23,0,0,0,681,2791
City of Urdaneta,Nancamaliran West,Fabian + Habagat,2021-07-23,0,0,0,444,1822
City of Urdaneta,Nancayasan,Fabian + Habagat,2021-07-23,0,0,0,1217,4989
City of Urdaneta,Oltama,Fabian + Habagat,2021-07-23,0,0,0,197,810
City of Urdaneta,Palina East,Fabian + Habagat,2021-07-23,0,0,0,836,3428
City of Urdaneta,Palina West,Fabian + Habagat,2021-07-23,4,16,3,1242,5091
City of Urdaneta,Pedro T. Orata,Fabian + Habagat,2021-07-23,0,0,0,508,2083
City of Urdaneta,Pinmaludpod,Fabian + Habagat,2021-07-23,5,24,4,1785,7318
City of Urdaneta,Poblacion,Fabian + Habagat,2021-07-23,0,0,0,963,3948
City of Urdaneta,San Jose,Fabian + Habagat,2021-07-23,6,30,4,2296,9415
City of Urdaneta,San Vicente,Fabian + Habagat,2021-07-23,5,25,5,1905,7810
City of Urdaneta,Santa Lucia,Fabian + Habagat,2021-07-23,0,0,0,956,3919
City of Urdaneta,Santo Domingo,Fabian + Habagat,2021-07-23,0,0,0,494,2025
City of Urdaneta,Sugcong,Fabian + Habagat,2021-07-23,0,0,0,85,347
City of Urdaneta,Tiposu,Fabian + Habagat,2021-07-23,0,0,0,476,1952
City of Urdaneta,Tulong,Fabian + Habagat,2021-07-23,0,0,0,1171,4801
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
City of Urdaneta,Anonas,Maring,2021-10-11,0,0,0,2212,9068
City of Urdaneta,Bactad East,Maring,2021-10-11,0,0,0,734,3008
City of Urdaneta,Bayaoas,Maring,2021-10-11,0,0,0,2261,9270
City of Urdaneta,Bolaoen,Maring,2021-10-11,0,0,0,409,1678
City of Urdaneta,Cabaruan,Maring,2021-10-11,0,0,0,324,1331
City of Urdaneta,Cabuloan,Maring,2021-10-11,0,0,0,839,3442
City of Urdaneta,Camanang,Maring,2021-10-11,0,0,0,1016,4165
City of Urdaneta,Camantiles,Maring,2021-10-11,0,0,0,1108,4541
City of Urdaneta,Casantaan,Maring,2021-10-11,0,0,0,645,2647
City of Urdaneta,Catablan,Maring,2021-10-11,1,3,1,2473,10138
City of Urdaneta,Cayambanan,Maring,2021-10-11,0,0,0,903,3702
City of Urdaneta,Consolacion,Maring,2021-10-11,0,0,0,607,2487
City of Urdaneta,Dilan-Paurido,Maring,2021-10-11,0,0,0,1954,8012
City of Urdaneta,Labit Proper,Maring,2021-10-11,0,0,0,681,2791
City of Urdaneta,Labit West,Maring,2021-10-11,0,0,0,1002,4107
City of Urdaneta,Mabanogbog,Maring,2021-10-11,0,0,0,1139,4671
City of Urdaneta,Macalong,Maring,2021-10-11,0,0,0,568,2328
City of Urdaneta,Nancalobasaan,Maring,2021-10-11,0,0,0,1132,4642
City of Urdaneta,Nancamaliran East,Maring,2021-10-11,0,0,0,681,2791
City of Urdaneta,Nancamaliran West,Maring,2021-10-11,0,0,0,444,1822
City of Urdaneta,Nancayasan,Maring,2021-10-11,0,0,0,1217,4989
City of Urdaneta,Oltama,Maring,2021-10-11,0,0,0,197,810
City of Urdaneta,Palina East,Maring,2021-10-11,0,0,0,836,3428
City of Urdaneta,Palina West,Maring,2021-10-11,0,0,0,1242,5091
City of Urdaneta,Pedro T. Orata,Maring,2021-10-11,0,0,0,508,2083
City of Urdaneta,Pinmaludpod,Maring,2021-10-11,0,0,0,1785,7318
City of Urdaneta,Poblacion,Maring,2021-10-11,0,0,0,963,3948
City of Urdaneta,San Jose,Maring,2021-10-11,1,3,1,2296,9415
City of Urdaneta,San Vicente,Maring,2021-10-11,0,0,0,1905,7810
City of Urdaneta,Santa Lucia,Maring,2021-10-11,0,0,0,956,3919
City of Urdaneta,Santo Domingo,Maring,2021-10-11,0,0,0,494,2025
City of Urdaneta,Sugcong,Maring,2021-10-11,0,0,0,85,347
City of Urdaneta,Tiposu,Maring,2021-10-11,0,0,0,476,1952
City of Urdaneta,Tulong,Maring,2021-10-11,0,0,0,1171,4801
""",
}

# typhoon_key(s) matching scripts/typhoon_calendar_2021_2026.py
_TYPHOON_KEYS = {
    "maymay_2026": ["maymay_2026"],
    "ramil_2025": ["ramil_2025"],
    "nika_ofel_pepito_2024": ["nika_2024", "ofel_2024", "pepito_2024"],
    "kristine_leon_2024": ["kristine_2024", "leon_2024"],
    "enteng_habagat_2024": ["enteng_2024"],
    "egay_2023": ["egay_2023"],
    "karding_2022": ["karding_2022"],
    "paeng_2022": ["paeng_2022"],
    "fabian_habagat_2021": ["fabian_2021"],
    "maring_2021": ["maring_2021"],
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
        good = len(rows) == 34
        ok &= good
        print(f"{rep['key']:<24} 34 brgy={len(rows) == 34!s:<6} families={fam:>5,} packs={packs:>5,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print("\nAll 10 Urdaneta reports structurally OK." if ok else "\nMISMATCH - recheck transcription.")
