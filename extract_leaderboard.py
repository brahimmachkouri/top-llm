import requests
import json

API_URL = "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard/api/leaderboard"
response = requests.get(API_URL)
response.raise_for_status()
data = response.json()

# Les modèles sont dans data['models']
models = data['models']

# Détection open-source vs propriétaire : on utilise 'license' (comme avant)
OPEN_SOURCE_LICENSES = [
    'apache-2.0', 'mit', 'bsd-3-clause', 'bsd-2-clause', 'gpl-3.0', 'lgpl-3.0', 'cc-by-4.0',
    'cc-by-sa-4.0', 'isc', 'mpl-2.0', 'openrail', 'openrail++', 'openrail-m', 'bigscience-openrail-m',
    'bigscience-bloom-rail-1.0'
]

open_src = [m for m in models if (m.get('license', '') or '').lower() in OPEN_SOURCE_LICENSES]
proprietary = [m for m in models if (m.get('license', '') or '').lower() not in OPEN_SOURCE_LICENSES]

# Tri par score 'average'
open_src_sorted = sorted(open_src, key=lambda x: x.get('average', 0), reverse=True)[:10]
proprietary_sorted = sorted(proprietary, key=lambda x: x.get('average', 0), reverse=True)[:10]

def to_md(lst, title):
    md = f"## {title}\n\n| Rang | Modèle | Score | Licence | Org | Params | Contexte max |\n"
    md += "|---|---|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += f"| {i} | `{m.get('model', '')}` | {m.get('average', 0):.2f} | {m.get('license', '')} | {m.get('organization', '')} | {m.get('num_params', '')} | {m.get('max_seq_len', '')} |\n"
    return md

with open("top10_llms.md", "w", encoding="utf-8") as f:
    f.write(to_md(open_src_sorted, "Top 10 Open Source"))
    f.write("\n\n")
    f.write(to_md(proprietary_sorted, "Top 10 Propriétaires"))

with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump({
        "top10_open_source": open_src_sorted,
        "top10_proprietary": proprietary_sorted
    }, f, indent=2, ensure_ascii=False)

print("Extraction terminée. Résultats : top10_llms.json & top10_llms.md")
