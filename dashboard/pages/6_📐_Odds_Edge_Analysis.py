"""
Odds Edge Analysis
Average odds taken vs market-implied win probability vs actual results —
per system, per league, per season and per month.
"""
import os as _os
import sys as _sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Odds Edge Analysis", page_icon="📐", layout="wide")
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
import fts_ui as ui  # noqa: E402

ui.apply_theme()
ui.hero("📐", "Odds Edge Analysis",
        "Is the edge real? Actual strike rate vs the win rate the odds implied — by league, season and month")

bets = ui.load_bets()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    inc_btd = st.toggle("Include the 4 test systems", value=False)
    sys_opts = ui.SYSTEM_ORDER if inc_btd else ui.LIVE_SYSTEMS
    sel_sys = st.multiselect("Systems", sys_opts, default=sys_opts)
    seasons = sorted(bets["season"].unique())
    sel_seasons = st.multiselect("Seasons", seasons, default=seasons)
    comm = st.number_input("Exchange commission %", 0.0, 10.0, 2.0, 0.5,
                           help="Used for the break-even strike rate (same maths as the Price Leak Calculator)") / 100
    min_n = st.slider("Grey out cells with fewer than … bets", 1, 30, 10)

df = bets[bets["system"].isin(sel_sys) & bets["season"].isin(sel_seasons)].copy()
if df.empty:
    st.warning("No bets match the filters.")
    st.stop()

lay = df["bet_type"].eq("LAY")
o = df["odds"]
df["implied"] = np.where(lay, 1 - 1 / o, 1 / o)
df["breakeven"] = np.where(lay, (o - 1) / ((o - 1) + (1 - comm)), 1 / (1 + (o - 1) * (1 - comm)))


def edge_table(d: pd.DataFrame, by) -> pd.DataFrame:
    g = d.groupby(by, observed=True).agg(
        Bets=("pl", "size"), AvgOdds=("odds", "mean"), Implied=("implied", "mean"),
        BreakEven=("breakeven", "mean"), Actual=("won", "mean"), PL=("pl", "sum")).reset_index()
    g["Implied"] *= 100
    g["BreakEven"] *= 100
    g["Actual"] *= 100
    g["Edge"] = g["Actual"] - g["Implied"]
    g["EdgeComm"] = g["Actual"] - g["BreakEven"]
    g["ROI"] = g["PL"] / g["Bets"] * 100
    return g


NICE = {"AvgOdds": "Avg Odds", "Implied": "Implied Win %", "BreakEven": "Break-even %",
        "Actual": "Actual Win %", "Edge": "Edge (pp)", "EdgeComm": "Edge after comm (pp)",
        "PL": "P/L", "ROI": "ROI %"}
FMT = {"Avg Odds": "{:.2f}", "Implied Win %": "{:.1f}%", "Break-even %": "{:.1f}%", "Actual Win %": "{:.1f}%",
       "Edge (pp)": "{:+.2f}", "Edge after comm (pp)": "{:+.2f}", "P/L": "{:+.2f}", "ROI %": "{:+.2f}%",
       "Bets": "{:.0f}"}
MEASURES = {"Edge (pp)": "Edge", "Edge after comm (pp)": "EdgeComm", "Actual Win %": "Actual",
            "ROI %": "ROI", "P/L": "PL", "Avg Odds": "AvgOdds", "Bets": "Bets"}


def styled(t: pd.DataFrame, height=None):
    sty = (t.style.format({k: v for k, v in FMT.items() if k in t.columns})
           .map(lambda v: ui.heat_style(v, 12), subset=[c for c in ["Edge (pp)", "Edge after comm (pp)"] if c in t.columns])
           .map(ui.pl_style, subset=[c for c in ["P/L", "ROI %"] if c in t.columns]))
    if "System" in t.columns:
        sty = sty.map(ui.system_style, subset=["System"])
    kw = {"height": height} if height else {}
    return st.dataframe(sty, use_container_width=True, hide_index=True, **kw)


