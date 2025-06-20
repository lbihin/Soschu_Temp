# Preview-Based Workflow Documentation

Cette documentation décrit le nouveau workflow basé sur la prévisualisation qui sépare la computation des ajustements de la génération des fichiers.

## Vue d'ensemble

Le nouveau système fonctionne en deux étapes distinctes :

1. **Preview** : Calcule tous les ajustements et prépare les données sans sauvegarder de fichiers
2. **Generation** : Utilise les données pré-calculées pour générer les fichiers sélectionnés

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Preview Phase                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  preview_weather_solar_processing()                    │ │
│  │                                                         │ │
│  │  • Load weather + solar data                           │ │
│  │  • For each facade:                                    │ │
│  │    - Create deep copy of weather data                  │ │
│  │    - Apply adjustments to copy                         │ │
│  │    - Store adjusted data by facade                     │ │
│  │  • Return PreviewResult with:                          │ │
│  │    - Statistics and sample adjustments                 │ │
│  │    - Adjusted weather data by facade                   │ │
│  │    - Metadata for file generation                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
                        User reviews preview
                        Selects facades to generate
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Generation Phase                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  generate_files_from_preview()                         │ │
│  │                                                         │ │
│  │  • Use pre-computed adjusted data                      │ │
│  │  • Generate files for selected facades only            │ │
│  │  • Support multiple output formats                     │ │
│  │  • No redundant calculations                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Fonctions principales

### `preview_weather_solar_processing()`

**Objectif** : Calcule tous les ajustements et prépare les données sans créer de fichiers.

**Paramètres** :
- `weather_file_path` : Chemin vers le fichier météo
- `solar_file_path` : Chemin vers le fichier solaire HTML
- `threshold` : Seuil d'irradiance solaire en W/m²
- `delta_t` : Augmentation de température en °C
- `max_sample_adjustments` : Nombre max d'ajustements d'exemple à retourner

**Retourne** : `PreviewResult` contenant :
- `facade_combinations` : Liste des combinaisons façade/bâtiment trouvées
- `total_adjustments` : Nombre total d'ajustements qui seront appliqués
- `adjustments_by_facade` : Nombre d'ajustements par façade
- `sample_adjustments` : Échantillons d'ajustements pour l'affichage
- `parameters` : Paramètres utilisés
- `weather_metadata` : Métadonnées du fichier météo
- `adjusted_weather_data_by_facade` : **Données météo ajustées par façade**

### `generate_files_from_preview()`

**Objectif** : Génère les fichiers de sortie à partir des données pré-calculées.

**Paramètres** :
- `preview_result` : Résultat de la prévisualisation
- `output_dir` : Répertoire de sortie
- `output_generator` : Générateur de sortie (optionnel)
- `selected_facades` : Façades sélectionnées (optionnel, toutes par défaut)

**Retourne** : Dictionnaire mappant les façades aux chemins des fichiers générés.

## Utilisation

### 1. Workflow basique

```python
from core import preview_weather_solar_processing, generate_files_from_preview

# Étape 1: Prévisualisation (pas de fichiers créés)
preview_result = preview_weather_solar_processing(
    weather_file="data/weather.dat",
    solar_file="data/solar.html",
    threshold=200.0,
    delta_t=7.0
)

# Afficher les statistiques à l'utilisateur
print(f"Total adjustments: {preview_result.total_adjustments}")
for facade, count in preview_result.adjustments_by_facade.items():
    print(f"  {facade}: {count} adjustments")

# Étape 2: Génération des fichiers (seulement quand l'utilisateur confirme)
output_files = generate_files_from_preview(
    preview_result,
    output_dir="output",
    selected_facades=["f2_Building body", "f3_Building body"]
)
```

### 2. Workflow avec différents formats

```python
from output_generator import create_csv_generator, create_json_generator

# Prévisualisation
preview_result = preview_weather_solar_processing(...)

# Génération en CSV
csv_files = generate_files_from_preview(
    preview_result,
    output_dir="output/csv",
    output_generator=create_csv_generator()
)

# Génération en JSON
json_files = generate_files_from_preview(
    preview_result,
    output_dir="output/json", 
    output_generator=create_json_generator()
)
```

### 3. Analyse des données ajustées

