"""
FTS Home Odds Dashboard — shared look, colours and data loading.

Every page calls:
    import fts_ui as ui
    ui.apply_theme()
right after st.set_page_config(...). Change colours here once and every page follows.
"""
from __future__ import annotations

import json
import os

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, "data", "portfolio_master_sheet.json")
INFO_PATH = os.path.join(ROOT, "data", "build_info.json")

# ── Palette ───────────────────────────────────────────────────────────────────
BG = "#06140F"
SURFACE = "#0D2219"
SURFACE_2 = "#13301F"
BORDER = "#1F4A36"
TEXT = "#E6F4EC"
MUTED = "#8DB5A0"
ACCENT = "#10B981"
GREEN = "#22C55E"
RED = "#EF4444"
AMBER = "#F59E0B"

SYSTEM_COLORS = {
    "Lay U1.5": "#38BDF8",
    "Lay O3.5": "#A78BFA",
    "Back FHG O1.5": "#FBBF24",
    "Lay FHG U0.5": "#FB923C",
    "Home Lay": "#F472B6",
    "Away Lay": "#60A5FA",
    "Draw Lay": "#2DD4BF",
}
SYSTEM_ORDER = list(SYSTEM_COLORS.keys())
LIVE_SYSTEMS = SYSTEM_ORDER[:3]
TEST_SYSTEMS = SYSTEM_ORDER[3:]
STATUS = {s: "LIVE" for s in LIVE_SYSTEMS} | {s: "TEST" for s in TEST_SYSTEMS}
BET_TYPE = {s: "LAY" for s in SYSTEM_ORDER} | {"Back FHG O1.5": "BACK"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ── Plotly template: every chart picks this up automatically ─────────────────
_tpl = go.layout.Template(pio.templates["plotly_dark"])
_tpl.layout.update(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=12),
    colorway=list(SYSTEM_COLORS.values()) + [ACCENT, AMBER, GREEN, RED],
    xaxis=dict(gridcolor="rgba(141,181,160,0.12)", zerolinecolor="rgba(141,181,160,0.25)",
               linecolor=BORDER),
    yaxis=dict(gridcolor="rgba(141,181,160,0.12)", zerolinecolor="rgba(141,181,160,0.25)",
               linecolor=BORDER),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
    hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER, font=dict(color=TEXT)),
    margin=dict(l=10, r=10, t=30, b=10),
)
pio.templates["fts"] = _tpl
pio.templates.default = "fts"
TEMPLATE = "fts"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}}
.stApp {{ background: radial-gradient(1200px 600px at 85% -10%, rgba(16,185,129,0.10), transparent 60%), {BG}; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px; }}

/* text */
h1, h2, h3, h4, h5, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{ color: {TEXT} !important; letter-spacing: -0.02em; }}
h1 {{ font-weight: 800 !important; }}
h2, h3 {{ font-weight: 700 !important; }}
p, li, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {TEXT}; }}
[data-testid="stCaptionContainer"], .stCaption, small {{ color: {MUTED} !important; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #0B2A1D 0%, #061410 100%) !important;
  border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] * {{ color: {TEXT}; }}
[data-testid="stSidebarNav"] a {{ border-radius: 8px; margin: 1px 6px; }}
[data-testid="stSidebarNav"] a:hover {{ background: rgba(16,185,129,0.12); }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: rgba(16,185,129,0.20); }}
[data-testid="stSidebarNav"] span {{ color: {TEXT} !important; font-weight: 500; }}

[data-testid="stSidebarNav"] li:first-child span p {{ font-size: 0 !important; }}
[data-testid="stSidebarNav"] li:first-child span p::after {{ content: "🏠  Home"; font-size: 0.875rem; }}

/* metrics as cards */
[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset; }}
[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; font-size: 0.78rem !important;
  text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }}
[data-testid="stMetricValue"] {{ color: {TEXT} !important; font-weight: 700; font-size: 1.55rem !important; }}
[data-testid="stMetricValue"] p, [data-testid="stMetricValue"] div {{ font-size: 1.55rem !important; overflow: visible !important;
  text-overflow: clip !important; white-space: nowrap; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 10px 10px 0 0; padding: 8px 16px;
  color: {MUTED}; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ color: {TEXT} !important; background: {SURFACE}; }}

/* inputs */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stNumberInput input, .stDateInput input,
.stTextInput input {{ background: {SURFACE_2} !important; border-color: {BORDER} !important; color: {TEXT} !important; }}
[data-baseweb="tag"] {{ background: rgba(16,185,129,0.22) !important; }}
[data-baseweb="popover"] li, [data-baseweb="menu"] li {{ background: {SURFACE_2}; color: {TEXT}; }}

/* buttons */
.stButton > button, .stDownloadButton > button {{ border-radius: 10px; font-weight: 600; border: 1px solid {BORDER}; }}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: linear-gradient(135deg, {ACCENT}, #0E9F6E); border: 0; color: white; }}

/* containers */
[data-testid="stExpander"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 12px; overflow: hidden; }}
hr {{ border-color: {BORDER} !important; opacity: 0.6; }}
[data-testid="stPlotlyChart"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; padding: 6px; }}

/* custom components */
.fts-hero {{ display:flex; align-items:center; gap:16px; margin: 0 0 18px 0; }}
.fts-hero .ico {{ width:52px; height:52px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:1.6rem; background: linear-gradient(135deg, rgba(16,185,129,0.35), rgba(16,185,129,0.08));
  border:1px solid rgba(16,185,129,0.35); }}
