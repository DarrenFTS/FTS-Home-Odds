"""Page 7: Monte Carlo Simulation — FTS Home Odds Portfolio"""
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import SIDEBAR_CSS, sidebar_brand, G_PANEL, G_MID, G_ACCENT, G_TEST, G_BUF, G_LIVE

st.set_page_config(page_title="Monte Carlo", page_icon="🎲", layout="wide")
sidebar_brand()

# ── Load portfolio data ────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "portfolio_data.json")

@st.cache_data
def load_portfolio():
    with open(DATA_PATH) as f:
        return json.load(f)

PORT = load_portfolio()

LIVE_SYSTEMS = {k for k, v in PORT.items() if v.get("live", False)}
SYS_COLORS = {
    "Lay U1.5":      "#2ecc71",
    "Lay O3.5":      "#1abc9c",
    "Back FHG O1.5": "#16a085",
    "Lay FHG U0.5":  "#27ae60",
    "Home Lay":      "#1e8449",
    "Away Lay":      "#145a32",
    "Draw Lay":      "#0e6655",
}

# ── Monte Carlo engine ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def run_mc(sys_name: str, horizon: int, n_sims: int = 5000, bank: float = 100.0,
           ruin_threshold: float = 20.0, seed: int = 42):
    """Bootstrap resample from historical monthly P&L data to simulate future paths."""
    data = PORT[sys_name]
    # Reconstruct approximate per-bet distribution from historical data
    # Use season P&L and bets to derive per-bet returns distribution
    seasons = data.get("seasons", [])
    if not seasons:
        return None

    # Build per-bet avg and std from historical data
    total_pl   = data["total_pl"]
    total_bets = data["total_bets"]
    win_rate   = data["win_rate"] / 100.0
    avg_bet    = total_pl / total_bets

    # Reconstruct per-bet P&L array from monthly data
    monthly_pl  = data.get("monthly_cum_pl", [])
    if len(monthly_pl) >= 2:
        diffs = [monthly_pl[0]] + [monthly_pl[i] - monthly_pl[i-1] for i in range(1, len(monthly_pl))]
    else:
        diffs = [avg_bet]

    # Scale diffs to per-bet by dividing by approximate bets per month
    approx_bets_pm = max(total_bets / max(len(diffs), 1), 1)
    per_bet_approx = [d / approx_bets_pm for d in diffs if abs(d) < 500]

    # If we don't have enough data, synthesise from win rate + avg
    # Using a simplified two-outcome model: wins return ~+0.97u, losses vary
    np.random.seed(seed)
    if len(per_bet_approx) < 20:
        # Synthetic: typical lay bet win = ~+stake, loss = -liability
        # We derive from avg and win_rate: avg = wr*win_amt + (1-wr)*loss_amt
        # Assume win_amt = 0.97 (lay at ~2.0), solve for loss_amt
        win_amt  = 0.97
        loss_amt = (avg_bet - win_rate * win_amt) / (1 - win_rate) if (1 - win_rate) > 0 else -2.0
        bets_arr = np.where(
            np.random.random((n_sims * horizon,)) < win_rate,
            win_amt, loss_amt
        ).reshape(n_sims, horizon)
    else:
        bets_arr = np.random.choice(per_bet_approx, size=(n_sims, horizon), replace=True)

    # Compute paths
    cum       = np.cumsum(bets_arr, axis=1)
    bank_path = bank + cum
    terminal  = cum[:, -1]

    # Drawdown from peak
    pk     = np.maximum.accumulate(cum, axis=1)
    dd_all = (cum - pk).min(axis=1)

    # Ruin
    pct_ruin   = (bank_path < ruin_threshold).any(axis=1).mean() * 100
    pct_profit = (terminal > 0).mean() * 100

    # Losing runs (sample 1000)
    idx  = np.random.choice(n_sims, min(1000, n_sims), replace=False)
    llrs = []
    for i in idx:
        mx = cr = 0
        for v in bets_arr[i]:
            if v < 0: cr += 1; mx = max(mx, cr)
            else: cr = 0
        llrs.append(mx)
    llrs = np.array(llrs)

    # Histogram
    edges = list(range(-300, 801, 25))
    hist, _ = np.histogram(terminal, bins=edges)
    hist_pct = (hist / n_sims * 100).tolist()

    return {
        "n_sims":      n_sims,
        "horizon":     horizon,
        "bank":        bank,
        "ruin_thresh": ruin_threshold,
        "win_rate":    round(win_rate * 100, 1),
        "avg_bet":     round(avg_bet, 4),
        "pl_mean":     round(float(terminal.mean()), 2),
        "pl_p5":       round(float(np.percentile(terminal,  5)), 2),
        "pl_p25":      round(float(np.percentile(terminal, 25)), 2),
        "pl_p50":      round(float(np.percentile(terminal, 50)), 2),
        "pl_p75":      round(float(np.percentile(terminal, 75)), 2),
        "pl_p95":      round(float(np.percentile(terminal, 95)), 2),
        "pct_profit":  round(pct_profit, 1),
        "pct_ruin":    round(pct_ruin, 2),
        "dd_med":      round(float(np.median(dd_all)), 2),
        "dd_p5":       round(float(np.percentile(dd_all, 5)), 2),
        "dd_pct_med":  round(float(abs(np.median(dd_all)) / bank * 100), 1),
        "dd_pct_p5":   round(float(abs(np.percentile(dd_all, 5)) / bank * 100), 1),
        "llr_med":     int(np.median(llrs)),
        "llr_p75":     int(np.percentile(llrs, 75)),
        "llr_p90":     int(np.percentile(llrs, 90)),
        "llr_p95":     int(np.percentile(llrs, 95)),
        "llr_max":     int(llrs.max()),
        "hist_edges":  edges[:-1],
        "hist_pct":    [round(v, 2) for v in hist_pct],
        "terminal":    terminal,
        "dd_all":      dd_all,
        "cum_paths":   cum[:50],   # store 50 paths for fan chart
    }


