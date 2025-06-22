#!/usr/bin/env python3
"""
Script pour compiler des exécutables avec PyInstaller.
Sur macOS, peut générer à la fois des exécutables macOS et Windows.
Sur Windows, génère uniquement un exécutable Windows.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def build_native_macos(
    project_root, entrypoint, exe_name, dist_dir, is_github_actions=False
):
    """Génère un exécutable macOS natif.

    Args:
        project_root (Path): Chemin racine du projet
        entrypoint (Path): Chemin vers le fichier principal
        exe_name (str): Nom de l'exécutable
        dist_dir (Path): Répertoire de destination
        is_github_actions (bool): Si True, les exécutables restent dans dist/

    Returns:
        bool: True si le build a réussi, False sinon
    """
    print("[INFO] Compilation native pour macOS...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        exe_name,
        "--add-data",
        f"{project_root}/src:src",
        str(entrypoint),
    ]

    try:
        subprocess.run(cmd, check=True)

        # Vérifier si l'exécutable a été généré
        built_macos = Path("dist") / exe_name
        if built_macos.exists():
            # Pour GitHub Actions, on laisse l'exécutable en place
            if not is_github_actions:
                # Pour usage local, on le déplace dans le sous-dossier macos
                final_path = dist_dir / exe_name
                if final_path.exists():
                    final_path.unlink()
                built_macos.rename(final_path)
                print(f"[SUCCES] Exécutable macOS généré : {final_path}")
            else:
                print(f"[SUCCES] Exécutable macOS généré : {built_macos}")
            return True
        else:
            print("[ERREUR] Aucun exécutable macOS trouvé après build.")
            print("Contenu du répertoire dist:")
            for file in Path("dist").glob("*"):
                print(f"  - {file}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de la compilation macOS : {e}")
        return False


def build_native_windows(
    project_root, entrypoint, exe_name, icon_path, dist_dir, is_github_actions=False
):
    """Génère un exécutable Windows natif, à utiliser sur Windows.

    Args:
        project_root (Path): Chemin racine du projet
        entrypoint (Path): Chemin vers le fichier principal
        exe_name (str): Nom de l'exécutable
        icon_path (Path): Chemin vers l'icône
        dist_dir (Path): Répertoire de destination
        is_github_actions (bool): Si True, les exécutables restent dans dist/

    Returns:
        bool: True si le build a réussi, False sinon
    """
    print("[INFO] Compilation Windows native avec PyInstaller...")

    # Ajuster le séparateur pour Windows
    add_data_param = (
        f"{project_root}\\src;src"
        if platform.system() == "Windows"
        else f"{project_root}/src:src"
    )

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--icon",
        str(icon_path),
        "--name",
        exe_name,
        "--add-data",
        add_data_param,
        str(entrypoint),
    ]

    try:
        subprocess.run(cmd, check=True)

        built_exe = Path("dist") / f"{exe_name}.exe"
        if built_exe.exists():
            # Pour GitHub Actions, on laisse l'exécutable en place
            if not is_github_actions:
                # Pour usage local, on le déplace dans le sous-dossier
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_exe.rename(final_path)
                print(f"[SUCCES] .exe généré : {final_path}")
            else:
                print(f"[SUCCES] .exe généré : {built_exe}")
            return True
        else:
            print("[ERREUR] Aucun .exe trouvé après build.")
            print("Contenu du répertoire dist:")
            for file in Path("dist").glob("*"):
                print(f"  - {file}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur PyInstaller : {e}")
        return False


def build_windows_on_macos(
    project_root, entrypoint, exe_name, icon_path, dist_dir, is_github_actions=False
):
    """Cross-compilation d'un exécutable Windows depuis macOS.

    Args:
        project_root (Path): Chemin racine du projet
        entrypoint (Path): Chemin vers le fichier principal
        exe_name (str): Nom de l'exécutable
        icon_path (Path): Chemin vers l'icône
        dist_dir (Path): Répertoire de destination
        is_github_actions (bool): Si True, les exécutables restent dans dist/

    Returns:
        bool: True si le build a réussi, False sinon
    """
    print("[INFO] Cross-compilation Windows depuis macOS...")
    print(f"[INFO] Compilation de l'exécutable à partir de: {entrypoint}")
    print(f"[INFO] Utilisation de l'icône: {icon_path}")

    # Créer un fichier .spec pour cibler Windows
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['{entrypoint.replace(os.sep, "/")}'],
             pathex=['{project_root.as_posix()}'],
             binaries=[],
             datas=[
                ('{project_root.as_posix()}/src', 'src')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='{exe_name}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='{icon_path.replace(os.sep, "/")}')
"""

    # Écriture du fichier .spec
    spec_file = Path(project_root) / f"{exe_name}_windows.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)

    print(f"[SUCCES] Fichier spec créé: {spec_file}")

    # Utiliser le fichier spec
    cmd = [
        "pyinstaller",
        "--clean",
        str(spec_file),
    ]

    try:
        print(
            "[INFO] Exécution de PyInstaller (compilation croisée macOS -> Windows)..."
        )
        subprocess.run(cmd, check=True)

        # Déplacer l'exécutable vers le répertoire final
        built_exe = Path("dist") / f"{exe_name}.exe"
        if built_exe.exists():
            # Pour GitHub Actions, on laisse l'exécutable en place
            if not is_github_actions:
                # Pour usage local, on le déplace dans le sous-dossier
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_exe.rename(final_path)
                print(f"[SUCCES] .exe généré avec succès : {final_path}")
            else:
                print(f"[SUCCES] .exe généré avec succès : {built_exe}")
            return True

        # Deuxième tentative - chercher dans le répertoire dist sans extension .exe
        built_file = Path("dist") / exe_name
        if built_file.exists():
            # Pour GitHub Actions, on laisse l'exécutable en place
            if not is_github_actions:
                # Pour usage local, on le déplace dans le sous-dossier
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_file.rename(final_path)
                print(f"[SUCCES] .exe généré avec succès : {final_path}")
            else:
                # Renommer pour avoir l'extension .exe
                final_path = Path("dist") / f"{exe_name}.exe"
                built_file.rename(final_path)
                print(f"[SUCCES] .exe généré avec succès : {final_path}")
            return True
        else:
            print(
                "[ERREUR] Le fichier executable n'a pas été trouvé après compilation."
            )
            print("Contenu du répertoire dist:")
            for file in Path("dist").glob("*"):
                print(f"  - {file}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de la compilation avec PyInstaller : {e}")
        return False


