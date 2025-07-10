#!/usr/bin/env python3
"""
extract_leaderboard.py  ·  Scrape https://lmarena.ai/leaderboard,
                          sépare open-source / propriétaire,
                          exporte Top-10 en Markdown + JSON.

Dépendances :
    pip install requests pandas beautifulsoup4 lxml
"""

import re
import sys
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────
URL        = "https://lmarena.ai/leaderboard"
TOP_N      = 10
OUT_MD     = "top10_llms.md"
OUT_JSON   = "top10_llms.json"
UA_HEADER  = {"User-Agent": "llm-top-10-gh-action"}
OSS_REGEX  = r"(apache|mit|bsd|gpl|mpl|lgpl|cc-by|openrail|bigscience)"

# ─── 1. Télécharger la page ───────────────────────────────────────────────
print("📥 Fetching leaderboard page…")
html = requests.get(URL, headers=UA_HEADER, timeout=30).text
soup = BeautifulSoup(html, "lxml")

# ─── 2. Extraire le blob JSON du script Gradio ────────────────────────────
script_tag = next(
    (s for s in soup.find_all("script") if s.string and "window.gradio_config" in s.string),
    None
)
if not script_tag:
    sys.exit("❌ Gradio config introuvable – structure du site changée ?")

match = re.search(
    r"window\.gradio_config\s*=\s*(\{.*?\})\s*;",
    script_tag.string,
    re.S  # DOTALL : le '.' englobe les retours ligne
)
if not match:
    sys.exit("❌ JSON Gradio non trouvé – structure du site changée ?")

try:
    gradio_cfg = json.loads(match.group(1))
except json.JSONDecodeError as e:
    sys.exit(f"❌ JSON invalide : {e}")

# ─── 3. Trouver le composant “Leaderboard” et ses données ──────────────────
lb_data = None
for comp in gradio_cfg.get("components", []):
    props = comp.get("props", {})
    if props.get("label") == "Leaderboard" and "value" in props:
        val = props["value"]
        if isinstance(val, dict) and "headers" in val and "data" in val:
            lb_data = val
            break

if not lb_data:
    sys.exit("❌ Données leaderboard non trouvées – structure Gradio changée ?")

headers = lb_data["headers"]
rows    = lb_data["data"]
df      = pd.DataFrame(rows, columns=headers)

# ─── 4. Normaliser et trier ───────────────────────────────────────────────
df = df.rename(columns={
    "Model": "model_name",
    "Arena Score": "arena_score",
    "License": "license"
})
df["arena_score"] = pd.to_numeric(df["arena_score"], errors="coerce")
df = df.dropna(subset=["arena_score"]).sort_values("arena_score", ascending=False)

# ─── 5. Séparer open-source / propriétaire ────────────────────────────────
is_open = df["license"].str.contains(OSS_REGEX, case=False, na=False)
top_open = df[is_open].head(TOP_N).reset_index(drop=True)
top_prop = df[~is_open].head(TOP_N).reset_index(drop=True)

print(f"✅ {len(top_open)} open-source, {len(top_prop)} propriétaires sélectionnés.")

# ─── 6. Export JSON ────────────────────────────────────────────────────────
payload = {
    "last_update_utc": datetime.utcnow().isoformat(),
    "source": URL,
    "top_open_source": json.loads(
        top_open[["model_name", "arena_score", "license"]].to_json(orient="records")),
    "top_proprietary": json.loads(
        top_prop[["model_name", "arena_score", "license"]].to_json(orient="records"))
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

# ─── 7. Export Markdown ────────────────────────────────────────────────────
def mk_table(df_in, title, extra=False):
    md = f"## {title}\n\n| # | Modèle | Score |" + (" Licence |" if extra else "") + "\n"
    md += "|---|---|---|" + ("---|" if extra else "") + "\n"
    for rank, (_, row) in enumerate(df_in.iterrows(), start=1):
        md += f"| {rank} | **{row['model_name']}** | {row['arena_score']:.2f} |"
        if extra:
            md += f" `{row['license']}` |"
        md += "\n"
    return md

md_content = (
    f"# 🏆 Top {TOP_N} LLMs – LM Arena\n"
    f"*Mise à jour : {datetime.utcnow():%Y-%m-%d %H:%M UTC}*\n\n"
    + mk_table(top_prop, f"Top {TOP_N} propriétaires")
    + "\n\n"
    + mk_table(top_open, f"Top {TOP_N} open-source", extra=True)
    + "\n\n*Source : <{URL}>*\n"
)
with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(md_content)

print("🎉  Fichiers générés :", OUT_MD, "&", OUT_JSON)
