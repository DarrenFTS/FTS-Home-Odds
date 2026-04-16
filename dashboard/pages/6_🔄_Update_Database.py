"""Page 6: Update Database — Upload new results file to refresh portfolio data"""
import streamlit as st
import pandas as pd
import numpy as np
import json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dashboard.theme import sidebar_brand, G_PANEL, G_MID, G_ACCENT

st.set_page_config(page_title="Update Database", page_icon="🔄", layout="wide")
sidebar_brand()

st.title("🔄 Update Database")
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-left:3px solid {G_ACCENT};'
    f'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:0.85rem;color:#b2dfdb">'
    f'Upload the latest <strong style="color:#fff">FTS Advanced Results — Odds.xlsx</strong> file to '
    f'regenerate all portfolio statistics. This will overwrite '
    f'<code>data/portfolio_data.json</code> with fresh calculations from the new data.</div>',
    unsafe_allow_html=True
)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "data", "portfolio_data.json")

# Show current data status
if os.path.exists(DATA_PATH):
    with open(DATA_PATH) as f:
        current = json.load(f)
    c1, c2, c3 = st.columns(3)
    total_bets = sum(v["total_bets"] for v in current.values())
    total_pl   = sum(v["total_pl"]   for v in current.values())
    c1.metric("Current Total Bets", f"{total_bets:,}")
    c2.metric("Current Total P&L",  f"+{total_pl:.2f}u")
    c3.metric("Systems Loaded",     len(current))
else:
    st.warning("No portfolio data found. Upload a results file to generate it.")

st.divider()

uploaded = st.file_uploader(
    "Upload FTS Advanced Results — Odds.xlsx",
    type=['xlsx','xls'],
    help="This should be the full historical results file, not the PreMatch file."
)

