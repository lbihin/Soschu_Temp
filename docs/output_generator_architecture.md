# OutputGenerator Architecture

Cette documentation décrit la nouvelle architecture de génération de fichiers qui utilise le pattern Strategy pour séparer clairement la logique de traitement des données de la génération de fichiers.

## Vue d'ensemble

L'architecture utilise plusieurs design patterns pour créer une solution flexible et extensible :

1. **Strategy Pattern** : Pour les différents formats de sortie
2. **Factory Pattern** : Pour créer facilement des générateurs préconfigurés
3. **Dependency Injection** : Pour découpler le traitement de la génération

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Processing Logic                    │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  CoreProcessor  │ -> │      OutputGenerator           │ │
│  │                 │    │                                 │ │
│  │ - Data Loading  │    │ ┌─────────────────────────────┐ │ │
│  │ - Synchronization│    │ │     OutputStrategy          │ │ │
│  │ - Preprocessing │    │ │   (Strategy Pattern)        │ │ │
│  │ - Adjustments   │    │ │                             │ │ │
│  └─────────────────┘    │ │ ┌─────────────────────────┐ │ │ │
│                         │ │ │   TRYFormatStrategy    │ │ │ │
│                         │ │ └─────────────────────────┘ │ │ │
│                         │ │ ┌─────────────────────────┐ │ │ │
│                         │ │ │   CSVFormatStrategy    │ │ │ │
│                         │ │ └─────────────────────────┘ │ │ │
│                         │ │ ┌─────────────────────────┐ │ │ │
│                         │ │ │   JSONFormatStrategy   │ │ │ │
│                         │ │ └─────────────────────────┘ │ │ │
│                         │ └─────────────────────────────┘ │ │
│                         └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Classes principales

### OutputStrategy (Interface abstraite)

```python
class OutputStrategy(ABC):
    @abstractmethod
    def generate_output(self, file_path: Path, metadata: WeatherFileMetadata, 
                       data_points: List[WeatherDataPoint], **kwargs: Any) -> None:
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        pass
```

### Implémentations concrètes

1. **TRYFormatStrategy** : Génère des fichiers au format TRY original
2. **CSVFormatStrategy** : Génère des fichiers CSV configurables
3. **JSONFormatStrategy** : Génère des fichiers JSON avec métadonnées

### OutputGenerator (Context)

Le générateur principal qui utilise une stratégie pour créer les fichiers :

```python
class OutputGenerator:
    def __init__(self, strategy: OutputStrategy):
        self.strategy = strategy
    
    def generate_file(self, file_path: Path, metadata: WeatherFileMetadata, 
                     data_points: List[WeatherDataPoint], **kwargs: Any) -> Path:
        # Utilise la stratégie actuelle pour générer le fichier
        self.strategy.generate_output(file_path, metadata, data_points, **kwargs)
        return file_path
    
    def set_strategy(self, strategy: OutputStrategy) -> None:
        # Permet de changer de stratégie à l'exécution
        self.strategy = strategy
```

## Avantages de cette architecture

### 1. Séparation des responsabilités
- **CoreProcessor** : Se concentre uniquement sur le traitement des données
- **OutputGenerator** : Se concentre uniquement sur la génération de fichiers
- **OutputStrategy** : Chaque stratégie gère un format spécifique

### 2. Extensibilité
Ajouter un nouveau format est simple :

```python
class XMLFormatStrategy(OutputStrategy):
    def generate_output(self, file_path: Path, metadata: WeatherFileMetadata,
                       data_points: List[WeatherDataPoint], **kwargs: Any) -> None:
        # Implémentation pour XML
        pass
    
    def get_file_extension(self) -> str:
        return ".xml"
```

### 3. Flexibilité
- Changement de format à l'exécution
- Configuration personnalisée par format
- Réutilisation des stratégies

### 4. Testabilité
- Chaque composant peut être testé indépendamment
- Mock facile des stratégies pour les tests
- Injection de dépendances facilite les tests unitaires

## Utilisation

### Utilisation simple avec les factory functions

```python
from output_generator import create_try_generator, create_csv_generator

# Format TRY par défaut
output_files = process_weather_with_solar_data(
    weather_file, solar_file, threshold, delta_t
)

# Format CSV
csv_generator = create_csv_generator()
output_files = process_weather_with_solar_data(
    weather_file, solar_file, threshold, delta_t, 
    output_dir="output", output_generator=csv_generator
)
```

### Utilisation avancée avec configuration personnalisée

```python
from output_generator import OutputGenerator, CSVFormatStrategy

# CSV avec point-virgule comme délimiteur
custom_csv = OutputGenerator(CSVFormatStrategy(delimiter=";", include_header=False))
output_files = process_weather_with_solar_data(
    weather_file, solar_file, threshold, delta_t,
    output_generator=custom_csv
)
```

### Changement dynamique de stratégie

```python
generator = create_try_generator()

# Génération en format TRY
process_weather_with_solar_data(..., output_generator=generator)

# Changement vers CSV
generator.set_strategy(CSVFormatStrategy())
process_weather_with_solar_data(..., output_generator=generator)
```

## Patterns utilisés

### 1. Strategy Pattern
- **Contexte** : `OutputGenerator`
- **Interface Strategy** : `OutputStrategy`
- **Stratégies concrètes** : `TRYFormatStrategy`, `CSVFormatStrategy`, `JSONFormatStrategy`

**Avantage** : Permet de varier l'algorithme de génération de fichier indépendamment du client qui l'utilise.

### 2. Factory Pattern
```python
def create_try_generator() -> OutputGenerator:
    return OutputGenerator(TRYFormatStrategy())

def create_csv_generator(delimiter=",", include_header=True) -> OutputGenerator:
    return OutputGenerator(CSVFormatStrategy(delimiter, include_header))
```

**Avantage** : Simplifie la création d'objets complexes et fournit une interface claire.

### 3. Dependency Injection
```python
class CoreProcessor:
    def __init__(self, output_generator: Optional[OutputGenerator] = None):
        self.output_generator = output_generator or create_try_generator()
```

**Avantage** : Facilite les tests et rend le code plus flexible.

## Migration depuis l'ancienne architecture

### Avant
```python
class CoreProcessor:
    def save_weather_data(self, file_path, metadata, weather_data):
        # Logique de génération de fichier mélangée avec le traitement
        with open(file_path, "w") as f:
            # ... code de génération ...
```

### Après
```python
class CoreProcessor:
    def __init__(self, output_generator: Optional[OutputGenerator] = None):
        self.output_generator = output_generator or create_try_generator()
    
    def process_all_facades(...):
        # ... logique de traitement ...
        self.output_generator.generate_file(output_file_path, metadata, data)
```

## Extension future

Cette architecture facilite l'ajout de nouvelles fonctionnalités :

1. **Nouveaux formats** : Créer une nouvelle `OutputStrategy`
2. **Compression** : Ajouter une couche de compression dans `OutputGenerator`
3. **Validation** : Ajouter validation des données avant génération
4. **Métadonnées enrichies** : Facilement ajoutables dans chaque stratégie
5. **Output multiple** : Générer plusieurs formats simultanément

## Conclusion

Cette nouvelle architecture offre :
- ✅ Séparation claire des responsabilités
- ✅ Code plus maintenable et testable
- ✅ Extensibilité pour de nouveaux formats
- ✅ Flexibilité dans l'utilisation
- ✅ Respect des principes SOLID
- ✅ Utilisation appropriée des design patterns
