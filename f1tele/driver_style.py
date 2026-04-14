"""
Odcisk palca stylu jazdy kierowcy (Driver Style Fingerprint).
Oblicza wielowymiarowe metryki charakteryzujące styl jazdy:
  - agresywność hamowania
  - wcześniejszość gazu
  - płynność kierownicy (z danych toru)
  - zużycie mocy silnika
  - efektywność zakrętów
  - stała gazu (% okrążenia z >90% throttle)
  - stała hamowania (% okrążenia z >5% brake)
  - maksymalna prędkość
  - czas biegu neutralnego

Wyświetla wykres radarowy oraz tabelę metryk.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

from .data_loader import DriverLapData, SessionData
from .corner_analysis import CornerAnalysis

console = Console()
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "plots"

PLOT_STYLE = {
    "figure.facecolor": "#0F0F0F",
    "axes.facecolor": "#1A1A1A",
    "text.color": "#CCCCCC",
    "font.family": "monospace",
}


@dataclass
class StyleFingerprint:
    """Metryki stylu jazdy jednego kierowcy (0–100, wyżej = lepiej/więcej)."""
    driver: str
    color: str

    # Metryki obliczone z telemetrii
    full_throttle_pct: float          # % okrążenia z pełnym gazem
    heavy_braking_pct: float          # % okrążenia z intensywnym hamowaniem
    coasting_pct: float               # % okrążenia bez gazu i bez hamulca (coast)
    avg_apex_speed_norm: float        # Znormalizowana śr. prędkość w apeksach
    braking_aggressiveness: float     # Śr. maks. siła hamowania (0–100)
    throttle_smoothness: float        # Płynność gazu (1 - std/mean)
    high_rpm_pct: float               # % czasu z RPM > 90% max
    avg_speed_norm: float             # Znormalizowana śr. prędkość
    gear_change_freq: float           # Częstotliwość zmian biegów (norm.)
    braking_consistency: float        # Spójność punktów hamowania

    raw_metrics: dict = field(default_factory=dict)


METRIC_LABELS = [
    "Pełny gaz",
    "Intensywne\nhamowanie",
    "Wybieg\n(coasting)",
    "Prędkość\nw zakrętach",
    "Agresywność\nhamowania",
    "Płynność\ngazu",
    "Wysokie RPM",
    "Śr. prędkość",
    "Zmiany\nbiegów",
    "Spójność\nhamowania",
]

METRIC_FIELDS = [
    "full_throttle_pct",
    "heavy_braking_pct",
    "coasting_pct",
    "avg_apex_speed_norm",
    "braking_aggressiveness",
    "throttle_smoothness",
    "high_rpm_pct",
    "avg_speed_norm",
    "gear_change_freq",
    "braking_consistency",
]


def _safe_norm(value: float, lo: float, hi: float) -> float:
    """Normalizuje wartość do przedziału 0–100."""
    if hi <= lo:
        return 50.0
    return float(np.clip((value - lo) / (hi - lo) * 100, 0, 100))


def compute_style_fingerprint(
    data: DriverLapData,
    corner_analysis: Optional[CornerAnalysis] = None,
    fleet_stats: Optional[dict] = None,
) -> StyleFingerprint:
    """
    Oblicza metryki stylu jazdy dla jednego kierowcy.

    Args:
        data: Dane okrążenia kierowcy
        corner_analysis: Wyniki analizy zakrętów (opcjonalne)
        fleet_stats: Statystyki floty do normalizacji (min/max per metryka)

    Returns:
        Obiekt StyleFingerprint
    """
    telem = data.telemetry
    n = len(telem)
    if n == 0:
        return StyleFingerprint(
            driver=data.driver, color=data.color,
            **{f: 0.0 for f in METRIC_FIELDS},
        )

    speed = telem["Speed"].values
    throttle = telem["Throttle"].values if "Throttle" in telem.columns else np.zeros(n)
    brake = telem["Brake"].values if "Brake" in telem.columns else np.zeros(n)
    rpm = telem["RPM"].values if "RPM" in telem.columns else np.zeros(n)
    gear = telem["nGear"].values if "nGear" in telem.columns else np.ones(n)

    # Normalizacja hamulca
    if brake.max() <= 1.0:
        brake = brake * 100.0

    # Pełny gaz % (throttle > 90%)
    full_throttle_pct = float((throttle > 90).sum() / n * 100)

    # Intensywne hamowanie (brake > 20%)
    heavy_braking_pct = float((brake > 20).sum() / n * 100)

    # Coasting: throttle < 10% AND brake < 5%
    coasting_pct = float(((throttle < 10) & (brake < 5)).sum() / n * 100)

    # Prędkość w zakrętach (z analizy zakrętów)
    avg_apex_speed_norm = 0.0
    braking_aggressiveness = 0.0
    braking_consistency = 0.0

    if corner_analysis and data.driver in corner_analysis.driver_corners:
        events = corner_analysis.driver_corners[data.driver]
        if events:
            apex_speeds = [e.apex_speed for e in events]
            avg_apex_speed_norm = float(np.mean(apex_speeds))
            braking_aggressiveness = float(np.mean([e.max_brake_pressure for e in events]))
            brake_dists = [e.braking_distance for e in events]
            if len(brake_dists) > 1:
                braking_consistency = float(
                    max(0, 100 - np.std(brake_dists) / (np.mean(brake_dists) + 1) * 100)
                )
            else:
                braking_consistency = 50.0

    # Płynność gazu (1 - zmienność)
    throt_valid = throttle[throttle > 5]
    if len(throt_valid) > 1:
        throttle_smoothness = float(
            max(0, 100 - (np.std(throt_valid) / (np.mean(throt_valid) + 1e-6)) * 100)
        )
    else:
        throttle_smoothness = 50.0

    # Wysokie RPM (>90% max)
    max_rpm = rpm.max()
    if max_rpm > 0:
        high_rpm_pct = float((rpm > 0.9 * max_rpm).sum() / n * 100)
    else:
        high_rpm_pct = 0.0

    # Średnia prędkość
    avg_speed_norm = float(np.mean(speed))

    # Częstotliwość zmian biegów
    gear_changes = np.sum(np.diff(gear.astype(int)) != 0)
    gear_change_freq = float(gear_changes / n * 1000)  # per 1000 próbek

    raw = {
        "full_throttle_pct": full_throttle_pct,
        "heavy_braking_pct": heavy_braking_pct,
        "coasting_pct": coasting_pct,
        "avg_apex_speed_raw": avg_apex_speed_norm,
        "braking_aggressiveness": braking_aggressiveness,
        "throttle_smoothness": throttle_smoothness,
        "high_rpm_pct": high_rpm_pct,
        "avg_speed_raw": avg_speed_norm,
        "gear_change_freq": gear_change_freq,
        "braking_consistency": braking_consistency,
    }

    return StyleFingerprint(
        driver=data.driver,
        color=data.color,
        full_throttle_pct=full_throttle_pct,
        heavy_braking_pct=heavy_braking_pct,
        coasting_pct=coasting_pct,
        avg_apex_speed_norm=avg_apex_speed_norm,
        braking_aggressiveness=braking_aggressiveness,
        throttle_smoothness=throttle_smoothness,
        high_rpm_pct=high_rpm_pct,
        avg_speed_norm=avg_speed_norm,
        gear_change_freq=gear_change_freq,
        braking_consistency=braking_consistency,
        raw_metrics=raw,
    )


def normalize_fingerprints(
    fingerprints: list[StyleFingerprint],
) -> list[StyleFingerprint]:
    """
    Normalizuje metryki radarowe do skali 0–100 względem floty kierowców.
    """
    if len(fingerprints) < 2:
        return fingerprints

    for field_name in METRIC_FIELDS:
        vals = [getattr(fp, field_name) for fp in fingerprints]
        lo, hi = min(vals), max(vals)
        for fp in fingerprints:
            raw_val = getattr(fp, field_name)
            norm_val = _safe_norm(raw_val, lo, hi)
            object.__setattr__(fp, field_name, norm_val)

    return fingerprints


def plot_radar_chart(
    fingerprints: list[StyleFingerprint],
    session_data: SessionData,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Wykres radarowy porównujący style jazdy kierowców.
    """
    plt.rcParams.update(PLOT_STYLE)

    n_metrics = len(METRIC_LABELS)
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # zamknij wielokąt

    fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw={"polar": True})
    fig.patch.set_facecolor("#0F0F0F")
    ax.set_facecolor("#111111")

    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Style jazdy kierowców",
        fontsize=13, fontweight="bold", color="#FFFFFF", y=0.97,
    )

    # Siatka
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(METRIC_LABELS, fontsize=8.5, color="#BBBBBB")
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color="#666666")
    ax.set_ylim(0, 100)
    ax.grid(color="#333333", linewidth=0.7, alpha=0.6)
    ax.spines["polar"].set_color("#444444")
    ax.tick_params(colors="#888888")

    for fp in fingerprints:
        values = [getattr(fp, f) for f in METRIC_FIELDS]
        values += values[:1]

        ax.plot(angles, values, color=fp.color, linewidth=2.0,
                linestyle="-", alpha=0.9, label=fp.driver)
        ax.fill(angles, values, color=fp.color, alpha=0.12)

        # Punkty na narożnikach
        ax.scatter(angles[:-1], values[:-1], color=fp.color,
                   s=40, zorder=5, alpha=0.9)

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.35, 1.12),
        fontsize=11,
        framealpha=0.7,
        facecolor="#222222",
        edgecolor="#444444",
        labelcolor="#CCCCCC",
    )

    if save:
        drivers_str = "_".join(sorted(fp.driver for fp in fingerprints))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_radar.png"
        )
        out_path = OUTPUT_DIR / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        console.print(f"[bold green]✓ Zapisano:[/bold green] {out_path}")
        if not show:
            plt.close(fig)
        return out_path

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    if show:
        plt.show()
    plt.close(fig)
    return buf


