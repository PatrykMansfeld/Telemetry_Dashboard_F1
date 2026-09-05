"""
Zakładka „Podsumowanie” — tabela wyników i strata do lidera.

Czasy okrążeń są już w listwie kierowców nad zakładkami, więc tutaj pokazujemy
to, czego tam nie widać: rozbicie na sektory, który sektor kto wygrał
i skąd bierze się strata.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from f1tele.pipeline import AnalysisResult

from ..components import caption, chart, subheader, table

MEDALS = ["🥇", "🥈", "🥉"]
SECTORS = ("sector1", "sector2", "sector3")


def render(result: AnalysisResult) -> None:
    drivers = result.sorted_drivers
    if not drivers:
        st.info("Brak danych kierowców.")
        return

    subheader("Okrążenia i sektory")
    table(_lap_table(drivers), download="okrazenia_sektory")
    caption("★ oznacza najlepszy czas w danym sektorze. "
            "Delta liczona do najszybszego okrążenia w zestawieniu.")

    subheader("Gdzie tracisz czas")
    table(_sector_gap_table(drivers), download="strata_sektorowa")
    caption("Strata do najlepszego czasu w każdym sektorze — pokazuje, "
            "który fragment toru kosztuje kierowcę najwięcej.")

    if "weather" in result.figures:
        subheader("Warunki")
        chart(result.figures["weather"])


def _best_sectors(drivers) -> dict[str, float]:
    """Najlepszy czas w każdym sektorze (0 pomijamy — brak pomiaru)."""
    best = {}
    for name in SECTORS:
        times = [getattr(d, name) for d in drivers if getattr(d, name) > 0]
        best[name] = min(times) if times else 0.0
    return best


def _lap_table(drivers) -> pd.DataFrame:
    reference = drivers[0].lap_time
    best = _best_sectors(drivers)

    rows = []
    for i, d in enumerate(drivers):
        delta = d.lap_time - reference
        row = {
            "#":        MEDALS[i] if i < len(MEDALS) else str(i + 1),
            "Kierowca": d.driver,
            "Czas":     d.lap_time_str,
            "Delta":    "—" if delta == 0 else f"+{delta:.3f}",
        }
        for number, name in enumerate(SECTORS, start=1):
            value = getattr(d, name)
            is_best = value > 0 and abs(value - best[name]) < 1e-6
            row[f"S{number}"] = f"{'★ ' if is_best else ''}{value:.3f}" if value else "—"
        row["Okrążenie"] = d.lap_number
        row["Opona"] = d.compound.title()
        row["Zespół"] = d.team
        rows.append(row)
    return pd.DataFrame(rows)


def _sector_gap_table(drivers) -> pd.DataFrame:
    """Strata w każdym sektorze plus suma — czyli teoretyczny zysk do odzyskania."""
    best = _best_sectors(drivers)
    rows = []
    for d in drivers:
        gaps = {}
        total = 0.0
        for number, name in enumerate(SECTORS, start=1):
            value = getattr(d, name)
            gap = value - best[name] if value > 0 and best[name] > 0 else 0.0
            total += gap
            gaps[f"S{number} [s]"] = f"+{gap:.3f}" if gap > 0.0005 else "—"
        rows.append({"Kierowca": d.driver, **gaps, "Razem [s]": f"+{total:.3f}"})
    return pd.DataFrame(rows)
