from __future__ import annotations

import streamlit as st


def render_welcome() -> None:
    st.markdown("""
    <div class="welcome fade-in">
        <div class="welcome-title">Witaj w F1 Telemetria</div>
        <div class="welcome-sub">
            Wybierz sesję i kierowców w panelu powyżej, następnie kliknij
            <span class="accent">URUCHOM ANALIZĘ</span>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("📈", "Telemetria",      "Prędkość · Delta · Gaz · Hamulec · Biegi · RPM",        "#e10600"),
        ("🔄", "Zakręty",         "Punkt hamowania · Prędkość apeksu · Wyjście z gazu",      "#ff7a00"),
        ("🏁", "Sektory",         "Mini-sektory · Dominacja · Mapa ciepła S1/S2/S3",         "#c8ff3d"),
        ("🎯", "Styl jazdy",      "Radar 10 metryk · Porównanie słupkowe",                   "#00d1ff"),
        ("🗺️", "Mapa toru",      "Dominacja · Gradient prędkości · Biegi · Animacja",        "#3bd971"),
        ("🏎", "Race Pace",       "Czas okrążenia · Trend · Składy opon · Sfinty",           "#f9c74f"),
        ("📊", "Podsumowanie",    "Tabela wyników · Profile kierowców · Czasy sektorów",      "#a78bfa"),
        ("🔀", "Cross-session",   "Porównanie sesji A vs B · Telemetria między GP / latami",  "#fb7185"),
    ]
    cols = st.columns(4)
    for i, (icon, title, desc, accent) in enumerate(features):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="feature-card" style="--accent:{accent}">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="note-card fade-in delay-6">
        💡 Wszystkie wykresy są interaktywne — zoom, hover, pan.
        Dane pobierane przez FastF1 i cache'owane lokalnie.<br>
        Kliknij <b>🔄 Załaduj kierowców z sesji</b>, aby pobrać aktualną listę kierowców dla wybranego GP.
    </div>
    """, unsafe_allow_html=True)
