"""
Generator raportu tekstowego HTML podsumowującego analizę.
Tworzy plik HTML z tabelami, linkami do wykresów i metrykami.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Optional

from rich.console import Console

from .data_loader import DriverLapData, SessionData
from .driver_style import StyleFingerprint

console = Console()
REPORT_DIR = Path(__file__).parent.parent / "output" / "reports"
PLOT_DIR   = Path(__file__).parent.parent / "output" / "plots"


def generate_html_report(
    session_data: SessionData,
    drivers_data: dict[str, DriverLapData],
    fingerprints: list[StyleFingerprint],
    plot_paths: list[Optional[Path]],
) -> Path:
    """
    Generuje raport HTML z wynikami analizy.

    Args:
        session_data: Dane sesji
        drivers_data: Dane kierowców
        fingerprints: Metryki stylu jazdy
        plot_paths: Lista ścieżek do wykresów

    Returns:
        Ścieżka do pliku HTML
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    drivers_str = "_".join(sorted(drivers_data.keys()))
    filename = (
        f"{session_data.year}_{session_data.event_name.replace(' ', '_')}_"
        f"{session_data.session_type}_{drivers_str}_report.html"
    )
    out_path = REPORT_DIR / filename

    # Tabela okrążeń
    sorted_drivers = sorted(drivers_data.values(), key=lambda d: d.lap_time)

    lap_rows = ""
    for i, d in enumerate(sorted_drivers):
        delta = d.lap_time - sorted_drivers[0].lap_time
        delta_str = f"+{delta:.3f}s" if delta > 0 else "POLE"
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"P{i+1}"
        lap_rows += f"""
        <tr>
            <td>{medal}</td>
            <td><span style="color:{d.color};font-weight:bold">{d.driver}</span></td>
            <td>{d.lap_time_str}</td>
            <td>{delta_str}</td>
            <td>{d.sector1:.3f}s</td>
            <td>{d.sector2:.3f}s</td>
            <td>{d.sector3:.3f}s</td>
            <td>{d.lap_number}</td>
            <td>{d.compound}</td>
        </tr>"""

    # Tabela metryk stylu
    metric_rows = ""
    from .driver_style import METRIC_LABELS, METRIC_FIELDS
    for label, field_name in zip(METRIC_LABELS, METRIC_FIELDS):
        label_clean = label.replace("\n", " ")
        vals = [getattr(fp, field_name) for fp in fingerprints]
        best_val = max(vals)
        row = f"<tr><td><strong>{label_clean}</strong></td>"
        for fp, val in zip(fingerprints, vals):
            style = "background:#1a4a1a;color:#88ff88;font-weight:bold" if val == best_val else ""
            row += f'<td style="{style}">{val:.1f}</td>'
        row += "</tr>"
        metric_rows += row

    plot_files = [p for p in plot_paths if isinstance(p, Path)]

    # Wykresy
    plots_html = ""
    for p in plot_files:
        rel = p.relative_to(REPORT_DIR.parent)
        plots_html += f"""
        <div class="plot-card">
            <h3>{p.stem.replace('_', ' ')}</h3>
            <a href="../{rel.as_posix()}" target="_blank">
                <img src="../{rel.as_posix()}" alt="{p.stem}" loading="lazy">
            </a>
        </div>"""

    # Driver cards
    driver_cards = ""
    for fp in fingerprints:
        d = drivers_data.get(fp.driver)
        if not d:
            continue
        driver_cards += f"""
        <div class="driver-card" style="border-left: 4px solid {fp.color}">
            <h3 style="color:{fp.color}">{fp.driver}</h3>
            <p>Czas: <strong>{d.lap_time_str}</strong></p>
            <p>Okrążenie: #{d.lap_number} | Opona: {d.compound}</p>
            <p>S1: {d.sector1:.3f}s | S2: {d.sector2:.3f}s | S3: {d.sector3:.3f}s</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Telemetria — {session_data.event_name} {session_data.year}</title>
    <style>
        :root {{
            --bg: #0f0f0f;
            --bg2: #1a1a1a;
            --bg3: #222222;
            --border: #333333;
            --text: #cccccc;
            --accent: #e10600;
            --green: #27f4d2;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: 'Courier New', monospace;
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #1a0000, #0f0f0f);
            border-bottom: 2px solid var(--accent);
            padding: 24px 32px;
        }}
        header h1 {{ font-size: 1.8rem; color: #ffffff; }}
        header h1 span {{ color: var(--accent); }}
        header .meta {{
            color: #888888;
            font-size: 0.85rem;
            margin-top: 6px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 32px; }}
        h2 {{
            font-size: 1.2rem;
            color: #ffffff;
            margin: 32px 0 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid var(--border);
        }}
        .driver-cards {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .driver-card {{
            background: var(--bg2);
            border-radius: 8px;
            padding: 16px 20px;
            min-width: 200px;
        }}
        .driver-card h3 {{ font-size: 1.1rem; margin-bottom: 8px; }}
        .driver-card p {{ font-size: 0.82rem; color: #aaaaaa; margin: 2px 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 0.85rem;
        }}
        th {{
            background: var(--bg3);
            color: #ffffff;
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 8px 14px;
            border-bottom: 1px solid var(--border);
            color: var(--text);
        }}
        tr:hover td {{ background: var(--bg3); }}
        .plots-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}
        .plot-card {{
            background: var(--bg2);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid var(--border);
        }}
        .plot-card h3 {{
            font-size: 0.85rem;
            color: #888888;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .plot-card img {{
            width: 100%;
            border-radius: 4px;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .plot-card img:hover {{ opacity: 0.9; }}
        footer {{
            text-align: center;
            padding: 24px;
            color: #555555;
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
        }}
        .badge {{
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-left: 8px;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🏎 F1 Telemetria — <span>{session_data.event_name}</span> {session_data.year}</h1>
        <div class="meta">
            Sesja: {session_data.session_type} &nbsp;|&nbsp;
            Tor: {session_data.circuit_name}, {session_data.country} &nbsp;|&nbsp;
            Wygenerowano: {now}
        </div>
    </header>

    <div class="container">

        <h2>Kierowcy <span class="badge">{len(drivers_data)}</span></h2>
        <div class="driver-cards">{driver_cards}</div>

        <h2>Wyniki okrążeń</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th><th>Kierowca</th><th>Czas</th><th>Delta</th>
                    <th>S1</th><th>S2</th><th>S3</th><th>Okrążenie</th><th>Opona</th>
                </tr>
            </thead>
            <tbody>{lap_rows}</tbody>
        </table>

        <h2>Metryki stylu jazdy</h2>
        <table>
            <thead>
                <tr>
                    <th>Metryka</th>
                    {"".join(f"<th>{fp.driver}</th>" for fp in fingerprints)}
                </tr>
            </thead>
            <tbody>{metric_rows}</tbody>
        </table>

        <h2>Wykresy telemetryczne <span class="badge">{len(plot_files)}</span></h2>
        <div class="plots-grid">{plots_html}</div>

    </div>

    <footer>
        Wygenerowano przez F1 Telemetria &nbsp;·&nbsp; FastF1 &nbsp;·&nbsp; {now}
    </footer>
</body>
</html>"""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    console.print(f"[bold green]✓ Raport HTML:[/bold green] {out_path}")
    return out_path
