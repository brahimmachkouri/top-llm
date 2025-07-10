#!/usr/bin/env python3
"""
extract_leaderboard.py  ·  Fetch LM Arena leaderboard via HF Space API,
                           sépare open-source / propriétaire, exporte Top-10.
"""

import requests, pandas as pd, json, os, sys

API_URL   = "https://lmarena-ai-chatbot-arena-leaderboard.hf.space/run/predict"
TIMEOUT   = 30
PAYLOAD   = {"data": [0]}            # 0 = onglet "Leaderboard" dans l'UI Gradio

# --- 1. Appel de l'API -------------------------------------------------------
print("Fetching LM Arena leaderboard …")
resp = requests.post(API_URL, json=PAYLOAD, timeout=TIMEOUT)
resp.raise_for_status()

# La réponse contient data[0] => un dict {headers: [...], data: [[...], …]}
table   = resp.json()["data"][0]
headers = table["headers"]
rows    = table["data"]                 # liste de listes

# --- 2. Conversion en DataFrame ---------------------------------------------
df = pd.DataFrame(rows, columns=headers)

# Harmoniser les noms de colonnes qu'on va utiliser
# (le Space renvoie 'Score' et 'License' avec majuscules)
df.columns = df.columns.str.lower().str.replace(" ", "_")

SCORE_COL = "score"                     # alias court
if "arena_score" in df.columns:
    SCORE_COL = "arena_score"

# --- 3. Détection open-source vs propriétaire -------------------------------
OSS_LICENSES = {
    "apache-2.0", "apache 2.0", "mit", "gpl-3.0", "bsd-3-clause", "bsd-2-clause",
    "cc-by-4.0", "cc-by-sa-4.0", "mpl-2.0", "openrail", "openrail-m", "openrail++"
}

df["license"] = df["license"].str.lower().fillna("")

open_src = df[df["license"].isin(OSS_LICENSES)]
prop     = df[~df["license"].isin(OSS_LICENSES)]

top10_open = open_src.sort_values(SCORE_COL, ascending=False).head(10)
top10_prop = prop.sort_values(SCORE_COL,   ascending=False).head(10)

# --- 4. Export JSON ----------------------------------------------------------
keep = ["model", SCORE_COL, "license", "organization"]
result = {
    "top10_open_source": top10_open[keep].to_dict(orient="records"),
    "top10_proprietary": top10_prop[keep].to_dict(orient="records")
}

with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# --- 5. Export Markdown ------------------------------------------------------
def to_md(lst, title):
    col_score = SCORE_COL.replace("_", " ").title()
    md = f"## {title}\n\n| # | Modèle | {col_score} | Licence | Org |\n"
    md += "|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += (
            f"| {i} | `{m['model']}` | {m[SCORE_COL]} | "
            f"{m['license']} | {m['organization']} |\n"
        )
    return md

with open("top10_llms.md", "w", encoding="utf-8") as f:
    f.write(to_md(result["top10_open_source"], "Top 10 Open Source"))
    f.write("\n\n")
    f.write(to_md(result["top10_proprietary"], "Top 10 Propriétaires"))

print("✅  Fichiers générés : top10_llms.md  &  top10_llms.json")
