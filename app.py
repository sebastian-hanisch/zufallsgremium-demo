"""Zufallsgremium: gleiche Chance trotz Quoten - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Gelber Kandidat der Linie „Abstimmen und Fair Teilen“: aus freiwilligen Meldungen wird ein Gremium gelost, das Quoten für Geschlecht, Alter und Region erfüllt. Gesucht ist ein LOS über zulässige Gremien, das jeder Person eine
möglichst gleiche Chance gibt (Leximin, Spaltengenerierung); verglichen wird mit dem einfachen Ziehen mit Quoten. Der Kern liegt in zgr_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import zgr_constants as C
import zgr_evaluation as ev
from zgr_evaluation import Settings, analyse, num
from zgr_layout import dunkles_design, kopf_css
from zgr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zgr_scenario import parse_pool
from zgr_visualization import build_gain_series, build_group_series, build_groups, build_people, build_slack_series

st.set_page_config(page_title="Zufallsgremium – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_gain():
    return ev.series_gain()


@st.cache_data(show_spinner=False)
def _series_slack():
    return ev.series_slack()


@st.cache_data(show_spinner=False)
def _series_groups():
    return ev.series_groups()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zgr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎲 Zufallsgremium: gleiche Chance trotz Quoten")
st.markdown(
    """
Ein Verein lost ein **Gremium aus Freiwilligen**. Das Gremium soll die Mitglieder **abbilden** (Quoten für Geschlecht, Alter und Region), aber es melden sich nicht alle Gruppen gleich häufig. Wer zu einer gut vertretenen Gruppe gehört, hat beim **einfachen Ziehen mit Quoten** eine deutlich kleinere Chance als die anderen.
Die Demo sucht ein **Los**: eine Wahrscheinlichkeitsverteilung über **alle zulässigen Gremien**, die jeder Person **möglichst die gleiche Chance** gibt, ins Gremium zu kommen. **Leximin** maximiert die kleinste Chance, dann die zweitkleinste und so weiter; gerechnet wird per **Spaltengenerierung** (lineares Programm über die Gremien, das Preisproblem ist ein ganzzahliges Programm).
Verwandt: `column-generation-demo` (dasselbe Rechenverfahren am Cutting-Stock-Problem), `unteilbare-gueter-demo` (Leximin als Regel für Güter) und `gemeinsames-budget-demo` (proportionale Vertretung bei Projekten).

Weiter unten: die **Kernfrage**, der Abschnitt **🔬 Feste Reihen** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
1. **Pool und Quoten.** Jede Person hat ein Geschlecht (2), eine Altersgruppe (3) und eine Region (3). Für jede Kategorie gilt eine Quote: der Bevölkerungsanteil mal Plätze, abgerundet und aufgerundet, plus der eingestellte Spielraum. **Zulässig** ist jedes Gremium aus k Personen, das alle Quoten einhält.
2. **Einfaches Ziehen** (Schätzung): die Personen werden in zufälliger Reihenfolge durchgegangen, jede kommt hinein, solange keine obere Quote überschritten wird; erfüllt das Ergebnis nicht alle unteren Quoten, wird neu gezogen. Die Chancen werden aus 3.000 gültigen Ziehungen geschätzt.
3. **Leximin.** Gesucht ist ein Los p über zulässige Gremien. Die Chance einer Person ist die Summe der Wahrscheinlichkeiten der Gremien, in denen sie sitzt. Stufe 1 maximiert die **kleinste** Chance; wer dann nicht mehr besser gestellt werden kann, wird festgelegt, und die nächste Stufe maximiert die kleinste Chance der übrigen. Personen mit denselben Merkmalen sind austauschbar und bekommen dieselbe Chance, deshalb wird auf diesen **Gruppen** gerechnet.
4. **Spaltengenerierung.** Das lineare Programm hat sehr viele Gremien als Spalten. Es startet mit wenigen und fügt jeweils das Gremium hinzu, das zu den Dualpreisen am meisten bringt (ein ganzzahliges Programm über die Zahl der Personen je Gruppe), bis keines mehr hilft.
5. **Ziehung.** Aus dem Los wird erst ein Gremium nach seiner Wahrscheinlichkeit gewählt, dann je Gruppe die Mitglieder gleichmäßig.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

