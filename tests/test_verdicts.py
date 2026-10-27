"""Verdikte, Tabellen, Texte und Formatierung als reine Funktionen: jeder Zweig mit Beispielen, deren Text von Hand erwartet wird."""

import zgr_constants as C
import zgr_evaluation as ev


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_formatting():
    assert ev.num(1.5, 2) == "1,50" and ev.num(-0.5) == "−0,5" and ev.pct(0.105) == "10,5 %" and ev.pct(-0.012) == "−1,2 %" and ev.pct(None) == "–" and ev.pct(float("nan")) == "–"
    assert ev.category_name(1, 2) == "55+" and ev.category_name(2, 0) == "Nord"
    assert ev.person_text([(0, 1, 2)], 0) == "Person 1 (Frauen, 35–54, Süd)"


def test_group_rows_of_the_four_person_example():
    rows = ev.group_rows(analyse("Vier Freiwillige, zwei Plätze"))
    assert len(rows) == 8
    assert rows[0] == {"Merkmal": "Geschlecht", "Kategorie": "Frauen", "im Pool": "2 (50 %)", "Quote": "1 bis 1 von 2", "Leximin": "50,0 %", "Einfaches Ziehen": rows[0]["Einfaches Ziehen"]}
    assert rows[3]["Kategorie"] == "35–54" and rows[3]["im Pool"] == "1 (25 %)" and rows[3]["Quote"] == "0 bis 1 von 2"
    assert rows[4]["Kategorie"] == "55+" and rows[4]["Leximin"] == "50,0 %" and rows[7]["Kategorie"] == "Süd" and rows[7]["im Pool"] == "1 (25 %)"


def test_group_rows_show_a_dash_for_empty_categories():
    a = ev.analyse(ev.Settings(k=2, slack=1, pool="\n".join(["0 0 0", "1 0 0", "0 0 0", "1 0 0"])))
    rows = ev.group_rows(a)
    empty = next(r for r in rows if r["Kategorie"] == "35–54")
    assert empty["im Pool"] == "0 (0 %)" and empty["Leximin"] == "–" and empty["Einfaches Ziehen"] == "–"


def test_lottery_rows_of_the_four_person_example():
    rows = ev.lottery_rows(analyse("Vier Freiwillige, zwei Plätze"))
    assert len(rows) == 2 and {r["Wahrscheinlichkeit"] for r in rows} == {"50,0 %"}
    assert {r["Region"] for r in rows} == {"Nord 1 · Mitte 0 · Süd 1", "Nord 1 · Mitte 1 · Süd 0"} and rows[0]["Geschlecht"] == "Frauen 1 · Männer 1"


def test_demo_rows_and_composition():
    a = analyse("Vier Freiwillige, zwei Plätze")
    assert len(a.demo) == 2 and a.demo in ((0, 3), (1, 2))
    rows = ev.demo_rows(a)
    assert [r["Person"] for r in rows] == [f"Person {i + 1}" for i in a.demo] and all(r["Chance (Leximin)"] == "50,0 %" for r in rows)
    comp = ev.demo_composition(a)
    assert sum(r["im Gremium"] for r in comp[:2]) == 2 and comp[0]["Quote"] == "1 bis 1" and sum(r["im Gremium"] for r in comp[2:5]) == 2


def test_lowest_group():
    a = analyse("Vier Freiwillige, zwei Plätze")
    fname, cat, m = ev.lowest_group(a, "einfach")
    assert m == min(sum(a.simple[i] for i, p in enumerate(a.pool) if p[f] == v) / sum(1 for p in a.pool if p[f] == v)
                    for f in range(3) for v in range(len(C.SHARES[f])) if any(p[f] == v for p in a.pool))
    assert ev.lowest_group(a, "leximin")[2] == 0.5 or abs(ev.lowest_group(a, "leximin")[2] - 0.5) < 1e-8


def test_verdict_for_the_default_preset():
    kind, text = ev.verdict_state(analyse("Achtzig Freiwillige, zehn Plätze"))
    assert kind == "success" and text == (
        "Leximin: die kleinste Chance liegt bei 10,5 % (ideal bei Gleichheit: 12,5 %, also 84 % davon). Einfaches Ziehen mit Quoten: die kleinste Chance liegt bei etwa 9,2 % (Schätzung), 12 % unter dem Leximin-Wert. "
        "Am schlechtesten stehen beim einfachen Ziehen im Mittel „55+“ (Alter) mit 9,7 %.")


def test_verdict_for_the_four_person_example():
    kind, text = ev.verdict_state(analyse("Vier Freiwillige, zwei Plätze"))
    assert kind == "success" and text.startswith("Leximin: die kleinste Chance liegt bei 50,0 % (ideal bei Gleichheit: 50,0 %, also 100 % davon). Einfaches Ziehen mit Quoten: die kleinste Chance liegt bei etwa 37,")


