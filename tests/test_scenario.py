"""Szenario: Pool der Freiwilligen, Verzerrung der Meldungen, Texteingabe."""

import numpy as np
import pytest

import zgr_constants as C
import zgr_scenario as S


def test_category_weights_by_hand():
    assert S.category_weights(0, 0) == pytest.approx([0.5, 0.5]) and S.category_weights(1, 0) == pytest.approx([0.3, 0.4, 0.3]) and S.category_weights(2, 0) == pytest.approx([0.45, 0.35, 0.2])
    assert S.category_weights(0, 100) == pytest.approx([0.8, 0.2])                                     # 0,5 · 1,6 und 0,5 · 0,4
    assert S.category_weights(1, 100) == pytest.approx([0.06, 0.4, 0.54])                              # 0,3 · 0,2, 0,4 · 1, 0,3 · 1,8
    assert S.category_weights(2, 100) == pytest.approx([0.765 / 1.175, 0.35 / 1.175, 0.06 / 1.175])
    for f in range(3):
        for bias in (0, 50, 90):
            assert sum(S.category_weights(f, bias)) == pytest.approx(1.0)


def test_pool_is_deterministic_and_has_valid_categories():
    a = S.make_pool(50, 40, 3)
    assert a == S.make_pool(50, 40, 3) and a != S.make_pool(50, 40, 4) and len(a) == 50
    assert all(len(p) == 3 and 0 <= p[0] <= 1 and 0 <= p[1] <= 2 and 0 <= p[2] <= 2 for p in a)


def test_default_pool_by_hand():
    pool = S.make_pool(C.DEFAULT_N, C.DEFAULT_BIAS, C.DEFAULT_SEED)
    assert len(pool) == 80 and pool[:3] == S.make_pool(80, 50, 4)[:3]
    women = sum(1 for p in pool if p[0] == 0)
    assert 40 < women < 70                                                                                # Frauen melden sich häufiger: erwartet etwa 65 %


@pytest.mark.parametrize("bias", [0, 50, 90])
def test_large_pools_follow_the_category_weights(bias):
    pool = S.make_pool(20000, bias, 1)
    for f in range(3):
        freq = np.bincount([p[f] for p in pool], minlength=len(C.SHARES[f])) / len(pool)
        assert freq == pytest.approx(S.category_weights(f, bias), abs=0.015)


def test_features_are_drawn_independently():
    pool = S.make_pool(30000, 60, 2)
    both = sum(1 for p in pool if p[0] == 0 and p[1] == 2) / len(pool)
    w0, w1 = S.category_weights(0, 60)[0], S.category_weights(1, 60)[2]
    assert both == pytest.approx(w0 * w1, abs=0.01)


def test_parse_pool_accepts_every_separator():
    rows, err = S.parse_pool("0 1 2\n1,0,0\n0;2;1\r\n\r\n1 1 1")
    assert err is None and rows == [(0, 1, 2), (1, 0, 0), (0, 2, 1), (1, 1, 1)]


def test_parse_pool_empty_is_no_input_and_no_error():
    assert S.parse_pool("") == (None, None) and S.parse_pool("  \n ") == (None, None) and S.parse_pool(None) == (None, None)


@pytest.mark.parametrize("text,fragment", [
    ("0 0 0", "2 bis 200 Zeilen"),
    ("\n".join(["0 0 0"] * 201), "2 bis 200 Zeilen"),
    ("0 0 0\n0 0", "Zeile 2: Es müssen 3 Ziffern sein (Geschlecht, Alter, Region), eingegeben: 2"),
    ("0 0 0\n0 0 0 0", "Zeile 2: Es müssen 3 Ziffern sein (Geschlecht, Alter, Region), eingegeben: 4"),
    ("0 0 0\n0 x 0", "Zeile 2: „x“ ist keine Ziffer."),
    ("0 0 0\n0 -1 0", "Zeile 2: „-1“ ist keine Ziffer."),
    ("0 0 0\n2 0 0", "Zeile 2: Geschlecht hat nur die Kategorien 0 bis 1 (eingegeben: 2)"),
    ("0 0 0\n0 3 0", "Zeile 2: Alter hat nur die Kategorien 0 bis 2 (eingegeben: 3)"),
    ("0 0 0\n0 0 3", "Zeile 2: Region hat nur die Kategorien 0 bis 2 (eingegeben: 3)"),
])
def test_parse_pool_rejects_bad_input_with_a_message(text, fragment):
    rows, err = S.parse_pool(text)
    assert rows is None and fragment in err


def test_parse_pool_accepts_the_bounds():
    assert S.parse_pool("\n".join(["0 0 0"] * 2))[1] is None and S.parse_pool("\n".join(["1 2 2"] * 200))[1] is None
