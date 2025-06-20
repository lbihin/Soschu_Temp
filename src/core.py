"""
Core functionality for the Soschu Temperature tool.

This module provides the main processing logic to adjust weather data based on
solar irradiance thresholds for different facade orientations of building bodies.
"""

import logging
import re
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

from config import Config
from output_generator import OutputGenerator, create_try_generator
from solar import SolarDataPoint, SolarFileMetadata, load_solar_irridance_data
from weather import WeatherDataPoint, WeatherFileMetadata, load_weather_data

# Setup logging
logger = logging.getLogger(__name__)


class FacadeProcessingResult(BaseModel):
    """Résultat du traitement pour une façade spécifique."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    facade_id: str
    building_body: str
    wheater_data: List[WeatherDataPoint]
    solar_data: List[SolarDataPoint]
    adjustments_count: int = Field(ge=0, description="Number of adjustments made")

    class Config:
        arbitrary_types_allowed = True

    def count_weather_data_points(self) -> int:
        """
        Count the total number of weather data points processed for this facade.

        Returns:
            Total number of weather data points
        """
        return len(self.wheater_data)
    
    def count_solar_data_points(self) -> int:
        """
        Count the total number of solar data points processed for this facade.

        Returns:
            Total number of solar data points
        """
        return len(self.solar_data)
    
    def get_full_name(self) -> str:
        """        Get a full descriptive name for this facade processing result."""
        return f"{self.facade_id} {self.building_body}"
    


class ProcessingResult(BaseModel):
    """Résultat du traitement contenant toutes les données nécessaires pour la preview et la génération."""

    # Métadonnées et paramètres
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    threshold: float = Field(
        ge=0,
        description="Solar irradiance threshold in W/m² above which temperature is adjusted",
    )
    delta_t: float = Field(
        ge=0,
        description="Temperature increase in °C to apply when threshold is exceeded",
    )
    weather_file: str = Field(description="Path to the weather data file")
    solar_file: str = Field(description="Path to the solar irradiance HTML file")
    data: Dict[str, FacadeProcessingResult] = Field(
        description="Processed data for each facade, keyed by unique ID"
    )

    class Config:
        arbitrary_types_allowed = True

    def count_facades(self) -> int:
        """
        Count the number of facades processed in this result.

        Returns:
            Total number of unique facades
        """
        return len(self.data)

    def count_adjustments(self) -> int:
        """
        Count the total number of temperature adjustments made across all facades.

        Returns:
            Total number of adjustments
        """
        total_adjustments = 0
        for facade_result in self.data.values():
            total_adjustments += facade_result.adjustments_count
        return total_adjustments

    def count_overall_weather_data_points(self) -> int:
        """
        Count the total number of weather data points across all facades.

        Returns:
            Total number of weather data points
        """
        total_count = 0
        for facade_result in self.data.values():
            total_count += facade_result.count_weather_data_points()
        return total_count

    def count_solar_data_points(self) -> int:
        """
        Count the total number of solar data points across all facades.

        Returns:
            Total number of solar data points
        """
        total_count = 0
        for facade_result in self.data.values():
            total_count += facade_result.count_solar_data_points()
        return total_count


class PreviewAdjustment(BaseModel):
    """Représente un ajustement de température pour la prévisualisation."""

    datetime_str: str = Field(description="Formatted datetime string")
    facade_id: str = Field(description="Facade identifier (e.g., f1, f2)")
    building_body: str = Field(description="Building body identifier")
    original_temp: float = Field(description="Original temperature in °C")
    adjusted_temp: float = Field(description="Adjusted temperature in °C")
    solar_irradiance: float = Field(ge=0, description="Solar irradiance in W/m²")
    threshold: float = Field(ge=0, description="Threshold value in W/m²")
    weather_datetime: Optional[str] = Field(None, description="Weather data timestamp")
    solar_datetime: Optional[str] = Field(None, description="Solar data timestamp")

    @model_validator(mode="after")
    def set_default_datetimes(self):
        """Set weather_datetime and solar_datetime to datetime_str if not provided."""
        if self.weather_datetime is None:
            self.weather_datetime = self.datetime_str
        if self.solar_datetime is None:
            self.solar_datetime = self.datetime_str
        return self

    @model_validator(mode="after")
    def validate_temperature_adjustment(self):
        """Validate that adjusted temperature is greater than original when solar irradiance exceeds threshold."""
        if (
            self.solar_irradiance > self.threshold
            and self.adjusted_temp <= self.original_temp
        ):
            raise ValueError(
                f"Adjusted temperature {self.adjusted_temp}°C should be greater than original {self.original_temp}°C when solar irradiance {self.solar_irradiance} W/m² exceeds threshold {self.threshold} W/m²"
            )
        return self


class PreviewResult(BaseModel):
    """Résultat de la prévisualisation pour l'affichage GUI."""

    # Inherit all data from ProcessingResult
    processing_result: ProcessingResult

    # Additional preview-specific data
    sample_adjustments: List[PreviewAdjustment] = Field(
        description="Sample adjustments for preview"
    )
    max_sample_adjustments: int = Field(
        ge=0, description="Maximum number of sample adjustments"
    )

    @model_validator(mode="after")
    def validate_sample_adjustments_count(self):
        """Validate that sample adjustments don't exceed max limit."""
        if len(self.sample_adjustments) > self.max_sample_adjustments:
            raise ValueError(
                f"Number of sample adjustments {len(self.sample_adjustments)} exceeds maximum {self.max_sample_adjustments}"
            )
        return self

    class Config:
        arbitrary_types_allowed = True


