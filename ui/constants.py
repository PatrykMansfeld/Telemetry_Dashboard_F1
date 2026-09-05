"""
Stałe interfejsu.

Nazwy sesji i kody kierowców pochodzą z `f1tele` — UI ich nie duplikuje,
żeby nie rozjechały się z backendem.
"""

from __future__ import annotations

from f1tele.config import MAX_ROUNDS_FALLBACK, SEASON_ROUNDS
from f1tele.data_loader import DRIVER_COLORS, SESSION_LABELS, SESSION_TYPES

SESSIONS = SESSION_TYPES

# Zapasowa lista kierowców, zanim użytkownik pobierze skład z wybranej sesji.
KNOWN_DRIVERS = sorted(DRIVER_COLORS)

__all__ = ["SESSIONS", "SESSION_LABELS", "KNOWN_DRIVERS", "max_round_for_year"]


def max_round_for_year(year: int) -> int:
    """Liczba rund w sezonie; dla lat spoza słownika przyjmujemy wartość zapasową."""
    return SEASON_ROUNDS.get(int(year), MAX_ROUNDS_FALLBACK)
