"""
REAL records given to the team: Calasiao per-barangay disaster reports for 25
named typhoons, 2021-2026 - one CSV per typhoon, all 24 barangays reported in
every file (Calasiao's data is notably complete compared to Sta. Barbara and
Urdaneta, where many barangays go unreported/unaffected per event). Columns:
Affected Families, Affected Individuals, Food Packs Given, Total Number of
Families, Total Number of Individuals (the last two are a POPULATION SNAPSHOT
AT THAT TIME - the Stage 1 share-model predictor - not a constant; population
grows slightly release to release in these sheets).

This is separate, ADDITIONAL real data from the 2025 Crising/Emong and
Nando/Opong events already covered by scripts/real_calasiao_reports_2025.py -
none of these 25 typhoons is a 2025 event, so there's no overlap to
reconcile.

Transcribed verbatim as CSV text (not hand-built dicts) and parsed with
csv.DictReader - safer against transcription slips than re-typing 25 x 24
rows by hand, and auditable against the source text directly. Barangay names
here use "Cabiloocan"; the barangays table spells it "Cabilocaan" (see
normalize(), same alias real_calasiao_reports_2025.py already uses).

Run this file to print a structural sanity check per typhoon (24 barangays,
no negative values, Food Packs Given plausible against Affected Families).
"""
import csv
import io

from _barangay_names import strip_accents_and_punct

