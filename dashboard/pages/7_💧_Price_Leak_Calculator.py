"""
Price Leak Finder — where do your ticks go?
Same maths as the FTS Betslip LM-BS09 tool (FTS Confidence Section 4 / LM-BS08):
headroom to the zero-edge price, the gap between tested and taken odds in ticks,
and how much edge each part of the day is costing.
"""
import os as _os
import sys as _sys

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Price Leak Calculator", page_icon="💧", layout="wide")
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
import fts_ui as ui  # noqa: E402

ui.apply_theme()
ui.hero("💧", "Price Leak Calculator",
        "Where do your ticks go? Split the gap between the tested price and the price you got")

# ── Maths (identical to the FTS tool) ────────────────────────────────────────
BANDS = [(1.01, 2, 0.01), (2, 3, 0.02), (3, 4, 0.05), (4, 6, 0.1), (6, 10, 0.2), (10, 20, 0.5),
         (20, 30, 1), (30, 50, 2), (50, 100, 5), (100, 1000, 10)]


def pos(o):
    """Position of a price on the Betfair tick ladder (fractions allowed)."""
    o = min(1000.0, max(1.01, o))
    acc = 0.0
    for a, b, inc in BANDS:
        if o <= b:
            return acc + (o - a) / inc
        acc += (b - a) / inc
    return acc


def break_even(lay, o, c):
    return (o - 1) / ((o - 1) + (1 - c)) if lay else 1 / (1 + (o - 1) * (1 - c))


def roi_stake(lay, p, o, c):
    return p * (1 - c) - (1 - p) * (o - 1) if lay else p * (o - 1) * (1 - c) - (1 - p)


def be_price(lay, p, c):
    return 1 + p * (1 - c) / (1 - p) if lay else 1 + (1 - p) / (p * (1 - c))


def worse_ticks(lay, tested, other):
    return pos(other) - pos(tested) if lay else pos(tested) - pos(other)


def pts(x):
    return ("+" if x >= 0 else "−") + f"{abs(x * 100):.2f}"


def tk(x):
    return "0" if abs(x) < 0.05 else ("−" if x < 0 else "") + f"{abs(x):.1f}"


def odds_s(o):
    return f"{o:.1f}" if o >= 10 else f"{o:.2f}"


def p1(x):
    return ("−" if x < 0 else "") + f"{abs(x):.1f}"


# ── Defaults (the FTS running example: lay the draw at 3.5) ──────────────────
DEFAULTS = dict(pl_kind="I lay", pl_tested=3.50, pl_sr=72.86, pl_comm=2.0, pl_src="No — it was better than any price I could get",
                pl_tt=1, pl_n1=30, pl_o1=3.65, pl_n2=50, pl_o2=3.60, pl_n3=120, pl_o3=3.55)
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

bets = ui.load_bets()

with st.expander("⚡ Pre-fill from one of my systems", expanded=False):
    st.caption("Loads the average odds and strike rate your system was tested at (full history), "
               "and last month's bet count. You then enter the average odds you actually got in each part of the day.")
    a, b, c = st.columns([1.2, 1.6, 1])
    pf_sys = a.selectbox("System", ui.SYSTEM_ORDER, key="pf_sys")
    pf_lg = b.selectbox("League", ["All leagues"] + sorted(bets.loc[bets.system == pf_sys, "league"].unique()), key="pf_lg")
    if c.button("Load", use_container_width=True, type="primary"):
        sd = bets[bets.system == pf_sys]
        if pf_lg != "All leagues":
            sd = sd[sd.league == pf_lg]
        last_m = sd["month"].max()
        n_last = int((sd["month"] == last_m).sum())
        st.session_state.update(
            pl_kind="I lay" if ui.BET_TYPE[pf_sys] == "LAY" else "I back",
            pl_tested=round(float(sd["odds"].mean()), 2), pl_sr=round(float(sd["won"].mean() * 100), 2),
            pl_src="Yes", pl_n1=0, pl_o1=0.0, pl_n2=0, pl_o2=0.0, pl_n3=n_last, pl_o3=round(float(sd["odds"].mean()), 2))
        st.success(f"Loaded {pf_sys} · {pf_lg}: {len(sd):,} bets tested at {sd['odds'].mean():.2f} with "
                   f"{sd['won'].mean() * 100:.1f}% strike rate. Last month ({last_m.strftime('%b %Y')}): {n_last} bets — "
                   "put them in the windows below with the odds you actually took.")
        st.rerun()

