# Tests pour le module Weather

Ce dossier contient une suite complète de tests pour le module de traitement des données météorologiques.

## Structure des Tests

### `conftest.py`
Contient les fixtures pytest partagées :
- `sample_weather_file` : Chemin vers le fichier de données météo d'exemple
- `sample_weather_data_point` : Point de données météo valide pour les tests
- `sample_metadata` : Métadonnées d'exemple
- `sample_data_points` : Liste de points de données pour une journée
- `weather_analyzer` : Instance d'analyseur avec données d'exemple
- `invalid_weather_data` : Données invalides pour tester la validation

### `test_weather_models.py`
Tests pour les modèles Pydantic :
- **`TestWeatherDataPoint`** : Tests pour la classe `WeatherDataPoint`
  - Création valide de points de données
  - Calculs (irradiance solaire totale, conversion datetime)
  - Méthodes utilitaires (`is_daylight_hour`, `is_high_solar`)
  - Validation des données (température, direction vent, etc.)
  - Sérialisation/désérialisation

- **`TestWeatherFileMetadata`** : Tests pour la classe `WeatherFileMetadata`
  - Création avec valeurs par défaut
  - Méthodes utilitaires (`get_location_string`, `get_summary`)
  - Sérialisation et nettoyage des espaces

### `test_weather_parser.py`
Tests pour le parser de fichiers météo :
- **`TestWeatherDataParser`** : Tests pour la classe `WeatherDataParser`
  - Initialisation du parser
  - Parsing de fichiers (succès et erreurs)
  - Extraction des métadonnées depuis l'en-tête
  - Parsing des lignes de données individuelles
  - Gestion des erreurs (fichier inexistant, format invalide)
  - Validation des champs numériques

### `test_weather_analyzer.py`
Tests pour l'analyseur de données :
- **`TestWeatherDataAnalyzer`** : Tests pour la classe `WeatherDataAnalyzer`
  - Calculs statistiques (température, radiation solaire, vent)
  - Filtrage par mois et par heure
  - Données des heures de jour
  - Export JSON
  - Périodes de forte radiation solaire
  - Validation de la qualité des données
  - Gestion des cas limites (données vides, point unique)

### `test_integration.py`
Tests d'intégration pour le pipeline complet :
- **`TestWeatherIntegration`** : Tests end-to-end
  - Chargement et analyse complète des données
  - Analyses saisonnières
  - Patterns horaires
  - Consistance entre parser et analyseur
  - Tests des méthodes des points de données avec vraies données

### `test_performance.py`
Tests de performance (marqués avec `@pytest.mark.slow`) :
- **`TestWeatherPerformance`** : Tests de performance
  - Temps de parsing des fichiers
  - Performance des calculs statistiques
  - Validation efficace des points de données
  - Performance du filtrage sur gros datasets
  - Utilisation mémoire raisonnable

## Exécution des Tests

### Commandes de base
```bash
# Tous les tests
poetry run pytest

# Tests avec détails
poetry run pytest -v

# Tests avec couverture
poetry run pytest --cov=src --cov-report=html
```

### Utilisation du Makefile
```bash
# Tous les tests
make test

# Tests unitaires seulement
make test-unit

# Tests d'intégration seulement
make test-integration

# Tests spécifiques
make test-models
make test-parser
make test-analyzer

# Tests avec couverture
make test-coverage

# Tests avec sortie détaillée
make test-verbose
```

### Filtrage par marqueurs
```bash
# Exclure les tests lents
pytest -m "not slow"

# Seulement les tests d'intégration
pytest -m "integration"

# Seulement les tests unitaires
pytest -m "unit"
```

## Configuration

### `pytest.ini`
Configuration pytest avec :
- Chemins de test
- Marqueurs personnalisés
- Filtres d'avertissement
- Options par défaut

### Couverture de Code
- Configuration dans `pytest.ini`
- Rapports HTML générés dans `htmlcov/`
- Exclusion des fichiers de test
- Lignes exclues (pragmas, méthodes abstraites, etc.)

## Fixtures et Données de Test

### Données d'Exemple
- Utilise le fichier `tests/data/TRY2045_488284093163_Jahr.dat`
- Génère des données synthétiques pour les tests unitaires
- Cas de test avec données invalides pour validation

### Mocking
- Utilise `unittest.mock` pour simuler des opérations fichier
- Tests d'erreurs d'encodage et de fichiers manquants
- Isolation des tests du système de fichiers

## Bonnes Pratiques

### Structure des Tests
- Un fichier de test par module principal
- Classes de test groupées par fonctionnalité
- Noms de test descriptifs
- Documentation des cas de test

### Assertions
- Assertions spécifiques et descriptives
- Vérification des types et valeurs
- Tests des cas limites et erreurs
- Validation des contraintes métier

### Performance
- Tests de performance séparés avec marqueur `slow`
- Métriques de temps et mémoire
- Tests de scalabilité
- Validation des optimisations Pydantic

## Couverture Actuelle

- **Module weather.py** : 86% de couverture
- **Total projet** : 75% de couverture
- **51 tests** passent avec succès
- **Temps d'exécution** : ~0.5 secondes (tests rapides)

## Ajout de Nouveaux Tests

Pour ajouter de nouveaux tests :

1. **Tests unitaires** : Ajouter dans le fichier approprié (`test_weather_models.py`, etc.)
2. **Tests d'intégration** : Ajouter dans `test_integration.py`
3. **Tests de performance** : Ajouter dans `test_performance.py` avec marqueur `@pytest.mark.slow`
4. **Nouvelles fixtures** : Ajouter dans `conftest.py`

### Exemple de nouveau test
```python
def test_nouvelle_fonctionnalite(sample_weather_data_point):
    """Test de la nouvelle fonctionnalité."""
    # Arrange
    point = sample_weather_data_point
    
    # Act
    result = point.nouvelle_methode()
    
    # Assert
    assert result is not None
    assert isinstance(result, expected_type)
```
