"""Page 5: Results Dashboard — Historical performance with cumulative P&L curves"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def hex_alpha(hex_color, alpha=0.67):
    """Convert #rrggbb hex + alpha float to rgba() string."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


st.set_page_config(page_title="Results Dashboard", page_icon="📉", layout="wide")
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
import fts_ui as ui
ui.apply_theme()

# ── System figures — calculated live from data/portfolio_master_sheet.json ────
# (previously typed in by hand; now every upload of new results refreshes them)
def _build_system_data():
    df = ui.load_bets()
    out = {}
    for sys_name in ui.SYSTEM_ORDER:
        s = df[df["system"] == sys_name].sort_values("date")
        if s.empty:
            continue
        cum = s["pl"].cumsum().reset_index(drop=True)
        dd = cum - cum.cummax()
        trough = int(dd.idxmin())
        peak_i = int(cum.iloc[:trough + 1].idxmax()) if trough > 0 else 0
        dates = s["date"].reset_index(drop=True)
        def _grp(col, label):
            g = s.groupby(col).agg(pl=("pl", "sum"), bets=("pl", "size"),
                                   avg_xg=("home_odds", "mean"), avg_odds=("odds", "mean")).reset_index()
            g = g.rename(columns={col: label}).round({"pl": 2, "avg_xg": 3, "avg_odds": 3})
            return g.to_dict("records")
        comps = sorted(_grp("league", "Competition"), key=lambda r: -r["pl"])
        out[sys_name] = {
            "total_pl": round(float(s["pl"].sum()), 2), "total_bets": int(len(s)),
            "max_dd": round(float(dd.min()), 2),
            "dd_start": dates.iloc[peak_i].strftime("%Y-%m-%d"),
            "dd_end": dates.iloc[trough].strftime("%Y-%m-%d"),
            "avg_xg": round(float(s["home_odds"].mean()), 3),
            "avg_odds": round(float(s["odds"].mean()), 3),
            "color": ui.SYSTEM_COLORS[sys_name],
            "seasons": _grp("season", "Season"),
            "competitions": comps,
        }
    return out

SYSTEM_DATA = _build_system_data()

SYSTEMS = list(SYSTEM_DATA.keys())
TOTAL_PL   = sum(d["total_pl"]   for d in SYSTEM_DATA.values())
TOTAL_BETS = sum(d["total_bets"] for d in SYSTEM_DATA.values())
WORST_DD   = min(d["max_dd"]     for d in SYSTEM_DATA.values())
WORST_SYS  = min(SYSTEM_DATA, key=lambda k: SYSTEM_DATA[k]["max_dd"])
N_PROFIT   = sum(1 for d in SYSTEM_DATA.values() if d["total_pl"] > 0)
N_SEASONS  = ui.load_bets()["season"].nunique()
CUM_ENDPOINTS = {k: {"final": v["total_pl"]} for k, v in SYSTEM_DATA.items()}

# ── Load full bet-by-bet master sheet for accurate cum + drawdown ─────────────
def load_master_sheet():
    # shared loader — refreshes automatically when the data file is updated
    return ui.load_bets().sort_values("date")

