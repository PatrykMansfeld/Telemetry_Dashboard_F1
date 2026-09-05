"""
Dashboard uruchamiany bez przeglądarki (streamlit.testing).

Sprawdzamy, że ekran startowy i wszystkie zakładki renderują się bez wyjątku —
w obu motywach i z załadowaną sesją B.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from f1tele import plots
from f1tele.corner_analysis import run_corner_analysis
from f1tele.driver_style import compute_style_fingerprint, normalize_fingerprints
from f1tele.pipeline import AnalysisResult
from f1tele.sector_analysis import compute_mini_sectors, compute_sector_stats

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture(scope="module")
def result_factory(drivers, session, race_pace, positions, weather):
    """Buduje gotowy AnalysisResult bez odpytywania FastF1."""
    def build(theme: str) -> AnalysisResult:
        corners = run_corner_analysis(drivers)
        fingerprints = normalize_fingerprints(
            [compute_style_fingerprint(d, corners) for d in drivers.values()])
        figures = {
            "telemetry": plots.plot_telemetry_interactive(drivers, session, theme=theme),
            "corners": plots.plot_corners_interactive(drivers, corners, session,
                                                      theme=theme),
            "radar": plots.plot_radar_interactive(fingerprints, session, theme=theme),
            "track_dominance": plots.plot_driver_dominance_map_interactive(
                drivers, session, theme=theme),
            "race_pace": plots.plot_race_pace_interactive(race_pace, drivers, session,
                                                          theme=theme),
            "weather": plots.plot_weather_interactive(weather, session, theme=theme),
        }
        return AnalysisResult(
            session=session, drivers=drivers, theme=theme, corners=corners,
            mini_sectors=compute_mini_sectors(drivers, 20),
            sector_stats=compute_sector_stats(drivers),
            fingerprints=fingerprints, race_pace=race_pace, positions=positions,
            weather=weather, figures=figures,
            warnings=["przyklad: TypeError — test"],
        )
    return build


def _run(**session_state) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=300)
    for key, value in session_state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception, [str(e.value) for e in app.exception]
    return app


def test_welcome_screen_renders():
    app = _run()
    assert any("Zacznij od wyboru sesji" in block.value for block in app.markdown)
    assert any("Uruchom analizę" in button.label for button in app.button)


def test_controls_live_in_the_sidebar():
    """Panel sterowania ma być w sidebarze, a nie nad wynikami."""
    app = _run()
    labels = [widget.label for widget in app.sidebar.number_input]
    assert "Rok" in labels, labels
    assert any("Uruchom analizę" in b.label for b in app.sidebar.button)


def test_theme_toggle_switches_state():
    app = _run()
    toggle = next(b for b in app.button if "Jasny" in b.label or "Ciemny" in b.label)
    app = toggle.click().run()
    assert not app.exception, [str(e.value) for e in app.exception]
    assert app.session_state["theme"] == "light"


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_all_tabs_render_with_results(result_factory, theme):
    app = _run(theme=theme, result=result_factory(theme))
    assert len(app.tabs) >= 9
    assert any("Test Grand Prix" in block.value for block in app.markdown)


def test_tables_use_the_app_theme(result_factory):
    """
    Tabele rysujemy własnym HTML-em (components.table).

    `st.dataframe` rysuje się na canvasie i bierze kolory z config.toml, więc
    w motywie wybranym w aplikacji wyglądałaby obco. Ten test pilnuje, żeby
    nie wróciła tylnymi drzwiami.
    """
    app = _run(theme="light", result=result_factory("light"))
    assert not app.dataframe, "zakładki powinny używać components.table"
    assert any('class="data-table"' in block.value for block in app.markdown)


def test_cross_session_renders(result_factory):
    app = _run(theme="light", result=result_factory("light"),
               session_b=result_factory("light"))
    assert any("SESJA B" in block.value for block in app.markdown)
