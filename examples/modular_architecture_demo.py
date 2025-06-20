"""
Démonstration de l'architecture modulaire refactorisée.

Ce script montre comment utiliser les services indépendants pour le traitement,
la prévisualisation et la génération de fichiers.
"""

import logging
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core import CoreProcessor
from file_generation_service import create_file_generation_service
from output_generator import create_try_generator
from preview import create_preview_service


def demo_modular_workflow():
    """Démontre le workflow modulaire avec séparation des responsabilités."""

    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("=== Démonstration de l'Architecture Modulaire ===")

    # Paramètres de test
    weather_file = "tests/data/TRY2045_488284093163_Jahr.dat"
    solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
    threshold = 200.0  # W/m²
    delta_t = 7.0  # °C
    output_dir = "test_output"

    # Vérifier que les fichiers existent
    if not Path(weather_file).exists():
        logger.error(f"Weather file not found: {weather_file}")
        return

    if not Path(solar_file).exists():
        logger.error(f"Solar file not found: {solar_file}")
        return

    try:
        # ÉTAPE 1: Traitement des données uniquement (pas de génération de fichiers)
        logger.info("Étape 1: Traitement des données avec CoreProcessor")
        processor = CoreProcessor()
        processing_result = processor.process_all_facades(
            weather_file, solar_file, threshold, delta_t
        )

        logger.info(
            f"Traitement terminé: {processing_result.total_adjustments} ajustements totaux"
        )
        logger.info(
            f"Façades traitées: {list(processing_result.adjustments_by_facade.keys())}"
        )

        # ÉTAPE 2: Génération de preview pour l'interface utilisateur
        logger.info("Étape 2: Génération de preview avec PreviewService")
        preview_service = create_preview_service()
        preview_result = preview_service.create_preview_from_processing_result(
            processing_result, max_sample_adjustments=15
        )

        logger.info(
            f"Preview créé avec {len(preview_result.sample_adjustments)} échantillons"
        )

        # Afficher quelques statistiques de preview
        stats = preview_service.get_processing_statistics(processing_result)
        logger.info(
            f"Statistiques: {stats['total_facades']} façades, {stats['total_adjustments']} ajustements"
        )

        # ÉTAPE 3: Génération de fichiers avec FileGenerationService
        logger.info("Étape 3: Génération de fichiers avec FileGenerationService")

        # Option 3a: Génération directe depuis ProcessingResult
        file_service = create_file_generation_service()
        output_files_1 = file_service.generate_files_from_processing_result(
            processing_result,
            output_dir=f"{output_dir}/direct",
            selected_facades=None,  # Toutes les façades
        )

        logger.info(f"Fichiers générés directement: {len(output_files_1)}")

        # Option 3b: Génération depuis PreviewResult
        output_files_2 = file_service.generate_files_from_preview_result(
            preview_result,
            output_dir=f"{output_dir}/from_preview",
            selected_facades=list(processing_result.adjustments_by_facade.keys())[
                :2
            ],  # Seulement 2 façades
        )

        logger.info(f"Fichiers générés depuis preview: {len(output_files_2)}")

        # ÉTAPE 4: Démonstration de la flexibilité avec différents générateurs
        logger.info("Étape 4: Utilisation de différents générateurs de sortie")

        # Utilisation d'un générateur spécifique
        try_generator = create_try_generator()
        custom_file_service = create_file_generation_service(try_generator)

        # Génération d'un fichier spécifique
        if processing_result.adjusted_weather_data_by_facade:
            # Utiliser la première façade qui existe vraiment
            facade_key = list(processing_result.adjusted_weather_data_by_facade.keys())[
                0
            ]
            single_file = custom_file_service.generate_single_facade_file(
                processing_result,
                facade_key,
                f"{output_dir}/single/{facade_key}_custom.dat",
            )
            logger.info(f"Fichier spécifique généré: {single_file}")
        else:
            logger.warning("Aucune façade trouvée dans les résultats de traitement")

        # ÉTAPE 5: Validation et vérification
        logger.info("Étape 5: Validation des résultats")

        # Vérifier que les répertoires ont été créés
        if file_service.validate_output_directory(output_dir):
            logger.info("Répertoire de sortie validé avec succès")

        # Afficher les formats supportés
        supported_formats = file_service.get_supported_formats()
        logger.info(f"Formats supportés: {supported_formats}")

        # Résumé final
        logger.info("=== Résumé de la Démonstration ===")
        logger.info(
            f"✅ Données traitées: {processing_result.total_adjustments} ajustements"
        )
        logger.info(
            f"✅ Preview générée: {len(preview_result.sample_adjustments)} échantillons"
        )
        logger.info(
            f"✅ Fichiers générés: {len(output_files_1) + len(output_files_2) + 1}"
        )
        logger.info("✅ Architecture modulaire validée!")

        return {
            "processing_result": processing_result,
            "preview_result": preview_result,
            "output_files": {**output_files_1, **output_files_2},
        }

    except Exception as e:
        logger.error(f"Erreur pendant la démonstration: {e}")
        raise