def build_cum_curve(sys_name):
    """Return (dates, cum_pl, drawdown) from full bet-by-bet data."""
    df = load_master_sheet()
    sub = df[df["system"] == sys_name].sort_values("date").reset_index(drop=True)
    cum  = sub["pl"].cumsum().values
    peak = np.maximum.accumulate(cum)
    dd   = cum - peak
    dates = sub["date"].dt.strftime("%Y-%m-%d").tolist()
    return (
        dates,
        [round(float(x), 2) for x in cum],
        [round(float(x), 2) for x in dd],
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📉 Results Dashboard")
st.markdown(f"Historical performance across 3 live systems + 4 test · {N_SEASONS} seasons · results to {ui.load_bets()['date'].max():%d %b %Y}")
st.divider()

# ── Tab navigation ────────────────────────────────────────────────────────────
tab_overview, *_sys_tabs = st.tabs(["📊 Portfolio Overview"] + [f"{s} {'🟢' if s in ui.LIVE_SYSTEMS else '🧪'}" for s in ui.SYSTEM_ORDER])

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Portfolio P&L", f"+{TOTAL_PL:.2f} pts", "3 live systems + 4 test")
    c2.metric("🎯 Total Bets",           f"{TOTAL_BETS:,}",      f"Across {N_SEASONS} seasons")
    c3.metric("📉 Worst System DD",       f"{WORST_DD:.2f} pts",  WORST_SYS)
    c4.metric("✅ Systems Profitable",    f"{N_PROFIT} / {len(SYSTEM_DATA)}", f"{N_PROFIT/len(SYSTEM_DATA):.0%} of systems in profit")
    st.divider()

    # System summary cards
    st.subheader("System Summary")
    cols = st.columns(4)
    for i, sys in enumerate(SYSTEMS):
        d = SYSTEM_DATA[sys]
        with cols[i % 4]:
            roi = (d["total_pl"] / d["total_bets"]) * 100
            st.markdown(f"""
            <div style="background:#0D2219;border:1px solid {d['color']}44;
                        border-top:3px solid {d['color']};border-radius:10px;
                        padding:16px;margin-bottom:8px">
                <div style="color:{d['color']};font-weight:700;font-size:1rem;margin-bottom:8px">{sys}</div>
                <div style="font-size:1.8rem;font-weight:800;color:#3fb950">+{d['total_pl']:.2f}</div>
                <div style="color:#8DB5A0;font-size:0.75rem;margin-top:6px">
                    {d['total_bets']} bets · ROI: +{roi:.1f}%<br>
                    DD: <span style="color:#f85149">{d['max_dd']:.2f}</span> · 
                    Avg odds: {d['avg_odds']}
                </div>
            </div>""", unsafe_allow_html=True)
    st.divider()

    # Cumulative P&L — all systems on one chart
    st.subheader("Cumulative P&L — All Systems")
    fig_all = go.Figure()
    for sys in SYSTEMS:
        d = SYSTEM_DATA[sys]
        dates, values, _ = build_cum_curve(sys)
        fig_all.add_trace(go.Scatter(
            x=dates, y=values,
            name=sys,
            line=dict(color=d["color"], width=2.5),
            mode="lines",
            hovertemplate=f"<b>{sys}</b><br>Date: %{{x}}<br>P&L: %{{y:.2f}} pts<extra></extra>",
        ))
    fig_all.add_hline(y=0, line_dash="dot", line_color="#1F4A36")
    fig_all.update_layout(
        height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#e6edf3", size=12),
        xaxis=dict(gridcolor="rgba(48,54,61,0.27)", showgrid=True),
        yaxis=dict(gridcolor="rgba(48,54,61,0.27)", showgrid=True, title="Cumulative P&L (pts)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1F4A36", borderwidth=1),
        hovermode="x unified", margin=dict(t=20, b=40, l=60, r=20),
    )
    st.plotly_chart(fig_all, use_container_width=True)
    st.divider()

    # Side-by-side bar charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("P&L by System")
        fig_bar = go.Figure(go.Bar(
            x=SYSTEMS,
            y=[SYSTEM_DATA[s]["total_pl"] for s in SYSTEMS],
            marker_color=[SYSTEM_DATA[s]["color"] for s in SYSTEMS],
            text=[f"+{SYSTEM_DATA[s]['total_pl']:.1f}" for s in SYSTEMS],
            textposition="outside",
        ))
        fig_bar.update_layout(
            height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="P&L (pts)"),
            margin=dict(t=20, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Max Drawdown by System")
        fig_dd = go.Figure(go.Bar(
            x=[SYSTEM_DATA[s]["max_dd"] for s in SYSTEMS],
            y=SYSTEMS,
            orientation="h",
            marker_color='rgba(248,81,73,0.67)',
            marker_line_color="#f85149",
            marker_line_width=1.5,
            text=[f"{SYSTEM_DATA[s]['max_dd']:.2f}" for s in SYSTEMS],
            textposition="outside",
        ))
        fig_dd.update_layout(
            height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="Max Drawdown (pts)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            margin=dict(t=20, b=40, l=160, r=60),
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    # Bet distribution doughnut
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("Bet Volume by System")
        fig_pie = go.Figure(go.Pie(
            labels=SYSTEMS,
            values=[SYSTEM_DATA[s]["total_bets"] for s in SYSTEMS],
            marker=dict(colors=[SYSTEM_DATA[s]["color"] for s in SYSTEMS]),
            hole=0.5,
            textinfo="label+percent",
        ))
        fig_pie.update_layout(
            height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e6edf3"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1F4A36"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_d2:
        st.subheader("Avg Odds by System")
        fig_odds = go.Figure(go.Bar(
            x=SYSTEMS,
            y=[SYSTEM_DATA[s]["avg_odds"] for s in SYSTEMS],
            marker_color=[hex_alpha(SYSTEM_DATA[s]["color"]) for s in SYSTEMS],
            marker_line_color=[SYSTEM_DATA[s]["color"] for s in SYSTEMS],
            marker_line_width=1.5,
            text=[str(SYSTEM_DATA[s]["avg_odds"]) for s in SYSTEMS],
            textposition="outside",
        ))
        fig_odds.update_layout(
            height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e6edf3"), showlegend=False,
            xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.27)", title="Avg Odds", range=[0, 6]),
            margin=dict(t=20, b=40, l=60, r=20),
        )
        st.plotly_chart(fig_odds, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM TAB RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def render_system_tab(tab, sys_name):
    d = SYSTEM_DATA[sys_name]
    color = d["color"]
    roi = (d["total_pl"] / d["total_bets"]) * 100

    with tab:
        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total P&L",   f"+{d['total_pl']:.2f} pts")
        c2.metric("🎯 Total Bets",  f"{d['total_bets']:,}")
        c3.metric("📈 ROI",         f"+{roi:.2f}%")
        c4.metric("📉 Max Drawdown",f"{d['max_dd']:.2f} pts")

        # DD highlight
        st.markdown(f"""
        <div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.3);
                    border-radius:8px;padding:14px 20px;margin:12px 0;
                    display:flex;gap:40px;flex-wrap:wrap">
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Max Drawdown</div>
                 <div style="color:#f85149;font-weight:700;font-size:1.1rem">{d['max_dd']:.2f} pts</div></div>
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Peak Before DD</div>
                 <div style="font-weight:600">{d['dd_start']}</div></div>
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">DD Trough Date</div>
                 <div style="font-weight:600">{d['dd_end']}</div></div>
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Recovery Status</div>
                 <div style="color:#3fb950;font-weight:700">✓ Recovered</div></div>
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Avg Home Odds</div>
                 <div style="font-weight:600">{d['avg_xg']}</div></div>
            <div><div style="color:#8DB5A0;font-size:0.7rem;text-transform:uppercase;
                             letter-spacing:0.5px;margin-bottom:4px">Avg Odds</div>
                 <div style="font-weight:600">{d['avg_odds']}</div></div>
        </div>""", unsafe_allow_html=True)

        # Cumulative P&L + Drawdown — dual-axis single chart
        st.subheader("Cumulative P&L & Drawdown")
        dates, values, dd_arr = build_cum_curve(sys_name)

        fig_cum = go.Figure()

        # P&L line — left y-axis (y1)
        fig_cum.add_trace(go.Scatter(
            x=dates, y=values,
            fill="tozeroy",
            line=dict(color=color, width=2.5),
            fillcolor=hex_alpha(color, 0.13),
            mode="lines",
            name=sys_name,
            yaxis="y1",
            hovertemplate="P&L: %{y:.2f} pts<extra></extra>",
        ))

        # Drawdown line — right y-axis (y2)
        fig_cum.add_trace(go.Scatter(
            x=dates, y=dd_arr,
            line=dict(color="#f85149", width=1.5),
            mode="lines",
            name="Drawdown",
            yaxis="y2",
            hovertemplate="DD: %{y:.2f} pts<extra></extra>",
        ))

        fig_cum.update_layout(
            height=380,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e6edf3"),
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="v", x=1.08, y=1,
                font=dict(size=11), bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(t=20, b=40, l=65, r=75),
            xaxis=dict(
                gridcolor="rgba(48,54,61,0.27)", showgrid=True,
            ),
            yaxis=dict(
                title=dict(text="Cumulative P&L (units)", font=dict(color=color)),
                tickfont=dict(color=color),
                gridcolor="rgba(48,54,61,0.27)", showgrid=True,
                side="left",
            ),
            yaxis2=dict(
                title=dict(text="Drawdown (u)", font=dict(color="#f85149")),
                tickfont=dict(color="#f85149"),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=True,
                zerolinecolor="rgba(248,81,73,0.25)",
                zerolinewidth=1,
            ),
        )
        st.plotly_chart(fig_cum, use_container_width=True)

        # Season + Competition charts
        col_s, col_c = st.columns(2)

        with col_s:
            st.subheader("Results by Season")
            season_metric = st.selectbox("Metric", ["P&L (pts)","Bets","Avg Home Odds","Avg Odds"],
                                          key=f"sm_{sys_name}")
            metric_map = {"P&L (pts)":"pl","Bets":"bets","Avg Home Odds":"avg_xg","Avg Odds":"avg_odds"}
            m = metric_map[season_metric]

            # Merge calendar-year seasons into adjacent winter seasons
            # '2022'→'2022-2023', '2023'→'2023-2024', '2024'→'2024-2025', '2025'→'2025-2026'
            CAL_MERGE = {"2022":"2022-2023","2023":"2023-2024","2024":"2024-2025","2025":"2025-2026"}
            merged = {}
            for s in d["seasons"]:
                lbl = CAL_MERGE.get(s["Season"], s["Season"])
                if lbl not in merged:
                    merged[lbl] = {"Season":lbl,"pl":0,"bets":0,"avg_xg":[],"avg_odds":[]}
                merged[lbl]["pl"]    += s["pl"]
                merged[lbl]["bets"]  += s["bets"]
                merged[lbl]["avg_xg"].append(s.get("avg_xg",0))
                merged[lbl]["avg_odds"].append(s.get("avg_odds",0))
            for lbl in merged:
                xgs   = [v for v in merged[lbl]["avg_xg"]   if v]
                odds  = [v for v in merged[lbl]["avg_odds"]  if v]
                merged[lbl]["avg_xg"]   = round(sum(xgs)/len(xgs),3)   if xgs   else 0
                merged[lbl]["avg_odds"] = round(sum(odds)/len(odds),3)  if odds  else 0
            season_order = ["2021-2022","2022-2023","2023-2024","2024-2025","2025-2026"]
            seasons_merged = [merged[k] for k in season_order if k in merged]

            s_labels = [s["Season"] for s in seasons_merged]
            s_vals   = [s[m] for s in seasons_merged]
            s_colors = ['rgba(63,185,80,0.67)' if v >= 0 else 'rgba(248,81,73,0.53)' for v in s_vals] if m == "pl" else [hex_alpha(color)]*len(s_vals)
            s_borders= ["#3fb950" if v >= 0 else "#f85149" for v in s_vals] if m == "pl" else [color]*len(s_vals)

            fig_s = go.Figure(go.Bar(
                x=s_labels, y=s_vals,
                marker_color=s_colors,
                marker_line_color=s_borders,
                marker_line_width=1.5,
                text=[f"{v:+.2f}" if m=="pl" else f"{v:.3f}" for v in s_vals],
                textposition="outside",
            ))
            fig_s.update_layout(
                height=320, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e6edf3"), showlegend=False,
                xaxis=dict(gridcolor="rgba(48,54,61,0.27)", tickangle=0),
                yaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
                margin=dict(t=30, b=60, l=60, r=20),
            )
            st.plotly_chart(fig_s, use_container_width=True)

        with col_c:
            st.subheader("Results by Competition")
            comp_metric = st.selectbox("Metric", ["P&L (pts)","Bets","Avg Home Odds","Avg Odds"],
                                        key=f"cm_{sys_name}")
            m2 = metric_map[comp_metric]
            comps = sorted(d["competitions"], key=lambda x: x[m2], reverse=True)
            c_labels = [c["Competition"] for c in comps]
            c_vals   = [c[m2] for c in comps]
            c_colors = ['rgba(63,185,80,0.67)' if v >= 0 else 'rgba(248,81,73,0.53)' for v in c_vals] if m2=="pl" else [hex_alpha(color)]*len(c_vals)
            c_borders= ["#3fb950" if v >= 0 else "#f85149" for v in c_vals] if m2=="pl" else [color]*len(c_vals)

            fig_c = go.Figure(go.Bar(
                x=c_vals, y=c_labels,
                orientation="h",
                marker_color=c_colors,
                marker_line_color=c_borders,
                marker_line_width=1.5,
                text=[f"{v:+.2f}" if m2=="pl" else f"{v:.3f}" for v in c_vals],
                textposition="outside",
            ))
            fig_c.update_layout(
                height=320, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e6edf3", size=11), showlegend=False,
                xaxis=dict(gridcolor="rgba(48,54,61,0.27)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                margin=dict(t=30, b=40, l=180, r=60),
            )
            st.plotly_chart(fig_c, use_container_width=True)

        # Breakdowns tables
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader("Season Breakdown")
            sort_s = st.selectbox("Sort by", ["Chronological","P&L (desc)","Bets (desc)"],
                                   key=f"sort_s_{sys_name}")
            df_s = pd.DataFrame(d["seasons"])
            if sort_s == "P&L (desc)":   df_s = df_s.sort_values("pl", ascending=False)
            elif sort_s == "Bets (desc)": df_s = df_s.sort_values("bets", ascending=False)
            df_s_disp = df_s.rename(columns={"Season":"Season","pl":"P&L","bets":"Bets",
                                               "avg_xg":"Avg Home Odds","avg_odds":"Avg Odds"})
            df_s_disp["P&L"] = df_s_disp["P&L"].apply(lambda x: f"+{x:.2f}" if x>=0 else f"{x:.2f}")
            st.dataframe(df_s_disp, use_container_width=True, hide_index=True)

        with col_t2:
            st.subheader("Competition Breakdown")
            sort_c = st.selectbox("Sort by", ["P&L (desc)","Bets (desc)","Avg Home Odds","Avg Odds"],
                                   key=f"sort_c_{sys_name}")
            df_c = pd.DataFrame(d["competitions"])
            sort_col_map = {"P&L (desc)":"pl","Bets (desc)":"bets","Avg Home Odds":"avg_xg","Avg Odds":"avg_odds"}
            df_c = df_c.sort_values(sort_col_map[sort_c], ascending=False)
            df_c_disp = df_c.rename(columns={"Competition":"League","pl":"P&L","bets":"Bets",
                                              "avg_xg":"Avg Home Odds","avg_odds":"Avg Odds"})
            df_c_disp["P&L"] = df_c_disp["P&L"].apply(lambda x: f"+{x:.2f}" if x>=0 else f"{x:.2f}")
            st.dataframe(df_c_disp, use_container_width=True, hide_index=True)


# ── Render each system tab ────────────────────────────────────────────────────
for _t, _s in zip(_sys_tabs, ui.SYSTEM_ORDER):
    render_system_tab(_t, _s)
