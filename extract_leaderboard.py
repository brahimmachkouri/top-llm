#!/usr/bin/env python3
"""
extract_leaderboard.py
"""

import requests, pandas as pd, io, json
from datetime import datetime
from bs4 import BeautifulSoup

# ─── CONFIG ────────────────────────────────────────────────────────────────
CSV_URL   = "https://raw.githubusercontent.com/fboulnois/llm-leaderboard-csv/refs/heads/main/csv/lmsys.csv"
REPO_URL  = "https://github.com/fboulnois/llm-leaderboard-csv"
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


def get_latest_release_date(url: str) -> str:
    """
    Récupère la date de la dernière release indiquée par le label 'Latest'
    sur une page GitHub.

    :param url: URL de la page GitHub à scrapper
    :return: date au format AAAA.MM.JJ
    :raises: HTTPError si la requête échoue, ValueError si le sélecteur ne trouve rien
    """
    # 1. Télécharger le HTML
    response = requests.get(url)
    response.raise_for_status()

    # 2. Parser le HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # 3. Sélectionner le span contenant le texte gras (date)
    #    On cible le premier span à l’intérieur d’un div.d-flex
    #    dont la classe contient 'css-truncate-target text-bold'
    date_span = soup.select_one('div.d-flex span.css-truncate-target.text-bold')

    if not date_span:
        raise ValueError("Date de la dernière release introuvable.")

    # 4. Retourner le texte (p.ex. '2025.07.10')
    return date_span.get_text(strip=True)


# Génération du contenu
#now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
maj = ""
try:
    date = get_latest_release_date(REPO_URL)
    maj = f"(mise à jour : {date})"
except Exception as e:
    print(f"Erreur : {e}")
md = (
    f"# 🏆 Top {TOP_N} LLMs {maj}\n\n"
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
