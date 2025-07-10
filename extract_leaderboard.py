#!/usr/bin/env python3
"""
extract_leaderboard.py
"""

import requests, pandas as pd, io, json
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────
CSV_URL   = "https://raw.githubusercontent.com/fboulnois/llm-leaderboard-csv/refs/heads/main/csv/lmsys.csv"
SCORE_COL = "arena_score"
TOP_N     = 10
OUT_MD    = "top10_llms.md"
OUT_JSON  = "top10_llms.json"

OSS = {
    "apache 2.0","apache-2.0","mit","bsd-3-clause","bsd-2-clause",
    "gpl-3.0","cc-by-4.0","cc-by-sa-4.0","isc","mpl-2.0",
    "openrail","openrail++","openrail-m","bigscience-openrail-m",
    "bigscience-bloom-rail-1.0"
}

# ─── 1. Chargement CSV ─────────────────────────────────────────────────────
resp = requests.get(CSV_URL, timeout=30)
resp.raise_for_status()
df = pd.read_csv(io.StringIO(resp.text))

# ─── 2. Filtrage et tri ────────────────────────────────────────────────────
df["license"] = df["license"].str.lower().fillna("")
open_src = df[df["license"].isin(OSS)]
prop     = df[~df["license"].isin(OSS)]

top10_open = open_src.sort_values(SCORE_COL, ascending=False).head(TOP_N)
top10_prop = prop.sort_values(SCORE_COL,   ascending=False).head(TOP_N)

keep = ["model", SCORE_COL, "license", "organization"]
result = {
    "top10_open_source":    top10_open[keep].to_dict(orient="records"),
    "top10_proprietary":    top10_prop[keep].to_dict(orient="records")
}

# ─── 3. Export JSON ────────────────────────────────────────────────────────
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# ─── 4. Export Markdown + footer statique ──────────────────────────────────
def to_md(lst, title):
    md = f"## {title}\n\n| # | Modèle | Score | Licence | Org |\n"
    md += "|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += (
            f"| {i} | `{m['model']}` | {m[SCORE_COL]} | "
            f"{m['license']} | {m['organization']} |\n"
        )
    return md

# Génération du contenu
now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
md = (
    f"# 🏆 Top {TOP_N} LLMs (mise à jour : {now})\n\n"
    + to_md(result["top10_open_source"], "Top 10 Open Source")
    + "\n\n"
    + to_md(result["top10_proprietary"], "Top 10 Propriétaires")
    + "\n\n---\n\n"
    + '<div align="center"><sub>Made with ♥ and automation.</sub></div>\n'
    + '<style>.footer { display: none; }</style>'
)

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(md)

print("✅ Fichiers générés :", OUT_MD, "&", OUT_JSON)
