# Zufallsgremium: gleiche Chance trotz Quoten – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-zufallsgremium-demo.streamlit.app/)** -->

Gelber Kandidat der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [column-generation-demo](https://github.com/sebastian-hanisch/column-generation-demo) (dasselbe Rechenverfahren am Cutting-Stock-Problem), [unteilbare-gueter-demo](https://github.com/sebastian-hanisch/unteilbare-gueter-demo) (Leximin als Regel für Güter), [gemeinsames-budget-demo](https://github.com/sebastian-hanisch/gemeinsames-budget-demo) und [komitee-wahl-demo](https://github.com/sebastian-hanisch/komitee-wahl-demo) (proportionale Vertretung bei Wahlen).
Die Demo fragt: **Ein Verein lost ein Gremium aus Freiwilligen. Es muss Quoten für Geschlecht, Alter und Region erfüllen, aber nicht alle Gruppen melden sich gleich häufig. Wer zu einer gut vertretenen Gruppe gehört, hat beim einfachen Ziehen mit Quoten eine deutlich kleinere Chance – wie gleich lassen sich die Chancen machen, wenn man ein Los über alle zulässigen Gremien rechnet?** **Leximin** maximiert die kleinste Chance, dann die zweitkleinste und so weiter; gerechnet wird per **Spaltengenerierung** (lineares Programm über die Gremien, das Preisproblem ist ein ganzzahliges Programm), und das Ergebnis wird mit dem einfachen Ziehen und mit der idealen Chance k/n verglichen.

Der Kern ist eigener Code (`numpy`, `scipy` mit HiGHS für das lineare Programm und das ganzzahlige Preisproblem). Unabhängige Orakel in den Tests: die **Aufzählung aller zulässigen Gremien** einer kleinen Auswahl mit den Leximin-Stufen als lineare Programme über alle Spalten (auf Personen statt auf Gruppen gerechnet), die **exakten Wahrscheinlichkeiten des einfachen Ziehens durch Aufzählung aller Reihenfolgen** gegen die Schätzung aus Zufallsziehungen.

## Warum dieses Problem

Beim einfachen Ziehen mit Quoten (Personen in zufälliger Reihenfolge durchgehen, aufnehmen, solange keine Obergrenze überschritten wird) sind die Chancen **ungleich**: wer zu einer häufig gemeldeten Gruppe gehört, kommt seltener hinein. In der Demo liegt die **kleinste Chance** bei 100 Freiwilligen und zehn Plätzen zwischen **6,4 %** (unverzerrte Meldungen) und **4,2 %** (starke Verzerrung), die ideale Chance wäre 10 %. Das Leximin-Los hebt sie auf **10,0 %** bzw. **7,2 %**, also um **55 bis 73 %**, und das in jedem der 40 Pools. Es erreicht die ideale Chance nur, wenn die Quoten Raum lassen.
Das Muster der Gewinner und Verlierer ist klar: wer sich **seltener meldet** (Männer, Jüngere, der Süden), wird beim einfachen Ziehen bevorzugt, wer sich **häufiger meldet** (Frauen, Ältere, der Norden), benachteiligt; Leximin gleicht das zu großen Teilen aus.

## Modell

**Pool.** n Freiwillige mit je einer Kategorie für Geschlecht (2), Altersgruppe (3) und Region (3). Wer sich meldet, ist verzerrt: die Meldewahrscheinlichkeit einer Kategorie ist ihr Bevölkerungsanteil mal (1 + Verzerrung · Neigung); Frauen, Ältere und der Norden melden sich häufiger.
**Quoten.** Für jede Kategorie: der Bevölkerungsanteil mal Plätze, abgerundet und aufgerundet (mit Brüchen gerechnet), plus der Spielraum in Plätzen. **Zulässig** ist jedes Gremium aus k Personen, das alle Quoten einhält.
**Los und Leximin.** Ein Los ist eine Wahrscheinlichkeitsverteilung über zulässige Gremien; die Chance einer Person ist die Summe der Wahrscheinlichkeiten der Gremien, in denen sie sitzt. Stufe 1 maximiert die kleinste Chance; Personen, deren Chance nicht mehr steigerbar ist (positiver Dualpreis), werden festgelegt, die nächste Stufe maximiert die kleinste Chance der übrigen. **Personen mit denselben Kategorien sind austauschbar**, deshalb wird auf Gruppen gerechnet (Zahl der Mitglieder je Gruppe in jedem Gremium).
**Einfaches Ziehen.** Zufällige Reihenfolge, aufnehmen, solange keine Obergrenze überschritten wird, aufhören bei k; gültig nur, wenn alle Untergrenzen erfüllt sind (sonst neu ziehen). Die Chancen sind Schätzungen aus 3.000 gültigen Ziehungen.
Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`zgr_algorithm.py`): Quoten, Gruppen, Preisproblem (`best_vector`, ganzzahlig), eine Stufe der Spaltengenerierung (`_stage`), `leximin` (alle Stufen oder `max_stages`), einfaches Ziehen (`greedy_panel`, Schätzung und exakte Aufzählung), Beispielziehung aus dem Los.
- **Szenario und Auswertung** (`zgr_scenario.py`, `zgr_evaluation.py`): Pool aus Verzerrung und Zufalls-Seed, Texteingabe mit Prüfung, Tabellen je Gruppe und Los, drei feste Reihen, alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): sechs Schnellstart-Szenarien (eines von Hand nachgerechnet), Regler für Plätze, Spielraum, Freiwillige, Verzerrung und Zufalls-Seed, Nummer der Beispielziehung, Textfeld für einen eigenen Pool, Chancen je Person und je Gruppe, das Los, eine Beispielziehung, Kernfrage, drei Reiter mit festen Reihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Das Los ist **exakt** gerechnet (HiGHS, Toleranz 10⁻⁶ bis 10⁻⁹); das einfache Ziehen ist eine **Schätzung** mit festem Zufalls-Seed, die Tests vergleichen sie mit Toleranz. Die Reihen laufen auf zufälligen Pools mit **100 Freiwilligen und zehn Plätzen** (Spielraum 1, wenn nicht anders genannt), je Zeile 10 Pools; die Gruppenreihe 20 Pools.

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Das Leximin-Los gleicht auf 40 kleinen Zufallspools (5 bis 9 Personen, zulässige und unzulässige) **der Aufzählung aller zulässigen Gremien** mit den Stufen als lineare Programme über alle Spalten (sortierte Chancen auf 10⁻⁶); Zulässigkeit, bestes Gremium zu Gewichten und Gruppengleichheit gleich der Aufzählung; die exakten Wahrscheinlichkeiten des einfachen Ziehens (alle Reihenfolgen) gleich der Zählung der Gremien, die Schätzung innerhalb 4,5 Standardabweichungen; Leximin ist lexikografisch mindestens so gut wie das einfache Ziehen. | `test_oracle_zufallsgremium.py`, `test_algorithm.py` |
| Wie viel hebt Leximin die kleinste Chance? | Kleinste Chance bei Leximin gegen einfaches Ziehen, Verzerrung 0 / 30 / 60 / 90 %: **10,0 / 9,6 / 8,4 / 7,2 %** gegen **6,4 / 6,0 / 4,9 / 4,2 %** (ideal 10,0 %); Leximin ist **in allen 40 Pools besser**, um 55 bis 73 %. | `test_claims.py::test_smallest_chance_per_bias`, `…::test_leximin_beats_simple_drawing_in_every_pool_and_never_reaches_the_ideal` |
| Was kosten die Quoten? | Kleinste Leximin-Chance im Verhältnis zur idealen: Spielraum 0 / 1 / 2 Plätze bei 30 % Verzerrung **81 / 96 / 100 %**, bei 90 % Verzerrung **43 / 70 / 88 %**. Ohne Spielraum fesseln die Quoten das Los, mit zwei Plätzen fast nicht. | `test_claims.py::test_price_of_the_quotas` |
| Wer gewinnt, wer verliert? | Mittlere Chance je Kategorie bei 50 % Verzerrung (ideal 10,0 %), einfaches Ziehen / Leximin: Frauen (65 % des Pools) 8,7 / 9,2 %, Männer (35 %) **12,6 / 11,7 %**; 18–34 (18 %) **14,3 / 12,0 %**, 55+ (41 %) **8,4 / 9,3 %**; Nord (56 %) 9,2 / 9,9 %, Süd (14 %) **13,0 / 10,9 %**. | `test_claims.py::test_mean_chance_per_category` |
| Vier Freiwillige, zwei Plätze (von Hand) | Eine Frau und ein Mann, die sich in Alter und Region unterscheiden: zulässig sind **drei Paare**. Leximin: jede Person **1/2** (zwei Paare je 1/2); einfaches Ziehen (alle 24 Reihenfolgen): **3/8, 5/8, 3/8, 5/8**. | `test_algorithm.py::test_leximin_gives_everyone_one_half_in_the_four_person_example`, `…::test_exact_greedy_probabilities_of_the_four_person_example` |
| Schnellstart-Szenarien | Achtzig Freiwillige (kleinste Chance 10,5 % gegen 8,6 %), starke Verzerrung (8,2 gegen 5,8 %, ideal 12,0 %), ohne Verzerrung (Leximin für alle 12,5 %, einfaches Ziehen 8,9 %), strenge Quoten (7,9 %, 63 % der idealen), kleiner Pool (35,7 gegen 28,6 %, manche Chance 100 %), das Vierer-Beispiel. | `test_presets.py` |
| Vormessung | Eine Vormessung vor dem Bau (12 Pools, Wegwerfskript, erste Stufe) zeigte denselben Sinn: kleinste Chance +30 bis 60 % gegenüber dem einfachen Ziehen; **keine Zahl daraus** steht hier, alle Zahlen sind die der festen Reihen der Demo. | – |

