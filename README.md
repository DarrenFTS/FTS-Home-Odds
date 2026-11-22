# FTS Home Odds Portfolio Dashboard

Same design and tabs as the FTS xG dashboard, on an emerald-green background so the two are easy to tell apart.
3 LIVE systems (Lay U1.5, Lay O3.5, Back FHG O1.5) + 4 TEST systems (Lay FHG U0.5, Home Lay, Away Lay, Draw Lay).

Tabs: Home · Daily Selector · Portfolio · Results Dashboard · System Performance (incl. Monte Carlo) · Analytics ·
Odds Edge Analysis · Price Leak Calculator · Update Database.

- `fts_ui.py` – shared colours, CSS and data loading (change the look in one place)
- `data/portfolio_master_sheet.json` – every qualifying bet; all pages read this one file
- `systems/all_systems.py` – the league / home-odds-band rules (`SYSTEM_DEFS`), used by the Daily Selector AND the rebuild
- `systems/portfolio_builder.py` – turns the FTS Advanced Results – Odds Excel into the bet file
- `scripts/update_dashboard.py` – optional: rebuild on your own computer

Monthly update: Update Database tab → drop in the results Excel → Rebuild → Save (or upload the two files in `data/` to GitHub).
Rule change: edit `SYSTEM_DEFS` in `systems/all_systems.py`, then run an update.
