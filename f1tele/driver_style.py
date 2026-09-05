"""
Odcisk palca stylu jazdy kierowcy (Driver Style Fingerprint).

Liczymy 10 metryk opisujących, *jak* kierowca jedzie okrążenie — nie jak
szybko. Metryki mają różne jednostki, więc przed pokazaniem na radarze
`normalize_fingerprints` skaluje je do 0–100 **względem porównywanej grupy**:
100 = najwyższa wartość w tym zestawieniu, nie wartość absolutna.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import (
    BRAKE_COAST_THRESHOLD,
    BRAKE_HEAVY_THRESHOLD,
    HIGH_RPM_THRESHOLD,
    THROTTLE_ACTIVE_THRESHOLD,
    THROTTLE_COAST_THRESHOLD,
    THROTTLE_FULL_THRESHOLD,
)
from .corner_analysis import CornerAnalysis
from .data_loader import DriverLapData


@dataclass
class StyleFingerprint:
    """Metryki stylu jazdy jednego kierowcy (0–100, wyżej = więcej danej cechy)."""
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

# Jednostki surowych metryk — pokazujemy je obok wartości znormalizowanych,
# żeby było widać, czy różnica na radarze to 20 km/h, czy 0,2 km/h.
METRIC_UNITS = [
    "%", "%", "%", "km/h", "%", "pkt", "%", "km/h", "zm./1000 pr.", "pkt",
]

# Minimalna liczba kierowców, przy której skalowanie względem grupy ma sens.
MIN_DRIVERS_FOR_SCALE = 3

# Neutralna wartość, gdy metryki nie da się policzyć (za mało danych).
NEUTRAL = 50.0


def _safe_norm(value: float, lo: float, hi: float) -> float:
    """Skaluje wartość do 0–100 w zakresie [lo, hi]."""
    if hi <= lo:
        return NEUTRAL
    return float(np.clip((value - lo) / (hi - lo) * 100, 0, 100))


def _stability(values: np.ndarray) -> float:
    """Powtarzalność serii jako 100 − współczynnik zmienności [%]."""
    if len(values) < 2:
        return NEUTRAL
    mean = float(np.mean(values))
    return float(max(0.0, 100 - np.std(values) / (abs(mean) + 1e-6) * 100))


def compute_style_fingerprint(
    data: DriverLapData,
    corner_analysis: CornerAnalysis | None = None,
) -> StyleFingerprint:
    """Liczy surowe (nieznormalizowane) metryki stylu jazdy z telemetrii okrążenia."""
    telem = data.telemetry
    n = len(telem)
    if n == 0:
        return StyleFingerprint(
            driver=data.driver, color=data.color,
            **dict.fromkeys(METRIC_FIELDS, 0.0),
        )

    def channel(name: str, default: float = 0.0) -> np.ndarray:
        if name in telem.columns:
            return telem[name].values
        return np.full(n, default)

    speed    = channel("Speed")
    throttle = channel("Throttle")
    rpm      = channel("RPM")
    gear     = channel("nGear", 1.0)
    brake    = channel("Brake")
    if brake.max() <= 1.0:
        brake = brake * 100.0

    full_throttle_pct = float((throttle > THROTTLE_FULL_THRESHOLD).sum() / n * 100)
    heavy_braking_pct = float((brake > BRAKE_HEAVY_THRESHOLD).sum() / n * 100)
    coasting_pct      = float((
        (throttle < THROTTLE_COAST_THRESHOLD) & (brake < BRAKE_COAST_THRESHOLD)
    ).sum() / n * 100)

    avg_apex_speed         = 0.0
    braking_aggressiveness = 0.0
    braking_consistency    = 0.0

    events = (corner_analysis.driver_corners.get(data.driver, [])
              if corner_analysis else [])
    if events:
        avg_apex_speed         = float(np.mean([e.apex_speed for e in events]))
        braking_aggressiveness = float(np.mean([e.max_brake_pressure for e in events]))
        braking_consistency    = _stability(np.array([e.braking_distance for e in events]))

    throt_valid = throttle[throttle > THROTTLE_ACTIVE_THRESHOLD]
    throttle_smoothness = _stability(throt_valid)

    max_rpm = rpm.max()
    high_rpm_pct = (float((rpm > HIGH_RPM_THRESHOLD * max_rpm).sum() / n * 100)
                    if max_rpm > 0 else 0.0)

    avg_speed        = float(np.mean(speed))
    gear_changes     = int(np.sum(np.diff(gear.astype(int)) != 0))
    gear_change_freq = float(gear_changes / n * 1000)

    metrics = dict(
        full_throttle_pct=full_throttle_pct,
        heavy_braking_pct=heavy_braking_pct,
        coasting_pct=coasting_pct,
        avg_apex_speed_norm=avg_apex_speed,
        braking_aggressiveness=braking_aggressiveness,
        throttle_smoothness=throttle_smoothness,
        high_rpm_pct=high_rpm_pct,
        avg_speed_norm=avg_speed,
        gear_change_freq=gear_change_freq,
        braking_consistency=braking_consistency,
    )

    return StyleFingerprint(
        driver=data.driver,
        color=data.color,
        raw_metrics=dict(metrics),
        **metrics,
    )


def normalize_fingerprints(
    fingerprints: list[StyleFingerprint],
) -> list[StyleFingerprint]:
    """
    Skaluje każdą metrykę do 0–100 w obrębie porównywanej grupy.

    Modyfikuje przekazane obiekty w miejscu i zwraca tę samą listę.
    Przy jednym kierowcy skalowanie nie ma sensu — zwracamy bez zmian.

    Uwaga przy dwóch kierowcach: min–max zawsze da 0 i 100, niezależnie od tego,
    czy różnica jest duża czy śladowa. Surowe wartości zostają w `raw_metrics`
    i to je warto pokazać obok wykresu (patrz `MIN_DRIVERS_FOR_SCALE`).
    """
    if len(fingerprints) < 2:
        return fingerprints

    for field_name in METRIC_FIELDS:
        vals = [getattr(fp, field_name) for fp in fingerprints]
        lo, hi = min(vals), max(vals)
        for fp in fingerprints:
            setattr(fp, field_name, _safe_norm(getattr(fp, field_name), lo, hi))

    return fingerprints