class FacadeProcessor:
    """Processes weather data adjustments based on facade solar irradiance."""

    def __init__(self, threshold: float, delta_t: float):
        """
        Initialize the facade processor.

        Args:
            threshold: Solar irradiance threshold in W/m² above which temperature is adjusted
            delta_t: Temperature increase in °C to apply when threshold is exceeded
        """
        self.threshold = threshold
        self.delta_t = delta_t
        self.logger = logging.getLogger(__name__)
        self.weather_data = None
        self.solar_data = None

    def process_facade_data(
        self,
        weather_data: List[WeatherDataPoint],
        solar_metadata: SolarFileMetadata,
        solar_data: List[SolarDataPoint],
        facade_id: str = "",
        building_body: str = "",
    ) -> Optional[FacadeProcessingResult]:
        """
        Process weather data for a specific facade of a building body.

        Args:
            weather_data: Weather data points to modify
            solar_metadata: Solar file metadata
            solar_data: Solar irradiance data points
            facade_id: Facade identifier (e.g., "f1", "f2", etc.)
            building_body: Building body identifier (e.g., "Building body", "Building body 2")

        Returns:
            FacadeProcessingResult containing processed data
        """
        self.logger.info(f"Processing facade {facade_id} of {building_body}")

        # Find the specific facade column in solar data
        facade_column = self._find_facade_column(
            solar_metadata, facade_id, building_body
        )
        if not facade_column:
            self.logger.warning(
                f"No solar data found for facade {facade_id} of {building_body}"
            )
            return

        self.logger.info(f"Found solar column: {facade_column}")

        # Create a lookup table for solar irradiance by datetime
        solar_lookup = self._create_solar_lookup(solar_data, facade_column)

        # Create deep copy of weather data for this facade
        facade_weather_data = deepcopy(weather_data)

        # Process each weather data point
        count_adjustments = 0
        for weather_point in facade_weather_data:
            # Find corresponding solar irradiance value
            solar_irradiance = self._get_solar_irradiance_for_datetime(
                solar_lookup, weather_point
            )

            # Apply temperature adjustment if threshold is exceeded
            if solar_irradiance is not None and solar_irradiance > self.threshold:
                # Update the adjusted temperature
                weather_point.adjusted_temperature += self.delta_t
                count_adjustments += 1
                self.logger.debug(
                    f"Adjusted temperature for {weather_point.month:02d}-{weather_point.day:02d} "
                    f"{weather_point.hour:02d}:00 - Solar: {solar_irradiance:.1f} W/m² > {self.threshold} W/m², "
                    f"Temp: {weather_point.temperature:.1f}°C → {weather_point.adjusted_temperature:.1f}°C"
                )

        self.logger.info(
            f"Made {count_adjustments} temperature adjustments out of {len(weather_data)} data points"
        )

        # Create and return the facade processing result
        return FacadeProcessingResult(
            facade_id=facade_id,
            building_body=building_body,
            wheater_data=facade_weather_data,
            solar_data=solar_data,
            adjustments_count=count_adjustments,
        )

    def _find_facade_column(
        self, solar_metadata: SolarFileMetadata, facade_id: str, building_body: str
    ) -> Optional[str]:
        """
        Find the solar data column corresponding to the specific facade and building body.

        Args:
            solar_metadata: Solar file metadata containing facade columns
            facade_id: Facade identifier (e.g., "f1", "f2")
            building_body: Building body identifier

        Returns:
            Column name if found, None otherwise
        """
        for column in solar_metadata.facade_columns:
            # Check if column matches both facade and building body
            if facade_id in column and building_body in column:
                return column

        return None

    def _create_solar_lookup(
        self, solar_data: List[SolarDataPoint], facade_column: str
    ) -> Dict[datetime, float]:
        """
        Create a lookup table for solar irradiance values by datetime.

        Uses naive datetime objects to enable direct comparison with weather data.

        Args:
            solar_data: List of solar data points
            facade_column: Name of the facade column to extract values from

        Returns:
            Dictionary mapping naive datetime to irradiance value
        """
        lookup = {}

        for solar_point in solar_data:
            if facade_column in solar_point.irradiance_values:
                # Use naive datetime for comparison (solar timestamps are already naive)
                dt_key = solar_point.timestamp
                irradiance = solar_point.irradiance_values[facade_column]
                lookup[dt_key] = irradiance

        self.logger.debug(
            f"Created solar lookup with {len(lookup)} entries for column {facade_column}"
        )
        return lookup

    def _get_solar_irradiance_for_datetime(
        self,
        solar_lookup: Dict[datetime, float],
        weather_point: WeatherDataPoint,
    ) -> Optional[float]:
        """
        Get solar irradiance value for a specific weather data point.

        This method searches for a matching timestamp in the solar lookup dictionary
        and returns the corresponding irradiance value when found.

            solar_lookup: Dictionary mapping datetime objects to solar irradiance values
            weather_point: Weather data point containing the timestamp to look up

            float: Solar irradiance value in W/m² if a matching timestamp is found
            None: If no matching timestamp exists in the lookup table
        """
        for lookup_solar_dt, solar_irradiance in solar_lookup.items():
            # Compare naive timestamps directly
            if weather_point.timestamp == lookup_solar_dt:
                return solar_irradiance


