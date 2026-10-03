"""
REAL records given to the team: Calasiao per-barangay disaster reports for 14
typhoon reports, 2021-2026, all 24 barangays per file, in the same clean
tabulated CSV format as Urdaneta's (updated dataset delivered 2026-10-03).

This dataset REPLACES the previous Calasiao sources entirely (decided
2026-10-03):
  * the old 25-typhoon version of this module - its figures were on a very
    different scale (every barangay affected in nearly every storm, e.g.
    Maymay 2026 5,489 packs vs 5 here; Kristine 2024 9,316 vs 1), and 13 of
    its typhoons (Kiyapo, Gardo, Ester, Marce, Butchoy, Goring, Falcon,
    Dodong, Neneng, Florita, Kiko, Jolina, Fabian) are not in the updated
    set, so they were dropped rather than mixed with the new scale;
  * real_calasiao_reports_2025.py - Crising/Emong (packs had been ESTIMATED
    from a packs-per-family ratio) and Nando/Opong (packs summed from the
    report's assistance tables, 19 of 24 barangays). The updated dataset
    gives both with real Food Packs Given and population columns.

Combined reports spanning more than one calendar typhoon:
  Crising & Emong (Jul 2025) -> crising_2025, emong_2025
  Nando & Opong   (Sep 2025) -> nando_2025 (Opong is not in
                                 scripts/typhoon_calendar_2021_2026.py)

Data-quality notes kept from the source (not corrected - figures are as given):
  * Crising & Emong: several barangays got roughly 2 packs per affected
    family (e.g. Mancup 2,600 packs / 1,300 families, Poblacion West 900 /
    450) - plausibly two distributions (one per storm); kept as reported.
  * Crising & Emong / Nando & Opong: some "Total Number of Families" differ
    between the two 2025 reports for the same barangay (e.g. Banaoang 1,220
    vs 2,200, Bued 1,500 vs 1,421) - kept as each report's own snapshot.

Run this file to print a structural sanity check per report.
"""
import csv
import io

from _barangay_names import strip_accents_and_punct


def normalize(name):
    """Older Calasiao sheets spell 'Cabiloocan'; the barangays table spells
    it 'Cabilocaan'."""
    s = strip_accents_and_punct(name)
    return {"cabiloocan": "cabilocaan"}.get(s, s)


