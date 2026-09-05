"""Zakładka „Sektory” — mini-sektory, mapa ciepła i statystyki S1/S2/S3."""

from __future__ import annotations

import pandas as pd

from f1tele.pipeline import AnalysisResult

from ..components import caption, chart, empty_module, subheader, table

STAT_COLUMNS = {
    "Driver":           "Kierowca",
    "Sector":           "Sektor",
    "Official_s":       "Oficjalny [s]",
    "Time_s":           "Z telemetrii [s]",
    "Diff_s":           "Różnica [s]",
    "MaxSpeed":         "Max V [km/h]",
    "AvgSpeed":         "Śr. V [km/h]",
    "FullThrottle_pct": "Pełny gaz %",
    "Braking_pct":      "Hamowanie %",
}


def render(result: AnalysisResult) -> None:
    drawn = chart(result.figures.get("mini_sectors"))
    drawn = chart(result.figures.get("sector_heatmap")) or drawn

    if "sector_colors" in result.figures:
        subheader("🟣 Purple / 🟢 Green / 🟡 Yellow")
        drawn = chart(result.figures["sector_colors"]) or drawn

    stats = result.sector_stats
    if stats is not None and not stats.empty:
        subheader("Statystyki sektorowe")
        table(_stats_table(stats), max_height=420, download="statystyki_sektorowe")
        caption(_accuracy_note(stats))
        drawn = True

    if not drawn:
        empty_module("Sektory")


def _stats_table(stats: pd.DataFrame) -> pd.DataFrame:
    """Sektory posortowane S1→S3, w każdym od najszybszego kierowcy."""
    columns = [c for c in STAT_COLUMNS if c in stats.columns]
    return (stats[columns]
            .rename(columns=STAT_COLUMNS)
            .sort_values(["Sektor", "Oficjalny [s]"])
            .reset_index(drop=True))


def _accuracy_note(stats: pd.DataFrame) -> str:
    """
    Wyjaśnia różnicę między czasem oficjalnym a policzonym z telemetrii.

    „Oficjalny” to pomiar z pętli indukcyjnych toru, „z telemetrii” — całka
    z prędkości po dystansie. Rozjazd pokazuje, ile wynosi błąd tej metody.
    """
    official = bool(stats["Official"].all()) if "Official" in stats.columns else False
    if not official:
        return ("Granice sektorów są przybliżone (równy podział dystansu) — sesja "
                "nie udostępniła czasów sektorowych dla wszystkich okrążeń.")

    diff = stats["Diff_s"].abs()
    return (f"Granice sektorów wyznaczone z oficjalnych czasów. Kolumna „różnica” "
            f"to rozjazd między pomiarem toru a całką z telemetrii — tutaj średnio "
            f"{diff.mean():.3f} s, maksymalnie {diff.max():.3f} s.")
