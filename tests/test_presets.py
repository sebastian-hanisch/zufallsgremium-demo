"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, keines auf einem Rand der Regler, keines durch eine einzelne Regleränderung vom Standard;
die Aussagen der Hilfetexte stimmen mit der Rechnung überein."""

from fractions import Fraction as F

import pytest

import zgr_algorithm as A
import zgr_constants as C
import zgr_evaluation as ev
import zgr_presets as P
import zgr_scenario as S

FIRST = "Achtzig Freiwillige, zehn Plätze"
BOUNDS = {"n": (C.N_MIN, C.N_MAX), "k": (C.K_MIN, C.K_MAX), "bias": (C.BIAS_MIN, C.BIAS_MAX), "slack": (C.SLACK_MIN, C.SLACK_MAX), "seed": (0, C.SEED_MAX), "draw": (0, C.DRAW_MAX)}


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds():
    for name, p in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert lo <= p[key] <= hi, (name, key)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[FIRST]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_preset_sits_on_a_bound_of_n_k_or_bias():
    for name, preset in C.PRESETS.items():
        for key in ("n", "k", "bias"):
            lo, hi = BOUNDS[key]
            assert preset[key] not in (lo, hi) or (key, name) == ("bias", "Ohne Verzerrung"), (name, key)       # „Ohne Verzerrung“ ist der Fall bias = 0 selbst


def test_no_single_change_of_the_default_produces_another_preset():
    default = C.PRESETS[FIRST]
    for name, p in C.PRESETS.items():
        if name == FIRST:
            continue
        diff = sum(1 for k in p if p[k] != default[k])
        assert diff >= 2 or name in ("Ohne Verzerrung", "Strenge Quoten"), name          # diese beiden sind je ein benannter Grenzfall des Reglers (Verzerrung 0, Spielraum 0)


def test_presets_are_pairwise_different():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_presets_with_a_pool_have_matching_n():
    for name, p in C.PRESETS.items():
        rows, err = S.parse_pool(p["pool"])
        assert err is None, name
        if rows is not None:
            assert p["n"] == len(rows), name


def test_presets_are_feasible_and_have_no_errors():
    for name in C.PRESETS:
        a = analyse(name)
        assert a.feasible and a.errors == [] and a.note == "", name


# --- Aussagen der Hilfetexte ---------------------------------------------------------------------------------------------------------------

def test_default_preset_help():
    a = analyse(FIRST)
    assert a.n == 80 and a.k == 10 and ev.pct(min(a.leximin)) == "10,5 %" and ev.pct(min(a.simple)) == "9,2 %"


def test_strong_bias_preset_help():
    a = analyse("Starke Verzerrung")
    assert ev.pct(min(a.leximin)) == "8,2 %" and ev.pct(min(a.simple)) == "6,7 %" and ev.pct(a.ideal) == "12,0 %"


def test_no_bias_preset_help():
    a = analyse("Ohne Verzerrung")
    assert all(x == pytest.approx(0.125, abs=1e-8) for x in a.leximin) and ev.pct(min(a.simple)) == "9,1 %"


def test_strict_quotas_preset_help():
    a = analyse("Strenge Quoten")
    assert ev.pct(min(a.leximin)) == "7,9 %" and ev.pct(min(a.leximin) / a.ideal, 0) == "63 %" and ev.pct(min(a.simple)) == "7,3 %"


def test_small_pool_preset_help():
    a = analyse("Kleiner Pool")
    assert max(a.leximin) == pytest.approx(1.0, abs=1e-8) and ev.pct(min(a.leximin)) == "35,7 %" and ev.pct(min(a.simple)) == "30,5 %"


def test_four_person_preset_help():
    a = analyse("Vier Freiwillige, zwei Plätze")
    assert a.leximin == pytest.approx([0.5] * 4, abs=1e-8)
    exact, _ = A.exact_greedy_probabilities(a.pool, a.k, a.quotas)
    assert exact == [F(3, 8), F(5, 8), F(3, 8), F(5, 8)] and "3/8 und 5/8" in C.PRESET_HELP["Vier Freiwillige, zwei Plätze"]