# ── Page header ────────────────────────────────────────────────────────────────
st.title("🎲 Monte Carlo Simulation")
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid {G_ACCENT};'
    f'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:0.85rem;color:#b2dfdb">'
    f'Bootstrap resampling from historical bet returns &nbsp;·&nbsp; '
    f'5,000 simulations per run &nbsp;·&nbsp; Starting bank: <strong>100u</strong> &nbsp;·&nbsp; '
    f'Ruin threshold: bank falls below <strong>20u</strong> (80% drawdown)</div>',
    unsafe_allow_html=True
)

# ── Controls ───────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
with ctrl1:
    sys_options = list(PORT.keys())
    sys_name = st.selectbox(
        "System",
        sys_options,
        format_func=lambda x: f"{'🟢' if x in LIVE_SYSTEMS else '🔵'} {x}"
    )
with ctrl2:
    horizon = st.select_slider(
        "Bet horizon",
        options=[250, 500, 750, 1000, 1500, 2000],
        value=1000,
        format_func=lambda x: f"{x:,} bets"
    )
with ctrl3:
    st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
    run_btn = st.button("▶  Run simulation", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Run simulation ─────────────────────────────────────────────────────────────
state_key = f"mc_{sys_name}_{horizon}"
if run_btn or state_key not in st.session_state:
    with st.spinner(f"Running 5,000 simulations for {sys_name} over {horizon:,} bets..."):
        result = run_mc(sys_name, horizon)
        st.session_state[state_key] = result
else:
    result = st.session_state[state_key]

if result is None:
    st.error("Insufficient historical data to run simulation.")
    st.stop()

R = result
sys_color = SYS_COLORS.get(sys_name, G_ACCENT)
is_live   = sys_name in LIVE_SYSTEMS
data_sys  = PORT[sys_name]

# ── KPI strip ──────────────────────────────────────────────────────────────────
def kpi_colour(label, val):
    """Return green/amber/red based on metric type and value."""
    if label == "% in profit":
        return "green" if val >= 99 else "normal" if val >= 90 else "inverse"
    if label == "Ruin probability":
        return "green" if val <= 0.01 else "normal" if val <= 1 else "inverse"
    return "normal"

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Historical bets",   f"{data_sys['total_bets']:,}",
          delta=f"Win rate {data_sys['win_rate']}%")