_FILES = {
    "maymay_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Maymay,2026-08-06,0,0,0,1739,7131
Calasiao,Ambuetel,Maymay,2026-08-06,0,0,0,752,3081
Calasiao,Banaoang,Maymay,2026-08-06,0,0,0,1241,5088
Calasiao,Bued,Maymay,2026-08-06,0,0,0,1441,5908
Calasiao,Buenlag,Maymay,2026-08-06,0,0,0,2001,8206
Calasiao,Cabilocaan,Maymay,2026-08-06,0,0,0,796,3262
Calasiao,Dinalaoan,Maymay,2026-08-06,0,0,0,1016,4167
Calasiao,Doyong,Maymay,2026-08-06,0,0,0,988,4052
Calasiao,Gabon,Maymay,2026-08-06,0,0,0,679,2782
Calasiao,Lasip,Maymay,2026-08-06,2,7,2,766,3139
Calasiao,Longos,Maymay,2026-08-06,0,0,0,756,3101
Calasiao,Lumbang,Maymay,2026-08-06,0,0,0,679,2784
Calasiao,Macabito,Maymay,2026-08-06,0,0,0,1096,4494
Calasiao,Malabago,Maymay,2026-08-06,0,0,0,1092,4477
Calasiao,Mancup,Maymay,2026-08-06,3,11,3,925,3793
Calasiao,Nagsaing,Maymay,2026-08-06,0,0,0,1480,6066
Calasiao,Nalsian,Maymay,2026-08-06,0,0,0,1513,6203
Calasiao,Poblacion East,Maymay,2026-08-06,0,0,0,412,1691
Calasiao,Poblacion West,Maymay,2026-08-06,0,0,0,123,506
Calasiao,Quesban,Maymay,2026-08-06,0,0,0,782,3205
Calasiao,San Miguel,Maymay,2026-08-06,0,0,0,1924,7890
Calasiao,San Vicente,Maymay,2026-08-06,0,0,0,518,2122
Calasiao,Songkoy,Maymay,2026-08-06,0,0,0,732,3001
Calasiao,Talibaew,Maymay,2026-08-06,0,0,0,1152,4722
""",
    "nando_opong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Nando & Opong,2025-09-22,0,0,0,1695,7046
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
    "crising_emong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Crising & Emong,2025-07-18,1030,5162,1030,1695,7046
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
    "pepito_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Pepito,2024-11-16,0,0,0,1719,7046
Calasiao,Ambuetel,Pepito,2024-11-16,7,26,7,739,3031
Calasiao,Banaoang,Pepito,2024-11-16,8,29,7,1236,5069
Calasiao,Bued,Pepito,2024-11-16,10,36,8,1440,5904
Calasiao,Buenlag,Pepito,2024-11-16,0,0,0,2008,8231
Calasiao,Cabilocaan,Pepito,2024-11-16,0,0,0,772,3167
Calasiao,Dinalaoan,Pepito,2024-11-16,0,0,0,1012,4149
Calasiao,Doyong,Pepito,2024-11-16,0,0,0,980,4020
Calasiao,Gabon,Pepito,2024-11-16,0,0,0,698,2861
Calasiao,Lasip,Pepito,2024-11-16,0,0,0,786,3223
Calasiao,Longos,Pepito,2024-11-16,0,0,0,749,3069
Calasiao,Lumbang,Pepito,2024-11-16,0,0,0,644,2642
Calasiao,Macabito,Pepito,2024-11-16,0,0,0,1088,4461
Calasiao,Malabago,Pepito,2024-11-16,8,29,6,1080,4427
Calasiao,Mancup,Pepito,2024-11-16,0,0,0,911,3735
Calasiao,Nagsaing,Pepito,2024-11-16,0,0,0,1479,6064
Calasiao,Nalsian,Pepito,2024-11-16,0,0,0,1568,6429
Calasiao,Poblacion East,Pepito,2024-11-16,0,0,0,411,1684
Calasiao,Poblacion West,Pepito,2024-11-16,0,0,0,149,609
Calasiao,Quesban,Pepito,2024-11-16,0,0,0,780,3200
Calasiao,San Miguel,Pepito,2024-11-16,0,0,0,1913,7842
Calasiao,San Vicente,Pepito,2024-11-16,0,0,0,516,2117
Calasiao,Songkoy,Pepito,2024-11-16,0,0,0,719,2949
Calasiao,Talibaew,Pepito,2024-11-16,12,44,11,1160,4757
""",
    "ofel_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Ofel,2024-11-14,0,0,0,1719,7046
Calasiao,Ambuetel,Ofel,2024-11-14,0,0,0,739,3031
Calasiao,Banaoang,Ofel,2024-11-14,0,0,0,1236,5069
Calasiao,Bued,Ofel,2024-11-14,7,25,7,1440,5904
Calasiao,Buenlag,Ofel,2024-11-14,0,0,0,2008,8231
Calasiao,Cabilocaan,Ofel,2024-11-14,0,0,0,772,3167
Calasiao,Dinalaoan,Ofel,2024-11-14,6,22,5,1012,4149
Calasiao,Doyong,Ofel,2024-11-14,0,0,0,980,4020
Calasiao,Gabon,Ofel,2024-11-14,6,22,5,698,2861
Calasiao,Lasip,Ofel,2024-11-14,8,29,7,786,3223
Calasiao,Longos,Ofel,2024-11-14,0,0,0,749,3069
Calasiao,Lumbang,Ofel,2024-11-14,0,0,0,644,2642
Calasiao,Macabito,Ofel,2024-11-14,0,0,0,1088,4461
Calasiao,Malabago,Ofel,2024-11-14,0,0,0,1080,4427
Calasiao,Mancup,Ofel,2024-11-14,0,0,0,911,3735
Calasiao,Nagsaing,Ofel,2024-11-14,8,29,7,1479,6064
Calasiao,Nalsian,Ofel,2024-11-14,0,0,0,1568,6429
Calasiao,Poblacion East,Ofel,2024-11-14,0,0,0,411,1684
Calasiao,Poblacion West,Ofel,2024-11-14,0,0,0,149,609
Calasiao,Quesban,Ofel,2024-11-14,0,0,0,780,3200
Calasiao,San Miguel,Ofel,2024-11-14,0,0,0,1913,7842
Calasiao,San Vicente,Ofel,2024-11-14,0,0,0,516,2117
Calasiao,Songkoy,Ofel,2024-11-14,0,0,0,719,2949
Calasiao,Talibaew,Ofel,2024-11-14,0,0,0,1160,4757
""",
    "nika_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Nika,2024-11-10,0,0,0,1719,7046
Calasiao,Ambuetel,Nika,2024-11-10,0,0,0,739,3031
Calasiao,Banaoang,Nika,2024-11-10,0,0,0,1236,5069
Calasiao,Bued,Nika,2024-11-10,0,0,0,1440,5904
Calasiao,Buenlag,Nika,2024-11-10,0,0,0,2008,8231
Calasiao,Cabilocaan,Nika,2024-11-10,0,0,0,772,3167
Calasiao,Dinalaoan,Nika,2024-11-10,0,0,0,1012,4149
Calasiao,Doyong,Nika,2024-11-10,8,29,7,980,4020
Calasiao,Gabon,Nika,2024-11-10,0,0,0,698,2861
Calasiao,Lasip,Nika,2024-11-10,0,0,0,786,3223
Calasiao,Longos,Nika,2024-11-10,0,0,0,749,3069
Calasiao,Lumbang,Nika,2024-11-10,0,0,0,644,2642
Calasiao,Macabito,Nika,2024-11-10,0,0,0,1088,4461
Calasiao,Malabago,Nika,2024-11-10,0,0,0,1080,4427
Calasiao,Mancup,Nika,2024-11-10,0,0,0,911,3735
Calasiao,Nagsaing,Nika,2024-11-10,7,26,7,1479,6064
Calasiao,Nalsian,Nika,2024-11-10,5,18,4,1568,6429
Calasiao,Poblacion East,Nika,2024-11-10,0,0,0,411,1684
Calasiao,Poblacion West,Nika,2024-11-10,0,0,0,149,609
Calasiao,Quesban,Nika,2024-11-10,0,0,0,780,3200
Calasiao,San Miguel,Nika,2024-11-10,0,0,0,1913,7842
Calasiao,San Vicente,Nika,2024-11-10,0,0,0,516,2117
Calasiao,Songkoy,Nika,2024-11-10,0,0,0,719,2949
Calasiao,Talibaew,Nika,2024-11-10,0,0,0,1160,4757
""",
    "leon_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Leon,2024-11-01,0,0,0,1719,7046
Calasiao,Ambuetel,Leon,2024-11-01,0,0,0,739,3031
Calasiao,Banaoang,Leon,2024-11-01,0,0,0,1236,5069
Calasiao,Bued,Leon,2024-11-01,0,0,0,1440,5904
Calasiao,Buenlag,Leon,2024-11-01,0,0,0,2008,8231
Calasiao,Cabilocaan,Leon,2024-11-01,0,0,0,772,3167
Calasiao,Dinalaoan,Leon,2024-11-01,0,0,0,1012,4149
Calasiao,Doyong,Leon,2024-11-01,0,0,0,980,4020
Calasiao,Gabon,Leon,2024-11-01,0,0,0,698,2861
Calasiao,Lasip,Leon,2024-11-01,0,0,0,786,3223
Calasiao,Longos,Leon,2024-11-01,0,0,0,749,3069
Calasiao,Lumbang,Leon,2024-11-01,0,0,0,644,2642
Calasiao,Macabito,Leon,2024-11-01,0,0,0,1088,4461
Calasiao,Malabago,Leon,2024-11-01,0,0,0,1080,4427
Calasiao,Mancup,Leon,2024-11-01,0,0,0,911,3735
Calasiao,Nagsaing,Leon,2024-11-01,1,4,1,1479,6064
Calasiao,Nalsian,Leon,2024-11-01,0,0,0,1568,6429
Calasiao,Poblacion East,Leon,2024-11-01,0,0,0,411,1684
Calasiao,Poblacion West,Leon,2024-11-01,0,0,0,149,609
Calasiao,Quesban,Leon,2024-11-01,0,0,0,780,3200
Calasiao,San Miguel,Leon,2024-11-01,0,0,0,1913,7842
Calasiao,San Vicente,Leon,2024-11-01,0,0,0,516,2117
Calasiao,Songkoy,Leon,2024-11-01,0,0,0,719,2949
Calasiao,Talibaew,Leon,2024-11-01,0,0,0,1160,4757
""",
    "kristine_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Kristine,2024-10-24,0,0,0,1719,7046
Calasiao,Ambuetel,Kristine,2024-10-24,0,0,0,739,3031
Calasiao,Banaoang,Kristine,2024-10-24,0,0,0,1236,5069
Calasiao,Bued,Kristine,2024-10-24,0,0,0,1440,5904
Calasiao,Buenlag,Kristine,2024-10-24,0,0,0,2008,8231
Calasiao,Cabilocaan,Kristine,2024-10-24,0,0,0,772,3167
Calasiao,Dinalaoan,Kristine,2024-10-24,0,0,0,1012,4149
Calasiao,Doyong,Kristine,2024-10-24,0,0,0,980,4020
Calasiao,Gabon,Kristine,2024-10-24,0,0,0,698,2861
Calasiao,Lasip,Kristine,2024-10-24,0,0,0,786,3223
Calasiao,Longos,Kristine,2024-10-24,0,0,0,749,3069
Calasiao,Lumbang,Kristine,2024-10-24,0,0,0,644,2642
Calasiao,Macabito,Kristine,2024-10-24,0,0,0,1088,4461
Calasiao,Malabago,Kristine,2024-10-24,1,2,1,1080,4427
Calasiao,Mancup,Kristine,2024-10-24,0,0,0,911,3735
Calasiao,Nagsaing,Kristine,2024-10-24,0,0,0,1479,6064
Calasiao,Nalsian,Kristine,2024-10-24,0,0,0,1568,6429
Calasiao,Poblacion East,Kristine,2024-10-24,0,0,0,411,1684
Calasiao,Poblacion West,Kristine,2024-10-24,0,0,0,149,609
Calasiao,Quesban,Kristine,2024-10-24,0,0,0,780,3200
Calasiao,San Miguel,Kristine,2024-10-24,0,0,0,1913,7842
Calasiao,San Vicente,Kristine,2024-10-24,0,0,0,516,2117
Calasiao,Songkoy,Kristine,2024-10-24,0,0,0,719,2949
Calasiao,Talibaew,Kristine,2024-10-24,0,0,0,1160,4757
""",
    "enteng_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Enteng,2024-09-02,0,0,0,1719,7046
Calasiao,Ambuetel,Enteng,2024-09-02,0,0,0,739,3031
Calasiao,Banaoang,Enteng,2024-09-02,0,0,0,1236,5069
Calasiao,Bued,Enteng,2024-09-02,0,0,0,1440,5904
Calasiao,Buenlag,Enteng,2024-09-02,0,0,0,2008,8231
Calasiao,Cabilocaan,Enteng,2024-09-02,11,41,9,772,3167
Calasiao,Dinalaoan,Enteng,2024-09-02,0,0,0,1012,4149
Calasiao,Doyong,Enteng,2024-09-02,23,86,18,980,4020
Calasiao,Gabon,Enteng,2024-09-02,16,60,13,698,2861
Calasiao,Lasip,Enteng,2024-09-02,25,93,21,786,3223
Calasiao,Longos,Enteng,2024-09-02,17,64,14,749,3069
Calasiao,Lumbang,Enteng,2024-09-02,0,0,0,644,2642
Calasiao,Macabito,Enteng,2024-09-02,0,0,0,1088,4461
Calasiao,Malabago,Enteng,2024-09-02,0,0,0,1080,4427
Calasiao,Mancup,Enteng,2024-09-02,25,93,18,911,3735
Calasiao,Nagsaing,Enteng,2024-09-02,22,82,20,1479,6064
Calasiao,Nalsian,Enteng,2024-09-02,0,0,0,1568,6429
Calasiao,Poblacion East,Enteng,2024-09-02,0,0,0,411,1684
Calasiao,Poblacion West,Enteng,2024-09-02,11,41,8,149,609
Calasiao,Quesban,Enteng,2024-09-02,0,0,0,780,3200
Calasiao,San Miguel,Enteng,2024-09-02,0,0,0,1913,7842
Calasiao,San Vicente,Enteng,2024-09-02,0,0,0,516,2117
Calasiao,Songkoy,Enteng,2024-09-02,0,0,0,719,2949
Calasiao,Talibaew,Enteng,2024-09-02,0,0,0,1160,4757
""",
    "carina_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Carina,2024-07-23,0,0,0,1719,7046
Calasiao,Ambuetel,Carina,2024-07-23,36,144,34,739,3031
Calasiao,Banaoang,Carina,2024-07-23,0,0,0,1236,5069
Calasiao,Bued,Carina,2024-07-23,49,196,46,1440,5904
Calasiao,Buenlag,Carina,2024-07-23,0,0,0,2008,8231
Calasiao,Cabilocaan,Carina,2024-07-23,26,104,19,772,3167
Calasiao,Dinalaoan,Carina,2024-07-23,41,164,37,1012,4149
Calasiao,Doyong,Carina,2024-07-23,53,212,38,980,4020
Calasiao,Gabon,Carina,2024-07-23,0,0,0,698,2861
Calasiao,Lasip,Carina,2024-07-23,0,0,0,786,3223
Calasiao,Longos,Carina,2024-07-23,40,160,38,749,3069
Calasiao,Lumbang,Carina,2024-07-23,0,0,0,644,2642
Calasiao,Macabito,Carina,2024-07-23,38,152,32,1088,4461
Calasiao,Malabago,Carina,2024-07-23,0,0,0,1080,4427
Calasiao,Mancup,Carina,2024-07-23,57,228,44,911,3735
Calasiao,Nagsaing,Carina,2024-07-23,0,0,0,1479,6064
Calasiao,Nalsian,Carina,2024-07-23,0,0,0,1568,6429
Calasiao,Poblacion East,Carina,2024-07-23,28,112,21,411,1684
Calasiao,Poblacion West,Carina,2024-07-23,0,0,0,149,609
Calasiao,Quesban,Carina,2024-07-23,0,0,0,780,3200
Calasiao,San Miguel,Carina,2024-07-23,39,156,27,1913,7842
Calasiao,San Vicente,Carina,2024-07-23,34,136,30,516,2117
Calasiao,Songkoy,Carina,2024-07-23,0,0,0,719,2949
Calasiao,Talibaew,Carina,2024-07-23,59,236,53,1160,4757
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Egay,2023-07-26,57,270,52,1708,6879
Calasiao,Ambuetel,Egay,2023-07-26,0,0,0,733,2933
Calasiao,Banaoang,Egay,2023-07-26,59,279,53,1234,5032
Calasiao,Bued,Egay,2023-07-26,71,336,60,1440,5896
Calasiao,Buenlag,Egay,2023-07-26,0,0,0,2011,8281
Calasiao,Cabilocaan,Egay,2023-07-26,0,0,0,761,2985
Calasiao,Dinalaoan,Egay,2023-07-26,59,279,42,1010,4114
Calasiao,Doyong,Egay,2023-07-26,76,359,65,977,3957
Calasiao,Gabon,Egay,2023-07-26,0,0,0,708,3026
Calasiao,Lasip,Egay,2023-07-26,0,0,0,797,3398
Calasiao,Longos,Egay,2023-07-26,0,0,0,745,3006
Calasiao,Lumbang,Egay,2023-07-26,45,213,38,628,2379
Calasiao,Macabito,Egay,2023-07-26,54,255,39,1084,4395
Calasiao,Malabago,Egay,2023-07-26,59,279,49,1074,4329
Calasiao,Mancup,Egay,2023-07-26,0,0,0,904,3621
Calasiao,Nagsaing,Egay,2023-07-26,74,350,57,1479,6060
Calasiao,Nalsian,Egay,2023-07-26,51,241,46,1596,6906
Calasiao,Poblacion East,Egay,2023-07-26,0,0,0,410,1671
Calasiao,Poblacion West,Egay,2023-07-26,0,0,0,163,883
Calasiao,Quesban,Egay,2023-07-26,0,0,0,780,3191
Calasiao,San Miguel,Egay,2023-07-26,0,0,0,1907,7747
Calasiao,San Vicente,Egay,2023-07-26,48,227,40,516,2107
Calasiao,Songkoy,Egay,2023-07-26,0,0,0,713,2848
Calasiao,Talibaew,Egay,2023-07-26,85,402,71,1164,4827
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Paeng,2022-10-29,0,0,0,1698,6879
Calasiao,Ambuetel,Paeng,2022-10-29,0,0,0,727,2933
Calasiao,Banaoang,Paeng,2022-10-29,0,0,0,1232,5032
Calasiao,Bued,Paeng,2022-10-29,0,0,0,1439,5896
Calasiao,Buenlag,Paeng,2022-10-29,0,0,0,2014,8281
Calasiao,Cabilocaan,Paeng,2022-10-29,0,0,0,750,2985
Calasiao,Dinalaoan,Paeng,2022-10-29,0,0,0,1008,4114
Calasiao,Doyong,Paeng,2022-10-29,0,0,0,973,3957
Calasiao,Gabon,Paeng,2022-10-29,0,0,0,718,3026
Calasiao,Lasip,Paeng,2022-10-29,0,0,0,807,3398
Calasiao,Longos,Paeng,2022-10-29,0,0,0,741,3006
Calasiao,Lumbang,Paeng,2022-10-29,0,0,0,611,2379
Calasiao,Macabito,Paeng,2022-10-29,0,0,0,1080,4395
Calasiao,Malabago,Paeng,2022-10-29,0,0,0,1068,4329
Calasiao,Mancup,Paeng,2022-10-29,0,0,0,897,3621
Calasiao,Nagsaing,Paeng,2022-10-29,0,0,0,1479,6060
Calasiao,Nalsian,Paeng,2022-10-29,0,0,0,1625,6906
Calasiao,Poblacion East,Paeng,2022-10-29,0,0,0,409,1671
Calasiao,Poblacion West,Paeng,2022-10-29,0,0,0,179,883
Calasiao,Quesban,Paeng,2022-10-29,0,0,0,779,3191
Calasiao,San Miguel,Paeng,2022-10-29,0,0,0,1901,7747
Calasiao,San Vicente,Paeng,2022-10-29,0,0,0,515,2107
Calasiao,Songkoy,Paeng,2022-10-29,1,2,1,707,2848
Calasiao,Talibaew,Paeng,2022-10-29,0,0,0,1169,4827
""",
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Karding,2022-09-25,0,0,0,1698,6879
Calasiao,Ambuetel,Karding,2022-09-25,0,0,0,727,2933
Calasiao,Banaoang,Karding,2022-09-25,0,0,0,1232,5032
Calasiao,Bued,Karding,2022-09-25,0,0,0,1439,5896
Calasiao,Buenlag,Karding,2022-09-25,0,0,0,2014,8281
Calasiao,Cabilocaan,Karding,2022-09-25,0,0,0,750,2985
Calasiao,Dinalaoan,Karding,2022-09-25,0,0,0,1008,4114
Calasiao,Doyong,Karding,2022-09-25,2,7,2,973,3957
Calasiao,Gabon,Karding,2022-09-25,0,0,0,718,3026
Calasiao,Lasip,Karding,2022-09-25,0,0,0,807,3398
Calasiao,Longos,Karding,2022-09-25,0,0,0,741,3006
Calasiao,Lumbang,Karding,2022-09-25,0,0,0,611,2379
Calasiao,Macabito,Karding,2022-09-25,0,0,0,1080,4395
Calasiao,Malabago,Karding,2022-09-25,0,0,0,1068,4329
Calasiao,Mancup,Karding,2022-09-25,0,0,0,897,3621
Calasiao,Nagsaing,Karding,2022-09-25,0,0,0,1479,6060
Calasiao,Nalsian,Karding,2022-09-25,0,0,0,1625,6906
Calasiao,Poblacion East,Karding,2022-09-25,0,0,0,409,1671
Calasiao,Poblacion West,Karding,2022-09-25,0,0,0,179,883
Calasiao,Quesban,Karding,2022-09-25,0,0,0,779,3191
Calasiao,San Miguel,Karding,2022-09-25,0,0,0,1901,7747
Calasiao,San Vicente,Karding,2022-09-25,0,0,0,515,2107
Calasiao,Songkoy,Karding,2022-09-25,0,0,0,707,2848
Calasiao,Talibaew,Karding,2022-09-25,0,0,0,1169,4827
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Maring,2021-10-11,0,0,0,1688,6879
Calasiao,Ambuetel,Maring,2021-10-11,0,0,0,721,2933
Calasiao,Banaoang,Maring,2021-10-11,0,0,0,1230,5032
Calasiao,Bued,Maring,2021-10-11,0,0,0,1439,5896
Calasiao,Buenlag,Maring,2021-10-11,0,0,0,2017,8281
Calasiao,Cabilocaan,Maring,2021-10-11,8,31,7,739,2985
Calasiao,Dinalaoan,Maring,2021-10-11,12,46,11,1006,4114
Calasiao,Doyong,Maring,2021-10-11,0,0,0,969,3957
Calasiao,Gabon,Maring,2021-10-11,11,42,10,728,3026
Calasiao,Lasip,Maring,2021-10-11,17,65,15,818,3398
Calasiao,Longos,Maring,2021-10-11,12,46,10,737,3006
Calasiao,Lumbang,Maring,2021-10-11,0,0,0,596,2379
Calasiao,Macabito,Maring,2021-10-11,0,0,0,1076,4395
Calasiao,Malabago,Maring,2021-10-11,0,0,0,1062,4329
Calasiao,Mancup,Maring,2021-10-11,0,0,0,890,3621
Calasiao,Nagsaing,Maring,2021-10-11,0,0,0,1478,6060
Calasiao,Nalsian,Maring,2021-10-11,0,0,0,1655,6906
Calasiao,Poblacion East,Maring,2021-10-11,0,0,0,408,1671
Calasiao,Poblacion West,Maring,2021-10-11,0,0,0,196,883
Calasiao,Quesban,Maring,2021-10-11,0,0,0,779,3191
Calasiao,San Miguel,Maring,2021-10-11,0,0,0,1895,7747
Calasiao,San Vicente,Maring,2021-10-11,0,0,0,515,2107
Calasiao,Songkoy,Maring,2021-10-11,0,0,0,701,2848
Calasiao,Talibaew,Maring,2021-10-11,0,0,0,1173,4827
""",
}

# typhoon_key(s) matching scripts/typhoon_calendar_2021_2026.py
_TYPHOON_KEYS = {
    "maymay_2026": ["maymay_2026"],
    "nando_opong_2025": ["nando_2025"],
    "crising_emong_2025": ["crising_2025", "emong_2025"],
    "pepito_2024": ["pepito_2024"],
    "ofel_2024": ["ofel_2024"],
    "nika_2024": ["nika_2024"],
    "leon_2024": ["leon_2024"],
    "kristine_2024": ["kristine_2024"],
    "enteng_2024": ["enteng_2024"],
    "carina_2024": ["carina_2024"],
    "egay_2023": ["egay_2023"],
    "paeng_2022": ["paeng_2022"],
    "karding_2022": ["karding_2022"],
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
        good = len(rows) == 24 and len({normalize(r["barangay"]) for r in rows}) == 24
        ok &= good
        print(f"{rep['key']:<22} 24 brgy={good!s:<6} families={fam:>6,} packs={packs:>6,}  "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Calasiao reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
