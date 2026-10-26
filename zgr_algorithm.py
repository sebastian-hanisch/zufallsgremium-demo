"""Kern: Zufallsgremium aus Freiwilligen unter Quoten. Eine Person hat je Merkmal eine Kategorie (Tupel von Ziffern); ein Gremium aus k Personen ist zulässig, wenn für jede Kategorie die Zahl der Mitglieder
zwischen ihrer unteren und oberen Quote liegt. Gesucht ist ein LOS (eine Wahrscheinlichkeitsverteilung über zulässige Gremien), das jeder Person eine möglichst gleiche Chance gibt: **Leximin** maximiert die kleinste
Auswahlwahrscheinlichkeit, dann die zweitkleinste usw. (Spaltengenerierung nach Flanigan u. a.).

Personen mit denselben Kategorien (eine „Zelle“) sind austauschbar; das Los wird deshalb auf Zellen gerechnet (ganzzahliger Mengenvektor je Gremium) und danach gleichmäßig auf die Mitglieder der Zelle verteilt.
Die Quoten werden exakt (Brüche) gerundet, die Programme mit HiGHS (scipy) gelöst."""

import math
from fractions import Fraction

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

TOL = 1e-9


def make_quotas(shares, k: int, slack: int) -> dict:
    """Untere und obere Quote je (Merkmal, Kategorie): abgerundeter und aufgerundeter Anteil von k, mit `slack` Plätzen Spielraum (nicht unter 0, nicht über k)."""
    if k < 1 or slack < 0:
        raise ValueError("k ≥ 1 und slack ≥ 0")
    out = {}
    for f, row in enumerate(shares):
        for v, share in enumerate(row):
            exact = Fraction(share) * k
            out[(f, v)] = (max(0, math.floor(exact) - slack), min(k, math.ceil(exact) + slack))
    return out


def cells_of(pool) -> tuple:
    """(Zellen als sortierte Liste der Kategorietupel, Zahl der Personen je Zelle, Zelle je Person)."""
    cells = sorted(set(pool))
    index = {c: i for i, c in enumerate(cells)}
    counts = [0] * len(cells)
    of_person = []
    for p in pool:
        counts[index[p]] += 1
        of_person.append(index[p])
    return cells, counts, of_person


def _constraints(cells, counts, k, quotas):
    nc = len(cells)
    rows = [np.ones((1, nc))]
    lo, hi = [k], [k]
    for (f, v), (a, b) in quotas.items():
        rows.append(np.array([[1.0 if c[f] == v else 0.0 for c in cells]]))
        lo.append(a)
        hi.append(b)
    return LinearConstraint(np.vstack(rows), lo, hi)


def best_vector(cells, counts, k, quotas, weights):
    """Zulässiger Mengenvektor (Mitglieder je Zelle) mit der größten gewichteten Summe; None, wenn es keinen gibt. Gleichstände entscheidet der Löser."""
    nc = len(cells)
    res = milp(-np.array(weights, dtype=float), constraints=[_constraints(cells, counts, k, quotas)], integrality=np.ones(nc), bounds=Bounds(0, counts))
    if res.status != 0:
        return None
    return tuple(int(round(x)) for x in res.x), float(-res.fun)


def is_feasible(cells, counts, k, quotas) -> bool:
    return best_vector(cells, counts, k, quotas, [0.0] * len(cells)) is not None


def _stage(cells, counts, k, quotas, panels, fixed, max_iter=500):
    """Eine Stufe der Spaltengenerierung: größtes z mit π_c ≥ z für alle nicht festgelegten Zellen und π_c ≥ fixed[c] für die festgelegten. Rückgabe (z, p, panels, y) mit den Dualpreisen y je Zelle."""
    nc = len(cells)
    free = [c for c in range(nc) if c not in fixed]
    for it in range(max_iter):
        m = len(panels)
        a_ub = np.zeros((nc, m + 1))
        b_ub = np.zeros(nc)
        for j, vec in enumerate(panels):
            for c in range(nc):
                a_ub[c, j] = -vec[c] / counts[c]
        for c in free:
            a_ub[c, m] = 1.0
        for c in fixed:
            b_ub[c] = -(fixed[c] - 1e-10)
        res = linprog(np.r_[np.zeros(m), -1.0], A_ub=a_ub, b_ub=b_ub, A_eq=np.r_[np.ones(m), 0.0].reshape(1, -1), b_eq=[1.0],
                      bounds=[(0, None)] * m + [(None, None)], method="highs")
        if res.status != 0:
            raise ValueError("Das lineare Programm hat keine Lösung")
        z = float(res.x[m])
        y = -np.asarray(res.ineqlin.marginals)
        mu = float(-res.eqlin.marginals[0]) if hasattr(res, "eqlin") else z
        weights = [y[c] / counts[c] for c in range(nc)]
        found = best_vector(cells, counts, k, quotas, weights)
        if found is None or found[1] <= mu + 1e-8 or found[0] in panels:
            return z, res.x[:m], panels, y
        panels = panels + [found[0]]
    raise RuntimeError("Spaltengenerierung ohne Ende")


