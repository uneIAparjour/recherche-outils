# recherche-outils

Moteur de recherche multi-catégories pour [uneiaparjour.fr](https://www.uneiaparjour.fr).

## Fonctionnement

Un overlay plein écran s'ouvre au clic sur la loupe du thème WordPress (Kenta Artistic Blog). Il permet de rechercher parmi toutes les publications d'applications référencées sur le site, avec :

- **Recherche textuelle** sur le titre et la description, avec surbrillance des occurrences
- **Recherche multi-mots** : chaque mot saisi doit être présent (logique ET implicite)
- **Insensibilité aux accents** : "edition" trouve "édition" et inversement
- **Tolérance au pluriel** : "image" trouve "images" et inversement
- **Filtrage par catégories** (tags cliquables, multi-sélection, triés alphabétiquement)
- **Logique ET / OU** entre les catégories sélectionnées (visible dès 2 tags actifs, ET par défaut)
- **Pagination** par blocs de 48 résultats
- Clic sur un tag dans une carte → active immédiatement ce filtre

Les données sont chargées à l'ouverture depuis le CSV du dépôt [`uneIAparjour/base`](https://github.com/uneIAparjour/base) (mis à jour automatiquement chaque nuit).

## Fichiers

| Fichier | Rôle |
|---|---|
| `recherche-overlay.css` | Styles de l'overlay |
| `recherche-overlay.js`  | Logique : chargement CSV, filtres, rendu |
| `functions-snippet.php` | Extrait à ajouter dans `functions.php` du thème enfant |

## Installation

1. Copier `recherche-overlay.css` et `recherche-overlay.js` à la racine du dossier du thème enfant, pour uneIAparjour.fr : wp-content/themes/kenta-artistic-blog

2. Ajouter le contenu de `functions-snippet.php` à la fin de `functions.php` du thème enfant.

3. Vider le cache après chaque mise à jour des fichiers JS/CSS. Pour uneIaparjour.fr, depuis WP Super Cache.

## Source de données

```
https://raw.githubusercontent.com/uneIAparjour/base/main/base-uneiaparjour.csv
```

Mise à jour automatique chaque nuit via le workflow `nightly-update.yml` du dépôt [`uneIAparjour/base`](https://github.com/uneIAparjour/base).

## Compatibilité et points techniques

- Thème : **Kenta Artistic Blog** (WP Moose)
- Sélecteur de la loupe : `.kenta-search-button` (classe native du thème)
- Interception via écoute `document` en phase de capture (`true`) pour passer avant le système `kenta-toggleable` natif, qui ouvre normalement `#kenta-search-modal`
- La modal Kenta est refermée immédiatement via `setTimeout` si elle s'ouvre en parallèle
- PapaParse chargé via CDN (cdnjs.cloudflare.com), en footer
- **Cache** : le cache doit être vidé après chaque déploiement d'une nouvelle version JS

## Licence

CC BY 4.0 — Bertrand Formet