class CoreProcessor:
    """Main processor for weather data adjustments. Focuses only on data processing."""

    def __init__(self):
        """Initialize the core processor."""
        self.logger = logging.getLogger(__name__)

    def process_all_facades(
        self,
        weather_file_path: str,
        solar_file_path: str,
        threshold: float,
        delta_t: float,
    ) -> ProcessingResult:
        """
        Process all facades and return complete processing result.
        This method only handles data processing, not file generation.

        Args:
            weather_file_path: Path to the weather data file
            solar_file_path: Path to the solar irradiance HTML file
            threshold: Solar irradiance threshold in W/m²
            delta_t: Temperature increase in °C

        Returns:
            ProcessingResult containing all processed data and statistics
        """
        self.logger.info("Starting facade processing...")

        # Load solar data first to extract year for configuration
        solar_metadata, solar_data = load_solar_irridance_data(solar_file_path)
        self.logger.info(f"Loaded {len(solar_data)} solar data points")

        # Set configuration year from solar data
        if solar_data:
            config = Config()
            config.year = solar_data[0].timestamp.year

        # Load weather data
        weather_metadata, weather_data = load_weather_data(weather_file_path)
        self.logger.info(f"Loaded {len(weather_data)} weather data points")

        # Extract facade combinations
        facade_combinations = self._extract_facade_combinations(solar_metadata)
        self.logger.info(
            f"Found {len(facade_combinations)} facade combinations: {facade_combinations}"
        )

        # Process each facade and collect results
        processed_data = {}
        facade_processor = FacadeProcessor(threshold=threshold, delta_t=delta_t)

        for facade_id, building_body in facade_combinations:
            self.logger.info(f"Processing {facade_id} of {building_body}")

            # Process facade data
            processing_result = facade_processor.process_facade_data(
                weather_data=weather_data,
                solar_metadata=solar_metadata,
                solar_data=solar_data,
                facade_id=facade_id,
                building_body=building_body,
            )

            # Store results
            processed_data[processing_result.id] = processing_result

        # Create parameters dictionary
        parameters = {
            "threshold": threshold,
            "delta_t": delta_t,
            "weather_file": weather_file_path,
            "solar_file": solar_file_path,
            "data": processed_data,
        }

        # Create and return processing result
        return ProcessingResult(**parameters)

    def _extract_facade_combinations(
        self, solar_metadata: SolarFileMetadata
    ) -> List[Tuple[str, str]]:
        """
        Extract unique facade and building body combinations from solar metadata.

        Args:
            solar_metadata: Solar file metadata containing facade columns

        Returns:
            List of (facade_id, building_body) tuples
        """
        combinations = set()

        for column in solar_metadata.facade_columns:
            # Parse facade ID (e.g., "f1", "f2", "f3", "f4")
            facade_match = re.search(r"(f\d+)", column)
            if not facade_match:
                continue
            facade_id = facade_match.group(1)

            # Parse building body (e.g., "Building body", "Building body 2")
            building_match = re.search(r"(Building body(?:\s+\d+)?)", column)
            if not building_match:
                continue
            building_body = building_match.group(1)

            combinations.add((facade_id, building_body))

        return sorted(list(combinations))


