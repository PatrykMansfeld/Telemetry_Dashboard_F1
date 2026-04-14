"""
F1 Telemetria — główny punkt wejścia CLI.

Użycie:
    python main.py compare --year 2024 --round 5 --session Q --drivers VER,HAM,NOR
    python main.py compare --year 2023 --round Monaco --session Q --drivers LEC,VER
    python main.py schedule          # Lista wyścigów sezonu
    python main.py schedule --year 2023
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

# Importy modułów projektu
from f1tele.data_loader import (
    load_session, load_drivers_data,
    print_lap_summary, get_available_sessions,
)
from f1tele.lap_analysis import plot_telemetry_comparison, plot_speed_trace_detail
from f1tele.corner_analysis import (
    run_corner_analysis, print_corner_comparison_table, plot_corner_comparison,
)
from f1tele.sector_analysis import (
    compute_mini_sectors, compute_sector_stats,
    print_sector_stats, plot_mini_sector_dominance, plot_sector_heatmap,
)
from f1tele.driver_style import (
    compute_style_fingerprint, normalize_fingerprints,
    plot_radar_chart, plot_style_bar_comparison, print_style_table,
)
from f1tele.track_map import (
    plot_driver_dominance_map, plot_speed_heatmap_track, plot_gear_map,
)
from f1tele.report import generate_html_report

console = Console()


BANNER = """
[bold red]╔═══════════════════════════════════════════════════════════╗[/bold red]
[bold red]║[/bold red]  [bold white]🏎  F1 TELEMETRIA[/bold white]  [dim]— porównanie stylu jazdy kierowców[/dim]  [bold red]║[/bold red]
[bold red]╚═══════════════════════════════════════════════════════════╝[/bold red]
[dim]FastF1 | Python | Matplotlib | Scipy[/dim]
"""


def print_banner() -> None:
    console.print(BANNER)


@click.group()
def cli() -> None:
    """F1 Telemetria — narzędzie do analizy i porównania telemetrii kierowców F1."""
    print_banner()


@cli.command("compare")
@click.option("--year",    "-y", required=True, type=int,        help="Rok sezonu (np. 2024)")
@click.option("--round",   "-r", required=True,                  help="Numer rundy lub nazwa GP (np. 5 lub Monaco)")
@click.option("--session", "-s", default="Q", show_default=True, help="Typ sesji: Q, R, FP1, FP2, FP3, S, SS")
@click.option("--drivers", "-d", required=True,                  help="Kody kierowców oddzielone przecinkami (np. VER,HAM,NOR)")
@click.option("--laps",    "-l", default=None,                   help="Numery okrążeń (opcjonalne, format: VER=1,HAM=3)")
@click.option("--no-save", is_flag=True, default=False,          help="Nie zapisuj wykresów do pliku")
@click.option("--show",    is_flag=True, default=False,          help="Wyświetl wykresy interaktywnie")
@click.option("--no-report", is_flag=True, default=False,        help="Nie generuj raportu HTML")
@click.option("--mini-sectors", "-m", default=25, show_default=True, type=int,
              help="Liczba mini-sektorów do analizy dominacji")
@click.option("--modules", default="all", show_default=True,
              help="Moduły do uruchomienia: all / telemetry,corners,sectors,style,track,report")
def compare(
    year: int,
    round: str,
    session: str,
    drivers: str,
    laps: Optional[str],
    no_save: bool,
    show: bool,
    no_report: bool,
    mini_sectors: int,
    modules: str,
) -> None:
    """
    Porównaj telemetrię wybranych kierowców F1.

    Przykłady:\n
      python main.py compare -y 2024 -r 5 -s Q -d VER,HAM,NOR\n
      python main.py compare -y 2023 -r Monaco -s Q -d LEC,VER\n
      python main.py compare -y 2024 -r 1 -s R -d VER,NOR --modules telemetry,style\n
    """
    save = not no_save
    report = not no_report

    if report and not save:
        console.print(
            "[yellow]⚠ Raport wymaga zapisanych wykresów. Pomijam raport przy --no-save.[/yellow]"
        )
        report = False

    # Parsowanie modułów
    if modules == "all":
        run_mods = {"telemetry", "corners", "sectors", "style", "track", "report"}
    else:
        run_mods = set(m.strip().lower() for m in modules.split(","))

    # Parsowanie kierowców
    driver_list = [d.strip().upper() for d in drivers.split(",") if d.strip()]
    if not driver_list:
        console.print("[red]Błąd: Podaj co najmniej jednego kierowcę[/red]")
        sys.exit(1)

    # Parsowanie numerów okrążeń
    lap_numbers: dict[str, int] = {}
    if laps:
        for part in laps.split(","):
            if "=" in part:
                drv, ln = part.split("=", 1)
                try:
                    lap_numbers[drv.strip().upper()] = int(ln.strip())
                except ValueError:
                    pass

    # Parsowanie numeru rundy (cyfra lub nazwa)
    try:
        round_val: int | str = int(round)
    except ValueError:
        round_val = round

    console.print(f"\n[bold cyan]Analiza:[/bold cyan] {year} GP#{round_val} [{session.upper()}]")
    console.print(f"[bold cyan]Kierowcy:[/bold cyan] {', '.join(driver_list)}\n")

    # ── ŁADOWANIE DANYCH ────────────────────────────────────────────────────
    session_data = load_session(year, round_val, session.upper())
    drivers_data = load_drivers_data(session_data, driver_list, lap_numbers or None)

    if not drivers_data:
        console.print("[red]Błąd: Nie udało się pobrać danych dla żadnego kierowcy[/red]")
        sys.exit(1)

    console.print()
    print_lap_summary(drivers_data)
    console.print()

    plot_paths: list[Path] = []

    def _record_plot(path: object | None) -> None:
        if isinstance(path, Path):
            plot_paths.append(path)

    # ── TELEMETRIA ──────────────────────────────────────────────────────────
    if "telemetry" in run_mods:
        console.rule("[bold]Analiza telemetrii[/bold]")
        p = plot_telemetry_comparison(drivers_data, session_data, save=save, show=show)
        _record_plot(p)

    # ── ZAKRĘTY ─────────────────────────────────────────────────────────────
    corner_analysis = None
    if "corners" in run_mods:
        console.rule("[bold]Analiza zakrętów[/bold]")
        corner_analysis = run_corner_analysis(drivers_data)
        print_corner_comparison_table(corner_analysis)
        p = plot_corner_comparison(
            drivers_data, corner_analysis, session_data, save=save, show=show
        )
        _record_plot(p)

    # ── SEKTORY ─────────────────────────────────────────────────────────────
    if "sectors" in run_mods:
        console.rule("[bold]Analiza sektorów[/bold]")
        mini_sector_data = compute_mini_sectors(drivers_data, mini_sectors)
        stats_df = compute_sector_stats(drivers_data)
        print_sector_stats(stats_df)
        p1 = plot_mini_sector_dominance(
            drivers_data, mini_sector_data, session_data, save=save, show=show
        )
        p2 = plot_sector_heatmap(stats_df, drivers_data, session_data, save=save, show=show)
        _record_plot(p1)
        _record_plot(p2)

    # ── STYL JAZDY ──────────────────────────────────────────────────────────
    fingerprints = []
    if "style" in run_mods:
        console.rule("[bold]Odcisk palca stylu jazdy[/bold]")
        raw_fps = [
            compute_style_fingerprint(data, corner_analysis)
            for data in drivers_data.values()
        ]
        fingerprints = normalize_fingerprints(raw_fps)
        print_style_table(fingerprints)
        p1 = plot_radar_chart(fingerprints, session_data, save=save, show=show)
        p2 = plot_style_bar_comparison(fingerprints, session_data, save=save, show=show)
        _record_plot(p1)
        _record_plot(p2)

    # ── MAPA TORU ───────────────────────────────────────────────────────────
    if "track" in run_mods:
        console.rule("[bold]Mapy toru[/bold]")
        p1 = plot_driver_dominance_map(drivers_data, session_data, save=save, show=show)
        _record_plot(p1)
        for d in drivers_data.values():
            p2 = plot_speed_heatmap_track(d, session_data, save=save, show=show)
            p3 = plot_gear_map(d, session_data, save=save, show=show)
            _record_plot(p2)
            _record_plot(p3)

    # ── RAPORT HTML ─────────────────────────────────────────────────────────
    if report and save and "report" in run_mods and fingerprints:
        console.rule("[bold]Generowanie raportu[/bold]")
        report_path = generate_html_report(
            session_data, drivers_data, fingerprints,
            plot_paths,
        )
        console.print(
            Panel(
                f"[bold green]Raport gotowy![/bold green]\n"
                f"[link=file://{report_path.resolve()}]{report_path}[/link]",
                title="HTML Report",
                border_style="green",
            )
        )

    # Podsumowanie
    saved = list(plot_paths)
    console.print()
    console.print(
        Panel(
            f"[bold]Zapisano {len(saved)} wykresów[/bold]\n"
            + "\n".join(f"  [dim]→[/dim] {p.name}" for p in saved),
            title="[green]Analiza zakończona[/green]",
            border_style="green",
        )
    )


@cli.command("schedule")
@click.option("--year", "-y", default=2024, show_default=True, type=int,
              help="Rok sezonu")
def schedule(year: int) -> None:
    """Wyświetl harmonogram wyścigów sezonu."""
    console.print(f"\n[bold cyan]Harmonogram sezonu {year}[/bold cyan]\n")
    df = get_available_sessions(year)

    if df.empty:
        console.print("[red]Brak danych harmonogramu[/red]")
        return

    table = Table(
        title=f"[bold]Sezon F1 {year}[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Runda", justify="center", width=7)
    table.add_column("Nazwa GP", width=30)
    table.add_column("Tor / Miasto", width=20)
    table.add_column("Kraj", width=15)
    table.add_column("Data", width=12)

    for _, row in df.iterrows():
        table.add_row(
            str(int(row["RoundNumber"])) if row["RoundNumber"] else "—",
            str(row["EventName"]),
            str(row.get("Location", "—")),
            str(row.get("Country", "—")),
            str(row.get("EventDate", "—"))[:10],
        )

    console.print(table)


@cli.command("drivers")
@click.option("--year",    "-y", required=True, type=int, help="Rok sezonu")
@click.option("--round",   "-r", required=True,           help="Numer rundy lub nazwa GP")
@click.option("--session", "-s", default="Q", show_default=True, help="Typ sesji")
def drivers_list(year: int, round: str, session: str) -> None:
    """Wyświetl listę kierowców w danej sesji."""
    try:
        round_val: int | str = int(round)
    except ValueError:
        round_val = round

    sd = load_session(year, round_val, session.upper(), verbose=False)

    table = Table(
        title=f"[bold]Kierowcy — {sd.event_name} {sd.year} [{sd.session_type}][/bold]",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Kod kierowcy", width=12)

    for drv in sd.drivers:
        table.add_row(str(drv))

    console.print(table)


if __name__ == "__main__":
    cli()
