"""
Preview Service - Indépendant du traitement principal.

Ce module fournit des services de prévisualisation qui utilisent les résultats
du CoreProcessor pour générer des previews pour l'interface utilisateur.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field

from core import PreviewAdjustment, ProcessingResult


class PreviewSummaryData(BaseModel):
    """Données de résumé pour la fenêtre de preview."""

    count_facades: int = Field(..., description="Nombre total de façades")
    count_adjustments: int = Field(..., description="Nombre total d'ajustements")
    count_weather_data_points: int = Field(
        ..., description="Nombre total de points de données météo"
    )
    count_solar_data_points: int = Field(
        ..., description="Nombre total de points de données solaires"
    )
    threshold: int = Field(..., description="Seuil d'irradiance pour les ajustements")
    delta_t: int = Field(..., description="Delta T pour les ajustements de température")
    table: Dict[str, tuple[int, float]] = Field(
        default_factory=dict, description="Tableau de résumé des façades"
    )
    weather_filename: str = Field(
        ..., description="Nom du fichier météo utilisé pour le traitement"
    )
    solar_filename: str = Field(
        ..., description="Nom du fichier solaire utilisé pour le traitement"
    )

    @classmethod
    def from_processing_result(
        cls, processing_result: ProcessingResult
    ) -> "PreviewSummaryData":
        """
        Crée un PreviewSummaryData à partir d'un ProcessingResult.

        Args:
            processing_result: Résultat du traitement des données

        Returns:
            Instance de PreviewSummaryData
        """
        table = {
            facade.get_full_name(): (facade.adjustments_count, facade.get_percentage_adjusted())
            for facade in processing_result.data.values()
        }

        weather_filename = processing_result.weather_file
        solar_filename = processing_result.solar_file
        
        return cls(
            count_facades=processing_result.count_facades(),
            count_adjustments=processing_result.count_adjustments(),
            count_weather_data_points=processing_result.count_overall_weather_data_points(),
            count_solar_data_points=processing_result.count_solar_data_points(),
            threshold=processing_result.threshold,
            delta_t=processing_result.delta_t,
            weather_filename=weather_filename,
            solar_filename=solar_filename,
            table=table,
        )


class PreviewService:
    """Service indépendant pour la génération de previews."""

    def __init__(self, processing_result: ProcessingResult):
        """Initialize avec un ProcessingResult."""
        self.processing_result = processing_result
        self.logger = logging.getLogger(__name__)

    def get_summary(self) -> "PreviewSummaryData":
        """Obtient les données de résumé pour la fenêtre principale."""
        return PreviewSummaryData.from_processing_result(self.processing_result)

    @classmethod
    def from_processing_result(
        cls, processing_result: ProcessingResult
    ) -> "PreviewService":
        """
        Factory method pour créer un PreviewService à partir d'un ProcessingResult.

        Args:
            processing_result: Résultat du traitement des données

        Returns:
            Instance de PreviewService prête pour utilisation dans le GUI
        """
        return PreviewService(processing_result)


def create_preview_from_processing_result(
    processing_result: ProcessingResult,
    max_sample_adjustments: int = 20,
) -> PreviewService:
    """
    Crée un résultat de prévisualisation à partir d'un résultat de traitement.

    Args:
        processing_result: Résultat du traitement des données
        max_sample_adjustments: Nombre max d'ajustements d'exemple à inclure

    Returns:
        PreviewResult contenant les échantillons pour l'affichage GUI
    """
    return PreviewService.from_processing_result(processing_result)


@dataclass
class FacadeDetailData:
    """Données détaillées pour une façade spécifique."""

    facade_id: str
    building_body: str
    facade_key: str
    adjustments_count: int
    percentage_of_total: float
    sample_adjustments: List[PreviewAdjustment]
    monthly_distribution: Dict[int, int]  # mois -> nombre d'ajustements
    hourly_distribution: Dict[int, int]  # heure -> nombre d'ajustements


@dataclass
class SeasonalAnalysisData:
    """Données d'analyse saisonnière."""

    summer_adjustments: int
    winter_adjustments: int
    spring_adjustments: int
    autumn_adjustments: int
    summer_percentage: float
    winter_percentage: float
    spring_percentage: float
    autumn_percentage: float


