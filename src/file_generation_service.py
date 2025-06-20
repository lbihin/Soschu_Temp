"""
File Generation Service - Indépendant du traitement principal.

Ce module fournit des services de génération de fichiers qui utilisent les résultats
du CoreProcessor pour générer des fichiers de sortie dans différents formats.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from core import PreviewResult, ProcessingResult
from output_generator import OutputGenerator, create_try_generator


class FileGenerationService:
    """Service indépendant pour la génération de fichiers."""

    def __init__(self, output_generator: Optional[OutputGenerator] = None):
        """
        Initialize the file generation service.

        Args:
            output_generator: Output generator to use. If None, defaults to TRY format.
        """
        self.output_generator = output_generator or create_try_generator()
        self.logger = logging.getLogger(__name__)

    def set_output_generator(self, output_generator: OutputGenerator) -> None:
        """
        Change the output generator.

        Args:
            output_generator: New output generator to use
        """
        self.output_generator = output_generator

    def generate_files_from_processing_result(
        self,
        processing_result: ProcessingResult,
        output_dir: str = "output",
        selected_facades: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Génère les fichiers de sortie à partir d'un résultat de traitement.

        Args:
            processing_result: Résultat du traitement contenant les données ajustées
            output_dir: Répertoire de sortie
            selected_facades: Liste des façades sélectionnées à générer. Si None, génère toutes les façades.

        Returns:
            Dictionnaire mappant les identifiants de façade aux chemins des fichiers de sortie
        """
        self.logger.info("Generating files from processing result...")

        # Créer le répertoire de sortie
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Extraire le nom de base du fichier météo
        weather_file_base = Path(processing_result.parameters["weather_file"]).stem

        # Générer les fichiers pour les façades sélectionnées ou toutes les façades
        output_files = {}
        facades_to_generate = selected_facades or list(
            processing_result.adjusted_weather_data_by_facade.keys()
        )

        for facade_key in facades_to_generate:
            if facade_key not in processing_result.adjusted_weather_data_by_facade:
                self.logger.warning(
                    f"Facade {facade_key} not found in processing result"
                )
                continue

            self.logger.info(f"Generating file for {facade_key}")

            # Récupérer les données ajustées pour cette façade
            adjusted_weather_data = processing_result.adjusted_weather_data_by_facade[
                facade_key
            ]

            # Générer le nom de fichier de sortie
            safe_facade_key = facade_key.replace(" ", "_").replace("$", "_")
            output_filename = f"{weather_file_base}_{safe_facade_key}.dat"
            output_file_path = output_path / output_filename

            # Générer le fichier en utilisant l'OutputGenerator
            self.output_generator.generate_file(
                output_file_path,
                processing_result.weather_metadata,
                adjusted_weather_data,
            )

            output_files[facade_key] = str(output_file_path)
            self.logger.info(f"Saved adjusted weather data to: {output_file_path}")

        self.logger.info(
            f"File generation complete. Generated {len(output_files)} files."
        )
        return output_files

    def generate_files_from_preview_result(
        self,
        preview_result: PreviewResult,
        output_dir: str = "output",
        selected_facades: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Génère les fichiers de sortie à partir d'un résultat de prévisualisation.

        Args:
            preview_result: Résultat de la prévisualisation contenant les données ajustées
            output_dir: Répertoire de sortie
            selected_facades: Liste des façades sélectionnées à générer. Si None, génère toutes les façades.

        Returns:
            Dictionnaire mappant les identifiants de façade aux chemins des fichiers de sortie
        """
        return self.generate_files_from_processing_result(
            preview_result.processing_result, output_dir, selected_facades
        )

    def generate_single_facade_file(
        self,
        processing_result: ProcessingResult,
        facade_key: str,
        output_file_path: str,
    ) -> str:
        """
        Génère un fichier pour une seule façade.

        Args:
            processing_result: Résultat du traitement
            facade_key: Clé de la façade à générer
            output_file_path: Chemin du fichier de sortie

        Returns:
            Chemin du fichier généré

        Raises:
            ValueError: Si la façade n'existe pas dans les résultats
        """
        if facade_key not in processing_result.adjusted_weather_data_by_facade:
            raise ValueError(f"Facade {facade_key} not found in processing result")

        self.logger.info(f"Generating single file for facade {facade_key}")

        # Récupérer les données ajustées pour cette façade
        adjusted_weather_data = processing_result.adjusted_weather_data_by_facade[
            facade_key
        ]

        # Créer le répertoire de sortie si nécessaire
        output_path = Path(output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Générer le fichier
        self.output_generator.generate_file(
            output_path, processing_result.weather_metadata, adjusted_weather_data
        )

        self.logger.info(f"Generated file for facade {facade_key}: {output_path}")
        return str(output_path)

    def get_supported_formats(self) -> List[str]:
        """
        Obtient la liste des formats de sortie supportés.

        Returns:
            Liste des extensions de fichier supportées
        """
        # For now, we support only the current strategy's format
        # This could be extended to support multiple formats
        return [self.output_generator.strategy.get_file_extension()]

    def validate_output_directory(self, output_dir: str) -> bool:
        """
        Valide si le répertoire de sortie peut être utilisé.

        Args:
            output_dir: Répertoire de sortie à valider

        Returns:
            True si le répertoire est valide, False sinon
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            return output_path.exists() and output_path.is_dir()
        except Exception as e:
            self.logger.error(f"Failed to validate output directory {output_dir}: {e}")
            return False


# Factory function for easy instantiation
def create_file_generation_service(
    output_generator: Optional[OutputGenerator] = None,
) -> FileGenerationService:
    """
    Create a file generation service instance.

    Args:
        output_generator: Optional output generator. If None, defaults to TRY format.

    Returns:
        FileGenerationService instance
    """
    return FileGenerationService(output_generator)
