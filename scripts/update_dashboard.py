"""
Rebuild the dashboard data on your own computer (alternative to the Update Database page).

    python scripts/update_dashboard.py "FTS Advanced Results - Odds.xlsx"

Writes data/portfolio_master_sheet.json and data/build_info.json, then prints a summary.
Upload (or git push) those two files to GitHub and the dashboard refreshes.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from systems import portfolio_builder as pb  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
bets, df, notes = pb.rebuild(sys.argv[1])
for n in notes:
    print("NOTE:", n)
open(os.path.join(ROOT, "data", "portfolio_master_sheet.json"), "wb").write(pb.to_json_bytes(bets))
json.dump(pb.build_info(bets, df), open(os.path.join(ROOT, "data", "build_info.json"), "w"), indent=2)
print(pb.summarise(bets).to_string())
print(f"\nResults to {df['Date'].max():%d %b %Y} · {len(bets):,} bets written to data/")
