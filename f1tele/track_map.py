"""
Mapa toru z dominacją kierowców.
Koloruje każdy segment toru kolorem kierowcy, który był w nim najszybszy.
Obsługuje też mapę prędkości (gradient prędkości wzdłuż toru) i mapę biegów.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from rich.console import Console

from .data_loader import DriverLapData, SessionData

console = Console()
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "plots"

PLOT_STYLE = {
    "figure.facecolor": "#0F0F0F",
    "axes.facecolor": "#0A0A0A",
    "axes.edgecolor": "#333333",
    "text.color": "#CCCCCC",
    "font.family": "monospace",
}


def _get_xy(telemetry: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Pobiera współrzędne X,Y z telemetrii."""
    if "X" in telemetry.columns and "Y" in telemetry.columns:
        return telemetry["X"].values, telemetry["Y"].values
    return np.array([]), np.array([])


def _resample_to_distance(
    telemetry: pd.DataFrame,
    channel: str,
    n_points: int = 2000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Resample X,Y i kanał na równomierną siatkę dystansu.
    Zwraca (x, y, channel_values).
    """
    x, y = _get_xy(telemetry)
    dist = telemetry["Distance"].values

    if len(x) == 0 or len(dist) == 0:
        return np.array([]), np.array([]), np.array([])

    vals = telemetry[channel].values if channel in telemetry.columns else np.zeros(len(dist))

    # Usuń duplikaty
    _, idx = np.unique(dist, return_index=True)
    dist, x, y, vals = dist[idx], x[idx], y[idx], vals[idx]

    if len(dist) < 4:
        return np.array([]), np.array([]), np.array([])

    common = np.linspace(dist[0], dist[-1], n_points)
    xi  = interp1d(dist, x,    kind="linear", fill_value="extrapolate")(common)
    yi  = interp1d(dist, y,    kind="linear", fill_value="extrapolate")(common)
    vi  = interp1d(dist, vals, kind="linear", fill_value="extrapolate")(common)

    return xi, yi, vi


def plot_driver_dominance_map(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    n_points: int = 2000,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Mapa toru: każdy segment pokolorowany kolorem najszybszego kierowcy.
    Prędkość porównana interpolacją na wspólną siatkę dystansu.
    """
    plt.rcParams.update(PLOT_STYLE)

    if not drivers_data:
        return None

    # Sprawdź czy mamy dane X,Y
    sample_drv = next(iter(drivers_data.values()))
    has_xy = "X" in sample_drv.telemetry.columns and "Y" in sample_drv.telemetry.columns

    if not has_xy:
        console.print("[yellow]⚠ Brak danych pozycji (X,Y) — mapa toru niedostępna[/yellow]")
        return None

    # Interpoluj dane na wspólną siatkę
    max_dist = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    common_dist = np.linspace(0, max_dist, n_points)

    driver_speeds: dict[str, np.ndarray] = {}
    ref_xy: tuple[np.ndarray, np.ndarray] = (np.array([]), np.array([]))

    for i, (drv, data) in enumerate(drivers_data.items()):
        xi, yi, spd = _resample_to_distance(data.telemetry, "Speed", n_points)
        driver_speeds[drv] = spd
        if i == 0 and len(xi) > 0:
            ref_xy = (xi, yi)

    if len(ref_xy[0]) == 0:
        console.print("[red]Brak współrzędnych toru[/red]")
        return None

    x_ref, y_ref = ref_xy

    # Wyznacz najszybszy kierowca w każdym segmencie
    n_segs = n_points - 1
    fastest_colors = []
    drivers_list = list(drivers_data.keys())

    for seg_i in range(n_segs):
        seg_speeds = {
            drv: driver_speeds[drv][seg_i]
            for drv in drivers_list
            if drv in driver_speeds and len(driver_speeds[drv]) > seg_i
        }
        if not seg_speeds:
            fastest_colors.append("#555555")
            continue
        fastest = max(seg_speeds, key=seg_speeds.get)
        fastest_colors.append(drivers_data[fastest].color)

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0A0A0A")
    ax.set_facecolor("#0A0A0A")
    ax.set_aspect("equal")
    ax.axis("off")

    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Dominacja na torze  |  {session_data.session_type}",
        fontsize=13, fontweight="bold", color="#FFFFFF", y=0.98,
    )

    # Tło toru (gruba linia szara)
    ax.plot(x_ref, y_ref, color="#2A2A2A", linewidth=12, solid_capstyle="round", zorder=1)

    # Segmenty z kolorami dominacji
    points  = np.c_[x_ref, y_ref].reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    for seg, color in zip(segments, fastest_colors):
        lc = LineCollection([seg], colors=[color], linewidths=5, zorder=2, capstyle="round")
        ax.add_collection(lc)

    # Linia środkowa toru
    ax.plot(x_ref, y_ref, color="#FFFFFF", linewidth=0.4, alpha=0.15, zorder=3)

    # Punkt startowy
    ax.scatter(x_ref[0], y_ref[0], color="#FFFF00", s=120, zorder=10,
               marker="D", linewidths=0, label="Start/Meta")
    ax.annotate("S/F", xy=(x_ref[0], y_ref[0]),
                xytext=(10, 10), textcoords="offset points",
                fontsize=9, color="#FFFF00", fontweight="bold")

    # Legenda
    legend_elements = [
        Patch(facecolor=drivers_data[d].color, label=f"{d}  {drivers_data[d].lap_time_str}")
        for d in drivers_list
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower right",
        fontsize=10,
        framealpha=0.85,
        facecolor="#1A1A1A",
        edgecolor="#444444",
        labelcolor="#CCCCCC",
    )

    if save:
        drivers_str = "_".join(sorted(drivers_data.keys()))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_track_dominance.png"
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