.fts-hero h1 {{ margin:0; padding:0; font-size:1.9rem; line-height:1.1; }}
.fts-hero .sub {{ color:{MUTED}; font-size:0.92rem; margin-top:4px; }}
.fts-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px; height:100%; }}
.fts-card .lbl {{ color:{MUTED}; font-size:0.74rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; }}
.fts-card .val {{ color:{TEXT}; font-size:1.55rem; font-weight:700; margin-top:4px; }}
.fts-card .sub {{ color:{MUTED}; font-size:0.8rem; margin-top:2px; }}
.fts-pill {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:0.7rem; font-weight:700;
  letter-spacing:0.05em; }}
.fts-banner {{ border-radius:14px; padding:16px 18px; border:1px solid {BORDER}; background:{SURFACE}; margin-bottom:14px; }}
.fts-banner b {{ color:{TEXT}; }}
.fts-section {{ display:flex; align-items:center; gap:10px; margin: 18px 0 8px 0; }}
.fts-section .bar {{ width:4px; height:20px; border-radius:4px; background:{ACCENT}; }}
.fts-section .t {{ font-size:1.12rem; font-weight:700; color:{TEXT}; }}
.fts-section .s {{ color:{MUTED}; font-size:0.85rem; }}
</style>
"""


def apply_theme():
    """Inject the shared CSS and sidebar brand. Call once per page after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)
    info = build_info()
    fresh = f"Results to {pd.to_datetime(info['results_to']).strftime('%d %b %Y')}" if info else ""
    st.sidebar.markdown(
        f'<div style="padding:4px 4px 14px 4px;border-bottom:1px solid {BORDER};margin-bottom:10px">'
        f'<div style="font-weight:800;font-size:1.05rem">🎰 FTS Home Odds Dashboard</div>'
        f'<div style="color:{MUTED};font-size:0.78rem;margin-top:2px">{fresh}</div></div>',
        unsafe_allow_html=True)


def hero(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="fts-hero"><div class="ico">{icon}</div><div><h1>{title}</h1>'
        f'<div class="sub">{subtitle}</div></div></div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "", color: str = ACCENT):
    st.markdown(
        f'<div class="fts-section"><div class="bar" style="background:{color}"></div>'
        f'<div class="t">{title}</div><div class="s">{subtitle}</div></div>', unsafe_allow_html=True)


def card(label: str, value: str, sub: str = "", color: str | None = None):
    edge = f"border-left:4px solid {color};" if color else ""
    return (f'<div class="fts-card" style="{edge}"><div class="lbl">{label}</div>'
            f'<div class="val">{value}</div><div class="sub">{sub}</div></div>')


def pill(text: str, color: str):
    return (f'<span class="fts-pill" style="background:{color}22;color:{color};'
            f'border:1px solid {color}55">{text}</span>')


def status_pill(system: str):
    return pill(STATUS.get(system, ""), GREEN if STATUS.get(system) == "LIVE" else AMBER)


def hex_rgba(h: str, a: float):
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load(path: str, mtime: float) -> pd.DataFrame:
    df = pd.DataFrame(json.load(open(path)))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["won"] = df["won"].astype(bool)
    df["month"] = df["date"].dt.to_period("M")
    df["bet_type"] = df["system"].map(BET_TYPE)
    df["home_odds"] = pd.to_numeric(df.get("home_odds"), errors="coerce")
    return df.sort_values(["date", "system"]).reset_index(drop=True)


def load_bets() -> pd.DataFrame:
    """All bets. Re-reads automatically whenever the data file changes."""
    return _load(DATA_PATH, os.path.getmtime(DATA_PATH)).copy()


def build_info() -> dict | None:
    try:
        return json.load(open(INFO_PATH))
    except Exception:
        try:
            d = json.load(open(DATA_PATH))
            return {"results_to": max(r["date"] for r in d), "bets": len(d)}
        except Exception:
            return None


def summary(df: pd.DataFrame, by: str | list | None = None) -> pd.DataFrame:
    """Bets, P/L, ROI, strike rate, avg odds, max drawdown — optionally grouped."""
    def _one(g):
        g = g.sort_values("date")
        cum = g["pl"].cumsum()
        return pd.Series({
            "Bets": len(g), "Won": int(g["won"].sum()), "P/L": g["pl"].sum(),
            "ROI %": g["pl"].sum() / len(g) * 100 if len(g) else 0,
            "SR %": g["won"].mean() * 100 if len(g) else 0,
            "Avg Odds": g["odds"].mean(),
            "Max DD": float((cum - cum.cummax()).min()) if len(g) else 0,
        })
    if by is None:
        return _one(df).to_frame().T
    return df.groupby(by, observed=True).apply(_one, include_groups=False).reset_index()


# ── Table styling (dark-friendly) ────────────────────────────────────────────
def pl_style(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    if pd.isna(v):
        return f"color:{MUTED}"
    if v > 0:
        return f"color:{GREEN};font-weight:600"
    if v < 0:
        return f"color:{RED};font-weight:600"
    return ""


def heat_style(v, scale: float = 30):
    """Green/red background intensity by value (ROI %, P/L, edge)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    if pd.isna(v):
        return f"color:{MUTED};background-color:transparent"
    a = min(abs(v) / scale, 1) * 0.55 + 0.08
    col = "34,197,94" if v > 0 else "239,68,68" if v < 0 else "143,163,191"
    return f"background-color:rgba({col},{a:.2f});color:{TEXT};font-weight:600"


def system_style(v):
    c = SYSTEM_COLORS.get(v)
    return f"color:{c};font-weight:700" if c else ""
