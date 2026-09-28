"""
Shared accent/punctuation-stripping core for matching a real-report barangay
name (PSA/DSWD/LGU sheet spelling) against the barangays table's plain-ASCII
convention (no diacritics, "Santa" spelled out, never "Sta."). Each real-data
module keeps its own small alias dict on top of this for the spelling
differences that are specific to its source (e.g. "Tiposu"->"tipuso",
"Carusucan"->"carusocan") - this only factors out the NFKD-strip boilerplate
that used to be duplicated in real_urdaneta_reports_2025.py and
sample_sta_barbara_aug2026.py.
"""
import unicodedata


def strip_accents_and_punct(name):
    """'Población Norte' -> 'poblacion norte', 'Sta. Lucia' -> 'sta lucia'
    (callers alias the remaining 'sta'/short forms themselves)."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    for ch in ".,'-":
        s = s.replace(ch, " ")
    return " ".join(s.split())