k2.metric("Expected P&L",      f"+{R['pl_mean']:.1f}u",
          delta=f"Median {R['pl_p50']:+.1f}u")
k3.metric("% in profit",       f"{R['pct_profit']:.1f}%",
          delta=f"of {R['n_sims']:,} sims")
k4.metric("Ruin probability",  f"{R['pct_ruin']:.2f}%",
          delta="bank < 20u ever")
k5.metric("DD median",         f"{R['dd_med']:.1f}u",
          delta=f"{R['dd_pct_med']:.1f}% of bank")
k6.metric("DD worst 5%",       f"{R['dd_p5']:.1f}u",
          delta=f"{R['dd_pct_p5']:.1f}% of bank")

st.divider()

# ── Row 1: Fan chart + P&L distribution ───────────────────────────────────────
col_fan, col_dist = st.columns([3, 2])

with col_fan:
    st.subheader("Simulation paths — first 50 runs")
    fig_fan = go.Figure()
    x_axis  = list(range(horizon + 1))

    # Draw 50 individual paths (light)
    for i, path in enumerate(R["cum_paths"]):
        fig_fan.add_trace(go.Scatter(
            x=x_axis[1:], y=path.tolist(),
            mode="lines", line=dict(width=0.6, color=sys_color),
            opacity=0.25, showlegend=False, hoverinfo="skip"
        ))

    # Percentile bands
    all_paths = R["cum_paths"]
    p5  = np.percentile(all_paths, 5,  axis=0)
    p25 = np.percentile(all_paths, 25, axis=0)
    p50 = np.percentile(all_paths, 50, axis=0)
    p75 = np.percentile(all_paths, 75, axis=0)
    p95 = np.percentile(all_paths, 95, axis=0)

    fig_fan.add_trace(go.Scatter(
        x=x_axis[1:]+x_axis[1:][::-1],
        y=p95.tolist()+p5.tolist()[::-1],
        fill="toself", fillcolor=f"rgba({int(sys_color[1:3],16)},{int(sys_color[3:5],16)},{int(sys_color[5:7],16)},0.08)",
        line=dict(width=0), showlegend=False, hoverinfo="skip", name="P5–P95"
    ))
    fig_fan.add_trace(go.Scatter(
        x=x_axis[1:], y=p50.tolist(),
        mode="lines", line=dict(width=2.5, color=sys_color, dash="solid"),
        name="Median path"
    ))
    fig_fan.add_trace(go.Scatter(
        x=x_axis[1:], y=p5.tolist(),
        mode="lines", line=dict(width=1, color="#e74c3c", dash="dash"),
        name="P5 (worst 5%)"
    ))
    fig_fan.add_trace(go.Scatter(
        x=x_axis[1:], y=p95.tolist(),
        mode="lines", line=dict(width=1, color=sys_color, dash="dash"),
        name="P95 (best 5%)"
    ))
    fig_fan.add_hline(y=0, line_width=1, line_dash="dot", line_color="#666")

    fig_fan.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=320,
        font=dict(color="#e8f5e9", size=11),
        xaxis=dict(showgrid=True, gridcolor="#1a4a20", title="Bets"),
        yaxis=dict(showgrid=True, gridcolor="#1a4a20", title="Cumulative P&L (u)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_fan, use_container_width=True)

with col_dist:
    st.subheader("P&L distribution")
    edges = R["hist_edges"]
    pcts  = R["hist_pct"]
    bar_colors = ["#e74c3c" if e < 0 else "#f39c12" if e < 50 else sys_color for e in edges]

    fig_dist = go.Figure(go.Bar(
        x=[f"{e:+d}" for e in edges],
        y=pcts,
        marker_color=bar_colors,
        marker_line_width=0,
    ))
    # Add mean line
    mean_idx = min(range(len(edges)), key=lambda i: abs(edges[i] - R["pl_mean"]))
    fig_dist.add_vline(
        x=mean_idx, line_width=2, line_dash="dash", line_color=sys_color,
        annotation_text=f"Mean {R['pl_mean']:+.0f}u", annotation_position="top right",
        annotation_font_color=sys_color
    )

    fig_dist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=320,
        font=dict(color="#e8f5e9", size=10),
        xaxis=dict(showgrid=False, title="Terminal P&L (u)",
                   tickmode="array",
                   tickvals=list(range(0,len(edges),4)),
                   ticktext=[f"{edges[i]:+d}" for i in range(0,len(edges),4)]),
        yaxis=dict(showgrid=True, gridcolor="#1a4a20", title="% of simulations"),
        bargap=0.05,
    )
    st.plotly_chart(fig_dist, use_container_width=True)

