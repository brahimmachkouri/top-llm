# llm-top-10

Ce dépôt maintient automatiquement, via GitHub Actions, les top 10 LLM :
- **Open-source** (licence permissive, utilisable localement)
- **Propriétaires** (API only, modèles fermés)

La mise à jour se fait chaque semaine à partir de l’[Open LLM Leaderboard Hugging Face](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard).

## Résultats

- [top10_llms.md](./top10_llms.md) : tables lisibles
- [top10_llms.json](./top10_llms.json) : format data/API

## Comment ça marche

- Script Python (`extract_leaderboard.py`) télécharge, trie et formate les données
- GitHub Actions exécute le script chaque semaine et commit la mise à jour automatiquement

## Inspiré par les classements Hugging Face et Vellum AI

> [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard)
