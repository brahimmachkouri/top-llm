#!/usr/bin/env python3
"""
extract_leaderboard_v2.py · Fetch LM Arena leaderboard via HF Datasets,
                              sépare open-source / propriétaire, exporte Top-10.
"""

# Il faut installer 'datasets' et 'pyarrow' :
# pip install datasets pyarrow
from datasets import load_dataset
import pandas as pd
import json
import os
import sys

# --- 1. Chargement des données depuis le Hub Hugging Face --------------------
print("Fetching LM Arena leaderboard from Hugging Face Hub…")
try:
    # Charge le dataset directement
    dataset = load_dataset("lmsys/chatbot_arena_leaderboard")
    
    # Le dataset contient plusieurs tables, on prend la principale 'leaderboard_table'
    df = dataset["leaderboard_table"].to_pandas()
    
except Exception as e:
    print(f"Erreur lors du chargement du dataset : {e}", file=sys.stderr)
    sys.exit(1)

# --- 2. Préparation du DataFrame --------------------------------------------
# Les noms de colonnes sont déjà propres (ex: 'arena_score', 'license', 'organization')
SCORE_COL = "arena_score"

# S'assurer que la colonne 'arena_score' existe
if SCORE_COL not in df.columns:
    print(f"La colonne attendue '{SCORE_COL}' n'a pas été trouvée.", file=sys.stderr)
    sys.exit(1)

# --- 3. Détection open-source vs propriétaire -------------------------------
# La logique reste la même, excellente définition des licences !
OSS_LICENSES = {
    "apache-2.0", "apache 2.0", "mit", "gpl-3.0", "bsd-3-clause", "bsd-2-clause",
    "cc-by-4.0", "cc-by-sa-4.0", "mpl-2.0", "openrail", "openrail-m", "openrail++",
    "llama-3-community-license", "mistral-7b-license" # Ajout de quelques licences communes
}

df["license"] = df["license"].str.lower().fillna("")

# On filtre les modèles qui n'ont pas encore de score
df_scored = df.dropna(subset=[SCORE_COL])

open_src = df_scored[df_scored["license"].isin(OSS_LICENSES)]
prop     = df_scored[~df_scored["license"].isin(OSS_LICENSES)]

top10_open = open_src.sort_values(SCORE_COL, ascending=False).head(10)
top10_prop = prop.sort_values(SCORE_COL,   ascending=False).head(10)

# --- 4. Export JSON ----------------------------------------------------------
# La logique reste la même
keep = ["model", SCORE_COL, "license", "organization"]
result = {
    "top10_open_source": top10_open[keep].to_dict(orient="records"),
    "top10_proprietary": top10_prop[keep].to_dict(orient="records")
}

with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# --- 5. Export Markdown ------------------------------------------------------
# La logique reste la même
def to_md(lst, title):
    col_score = SCORE_COL.replace("_", " ").title()
    md = f"## {title}\n\n| # | Modèle | {col_score} | Licence | Org |\n"
    md += "|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += (
            f"| {i} | `{m['model']}` | {m[SCORE_COL]:.2f} | "
            f"`{m['license']}` | {m['organization']} |\n"
        )
    return md

with open("top10_llms.md", "w", encoding="utf-8") as f:
    f.write(to_md(result["top10_open_source"], "Top 10 Open Source"))
    f.write("\n\n")
    f.write(to_md(result["top10_proprietary"], "Top 10 Propriétaires"))

print("✅  Fichiers générés : top10_llms.md  &  top10_llms.json")