# ── Row 2: Drawdown distribution + Percentile table ───────────────────────────
col_dd, col_pctl = st.columns([3, 2])

with col_dd:
    st.subheader("Drawdown distribution")
    dd_vals = R["dd_all"]
    dd_edges = list(range(-100, 5, 2))
    dd_hist, _ = np.histogram(dd_vals, bins=dd_edges)
    dd_pct = (dd_hist / R["n_sims"] * 100)
    dd_colors = ["#e74c3c" if e < -30 else "#f39c12" if e < -15 else "#2ecc71" for e in dd_edges[:-1]]

    fig_dd = go.Figure(go.Bar(
        x=[f"{e}" for e in dd_edges[:-1]],
        y=dd_pct.tolist(),
        marker_color=dd_colors,
        marker_line_width=0,
    ))
    fig_dd.add_vline(
        x=list(range(len(dd_edges)-1))[min(range(len(dd_edges)-1), key=lambda i: abs(dd_edges[i]-R["dd_med"]))],
        line_width=2, line_dash="dash", line_color="#f39c12",
        annotation_text=f"Median {R['dd_med']:.1f}u",
        annotation_position="top right", annotation_font_color="#f39c12"
    )
    fig_dd.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=280,
        font=dict(color="#e8f5e9", size=10),
        xaxis=dict(showgrid=False, title="Max drawdown from peak (u)",
                   tickmode="array",
                   tickvals=list(range(0,len(dd_edges)-1,5)),
                   ticktext=[f"{dd_edges[i]}" for i in range(0,len(dd_edges)-1,5)]),
        yaxis=dict(showgrid=True, gridcolor="#1a4a20", title="% of simulations"),
        bargap=0.05,
    )
    st.plotly_chart(fig_dd, use_container_width=True)

