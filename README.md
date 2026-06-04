# FTS Home Odds Portfolio Dashboard

A Streamlit dashboard for the **FTS Home Odds Portfolio** — 7 betting systems driven by home odds band analysis rather than xG models.

🟢 **Live systems** (actively staked): Lay U1.5, Lay O3.5, Back FHG O1.5
🔵 **Test systems** (tracking only): Lay FHG U0.5, Home Lay, Away Lay, Draw Lay

---

## Portfolio Overview

| System | Rules | Bet Type | Status |
|--------|-------|----------|--------|
| Lay U1.5 | 12 | Lay Under 1.5 Goals | 🟢 LIVE |
| Lay O3.5 | 10 | Lay Over 3.5 Goals | 🟢 LIVE |
| Back FHG O1.5 | 7 | Back FH Over 1.5 Goals | 🟢 LIVE |
| Lay FHG U0.5 | 10 | Lay FH Under 0.5 Goals | 🔵 TEST |
| Home Lay | 10 | Lay Home Win | 🔵 TEST |
| Away Lay | 10 | Lay Away Win | 🔵 TEST |
| Draw Lay | 10 | Lay the Draw | 🔵 TEST |

All systems use **home odds bands** (not xG) as the filter criterion, with a **±10% buffer** applied in the daily selector to capture late price movement.

---

## Repository Structure

```
FTS-Home-Odds/
├── dashboard/
│   ├── 🎰_FTS_Home_Odds.py          # Home page
│   ├── theme.py                      # Shared dark green theme
│   └── pages/
│       ├── 1_🎯_Daily_Selector.py    # Upload PreMatch → generate bets
│       ├── 2_📊_Portfolio.py         # Portfolio overview & combined P&L
│       ├── 3_📉_Results_Dashboard.py # Per-system charts & breakdowns
│       ├── 4_📈_System_Performance.py# Rule-level edge analysis
│       ├── 5_🔬_Analytics.py         # Rolling ROI, radar, risk metrics
│       └── 6_🔄_Update_Database.py   # Upload new results to refresh data
├── systems/
│   ├── __init__.py
│   └── all_systems.py               # All 7 systems, rules, buffer logic
├── data/
│   └── portfolio_data.json          # Pre-computed historical stats
├── .streamlit/
│   └── config.toml                  # Dark green theme
├── requirements.txt
└── README.md
```

---

## Pages

### 🎯 Daily Selector
Upload the **FTS Advanced PreMatch Excel** file. The app scans all 7 systems using home odds bands with a ±10% buffer and returns:
- **LIVE bets** (green) — Lay U1.5, Lay O3.5 & Back FHG O1.5 selections to place
- **TEST bets** (blue) — Lay FHG U0.5, Home Lay, Away Lay, Draw Lay selections to track only
- Colour-coded table: ✅ in range vs ⚠️ buffer zone (recheck at kick-off)
- Downloadable Excel with LIVE and TEST on separate sheets

### 📊 Portfolio
Combined cumulative P&L chart for all 7 systems, system summary table, P&L and ROI bar comparisons, and bank management guidance.

### 📉 Results Dashboard
Per-system tab with:
- Cumulative P&L curve with drawdown overlay
- Monthly P&L bar charts by season and competition
- Sortable season and competition breakdown tables
- Full rules table with historical ROI per rule

### 📈 System Performance
- Rule-level ROI bar chart
- Competition P&L scatter plot (bubble size = ROI%)
- Cross-system comparison table with selected system highlighted

### 🔬 Analytics
- Rolling monthly P&L bar charts (multi-system)
- Season P&L box-plot distribution
- Risk-adjusted metrics (ROI/DD ratio)
- Multi-metric radar chart (up to 4 systems)

### 🔄 Update Database
Upload a new results file to recalculate all portfolio statistics. Overwrites `data/portfolio_data.json`.

---

## Setup & Deployment

