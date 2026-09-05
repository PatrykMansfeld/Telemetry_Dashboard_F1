"""
Logika analityczna: zakręty z planu toru i sektory z oficjalnych czasów.

Obie rzeczy były wcześniej przybliżeniami (detekcja minimów prędkości i podział
okrążenia na trzy równe części) — te testy pilnują, żeby nie wróciły po cichu.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from f1tele.corner_analysis import (
    corners_from_circuit,
    detect_corners,
    run_corner_analysis,
)
from f1tele.pipeline import AnalysisRequest, Modules
from f1tele.sector_analysis import (
    compute_sector_stats,
    sector_bounds,
    uses_official_sectors,
)


@pytest.fixture
def circuit_corners() -> pd.DataFrame:
    """Plan toru w formacie FastF1: numery, litery i dystans od startu."""
    return pd.DataFrame({
        "Number":   [1, 2, 3, 7, 7, 20],
        "Letter":   ["", "", "", "A", "B", ""],
        "Distance": [500.0, 1200.0, 1800.0, 2600.0, 2750.0, 9999.0],
    })


# ── Zakręty ──────────────────────────────────────────────────────────────────
def test_official_corners_keep_track_numbering(circuit_corners):
    corners = corners_from_circuit(circuit_corners, max_distance=5000.0)

    assert [c["name"] for c in corners] == ["T1", "T2", "T3", "T7A", "T7B"]
    # Zakręt poza długością okrążenia wypada
    assert all(c["distance"] < 5000 for c in corners)


def test_official_corners_win_over_detection(drivers, circuit_corners):
    analysis = run_corner_analysis(drivers, circuit_corners)

    assert analysis.is_official
    assert len(analysis.corners) == 5
    assert all(len(events) > 0 for events in analysis.driver_corners.values())


def test_detection_is_the_fallback(drivers):
    """Bez planu toru nadal coś policzymy, ale oznaczamy to jako przybliżenie."""
    analysis = run_corner_analysis(drivers, pd.DataFrame())

    assert not analysis.is_official
    assert analysis.corners

    leader = min(drivers.values(), key=lambda d: d.lap_time)
    detected = detect_corners(leader.telemetry)
    assert [c["distance"] for c in analysis.corners] == [c["distance"] for c in detected]


def test_min_speed_reflects_the_slowest_pass(drivers, circuit_corners):
    """Po analizie `min_speed` zakrętu to najniższa prędkość w całej stawce."""
    analysis = run_corner_analysis(drivers, circuit_corners)

    for corner in analysis.corners:
        apexes = [e.apex_speed for events in analysis.driver_corners.values()
                  for e in events if e.corner_id == corner["id"]]
        assert corner["min_speed"] == pytest.approx(min(apexes))


def test_corner_events_measure_every_driver(drivers, circuit_corners):
    analysis = run_corner_analysis(drivers, circuit_corners)

    for driver, events in analysis.driver_corners.items():
        for event in events:
            assert event.driver == driver
            assert event.apex_speed > 0
            assert event.braking_distance >= 0
            assert event.braking_point <= event.apex_distance


# ── Sektory ──────────────────────────────────────────────────────────────────
def test_sector_bounds_follow_official_times(drivers):
    """
    Granice sektorów mają wynikać z czasów, nie z równego podziału dystansu.

    Fixture ma sektory 30/35/35 % czasu okrążenia, więc pierwsza granica
    nie może wypaść w jednej trzeciej dystansu.
    """
    driver = drivers["VER"]
    assert uses_official_sectors(driver)

    bounds = sector_bounds(driver)
    total = float(driver.telemetry["Distance"].max())

    assert len(bounds) == 3
    assert bounds[0][0] == 0.0
    assert bounds[-1][1] == pytest.approx(total)
    # kolejne sektory nie zachodzą na siebie
    assert bounds[0][1] == bounds[1][0]
    assert bounds[1][1] == bounds[2][0]
    # granica S1 wypada wyraźnie przed jedną trzecią dystansu
    assert bounds[0][1] < total / 3


def test_sector_bounds_fall_back_without_time_channel(drivers):
    driver = drivers["VER"]
    stripped = driver.telemetry.drop(columns=["Time"])
    fallback = type(driver)(**{**vars(driver), "telemetry": stripped})

    assert not uses_official_sectors(fallback)
    bounds = sector_bounds(fallback)
    total = float(stripped["Distance"].max())
    assert bounds[0][1] == pytest.approx(total / 3)


def test_sector_stats_compare_official_with_telemetry(drivers):
    stats = compute_sector_stats(drivers)

    assert set(stats["Sector"]) == {"S1", "S2", "S3"}
    assert stats["Official"].all()

    # Czas z telemetrii powinien trzymać się blisko oficjalnego — to ta sama
    # całka, tylko liczona na innej siatce próbek.
    assert np.abs(stats["Diff_s"]).max() < 0.5

    # Suma sektorów odtwarza czas okrążenia
    for driver, group in stats.groupby("Driver"):
        assert group["Time_s"].sum() == pytest.approx(drivers[driver].lap_time, abs=0.5)


# ── Klucz cache ──────────────────────────────────────────────────────────────
def test_cache_key_ignores_theme_but_not_parameters():
    base = dict(year=2024, round_number=5, session_type="Q", drivers=["VER", "NOR"])

    dark = AnalysisRequest(**base, theme="dark")
    light = AnalysisRequest(**base, theme="light")
    assert dark.cache_key() == light.cache_key(), "motyw zmieniamy bez przeliczania"

    assert AnalysisRequest(**base, lap_number=12).cache_key() != dark.cache_key()
    assert AnalysisRequest(**base, mini_sectors=40).cache_key() != dark.cache_key()
    assert AnalysisRequest(
        **base, modules=Modules(track=False)).cache_key() != dark.cache_key()

    # Kolejność kierowców nie tworzy nowego wpisu
    swapped = AnalysisRequest(year=2024, round_number=5, session_type="Q",
                              drivers=["NOR", "VER"])
    assert swapped.cache_key() == dark.cache_key()
