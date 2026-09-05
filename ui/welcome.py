"""Ekran powitalny — widoczny, dopóki nie ma wyników analizy."""

from __future__ import annotations

import streamlit as st

from f1tele.config import DEFAULT_DRIVERS, DEFAULT_ROUND, DEFAULT_YEAR

# (tytuł, opis, kolor akcentu) — kolory te same, co w listwie kierowców
FEATURES = [
    ("Telemetria",    "Prędkość, gaz, hamulec, biegi, RPM i delta czasu",      "#e10600"),
    ("Zakręty",       "Punkt hamowania, prędkość apeksu, powrót do gazu",      "#ff8000"),
    ("Sektory",       "Mini-sektory, dominacja, mapa ciepła S1/S2/S3",         "#c8ff3d"),
    ("Styl jazdy",    "Radar 10 metryk i porównanie słupkowe",                 "#00d1ff"),
    ("Mapa toru",     "Dominacja, prędkość, biegi, DRS, animacja okrążenia",   "#3bd971"),
    ("Race pace",     "Tempo wyścigu, degradacja opon, stinty, pozycje",       "#f9c74f"),
    ("Podsumowanie",  "Czasy, rozbicie na sektory i strata do lidera",         "#a78bfa"),
    ("Porównanie",    "Dwie sesje obok siebie — inne GP albo inny sezon",      "#fb7185"),
]


def render_welcome() -> None:
    st.markdown(f"""
    <div class="welcome">
        <div class="welcome-title">Zacznij od wyboru sesji</div>
        <div class="welcome-sub">
            W panelu po lewej ustaw rok, rundę i typ sesji, wybierz kierowców,
            a następnie kliknij <span class="accent">Uruchom analizę</span>.<br>
            Domyślnie: <b>{DEFAULT_YEAR}</b>, runda <b>{DEFAULT_ROUND}</b>,
            kwalifikacje, {", ".join(DEFAULT_DRIVERS)}.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Co policzy analiza</div>',
                unsafe_allow_html=True)

    columns = st.columns(4)
    for i, (title, description, accent) in enumerate(FEATURES):
        with columns[i % 4]:
            st.markdown(f"""
            <div class="feature-card" style="--accent-c:{accent}">
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{description}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="note-card" style="margin-top:1rem">
        Dane pochodzą z <b>FastF1</b> i są zapisywane w lokalnym cache — pierwsza
        analiza danej sesji trwa dłużej, każda kolejna rusza od razu.
        Wykresy są interaktywne: przybliżanie, przesuwanie i podgląd wartości
        pod kursorem.
    </div>
    """, unsafe_allow_html=True)
