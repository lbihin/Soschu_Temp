import sys
from pathlib import Path


def demo(save_output: bool = False) -> None:
    """
    Exemple de traitement des données de façade avec CoreProcessor.
    Ce script montre comment utiliser CoreProcessor pour traiter les données
    de façade et générer un résultat de prévisualisation.
    """

    # Simuler un résultat de prévisualisation
    root_dir = Path(__file__).parent.parent
    # Chemins vers les fichiers de test
    weather_file = root_dir / "tests" / "data" / "TRY2045_488284093163_Jahr.dat"
    solar_file = (
        root_dir / "tests" / "data" / "Solare Einstrahlung auf die Fassade.html"
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
        delta_t=2.0,
    )

    if save_output:
        # Save outputs objects (pkl)
        output_dir = root_dir / "exemple" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "processing_result.pkl", "wb") as f:
            import pickle

            pickle.dump(processing_result, f)
        print(f"Processing result saved to {output_dir / 'processing_result.pkl'}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from core import CoreProcessor

    # Exécuter la démo
    demo(save_output=True)
