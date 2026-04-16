"""FTS Home Odds Dashboard — Home Page"""
import streamlit as st
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard.theme import SIDEBAR_CSS, G_PANEL, G_ACCENT, G_MID, G_TEST, G_LIVE, SYS_COLORS, sidebar_brand

st.set_page_config(page_title="FTS Home Odds", page_icon="🎰", layout="wide",
                   initial_sidebar_state="expanded")

sidebar_brand("🎰 FTS Home Odds")

# ── Load portfolio data ────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "portfolio_data.json")
with open(DATA_PATH) as f:
    PORT = json.load(f)

# ── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{G_ACCENT},{G_MID});'
        f'border-radius:16px;padding:14px;text-align:center;'
        f'font-size:2.4rem;line-height:1;margin-top:4px">🎰</div>',
        unsafe_allow_html=True
    )
with col_title:
    total_pl   = sum(v["total_pl"]   for v in PORT.values())
    total_bets = sum(v["total_bets"] for v in PORT.values())
    avg_roi    = sum(v["roi"]        for v in PORT.values()) / len(PORT)
    st.markdown(
        f'<div style="padding-left:8px">'
        f'<div style="color:#ffffff;font-size:2rem;font-weight:800;'
        f'letter-spacing:-0.5px;line-height:1.1">'
        f'🎰 FTS Home Odds Dashboard</div>'
        f'<div style="color:{G_ACCENT};font-size:0.9rem;margin-top:4px">'
        f'7 systems &nbsp;·&nbsp; home odds bands &nbsp;·&nbsp; '
        f'{total_bets:,} bets &nbsp;·&nbsp; +{total_pl:.0f} pts &nbsp;·&nbsp; '
        f'+{avg_roi:.1f}% avg ROI</div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ── KPI strip ──────────────────────────────────────────────────────────────────
live_pl   = sum(v["total_pl"]   for v in PORT.values() if v["live"])
live_bets = sum(v["total_bets"] for v in PORT.values() if v["live"])
test_pl   = sum(v["total_pl"]   for v in PORT.values() if not v["live"])
live_sys  = sum(1 for v in PORT.values() if v["live"])
test_sys  = sum(1 for v in PORT.values() if not v["live"])

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Portfolio P&L",  f"+{total_pl:.0f} pts",  f"{total_bets:,} bets")
c2.metric("Avg ROI",        f"+{avg_roi:.1f}%",       "7 systems")
c3.metric("🟢 Live P&L",   f"+{live_pl:.0f} pts",    f"{live_sys} systems")
c4.metric("🟢 Live Bets",  f"{live_bets:,}",          "Lay U1.5 + Lay O3.5")
c5.metric("🔵 Test P&L",   f"+{test_pl:.0f} pts",     f"{test_sys} systems")
c6.metric("Max DD",         f"{min(v['max_dd'] for v in PORT.values()):.1f} pts", "worst rule")

st.divider()

# ── System cards ───────────────────────────────────────────────────────────────
st.markdown("<h3>System Overview</h3>", unsafe_allow_html=True)

cols = st.columns(4)
for i, (name, data) in enumerate(PORT.items()):
    color  = data["color"]
    is_live = data["live"]
    badge  = f'<span style="background:{G_LIVE};color:#000;font-size:0.65rem;font-weight:700;padding:2px 7px;border-radius:10px">LIVE</span>' if is_live else f'<span style="background:{G_TEST};color:#000;font-size:0.65rem;font-weight:700;padding:2px 7px;border-radius:10px">TEST</span>'
    with cols[i % 4]:
        st.markdown(
            f'<div style="background:{G_PANEL};border:1px solid {G_MID};'
            f'border-top:3px solid {color};border-radius:10px;'
            f'padding:16px;margin-bottom:14px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
            f'<span style="color:#fff;font-weight:700;font-size:0.95rem">{name}</span>'
            f'{badge}</div>'
            f'<div style="color:{color};font-size:1.5rem;font-weight:800">+{data["total_pl"]:.0f}u</div>'
            f'<div style="color:#81c784;font-size:0.8rem;margin-top:2px">'
            f'+{data["roi"]:.1f}% ROI &nbsp;·&nbsp; {data["total_bets"]:,} bets</div>'
            f'<div style="color:#e74c3c;font-size:0.78rem;margin-top:4px">'
            f'Max DD: {data["max_dd"]:.1f}u</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.divider()

# ── Navigation cards ───────────────────────────────────────────────────────────
st.markdown("<h3>Navigate</h3>", unsafe_allow_html=True)
nav = [
    ("🎯", "Daily Selector",     G_ACCENT,  "Upload today's PreMatch file — generates LIVE & TEST selections"),
    ("📊", "Portfolio",          "#0e9973",  "Full portfolio P&L, drawdown and season overview"),
    ("📉", "Results Dashboard",  "#1a7a3c",  "Cumulative P&L curves, per-system charts and competition breakdown"),
    ("📈", "System Performance", "#155a1e",  "Per-rule edge analysis, win rates and ROI by league"),
    ("🔬", "Analytics",          "#0a4015",  "Rolling ROI, distributions and deep-dive statistics"),
    ("🔄", "Update Database",    "#2c3e50",  "Upload new results file to refresh all portfolio data"),
]
ncols = st.columns(3)
for i, (icon, title, color, desc) in enumerate(nav):
    with ncols[i % 3]:
        st.markdown(
            f'<div style="background:{G_PANEL};border:1px solid {G_MID};'
            f'border-top:3px solid {color};border-radius:10px;'
            f'padding:18px;margin-bottom:16px;min-height:100px">'
            f'<div style="font-size:1.4rem;margin-bottom:6px">{icon}'
            f'<span style="color:#fff;font-weight:700;font-size:1rem;'
            f'vertical-align:middle;margin-left:6px">{title}</span></div>'
            f'<div style="color:#81c784;font-size:0.78rem;line-height:1.4">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-radius:8px;'
    f'padding:14px 18px;margin-top:8px;color:#81c784;font-size:0.8rem">'
    f'<span style="color:{G_ACCENT};font-weight:600">ℹ️ Betting status:</span> '
    f'<strong style="color:#2ecc71">LIVE</strong> systems (Lay U1.5, Lay O3.5) are actively staked. '
    f'<strong style="color:#5dade2">TEST</strong> systems are tracked for performance monitoring only — '
    f'no real stakes placed. Use <strong style="color:#fff">Daily Selector</strong> to generate today\'s bets.'
    f'</div>',
    unsafe_allow_html=True
)