## Ehrliche Grenzen

- **Gleiche Chance ist ein Ziel unter mehreren.** Leximin sagt nichts über die Qualität eines einzelnen Gremiums; wer die Abbildung der Bevölkerung nur im Mittel über viele Lose will, bewertet es anders.
- **Wenige Merkmale, Quoten je Merkmal.** Die Quoten gelten für jede Kategorie einzeln, nicht für Kombinationen; mit vielen Merkmalen wird die Zahl der Gruppen groß, und manche Pools lassen kein zulässiges Gremium zu (die Demo meldet das).
- **Die Merkmale sind bekannt und ehrlich.**
- **Das einfache Ziehen ist eine Schätzung** (3.000 gültige Ziehungen, Fehler um einen halben Prozentpunkt) und **eine** übliche Vorgehensweise; echte Verfahren der Praxis sind komplizierter.
- **Gruppen statt Personen.** Personen derselben Kategorien sind austauschbar; bei weiteren Unterschieden (Vorlieben, Verfügbarkeit) müsste auf Personen gerechnet werden.
- **Leximin bis zu den Stufen der Dualpreise.** Bei entarteten Dualpreisen werden Personen mit gleicher Chance nacheinander festgelegt (mehrere Stufen mit demselben Wert); das Ergebnis stimmt mit der Aufzählung überein, die Zahl der Stufen ist aber kein Maß.
- **Reihen mit wenigen Pools.** Je Zeile 10 Pools (Reihe 3: 20) mit festen Zufalls-Seeds, aus Rechenzeit; die Mittel schwanken von Pool zu Pool.
- **Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Flanigan, Gölz, Gupta, Hennig, Procaccia, „Fair algorithms for selecting citizens’ assemblies“, Nature 2021; Gilmore und Gomory (1961) zur Spaltengenerierung.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9199.
- **Plan:** „Auswahl eines repräsentativen Gremiums mit möglichst gleicher Auswahlwahrscheinlichkeit; LP über Gremien (Spaltengenerierung)“. Umgesetzt; die Stufen nach der ersten (volles Leximin) sind gerechnet, die Reihen nutzen für die kleinste Chance nur Stufe 1.
- **Neu gegenüber dem Plan:** der **Preis der Quoten** (Spielraum), die Aufschlüsselung **nach Gruppen** (wer gewinnt, wer verliert), die Rechnung **auf Gruppen** statt auf Personen (exakt, viel schneller) und eine **eigene Eingabe des Pools**.
- **Preisproblem:** `scipy.optimize.milp` (HiGHS); Gleichstände unter gleich guten Gremien entscheidet der Löser, das Ergebnis (das Los) ist davon unabhängig, die Zusammensetzung des Loses nicht.
- **Reglerspanne:** Freiwillige 2 bis 200, Plätze 1 bis 16, Verzerrung 0 bis 100 %, Spielraum 0 bis 2 Plätze.

