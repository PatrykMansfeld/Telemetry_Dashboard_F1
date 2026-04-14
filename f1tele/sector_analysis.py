"""
Analiza sektorów i mini-sektorów.
Dzieli okrążenie na 3 oficjalne sektory oraz N równych mini-sektorów.
Dla każdego mini-sektora oblicza dominację kierowcy (kto był szybszy).
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
from scipy.interpolate import interp1d
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
    "text.color": "#CCCCCC",
    "font.family": "monospace",
}


@dataclass
class MiniSector:
    """Wyniki jednego mini-sektora."""
    index: int
    dist_start: float
    dist_end: float
    fastest_driver: str
    times: dict[str, float]          # {driver: czas_przejazdu}
    speeds: dict[str, float]         # {driver: avg_speed}


def _time_in_range(
    telemetry: pd.DataFrame,
    d_start: float,
    d_end: float,
) -> float:
    """Oblicza czas przejazdu odcinka [d_start, d_end] w sekundach."""
    mask = (telemetry["Distance"] >= d_start) & (telemetry["Distance"] <= d_end)
    seg = telemetry[mask]
    if len(seg) < 2:
        return 0.0

    dist = seg["Distance"].values
    speed = seg["Speed"].values
    # Czas = suma (Δdystans / prędkość_m/s)
    dt = np.where(speed > 1, np.diff(dist, prepend=dist[0]) / (speed / 3.6), 0)
    return float(dt.sum())


def _avg_speed_in_range(
    telemetry: pd.DataFrame,
    d_start: float,
    d_end: float,
) -> float:
    mask = (telemetry["Distance"] >= d_start) & (telemetry["Distance"] <= d_end)
    seg = telemetry[mask]
    if seg.empty:
        return 0.0
    return float(seg["Speed"].mean())


def compute_mini_sectors(
    drivers_data: dict[str, DriverLapData],
    n_sectors: int = 25,
) -> list[MiniSector]:
    """
    Dzieli okrążenie na n równych mini-sektorów i oblicza dominację.

    Args:
        drivers_data: Słownik {driver: DriverLapData}
        n_sectors: Liczba mini-sektorów

    Returns:
        Lista obiektów MiniSector
    """
    if not drivers_data:
        return []

    max_dist = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    edges = np.linspace(0, max_dist, n_sectors + 1)

    mini_sectors: list[MiniSector] = []

    for i in range(n_sectors):
        d_start = float(edges[i])
        d_end   = float(edges[i + 1])

        times: dict[str, float] = {}
        speeds: dict[str, float] = {}

        for drv, data in drivers_data.items():
            t = _time_in_range(data.telemetry, d_start, d_end)
            s = _avg_speed_in_range(data.telemetry, d_start, d_end)
            times[drv]  = t
            speeds[drv] = s

        valid = {k: v for k, v in times.items() if v > 0}
        fastest = min(valid, key=valid.get) if valid else ""

        mini_sectors.append(MiniSector(
            index=i + 1,
            dist_start=d_start,
            dist_end=d_end,
            fastest_driver=fastest,
            times=times,
            speeds=speeds,
        ))

    return mini_sectors


def compute_sector_stats(
    drivers_data: dict[str, DriverLapData],
) -> pd.DataFrame:
    """
    Oblicza statystyki dla każdego z 3 oficjalnych sektorów:
    czas, prędkość max, prędkość średnia, % pełnego gazu, % hamowania.
    """
    rows = []
    for drv, data in drivers_data.items():
        telem = data.telemetry
        total_dist = telem["Distance"].max()
        sector_bounds = [
            (0.0,           total_dist / 3),
            (total_dist / 3,     2 * total_dist / 3),
            (2 * total_dist / 3, total_dist),
        ]

        for s_idx, (d_start, d_end) in enumerate(sector_bounds, start=1):
            mask = (telem["Distance"] >= d_start) & (telem["Distance"] <= d_end)
            seg = telem[mask]
            if seg.empty:
                continue

            full_throttle_pct = (
                (seg["Throttle"] > 90).sum() / len(seg) * 100
                if "Throttle" in seg.columns else 0
            )
            brake_pct = (
                (seg["Brake"] > 5).sum() / len(seg) * 100
                if "Brake" in seg.columns else 0
            )
            # Korekta dla Brake 0/1
            brake_col = seg["Brake"].values if "Brake" in seg.columns else np.zeros(len(seg))
            if brake_col.max() <= 1:
                brake_pct = (brake_col > 0.05).sum() / len(seg) * 100

            rows.append({
                "Driver": drv,
                "Sector": f"S{s_idx}",
                "Time_s": _time_in_range(data.telemetry, d_start, d_end),
                "MaxSpeed": float(seg["Speed"].max()),
                "AvgSpeed": float(seg["Speed"].mean()),
                "FullThrottle_pct": full_throttle_pct,
                "Braking_pct": brake_pct,
                "Official_s": [data.sector1, data.sector2, data.sector3][s_idx - 1],
            })

    return pd.DataFrame(rows)


def print_sector_stats(stats_df: pd.DataFrame) -> None:
    """Wyświetla tabelę statystyk sektorowych."""
    table = Table(
        title="[bold]Statystyki sektorowe[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    for col in ["Kierowca", "Sektor", "Czas [s]", "MaxV [km/h]", "AvgV [km/h]",
                "Pełny gaz%", "Hamowanie%", "Oficjalny [s]"]:
        table.add_column(col, justify="right" if col not in ("Kierowca", "Sektor") else "left")

    for _, row in stats_df.sort_values(["Sector", "Time_s"]).iterrows():
        table.add_row(
            str(row["Driver"]),
            str(row["Sector"]),
            f"{row['Time_s']:.3f}",
            f"{row['MaxSpeed']:.1f}",
            f"{row['AvgSpeed']:.1f}",
            f"{row['FullThrottle_pct']:.1f}%",
            f"{row['Braking_pct']:.1f}%",
            f"{row['Official_s']:.3f}" if row["Official_s"] > 0 else "—",
        )

    console.print(table)


def plot_mini_sector_dominance(
    drivers_data: dict[str, DriverLapData],
    mini_sectors: list[MiniSector],
    session_data: SessionData,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Wykres paskowy dominacji mini-sektorów + wykresy prędkości.
    Każdy mini-sektor jest pokolorowany kolorem najszybszego kierowcy.
    """
    plt.rcParams.update(PLOT_STYLE)

    if not mini_sectors:
        return None

    drivers = list(drivers_data.keys())

    fig, axes = plt.subplots(3, 1, figsize=(18, 9), gridspec_kw={"height_ratios": [1, 2, 2]})
    fig.patch.set_facecolor("#0F0F0F")
    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Dominacja mini-sektorów  |  {session_data.session_type}",
        fontsize=13, fontweight="bold", color="#FFFFFF", y=0.99,
    )

    ax_dom, ax_time, ax_speed = axes
    for ax in axes:
        ax.set_facecolor("#1A1A1A")
        ax.tick_params(colors="#888888", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

    # ── PASEK DOMINACJI ────────────────────────────────────────────────────
    ax_dom.set_title("Dominacja w mini-sektorach", fontsize=10, color="#AAAAAA")
    ax_dom.set_yticks([])
    ax_dom.set_xlim(0, mini_sectors[-1].dist_end)

    for ms in mini_sectors:
        fastest = ms.fastest_driver
        color = drivers_data[fastest].color if fastest in drivers_data else "#555555"
        ax_dom.barh(
            0, ms.dist_end - ms.dist_start, left=ms.dist_start,
            color=color, height=0.8, alpha=0.9
        )

    # Legenda
    patches = [
        mpatches.Patch(color=drivers_data[d].color, label=d)
        for d in drivers
    ]
    ax_dom.legend(handles=patches, loc="upper right", fontsize=9, framealpha=0.7)
    ax_dom.set_xlabel("")

    # ── DELTA CZASU W MINI-SEKTORACH ───────────────────────────────────────
    ax_time.set_title("Skumulowana delta czasu [s]", fontsize=10, color="#AAAAAA")
    ax_time.set_ylabel("Δ czas [s]", fontsize=9, color="#CCCCCC")
    ax_time.axhline(0, color="#555555", linewidth=0.8, linestyle="--")
    ax_time.grid(True, alpha=0.25, linewidth=0.5)

    if len(drivers) >= 2:
        ref_drv = min(drivers_data.values(), key=lambda d: d.lap_time).driver
        for drv in drivers:
            if drv == ref_drv:
                continue
            cum_delta = 0.0
            dists = []
            deltas = []
            for ms in mini_sectors:
                ref_t = ms.times.get(ref_drv, 0)
                drv_t = ms.times.get(drv, 0)
                if ref_t > 0 and drv_t > 0:
                    cum_delta += drv_t - ref_t
                dists.append(ms.dist_end)
                deltas.append(cum_delta)

            color = drivers_data[drv].color
            ax_time.plot(dists, deltas, color=color, linewidth=1.5, label=f"{drv} vs {ref_drv}")
            ax_time.fill_between(dists, 0, deltas, color=color, alpha=0.08)

        ax_time.legend(fontsize=9, framealpha=0.6)

    # ── PRĘDKOŚĆ ŚREDNIA W MINI-SEKTORACH ──────────────────────────────────
    ax_speed.set_title("Średnia prędkość w mini-sektorach [km/h]", fontsize=10, color="#AAAAAA")
    ax_speed.set_ylabel("Prędkość [km/h]", fontsize=9, color="#CCCCCC")
    ax_speed.set_xlabel("Dystans [m]", fontsize=9, color="#CCCCCC")
    ax_speed.grid(True, alpha=0.25, linewidth=0.5)

    for drv in drivers:
        dists  = [ms.dist_start + (ms.dist_end - ms.dist_start) / 2 for ms in mini_sectors]
        speeds = [ms.speeds.get(drv, 0) for ms in mini_sectors]
        ax_speed.plot(dists, speeds, color=drivers_data[drv].color,
                      linewidth=1.4, label=drv, alpha=0.9)

    ax_speed.legend(fontsize=9, framealpha=0.6)

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    if save:
        drivers_str = "_".join(sorted(drivers_data.keys()))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_mini_sectors.png"
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


def plot_sector_heatmap(
    stats_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    save: bool = True,
    show: bool = False,
) -> Optional[Path]:
    """
    Mapa ciepła statystyk sektorowych: każdy kierowca × sektor.
    """
    plt.rcParams.update(PLOT_STYLE)
    if stats_df.empty:
        return None

    metrics = ["Time_s", "MaxSpeed", "AvgSpeed", "FullThrottle_pct", "Braking_pct"]
    metric_labels = ["Czas [s]", "Max V [km/h]", "Śr. V [km/h]", "Pełny gaz %", "Hamowanie %"]

    sectors = ["S1", "S2", "S3"]
    drivers = sorted(stats_df["Driver"].unique())

    fig, axes = plt.subplots(1, len(metrics), figsize=(18, max(4, len(drivers) * 1.2 + 2)))
    fig.patch.set_facecolor("#0F0F0F")
    fig.suptitle(
        f"{session_data.event_name} {session_data.year}  |  Mapa ciepła sektorów",
        fontsize=12, fontweight="bold", color="#FFFFFF",
    )

    for ax, metric, label in zip(axes, metrics, metric_labels):
        ax.set_facecolor("#1A1A1A")
        ax.set_title(label, fontsize=9, color="#CCCCCC", pad=4)
        ax.tick_params(colors="#888888", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")

        matrix = np.zeros((len(drivers), len(sectors)))
        for i, drv in enumerate(drivers):
            for j, sec in enumerate(sectors):
                row = stats_df[(stats_df["Driver"] == drv) & (stats_df["Sector"] == sec)]
                if not row.empty:
                    matrix[i, j] = float(row[metric].iloc[0])

        # Normalizacja kolumn (niższy czas = lepiej → odwróć dla czasu)
        normed = matrix.copy()
        for j in range(len(sectors)):
            col = matrix[:, j]
            col_min, col_max = col.min(), col.max()
            if col_max > col_min:
                if metric == "Time_s":
                    normed[:, j] = 1.0 - (col - col_min) / (col_max - col_min)
                else:
                    normed[:, j] = (col - col_min) / (col_max - col_min)
            else:
                normed[:, j] = 0.5

        im = ax.imshow(normed, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

        for i in range(len(drivers)):
            for j in range(len(sectors)):
                val = matrix[i, j]
                txt = f"{val:.2f}" if metric in ("Time_s",) else f"{val:.1f}"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=7, color="#FFFFFF", fontweight="bold")

        ax.set_xticks(range(len(sectors)))
        ax.set_xticklabels(sectors)
        ax.set_yticks(range(len(drivers)))
        ax.set_yticklabels(drivers)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if save:
        drivers_str = "_".join(sorted(drivers))
        filename = (
            f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
            f"{session_data.session_type}_{drivers_str}_sector_heatmap.png"
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
