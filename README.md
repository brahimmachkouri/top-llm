# llm-top-10

> _Suivi automatisé du **Top 10** des modèles LLM : open‑source **vs** propriétaires._  
> Mises à jour hebdomadaires via **GitHub Actions** · Résultats consultables en JSON, Markdown **et** GitHub Pages.

---

## 🚀 Qu’est‑ce que c’est ?
Ce dépôt maintient **automatiquement** deux classements basés sur l’*Open LLM Leaderboard* (CSV publié par `fboulnois/llm-leaderboard-csv`) :

1. **Top 10 open‑source** – modèles libres (licence permissive) utilisables localement.
2. **Top 10 propriétaires** – modèles accessibles uniquement via API (GPT‑4o, Gemini 2.5 Pro, Claude 4, etc.).

Les classements sont republiés :
- en **Markdown** : [`top10_llms.md`](./top10_llms.md)
- en **JSON** : [`top10_llms.json`](./top10_llms.json)
- sur **GitHub Pages** : <https://<USER>.github.io/llm-top-10/> (copie de `top10_llms.md`)

---

## 📑 Utiliser ces données
- **Front end** : consommez directement le JSON pour alimenter un tableau de bord.
- **Automatisation** : récupérez `top10_llms.json` via Raw GitHub.

---

## 📜 Licence du repository

[MIT](LICENSE) – libre d’utilisation, modification et redistribution.

---

## 🙏 Crédits & sources

* **Open LLM Leaderboard** : [LMArena](https://lmarena.ai/leaderboard)

---

> *Made with ♥ and automation.*
