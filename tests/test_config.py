"""
Konfiguracja musi być żywa.

Przed refactorem `config.py` nie był przez nikogo importowany — zmiana progu
nie robiła nic. Ten test pilnuje, żeby każda stała z `f1tele/config.py` była
naprawdę gdzieś używana.
"""

from __future__ import annotations

import re
from pathlib import Path

from f1tele import config

ROOT = Path(__file__).resolve().parent.parent
SEARCH_DIRS = ["f1tele", "ui"]
CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _sources() -> str:
    files = [ROOT / "app.py"]
    for folder in SEARCH_DIRS:
        files += sorted((ROOT / folder).rglob("*.py"))
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in files
        if path.name != "config.py"
    )


def test_every_config_constant_is_used():
    code = _sources()
    unused = [
        name for name in vars(config)
        if CONSTANT.match(name) and not re.search(rf"\b{name}\b", code)
    ]
    assert not unused, f"Nieużywane stałe konfiguracji: {unused}"


def test_season_rounds_cover_the_selectable_years():
    """Każdy rok możliwy do wybrania w UI musi mieć znaną liczbę rund."""
    from ui.constants import max_round_for_year

    for year in range(config.MIN_YEAR, config.MAX_YEAR + 1):
        assert max_round_for_year(year) >= 10, year


def test_defaults_are_within_allowed_ranges():
    assert config.MIN_YEAR <= config.DEFAULT_YEAR <= config.MAX_YEAR
    assert 1 <= int(config.DEFAULT_ROUND) <= config.SEASON_ROUNDS[config.DEFAULT_YEAR]
    assert config.DEFAULT_SESSION in __import__(
        "f1tele.data_loader", fromlist=["SESSION_TYPES"]).SESSION_TYPES
    assert len(config.DEFAULT_DRIVERS) <= config.MAX_DRIVERS
    assert config.DEFAULT_PLOT_THEME in __import__(
        "f1tele.plots", fromlist=["THEMES"]).THEMES
