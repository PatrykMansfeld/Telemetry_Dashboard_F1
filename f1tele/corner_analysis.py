"""
Analiza zakrętów (corner-by-corner).
Wyznacza punkty hamowania, apeksy i wyjścia z zakrętów dla każdego kierowcy.
Porównuje styl jazdy: agresywność hamowania, wcześniejszość gazu i prędkość szczytową.
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
from scipy.signal import find_peaks, savgol_filter
from rich.console import Console
from rich.table import Table
from rich import box

from .data_loader import DriverLapData, SessionData

console = Console()
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "plots"

PLOT_STYLE = {
    "figure.facecolor": "#0F0F0F",
    "axes.facecolor": "#1A1A1A",
    "axes.edgecolor": "#444444",
    "axes.labelcolor": "#CCCCCC",
    "axes.titlecolor": "#FFFFFF",
    "xtick.color": "#888888",
    "ytick.color": "#888888",
    "grid.color": "#2A2A2A",
    "grid.linewidth": 0.6,
    "text.color": "#CCCCCC",
    "font.family": "monospace",
}


@dataclass
class CornerEvent:
    """Dane jednego zakrętu dla jednego kierowcy."""
    corner_id: int
    driver: str
    braking_point: float           # dystans [m] rozpoczęcia hamowania
    apex_speed: float              # prędkość w apeksie [km/h]
    apex_distance: float           # dystans apeksu [m]
    exit_throttle_point: float     # dystans [m] pełnego gazu po wyjściu
    min_speed: float               # minimalna prędkość w zakręcie [km/h]
    max_brake_pressure: float      # maks. siła hamowania [0-100]
    braking_distance: float        # dystans hamowania [m]
    corner_time: float             # czas przejazdu zakrętu [s]


@dataclass
class CornerAnalysis:
    """Pełna analiza zakrętów dla sesji."""
    corners: list[dict]            # lokalizacja zakrętów {id, distance, name}
    driver_corners: dict[str, list[CornerEvent]] = field(default_factory=dict)


def _smooth_speed(speed: np.ndarray, window: int = 21) -> np.ndarray:
    """Wygładza profil prędkości filtrem Savitzky-Golay."""
    if len(speed) < window:
        return speed
    return savgol_filter(speed, min(window, len(speed) - (1 if len(speed) % 2 == 0 else 0)), 3)


def detect_corners(
    telemetry: pd.DataFrame,
    min_speed_drop: float = 30.0,
    min_distance_between: float = 200.0,
) -> list[dict]:
    """
    Wykrywa zakręty na podstawie lokalnych minimów prędkości.

    Args:
        telemetry: DataFrame z kolumnami Distance i Speed
        min_speed_drop: Minimalny spadek prędkości [km/h] przed minimum
        min_distance_between: Minimalna odległość między zakrętami [m]

    Returns:
        Lista słowników opisujących zakręty
    """
    dist = telemetry["Distance"].values
    speed = telemetry["Speed"].values
    smooth = _smooth_speed(speed)

    min_dist_samples = max(1, int(min_distance_between / (dist[-1] / len(dist))))

    valleys, props = find_peaks(-smooth, distance=min_dist_samples, prominence=min_speed_drop)

    corners = []
    for cid, idx in enumerate(valleys, start=1):
        corners.append({
            "id": cid,
            "distance": float(dist[idx]),
            "min_speed": float(speed[idx]),
            "name": f"T{cid}",
        })

    return corners


def analyze_corner_events(
    driver: str,
    telemetry: pd.DataFrame,
    corners: list[dict],
    window_before: float = 300.0,
    window_after: float = 200.0,
) -> list[CornerEvent]:
    """
    Dla każdego zakrętu oblicza punkt hamowania, apeks i wyjście.

    Args:
        driver: Kod kierowcy
        telemetry: DataFrame z pełną telemetrią
        corners: Lista zakrętów z detect_corners()
        window_before: Okno przed apeksem [m]
        window_after: Okno po apeksie [m]

    Returns:
        Lista obiektów CornerEvent
    """
    dist = telemetry["Distance"].values
    speed = telemetry["Speed"].values
    throttle = telemetry["Throttle"].values if "Throttle" in telemetry.columns else np.zeros_like(speed)
    brake = telemetry["Brake"].values if "Brake" in telemetry.columns else np.zeros_like(speed)

    if brake.max() <= 1.0:
        brake = brake * 100.0

    events: list[CornerEvent] = []

    for corner in corners:
        apex_d = corner["distance"]

        mask = (dist >= apex_d - window_before) & (dist <= apex_d + window_after)
        if mask.sum() < 5:
            continue

        seg_dist  = dist[mask]
        seg_speed = speed[mask]
        seg_throt = throttle[mask]
        seg_brake = brake[mask]

        # Apeks = minimum prędkości w oknie
        apex_local_idx = np.argmin(seg_speed)
        apex_d_actual  = float(seg_dist[apex_local_idx])
        apex_speed     = float(seg_speed[apex_local_idx])

        # Punkt hamowania: ostatnie miejsce gdzie hamulec > 5% przed apeksem
        before_apex = seg_dist <= apex_d_actual
        brake_before = seg_brake[before_apex]
        dist_before  = seg_dist[before_apex]

        braking_indices = np.where(brake_before > 5.0)[0]
        if len(braking_indices) > 0:
            brake_start_idx = braking_indices[0]
            braking_point   = float(dist_before[brake_start_idx])
        else:
            braking_point = apex_d_actual - 50.0

        # Punkt pełnego gazu: miejsce gdzie throttle > 80% po apeksie
        after_apex   = seg_dist >= apex_d_actual
        throt_after  = seg_throt[after_apex]
        dist_after   = seg_dist[after_apex]

        throttle_idx = np.where(throt_after > 80.0)[0]
        exit_throttle_point = (
            float(dist_after[throttle_idx[0]])
            if len(throttle_idx) > 0
            else apex_d_actual + 100.0
        )

        braking_distance = apex_d_actual - braking_point
        max_brake        = float(seg_brake.max())

        # Czas przejazdu zakrętu (przybliżony z odcinka)
        dt = np.where(seg_speed > 1, np.diff(seg_dist, prepend=seg_dist[0]) / (seg_speed / 3.6), 0)
        corner_time = float(dt.sum())

        events.append(CornerEvent(
            corner_id=corner["id"],
            driver=driver,
            braking_point=braking_point,
            apex_speed=apex_speed,
            apex_distance=apex_d_actual,
            exit_throttle_point=exit_throttle_point,
            min_speed=apex_speed,
            max_brake_pressure=max_brake,
            braking_distance=max(0.0, braking_distance),
            corner_time=corner_time,
        ))

    return events


def run_corner_analysis(
    drivers_data: dict[str, DriverLapData],
) -> CornerAnalysis:
    """
    Przeprowadza pełną analizę zakrętów dla wszystkich kierowców.
    Zakręty wykrywane są z telemetrii lidera (najszybszego kierowcy).
    """
    if not drivers_data:
        return CornerAnalysis(corners=[])

    # Wykryj zakręty z danych lidera
    leader = min(drivers_data.values(), key=lambda d: d.lap_time)
    corners = detect_corners(leader.telemetry)
    console.print(f"[cyan]Wykryto {len(corners)} zakrętów[/cyan]")

    analysis = CornerAnalysis(corners=corners)

    for drv, data in drivers_data.items():
        events = analyze_corner_events(drv, data.telemetry, corners)
        analysis.driver_corners[drv] = events

    return analysis


def print_corner_comparison_table(analysis: CornerAnalysis) -> None:
    """Wyświetla tabelę porównania kierowców w każdym zakręcie."""
    drivers = list(analysis.driver_corners.keys())
    if not drivers or not analysis.corners:
        return

    table = Table(
        title="[bold]Analiza zakrętów — porównanie kierowców[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Zakręt", style="bold", width=8)
    table.add_column("Dystans [m]", justify="right", width=12)
    for drv in drivers:
        table.add_column(f"{drv}\nApeks km/h", justify="right", width=12)
        table.add_column(f"{drv}\nHam. [m]", justify="right", width=10)

    for corner in analysis.corners:
        cid = corner["id"]
        row = [f"T{cid}", f"{corner['distance']:.0f}"]

        for drv in drivers:
            events = {e.corner_id: e for e in analysis.driver_corners.get(drv, [])}
            ev = events.get(cid)
            if ev:
                row.append(f"{ev.apex_speed:.1f}")
                row.append(f"{ev.braking_distance:.1f}")
            else:
                row.extend(["—", "—"])

        table.add_row(*row)

    console.print(table)


def plot_corner_comparison(
    drivers_data: dict[str, DriverLapData],
    analysis: CornerAnalysis,
    session_data: SessionData,
    max_corners: int = 12,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Wykres słupkowy porównujący prędkość w apeksach i dystans hamowania dla każdego zakrętu.
    """
    plt.rcParams.update(PLOT_STYLE)

    corners_to_show = analysis.corners[:max_corners]
    n = len(corners_to_show)
    if n == 0:
        return None

    drivers = list(drivers_data.keys())
    n_drivers = len(drivers)
    colors   = [drivers_data[d].color for d in drivers]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 11))
    fig.patch.set_facecolor("#0F0F0F")
    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Analiza zakrętów zakręt po zakręcie",
        fontsize=13, fontweight="bold", color="#FFFFFF", y=0.98,
    )

    x = np.arange(n)
    bar_w = 0.8 / n_drivers

    for ax in (ax1, ax2, ax3):
        ax.set_facecolor("#1A1A1A")
        ax.grid(True, alpha=0.25, axis="y", linewidth=0.5)
        ax.tick_params(colors="#888888", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

    # ── PRĘDKOŚĆ W APEKSIE ─────────────────────────────────────────────────
    ax1.set_ylabel("Prędkość w apeksie [km/h]", fontsize=9, color="#CCCCCC")
    ax1.set_title("Prędkość minimalna w zakręcie", fontsize=10, color="#AAAAAA")

    for i, (drv, color) in enumerate(zip(drivers, colors)):
        events_map = {e.corner_id: e for e in analysis.driver_corners.get(drv, [])}
        apex_speeds = [events_map.get(c["id"], None) for c in corners_to_show]
        vals = [e.apex_speed if e else 0 for e in apex_speeds]
        bars = ax1.bar(x + i * bar_w - (n_drivers - 1) * bar_w / 2, vals,
                       bar_w * 0.9, color=color, alpha=0.85, label=drv)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         f"{val:.0f}", ha="center", va="bottom",
                         fontsize=6, color=color, rotation=90)

    ax1.legend(fontsize=9, framealpha=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"T{c['id']}" for c in corners_to_show])

    # ── DYSTANS HAMOWANIA ──────────────────────────────────────────────────
    ax2.set_ylabel("Dystans hamowania [m]", fontsize=9, color="#CCCCCC")
    ax2.set_title("Punkt hamowania przed apeksem", fontsize=10, color="#AAAAAA")

    for i, (drv, color) in enumerate(zip(drivers, colors)):
        events_map = {e.corner_id: e for e in analysis.driver_corners.get(drv, [])}
        brake_dists = [events_map[c["id"]].braking_distance
                       if c["id"] in events_map else 0
                       for c in corners_to_show]
        ax2.bar(x + i * bar_w - (n_drivers - 1) * bar_w / 2, brake_dists,
                bar_w * 0.9, color=color, alpha=0.85, label=drv)

    ax2.legend(fontsize=9, framealpha=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"T{c['id']}" for c in corners_to_show])

    # ── PUNKT WYJŚCIA (FULL THROTTLE) ──────────────────────────────────────
    ax3.set_ylabel("Dystans po apeksie → pełny gaz [m]", fontsize=9, color="#CCCCCC")
    ax3.set_title("Wczesność powrotu do gazu", fontsize=10, color="#AAAAAA")
    ax3.set_xlabel("Zakręt", fontsize=9, color="#CCCCCC")

    for i, (drv, color) in enumerate(zip(drivers, colors)):
        events_map = {e.corner_id: e for e in analysis.driver_corners.get(drv, [])}
        exit_dists = [
            max(0, events_map[c["id"]].exit_throttle_point - events_map[c["id"]].apex_distance)
            if c["id"] in events_map else 0
            for c in corners_to_show
        ]
        ax3.bar(x + i * bar_w - (n_drivers - 1) * bar_w / 2, exit_dists,
                bar_w * 0.9, color=color, alpha=0.85, label=drv)

    ax3.legend(fontsize=9, framealpha=0.6)
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"T{c['id']}" for c in corners_to_show])

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save:
        drivers_str = "_".join(sorted(drivers_data.keys()))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_corners.png"
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
