"""Kern von Hand gerechnet: Quoten, Zellen, zulässige Gremien, einfaches Ziehen, Leximin am Beispiel mit vier Personen, Eingabeprüfung."""

from fractions import Fraction as F

import numpy as np
import pytest

import zgr_algorithm as A
import zgr_constants as C


# --- Quoten ------------------------------------------------------------------------------------------------------------------------------------

def test_quotas_by_hand_for_ten_seats_and_one_slack():
    q = A.make_quotas(C.SHARES, 10, 1)
    assert q[(0, 0)] == (4, 6) and q[(0, 1)] == (4, 6)                                          # 5 und 5, ±1
    assert q[(1, 0)] == (2, 4) and q[(1, 1)] == (3, 5) and q[(1, 2)] == (2, 4)                 # 3, 4, 3
    assert q[(2, 0)] == (3, 6) and q[(2, 1)] == (2, 5) and q[(2, 2)] == (1, 3)                 # 4,5 → 4 und 5; 3,5 → 3 und 4; 2


def test_quotas_for_two_seats_without_slack_and_the_clamps():
    q = A.make_quotas(C.SHARES, 2, 0)
    assert q[(0, 0)] == (1, 1) and q[(1, 0)] == (0, 1) and q[(1, 1)] == (0, 1) and q[(2, 2)] == (0, 1)       # 0,6 / 0,8 / 0,4 Plätze: 0 bis 1
    wide = A.make_quotas(C.SHARES, 2, 2)
    assert wide[(0, 0)] == (0, 2) and all(0 <= lo <= hi <= 2 for lo, hi in wide.values())                     # nach unten bei 0, nach oben bei k begrenzt


def test_quotas_use_exact_fractions():
    shares = ((F(3, 10), F(7, 10)),)
    assert A.make_quotas(shares, 10, 0) == {(0, 0): (3, 3), (0, 1): (7, 7)}                    # 0,3 · 10 ist genau 3, auch wenn 0.3 · 10 als Gleitkomma 3.0000000000000004 wäre


@pytest.mark.parametrize("k,slack", [(0, 1), (-1, 0), (3, -1)])
def test_quotas_reject_bad_arguments(k, slack):
    with pytest.raises(ValueError):
        A.make_quotas(C.SHARES, k, slack)


# --- Zellen und zulässige Gremien -----------------------------------------------------------------------------------------------------------------

def test_cells_group_equal_persons():
    pool = [(1, 0, 2), (0, 0, 1), (1, 0, 2), (0, 0, 1), (0, 0, 1)]
    cells, counts, of_person = A.cells_of(pool)
    assert cells == [(0, 0, 1), (1, 0, 2)] and counts == [3, 2] and of_person == [1, 0, 1, 0, 0]


def test_feasible_panels_of_the_four_person_example(mini):
    pool, k, quotas = mini
    ok = [p for p in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)] if A.panel_ok(pool, p, k, quotas)]
    assert ok == [(0, 3), (1, 2), (1, 3)]


def test_panel_ok_rejects_wrong_sizes_duplicates_and_quota_violations(mini):
    pool, k, quotas = mini
    assert not A.panel_ok(pool, (0,), k, quotas) and not A.panel_ok(pool, (0, 0), k, quotas) and not A.panel_ok(pool, (0, 1, 3), k, quotas)
    assert not A.panel_ok(pool, (0, 1), k, quotas) and not A.panel_ok(pool, (0, 2), k, quotas) and not A.panel_ok(pool, (2, 3), k, quotas)


def test_panel_ok_rejects_a_repeated_person_even_if_the_quotas_would_fit():
    pool = [(0, 0, 0), (1, 1, 1)]
    wide = A.make_quotas(C.SHARES, 2, 2)
    assert A.panel_ok(pool, (0, 1), 2, wide) and not A.panel_ok(pool, (0, 0), 2, wide) and not A.panel_ok(pool, (1, 1), 2, wide)


def test_best_vector_maximises_the_weighted_sum(mini):
    pool, k, quotas = mini
    cells, counts, _ = A.cells_of(pool)
    vec, value = A.best_vector(cells, counts, k, quotas, [0.0, 0.0, 0.0, 0.0])
    assert sum(vec) == 2 and value == 0
    vec, value = A.best_vector(cells, counts, k, quotas, [5.0, 0.0, 0.0, 1.0])
    assert vec == (1, 0, 0, 1) and value == 6.0
    vec, value = A.best_vector(cells, counts, k, quotas, [0.0, 3.0, 4.0, 0.0])
    assert vec == (0, 1, 1, 0) and value == 7.0