# typhoon_key must match scripts/typhoon_calendar_2021_2026.py
_FILES = {
    "maymay_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Maymay,2026-08-06,235,1137,242,1056,5291
Calasiao,Ambuetel,Maymay,2026-08-06,164,657,140,993,3973
Calasiao,Banaoang,Maymay,2026-08-06,147,617,163,1178,4711
Calasiao,Bued,Maymay,2026-08-06,282,1150,262,1537,6226
Calasiao,Buenlag,Maymay,2026-08-06,489,1942,555,2210,8840
Calasiao,Cabiloocan,Maymay,2026-08-06,115,593,131,522,2609
Calasiao,Dinalaoan,Maymay,2026-08-06,199,949,181,1300,6498
Calasiao,Doyong,Maymay,2026-08-06,250,613,216,1742,4461
Calasiao,Gabon,Maymay,2026-08-06,150,778,148,778,3890
Calasiao,Lasip,Maymay,2026-08-06,344,1072,299,1414,4234
Calasiao,Longos,Maymay,2026-08-06,244,966,216,1235,4940
Calasiao,Lumbang,Maymay,2026-08-06,198,497,202,810,2083
Calasiao,Macabito,Maymay,2026-08-06,211,1001,222,1040,4721
Calasiao,Malabago,Maymay,2026-08-06,320,865,287,1868,5076
Calasiao,Mancup,Maymay,2026-08-06,327,1371,300,1332,5326
Calasiao,Nagsaing,Maymay,2026-08-06,270,1315,258,2162,10793
Calasiao,Nalsian,Maymay,2026-08-06,548,1439,603,2309,5828
Calasiao,Poblacion East,Maymay,2026-08-06,109,449,116,864,3459
Calasiao,Poblacion West,Maymay,2026-08-06,94,197,81,461,922
Calasiao,Quesban,Maymay,2026-08-06,86,264,97,618,1852
Calasiao,San Miguel,Maymay,2026-08-06,277,1099,285,1332,5395
Calasiao,San Vicente,Maymay,2026-08-06,116,446,110,533,2132
Calasiao,Songkoy,Maymay,2026-08-06,130,500,129,847,3387
Calasiao,Talibaew,Maymay,2026-08-06,276,1324,246,1947,9592
""",
    "kiyapo_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Kiyapo,2026-07-24,69,357,59,1056,5291
Calasiao,Ambuetel,Kiyapo,2026-07-24,60,251,60,993,3973
Calasiao,Banaoang,Kiyapo,2026-07-24,71,279,62,1178,4711
Calasiao,Bued,Kiyapo,2026-07-24,114,456,109,1537,6226
Calasiao,Buenlag,Kiyapo,2026-07-24,133,553,132,2210,8840
Calasiao,Cabiloocan,Kiyapo,2026-07-24,23,109,19,522,2609
Calasiao,Dinalaoan,Kiyapo,2026-07-24,66,333,66,1300,6498
Calasiao,Doyong,Kiyapo,2026-07-24,130,318,130,1742,4461
Calasiao,Gabon,Kiyapo,2026-07-24,55,285,51,778,3890
Calasiao,Lasip,Kiyapo,2026-07-24,62,192,62,1414,4234
Calasiao,Longos,Kiyapo,2026-07-24,79,329,67,1235,4940
Calasiao,Lumbang,Kiyapo,2026-07-24,28,72,28,810,2083
Calasiao,Macabito,Kiyapo,2026-07-24,42,195,43,1040,4721
Calasiao,Malabago,Kiyapo,2026-07-24,78,214,74,1868,5076
Calasiao,Mancup,Kiyapo,2026-07-24,71,275,59,1332,5326
Calasiao,Nagsaing,Kiyapo,2026-07-24,146,750,130,2162,10793
Calasiao,Nalsian,Kiyapo,2026-07-24,79,205,78,2309,5828
Calasiao,Poblacion East,Kiyapo,2026-07-24,36,145,37,864,3459
Calasiao,Poblacion West,Kiyapo,2026-07-24,34,68,30,461,922
Calasiao,Quesban,Kiyapo,2026-07-24,37,107,30,618,1852
Calasiao,San Miguel,Kiyapo,2026-07-24,52,215,45,1332,5395
Calasiao,San Vicente,Kiyapo,2026-07-24,31,123,28,533,2132
Calasiao,Songkoy,Kiyapo,2026-07-24,32,122,34,847,3387
Calasiao,Talibaew,Kiyapo,2026-07-24,95,449,89,1947,9592
""",
    "gardo_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Gardo,2026-06-25,66,318,69,1056,5291
Calasiao,Ambuetel,Gardo,2026-06-25,94,392,88,993,3973
Calasiao,Banaoang,Gardo,2026-06-25,72,285,70,1178,4711
Calasiao,Bued,Gardo,2026-06-25,179,760,169,1537,6226
Calasiao,Buenlag,Gardo,2026-06-25,187,718,186,2210,8840
Calasiao,Cabiloocan,Gardo,2026-06-25,38,183,31,522,2609
Calasiao,Dinalaoan,Gardo,2026-06-25,78,397,65,1300,6498
Calasiao,Doyong,Gardo,2026-06-25,206,506,219,1742,4461
Calasiao,Gabon,Gardo,2026-06-25,53,252,54,778,3890
Calasiao,Lasip,Gardo,2026-06-25,105,322,90,1414,4234
Calasiao,Longos,Gardo,2026-06-25,78,321,79,1235,4940
Calasiao,Lumbang,Gardo,2026-06-25,90,237,74,810,2083
Calasiao,Macabito,Gardo,2026-06-25,102,473,96,1040,4721
Calasiao,Malabago,Gardo,2026-06-25,217,575,236,1868,5076
Calasiao,Mancup,Gardo,2026-06-25,137,521,110,1332,5326
Calasiao,Nagsaing,Gardo,2026-06-25,214,1102,176,2162,10793
Calasiao,Nalsian,Gardo,2026-06-25,182,470,155,2309,5828
Calasiao,Poblacion East,Gardo,2026-06-25,96,384,79,864,3459
Calasiao,Poblacion West,Gardo,2026-06-25,38,77,35,461,922
Calasiao,Quesban,Gardo,2026-06-25,62,179,64,618,1852
Calasiao,San Miguel,Gardo,2026-06-25,109,448,108,1332,5395
Calasiao,San Vicente,Gardo,2026-06-25,45,178,47,533,2132
Calasiao,Songkoy,Gardo,2026-06-25,99,407,96,847,3387
Calasiao,Talibaew,Gardo,2026-06-25,151,711,165,1947,9592
""",
    "ester_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Ester,2026-06-03,39,186,36,1056,5291
Calasiao,Ambuetel,Ester,2026-06-03,29,114,28,993,3973
Calasiao,Banaoang,Ester,2026-06-03,25,100,21,1178,4711
Calasiao,Bued,Ester,2026-06-03,51,201,42,1537,6226
Calasiao,Buenlag,Ester,2026-06-03,50,201,47,2210,8840
Calasiao,Cabiloocan,Ester,2026-06-03,10,52,8,522,2609
Calasiao,Dinalaoan,Ester,2026-06-03,33,161,28,1300,6498
Calasiao,Doyong,Ester,2026-06-03,68,177,64,1742,4461
Calasiao,Gabon,Ester,2026-06-03,16,79,13,778,3890
Calasiao,Lasip,Ester,2026-06-03,39,118,36,1414,4234
Calasiao,Longos,Ester,2026-06-03,14,57,14,1235,4940
Calasiao,Lumbang,Ester,2026-06-03,21,52,17,810,2083
Calasiao,Macabito,Ester,2026-06-03,11,48,11,1040,4721
Calasiao,Malabago,Ester,2026-06-03,53,146,50,1868,5076
Calasiao,Mancup,Ester,2026-06-03,50,202,44,1332,5326
Calasiao,Nagsaing,Ester,2026-06-03,62,316,54,2162,10793
Calasiao,Nalsian,Ester,2026-06-03,70,172,63,2309,5828
Calasiao,Poblacion East,Ester,2026-06-03,21,86,15,864,3459
Calasiao,Poblacion West,Ester,2026-06-03,7,13,7,461,922
Calasiao,Quesban,Ester,2026-06-03,23,70,19,618,1852
Calasiao,San Miguel,Ester,2026-06-03,46,192,40,1332,5395
Calasiao,San Vicente,Ester,2026-06-03,9,35,7,533,2132
Calasiao,Songkoy,Ester,2026-06-03,17,68,15,847,3387
Calasiao,Talibaew,Ester,2026-06-03,74,348,64,1947,9592
""",
    "pepito_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Pepito,2024-11-16,86,437,86,1005,5036
Calasiao,Ambuetel,Pepito,2024-11-16,77,321,81,945,3781
Calasiao,Banaoang,Pepito,2024-11-16,71,293,76,1121,4484
Calasiao,Bued,Pepito,2024-11-16,157,613,165,1463,5926
Calasiao,Buenlag,Pepito,2024-11-16,206,784,166,2103,8414
Calasiao,Cabiloocan,Pepito,2024-11-16,58,295,51,497,2483
Calasiao,Dinalaoan,Pepito,2024-11-16,82,395,71,1237,6185
Calasiao,Doyong,Pepito,2024-11-16,177,446,150,1659,4246
Calasiao,Gabon,Pepito,2024-11-16,85,437,72,740,3702
Calasiao,Lasip,Pepito,2024-11-16,153,463,158,1346,4030
Calasiao,Longos,Pepito,2024-11-16,118,491,122,1176,4702
Calasiao,Lumbang,Pepito,2024-11-16,85,212,86,771,1982
Calasiao,Macabito,Pepito,2024-11-16,91,423,85,990,4494
Calasiao,Malabago,Pepito,2024-11-16,201,549,177,1778,4831
Calasiao,Mancup,Pepito,2024-11-16,94,362,89,1268,5069
Calasiao,Nagsaing,Pepito,2024-11-16,131,652,110,2058,10273
Calasiao,Nalsian,Pepito,2024-11-16,197,497,189,2198,5547
Calasiao,Poblacion East,Pepito,2024-11-16,92,350,97,822,3293
Calasiao,Poblacion West,Pepito,2024-11-16,39,78,39,439,878
Calasiao,Quesban,Pepito,2024-11-16,65,192,60,588,1763
Calasiao,San Miguel,Pepito,2024-11-16,149,578,148,1268,5135
Calasiao,San Vicente,Pepito,2024-11-16,50,191,49,507,2029
Calasiao,Songkoy,Pepito,2024-11-16,81,338,73,806,3223
Calasiao,Talibaew,Pepito,2024-11-16,220,1085,208,1854,9130
""",
    "ofel_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Ofel,2024-11-14,90,472,73,1005,5036
Calasiao,Ambuetel,Ofel,2024-11-14,88,340,91,945,3781
Calasiao,Banaoang,Ofel,2024-11-14,131,525,109,1121,4484
Calasiao,Bued,Ofel,2024-11-14,138,561,140,1463,5926
Calasiao,Buenlag,Ofel,2024-11-14,191,775,200,2103,8414
Calasiao,Cabiloocan,Ofel,2024-11-14,45,223,49,497,2483
Calasiao,Dinalaoan,Ofel,2024-11-14,90,458,83,1237,6185
Calasiao,Doyong,Ofel,2024-11-14,175,431,192,1659,4246
Calasiao,Gabon,Ofel,2024-11-14,60,287,53,740,3702
Calasiao,Lasip,Ofel,2024-11-14,113,322,105,1346,4030
Calasiao,Longos,Ofel,2024-11-14,100,408,91,1176,4702
Calasiao,Lumbang,Ofel,2024-11-14,59,148,60,771,1982
Calasiao,Macabito,Ofel,2024-11-14,115,523,100,990,4494
Calasiao,Malabago,Ofel,2024-11-14,192,516,166,1778,4831
Calasiao,Mancup,Ofel,2024-11-14,86,353,90,1268,5069
Calasiao,Nagsaing,Ofel,2024-11-14,202,1005,196,2058,10273
Calasiao,Nalsian,Ofel,2024-11-14,162,428,147,2198,5547
Calasiao,Poblacion East,Ofel,2024-11-14,81,335,85,822,3293
Calasiao,Poblacion West,Ofel,2024-11-14,39,76,38,439,878
Calasiao,Quesban,Ofel,2024-11-14,40,124,36,588,1763
Calasiao,San Miguel,Ofel,2024-11-14,141,558,129,1268,5135
Calasiao,San Vicente,Ofel,2024-11-14,38,151,33,507,2029
Calasiao,Songkoy,Ofel,2024-11-14,48,196,42,806,3223
Calasiao,Talibaew,Ofel,2024-11-14,138,666,130,1854,9130
""",
    "nika_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Nika,2024-11-10,75,366,61,1005,5036
Calasiao,Ambuetel,Nika,2024-11-10,43,175,43,945,3781
Calasiao,Banaoang,Nika,2024-11-10,42,162,35,1121,4484
Calasiao,Bued,Nika,2024-11-10,68,276,54,1463,5926
Calasiao,Buenlag,Nika,2024-11-10,98,380,102,2103,8414
Calasiao,Cabiloocan,Nika,2024-11-10,33,158,34,497,2483
Calasiao,Dinalaoan,Nika,2024-11-10,43,213,45,1237,6185
Calasiao,Doyong,Nika,2024-11-10,116,304,102,1659,4246
Calasiao,Gabon,Nika,2024-11-10,29,147,23,740,3702
Calasiao,Lasip,Nika,2024-11-10,54,160,41,1346,4030
Calasiao,Longos,Nika,2024-11-10,59,243,57,1176,4702
Calasiao,Lumbang,Nika,2024-11-10,42,109,37,771,1982
Calasiao,Macabito,Nika,2024-11-10,37,170,32,990,4494
Calasiao,Malabago,Nika,2024-11-10,119,337,105,1778,4831
Calasiao,Mancup,Nika,2024-11-10,74,303,65,1268,5069
Calasiao,Nagsaing,Nika,2024-11-10,85,434,86,2058,10273
Calasiao,Nalsian,Nika,2024-11-10,151,389,152,2198,5547
Calasiao,Poblacion East,Nika,2024-11-10,53,215,47,822,3293
Calasiao,Poblacion West,Nika,2024-11-10,20,41,16,439,878
Calasiao,Quesban,Nika,2024-11-10,30,92,29,588,1763
Calasiao,San Miguel,Nika,2024-11-10,78,308,68,1268,5135
Calasiao,San Vicente,Nika,2024-11-10,27,109,24,507,2029
Calasiao,Songkoy,Nika,2024-11-10,51,213,41,806,3223
Calasiao,Talibaew,Nika,2024-11-10,116,587,101,1854,9130
""",
    "marce_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Marce,2024-11-07,79,396,79,1005,5036
Calasiao,Ambuetel,Marce,2024-11-07,58,221,51,945,3781
Calasiao,Banaoang,Marce,2024-11-07,58,238,50,1121,4484
Calasiao,Bued,Marce,2024-11-07,95,386,77,1463,5926
Calasiao,Buenlag,Marce,2024-11-07,154,591,153,2103,8414
Calasiao,Cabiloocan,Marce,2024-11-07,19,90,15,497,2483
Calasiao,Dinalaoan,Marce,2024-11-07,84,440,63,1237,6185
Calasiao,Doyong,Marce,2024-11-07,90,230,89,1659,4246
Calasiao,Gabon,Marce,2024-11-07,29,145,25,740,3702
Calasiao,Lasip,Marce,2024-11-07,96,280,99,1346,4030
Calasiao,Longos,Marce,2024-11-07,52,202,50,1176,4702
Calasiao,Lumbang,Marce,2024-11-07,42,104,40,771,1982
Calasiao,Macabito,Marce,2024-11-07,34,159,33,990,4494
Calasiao,Malabago,Marce,2024-11-07,123,339,105,1778,4831
Calasiao,Mancup,Marce,2024-11-07,63,249,64,1268,5069
Calasiao,Nagsaing,Marce,2024-11-07,71,368,54,2058,10273
Calasiao,Nalsian,Marce,2024-11-07,89,219,91,2198,5547
Calasiao,Poblacion East,Marce,2024-11-07,45,178,46,822,3293
Calasiao,Poblacion West,Marce,2024-11-07,18,36,16,439,878
Calasiao,Quesban,Marce,2024-11-07,40,123,38,588,1763
Calasiao,San Miguel,Marce,2024-11-07,60,239,48,1268,5135
Calasiao,San Vicente,Marce,2024-11-07,37,150,36,507,2029
Calasiao,Songkoy,Marce,2024-11-07,31,123,30,806,3223
Calasiao,Talibaew,Marce,2024-11-07,109,517,97,1854,9130
""",
    "leon_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Leon,2024-10-24,74,353,61,1005,5036
Calasiao,Ambuetel,Leon,2024-10-24,40,164,41,945,3781
Calasiao,Banaoang,Leon,2024-10-24,75,295,76,1121,4484
Calasiao,Bued,Leon,2024-10-24,68,268,70,1463,5926
Calasiao,Buenlag,Leon,2024-10-24,129,526,122,2103,8414
Calasiao,Cabiloocan,Leon,2024-10-24,39,194,39,497,2483
Calasiao,Dinalaoan,Leon,2024-10-24,80,414,70,1237,6185
Calasiao,Doyong,Leon,2024-10-24,110,284,93,1659,4246
Calasiao,Gabon,Leon,2024-10-24,30,152,23,740,3702
Calasiao,Lasip,Leon,2024-10-24,102,294,77,1346,4030
Calasiao,Longos,Leon,2024-10-24,42,175,36,1176,4702
Calasiao,Lumbang,Leon,2024-10-24,29,71,22,771,1982
Calasiao,Macabito,Leon,2024-10-24,64,294,61,990,4494
Calasiao,Malabago,Leon,2024-10-24,119,309,110,1778,4831
Calasiao,Mancup,Leon,2024-10-24,61,252,61,1268,5069
Calasiao,Nagsaing,Leon,2024-10-24,153,731,155,2058,10273
Calasiao,Nalsian,Leon,2024-10-24,166,438,130,2198,5547
Calasiao,Poblacion East,Leon,2024-10-24,33,127,25,822,3293
Calasiao,Poblacion West,Leon,2024-10-24,32,66,30,439,878
Calasiao,Quesban,Leon,2024-10-24,42,128,35,588,1763
Calasiao,San Miguel,Leon,2024-10-24,44,171,43,1268,5135
Calasiao,San Vicente,Leon,2024-10-24,20,79,18,507,2029
Calasiao,Songkoy,Leon,2024-10-24,25,98,21,806,3223
Calasiao,Talibaew,Leon,2024-10-24,122,593,103,1854,9130
""",
    "kristine_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Kristine,2024-10-24,285,1440,307,1005,5036
Calasiao,Ambuetel,Kristine,2024-10-24,265,1073,276,945,3781
Calasiao,Banaoang,Kristine,2024-10-24,303,1265,295,1121,4484
Calasiao,Bued,Kristine,2024-10-24,399,1550,435,1463,5926
Calasiao,Buenlag,Kristine,2024-10-24,801,3294,817,2103,8414
Calasiao,Cabiloocan,Kristine,2024-10-24,144,685,157,497,2483
Calasiao,Dinalaoan,Kristine,2024-10-24,414,2039,453,1237,6185
Calasiao,Doyong,Kristine,2024-10-24,525,1403,588,1659,4246
Calasiao,Gabon,Kristine,2024-10-24,213,1108,195,740,3702
Calasiao,Lasip,Kristine,2024-10-24,444,1317,431,1346,4030
Calasiao,Longos,Kristine,2024-10-24,304,1250,275,1176,4702
Calasiao,Lumbang,Kristine,2024-10-24,256,688,241,771,1982
Calasiao,Macabito,Kristine,2024-10-24,277,1271,291,990,4494
Calasiao,Malabago,Kristine,2024-10-24,616,1727,587,1778,4831
Calasiao,Mancup,Kristine,2024-10-24,376,1473,344,1268,5069
Calasiao,Nagsaing,Kristine,2024-10-24,789,4051,879,2058,10273
Calasiao,Nalsian,Kristine,2024-10-24,552,1441,620,2198,5547
Calasiao,Poblacion East,Kristine,2024-10-24,263,1078,272,822,3293
Calasiao,Poblacion West,Kristine,2024-10-24,125,240,121,439,878
Calasiao,Quesban,Kristine,2024-10-24,150,442,169,588,1763
Calasiao,San Miguel,Kristine,2024-10-24,449,1881,500,1268,5135
Calasiao,San Vicente,Kristine,2024-10-24,147,591,152,507,2029
Calasiao,Songkoy,Kristine,2024-10-24,297,1191,291,806,3223
Calasiao,Talibaew,Kristine,2024-10-24,642,3309,620,1854,9130
""",
    "enteng_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Enteng,2024-09-02,185,969,208,1005,5036
Calasiao,Ambuetel,Enteng,2024-09-02,134,551,151,945,3781
Calasiao,Banaoang,Enteng,2024-09-02,144,567,155,1121,4484
Calasiao,Bued,Enteng,2024-09-02,206,867,192,1463,5926
Calasiao,Buenlag,Enteng,2024-09-02,475,1832,475,2103,8414
Calasiao,Cabiloocan,Enteng,2024-09-02,119,578,111,497,2483
Calasiao,Dinalaoan,Enteng,2024-09-02,230,1129,198,1237,6185
Calasiao,Doyong,Enteng,2024-09-02,238,589,269,1659,4246
Calasiao,Gabon,Enteng,2024-09-02,154,800,139,740,3702
Calasiao,Lasip,Enteng,2024-09-02,299,861,302,1346,4030
Calasiao,Longos,Enteng,2024-09-02,238,939,265,1176,4702
Calasiao,Lumbang,Enteng,2024-09-02,148,384,165,771,1982
Calasiao,Macabito,Enteng,2024-09-02,132,629,137,990,4494
Calasiao,Malabago,Enteng,2024-09-02,304,851,283,1778,4831
Calasiao,Mancup,Enteng,2024-09-02,315,1269,302,1268,5069
Calasiao,Nagsaing,Enteng,2024-09-02,452,2244,408,2058,10273
Calasiao,Nalsian,Enteng,2024-09-02,476,1147,522,2198,5547
Calasiao,Poblacion East,Enteng,2024-09-02,126,511,144,822,3293
Calasiao,Poblacion West,Enteng,2024-09-02,86,175,81,439,878
Calasiao,Quesban,Enteng,2024-09-02,71,203,64,588,1763
Calasiao,San Miguel,Enteng,2024-09-02,254,1021,255,1268,5135
Calasiao,San Vicente,Enteng,2024-09-02,120,462,110,507,2029
Calasiao,Songkoy,Enteng,2024-09-02,165,628,140,806,3223
Calasiao,Talibaew,Enteng,2024-09-02,308,1457,295,1854,9130
""",
    "carina_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Carina,2024-07-23,559,2787,547,1005,5036
Calasiao,Ambuetel,Carina,2024-07-23,510,2131,475,945,3781
Calasiao,Banaoang,Carina,2024-07-23,569,2303,549,1121,4484
Calasiao,Bued,Carina,2024-07-23,682,2663,656,1463,5926
Calasiao,Buenlag,Carina,2024-07-23,938,3789,1028,2103,8414
Calasiao,Cabiloocan,Carina,2024-07-23,217,1032,217,497,2483
Calasiao,Dinalaoan,Carina,2024-07-23,646,3128,642,1237,6185
Calasiao,Doyong,Carina,2024-07-23,724,1908,771,1659,4246
Calasiao,Gabon,Carina,2024-07-23,304,1459,310,740,3702
Calasiao,Lasip,Carina,2024-07-23,672,2040,623,1346,4030
Calasiao,Longos,Carina,2024-07-23,505,2059,517,1176,4702
Calasiao,Lumbang,Carina,2024-07-23,348,878,413,771,1982
Calasiao,Macabito,Carina,2024-07-23,452,2065,455,990,4494
Calasiao,Malabago,Carina,2024-07-23,844,2377,1012,1778,4831
Calasiao,Mancup,Carina,2024-07-23,590,2287,660,1268,5069
Calasiao,Nagsaing,Carina,2024-07-23,899,4267,1052,2058,10273
Calasiao,Nalsian,Carina,2024-07-23,1047,2727,1070,2198,5547
Calasiao,Poblacion East,Carina,2024-07-23,459,1830,435,822,3293
Calasiao,Poblacion West,Carina,2024-07-23,177,356,193,439,878
Calasiao,Quesban,Carina,2024-07-23,331,951,360,588,1763
Calasiao,San Miguel,Carina,2024-07-23,592,2398,559,1268,5135
Calasiao,San Vicente,Carina,2024-07-23,229,918,270,507,2029
Calasiao,Songkoy,Carina,2024-07-23,338,1351,386,806,3223
Calasiao,Talibaew,Carina,2024-07-23,1064,5082,998,1854,9130
""",
    "butchoy_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Butchoy,2024-07-22,78,409,70,1005,5036
Calasiao,Ambuetel,Butchoy,2024-07-22,31,129,27,945,3781
Calasiao,Banaoang,Butchoy,2024-07-22,84,340,84,1121,4484
Calasiao,Bued,Butchoy,2024-07-22,56,233,46,1463,5926
Calasiao,Buenlag,Butchoy,2024-07-22,106,439,106,2103,8414
Calasiao,Cabiloocan,Butchoy,2024-07-22,19,92,17,497,2483
Calasiao,Dinalaoan,Butchoy,2024-07-22,69,341,54,1237,6185
Calasiao,Doyong,Butchoy,2024-07-22,70,183,71,1659,4246
Calasiao,Gabon,Butchoy,2024-07-22,24,121,23,740,3702
Calasiao,Lasip,Butchoy,2024-07-22,43,133,34,1346,4030
Calasiao,Longos,Butchoy,2024-07-22,71,285,67,1176,4702
Calasiao,Lumbang,Butchoy,2024-07-22,35,89,32,771,1982
Calasiao,Macabito,Butchoy,2024-07-22,51,235,45,990,4494
Calasiao,Malabago,Butchoy,2024-07-22,92,238,86,1778,4831
Calasiao,Mancup,Butchoy,2024-07-22,69,268,68,1268,5069
Calasiao,Nagsaing,Butchoy,2024-07-22,142,706,114,2058,10273
Calasiao,Nalsian,Butchoy,2024-07-22,118,286,93,2198,5547
Calasiao,Poblacion East,Butchoy,2024-07-22,42,161,37,822,3293
Calasiao,Poblacion West,Butchoy,2024-07-22,24,46,23,439,878
Calasiao,Quesban,Butchoy,2024-07-22,20,61,20,588,1763
Calasiao,San Miguel,Butchoy,2024-07-22,70,271,63,1268,5135
Calasiao,San Vicente,Butchoy,2024-07-22,25,105,20,507,2029
Calasiao,Songkoy,Butchoy,2024-07-22,59,248,57,806,3223
Calasiao,Talibaew,Butchoy,2024-07-22,131,625,137,1854,9130
""",
    "goring_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Goring,2023-08-23,48,235,42,980,4913
Calasiao,Ambuetel,Goring,2023-08-23,50,209,40,922,3689
Calasiao,Banaoang,Goring,2023-08-23,77,315,77,1094,4375
Calasiao,Bued,Goring,2023-08-23,98,401,83,1428,5781
Calasiao,Buenlag,Goring,2023-08-23,94,371,93,2052,8208
Calasiao,Cabiloocan,Goring,2023-08-23,16,78,16,484,2422
Calasiao,Dinalaoan,Goring,2023-08-23,51,244,39,1207,6035
Calasiao,Doyong,Goring,2023-08-23,93,234,97,1618,4142
Calasiao,Gabon,Goring,2023-08-23,54,283,45,722,3612
Calasiao,Lasip,Goring,2023-08-23,45,129,40,1314,3932
Calasiao,Longos,Goring,2023-08-23,75,298,62,1147,4588
Calasiao,Lumbang,Goring,2023-08-23,38,99,36,752,1934
Calasiao,Macabito,Goring,2023-08-23,65,305,62,966,4384
Calasiao,Malabago,Goring,2023-08-23,63,177,53,1734,4713
Calasiao,Mancup,Goring,2023-08-23,72,284,70,1237,4946
Calasiao,Nagsaing,Goring,2023-08-23,80,389,66,2007,10023
Calasiao,Nalsian,Goring,2023-08-23,81,212,75,2144,5412
Calasiao,Poblacion East,Goring,2023-08-23,37,147,39,802,3212
Calasiao,Poblacion West,Goring,2023-08-23,24,47,24,428,857
Calasiao,Quesban,Goring,2023-08-23,36,113,28,574,1720
Calasiao,San Miguel,Goring,2023-08-23,66,276,66,1237,5009
Calasiao,San Vicente,Goring,2023-08-23,37,141,31,495,1980
Calasiao,Songkoy,Goring,2023-08-23,28,109,29,786,3145
Calasiao,Talibaew,Goring,2023-08-23,107,550,92,1808,8907
""",
    "falcon_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Falcon,2023-07-29,29,152,22,980,4913
Calasiao,Ambuetel,Falcon,2023-07-29,20,78,20,922,3689
Calasiao,Banaoang,Falcon,2023-07-29,16,61,11,1094,4375
Calasiao,Bued,Falcon,2023-07-29,31,131,30,1428,5781
Calasiao,Buenlag,Falcon,2023-07-29,66,277,65,2052,8208
Calasiao,Cabiloocan,Falcon,2023-07-29,10,48,10,484,2422
Calasiao,Dinalaoan,Falcon,2023-07-29,39,186,35,1207,6035
Calasiao,Doyong,Falcon,2023-07-29,35,88,28,1618,4142
Calasiao,Gabon,Falcon,2023-07-29,11,52,9,722,3612
Calasiao,Lasip,Falcon,2023-07-29,27,85,20,1314,3932
Calasiao,Longos,Falcon,2023-07-29,45,175,36,1147,4588
Calasiao,Lumbang,Falcon,2023-07-29,26,69,22,752,1934
Calasiao,Macabito,Falcon,2023-07-29,11,50,9,966,4384
Calasiao,Malabago,Falcon,2023-07-29,65,171,53,1734,4713
Calasiao,Mancup,Falcon,2023-07-29,46,175,38,1237,4946
Calasiao,Nagsaing,Falcon,2023-07-29,69,354,49,2007,10023
Calasiao,Nalsian,Falcon,2023-07-29,24,58,23,2144,5412
Calasiao,Poblacion East,Falcon,2023-07-29,14,57,14,802,3212
Calasiao,Poblacion West,Falcon,2023-07-29,9,18,9,428,857
Calasiao,Quesban,Falcon,2023-07-29,16,47,15,574,1720
Calasiao,San Miguel,Falcon,2023-07-29,24,95,17,1237,5009
Calasiao,San Vicente,Falcon,2023-07-29,16,67,14,495,1980
Calasiao,Songkoy,Falcon,2023-07-29,30,114,23,786,3145
Calasiao,Talibaew,Falcon,2023-07-29,44,227,43,1808,8907
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Egay,2023-07-26,538,2792,641,980,4913
Calasiao,Ambuetel,Egay,2023-07-26,410,1576,388,922,3689
Calasiao,Banaoang,Egay,2023-07-26,540,2199,639,1094,4375
Calasiao,Bued,Egay,2023-07-26,757,3111,855,1428,5781
Calasiao,Buenlag,Egay,2023-07-26,990,3980,903,2052,8208
Calasiao,Cabiloocan,Egay,2023-07-26,262,1275,308,484,2422
Calasiao,Dinalaoan,Egay,2023-07-26,623,3054,585,1207,6035
Calasiao,Doyong,Egay,2023-07-26,721,1871,800,1618,4142
Calasiao,Gabon,Egay,2023-07-26,303,1450,320,722,3612
Calasiao,Lasip,Egay,2023-07-26,663,1962,641,1314,3932
Calasiao,Longos,Egay,2023-07-26,583,2218,577,1147,4588
Calasiao,Lumbang,Egay,2023-07-26,363,977,397,752,1934
Calasiao,Macabito,Egay,2023-07-26,540,2444,524,966,4384
Calasiao,Malabago,Egay,2023-07-26,771,2192,857,1734,4713
Calasiao,Mancup,Egay,2023-07-26,563,2143,591,1237,4946
Calasiao,Nagsaing,Egay,2023-07-26,1046,5181,1022,2007,10023
Calasiao,Nalsian,Egay,2023-07-26,1115,2934,1079,2144,5412
Calasiao,Poblacion East,Egay,2023-07-26,326,1284,335,802,3212
Calasiao,Poblacion West,Egay,2023-07-26,224,434,255,428,857
Calasiao,Quesban,Egay,2023-07-26,306,917,294,574,1720
Calasiao,San Miguel,Egay,2023-07-26,711,2824,815,1237,5009
Calasiao,San Vicente,Egay,2023-07-26,219,852,247,495,1980
Calasiao,Songkoy,Egay,2023-07-26,356,1488,373,786,3145
Calasiao,Talibaew,Egay,2023-07-26,784,3755,804,1808,8907
""",
    "dodong_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Dodong,2023-07-13,28,146,28,980,4913
Calasiao,Ambuetel,Dodong,2023-07-13,24,98,17,922,3689
Calasiao,Banaoang,Dodong,2023-07-13,35,139,32,1094,4375
Calasiao,Bued,Dodong,2023-07-13,42,166,30,1428,5781
Calasiao,Buenlag,Dodong,2023-07-13,78,300,66,2052,8208
Calasiao,Cabiloocan,Dodong,2023-07-13,10,49,9,484,2422
Calasiao,Dinalaoan,Dodong,2023-07-13,47,229,42,1207,6035
Calasiao,Doyong,Dodong,2023-07-13,31,80,25,1618,4142
Calasiao,Gabon,Dodong,2023-07-13,11,53,8,722,3612
Calasiao,Lasip,Dodong,2023-07-13,49,147,38,1314,3932
Calasiao,Longos,Dodong,2023-07-13,43,181,36,1147,4588
Calasiao,Lumbang,Dodong,2023-07-13,11,27,8,752,1934
Calasiao,Macabito,Dodong,2023-07-13,20,87,15,966,4384
Calasiao,Malabago,Dodong,2023-07-13,31,85,30,1734,4713
Calasiao,Mancup,Dodong,2023-07-13,40,158,33,1237,4946
Calasiao,Nagsaing,Dodong,2023-07-13,52,256,42,2007,10023
Calasiao,Nalsian,Dodong,2023-07-13,25,62,25,2144,5412
Calasiao,Poblacion East,Dodong,2023-07-13,11,44,10,802,3212
Calasiao,Poblacion West,Dodong,2023-07-13,15,29,12,428,857
Calasiao,Quesban,Dodong,2023-07-13,10,30,8,574,1720
Calasiao,San Miguel,Dodong,2023-07-13,48,201,46,1237,5009
Calasiao,San Vicente,Dodong,2023-07-13,5,19,5,495,1980
Calasiao,Songkoy,Dodong,2023-07-13,29,116,25,786,3145
Calasiao,Talibaew,Dodong,2023-07-13,18,88,18,1808,8907
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Paeng,2022-10-29,248,1214,273,956,4793
Calasiao,Ambuetel,Paeng,2022-10-29,318,1294,314,900,3599
Calasiao,Banaoang,Paeng,2022-10-29,349,1391,363,1067,4268
Calasiao,Bued,Paeng,2022-10-29,373,1570,358,1393,5640
Calasiao,Buenlag,Paeng,2022-10-29,794,3315,719,2002,8008
Calasiao,Cabiloocan,Paeng,2022-10-29,151,779,180,473,2363
Calasiao,Dinalaoan,Paeng,2022-10-29,374,1827,360,1177,5887
Calasiao,Doyong,Paeng,2022-10-29,619,1539,665,1579,4041
Calasiao,Gabon,Paeng,2022-10-29,191,957,226,705,3524
Calasiao,Lasip,Paeng,2022-10-29,346,1069,364,1281,3836
Calasiao,Longos,Paeng,2022-10-29,429,1751,416,1119,4476
Calasiao,Lumbang,Paeng,2022-10-29,282,724,256,734,1887
Calasiao,Macabito,Paeng,2022-10-29,236,1070,244,943,4277
Calasiao,Malabago,Paeng,2022-10-29,500,1310,502,1692,4598
Calasiao,Mancup,Paeng,2022-10-29,359,1484,323,1207,4825
Calasiao,Nagsaing,Paeng,2022-10-29,710,3665,665,1958,9778
Calasiao,Nalsian,Paeng,2022-10-29,814,2098,953,2092,5280
Calasiao,Poblacion East,Paeng,2022-10-29,230,909,234,783,3134
Calasiao,Poblacion West,Paeng,2022-10-29,167,337,168,418,836
Calasiao,Quesban,Paeng,2022-10-29,176,516,161,560,1678
Calasiao,San Miguel,Paeng,2022-10-29,320,1339,315,1207,4887
Calasiao,San Vicente,Paeng,2022-10-29,189,737,185,483,1931
Calasiao,Songkoy,Paeng,2022-10-29,251,973,254,767,3068
Calasiao,Talibaew,Paeng,2022-10-29,694,3549,794,1764,8690
""",
    "neneng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Neneng,2022-10-16,11,52,9,956,4793
Calasiao,Ambuetel,Neneng,2022-10-16,15,61,13,900,3599
Calasiao,Banaoang,Neneng,2022-10-16,35,142,32,1067,4268
Calasiao,Bued,Neneng,2022-10-16,51,204,41,1393,5640
Calasiao,Buenlag,Neneng,2022-10-16,79,305,72,2002,8008
Calasiao,Cabiloocan,Neneng,2022-10-16,14,67,13,473,2363
Calasiao,Dinalaoan,Neneng,2022-10-16,43,218,40,1177,5887
Calasiao,Doyong,Neneng,2022-10-16,54,133,46,1579,4041
Calasiao,Gabon,Neneng,2022-10-16,18,93,17,705,3524
Calasiao,Lasip,Neneng,2022-10-16,45,136,44,1281,3836
Calasiao,Longos,Neneng,2022-10-16,34,139,26,1119,4476
Calasiao,Lumbang,Neneng,2022-10-16,8,20,6,734,1887
Calasiao,Macabito,Neneng,2022-10-16,12,56,10,943,4277
Calasiao,Malabago,Neneng,2022-10-16,49,135,44,1692,4598
Calasiao,Mancup,Neneng,2022-10-16,30,114,28,1207,4825
Calasiao,Nagsaing,Neneng,2022-10-16,64,320,55,1958,9778
Calasiao,Nalsian,Neneng,2022-10-16,62,150,57,2092,5280
Calasiao,Poblacion East,Neneng,2022-10-16,14,54,11,783,3134
Calasiao,Poblacion West,Neneng,2022-10-16,13,25,12,418,836
Calasiao,Quesban,Neneng,2022-10-16,22,66,18,560,1678
Calasiao,San Miguel,Neneng,2022-10-16,29,120,27,1207,4887
Calasiao,San Vicente,Neneng,2022-10-16,14,57,10,483,1931
Calasiao,Songkoy,Neneng,2022-10-16,11,43,10,767,3068
Calasiao,Talibaew,Neneng,2022-10-16,34,169,24,1764,8690
""",
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Karding,2022-09-25,73,352,70,956,4793
Calasiao,Ambuetel,Karding,2022-09-25,67,258,57,900,3599
Calasiao,Banaoang,Karding,2022-09-25,67,260,60,1067,4268
Calasiao,Bued,Karding,2022-09-25,109,453,97,1393,5640
Calasiao,Buenlag,Karding,2022-09-25,180,697,163,2002,8008
Calasiao,Cabiloocan,Karding,2022-09-25,29,141,23,473,2363
Calasiao,Dinalaoan,Karding,2022-09-25,122,613,105,1177,5887
Calasiao,Doyong,Karding,2022-09-25,140,374,116,1579,4041
Calasiao,Gabon,Karding,2022-09-25,77,382,73,705,3524
Calasiao,Lasip,Karding,2022-09-25,141,418,134,1281,3836
Calasiao,Longos,Karding,2022-09-25,113,474,102,1119,4476
Calasiao,Lumbang,Karding,2022-09-25,81,213,80,734,1887
Calasiao,Macabito,Karding,2022-09-25,79,353,64,943,4277
Calasiao,Malabago,Karding,2022-09-25,115,299,118,1692,4598
Calasiao,Mancup,Karding,2022-09-25,91,351,75,1207,4825
Calasiao,Nagsaing,Karding,2022-09-25,216,1118,216,1958,9778
Calasiao,Nalsian,Karding,2022-09-25,161,396,143,2092,5280
Calasiao,Poblacion East,Karding,2022-09-25,69,267,64,783,3134
Calasiao,Poblacion West,Karding,2022-09-25,32,67,35,418,836
Calasiao,Quesban,Karding,2022-09-25,52,152,57,560,1678
Calasiao,San Miguel,Karding,2022-09-25,95,379,76,1207,4887
Calasiao,San Vicente,Karding,2022-09-25,40,160,38,483,1931
Calasiao,Songkoy,Karding,2022-09-25,55,220,44,767,3068
Calasiao,Talibaew,Karding,2022-09-25,134,633,123,1764,8690
""",
    "florita_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Florita,2022-08-23,26,136,25,956,4793
Calasiao,Ambuetel,Florita,2022-08-23,13,50,11,900,3599
Calasiao,Banaoang,Florita,2022-08-23,13,51,9,1067,4268
Calasiao,Bued,Florita,2022-08-23,42,175,41,1393,5640
Calasiao,Buenlag,Florita,2022-08-23,29,119,26,2002,8008
Calasiao,Cabiloocan,Florita,2022-08-23,7,36,7,473,2363
Calasiao,Dinalaoan,Florita,2022-08-23,20,105,16,1177,5887
Calasiao,Doyong,Florita,2022-08-23,39,105,37,1579,4041
Calasiao,Gabon,Florita,2022-08-23,10,50,9,705,3524
Calasiao,Lasip,Florita,2022-08-23,26,75,21,1281,3836
Calasiao,Longos,Florita,2022-08-23,35,133,30,1119,4476
Calasiao,Lumbang,Florita,2022-08-23,17,42,14,734,1887
Calasiao,Macabito,Florita,2022-08-23,27,123,19,943,4277
Calasiao,Malabago,Florita,2022-08-23,67,187,66,1692,4598
Calasiao,Mancup,Florita,2022-08-23,16,62,11,1207,4825
Calasiao,Nagsaing,Florita,2022-08-23,65,317,48,1958,9778
Calasiao,Nalsian,Florita,2022-08-23,47,123,44,2092,5280
Calasiao,Poblacion East,Florita,2022-08-23,14,54,14,783,3134
Calasiao,Poblacion West,Florita,2022-08-23,11,22,8,418,836
Calasiao,Quesban,Florita,2022-08-23,7,21,6,560,1678
Calasiao,San Miguel,Florita,2022-08-23,15,63,13,1207,4887
Calasiao,San Vicente,Florita,2022-08-23,16,61,15,483,1931
Calasiao,Songkoy,Florita,2022-08-23,9,37,8,767,3068
Calasiao,Talibaew,Florita,2022-08-23,36,178,35,1764,8690
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Maring,2021-10-11,127,614,142,933,4677
Calasiao,Ambuetel,Maring,2021-10-11,197,760,216,878,3511
Calasiao,Banaoang,Maring,2021-10-11,258,1048,246,1041,4164
Calasiao,Bued,Maring,2021-10-11,260,1014,222,1359,5503
Calasiao,Buenlag,Maring,2021-10-11,481,1953,485,1953,7813
Calasiao,Cabiloocan,Maring,2021-10-11,111,551,123,461,2306
Calasiao,Dinalaoan,Maring,2021-10-11,261,1267,242,1149,5744
Calasiao,Doyong,Maring,2021-10-11,243,606,249,1540,3943
Calasiao,Gabon,Maring,2021-10-11,106,526,94,688,3438
Calasiao,Lasip,Maring,2021-10-11,298,879,294,1250,3742
Calasiao,Longos,Maring,2021-10-11,214,891,209,1092,4367
Calasiao,Lumbang,Maring,2021-10-11,171,440,173,716,1841
Calasiao,Macabito,Maring,2021-10-11,173,747,170,920,4173
Calasiao,Malabago,Maring,2021-10-11,237,612,258,1651,4486
Calasiao,Mancup,Maring,2021-10-11,168,670,179,1178,4707
Calasiao,Nagsaing,Maring,2021-10-11,368,1805,370,1911,9540
Calasiao,Nalsian,Maring,2021-10-11,392,1017,346,2041,5151
Calasiao,Poblacion East,Maring,2021-10-11,147,574,137,764,3058
Calasiao,Poblacion West,Maring,2021-10-11,90,180,92,408,815
Calasiao,Quesban,Maring,2021-10-11,119,371,117,546,1637
Calasiao,San Miguel,Maring,2021-10-11,235,952,236,1178,4768
Calasiao,San Vicente,Maring,2021-10-11,99,394,100,471,1884
Calasiao,Songkoy,Maring,2021-10-11,136,568,144,748,2993
Calasiao,Talibaew,Maring,2021-10-11,403,2073,374,1721,8478
""",
    "kiko_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Kiko,2021-09-11,22,110,16,933,4677
Calasiao,Ambuetel,Kiko,2021-09-11,11,43,9,878,3511
Calasiao,Banaoang,Kiko,2021-09-11,36,139,25,1041,4164
Calasiao,Bued,Kiko,2021-09-11,52,211,39,1359,5503
Calasiao,Buenlag,Kiko,2021-09-11,51,194,44,1953,7813
Calasiao,Cabiloocan,Kiko,2021-09-11,18,93,16,461,2306
Calasiao,Dinalaoan,Kiko,2021-09-11,20,99,15,1149,5744
Calasiao,Doyong,Kiko,2021-09-11,51,131,48,1540,3943
Calasiao,Gabon,Kiko,2021-09-11,14,68,13,688,3438
Calasiao,Lasip,Kiko,2021-09-11,49,152,46,1250,3742
Calasiao,Longos,Kiko,2021-09-11,38,156,29,1092,4367
Calasiao,Lumbang,Kiko,2021-09-11,18,46,13,716,1841
Calasiao,Macabito,Kiko,2021-09-11,10,44,8,920,4173
Calasiao,Malabago,Kiko,2021-09-11,51,145,43,1651,4486
Calasiao,Mancup,Kiko,2021-09-11,45,189,44,1178,4707
Calasiao,Nagsaing,Kiko,2021-09-11,40,194,31,1911,9540
Calasiao,Nalsian,Kiko,2021-09-11,32,78,28,2041,5151
Calasiao,Poblacion East,Kiko,2021-09-11,28,116,24,764,3058
Calasiao,Poblacion West,Kiko,2021-09-11,12,25,9,408,815
Calasiao,Quesban,Kiko,2021-09-11,16,50,15,546,1637
Calasiao,San Miguel,Kiko,2021-09-11,38,154,29,1178,4768
Calasiao,San Vicente,Kiko,2021-09-11,16,63,15,471,1884
Calasiao,Songkoy,Kiko,2021-09-11,29,115,24,748,2993
Calasiao,Talibaew,Kiko,2021-09-11,66,332,50,1721,8478
""",
    "jolina_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Jolina,2021-09-07,27,142,26,933,4677
Calasiao,Ambuetel,Jolina,2021-09-07,16,63,14,878,3511
Calasiao,Banaoang,Jolina,2021-09-07,11,44,8,1041,4164
Calasiao,Bued,Jolina,2021-09-07,18,70,17,1359,5503
Calasiao,Buenlag,Jolina,2021-09-07,27,105,22,1953,7813
Calasiao,Cabiloocan,Jolina,2021-09-07,17,81,14,461,2306
Calasiao,Dinalaoan,Jolina,2021-09-07,30,156,28,1149,5744
Calasiao,Doyong,Jolina,2021-09-07,55,138,45,1540,3943
Calasiao,Gabon,Jolina,2021-09-07,14,73,14,688,3438
Calasiao,Lasip,Jolina,2021-09-07,18,52,14,1250,3742
Calasiao,Longos,Jolina,2021-09-07,19,76,17,1092,4367
Calasiao,Lumbang,Jolina,2021-09-07,13,32,11,716,1841
Calasiao,Macabito,Jolina,2021-09-07,19,87,19,920,4173
Calasiao,Malabago,Jolina,2021-09-07,51,139,45,1651,4486
Calasiao,Mancup,Jolina,2021-09-07,36,137,35,1178,4707
Calasiao,Nagsaing,Jolina,2021-09-07,64,332,60,1911,9540
Calasiao,Nalsian,Jolina,2021-09-07,44,110,32,2041,5151
Calasiao,Poblacion East,Jolina,2021-09-07,22,84,16,764,3058
Calasiao,Poblacion West,Jolina,2021-09-07,7,14,6,408,815
Calasiao,Quesban,Jolina,2021-09-07,6,17,4,546,1637
Calasiao,San Miguel,Jolina,2021-09-07,15,60,11,1178,4768
Calasiao,San Vicente,Jolina,2021-09-07,17,69,13,471,1884
Calasiao,Songkoy,Jolina,2021-09-07,13,51,11,748,2993
Calasiao,Talibaew,Jolina,2021-09-07,24,122,24,1721,8478
""",
    "fabian_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Calasiao,Ambonao,Fabian,2021-07-20,18,87,16,933,4677
Calasiao,Ambuetel,Fabian,2021-07-20,11,44,9,878,3511
Calasiao,Banaoang,Fabian,2021-07-20,12,48,9,1041,4164
Calasiao,Bued,Fabian,2021-07-20,31,120,23,1359,5503
Calasiao,Buenlag,Fabian,2021-07-20,44,182,32,1953,7813
Calasiao,Cabiloocan,Fabian,2021-07-20,8,41,8,461,2306
Calasiao,Dinalaoan,Fabian,2021-07-20,31,153,31,1149,5744
Calasiao,Doyong,Fabian,2021-07-20,18,48,14,1540,3943
Calasiao,Gabon,Fabian,2021-07-20,10,48,8,688,3438
Calasiao,Lasip,Fabian,2021-07-20,43,125,38,1250,3742
Calasiao,Longos,Fabian,2021-07-20,32,126,28,1092,4367
Calasiao,Lumbang,Fabian,2021-07-20,9,22,7,716,1841
Calasiao,Macabito,Fabian,2021-07-20,28,126,22,920,4173
Calasiao,Malabago,Fabian,2021-07-20,46,124,36,1651,4486
Calasiao,Mancup,Fabian,2021-07-20,40,163,31,1178,4707
Calasiao,Nagsaing,Fabian,2021-07-20,52,260,50,1911,9540
Calasiao,Nalsian,Fabian,2021-07-20,65,161,65,2041,5151
Calasiao,Poblacion East,Fabian,2021-07-20,10,40,9,764,3058
Calasiao,Poblacion West,Fabian,2021-07-20,6,12,4,408,815
Calasiao,Quesban,Fabian,2021-07-20,16,49,14,546,1637
Calasiao,San Miguel,Fabian,2021-07-20,43,171,39,1178,4768
Calasiao,San Vicente,Fabian,2021-07-20,13,52,11,471,1884
Calasiao,Songkoy,Fabian,2021-07-20,26,109,22,748,2993
Calasiao,Talibaew,Fabian,2021-07-20,52,245,47,1721,8478
""",
}


