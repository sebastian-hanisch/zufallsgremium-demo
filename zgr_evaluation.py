"""Auswertung: Einstellungen, Los und einfaches Ziehen, Kennzahlen, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Reihen."""

import math
from dataclasses import dataclass

import numpy as np

import zgr_algorithm as A
import zgr_constants as C
import zgr_scenario as S


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",").replace("-", "−")


def category_name(f: int, v: int) -> str:
    return C.FEATURES[f][2][v]


def person_text(pool, i: int) -> str:
    return f"Person {i + 1} ({', '.join(category_name(f, v) for f, v in enumerate(pool[i]))})"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    k: int = C.DEFAULT_K
    bias: int = C.DEFAULT_BIAS
    slack: int = C.DEFAULT_SLACK
    seed: int = C.DEFAULT_SEED
    draw: int = C.DEFAULT_DRAW
    pool: str = ""


@dataclass
class Analysis:
    settings: Settings
    pool: list
    source: str            # "eingegeben" oder "erzeugt"
    errors: list
    note: str
    n: int
    k: int
    quotas: dict
    cells: list
    counts: list
    of_person: list
    feasible: bool
    lottery: object        # Leximin-Los oder None
    leximin: list          # Auswahlwahrscheinlichkeit je Person
    simple: list           # geschätzte Wahrscheinlichkeit je Person beim einfachen Ziehen
    tries: int             # Versuche des einfachen Ziehens für die gültigen Ziehungen
    ideal: float           # k / n
    demo: tuple            # Beispielziehung: Personennummern


def analyse(settings: Settings) -> Analysis:
    errors, note = [], ""
    rows, err = S.parse_pool(settings.pool)
    if err:
        errors.append("Eigener Pool: " + err + " Die Eingabe wird ignoriert.")
    if rows is not None:
        pool, source = rows, "eingegeben"
    else:
        pool, source = S.make_pool(settings.n, settings.bias, settings.seed), "erzeugt"
    n = len(pool)
    k = settings.k
    if k > n:
        note = f"Der Pool hat nur {n} Personen, gelost wird mit {n} Plätzen statt {k}."
        k = n
    quotas = A.make_quotas(C.SHARES, k, settings.slack)
    cells, counts, of_person = A.cells_of(pool)
    feasible = A.is_feasible(cells, counts, k, quotas)
    base = dict(settings=settings, pool=pool, source=source, errors=errors, note=note, n=n, k=k, quotas=quotas, cells=cells, counts=counts, of_person=of_person, ideal=k / n)
    if not feasible:
        return Analysis(feasible=False, lottery=None, leximin=[], simple=[], tries=0, demo=(), **base)
    lottery = A.leximin(cells, counts, k, quotas)
    leximin = A.person_probabilities(lottery["pi"], of_person)
    try:
        simple, tries = A.greedy_probabilities(pool, k, quotas, C.GREEDY_DRAWS, settings.seed)
    except ValueError:
        simple, tries = [float("nan")] * n, 0
    demo = A.sample_panel(lottery, cells, of_person, settings.seed * 1000 + settings.draw)
    return Analysis(feasible=True, lottery=lottery, leximin=leximin, simple=simple, tries=tries, demo=demo, **base)


# --- Tabellen und Texte ---------------------------------------------------------------------------------------------------------------------

def group_rows(a: Analysis) -> list:
    """Je Kategorie: Anteil im Pool, Quote, mittlere Auswahlwahrscheinlichkeit beim Leximin-Los und beim einfachen Ziehen, jeweils gegen die ideale Chance k/n."""
    rows = []
    for f, (_, fname, cats) in enumerate(C.FEATURES):
        for v, cat in enumerate(cats):
            members = [i for i, p in enumerate(a.pool) if p[f] == v]
            lo, hi = a.quotas[(f, v)]
            row = {"Merkmal": fname, "Kategorie": cat, "im Pool": f"{len(members)} ({pct(len(members) / a.n, 0)})", "Quote": f"{lo} bis {hi} von {a.k}"}
            if members:
                row["Leximin"] = pct(float(np.mean([a.leximin[i] for i in members])))
                row["Einfaches Ziehen"] = pct(float(np.mean([a.simple[i] for i in members])))
            else:
                row["Leximin"] = row["Einfaches Ziehen"] = "–"
            rows.append(row)
    return rows


def lottery_rows(a: Analysis, limit: int = 8) -> list:
    """Die wahrscheinlichsten Gremien des Leximin-Loses als Zahl der Mitglieder je Kategorie."""
    order = sorted(range(len(a.lottery["panels"])), key=lambda j: -a.lottery["probs"][j])[:limit]
    rows = []
    for j in order:
        vec = a.lottery["panels"][j]
        row = {"Wahrscheinlichkeit": pct(a.lottery["probs"][j])}
        for f, (_, fname, cats) in enumerate(C.FEATURES):
            row[fname] = " · ".join(f"{cat} {sum(vec[c] for c, cell in enumerate(a.cells) if cell[f] == v)}" for v, cat in enumerate(cats))
        rows.append(row)
    return rows