def heatmap(pv: pd.DataFrame, counts: pd.DataFrame, measure: str, title: str = ""):
    z = pv.values.astype(float)
    n = counts.reindex(index=pv.index, columns=pv.columns).values
    f = FMT.get(measure, "{:.2f}")
    text = [["" if np.isnan(v) else f.format(v) + (f" ({int(c)})" if measure != "Bets" and not np.isnan(c) else "")
             for v, c in zip(rz, rn)] for rz, rn in zip(z, n)]
    zc = np.where(np.nan_to_num(n, nan=0) < min_n, np.nan, z)  # thin samples left uncoloured
    signed = measure in ("Edge (pp)", "Edge after comm (pp)", "ROI %", "P/L")
    if signed:
        lim = np.nanpercentile(np.abs(zc), 90) if np.isfinite(zc).any() else 1
        lim = lim or 1
        cs, zmin, zmax = [[0, ui.RED], [0.5, ui.SURFACE_2], [1, ui.GREEN]], -lim, lim
    else:
        cs, zmin, zmax = [[0, ui.SURFACE_2], [1, ui.ACCENT]], None, None
    fig = go.Figure(go.Heatmap(z=zc, x=[str(c) for c in pv.columns], y=list(pv.index), text=text,
                               texttemplate="%{text}", textfont=dict(color=ui.TEXT, size=11), colorscale=cs, zmin=zmin, zmax=zmax,
                               showscale=False, xgap=3, ygap=3, hovertemplate="%{y} · %{x}<br>%{text} bets<extra></extra>"))
    fig.add_trace(go.Heatmap(z=np.where(np.isnan(zc) & ~np.isnan(z), 0, np.nan), x=[str(c) for c in pv.columns],
                             y=list(pv.index), colorscale=[[0, "rgba(143,163,191,0.10)"], [1, "rgba(143,163,191,0.10)"]],
                             showscale=False, xgap=3, ygap=3, hoverinfo="skip"))
    fig.data = (fig.data[1], fig.data[0])
    fig.update_layout(height=80 + 42 * len(pv), yaxis=dict(autorange="reversed", showgrid=False, type="category"),
                      xaxis=dict(side="top", showgrid=False, type="category"),
                      title=dict(text=title, font=dict(size=13)), margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)


# ── KPIs ──────────────────────────────────────────────────────────────────────
ov = edge_table(df, ["system", "league"])
tot = edge_table(df.assign(all="all"), "all").iloc[0]
weak = ov.loc[ov["Edge"].idxmin()]
c = st.columns(5)
c[0].markdown(ui.card("League-system combos", f"{len(ov)}", f"{len(df):,} bets"), unsafe_allow_html=True)
c[1].markdown(ui.card("Positive edge", f"{(ov['Edge'] > 0).sum()} / {len(ov)}",
                      "all leagues beating the odds" if (ov["Edge"] > 0).all() else "some leagues below the odds",
                      ui.GREEN if (ov["Edge"] > 0).all() else ui.AMBER), unsafe_allow_html=True)
c[2].markdown(ui.card("Portfolio edge", f"{tot['Edge']:+.2f}pp", f"actual {tot['Actual']:.1f}% vs implied {tot['Implied']:.1f}%",
                      ui.ACCENT), unsafe_allow_html=True)
c[3].markdown(ui.card("Edge after commission", f"{tot['EdgeComm']:+.2f}pp", f"vs break-even at {comm:.0%} commission",
                      ui.GREEN if tot["EdgeComm"] > 0 else ui.RED), unsafe_allow_html=True)
c[4].markdown(ui.card("Weakest", f"{weak['Edge']:+.2f}pp", f"{weak['system']} · {weak['league']}",
                      ui.AMBER), unsafe_allow_html=True)
st.write("")

tab_ov, tab_season, tab_month = st.tabs(["📋 Overview", "📆 Season by season", "🗓️ Month by month"])

