"""
Exemple d'utilisation du PreviewService modulaire.

Ce script montre comment utiliser la nouvelle architecture du PreviewService
avec des classes indépendantes pour différents types de données de preview.
"""

import sys
from pathlib import Path
import tkinter as tk
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gui.components.preview_window import show_preview_window
from core import CoreProcessor
from preview import PreviewService

# Ajouter le répertoire src au path pour les imports
if __name__ == "__main__":


    # Exemple d'utilisation dans un script standalone
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale

    # Simuler un résultat de prévisualisation
    root_dir = Path(__file__).parent.parent
    # Chemins vers les fichiers de test
    weather_file = (
        root_dir / "tests" / "data" / "TRY2045_488284093163_Jahr.dat"
    )
    solar_file = (
        root_dir/ "tests" / "data" / "Solare Einstrahlung auf die Fassade.html"
    )

    if not weather_file.exists() or not solar_file.exists():
        print(
            "Fichiers de test non trouvés. Exécutez d'abord les tests pour générer les données."
        )
        sys.exit(1) 

    # 1. Traitement des données avec CoreProcessor
    processor = CoreProcessor()
    processing_result = processor.process_all_facades(
        weather_file_path=str(weather_file),
        solar_file_path=str(solar_file),
        threshold=200.0,
        delta_t=2.0,)
    result = PreviewService.from_processing_result(processing_result)
    show_preview_window(root, result)
    root.mainloop()