# 🏎 F1 Telemetria — Porównanie stylu jazdy kierowców

Rozbudowane narzędzie CLI do analizy i wizualizacji danych telemetrycznych Formuły 1.
Korzysta z biblioteki **FastF1** (Python) — daje dostęp do prędkości, gazu, hamulca, biegów i pozycji GPS zakręt po zakręcie.

---

## Funkcje

| Moduł | Opis |
|---|---|
| **Telemetria** | Prędkość, gaz, hamulec, biegi, RPM — wspólny wykres z deltą czasu |
| **Zakręty** | Wykrycie zakrętów, punkt hamowania, apeks, wyjście z gazu |
| **Mini-sektory** | Dominacja w N mini-sektorach, skumulowana delta, mapa ciepła |
| **Sektory** | Statystyki S1/S2/S3: czas, prędkości, % gazu, % hamowania |
| **Styl jazdy** | Radar chart + wykres słupkowy 10 metryk charakteryzujących styl |
| **Mapa toru** | Dominacja na torze, mapa prędkości, mapa biegów (wymaga danych GPS) |
| **Raport HTML** | Pełny raport z tabelami i wykresami |

---

## Instalacja

```bash
# Utwórz środowisko wirtualne
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt
```

---

## Frontend (Streamlit)

Oprócz CLI dostępny jest pełny **interfejs webowy** — uruchom i otwórz w przeglądarce:

```bash
streamlit run app.py
```

Aplikacja otworzy się pod adresem `http://localhost:8501`.

### Co oferuje frontend

| Sekcja | Opis |
| --- | --- |
| **Sidebar** | Wybór roku, rundy, sesji, kierowców i opcji analizy |
| **Podsumowanie** | Tabela wyników + karty kierowców |
| **Telemetria** | Pełny 6-panelowy wykres z możliwością pobrania |
| **Zakręty** | Wykresy + tabela danych zakrętowych |
| **Sektory** | Mini-sektory, dominacja, mapa ciepła |
| **Styl jazdy** | Radar + tabela 10 metryk |
| **Mapa toru** | Mapy dominacji / prędkości / biegów |
| **Raport** | Podgląd i pobieranie raportu HTML |

---

## Szybki start

### Porównaj telemetrię w kwalifikacjach

```bash
python main.py compare --year 2024 --round 5 --session Q --drivers VER,HAM,NOR
```

### Porównaj w wyścigu

```bash
python main.py compare --year 2024 --round Monaco --session R --drivers LEC,VER,NOR
```

### Wybierz konkretne okrążenia

```bash
python main.py compare -y 2024 -r 1 -s Q -d VER,NOR --laps VER=1,NOR=3
```

### Uruchom tylko wybrane moduły

```bash
python main.py compare -y 2024 -r 5 -s Q -d VER,HAM --modules telemetry,style
```

### Wyświetl harmonogram sezonu

```bash
python main.py schedule --year 2024
```

### Wyświetl kierowców w sesji

```bash
python main.py drivers --year 2024 --round 5 --session Q
```

---

## Opcje polecenia `compare`

| Opcja | Skrót | Opis |
|---|---|---|
| `--year` | `-y` | Rok sezonu (np. 2024) |
| `--round` | `-r` | Numer rundy lub nazwa GP (np. `5` lub `Monaco`) |
| `--session` | `-s` | Typ sesji: `Q`, `R`, `FP1`, `FP2`, `FP3`, `S`, `SS` |
| `--drivers` | `-d` | Kody kierowców oddzielone `,` (np. `VER,HAM,NOR`) |
| `--laps` | `-l` | Konkretne okrążenia: `VER=1,HAM=3` |
| `--mini-sectors` | `-m` | Liczba mini-sektorów (domyślnie 25) |
| `--modules` | | Moduły: `all` lub `telemetry,corners,sectors,style,track,report` |
| `--no-save` | | Nie zapisuj wykresów |
| `--show` | | Wyświetl wykresy interaktywnie |
| `--no-report` | | Nie generuj raportu HTML |

---

## Struktura projektu

```
F1_Tele/
├── main.py                  ← Główny punkt wejścia CLI
├── config.py                ← Konfiguracja
├── requirements.txt
├── f1tele/
│   ├── __init__.py
│   ├── data_loader.py       ← Ładowanie danych FastF1 + cache
│   ├── lap_analysis.py      ← Wykresy telemetrii (prędkość, gaz, hamulec, biegi)
│   ├── corner_analysis.py   ← Analiza zakręt-po-zakręcie
│   ├── sector_analysis.py   ← Mini-sektory i sektory
│   ├── driver_style.py      ← Odcisk palca stylu jazdy + radar
│   ├── track_map.py         ← Mapy toru (dominacja, prędkość, biegi)
│   └── report.py            ← Generator raportu HTML
├── cache/                   ← Cache FastF1 (automatyczny)
└── output/
    ├── plots/               ← Zapisane wykresy PNG
    └── reports/             ← Raporty HTML
```

---

## Metryki stylu jazdy

| Metryka | Opis |
|---|---|
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
- Wolne miejsce na dysku (~500 MB cache na sezon)

---

## Przykładowe wyniki

Po uruchomieniu w folderze `output/plots/` pojawią się:

- `*_telemetry.png` — 6-panelowy wykres telemetrii
- `*_corners.png` — słupki zakręt-po-zakręcie
- `*_mini_sectors.png` — dominacja w mini-sektorach
- `*_sector_heatmap.png` — mapa ciepła sektorów
- `*_radar.png` — radar stylu jazdy
- `*_style_bars.png` — porównanie metryk
- `*_track_dominance.png` — mapa toru (jeśli dostępne GPS)
- `*_speed_map.png` — mapa prędkości na torze
- `*_gear_map.png` — mapa biegów na torze

Raport HTML: `output/reports/*.html`

---

## Licencja

Projekt edukacyjny. Dane F1 pochodzą z FastF1 / Ergast API.
