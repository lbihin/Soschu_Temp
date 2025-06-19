# Solar Data Processing Module

Le module `solar.py` fournit des fonctionnalités robustes pour parser et analyser les fichiers HTML d'irradiation solaire exportés depuis IDA Modeler.

## Fonctionnalités

### 1. Parsing de fichiers HTML
- Parse les fichiers HTML d'irradiation solaire d'IDA Modeler
- Extrait les métadonnées du projet (logiciel, objet, système, dates)
- Identifie automatiquement les colonnes de façades
- Support pour plusieurs bâtiments et orientations de façades

### 2. Modèles de données (Pydantic)
- `SolarDataPoint`: Point de données horaire avec validation
- `SolarFileMetadata`: Métadonnées extraites du fichier
- Validation automatique des valeurs d'irradiation (non-négatives)

### 3. Analyse des données
- Statistiques d'irradiation par façade
- Totaux journaliers et annuels
- Identification des périodes de forte irradiation
- Analyse par corps de bâtiment
- Validation de la qualité des données

### 4. Export et visualisation
- Export CSV avec gestion correcte des virgules
- Support pour l'analyse ultérieure

## Utilisation

### Parsing de base
```python
from src.solar import SolarDataParser, SolarDataAnalyzer

# Parser un fichier HTML
parser = SolarDataParser()
metadata, data_points = parser.parse_file("solar_data.html")

# Analyser les données
analyzer = SolarDataAnalyzer(data_points)
stats = analyzer.get_irradiance_stats()
```

### Analyse avancée
```python
# Obtenir les statistiques par façade
irradiance_stats = analyzer.get_irradiance_stats()
for facade, stats in irradiance_stats.items():
    print(f"{facade}: Max={stats['max']} W/m², Moyenne={stats['mean']:.1f} W/m²")

# Analyser par corps de bâtiment
building_stats = analyzer.get_building_body_stats()
for building, stats in building_stats.items():
    print(f"{building}: {stats['facade_count']} façades, Total={stats['total_irradiance']:.1f} kWh")

# Filtrer les périodes de forte irradiation
peak_periods = analyzer.get_peak_irradiance_periods(threshold=200.0)
print(f"Trouvé {len(peak_periods)} périodes avec irradiation > 200 W/m²")
```

### Export des données
```python
# Export CSV
analyzer.export_to_csv("solar_export.csv")

# Totaux journaliers
daily_totals = analyzer.get_daily_totals()
for date, totals in daily_totals.items():
    print(f"{date}: {sum(totals.values()):.1f} kWh total")
```

## Structure des données

### Format des colonnes de façade
Le parser reconnaît automatiquement les colonnes suivant le pattern :
- `"Gesamte solare Einstrahlung, f3$Building body, W/m2"`
- `"Gesamte solare Einstrahlung, f4$Building body 2, W/m2"`

Où :
- `f3`, `f4`, etc. = orientation de la façade
- `Building body` = corps de bâtiment principal
- `Building body 2` = corps de bâtiment secondaire (optionnel)

### Métadonnées extraites
- Titre du rapport
- Information sur le logiciel et licence
- Nom de l'objet/projet
- Chemin du système
- Dates de simulation et sauvegarde
- Liste des colonnes de façades

## Tests

Le module est entièrement testé avec :
- **28 tests unitaires** dans `test_solar.py`
- **6 tests d'intégration** dans `test_solar_integration.py`
- **Couverture de 91%** du code source

### Exécution des tests
```bash
# Tests solar uniquement
make test-solar

# Tests avec couverture
make test-coverage

# Tests spécifiques
poetry run pytest tests/test_solar.py -v
poetry run pytest tests/test_solar_integration.py -v
```

## Validation des données

Le module inclut une validation robuste :
- Valeurs d'irradiation non-négatives
- Validation des timestamps
- Détection des valeurs extrêmes (> 1500 W/m²)
- Identification des lacunes temporelles
- Score de qualité automatique

## Exemple de fichier de test

Un fichier de test minimal `solar_test_small.html` est fourni dans `tests/data/` pour démontrer le format attendu et tester les fonctionnalités.

## Intégration avec le projet

Le module solar s'intègre parfaitement avec le module weather existant :
- Même architecture Pydantic
- Tests pytest compatibles
- Même style de documentation
- Outils de développement partagés (Makefile, pytest.ini)

## Performances

- Parsing rapide (< 1 seconde pour fichiers moyens)
- Analyse efficace des données
- Gestion mémoire optimisée pour gros fichiers
- Support pour fichiers avec milliers de points de données
