#!/usr/bin/env python3
"""
extract_leaderboard.py  ·  Fetch LM Arena leaderboard from HF Hub,
                           sépare open-source / propriétaire, exporte Top-10.
"""

import os
import sys
import json
import pandas as pd
from datasets import load_dataset
from datetime import datetime

# --- CONFIGURATION ---
DATASET_ID = "lmsys/chatbot_arena_leaderboard"
OUTPUT_MD = "top10_llms.md"
OUTPUT_JSON = "top10_llms.json"
TOP_N = 10

# --- LOGIQUE ---

def fetch_leaderboard():
    """
    Récupère le leaderboard depuis le dataset Hugging Face en utilisant
    une authentification sécurisée.
    """
    print("Fetching LM Arena leaderboard from Hugging Face Hub…")
    try:
        # Récupère le token depuis les variables d'environnement (passé par le workflow)
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            print("❌ Erreur: La variable d'environnement HF_TOKEN n'est pas définie.", file=sys.stderr)
            print("Veuillez la configurer dans les Secrets de votre dépôt GitHub.", file=sys.stderr)
            sys.exit(1)

        # Utilise le token pour s'authentifier et charger le dataset
        dataset = load_dataset(DATASET_ID, token=hf_token)
        
        # Le dataset contient plusieurs tables, on prend la plus récente
        df = dataset['latest_arena_leaderboard'].to_pandas()
        
        print("✅ Leaderboard data fetched successfully!")
        return df
    except Exception as e:
        print(f"❌ Erreur lors du chargement du dataset depuis Hugging Face : {e}", file=sys.stderr)
        sys.exit(1)

def process_data(df):
    """
    Traite le DataFrame pour filtrer et classer les modèles.
    """
    print("Processing data...")
    # S'assurer que la colonne 'arena_score' est numérique
    df['arena_score'] = pd.to_numeric(df['arena_score'], errors='coerce')
    df = df.dropna(subset=['arena_score'])
    df = df.sort_values(by="arena_score", ascending=False)
    
    # Filtrer les modèles open source
    # La colonne 'license' contient souvent des infos comme 'apache-2.0', 'mit', etc.
    # On considère un modèle comme open source s'il a une licence non-propriétaire.
    # On peut se baser sur la présence du mot "proprietary" ou non.
    # Ici, nous allons assumer que si la licence n'est pas vide/None et pas propriétaire, c'est open source.
    # Une approche plus robuste peut être nécessaire si le format de la colonne change.
    df_open = df[~df['license'].str.contains('proprietary', case=False, na=True)].head(TOP_N)
    
    # Filtrer les modèles propriétaires
    df_proprietary = df[df['license'].str.contains('proprietary', case=False, na=False)].head(TOP_N)

    print(f"✅ Found {len(df_open)} open source models and {len(df_proprietary)} proprietary models for the Top {TOP_N}.")
    return df_open, df_proprietary

def format_as_markdown(df_open, df_proprietary):
    """
    Génère une chaîne de caractères formatée en Markdown.
    """
    print(f"Formatting data as Markdown for '{OUTPUT_MD}'...")
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    md = f"""# 🏆 Top {TOP_N} LLMs du Chatbot Arena

*Dernière mise à jour : {now}*

## 👑 Top {TOP_N} Modèles Propriétaires

| Rang | Modèle | Score Arena |
|:----:|:-------|:-----------:|
"""
    for index, row in df_proprietary.iterrows():
        md += f"| {index + 1} | **{row['model_name']}** | {row['arena_score']:.2f} |\n"

    md += f"""
## 🗽 Top {TOP_N} Modèles Open Source

| Rang | Modèle | Score Arena | Licence |
|:----:|:-------|:-----------:|:--------|
"""
    for index, row in df_open.iterrows():
        md += f"| {index + 1} | **{row['model_name']}** | {row['arena_score']:.2f} | `{row['license']}` |\n"
        
    md += "\n*Source : [LMSYS Chatbot Arena Leaderboard](https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard)*"
    
    print("✅ Markdown content generated.")
    return md

def format_as_json(df_open, df_proprietary):
    """
    Génère une structure de données JSON.
    """
    print(f"Formatting data as JSON for '{OUTPUT_JSON}'...")
    now = datetime.utcnow().isoformat()
    
    data = {
        "last_updated_utc": now,
        "source": "https://huggingface.co/datasets/lmsys/chatbot_arena_leaderboard",
        "top_proprietary": json.loads(df_proprietary[['model_name', 'arena_score']].to_json(orient='records')),
        "top_open_source": json.loads(df_open[['model_name', 'arena_score', 'license']].to_json(orient='records'))
    }
    
    print("✅ JSON content generated.")
    return json.dumps(data, indent=2)

def save_output(filename, content):
    """
    Sauvegarde le contenu dans un fichier.
    """
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
    
    # Générer et sauvegarder le fichier Markdown
    markdown_output = format_as_markdown(df_open, df_proprietary)
    save_output(OUTPUT_MD, markdown_output)
    
    # Générer et sauvegarder le fichier JSON
    json_output = format_as_json(df_open, df_proprietary)
    save_output(OUTPUT_JSON, json_output)
    
    print("\n🎉 Script finished successfully!")

if __name__ == "__main__":
    main()
