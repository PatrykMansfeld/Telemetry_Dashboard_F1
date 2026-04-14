"""
Moduł analizy okrążeń — wykresy telemetrii: prędkość, gaz, hamulec, biegi.
Obsługuje porównanie wielu kierowców na jednym wykresie.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.gridspec import GridSpec
from scipy.interpolate import interp1d
from rich.console import Console

from .data_loader import DriverLapData, SessionData

console = Console()

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    "legend.facecolor": "#222222",
    "legend.edgecolor": "#444444",
    "legend.labelcolor": "#CCCCCC",
    "text.color": "#CCCCCC",
    "font.family": "monospace",
}


def _apply_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def _common_distance_axis(drivers_data: dict[str, DriverLapData]) -> np.ndarray:
    """Tworzy wspólną oś dystansu dla porównania kierowców."""
    max_dist = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    return np.linspace(0, max_dist, 1500)


def _interpolate_channel(
    telemetry: pd.DataFrame,
    channel: str,
    common_dist: np.ndarray,
) -> np.ndarray:
    """Interpoluje kanał telemetrii na wspólną oś dystansu."""
    dist = telemetry["Distance"].values
    values = telemetry[channel].values

    # Usuń duplikaty dystansu
    _, idx = np.unique(dist, return_index=True)
    dist = dist[idx]
    values = values[idx]

    if len(dist) < 2:
        return np.zeros_like(common_dist)

    f = interp1d(dist, values, kind="linear", bounds_error=False, fill_value="extrapolate")
    return f(common_dist)


def plot_telemetry_comparison(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Główny wykres porównania telemetrii: prędkość, gaz, hamulec, biegi, RPM.

    Args:
        drivers_data: Słownik {driver: DriverLapData}
        session_data: Informacje o sesji
        save: Czy zapisać do pliku
        show: Czy wyświetlić interaktywnie

    Returns:
        Ścieżka do zapisanego pliku lub None
    """
    _apply_style()
    n_drivers = len(drivers_data)
    if n_drivers == 0:
        console.print("[red]Brak danych do wykresu[/red]")
        return None

    common_dist = _common_distance_axis(drivers_data)

    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor("#0F0F0F")

    title = (
        f"{session_data.event_name} {session_data.year}  |  {session_data.session_type}  |  "
        f"{session_data.circuit_name}"
    )
    fig.suptitle(title, fontsize=14, fontweight="bold", color="#FFFFFF", y=0.98)

    gs = GridSpec(
        6, 1,
        figure=fig,
        height_ratios=[3, 1.5, 1, 1, 1.2, 0.8],
        hspace=0.08,
        left=0.07, right=0.97, top=0.94, bottom=0.06,
    )

    ax_speed  = fig.add_subplot(gs[0])
    ax_delta  = fig.add_subplot(gs[1], sharex=ax_speed)
    ax_throt  = fig.add_subplot(gs[2], sharex=ax_speed)
    ax_brake  = fig.add_subplot(gs[3], sharex=ax_speed)
    ax_gear   = fig.add_subplot(gs[4], sharex=ax_speed)
    ax_rpm    = fig.add_subplot(gs[5], sharex=ax_speed)

    axes = [ax_speed, ax_delta, ax_throt, ax_brake, ax_gear, ax_rpm]
    for ax in axes:
        ax.set_facecolor("#1A1A1A")
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.tick_params(colors="#888888", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

    # ── PRĘDKOŚĆ ───────────────────────────────────────────────────────────
    ax_speed.set_ylabel("Prędkość [km/h]", fontsize=9, color="#CCCCCC")
    ax_speed.set_title("Porównanie telemetrii", fontsize=10, color="#AAAAAA", pad=4)

    reference_speed: Optional[np.ndarray] = None
    driver_list = list(drivers_data.values())

    for i, d in enumerate(driver_list):
        spd = _interpolate_channel(d.telemetry, "Speed", common_dist)
        ax_speed.plot(common_dist, spd, color=d.color, linewidth=1.4,
                      label=f"{d.driver}  {d.lap_time_str}", alpha=0.92)
        if reference_speed is None:
            reference_speed = spd

    ax_speed.set_ylim(bottom=0)
    ax_speed.legend(loc="upper right", fontsize=9, framealpha=0.7)

    # ── DELTA CZASU ────────────────────────────────────────────────────────
    ax_delta.set_ylabel("Δ czas [s]", fontsize=9, color="#CCCCCC")
    ax_delta.axhline(0, color="#555555", linewidth=0.8, linestyle="--")

    if reference_speed is not None and len(driver_list) > 1:
        ref_d = driver_list[0]
        ref_spd = _interpolate_channel(ref_d.telemetry, "Speed", common_dist)

        for d in driver_list[1:]:
            spd = _interpolate_channel(d.telemetry, "Speed", common_dist)
            # Przybliżona delta czasu z różnicy prędkości
            speed_diff = spd - ref_spd
            # Czas pokonania każdego metra segmentu
            step = np.diff(common_dist, prepend=common_dist[0])
            ref_time_per_m = np.where(ref_spd > 1, step / (ref_spd / 3.6), 0)
            drv_time_per_m = np.where(spd > 1, step / (spd / 3.6), 0)
            delta = np.cumsum(drv_time_per_m - ref_time_per_m)
            ax_delta.plot(
                common_dist, delta, color=d.color, linewidth=1.2,
                label=f"{d.driver} vs {ref_d.driver}", alpha=0.9,
            )
            ax_delta.fill_between(common_dist, 0, delta,
                                  color=d.color, alpha=0.08)

        ax_delta.legend(loc="upper right", fontsize=8, framealpha=0.6)
    else:
        ax_delta.text(0.5, 0.5, "Delta wymaga ≥ 2 kierowców",
                      ha="center", va="center", transform=ax_delta.transAxes,
                      color="#666666", fontsize=9)

    # ── GAZ ────────────────────────────────────────────────────────────────
    ax_throt.set_ylabel("Gaz [%]", fontsize=9, color="#CCCCCC")
    for d in driver_list:
        throt = _interpolate_channel(d.telemetry, "Throttle", common_dist)
        ax_throt.plot(common_dist, throt, color=d.color, linewidth=1.0, alpha=0.85)
        ax_throt.fill_between(common_dist, 0, throt, color=d.color, alpha=0.07)
    ax_throt.set_ylim(0, 105)

    # ── HAMULEC ────────────────────────────────────────────────────────────
    ax_brake.set_ylabel("Hamulec", fontsize=9, color="#CCCCCC")
    for d in driver_list:
        brake = _interpolate_channel(d.telemetry, "Brake", common_dist)
        # Brake bywa 0/1 (bool) lub 0–100
        if brake.max() <= 1:
            brake = brake * 100
        ax_brake.plot(common_dist, brake, color=d.color, linewidth=1.0, alpha=0.85)
        ax_brake.fill_between(common_dist, 0, brake, color=d.color, alpha=0.07)
    ax_brake.set_ylim(-5, 110)

    # ── BIEGI ──────────────────────────────────────────────────────────────
    ax_gear.set_ylabel("Bieg", fontsize=9, color="#CCCCCC")
    for d in driver_list:
        gear = _interpolate_channel(d.telemetry, "nGear", common_dist)
        gear = np.clip(np.round(gear), 1, 8)
        ax_gear.step(common_dist, gear, color=d.color, linewidth=1.0,
                     where="post", alpha=0.85)
    ax_gear.set_yticks(range(1, 9))
    ax_gear.set_ylim(0.5, 8.5)

    # ── RPM ────────────────────────────────────────────────────────────────
    ax_rpm.set_ylabel("RPM", fontsize=9, color="#CCCCCC")
    ax_rpm.set_xlabel("Dystans [m]", fontsize=9, color="#CCCCCC")
    for d in driver_list:
        rpm = _interpolate_channel(d.telemetry, "RPM", common_dist)
        ax_rpm.plot(common_dist, rpm, color=d.color, linewidth=1.0, alpha=0.85)

    # Ukryj etykiety osi X na górnych wykresach
    for ax in axes[:-1]:
        ax.tick_params(labelbottom=False)

    if save:
        drivers_str = "_".join(sorted(drivers_data.keys()))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_telemetry.png"
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


def plot_speed_trace_detail(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    distance_range: tuple[float, float] = (0, None),
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Szczegółowy wykres prędkości dla wybranego zakresu dystansu (np. konkretny sektor).
    """
    _apply_style()
    common_dist = _common_distance_axis(drivers_data)

    d_start = distance_range[0]
    d_end = distance_range[1] or common_dist[-1]
    mask = (common_dist >= d_start) & (common_dist <= d_end)
    dist_seg = common_dist[mask]

    fig, axes = plt.subplots(3, 1, figsize=(16, 9), sharex=True)
    fig.patch.set_facecolor("#0F0F0F")
    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Szczegółowa analiza [{d_start:.0f}–{d_end:.0f} m]",
        fontsize=12, fontweight="bold", color="#FFFFFF",
    )

    channels = [("Speed", "Prędkość [km/h]"), ("Throttle", "Gaz [%]"), ("Brake", "Hamulec [%]")]

    for ax, (ch, label) in zip(axes, channels):
        ax.set_facecolor("#1A1A1A")
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.set_ylabel(label, fontsize=9, color="#CCCCCC")
        ax.tick_params(colors="#888888", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

        for d in drivers_data.values():
            vals = _interpolate_channel(d.telemetry, ch, common_dist)[mask]
            if ch == "Brake" and vals.max() <= 1:
                vals = vals * 100
            ax.plot(dist_seg, vals, color=d.color, linewidth=1.5,
                    label=d.driver, alpha=0.9)
            ax.fill_between(dist_seg, 0, vals, color=d.color, alpha=0.05)

    axes[0].legend(fontsize=9, loc="upper right", framealpha=0.7)
    axes[-1].set_xlabel("Dystans [m]", fontsize=9, color="#CCCCCC")
    plt.tight_layout()

    if save:
        drivers_str = "_".join(sorted(drivers_data.keys()))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_speed_detail.png"
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
