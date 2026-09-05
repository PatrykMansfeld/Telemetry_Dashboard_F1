"""
Wspólne narzędzia numeryczne dla wykresów.

Telemetria każdego kierowcy ma własną, nierówną siatkę próbek — zanim
cokolwiek porównamy, sprowadzamy kanały na wspólną oś dystansu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from ..data_loader import DriverLapData


def interp(telem: pd.DataFrame, channel: str, common: np.ndarray) -> np.ndarray:
    """Interpoluje kanał telemetrii na wspólną siatkę dystansu `common`."""
    dist = telem["Distance"].values
    vals = (telem[channel].values if channel in telem.columns
            else np.zeros(len(dist)))
    _, idx = np.unique(dist, return_index=True)
    dist, vals = dist[idx], vals[idx]
    if len(dist) < 2:
        return np.zeros_like(common)
    f = interp1d(dist, vals, kind="linear",
                 bounds_error=False, fill_value="extrapolate")
    return f(common)


def common_distance(drivers_data: dict[str, DriverLapData], n: int = 1500) -> np.ndarray:
    """Wspólna oś dystansu: od zera do najkrótszego okrążenia w zestawie."""
    max_d = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    return np.linspace(0, max_d, n)


def resample_xy(
    telem: pd.DataFrame, channel: str, n: int = 2000
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Resampluje pozycję GPS wraz z kanałem telemetrii na `n` równych punktów.

    Zwraca `(x, y, wartości)`; puste tablice, gdy sesja nie ma danych GPS.
    """
    if "X" not in telem.columns or "Y" not in telem.columns:
        return np.array([]), np.array([]), np.array([])
    dist = telem["Distance"].values
    x = telem["X"].values
    y = telem["Y"].values
    vals = (telem[channel].values if channel in telem.columns
            else np.zeros(len(dist)))
    _, idx = np.unique(dist, return_index=True)
    dist, x, y, vals = dist[idx], x[idx], y[idx], vals[idx]
    if len(dist) < 4:
        return np.array([]), np.array([]), np.array([])
    common = np.linspace(dist[0], dist[-1], n)
    xi = interp1d(dist, x,    fill_value="extrapolate")(common)
    yi = interp1d(dist, y,    fill_value="extrapolate")(common)
    vi = interp1d(dist, vals, fill_value="extrapolate")(common)
    return xi, yi, vi
