"""FTS Home Odds Portfolio Dashboard — Home (all figures calculated from data/portfolio_master_sheet.json)"""
import os as _os
import sys as _sys

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="FTS Home Odds Systems", page_icon="🎰", layout="wide", initial_sidebar_state="expanded")
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import fts_ui as ui  # noqa: E402

ui.apply_theme()
bets = ui.load_bets()
live = bets[bets["system"].isin(ui.LIVE_SYSTEMS)]
n_lg = bets.groupby("system")["league"].nunique()
last = bets["date"].max()

ui.hero("🎰", "FTS Home Odds Systems Dashboard",
        f"{ui.pill('3 LIVE', ui.GREEN)} {ui.pill('4 TEST', ui.AMBER)} &nbsp;·&nbsp; "
        f"{len(bets):,} bets · {bets['pl'].sum() / len(bets) * 100:+.2f}% ROI · results to {last:%d %b %Y}")

# ── Headline KPIs ─────────────────────────────────────────────────────────────
this_m = bets["month"].max()
mb = live[live["month"] == this_m]
s26 = live[live["season"] == bets["season"].max()]
k = st.columns(5)
k[0].markdown(ui.card("Live P/L", f"{live['pl'].sum():+.2f} pts", f"{len(live):,} bets · {live['pl'].sum() / len(live) * 100:+.2f}% ROI",
                      ui.GREEN), unsafe_allow_html=True)
k[1].markdown(ui.card("All systems P/L", f"{bets['pl'].sum():+.2f} pts", "incl. 4 test systems (paper)", ui.ACCENT),
              unsafe_allow_html=True)
k[2].markdown(ui.card(f"Season {bets['season'].max()}", f"{s26['pl'].sum():+.2f} pts", f"{len(s26)} live bets",
                      ui.GREEN if s26["pl"].sum() >= 0 else ui.RED), unsafe_allow_html=True)
k[3].markdown(ui.card(f"{this_m.strftime('%B %Y')}", f"{mb['pl'].sum():+.2f} pts", f"{len(mb)} live bets",
                      ui.GREEN if mb["pl"].sum() >= 0 else ui.RED), unsafe_allow_html=True)
k[4].markdown(ui.card("Strike rate (live)", f"{live['won'].mean() * 100:.1f}%", f"{bets['league'].nunique()} leagues covered",
                      ui.MUTED), unsafe_allow_html=True)

# ── System cards with sparkline ──────────────────────────────────────────────
ui.section("Systems", "cumulative P/L since 2021 · click a page in the sidebar for detail")
for _i, s in enumerate(ui.SYSTEM_ORDER):
    if _i % 4 == 0:
        cols = st.columns(4)
    col = cols[_i % 4]
    sb = bets[bets["system"] == s]
    clr = ui.SYSTEM_COLORS[s]
    cum = sb["pl"].cumsum()
    dd = float((cum - cum.cummax()).min())
    with col:
        st.markdown(
            f'<div class="fts-card" style="border-top:3px solid {clr};padding-bottom:6px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<div style="font-weight:700;font-size:1rem">{s}</div>{ui.status_pill(s)}</div>'
            f'<div class="val" style="color:{clr}">{sb["pl"].sum():+.2f}</div>'
            f'<div class="sub">{len(sb):,} bets · {sb["pl"].sum() / len(sb) * 100:+.2f}% ROI · '
            f'{sb["won"].mean() * 100:.1f}% SR</div>'
            f'<div class="sub">{n_lg.get(s, 0)} leagues · max DD {dd:.1f}</div></div>', unsafe_allow_html=True)
        f = go.Figure(go.Scatter(x=sb["date"], y=cum, mode="lines", line=dict(color=clr, width=2),
                                 fill="tozeroy", fillcolor=ui.hex_rgba(clr, 0.12),
                                 hovertemplate="%{x|%d %b %Y}<br>%{y:+.2f}<extra></extra>"))
        f.update_layout(height=110, margin=dict(l=0, r=0, t=0, b=0), xaxis=dict(visible=False),
                        yaxis=dict(visible=False), showlegend=False)
        st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})

# ── Portfolio curve ───────────────────────────────────────────────────────────
ui.section("Portfolio growth", "live systems combined vs each system")
fig = go.Figure()
for s in ui.SYSTEM_ORDER:
    sb = bets[bets["system"] == s]
    fig.add_trace(go.Scatter(x=sb["date"], y=sb["pl"].cumsum(), name=s, mode="lines",
                             line=dict(color=ui.SYSTEM_COLORS[s], width=1.6),
                             visible=True if s in ui.LIVE_SYSTEMS else "legendonly"))
fig.add_trace(go.Scatter(x=live["date"], y=live["pl"].cumsum(), name="Live combined", mode="lines",
                         line=dict(color=ui.TEXT, width=3)))
fig.update_layout(height=360, yaxis_title="P/L (pts)", hovermode="x unified", legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, use_container_width=True)

# ── Navigation ────────────────────────────────────────────────────────────────
ui.section("Pages")
nav = [
    ("🎯", "Daily Selector", "Upload today's PreMatch file to generate qualifying selections"),
    ("📊", "Portfolio", "Performance breakdown with season and league charts and filters"),
    ("📉", "Results Dashboard", "Cumulative P/L curves, drawdowns and competition breakdown per system"),
    ("📈", "System Performance", "Per-system detail, season & month totals and Monte Carlo risk"),
    ("🔬", "Analytics", "Odds bands, distributions, rolling ROI and deep-dive analytics"),
    ("📐", "Odds Edge Analysis", "Actual vs implied win rate per league — by season and month"),
    ("💧", "Price Leak Calculator", "Find where the ticks go between the tested price and the price you get"),
    ("🔄", "Update Database", "Upload the monthly FTS Advanced Results – Odds file — every page refreshes"),
]
cols = st.columns(4)
for i, (ico, title, desc) in enumerate(nav):
    with cols[i % 4]:
        st.markdown(
            f'<div class="fts-card" style="margin-bottom:14px;min-height:112px">'
            f'<div style="font-size:1.3rem">{ico} <span style="font-weight:700;font-size:1rem;vertical-align:middle">{title}</span></div>'
            f'<div class="sub" style="margin-top:6px;line-height:1.4">{desc}</div></div>', unsafe_allow_html=True)
