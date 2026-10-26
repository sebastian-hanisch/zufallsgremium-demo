"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

from fractions import Fraction

N_MIN, N_MAX, DEFAULT_N = 2, 200, 80            # Freiwillige im Pool
K_MIN, K_MAX, DEFAULT_K = 1, 16, 10             # Sitze im Gremium
BIAS_MIN, BIAS_MAX, DEFAULT_BIAS = 0, 100, 50   # Verzerrung der Meldungen in %
SLACK_MIN, SLACK_MAX, DEFAULT_SLACK = 0, 2, 1   # Spielraum der Quoten (Plätze nach oben und unten)
SEED_MAX, DEFAULT_SEED = 9999, 4
DRAW_MAX, DEFAULT_DRAW = 99, 0                  # Nummer der Beispielziehung
POOL_MAX = N_MAX

# Merkmale: (Schlüssel, Name, Kategorien); Bevölkerungsanteile als Brüche, damit die Quoten exakt gerundet werden
FEATURES = (
    ("geschlecht", "Geschlecht", ("Frauen", "Männer")),
    ("alter", "Alter", ("18–34", "35–54", "55+")),
    ("region", "Region", ("Nord", "Mitte", "Süd")),
)
SHARES = (
    (Fraction(1, 2), Fraction(1, 2)),
    (Fraction(3, 10), Fraction(2, 5), Fraction(3, 10)),
    (Fraction(9, 20), Fraction(7, 20), Fraction(1, 5)),
)
# Wer sich meldet: Faktor 1 + (Verzerrung in %) · Neigung je Kategorie (Frauen, Ältere und der Norden melden sich häufiger)
TILT = ((0.6, -0.6), (-0.8, 0.0, 0.8), (0.7, 0.0, -0.7))

METHODS = {
    "leximin": "Leximin (gleiche Chance, soweit die Quoten es erlauben)",
    "einfach": "Einfaches Ziehen mit Quoten (Schätzung)",
}
METHOD_SHORT = {"leximin": "Leximin", "einfach": "Einfaches Ziehen"}
METHOD_COLORS = {"leximin": "#2F6B65", "einfach": "#b04a3a", "ideal": "#888888"}

GREEDY_DRAWS = 3000          # Ziehungen für die Schätzung des einfachen Ziehens
COLOR_ALERT = "#c0392b"

# Feste Reihen (Zufallspools mit festen Zufalls-Seeds)
SERIES_SEED = 400000
SERIES_RUNS = 10
SERIES_DRAWS = 800
SERIES_BIASES = (0, 30, 60, 90)
SERIES_N = 100
SERIES_SLACKS = (0, 1, 2)
SERIES_SLACK_BIASES = (30, 90)
SERIES_K = 10
GROUP_RUNS = 20

NL = chr(10)


def pool_lines(*rows):
    return NL.join(rows)


PRESETS = {
    "Achtzig Freiwillige, zehn Plätze": {"n": 80, "k": 10, "bias": 50, "slack": 1, "seed": 4, "draw": 0, "pool": ""},
    "Starke Verzerrung": {"n": 100, "k": 12, "bias": 90, "slack": 1, "seed": 4, "draw": 0, "pool": ""},
    "Ohne Verzerrung": {"n": 80, "k": 10, "bias": 0, "slack": 1, "seed": 4, "draw": 0, "pool": ""},
    "Strenge Quoten": {"n": 80, "k": 10, "bias": 50, "slack": 0, "seed": 4, "draw": 0, "pool": ""},
    "Kleiner Pool": {"n": 30, "k": 12, "bias": 50, "slack": 1, "seed": 4, "draw": 0, "pool": ""},
    "Vier Freiwillige, zwei Plätze": {
        "n": 4, "k": 2, "bias": 50, "slack": 0, "seed": 4, "draw": 0,
        "pool": pool_lines("0 0 0", "0 0 1", "1 1 0", "1 2 2"),
    },
}
PRESET_HELP = {
    "Achtzig Freiwillige, zehn Plätze": "Voreinstellung: 80 Freiwillige, zehn Plätze, Quoten für Geschlecht, Alter und Region mit einem Platz Spielraum; Frauen, Ältere und der Norden melden sich häufiger.",
    "Starke Verzerrung": "Die Meldungen sind stark verzerrt (90 %): die kleinste Chance sinkt beim einfachen Ziehen auf 5,8 %, Leximin hält 8,2 % (ideal k/n wären 12,0 %).",
    "Ohne Verzerrung": "Die Freiwilligen spiegeln die Bevölkerung: Leximin erreicht für alle die ideale Chance k/n = 12,5 %; das einfache Ziehen lässt die kleinste Chance trotzdem auf 8,9 % fallen, weil die Quoten die Chancen ungleich machen.",
    "Strenge Quoten": "Ohne Spielraum (genau abgerundet oder aufgerundet) werden die Quoten zur Fessel: die kleinste Leximin-Chance fällt auf 7,9 % (63 % der idealen), das einfache Ziehen liegt bei 6,2 %.",
    "Kleiner Pool": "Nur 30 Freiwillige für zwölf Plätze: manche Gruppen sind so schwach vertreten, dass ihre Mitglieder in jedem zulässigen Gremium sitzen (Chance 100 %); die kleinste Chance liegt bei Leximin bei 35,7 %, beim einfachen Ziehen bei 28,6 %.",
    "Vier Freiwillige, zwei Plätze": "Eine Frau und ein Mann, die sich in Alter und Region unterscheiden: zulässig sind nur drei Paare. Leximin gibt jedem genau die Chance 1/2; beim einfachen Ziehen sind die Chancen ungleich: 3/8 und 5/8 (zwei Personen kommen in zwei zulässigen Paaren vor, zwei nur in einem).",
}