def plot_speed_heatmap_track(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = 2000,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Mapa ciepła prędkości jednego kierowcy na torze.
    Kolor każdego segmentu = prędkość (niebieski → czerwony).
    """
    plt.rcParams.update(PLOT_STYLE)

    telem = driver_data.telemetry
    if "X" not in telem.columns:
        console.print("[yellow]⚠ Brak danych X,Y — mapa prędkości niedostępna[/yellow]")
        return None

    xi, yi, spd = _resample_to_distance(telem, "Speed", n_points)
    if len(xi) == 0:
        return None

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0A0A0A")
    ax.set_facecolor("#0A0A0A")
    ax.set_aspect("equal")
    ax.axis("off")

    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Mapa prędkości: {driver_data.driver}  |  {driver_data.lap_time_str}",
        fontsize=12, fontweight="bold", color="#FFFFFF", y=0.98,
    )

    # Tło toru
    ax.plot(xi, yi, color="#1A1A1A", linewidth=14, solid_capstyle="round", zorder=1)

    # Segmenty kolorowane prędkością
    norm = plt.Normalize(spd.min(), spd.max())
    cmap = plt.cm.RdYlGn

    points   = np.c_[xi, yi].reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    lc = LineCollection(segments, cmap=cmap, norm=norm, linewidths=5,
                        capstyle="round", zorder=2)
    lc.set_array(spd[:-1])
    ax.add_collection(lc)

    # Colorbar
    cbar = fig.colorbar(lc, ax=ax, orientation="horizontal",
                        fraction=0.03, pad=0.02, shrink=0.5)
    cbar.set_label("Prędkość [km/h]", fontsize=9, color="#CCCCCC")
    cbar.ax.tick_params(colors="#888888", labelsize=8)

    # Start/Meta
    ax.scatter(xi[0], yi[0], color="#FFFF00", s=150, zorder=10,
               marker="D", linewidths=0)
    ax.annotate("S/F", xy=(xi[0], yi[0]),
                xytext=(10, 10), textcoords="offset points",
                fontsize=9, color="#FFFF00", fontweight="bold")

    if save:
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{driver_data.driver}_speed_map.png"
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


def plot_gear_map(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = 2000,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Mapa biegów na torze — każdy segment pokolorowany aktywnym biegiem.
    """
    plt.rcParams.update(PLOT_STYLE)

    telem = driver_data.telemetry
    if "X" not in telem.columns or "nGear" not in telem.columns:
        console.print("[yellow]⚠ Brak danych X,Y lub biegów — mapa biegów niedostępna[/yellow]")
        return None

    xi, yi, gear = _resample_to_distance(telem, "nGear", n_points)
    gear = np.clip(np.round(gear), 1, 8).astype(int)

    if len(xi) == 0:
        return None

    # Kolory biegów 1–8
    gear_colors = plt.cm.plasma(np.linspace(0.1, 0.95, 8))

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0A0A0A")
    ax.set_facecolor("#0A0A0A")
    ax.set_aspect("equal")
    ax.axis("off")

    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Mapa biegów: {driver_data.driver}  |  {driver_data.lap_time_str}",
        fontsize=12, fontweight="bold", color="#FFFFFF", y=0.98,
    )

    ax.plot(xi, yi, color="#1A1A1A", linewidth=14, solid_capstyle="round", zorder=1)

    for g in range(1, 9):
        mask = gear[:-1] == g
        if not mask.any():
            continue
        points   = np.c_[xi, yi].reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        seg_g    = segments[mask]
        if len(seg_g) == 0:
            continue
        color = gear_colors[g - 1]
        lc = LineCollection(seg_g, colors=[color], linewidths=5,
                            capstyle="round", zorder=2)
        ax.add_collection(lc)

    # Legenda biegów
    gear_patches = [
        Patch(facecolor=gear_colors[g - 1], label=f"Bieg {g}")
        for g in range(1, 9)
        if (gear == g).any()
    ]
    ax.legend(
        handles=gear_patches, loc="lower right", fontsize=9,
        framealpha=0.85, facecolor="#1A1A1A", edgecolor="#444444", labelcolor="#CCCCCC",
        ncol=2,
    )

    ax.scatter(xi[0], yi[0], color="#FFFF00", s=150, zorder=10, marker="D")
    ax.annotate("S/F", xy=(xi[0], yi[0]),
                xytext=(10, 10), textcoords="offset points",
                fontsize=9, color="#FFFF00", fontweight="bold")

    if save:
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{driver_data.driver}_gear_map.png"
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
