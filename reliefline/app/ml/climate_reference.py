"""
Real-world climate reference data still used by the two-stage forecaster's
seasonal display flags (app.ml.predict.forecast_lgu's is_wet_season /
is_peak_season). Trimmed down from the larger module that used to anchor the
SARIMAX forecaster's synthetic history generator (scripts/seed_monthly_history.py,
now deleted) - EVENTS, ONI, oni_for, severity_for, TC_CLIMO and the baseline-
incident constants were only ever consumed by that generator or the SARIMAX
exogenous features and are gone with it. The typhoon calendar those events
were transcribed from is now scripts/typhoon_calendar_2021_2026.py (36
source-verified events, loaded into the `typhoon_calendar` table), which is
the authoritative source for Stage 2's climatology and P(relief) - see
app.ml.train module doc.

VERIFIED (looked up, source noted):
  * RAINFALL_NORMAL_MM / RAINY_DAYS - PAGASA Dagupan station, 1991-2020
    normals (Wikipedia "Dagupan" climate table, transcribed from PAGASA).
  * Climate type / seasons - Dagupan is Type I: dry Nov-May, wet Jun-Oct,
    heaviest rain Jul-Aug (City Government of Dagupan, "Climate").
"""

# PAGASA Dagupan normals 1991-2020, mm per month (Jan..Dec). Annual 2,516.7.
RAINFALL_NORMAL_MM = [5.7, 9.5, 23.0, 69.5, 218.2, 335.5, 532.7, 619.5, 401.6, 226.6, 54.9, 20.0]
RAINY_DAYS = [2, 2, 3, 4, 11, 16, 20, 21, 19, 9, 5, 3]

# Type I climate (Dagupan / Pangasinan): dry Nov-May, wet Jun-Oct.
WET_SEASON_MONTHS = {6, 7, 8, 9, 10}
# Peak typhoon / habagat months (PAGASA: ~70% of TCs Jul-Oct). Drives the
# "more weight on the rainy season" display flag on the forecast.
PEAK_MONTHS = {7, 8, 9, 10}