def test_is_feasible_detects_impossible_quotas():
    pool = [(0, 0, 0)] * 5                                                                     # nur Frauen: mit genau einer Frau und einem Mann nicht zu besetzen
    cells, counts, _ = A.cells_of(pool)
    assert not A.is_feasible(cells, counts, 2, A.make_quotas(C.SHARES, 2, 0))
    assert A.best_vector(cells, counts, 2, A.make_quotas(C.SHARES, 2, 0), [1.0]) is None
    with pytest.raises(ValueError):
        A.leximin(cells, counts, 2, A.make_quotas(C.SHARES, 2, 0))


# --- Einfaches Ziehen -------------------------------------------------------------------------------------------------------------------------

def test_greedy_panel_depends_on_the_order(mini):
    pool, k, quotas = mini
    assert A.greedy_panel(pool, [0, 1, 2, 3], k, quotas) == (0, 3)                             # a, dann b (zwei Frauen: abgelehnt), c (Region 0 doppelt: abgelehnt), d
    assert A.greedy_panel(pool, [1, 2, 0, 3], k, quotas) == (1, 2)
    assert A.greedy_panel(pool, [3, 0, 1, 2], k, quotas) == (0, 3)
    assert A.greedy_panel(pool, [2, 3, 0, 1], k, quotas) == (1, 2)                             # c, d (zwei Männer: abgelehnt), a (Region 0: abgelehnt), b


def test_greedy_panel_fails_when_a_lower_quota_is_missed():
    pool = [(0, 0, 0), (0, 0, 0), (0, 0, 0), (1, 1, 1)]
    quotas = A.make_quotas(C.SHARES, 2, 0)                                                     # eine Frau und ein Mann sind nötig
    assert A.greedy_panel(pool, [3, 0, 1, 2], 2, quotas) == (0, 3)
    assert A.greedy_panel(pool, [0, 1, 2, 3], 2, quotas) == (0, 3)                             # die zweite Frau wird wegen der Obergrenze abgelehnt, dann der Mann genommen


def test_exact_greedy_probabilities_of_the_four_person_example(mini):
    pool, k, quotas = mini
    probs, valid = A.exact_greedy_probabilities(pool, k, quotas)
    assert valid == 24 and probs == [F(3, 8), F(5, 8), F(3, 8), F(5, 8)]
    assert sum(probs) == k


def test_estimated_greedy_probabilities_are_close_and_deterministic(mini):
    pool, k, quotas = mini
    est, tries = A.greedy_probabilities(pool, k, quotas, 4000, seed=3)
    assert est == A.greedy_probabilities(pool, k, quotas, 4000, seed=3)[0] and tries >= 4000
    for got, want in zip(est, (3 / 8, 5 / 8, 3 / 8, 5 / 8)):
        assert abs(got - want) < 4 * np.sqrt(want * (1 - want) / 4000)                         # vier Standardabweichungen
    assert sum(est) == pytest.approx(k)


def test_exact_greedy_probabilities_edge_cases():
    quotas = A.make_quotas(C.SHARES, 1, 1)
    probs, valid = A.exact_greedy_probabilities([(0, 0, 0)], 1, quotas)                            # eine Person, eine Reihenfolge
    assert probs == [F(1)] and valid == 1
    with pytest.raises(ValueError):
        A.exact_greedy_probabilities([(0, 0, 0)] * 3, 2, A.make_quotas(C.SHARES, 2, 0))           # nur Frauen: nie gültig


def test_greedy_probabilities_stop_after_the_maximal_number_of_tries():
    """Drei Frauen (0, 0, 0), ein Mann (1, 0, 1) im selben Alter wie die Frauen und ein Mann (1, 1, 1): beginnt die Reihenfolge mit dem ersten Mann, kommt keine Frau mehr hinein (gleiches Alter) und der zweite Mann nicht
    (zwei Männer): ungültig. Ein Teil der Reihenfolgen scheitert also; bei einem Versuch je Ziehung ist nach genau 40 Versuchen Schluss."""
    pool = [(0, 0, 0)] * 3 + [(1, 0, 1), (1, 1, 1)]
    quotas = A.make_quotas(C.SHARES, 2, 0)
    est, tries = A.greedy_probabilities(pool, 2, quotas, 40, seed=1, max_tries=1)
    assert tries == 40 and sum(est) == pytest.approx(2.0)