with st.expander("ℹ️ How to use this", expanded=False):
    st.markdown(
        "Take last month's bets on **one system** from your record. Group them by when you placed them — "
        "**early**, **middle of the day**, or in the **last hour** before kick-off — and work out the number of bets "
        "and the average odds taken in each group. Leave a group at 0 bets if you never bet then.\n\n"
        "For a lay system, the strike rate is the share of lays that won (the selection did not win). "
        "Ticks are counted on the standard exchange price ladder, so fractions of a tick are normal for an average price.")

left, right = st.columns([1, 1.25], gap="large")

with left:
    ui.section("1 · Your system", "as it was tested, and as your record shows it")
    kind = st.radio("Bet type", ["I back", "I lay"], horizontal=True, key="pl_kind")
    lay = kind == "I lay"
    x1, x2, x3 = st.columns(3)
    tested = x1.number_input("Tested average odds", 1.01, 1000.0, step=0.01, key="pl_tested",
                             help="The average lay price in testing" if lay else "The average price in testing")
    sr = x2.number_input("Strike rate %", 0.1, 99.9, step=0.1, key="pl_sr",
                         help="Share of lays that won (selection lost)" if lay else "Share of bets that won")
    cm = x3.number_input("Commission %", 0.0, 10.0, step=0.5, key="pl_comm", help="On net winnings per market")

    ui.section("2 · Your test price", "could you ever actually have bet at it?")
    src = st.radio("Was the tested price one you could have bet at?",
                   ["Yes", "No — it was better than any price I could get", "Not sure"], key="pl_src",
                   captions=["The right side of the market, at the time I bet.",
                             "e.g. I lay and the test used the back price — at least one tick.",
                             "Treat the whole gap as placing, and add a to-do to find out."])
    test_ticks = 0
    if src.startswith("No"):
        test_ticks = st.radio("How many ticks better than you could get?", [1, 2, 3], horizontal=True,
                              format_func=lambda t: f"{t} tick" + ("s" if t > 1 else ""), key="pl_tt")

    ui.section("3 · Your prices last month", "bets on this system grouped by when you placed them")
    WIN = [("pl_n1", "pl_o1", "Early", "early", "First thing, well before team news"),
           ("pl_n2", "pl_o2", "Middle of the day", "in the middle of the day", "Between early and the last hour"),
           ("pl_n3", "pl_o3", "Last hour", "in the last hour", "From team news to kick-off")]
    for nk, ok, lab, _, hint in WIN:
        w1, w2, w3 = st.columns([1.3, 1, 1])
        w1.markdown(f"**{lab}**<br><span style='color:{ui.MUTED};font-size:0.8rem'>{hint}</span>", unsafe_allow_html=True)
        w2.number_input("Bets", 0, 100000, step=1, key=nk, label_visibility="visible")
        w3.number_input("Average odds taken", 0.0, 1000.0, step=0.01, key=ok)

# ── Calculation ───────────────────────────────────────────────────────────────
errs, wins = [], []
for nk, ok, lab, phrase, _ in WIN:
    n, o = st.session_state[nk], st.session_state[ok]
    if not n or n <= 0:
        continue
    if not (1.01 <= o <= 1000):
        errs.append(f"{lab}: add the average odds taken, or set bets to 0.")
        continue
    wins.append(dict(label=lab, phrase=phrase, n=int(round(n)), o=float(o)))
if not errs and not wins:
    errs.append("Add the bets and average odds for at least one window.")

