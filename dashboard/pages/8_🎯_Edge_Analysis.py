"""Page 8: Odds vs Implied Odds Edge Analysis — FTS Home Odds Portfolio"""
import streamlit as st
import pandas as pd
import json
import os
import sys
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import SIDEBAR_CSS, sidebar_brand, G_PANEL, G_MID, G_ACCENT, G_TEST, G_BUF, G_LIVE

st.set_page_config(page_title="Edge Analysis", page_icon="🎯", layout="wide")
sidebar_brand()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "portfolio_data.json")

@st.cache_data
def load_portfolio():
    with open(DATA_PATH) as f:
        return json.load(f)

PORT = load_portfolio()
EDGE = PORT.get("_edge_analysis", {})

SYS_COLORS = {"Lay U1.5": "#2ecc71", "Lay O3.5": "#1abc9c", "Back FHG O1.5": "#16a085"}
SYS_TYPE = {"Lay U1.5": "LAY", "Lay O3.5": "LAY", "Back FHG O1.5": "BACK"}

st.title("🎯 Odds vs Implied Odds — Edge Analysis")
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid {G_ACCENT};'
    f'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:0.85rem;color:#b2dfdb">'
    f'Confirms the ROI in each league is backed by genuine pricing value, not just favourable variance — '
    f'by comparing the price actually taken to the price implied by how often the bet has actually won. '
    f'Updated: <strong>{EDGE.get("updated", "n/a")}</strong></div>',
    unsafe_allow_html=True
)

with st.expander("📖 How to read this page", expanded=False):
    st.markdown("""
**Average Odds** — the straight average of the lay/back price across every qualifying bet in that league.

**Win Rate** — % of qualifying bets that were profitable (empirical, from actual results).

**Implied Odds (from results)** — = 1 ÷ Win Rate. The decimal odds that would exactly break even given how
often the bet has actually won — i.e. the "fair price" for our own win rate.

**Effective Odds (LAY systems only)** — = Average Odds ÷ (Average Odds − 1). Laying a selection at price L
is mathematically equivalent to backing the *opposite* outcome at L/(L−1). Since win rate is defined on the
outcome we actually win on, Effective Odds — not the raw lay price — is the correct comparison against
Implied Odds.

**Edge %** — = (Comparison Odds ÷ Implied Odds − 1) × 100, where Comparison Odds is Effective Odds for LAY
systems and Average Odds for BACK systems. A positive Edge % means the price taken was consistently better
than what the actual win rate alone would justify — a genuine, structural edge rather than just having won
more than expected by chance.

⚠️ **Caveat:** every league shown here was already selected for positive ROI, so finding a positive edge
again is partly re-confirming the same signal rather than an independent test. It confirms the effect shows
up in the pricing itself (not purely in the P&L sequence), which is a meaningful sanity check — but it
is not proof against overfitting on its own.
""")

sys_name = st.selectbox("System", list(SYS_COLORS.keys()),
                         format_func=lambda x: f"🟢 {x}")

rows = EDGE.get("systems", {}).get(sys_name, [])
if not rows:
    st.warning("No edge data available for this system.")
    st.stop()

is_lay = SYS_TYPE[sys_name] == "LAY"
color = SYS_COLORS[sys_name]

df = pd.DataFrame(rows).sort_values("edge_pct", ascending=False).reset_index(drop=True)
total_bets = int(df["bets"].sum())
avg_edge = df["edge_pct"].mean()
avg_roi = (df["pl"].sum() / df["bets"].sum()) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Leagues", len(df))
k2.metric("Total bets", f"{total_bets:,}")
k3.metric("Avg edge", f"+{avg_edge:.1f}%")
k4.metric("Avg ROI", f"+{avg_roi:.1f}%")

st.divider()

# Bar chart: edge % per league
st.subheader("Edge % by league")
fig = go.Figure(go.Bar(
    x=df["comp"] + " [" + df["lo"].astype(str) + "–" + df["hi"].astype(str) + "]",
    y=df["edge_pct"],
    marker_color=[color if v >= 8 else "#f39c12" for v in df["edge_pct"]],
    text=[f"+{v:.1f}%" for v in df["edge_pct"]],
    textposition="outside",
))
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0), height=380,
    font=dict(color="#e8f5e9", size=11),
    xaxis=dict(showgrid=False, tickangle=-35),
    yaxis=dict(showgrid=True, gridcolor="#1a4a20", title="Edge %"),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Detail table
st.subheader("League detail")
disp = df.copy()
disp["Odds Range"] = disp["lo"].astype(str) + "–" + disp["hi"].astype(str)
cols_show = ["comp", "Odds Range", "bets", "avg_odds"]
rename = {"comp": "League", "bets": "Bets", "avg_odds": "Avg Odds"}
if is_lay:
    cols_show.append("avg_eff_odds")
    rename["avg_eff_odds"] = "Effective Odds"
cols_show += ["win_rate", "implied_odds", "edge_pct", "roi"]
rename.update({"win_rate": "Win %", "implied_odds": "Implied Odds", "edge_pct": "Edge %", "roi": "ROI %"})
disp = disp.rename(columns=rename)[[rename.get(c, c) for c in cols_show]]

st.dataframe(
    disp.style.format({
        "Avg Odds": "{:.2f}", "Effective Odds": "{:.2f}", "Win %": "{:.1f}%",
        "Implied Odds": "{:.3f}", "Edge %": "+{:.1f}%", "ROI %": "+{:.1f}%",
    }),
    use_container_width=True, hide_index=True, height=min(600, 60 + len(disp) * 35)
)

# Flag weakest edges
weakest = df.nsmallest(3, "edge_pct")
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid #f39c12;'
    f'border-radius:6px;padding:12px 16px;margin-top:12px;font-size:0.85rem;color:#e8d9b5">'
    f'<strong style="color:#fff">Thinnest cushion — watch these first if pricing tightens:</strong><br>'
    + " · ".join([f"{r['comp']} ({r['edge_pct']:+.1f}%)" for _, r in weakest.iterrows()])
    + '</div>',
    unsafe_allow_html=True
)
