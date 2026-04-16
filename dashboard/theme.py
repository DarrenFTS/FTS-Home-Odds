"""Shared theme constants and CSS for FTS Home Odds Dashboard."""

# ── Brand colours (dark green theme) ─────────────────────────────────────────
G_DARK   = "#0a1f0e"   # page background
G_PANEL  = "#0d2b12"   # sidebar / card background
G_MID    = "#155a1e"   # mid green
G_ACCENT = "#2ecc71"   # primary accent — bright green
G_SOFT   = "#27ae60"   # softer green
G_LIVE   = "#2ecc71"   # LIVE badge
G_TEST   = "#5dade2"   # TEST badge (blue distinguishes from live)
G_BUF    = "#f39c12"   # buffer warning amber
G_ERR    = "#e74c3c"   # red for drawdown / loss
G_TEXT   = "#e8f5e9"   # primary text
G_MUTED  = "#81c784"   # muted text
G_BORDER = "#1e5c28"   # border colour

# ── System colours ────────────────────────────────────────────────────────────
SYS_COLORS = {
    "Lay U1.5":      "#2ecc71",
    "Lay O3.5":      "#1abc9c",
    "Lay FHG U0.5":  "#27ae60",
    "Back FHG O1.5": "#16a085",
    "Home Lay":      "#1e8449",
    "Away Lay":      "#145a32",
    "Draw Lay":      "#0e6655",
}

SIDEBAR_CSS = f"""
<style>
[data-testid="stSidebar"] {{ background: {G_PANEL} !important; }}
[data-testid="stSidebar"],
[data-testid="stSidebar"] *,
[data-testid="stSidebarNav"],
[data-testid="stSidebarNav"] *,
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavLink"] *,
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarNavSeparator"] *,
section[data-testid="stSidebar"] a,
section[data-testid="stSidebar"] a *,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] li *,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div {{ color: #ffffff !important; }}
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stHeadingWithActionElements"] h3,
div[class*="stHeading"] h1,
div[class*="stHeading"] h2,
div[class*="stHeading"] h3 {{ color: #ffffff !important; }}
</style>
"""

PLOT_LAYOUT = dict(
    plot_bgcolor="#061208",
    paper_bgcolor="#061208",
    font=dict(color="#e8f5e9"),
    xaxis=dict(gridcolor="rgba(46,204,113,0.08)", showgrid=True),
    yaxis=dict(gridcolor="rgba(46,204,113,0.08)", showgrid=True),
    hovermode="x unified",
    margin=dict(t=20, b=40, l=60, r=20),
)

def hex_alpha(hex_color: str, alpha: float = 0.55) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def sidebar_brand(label: str = "⚽ FTS Home Odds"):
    import streamlit as st
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div style="padding:8px 0 16px 0;border-bottom:1px solid rgba(46,204,113,0.25);'
        f'margin-bottom:8px">'
        f'<span style="color:#2ecc71;font-size:1rem;font-weight:700">{label}</span></div>',
        unsafe_allow_html=True
    )
