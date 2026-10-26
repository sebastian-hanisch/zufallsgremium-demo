"""Orakel (DEMO-PLAYBOOK §12): unabhängige Gegenrechnungen.

- Leximin: Aufzählung ALLER zulässigen Gremien einer kleinen Auswahl (auf Personen, nicht auf Gruppen) und die Stufen als lineare Programme über alle Spalten; die sortierten Chancen müssen übereinstimmen.
- Einfaches Ziehen: exakte Wahrscheinlichkeiten durch Aufzählung aller Reihenfolgen gegen die Schätzung aus Zufallsziehungen.
- Eigenschaften: Los ist eine Verteilung, jede Spalte ist zulässig, Leximin ist lexikografisch mindestens so gut wie jedes andere Los (hier: das einfache Ziehen), alle Mitglieder einer Gruppe haben dieselbe Chance."""

import itertools
import random
from fractions import Fraction

import numpy as np
import pytest
from scipy.optimize import linprog

import zgr_algorithm as A
import zgr_constants as C


def random_pool(rng, n):
    return [(rng.randint(0, 1), rng.randint(0, 2), rng.randint(0, 2)) for _ in range(n)]


def all_feasible_panels(pool, k, quotas):
    return [c for c in itertools.combinations(range(len(pool)), k) if A.panel_ok(pool, c, k, quotas)]


def brute_leximin(pool, k, quotas):
    """Die sortierten Chancen des Leximin-Loses, auf Personen gerechnet. Stufe für Stufe: größtes z mit π_i ≥ z für die freien Personen; dann wird jede freie Person, deren Chance bei π_j ≥ z (alle freien j) nicht über z
    steigen kann, auf z festgelegt (Ergebnis ist unabhängig von der Wahl der Dualpreise)."""
    n = len(pool)
    panels = all_feasible_panels(pool, k, quotas)
    if not panels:
        return None
    m = len(panels)
    inc = np.zeros((n, m))
    for j, p in enumerate(panels):
        for i in p:
            inc[i, j] = 1
    fixed = {}
    while len(fixed) < n:
        free = [i for i in range(n) if i not in fixed]
        a = np.zeros((n, m + 1))
        b = np.zeros(n)
        a[:, :m] = -inc
        for i in free:
            a[i, m] = 1
        for i in fixed:
            b[i] = -(fixed[i] - 1e-10)
        res = linprog(np.r_[np.zeros(m), -1], A_ub=a, b_ub=b, A_eq=np.r_[np.ones(m), 0].reshape(1, -1), b_eq=[1], bounds=[(0, None)] * m + [(None, None)], method="highs")
        z = res.x[m]
        rhs = np.zeros(n)
        for j in free:
            rhs[j] = -(z - 1e-9)
        for j in fixed:
            rhs[j] = -(fixed[j] - 1e-10)
        stuck = []
        for i in free:
            r2 = linprog(-inc[i], A_ub=-inc, b_ub=rhs, A_eq=np.ones((1, m)), b_eq=[1], bounds=[(0, None)] * m, method="highs")
            if -r2.fun <= z + 1e-7:
                stuck.append(i)
        for i in stuck or [free[0]]:
            fixed[i] = z
    return sorted(fixed.values())


def test_leximin_matches_the_enumeration_of_all_panels():
    rng = random.Random(1)
    compared = infeasible = 0
    for _ in range(40):
        n, k = rng.randint(5, 9), rng.randint(2, 4)
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, rng.choice([0, 1]))
        want = brute_leximin(pool, k, quotas)
        cells, counts, of_person = A.cells_of(pool)
        if want is None:
            infeasible += 1
            assert not A.is_feasible(cells, counts, k, quotas)
            continue
        lot = A.leximin(cells, counts, k, quotas)
        got = sorted(A.person_probabilities(lot["pi"], of_person))
        assert got == pytest.approx(want, abs=1e-6), (pool, k, quotas)
        compared += 1
    assert compared >= 20 and infeasible >= 1                                         # Prüfung nicht leer: zulässige und unzulässige Fälle kommen vor


def test_feasibility_matches_the_enumeration():
    rng = random.Random(2)
    seen = {True: 0, False: 0}
    for _ in range(150):
        n, k = rng.randint(3, 9), rng.randint(1, 4)
        if k > n:
            continue
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, rng.choice([0, 1]))
        cells, counts, _ = A.cells_of(pool)
        feasible = A.is_feasible(cells, counts, k, quotas)
        assert feasible == bool(all_feasible_panels(pool, k, quotas))
        seen[feasible] += 1
    assert seen[True] > 20 and seen[False] > 20


