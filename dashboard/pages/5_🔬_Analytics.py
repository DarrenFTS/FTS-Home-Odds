"""Page 5: Analytics — Rolling ROI, distributions, deep-dive statistics"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, os, sys, math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import sidebar_brand, G_PANEL, G_MID, G_ACCENT, PLOT_LAYOUT, hex_alpha

st.set_page_config(page_title="Analytics", page_icon="🔬", layout="wide")
sidebar_brand()

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "portfolio_data.json")
with open(DATA_PATH) as f:
    PORT = json.load(f)

st.title("🔬 Analytics")
st.markdown("Deep-dive statistics across the portfolio — rolling performance, distributions, and risk metrics.")

SYSTEMS = list(PORT.keys())

# ── Tab layout ─────────────────────────────────────────────────────────────────
tab_roll, tab_dist, tab_risk, tab_compare = st.tabs([
    "📈 Rolling ROI", "📊 Distributions", "🛡️ Risk Metrics", "⚖️ System Comparison"
])

# ══ Rolling ROI ════════════════════════════════════════════════════════════════
with tab_roll:
    st.subheader("Rolling Monthly P&L by System")
    st.markdown("Each bar represents one calendar month's P&L. Green = profitable, red = losing.")

    sel_roll = st.multiselect("Systems to display",
                              SYSTEMS, default=SYSTEMS[:3],
                              key="roll_sys")

    if sel_roll:
        fig_roll = make_subplots(
            rows=len(sel_roll), cols=1,
            shared_xaxes=True,
            subplot_titles=[f"{'🟢' if PORT[s]['live'] else '🔵'} {s}" for s in sel_roll],
            vertical_spacing=0.08,
        )
        for i, sname in enumerate(sel_roll, 1):
            d      = PORT[sname]
            color  = d["color"]
            dates  = d["monthly_dates"]
            cumpl  = d["monthly_cum_pl"]
            # Derive monthly P&L from cumulative
            monthly_pl = [cumpl[0]] + [cumpl[j] - cumpl[j-1] for j in range(1, len(cumpl))]
            bar_colors = ['rgba(46,204,113,0.65)' if v >= 0 else 'rgba(231,76,60,0.55)'
                          for v in monthly_pl]
            bar_lines  = ['#2ecc71' if v >= 0 else '#e74c3c' for v in monthly_pl]

            fig_roll.add_trace(go.Bar(
                x=dates, y=monthly_pl,
                marker_color=bar_colors,
                marker_line_color=bar_lines,
                marker_line_width=1,
                name=sname,
                hovertemplate=f"{sname}<br>%{{x}}<br>P&L: %{{y:.2f}}u<extra></extra>",
                showlegend=False,
            ), row=i, col=1)
            fig_roll.add_hline(y=0, line_dash="dot",
                               line_color="rgba(255,255,255,0.15)", row=i, col=1)

        fig_roll.update_layout(
            height=260 * len(sel_roll),
            plot_bgcolor="#061208", paper_bgcolor="#061208",
            font=dict(color="#e8f5e9"),
            margin=dict(t=50, b=40, l=60, r=20),
            showlegend=False,
        )
        for i in range(1, len(sel_roll)+1):
            fig_roll.update_xaxes(gridcolor="rgba(46,204,113,0.08)", row=i, col=1)
            fig_roll.update_yaxes(gridcolor="rgba(46,204,113,0.08)",
                                  title_text="P&L (u)", row=i, col=1)
        st.plotly_chart(fig_roll, use_container_width=True)

# ══ Distributions ══════════════════════════════════════════════════════════════
with tab_dist:
    st.subheader("Season P&L Distribution")
    st.markdown("How are seasonal returns distributed across all systems?")

    all_season_pls = []
    for sname, d in PORT.items():
        for s in d["seasons"]:
            all_season_pls.append({
                "System": sname,
                "Season": s["season"],
                "P&L":    s["pl"],
                "Bets":   s["bets"],
                "ROI%":   s["roi"],
                "Live":   d["live"],
            })
    df_all = pd.DataFrame(all_season_pls)

    fig_box = go.Figure()
    for sname in SYSTEMS:
        sub = df_all[df_all["System"] == sname]["P&L"].tolist()
        color = PORT[sname]["color"]
        fig_box.add_trace(go.Box(
            y=sub, name=f"{'🟢' if PORT[sname]['live'] else '🔵'} {sname}",
            marker_color=color,
            line_color=color,
            fillcolor=hex_alpha(color, 0.25),
            boxpoints="all",
            jitter=0.4,
            pointpos=0,
            hovertemplate="%{y:.2f}u<extra></extra>",
        ))
    fig_box.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig_box.update_layout(**{
        **PLOT_LAYOUT,
        "height": 420,
        "yaxis": dict(**PLOT_LAYOUT.get("yaxis",{}), title="Season P&L (units)"),
        "showlegend": False,
        "margin": dict(t=20, b=80, l=60, r=20),
        "xaxis": dict(tickangle=30, gridcolor="rgba(46,204,113,0.05)"),
    })
    st.plotly_chart(fig_box, use_container_width=True)
    st.caption("Each dot = one season. Box shows median, IQR and whiskers. Green dot above zero line = profitable season.")

    st.divider()
    st.subheader("Losing vs Profitable Seasons")
    loss_data = []
    for sname, d in PORT.items():
        total_s  = len(d["seasons"])
        losing_s = sum(1 for s in d["seasons"] if s["pl"] < 0)
        loss_data.append({
            "System":          sname,
            "Status":          "🟢 LIVE" if d["live"] else "🔵 TEST",
            "Total Seasons":   total_s,
            "Profitable":      total_s - losing_s,
            "Losing":          losing_s,
            "Win Rate (Seas)": f"{((total_s-losing_s)/total_s*100):.0f}%" if total_s else "—",
        })
    st.dataframe(pd.DataFrame(loss_data), use_container_width=True, hide_index=True)

# ══ Risk Metrics ═══════════════════════════════════════════════════════════════
with tab_risk:
    st.subheader("Risk-Adjusted Metrics")
    st.markdown("Drawdown depth and portfolio risk profile by system.")

    risk_rows = []
    for sname, d in PORT.items():
        roi = d["roi"]
        dd  = abs(d["max_dd"])
        cal = roi / dd if dd > 0 else 0   # Calmar-style ratio (ROI / max DD)
        risk_rows.append({
            "System":         sname,
            "Status":         "🟢 LIVE" if d["live"] else "🔵 TEST",
            "ROI%":           f"+{roi:.1f}%",
            "Max Drawdown":   f"{d['max_dd']:.2f}u",
            "ROI/DD Ratio":   f"{cal:.2f}",
            "Bets/Season":    f"{d['total_bets'] / max(len(d['seasons']),1):.0f}",
            "Avg Season P&L": f"+{sum(s['pl'] for s in d['seasons'])/max(len(d['seasons']),1):.2f}u",
        })

    df_risk = pd.DataFrame(risk_rows)

    def style_risk(v):
        try:
            val = float(str(v).replace('%','').replace('+','').replace('u',''))
            if val > 0: return 'color:#2ecc71;font-weight:bold'
            if val < 0: return 'color:#e74c3c;font-weight:bold'
        except: pass
        if 'LIVE' in str(v): return 'color:#2ecc71;font-weight:bold'
        if 'TEST' in str(v): return 'color:#5dade2;font-weight:bold'
        return ''

    st.dataframe(
        df_risk.style.map(style_risk, subset=["Status","ROI%","Max Drawdown","Avg Season P&L"]),
        use_container_width=True, hide_index=True
    )

    st.markdown(
        f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-radius:6px;'
        f'padding:12px 16px;margin-top:8px;font-size:0.8rem;color:#81c784">'
        f'<b style="color:#e8f5e9">ROI/DD Ratio</b> = ROI% ÷ |Max Drawdown|. '
        f'Higher = more return per unit of drawdown risk. '
        f'Target: >1.0 for a healthy risk-return profile.'
        f'</div>',
        unsafe_allow_html=True
    )

    st.divider()
    st.subheader("Drawdown Comparison")
    dd_names  = [r["System"]  for r in risk_rows]
    dd_vals   = [abs(d["max_dd"]) for d in PORT.values()]
    dd_colors = [PORT[n]["color"] for n in dd_names]
    fig_dd = go.Figure(go.Bar(
        x=dd_names, y=dd_vals,
        marker_color=dd_colors,
        marker_line_color=[hex_alpha(c, 1.0) for c in dd_colors],
        marker_line_width=1.5,
        text=[f"{v:.1f}u" for v in dd_vals],
        textposition="outside",
    ))
    fig_dd.add_hline(y=20, line_dash="dash", line_color="#e74c3c",
                     annotation_text="DD limit (20u)", annotation_font_color="#e74c3c")
    fig_dd.update_layout(**{
        **PLOT_LAYOUT,
        "height": 350,
        "yaxis": dict(**PLOT_LAYOUT.get("yaxis",{}), title="Max Drawdown (units)"),
        "xaxis": dict(tickangle=20, gridcolor="rgba(46,204,113,0.05)"),
        "margin": dict(t=20, b=80, l=60, r=20),
        "showlegend": False,
    })
    st.plotly_chart(fig_dd, use_container_width=True)

# ══ System Comparison ══════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("Multi-Metric Radar — System Comparison")
    st.markdown("Select up to 4 systems to compare across 5 key metrics.")

    sel_radar = st.multiselect("Systems", SYSTEMS, default=SYSTEMS[:3], max_selections=4)

    if sel_radar:
        # Normalise metrics 0–1 across all systems
        all_rois = [PORT[s]["roi"]        for s in SYSTEMS]
        all_pls  = [PORT[s]["total_pl"]   for s in SYSTEMS]
        all_wrs  = [PORT[s]["win_rate"]   for s in SYSTEMS]
        all_dds  = [abs(PORT[s]["max_dd"])for s in SYSTEMS]
        all_bets = [PORT[s]["total_bets"] for s in SYSTEMS]

        def norm(val, vals):
            lo, hi = min(vals), max(vals)
            return (val - lo) / (hi - lo) if hi > lo else 0.5

        cats = ["ROI%", "Total P&L", "Win Rate", "Low Drawdown", "Volume"]
        fig_rad = go.Figure()
        for sname in sel_radar:
            d = PORT[sname]
            vals_n = [
                norm(d["roi"],           all_rois),
                norm(d["total_pl"],      all_pls),
                norm(d["win_rate"],      all_wrs),
                norm(-abs(d["max_dd"]),  [-x for x in all_dds]),  # lower DD = better
                norm(d["total_bets"],    all_bets),
            ]
            vals_n += [vals_n[0]]  # close polygon
            fig_rad.add_trace(go.Scatterpolar(
                r=vals_n, theta=cats + [cats[0]],
                fill="toself",
                name=f"{'🟢' if d['live'] else '🔵'} {sname}",
                line=dict(color=d["color"], width=2),
                fillcolor=hex_alpha(d["color"], 0.18),
            ))

        fig_rad.update_layout(
            polar=dict(
                bgcolor="#061208",
                radialaxis=dict(visible=True, range=[0,1], tickfont=dict(color="#81c784"),
                                gridcolor="rgba(46,204,113,0.15)"),
                angularaxis=dict(tickfont=dict(color="#e8f5e9", size=12),
                                 gridcolor="rgba(46,204,113,0.15)"),
            ),
            paper_bgcolor="#061208",
            font=dict(color="#e8f5e9"),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#e8f5e9')),
            height=500,
            margin=dict(t=60, b=60, l=80, r=80),
        )
        st.plotly_chart(fig_rad, use_container_width=True)
        st.caption("All axes normalised 0–1 across all 7 systems. Higher = better for all metrics (drawdown axis inverted so lower DD = higher score).")