def plot_style_bar_comparison(
    fingerprints: list[StyleFingerprint],
    session_data: SessionData,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Poziomy wykres słupkowy porównujący metryki stylu jazdy.
    Każda metryka to jedna "runda" słupków.
    """
    plt.rcParams.update(PLOT_STYLE)

    n_metrics = len(METRIC_LABELS)
    n_drivers = len(fingerprints)
    if n_drivers == 0:
        return None

    fig, ax = plt.subplots(figsize=(14, max(6, n_metrics * 1.2)))
    fig.patch.set_facecolor("#0F0F0F")
    ax.set_facecolor("#1A1A1A")
    ax.tick_params(colors="#888888", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Metryki stylu jazdy",
        fontsize=12, fontweight="bold", color="#FFFFFF",
    )

    y = np.arange(n_metrics)
    bar_h = 0.7 / n_drivers

    for i, fp in enumerate(fingerprints):
        vals = [getattr(fp, f) for f in METRIC_FIELDS]
        bars = ax.barh(
            y + i * bar_h - (n_drivers - 1) * bar_h / 2,
            vals, bar_h * 0.9,
            color=fp.color, alpha=0.85, label=fp.driver,
        )
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(
                    val + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}",
                    va="center", ha="left", fontsize=7, color=fp.color,
                )

    ax.set_yticks(y)
    ax.set_yticklabels(METRIC_LABELS, fontsize=9, color="#CCCCCC")
    ax.set_xlabel("Wartość metryki (0–100)", fontsize=9, color="#CCCCCC")
    ax.set_xlim(0, 115)
    ax.axvline(50, color="#444444", linewidth=0.8, linestyle="--")
    ax.legend(fontsize=10, framealpha=0.7, facecolor="#222222",
              edgecolor="#444444", labelcolor="#CCCCCC")
    ax.grid(True, alpha=0.2, axis="x", linewidth=0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if save:
        drivers_str = "_".join(sorted(fp.driver for fp in fingerprints))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_style_bars.png"
        )
        out_path = OUTPUT_DIR / filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        console.print(f"[bold green]✓ Zapisano:[/bold green] {out_path}")
        if not show:
            plt.close(fig)
        return out_path

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    if show:
        plt.show()
    plt.close(fig)
    return buf


def print_style_table(fingerprints: list[StyleFingerprint]) -> None:
    """Wyświetla tabelę metryk stylu jazdy."""
    table = Table(
        title="[bold]Metryki stylu jazdy kierowców[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metryka", width=22)
    for fp in fingerprints:
        table.add_column(fp.driver, justify="right", width=10)

    metric_display = [
        ("Pełny gaz [%]", "full_throttle_pct"),
        ("Intensywne hamowanie [%]", "heavy_braking_pct"),
        ("Wybieg (coasting) [%]", "coasting_pct"),
        ("Prędkość w apeksach", "avg_apex_speed_norm"),
        ("Agresywność hamowania", "braking_aggressiveness"),
        ("Płynność gazu", "throttle_smoothness"),
        ("Wysokie RPM [%]", "high_rpm_pct"),
        ("Średnia prędkość", "avg_speed_norm"),
        ("Częstość zmian biegów", "gear_change_freq"),
        ("Spójność hamowania", "braking_consistency"),
    ]

    for label, field_name in metric_display:
        vals = [getattr(fp, field_name) for fp in fingerprints]
        best_idx = int(np.argmax(vals))
        row = [label]
        for i, (fp, val) in enumerate(zip(fingerprints, vals)):
            color_tag = "green" if i == best_idx else "white"
            row.append(f"[{color_tag}]{val:.1f}[/{color_tag}]")
        table.add_row(*row)

    console.print(table)
