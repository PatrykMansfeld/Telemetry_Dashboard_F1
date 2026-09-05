"""Pipeline analizy na podstawionej warstwie danych (bez sieci)."""

from __future__ import annotations

import pytest

from f1tele import pipeline, plots


@pytest.fixture
def fake_data(monkeypatch, drivers, session, race_pace, positions, weather):
    """Podmienia dostęp do FastF1 na dane syntetyczne."""
    def fake_load_drivers(_session, wanted, on_progress=None, **_kwargs):
        for i, drv in enumerate(wanted, start=1):
            if on_progress:
                on_progress(drv, i, len(wanted))
        return {d: drivers[d] for d in wanted if d in drivers}

    monkeypatch.setattr(pipeline, "load_session", lambda *a, **k: session)
    monkeypatch.setattr(pipeline, "load_drivers_data", fake_load_drivers)
    monkeypatch.setattr(pipeline, "get_race_pace_data", lambda *a, **k: race_pace)
    monkeypatch.setattr(pipeline, "get_position_data", lambda *a, **k: positions)
    monkeypatch.setattr(pipeline, "get_weather_data", lambda *a, **k: weather)


def _request(**overrides) -> pipeline.AnalysisRequest:
    params = dict(year=2024, round_number=5, session_type="Q",
                  drivers=["VER", "NOR", "LEC"], mini_sectors=20)
    params.update(overrides)
    return pipeline.AnalysisRequest(**params)


def test_full_run_produces_all_sections(fake_data):
    steps: list[tuple[int, str]] = []
    result = pipeline.run_analysis(_request(),
                                   on_progress=lambda p, t: steps.append((p, t)))

    assert result.warnings == []
    assert len(result.figures) >= 15
    assert result.corners is not None and result.corners.corners
    assert result.sector_stats is not None and not result.sector_stats.empty
    assert len(result.fingerprints) == 3
    assert not result.race_pace.empty
    assert result.has_gps
    assert steps[-1][0] == 100


def test_drivers_sorted_by_lap_time(fake_data):
    result = pipeline.run_analysis(_request())
    times = [d.lap_time for d in result.sorted_drivers]
    assert times == sorted(times)


def test_disabled_modules_are_skipped(fake_data):
    result = pipeline.run_analysis(_request(
        drivers=["VER", "NOR"],
        modules=pipeline.Modules(telemetry=True, corners=False, sectors=False,
                                 style=False, track=False, race_pace=False,
                                 weather=False),
    ))
    assert set(result.figures) == {"telemetry", "delta_time"}
    assert result.warnings == []


def test_failing_plot_is_reported_not_raised(fake_data, monkeypatch):
    """Wywrotka jednego wykresu nie może przerwać całej analizy."""
    monkeypatch.setattr(plots, "plot_radar_interactive",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    result = pipeline.run_analysis(_request(
        drivers=["VER", "NOR"],
        modules=pipeline.Modules(telemetry=False, corners=False, sectors=False,
                                 style=True, track=False, race_pace=False,
                                 weather=False),
    ))
    assert len(result.warnings) == 1
    assert "radar" in result.warnings[0]
    assert "style_bars" in result.figures


def test_empty_driver_list_raises(fake_data):
    with pytest.raises(ValueError, match="kierowc"):
        pipeline.run_analysis(_request(drivers=[]))


def test_theme_reaches_the_figures(fake_data):
    result = pipeline.run_analysis(_request(theme="light"))
    assert result.theme == "light"
    assert str(result.figures["telemetry"].layout.paper_bgcolor).upper() != "#0F0F0F"


def test_track_animation_is_built_on_demand(fake_data):
    result = pipeline.run_analysis(_request())
    assert not any("animation" in key for key in result.figures)
    animation = pipeline.build_track_animation(result, n_frames=20)
    assert animation is not None and len(animation.frames) == 20
