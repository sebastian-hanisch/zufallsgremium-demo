"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout. Das Los ist exakt gerechnet (Spaltengenerierung); das einfache Ziehen ist eine Schätzung mit festem Zufalls-Seed."""

import sys
import time

sys.path.insert(0, ".")
import zgr_constants as C
import zgr_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, a.n, a.k, p["bias"], p["slack"])
    print("   ", ev.verdict_state(a))
    for r in ev.group_rows(a):
        print("   ", r)

rows = ev.series_gain()
print("REIHE 1 (kleinste Chance je Verzerrung)")
for r in ev.gain_table(rows):
    print("   ", r)
print("   ", ev.verdict_series_gain(rows))
rows = ev.series_slack()
print("REIHE 2 (Preis der Quoten)")
for r in ev.slack_table(rows):
    print("   ", r)
print("   ", ev.verdict_series_slack(rows))
rows = ev.series_groups()
print("REIHE 3 (Chancen je Kategorie)")
for r in ev.group_table(rows):
    print("   ", r)
print("   ", ev.verdict_series_groups(rows))
print("sec", round(time.time() - t0, 1))
