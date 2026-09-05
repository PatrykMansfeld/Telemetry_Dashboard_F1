# 🏎 F1 Telemetria — Analiza danych kierowców F1

Interaktywny dashboard do analizy i wizualizacji danych telemetrycznych Formuły 1.
Korzysta z biblioteki **FastF1** — daje dostęp do prędkości, gazu, hamulca, biegów
i pozycji GPS zakręt po zakręcie.

---

## Funkcje

| Moduł | Opis |
| --- | --- |
| **Telemetria** | Prędkość, gaz, hamulec, biegi, RPM — interaktywny wykres z deltą czasu |
| **Zakręty** | Oficjalna numeracja toru z FastF1, punkt hamowania, prędkość apeksu, wyjście z gazu |
| **Mini-sektory** | Dominacja w N mini-sektorach, skumulowana delta, mapa ciepła |
| **Sektory** | S1/S2/S3 na granicach z oficjalnych czasów: czas, prędkości, % gazu, % hamowania, kolory Purple/Green/Yellow |
| **Styl jazdy** | Radar + wykres słupkowy 10 metryk charakteryzujących styl |
| **Mapa toru** | Dominacja, gradient prędkości, biegi, strefy DRS (wymaga danych GPS) |
| **Animacja toru** | Animowana pozycja kierowców na torze klatka po klatce |
| **Race Pace** | Czasy okrążeń, trend, degradacja opon, stinty, pozycje |
| **Cross-session** | Porównanie telemetrii i stylu jazdy między dwiema sesjami / latami |

### Skąd biorą się liczby

- **Zakręty** pochodzą z planu toru w FastF1 (`get_circuit_info`), więc numeracja
  zgadza się z transmisją — łącznie z wariantami typu *T7A / T7B*. Gdy sesja nie
  udostępnia planu, wracamy do wykrywania minimów prędkości i wyraźnie to
  zaznaczamy w zakładce.
- **Granice sektorów** wyznaczamy z oficjalnych czasów sektorowych: znając czas
  końca S1 i S2 odczytujemy z telemetrii, na jakim dystansie kierowca je
  osiągnął. Tabela pokazuje obok siebie czas oficjalny i policzony z telemetrii,
  więc widać, ile wynosi błąd metody.
- **Kolory kierowców** biorą się z barw zespołów zwracanych przez FastF1, dzięki
  czemu składy z nowych sezonów też są poprawne.
- **Metryki stylu jazdy** są skalowane względem porównywanej grupy; obok skali
  0–100 tabela podaje wartości surowe w jednostkach fizycznych.

### Wydajność

Policzone analizy zostają w pamięci sesji — powrót do wcześniejszych parametrów
jest natychmiastowy (bez ponownego liczenia wykresów). FastF1 dodatkowo trzyma
pobrane dane w `cache/`.

### Układ

Sidebar to panel sterowania („co analizujemy”), główna kolumna to wyniki
(„co z tego wyszło”). Po uruchomieniu analizy wyniki są od razu na wierzchu —
panel można zwinąć jednym kliknięciem, a listwa zakładek przykleja się do góry
ekranu, więc nawigacja jest pod ręką także w połowie długiego wykresu.

Nad zakładkami stale widać kontekst: która sesja jest wczytana i czasy okrążeń
porównywanych kierowców w kolorach zespołów.

### Motyw jasny i ciemny

Cały interfejs — łącznie z tabelami, które rysujemy własnym HTML-em zamiast
`st.dataframe` — trzyma się jednej palety. Dashboard startuje w motywie, w którym
Streamlit rysuje własne widgety (ustawienie przeglądarki lub menu ⋮ → *Settings →
Appearance*). Przycisk w prawym górnym rogu nadpisuje motyw na czas sesji
i przemalowuje **już wygenerowane** wykresy, bez ponownego liczenia analizy.

---

## Instalacja

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

Wymagania: Python 3.10+, połączenie z internetem przy pierwszym pobraniu danych,
ok. 500 MB miejsca na cache sezonu.

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
| **Telemetria** | 6-panelowy wykres (prędkość, delta, gaz, hamulec, biegi, RPM) + delta czasu |
| **Zakręty** | Wykresy porównawcze, punkty hamowania, tabela danych zakrętowych |
| **Sektory** | Mini-sektory, mapa dominacji, mapa ciepła, statystyki S1/S2/S3 |
| **Styl jazdy** | Radar + słupki 10 metryk, tabela wartości |
| **Mapa toru** | Mapy dominacji / prędkości / biegów, DRS, animacja okrążenia |
| **Race Pace** | Tempo wyścigu, degradacja opon, stinty, pozycje, statystyki okrążeń |
| **Cross-session** | Porównanie sesji A vs B (np. Monaco 2023 vs 2024) |
| **Info** | Lista wygenerowanych wykresów oraz modułów, które się nie powiodły |

---

## Panel sterowania (sidebar)

- Rok, runda i typ sesji (`Q / R / FP1 / FP2 / FP3 / S / SS`)
- Skład kierowców pobierany z wybranej sesji — odświeża się automatycznie po
  zmianie parametrów sesji
- Ręczny wpis kodów kierowców — nadpisuje wybór z listy
- Okrążenie: najszybsze każdego kierowcy albo konkretny numer (porównanie
  świeżej i zużytej opony w tym samym wyścigu)
