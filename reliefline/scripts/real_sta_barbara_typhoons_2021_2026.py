"""
REAL records given to the team: Santa Barbara per-barangay disaster reports
for 14 typhoon reports, 2021-2026, all 29 barangays per file, in the same
14-report structure as Calasiao's and Urdaneta's sets.

Current version = the Sta. Barbara set delivered 2026-10-03 (second delivery
that day). It REPLACES real_sta_barbara_typhoons_2021_2025.py (7 reports, on
different figures for the same storms - e.g. Egay 2023 7,803 packs there vs
3,826 here, Kristine 2024 1,571 vs 1 here) and
retires sample_sta_barbara_aug2026.py from the loader: this set's
Luis & Maymay & Neneng & Pilandok (2026) report has exactly the same
per-barangay pack counts as that Aug 2026 DSWD+LGU distribution sheet
(DSWD + LGU lots summed, e.g. Alibago 497 + 200 = 697, Tuliao 800 + 800 =
1,600), now with affected-family and population figures - loading both
would count the same 14,071 packs twice. New vs the old module: the 2026
report, Paolo / Uwan / Mirasol & Nando & Opong (2025), Nika & Ofel & Pepito
(2024), Karding (2022), Fabian (2021); Kristine 2024 is now Kristine & Leon.

Unaffected barangays are 0 rows - CONFIRMED zeros, loaded as 0 (they count
toward the share fit like Urdaneta's and Calasiao's zeros).

Each report links to every storm its "Name of Typhoon" column names (see
_storms.py; the typhoon calendar is built from these reports - see
scripts/typhoon_calendar_from_reports.py) - one relief_events row each, not
a per-storm split the source data can't support. Combined reports:
  Luis & Maymay & Neneng & Pilandok (2026) -> luis_2026, maymay_2026,
                                     neneng_2026, pilandok_2026
  Mirasol & Nando & Opong (Sep 2025) -> mirasol_2025, nando_2025, opong_2025
  Crising & Dante & Emong (Jul 2025) -> crising_2025, dante_2025, emong_2025
  Nika & Ofel & Pepito    (Nov 2024) -> nika_2024, ofel_2024, pepito_2024
  Kristine & Leon         (Oct 2024) -> kristine_2024, leon_2024
"& Habagat" in a source file name (Enteng, Carina, Egay) is not a calendar
typhoon and maps to the named storm only.

Source dates are DD/MM/YYYY, some a "start - end" range; parse() converts
them to ISO, taking the start of a range. The CSV text is kept exactly as
given.

Data-quality notes kept from the source (not corrected - figures are as given):
  * Luis & Maymay & Neneng & Pilandok 2026: packs exceed affected families
    in several barangays (e.g. Alibago 697 / 352, Tuliao 1,600 / 1,127) -
    plausibly more than one distribution across the four storms - and five
    barangays report affected families but 0 packs (Botao, Maronong,
    Patayac, Primicias, Tebag East).
  * Near-zero events: Kristine & Leon 2024 (1 pack, Sonquil only), Karding
    2022 (6 packs), Paeng 2022 (10 packs). Kept - they are real "no
    significant relief" outcomes.
  * "Total Number of Families" is one snapshot for the 2021-2023 reports
    (e.g. Alibago 393) and another for 2024-2026 (Alibago 452).

Run this file to print a structural sanity check per report.
"""
import csv
import io
from datetime import datetime

from _barangay_names import strip_accents_and_punct
from _storms import storm_keys