with right:
    ui.section("Price leak — your result", "", ui.AMBER)
    if errs:
        st.error(" ".join(errs))
        st.stop()

    p, c = sr / 100, cm / 100
    be = break_even(lay, tested, c)
    edge0 = p - be
    roi0 = roi_stake(lay, p, tested, c)
    bp = be_price(lay, p, c)
    hr = worse_ticks(lay, tested, bp)

    total_n = w_tc = w_gap = w_edge = total_lost = 0.0
    worst = None
    rows = []
    for w in wins:
        w["gap"] = worse_ticks(lay, tested, w["o"])
        w["tc"] = min(test_ticks, max(w["gap"], 0)) if test_ticks else 0
        w["placing"] = w["gap"] - w["tc"]
        w["edge"] = p - break_even(lay, w["o"], c)
        w["lost"] = (roi0 - roi_stake(lay, p, w["o"], c)) * w["n"]
        w["placingLost"] = w["lost"] * max(0, min(1, w["placing"] / w["gap"])) if w["gap"] > 0 else 0
        total_n += w["n"]; w_tc += w["tc"] * w["n"]; w_gap += w["gap"] * w["n"]
        w_edge += w["edge"] * w["n"]; total_lost += w["lost"]
        if worst is None or w["placingLost"] > worst["placingLost"]:
            worst = w
        rows.append({"Window": w["label"], "Bets": w["n"], "Odds taken": odds_s(w["o"]), "Gap (ticks)": tk(w["gap"]),
                     "Test price": tk(w["tc"]), "Placing": tk(w["placing"]), "Edge (pts)": pts(w["edge"]),
                     "Points lost": p1(w["lost"]), "_edge": w["edge"]})
    avg_gap, avg_edge, avg_tc = w_gap / total_n, w_edge / total_n, w_tc / total_n
    avg_placing = avg_gap - avg_tc
    test_share = avg_tc / avg_gap if avg_gap > 0 else 0

    # verdict (same rules as the FTS tool)
    if edge0 <= 0:
        tone, verdict = ui.RED, "No edge at the tested price"
        detail = (f"At {odds_s(tested)} with {cm:g}% commission you need {be * 100:.1f}% to break even, and the record "
                  f"shows {sr:.1f}%. The price is not the first problem to look at.")
    elif avg_edge <= 0:
        tone, verdict = ui.RED, "The price gap has taken the whole edge"
        detail = (f"You have {tk(hr)} ticks of headroom and an average gap of {tk(avg_gap)} ticks. At the prices you "
                  f"actually got, the edge is {pts(avg_edge)} points."
                  + (f" {round(test_share * 100)}% of the gap comes from the test price, so re-run the test at a price "
                     "you could have got before changing anything else." if test_ticks else ""))
    elif test_ticks and test_share >= 0.5:
        tone, verdict = ui.AMBER, "Your biggest leak is the test price"
        detail = (f"{round(test_share * 100)}% of your {tk(avg_gap)}-tick gap comes from testing at a price you could "
                  f"never get. No change to your timing will recover it. Re-run the test {test_ticks} "
                  f"{'tick' if test_ticks == 1 else 'ticks'} worse and see what edge is left.")
    elif worst and worst["placingLost"] > 0.5 * total_lost and len(wins) > 1:
        tone, verdict = ui.AMBER, f"Most of the leak is {worst['phrase']}"
        detail = (f"Bets placed {worst['phrase']} cost about {p1(worst['lost'])} of the {p1(total_lost)} points lost to "
                  f"price last month, at an average of {tk(worst['gap'])} ticks worse than tested. That is where to look first.")
    elif avg_gap >= 0.5 * hr:
        tone, verdict = ui.AMBER, "The gap is using most of your edge"
        detail = (f"An average gap of {tk(avg_gap)} ticks against {tk(hr)} ticks of headroom: "
                  f"{round(avg_gap / hr * 100)}% of the edge handed over in price, spread across the day.")
    else:
        tone, verdict = ui.GREEN, ("A small leak" if avg_gap > 0.05 else "No leak to speak of")
        detail = (f"An average gap of {tk(avg_gap)} ticks against {tk(hr)} ticks of headroom. Keep running the check "
                  "monthly; if the gap starts to grow, this is where it will show first.")

    st.markdown(
        f'<div class="fts-banner" style="border-left:5px solid {tone};background:linear-gradient(90deg,{ui.hex_rgba(tone, 0.14)},{ui.SURFACE})">'
        f'<div style="color:{tone};font-size:0.75rem;font-weight:700;letter-spacing:.06em">VERDICT</div>'
        f'<div style="font-size:1.35rem;font-weight:800;margin:4px 0 6px 0">{verdict}</div>'
        f'<div style="color:{ui.TEXT};opacity:.9">{detail}</div></div>', unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    s1.markdown(ui.card("Headroom at tested odds", f"{tk(hr) if edge0 > 0 else '0'} ticks",
                        f"edge reaches zero at {bp:.2f}" if edge0 > 0 and bp >= 10 else
                        (f"edge reaches zero at {bp:.3f}" if edge0 > 0 else "no edge at the tested price"),
                        ui.GREEN if hr >= 2 else ui.AMBER), unsafe_allow_html=True)
    s2.markdown(ui.card("Average price gap", f"{tk(avg_gap)} ticks",
                        f"{tk(avg_tc)} from the test price, {tk(avg_placing)} from placing" if test_ticks else
                        ("test price not yet checked" if src == "Not sure" else "all of it from placing"),
                        ui.AMBER if edge0 > 0 and avg_gap >= 0.5 * hr else ui.ACCENT), unsafe_allow_html=True)
    s3.markdown(ui.card("Edge at the prices you got", f"{pts(avg_edge)} pts", f"against {pts(edge0)} at the tested odds",
                        ui.GREEN if avg_edge > 0 else ui.RED), unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("**Where the gap comes from**")
    tbl = pd.DataFrame(rows)
    st.dataframe(tbl.drop(columns="_edge").style.apply(
        lambda r: [""] * 6 + [f"color:{ui.GREEN if tbl.loc[r.name, '_edge'] > 0 else ui.RED};font-weight:700"] + [""],
        axis=1), use_container_width=True, hide_index=True)
    st.caption(f"Points lost: points of {'backer’s stake' if lay else 'stake'} given up last month compared with "
               f"betting every one at the tested price, at your strike rate. Over these {int(total_n)} bets: about "
               f"{p1(total_lost)} points." + (" Fewer than 60 bets in a month: treat the averages as rough." if total_n < 60 else ""))

    todo = []
    if src == "Not sure":
        todo.append("**Find out what price the test used.** When it was recorded, which side of the market, and where it "
                    "came from. Write it on the system card. If you lay and it was the back price, you are at least a "
                    "tick behind before you start.")
    if test_ticks:
        todo.append(f"**Re-run the test at a price you could have got.** {test_ticks} {'tick' if test_ticks == 1 else 'ticks'} "
                    "worse than the tested odds. If the edge does not survive, pause the system and keep logging it on "
                    "paper. Do not bin it on a bad night.")
    if worst and len(wins) > 1 and worst["placingLost"] > 0:
        todo.append(f"**Look at your {worst['label'].lower()} bets first.** Is that when the system was tested? Is the gap "
                    "between back and lay wider then, or is there less money at your price than your stake?")
    todo.append("**Add one column: took the price, or asked for one.** For the ones you asked for, record whether they "
                "were matched and what the unmatched ones did. Compare strike rates: if the missed bets win more often, "
                "asking is costing you.")
    todo.append("**Run this again next month.** Same system, same windows. The price gap moves months before the results do.")
    st.markdown("**What to do**")
    st.markdown("\n".join(f"{i}. {t}" for i, t in enumerate(todo, 1)))

    with st.expander("Tick ladder reference"):
        st.markdown("| Price range | Tick size |\n|---|---|\n" +
                    "\n".join(f"| {a:g} – {b:g} | {inc:g} |" for a, b, inc in BANDS[:6]))

st.caption("Calculator logic follows the FTS Betslip Episode 9 'Price Leak Finder' (ftsincome.co.uk). "
           "Nothing you enter is stored or sent anywhere.")