# For backward compatibility - but recommend using the new services
def preview_weather_solar_processing(
    weather_file_path: str,
    solar_file_path: str,
    threshold: float,
    delta_t: float,
    max_sample_adjustments: int = 20,
) -> PreviewResult:
    """
    Legacy function for backward compatibility.
    Recommend using PreviewService.create_preview_from_processing_result() instead.
    """
    from preview import create_preview_service

    # Process all data using CoreProcessor
    processor = CoreProcessor()
    processing_result = processor.process_all_facades(
        weather_file_path, solar_file_path, threshold, delta_t
    )

    # Create preview using the new service
    preview_service = create_preview_service()
    return preview_service.create_preview_from_processing_result(
        processing_result, max_sample_adjustments
    )


def process_weather_with_solar_data(
    weather_file_path: str,
    solar_file_path: str,
    threshold: float,
    delta_t: float,
    output_dir: str = "output",
    output_generator: Optional[OutputGenerator] = None,
) -> Dict[str, str]:
    """
    Legacy function for backward compatibility.
    Recommend using CoreProcessor + FileGenerationService instead.
    """
    from file_generation_service import create_file_generation_service

    # Process all data first
    processor = CoreProcessor()
    processing_result = processor.process_all_facades(
        weather_file_path, solar_file_path, threshold, delta_t
    )

    # Generate files using the new service
    file_service = create_file_generation_service(output_generator)
    return file_service.generate_files_from_processing_result(
        processing_result, output_dir
    )


def generate_files_from_preview(
    preview_result: PreviewResult,
    output_dir: str = "output",
    output_generator: Optional[OutputGenerator] = None,
    selected_facades: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Legacy function for backward compatibility.
    Recommend using FileGenerationService.generate_files_from_preview_result() instead.
    """
    from file_generation_service import create_file_generation_service

    file_service = create_file_generation_service(output_generator)
    return file_service.generate_files_from_preview_result(
        preview_result, output_dir, selected_facades
    )


# Example usage
if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(level=logging.DEBUG)

    # Test parameters
    weather_file = "tests/data/TRY2045_488284093163_Jahr.dat"
    solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
    threshold = 200.0  # W/m²
    delta_t = 7.0  # °C

    try:
        output_files = process_weather_with_solar_data(
            weather_file, solar_file, threshold, delta_t
        )

        print(f"Generated {len(output_files)} output files:")
        for facade, filepath in output_files.items():
            print(f"  {facade}: {filepath}")

    except Exception as e:
        print(f"Error: {e}")