_pool_valid, _ = parse_pool(st.session_state["pool_text"])
custom = _pool_valid is not None
with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Gremium**")
    k = st.slider("Plätze im Gremium", *bounds("k_slider"), key="k_slider", help="Wie viele Personen gelost werden (höchstens so viele, wie sich gemeldet haben).")
    slack = st.slider("Spielraum der Quoten (Plätze)", *bounds("slack_slider"), key="slack_slider", help="Wie viele Plätze eine Kategorie über oder unter ihrem Bevölkerungsanteil liegen darf. 0 = genau abgerundet oder aufgerundet.")
    st.markdown("**Freiwillige**")
    n = st.slider("Zahl der Freiwilligen", *bounds("n_slider"), key="n_slider", disabled=custom, help="Wie viele Personen sich gemeldet haben. Bei einem eigenen Pool bestimmt die Zahl der Zeilen den Wert.")
    bias = st.slider("Verzerrung der Meldungen (%)", *bounds("bias_slider"), key="bias_slider", disabled=custom, help="Wie stark sich Frauen, Ältere und der Norden häufiger melden. 0 = die Freiwilligen spiegeln die Bevölkerung.")
    seed = st.number_input("Zufalls-Seed des Pools", *bounds("seed_input"), key="seed_input", step=1, disabled=custom)
    st.button("🎲 Neuen Pool erzeugen", width="stretch", on_click=randomize_seed, disabled=custom)
    draw = st.number_input("Nummer der Beispielziehung", *bounds("draw_input"), key="draw_input", step=1, help="Jede Nummer ist eine andere Ziehung aus demselben Los.")
    st.markdown("**Eigener Pool (optional)**")
    pool_text = st.text_area("Eine Person je Zeile", key="pool_text", height=110, placeholder="Geschlecht Alter Region als Ziffern, z. B.\n0 0 0\n1 2 1",
                             help="Je Zeile drei Ziffern: Geschlecht (0 Frauen, 1 Männer), Alter (0 18–34, 1 35–54, 2 55+), Region (0 Nord, 1 Mitte, 2 Süd), getrennt durch Leerzeichen oder Komma. Leer lassen, um den Pool erzeugen zu lassen.")

sync_query_params({"n_slider": int(n), "k_slider": int(k), "bias_slider": int(bias), "slack_slider": int(slack), "seed_input": int(seed), "draw_input": int(draw), "pool_text": pool_text})

settings = Settings(n=int(n), k=int(k), bias=int(bias), slack=int(slack), seed=int(seed), draw=int(draw), pool=pool_text)
with st.spinner("Rechne das Los …"):
    a = _analysis(settings)
for message in a.errors:
    st.warning(message)
if a.note:
    st.info(a.note)
if not a.feasible:
    st.error(f"Mit diesem Pool ({a.n} Freiwillige) und {a.k} Plätzen gibt es kein Gremium, das alle Quoten erfüllt: manche Kategorie ist zu schwach vertreten. Mehr Spielraum, weniger Plätze oder ein größerer Pool helfen.")
    st.stop()

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

low_l, low_s = min(a.leximin), min(a.simple)
st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric("Kleinste Chance (Leximin)", ev.pct(low_l), delta=f"ideal k/n = {ev.pct(a.ideal)}: {ev.pct(low_l / a.ideal, 0)} davon", delta_color="off")
m2.metric("Kleinste Chance (einfaches Ziehen)", ev.pct(low_s), delta=f"{ev.pct(1 - low_s / low_l, 0)} unter Leximin", delta_color="off")
m3.metric("Gremien im Los", f"{len(a.lottery['panels'])}", delta=f"{len(a.cells)} Gruppen, {len(a.lottery['levels'])} Stufen", delta_color="off")
if a.source == "eingegeben":
    st.caption(f"Der eigene Pool bestimmt die Zahl der Freiwilligen ({a.n}); Verzerrung und Zufalls-Seed haben keine Wirkung.")
st.markdown("**Chancen je Person**")
st.plotly_chart(build_people(a), width="stretch", key="people_chart")
st.caption("Jede Person ist ein Punkt der Linie (von der kleinsten zur größten Chance). Leximin hebt das untere Ende; beim einfachen Ziehen liegt es deutlich tiefer.")
st.markdown("**Chancen je Gruppe**")
st.plotly_chart(build_groups(a), width="stretch", key="groups_chart")
st.table(ev.group_rows(a))
with st.expander("Das Los: die wahrscheinlichsten Gremien"):
    st.table(ev.lottery_rows(a))
