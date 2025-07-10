import requests, pandas as pd, io, json

CSV_URL = ("https://raw.githubusercontent.com/fboulnois/llm-leaderboard-csv/refs/heads/main/csv/lmsys.csv")

csv_text = requests.get(CSV_URL, timeout=30).text
df = pd.read_csv(io.StringIO(csv_text))

# colonne contenant le score
SCORE_COL = "arena_score"

# liste (non exhaustive) des licences open-source
OSS = {
    "apache 2.0", "apache-2.0", "mit", "bsd-3-clause", "bsd-2-clause",
    "gpl-3.0", "cc-by-4.0", "cc-by-sa-4.0", "isc", "mpl-2.0",
    "openrail", "openrail++", "openrail-m", "bigscience-openrail-m",
    "bigscience-bloom-rail-1.0"
}

df["license"] = df["license"].str.lower().fillna("")

# filtrage open-source vs propriétaire
open_src = df[df["license"].isin(OSS)]
prop     = df[~df["license"].isin(OSS)]

top10_open = open_src.sort_values(SCORE_COL, ascending=False).head(10)
top10_prop = prop.sort_values(SCORE_COL,   ascending=False).head(10)

keep = ["model", SCORE_COL, "license", "organization"]
result = {
    "top10_open_source": top10_open[keep].to_dict(orient="records"),
    "top10_proprietary": top10_prop[keep].to_dict(orient="records")
}

# ── export JSON ─────────────────────────────────────────
with open("top10_llms.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# ── export Markdown ─────────────────────────────────────
def to_md(lst, title):
    md = f"## {title}\n\n| # | Modèle | Score | Licence | Org |\n"
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

print("✅ Fichiers générés : top10_llms.md & top10_llms.json")