def test_best_vector_matches_the_enumeration_of_all_vectors():
    rng = random.Random(3)
    for _ in range(60):
        n, k = rng.randint(4, 8), rng.randint(2, 4)
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, 1)
        cells, counts, of_person = A.cells_of(pool)
        weights = [rng.random() for _ in cells]
        got = A.best_vector(cells, counts, k, quotas, weights)
        panels = all_feasible_panels(pool, k, quotas)
        if not panels:
            assert got is None
            continue
        best = max(sum(weights[of_person[i]] for i in p) for p in panels)
        assert got[1] == pytest.approx(best, abs=1e-8)


def test_the_lottery_is_a_distribution_over_feasible_panels_and_groups_are_equal():
    rng = random.Random(4)
    for _ in range(25):
        n, k = rng.randint(8, 24), rng.randint(3, 6)
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, 1)
        cells, counts, of_person = A.cells_of(pool)
        if not A.is_feasible(cells, counts, k, quotas):
            continue
        lot = A.leximin(cells, counts, k, quotas)
        assert sum(lot["probs"]) == pytest.approx(1.0) and min(lot["probs"]) > 0
        for vec in lot["panels"]:
            assert sum(vec) == k and all(0 <= x <= counts[c] for c, x in enumerate(vec))
            panel = tuple(i for c, x in enumerate(vec) for i in [j for j, cc in enumerate(of_person) if cc == c][:x])
            assert A.panel_ok(pool, panel, k, quotas)
        person = A.person_probabilities(lot["pi"], of_person)
        assert sum(person) == pytest.approx(k) and max(person) <= 1 + 1e-9
        by_cell = {}
        for i, c in enumerate(of_person):
            by_cell.setdefault(c, set()).add(round(person[i], 12))
        assert all(len(v) == 1 for v in by_cell.values())


def test_leximin_is_lexicographically_at_least_as_good_as_the_exact_greedy_lottery():
    rng = random.Random(5)
    strict = 0
    for _ in range(30):
        n, k = rng.randint(5, 7), rng.randint(2, 3)
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, 1)
        cells, counts, of_person = A.cells_of(pool)
        if not A.is_feasible(cells, counts, k, quotas):
            continue
        try:
            greedy, _ = A.exact_greedy_probabilities(pool, k, quotas)
        except ValueError:
            continue
        lx = sorted(A.person_probabilities(A.leximin(cells, counts, k, quotas)["pi"], of_person))
        simple = sorted(float(x) for x in greedy)
        assert min(lx) >= min(simple) - 1e-8 and min(lx) <= k / n + 1e-9
        assert tuple(round(x, 7) for x in lx) >= tuple(round(x, 7) for x in simple)             # lexikografisch (auf sieben Stellen gerundet)
        strict += min(lx) > min(simple) + 1e-6
    assert strict >= 10


def test_greedy_estimate_matches_the_exact_probabilities():
    rng = random.Random(6)
    checked = 0
    for _ in range(12):
        n, k = 6, 2
        pool = random_pool(rng, n)
        quotas = A.make_quotas(C.SHARES, k, 1)
        try:
            exact, _ = A.exact_greedy_probabilities(pool, k, quotas)
        except ValueError:
            continue
        est, _ = A.greedy_probabilities(pool, k, quotas, 6000, seed=7)
        for e, x in zip(est, exact):
            assert abs(e - float(x)) < 4.5 * np.sqrt(float(x) * (1 - float(x)) / 6000) + 1e-9
        assert sum(exact) == k
        checked += 1
    assert checked >= 8


def test_exact_greedy_probabilities_equal_the_enumeration_of_panel_counts():
    rng = random.Random(8)
    for _ in range(10):
        pool = random_pool(rng, 6)
        quotas = A.make_quotas(C.SHARES, 2, 1)
        counts = {}
        valid = 0
        for order in itertools.permutations(range(6)):
            panel = A.greedy_panel(pool, order, 2, quotas)
            if panel is not None:
                valid += 1
                counts[panel] = counts.get(panel, 0) + 1
        if not valid:
            continue
        probs, v = A.exact_greedy_probabilities(pool, 2, quotas)
        assert v == valid
        for i in range(6):
            assert probs[i] == Fraction(sum(c for p, c in counts.items() if i in p), valid)
        assert all(A.panel_ok(pool, p, 2, quotas) for p in counts)