def main():
    """Fonction principale du script."""
    # Obtenir le chemin absolu du répertoire actuel du projet
    project_root = Path(__file__).parent.parent.absolute()
    entrypoint = project_root / "src" / "main.py"
    exe_name = "soschu_temp"
    icon_path = project_root / "tools" / "assets" / "icon.ico"

    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    # Sur GitHub Actions, les artefacts sont recherchés directement dans dist/
    # Sinon, pour un usage local, nous créons les dossiers dist/windows et dist/macos
    if is_github_actions:
        dist_dir_windows = Path(project_root / "dist")
        dist_dir_macos = Path(project_root / "dist")
    else:
        # Pour usage local, on crée toujours les deux dossiers
        dist_dir_windows = Path(project_root / "dist" / "windows")
        dist_dir_macos = Path(project_root / "dist" / "macos")
        dist_dir_windows.mkdir(parents=True, exist_ok=True)
        dist_dir_macos.mkdir(parents=True, exist_ok=True)

    # En local sur macOS, on compile toujours pour macOS et Windows
    # Sur GitHub Actions ou sur Windows, on compile uniquement pour la plateforme actuelle
    if is_macos and not is_github_actions:
        # Sur macOS local, compiler à la fois macOS et Windows
        print(
            "[INFO] Mode de compilation local sur macOS: génération des exécutables macOS et Windows"
        )
        macos_success = build_native_macos(
            project_root, entrypoint, exe_name, dist_dir_macos, is_github_actions
        )
        windows_success = build_windows_on_macos(
            project_root,
            entrypoint,
            exe_name,
            icon_path,
            dist_dir_windows,
            is_github_actions,
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
    elif is_macos and is_github_actions:
        # Sur GitHub Actions avec macOS, compiler uniquement pour macOS
        success = build_native_macos(
            project_root, entrypoint, exe_name, dist_dir_macos, is_github_actions
        )
        return 0 if success else 1
    elif is_windows:
        # Sur Windows (local ou GitHub Actions), compiler uniquement pour Windows
        success = build_native_windows(
            project_root,
            entrypoint,
            exe_name,
            icon_path,
            dist_dir_windows,
            is_github_actions,
        )
        return 0 if success else 1
    else:
        print(
            f"[ERREUR] Système d'exploitation non pris en charge: {platform.system()}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
