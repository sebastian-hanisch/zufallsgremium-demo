"""Abbildungen: Aufbau, gesperrte Achsen, Werte an der Hand-Analyse."""

import pytest

import zgr_constants as C
import zgr_evaluation as ev
import zgr_visualization as V


def locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_people_figure_sorts_the_chances_and_marks_the_ideal():
    a = analyse("Vier Freiwillige, zwei Plätze")
    fig = V.build_people(a)
    assert [t.name for t in fig.data] == ["Einfaches Ziehen", "Leximin"]
    assert list(fig.data[1].y) == pytest.approx([0.5] * 4) and list(fig.data[0].y) == sorted(a.simple) and list(fig.data[0].x) == [1, 2, 3, 4]
    assert [s.y0 for s in fig.layout.shapes] == [pytest.approx(0.5)] and fig.data[0].line.shape == "hv" and locked(fig)


def test_group_figure_has_one_value_per_category():
    a = analyse("Vier Freiwillige, zwei Plätze")
    fig = V.build_groups(a)
    assert len(fig.data[0].x) == 8 and list(fig.data[0].x)[:2] == ["Geschlecht: Frauen", "Geschlecht: Männer"]
    assert list(fig.data[1].y)[:2] == pytest.approx([0.5, 0.5]) and fig.data[1].y[3] == pytest.approx(0.5) and fig.layout.barmode == "group" and locked(fig)


def test_group_figure_leaves_empty_categories_blank():
    a = ev.analyse(ev.Settings(k=2, slack=1, pool="\n".join(["0 0 0", "1 0 0", "0 0 0", "1 0 0"])))
    fig = V.build_groups(a)
    labels = list(fig.data[1].x)
    assert fig.data[1].y[labels.index("Alter: 35–54")] is None and fig.data[0].y[labels.index("Alter: 35–54")] is None


def test_gain_series_figure():
    rows = [{"bias": b, "n": 100, "runs": 10, "skipped": 0, "leximin_min": 0.09, "simple_min": 0.06, "ideal": 0.1, "better": 10} for b in C.SERIES_BIASES]
    fig = V.build_gain_series(rows)
    assert [t.name for t in fig.data] == ["Einfaches Ziehen", "Leximin", "ideal k/n"] and list(fig.data[0].x) == ["0 %", "30 %", "60 %", "90 %"]
    assert list(fig.data[0].y) == [0.06] * 4 and list(fig.data[1].y) == [0.09] * 4 and list(fig.data[2].y) == [0.1] * 4 and locked(fig)


def test_slack_series_figure():
    rows = [{"slack": s, "bias": b, "runs": 10, "skipped": 0, "share": 0.5 + 0.1 * s} for s in C.SERIES_SLACKS for b in C.SERIES_SLACK_BIASES]
    fig = V.build_slack_series(rows)
    assert [t.name for t in fig.data] == ["Verzerrung 30 %", "Verzerrung 90 %"] and list(fig.data[0].x) == ["0 Plätze", "1 Plätze", "2 Plätze"]
    assert list(fig.data[0].y) == pytest.approx([0.5, 0.6, 0.7]) and tuple(fig.layout.yaxis.range) == (0, 1.05) and locked(fig)


def test_group_series_figure():
    rows = [{"feature": f, "category": v, "runs": 5, "share": 0.3, "leximin": 0.11, "simple": 0.09, "ideal": 0.1} for f, row in enumerate(C.SHARES) for v in range(len(row))]
    fig = V.build_group_series(rows)
    assert len(fig.data[0].x) == 8 and list(fig.data[0].x)[-1] == "Region: Süd" and list(fig.data[1].y) == [0.11] * 8 and [s.y0 for s in fig.layout.shapes] == [pytest.approx(0.1)] and locked(fig)
