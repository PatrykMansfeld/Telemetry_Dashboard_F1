"""
F1 Telemetria — analiza i porównanie stylu jazdy kierowców Formuły 1.

Warstwy pakietu:
    config           — progi analizy i wartości domyślne
    data_loader      — pobieranie sesji i telemetrii z FastF1
    corner_analysis  — detekcja zakrętów i pomiary corner-by-corner
    sector_analysis  — sektory i mini-sektory
    driver_style     — metryki stylu jazdy
    plots            — wykresy Plotly (z obsługą motywu jasnego i ciemnego)
    pipeline         — orkiestracja: parametry sesji -> gotowe wykresy

Powered by FastF1.
"""

__version__ = "2.0.0"
