"""
Odcisk palca stylu jazdy kierowcy (Driver Style Fingerprint).
Oblicza wielowymiarowe metryki charakteryzujące styl jazdy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from .data_loader import DriverLapData
from .corner_analysis import CornerAnalysis


@dataclass
class StyleFingerprint:
    """Metryki stylu jazdy jednego kierowcy (0–100, wyżej = lepiej/więcej)."""
    driver: str
    color: str

    full_throttle_pct: float
    heavy_braking_pct: float
    coasting_pct: float
    avg_apex_speed_norm: float
    braking_aggressiveness: float
    throttle_smoothness: float
    high_rpm_pct: float
    avg_speed_norm: float
    gear_change_freq: float
    braking_consistency: float

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
    if hi <= lo:
        return 50.0
    return float(np.clip((value - lo) / (hi - lo) * 100, 0, 100))


def compute_style_fingerprint(
    data: DriverLapData,
    corner_analysis: Optional[CornerAnalysis] = None,
    fleet_stats: Optional[dict] = None,
) -> StyleFingerprint:
    telem = data.telemetry
    n = len(telem)
    if n == 0:
        return StyleFingerprint(
            driver=data.driver, color=data.color,
            **{f: 0.0 for f in METRIC_FIELDS},
        )

    speed    = telem["Speed"].values
    throttle = telem["Throttle"].values if "Throttle" in telem.columns else np.zeros(n)
    brake    = telem["Brake"].values    if "Brake"    in telem.columns else np.zeros(n)
    rpm      = telem["RPM"].values      if "RPM"      in telem.columns else np.zeros(n)
    gear     = telem["nGear"].values    if "nGear"    in telem.columns else np.ones(n)

    if brake.max() <= 1.0:
        brake = brake * 100.0

    full_throttle_pct = float((throttle > 90).sum() / n * 100)
    heavy_braking_pct = float((brake > 20).sum() / n * 100)
    coasting_pct      = float(((throttle < 10) & (brake < 5)).sum() / n * 100)

    avg_apex_speed_norm  = 0.0
    braking_aggressiveness = 0.0
    braking_consistency    = 0.0

    if corner_analysis and data.driver in corner_analysis.driver_corners:
        events = corner_analysis.driver_corners[data.driver]
        if events:
            avg_apex_speed_norm    = float(np.mean([e.apex_speed for e in events]))
            braking_aggressiveness = float(np.mean([e.max_brake_pressure for e in events]))
            brake_dists = [e.braking_distance for e in events]
            if len(brake_dists) > 1:
                braking_consistency = float(
                    max(0, 100 - np.std(brake_dists) / (np.mean(brake_dists) + 1) * 100)
                )
            else:
                braking_consistency = 50.0

    throt_valid = throttle[throttle > 5]
    if len(throt_valid) > 1:
        throttle_smoothness = float(
            max(0, 100 - (np.std(throt_valid) / (np.mean(throt_valid) + 1e-6)) * 100)
        )
    else:
        throttle_smoothness = 50.0

    max_rpm = rpm.max()
    high_rpm_pct = float((rpm > 0.9 * max_rpm).sum() / n * 100) if max_rpm > 0 else 0.0

    avg_speed_norm  = float(np.mean(speed))
    gear_changes    = np.sum(np.diff(gear.astype(int)) != 0)
    gear_change_freq = float(gear_changes / n * 1000)

    raw = {
        "full_throttle_pct":    full_throttle_pct,
        "heavy_braking_pct":    heavy_braking_pct,
        "coasting_pct":         coasting_pct,
        "avg_apex_speed_raw":   avg_apex_speed_norm,
        "braking_aggressiveness": braking_aggressiveness,
        "throttle_smoothness":  throttle_smoothness,
        "high_rpm_pct":         high_rpm_pct,
        "avg_speed_raw":        avg_speed_norm,
        "gear_change_freq":     gear_change_freq,
        "braking_consistency":  braking_consistency,
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
    if len(fingerprints) < 2:
        return fingerprints

    for field_name in METRIC_FIELDS:
        vals = [getattr(fp, field_name) for fp in fingerprints]
        lo, hi = min(vals), max(vals)
        for fp in fingerprints:
            object.__setattr__(fp, field_name, _safe_norm(getattr(fp, field_name), lo, hi))

    return fingerprints
