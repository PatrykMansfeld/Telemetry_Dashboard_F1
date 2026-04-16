# 🏎 F1 Telemetria — Analiza danych kierowców F1

Interaktywny dashboard do analizy i wizualizacji danych telemetrycznych Formuły 1.
Korzysta z biblioteki **FastF1** — daje dostęp do prędkości, gazu, hamulca, biegów i pozycji GPS zakręt po zakręcie.

---

## Funkcje

| Moduł | Opis |
| --- | --- |
| **Telemetria** | Prędkość, gaz, hamulec, biegi, RPM — interaktywny wykres z deltą czasu |
| **Zakręty** | Wykrycie zakrętów, punkt hamowania, prędkość apeksu, wyjście z gazu |
| **Mini-sektory** | Dominacja w N mini-sektorach, skumulowana delta, mapa ciepła |
| **Sektory** | Statystyki S1/S2/S3: czas, prędkości, % gazu, % hamowania |
| **Styl jazdy** | Radar chart + wykres słupkowy 10 metryk charakteryzujących styl |
| **Mapa toru** | Dominacja, gradient prędkości, biegi (wymaga danych GPS) |
| **Animacja toru** | Animowana pozycja kierowców na torze klatka po klatce |
| **Race Pace** | Czasy okrążeń wyścigu, trend, skład opon, pit-stopy |
| **Cross-session** | Porównanie telemetrii i stylu jazdy między dwoma sesjami / latami |

---

## Instalacja

```bash
# Utwórz środowisko wirtualne
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt
```

---

## Uruchomienie

```bash
streamlit run app.py
```

Aplikacja otworzy się pod adresem `http://localhost:8501`.

---

## Zakładki dashboardu

| Zakładka | Opis |
| --- | --- |
| **Podsumowanie** | Tabela wyników, karty kierowców z sektorami i składem opon |
| **Telemetria** | Interaktywny 6-panelowy wykres (prędkość, delta, gaz, hamulec, biegi, RPM) |
| **Zakręty** | Wykresy porównawcze + tabela danych zakrętowych |
| **Sektory** | Mini-sektory, mapa dominacji, mapa ciepła S1/S2/S3 |
| **Styl jazdy** | Radar chart + słupki porównawcze 10 metryk |
| **Mapa toru** | Mapy dominacji / prędkości / biegów + animacja okrążenia |
| **Race Pace** | Wykres tempa wyścigu, składy opon, statystyki okrążeń |
| **Cross-session** | Porównanie sesji A vs B (np. Monaco 2023 vs 2024) |
| **Info** | Lista wygenerowanych wykresów, informacje o sesji B |

---

## Sidebar — opcje

- Rok, runda (numer lub nazwa GP), typ sesji (`Q / R / FP1 / FP2 / FP3 / S / SS`)
- Dynamiczne ładowanie listy kierowców z wybranej sesji
- Ręczny wpis kodów kierowców (nadpisuje multiselect)
- Wybór modułów analizy (można wyłączyć niepotrzebne)
- Liczba mini-sektorów (10–50)
- Porównanie sesji B (cross-session) w rozwijanym panelu

---

## Struktura projektu

```text
Telemetry_Dashboard_F1/
├── app.py                       ← Frontend Streamlit (główny punkt wejścia)
├── config.py                    ← Konfiguracja (ścieżki, progi, parametry)
├── requirements.txt
├── .streamlit/
│   └── config.toml              ← Motyw Streamlit
├── f1tele/
│   ├── __init__.py
│   ├── data_loader.py           ← Ładowanie danych FastF1 + cache
│   ├── plots_interactive.py     ← Wykresy interaktywne (Plotly)
│   ├── lap_analysis.py          ← Wykresy telemetrii (matplotlib)
│   ├── corner_analysis.py       ← Analiza zakręt-po-zakręcie
│   ├── sector_analysis.py       ← Mini-sektory i sektory
│   ├── driver_style.py          ← Odcisk palca stylu jazdy + radar
│   ├── track_map.py             ← Mapy toru (matplotlib)
│   └── report.py                ← Generator raportu HTML
├── cache/                       ← Cache FastF1 (automatyczny, w .gitignore)
└── output/
    ├── plots/                   ← Zapisane wykresy PNG
    └── reports/                 ← Raporty HTML
```

---

## Metryki stylu jazdy

| Metryka | Opis |
| --- | --- |
| **Pełny gaz** | % okrążenia z throttle > 90% |
| **Intensywne hamowanie** | % okrążenia z brake > 20% |
| **Wybieg (coasting)** | % okrążenia bez gazu i bez hamulca |
| **Prędkość w zakrętach** | Średnia prędkość minimalna w apeksach |
| **Agresywność hamowania** | Średnia maksymalna siła hamowania |
| **Płynność gazu** | Stabilność dławika (1 - CV) |
| **Wysokie RPM** | % czasu z RPM > 90% maksymalnego |
| **Średnia prędkość** | Ogólna średnia prędkość na okrążeniu |
| **Zmiany biegów** | Częstotliwość zmian przełożeń |
| **Spójność hamowania** | Powtarzalność punktów hamowania w zakrętach |

---

## Wymagania

- Python 3.10+
- Połączenie z internetem (pierwsze pobranie danych FastF1)
- ~500 MB wolnego miejsca na dysku (cache na sezon)

---

## Licencja

Projekt edukacyjny. Dane F1 pochodzą z FastF1 / Ergast API — wyłącznie do użytku niekomercyjnego.
