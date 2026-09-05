"""
Ładowanie i cachowanie danych telemetrycznych FastF1.

Moduł nic nie rysuje i nie wie nic o interfejsie — zwraca surowe struktury
(`SessionData`, `DriverLapData`), z których korzysta warstwa wykresów i UI.
Postęp i błędy trafiają do standardowego `logging`, więc dashboard może je
przechwycić i pokazać użytkownikowi po swojemu.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field

import fastf1
import pandas as pd

from .config import CACHE_DIR

warnings.filterwarnings("ignore")

log = logging.getLogger(__name__)

CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

# Kanały telemetrii, których wymagamy od każdego okrążenia (stała kolejność kolumn).
# „Time” to czas od startu okrążenia w sekundach — pozwala odwzorować oficjalne
# granice sektorów na osi dystansu.
TELEMETRY_CHANNELS = ["Distance", "Time", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS"]

DRIVER_COLORS: dict[str, str] = {
    "VER": "#3671C6",
    "PER": "#3671C6",
    "HAM": "#27F4D2",
    "RUS": "#27F4D2",
    "LEC": "#E8002D",
    "SAI": "#E8002D",
    "NOR": "#FF8000",
    "PIA": "#FF8000",
    "ALO": "#358C75",
    "STR": "#358C75",
    "OCO": "#FF87BC",
    "GAS": "#FF87BC",
    "ALB": "#64C4FF",
    "SAR": "#64C4FF",
    "BOT": "#C92D4B",
    "ZHO": "#C92D4B",
    "HUL": "#B6BABD",
    "MAG": "#B6BABD",
    "TSU": "#356FAD",
    "LAW": "#356FAD",
    "RIC": "#356FAD",
    "DEV": "#356FAD",
    "BEA": "#229971",
    "ANT": "#229971",
}

FALLBACK_COLORS = [
    "#FF0000", "#0000FF", "#00FF00", "#FF8C00", "#9400D3",
    "#00CED1", "#FF1493", "#32CD32", "#FFD700", "#FF6347",
]

SESSION_LABELS: dict[str, str] = {
    "Q":   "Kwalifikacje",
    "R":   "Wyścig",
    "FP1": "Trening 1",
    "FP2": "Trening 2",
    "FP3": "Trening 3",
    "S":   "Sprint",
    "SS":  "Sprint Shootout",
}

SESSION_TYPES = list(SESSION_LABELS)


@dataclass
class DriverLapData:
    """Kompletne dane telemetryczne jednego okrążenia kierowcy."""
    driver: str
    lap_number: int
    lap_time: float          # sekundy
    lap_time_str: str
    compound: str
    sector1: float
    sector2: float
    sector3: float
    telemetry: pd.DataFrame  # Distance, Speed, Throttle, Brake, nGear, RPM, DRS (+ X, Y)
    color: str
    team: str = ""

    @property
    def has_gps(self) -> bool:
        """Czy okrążenie ma pozycję GPS (wymagana przez mapy toru i animację)."""
        return "X" in self.telemetry.columns and "Y" in self.telemetry.columns


@dataclass
class SessionData:
    """Dane całej sesji wyścigowej."""
    year: int
    round_number: int
    event_name: str
    session_type: str        # pełna nazwa sesji (np. Kwalifikacje, Wyścig)
    circuit_name: str
    country: str
    drivers: list[str] = field(default_factory=list)
    fastest_laps: dict[str, DriverLapData] = field(default_factory=dict)
    driver_colors: dict[str, str] = field(default_factory=dict)
    corners: pd.DataFrame = field(default_factory=pd.DataFrame)
    _session: object = field(default=None, repr=False)

    @property
    def label(self) -> str:
        """Czytelny opis sesji, np. „Monaco Grand Prix 2024 — Kwalifikacje”."""
        return f"{self.event_name} {self.year} — {self.session_type}"

    def color_for(self, driver: str, index: int = 0) -> str:
        """Kolor kierowcy: najpierw barwa zespołu z sesji, potem lista zapasowa."""
        return self.driver_colors.get(driver.upper()) or get_driver_color(driver, index)


def get_driver_color(driver: str, index: int = 0) -> str:
    """Zwraca kolor kierowcy lub kolor zapasowy."""
    return DRIVER_COLORS.get(driver.upper(), FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def format_lap_time(seconds: float) -> str:
    """Sekundy → zapis M:SS.mmm."""
    m, s = divmod(float(seconds), 60)
    return f"{int(m)}:{s:06.3f}"


def describe_drivers(ff1_session) -> list[dict]:
    """
    Opisuje kierowców sesji: {abbr, full_name, team}.

    FastF1 identyfikuje kierowców numerami startowymi ("1", "16"), a my w całej
    aplikacji posługujemy się kodami ("VER", "LEC") — tłumaczymy je tutaj, raz.
    """
    result: list[dict] = []
    for number in getattr(ff1_session, "drivers", []) or []:
        abbr, full_name, team, color = str(number), str(number), "", ""
        try:
            info = ff1_session.get_driver(number)
            abbr = str(info.get("Abbreviation") or number)
            full_name = str(info.get("FullName", abbr))
            team = str(info.get("TeamName", ""))
            color = _team_color(info.get("TeamColor"))
        except Exception:
            log.warning("Brak opisu kierowcy o numerze %s", number)
        result.append({"abbr": abbr, "full_name": full_name, "team": team, "color": color})
    return result


def _team_color(value) -> str:
    """
    Barwa zespołu z FastF1 („3671C6”) na format CSS.

    Bierzemy ją zamiast wpisanej na sztywno listy, dzięki czemu składy
    z nowych sezonów też dostają właściwe kolory.
    """
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return ""
    try:
        int(text, 16)
    except ValueError:
        return ""
    return f"#{text.upper()}"


def load_circuit_corners(ff1_session) -> pd.DataFrame:
    """
    Oficjalne zakręty toru: numer, litera (np. 7A) i dystans od linii startu.

    FastF1 zna prawdziwą numerację, więc nie musimy zgadywać jej z przebiegu
    prędkości. Pusty DataFrame oznacza, że dla tej sesji dane nie są dostępne.
    """
    try:
        corners = ff1_session.get_circuit_info().corners
    except Exception:
        log.warning("Brak danych o zakrętach toru", exc_info=True)
        return pd.DataFrame()

    if corners is None or corners.empty or "Distance" not in corners.columns:
        return pd.DataFrame()

    corners = corners.dropna(subset=["Distance"]).sort_values("Distance")
    return corners.reset_index(drop=True)


def load_session(
    year: int,
    round_number: int | str,
    session_type: str = "Q",
) -> SessionData:
    """
    Ładuje sesję F1 wraz z telemetrią i pogodą.

    Args:
        year: Rok sezonu (np. 2024)
        round_number: Numer rundy lub nazwa GP (np. 5 lub 'Monaco')
        session_type: Typ sesji: Q, R, FP1, FP2, FP3, S, SS
    """
    log.info("Ładowanie sesji %s GP#%s [%s]", year, round_number, session_type)

    ff1_session = fastf1.get_session(year, round_number, session_type)
    ff1_session.load(telemetry=True, weather=True, messages=False)

    event = ff1_session.event
    sd = SessionData(
        year=year,
        round_number=ff1_session.event.RoundNumber,
        event_name=str(event.get("EventName", f"GP #{round_number}")),
        session_type=SESSION_LABELS.get(session_type, session_type),
        circuit_name=str(event.get("Location", "Unknown")),
        country=str(event.get("Country", "Unknown")),
        _session=ff1_session,
    )

    described = describe_drivers(ff1_session)
    sd.drivers = [d["abbr"] for d in described]
    sd.driver_colors = {d["abbr"]: d["color"] for d in described if d["color"]}
    sd.corners = load_circuit_corners(ff1_session)

    log.info("Załadowano: %s | %s, %s | zakrętów: %d",
             sd.label, sd.circuit_name, sd.country, len(sd.corners))
    return sd


def get_fastest_lap(
    session_data: SessionData,
    driver: str,
    lap_number: int | None = None,
) -> DriverLapData | None:
    """
    Pobiera najszybsze (lub konkretne) okrążenie kierowcy.

    Args:
        session_data: Załadowana sesja
        driver: Kod kierowcy (np. 'VER', 'HAM')
        lap_number: Numer okrążenia (None = najszybsze)

    Returns:
        DriverLapData lub None, jeśli brak danych
    """
    ff1 = session_data._session
    try:
        drv_laps = ff1.laps.pick_drivers(driver.upper())
        if drv_laps.empty:
            log.warning("Brak okrążeń dla kierowcy %s", driver)
            return None

        if lap_number is not None:
            lap = drv_laps[drv_laps["LapNumber"] == lap_number]
            if lap.empty:
                log.warning("Nie znaleziono okrążenia #%s dla %s", lap_number, driver)
                return None
            lap = lap.iloc[0]
        else:
            lap = drv_laps.pick_fastest()

        telem = lap.get_telemetry().add_distance()

        # Czas od startu okrążenia w sekundach — na nim opieramy granice sektorów.
        if "Time" in telem.columns:
            telem["Time"] = pd.to_timedelta(telem["Time"]).dt.total_seconds()

        # Normalizacja kolumn — stała kolejność, brakujące kanały wypełniamy zerami.
        for col in TELEMETRY_CHANNELS:
            if col not in telem.columns:
                telem[col] = 0

        gps_cols = [c for c in ("X", "Y") if c in telem.columns]
        telem = telem[TELEMETRY_CHANNELS + gps_cols].copy()
        telem = telem.dropna(subset=["Distance", "Speed"])
        telem = telem.sort_values("Distance").reset_index(drop=True)

        lap_time_s = float(lap["LapTime"].total_seconds()) if pd.notna(lap["LapTime"]) else 0.0

        def _sector(name: str) -> float:
            value = lap.get(name)
            return float(value.total_seconds()) if pd.notna(value) else 0.0

        team = str(lap.get("Team", "")) if "Team" in lap.index else ""

        idx = (list(session_data.drivers).index(driver.upper())
               if driver.upper() in session_data.drivers else 0)
        color = session_data.color_for(driver, idx)

        return DriverLapData(
            driver=driver.upper(),
            lap_number=int(lap["LapNumber"]),
            lap_time=lap_time_s,
            lap_time_str=format_lap_time(lap_time_s),
            compound=str(lap.get("Compound", "UNKNOWN")),
            sector1=_sector("Sector1Time"),
            sector2=_sector("Sector2Time"),
            sector3=_sector("Sector3Time"),
            telemetry=telem,
            color=color,
            team=team,
        )
    except Exception:
        log.exception("Błąd pobierania danych dla %s", driver)
        return None


def load_drivers_data(
    session_data: SessionData,
    drivers: list[str],
    lap_numbers: dict[str, int] | None = None,
    on_progress=None,
) -> dict[str, DriverLapData]:
    """
    Ładuje dane dla listy kierowców.

    Args:
        session_data: Załadowana sesja
        drivers: Lista kodów kierowców
        lap_numbers: Opcjonalny słownik {driver: lap_number}
        on_progress: Opcjonalne `callback(driver, i, total)` do raportowania postępu

    Returns:
        Słownik {driver: DriverLapData} — bez kierowców, dla których brak danych
    """
    results: dict[str, DriverLapData] = {}
    total = len(drivers)

    for i, drv in enumerate(drivers, start=1):
        if on_progress is not None:
            on_progress(drv, i, total)
        data = get_fastest_lap(session_data, drv, (lap_numbers or {}).get(drv))
        if data is not None:
            results[drv] = data
            session_data.fastest_laps[drv] = data

    return results


def get_available_sessions(year: int) -> pd.DataFrame:
    """Zwraca harmonogram sezonu: runda, nazwa GP, miasto, kraj, data."""
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule[["RoundNumber", "EventName", "Location", "Country", "EventDate"]]
    except Exception:
        log.exception("Błąd pobierania harmonogramu %s", year)
        return pd.DataFrame()


def get_weather_data(session_data: SessionData) -> pd.DataFrame:
    """
    Dane pogodowe sesji.

    Kolumny: Time, AirTemp, TrackTemp, Humidity, Pressure, WindSpeed,
    WindDirection, Rainfall. Pusty DataFrame, gdy sesja ich nie ma.
    """
    try:
        ff1 = session_data._session
        if ff1 is None:
            return pd.DataFrame()
        wdf = ff1.weather_data
        if wdf is None or wdf.empty:
            return pd.DataFrame()
        return wdf.reset_index(drop=True)
    except Exception:
        log.exception("Błąd pobierania danych pogodowych")
        return pd.DataFrame()


def get_session_drivers_list(
    year: int,
    round_number: int | str,
    session_type: str = "Q",
) -> list[dict]:
    """
    Szybko pobiera listę kierowców z sesji, bez ładowania telemetrii.

    Returns:
        Lista słowników {abbr, full_name, team}
    """
    ff1_session = fastf1.get_session(year, round_number, session_type)
    ff1_session.load(telemetry=False, weather=False, messages=False)
    return describe_drivers(ff1_session)


def get_position_data(
    session_data: SessionData,
    drivers: list[str],
) -> pd.DataFrame:
    """
    Pozycja okrążenie po okrążeniu dla każdego kierowcy (głównie dla wyścigu).

    Returns:
        DataFrame: Driver, LapNumber, Position, Color
    """
    ff1 = session_data._session
    rows: list[dict] = []

    for drv in drivers:
        try:
            drv_laps = ff1.laps.pick_drivers(drv.upper())
            if drv_laps.empty:
                continue
            color = session_data.color_for(drv)
            for _, lap in drv_laps.iterrows():
                pos = lap.get("Position")
                if pos is None or pd.isna(pos):
                    continue
                rows.append({
                    "Driver":    drv.upper(),
                    "LapNumber": int(lap["LapNumber"]),
                    "Position":  int(pos),
                    "Color":     color,
                })
        except Exception:
            log.exception("Pozycje: błąd dla %s", drv)

    return pd.DataFrame(rows)


def get_race_pace_data(
    session_data: SessionData,
    drivers: list[str],
) -> pd.DataFrame:
    """
    Wszystkie miarodajne okrążenia kierowców do analizy tempa wyścigu.

    Odfiltrowuje pit-lapy i outliery (`pick_quicklaps`).

    Returns:
        DataFrame: Driver, LapNumber, LapTime_s, Compound, Stint, Color
    """
    ff1 = session_data._session
    rows: list[dict] = []

    for drv in drivers:
        try:
            drv_laps = ff1.laps.pick_drivers(drv.upper()).pick_quicklaps()
            if drv_laps.empty:
                continue
            color = session_data.color_for(drv)
            for _, lap in drv_laps.iterrows():
                if not pd.notna(lap["LapTime"]):
                    continue
                try:
                    stint = int(lap["Stint"]) if pd.notna(lap.get("Stint")) else 0
                except (TypeError, ValueError):
                    stint = 0
                rows.append({
                    "Driver":    drv.upper(),
                    "LapNumber": int(lap["LapNumber"]),
                    "LapTime_s": float(lap["LapTime"].total_seconds()),
                    "Compound":  str(lap.get("Compound", "UNKNOWN")),
                    "Stint":     stint,
                    "Color":     color,
                })
        except Exception:
            log.exception("Race pace: błąd dla %s", drv)

    return pd.DataFrame(rows)
