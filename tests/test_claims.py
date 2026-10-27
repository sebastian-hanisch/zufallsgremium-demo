"""Zahlen der README (Befunde): jede dort genannte Zahl steht hier als Behauptung, gerechnet mit den festen Zufalls-Seeds der Reihen.
Das Los ist exakt (HiGHS, Toleranz 1e-6); die Chancen des einfachen Ziehens sind Schätzungen aus Zufallsziehungen mit festem Seed und werden mit einer Toleranz von drei Promille verglichen."""

import pytest

import zgr_constants as C
import zgr_evaluation as ev

SIMPLE_TOL = 3e-3
EXACT_TOL = 2e-5


@pytest.fixture(scope="module")
def gain():
    return ev.series_gain()


@pytest.fixture(scope="module")
def slack():
    return ev.series_slack()


@pytest.fixture(scope="module")
def groups():
    return ev.series_groups()


def row(rows, **kw):
    return next(r for r in rows if all(r[k] == v for k, v in kw.items()))


# --- Reihe 1: wie viel hebt Leximin? ----------------------------------------------------------------------------------------------------------

def test_smallest_chance_per_bias(gain):
    expected = {0: (0.09964, 0.08119), 30: (0.0959, 0.07799), 60: (0.08393, 0.0659), 90: (0.07223, 0.05707)}
    for bias, (lx, sm) in expected.items():
        r = row(gain, bias=bias)
        assert r["leximin_min"] == pytest.approx(lx, abs=EXACT_TOL) and r["simple_min"] == pytest.approx(sm, abs=SIMPLE_TOL), bias
        assert r["runs"] == 10 and r["skipped"] == 0 and r["better"] == 10 and r["ideal"] == pytest.approx(0.1)


def test_leximin_beats_simple_drawing_in_every_pool_and_stays_below_the_ideal(gain):
    assert all(r["better"] == r["runs"] and r["leximin_min"] <= r["ideal"] + 1e-9 for r in gain)
    assert [r["leximin_min"] for r in gain] == sorted((r["leximin_min"] for r in gain), reverse=True)        # mehr Verzerrung, kleinere beste Chance


def test_readme_strings_of_the_first_series(gain):
    assert [ev.pct(r["leximin_min"]) for r in gain] == ["10,0 %", "9,6 %", "8,4 %", "7,2 %"]
    assert [ev.pct(r["simple_min"]) for r in gain] == ["8,1 %", "7,8 %", "6,6 %", "5,7 %"]
    gains = [r["leximin_min"] / r["simple_min"] - 1 for r in gain]
    assert (ev.pct(min(gains), 0), ev.pct(max(gains), 0)) == ("23 %", "27 %")                       # „um etwa 23 bis 27 %“ in der README


def test_gain_verdict_and_table(gain):
    kind, text = ev.verdict_series_gain(gain)
    assert text == ("Über 40 Pools hebt Leximin die kleinste Chance in 40 gegenüber dem einfachen Ziehen; bei verzerrten Meldungen im Mittel um 23 % bis 27 %. "
                    "Die ideale Chance k/n erreicht es nur, wenn die Quoten der Auswahl genug Raum lassen.")
    t = ev.gain_table(gain)
    assert t[0] == {"Verzerrung": "0 %", "Freiwillige": 100, "Pools": "10 (ausgelassen: 0)", "ideal k/n": "10,0 %", "Leximin: kleinste Chance": "10,0 %", "Einfaches Ziehen: kleinste Chance": "8,1 %", "Leximin besser in": "10 von 10"}
    assert t[3]["Leximin: kleinste Chance"] == "7,2 %" and t[3]["Einfaches Ziehen: kleinste Chance"] == "5,7 %"


# --- Reihe 2: Preis der Quoten -----------------------------------------------------------------------------------------------------------------