```python
# Analyser les données avant génération
for facade_key, weather_data in preview_result.adjusted_weather_data_by_facade.items():
    adjusted_points = [wp for wp in weather_data if wp.adjusted_temperature != wp.temperature]
    
    print(f"Facade {facade_key}:")
    print(f"  Adjusted points: {len(adjusted_points)} / {len(weather_data)}")
    
    if adjusted_points:
        avg_increase = sum(wp.adjusted_temperature - wp.temperature for wp in adjusted_points) / len(adjusted_points)
        print(f"  Average temperature increase: {avg_increase:.2f}°C")
```

## Avantages du nouveau système

### 1. **Séparation claire des responsabilités**
- **Preview** : Computation et analyse des données
- **Generation** : Création des fichiers de sortie

### 2. **Expérience utilisateur améliorée**
- L'utilisateur voit exactement ce qui sera ajusté avant la génération
- Possibilité de sélectionner quelles façades générer
- Pas d'attente lors de la prévisualisation

### 3. **Performance optimisée**
- Calculs effectués une seule fois lors de la prévisualisation
- Génération de fichiers très rapide (pas de recalcul)
- Possibilité de générer plusieurs formats à partir des mêmes données

### 4. **Flexibilité**
- Génération sélective des façades
- Support de multiples formats de sortie
- Possibilité d'analyser les données avant génération

### 5. **Robustesse**
- Séparation des erreurs de calcul et de génération
- Possibilité de régénérer les fichiers sans recalculer

## Intégration avec l'interface utilisateur

### Dans la fenêtre de prévisualisation

```python
# Bouton "Preview" dans l'interface
def on_preview_clicked():
    try:
        preview_result = preview_weather_solar_processing(
            weather_file, solar_file, threshold, delta_t
        )
        
        # Afficher les statistiques
        display_preview_statistics(preview_result)
        
        # Afficher les échantillons d'ajustements
        display_sample_adjustments(preview_result.sample_adjustments)
        
        # Permettre à l'utilisateur de sélectionner les façades
        enable_facade_selection(preview_result.facade_combinations)
        
        # Stocker le résultat pour la génération ultérieure
        self.current_preview_result = preview_result
        
    except Exception as e:
        show_error(f"Preview failed: {e}")

# Bouton "Generate Files" dans l'interface
def on_generate_files_clicked():
    if not self.current_preview_result:
        show_error("No preview data available")
        return
    
    try:
        selected_facades = get_selected_facades_from_ui()
        output_format = get_selected_output_format()
        
        # Choisir le générateur selon le format
        generator = get_output_generator_for_format(output_format)
        
        output_files = generate_files_from_preview(
            self.current_preview_result,
            output_dir=self.output_directory,
            output_generator=generator,
            selected_facades=selected_facades
        )
        
        show_success(f"Generated {len(output_files)} files")
        
    except Exception as e:
        show_error(f"File generation failed: {e}")
```

## Migration depuis l'ancienne méthode

### Avant (ancienne méthode)
```python
# Calcul + génération en une seule étape
output_files = process_weather_with_solar_data(
    weather_file, solar_file, threshold, delta_t, output_dir
)
```

### Après (nouvelle méthode)
```python
# Étape 1: Prévisualisation
preview_result = preview_weather_solar_processing(
    weather_file, solar_file, threshold, delta_t
)

# Étape 2: Génération (si confirmée par l'utilisateur)
output_files = generate_files_from_preview(
    preview_result, output_dir, selected_facades=user_selection
)
```

## Structure des données

### PreviewResult
```python
PreviewResult(
    facade_combinations=[('f2', 'Building body'), ('f3', 'Building body'), ...],
    total_adjustments=3519,
    adjustments_by_facade={'f2_Building body': 1002, 'f3_Building body': 1598, ...},
    sample_adjustments=[PreviewAdjustment(...), ...],
    parameters={'threshold': 200.0, 'delta_t': 7.0, ...},
    weather_metadata=WeatherFileMetadata(...),
    adjusted_weather_data_by_facade={
        'f2_Building body': [WeatherDataPoint(adjusted_temperature=13.0, ...), ...],
        'f3_Building body': [WeatherDataPoint(adjusted_temperature=15.2, ...), ...],
        ...
    }
)
```

Cette nouvelle architecture offre une expérience utilisateur beaucoup plus fluide et une architecture plus robuste pour l'application.
