"""
REAL records given to the team: Santa Barbara per-barangay disaster reports
for 7 typhoon reports, 2021-2025, all 29 barangays per file (updated dataset
delivered 2026-10-03), alongside the Aug-2026 DSWD+LGU distribution sheet
(scripts/sample_sta_barbara_aug2026.py - unchanged by the update).

This dataset REPLACES the previous version of this module entirely (same
decision as Calasiao's, 2026-10-03): the old figures were on a different
scale for the overlapping events (e.g. Paeng 2022 4,376 packs vs 8 here) and
two of its typhoons (Karding 2022, Fabian 2021) are not in the updated set,
so they were dropped rather than mixed with the new scale. Kristine 2024 and
Carina 2024 are new.

Unaffected barangays are 0 rows in every file - CONFIRMED zeros, loaded as 0
(they count toward the share fit like Urdaneta's and Calasiao's zeros).

The Crising/Dante/Emong file (Jul 2025) is a single relief report covering
THREE calendar typhoons - it maps to three typhoon_keys via one relief_events
row and three relief_event_typhoons rows, not a per-storm split the source
data can't support.

Source dates are DD/MM/YYYY (Crising/Dante/Emong a "start - end" range);
parse() converts them to ISO, taking the start of a range. The CSV text is
kept exactly as given.

Data-quality notes kept from the source (not corrected - figures are as given):
  * Paeng 2022 / Maring 2021 "Total Number of Families" are roughly half the
    2023+ figures for the same barangays (e.g. Alibago 177/172 vs 361 in Egay
    2023) while "Total Number of Individuals" is identical - possibly a
    different family definition in the older sheets.
  * Maring 2021: Tuliao affected families = total families (684).
  * Maring is dated 28/10/2021 here; the typhoon calendar's key date is
    2021-10-11 (the report date is only used to order snapshots/backtests).

Run this file to print a structural sanity check per report.
"""
import csv
import io
from datetime import datetime

from _barangay_names import strip_accents_and_punct