_FILES = {
    "luis_maymay_neneng_pilandok_2026": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,352,1678,697,452,1744
Sta. Barbara,Balingueo,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,683,3298,300,1110,3920
Sta. Barbara,Banaoang,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,854,4367,653,1214,4536
Sta. Barbara,Banzal,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,332,1647,550,461,1712
Sta. Barbara,Botao,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,182,902,0,1001,3467
Sta. Barbara,Cablong,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,574,2979,507,868,3093
Sta. Barbara,Carusocan,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,309,1435,200,504,1960
Sta. Barbara,Dalongue,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,409,2143,729,680,2228
Sta. Barbara,Erfe,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,124,642,250,218,670
Sta. Barbara,Gueguesangen,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,341,1794,350,497,1864
Sta. Barbara,Leet,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,1426,6716,1017,1842,6968
Sta. Barbara,Malanay,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,589,2780,674,771,2884
Sta. Barbara,Maningding,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,900,4745,1012,1419,4930
Sta. Barbara,Maronong,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,577,2782,0,982,3479
Sta. Barbara,Maticmatic,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,930,4834,420,1280,5017
Sta. Barbara,Minien East,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,578,2946,275,969,3350
Sta. Barbara,Minien West,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,372,1810,25,1634,5273
Sta. Barbara,Nilombot,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,507,2495,550,706,2592
Sta. Barbara,Patayac,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,164,836,0,814,2843
Sta. Barbara,Payas,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,815,3855,400,1077,4002
Sta. Barbara,Poblacion Norte,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,778,3730,450,914,3872
Sta. Barbara,Poblacion Sur,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,320,1499,275,531,1556
Sta. Barbara,Primicias,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,377,1840,0,614,1909
Sta. Barbara,Sapang,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,433,2260,600,644,2346
Sta. Barbara,Sonquil,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,623,3249,1037,893,3375
Sta. Barbara,Tebag East,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,21,108,0,116,371
Sta. Barbara,Tebag West,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,500,2551,400,765,2650
Sta. Barbara,Tuliao,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,1127,5959,1600,1715,6187
Sta. Barbara,Ventinilla,"Luis, Maymay, Neneng, Pilandok ",01/08/2026 - 02/09/2026,677,3490,1100,972,3622
""",
    "uwan_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Uwan,09/11/2025 - 10/11/2025,39,151,34,452,1744
Sta. Barbara,Balingueo,Uwan,09/11/2025 - 10/11/2025,30,117,18,1110,3920
Sta. Barbara,Banaoang,Uwan,09/11/2025 - 10/11/2025,92,395,76,1214,4536
Sta. Barbara,Banzal,Uwan,09/11/2025 - 10/11/2025,49,196,42,461,1712
Sta. Barbara,Botao,Uwan,09/11/2025 - 10/11/2025,24,100,13,1001,3467
Sta. Barbara,Cablong,Uwan,09/11/2025 - 10/11/2025,23,95,13,868,3093
Sta. Barbara,Carusocan,Uwan,09/11/2025 - 10/11/2025,10,39,5,504,1960
Sta. Barbara,Dalongue,Uwan,09/11/2025 - 10/11/2025,60,244,50,680,2228
Sta. Barbara,Erfe,Uwan,09/11/2025 - 10/11/2025,7,27,4,218,670
Sta. Barbara,Gueguesangen,Uwan,09/11/2025 - 10/11/2025,14,54,9,497,1864
Sta. Barbara,Leet,Uwan,09/11/2025 - 10/11/2025,202,786,179,1842,6968
Sta. Barbara,Malanay,Uwan,09/11/2025 - 10/11/2025,89,385,76,771,2884
Sta. Barbara,Maningding,Uwan,09/11/2025 - 10/11/2025,111,440,88,1419,4930
Sta. Barbara,Maronong,Uwan,09/11/2025 - 10/11/2025,88,381,77,982,3479
Sta. Barbara,Maticmatic,Uwan,09/11/2025 - 10/11/2025,123,464,96,1280,5017
Sta. Barbara,Minien East,Uwan,09/11/2025 - 10/11/2025,25,105,16,969,3350
Sta. Barbara,Minien West,Uwan,09/11/2025 - 10/11/2025,32,135,15,1634,5273
Sta. Barbara,Nilombot,Uwan,09/11/2025 - 10/11/2025,57,227,46,706,2592
Sta. Barbara,Patayac,Uwan,09/11/2025 - 10/11/2025,22,86,15,814,2843
Sta. Barbara,Payas,Uwan,09/11/2025 - 10/11/2025,124,478,105,1077,4002
Sta. Barbara,Poblacion Norte,Uwan,09/11/2025 - 10/11/2025,90,358,70,914,3872
Sta. Barbara,Poblacion Sur,Uwan,09/11/2025 - 10/11/2025,42,159,39,531,1556
Sta. Barbara,Primicias,Uwan,09/11/2025 - 10/11/2025,50,202,42,614,1909
Sta. Barbara,Sapang,Uwan,09/11/2025 - 10/11/2025,71,302,57,644,2346
Sta. Barbara,Sonquil,Uwan,09/11/2025 - 10/11/2025,80,343,69,893,3375
Sta. Barbara,Tebag East,Uwan,09/11/2025 - 10/11/2025,3,12,1,116,371
Sta. Barbara,Tebag West,Uwan,09/11/2025 - 10/11/2025,19,76,10,765,2650
Sta. Barbara,Tuliao,Uwan,09/11/2025 - 10/11/2025,135,549,125,1715,6187
Sta. Barbara,Ventinilla,Uwan,09/11/2025 - 10/11/2025,95,405,78,972,3622
""",
    "paolo_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Paolo,02/10/2025 - 04/10/2025,17,67,13,452,1744
Sta. Barbara,Balingueo,Paolo,02/10/2025 - 04/10/2025,8,31,4,1110,3920
Sta. Barbara,Banaoang,Paolo,02/10/2025 - 04/10/2025,36,145,26,1214,4536
Sta. Barbara,Banzal,Paolo,02/10/2025 - 04/10/2025,17,63,15,461,1712
Sta. Barbara,Botao,Paolo,02/10/2025 - 04/10/2025,10,43,7,1001,3467
Sta. Barbara,Cablong,Paolo,02/10/2025 - 04/10/2025,8,33,4,868,3093
Sta. Barbara,Carusocan,Paolo,02/10/2025 - 04/10/2025,6,26,3,504,1960
Sta. Barbara,Dalongue,Paolo,02/10/2025 - 04/10/2025,17,65,12,680,2228
Sta. Barbara,Erfe,Paolo,02/10/2025 - 04/10/2025,3,13,2,218,670
Sta. Barbara,Gueguesangen,Paolo,02/10/2025 - 04/10/2025,6,23,3,497,1864
Sta. Barbara,Leet,Paolo,02/10/2025 - 04/10/2025,59,237,49,1842,6968
Sta. Barbara,Malanay,Paolo,02/10/2025 - 04/10/2025,20,75,17,771,2884
Sta. Barbara,Maningding,Paolo,02/10/2025 - 04/10/2025,46,177,32,1419,4930
Sta. Barbara,Maronong,Paolo,02/10/2025 - 04/10/2025,31,120,24,982,3479
Sta. Barbara,Maticmatic,Paolo,02/10/2025 - 04/10/2025,50,201,42,1280,5017
Sta. Barbara,Minien East,Paolo,02/10/2025 - 04/10/2025,9,34,4,969,3350
Sta. Barbara,Minien West,Paolo,02/10/2025 - 04/10/2025,16,64,10,1634,5273
Sta. Barbara,Nilombot,Paolo,02/10/2025 - 04/10/2025,23,89,19,706,2592
Sta. Barbara,Patayac,Paolo,02/10/2025 - 04/10/2025,6,25,3,814,2843
Sta. Barbara,Payas,Paolo,02/10/2025 - 04/10/2025,33,135,28,1077,4002
Sta. Barbara,Poblacion Norte,Paolo,02/10/2025 - 04/10/2025,34,145,30,914,3872
Sta. Barbara,Poblacion Sur,Paolo,02/10/2025 - 04/10/2025,15,63,13,531,1556
Sta. Barbara,Primicias,Paolo,02/10/2025 - 04/10/2025,19,76,18,614,1909
Sta. Barbara,Sapang,Paolo,02/10/2025 - 04/10/2025,25,99,22,644,2346
Sta. Barbara,Sonquil,Paolo,02/10/2025 - 04/10/2025,28,110,22,893,3375
Sta. Barbara,Tebag East,Paolo,02/10/2025 - 04/10/2025,2,8,1,116,371
Sta. Barbara,Tebag West,Paolo,02/10/2025 - 04/10/2025,6,23,4,765,2650
Sta. Barbara,Tuliao,Paolo,02/10/2025 - 04/10/2025,57,230,48,1715,6187
Sta. Barbara,Ventinilla,Paolo,02/10/2025 - 04/10/2025,31,133,23,972,3622
""",
    "mirasol_nando_opong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,201,884,173,452,1744
Sta. Barbara,Balingueo,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,140,647,81,1110,3920
Sta. Barbara,Banaoang,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,601,2819,509,1214,4536
Sta. Barbara,Banzal,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,242,1098,181,461,1712
Sta. Barbara,Botao,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,87,386,60,1001,3467
Sta. Barbara,Cablong,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,75,336,43,868,3093
Sta. Barbara,Carusocan,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,67,306,46,504,1960
Sta. Barbara,Dalongue,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,248,1052,205,680,2228
Sta. Barbara,Erfe,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,19,88,10,218,670
Sta. Barbara,Gueguesangen,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,51,224,34,497,1864
Sta. Barbara,Leet,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,841,4069,775,1842,6968
Sta. Barbara,Malanay,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,275,1336,199,771,2884
Sta. Barbara,Maningding,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,514,2297,428,1419,4930
Sta. Barbara,Maronong,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,317,1444,238,982,3479
Sta. Barbara,Maticmatic,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,685,2927,489,1280,5017
Sta. Barbara,Minien East,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,112,490,52,969,3350
Sta. Barbara,Minien West,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,193,845,95,1634,5273
Sta. Barbara,Nilombot,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,378,1700,335,706,2592
Sta. Barbara,Patayac,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,84,377,53,814,2843
Sta. Barbara,Payas,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,374,1679,346,1077,4002
Sta. Barbara,Poblacion Norte,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,303,1321,272,914,3872
Sta. Barbara,Poblacion Sur,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,247,1146,202,531,1556
Sta. Barbara,Primicias,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,208,902,151,614,1909
Sta. Barbara,Sapang,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,295,1255,260,644,2346
Sta. Barbara,Sonquil,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,460,1963,343,893,3375
Sta. Barbara,Tebag East,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,11,50,6,116,371
Sta. Barbara,Tebag West,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,99,452,57,765,2650
Sta. Barbara,Tuliao,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,917,3917,830,1715,6187
Sta. Barbara,Ventinilla,"Mirasol, Nando, Opong ",22/09/2025 - 27/09/2025,436,2114,374,972,3622
""",
    "crising_dante_emong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,339,1657,311,452,1744
Sta. Barbara,Balingueo,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,144,681,98,1110,3920
Sta. Barbara,Banaoang,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,871,4331,708,1214,4536
Sta. Barbara,Banzal,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,289,1350,243,461,1712
Sta. Barbara,Botao,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,153,715,104,1001,3467
Sta. Barbara,Cablong,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,156,721,86,868,3093
Sta. Barbara,Carusocan,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,80,407,37,504,1960
Sta. Barbara,Dalongue,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,447,2183,319,680,2228
Sta. Barbara,Erfe,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,40,208,26,218,670
Sta. Barbara,Gueguesangen,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,73,374,45,497,1864
Sta. Barbara,Leet,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,1232,5814,1138,1842,6968
Sta. Barbara,Malanay,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,349,1685,249,771,2884
Sta. Barbara,Maningding,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,807,4022,667,1419,4930
Sta. Barbara,Maronong,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,474,2381,350,982,3479
Sta. Barbara,Maticmatic,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,962,4508,792,1280,5017
Sta. Barbara,Minien East,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,138,722,93,969,3350
Sta. Barbara,Minien West,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,234,1170,117,1634,5273
Sta. Barbara,Nilombot,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,431,2208,325,706,2592
Sta. Barbara,Patayac,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,115,605,80,814,2843
Sta. Barbara,Payas,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,602,2966,438,1077,4002
Sta. Barbara,Poblacion Norte,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,624,3007,548,914,3872
Sta. Barbara,Poblacion Sur,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,287,1420,215,531,1556
Sta. Barbara,Primicias,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,288,1384,255,614,1909
Sta. Barbara,Sapang,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,460,2177,421,644,2346
Sta. Barbara,Sonquil,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,610,3176,537,893,3375
Sta. Barbara,Tebag East,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,20,99,12,116,371
Sta. Barbara,Tebag West,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,124,596,60,765,2650
Sta. Barbara,Tuliao,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,1052,5120,785,1715,6187
Sta. Barbara,Ventinilla,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,612,3048,565,972,3622
""",
    "nika_ofel_pepito_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,4,19,3,452,1744
Sta. Barbara,Balingueo,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,3,16,2,1110,3920
Sta. Barbara,Banaoang,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,8,42,7,1214,4536
Sta. Barbara,Banzal,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,3,15,3,461,1712
Sta. Barbara,Botao,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,3,16,2,1001,3467
Sta. Barbara,Cablong,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,2,9,1,868,3093
Sta. Barbara,Carusocan,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,2,10,1,504,1960
Sta. Barbara,Dalongue,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,8,40,6,680,2228
Sta. Barbara,Erfe,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,1,5,1,218,670
Sta. Barbara,Gueguesangen,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,2,10,1,497,1864
Sta. Barbara,Leet,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,13,67,12,1842,6968
Sta. Barbara,Malanay,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,5,25,4,771,2884
Sta. Barbara,Maningding,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,9,47,7,1419,4930
Sta. Barbara,Maronong,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,7,37,6,982,3479
Sta. Barbara,Maticmatic,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,9,47,8,1280,5017
Sta. Barbara,Minien East,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,3,15,1,969,3350
Sta. Barbara,Minien West,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,4,20,2,1634,5273
Sta. Barbara,Nilombot,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,5,23,4,706,2592
Sta. Barbara,Patayac,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,2,10,1,814,2843
Sta. Barbara,Payas,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,6,31,5,1077,4002
Sta. Barbara,Poblacion Norte,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,6,31,5,914,3872
Sta. Barbara,Poblacion Sur,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,4,21,3,531,1556
Sta. Barbara,Primicias,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,6,30,4,614,1909
Sta. Barbara,Sapang,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,5,25,4,644,2346
Sta. Barbara,Sonquil,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,10,53,8,893,3375
Sta. Barbara,Tebag East,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,1,5,1,116,371
Sta. Barbara,Tebag West,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,2,10,1,765,2650
Sta. Barbara,Tuliao,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,11,55,8,1715,6187
Sta. Barbara,Ventinilla,"Nika, Ofel, Pepito ",11/11/2024 - 19/11/2024,8,41,7,972,3622
""",
    "kristine_leon_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,452,1744
Sta. Barbara,Balingueo,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1110,3920
Sta. Barbara,Banaoang,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1214,4536
Sta. Barbara,Banzal,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,461,1712
Sta. Barbara,Botao,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1001,3467
Sta. Barbara,Cablong,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,868,3093
Sta. Barbara,Carusocan,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,504,1960
Sta. Barbara,Dalongue,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,680,2228
Sta. Barbara,Erfe,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,218,670
Sta. Barbara,Gueguesangen,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,497,1864
Sta. Barbara,Leet,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1842,6968
Sta. Barbara,Malanay,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,771,2884
Sta. Barbara,Maningding,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1419,4930
Sta. Barbara,Maronong,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,982,3479
Sta. Barbara,Maticmatic,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1280,5017
Sta. Barbara,Minien East,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,969,3350
Sta. Barbara,Minien West,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1634,5273
Sta. Barbara,Nilombot,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,706,2592
Sta. Barbara,Patayac,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,814,2843
Sta. Barbara,Payas,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1077,4002
Sta. Barbara,Poblacion Norte,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,914,3872
Sta. Barbara,Poblacion Sur,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,531,1556
Sta. Barbara,Primicias,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,614,1909
Sta. Barbara,Sapang,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,644,2346
Sta. Barbara,Sonquil,"Kristine, Leon ",23/10/2024 - 29/10/2024,1,5,1,893,3375
Sta. Barbara,Tebag East,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,116,371
Sta. Barbara,Tebag West,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,765,2650
Sta. Barbara,Tuliao,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,1715,6187
Sta. Barbara,Ventinilla,"Kristine, Leon ",23/10/2024 - 29/10/2024,0,0,0,972,3622
""",
    "enteng_habagat_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Enteng,04/09/2024 - 12/09/2024,74,291,66,452,1744
Sta. Barbara,Balingueo,Enteng,04/09/2024 - 12/09/2024,44,185,25,1110,3920
Sta. Barbara,Banaoang,Enteng,04/09/2024 - 12/09/2024,228,883,211,1214,4536
Sta. Barbara,Banzal,Enteng,04/09/2024 - 12/09/2024,93,385,79,461,1712
Sta. Barbara,Botao,Enteng,04/09/2024 - 12/09/2024,45,171,24,1001,3467
Sta. Barbara,Cablong,Enteng,04/09/2024 - 12/09/2024,43,176,28,868,3093
Sta. Barbara,Carusocan,Enteng,04/09/2024 - 12/09/2024,25,95,14,504,1960
Sta. Barbara,Dalongue,Enteng,04/09/2024 - 12/09/2024,118,490,90,680,2228
Sta. Barbara,Erfe,Enteng,04/09/2024 - 12/09/2024,9,37,6,218,670
Sta. Barbara,Gueguesangen,Enteng,04/09/2024 - 12/09/2024,18,75,12,497,1864
Sta. Barbara,Leet,Enteng,04/09/2024 - 12/09/2024,270,1059,196,1842,6968
Sta. Barbara,Malanay,Enteng,04/09/2024 - 12/09/2024,151,613,111,771,2884
Sta. Barbara,Maningding,Enteng,04/09/2024 - 12/09/2024,287,1210,226,1419,4930
Sta. Barbara,Maronong,Enteng,04/09/2024 - 12/09/2024,139,531,118,982,3479
Sta. Barbara,Maticmatic,Enteng,04/09/2024 - 12/09/2024,228,906,178,1280,5017
Sta. Barbara,Minien East,Enteng,04/09/2024 - 12/09/2024,36,150,22,969,3350
Sta. Barbara,Minien West,Enteng,04/09/2024 - 12/09/2024,84,324,39,1634,5273
Sta. Barbara,Nilombot,Enteng,04/09/2024 - 12/09/2024,130,535,92,706,2592
Sta. Barbara,Patayac,Enteng,04/09/2024 - 12/09/2024,37,137,20,814,2843
Sta. Barbara,Payas,Enteng,04/09/2024 - 12/09/2024,165,691,119,1077,4002
Sta. Barbara,Poblacion Norte,Enteng,04/09/2024 - 12/09/2024,158,596,143,914,3872
Sta. Barbara,Poblacion Sur,Enteng,04/09/2024 - 12/09/2024,104,417,83,531,1556
Sta. Barbara,Primicias,Enteng,04/09/2024 - 12/09/2024,82,330,66,614,1909
Sta. Barbara,Sapang,Enteng,04/09/2024 - 12/09/2024,100,375,74,644,2346
Sta. Barbara,Sonquil,Enteng,04/09/2024 - 12/09/2024,144,559,126,893,3375
Sta. Barbara,Tebag East,Enteng,04/09/2024 - 12/09/2024,5,21,3,116,371
Sta. Barbara,Tebag West,Enteng,04/09/2024 - 12/09/2024,33,128,21,765,2650
Sta. Barbara,Tuliao,Enteng,04/09/2024 - 12/09/2024,348,1449,252,1715,6187
Sta. Barbara,Ventinilla,Enteng,04/09/2024 - 12/09/2024,189,729,172,972,3622
""",
    "carina_habagat_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Carina,22/07/2024 - 26/07/2024,4,19,3,452,1744
Sta. Barbara,Balingueo,Carina,22/07/2024 - 26/07/2024,2,10,1,1110,3920
Sta. Barbara,Banaoang,Carina,22/07/2024 - 26/07/2024,8,42,7,1214,4536
Sta. Barbara,Banzal,Carina,22/07/2024 - 26/07/2024,4,19,3,461,1712
Sta. Barbara,Botao,Carina,22/07/2024 - 26/07/2024,2,9,1,1001,3467
Sta. Barbara,Cablong,Carina,22/07/2024 - 26/07/2024,2,10,1,868,3093
Sta. Barbara,Carusocan,Carina,22/07/2024 - 26/07/2024,2,10,1,504,1960
Sta. Barbara,Dalongue,Carina,22/07/2024 - 26/07/2024,5,26,4,680,2228
Sta. Barbara,Erfe,Carina,22/07/2024 - 26/07/2024,1,5,1,218,670
Sta. Barbara,Gueguesangen,Carina,22/07/2024 - 26/07/2024,2,10,1,497,1864
Sta. Barbara,Leet,Carina,22/07/2024 - 26/07/2024,11,57,10,1842,6968
Sta. Barbara,Malanay,Carina,22/07/2024 - 26/07/2024,4,21,3,771,2884
Sta. Barbara,Maningding,Carina,22/07/2024 - 26/07/2024,7,37,5,1419,4930
Sta. Barbara,Maronong,Carina,22/07/2024 - 26/07/2024,6,28,5,982,3479
Sta. Barbara,Maticmatic,Carina,22/07/2024 - 26/07/2024,9,46,7,1280,5017
Sta. Barbara,Minien East,Carina,22/07/2024 - 26/07/2024,2,10,1,969,3350
Sta. Barbara,Minien West,Carina,22/07/2024 - 26/07/2024,3,15,2,1634,5273
Sta. Barbara,Nilombot,Carina,22/07/2024 - 26/07/2024,4,20,3,706,2592
Sta. Barbara,Patayac,Carina,22/07/2024 - 26/07/2024,2,10,1,814,2843
Sta. Barbara,Payas,Carina,22/07/2024 - 26/07/2024,6,30,5,1077,4002
Sta. Barbara,Poblacion Norte,Carina,22/07/2024 - 26/07/2024,7,33,6,914,3872
Sta. Barbara,Poblacion Sur,Carina,22/07/2024 - 26/07/2024,4,21,3,531,1556
Sta. Barbara,Primicias,Carina,22/07/2024 - 26/07/2024,5,24,4,614,1909
Sta. Barbara,Sapang,Carina,22/07/2024 - 26/07/2024,5,26,4,644,2346
Sta. Barbara,Sonquil,Carina,22/07/2024 - 26/07/2024,5,24,5,893,3375
Sta. Barbara,Tebag East,Carina,22/07/2024 - 26/07/2024,1,5,1,116,371
Sta. Barbara,Tebag West,Carina,22/07/2024 - 26/07/2024,2,10,1,765,2650
Sta. Barbara,Tuliao,Carina,22/07/2024 - 26/07/2024,8,37,6,1715,6187
Sta. Barbara,Ventinilla,Carina,22/07/2024 - 26/07/2024,7,36,5,972,3622
""",
    "egay_habagat_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Egay,25/07/2023,140,656,104,393,1564
Sta. Barbara,Balingueo,Egay,25/07/2023,69,324,40,885,3911
Sta. Barbara,Banaoang,Egay,25/07/2023,262,1344,212,1066,4477
Sta. Barbara,Banzal,Egay,25/07/2023,107,515,91,422,1571
Sta. Barbara,Botao,Egay,25/07/2023,47,246,28,788,3401
Sta. Barbara,Cablong,Egay,25/07/2023,46,232,24,671,3058
Sta. Barbara,Carusocan,Egay,25/07/2023,46,220,28,479,1876
Sta. Barbara,Dalongue,Egay,25/07/2023,115,609,86,470,2030
Sta. Barbara,Erfe,Egay,25/07/2023,15,73,8,179,652
Sta. Barbara,Gueguesangen,Egay,25/07/2023,33,172,16,443,1831
Sta. Barbara,Leet,Egay,25/07/2023,500,2387,445,1724,7275
Sta. Barbara,Malanay,Egay,25/07/2023,199,996,147,638,2764
Sta. Barbara,Maningding,Egay,25/07/2023,373,1765,322,1188,4890
Sta. Barbara,Maronong,Egay,25/07/2023,275,1281,252,802,3304
Sta. Barbara,Maticmatic,Egay,25/07/2023,344,1757,253,1165,5116
Sta. Barbara,Minien East,Egay,25/07/2023,44,232,27,759,3260
Sta. Barbara,Minien West,Egay,25/07/2023,86,403,47,1264,5230
Sta. Barbara,Nilombot,Egay,25/07/2023,211,1124,181,577,2434
Sta. Barbara,Patayac,Egay,25/07/2023,46,234,25,704,2880
Sta. Barbara,Payas,Egay,25/07/2023,198,1039,153,858,3928
Sta. Barbara,Poblacion Norte,Egay,25/07/2023,308,1565,251,1059,4677
Sta. Barbara,Poblacion Sur,Egay,25/07/2023,135,665,104,455,1766
Sta. Barbara,Primicias,Egay,25/07/2023,115,601,105,472,1819
Sta. Barbara,Sapang,Egay,25/07/2023,144,759,127,531,2315
Sta. Barbara,Sonquil,Egay,25/07/2023,258,1302,196,771,3272
Sta. Barbara,Tebag East,Egay,25/07/2023,9,46,5,118,439
Sta. Barbara,Tebag West,Egay,25/07/2023,38,202,22,592,2538
Sta. Barbara,Tuliao,Egay,25/07/2023,455,2267,331,1503,6424
Sta. Barbara,Ventinilla,Egay,25/07/2023,277,1461,196,833,3485
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Paeng,29/10/2022,0,0,0,393,1564
Sta. Barbara,Balingueo,Paeng,29/10/2022,0,0,0,885,3911
Sta. Barbara,Banaoang,Paeng,29/10/2022,1,5,1,1066,4477
Sta. Barbara,Banzal,Paeng,29/10/2022,0,0,0,422,1571
Sta. Barbara,Botao,Paeng,29/10/2022,0,0,0,788,3401
Sta. Barbara,Cablong,Paeng,29/10/2022,0,0,0,671,3058
Sta. Barbara,Carusocan,Paeng,29/10/2022,0,0,0,479,1876
Sta. Barbara,Dalongue,Paeng,29/10/2022,0,0,0,470,2030
Sta. Barbara,Erfe,Paeng,29/10/2022,0,0,0,179,652
Sta. Barbara,Gueguesangen,Paeng,29/10/2022,0,0,0,443,1831
Sta. Barbara,Leet,Paeng,29/10/2022,1,5,1,1724,7275
Sta. Barbara,Malanay,Paeng,29/10/2022,1,5,1,638,2764
Sta. Barbara,Maningding,Paeng,29/10/2022,1,5,1,1188,4890
Sta. Barbara,Maronong,Paeng,29/10/2022,0,0,0,802,3304
Sta. Barbara,Maticmatic,Paeng,29/10/2022,1,5,1,1165,5116
Sta. Barbara,Minien East,Paeng,29/10/2022,0,0,0,759,3260
Sta. Barbara,Minien West,Paeng,29/10/2022,0,0,0,1264,5230
Sta. Barbara,Nilombot,Paeng,29/10/2022,0,0,0,577,2434
Sta. Barbara,Patayac,Paeng,29/10/2022,0,0,0,704,2880
Sta. Barbara,Payas,Paeng,29/10/2022,1,5,1,858,3928
Sta. Barbara,Poblacion Norte,Paeng,29/10/2022,1,5,1,1059,4677
Sta. Barbara,Poblacion Sur,Paeng,29/10/2022,0,0,0,455,1766
Sta. Barbara,Primicias,Paeng,29/10/2022,0,0,0,472,1819
Sta. Barbara,Sapang,Paeng,29/10/2022,0,0,0,531,2315
Sta. Barbara,Sonquil,Paeng,29/10/2022,2,10,2,771,3272
Sta. Barbara,Tebag East,Paeng,29/10/2022,0,0,0,118,439
Sta. Barbara,Tebag West,Paeng,29/10/2022,0,0,0,592,2538
Sta. Barbara,Tuliao,Paeng,29/10/2022,1,5,1,1503,6424
Sta. Barbara,Ventinilla,Paeng,29/10/2022,0,0,0,833,3485
""",
    "karding_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Karding,25/09/2022 - 26/09/2022,0,0,0,393,1564
Sta. Barbara,Balingueo,Karding,25/09/2022 - 26/09/2022,0,0,0,885,3911
Sta. Barbara,Banaoang,Karding,25/09/2022 - 26/09/2022,0,0,0,1066,4477
Sta. Barbara,Banzal,Karding,25/09/2022 - 26/09/2022,0,0,0,422,1571
Sta. Barbara,Botao,Karding,25/09/2022 - 26/09/2022,0,0,0,788,3401
Sta. Barbara,Cablong,Karding,25/09/2022 - 26/09/2022,0,0,0,671,3058
Sta. Barbara,Carusocan,Karding,25/09/2022 - 26/09/2022,0,0,0,479,1876
Sta. Barbara,Dalongue,Karding,25/09/2022 - 26/09/2022,0,0,0,470,2030
Sta. Barbara,Erfe,Karding,25/09/2022 - 26/09/2022,0,0,0,179,652
Sta. Barbara,Gueguesangen,Karding,25/09/2022 - 26/09/2022,0,0,0,443,1831
Sta. Barbara,Leet,Karding,25/09/2022 - 26/09/2022,1,4,1,1724,7275
Sta. Barbara,Malanay,Karding,25/09/2022 - 26/09/2022,0,0,0,638,2764
Sta. Barbara,Maningding,Karding,25/09/2022 - 26/09/2022,1,5,1,1188,4890
Sta. Barbara,Maronong,Karding,25/09/2022 - 26/09/2022,0,0,0,802,3304
Sta. Barbara,Maticmatic,Karding,25/09/2022 - 26/09/2022,1,4,1,1165,5116
Sta. Barbara,Minien East,Karding,25/09/2022 - 26/09/2022,0,0,0,759,3260
Sta. Barbara,Minien West,Karding,25/09/2022 - 26/09/2022,0,0,0,1264,5230
Sta. Barbara,Nilombot,Karding,25/09/2022 - 26/09/2022,0,0,0,577,2434
Sta. Barbara,Patayac,Karding,25/09/2022 - 26/09/2022,0,0,0,704,2880
Sta. Barbara,Payas,Karding,25/09/2022 - 26/09/2022,0,0,0,858,3928
Sta. Barbara,Poblacion Norte,Karding,25/09/2022 - 26/09/2022,0,0,0,1059,4677
Sta. Barbara,Poblacion Sur,Karding,25/09/2022 - 26/09/2022,0,0,0,455,1766
Sta. Barbara,Primicias,Karding,25/09/2022 - 26/09/2022,0,0,0,472,1819
Sta. Barbara,Sapang,Karding,25/09/2022 - 26/09/2022,0,0,0,531,2315
Sta. Barbara,Sonquil,Karding,25/09/2022 - 26/09/2022,1,4,1,771,3272
Sta. Barbara,Tebag East,Karding,25/09/2022 - 26/09/2022,0,0,0,118,439
Sta. Barbara,Tebag West,Karding,25/09/2022 - 26/09/2022,0,0,0,592,2538
Sta. Barbara,Tuliao,Karding,25/09/2022 - 26/09/2022,1,5,1,1503,6424
Sta. Barbara,Ventinilla,Karding,25/09/2022 - 26/09/2022,1,5,1,833,3485
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Maring,28/10/2021,223,1167,197,393,1564
Sta. Barbara,Balingueo,Maring,28/10/2021,153,773,88,885,3911
Sta. Barbara,Banaoang,Maring,28/10/2021,716,3743,535,1066,4477
Sta. Barbara,Banzal,Maring,28/10/2021,191,1010,155,422,1571
Sta. Barbara,Botao,Maring,28/10/2021,122,590,75,788,3401
Sta. Barbara,Cablong,Maring,28/10/2021,102,489,55,671,3058
Sta. Barbara,Carusocan,Maring,28/10/2021,81,402,43,479,1876
Sta. Barbara,Dalongue,Maring,28/10/2021,250,1183,218,470,2030
Sta. Barbara,Erfe,Maring,28/10/2021,21,99,12,179,652
Sta. Barbara,Gueguesangen,Maring,28/10/2021,72,381,44,443,1831
Sta. Barbara,Leet,Maring,28/10/2021,1066,5346,876,1724,7275
Sta. Barbara,Malanay,Maring,28/10/2021,373,1772,329,638,2764
Sta. Barbara,Maningding,Maring,28/10/2021,595,2834,507,1188,4890
Sta. Barbara,Maronong,Maring,28/10/2021,456,2158,376,802,3304
Sta. Barbara,Maticmatic,Maring,28/10/2021,774,4088,579,1165,5116
Sta. Barbara,Minien East,Maring,28/10/2021,98,470,50,759,3260
Sta. Barbara,Minien West,Maring,28/10/2021,167,828,107,1264,5230
Sta. Barbara,Nilombot,Maring,28/10/2021,401,1912,362,577,2434
Sta. Barbara,Patayac,Maring,28/10/2021,76,385,44,704,2880
Sta. Barbara,Payas,Maring,28/10/2021,586,2875,476,858,3928
Sta. Barbara,Poblacion Norte,Maring,28/10/2021,744,3836,596,1059,4677
Sta. Barbara,Poblacion Sur,Maring,28/10/2021,226,1070,183,455,1766
Sta. Barbara,Primicias,Maring,28/10/2021,233,1144,170,472,1819
Sta. Barbara,Sapang,Maring,28/10/2021,285,1319,252,531,2315
Sta. Barbara,Sonquil,Maring,28/10/2021,420,2011,366,771,3272
Sta. Barbara,Tebag East,Maring,28/10/2021,17,88,8,118,439
Sta. Barbara,Tebag West,Maring,28/10/2021,85,437,47,592,2538
Sta. Barbara,Tuliao,Maring,28/10/2021,820,3993,696,1503,6424
Sta. Barbara,Ventinilla,Maring,28/10/2021,558,2772,516,833,3485
""",
    "fabian_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Fabian,22/07/2021 - 26/07/2021,36,189,26,393,1564
Sta. Barbara,Balingueo,Fabian,22/07/2021 - 26/07/2021,19,88,10,885,3911
Sta. Barbara,Banaoang,Fabian,22/07/2021 - 26/07/2021,87,453,66,1066,4477
Sta. Barbara,Banzal,Fabian,22/07/2021 - 26/07/2021,35,177,29,422,1571
Sta. Barbara,Botao,Fabian,22/07/2021 - 26/07/2021,19,95,12,788,3401
Sta. Barbara,Cablong,Fabian,22/07/2021 - 26/07/2021,15,72,8,671,3058
Sta. Barbara,Carusocan,Fabian,22/07/2021 - 26/07/2021,11,58,6,479,1876
Sta. Barbara,Dalongue,Fabian,22/07/2021 - 26/07/2021,31,151,22,470,2030
Sta. Barbara,Erfe,Fabian,22/07/2021 - 26/07/2021,5,26,3,179,652
Sta. Barbara,Gueguesangen,Fabian,22/07/2021 - 26/07/2021,9,47,4,443,1831
Sta. Barbara,Leet,Fabian,22/07/2021 - 26/07/2021,118,587,86,1724,7275
Sta. Barbara,Malanay,Fabian,22/07/2021 - 26/07/2021,60,278,54,638,2764
Sta. Barbara,Maningding,Fabian,22/07/2021 - 26/07/2021,101,533,87,1188,4890
Sta. Barbara,Maronong,Fabian,22/07/2021 - 26/07/2021,52,272,41,802,3304
Sta. Barbara,Maticmatic,Fabian,22/07/2021 - 26/07/2021,107,519,76,1165,5116
Sta. Barbara,Minien East,Fabian,22/07/2021 - 26/07/2021,17,86,12,759,3260
Sta. Barbara,Minien West,Fabian,22/07/2021 - 26/07/2021,29,143,15,1264,5230
Sta. Barbara,Nilombot,Fabian,22/07/2021 - 26/07/2021,52,247,41,577,2434
Sta. Barbara,Patayac,Fabian,22/07/2021 - 26/07/2021,17,80,11,704,2880
Sta. Barbara,Payas,Fabian,22/07/2021 - 26/07/2021,74,378,60,858,3928
Sta. Barbara,Poblacion Norte,Fabian,22/07/2021 - 26/07/2021,105,529,84,1059,4677
Sta. Barbara,Poblacion Sur,Fabian,22/07/2021 - 26/07/2021,28,143,22,455,1766
Sta. Barbara,Primicias,Fabian,22/07/2021 - 26/07/2021,41,209,30,472,1819
Sta. Barbara,Sapang,Fabian,22/07/2021 - 26/07/2021,44,211,36,531,2315
Sta. Barbara,Sonquil,Fabian,22/07/2021 - 26/07/2021,57,269,42,771,3272
Sta. Barbara,Tebag East,Fabian,22/07/2021 - 26/07/2021,3,16,1,118,439
Sta. Barbara,Tebag West,Fabian,22/07/2021 - 26/07/2021,12,56,6,592,2538
Sta. Barbara,Tuliao,Fabian,22/07/2021 - 26/07/2021,129,657,105,1503,6424
Sta. Barbara,Ventinilla,Fabian,22/07/2021 - 26/07/2021,77,381,69,833,3485
""",
}

def normalize(name):
    return strip_accents_and_punct(name)


def _iso_date(raw):
    """'22/07/2025 - 25/07/2025' -> '2025-07-22' (DD/MM/YYYY, start of range)."""
    return datetime.strptime(raw.split(" - ")[0].strip(), "%d/%m/%Y").date().isoformat()


def parse(report_key):
    reader = csv.DictReader(io.StringIO(_FILES[report_key]))
    return [{
        "barangay": r["Barangay"],
        "storm": r["Name of Typhoon"],
        "date": _iso_date(r["Date ng Typhoon"]),
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
        affected = sum(1 for r in rows if r["food_packs_given"] > 0)
        good = len(rows) == 29 and len({normalize(r["barangay"]) for r in rows}) == 29
        ok &= good
        print(f"{rep['key']:<34} {rows[0]['date']} 29 brgy={good!s:<6} served={affected:>2}/29 "
              f"families={fam:>6,} packs={packs:>6,}  {'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Sta. Barbara reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
