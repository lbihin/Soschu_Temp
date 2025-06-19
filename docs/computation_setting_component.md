# ComputationSetting Component

## Description
Le composant `ComputationSetting` est un widget réutilisable pour créer des paramètres de calcul avec :
- Un label descriptif
- Un champ de saisie avec valeur par défaut
- Une unité affichée à côté
- Une info-bulle optionnelle avec description

## Utilisation de base

```python
from gui.components.computation_setting import ComputationSetting

# Créer un paramètre simple
temperature_setting = ComputationSetting(
    parent_frame,
    setting_name="Temperature",
    default_value="25.0",
    unit_text="°C"
)
temperature_setting.grid(row=0, column=0, padx=5, pady=5)
```

## Utilisation avec validation numérique et tooltip

```python
pressure_setting = ComputationSetting(
    parent_frame,
    setting_name="Pressure",
    default_value="1013.25",
    unit_text="hPa",
    tooltip_description="Atmospheric pressure in hectopascals",
    validate_numeric=True,
    entry_width=12
)
pressure_setting.grid(row=0, column=1, padx=5, pady=5)
```

## Utilisation avec la fonction helper

```python
from gui.services import create_computation_setting

# Plus simple avec la fonction helper
coefficient = create_computation_setting(
    parent_frame,
    setting_name="Heat Transfer Coefficient",
    default_value="0.85",
    unit_text="W/m²K",
    tooltip_description="Heat transfer coefficient for thermal calculations",
    validate_numeric=True,
    row=0,
    column=2
)
```

## Méthodes disponibles

- `get_value()` : Retourne la valeur string du champ
- `get_numeric_value()` : Retourne la valeur float (ou None si invalide)
- `set_value(value)` : Définit une nouvelle valeur
- `clear()` : Vide le champ
- `is_valid()` : Vérifie si la valeur est valide (pour les champs numériques)
- `set_enabled(enabled)` : Active/désactive le champ

## Paramètres du constructeur

- `parent` : Widget parent
- `setting_name` : Nom du paramètre (affiché comme label)
- `default_value` : Valeur par défaut (string)
- `unit_text` : Texte de l'unité 
- `tooltip_description` : Description pour l'info-bulle (optionnel)
- `entry_width` : Largeur du champ de saisie (défaut: 15)
- `validate_numeric` : Active la validation numérique (défaut: False)

## Exemple complet

```python
import tkinter as tk
from gui.components.computation_setting import ComputationSetting

root = tk.Tk()
frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Configuration de la grille
frame.grid_columnconfigure(0, weight=1)
frame.grid_columnconfigure(1, weight=1)
frame.grid_columnconfigure(2, weight=1)

# Créer plusieurs paramètres
settings = [
    ComputationSetting(frame, "Temperature", "25.0", "°C", 
                      "Ambient temperature", True),
    ComputationSetting(frame, "Humidity", "60", "%", 
                      "Relative humidity", True),
    ComputationSetting(frame, "Wind Speed", "5.0", "m/s", 
                      "Wind speed at measurement height", True)
]

# Les placer dans la grille
for i, setting in enumerate(settings):
    setting.grid(row=0, column=i, padx=5, pady=5)

root.mainloop()
```
