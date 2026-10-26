"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import zgr_constants as C
import zgr_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.28), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _category_labels():
    return [f"{fname}: {cat}" for _, fname, cats in C.FEATURES for cat in cats]


def build_people(a):
    """Auswahlwahrscheinlichkeit jeder Person, aufsteigend sortiert: Leximin hebt das untere Ende, die gestrichelte Linie ist die ideale Chance k/n."""
    fig = go.Figure()
    for key, name, values in (("einfach", C.METHOD_SHORT["einfach"], sorted(a.simple)), ("leximin", C.METHOD_SHORT["leximin"], sorted(a.leximin))):
        fig.add_trace(go.Scatter(x=list(range(1, a.n + 1)), y=values, mode="lines", name=name, line=dict(color=C.METHOD_COLORS[key], width=3, shape="hv"),
                                 hovertemplate="Rang %{x}: %{y:.1%}<extra>" + name + "</extra>"))
    fig.add_hline(y=a.ideal, line_color=C.METHOD_COLORS["ideal"], line_dash="dash", annotation_text=f"ideal k/n = {ev.pct(a.ideal)}", annotation_position="top left")
    fig.update_xaxes(title_text="Personen, nach Chance sortiert")
    fig.update_yaxes(title_text="Chance, ins Gremium zu kommen", tickformat=".0%", rangemode="tozero")
    return _base(fig, height=340)


def build_groups(a):
    """Mittlere Chance je Kategorie bei Leximin und einfachem Ziehen, mit der idealen Chance k/n als Linie."""
    labels, lx, sm = [], [], []
    for f, (_, fname, cats) in enumerate(C.FEATURES):
        for v, cat in enumerate(cats):
            members = [i for i, p in enumerate(a.pool) if p[f] == v]
            labels.append(f"{fname}: {cat}")
            lx.append(sum(a.leximin[i] for i in members) / len(members) if members else None)
            sm.append(sum(a.simple[i] for i in members) / len(members) if members else None)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=sm, name=C.METHOD_SHORT["einfach"], marker_color=C.METHOD_COLORS["einfach"], hovertemplate="%{x}: %{y:.1%}<extra>Einfaches Ziehen</extra>"))
    fig.add_trace(go.Bar(x=labels, y=lx, name=C.METHOD_SHORT["leximin"], marker_color=C.METHOD_COLORS["leximin"], hovertemplate="%{x}: %{y:.1%}<extra>Leximin</extra>"))
    fig.add_hline(y=a.ideal, line_color=C.METHOD_COLORS["ideal"], line_dash="dash", annotation_text="ideal k/n", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Mittlere Chance", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=360)


def build_gain_series(rows):
    """Kleinste Chance bei Leximin und einfachem Ziehen je Verzerrung; die Raute ist die ideale Chance k/n."""
    xs = [f"{r['bias']} %" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["simple_min"] for r in rows], name=C.METHOD_SHORT["einfach"], marker_color=C.METHOD_COLORS["einfach"], hovertemplate="%{x}: %{y:.1%}<extra>Einfaches Ziehen</extra>"))
    fig.add_trace(go.Bar(x=xs, y=[r["leximin_min"] for r in rows], name=C.METHOD_SHORT["leximin"], marker_color=C.METHOD_COLORS["leximin"], hovertemplate="%{x}: %{y:.1%}<extra>Leximin</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["ideal"] for r in rows], mode="markers", name="ideal k/n", marker=dict(symbol="diamond", size=11, color="#222", line=dict(color="white", width=1))))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Kleinste Chance (Mittel)", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(title_text="Verzerrung der Meldungen", type="category")
    return _base(fig, height=340)


def build_slack_series(rows):
    """Kleinste Leximin-Chance im Verhältnis zur idealen je Spielraum der Quoten, eine Linie je Verzerrung."""
    fig = go.Figure()
    colors = {30: "#4c78a8", 90: "#b04a3a"}
    for bias in C.SERIES_SLACK_BIASES:
        sel = [r for r in rows if r["bias"] == bias]
        fig.add_trace(go.Scatter(x=[f"{r['slack']} Plätze" for r in sel], y=[r["share"] for r in sel], mode="lines+markers", name=f"Verzerrung {bias} %", line=dict(color=colors.get(bias, "#888"), width=2.5),
                                 hovertemplate="%{x}: %{y:.0%} der idealen Chance<extra>" + f"{bias} %" + "</extra>"))
    fig.update_yaxes(title_text="Kleinste Chance im Verhältnis zu k/n", tickformat=".0%", range=[0, 1.05])
    fig.update_xaxes(title_text="Spielraum der Quoten", type="category")
    return _base(fig, height=320)


def build_group_series(rows):
    """Mittlere Chance je Kategorie (Mittel über die Pools) bei einfachem Ziehen und Leximin, mit der idealen Chance als Linie."""
    labels = [f"{C.FEATURES[r['feature']][1]}: {C.FEATURES[r['feature']][2][r['category']]}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[r["simple"] for r in rows], name=C.METHOD_SHORT["einfach"], marker_color=C.METHOD_COLORS["einfach"], hovertemplate="%{x}: %{y:.1%}<extra>Einfaches Ziehen</extra>"))
    fig.add_trace(go.Bar(x=labels, y=[r["leximin"] for r in rows], name=C.METHOD_SHORT["leximin"], marker_color=C.METHOD_COLORS["leximin"], hovertemplate="%{x}: %{y:.1%}<extra>Leximin</extra>"))
    fig.add_hline(y=rows[0]["ideal"], line_color=C.METHOD_COLORS["ideal"], line_dash="dash", annotation_text="ideal k/n", annotation_position="top left")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Mittlere Chance", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=340)
