"""Page 2: Portfolio Overview"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import sidebar_brand, G_PANEL, G_MID, G_ACCENT, G_TEST, G_LIVE, PLOT_LAYOUT, hex_alpha

st.set_page_config(page_title="Portfolio", page_icon="📊", layout="wide")
sidebar_brand()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "portfolio_data.json")
with open(DATA_PATH) as f:
    PORT = json.load(f)

st.title("📊 Portfolio Overview")

# ── Portfolio summary table ────────────────────────────────────────────────────
st.subheader("All Systems Summary")
rows = []
for name, d in PORT.items():
    rows.append({
        'System':       name,
        'Status':       '🟢 LIVE' if d['live'] else '🔵 TEST',
        'Total P&L':    f"+{d['total_pl']:.2f}u",
        'Bets':         d['total_bets'],
        'Win Rate':     f"{d['win_rate']:.1f}%",
        'ROI%':         f"+{d['roi']:.1f}%",
        'Max Drawdown': f"{d['max_dd']:.2f}u",
        'Rules':        len(d['rules']),
    })
df_sum = pd.DataFrame(rows)

def style_summary(v):
    if 'LIVE' in str(v): return 'color:#2ecc71;font-weight:bold'
    if 'TEST' in str(v): return 'color:#5dade2;font-weight:bold'
    if str(v).startswith('+'): return 'color:#2ecc71;font-weight:bold'
    if str(v).startswith('-'): return 'color:#e74c3c;font-weight:bold'
    return ''

st.dataframe(
    df_sum.style.map(style_summary, subset=['Status','Total P&L','ROI%','Max Drawdown']),
    use_container_width=True, hide_index=True
)

st.divider()

# ── Combined cumulative P&L chart ──────────────────────────────────────────────
st.subheader("Combined Portfolio Cumulative P&L")
fig = go.Figure()

for name, d in PORT.items():
    dates  = d['monthly_dates']
    values = d['monthly_cum_pl']
    color  = d['color']
    dash   = 'solid' if d['live'] else 'dot'
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        mode='lines',
        name=f"{'🟢' if d['live'] else '🔵'} {name}",
        line=dict(color=color, width=2.5 if d['live'] else 1.5, dash=dash),
        hovertemplate=f"{name}<br>%{{x}}<br>P&L: %{{y:.2f}}u<extra></extra>",
    ))

fig.add_hline(y=0, line_dash="dot", line_color="#30363d")
layout = dict(PLOT_LAYOUT)
layout.update(dict(
    height=420,
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(46,204,113,0.2)',
                borderwidth=1, font=dict(color='#e8f5e9', size=11)),
    yaxis=dict(**PLOT_LAYOUT.get('yaxis',{}), title="Cumulative P&L (units)"),
))
fig.update_layout(**layout)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Side-by-side metrics ───────────────────────────────────────────────────────
st.subheader("System Comparison")
col_pl, col_roi = st.columns(2)

with col_pl:
    st.markdown("**Total P&L by System**")
    names  = list(PORT.keys())
    pls    = [PORT[n]['total_pl'] for n in names]
    colors = [PORT[n]['color'] for n in names]
    fig_bar = go.Figure(go.Bar(
        x=pls, y=names, orientation='h',
        marker_color=colors,
        text=[f"+{p:.0f}u" for p in pls],
        textposition='outside',
    ))
    fig_bar.update_layout(**{**PLOT_LAYOUT, 'height': 320,
        'xaxis': dict(**PLOT_LAYOUT.get('xaxis',{}), title="P&L (units)"),
        'margin': dict(t=20,b=20,l=160,r=80)})
    st.plotly_chart(fig_bar, use_container_width=True)

with col_roi:
    st.markdown("**ROI% by System**")
    rois = [PORT[n]['roi'] for n in names]
    fig_roi = go.Figure(go.Bar(
        x=rois, y=names, orientation='h',
        marker_color=colors,
        text=[f"+{r:.1f}%" for r in rois],
        textposition='outside',
    ))
    fig_roi.update_layout(**{**PLOT_LAYOUT, 'height': 320,
        'xaxis': dict(**PLOT_LAYOUT.get('xaxis',{}), title="ROI%"),
        'margin': dict(t=20,b=20,l=160,r=80)})
    st.plotly_chart(fig_roi, use_container_width=True)

# ── Bank management guide ──────────────────────────────────────────────────────
st.divider()
st.subheader("Bank Management Guide")
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid #2ecc71;'
        f'border-radius:6px;padding:14px;margin-bottom:12px">'
        f'<div style="color:#2ecc71;font-weight:700;margin-bottom:8px">🟢 LAY BANK (Live Systems)</div>'
        f'<div style="font-size:0.85rem;color:#b2dfdb;line-height:1.7">'
        f'<b>Systems:</b> Lay U1.5 + Lay O3.5<br>'
        f'<b>Recommended bank:</b> 50 units<br>'
        f'<b>Stake per bet:</b> 1.0u (0.5u buffer zone)<br>'
        f'<b>Compound:</b> Monthly from month 4+<br>'
        f'<b>Review threshold:</b> –20u from peak</div></div>',
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid #5dade2;'
        f'border-radius:6px;padding:14px;margin-bottom:12px">'
        f'<div style="color:#5dade2;font-weight:700;margin-bottom:8px">🔵 TEST BANK (Tracking Only)</div>'
        f'<div style="font-size:0.85rem;color:#b2dfdb;line-height:1.7">'
        f'<b>Systems:</b> All 5 test systems<br>'
        f'<b>Purpose:</b> Performance tracking — no real stakes<br>'
        f'<b>Review:</b> After 6 months live data<br>'
        f'<b>Promotion criteria:</b> Live ROI ≥ backtest × 0.7</div></div>',
        unsafe_allow_html=True
    )
