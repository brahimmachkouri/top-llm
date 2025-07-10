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
OSS_REGEX  = r"(apache|mit|bsd|gpl|mpl|lgpl|cc-by|openrail|bigscience)"

# NOUVEAUX EN-TÊTES POUR CONTOURNER L'ERREUR 403 (Cloudflare, etc.)
# Ils simulent une requête d'un navigateur Chrome sur Windows.
HEADERS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


# ─── 1. Télécharger la page ───────────────────────────────────────────────
print("📥 Fetching leaderboard page with browser headers...")
try:
    # On utilise maintenant la variable HEADERS complète
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
except requests.RequestException as e:
    sys.exit(f"❌ Erreur de réseau ou HTTP en téléchargeant la page : {e}")

# Le reste du script est inchangé car sa logique est toujours valide.

# ─── 2. Extraire le blob JSON du script Gradio ────────────────────────────
print("🔍 Searching for Gradio data blob in <script> tags...")
gradio_json_str = None
config_regex = re.compile(r"window.gradio_config\s*=\s*(\{.*\});", re.DOTALL)

for script in soup.find_all("script"):
    if script.string:
        match = config_regex.search(script.string)
        if match:
            gradio_json_str = match.group(1)
            print("✅ Found Gradio data blob.")
            break

if not gradio_json_str:
    sys.exit("❌ Données de configuration Gradio introuvables. La structure du site a probablement changé.")

try:
    gradio_cfg = json.loads(gradio_json_str)
except json.JSONDecodeError as e:
    sys.exit(f"❌ JSON de configuration invalide : {e}")


# ─── 3. Trouver le composant “Leaderboard” et ses données ──────────────────
lb_data = None
for comp in gradio_cfg.get("components", []):
    props = comp.get("props", {})
    if isinstance(props, dict) and props.get("label") == "Leaderboard" and "value" in props:
        val = props["value"]
        if isinstance(val, dict) and "headers" in val and "data" in val:
            lb_data = val
            print("✅ Extracted leaderboard data from components.")
            break

if not lb_data:
    sys.exit("❌ Données du leaderboard non trouvées dans la config. La structure Gradio a changé.")

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

print(f"✅ Selected {len(top_open)} open-source and {len(top_prop)} proprietary models.")

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
    + f"\n\n*Source : <{URL}>*\n"
)
with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"🎉 Files generated: {OUT_MD} & {OUT_JSON}")