def demo_rows(a: Analysis) -> list:
    return [{"Person": f"Person {i + 1}", **{C.FEATURES[f][1]: category_name(f, v) for f, v in enumerate(a.pool[i])}, "Chance (Leximin)": pct(a.leximin[i])} for i in a.demo]


def demo_composition(a: Analysis) -> list:
    """Je Kategorie: Zahl der Mitglieder der Beispielziehung gegen die Quote."""
    out = []
    for f, (_, fname, cats) in enumerate(C.FEATURES):
        for v, cat in enumerate(cats):
            have = sum(1 for i in a.demo if a.pool[i][f] == v)
            lo, hi = a.quotas[(f, v)]
            out.append({"Merkmal": fname, "Kategorie": cat, "im Gremium": have, "Quote": f"{lo} bis {hi}"})
    return out


def lowest_group(a: Analysis, key: str) -> tuple:
    """(Merkmal, Kategorie, mittlere Chance) der Kategorie mit der kleinsten mittleren Chance; key „leximin“ oder „einfach“."""
    probs = a.leximin if key == "leximin" else a.simple
    best = None
    for f, (_, fname, cats) in enumerate(C.FEATURES):
        for v, cat in enumerate(cats):
            members = [i for i, p in enumerate(a.pool) if p[f] == v]
            if members:
                m = float(np.mean([probs[i] for i in members]))
                if best is None or m < best[2]:
                    best = (fname, cat, m)
    return best


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_state(a: Analysis):
    """Kernfrage: wie gleich sind die Chancen? Rückgabe (st-Methode, Text)."""
    low_l, low_s = min(a.leximin), min(a.simple)
    text = (f"Leximin: die kleinste Chance liegt bei {pct(low_l)} (ideal bei Gleichheit: {pct(a.ideal)}, also {pct(low_l / a.ideal, 0)} davon). "
            f"Einfaches Ziehen mit Quoten: die kleinste Chance liegt bei {pct(low_s)}, {pct(1 - low_s / low_l, 0)} unter dem Leximin-Wert.")
    fname, cat, m = lowest_group(a, "einfach")
    text += f" Am schlechtesten stehen beim einfachen Ziehen im Mittel „{cat}“ ({fname}) mit {pct(m)}."
    return ("success" if low_l >= low_s - 1e-9 else "warning"), text


def verdict_series_gain(rows):
    """Reihe 1: wie viel hebt Leximin die kleinste Chance? Rückgabe (st-Methode, Text)."""
    worse = sum(r["better"] for r in rows)
    tot = sum(r["runs"] for r in rows)
    gain = [r["leximin_min"] / r["simple_min"] - 1 for r in rows if r["bias"] > 0]
    text = (f"Über {tot:,} Pools".replace(",", ".") + f" hebt Leximin die kleinste Chance in {worse} gegenüber dem einfachen Ziehen; bei verzerrten Meldungen im Mittel um {pct(min(gain), 0)} bis {pct(max(gain), 0)}. "
            "Die ideale Chance k/n erreicht es nie ganz, weil die Quoten die Auswahl einengen.")
    return "info", text


def verdict_series_slack(rows):
    """Reihe 2: Preis der Quoten. Rückgabe (st-Methode, Text)."""
    zero = [r for r in rows if r["slack"] == 0]
    two = [r for r in rows if r["slack"] == 2]
    text = (f"Ohne Spielraum erreicht die kleinste Chance im Mittel {pct(sum(r['share'] for r in zero) / len(zero), 0)} der idealen k/n, mit zwei Plätzen Spielraum {pct(sum(r['share'] for r in two) / len(two), 0)}: "
            "je enger die Quoten, desto weniger kann das Los angleichen.")
    return "info", text


def verdict_series_groups(rows):
    """Reihe 3: wer gewinnt, wer verliert? Rückgabe (st-Methode, Text)."""
    men = next(r for r in rows if r["feature"] == 0 and r["category"] == 1)
    old = next(r for r in rows if r["feature"] == 1 and r["category"] == 2)
    text = (f"Bei {C.DEFAULT_BIAS} % Verzerrung stellen Männer {pct(men['share'], 0)} des Pools; sie haben beim einfachen Ziehen im Mittel {pct(men['simple'])}, beim Leximin {pct(men['leximin'])} "
            f"(ideal {pct(men['ideal'])}). Die Älteren (55+), im Pool stark vertreten, fallen von {pct(old['ideal'])} (ideal) auf {pct(old['simple'])} beim einfachen Ziehen und {pct(old['leximin'])} beim Leximin.")
    return "info", text


# --- Feste Reihen ---------------------------------------------------------------------------------------------------------------------------

def _instance(n, bias, seed):
    pool = S.make_pool(n, bias, seed)
    cells, counts, of_person = A.cells_of(pool)
    return pool, cells, counts, of_person