def test_greedy_probabilities_fail_without_any_valid_panel():
    pool = [(0, 0, 0)] * 4
    with pytest.raises(ValueError):
        A.greedy_probabilities(pool, 2, A.make_quotas(C.SHARES, 2, 0), 10, 1, max_tries=5)


# --- Leximin ------------------------------------------------------------------------------------------------------------------------------------

def test_leximin_gives_everyone_one_half_in_the_four_person_example(mini):
    pool, k, quotas = mini
    cells, counts, of_person = A.cells_of(pool)
    lot = A.leximin(cells, counts, k, quotas)
    assert A.person_probabilities(lot["pi"], of_person) == pytest.approx([0.5] * 4, abs=1e-8)
    assert lot["levels"] == pytest.approx([0.5] * len(lot["levels"]), abs=1e-6) and lot["complete"]               # entartete Dualpreise: weitere Stufen mit demselben Wert
    assert sorted(lot["panels"]) == [(0, 1, 1, 0), (1, 0, 0, 1)] and lot["probs"] == pytest.approx([0.5, 0.5], abs=1e-8)


def test_leximin_with_a_forced_member_and_a_free_choice():
    """Eine Frau (a) muss in jedem Gremium sitzen, zwei Männer (b, c) teilen sich den zweiten Platz: a hat Chance 1, b und c je 1/2 (Quote Alter und Region lassen es zu, Spielraum 1)."""
    pool = [(0, 0, 0), (1, 1, 1), (1, 1, 1)]
    quotas = A.make_quotas(C.SHARES, 2, 0)
    cells, counts, of_person = A.cells_of(pool)
    lot = A.leximin(cells, counts, 2, quotas)
    assert A.person_probabilities(lot["pi"], of_person) == pytest.approx([1.0, 0.5, 0.5], abs=1e-8)
    assert lot["levels"][0] == pytest.approx(0.5, abs=1e-8) and lot["levels"] == sorted(lot["levels"]) and lot["complete"]


def test_leximin_single_stage_returns_the_smallest_chance(mini):
    pool, k, quotas = mini
    cells, counts, _ = A.cells_of(pool)
    first = A.leximin(cells, counts, k, quotas, max_stages=1)
    assert first["levels"] == pytest.approx([0.5], abs=1e-8) and min(first["pi"]) == pytest.approx(0.5, abs=1e-8)


def test_leximin_probabilities_sum_to_k_and_panels_are_feasible(mini):
    pool, k, quotas = mini
    cells, counts, of_person = A.cells_of(pool)
    lot = A.leximin(cells, counts, k, quotas)
    assert sum(lot["probs"]) == pytest.approx(1.0) and sum(A.person_probabilities(lot["pi"], of_person)) == pytest.approx(k)
    for vec in lot["panels"]:
        assert sum(vec) == k and all(0 <= x <= counts[c] for c, x in enumerate(vec))


# --- Beispielziehung --------------------------------------------------------------------------------------------------------------------------

def test_sample_panel_is_deterministic_feasible_and_follows_the_lottery(mini):
    pool, k, quotas = mini
    cells, counts, of_person = A.cells_of(pool)
    lot = A.leximin(cells, counts, k, quotas)
    assert A.sample_panel(lot, cells, of_person, 5) == A.sample_panel(lot, cells, of_person, 5)
    seen = {A.sample_panel(lot, cells, of_person, s) for s in range(60)}
    assert seen == {(0, 3), (1, 2)} and all(A.panel_ok(pool, p, k, quotas) for p in seen)       # beide Gremien des Loses kommen vor, kein anderes


def test_sample_panel_draws_group_members_without_repetition():
    pool = [(0, 0, 0)] * 5 + [(1, 1, 1)] * 5
    quotas = A.make_quotas(C.SHARES, 4, 1)
    cells, counts, of_person = A.cells_of(pool)
    lot = A.leximin(cells, counts, 4, quotas)
    for seed in range(30):
        panel = A.sample_panel(lot, cells, of_person, seed)
        assert len(set(panel)) == 4 and A.panel_ok(pool, panel, 4, quotas)
