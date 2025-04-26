# TCG Collector Image Scraper

Un script Python pour extraire les URLs des images de cartes depuis le site TCG Collector.

## Installation

1. Cloner ce dépôt ou télécharger les fichiers
2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

Le script peut être lancé avec différentes options :

```bash
python tcg_scraper.py [OPTIONS]
```

### Options disponibles

- `--order` : Ordre des dates de sortie (`oldToNew` ou `newToOld`)
- `--per-page` : Nombre de cartes par page (`30`, `60`, ou `120`). Par défaut : `60`
- `--search` : Terme de recherche pour les cartes (utilisez des guillemets pour les termes avec des espaces, ex: `--search "vstar universe"`)
- `--start-page` : Première page à extraire (par défaut : 1)
- `--end-page` : Dernière page à extraire (si non spécifié, toutes les pages disponibles seront extraites)
- `--output` : Fichier de sortie pour les URLs des images (si non spécifié, sera généré automatiquement à partir du terme de recherche et de la date/heure)
- `--jp` : Activer pour extraire les cartes japonaises (utilise l'URL "/cards/jp")
- `--sort-by` : Trier par rareté (`rarityDesc` pour décroissant ou `rarityAsc` pour croissant)
- `--force` : Ignorer la limite de pages initialement détectée, mais s'arrêtera automatiquement quand il n'y aura plus d'images

### Exemples

Exemple 1: Extraire toutes les cartes en ordre chronologique (du plus ancien au plus récent)
```bash
python tcg_scraper.py --order oldToNew
```

Exemple 2: Rechercher "Pikachu" avec 120 cartes par page, seulement les pages 1 à 3
```bash
python tcg_scraper.py --search "Pikachu" --per-page 120 --start-page 1 --end-page 3
```

Exemple 3: Extraire les 5 premières pages des cartes les plus récentes
```bash
python tcg_scraper.py --order newToOld --end-page 5
```

Exemple 4: Extraire les cartes japonaises
```bash
python tcg_scraper.py --jp
```

Exemple 5: Extraire les cartes en ordre de rareté décroissante
```bash
python tcg_scraper.py --sort-by rarityDesc
```

Exemple 6: Rechercher les cartes "VSTAR Universe" en japonais, ignorer la limite de pages détectée
```bash
python tcg_scraper.py --jp --search "vstar universe" --sort-by rarityDesc --end-page 20 --force
```

## Sortie

Le script génère un fichier texte contenant une URL d'image par ligne, chaque ligne se terminant par un point-virgule (`;`). 

Si aucun nom de fichier n'est spécifié avec `--output`, le script génère automatiquement un nom de fichier basé sur:
- Le terme de recherche (convertit en minuscules et remplace les caractères spéciaux par des underscores)
- Si l'option `--jp` est utilisée
- La date et l'heure actuelles (au format YYYY-MM-DD_HH-MM-SS)

Exemples de noms de fichiers générés:
- `vstar_universe_jp_2023-08-01_14-30-45.txt` (pour une recherche "vstar universe" avec option `--jp`)
- `pikachu_2023-08-01_14-30-45.txt` (pour une recherche "Pikachu")
- `all-cards_2023-08-01_14-30-45.txt` (si aucun terme de recherche n'est spécifié) 