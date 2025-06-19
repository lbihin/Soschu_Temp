# TriggerButton Component

## Description
Le composant `TriggerButton` est un bouton intelligent qui :
- Se désactive automatiquement si les éléments obligatoires ne sont pas présents
- Peut déclencher une fonction backend lors du clic
- Gère l'exécution en arrière-plan avec threading
- Affiche un état de chargement pendant l'exécution
- Fournit des callbacks pour succès et erreurs

## Fonctionnalités principales

### Validation automatique
Le bouton vérifie périodiquement (par défaut toutes les 500ms) si tous les éléments obligatoires sont valides :
- Widgets Entry avec contenu non vide
- Objets avec méthode `get_value()` retournant une valeur non nulle
- Objets avec méthode `is_valid()` retournant True
- Objets avec méthode `get_filename()` retournant un nom de fichier non vide
- Fonctions callable retournant True

### Exécution backend
- Exécution dans un thread séparé (configurable)
- Collecte automatique des arguments depuis les éléments obligatoires
- Gestion des erreurs avec callbacks
- État de chargement avec texte personnalisable

## Utilisation de base

```python
from gui.components.trigger_button import TriggerButton

def my_backend_function(arg1, arg2):
    # Votre logique backend ici
    import time
    time.sleep(2)  # Simulation d'un traitement long
    return f"Traitement terminé avec {arg1} et {arg2}"

def on_success(result):
    print(f"Succès: {result}")

def on_error(error):
    print(f"Erreur: {error}")

# Créer le bouton
button = TriggerButton(
    parent_frame,
    text="Exécuter",
    backend_function=my_backend_function,
    mandatory_elements=[entry1, entry2, file_selector],
    success_callback=on_success,
    error_callback=on_error,
    loading_text="Traitement en cours..."
)
```

## Utilisation avec la fonction helper

```python
from gui.services import create_trigger_button

# Plus simple avec la fonction helper
button = create_trigger_button(
    parent=params_frame,
    text="Calculer",
    backend_function=calculation_function,
    mandatory_elements=[weather_file, solar_file, temperature_setting],
    success_message="Calcul terminé",
    error_message="Erreur de calcul",
    row=0,
    column=2
)
```

## Types d'éléments obligatoires supportés

### Widgets Tkinter
```python
entry = tk.Entry(parent)
# Vérifie que entry.get() n'est pas vide
```

### Composants personnalisés
```python
file_selector = FileSelector(...)  # Utilise get_filename()
computation_setting = ComputationSetting(...)  # Utilise get_value() et is_valid()
```

### Fonctions de validation
```python
def custom_validation():
    return some_condition_is_met()

# Le bouton appellera cette fonction pour vérifier la validité
```

## Paramètres du constructeur

- `parent` : Widget parent
- `text` : Texte du bouton (défaut: "Execute")
- `backend_function` : Fonction à exécuter lors du clic
- `mandatory_elements` : Liste des éléments obligatoires
- `validate_function` : Fonction de validation personnalisée supplémentaire
- `success_callback` : Fonction appelée en cas de succès
- `error_callback` : Fonction appelée en cas d'erreur
- `loading_text` : Texte affiché pendant l'exécution (défaut: "Processing...")
- `run_in_thread` : Exécution en thread séparé (défaut: True)
- `check_interval` : Intervalle de vérification en ms (défaut: 500)

## Méthodes utiles

- `add_mandatory_element(element)` : Ajoute un élément obligatoire
- `remove_mandatory_element(element)` : Supprime un élément obligatoire
- `set_backend_function(func)` : Définit/change la fonction backend
- `force_validate()` : Force une vérification immédiate
- `simulate_click()` : Simule un clic (utile pour les tests)

## Exemple complet avec FileSelector et ComputationSetting

```python
import tkinter as tk
from gui.services import create_file_selector, create_computation_setting, create_trigger_button

def backend_calculation(weather_file, solar_file, threshold, delta_t):
    print(f"Traitement: {weather_file}, {solar_file}")
    print(f"Paramètres: seuil={threshold}, ΔT={delta_t}")
    
    # Simulation d'un calcul
    import time
    time.sleep(3)
    
    return "Calcul terminé avec succès"

root = tk.Tk()
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Créer les éléments obligatoires
weather_selector = create_file_selector(
    frame, "Fichier météo:", ".dat", "Weather files", row=0
)

solar_selector = create_file_selector(
    frame, "Fichier solaire:", ".html", "HTML files", row=1
)

threshold_setting = create_computation_setting(
    frame, "Seuil", "200", "W/m²", 
    tooltip_description="Seuil de rayonnement",
    validate_numeric=True, row=2, column=0
)

delta_t_setting = create_computation_setting(
    frame, "ΔT", "7", "°C",
    tooltip_description="Différence de température",
    validate_numeric=True, row=2, column=1
)

# Créer le bouton trigger
calculate_button = create_trigger_button(
    frame,
    text="Calculer",
    backend_function=backend_calculation,
    mandatory_elements=[weather_selector, solar_selector, threshold_setting, delta_t_setting],
    success_message="Calcul réussi",
    error_message="Erreur de calcul",
    row=3, column=0, columnspan=2
)

root.mainloop()
```

## Gestion des erreurs

Le bouton gère automatiquement :
- Exceptions dans la fonction backend
- Éléments obligatoires manquants
- Erreurs de validation
- Timeouts (si implémentés dans la fonction backend)

Les erreurs sont transmises au callback d'erreur ou affichées dans la console par défaut.