### Local
```bash
git clone https://github.com/DarrenFTS/FTS-Home-Odds.git
cd FTS-Home-Odds
pip install -r requirements.txt
streamlit run dashboard/🎰_FTS_Home_Odds.py
```

### Streamlit Cloud
1. Push this repo to `github.com/DarrenFTS/FTS-Home-Odds`
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → `DarrenFTS/FTS-Home-Odds` → `dashboard/🎰_FTS_Home_Odds.py`
4. App name: `FTS Home Odds`

---

## System Rules

### Lay U1.5 🟢 LIVE
Boundary: >= lo AND <= hi (inclusive) | Lay odds cap: < 6.00 | Buffer: ±10%

| Competition | Home Odds Range | Hist ROI% |
|-------------|----------------|-----------|
| Irish Premier League | 1.00–1.50 | +49.9% |
| German Bundesliga | 1.50–2.25 | +21.5% |
| German Bundesliga | 3.00–3.25 | +51.6% |
| German Bundesliga 2 | 3.00–3.25 | +35.9% |
| Polish Ekstraklasa | 1.50–1.75 | +31.4% |
| Polish Ekstraklasa | 2.75–3.00 | +23.9% |
| English League One | 3.75–4.00 | +23.3% |
| English Championship | 2.50–2.75 | +14.7% |
| Turkish Super Lig | 2.25–2.50 | +25.1% |
| Dutch Eredivisie | 3.50–4.00 | +33.3% |
| Austrian Bundesliga | 2.00–2.25 | +27.7% |
| Danish Superligaen | 3.75–4.50 | +25.2% |

### Lay O3.5 🟢 LIVE
Boundary: >= lo AND < hi (exclusive upper) | Lay odds cap: < 6.00 | Buffer: ±10%

| Competition | Home Odds Range | Hist ROI% |
|-------------|----------------|-----------|
| Turkish Super Lig | 1.50–2.00 | +19.1% |
| Belgian Premier League | 4.00–4.50 | +45.4% |
| Spanish Primera Division | 3.50–4.00 | +38.0% |
| French Ligue 2 | 2.75–3.00 | +27.5% |
| Swedish Allsvenskan | 2.75–3.00 | +29.1% |
| Dutch Eerste Divisie | 1.25–1.50 | +23.1% |
| Danish Superligaen | 2.00–2.50 | +18.7% |
| Austrian Bundesliga | 1.00–2.00 | +14.4% |
| Dutch Eredivisie | 1.75–2.00 | +19.4% |
| Italian Serie A | 3.50–4.00 | +20.4% |

### Back FHG O1.5 🟢 LIVE
Boundary: >= lo AND < hi (exclusive upper) | Back odds cap: < 6.00 | Buffer: ±10%

| Competition | Home Odds Range | Hist ROI% |
|-------------|----------------|-----------|
| English League One | 1.75–2.00 | +21.5% |
| Italian Serie A | 4.00–4.50 | +39.6% |
| Swedish Allsvenskan | 2.50–2.75 | +34.5% |
| Norwegian Tippeligaen | 3.50–4.00 | +31.6% |
| Turkish Super Lig | 2.50–3.00 | +17.6% |
| German Bundesliga | 3.50–3.75 | +37.2% |
| Belgian Premier League | 3.00–3.25 | +29.8% |

---

## Bank Management

| Bank | Systems | Size | Stake |
|------|---------|------|-------|
| Live Bank | Lay U1.5 + Lay O3.5 + Back FHG O1.5 | 100 units | 1.0u flat |
| Test Bank | 4 test systems | Track only | No real stakes |

**Compound:** Monthly from month 4, upward only when above starting bank.
**Review trigger:** Bank falls below 60% → reduce stakes 20%.

---

## Data Sources
- **Historical results:** FTS_Advanced_Results_-_Odds.xlsx (Sheet: FTSAdvanced, header row 2)
- **PreMatch fixtures:** FTSAdvanced-PreMatch.xlsx (daily, uploaded via Daily Selector)
- **Backtested period:** Season 2021–22 through 2025–26