# ── Overview ──────────────────────────────────────────────────────────────────
with tab_ov:
    t = ov.rename(columns={"system": "System", "league": "League", **NICE}).sort_values("Edge (pp)", ascending=False)
    t = t[["System", "League", "Bets", "Avg Odds", "Implied Win %", "Break-even %", "Actual Win %",
           "Edge (pp)", "Edge after comm (pp)", "P/L", "ROI %"]]
    styled(t, height=min(620, 40 + 35 * len(t)))
    st.download_button("⬇ Download table (CSV)", t.to_csv(index=False).encode(), "odds_edge_overview.csv")

    ss = ov.sort_values("Edge")
    fig = go.Figure(go.Bar(
        x=ss["Edge"], y=ss["league"] + " · " + ss["system"], orientation="h",
        marker_color=[ui.SYSTEM_COLORS[s] for s in ss["system"]],
        text=[f"{v:+.2f}pp" for v in ss["Edge"]], textposition="outside",
        customdata=np.c_[ss["Bets"], ss["Actual"], ss["Implied"]],
        hovertemplate="%{y}<br>Edge %{x:+.2f}pp<br>%{customdata[0]} bets · actual %{customdata[1]:.1f}% "
                      "vs implied %{customdata[2]:.1f}%<extra></extra>"))
    fig.add_vline(x=0, line_color="rgba(230,237,247,0.35)")
    fig.update_layout(height=max(380, 26 * len(ss)), xaxis_title="Edge (percentage points)",
                      title=dict(text="Edge by league", font=dict(size=13)), margin=dict(l=10, r=60, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ── Season by season ─────────────────────────────────────────────────────────
with tab_season:
    a, b = st.columns([2, 1])
    s_sys = a.radio("System", sel_sys, horizontal=True, key="ses_sys")
    s_meas = b.selectbox("Show", list(MEASURES), key="ses_meas")
    sd = df[df["system"] == s_sys]
    st_ = edge_table(sd, ["league", "season"])
    col = MEASURES[s_meas]
    pv = st_.pivot(index="league", columns="season", values=col)
    cnt = st_.pivot(index="league", columns="season", values="Bets")
    tl = edge_table(sd, "league").set_index("league")
    pv["All seasons"] = tl[col]
    cnt["All seasons"] = tl["Bets"]
    tsn = edge_table(sd, "season").set_index("season")
    pv.loc["ALL LEAGUES"] = list(tsn[col].reindex(pv.columns[:-1])) + [edge_table(sd.assign(a=1), "a")[col].iloc[0]]
    cnt.loc["ALL LEAGUES"] = list(tsn["Bets"].reindex(cnt.columns[:-1])) + [len(sd)]
    heatmap(pv, cnt, s_meas, f"{s_sys} — {s_meas} by league and season")

    ui.section("Season trend", "edge per season for each league", ui.SYSTEM_COLORS[s_sys])
    fl = go.Figure()
    for lg_, g in st_.groupby("league"):
        g = g[g["Bets"] >= min_n]
        fl.add_trace(go.Scatter(x=g["season"], y=g[col], mode="lines+markers", name=lg_,
                                customdata=g["Bets"], hovertemplate=f"{lg_}<br>%{{x}}: %{{y:.2f}} (%{{customdata}} bets)<extra></extra>"))
    fl.add_trace(go.Scatter(x=tsn.index, y=tsn[col], mode="lines+markers", name="ALL LEAGUES",
                            line=dict(color=ui.TEXT, width=3, dash="dot")))
    if col in ("Edge", "EdgeComm", "ROI", "PL"):
        fl.add_hline(y=0, line_color="rgba(230,237,247,0.3)")
    fl.update_layout(height=380, yaxis_title=s_meas, legend=dict(orientation="h", y=-0.2),
                     xaxis=dict(type="category"))
    st.plotly_chart(fl, use_container_width=True)

    with st.expander("Full season table (every system, league and season)"):
        full = edge_table(df, ["system", "league", "season"]).rename(
            columns={"system": "System", "league": "League", "season": "Season", **NICE})
        full = full[["System", "League", "Season", "Bets", "Avg Odds", "Implied Win %", "Actual Win %",
                     "Edge (pp)", "Edge after comm (pp)", "P/L", "ROI %"]]
        styled(full, height=520)
        st.download_button("⬇ Download (CSV)", full.to_csv(index=False).encode(), "odds_edge_by_season.csv")

# ── Month by month ───────────────────────────────────────────────────────────
with tab_month:
    a, b, c3 = st.columns([2, 1, 1])
    m_sys = a.radio("System", sel_sys, horizontal=True, key="mon_sys")
    m_meas = b.selectbox("Show", list(MEASURES), key="mon_meas")
    md = df[df["system"] == m_sys]
    months_all = sorted(md["month"].unique())
    span = c3.selectbox("Months shown", ["Last 12", "Last 24", "All"], key="mon_span")
    keep = months_all if span == "All" else months_all[-int(span.split()[1]):]
    mdk = md[md["month"].isin(keep)]
    mt = edge_table(mdk, ["league", "month"])
    col = MEASURES[m_meas]
    pv = mt.pivot(index="league", columns="month", values=col)
    cnt = mt.pivot(index="league", columns="month", values="Bets")
    tm = edge_table(mdk, "month").set_index("month")
    pv.loc["ALL LEAGUES"] = tm[col].reindex(pv.columns)
    cnt.loc["ALL LEAGUES"] = tm["Bets"].reindex(cnt.columns)
    pv.columns = [p.strftime("%b %y") for p in pv.columns]
    cnt.columns = pv.columns
    heatmap(pv, cnt, m_meas, f"{m_sys} — {m_meas} by league and month")
    st.caption(f"Monthly samples are small — cells with fewer than {min_n} bets are left uncoloured. "
               "Use the drill-down below for a rolling view that smooths the noise.")

    ui.section("League drill-down", "monthly odds vs results for one league", ui.SYSTEM_COLORS[m_sys])
    l1, l2 = st.columns([2, 1])
    lg_pick = l1.selectbox("League", ["All leagues"] + sorted(md["league"].unique()), key="mon_lg")
    roll = l2.slider("Rolling window (months)", 1, 12, 6, key="mon_roll")
    ld = md if lg_pick == "All leagues" else md[md["league"] == lg_pick]
    lm = edge_table(ld, "month").sort_values("month")
    # rolling = pooled over the window (bets-weighted), not an average of monthly averages
    agg = ld.groupby("month").agg(n=("pl", "size"), w=("won", "sum"), imp=("implied", "sum"), pl=("pl", "sum")).sort_index()
    r = agg.rolling(roll, min_periods=1).sum()
    lm = lm.set_index("month")
    lm["Roll Actual"] = r["w"] / r["n"] * 100
    lm["Roll Implied"] = r["imp"] / r["n"] * 100
    lm["Roll Edge"] = lm["Roll Actual"] - lm["Roll Implied"]
    lm = lm.reset_index()
    x = lm["month"].dt.to_timestamp()
    fg = go.Figure()
    fg.add_trace(go.Bar(x=x, y=lm["Bets"], name="Bets", marker_color="rgba(143,163,191,0.25)", yaxis="y2"))
    fg.add_trace(go.Scatter(x=x, y=lm["Roll Actual"], name=f"Actual win % ({roll}m rolling)",
                            line=dict(color=ui.SYSTEM_COLORS[m_sys], width=3)))
    fg.add_trace(go.Scatter(x=x, y=lm["Roll Implied"], name=f"Implied win % ({roll}m rolling)",
                            line=dict(color=ui.MUTED, width=2, dash="dash")))
    fg.update_layout(height=360, hovermode="x unified", yaxis=dict(title="Win %"),
                     yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Bets"),
                     legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fg, use_container_width=True)

    show = lm.sort_values("month", ascending=False).assign(Month=lambda d: d["month"].dt.strftime("%b %Y"))
    show = show.rename(columns={**NICE, "Roll Edge": f"Rolling {roll}m edge (pp)"})
    show = show[["Month", "Bets", "Avg Odds", "Implied Win %", "Actual Win %", "Edge (pp)",
                 f"Rolling {roll}m edge (pp)", "P/L", "ROI %"]]
    FMT[f"Rolling {roll}m edge (pp)"] = "{:+.2f}"
    styled(show, height=420)
    st.download_button("⬇ Download (CSV)", show.to_csv(index=False).encode(),
                       f"odds_edge_monthly_{m_sys}_{lg_pick}.csv".replace(" ", "_"))

st.caption("Edge = actual win rate minus the win rate implied by the odds taken. LAY bets: implied win % = 1 − 1/odds. "
           "BACK bets: implied win % = 1/odds. Edge after commission compares against the break-even strike rate "
           "once exchange commission is deducted from winnings.")