@dataclass
class StatisticalAnalysisData:
    """Données d'analyse statistique."""

    min_irradiance: float
    max_irradiance: float
    avg_irradiance: float
    min_temp_adjustment: float
    max_temp_adjustment: float
    avg_temp_adjustment: float
    adjustments_above_threshold: int
    threshold_exceeded_percentage: float


class PreviewDataAnalyzer:
    """Analyseur de données pour la génération de previews détaillées."""

    def __init__(self, processing_result: ProcessingResult):
        """Initialize avec un ProcessingResult."""
        self.processing_result = processing_result
        self.logger = logging.getLogger(__name__)

    def analyze_summary_data(self) -> PreviewSummaryData:
        """Analyse les données de résumé."""
        weather_filename = Path(self.processing_result.parameters["weather_file"]).name
        solar_filename = Path(self.processing_result.parameters["solar_file"]).name

        return PreviewSummaryData(
            total_facades=len(self.processing_result.facade_combinations),
            total_adjustments=self.processing_result.total_adjustments,
            weather_data_points=self.processing_result.parameters[
                "weather_data_points"
            ],
            solar_data_points=self.processing_result.parameters["solar_data_points"],
            facade_combinations=self.processing_result.facade_combinations,
            threshold=self.processing_result.parameters["threshold"],
            delta_t=self.processing_result.parameters["delta_t"],
            weather_filename=weather_filename,
            solar_filename=solar_filename,
        )

    def analyze_facade_details(self) -> List[FacadeDetailData]:
        """Analyse les détails par façade."""
        facade_details = []

        for facade_key in self.processing_result.adjusted_weather_data_by_facade.keys():
            facade_id, building_body = facade_key.split("_", 1)
            adjustments_count = self.processing_result.adjustments_by_facade.get(
                facade_key, 0
            )
            percentage = (
                adjustments_count / max(self.processing_result.total_adjustments, 1)
            ) * 100

            # Analyser la distribution mensuelle et horaire
            monthly_dist, hourly_dist = self._analyze_temporal_distribution(facade_key)

            # Créer des échantillons d'ajustements pour cette façade
            sample_adjustments = self._create_facade_sample_adjustments(facade_key)

            facade_detail = FacadeDetailData(
                facade_id=facade_id,
                building_body=building_body,
                facade_key=facade_key,
                adjustments_count=adjustments_count,
                percentage_of_total=percentage,
                sample_adjustments=sample_adjustments,
                monthly_distribution=monthly_dist,
                hourly_distribution=hourly_dist,
            )
            facade_details.append(facade_detail)

        return facade_details

    def analyze_seasonal_data(self) -> SeasonalAnalysisData:
        """Analyse les données saisonnières."""
        seasonal_counts = {"spring": 0, "summer": 0, "autumn": 0, "winter": 0}

        # Compter les ajustements par saison basé sur les statistiques
        for (
            facade_key,
            adjustments_count,
        ) in self.processing_result.adjustments_by_facade.items():
            # Répartition approximative par saison (25% chacune pour simplifier)
            # Dans une implémentation plus complexe, on analyserait les données réelles
            seasonal_counts["summer"] += adjustments_count // 4
            seasonal_counts["winter"] += adjustments_count // 4
            seasonal_counts["spring"] += adjustments_count // 4
            seasonal_counts["autumn"] += adjustments_count - (
                3 * (adjustments_count // 4)
            )

        total = sum(seasonal_counts.values()) or 1

        return SeasonalAnalysisData(
            summer_adjustments=seasonal_counts["summer"],
            winter_adjustments=seasonal_counts["winter"],
            spring_adjustments=seasonal_counts["spring"],
            autumn_adjustments=seasonal_counts["autumn"],
            summer_percentage=(seasonal_counts["summer"] / total) * 100,
            winter_percentage=(seasonal_counts["winter"] / total) * 100,
            spring_percentage=(seasonal_counts["spring"] / total) * 100,
            autumn_percentage=(seasonal_counts["autumn"] / total) * 100,
        )

    def analyze_statistical_data(
        self, sample_adjustments: List[PreviewAdjustment]
    ) -> StatisticalAnalysisData:
        """Analyse les données statistiques."""
        if not sample_adjustments:
            return StatisticalAnalysisData(
                min_irradiance=0,
                max_irradiance=0,
                avg_irradiance=0,
                min_temp_adjustment=0,
                max_temp_adjustment=0,
                avg_temp_adjustment=0,
                adjustments_above_threshold=0,
                threshold_exceeded_percentage=0,
            )

        irradiances = [adj.solar_irradiance for adj in sample_adjustments]
        temp_adjustments = [
            adj.adjusted_temp - adj.original_temp for adj in sample_adjustments
        ]
        threshold = self.processing_result.parameters["threshold"]
        above_threshold = len(
            [adj for adj in sample_adjustments if adj.solar_irradiance > threshold]
        )

        return StatisticalAnalysisData(
            min_irradiance=min(irradiances),
            max_irradiance=max(irradiances),
            avg_irradiance=sum(irradiances) / len(irradiances),
            min_temp_adjustment=min(temp_adjustments),
            max_temp_adjustment=max(temp_adjustments),
            avg_temp_adjustment=sum(temp_adjustments) / len(temp_adjustments),
            adjustments_above_threshold=above_threshold,
            threshold_exceeded_percentage=(above_threshold / len(sample_adjustments))
            * 100,
        )

    def _analyze_temporal_distribution(
        self, facade_key: str
    ) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Analyse la distribution temporelle (mensuelle et horaire)."""
        monthly_dist = {i: 0 for i in range(1, 13)}
        hourly_dist = {i: 0 for i in range(24)}

        # Approximation basée sur le nombre d'ajustements
        adjustments_count = self.processing_result.adjustments_by_facade.get(
            facade_key, 0
        )

        # Répartition approximative par mois (plus d'ajustements en été)
        summer_months = [6, 7, 8]
        for month in range(1, 13):
            if month in summer_months:
                monthly_dist[month] = (
                    adjustments_count // 6
                )  # Plus d'ajustements en été
            else:
                monthly_dist[month] = adjustments_count // 12

        # Répartition approximative par heure (plus d'ajustements aux heures de pointe solaire)
        peak_hours = [11, 12, 13, 14, 15]
        for hour in range(24):
            if hour in peak_hours:
                hourly_dist[hour] = (
                    adjustments_count // 10
                )  # Plus d'ajustements aux heures de pointe
            else:
                hourly_dist[hour] = adjustments_count // 24

        return monthly_dist, hourly_dist

    def _create_facade_sample_adjustments(
        self, facade_key: str, max_samples: int = 10
    ) -> List[PreviewAdjustment]:
        """Crée des échantillons d'ajustements pour une façade spécifique."""
        # Cette méthode sera implémentée pour créer des échantillons spécifiques à une façade
        # Pour l'instant, retourne une liste vide
        return []

    def _get_season(self, month: int) -> str:
        """Détermine la saison basée sur le mois."""
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"


# class PreviewService:
#     """Service indépendant pour la génération de previews avec données modulaires."""

#     def __init__(self, processing_result: ProcessingResult):
#         """Initialize avec un ProcessingResult pour un accès complet aux données."""
#         self.processing_result = processing_result
#         self.analyzer = PreviewDataAnalyzer(processing_result)
#         self.logger = logging.getLogger(__name__)

#         # Données pré-calculées pour les différentes fenêtres
#         self._summary_data: Optional[PreviewSummaryData] = None
#         self._facade_details: Optional[List[FacadeDetailData]] = None
#         self._seasonal_data: Optional[SeasonalAnalysisData] = None
#         self._statistical_data: Optional[StatisticalAnalysisData] = None
#         self._sample_adjustments: Optional[List[PreviewAdjustment]] = None

#     @classmethod
#     def from_processing_result(
#         cls, processing_result: ProcessingResult
#     ) -> "PreviewService":
#         """
#         Factory method pour créer un PreviewService à partir d'un ProcessingResult.

#         Args:
#             processing_result: Résultat du traitement des données

#         Returns:
#             Instance de PreviewService prête pour utilisation dans le GUI
#         """
#         return cls(processing_result)

#     def get_summary_data(self) -> PreviewSummaryData:
#         """Obtient les données de résumé pour la fenêtre principale."""
#         if self._summary_data is None:
#             self._summary_data = self.analyzer.analyze_summary_data()
#         return self._summary_data

#     def get_facade_details(self) -> List[FacadeDetailData]:
#         """Obtient les détails par façade pour l'onglet façades."""
#         if self._facade_details is None:
#             self._facade_details = self.analyzer.analyze_facade_details()
#         return self._facade_details

#     def get_seasonal_analysis(self) -> SeasonalAnalysisData:
#         """Obtient l'analyse saisonnière."""
#         if self._seasonal_data is None:
#             self._seasonal_data = self.analyzer.analyze_seasonal_data()
#         return self._seasonal_data

#     def get_statistical_analysis(self) -> StatisticalAnalysisData:
#         """Obtient l'analyse statistique."""
#         if self._statistical_data is None:
#             sample_adjustments = self.get_sample_adjustments()
#             self._statistical_data = self.analyzer.analyze_statistical_data(
#                 sample_adjustments
#             )
#         return self._statistical_data

#     def get_sample_adjustments(self, max_samples: int = 20) -> List[PreviewAdjustment]:
#         """Obtient les échantillons d'ajustements pour la prévisualisation."""
#         if self._sample_adjustments is None:
#             self._sample_adjustments = self._create_stratified_samples(max_samples)
#         return self._sample_adjustments or []

#     def get_facade_specific_data(self, facade_key: str) -> Optional[FacadeDetailData]:
#         """Obtient les données spécifiques à une façade."""
#         facade_details = self.get_facade_details()
#         for detail in facade_details:
#             if detail.facade_key == facade_key:
#                 return detail
#         return None

#     def get_legacy_processing_statistics(self) -> Dict[str, Any]:
#         """
#         Obtient des statistiques détaillées du traitement (méthode legacy).

#         Returns:
#             Dictionnaire avec les statistiques détaillées
#         """
#         summary = self.get_summary_data()
#         return {
#             "total_facades": summary.total_facades,
#             "total_adjustments": summary.total_adjustments,
#             "adjustments_by_facade": self.processing_result.adjustments_by_facade,
#             "weather_data_points": summary.weather_data_points,
#             "solar_data_points": summary.solar_data_points,
#             "threshold": summary.threshold,
#             "delta_t": summary.delta_t,
#             "facade_combinations": summary.facade_combinations,
#         }

#     def create_preview_from_processing_result(
#         self,
#         processing_result: ProcessingResult,
#         max_sample_adjustments: int = 20,
#     ) -> PreviewResult:
#         """
#         Crée un résultat de prévisualisation à partir d'un résultat de traitement (méthode legacy).

#         Args:
#             processing_result: Résultat du traitement des données
#             max_sample_adjustments: Nombre max d'ajustements d'exemple à inclure

#         Returns:
#             PreviewResult contenant les échantillons pour l'affichage GUI
#         """
#         self.logger.info("Creating preview from processing result...")

#         # Créer des échantillons d'ajustements stratifiés
#         sample_adjustments = self.get_sample_adjustments(max_sample_adjustments)

#         preview_result = PreviewResult(
#             processing_result=processing_result,
#             sample_adjustments=sample_adjustments,
#             max_sample_adjustments=max_sample_adjustments,
#         )

#         self.logger.info(
#             f"Preview created with {len(sample_adjustments)} sample adjustments"
#         )
#         return preview_result

#     def _create_stratified_samples(self, max_samples: int) -> List[PreviewAdjustment]:
#         """
#         Crée des échantillons stratifiés d'ajustements pour la prévisualisation.

#         Args:
#             max_samples: Nombre maximum d'échantillons

#         Returns:
#             Liste d'ajustements d'exemple stratifiés
#         """
#         sample_adjustments = []
#         facade_samples = {}  # Pour stratifier les échantillons par façade

#         # Charger les données originales pour créer les échantillons détaillés
#         solar_metadata, solar_data = load_solar_irridance_data(
#             self.processing_result.parameters["solar_file"]
#         )
#         weather_metadata, weather_data = load_weather_data(
#             self.processing_result.parameters["weather_file"]
#         )

#         # Import FacadeProcessor here to avoid circular imports
#         from core import FacadeProcessor

#         facade_processor = FacadeProcessor(
#             self.processing_result.parameters["threshold"],
#             self.processing_result.parameters["delta_t"],
#         )

#         for facade_key in self.processing_result.adjusted_weather_data_by_facade.keys():
#             facade_id, building_body = facade_key.split("_", 1)

#             # Initialize stratified sampling
#             facade_samples[facade_key] = {
#                 "summer": [],  # Mars-Septembre (heure d'été potentielle)
#                 "winter": [],  # Octobre-Février (heure d'hiver)
#             }

#             # Find the specific facade column
#             facade_column = facade_processor._find_facade_column(
#                 solar_metadata, facade_id, building_body
#             )
#             if not facade_column:
#                 continue

#             # Create solar lookup
#             solar_lookup = facade_processor._create_solar_lookup(
#                 solar_data, facade_column
#             )

#             # Sample from the original weather data to show adjustments
#             for weather_point in weather_data[:1000]:  # Sample from first 1000 points
#                 solar_irradiance = facade_processor._get_solar_irradiance_for_datetime(
#                     solar_lookup, weather_point
#                 )

#                 if (
#                     solar_irradiance is not None
#                     and solar_irradiance
#                     > self.processing_result.parameters["threshold"]
#                 ):
#                     # Determine season for stratified sampling
#                     season = "summer" if 3 <= weather_point.month <= 9 else "winter"

#                     # Add to stratified sample if not full for this facade/season
#                     if (
#                         len(facade_samples[facade_key][season]) < 3
#                     ):  # Max 3 per season per facade
#                         weather_time_str = f"{weather_point.month:02d}-{weather_point.day:02d} {weather_point.hour:02d}:00"
#                         adjustment = PreviewAdjustment(
#                             datetime_str=weather_time_str,
#                             facade_id=facade_id,
#                             building_body=building_body,
#                             original_temp=weather_point.temperature,
#                             adjusted_temp=weather_point.temperature
#                             + self.processing_result.parameters["delta_t"],
#                             solar_irradiance=solar_irradiance,
#                             threshold=self.processing_result.parameters["threshold"],
#                             weather_datetime=weather_time_str,
#                             solar_datetime=weather_time_str,
#                         )
#                         facade_samples[facade_key][season].append(adjustment)

#         # Build final stratified sample list
#         for facade_key, seasons in facade_samples.items():
#             for season, adjustments in seasons.items():
#                 sample_adjustments.extend(adjustments)
#                 if len(sample_adjustments) >= max_samples:
#                     break
#             if len(sample_adjustments) >= max_samples:
#                 break

#         return sample_adjustments[:max_samples]
#         """
#         Crée des échantillons stratifiés d'ajustements pour la prévisualisation.

#         Args:
#             processing_result: Résultat du traitement
#             max_samples: Nombre maximum d'échantillons

#         Returns:
#             Liste d'ajustements d'exemple stratifiés
#         """
#         sample_adjustments = []
#         facade_samples = {}  # Pour stratifier les échantillons par façade

#         # Charger les données originales pour créer les échantillons détaillés
#         solar_metadata, solar_data = load_solar_irridance_data(
#             processing_result.parameters["solar_file"]
#         )
#         weather_metadata, weather_data = load_weather_data(
#             processing_result.parameters["weather_file"]
#         )

#         # Import FacadeProcessor here to avoid circular imports
#         from .core import FacadeProcessor

#         facade_processor = FacadeProcessor(
#             processing_result.parameters["threshold"],
#             processing_result.parameters["delta_t"],
#         )

#         for facade_key in processing_result.adjusted_weather_data_by_facade.keys():
#             facade_id, building_body = facade_key.split("_", 1)

#             # Initialize stratified sampling
#             facade_samples[facade_key] = {
#                 "summer": [],  # Mars-Septembre (heure d'été potentielle)
#                 "winter": [],  # Octobre-Février (heure d'hiver)
#             }

#             # Find the specific facade column
#             facade_column = facade_processor._find_facade_column(
#                 solar_metadata, facade_id, building_body
#             )
#             if not facade_column:
#                 continue

#             # Create solar lookup
#             solar_lookup = facade_processor._create_solar_lookup(
#                 solar_data, facade_column
#             )

#             # Sample from the original weather data to show adjustments
#             for weather_point in weather_data[:1000]:  # Sample from first 1000 points
#                 solar_irradiance = facade_processor._get_solar_irradiance_for_datetime(
#                     solar_lookup, weather_point
#                 )

#                 if (
#                     solar_irradiance is not None
#                     and solar_irradiance > processing_result.parameters["threshold"]
#                 ):
#                     # Determine season for stratified sampling
#                     season = "summer" if 3 <= weather_point.month <= 9 else "winter"

#                     # Add to stratified sample if not full for this facade/season
#                     if (
#                         len(facade_samples[facade_key][season]) < 3
#                     ):  # Max 3 per season per facade
#                         weather_time_str = f"{weather_point.month:02d}-{weather_point.day:02d} {weather_point.hour:02d}:00"
#                         adjustment = PreviewAdjustment(
#                             datetime_str=weather_time_str,
#                             facade_id=facade_id,
#                             building_body=building_body,
#                             original_temp=weather_point.temperature,
#                             adjusted_temp=weather_point.adjusted_temperature
#                             + processing_result.parameters["delta_t"],
#                             solar_irradiance=solar_irradiance,
#                             threshold=processing_result.parameters["threshold"],
#                             weather_datetime=weather_time_str,
#                             solar_datetime=weather_time_str,
#                         )
#                         facade_samples[facade_key][season].append(adjustment)

#         # Build final stratified sample list
#         for facade_key, seasons in facade_samples.items():
#             for season, adjustments in seasons.items():
#                 sample_adjustments.extend(adjustments)
#                 if len(sample_adjustments) >= max_samples:
#                     break
#             if len(sample_adjustments) >= max_samples:
#                 break

#         return sample_adjustments[:max_samples]

#     def get_processing_statistics(self, processing_result: ProcessingResult) -> dict:
#         """
#         Obtient des statistiques détaillées du traitement.

#         Args:
#             processing_result: Résultat du traitement

#         Returns:
#             Dictionnaire avec les statistiques détaillées
#         """
#         return {
#             "total_facades": len(processing_result.facade_combinations),
#             "total_adjustments": processing_result.total_adjustments,
#             "adjustments_by_facade": processing_result.adjustments_by_facade,
#             "weather_data_points": processing_result.parameters["weather_data_points"],
#             "solar_data_points": processing_result.parameters["solar_data_points"],
#             "threshold": processing_result.parameters["threshold"],
#             "delta_t": processing_result.parameters["delta_t"],
#             "facade_combinations": processing_result.facade_combinations,
#         }


# Factory function for easy instantiation (DEPRECATED - use PreviewService.from_processing_result)
def create_preview_service(processing_result: ProcessingResult) -> PreviewService:
    """Create a preview service instance from processing result."""
    return PreviewService.from_processing_result(processing_result)
