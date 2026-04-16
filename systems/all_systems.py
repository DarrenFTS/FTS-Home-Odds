"""
FTS Home Odds Portfolio — 7 Systems
All systems use Home Back Odds bands (not xG).
Buffer: ±10% applied to home odds range for daily selector.

PreMatch file column mapping (header row 0, data from row 1 after re-header):
  Competition   : Col D  (idx 3)
  Home Team     : Col E  (idx 4)
  Away Team     : Col F  (idx 5)
  Home Back Odds: Col BX (idx 75)
  U1.5 Lay Odds : Col CK (idx 88)
  O3.5 Lay Odds : Col CQ (idx 94)
  FHGU0.5 Lay   : Col DA (idx 108) -- check against live file
  FHGO1.5 Back  : Col DC (idx 110) -- check against live file
  Home Lay Odds : Col O  (idx 14)
  Away Lay Odds : Col S  (idx 18)
  Draw Lay Odds : Col W  (idx 22)
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple

BUFFER = 0.10  # ±10% on home odds boundaries

# ── Column mapping for PreMatch file ─────────────────────────────────────────
PRE_COL = {
    'date':       0,   # Col A
    'time':       1,   # Col B
    'season':     2,   # Col C
    'comp':       3,   # Col D
    'home':       4,   # Col E
    'away':       5,   # Col F
    'home_odds':  75,  # Col BX — Home Win Back
    'u15_lay':    88,  # Col CK — U1.5 Lay Odds
    'o35_lay':    94,  # Col CQ — O3.5 Lay Odds
    'fhu05_lay': 108,  # Col DA — FHGU0.5 Lay Odds (verify per file)
    'fho15_back':115,  # Col DN — FHGO1.5 Back Odds (verify per file)
    'home_lay':   14,  # Col O  — Home Lay Odds
    'away_lay':   18,  # Col S  — Away Lay Odds
    'draw_lay':   22,  # Col W  — Draw Lay Odds
}


@dataclass
class BetSignal:
    date: str
    time: str
    season: str
    comp: str
    home: str
    away: str
    system: str
    live: bool
    bet_type: str   # LAY or BACK
    bet_label: str  # e.g. "O1.5" or "U3.5"
    home_odds: float
    lay_odds: float
    rule_lo: float
    rule_hi: float
    buf_lo: float
    buf_hi: float
    in_buffer: bool   # True = buffer zone only, False = exact range
    hist_roi: float


def load_fixture_file(path: str) -> pd.DataFrame:
    """Load an FTS Advanced PreMatch Excel. Returns normalised DataFrame."""
    raw = pd.read_excel(path, header=0)
    # Row 0 is the real header — re-apply
    raw.columns = raw.iloc[0]
    raw = raw.iloc[1:].reset_index(drop=True)

    # Build a clean frame by position
    out = pd.DataFrame()
    cols = list(raw.columns)

    def safe_col(idx, name):
        if idx < len(cols):
            return pd.to_numeric(raw.iloc[:, idx], errors='coerce') if name != 'text' else raw.iloc[:, idx]
        return pd.Series([np.nan] * len(raw))

    out['date']       = pd.to_datetime(raw.iloc[:, PRE_COL['date']], errors='coerce')
    out['time']       = raw.iloc[:, PRE_COL['time']].astype(str)
    out['season']     = raw.iloc[:, PRE_COL['season']].astype(str)
    out['comp']       = raw.iloc[:, PRE_COL['comp']].astype(str)
    out['home']       = raw.iloc[:, PRE_COL['home']].astype(str)
    out['away']       = raw.iloc[:, PRE_COL['away']].astype(str)
    out['home_odds']  = safe_col(PRE_COL['home_odds'], 'num')
    out['u15_lay']    = safe_col(PRE_COL['u15_lay'],   'num')
    out['o35_lay']    = safe_col(PRE_COL['o35_lay'],   'num')
    out['fhu05_lay']  = safe_col(PRE_COL['fhu05_lay'], 'num')
    out['fho15_back'] = safe_col(PRE_COL['fho15_back'],'num')
    out['home_lay']   = safe_col(PRE_COL['home_lay'],  'num')
    out['away_lay']   = safe_col(PRE_COL['away_lay'],  'num')
    out['draw_lay']   = safe_col(PRE_COL['draw_lay'],  'num')

    return out.dropna(subset=['comp']).reset_index(drop=True)


# ── System definitions ─────────────────────────────────────────────────────────
# Each rule: (competition, lo, hi)
# Historical ROI keyed by (comp, lo, hi, system)
HIST_ROI = {
    # Lay U1.5
    ("Irish Premier League",   1.00, 1.50, "Lay U1.5"): 54.2,
    ("German Bundesliga",      1.50, 2.25, "Lay U1.5"): 21.2,
    ("German Bundesliga",      3.00, 3.25, "Lay U1.5"): 44.6,
    ("German Bundesliga 2",    3.00, 3.25, "Lay U1.5"): 41.2,
    ("Polish Ekstraklasa",     1.50, 1.75, "Lay U1.5"): 29.8,
    ("German Bundesliga",      1.75, 2.00, "Lay U1.5"): 29.2,
    ("Polish Ekstraklasa",     2.75, 3.00, "Lay U1.5"): 28.4,
    ("English League One",     3.75, 4.00, "Lay U1.5"): 35.5,
    ("English Championship",   2.50, 2.75, "Lay U1.5"): 14.6,
    ("Dutch Eredivisie",       3.50, 4.00, "Lay U1.5"): 44.4,
    # Lay O3.5
    ("Turkish Super Lig",        1.50, 2.00, "Lay O3.5"): 18.8,
    ("Belgian Premier League",   4.00, 4.50, "Lay O3.5"): 43.5,
    ("Spanish Primera Division", 3.50, 4.00, "Lay O3.5"): 38.5,
    ("Turkish Super Lig",        1.75, 2.00, "Lay O3.5"): 21.9,
    ("French Ligue 2",           2.75, 3.00, "Lay O3.5"): 29.7,
    ("Spanish Primera Division", 3.50, 3.75, "Lay O3.5"): 40.6,
    ("Swedish Allsvenskan",      2.75, 3.00, "Lay O3.5"): 41.0,
    ("Belgian Premier League",   4.00, 5.00, "Lay O3.5"): 31.4,
    ("Spanish Primera Division", 3.00, 4.00, "Lay O3.5"): 21.2,
    ("Dutch Eerste Divisie",     1.25, 1.50, "Lay O3.5"): 24.0,
    # Lay FHG U0.5
    ("German Bundesliga",      3.50, 3.75, "Lay FHG U0.5"): 54.9,
    ("Irish Premier League",   1.00, 1.50, "Lay FHG U0.5"): 43.9,
    ("Spanish Primera Division",1.75,2.00, "Lay FHG U0.5"): 25.2,
    ("Brazilian Serie A",      1.50, 2.25, "Lay FHG U0.5"): 11.5,
    ("Polish Ekstraklasa",     2.00, 2.25, "Lay FHG U0.5"): 19.7,
    ("Swiss Super League",     3.00, 3.50, "Lay FHG U0.5"): 37.6,
    ("French Ligue 1",         1.00, 1.50, "Lay FHG U0.5"): 21.2,
    ("Brazilian Serie A",      3.00, 3.75, "Lay FHG U0.5"): 25.3,
    ("Polish Ekstraklasa",     1.25, 1.50, "Lay FHG U0.5"): 31.8,
    ("German Bundesliga",      3.00, 3.75, "Lay FHG U0.5"): 23.0,
    # Back FHG O1.5
    ("English League One",     1.75, 2.00, "Back FHG O1.5"): 22.4,
    ("Italian Serie A",        4.00, 4.50, "Back FHG O1.5"): 41.4,
    ("Swedish Allsvenskan",    2.50, 2.75, "Back FHG O1.5"): 37.1,
    ("Norwegian Tippeligaen",  3.50, 4.00, "Back FHG O1.5"): 42.1,
    ("Turkish Super Lig",      2.50, 3.00, "Back FHG O1.5"): 19.5,
    ("German Bundesliga",      3.50, 3.75, "Back FHG O1.5"): 37.2,
    # Home Lay
    ("Dutch Eredivisie",       5.00, 6.00, "Home Lay"): 66.5,
    ("USA MLS",                2.00, 3.00, "Home Lay"):  8.1,
    ("Italian Serie A",        4.50, 5.00, "Home Lay"): 46.4,
    ("Spanish Primera Division",4.50,5.25, "Home Lay"): 44.6,
    ("Turkish Super Lig",      3.00, 4.00, "Home Lay"): 18.5,
    ("Spanish Primera Division",4.00,5.00, "Home Lay"): 31.3,
    ("French Ligue 1",         5.00, 6.00, "Home Lay"): 34.5,
    ("English League One",     3.75, 4.50, "Home Lay"): 24.9,
    ("Japanese J-League",      3.25, 3.50, "Home Lay"): 39.2,
    ("Belgian Premier League", 2.00, 3.00, "Home Lay"): 11.2,
    # Away Lay
    ("Turkish Super Lig",      1.00, 2.00, "Away Lay"): 26.1,
    ("Turkish Super Lig",      1.50, 2.25, "Away Lay"): 19.4,
    ("Scottish Premiership",   1.00, 1.50, "Away Lay"): 48.8,
    ("Spanish Segunda Division",1.25,1.50, "Away Lay"): 63.7,
    ("Dutch Eredivisie",       1.25, 1.50, "Away Lay"): 32.1,
    ("Spanish Primera Division",2.00,2.50, "Away Lay"): 18.7,
    ("USA MLS",                1.00, 1.50, "Away Lay"): 28.7,
    ("Portuguese Primeira Liga",1.25,1.50, "Away Lay"): 28.8,
    ("Irish Premier League",   2.00, 2.50, "Away Lay"): 30.4,
    ("Belgian Premier League", 1.75, 2.00, "Away Lay"): 23.2,
    # Draw Lay
    ("Turkish Super Lig",      3.75, 4.50, "Draw Lay"): 67.0,
    ("Spanish Primera Division",1.25,1.50, "Draw Lay"): 36.1,
    ("Italian Serie A",        5.00, 6.00, "Draw Lay"): 40.7,
    ("English League One",     2.50, 2.75, "Draw Lay"): 21.8,
    ("Norwegian Tippeligaen",  1.25, 1.50, "Draw Lay"): 44.7,
    ("Norwegian Tippeligaen",  2.00, 3.00, "Draw Lay"): 16.6,
    ("Spanish Primera Division",1.75,2.00, "Draw Lay"): 18.2,
    ("South Korean K League Classic",2.75,3.00,"Draw Lay"): 32.2,
    ("French Ligue 2",         4.00, 5.00, "Draw Lay"): 30.7,
    ("English Championship",   2.75, 3.00, "Draw Lay"): 19.7,
}

SYSTEM_DEFS = [
    {
        "name": "Lay U1.5",
        "live": True,
        "bet_type": "LAY",
        "bet_label": "O1.5",
        "odds_key": "u15_lay",
        "color": "#2ecc71",
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
    {
        "name": "Lay O3.5",
        "live": True,
        "bet_type": "LAY",
        "bet_label": "U3.5",
        "odds_key": "o35_lay",
        "color": "#1abc9c",
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
    {
        "name": "Lay FHG U0.5",
        "live": False,
        "bet_type": "LAY",
        "bet_label": "FHO0.5",
        "odds_key": "fhu05_lay",
        "color": "#27ae60",
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
    {
        "name": "Back FHG O1.5",
        "live": False,
        "bet_type": "BACK",
        "bet_label": "FHO1.5",
        "odds_key": "fho15_back",
        "color": "#16a085",
        "rules": [
            ("English League One",    1.75, 2.00),
            ("Italian Serie A",       4.00, 4.50),
            ("Swedish Allsvenskan",   2.50, 2.75),
            ("Norwegian Tippeligaen", 3.50, 4.00),
            ("Turkish Super Lig",     2.50, 3.00),
            ("German Bundesliga",     3.50, 3.75),
        ]
    },
    {
        "name": "Home Lay",
        "live": False,
        "bet_type": "LAY",
        "bet_label": "Home",
        "odds_key": "home_lay",
        "color": "#1e8449",
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
    {
        "name": "Away Lay",
        "live": False,
        "bet_type": "LAY",
        "bet_label": "Away",
        "odds_key": "away_lay",
        "color": "#145a32",
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
    {
        "name": "Draw Lay",
        "live": False,
        "bet_type": "LAY",
        "bet_label": "Draw",
        "odds_key": "draw_lay",
        "color": "#0e6655",
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
]


def scan_all_systems(fixtures: pd.DataFrame) -> List[BetSignal]:
    """Run all 7 systems against fixture DataFrame. Returns sorted signal list."""
    signals = []
    for sys in SYSTEM_DEFS:
        sname    = sys["name"]
        odds_key = sys["odds_key"]
        bet_type = sys["bet_type"]
        bet_lab  = sys["bet_label"]
        live     = sys["live"]

        for comp, lo, hi in sys["rules"]:
            lo_buf = round(lo * (1 - BUFFER), 2)
            hi_buf = round(hi * (1 + BUFFER), 2)

            mask = fixtures['comp'] == comp
            if not mask.any():
                continue

            sub = fixtures[mask].copy()
            ho  = pd.to_numeric(sub['home_odds'], errors='coerce')
            lay = pd.to_numeric(sub[odds_key],    errors='coerce') if odds_key in sub.columns else pd.Series([np.nan]*len(sub))

            for idx, row in sub.iterrows():
                h = ho.loc[idx]
                l = lay.loc[idx]
                if pd.isna(h) or h == 0:
                    continue
                if pd.isna(l) or l <= 0 or l >= 6.0:
                    continue
                if not (lo_buf <= h <= hi_buf):
                    continue
                in_buf = not (lo <= h <= hi)
                roi = HIST_ROI.get((comp, lo, hi, sname), 0.0)
                signals.append(BetSignal(
                    date=str(row['date'])[:10] if not pd.isna(row['date']) else '',
                    time=str(row['time']),
                    season=str(row['season']),
                    comp=comp,
                    home=str(row['home']),
                    away=str(row['away']),
                    system=sname,
                    live=live,
                    bet_type=bet_type,
                    bet_label=bet_lab,
                    home_odds=round(float(h), 2),
                    lay_odds=round(float(l), 2),
                    rule_lo=lo,
                    rule_hi=hi,
                    buf_lo=lo_buf,
                    buf_hi=hi_buf,
                    in_buffer=in_buf,
                    hist_roi=roi,
                ))

    signals.sort(key=lambda s: (s.date, s.time, s.comp, s.home, s.system))
    return signals


def signals_to_dataframe(signals: List[BetSignal]) -> pd.DataFrame:
    if not signals:
        return pd.DataFrame()
    return pd.DataFrame([{
        'Date':       s.date,
        'Time':       s.time,
        'League':     s.comp,
        'Home':       s.home,
        'Away':       s.away,
        'System':     s.system,
        'Status':     '🟢 LIVE' if s.live else '🔵 TEST',
        'Bet':        s.bet_label,
        'Type':       s.bet_type,
        'Home Odds':  s.home_odds,
        'Lay Odds':   s.lay_odds,
        'Rule Range': f"{s.rule_lo}–{s.rule_hi}",
        'Buffered':   f"{s.buf_lo:.2f}–{s.buf_hi:.2f}",
        'In Buffer':  '⚠️ Check KO' if s.in_buffer else '✅ In Range',
        'Hist ROI':   f"+{s.hist_roi:.1f}%",
        '_live':      s.live,
        '_in_buf':    s.in_buffer,
    } for s in signals])