if uploaded:
    st.info("Processing results file — this may take a moment for large datasets...")
    with st.spinner("Loading and calculating..."):
        try:
            tmp = f"/tmp/results_{date.today()}.xlsx"
            with open(tmp, 'wb') as f:
                f.write(uploaded.read())

            df = pd.read_excel(tmp, header=1, sheet_name='FTSAdvanced')
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date').reset_index(drop=True)
            st.success(f"✅ Loaded {len(df):,} rows from results file.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    # ── System definitions (mirrors all_systems.py) ────────────────────────────
    SYSTEMS_CFG = {
        "Lay U1.5": {
            "pl_col": "U1.5 Lay PL", "odds_col": "U1.5 Lay Odds",
            "color": "#2ecc71", "live": True,
            "rules": [
                ("Irish Premier League",   1.00, 1.50),
                ("German Bundesliga",      1.50, 2.25),
                ("German Bundesliga",      3.00, 3.25),
                ("German Bundesliga 2",    3.00, 3.25),
                ("Polish Ekstraklasa",     1.50, 1.75),
                ("German Bundesliga",      1.75, 2.00),
                ("Polish Ekstraklasa",     2.75, 3.00),
                ("English League One",     3.75, 4.00),
                ("English Championship",   2.50, 2.75),
                ("Dutch Eredivisie",       3.50, 4.00),
            ]
        },
        "Lay O3.5": {
            "pl_col": "O3.5 Lay PL", "odds_col": "O3.5 Lay Odds",
            "color": "#1abc9c", "live": True,
            "rules": [
                ("Turkish Super Lig",        1.50, 2.00),
                ("Belgian Premier League",   4.00, 4.50),
                ("Spanish Primera Division", 3.50, 4.00),
                ("Turkish Super Lig",        1.75, 2.00),
                ("French Ligue 2",           2.75, 3.00),
                ("Spanish Primera Division", 3.50, 3.75),
                ("Swedish Allsvenskan",      2.75, 3.00),
                ("Belgian Premier League",   4.00, 5.00),
                ("Spanish Primera Division", 3.00, 4.00),
                ("Dutch Eerste Divisie",     1.25, 1.50),
            ]
        },
        "Lay FHG U0.5": {
            "pl_col": "FHGU0.5 Lay PL", "odds_col": "FHGU0.5 Lay Odds",
            "color": "#27ae60", "live": False,
            "rules": [
                ("German Bundesliga",       3.50, 3.75),
                ("Irish Premier League",    1.00, 1.50),
                ("Spanish Primera Division",1.75, 2.00),
                ("Brazilian Serie A",       1.50, 2.25),
                ("Polish Ekstraklasa",      2.00, 2.25),
                ("Swiss Super League",      3.00, 3.50),
                ("French Ligue 1",          1.00, 1.50),
                ("Brazilian Serie A",       3.00, 3.75),
                ("Polish Ekstraklasa",      1.25, 1.50),
                ("German Bundesliga",       3.00, 3.75),
            ]
        },
        "Back FHG O1.5": {
            "pl_col": "FHGO1.5 Back PL", "odds_col": "FHGO1.5 Back Odds",
            "color": "#16a085", "live": False,
            "rules": [
                ("English League One",    1.75, 2.00),
                ("Italian Serie A",       4.00, 4.50),
                ("Swedish Allsvenskan",   2.50, 2.75),
                ("Norwegian Tippeligaen", 3.50, 4.00),
                ("Turkish Super Lig",     2.50, 3.00),
                ("German Bundesliga",     3.50, 3.75),
            ]
        },
        "Home Lay": {
            "pl_col": "Home Lay PL", "odds_col": "Home Lay Odds",
            "color": "#1e8449", "live": False,
            "rules": [
                ("Dutch Eredivisie",        5.00, 6.00),
                ("USA MLS",                 2.00, 3.00),
                ("Italian Serie A",         4.50, 5.00),
                ("Spanish Primera Division",4.50, 5.25),
                ("Turkish Super Lig",       3.00, 4.00),
                ("Spanish Primera Division",4.00, 5.00),
                ("French Ligue 1",          5.00, 6.00),
                ("English League One",      3.75, 4.50),
                ("Japanese J-League",       3.25, 3.50),
                ("Belgian Premier League",  2.00, 3.00),
            ]
        },
        "Away Lay": {
            "pl_col": "Away Lay PL", "odds_col": "Away Lay Odds",
            "color": "#145a32", "live": False,
            "rules": [
                ("Turkish Super Lig",       1.00, 2.00),
                ("Turkish Super Lig",       1.50, 2.25),
                ("Scottish Premiership",    1.00, 1.50),
                ("Spanish Segunda Division",1.25, 1.50),
                ("Dutch Eredivisie",        1.25, 1.50),
                ("Spanish Primera Division",2.00, 2.50),
                ("USA MLS",                 1.00, 1.50),
                ("Portuguese Primeira Liga",1.25, 1.50),
                ("Irish Premier League",    2.00, 2.50),
                ("Belgian Premier League",  1.75, 2.00),
            ]
        },
        "Draw Lay": {
            "pl_col": "Draw Lay PL", "odds_col": "Draw Lay Odds",
            "color": "#0e6655", "live": False,
            "rules": [
                ("Turkish Super Lig",            3.75, 4.50),
                ("Spanish Primera Division",     1.25, 1.50),
                ("Italian Serie A",              5.00, 6.00),
                ("English League One",           2.50, 2.75),
                ("Norwegian Tippeligaen",        1.25, 1.50),
                ("Norwegian Tippeligaen",        2.00, 3.00),
                ("Spanish Primera Division",     1.75, 2.00),
                ("South Korean K League Classic",2.75, 3.00),
                ("French Ligue 2",               4.00, 5.00),
                ("English Championship",         2.75, 3.00),
            ]
        },
    }

    ODDS_COLS = {
        "Lay U1.5":      "U1.5 Lay Odds",
        "Lay O3.5":      "O3.5 Lay Odds",
        "Lay FHG U0.5":  "FHGU0.5 Lay Odds",
        "Back FHG O1.5": "FHGO1.5 Back Odds",
        "Home Lay":      "Home Lay Odds",
        "Away Lay":      "Away Lay Odds",
        "Draw Lay":      "Draw Lay Odds",
    }

    with st.spinner("Recalculating portfolio statistics..."):
        output = {}
        progress = st.progress(0)
        for idx, (sys_name, cfg) in enumerate(SYSTEMS_CFG.items()):
            pl_col   = cfg["pl_col"]
            odds_col = ODDS_COLS.get(sys_name)
            rules    = cfg["rules"]

            if pl_col not in df.columns:
                st.warning(f"Column '{pl_col}' not found — skipping {sys_name}")
                continue

            all_bets = []
            for comp, lo, hi in rules:
                mask = (
                    (df['Competition'] == comp) &
                    (df['Home Back Odds'] >= lo) &
                    (df['Home Back Odds'] <= hi) &
                    (df[pl_col].notna())
                )
                if odds_col and odds_col in df.columns:
                    mask &= (df[odds_col] >= 1.0) & (df[odds_col] < 6.0)
                sub = df[mask].copy()
                sub['_rule'] = f"{comp} {lo}–{hi}"
                all_bets.append(sub)

            if not all_bets:
                continue

            combined  = pd.concat(all_bets).sort_values('Date').reset_index(drop=True)
            total_pl  = combined[pl_col].sum()
            total_bets= len(combined)
            win_rate  = (combined[pl_col] > 0).mean() * 100
            roi       = total_pl / total_bets * 100 if total_bets else 0

            combined['cum_pl'] = combined[pl_col].cumsum()
            combined['peak']   = combined['cum_pl'].cummax()
            combined['dd']     = combined['cum_pl'] - combined['peak']
            max_dd = combined['dd'].min()

            combined['month'] = combined['Date'].dt.to_period('M')
            monthly = combined.groupby('month').agg(
                pl=(pl_col, 'sum'), bets=(pl_col, 'count')
            ).reset_index()
            monthly['month_str'] = monthly['month'].astype(str)
            monthly['cum_pl']    = monthly['pl'].cumsum()

            season_pl = combined.groupby('Season')[pl_col].agg(['sum','count']).reset_index()
            season_pl.columns = ['Season','pl','bets']
            season_pl['roi'] = season_pl['pl'] / season_pl['bets'] * 100

            comp_pl = combined.groupby('Competition')[pl_col].agg(['sum','count']).reset_index()
            comp_pl.columns = ['Competition','pl','bets']
            comp_pl['roi'] = comp_pl['pl'] / comp_pl['bets'] * 100
            comp_pl = comp_pl.sort_values('pl', ascending=False)

            output[sys_name] = {
                "total_pl":       round(total_pl, 2),
                "total_bets":     int(total_bets),
                "win_rate":       round(win_rate, 1),
                "roi":            round(roi, 2),
                "max_dd":         round(max_dd, 2),
                "color":          cfg["color"],
                "live":           cfg["live"],
                "monthly_dates":  monthly['month_str'].tolist(),
                "monthly_cum_pl": [round(v,2) for v in monthly['cum_pl'].tolist()],
                "seasons": season_pl.apply(
                    lambda r: {'season': r['Season'], 'pl': round(r['pl'],2),
                               'bets': int(r['bets']), 'roi': round(r['roi'],2)}, axis=1
                ).tolist(),
                "competitions": comp_pl.apply(
                    lambda r: {'comp': r['Competition'], 'pl': round(r['pl'],2),
                               'bets': int(r['bets']), 'roi': round(r['roi'],2)}, axis=1
                ).tolist(),
                "rules": [{"comp": r[0], "lo": r[1], "hi": r[2]} for r in rules],
            }
            progress.progress((idx + 1) / len(SYSTEMS_CFG))

    if output:
        with open(DATA_PATH, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        st.success("✅ Portfolio data updated successfully!")
        c1, c2, c3 = st.columns(3)
        new_bets = sum(v["total_bets"] for v in output.values())
        new_pl   = sum(v["total_pl"]   for v in output.values())
        c1.metric("New Total Bets", f"{new_bets:,}", f"{new_bets - total_bets:+,}")
        c2.metric("New Total P&L",  f"+{new_pl:.2f}u")
        c3.metric("Systems Updated",len(output))

        st.markdown(
            f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-radius:6px;'
            f'padding:12px 16px;margin-top:12px;color:#81c784;font-size:0.85rem">'
            f'✅ <code>data/portfolio_data.json</code> has been updated. '
            f'Navigate to any other page to see refreshed statistics. '
            f'Note: commit the updated JSON to GitHub to persist changes on Streamlit Cloud.'
            f'</div>',
            unsafe_allow_html=True
        )

        # Summary table
        rows = []
        for sname, d in output.items():
            rows.append({
                "System":    sname,
                "Bets":      d["total_bets"],
                "P&L":       f"+{d['total_pl']:.2f}u",
                "ROI%":      f"+{d['roi']:.1f}%",
                "Max DD":    f"{d['max_dd']:.2f}u",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.error("No data was generated. Check that the correct results file was uploaded.")

st.divider()
st.markdown(
    f'<div style="background:{G_PANEL};border:1px solid {G_MID};border-radius:6px;'
    f'padding:14px 18px;color:#81c784;font-size:0.8rem">'
    f'<b style="color:#e8f5e9">ℹ️ File requirements:</b> '
    f'The results file must be <code>FTS_Advanced_Results_-_Odds.xlsx</code> with sheet '
    f'<code>FTSAdvanced</code> and a header row at row 2. '
    f'Required columns: Competition, Home Back Odds, U1.5 Lay PL/Odds, O3.5 Lay PL/Odds, '
    f'FHGU0.5 Lay PL/Odds, FHGO1.5 Back PL, Home/Away/Draw Lay PL/Odds.'
    f'</div>',
    unsafe_allow_html=True
)
