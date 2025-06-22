#!/usr/bin/env python3
"""
Script d'entrée pour la compilation native.
Ce script compile un exécutable pour la plateforme actuelle (Windows ou macOS).
Usage: poetry run build-native [windows|macos]
"""

import argparse
import platform
import sys
from pathlib import Path

from tools.build_exe import (
    build_native_macos,
    build_native_windows,
    build_windows_on_macos,
)


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Compiler un exécutable natif pour la plateforme spécifiée."
    )
    parser.add_argument(
        "platform",
        choices=["windows", "macos"],
        nargs="?",
        help="Plateforme cible (windows ou macos). Par défaut: plateforme actuelle.",
    )
    args = parser.parse_args()

    # Obtenir le chemin absolu du répertoire actuel du projet
    project_root = Path(__file__).parent.parent.absolute()
    entrypoint = project_root / "src" / "main.py"
    exe_name = "soschu_temp"
    icon_path = project_root / "tools" / "assets" / "icon.ico"

    # Détecter la plateforme actuelle
    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"

    # Sélectionner la plateforme cible
    target_platform = args.platform
    if not target_platform:
        # Si aucune plateforme n'est spécifiée, utiliser la plateforme actuelle
        target_platform = "windows" if is_windows else "macos" if is_macos else None

    # Créer le répertoire de sortie
    dist_dir = project_root / "dist" / target_platform
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Compiler selon la plateforme cible
    if target_platform == "windows":
        if is_windows:
            # Compilation native Windows sur Windows
            success = build_native_windows(
                project_root, entrypoint, exe_name, icon_path, dist_dir
            )
        elif is_macos:
            # Cross-compilation Windows depuis macOS
            success = build_windows_on_macos(
                project_root, entrypoint, exe_name, icon_path, dist_dir
            )
        else:
            print(
                f"[ERREUR] Impossible de compiler pour Windows depuis {platform.system()}"
            )
            return 1
    elif target_platform == "macos":
        if is_macos:
            # Compilation native macOS sur macOS
            success = build_native_macos(project_root, entrypoint, exe_name, dist_dir)
        else:
            print(
                f"[ERREUR] Impossible de compiler pour macOS depuis {platform.system()}"
            )
            return 1
    else:
        print(f"[ERREUR] Plateforme cible non reconnue: {target_platform}")
        return 1

    if success:
        print(f"[SUCCÈS] Exécutable compilé pour {target_platform}")
        if target_platform == "windows":
            print(f"[INFO] Exécutable disponible: {dist_dir / (exe_name + '.exe')}")
        else:
            print(f"[INFO] Exécutable disponible: {dist_dir / exe_name}")
        return 0
    else:
        print(f"[ERREUR] La compilation a échoué pour {target_platform}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
