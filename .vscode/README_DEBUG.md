# Configuration de Débogage VS Code

## Configurations de Débogage Disponibles

### 1. **Debug Soschu Temperature Tool** (Configuration par défaut)
- **Point d'entrée** : `src/main.py`
- **Mode** : JustMyCode activé (ne s'arrête que sur votre code)
- **Usage** : Débogage normal de l'application

### 2. **Debug Soschu Tool (No JustMyCode)**
- **Point d'entrée** : `src/main.py`
- **Mode** : JustMyCode désactivé (peut s'arrêter dans les bibliothèques)
- **Usage** : Débogage approfondi, incluant les bibliothèques externes

### 3. **Debug Soschu Tool (Step Into Entry)**
- **Point d'entrée** : `src/main.py`
- **Mode** : S'arrête automatiquement au début du programme
- **Usage** : Débogage pas à pas depuis le début

## Comment Utiliser

### Méthode 1 : Menu Débogage
1. Ouvrez VS Code dans le dossier du projet
2. Allez dans le menu **Run** > **Start Debugging** (F5)
3. Sélectionnez la configuration désirée

### Méthode 2 : Panneau de Débogage
1. Cliquez sur l'icône de débogage dans la barre latérale (Ctrl+Shift+D)
2. Sélectionnez la configuration dans le menu déroulant
3. Cliquez sur le bouton Play ▶️

### Méthode 3 : Raccourcis Clavier
- **F5** : Démarre le débogage avec la configuration par défaut
- **Ctrl+F5** : Exécute sans débogage
- **Shift+F5** : Arrête le débogage

## Tâches Disponibles

### Exécution
- **Run Soschu Tool** (Ctrl+Shift+P > "Tasks: Run Task")
  - Exécute l'application sans débogage
  - Tâche de build par défaut (Ctrl+Shift+B)

### Développement
- **Install Dependencies** : Installe les dépendances avec Poetry
- **Run Tests** : Lance tous les tests avec pytest
- **Lint Code** : Vérifie le code avec flake8

## Points d'Arrêt (Breakpoints)

### Placer un Point d'Arrêt
1. Cliquez dans la marge gauche à côté du numéro de ligne
2. Ou placez le curseur sur une ligne et appuyez sur **F9**

### Types de Points d'Arrêt
- **Point d'arrêt simple** : S'arrête à chaque passage
- **Point d'arrêt conditionnel** : S'arrête seulement si une condition est vraie
- **Logpoint** : Affiche un message sans s'arrêter

## Variables et Expressions

### Panneau Variables
- Affiche toutes les variables locales et globales
- Permet de modifier les valeurs pendant le débogage

### Watch (Surveillance)
- Ajoutez des expressions à surveiller
- Clic droit > "Add to Watch" ou dans le panneau Watch

### Console de Débogage
- Exécutez du code Python dans le contexte actuel
- Accessible en bas de l'interface de débogage

## Conseils de Débogage

### Pour les Composants GUI (Tkinter)
1. Placez des points d'arrêt dans les callbacks des boutons
2. Utilisez la configuration "No JustMyCode" pour déboguer les problèmes Tkinter
3. Les variables Tkinter peuvent être complexes à inspecter

### Pour les Fonctions Backend
1. Testez d'abord les fonctions backend indépendamment
2. Utilisez des logpoints pour tracer l'exécution sans interrompre
3. Surveillez les arguments passés aux fonctions

### Pour le Threading
1. Les threads peuvent compliquer le débogage
2. Utilisez `run_in_thread=False` dans TriggerButton pour simplifier
3. Placez des points d'arrêt avant et après les appels de thread

## Structure des Fichiers de Configuration

```
.vscode/
├── launch.json     # Configurations de débogage
├── settings.json   # Paramètres VS Code spécifiques au projet
└── tasks.json      # Tâches automatisées
```

## Environnement Python

La configuration utilise automatiquement :
- **Interpréteur** : `.venv/bin/python` (environnement virtuel)
- **PYTHONPATH** : Inclut `src/` pour les imports
- **Working Directory** : Racine du projet

## Dépannage

### L'application ne démarre pas
1. Vérifiez que l'environnement virtuel est activé
2. Assurez-vous que les dépendances sont installées (`poetry install`)
3. Vérifiez les chemins dans `launch.json`

### Points d'arrêt ignorés
1. Assurez-vous que le fichier est sauvegardé
2. Vérifiez que vous utilisez la bonne configuration de débogage
3. Essayez "No JustMyCode" si vous déboguez des bibliothèques

### Problèmes de GUI
1. Tkinter peut parfois geler pendant le débogage
2. Utilisez "Continue" (F5) plutôt que "Step" dans les boucles d'événements
3. Fermez complètement l'application entre les sessions de débogage

## Extensions Recommandées

Pour une meilleure expérience de développement :
- **Python** (Microsoft) - Support Python complet
- **Python Debugger** (Microsoft) - Débogage Python avancé
- **Pylance** (Microsoft) - IntelliSense et type checking
- **GitLens** - Améliore l'intégration Git
