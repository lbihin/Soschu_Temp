#!/usr/bin/env python3
"""
Script pour compiler directement un exécutable Windows (.exe) avec PyInstaller.
Cette version contourne l'installation de Python sous Wine en utilisant
le mode cross-compilation de PyInstaller.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def main():
    # Obtenir le chemin absolu du répertoire actuel du projet
    project_root = Path(__file__).parent.parent.absolute()
    entrypoint = os.path.join(project_root, "src", "main.py")
    exe_name = "soschu_temp"
    icon_path = os.path.join(project_root, "tools", "assets", "icon.ico")
    
    # Sur GitHub Actions, les artefacts sont recherchés directement dans dist/
    # Sinon, pour un usage local, nous utilisons dist/windows ou dist/macos
    if os.environ.get("GITHUB_ACTIONS") == "true":
        dist_dir = Path(os.path.join(project_root, "dist"))
    else:
        # Pour usage local
        is_windows = platform.system() == "Windows"
        platform_folder = "windows" if is_windows else "macos"
        dist_dir = Path(os.path.join(project_root, "dist", platform_folder))
        dist_dir.mkdir(parents=True, exist_ok=True)
    
    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"
    
    # Build natif pour l'OS actuel
    if is_macos:
        print("[INFO] Compilation native pour macOS...")
        
        # Pour macOS, on génère un exécutable macOS
        cmd_macos = [
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
            subprocess.run(cmd_macos, check=True)
            
            # Vérifier si l'exécutable a été généré
            built_macos = Path("dist") / exe_name
            if built_macos.exists():
                # Pour GitHub Actions, on laisse l'exécutable en place
                if os.environ.get("GITHUB_ACTIONS") != "true":
                    # Pour usage local, on le déplace dans le sous-dossier macos
                    final_path = dist_dir / exe_name
                    if final_path.exists():
                        final_path.unlink()
                    built_macos.rename(final_path)
                    print(f"[SUCCES] Exécutable macOS généré : {final_path}")
                else:
                    print(f"[SUCCES] Exécutable macOS généré : {built_macos}")
                return
            else:
                print("[ERREUR] Aucun exécutable macOS trouvé après build.")
                print("Contenu du répertoire dist:")
                for file in Path("dist").glob("*"):
                    print(f"  - {file}")
        except subprocess.CalledProcessError as e:
            print(f"[ERREUR] Erreur lors de la compilation macOS : {e}")
            sys.exit(1)
        print(f"[INFO] Compilation de l'exécutable à partir de: {entrypoint}")
        print(f"[INFO] Utilisation de l'icône: {icon_path}")

        # Méthode directe de cross-compilation
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

        # Écrire le fichier spec
        spec_file = project_root / f"{exe_name}.spec"
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
                if os.environ.get("GITHUB_ACTIONS") != "true":
                    # Pour usage local, on le déplace dans le sous-dossier
                    final_path = dist_dir / f"{exe_name}.exe"
                    if final_path.exists():
                        final_path.unlink()
                    built_exe.rename(final_path)
                    print(f"[SUCCES] .exe généré avec succès : {final_path}")
                else:
                    print(f"[SUCCES] .exe généré avec succès : {built_exe}")
                return

            # Deuxième tentative - chercher dans le répertoire dist sans extension .exe
            built_file = Path("dist") / exe_name
            if built_file.exists():
                # Pour GitHub Actions, on laisse l'exécutable en place
                if os.environ.get("GITHUB_ACTIONS") != "true":
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
            else:
                print(
                    "[ERREUR] Le fichier executable n'a pas été trouvé après compilation."
                )
                print("[INFO] Contenu du répertoire dist:")
                for file in Path("dist").glob("*"):
                    print(f"  - {file}")
        except subprocess.CalledProcessError as e:
            print(f"[ERREUR] Erreur lors de la compilation avec PyInstaller : {e}")
            sys.exit(1)
    else:
        # Compilation native Windows
        print("[INFO] Compilation Windows native avec PyInstaller...")

        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--icon",
            str(icon_path),
            "--name",
            exe_name,
            "--add-data",
            f"{project_root}/src:src",
            str(entrypoint),
        ]

        try:
            subprocess.run(cmd, check=True)

            built_exe = Path("dist") / f"{exe_name}.exe"
            if built_exe.exists():
                # Pour GitHub Actions, on laisse l'exécutable en place
                if os.environ.get("GITHUB_ACTIONS") != "true":
                    # Pour usage local, on le déplace dans le sous-dossier windows
                    final_path = dist_dir / f"{exe_name}.exe"
                    if final_path.exists():
                        final_path.unlink()
                    built_exe.rename(final_path)
                    print(f"[SUCCES] .exe généré : {final_path}")
                else:
                    print(f"[SUCCES] .exe généré : {built_exe}")
            else:
                print("[ERREUR] Aucun .exe trouvé après build.")
        except subprocess.CalledProcessError as e:
            print("[ERREUR] Erreur PyInstaller :", e)
            sys.exit(1)


if __name__ == "__main__":
    main()
