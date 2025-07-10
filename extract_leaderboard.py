import requests
import pandas as pd
import io
import json

CSV_URL = "https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/main/results.csv"
response = requests.get(CSV_URL)
response.raise_for_status()
df = pd.read_csv(io.StringIO(response.text))

OPEN_SOURCE_LICENSES = [
    'apache-2.0', 'mit', 'bsd-3-clause', 'bsd-2-clause', 'gpl-3.0', 'lgpl-3.0', 'cc-by-4.0',
    'cc-by-sa-4.0', 'isc', 'mpl-2.0', 'openrail', 'openrail++', 'openrail-m', 'bigscience-openrail-m',
    'bigscience-bloom-rail-1.0'
]

df = df[df['average'] > 0]
df = df.drop_duplicates(subset=['model', 'revision'])
df['license'] = df['license'].str.lower().fillna('')
open_source = df[df['license'].isin(OPEN_SOURCE_LICENSES)]
proprietary = df[~df['license'].isin(OPEN_SOURCE_LICENSES)]

top10_open = open_source.sort_values('average', ascending=False).head(10)
top10_prop = proprietary.sort_values('average', ascending=False).head(10)

fields = ['model', 'average', 'license', 'organization', 'num_params', 'revision', 'max_seq_len']
top10_open_dict = top10_open[fields].to_dict(orient='records')
top10_prop_dict = top10_prop[fields].to_dict(orient='records')

with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump({
        "top10_open_source": top10_open_dict,
        "top10_proprietary": top10_prop_dict
    }, f, indent=2, ensure_ascii=False)

def to_md(lst, title):
    md = f"## {title}\n\n| Rang | Modèle | Score | Licence | Org | Params | Contexte max |\n"
    md += "|---|---|---|---|---|---|---|\n"
    for i, m in enumerate(lst, 1):
        md += f"| {i} | `{m['model']}` | {m['average']:.2f} | {m['license']} | {m['organization']} | {m['num_params']} | {m.get('max_seq_len', '')} |\n"
    return md

with open("top10_llms.md", "w", encoding="utf-8") as f:
    f.write(to_md(top10_open_dict, "Top 10 Open Source"))
    f.write("\n\n")
    f.write(to_md(top10_prop_dict, "Top 10 Propriétaires"))

print("Extraction terminée. Résultats : top10_llms.json & top10_llms.md")