_FILES = {
    # Combined report: three calendar typhoons in one relief distribution.
    "crising_dante_emong_2025": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,314,1527,230,480,1789
Sta. Barbara,Balingueo,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,799,3840,524,1053,3922
Sta. Barbara,Banaoang,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,912,4389,662,1222,4551
Sta. Barbara,Banzal,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,143,659,86,469,1747
Sta. Barbara,Botao,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,317,1532,193,935,3484
Sta. Barbara,Cablong,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,279,1327,166,833,3102
Sta. Barbara,Carusocan,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,207,951,111,532,1981
Sta. Barbara,Dalongue,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,437,2207,323,612,2278
Sta. Barbara,Erfe,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,52,226,28,181,675
Sta. Barbara,Gueguesangen,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,125,596,71,503,1872
Sta. Barbara,Leet,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,761,3639,534,1850,6891
Sta. Barbara,Malanay,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,515,2640,376,782,2914
Sta. Barbara,Maningding,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,935,4763,746,1326,4940
Sta. Barbara,Maronong,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,237,1098,145,946,3523
Sta. Barbara,Maticmatic,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,933,4534,634,1340,4992
Sta. Barbara,Minien East,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,338,1681,186,906,3373
Sta. Barbara,Minien West,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,394,1958,197,1419,5284
Sta. Barbara,Nilombot,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,290,1464,175,707,2632
Sta. Barbara,Patayac,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,320,1544,188,761,2834
Sta. Barbara,Payas,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,258,1283,148,1079,4021
Sta. Barbara,Poblacion Norte,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,614,3063,424,986,3671
Sta. Barbara,Poblacion Sur,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,146,679,81,404,1504
Sta. Barbara,Primicias,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,221,1072,123,519,1932
Sta. Barbara,Sapang,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,417,2112,298,632,2354
Sta. Barbara,Sonquil,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,582,2952,467,913,3401
Sta. Barbara,Tebag East,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,37,149,19,95,354
Sta. Barbara,Tebag West,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,177,853,102,719,2678
Sta. Barbara,Tuliao,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,1125,5324,1035,1645,6128
Sta. Barbara,Ventinilla,"Crising, Dante, Emong ",22/07/2025 - 25/07/2025,328,1553,234,981,3656
""",
    "kristine_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Kristine ,23/10/2024,66,253,48,452,1744
Sta. Barbara,Balingueo,Kristine ,23/10/2024,135,534,88,1110,3920
Sta. Barbara,Banaoang,Kristine ,23/10/2024,198,780,143,1214,4536
Sta. Barbara,Banzal,Kristine ,23/10/2024,0,0,0,461,1712
Sta. Barbara,Botao,Kristine ,23/10/2024,43,168,26,1001,3467
Sta. Barbara,Cablong,Kristine ,23/10/2024,49,189,29,868,3093
Sta. Barbara,Carusocan,Kristine ,23/10/2024,0,0,0,504,1960
Sta. Barbara,Dalongue,Kristine ,23/10/2024,87,380,64,680,2228
Sta. Barbara,Erfe,Kristine ,23/10/2024,0,0,0,218,670
Sta. Barbara,Gueguesangen,Kristine ,23/10/2024,0,0,0,497,1864
Sta. Barbara,Leet,Kristine ,23/10/2024,109,409,77,1842,6968
Sta. Barbara,Malanay,Kristine ,23/10/2024,120,499,87,771,2884
Sta. Barbara,Maningding,Kristine ,23/10/2024,251,934,200,1419,4930
Sta. Barbara,Maronong,Kristine ,23/10/2024,0,0,0,982,3479
Sta. Barbara,Maticmatic,Kristine ,23/10/2024,199,837,135,1280,5017
Sta. Barbara,Minien East,Kristine ,23/10/2024,0,0,0,969,3350
Sta. Barbara,Minien West,Kristine ,23/10/2024,85,350,42,1634,5273
Sta. Barbara,Nilombot,Kristine ,23/10/2024,35,147,21,706,2592
Sta. Barbara,Patayac,Kristine ,23/10/2024,0,0,0,814,2843
Sta. Barbara,Payas,Kristine ,23/10/2024,48,206,28,1077,4002
Sta. Barbara,Poblacion Norte,Kristine ,23/10/2024,132,522,92,914,3872
Sta. Barbara,Poblacion Sur,Kristine ,23/10/2024,0,0,0,531,1556
Sta. Barbara,Primicias,Kristine ,23/10/2024,0,0,0,614,1909
Sta. Barbara,Sapang,Kristine ,23/10/2024,90,345,64,644,2346
Sta. Barbara,Sonquil,Kristine ,23/10/2024,120,497,96,893,3375
Sta. Barbara,Tebag East,Kristine ,23/10/2024,0,0,0,116,371
Sta. Barbara,Tebag West,Kristine ,23/10/2024,39,166,22,765,2650
Sta. Barbara,Tuliao,Kristine ,23/10/2024,297,1210,273,1715,6187
Sta. Barbara,Ventinilla,Kristine ,23/10/2024,50,186,36,972,3622
""",
    "enteng_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Enteng ,02/09/2024,148,581,108,452,1744
Sta. Barbara,Balingueo,Enteng ,02/09/2024,263,987,172,1110,3920
Sta. Barbara,Banaoang,Enteng ,02/09/2024,279,1105,202,1214,4536
Sta. Barbara,Banzal,Enteng ,02/09/2024,0,0,0,461,1712
Sta. Barbara,Botao,Enteng ,02/09/2024,0,0,0,1001,3467
Sta. Barbara,Cablong,Enteng ,02/09/2024,75,312,45,868,3093
Sta. Barbara,Carusocan,Enteng ,02/09/2024,0,0,0,504,1960
Sta. Barbara,Dalongue,Enteng ,02/09/2024,110,456,81,680,2228
Sta. Barbara,Erfe,Enteng ,02/09/2024,0,0,0,218,670
Sta. Barbara,Gueguesangen,Enteng ,02/09/2024,0,0,0,497,1864
Sta. Barbara,Leet,Enteng ,02/09/2024,142,531,100,1842,6968
Sta. Barbara,Malanay,Enteng ,02/09/2024,169,641,123,771,2884
Sta. Barbara,Maningding,Enteng ,02/09/2024,355,1543,283,1419,4930
Sta. Barbara,Maronong,Enteng ,02/09/2024,0,0,0,982,3479
Sta. Barbara,Maticmatic,Enteng ,02/09/2024,272,1074,185,1280,5017
Sta. Barbara,Minien East,Enteng ,02/09/2024,0,0,0,969,3350
Sta. Barbara,Minien West,Enteng ,02/09/2024,113,425,56,1634,5273
Sta. Barbara,Nilombot,Enteng ,02/09/2024,76,313,46,706,2592
Sta. Barbara,Patayac,Enteng ,02/09/2024,0,0,0,814,2843
Sta. Barbara,Payas,Enteng ,02/09/2024,85,330,49,1077,4002
Sta. Barbara,Poblacion Norte,Enteng ,02/09/2024,283,1171,197,914,3872
Sta. Barbara,Poblacion Sur,Enteng ,02/09/2024,0,0,0,531,1556
Sta. Barbara,Primicias,Enteng ,02/09/2024,0,0,0,614,1909
Sta. Barbara,Sapang,Enteng ,02/09/2024,125,543,89,644,2346
Sta. Barbara,Sonquil,Enteng ,02/09/2024,215,806,172,893,3375
Sta. Barbara,Tebag East,Enteng ,02/09/2024,0,0,0,116,371
Sta. Barbara,Tebag West,Enteng ,02/09/2024,66,267,38,765,2650
Sta. Barbara,Tuliao,Enteng ,02/09/2024,514,2075,473,1715,6187
Sta. Barbara,Ventinilla,Enteng ,02/09/2024,97,388,69,972,3622
""",
    "carina_2024": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Carina ,24/07/2024,35,176,21,452,1744
Sta. Barbara,Balingueo,Carina ,24/07/2024,0,0,0,1110,3920
Sta. Barbara,Banaoang,Carina ,24/07/2024,0,0,0,1214,4536
Sta. Barbara,Banzal,Carina ,24/07/2024,0,0,0,461,1712
Sta. Barbara,Botao,Carina ,24/07/2024,0,0,0,1001,3467
Sta. Barbara,Cablong,Carina ,24/07/2024,0,0,0,868,3093
Sta. Barbara,Carusocan,Carina ,24/07/2024,0,0,0,504,1960
Sta. Barbara,Dalongue,Carina ,24/07/2024,48,244,30,680,2228
Sta. Barbara,Erfe,Carina ,24/07/2024,0,0,0,218,670
Sta. Barbara,Gueguesangen,Carina ,24/07/2024,0,0,0,497,1864
Sta. Barbara,Leet,Carina ,24/07/2024,0,0,0,1842,6968
Sta. Barbara,Malanay,Carina ,24/07/2024,0,0,0,771,2884
Sta. Barbara,Maningding,Carina ,24/07/2024,0,0,0,1419,4930
Sta. Barbara,Maronong,Carina ,24/07/2024,0,0,0,982,3479
Sta. Barbara,Maticmatic,Carina ,24/07/2024,0,0,0,1280,5017
Sta. Barbara,Minien East,Carina ,24/07/2024,0,0,0,969,3350
Sta. Barbara,Minien West,Carina ,24/07/2024,0,0,0,1634,5273
Sta. Barbara,Nilombot,Carina ,24/07/2024,0,0,0,706,2592
Sta. Barbara,Patayac,Carina ,24/07/2024,0,0,0,814,2843
Sta. Barbara,Payas,Carina ,24/07/2024,0,0,0,1077,4002
Sta. Barbara,Poblacion Norte,Carina ,24/07/2024,0,0,0,914,3872
Sta. Barbara,Poblacion Sur,Carina ,24/07/2024,0,0,0,531,1556
Sta. Barbara,Primicias,Carina ,24/07/2024,0,0,0,614,1909
Sta. Barbara,Sapang,Carina ,24/07/2024,0,0,0,644,2346
Sta. Barbara,Sonquil,Carina ,24/07/2024,47,230,43,893,3375
Sta. Barbara,Tebag East,Carina ,24/07/2024,0,0,0,116,371
Sta. Barbara,Tebag West,Carina ,24/07/2024,0,0,0,765,2650
Sta. Barbara,Tuliao,Carina ,24/07/2024,0,0,0,1715,6187
Sta. Barbara,Ventinilla,Carina ,24/07/2024,0,0,0,972,3622
""",
    "egay_2023": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Egay,25/07/2023,280,1391,181,361,1564
Sta. Barbara,Balingueo,Egay,25/07/2023,757,3681,696,834,3911
Sta. Barbara,Banaoang,Egay,25/07/2023,861,4184,659,962,4477
Sta. Barbara,Banzal,Egay,25/07/2023,125,607,72,357,1571
Sta. Barbara,Botao,Egay,25/07/2023,293,1455,175,734,3401
Sta. Barbara,Cablong,Egay,25/07/2023,258,1266,153,656,3058
Sta. Barbara,Carusocan,Egay,25/07/2023,187,893,115,413,1876
Sta. Barbara,Dalongue,Egay,25/07/2023,394,2025,304,463,2030
Sta. Barbara,Erfe,Egay,25/07/2023,43,214,24,142,652
Sta. Barbara,Gueguesangen,Egay,25/07/2023,112,567,57,395,1831
Sta. Barbara,Leet,Egay,25/07/2023,737,3568,462,1499,7275
Sta. Barbara,Malanay,Egay,25/07/2023,476,2481,319,607,2764
Sta. Barbara,Maningding,Egay,25/07/2023,885,4552,669,1047,4890
Sta. Barbara,Maronong,Egay,25/07/2023,213,1027,106,731,3304
Sta. Barbara,Maticmatic,Egay,25/07/2023,896,4394,676,1073,5116
Sta. Barbara,Minien East,Egay,25/07/2023,313,1591,195,708,3260
Sta. Barbara,Minien West,Egay,25/07/2023,368,1871,210,1120,5230
Sta. Barbara,Nilombot,Egay,25/07/2023,262,1362,167,543,2434
Sta. Barbara,Patayac,Egay,25/07/2023,301,1491,190,607,2880
Sta. Barbara,Payas,Egay,25/07/2023,237,1220,132,848,3928
Sta. Barbara,Poblacion Norte,Egay,25/07/2023,644,3260,412,867,4677
Sta. Barbara,Poblacion Sur,Egay,25/07/2023,143,697,86,342,1766
Sta. Barbara,Primicias,Egay,25/07/2023,199,1004,125,401,1819
Sta. Barbara,Sapang,Egay,25/07/2023,390,2012,258,497,2315
Sta. Barbara,Sonquil,Egay,25/07/2023,543,2789,359,713,3272
Sta. Barbara,Tebag East,Egay,25/07/2023,32,157,18,83,439
Sta. Barbara,Tebag West,Egay,25/07/2023,159,802,86,558,2538
Sta. Barbara,Tuliao,Egay,25/07/2023,1092,5207,722,1329,6424
Sta. Barbara,Ventinilla,Egay,25/07/2023,300,1462,175,763,3485
""",
    "paeng_2022": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Paeng,29/10/2022,0,0,0,177,1564
Sta. Barbara,Balingueo,Paeng,29/10/2022,0,0,0,420,3911
Sta. Barbara,Banaoang,Paeng,29/10/2022,0,0,0,485,4477
Sta. Barbara,Banzal,Paeng,29/10/2022,0,0,0,177,1571
Sta. Barbara,Botao,Paeng,29/10/2022,0,0,0,369,3401
Sta. Barbara,Cablong,Paeng,29/10/2022,0,0,0,331,3058
Sta. Barbara,Carusocan,Paeng,29/10/2022,0,0,0,206,1876
Sta. Barbara,Dalongue,Paeng,29/10/2022,0,0,0,228,2030
Sta. Barbara,Erfe,Paeng,29/10/2022,0,0,0,71,652
Sta. Barbara,Gueguesangen,Paeng,29/10/2022,0,0,0,199,1831
Sta. Barbara,Leet,Paeng,29/10/2022,0,0,0,765,7275
Sta. Barbara,Malanay,Paeng,29/10/2022,0,0,0,303,2764
Sta. Barbara,Maningding,Paeng,29/10/2022,0,0,0,527,4890
Sta. Barbara,Maronong,Paeng,29/10/2022,0,0,0,365,3304
Sta. Barbara,Maticmatic,Paeng,29/10/2022,0,0,0,544,5116
Sta. Barbara,Minien East,Paeng,29/10/2022,0,0,0,355,3260
Sta. Barbara,Minien West,Paeng,29/10/2022,0,0,0,564,5230
Sta. Barbara,Nilombot,Paeng,29/10/2022,0,0,0,270,2434
Sta. Barbara,Patayac,Paeng,29/10/2022,0,0,0,307,2880
Sta. Barbara,Payas,Paeng,29/10/2022,0,0,0,426,3928
Sta. Barbara,Poblacion Norte,Paeng,29/10/2022,0,0,0,459,4677
Sta. Barbara,Poblacion Sur,Paeng,29/10/2022,0,0,0,178,1766
Sta. Barbara,Primicias,Paeng,29/10/2022,0,0,0,200,1819
Sta. Barbara,Sapang,Paeng,29/10/2022,0,0,0,251,2315
Sta. Barbara,Sonquil,Paeng,29/10/2022,10,50,8,357,3272
Sta. Barbara,Tebag East,Paeng,29/10/2022,0,0,0,43,439
Sta. Barbara,Tebag West,Paeng,29/10/2022,0,0,0,279,2538
Sta. Barbara,Tuliao,Paeng,29/10/2022,0,0,0,678,6424
Sta. Barbara,Ventinilla,Paeng,29/10/2022,0,0,0,382,3485
""",
    "maring_2021": """Municipality,Barangay,Name of Typhoon,Date ng Typhoon,Affected Families,Affected Individuals,Food Packs Given,Total Number of Families,Total Number of Individuals
Sta. Barbara,Alibago,Maring,28/10/2021,130,1250,83,172,1564
Sta. Barbara,Balingueo,Maring,28/10/2021,341,3134,225,420,3911
Sta. Barbara,Banaoang,Maring,28/10/2021,414,3954,310,483,4477
Sta. Barbara,Banzal,Maring,28/10/2021,18,165,10,173,1571
Sta. Barbara,Botao,Maring,28/10/2021,66,604,41,367,3401
Sta. Barbara,Cablong,Maring,28/10/2021,43,377,25,330,3058
Sta. Barbara,Carusocan,Maring,28/10/2021,21,194,12,204,1876
Sta. Barbara,Dalongue,Maring,28/10/2021,194,1719,125,223,2030
Sta. Barbara,Erfe,Maring,28/10/2021,7,68,4,71,652
Sta. Barbara,Gueguesangen,Maring,28/10/2021,32,286,18,198,1831
Sta. Barbara,Leet,Maring,28/10/2021,100,974,64,773,7275
Sta. Barbara,Malanay,Maring,28/10/2021,269,2608,177,300,2764
Sta. Barbara,Maningding,Maring,28/10/2021,453,4292,344,526,4890
Sta. Barbara,Maronong,Maring,28/10/2021,62,584,38,360,3304
Sta. Barbara,Maticmatic,Maring,28/10/2021,524,4772,402,547,5116
Sta. Barbara,Minien East,Maring,28/10/2021,61,548,37,353,3260
Sta. Barbara,Minien West,Maring,28/10/2021,85,786,54,563,5230
Sta. Barbara,Nilombot,Maring,28/10/2021,27,256,15,266,2434
Sta. Barbara,Patayac,Maring,28/10/2021,52,478,31,308,2880
Sta. Barbara,Payas,Maring,28/10/2021,76,661,47,424,3928
Sta. Barbara,Poblacion Norte,Maring,28/10/2021,393,3454,294,481,4677
Sta. Barbara,Poblacion Sur,Maring,28/10/2021,27,235,15,184,1766
Sta. Barbara,Primicias,Maring,28/10/2021,34,314,20,198,1819
Sta. Barbara,Sapang,Maring,28/10/2021,198,1821,129,250,2315
Sta. Barbara,Sonquil,Maring,28/10/2021,322,2982,212,354,3272
Sta. Barbara,Tebag East,Maring,28/10/2021,6,52,3,45,439
Sta. Barbara,Tebag West,Maring,28/10/2021,39,347,23,276,2538
Sta. Barbara,Tuliao,Maring,28/10/2021,684,5992,629,684,6424
Sta. Barbara,Ventinilla,Maring,28/10/2021,66,641,41,378,3485
""",
}

# typhoon_key(s) matching scripts/typhoon_calendar_2021_2026.py
_TYPHOON_KEYS = {
    "crising_dante_emong_2025": ["crising_2025", "dante_2025", "emong_2025"],
    "kristine_2024": ["kristine_2024"],
    "enteng_2024": ["enteng_2024"],
    "carina_2024": ["carina_2024"],
    "egay_2023": ["egay_2023"],
    "paeng_2022": ["paeng_2022"],
    "maring_2021": ["maring_2021"],
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
        "date": _iso_date(r["Date ng Typhoon"]),
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
        affected = sum(1 for r in rows if r["food_packs_given"] > 0)
        good = len(rows) == 29 and len({normalize(r["barangay"]) for r in rows}) == 29
        ok &= good
        print(f"{rep['key']:<26} {rows[0]['date']} 29 brgy={good!s:<6} served={affected:>2}/29 "
              f"families={fam:>6,} packs={packs:>6,}  {'OK' if good else 'MISMATCH'}")
    print(f"\nAll {len(REPORTS)} Sta. Barbara reports structurally OK." if ok
          else "\nMISMATCH - recheck transcription.")
