"""Randfälle: Extremwerte der Regler, Invarianten jeder Analyse, kleine und unzulässige Pools, Adresszeile und eigener Pool."""

import itertools
import os

import pytest
from streamlit.testing.v1 import AppTest

import zgr_algorithm as A
import zgr_constants as C
import zgr_evaluation as ev

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
GRID = list(itertools.product((20, 60), (C.K_MIN, 6, C.K_MAX), (C.BIAS_MIN, 50, C.BIAS_MAX), (C.SLACK_MIN, 1, C.SLACK_MAX)))


@pytest.mark.parametrize("n,k,bias,slack", GRID)
def test_invariants_at_the_extremes(n, k, bias, slack):
    a = ev.analyse(ev.Settings(n=n, k=k, bias=bias, slack=slack, seed=3))
    assert a.n == n and a.k == min(k, n) and a.errors == [] and a.ideal == pytest.approx(a.k / n)
    if not a.feasible:
        assert a.lottery is None and not A.is_feasible(a.cells, a.counts, a.k, a.quotas)
        return
    assert sum(a.leximin) == pytest.approx(a.k) and len(a.leximin) == n and 0 <= min(a.leximin) <= a.ideal + 1e-9 and max(a.leximin) <= 1 + 1e-9
    assert sum(a.lottery["probs"]) == pytest.approx(1.0) and min(a.leximin) >= 0
    assert A.panel_ok(a.pool, a.demo, a.k, a.quotas) and len(set(a.demo)) == a.k
    if a.tries:
        assert sum(a.simple) == pytest.approx(a.k) and min(a.simple) <= a.ideal + 1e-9 and min(a.leximin) >= min(a.simple) - 0.02
    assert len(ev.group_rows(a)) == 8 and len(ev.lottery_rows(a)) >= 1
    if a.tries:
        assert ev.verdict_state(a)[1]


def test_one_seat_is_a_simple_lottery_with_quotas_of_zero_or_one():
    a = ev.analyse(ev.Settings(n=30, k=1, bias=50, slack=1, seed=2))
    assert a.feasible and sum(a.leximin) == pytest.approx(1.0) and len(a.demo) == 1


def test_pool_as_large_as_the_panel_gives_everyone_chance_one():
    a = ev.analyse(ev.Settings(k=4, slack=2, pool="\n".join(["0 0 0", "1 1 1", "0 1 2", "1 0 1"])))
    assert a.feasible and a.leximin == pytest.approx([1.0] * 4) and a.demo == (0, 1, 2, 3)


def test_unbiased_big_pool_reaches_the_ideal_for_everyone_with_enough_slack():
    a = ev.analyse(ev.Settings(n=120, k=10, bias=0, slack=2, seed=1))
    assert min(a.leximin) == pytest.approx(a.ideal, abs=1e-6)


def test_identical_people_share_the_chance_equally():
    a = ev.analyse(ev.Settings(k=2, slack=2, pool="\n".join(["0 0 0"] * 4 + ["1 1 1"] * 4)))
    assert a.leximin == pytest.approx([0.25] * 8, abs=1e-8)                                      # acht Personen, zwei Plätze: jeder 1/4


# --- App: Adresszeile und eigener Pool -----------------------------------------------------------------------------------------------------------

def _run(**params):
    at = AppTest.from_file(APP, default_timeout=180)
    for key, value in params.items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_with_a_pool_fills_the_text_area_and_disables_the_generator():
    at = _run(pool="0 0 0\n0 0 1\n1 1 0\n1 2 2", k="2", slack="0")
    assert at.sidebar.text_area(key="pool_text").value.count("\n") == 3
    assert at.sidebar.slider(key="n_slider").proto.disabled and at.sidebar.slider(key="bias_slider").proto.disabled and at.sidebar.number_input(key="seed_input").proto.disabled
    assert at.metric[0].value == "50,0 %" and at.metric[1].value == "37,0 %"


def test_permalink_values_are_clamped_and_bad_values_ignored():
    at = _run(n="9999", k="x", bias="-5", slack="7", seed="-3", draw="1000")
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.slider(key="k_slider").value == C.DEFAULT_K
    assert at.sidebar.slider(key="bias_slider").value == C.BIAS_MIN and at.sidebar.slider(key="slack_slider").value == C.SLACK_MAX
    assert at.sidebar.number_input(key="seed_input").value == 0 and at.sidebar.number_input(key="draw_input").value == C.DRAW_MAX


def test_bad_pool_shows_a_warning_and_the_app_still_runs():
    at = _run(pool="0 0 0\n0 0 7")
    assert any("Eigener Pool" in w.value for w in at.warning) and not at.sidebar.slider(key="n_slider").proto.disabled


def test_infeasible_pool_shows_an_error_and_stops():
    at = _run(pool="\n".join(["0 0 0"] * 4), k="2", slack="0")
    assert any("kein Gremium" in e.value for e in at.error) and not at.metric


def test_k_larger_than_the_pool_shows_a_note():
    at = _run(pool="0 0 0\n1 1 1\n0 1 2", k="8", slack="2")
    assert any("Der Pool hat nur 3 Personen" in i.value for i in at.info)


def test_a_different_example_draw_changes_nothing_but_the_draw():
    first = _run(draw="0")
    second = _run(draw="1")
    assert first.metric[0].value == second.metric[0].value and first.metric[1].value == second.metric[1].value


def test_changing_the_sliders_keeps_the_app_running():
    at = _run()
    for key, value in (("k_slider", 1), ("k_slider", 16), ("n_slider", 20), ("bias_slider", 100), ("slack_slider", 0)):
        at.sidebar.slider(key=key).set_value(value).run()
        assert not at.exception
