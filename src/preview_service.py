"""
Preview Service - Indépendant du traitement principal.

Ce module fournit des services de prévisualisation qui utilisent les résultats
du CoreProcessor pour générer des previews pour l'interface utilisateur.
"""

import logging
from typing import List

from core import PreviewAdjustment, PreviewResult, ProcessingResult
from output_generator import OutputGenerator
from solar import load_solar_irridance_data
from weather import load_weather_data


class PreviewService:
    """Service indépendant pour la génération de previews."""

    def __init__(self):
        """Initialize the preview service."""
        self.logger = logging.getLogger(__name__)

    def create_preview_from_processing_result(
        self,
        processing_result: ProcessingResult,
        max_sample_adjustments: int = 20,
    ) -> PreviewResult:
        """
        Crée un résultat de prévisualisation à partir d'un résultat de traitement.

        Args:
            processing_result: Résultat du traitement des données
            max_sample_adjustments: Nombre max d'ajustements d'exemple à inclure

        Returns:
            PreviewResult contenant les échantillons pour l'affichage GUI
        """
        self.logger.info("Creating preview from processing result...")

        # Créer des échantillons d'ajustements stratifiés
        sample_adjustments = self._create_stratified_samples(
            processing_result, max_sample_adjustments
        )

        preview_result = PreviewResult(
            processing_result=processing_result,
            sample_adjustments=sample_adjustments,
            max_sample_adjustments=max_sample_adjustments,
        )

        self.logger.info(
            f"Preview created with {len(sample_adjustments)} sample adjustments"
        )
        return preview_result

    def _create_stratified_samples(
        self, processing_result: ProcessingResult, max_samples: int
    ) -> List[PreviewAdjustment]:
        """
        Crée des échantillons stratifiés d'ajustements pour la prévisualisation.

        Args:
            processing_result: Résultat du traitement
            max_samples: Nombre maximum d'échantillons

        Returns:
            Liste d'ajustements d'exemple stratifiés
        """
        sample_adjustments = []
        facade_samples = {}  # Pour stratifier les échantillons par façade

        # Charger les données originales pour créer les échantillons détaillés
        solar_metadata, solar_data = load_solar_irridance_data(
            processing_result.parameters["solar_file"]
        )
        weather_metadata, weather_data = load_weather_data(
            processing_result.parameters["weather_file"]
        )

        # Import FacadeProcessor here to avoid circular imports
        from core import FacadeProcessor

        facade_processor = FacadeProcessor(
            processing_result.parameters["threshold"],
            processing_result.parameters["delta_t"],
        )

        for facade_key in processing_result.adjusted_weather_data_by_facade.keys():
            facade_id, building_body = facade_key.split("_", 1)

            # Initialize stratified sampling
            facade_samples[facade_key] = {
                "summer": [],  # Mars-Septembre (heure d'été potentielle)
                "winter": [],  # Octobre-Février (heure d'hiver)
            }

            # Find the specific facade column
            facade_column = facade_processor._find_facade_column(
                solar_metadata, facade_id, building_body
            )
            if not facade_column:
                continue

            # Create solar lookup
            solar_lookup = facade_processor._create_solar_lookup(
                solar_data, facade_column
            )

            # Sample from the original weather data to show adjustments
            for weather_point in weather_data[:1000]:  # Sample from first 1000 points
                solar_irradiance = facade_processor._get_solar_irradiance_for_datetime(
                    solar_lookup, weather_point
                )

                if (
                    solar_irradiance is not None
                    and solar_irradiance > processing_result.parameters["threshold"]
                ):
                    # Determine season for stratified sampling
                    season = "summer" if 3 <= weather_point.month <= 9 else "winter"

                    # Add to stratified sample if not full for this facade/season
                    if (
                        len(facade_samples[facade_key][season]) < 3
                    ):  # Max 3 per season per facade
                        weather_time_str = f"{weather_point.month:02d}-{weather_point.day:02d} {weather_point.hour:02d}:00"
                        adjustment = PreviewAdjustment(
                            datetime_str=weather_time_str,
                            facade_id=facade_id,
                            building_body=building_body,
                            original_temp=weather_point.temperature,
                            adjusted_temp=weather_point.adjusted_temperature
                            + processing_result.parameters["delta_t"],
                            solar_irradiance=solar_irradiance,
                            threshold=processing_result.parameters["threshold"],
                            weather_datetime=weather_time_str,
                            solar_datetime=weather_time_str,
                        )
                        facade_samples[facade_key][season].append(adjustment)

        # Build final stratified sample list
        for facade_key, seasons in facade_samples.items():
            for season, adjustments in seasons.items():
                sample_adjustments.extend(adjustments)
                if len(sample_adjustments) >= max_samples:
                    break
            if len(sample_adjustments) >= max_samples:
                break

        return sample_adjustments[:max_samples]

    def get_processing_statistics(self, processing_result: ProcessingResult) -> dict:
        """
        Obtient des statistiques détaillées du traitement.

        Args:
            processing_result: Résultat du traitement

        Returns:
            Dictionnaire avec les statistiques détaillées
        """
        return {
            "total_facades": len(processing_result.facade_combinations),
            "total_adjustments": processing_result.total_adjustments,
            "adjustments_by_facade": processing_result.adjustments_by_facade,
            "weather_data_points": processing_result.parameters["weather_data_points"],
            "solar_data_points": processing_result.parameters["solar_data_points"],
            "threshold": processing_result.parameters["threshold"],
            "delta_t": processing_result.parameters["delta_t"],
            "facade_combinations": processing_result.facade_combinations,
        }


# Factory function for easy instantiation
def create_preview_service() -> PreviewService:
    """Create a preview service instance."""
    return PreviewService()
