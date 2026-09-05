"""
Centralna konfiguracja projektu F1 Telemetria.

To jedyne miejsce, w którym trzymamy progi analizy i wartości domyślne —
moduły `corner_analysis`, `sector_analysis` i `driver_style` czytają je stąd,
więc zmiana tutaj realnie wpływa na wyniki.
"""

from __future__ import annotations

from pathlib import Path

# ── Ścieżki ────────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent   # katalog projektu
CACHE_DIR = _BASE_DIR / "cache"

# ── Domyślne parametry analizy ─────────────────────────────────────────────
DEFAULT_YEAR       = 2024
DEFAULT_ROUND      = 5          # Numer rundy lub nazwa GP, np. "Monaco"
DEFAULT_SESSION    = "Q"        # Q, R, FP1, FP2, FP3, S, SS
DEFAULT_DRIVERS    = ["VER", "NOR", "LEC"]
DEFAULT_MINI_SECTS = 25         # Liczba mini-sektorów
MAX_DRIVERS        = 6          # Limit kierowców w jednym porównaniu

# Zakres lat dostępny w interfejsie
MIN_YEAR = 2018
MAX_YEAR = 2026

# Liczba rund w sezonie; lata spoza słownika używają MAX_ROUNDS_FALLBACK
SEASON_ROUNDS: dict[int, int] = {
    2018: 21, 2019: 21, 2020: 17, 2021: 22,
    2022: 22, 2023: 22, 2024: 24, 2025: 24, 2026: 24,
}
MAX_ROUNDS_FALLBACK = 24

# ── Detekcja zakrętów ──────────────────────────────────────────────────────
CORNER_MIN_SPEED_DROP   = 30.0   # [km/h] minimalny spadek prędkości
CORNER_MIN_DIST_BETWEEN = 200.0  # [m] minimalna odległość między zakrętami
CORNER_WINDOW_BEFORE    = 300.0  # [m] okno przed apeksem
CORNER_WINDOW_AFTER     = 200.0  # [m] okno po apeksie
CORNER_BRAKE_ON         = 5.0    # [%] próg "hamulec wciśnięty" przy detekcji hamowania
CORNER_THROTTLE_ON      = 80.0   # [%] próg "powrót do gazu" na wyjściu
CORNER_SMOOTH_WINDOW    = 21     # Okno filtra Savitzky-Golay
CORNER_PLOT_LIMIT       = 20     # Ile zakrętów pokazujemy na wykresach porównawczych

# ── Progi stylu jazdy ──────────────────────────────────────────────────────
THROTTLE_FULL_THRESHOLD  = 90.0   # [%] próg "pełnego gazu"
BRAKE_HEAVY_THRESHOLD    = 20.0   # [%] próg "intensywnego hamowania"
THROTTLE_COAST_THRESHOLD = 10.0   # [%] próg wybiegu
BRAKE_COAST_THRESHOLD    = 5.0    # [%] próg wybiegu (hamulec)
HIGH_RPM_THRESHOLD       = 0.90   # Ułamek maks. RPM = "wysokie obroty"
BRAKE_ON_THRESHOLD       = 5.0    # [%] próg "hamulec wciśnięty" w statystykach sektorów
THROTTLE_ACTIVE_THRESHOLD = 5.0   # [%] próg "gaz wciśnięty" przy liczeniu płynności

# ── Wykresy ────────────────────────────────────────────────────────────────
DEFAULT_PLOT_THEME  = "dark"      # dark | light
TRACK_MAP_POINTS    = 2000        # Liczba punktów resamplingu map toru
ANIMATION_FRAMES    = 80          # Liczba klatek animacji okrążenia