## Verifikation

- **Kern:** jede Einheit an Mini-Fällen von Hand (Quoten mit Brüchen, die Gruppen, die drei zulässigen Paare des Vierer-Beispiels, einfaches Ziehen je Reihenfolge, exakte Wahrscheinlichkeiten 3/8 und 5/8, Leximin 1/2, ein erzwungenes Mitglied).
- **Orakel:** Aufzählung aller Gremien mit Leximin-Stufen als lineare Programme, Aufzählung aller Reihenfolgen, Zulässigkeit und beste Gewichtssumme gegen die Aufzählung (siehe Befunde).
- **Reihen und Texte:** jede Zahl dieser README in `tests/test_claims.py`; Verdikte, Tabellen und Eingabefehler als reine Funktionen (`tests/test_verdicts.py`), Randfälle und Adresszeile (`tests/test_edge_cases.py`).
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, keines auf einem Rand von Freiwilligen und Plätzen, kein Preset entsteht durch Änderung eines einzigen Reglers bis auf die zwei benannten Grenzfälle, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 66 Stellen im Kern `zgr_algorithm.py`, **60 gefangen**, **5 als äquivalent festgehalten** (Toleranzen von 10⁻¹⁰ und 10⁻⁸ in der Spaltengenerierung, die Zahl der Startgremien, die die Spaltengenerierung ohnehin ergänzt, die nie erreichte Obergrenze von 500 Runden), **1 Mutant mit Zeitüberschreitung** (Endlosschleife des Ziehens; zählt nicht als gefangen). Der erste Lauf ließ 4 überleben und 7 in die Zeitüberschreitung laufen: darunter **eine nie erreichbare Rückfallregel** in `leximin` (die Dualpreise der freien Gruppen summieren sich auf 1; ersetzt durch einen Fehler), **vier echte Lücken** (ein Pool ohne gültiges Gremium und ein Pool mit nur einer Person in `exact_greedy_probabilities`, die Versuchsgrenze des einfachen Ziehens, ein doppelt genanntes Mitglied in `panel_ok`; je ein neuer Test).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `zgr_algorithm.py` | Kern: Quoten, Spaltengenerierung, Leximin, einfaches Ziehen, Beispielziehung |
| `zgr_constants.py` | Regler-Grenzen, feste Reihen, Farben, Presets |
| `zgr_evaluation.py` | Analyse, Tabellen, Verdikte, drei feste Reihen |
| `zgr_layout.py` | Fester Kopf (Stylesheet) |
| `zgr_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `zgr_scenario.py` | Pool der Freiwilligen, Verzerrung, Texteingabe |
| `zgr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Kern, Orakel, Reihen und Claims, Verdikte, Randfälle, Szenario, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Kombinationsquoten** (junge Männer im Norden) und **mehr Merkmale**: die Zahl der Gruppen wächst, und Pools werden leicht unzulässig.
- **Andere Fairnessmaße** (Nash-Wohlfahrt, Gini der Chancen) und ein **Preis der Gleichheit** (Abweichung der einzelnen Gremien von der Bevölkerung): jeweils ein eigenes Thema.
- **Echte Praxisverfahren** als Vergleich (Panelot, Sortition Foundation): keine Quelle gelesen.
- **Pools mit Gruppen weiterer Eigenschaften** (Verfügbarkeit, Vorlieben): die Rechnung müsste auf Personen laufen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
