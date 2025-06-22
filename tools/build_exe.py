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
    dist_dir = Path(os.path.join(project_root, "dist", "windows"))
    dist_dir.mkdir(parents=True, exist_ok=True)

    if platform.system() == "Darwin":
        print("🛠 Compilation directe d'un .exe Windows depuis macOS...")
        print(f"🛠 Compilation de l'exécutable à partir de: {entrypoint}")
        print(f"🛠 Utilisation de l'icône: {icon_path}")

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

        print(f"✅ Fichier spec créé: {spec_file}")

        # Utiliser le fichier spec
        cmd = [
            "pyinstaller",
            "--clean",
            str(spec_file),
        ]

        try:
            print(
                "🛠 Exécution de PyInstaller (compilation croisée macOS -> Windows)..."
            )
            subprocess.run(cmd, check=True)

            # Déplacer l'exécutable vers le répertoire final
            built_exe = Path("dist") / f"{exe_name}.exe"
            if built_exe.exists():
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_exe.rename(final_path)
                print(f"✅ .exe généré avec succès : {final_path}")
                return

            # Deuxième tentative - chercher dans le répertoire dist sans extension .exe
            built_file = Path("dist") / exe_name
            if built_file.exists():
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_file.rename(final_path)
                print(f"✅ .exe généré avec succès : {final_path}")
            else:
                print("❌ Le fichier executable n'a pas été trouvé après compilation.")
                print("📁 Contenu du répertoire dist:")
                for file in Path("dist").glob("*"):
                    print(f"  - {file}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de la compilation avec PyInstaller : {e}")
            sys.exit(1)
    else:
        # Compilation native Windows
        print("🛠 Compilation Windows native avec PyInstaller...")

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
                final_path = dist_dir / f"{exe_name}.exe"
                if final_path.exists():
                    final_path.unlink()
                built_exe.rename(final_path)
                print(f"✅ .exe généré : {final_path}")
            else:
                print("❌ Aucun .exe trouvé après build.")
        except subprocess.CalledProcessError as e:
            print("❌ Erreur PyInstaller :", e)
            sys.exit(1)


if __name__ == "__main__":
    main()