def series_gain() -> list:
    """Je Verzerrung: mittlere kleinste Chance bei Leximin (Stufe 1) und einfachem Ziehen, ideale Chance k/n, Zahl der Pools mit Vorteil für Leximin. Pools, in denen die Quoten kein Gremium zulassen, zählen als ausgelassen."""
    rows = []
    k, n = C.SERIES_K, C.SERIES_N
    for bi, bias in enumerate(C.SERIES_BIASES):
        lx, sm, better, skipped = [], [], 0, 0
        for run in range(C.SERIES_RUNS):
            seed = C.SERIES_SEED + 1000 * bi + run
            pool, cells, counts, of_person = _instance(n, bias, seed)
            quotas = A.make_quotas(C.SHARES, k, C.DEFAULT_SLACK)
            if not A.is_feasible(cells, counts, k, quotas):
                skipped += 1
                continue
            lot = A.leximin(cells, counts, k, quotas, max_stages=1)
            simple, _ = A.greedy_probabilities(pool, k, quotas, C.SERIES_DRAWS, seed)
            lx.append(min(lot["pi"]))
            sm.append(min(simple))
            better += min(lot["pi"]) > min(simple) + 1e-9
        rows.append({"bias": bias, "n": n, "runs": len(lx), "skipped": skipped, "leximin_min": float(np.mean(lx)), "simple_min": float(np.mean(sm)), "ideal": k / n, "better": better})
    return rows


def series_slack() -> list:
    """Je Spielraum der Quoten und Verzerrung: kleinste Leximin-Chance im Verhältnis zur idealen k/n (Mittel über die Pools mit 100 Freiwilligen, Pools ohne zulässiges Gremium ausgelassen)."""
    rows = []
    k, n = C.SERIES_K, C.SERIES_N
    for si, slack in enumerate(C.SERIES_SLACKS):
        for bi, bias in enumerate(C.SERIES_SLACK_BIASES):
            shares, skipped = [], 0
            for run in range(C.SERIES_RUNS):
                seed = C.SERIES_SEED + 100000 + 10000 * si + 1000 * bi + run
                pool, cells, counts, of_person = _instance(n, bias, seed)
                quotas = A.make_quotas(C.SHARES, k, slack)
                if not A.is_feasible(cells, counts, k, quotas):
                    skipped += 1
                    continue
                shares.append(min(A.leximin(cells, counts, k, quotas, max_stages=1)["pi"]) / (k / n))
            rows.append({"slack": slack, "bias": bias, "runs": len(shares), "skipped": skipped, "share": float(np.mean(shares))})
    return rows


def series_groups() -> list:
    """Je Kategorie bei der Standard-Verzerrung (Pools mit 100 Freiwilligen): Anteil im Pool, mittlere Chance bei Leximin und einfachem Ziehen und ideale Chance (Mittel über die Pools)."""
    k, n = C.SERIES_K, 100
    acc = {}
    for run in range(C.GROUP_RUNS):
        seed = C.SERIES_SEED + 200000 + run
        pool, cells, counts, of_person = _instance(n, C.DEFAULT_BIAS, seed)
        quotas = A.make_quotas(C.SHARES, k, C.DEFAULT_SLACK)
        if not A.is_feasible(cells, counts, k, quotas):
            continue
        lot = A.leximin(cells, counts, k, quotas)
        lx = A.person_probabilities(lot["pi"], of_person)
        simple, _ = A.greedy_probabilities(pool, k, quotas, C.SERIES_DRAWS, seed)
        for f, (_, _, cats) in enumerate(C.FEATURES):
            for v in range(len(cats)):
                members = [i for i, p in enumerate(pool) if p[f] == v]
                if members:
                    a = acc.setdefault((f, v), {"share": [], "leximin": [], "simple": []})
                    a["share"].append(len(members) / n)
                    a["leximin"].append(float(np.mean([lx[i] for i in members])))
                    a["simple"].append(float(np.mean([simple[i] for i in members])))
    return [{"feature": f, "category": v, "runs": len(a["share"]), "share": float(np.mean(a["share"])), "leximin": float(np.mean(a["leximin"])), "simple": float(np.mean(a["simple"])), "ideal": k / n}
            for (f, v), a in sorted(acc.items())]


def gain_table(rows) -> list:
    return [{"Verzerrung": f"{r['bias']} %", "Freiwillige": r["n"], "Pools": f"{r['runs']} (ausgelassen: {r['skipped']})", "ideal k/n": pct(r["ideal"]), "Leximin: kleinste Chance": pct(r["leximin_min"]), "Einfaches Ziehen: kleinste Chance": pct(r["simple_min"]),
             "Leximin besser in": f"{r['better']} von {r['runs']}"} for r in rows]


def slack_table(rows) -> list:
    return [{"Spielraum": f"{r['slack']} Plätze", "Verzerrung": f"{r['bias']} %", "Pools": f"{r['runs']} (ausgelassen: {r['skipped']})", "kleinste Chance im Verhältnis zu k/n": pct(r["share"], 0)} for r in rows]


def group_table(rows) -> list:
    return [{"Merkmal": C.FEATURES[r["feature"]][1], "Kategorie": C.FEATURES[r["feature"]][2][r["category"]], "Anteil im Pool": pct(r["share"], 0), "ideal k/n": pct(r["ideal"]),
             "Einfaches Ziehen": pct(r["simple"]), "Leximin": pct(r["leximin"])} for r in rows]
