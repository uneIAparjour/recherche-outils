# recherche-outils

Moteur de recherche multi-catégories pour [uneiaparjour.fr](https://www.uneiaparjour.fr).

## Fonctionnement

Un overlay full-screen s'ouvre au clic sur la loupe du thème WordPress (Kenta Artistic Blog). Il permet de rechercher parmi les 1 000+ outils IA référencés sur le site, avec :

- **Recherche textuelle** sur le titre et la description, avec surbrillance des occurrences
- **Filtrage par catégories** (tags cliquables, multi-sélection)
- **Logique OU / ET** entre les catégories sélectionnées (visible dès 2 tags actifs)
- **Pagination** par blocs de 48 résultats
- Clic sur un tag dans une carte → active immédiatement ce filtre

Les données sont chargées depuis le CSV du dépôt [`uneIAparjour/base`](https://github.com/uneIAparjour/base) (mis à jour automatiquement chaque nuit).

## Fichiers

| Fichier | Rôle |
|---|---|
| `recherche-overlay.css` | Styles de l'overlay |
| `recherche-overlay.js`  | Logique : chargement CSV, filtres, rendu |
| `functions-snippet.php` | Extrait à ajouter dans `functions.php` du thème enfant |

## Installation

1. Copier `recherche-overlay.css` et `recherche-overlay.js` dans le dossier du thème enfant Kenta :
   ```
   wp-content/themes/kenta-child/
   ```

2. Ajouter le contenu de `functions-snippet.php` dans `functions.php` du thème enfant.

3. Vérifier que le thème enfant est bien actif dans WordPress (Apparence → Thèmes).

## Source de données

```
https://raw.githubusercontent.com/uneIAparjour/base/main/base-uneiaparjour.csv
```

Mise à jour automatique chaque nuit via le workflow `nightly-update.yml` du dépôt[`uneIAparjour/base`]([https://www.uneiaparjour.fr](https://github.com/uneIAparjour/base))

## Compatibilité

- Testé avec le thème Kenta Artistic Blog (WP Moose)
- Le sélecteur de la loupe est détecté automatiquement parmi plusieurs candidats connus du thème
- Si le bouton est injecté dynamiquement, un `MutationObserver` prend le relais (timeout 5s)

## Licence

CC BY 4.0 — Bertrand Formet