def leximin(cells, counts, k, quotas, max_stages=None) -> dict:
    """Das Leximin-Los über Mengenvektoren. Rückgabe: {"panels": [Vektor, …], "probs": [p, …], "pi": [Auswahlwahrscheinlichkeit je Person der Zelle, …], "levels": [z der Stufen]}.
    In jeder Stufe wird die kleinste Wahrscheinlichkeit der noch freien Zellen maximiert; Zellen mit positivem Dualpreis (nicht mehr steigerbar) werden auf diesem Wert festgelegt. Mit `max_stages` bricht die Rechnung nach so vielen Stufen ab (Stufe 1 liefert schon die kleinste Chance; die übrigen Wahrscheinlichkeiten sind dann nicht mehr leximin-optimal)."""
    nc = len(cells)
    rng = np.random.default_rng(0)
    panels = []
    for _ in range(max(10, nc)):
        found = best_vector(cells, counts, k, quotas, rng.random(nc))
        if found is None:
            raise ValueError("Die Quoten lassen kein Gremium zu")
        if found[0] not in panels:
            panels.append(found[0])
    fixed, levels = {}, []
    while len(fixed) < nc and (max_stages is None or len(levels) < max_stages):
        z, p, panels, y = _stage(cells, counts, k, quotas, panels, fixed)
        pi = [sum(p[j] * panels[j][c] / counts[c] for j in range(len(panels))) for c in range(nc)]
        levels.append(z)
        tight = [c for c in range(nc) if c not in fixed and y[c] > 1e-9]
        if not tight:                                   # unerreichbar: die Dualpreise der freien Zellen summieren sich auf 1
            raise RuntimeError("Kein positiver Dualpreis bei freien Zellen")
        for c in tight:
            fixed[c] = pi[c]
    keep = [j for j in range(len(panels)) if p[j] > 1e-9]
    probs = [float(p[j]) for j in keep]
    total = sum(probs)
    return {"panels": [panels[j] for j in keep], "probs": [x / total for x in probs], "pi": [sum(probs[i] / total * panels[j][c] / counts[c] for i, j in enumerate(keep)) for c in range(nc)], "levels": levels, "complete": len(fixed) == nc}


def person_probabilities(pi, of_person) -> list:
    return [pi[c] for c in of_person]


def greedy_panel(pool, order, k, quotas):
    """Einfaches Ziehen: die Personen in der Reihenfolge `order` durchgehen, jede aufnehmen, wenn dadurch keine obere Quote überschritten wird; aufhören bei k Personen. Das Gremium gilt nur, wenn alle unteren Quoten
    erfüllt sind (sonst None: neu ziehen)."""
    count = {key: 0 for key in quotas}
    chosen = []
    for i in order:
        keys = [(f, v) for f, v in enumerate(pool[i])]
        if all(count[key] < quotas[key][1] for key in keys):
            chosen.append(i)
            for key in keys:
                count[key] += 1
            if len(chosen) == k:
                break
    if len(chosen) == k and all(count[key] >= lo for key, (lo, _) in quotas.items()):
        return tuple(sorted(chosen))
    return None


def greedy_probabilities(pool, k, quotas, draws, seed, max_tries=200):
    """Auswahlwahrscheinlichkeiten des einfachen Ziehens, geschätzt aus `draws` gültigen Ziehungen (ungültige Reihenfolgen werden verworfen); Rückgabe (Liste je Person, Zahl der Versuche)."""
    rng = np.random.default_rng(seed)
    n = len(pool)
    counts = np.zeros(n)
    tries = got = 0
    while got < draws and tries < draws * max_tries:
        tries += 1
        panel = greedy_panel(pool, rng.permutation(n), k, quotas)
        if panel is not None:
            got += 1
            for i in panel:
                counts[i] += 1
    if got == 0:
        raise ValueError("Das einfache Ziehen findet kein gültiges Gremium")
    return list(counts / got), tries


def exact_greedy_probabilities(pool, k, quotas):
    """Dieselben Wahrscheinlichkeiten EXAKT durch Aufzählung aller Reihenfolgen (nur für kleine Pools): Anteil der Reihenfolgen mit gültigem Gremium, in denen die Person gewählt wird."""
    import itertools

    n = len(pool)
    counts = [0] * n
    valid = 0
    for order in itertools.permutations(range(n)):
        panel = greedy_panel(pool, order, k, quotas)
        if panel is not None:
            valid += 1
            for i in panel:
                counts[i] += 1
    if valid == 0:
        raise ValueError("Das einfache Ziehen findet kein gültiges Gremium")
    return [Fraction(c, valid) for c in counts], valid


def sample_panel(lottery, cells, of_person, seed):
    """Eine Beispielziehung aus dem Los: erst das Gremium nach seiner Wahrscheinlichkeit, dann je Zelle die Mitglieder gleichmäßig ohne Zurücklegen. Rückgabe die Personennummern, sortiert."""
    rng = np.random.default_rng(seed)
    j = int(rng.choice(len(lottery["panels"]), p=lottery["probs"]))
    vec = lottery["panels"][j]
    chosen = []
    for c, take in enumerate(vec):
        members = [i for i, cc in enumerate(of_person) if cc == c]
        chosen += [int(i) for i in rng.choice(members, size=take, replace=False)]
    return tuple(sorted(chosen))


def panel_ok(pool, panel, k, quotas) -> bool:
    if len(panel) != k or len(set(panel)) != k:
        return False
    for (f, v), (lo, hi) in quotas.items():
        c = sum(1 for i in panel if pool[i][f] == v)
        if not lo <= c <= hi:
            return False
    return True
