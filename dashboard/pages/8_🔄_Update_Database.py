"""
Update Database — monthly refresh in one upload.

Upload the latest FTS Advanced Results Excel → every system (3 live + 4 test)
is rebuilt from scratch with the rules in systems/all_systems.py (SYSTEM_DEFS) →
data/portfolio_master_sheet.json is replaced → every page refreshes.

Streamlit Cloud forgets files written by the app when it restarts, so the new data
must also be saved to GitHub: automatically (if a GitHub token is set in the app's
Secrets) or by downloading the file and uploading it to the data/ folder.
"""
import base64
import json
import os as _os
import sys as _sys

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Update Database", page_icon="🔄", layout="wide")
_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_sys.path.insert(0, _ROOT)
import fts_ui as ui  # noqa: E402
from systems import portfolio_builder as pb  # noqa: E402

ui.apply_theme()
ui.hero("🔄", "Update Database", "Upload the latest FTS Advanced Results – Odds file — every page refreshes from it")

try:
    GH = dict(st.secrets.get("github", {}))
except Exception:  # no secrets file set up
    GH = {}
HAS_GH = bool(GH.get("token"))


def gh_put(path_in_repo: str, content: bytes, message: str) -> str:
    """Create/replace one file in the GitHub repo. Returns the commit URL."""
    import requests
    repo, branch = GH.get("repo", "DarrenFTS/FTS-Home-Odds"), GH.get("branch", "main")
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    hdr = {"Authorization": f"Bearer {GH['token']}", "Accept": "application/vnd.github+json"}
    r = requests.get(url, headers=hdr, params={"ref": branch}, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": message, "content": base64.b64encode(content).decode(), "branch": branch}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=hdr, json=body, timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub said {r.status_code}: {r.json().get('message', r.text)[:200]}")
    return r.json()["commit"]["html_url"]


# ── Current database ─────────────────────────────────────────────────────────
cur = ui.load_bets()
info = ui.build_info() or {}
ui.section("Current database")
c = st.columns(4)
c[0].markdown(ui.card("Total bets", f"{len(cur):,}", f"{cur['system'].nunique()} systems"), unsafe_allow_html=True)
c[1].markdown(ui.card("Total P/L", f"{cur['pl'].sum():+.2f} pts", f"{cur['pl'].sum() / len(cur) * 100:+.2f}% ROI",
                      ui.GREEN if cur["pl"].sum() > 0 else ui.RED), unsafe_allow_html=True)
c[2].markdown(ui.card("Results to", cur["date"].max().strftime("%d %b %Y"),
                      f"from {cur['date'].min():%b %Y}", ui.ACCENT), unsafe_allow_html=True)