with col_pctl:
    st.subheader("P&L percentiles")
    pctl_df = pd.DataFrame([
        {"Percentile": "5th  (worst 5%)",  "P&L":  f"{R['pl_p5']:+.1f}u",  "vs Bank": f"{R['pl_p5']/100*100:+.1f}%"},
        {"Percentile": "25th",             "P&L":  f"{R['pl_p25']:+.1f}u", "vs Bank": f"{R['pl_p25']/100*100:+.1f}%"},
        {"Percentile": "50th (median)",    "P&L":  f"{R['pl_p50']:+.1f}u", "vs Bank": f"{R['pl_p50']/100*100:+.1f}%"},
        {"Percentile": "75th",             "P&L":  f"{R['pl_p75']:+.1f}u", "vs Bank": f"{R['pl_p75']/100*100:+.1f}%"},
        {"Percentile": "95th (best 5%)",   "P&L":  f"{R['pl_p95']:+.1f}u", "vs Bank": f"{R['pl_p95']/100*100:+.1f}%"},
        {"Percentile": "Mean",             "P&L":  f"{R['pl_mean']:+.1f}u","vs Bank": f"{R['pl_mean']/100*100:+.1f}%"},
    ])
    st.dataframe(pctl_df, use_container_width=True, hide_index=True, height=240)

    st.markdown(
        f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid '
        f'{"#2ecc71" if R["pct_ruin"]<=0.01 else "#f39c12" if R["pct_ruin"]<=1 else "#e74c3c"};'
        f'border-radius:6px;padding:10px 14px;font-size:0.82rem;color:#b2dfdb;margin-top:8px">'
        f'<strong style="color:#fff">Ruin probability:</strong> {R["pct_ruin"]:.2f}% &nbsp;|&nbsp; '
        f'<strong style="color:#fff">% in profit:</strong> {R["pct_profit"]:.1f}%</div>',
        unsafe_allow_html=True
    )

st.divider()

# ── Row 3: Losing run analysis ─────────────────────────────────────────────────
st.subheader("Longest losing run analysis")
st.markdown(
    f'<div style="font-size:0.82rem;color:#81c784;margin-bottom:12px">'
    f'How many consecutive losing bets should you expect over {horizon:,} bets? '
    f'Back FHG O1.5 has a much lower win rate (~43%) so losing runs are significantly longer — plan your bank accordingly.</div>',
    unsafe_allow_html=True
)

llr_cols = st.columns(5)
llr_data = [
    ("Median",      R["llr_med"],  "#2ecc71"),
    ("75th pct",    R["llr_p75"],  "#2ecc71" if R["llr_p75"] < 8  else "#f39c12"),
    ("90th pct",    R["llr_p90"],  "#2ecc71" if R["llr_p90"] < 10 else "#f39c12"),
    ("95th pct",    R["llr_p95"],  "#2ecc71" if R["llr_p95"] < 15 else "#e74c3c"),
    ("Worst seen",  R["llr_max"],  "#e74c3c"),
]
for col, (label, val, color) in zip(llr_cols, llr_data):
    col.markdown(
        f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-radius:8px;'
        f'padding:14px 10px;text-align:center">'
        f'<div style="font-size:28px;font-weight:500;color:{color}">{val}</div>'
        f'<div style="font-size:11px;color:#81c784;margin-top:4px">{label}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# ── Row 4: Multi-system comparison ────────────────────────────────────────────
st.divider()
with st.expander("📊  Compare all systems at selected horizon", expanded=False):
    st.markdown(f"Running quick comparison across all 7 systems at **{horizon:,} bets**...")
    cmp_rows = []
    prog = st.progress(0)
    sys_list = list(PORT.keys())
    for i, sn in enumerate(sys_list):
        r = run_mc(sn, horizon)
        prog.progress((i+1)/len(sys_list))
        if r:
            cmp_rows.append({
                "System":       sn,
                "Status":       "🟢 LIVE" if sn in LIVE_SYSTEMS else "🔵 TEST",
                "Win rate":     f"{PORT[sn]['win_rate']:.1f}%",
                "Exp P&L":      f"{r['pl_mean']:+.1f}u",
                "Median P&L":   f"{r['pl_p50']:+.1f}u",
                "P5 P&L":       f"{r['pl_p5']:+.1f}u",
                "P95 P&L":      f"{r['pl_p95']:+.1f}u",
                "% profit":     f"{r['pct_profit']:.1f}%",
                "Ruin %":       f"{r['pct_ruin']:.2f}%",
                "DD median":    f"{r['dd_med']:.1f}u",
                "DD worst 5%":  f"{r['dd_p5']:.1f}u",
                "LLR median":   r["llr_med"],
                "LLR P95":      r["llr_p95"],
            })
    prog.empty()
    if cmp_rows:
        cmp_df = pd.DataFrame(cmp_rows)
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)
