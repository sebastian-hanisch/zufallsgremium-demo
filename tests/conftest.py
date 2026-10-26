"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import zgr_algorithm as A  # noqa: E402
import zgr_constants as C  # noqa: E402


@pytest.fixture
def mini():
    """Vier Freiwillige (Geschlecht, Alter, Region): a = (0, 0, 0), b = (0, 0, 1), c = (1, 1, 0), d = (1, 2, 2); zwei Plätze, Spielraum 0, also genau eine Frau und ein Mann, je Alter und je Region höchstens einer.
    Zulässige Paare (Personen 0 bis 3): (a, d), (b, c), (b, d); (a, b) hat zwei Frauen, (a, c) zweimal Region 0, (c, d) zwei Männer.
    Leximin: p(a,d) = p(b,c) = 1/2 gibt jedem die Chance 1/2. Einfaches Ziehen (alle 24 Reihenfolgen): a 3/8, b 5/8, c 3/8, d 5/8."""
    pool = [(0, 0, 0), (0, 0, 1), (1, 1, 0), (1, 2, 2)]
    return pool, 2, A.make_quotas(C.SHARES, 2, 0)
