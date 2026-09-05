"""
Drobne komponenty wspólne dla zakładek.

Dwa najważniejsze:

* `chart()` — każdy wykres przechodzi przez niego, więc to jedyne miejsce,
  w którym figura dostaje aktualny motyw (także po przełączeniu go już po
  wygenerowaniu analizy).
* `table()` — tabele rysujemy własnym HTML-em zamiast `st.dataframe`.
  Wbudowana tabela Streamlita rysuje się na canvasie i bierze kolory
  z `config.toml`, więc nie da się jej dopasować do motywu wybranego
  w aplikacji; własna tabela trzyma się tych samych tokenów co reszta UI.
"""

from __future__ import annotations

import html
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from f1tele.plots import restyle

from . import state

# Komórka „liczbowa”: czas okrążenia, delta, procent, liczba — takie wyrównujemy
# do prawej, żeby cyfry układały się w kolumnę.
_NUMERIC = re.compile(r"^[+\-−]?[\d\s.,:]+(\s*[%sm])?$|^—$")

# Liczba miejsc po przecinku dla wartości zmiennoprzecinkowych bez własnego formatu.
_DECIMALS = 3


def _format(value) -> str:
    """Zamienia wartość na tekst gotowy do pokazania (bez ogonów po przecinku)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        return f"{value:.{_DECIMALS}f}".rstrip("0").rstrip(".") or "0"
    return str(value)


def chart(fig: go.Figure | None, *, key: str | None = None) -> bool:
    """Rysuje wykres w aktualnym motywie. Zwraca False, gdy nie było czego rysować."""
    if fig is None:
        return False
    st.plotly_chart(restyle(fig, state.current_theme()), width="stretch", key=key)
    return True


def table(df: pd.DataFrame, *, max_height: int | None = None,
          download: str | None = None) -> None:
    """
    Renderuje DataFrame jako tabelę w motywie aplikacji.

    Kolumny zawierające same wartości liczbowe wyrównujemy do prawej.
    `max_height` [px] włącza przewijanie z przyklejonym nagłówkiem.
    `download` (nazwa pliku bez rozszerzenia) dokłada przycisk pobrania CSV.
    """
    if df is None or df.empty:
        return

    cells = [[_format(value) for value in row]
             for row in df.itertuples(index=False, name=None)]
    align_right = [
        all(_NUMERIC.match(row[i].strip()) for row in cells if row[i].strip())
        for i in range(len(df.columns))
    ]

    head = "".join(
        f'<th class="{"num" if right else ""}">{html.escape(str(column))}</th>'
        for column, right in zip(df.columns, align_right)
    )
    rows = "".join(
        "<tr>" + "".join(
            f'<td class="{"num" if right else ""}">{html.escape(value)}</td>'
            for value, right in zip(row, align_right)
        ) + "</tr>"
        for row in cells
    )

    style = f' style="max-height:{max_height}px"' if max_height else ""
    st.markdown(
        f'<div class="table-wrap"{style}><table class="data-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True,
    )

    if download:
        # Eksportujemy surowe dane, nie sformatowany tekst — w arkuszu chcemy
        # liczby, a nie napisy z gwiazdkami i myślnikami.
        st.download_button(
            "Pobierz CSV", data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{download}.csv", mime="text/csv",
            key=f"csv_{download}", help="Dane z tej tabeli w formacie CSV",
        )


def subheader(text: str) -> None:
    """Nagłówek sekcji wewnątrz zakładki."""
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def note(html_content: str) -> None:
    """Kafelek z podpowiedzią."""
    st.markdown(f'<div class="note-card">{html_content}</div>', unsafe_allow_html=True)


def caption(text: str) -> None:
    """Objaśnienie pod tabelą lub wykresem."""
    st.markdown(f'<div class="hint">{text}</div>', unsafe_allow_html=True)


def empty_module(name: str) -> None:
    """Jednolity komunikat dla wyłączonego modułu lub braku danych."""
    st.info(f"Moduł **{name}** nie był uruchomiony albo sesja nie ma potrzebnych danych.")


def dim_color(hex_col: str) -> str:
    """Rozjaśnia kolor kierowcy — sesja B ma być odróżnialna od sesji A."""
    h = hex_col.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return hex_col
    mix = lambda c: min(255, int(c * 0.55 + 200 * 0.45))  # noqa: E731
    return f"#{mix(r):02x}{mix(g):02x}{mix(b):02x}"
