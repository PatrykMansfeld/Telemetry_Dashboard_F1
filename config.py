"""
Konfiguracja projektu F1 Telemetria.
Zmień te ustawienia aby dopasować projekt do swoich potrzeb.
"""

from pathlib import Path

# ── Ścieżki ────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CACHE_DIR  = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
PLOTS_DIR  = OUTPUT_DIR / "plots"
REPORT_DIR = OUTPUT_DIR / "reports"

# ── Domyślne parametry analizy ─────────────────────────────────────────────
DEFAULT_YEAR       = 2024
DEFAULT_ROUND      = 5          # Numer rundy lub nazwa np. "Monaco"
DEFAULT_SESSION    = "Q"        # Q, R, FP1, FP2, FP3, S, SS
DEFAULT_DRIVERS    = ["VER", "NOR", "LEC"]
DEFAULT_MINI_SECTS = 25         # Liczba mini-sektorów

# ── Jakość wykresów ────────────────────────────────────────────────────────
PLOT_DPI        = 150
PLOT_FACECOLOR  = "#0F0F0F"

# ── Detekcja zakrętów ──────────────────────────────────────────────────────
CORNER_MIN_SPEED_DROP      = 30.0   # [km/h] minimalny spadek prędkości
CORNER_MIN_DIST_BETWEEN    = 200.0  # [m] minimalna odległość między zakrętami
CORNER_WINDOW_BEFORE       = 300.0  # [m] okno przed apeksem
CORNER_WINDOW_AFTER        = 200.0  # [m] okno po apeksie

# ── Progi stylu jazdy ──────────────────────────────────────────────────────
THROTTLE_FULL_THRESHOLD    = 90.0   # [%] próg "pełnego gazu"
BRAKE_HEAVY_THRESHOLD      = 20.0   # [%] próg "intensywnego hamowania"
THROTTLE_COAST_THRESHOLD   = 10.0   # [%] próg wybiegu
BRAKE_COAST_THRESHOLD      = 5.0    # [%] próg wybiegu (hamulec)
HIGH_RPM_THRESHOLD         = 0.90   # Ułamek maks. RPM = "wysokie obroty"
