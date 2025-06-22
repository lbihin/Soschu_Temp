#!/usr/bin/env python3
"""
Script d'entrée pour la compilation locale macOS.
Ce script compile à la fois un exécutable macOS natif et un exécutable Windows via cross-compilation.
Fonctionne uniquement sur macOS.
Usage: poetry run build-local
"""

import platform
import sys
from pathlib import Path

from tools.build_exe import build_native_macos, build_windows_on_macos


def main():
    """Fonction principale du script."""
    # Vérifier que nous sommes bien sur macOS
    if platform.system() != "Darwin":
        print(
            f"[ERREUR] Ce script ne fonctionne que sur macOS, pas sur {platform.system()}"
        )
        return 1

    # Obtenir le chemin absolu du répertoire actuel du projet
    project_root = Path(__file__).parent.parent.absolute()
    entrypoint = project_root / "src" / "main.py"
    exe_name = "soschu_temp"
    icon_path = project_root / "tools" / "assets" / "icon.ico"

    # Créer les répertoires de sortie
    dist_dir_macos = project_root / "dist" / "macos"
    dist_dir_windows = project_root / "dist" / "windows"
    dist_dir_macos.mkdir(parents=True, exist_ok=True)
    dist_dir_windows.mkdir(parents=True, exist_ok=True)

    # Compiler pour macOS et Windows
    print(
        "[INFO] Mode de compilation local sur macOS: génération des exécutables macOS et Windows"
    )

    print("\n=== Compilation macOS ===")
    macos_success = build_native_macos(
        project_root, entrypoint, exe_name, dist_dir_macos
    )

    print("\n=== Compilation Windows (cross-compilation) ===")
    windows_success = build_windows_on_macos(
        project_root, entrypoint, exe_name, icon_path, dist_dir_windows
    )

    # Afficher un résumé
    print("\n[RÉSUMÉ] Résultat de la compilation:")
    print(f"  - macOS: {'RÉUSSI' if macos_success else 'ÉCHOUÉ'}")
    print(f"  - Windows: {'RÉUSSI' if windows_success else 'ÉCHOUÉ'}")

    if macos_success and windows_success:
        print(f"\n[INFO] Exécutables disponibles dans:")
        print(f"  - macOS: {dist_dir_macos / exe_name}")
        print(f"  - Windows: {dist_dir_windows / (exe_name + '.exe')}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
