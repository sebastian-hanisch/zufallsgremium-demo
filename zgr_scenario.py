"""Szenario: Pool der Freiwilligen (erzeugt oder eingegeben). Deterministisch aus (Zahl, Verzerrung, Zufalls-Seed)."""

import re

import numpy as np

import zgr_constants as C


def category_weights(feature: int, bias: int) -> list:
    """Wie wahrscheinlich sich jemand der Kategorien meldet: Bevölkerungsanteil mal (1 + Verzerrung · Neigung), auf 1 normiert."""
    raw = [float(share) * (1 + bias / 100 * tilt) for share, tilt in zip(C.SHARES[feature], C.TILT[feature])]
    total = sum(raw)
    return [x / total for x in raw]


def make_pool(n: int, bias: int, seed: int) -> list:
    """n Freiwillige als Tupel (Geschlecht, Alter, Region) mit den Ziffern der Kategorien; die Merkmale werden unabhängig gezogen."""
    rng = np.random.default_rng(seed)
    columns = [rng.choice(len(C.SHARES[f]), size=n, p=category_weights(f, bias)) for f in range(len(C.FEATURES))]
    return [tuple(int(col[i]) for col in columns) for i in range(n)]


def parse_pool(text: str):
    """Eingabe: eine Zeile je Person mit drei Ziffern (Geschlecht 0–1, Alter 0–2, Region 0–2), getrennt durch Leerzeichen, Komma oder Semikolon. Rückgabe (Pool oder None, Fehlermeldung oder None); leerer Text: (None, None)."""
    text = (text or "").strip()
    if not text:
        return None, None
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    if not C.N_MIN <= len(lines) <= C.POOL_MAX:
        return None, f"Es müssen {C.N_MIN} bis {C.POOL_MAX} Zeilen sein, eine je Person (eingegeben: {len(lines)})."
    pool = []
    for k, line in enumerate(lines, start=1):
        parts = [t for t in re.split(r"[,;\s]+", line) if t]
        if len(parts) != len(C.FEATURES):
            return None, f"Zeile {k}: Es müssen {len(C.FEATURES)} Ziffern sein (Geschlecht, Alter, Region), eingegeben: {len(parts)}."
        row = []
        for f, t in enumerate(parts):
            if not re.fullmatch(r"\d+", t):
                return None, f"Zeile {k}: „{t}“ ist keine Ziffer."
            if int(t) >= len(C.SHARES[f]):
                return None, f"Zeile {k}: {C.FEATURES[f][1]} hat nur die Kategorien 0 bis {len(C.SHARES[f]) - 1} (eingegeben: {t})."
            row.append(int(t))
        pool.append(tuple(row))
    return pool, None
