# Voyage au pays du non-écrit

Audit des implicites, sous-textes et angles morts dans une réponse de modèle de langage.

## Le problème

La réponse d'un LLM, aussi vraisemblable soit-elle, comporte des manques : des implicites que le modèle tient pour acquis, des conclusions logiques qu'il ne tire pas, des angles qu'il n'aborde pas. Ces non-dits sont invisibles pour l'utilisateur et c'est précisément ce que la délégation à la machine rend justement visible.

## L'approche

L'outil s'appuie sur une taxonomie de l'implicite issue de l'ontologie Wikidata, formalisée par [Arthur Sarazin](https://www.linkedin.com/pulse/voyage-au-pays-du-non-%C3%A9crit-arthur-sarazin-phd-hwswe). Chaque réponse est auditée selon 6 catégories :

| Catégorie | Ce qu'elle révèle |
|---|---|
| **Connotation** | Charges affectives et jugements de valeur portés par le choix des mots |
| **Sous-texte** | Message implicite véhiculé par le ton, la posture ou la mise en scène du propos |
| **Implicature** | Ce que le texte laisse entendre sans l'affirmer, par sous-entendu logique |
| **De facto** | Affirmations présentées comme des faits établis, sans source ni nuance |
| **Détail d'implémentation** | Conditions matérielles ou organisationnelles passées sous silence |
| **Omission pure** | Dimensions absentes du texte alors qu'elles sont structurantes pour le sujet |

## Utilisation

Collez une réponse produite par un modèle de langage (ChatGPT, Claude, Gemini, Mistral…) et, optionnellement, la question qui l'a produite. L'outil révèle les non-dits et produit :

- une **synthèse** identifiant le principal angle mort et ses conséquences
- un **audit détaillé** par catégorie avec infobulles explicatives
- une **instruction de correction** prête à copier-coller pour renvoyer au modèle d'origine
- un **export Markdown** de l'ensemble des résultats

## Déploiement

L'application tourne sur [Streamlit Cloud](https://streamlit.io/cloud) et utilise le modèle `mistralai/Mistral-Small-3.2-24B-Instruct-2506` via l'[API Albert](https://albert.api.etalab.gouv.fr).

### En local

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Renseigner ALBERT_API_KEY dans secrets.toml
streamlit run app.py
```

### Sur Streamlit Cloud

1. Connecter le repo GitHub
2. Pointer sur `app.py`
3. Dans **Settings → Secrets**, ajouter :

```toml
ALBERT_API_KEY = "votre-clé"
```

## Crédits

- Taxonomie de l'implicite : [Arthur Sarazin](https://www.linkedin.com/pulse/voyage-au-pays-du-non-%C3%A9crit-arthur-sarazin-phd-hwswe)
- Modèle : `mistralai/Mistral-Small-3.2-24B-Instruct-2506` via l'[API Albert](https://albert.api.etalab.gouv.fr) (DINUM / Etalab)

## Licence

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — Bertrand Formet pour [uneIAparjour.fr](https://uneIAparjour.fr)