- Liczba mini-sektorów (10–50)
- Moduły analizy (zwinięte; odznaczenie skraca czas liczenia)
- Porównanie z drugą sesją (cross-session) i kalendarz sezonu

Dane z każdej tabeli można pobrać jako CSV, a każdy wykres zapisać jako PNG
(ikona aparatu na pasku narzędzi wykresu).

---

## Struktura projektu

```text
Telemetry_Dashboard_F1/
├── app.py                       ← Punkt wejścia Streamlit (składa ekran)
├── requirements.txt
├── requirements-dev.txt         ← pytest, pyflakes
├── pytest.ini
├── .streamlit/config.toml       ← Motyw Streamlita
│
├── f1tele/                      ← Logika, niezależna od interfejsu
│   ├── config.py                ← Progi analizy i wartości domyślne
│   ├── data_loader.py           ← Sesje, telemetria, cache FastF1
│   ├── corner_analysis.py       ← Detekcja zakrętów, pomiary corner-by-corner
│   ├── sector_analysis.py       ← Sektory i mini-sektory
│   ├── driver_style.py          ← Metryki stylu jazdy
│   ├── pipeline.py              ← Orkiestracja: parametry sesji → wykresy
│   └── plots/                   ← Wykresy Plotly
│       ├── theme.py             ← Palety motywów + restyle()
│       ├── _resample.py         ← Wspólne narzędzia numeryczne
│       ├── telemetry.py  corners.py  sectors.py
│       ├── style.py      track.py    race.py     weather.py
│
├── ui/                          ← Warstwa Streamlit
│   ├── state.py                 ← Klucze i dostęp do session_state
│   ├── controls.py              ← Panel sterowania w sidebarze
│   ├── components.py            ← chart(), table(), nagłówki sekcji
│   ├── analysis.py              ← Uruchamianie pipeline'u + pasek postępu
│   ├── styles.py                ← CSS: tokeny motywów i style komponentów
│   ├── welcome.py
│   └── tabs/                    ← Jedna zakładka = jeden plik
│
├── tests/                       ← Testy na danych syntetycznych (bez sieci)
├── ruff.toml                    ← Konfiguracja lintera
├── .github/workflows/ci.yml     ← CI: ruff + pytest na Pythonie 3.10 i 3.13
└── cache/                       ← Cache FastF1 (automatyczny, w .gitignore)
```

---

## Konfiguracja

Wszystkie progi analizy siedzą w [`f1tele/config.py`](f1tele/config.py) i są
faktycznie używane przez moduły analityczne — zmiana wartości wpływa na wyniki:

| Grupa | Przykłady |
| --- | --- |
| Domyślne parametry | `DEFAULT_YEAR`, `DEFAULT_DRIVERS`, `DEFAULT_MINI_SECTS`, `MAX_DRIVERS` |
| Zakres sezonów | `MIN_YEAR`, `MAX_YEAR`, `SEASON_ROUNDS` |
| Detekcja zakrętów | `CORNER_MIN_SPEED_DROP`, `CORNER_MIN_DIST_BETWEEN`, `CORNER_WINDOW_BEFORE/AFTER` |
| Styl jazdy | `THROTTLE_FULL_THRESHOLD`, `BRAKE_HEAVY_THRESHOLD`, `HIGH_RPM_THRESHOLD` |
| Wykresy | `DEFAULT_PLOT_THEME`, `TRACK_MAP_POINTS`, `ANIMATION_FRAMES` |

---

## Metryki stylu jazdy

Metryki są skalowane do 0–100 **w obrębie porównywanej grupy** — 100 oznacza
najwyższy wynik w danym zestawieniu, a nie wartość absolutną.

| Metryka | Opis |
| --- | --- |
| **Pełny gaz** | % okrążenia z throttle > 90% |
| **Intensywne hamowanie** | % okrążenia z brake > 20% |
| **Wybieg (coasting)** | % okrążenia bez gazu i bez hamulca |
| **Prędkość w zakrętach** | Średnia prędkość minimalna w apeksach |
| **Agresywność hamowania** | Średnia maksymalna siła hamowania |
| **Płynność gazu** | Stabilność dławika (100 − współczynnik zmienności) |
| **Wysokie RPM** | % czasu z RPM > 90% maksymalnego |
| **Średnia prędkość** | Ogólna średnia prędkość na okrążeniu |
| **Zmiany biegów** | Częstotliwość zmian przełożeń |
| **Spójność hamowania** | Powtarzalność punktów hamowania w zakrętach |

---

## Testy

Testy działają na danych syntetycznych — nie potrzebują sieci ani cache'u FastF1.

```bash
pip install -r requirements-dev.txt
python -m pytest      # testy
ruff check .          # lint
```

Zakres: każdy wykres buduje się w obu motywach i daje się przemalować bez
gubienia kolorów kierowców; zakręty pochodzą z planu toru, a sektory z
oficjalnych czasów (z awaryjnym przybliżeniem, gdy danych brak); pipeline izoluje
błędy pojedynczych modułów; warstwa danych poprawnie normalizuje telemetrię
z podstawionej sesji FastF1; panel sterowania siedzi w sidebarze, tabele używają
motywu aplikacji, a wszystkie zakładki renderują się bez wyjątku.

Te same dwa polecenia uruchamia CI przy każdym pushu i pull requeście.

---

## Licencja

Projekt edukacyjny. Dane F1 pochodzą z FastF1 / Ergast API — wyłącznie do użytku
niekomercyjnego.
