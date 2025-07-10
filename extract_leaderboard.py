#!/usr-bin/env python3
"""
extract_leaderboard.py  ·  Fetch LM Arena leaderboard from its public API,
                           sépare open-source / propriétaire, exporte Top-10.
"""

import os
import sys
import json
import pandas as pd
import requests  # Nous utilisons requests pour appeler l'API
from datetime import datetime

# --- NOUVELLE CONFIGURATION ---
# URL directe de l'API du Space Hugging Face
API_URL = "https://lmarena-ai-chatbot-arena-leaderboard.hf.space/api/leaderboard"
OUTPUT_MD = "top10_llms.md"
OUTPUT_JSON = "top10_llms.json"
TOP_N = 10

# --- LOGIQUE ---

def fetch_leaderboard():
    """
    Récupère le leaderboard depuis l'API publique du Space Hugging Face.
    """
    print("Fetching LM Arena leaderboard from public API…")
    try:
        response = requests.get(API_URL)
        # Lève une exception si la requête a échoué (ex: status 404 ou 500)
        response.raise_for_status()
        
        # Le résultat est un JSON, on extrait la partie "data"
        json_data = response.json()
        headers = json_data['data'][0]
        rows = json_data['data'][1:]
        
        # Créer un DataFrame pandas avec les bonnes colonnes
        df = pd.DataFrame(rows, columns=headers)
        
        print("✅ Leaderboard data fetched successfully!")
        return df
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel à l'API : {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError) as e:
        print(f"❌ Erreur: Le format des données de l'API a peut-être changé. Détails: {e}", file=sys.stderr)
        sys.exit(1)

def process_data(df):
    """
    Traite le DataFrame pour filtrer, renommer et classer les modèles.
    """
    print("Processing data...")
    # Renommer les colonnes pour correspondre à notre logique standard
    df = df.rename(columns={
        'Model': 'model_name',
        'Arena Score': 'arena_score',
        'License': 'license'
    })
    
    # S'assurer que la colonne 'arena_score' est numérique et trier
    df['arena_score'] = pd.to_numeric(df['arena_score'], errors='coerce')
    df = df.dropna(subset=['arena_score'])
    df = df.sort_values(by="arena_score", ascending=False)
    
    # Filtrer les modèles open source
    df_open = df[df['license'].str.contains('apache|mit|llama|gpl|mpl', case=False, na=False)].head(TOP_N)
    
    # Filtrer les modèles propriétaires
    df_proprietary = df[~df['license'].str.contains('apache|mit|llama|gpl|mpl', case=False, na=True)].head(TOP_N)
    
    print(f"✅ Data processed. Found {len(df_open)} open-source and {len(df_proprietary)} proprietary models for the Top {TOP_N}.")
    return df_open, df_proprietary

# Les fonctions format_as_markdown, format_as_json, et save_output restent inchangées
# (Copiez-les depuis votre version précédente ou utilisez celles ci-dessous)

def format_as_markdown(df_open, df_proprietary):
    print(f"Formatting data as Markdown for '{OUTPUT_MD}'...")
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    md = f"# Top {TOP_N} LLMs - Leaderboard\n*Dernière mise à jour : {now}*\n\n"
    
    md += f"## 🏆 Top {TOP_N} Modèles Propriétaires\n"
    md += "| Rang | Modèle | Score Arena |\n|---|---|---|\n"
    for index, row in df_proprietary.iterrows():
        md += f"| {index + 1} | **{row['model_name']}** | {row['arena_score']:.2f} |\n"
        
    md += f"\n## 🌍 Top {TOP_N} Modèles Open Source\n"
    md += "| Rang | Modèle | Score Arena | Licence |\n|---|---|---|---|\n"
    for index, row in df_open.iterrows():
        md += f"| {index + 1} | **{row['model_name']}** | {row['arena_score']:.2f} | `{row['license']}` |\n"
        
    md += "\n*Source : [LMSYS Chatbot Arena Leaderboard](https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard)*"
    return md

def format_as_json(df_open, df_proprietary):
    print(f"Formatting data as JSON for '{OUTPUT_JSON}'...")
    now = datetime.utcnow().isoformat()
    data = {
        "last_updated_utc": now,
        "source": "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard",
        "top_proprietary": json.loads(df_proprietary[['model_name', 'arena_score']].to_json(orient='records')),
        "top_open_source": json.loads(df_open[['model_name', 'arena_score', 'license']].to_json(orient='records'))
    }
    return json.dumps(data, indent=2)

def save_output(filename, content):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Successfully saved file: '{filename}'")
    except IOError as e:
        print(f"❌ Erreur lors de l'écriture du fichier '{filename}': {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Fonction principale du script."""
    leaderboard_df = fetch_leaderboard()
    df_open, df_proprietary = process_data(leaderboard_df)
    
    markdown_output = format_as_markdown(df_open, df_proprietary)
    save_output(OUTPUT_MD, markdown_output)
    
    json_output = format_as_json(df_open, df_proprietary)
    save_output(OUTPUT_JSON, json_output)
    
    print("\n🎉 Script finished successfully!")

if __name__ == "__main__":
    main()