st.markdown(f"**Beispielziehung Nr. {a.settings.draw}** (aus dem Leximin-Los)")
st.table(ev.demo_composition(a))
st.table(ev.demo_rows(a))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie gleich kann man die Chancen machen?")
kind, text = ev.verdict_state(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Reihen --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Feste Reihen")
st.caption(
    f"Feste Programme, unabhängig von den Reglern: je Zeile {C.SERIES_RUNS} Zufallspools mit festen Zufalls-Seeds ({C.SERIES_N} Freiwillige, {C.SERIES_K} Plätze); das Los ist exakt gerechnet (Spaltengenerierung, HiGHS), "
    "das einfache Ziehen aus je 800 gültigen Ziehungen geschätzt. Jede Reihe rechnet auf Klick bis zu einer Minute."
)
tab1, tab2, tab3 = st.tabs(["Wie viel hebt Leximin?", "Was kosten die Quoten?", "Wer gewinnt, wer verliert?"])
with tab1:
    st.markdown("**Kleinste Chance je Verzerrung.** Die kleinste Auswahlwahrscheinlichkeit bei Leximin (Stufe 1) und beim einfachen Ziehen, gegen die ideale Chance k/n; in wie vielen Pools Leximin besser ist.")
    if st.button("Reihe rechnen", key="gain_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_gain()
        st.session_state["gain_done"] = time.perf_counter() - t0
    if "gain_done" in st.session_state:
        rows = _series_gain()
        st.plotly_chart(build_gain_series(rows), width="stretch", key="gain_chart")
        st.table(ev.gain_table(rows))
        kind, text = ev.verdict_series_gain(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['gain_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown("**Preis der Quoten.** Die kleinste Leximin-Chance im Verhältnis zur idealen k/n bei Spielraum 0, 1 und 2 Plätzen und zwei Stärken der Verzerrung: engere Quoten lassen weniger Raum für gleiche Chancen.")
    if st.button("Reihe rechnen", key="slack_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_slack()
        st.session_state["slack_done"] = time.perf_counter() - t0
    if "slack_done" in st.session_state:
        rows = _series_slack()
        st.plotly_chart(build_slack_series(rows), width="stretch", key="slack_chart")
        st.table(ev.slack_table(rows))
        kind, text = ev.verdict_series_slack(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['slack_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown(f"**Chancen je Kategorie** bei {C.DEFAULT_BIAS} % Verzerrung (Mittel über {C.GROUP_RUNS} Pools): wer sich seltener meldet, wird beim einfachen Ziehen bevorzugt, wer sich häufiger meldet, benachteiligt; Leximin gleicht das teilweise aus.")
    if st.button("Reihe rechnen", key="groups_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_groups()
        st.session_state["groups_done"] = time.perf_counter() - t0
    if "groups_done" in st.session_state:
        rows = _series_groups()
        st.plotly_chart(build_group_series(rows), width="stretch", key="group_series_chart")
        st.table(ev.group_table(rows))
        kind, text = ev.verdict_series_groups(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['groups_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Gleiche Chance ist das Ziel** | Wer andere Ziele hat (zum Beispiel die Abbildung der Bevölkerung im Mittel über viele Lose), bewertet das Los anders; Leximin sagt nichts über die Qualität eines einzelnen Gremiums. | – |
| **Wenige Merkmale, feste Quoten** | Die Quoten gelten je Merkmal einzeln, nicht für Kombinationen (junge Männer im Norden); mit vielen Merkmalen wird die Zahl der Gruppen groß, und manche Pools lassen kein zulässiges Gremium zu. | diese Demo (Reihe „Was kosten die Quoten?“) |
| **Die Merkmale sind bekannt und ehrlich** | Die Demo glaubt die Angaben der Freiwilligen. | – |
| **Das einfache Ziehen ist eine Schätzung** | Die Chancen kommen aus 3.000 Ziehungen und schwanken um etwa einen halben Prozentpunkt; echte Verfahren der Praxis sind komplizierter. | diese Demo (Gegenprobe durch Aufzählung bei kleinen Pools) |
| **Personen derselben Gruppe sind austauschbar** | Das gilt hier, weil nur die Merkmale zählen; bei weiteren Unterschieden (Vorlieben, Verfügbarkeit) müsste auf Personen gerechnet werden. | – |
| **Modell, kein Befund über Bürgerräte** | Die Zahlen sagen, was die Rechnung für erzeugte oder eingegebene Pools liefert, nicht, wie ein bestimmter Verein losen sollte. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gremien und Los.** $\mathcal{P}$ ist die Menge der zulässigen Gremien $P \subseteq N$ mit $|P| = k$ und $\ell_{f,v} \le |\{i \in P : \text{Merkmal } f \text{ von } i = v\}| \le u_{f,v}$ für alle Kategorien. Ein Los ist eine Verteilung $(p_P)_{P \in \mathcal{P}}$; die Chance von Person $i$ ist $\pi_i = \sum_{P \ni i} p_P$.

**Leximin.** Stufe 1: $\max z$ unter $\pi_i \ge z$ für alle $i$ und $\sum_P p_P = 1$. Danach werden Personen, deren Chance nicht mehr steigerbar ist (positiver Dualpreis), auf ihrem Wert festgelegt, und die nächste Stufe maximiert die kleinste Chance der übrigen; so entsteht der lexikografisch größte sortierte Chancenvektor.

**Spaltengenerierung.** Zu den Dualpreisen $y_i$ des Master-Programms ist das Preisproblem $\max_{P \in \mathcal{P}} \sum_{i \in P} y_i$ (ganzzahlig); ein Gremium mit Wert über dem Dualpreis der Summenbedingung verbessert das Los und wird als neue Spalte aufgenommen. Weil Personen derselben Gruppe austauschbar sind, rechnet die Demo mit der Zahl der Mitglieder je Gruppe.

**Ideal.** Wären alle Chancen gleich, wäre jede $k/n$; die Quoten und die verzerrten Meldungen machen das meist unmöglich.

**Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Flanigan, Gölz, Gupta, Hennig, Procaccia, „Fair algorithms for selecting citizens’ assemblies“, Nature 2021; Gilmore und Gomory (1961) zur Spaltengenerierung.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
