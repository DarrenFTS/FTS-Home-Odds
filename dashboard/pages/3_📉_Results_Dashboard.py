"""Page 3: Results Dashboard — Per-system P&L curves, drawdown, season & league breakdown"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import sidebar_brand, G_PANEL, G_MID, G_ACCENT, PLOT_LAYOUT, hex_alpha, SYS_COLORS

st.set_page_config(page_title="Results Dashboard", page_icon="📉", layout="wide")
sidebar_brand()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "portfolio_data.json")
with open(DATA_PATH) as f:
    PORT = json.load(f)

st.title("📉 Results Dashboard")
st.markdown("Detailed historical performance per system — cumulative P&L, drawdown analysis, season and competition breakdown.")

SYSTEMS = list(PORT.keys())
tabs = st.tabs([f"{'🟢' if PORT[s]['live'] else '🔵'} {s}" for s in SYSTEMS])

for tab, sys_name in zip(tabs, SYSTEMS):
    with tab:
        d     = PORT[sys_name]
        color = d["color"]
        is_live = d["live"]

        # ── Header metrics ─────────────────────────────────────────────────────
        badge_col = "#2ecc71" if is_live else "#5dade2"
        badge_txt = "LIVE — actively staked" if is_live else "TEST — tracking only"
        st.markdown(
            f'<div style="background:{G_PANEL};border:1px solid {G_MID};'
            f'border-left:4px solid {color};border-radius:8px;'
            f'padding:14px 20px;margin-bottom:16px;display:flex;gap:40px;flex-wrap:wrap">'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Status</div>'
            f'<div style="color:{badge_col};font-weight:700;font-size:1rem">{badge_txt}</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Total P&L</div>'
            f'<div style="color:#2ecc71;font-weight:700;font-size:1.1rem">+{d["total_pl"]:.2f}u</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Total Bets</div>'
            f'<div style="font-weight:600">{d["total_bets"]:,}</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">ROI%</div>'
            f'<div style="font-weight:600">+{d["roi"]:.1f}%</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Win Rate</div>'
            f'<div style="font-weight:600">{d["win_rate"]:.1f}%</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Max Drawdown</div>'
            f'<div style="color:#e74c3c;font-weight:700">{d["max_dd"]:.2f}u</div></div>'
            f'<div><div style="color:#81c784;font-size:0.7rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;margin-bottom:4px">Rules</div>'
            f'<div style="font-weight:600">{len(d["rules"])}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── Cumulative P&L chart ───────────────────────────────────────────────
        st.subheader("Cumulative P&L Curve")
        dates  = d["monthly_dates"]
        values = d["monthly_cum_pl"]

        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=dates, y=values,
            fill="tozeroy",
            line=dict(color=color, width=2.5),
            fillcolor=hex_alpha(color, 0.12),
            mode="lines",
            name=sys_name,
            hovertemplate="Month: %{x}<br>Cumulative P&L: %{y:.2f}u<extra></extra>",
        ))

        # Drawdown shading — approximate from cumulative curve
        if values:
            peak_so_far = values[0]
            dd_x, dd_y = [], []
            for x, v in zip(dates, values):
                peak_so_far = max(peak_so_far, v)
                dd_x.append(x)
                dd_y.append(v - peak_so_far)
            fig_cum.add_trace(go.Scatter(
                x=dd_x, y=dd_y,
                fill="tozeroy",
                line=dict(color="#e74c3c", width=1),
                fillcolor="rgba(231,76,60,0.08)",
                mode="lines",
                name="Drawdown",
                yaxis="y2",
                hovertemplate="Drawdown: %{y:.2f}u<extra></extra>",
            ))
            fig_cum.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title="Drawdown (u)", tickfont=dict(color="#e74c3c"),
                            titlefont=dict(color="#e74c3c"))
            )

        fig_cum.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
        layout = dict(PLOT_LAYOUT)
        layout.update(dict(
            height=400,
            yaxis=dict(**PLOT_LAYOUT.get("yaxis", {}), title="Cumulative P&L (units)"),
            showlegend=True,
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#e8f5e9', size=11)),
            margin=dict(t=10, b=40, l=70, r=70),
        ))
        fig_cum.update_layout(**layout)
        st.plotly_chart(fig_cum, use_container_width=True)

        # ── Season + Competition charts ────────────────────────────────────────
        col_s, col_c = st.columns(2)

        with col_s:
            st.subheader("Results by Season")
            metric_s = st.selectbox("Metric", ["P&L (u)", "Bets", "ROI%"],
                                    key=f"sm_{sys_name}")
            key_map = {"P&L (u)": "pl", "Bets": "bets", "ROI%": "roi"}
            mk = key_map[metric_s]
            seasons = d["seasons"]
            sl = [s["season"] for s in seasons]
            sv = [s[mk] for s in seasons]
            sc = ['rgba(46,204,113,0.6)' if v >= 0 else 'rgba(231,76,60,0.5)' for v in sv] \
                 if mk in ("pl","roi") else [hex_alpha(color)] * len(sv)
            sb = ['#2ecc71' if v >= 0 else '#e74c3c' for v in sv] \
                 if mk in ("pl","roi") else [color] * len(sv)

            fig_s = go.Figure(go.Bar(
                x=sl, y=sv, marker_color=sc, marker_line_color=sb,
                marker_line_width=1.5,
                text=[f"{v:+.2f}" if mk in ("pl","roi") else str(v) for v in sv],
                textposition="outside",
            ))
            fig_s.update_layout(**{**PLOT_LAYOUT, "height": 320,
                "xaxis": dict(**PLOT_LAYOUT.get("xaxis",{}), tickangle=45),
                "margin": dict(t=30, b=80, l=60, r=20), "showlegend": False})
            st.plotly_chart(fig_s, use_container_width=True)

        with col_c:
            st.subheader("Results by Competition")
            metric_c = st.selectbox("Metric", ["P&L (u)", "Bets", "ROI%"],
                                    key=f"cm_{sys_name}")
            mk2 = key_map[metric_c]
            comps = sorted(d["competitions"], key=lambda x: x[mk2], reverse=True)
            cl = [c["comp"] for c in comps]
            cv = [c[mk2]   for c in comps]
            cc = ['rgba(46,204,113,0.6)' if v >= 0 else 'rgba(231,76,60,0.5)' for v in cv] \
                 if mk2 in ("pl","roi") else [hex_alpha(color)] * len(cv)
            cb = ['#2ecc71' if v >= 0 else '#e74c3c' for v in cv] \
                 if mk2 in ("pl","roi") else [color] * len(cv)

            fig_c = go.Figure(go.Bar(
                x=cv, y=cl, orientation="h",
                marker_color=cc, marker_line_color=cb, marker_line_width=1.5,
                text=[f"{v:+.2f}" if mk2 in ("pl","roi") else str(v) for v in cv],
                textposition="outside",
            ))
            fig_c.update_layout(**{**PLOT_LAYOUT, "height": 320,
                "margin": dict(t=30, b=40, l=200, r=70), "showlegend": False,
                "yaxis": dict(gridcolor="rgba(0,0,0,0)")})
            st.plotly_chart(fig_c, use_container_width=True)

        # ── Breakdown tables ───────────────────────────────────────────────────
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader("Season Breakdown")
            sort_s = st.selectbox("Sort by", ["Chronological", "P&L (desc)", "Bets (desc)"],
                                  key=f"sort_s_{sys_name}")
            df_s = pd.DataFrame(d["seasons"]).rename(
                columns={"season": "Season", "pl": "P&L", "bets": "Bets", "roi": "ROI%"}
            )
            if sort_s == "P&L (desc)":   df_s = df_s.sort_values("P&L", ascending=False)
            elif sort_s == "Bets (desc)": df_s = df_s.sort_values("Bets", ascending=False)
            df_s["P&L"] = df_s["P&L"].apply(lambda x: f"+{x:.2f}" if x >= 0 else f"{x:.2f}")
            df_s["ROI%"] = df_s["ROI%"].apply(lambda x: f"+{x:.1f}%")

            def style_pl(v):
                if str(v).startswith('+'): return 'color:#2ecc71;font-weight:bold'
                if str(v).startswith('-'): return 'color:#e74c3c;font-weight:bold'
                return ''

            st.dataframe(df_s.style.map(style_pl, subset=["P&L"]),
                         use_container_width=True, hide_index=True)

        with col_t2:
            st.subheader("Competition Breakdown")
            sort_c = st.selectbox("Sort by", ["P&L (desc)", "Bets (desc)", "ROI% (desc)"],
                                  key=f"sort_c_{sys_name}")
            df_c = pd.DataFrame(d["competitions"]).rename(
                columns={"comp": "League", "pl": "P&L", "bets": "Bets", "roi": "ROI%"}
            )
            scm = {"P&L (desc)": "P&L", "Bets (desc)": "Bets", "ROI% (desc)": "ROI%"}
            df_c = df_c.sort_values(scm[sort_c], ascending=False)
            df_c["P&L"]  = df_c["P&L"].apply(lambda x: f"+{x:.2f}" if x >= 0 else f"{x:.2f}")
            df_c["ROI%"] = df_c["ROI%"].apply(lambda x: f"+{x:.1f}%")
            st.dataframe(df_c.style.map(style_pl, subset=["P&L"]),
                         use_container_width=True, hide_index=True)

        # ── Rules table ────────────────────────────────────────────────────────
        st.subheader("System Rules")
        from systems.all_systems import HIST_ROI
        rules_rows = []
        for r in d["rules"]:
            roi = HIST_ROI.get((r["comp"], r["lo"], r["hi"], sys_name), 0.0)
            lo_buf = round(r["lo"] * 0.90, 2)
            hi_buf = round(r["hi"] * 1.10, 2)
            rules_rows.append({
                "Competition":     r["comp"],
                "Home Odds":       f"{r['lo']}–{r['hi']}",
                "Buffered (±10%)": f"{lo_buf:.2f}–{hi_buf:.2f}",
                "Hist ROI%":       f"+{roi:.1f}%",
            })
        df_rules = pd.DataFrame(rules_rows)
        st.dataframe(df_rules.style.map(
            lambda v: 'color:#2ecc71;font-weight:bold' if str(v).startswith('+') else '',
            subset=["Hist ROI%"]),
            use_container_width=True, hide_index=True)
