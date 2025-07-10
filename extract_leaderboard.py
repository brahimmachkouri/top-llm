import requests
import pandas as pd
import io, json

# URL corrigée :
CSV_URL = (
    "https://raw.githubusercontent.com/"
    "fboulnois/llm-leaderboard-csv/refs/heads/main/csv/lmsys.csv"
)

resp = requests.get(CSV_URL, timeout=30)
resp.raise_for_status()
df = pd.read_csv(io.StringIO(resp.text))

# licences open-source (liste non exhaustive ; ajuste-la au besoin)
OSS = {
    'apache-2.0','mit','bsd-3-clause','bsd-2-clause','gpl-3.0',
    'cc-by-4.0','cc-by-sa-4.0','isc','mpl-2.0',
    'openrail','openrail++','openrail-m','bigscience-openrail-m',
    'bigscience-bloom-rail-1.0'
}

# nettoyage minimal
df = df.dropna(subset=['license', 'average'])
df['license'] = df['license'].str.lower()

open_src = df[df['license'].isin(OSS)]
prop     = df[~df['license'].isin(OSS)]

top10_open = open_src.sort_values('average', ascending=False).head(10)
top10_prop = prop.sort_values('average',  ascending=False).head(10)

keep = ['model','average','license','organization','num_params','max_seq_len']
out = {
    "top10_open_source": top10_open[keep].to_dict(orient='records'),
    "top10_proprietary": top10_prop[keep].to_dict(orient='records')
}

with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

def to_md(lst, title):
    md = f"## {title}\n\n| # | Modèle | Score | Licence | Org | Params | Ctx |\n"
    md += "|---|---|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += (
            f"| {i} | `{m['model']}` | {m['average']:.2f} | {m['license']} | "
            f"{m['organization']} | {int(m['num_params'])} | {int(m.get('max_seq_len',0))} |\n"
        )
    return md

with open("top10_llms.md", "w", encoding="utf-8") as f:
    f.write(to_md(out["top10_open_source"], "Top 10 Open Source"))
    f.write("\n\n")
    f.write(to_md(out["top10_proprietary"], "Top 10 Propriétaires"))

print("✅ Génération terminée : top10_llms.json & top10_llms.md")
