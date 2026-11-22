"""
FTS Home Odds Portfolio — rebuild engine (single source of truth)
=================================================================

Turns an "FTS Advanced Results - Odds" Excel file (sheet FTSAdvanced) into
data/portfolio_master_sheet.json — the file every dashboard page reads.

Used by:
  * dashboard/pages/8_🔄_Update_Database.py  (upload in the browser)
  * scripts/update_dashboard.py               (run on your own computer)

The league / home-odds-band rules come from SYSTEM_DEFS in systems/all_systems.py
(the same rules the Daily Selector uses), so a rule change is made in ONE place.
Columns are found by header name, so the rebuild still works if FTS move columns.

Qualifying bet = league matches a rule AND Home Back Odds are inside that rule's band
AND the lay/back price is >= 1.00 and < 6.00.
Band boundaries: Lay U1.5 inclusive both ends (>= lo and <= hi); all other systems
exclusive upper (>= lo and < hi).
"""
from __future__ import annotations

import io
import json
from datetime import datetime

import pandas as pd

from systems.all_systems import SYSTEM_DEFS

ODDS_MIN, ODDS_MAX = 1.00, 6.00          # lay/back price filter: >= 1.00 and < 6.00
CLASSIFY_HEADER = "Home Back Odds"

# system -> (odds header, P/L header, key)
MARKETS = {
    "Lay U1.5":      ("U1.5 Lay Odds",    "U1.5 Lay PL",    "lay_u1_5"),
    "Lay O3.5":      ("O3.5 Lay Odds",    "O3.5 Lay PL",    "lay_o3_5"),
    "Back FHG O1.5": ("FHGO1.5 Back Odds", "FHGO1.5 Back PL", "back_fhg_o1_5"),
    "Lay FHG U0.5":  ("FHGU0.5 Lay Odds", "FHGU0.5 Lay PL", "lay_fhg_u0_5"),
    "Home Lay":      ("Home Lay Odds",    "Home Lay PL",    "home_lay"),
    "Away Lay":      ("Away Lay Odds",    "Away Lay PL",    "away_lay"),
    "Draw Lay":      ("Draw Lay Odds",    "Draw Lay PL",    "draw_lay"),
}
ALL_SYSTEMS = list(MARKETS)

# fallback column positions (Nov 2026 layout) if a header name ever changes
FALLBACK_IDX = {
    "Date": 0, "Time": 1, "Season": 2, "Competition": 3, "Home Team": 4, "Away Team": 5,
    "Home Back Odds": 12, "Home Lay Odds": 14, "Home Lay PL": 15, "Away Lay Odds": 18, "Away Lay PL": 19,
    "Draw Lay Odds": 22, "Draw Lay PL": 23, "U1.5 Lay Odds": 30, "U1.5 Lay PL": 31,
    "O3.5 Lay Odds": 37, "O3.5 Lay PL": 38, "FHGU0.5 Lay Odds": 40, "FHGU0.5 Lay PL": 41,
    "FHGO1.5 Back Odds": 47, "FHGO1.5 Back PL": 48,
}


def load_results(src) -> tuple[pd.DataFrame, list[str]]:
    """Read the FTSAdvanced sheet (path, bytes or file-like). Returns (df, notes)."""
    if isinstance(src, (bytes, bytearray)):
        src = io.BytesIO(src)
    xl = pd.ExcelFile(src)
    sheet = "FTSAdvanced" if "FTSAdvanced" in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    names = [str(x).strip() if pd.notna(x) else "" for x in raw.iloc[1]]
    notes, cols = [], {}
    for h in FALLBACK_IDX:
        if h in names:
            cols[h] = names.index(h)          # first occurrence
        else:
            cols[h] = FALLBACK_IDX[h]
            notes.append(f"Header '{h}' not found — using column {FALLBACK_IDX[h] + 1}")
    data = raw.iloc[2:]
    df = pd.DataFrame({h: data.iloc[:, i].values for h, i in cols.items()})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
    df = df[df["Date"].notna()].copy()
    for h in df.columns:
        if h not in ("Date", "Time", "Season", "Competition", "Home Team", "Away Team"):
            df[h] = pd.to_numeric(df[h], errors="coerce")
    df["Season"] = df["Season"].astype(str).str.strip()
    df["Time"] = df["Time"].map(_fmt_time)
    return df.reset_index(drop=True), notes


def _fmt_time(t):
    if pd.isna(t):
        return None
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    s = str(t)
    return s[:5] if len(s) >= 5 and s[2] == ":" else s


def build_bets(df: pd.DataFrame) -> list[dict]:
    """Run every system over the results and return one record per qualifying bet."""
    out = []
    for sd in SYSTEM_DEFS:
        system = sd["name"]
        o_h, p_h, key = MARKETS[system]
        incl = bool(sd.get("inclusive_upper"))
        for comp, lo, hi in sd["rules"]:
            hb = df["Home Back Odds"]
            band = (hb >= lo) & ((hb <= hi) if incl else (hb < hi))
            sub = df[(df["Competition"] == comp) & band & df[o_h].notna() & df[p_h].notna()
                     & (df[o_h] >= ODDS_MIN) & (df[o_h] < ODDS_MAX)]
            for r in sub.itertuples(index=False):
                pl = getattr(r, _attr(df, p_h))
                out.append({
                    "date": r[0].strftime("%Y-%m-%d"), "time": r[1], "season": r[2], "league": r[3],
                    "home": r[4], "away": r[5], "system": system, "system_key": key,
                    "pl": round(float(pl), 2), "won": bool(pl > 0),
                    "odds": round(float(getattr(r, _attr(df, o_h))), 2),
                    "home_odds": round(float(r[df.columns.get_loc("Home Back Odds")]), 2),
                })
    # a match can only qualify once per system (rules for one league are non-overlapping bands)
    seen, uniq = set(), []
    for b in sorted(out, key=lambda b: (b["date"], b["time"] or "", b["system"])):
        k = (b["date"], b["time"], b["league"], b["home"], b["away"], b["system"])
        if k not in seen:
            seen.add(k)
            uniq.append(b)
    return uniq


def _attr(df, header):
    """itertuples renames awkward column names positionally — find the attribute name."""
    return f"_{df.columns.get_loc(header)}"


def summarise(bets: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(bets)
    if d.empty:
        return d
    g = d.groupby("system").agg(Bets=("pl", "size"), PL=("pl", "sum"), Won=("won", "mean"))
    g["ROI %"] = g["PL"] / g["Bets"] * 100
    g["SR %"] = g["Won"] * 100
    g = g.drop(columns="Won").reindex([s for s in ALL_SYSTEMS if s in g.index])
    g.loc["TOTAL"] = [g["Bets"].sum(), g["PL"].sum(), g["PL"].sum() / g["Bets"].sum() * 100, d["won"].mean() * 100]
    return g.round(2)


def rebuild(src) -> tuple[list[dict], pd.DataFrame, list[str]]:
    df, notes = load_results(src)
    return build_bets(df), df, notes


def to_json_bytes(bets: list[dict]) -> bytes:
    return json.dumps(bets, separators=(",", ":")).encode()


def build_info(bets: list[dict], df: pd.DataFrame) -> dict:
    return {
        "built": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "results_to": df["Date"].max().strftime("%Y-%m-%d"),
        "source_rows": int(len(df)),
        "bets": len(bets),
    }
