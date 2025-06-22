# Soschu-Temp : Compilation pour Windows

Ce projet permet de générer un exécutable Windows (.exe) depuis macOS en utilisant PyInstaller en mode cross-compilation.

## Compilation de l'exécutable Windows

Pour générer un exécutable Windows (.exe) compatible, utilisez la commande suivante :

```bash
poetry run build-exe
```

Cette commande va :
1. Créer un fichier de spécification PyInstaller optimisé pour Windows
2. Compiler votre application en un exécutable Windows
3. Placer le fichier .exe généré dans le dossier `dist/windows/`

## Localisation de l'exécutable

L'exécutable Windows sera généré à :

```
dist/windows/soschu_temp.exe
```

## Résolution des problèmes

Si vous rencontrez des erreurs lors de la compilation :

1. Vérifiez que l'icône `.ico` existe dans le dossier `tools/assets/`
2. Assurez-vous que PyInstaller est bien installé (`pip install pyinstaller`)
3. Si la compilation échoue sur macOS, tentez une compilation directe sur une machine Windows

## Notes sur Cross-Compilation

La cross-compilation peut parfois générer des exécutables incompatibles selon les bibliothèques utilisées. Si l'exécutable ne fonctionne pas correctement sur Windows, envisagez d'effectuer la compilation sur une machine Windows native.

## Structure du projet

- `tools/build_exe.py` : Script de génération d'exécutable Windows
- `tools/icon.py` : Utilitaire pour générer des icônes au format .ico
- `tools/assets/` : Contient les fichiers ressources comme l'icône de l'application
