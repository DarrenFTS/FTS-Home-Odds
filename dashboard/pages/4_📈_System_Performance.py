"""Page 4: System Performance — per-rule edge analysis"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import sidebar_brand, G_PANEL, G_MID, G_ACCENT, PLOT_LAYOUT, hex_alpha
from systems.all_systems import SYSTEM_DEFS, HIST_ROI

st.set_page_config(page_title="System Performance", page_icon="📈", layout="wide")
sidebar_brand()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "portfolio_data.json")
with open(DATA_PATH) as f:
    PORT = json.load(f)

st.title("📈 System Performance")
st.markdown("Rule-level edge analysis — historical ROI, win rates and P&L per competition.")

# ── System selector ────────────────────────────────────────────────────────────
SYSTEMS = list(PORT.keys())
sel = st.selectbox("Select System", SYSTEMS,
                   format_func=lambda s: f"{'🟢' if PORT[s]['live'] else '🔵'} {s}")

d     = PORT[sel]
color = d["color"]
sys_def = next((s for s in SYSTEM_DEFS if s["name"] == sel), None)

# ── Header ─────────────────────────────────────────────────────────────────────
badge = "🟢 LIVE — actively staked" if d["live"] else "🔵 TEST — tracking only"
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};'
    f'border-left:4px solid {color};border-radius:8px;padding:14px 20px;margin:12px 0">'
    f'<span style="color:{color};font-weight:700;font-size:1rem">{sel}</span>'
    f'&nbsp;&nbsp;<span style="color:#81c784;font-size:0.85rem">{badge}</span>'
    f'&nbsp;&nbsp;|&nbsp;&nbsp;'
    f'<span style="color:#e8f5e9">+{d["total_pl"]:.2f}u &nbsp; {d["total_bets"]:,} bets &nbsp; '
    f'+{d["roi"]:.1f}% ROI &nbsp; {d["win_rate"]:.1f}% win rate &nbsp; '
    f'Max DD: {d["max_dd"]:.2f}u</span></div>',
    unsafe_allow_html=True
)

st.divider()

# ── Rule-level performance table ───────────────────────────────────────────────
st.subheader("Rule-Level Performance")
rules = d["rules"]
comps_data = {c["comp"]: c for c in d["competitions"]}

rule_rows = []
for r in rules:
    lo, hi = r["lo"], r["hi"]
    comp   = r["comp"]
    roi    = HIST_ROI.get((comp, lo, hi, sel), 0.0)
    lo_buf = round(lo * 0.90, 2)
    hi_buf = round(hi * 1.10, 2)
    rule_rows.append({
        "Competition":     comp,
        "Home Odds":       f"{lo}–{hi}",
        "Buffered (±10%)": f"{lo_buf:.2f}–{hi_buf:.2f}",
        "Hist ROI%":       roi,
    })

df_rules = pd.DataFrame(rule_rows)

# ROI bar chart
st.markdown("**Historical ROI% per Rule**")
fig_r = go.Figure(go.Bar(
    x=df_rules["Hist ROI%"],
    y=[f"{r['Competition']} ({r['Home Odds']})" for r in rule_rows],
    orientation="h",
    marker_color=[hex_alpha(color, 0.7) if v >= 20
                  else hex_alpha(color, 0.45) for v in df_rules["Hist ROI%"]],
    marker_line_color=color, marker_line_width=1.5,
    text=[f"+{v:.1f}%" for v in df_rules["Hist ROI%"]],
    textposition="outside",
))
fig_r.update_layout(**{
    **PLOT_LAYOUT,
    "height": max(280, 40 * len(rule_rows) + 80),
    "xaxis": dict(**PLOT_LAYOUT.get("xaxis",{}), title="ROI%"),
    "yaxis": dict(gridcolor="rgba(0,0,0,0)"),
    "margin": dict(t=10, b=40, l=260, r=80),
    "showlegend": False,
})
st.plotly_chart(fig_r, use_container_width=True)

# Display rules table
df_disp = df_rules.copy()
df_disp["Hist ROI%"] = df_disp["Hist ROI%"].apply(lambda x: f"+{x:.1f}%")
st.dataframe(
    df_disp.style.map(
        lambda v: 'color:#2ecc71;font-weight:bold' if str(v).startswith('+') else '',
        subset=["Hist ROI%"]
    ),
    use_container_width=True, hide_index=True
)

st.divider()

# ── Competition performance ────────────────────────────────────────────────────
st.subheader("Competition P&L vs Bets")
comps  = d["competitions"]
c_labs = [c["comp"] for c in comps]
c_pls  = [c["pl"]   for c in comps]
c_bets = [c["bets"] for c in comps]
c_rois = [c["roi"]  for c in comps]

fig_scatter = go.Figure(go.Scatter(
    x=c_bets, y=c_pls,
    mode="markers+text",
    text=c_labs,
    textposition="top center",
    textfont=dict(color="#e8f5e9", size=10),
    marker=dict(
        size=[max(8, r * 0.5) for r in c_rois],
        color=c_rois,
        colorscale=[[0, "#145a32"], [0.5, "#2ecc71"], [1, "#abebc6"]],
        colorbar=dict(title=dict(text="ROI%", font=dict(color="#e8f5e9")),
                      tickfont=dict(color="#e8f5e9")),
        showscale=True,
        line=dict(color=color, width=1.5),
    ),
    hovertemplate="<b>%{text}</b><br>Bets: %{x}<br>P&L: %{y:.2f}u<extra></extra>",
))
fig_scatter.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
fig_scatter.update_layout(**{
    **PLOT_LAYOUT,
    "height": 400,
    "xaxis": dict(**PLOT_LAYOUT.get("xaxis",{}), title="Number of Bets"),
    "yaxis": dict(**PLOT_LAYOUT.get("yaxis",{}), title="Total P&L (units)"),
    "margin": dict(t=20, b=60, l=70, r=80),
    "showlegend": False,
})
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("Bubble size = ROI%. Colour scale: darker = lower ROI, brighter = higher ROI.")

st.divider()

# ── Cross-system ROI comparison ────────────────────────────────────────────────
st.subheader("Cross-System ROI Comparison")
st.markdown("How does this system compare across key metrics?")

comp_rows = []
for sname, sdata in PORT.items():
    comp_rows.append({
        "System":   sname,
        "Status":   "🟢 LIVE" if sdata["live"] else "🔵 TEST",
        "P&L (u)":  sdata["total_pl"],
        "Bets":     sdata["total_bets"],
        "ROI%":     sdata["roi"],
        "Win Rate": sdata["win_rate"],
        "Max DD":   sdata["max_dd"],
    })

df_comp = pd.DataFrame(comp_rows).sort_values("ROI%", ascending=False)
df_comp["P&L (u)"]  = df_comp["P&L (u)"].apply(lambda x: f"+{x:.2f}")
df_comp["ROI%"]     = df_comp["ROI%"].apply(lambda x: f"+{x:.1f}%")
df_comp["Win Rate"] = df_comp["Win Rate"].apply(lambda x: f"{x:.1f}%")
df_comp["Max DD"]   = df_comp["Max DD"].apply(lambda x: f"{x:.2f}")

def hl_selected(row):
    styles = [''] * len(row)
    if row['System'] == sel:
        styles = [f'background-color:{G_PANEL};color:{color};font-weight:bold'] * len(row)
    return styles

def colour_status(v):
    if 'LIVE' in str(v): return 'color:#2ecc71;font-weight:bold'
    if 'TEST' in str(v): return 'color:#5dade2;font-weight:bold'
    return ''

st.dataframe(
    df_comp.style
        .apply(hl_selected, axis=1)
        .map(colour_status, subset=["Status"]),
    use_container_width=True, hide_index=True
)
st.caption(f"Highlighted row = currently selected system ({sel})")