def normalize(name):
    return {"cabiloocan": "cabilocaan"}.get(strip_accents_and_punct(name), strip_accents_and_punct(name))


def parse(typhoon_key):
    """[{barangay, affected_families, affected_individuals, food_packs_given,
    total_families, total_individuals, date, typhoon_name}] for one typhoon."""
    reader = csv.DictReader(io.StringIO(_FILES[typhoon_key]))
    rows = []
    for r in reader:
        rows.append({
            "barangay": r["Barangay"],
            "date": r["Date ng Typhoon"],
            "typhoon_name": r["Name of Typhoon"],
            "affected_families": int(r["Affected Families"]),
            "affected_individuals": int(r["Affected Individuals"]),
            "food_packs_given": int(r["Food Packs Given"]),
            "total_families": int(r["Total Number of Families"]),
            "total_individuals": int(r["Total Number of Individuals"]),
        })
    return rows


REPORTS = [
    {"typhoon_keys": [key], "label": rows[0]["typhoon_name"] if (rows := parse(key)) else key,
     "report_date": rows[0]["date"], "rows": rows}
    for key in _FILES
]


if __name__ == "__main__":
    ok = True
    for rep in REPORTS:
        rows = rep["rows"]
        fam = sum(r["affected_families"] for r in rows)
        packs = sum(r["food_packs_given"] for r in rows)
        bad = [r for r in rows if min(r["affected_families"], r["affected_individuals"],
                                       r["food_packs_given"], r["total_families"],
                                       r["total_individuals"]) < 0]
        good = len(rows) == 24 and not bad
        ok &= good
        print(f"{rep['label']:<10}{rep['report_date']:<12} 24 brgy={len(rows) == 24!s:<6} "
              f"families={fam:>6,} packs={packs:>6,}  {'OK' if good else 'MISMATCH'}")
    print("\nAll 25 Calasiao typhoon reports structurally OK." if ok else "\nMISMATCH - recheck transcription.")