c[3].markdown(ui.card("Last rebuilt", info.get("built", "—"), "saving to GitHub: " + ("automatic ✅" if HAS_GH else "manual"),
                      ui.GREEN if HAS_GH else ui.AMBER), unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
ui.section("1 · Upload the new results file", "FTS Advanced Results Excel (sheet FTSAdvanced)")
up = st.file_uploader("Drop the file here", type=["xlsx"], label_visibility="collapsed")

if up is not None:
    key = f"{up.name}-{up.size}"
    if st.session_state.get("upd_key") != key:
        st.session_state.pop("upd", None)
        st.session_state["upd_key"] = key
    if "upd" not in st.session_state:
        if st.button("⚡ Rebuild all systems from this file", type="primary"):
            with st.status("Rebuilding…", expanded=True) as stt:
                st.write("Reading the FTSAdvanced sheet (about 30 seconds for a full file)…")
                df, notes = pb.load_results(up.getvalue())
                st.write(f"Loaded {len(df):,} matches · {df['date'].min():%d %b %Y} → {df['date'].max():%d %b %Y}")
                st.write("Running Lay U1.5, Lay O3.5, Back FHG O1.5, Lay FHG U0.5, Home Lay, Away Lay and Draw Lay…")
                new_bets = pb.build_bets(df)
                st.session_state["upd"] = dict(bets=new_bets, info=pb.build_info(new_bets, df), notes=notes)
                stt.update(label=f"Done — {len(new_bets):,} qualifying bets", state="complete")
            st.rerun()

res = st.session_state.get("upd")
if res:
    new = pd.DataFrame(res["bets"])
    new["date"] = pd.to_datetime(new["date"])
    for n in res["notes"]:
        st.warning(n)

    ui.section("2 · Check the result", "compare with what is live now before saving")
    old_s = ui.summary(cur, "system").set_index("system")
    new_s = ui.summary(new, "system").set_index("system")
    cmp = pd.DataFrame({
        "Bets (now)": old_s["Bets"], "Bets (new)": new_s["Bets"],
        "P/L (now)": old_s["P/L"], "P/L (new)": new_s["P/L"],
        "ROI % (new)": new_s["ROI %"],
    }).reindex(ui.SYSTEM_ORDER)
    cmp["Bets added"] = cmp["Bets (new)"] - cmp["Bets (now)"]
    cmp["P/L change"] = cmp["P/L (new)"] - cmp["P/L (now)"]
    cmp.loc["TOTAL"] = cmp.sum(numeric_only=True)
    cmp.loc["TOTAL", "ROI % (new)"] = new["pl"].sum() / len(new) * 100
    st.dataframe(cmp.style.format({"Bets (now)": "{:.0f}", "Bets (new)": "{:.0f}", "Bets added": "{:+.0f}",
                                   "P/L (now)": "{:+.2f}", "P/L (new)": "{:+.2f}", "P/L change": "{:+.2f}",
                                   "ROI % (new)": "{:+.2f}%"})
                 .map(ui.pl_style, subset=["P/L change", "Bets added"]), use_container_width=True)

    last = cur["date"].max()
    added = new[new["date"] > last].sort_values(["date", "system"])
    with st.expander(f"New bets since {last:%d %b %Y} ({len(added)})", expanded=len(added) > 0):
        if len(added):
            st.dataframe(added[["date", "time", "system", "league", "home", "away", "home_odds", "odds", "pl"]]
                         .style.format({"date": lambda d: d.strftime("%d/%m/%Y"), "odds": "{:.2f}",
                                        "home_odds": "{:.2f}", "pl": "{:+.2f}"}).map(ui.pl_style, subset=["pl"]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No bets after the current results date — the file may be the same as last time.")
    k = ["date", "league", "home", "away", "system"]
    mo = cur[cur["date"] <= last].merge(new[new["date"] <= last], on=k, how="outer", indicator=True,
                                         suffixes=("_o", "_n"))
    changed = int((mo["_merge"] != "both").sum() + ((mo["pl_o"] - mo["pl_n"]).abs() > 1e-6).sum())
    if changed:
        st.info(f"{changed} bets before the previous results date have changed or moved in/out of the systems. That happens when FTS correct "
                "historical odds or results in their file (e.g. a corrected price or result).")
    ui.section("3 · Save", "make the new data live")
    payload = pb.to_json_bytes(res["bets"])
    info_bytes = json.dumps(res["info"], indent=2).encode()
    s1, s2 = st.columns(2)
    with s1:
        if HAS_GH:
            if st.button("💾 Save to GitHub & refresh dashboard", type="primary", use_container_width=True):
                try:
                    with st.spinner("Saving to GitHub…"):
                        msg = f"Data update — results to {res['info']['results_to']} ({res['info']['bets']} bets)"
                        url = gh_put("data/portfolio_master_sheet.json", payload, msg)
                        gh_put("data/build_info.json", info_bytes, msg)
                    open(ui.DATA_PATH, "wb").write(payload)
                    open(ui.INFO_PATH, "wb").write(info_bytes)
                    st.cache_data.clear()
                    st.success(f"Saved. Streamlit will redeploy in a minute or two. [View commit]({url})")
                    st.balloons()
                except Exception as e:
                    st.error(f"Could not save to GitHub: {e}")
        else:
            if st.button("👁 Apply now (this session only)", use_container_width=True):
                open(ui.DATA_PATH, "wb").write(payload)
                open(ui.INFO_PATH, "wb").write(info_bytes)
                st.cache_data.clear()
                st.success("Applied — every page now shows the new data until the app restarts. "
                           "Download the two files and upload them to GitHub to keep it.")
    with s2:
        st.download_button("⬇ portfolio_master_sheet.json", payload, "portfolio_master_sheet.json",
                           "application/json", use_container_width=True, type="secondary" if HAS_GH else "primary")
        st.download_button("⬇ build_info.json", info_bytes, "build_info.json", "application/json",
                           use_container_width=True)
    if not HAS_GH:
        st.markdown(
            f'<div class="fts-banner" style="border-left:4px solid {ui.AMBER}">'
            "<b>To keep the update:</b> on GitHub open the <b>data</b> folder → <b>Add file → Upload files</b> → drop "
            "both downloaded files → <b>Commit changes</b>. The dashboard redeploys automatically.<br>"
            "<span style='color:#8FA3BF'>Want this to be one click? Add a GitHub token to the app's Secrets — see "
            "‘Monthly update guide’ below.</span></div>", unsafe_allow_html=True)

# ── Guide ─────────────────────────────────────────────────────────────────────
with st.expander("📘 Monthly update guide", expanded=False):
    st.markdown(f"""
**Each month (about 2 minutes):**
1. Download the latest **FTS Advanced Results – Odds** file (sheet FTSAdvanced).
2. Open this page → drop the file in → **Rebuild all systems**.
3. Check the comparison table (new bets added, P/L change).
4. **Save** — automatically to GitHub if the token is set up, otherwise download the two files and upload them to the
   `data/` folder on GitHub.

Every page — Portfolio, Results Dashboard, System Performance, Analytics, Odds Edge and the home page — reads
`data/portfolio_master_sheet.json`, so nothing else needs editing. No figures are typed into the code any more.

**One-time setup for one-click saving**
1. GitHub → your profile picture → **Settings → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token**. Repository access: only `FTS-Home-Odds`. Permissions: **Contents → Read and write**.
2. Streamlit Cloud → your app → **⋮ → Settings → Secrets**, paste:
```toml
[github]
token = "github_pat_xxxxxxxx"
repo = "DarrenFTS/FTS-Home-Odds"
branch = "main"
```
3. Save. This page will then show **Save to GitHub & refresh dashboard**.

**Changing a system** (adding/removing a league or moving a threshold): edit `SYSTEM_DEFS` in
`systems/all_systems.py` (the Daily Selector uses the same rules), then run an update — every page follows.

**Rules used in this rebuild**
""")
    rr = [{"System": sd["name"], "League": c, "Home odds band": f"{lo:.2f} – {hi:.2f}" + (" (incl.)" if sd.get("inclusive_upper") else " (excl.)"),
           "Bet odds": f"{pb.ODDS_MIN:.2f} – <{pb.ODDS_MAX:.2f}", "Status": "LIVE" if sd["live"] else "TEST"}
          for sd in pb.SYSTEM_DEFS for c, lo, hi in sd["rules"]]
    st.dataframe(pd.DataFrame(rr).style.map(ui.system_style, subset=["System"]), use_container_width=True,
                 hide_index=True, height=360)