def test_price_of_the_quotas(slack):
    expected = {(0, 30): 0.81162, (0, 90): 0.43006, (1, 30): 0.96468, (1, 90): 0.69996, (2, 30): 0.99589, (2, 90): 0.88137}
    for (s, bias), share in expected.items():
        r = row(slack, slack=s, bias=bias)
        assert r["share"] == pytest.approx(share, abs=EXACT_TOL) and r["runs"] == 10 and r["skipped"] == 0, (s, bias)


def test_more_slack_means_a_higher_smallest_chance(slack):
    for bias in C.SERIES_SLACK_BIASES:
        shares = [row(slack, slack=s, bias=bias)["share"] for s in C.SERIES_SLACKS]
        assert shares == sorted(shares) and shares[-1] <= 1 + 1e-9


def test_slack_verdict_and_table(slack):
    kind, text = ev.verdict_series_slack(slack)
    assert text == "Ohne Spielraum erreicht die kleinste Chance im Mittel 62 % der idealen k/n, mit zwei Plätzen Spielraum 94 %: je enger die Quoten, desto weniger kann das Los angleichen."
    t = ev.slack_table(slack)
    assert t[0] == {"Spielraum": "0 Plätze", "Verzerrung": "30 %", "Pools": "10 (ausgelassen: 0)", "kleinste Chance im Verhältnis zu k/n": "81 %"} and t[1]["kleinste Chance im Verhältnis zu k/n"] == "43 %"


# --- Reihe 3: Wer gewinnt, wer verliert? ---------------------------------------------------------------------------------------------------------

def test_mean_chance_per_category(groups):
    expected = {  # (Merkmal, Kategorie): (Anteil im Pool, Leximin, einfaches Ziehen)
        (0, 0): (0.652, 0.09193, 0.08733), (0, 1): (0.348, 0.11745, 0.12567), (1, 0): (0.183, 0.12015, 0.14344), (1, 1): (0.4055, 0.10119, 0.10059), (1, 2): (0.4115, 0.09298, 0.08403),
        (2, 0): (0.5635, 0.09898, 0.09243), (2, 1): (0.3015, 0.10013, 0.10568), (2, 2): (0.135, 0.10922, 0.1299)}
    for (f, v), (share, lx, sm) in expected.items():
        r = row(groups, feature=f, category=v)
        assert r["share"] == pytest.approx(share, abs=1e-6) and r["leximin"] == pytest.approx(lx, abs=EXACT_TOL) and r["simple"] == pytest.approx(sm, abs=SIMPLE_TOL), (f, v)
        assert r["runs"] == 20 and r["ideal"] == pytest.approx(0.1)


def test_those_who_volunteer_less_are_favoured_and_leximin_is_closer_to_the_ideal(groups):
    men, women = row(groups, feature=0, category=1), row(groups, feature=0, category=0)
    assert men["simple"] > men["leximin"] > men["ideal"] > women["leximin"] > women["simple"]
    young, old = row(groups, feature=1, category=0), row(groups, feature=1, category=2)
    assert young["simple"] > young["leximin"] > young["ideal"] > old["leximin"] > old["simple"]
    assert abs(old["leximin"] - old["ideal"]) < abs(old["simple"] - old["ideal"])


def test_groups_verdict_and_table(groups):
    kind, text = ev.verdict_series_groups(groups)
    assert text == ("Bei 50 % Verzerrung stellen Männer 35 % des Pools; sie haben beim einfachen Ziehen im Mittel 12,6 %, beim Leximin 11,7 % (ideal 10,0 %). "
                    "Die Älteren (55+), im Pool stark vertreten, fallen von 10,0 % (ideal) auf 8,4 % beim einfachen Ziehen und 9,3 % beim Leximin.")
    t = ev.group_table(groups)
    assert t[1] == {"Merkmal": "Geschlecht", "Kategorie": "Männer", "Anteil im Pool": "35 %", "ideal k/n": "10,0 %", "Einfaches Ziehen": "12,6 %", "Leximin": "11,7 %"}


def test_series_are_deterministic(gain, groups):
    again = ev.series_groups()
    assert [(r["leximin"], r["simple"]) for r in again] == [(r["leximin"], r["simple"]) for r in groups]