def test_infeasible_pool_is_reported():
    a = ev.analyse(ev.Settings(k=2, slack=0, pool="\n".join(["0 0 0"] * 4)))
    assert not a.feasible and a.lottery is None and a.leximin == [] and a.demo == ()


def test_k_larger_than_the_pool_is_reduced_with_a_note():
    a = ev.analyse(ev.Settings(k=8, slack=2, pool="\n".join(["0 0 0", "1 1 1", "0 1 2"])))
    assert a.k == 3 and a.note == "Der Pool hat nur 3 Personen, gelost wird mit 3 Plätzen statt 8." and a.feasible
    assert a.leximin == [1.0, 1.0, 1.0]


def test_invalid_pool_falls_back_to_a_generated_one_with_a_message():
    a = ev.analyse(ev.Settings(pool="0 0 0\n0 0 9"))
    assert a.source == "erzeugt" and a.n == C.DEFAULT_N
    assert a.errors == ["Eigener Pool: Zeile 2: Region hat nur die Kategorien 0 bis 2 (eingegeben: 9). Die Eingabe wird ignoriert."]


def test_pool_overrides_the_number_of_freiwillige():
    a = ev.analyse(ev.Settings(n=150, k=2, slack=1, pool="\n".join(["0 0 0", "1 1 1", "0 1 1", "1 0 0"])))
    assert a.source == "eingegeben" and a.n == 4 and a.errors == []


# --- Reihen-Verdikte mit künstlichen Zeilen ---------------------------------------------------------------------------------------------------

def _gain_rows():
    return [{"bias": b, "n": 100, "runs": 10, "skipped": 0, "leximin_min": 0.09 - b / 2000, "simple_min": 0.06 - b / 2400, "ideal": 0.1, "better": 10} for b in (0, 30, 60, 90)]


def test_verdict_series_gain():
    kind, text = ev.verdict_series_gain(_gain_rows())
    assert kind == "info" and text == ("Über 40 Pools hebt Leximin die kleinste Chance in 40 gegenüber dem einfachen Ziehen; bei verzerrten Meldungen im Mittel um 58 % bis 100 %. "
                                       "Die ideale Chance k/n erreicht es nur, wenn die Quoten der Auswahl genug Raum lassen.")


def _slack_rows():
    return [{"slack": s, "bias": b, "runs": 10, "skipped": 0, "share": 0.5 + 0.2 * s - (b / 1000)} for s in (0, 1, 2) for b in (30, 90)]


def test_verdict_series_slack():
    kind, text = ev.verdict_series_slack(_slack_rows())
    assert kind == "info" and text == ("Ohne Spielraum erreicht die kleinste Chance im Mittel 44 % der idealen k/n, mit zwei Plätzen Spielraum 84 %: je enger die Quoten, desto weniger kann das Los angleichen.")


def _group_rows():
    rows = []
    for f, row in enumerate(C.SHARES):
        for v in range(len(row)):
            rows.append({"feature": f, "category": v, "runs": 5, "share": 0.35 if (f, v) == (0, 1) else 0.4, "leximin": 0.11, "simple": 0.125 if (f, v) == (0, 1) else 0.08, "ideal": 0.1})
    return rows


def test_verdict_series_groups():
    kind, text = ev.verdict_series_groups(_group_rows())
    assert kind == "info" and text == ("Bei 50 % Verzerrung stellen Männer 35 % des Pools; sie haben beim einfachen Ziehen im Mittel 12,5 %, beim Leximin 11,0 % (ideal 10,0 %). "
                                       "Die Älteren (55+), im Pool stark vertreten, fallen von 10,0 % (ideal) auf 8,0 % beim einfachen Ziehen und 11,0 % beim Leximin.")


def test_series_tables_format_the_rows():
    g = ev.gain_table(_gain_rows())[0]
    assert g == {"Verzerrung": "0 %", "Freiwillige": 100, "Pools": "10 (ausgelassen: 0)", "ideal k/n": "10,0 %", "Leximin: kleinste Chance": "9,0 %", "Einfaches Ziehen: kleinste Chance": "6,0 %", "Leximin besser in": "10 von 10"}
    s = ev.slack_table(_slack_rows())[1]
    assert s == {"Spielraum": "0 Plätze", "Verzerrung": "90 %", "Pools": "10 (ausgelassen: 0)", "kleinste Chance im Verhältnis zu k/n": "41 %"}
    r = ev.group_table(_group_rows())[1]
    assert r == {"Merkmal": "Geschlecht", "Kategorie": "Männer", "Anteil im Pool": "35 %", "ideal k/n": "10,0 %", "Einfaches Ziehen": "12,5 %", "Leximin": "11,0 %"}