def demo_gui_integration_pattern():
    """Démontre le pattern d'intégration GUI recommandé."""

    logger = logging.getLogger(__name__)
    logger.info("=== Pattern d'Intégration GUI ===")

    # Pattern typique pour une interface utilisateur
    weather_file = "tests/data/TRY2045_488284093163_Jahr.dat"
    solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
    threshold = 150.0
    delta_t = 5.0

    try:
        # 1. L'utilisateur clique sur "Analyser" - on fait le traitement
        logger.info("1. Traitement initial (clic sur Analyser)")
        processor = CoreProcessor()
        processing_result = processor.process_all_facades(
            weather_file, solar_file, threshold, delta_t
        )

        # 2. L'utilisateur veut voir un aperçu - on génère la preview
        logger.info("2. Génération preview (clic sur Aperçu)")
        preview_service = create_preview_service()
        preview_result = preview_service.create_preview_from_processing_result(
            processing_result
        )

        # 3. L'interface affiche les statistiques et échantillons
        logger.info("3. Affichage des données dans l'interface")
        stats = preview_service.get_processing_statistics(processing_result)

        # Simulation de l'affichage GUI
        print(f"   📊 Façades trouvées: {stats['total_facades']}")
        print(f"   📊 Ajustements totaux: {stats['total_adjustments']}")
        print(f"   📊 Exemples d'ajustements:")
        for i, adj in enumerate(preview_result.sample_adjustments[:3]):
            print(
                f"      {i+1}. {adj.datetime_str}: {adj.original_temp:.1f}°C → {adj.adjusted_temp:.1f}°C ({adj.facade_id})"
            )

        # 4. L'utilisateur sélectionne des façades et clique sur "Générer"
        logger.info("4. Génération de fichiers (clic sur Générer)")
        file_service = create_file_generation_service()

        # Simulation de sélection utilisateur (premières 2 façades)
        selected_facades = list(processing_result.adjustments_by_facade.keys())[:2]
        output_files = file_service.generate_files_from_processing_result(
            processing_result,
            output_dir="gui_output",
            selected_facades=selected_facades,
        )

        logger.info(f"✅ Pattern GUI démontré - {len(output_files)} fichiers générés")

    except Exception as e:
        logger.error(f"Erreur dans le pattern GUI: {e}")
        raise


if __name__ == "__main__":
    print("🚀 Démonstration de l'Architecture Modulaire Soschu")
    print("=" * 60)

    # Démonstration principale
    demo_results = demo_modular_workflow()

    print("\n" + "=" * 60)

    # Démonstration du pattern GUI
    demo_gui_integration_pattern()

    print("\n🎉 Démonstration terminée avec succès!")
    print("\nLes services sont maintenant complètement modulaires:")
    print("  • CoreProcessor: traitement de données uniquement")
    print("  • PreviewService: génération d'aperçus pour GUI")
    print("  • FileGenerationService: génération de fichiers de sortie")
    print("  • OutputGenerator: stratégies de format de sortie")
