"""
Core functionality for the Soschu Temperature tool.

This module provides the main processing logic to adjust weather data based on
solar irradiance thresholds for different facade orientations of building bodies.
"""

import logging
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from solar import SolarDataPoint, SolarFileMetadata, load_solar_irridance_data
from weather import WeatherDataPoint, WeatherFileMetadata, load_weather_data

# Setup logging
logger = logging.getLogger(__name__)


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

    def process_facade_data(
        self,
        weather_metadata: WeatherFileMetadata,
        weather_data: List[WeatherDataPoint],
        solar_metadata: SolarFileMetadata,
        solar_data: List[SolarDataPoint],
        facade_id: str,
        building_body: str,
    ) -> Tuple[WeatherFileMetadata, List[WeatherDataPoint]]:
        """
        Process weather data for a specific facade of a building body.

        Args:
            weather_metadata: Original weather file metadata
            weather_data: Original weather data points
            solar_metadata: Solar file metadata
            solar_data: Solar irradiance data points
            facade_id: Facade identifier (e.g., "f1", "f2", etc.)
            building_body: Building body identifier (e.g., "Building body", "Building body 2")

        Returns:
            Tuple of adjusted weather metadata and weather data points
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
            return weather_metadata, weather_data

        self.logger.info(f"Found solar column: {facade_column}")

        # Create a lookup table for solar irradiance by datetime
        solar_lookup = self._create_solar_lookup(solar_data, facade_column)

        # Process each weather data point
        adjusted_weather_data = []
        adjustments_made = 0

        for weather_point in weather_data:
            # Create a copy of the weather point for modification
            adjusted_point = deepcopy(weather_point)

            # Find corresponding solar irradiance value
            solar_irradiance = self._get_solar_irradiance_for_datetime(
                solar_lookup, weather_point
            )

            # Apply temperature adjustment if threshold is exceeded
            if solar_irradiance is not None and solar_irradiance > self.threshold:
                adjusted_point.temperature += self.delta_t
                adjustments_made += 1
                self.logger.debug(
                    f"Adjusted temperature for {weather_point.month:02d}-{weather_point.day:02d} "
                    f"{weather_point.hour:02d}:00 - Solar: {solar_irradiance:.1f} W/m² > {self.threshold} W/m², "
                    f"Temp: {weather_point.temperature:.1f}°C → {adjusted_point.temperature:.1f}°C"
                )

            adjusted_weather_data.append(adjusted_point)

        self.logger.info(
            f"Made {adjustments_made} temperature adjustments out of {len(weather_data)} data points"
        )

        # Create adjusted metadata
        adjusted_metadata = self._create_adjusted_metadata(
            weather_metadata, facade_id, building_body, adjustments_made
        )

        return adjusted_metadata, adjusted_weather_data

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
        Get solar irradiance value for specific weather data point.

        Uses naive datetime comparison to handle MEZ/MESZ differences correctly.
        Matches based on month/day/hour regardless of year.

        Args:
            solar_lookup: Solar irradiance lookup table
            weather_point: Weather data point to find solar irradiance for

        Returns:
            Solar irradiance value in W/m² or None if not found
        """
        # Try direct lookup first (for cases where years match)
        weather_dt = weather_point.to_datetime_for_comparison()
        irradiance = solar_lookup.get(weather_dt)

        if irradiance is not None:
            return irradiance

        # If no exact match, try matching by month/day/hour regardless of year
        weather_month = weather_point.month
        weather_day = weather_point.day
        weather_hour = weather_point.hour - 1  # Convert to 0-23 format

        for solar_dt, solar_irradiance in solar_lookup.items():
            if (
                solar_dt.month == weather_month
                and solar_dt.day == weather_day
                and solar_dt.hour == weather_hour
            ):
                self.logger.debug(
                    f"Found solar data by date/time match: "
                    f"Weather: {weather_month:02d}-{weather_day:02d} {weather_hour:02d}:00, "
                    f"Solar: {solar_dt}"
                )
                return solar_irradiance

        # If still no match, try a tolerance-based search
        for solar_dt, solar_irradiance in solar_lookup.items():
            # Create comparable datetimes with same year
            weather_dt_adjusted = weather_dt.replace(year=solar_dt.year)
            time_diff = abs((weather_dt_adjusted - solar_dt).total_seconds())
            if time_diff <= 1800:  # 30 minutes tolerance
                self.logger.debug(
                    f"Found solar data with {time_diff/60:.1f} min difference: "
                    f"Weather: {weather_dt_adjusted}, Solar: {solar_dt}"
                )
                return solar_irradiance

        return None

    def _create_adjusted_metadata(
        self,
        original_metadata: WeatherFileMetadata,
        facade_id: str,
        building_body: str,
        adjustments_made: int,
    ) -> WeatherFileMetadata:
        """
        Create adjusted weather metadata with processing information.

        Args:
            original_metadata: Original weather metadata
            facade_id: Facade identifier
            building_body: Building body identifier
            adjustments_made: Number of temperature adjustments made

        Returns:
            Adjusted weather metadata
        """
        # Create a copy of the original metadata
        adjusted_metadata = deepcopy(original_metadata)

        # Add processing information to data basis fields
        processing_info = (
            f"Processed for {facade_id} of {building_body} - "
            f"Threshold: {self.threshold} W/m², Delta T: {self.delta_t}°C, "
            f"Adjustments: {adjustments_made}"
        )

        # Update one of the data basis fields with processing info
        if adjusted_metadata.data_basis_3:
            adjusted_metadata.data_basis_3 = (
                f"{adjusted_metadata.data_basis_3} | {processing_info}"
            )
        else:
            adjusted_metadata.data_basis_3 = processing_info

        return adjusted_metadata


class CoreProcessor:
    """Main processor for the Soschu Temperature tool."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_all_facades(
        self,
        weather_file_path: str,
        solar_file_path: str,
        threshold: float,
        delta_t: float,
        output_dir: str = "output",
    ) -> Dict[str, str]:
        """
        Process all facades in the solar data and generate adjusted weather files.

        Args:
            weather_file_path: Path to the weather data file
            solar_file_path: Path to the solar irradiance HTML file
            threshold: Solar irradiance threshold in W/m²
            delta_t: Temperature increase in °C
            output_dir: Directory to save output files

        Returns:
            Dictionary mapping facade identifiers to output file paths
        """
        self.logger.info("Starting facade processing...")

        # Load weather data
        weather_metadata, weather_data = load_weather_data(weather_file_path)
        self.logger.info(f"Loaded {len(weather_data)} weather data points")

        # Load solar data
        solar_metadata, solar_data = load_solar_irridance_data(solar_file_path)
        self.logger.info(f"Loaded {len(solar_data)} solar data points")

        # Get all facade/building body combinations
        facade_combinations = self._extract_facade_combinations(solar_metadata)
        self.logger.info(
            f"Found {len(facade_combinations)} facade combinations: {facade_combinations}"
        )

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Extract base name from weather file (without extension)
        weather_file_base = Path(weather_file_path).stem

        # Process each facade combination
        facade_processor = FacadeProcessor(threshold, delta_t)
        output_files = {}

        for facade_id, building_body in facade_combinations:
            self.logger.info(f"Processing {facade_id} of {building_body}")

            # Process the facade
            adjusted_metadata, adjusted_weather_data = (
                facade_processor.process_facade_data(
                    weather_metadata,
                    weather_data,
                    solar_metadata,
                    solar_data,
                    facade_id,
                    building_body,
                )
            )

            # Generate output filename based on original weather file name
            safe_facade = facade_id.replace("$", "_")
            safe_building = building_body.replace(" ", "_").replace("$", "_")
            output_filename = f"{weather_file_base}_{safe_facade}_{safe_building}.dat"
            output_file_path = output_path / output_filename

            # Save adjusted weather data
            self.save_weather_data(
                output_file_path, adjusted_metadata, adjusted_weather_data
            )

            facade_key = f"{facade_id}_{building_body}"
            output_files[facade_key] = str(output_file_path)

            self.logger.info(f"Saved adjusted weather data to: {output_file_path}")

        self.logger.info(f"Processing complete. Generated {len(output_files)} files.")
        return output_files

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

    def save_weather_data(
        self,
        file_path: Path,
        metadata: WeatherFileMetadata,
        weather_data: List[WeatherDataPoint],
    ) -> None:
        """
        Save adjusted weather data to a file in TRY format, preserving the exact original format.

        Args:
            file_path: Output file path
            metadata: Weather metadata with original lines
            weather_data: List of weather data points
        """
        with open(file_path, "w", encoding="latin1") as f:
            # Write original header lines to preserve exact format
            for header_line in metadata.original_header_lines:
                f.write(header_line)

            # Write data lines, preserving original format but with updated values
            if len(metadata.original_data_lines) == len(weather_data):
                # We have original lines - preserve their exact format
                for original_line, data_point in zip(
                    metadata.original_data_lines, weather_data
                ):
                    modified_line = data_point.to_original_format_line(original_line)
                    f.write(modified_line)
            else:
                # Fallback to standard format if original lines not available
                self.logger.warning(
                    "Original data lines not available, using standard format"
                )
                for point in weather_data:
                    f.write(point._format_standard_line())


class PreviewAdjustment:
    """Représente un ajustement de température qui sera appliqué."""

    def __init__(
        self,
        datetime_str: str,
        facade_id: str,
        building_body: str,
        original_temp: float,
        adjusted_temp: float,
        solar_irradiance: float,
        threshold: float,
    ):
        self.datetime_str = datetime_str
        self.facade_id = facade_id
        self.building_body = building_body
        self.original_temp = original_temp
        self.adjusted_temp = adjusted_temp
        self.solar_irradiance = solar_irradiance
        self.threshold = threshold


class PreviewResult(NamedTuple):
    """Résultat de la prévisualisation."""

    facade_combinations: List[Tuple[str, str]]
    total_adjustments: int
    adjustments_by_facade: Dict[str, int]
    sample_adjustments: List[PreviewAdjustment]
    parameters: Dict[str, Any]


def preview_weather_solar_processing(
    weather_file_path: str,
    solar_file_path: str,
    threshold: float,
    delta_t: float,
    max_sample_adjustments: int = 20,
) -> PreviewResult:
    """
    Prévisualise les conversions qui vont être appliquées sans générer les fichiers.

    Args:
        weather_file_path: Chemin vers le fichier météo
        solar_file_path: Chemin vers le fichier solaire HTML
        threshold: Seuil d'irradiance solaire en W/m²
        delta_t: Augmentation de température en °C
        max_sample_adjustments: Nombre max d'ajustements d'exemple à retourner

    Returns:
        PreviewResult contenant un résumé des conversions qui seront appliquées
    """
    logger.info("Starting preview of facade processing...")

    # Charger les données météo
    weather_metadata, weather_data = load_weather_data(weather_file_path)
    logger.info(f"Loaded {len(weather_data)} weather data points")

    # Charger les données solaires
    solar_metadata, solar_data = load_solar_irridance_data(solar_file_path)
    logger.info(f"Loaded {len(solar_data)} solar data points")

    # Obtenir les combinaisons façade/bâtiment
    processor = CoreProcessor()
    facade_combinations = processor._extract_facade_combinations(solar_metadata)
    logger.info(f"Found {len(facade_combinations)} facade combinations")

    # Analyser chaque combinaison de façade
    total_adjustments = 0
    adjustments_by_facade = {}
    sample_adjustments = []

    facade_processor = FacadeProcessor(threshold, delta_t)

    for facade_id, building_body in facade_combinations:
        logger.info(f"Previewing {facade_id} of {building_body}")

        # Trouver la colonne de façade spécifique
        facade_column = facade_processor._find_facade_column(
            solar_metadata, facade_id, building_body
        )
        if not facade_column:
            logger.warning(
                f"No solar data found for facade {facade_id} of {building_body}"
            )
            adjustments_by_facade[f"{facade_id}_{building_body}"] = 0
            continue

        # Créer la table de lookup solaire
        solar_lookup = facade_processor._create_solar_lookup(solar_data, facade_column)

        # Compter les ajustements pour cette façade
        facade_adjustments = 0
        facade_key = f"{facade_id}_{building_body}"

        for weather_point in weather_data:
            # Trouver la valeur d'irradiance solaire correspondante
            solar_irradiance = facade_processor._get_solar_irradiance_for_datetime(
                solar_lookup, weather_point
            )

            # Vérifier si un ajustement sera appliqué
            if solar_irradiance is not None and solar_irradiance > threshold:
                facade_adjustments += 1
                total_adjustments += 1

                # Ajouter à l'échantillon d'ajustements si pas encore plein
                if len(sample_adjustments) < max_sample_adjustments:
                    adjustment = PreviewAdjustment(
                        datetime_str=f"{weather_point.month:02d}-{weather_point.day:02d} {weather_point.hour:02d}:00",
                        facade_id=facade_id,
                        building_body=building_body,
                        original_temp=weather_point.temperature,
                        adjusted_temp=weather_point.temperature + delta_t,
                        solar_irradiance=solar_irradiance,
                        threshold=threshold,
                    )
                    sample_adjustments.append(adjustment)

        adjustments_by_facade[facade_key] = facade_adjustments
        logger.info(f"Facade {facade_key}: {facade_adjustments} adjustments")

    # Paramètres de traitement
    parameters = {
        "threshold": threshold,
        "delta_t": delta_t,
        "weather_file": weather_file_path,
        "solar_file": solar_file_path,
        "weather_data_points": len(weather_data),
        "solar_data_points": len(solar_data),
    }

    result = PreviewResult(
        facade_combinations=facade_combinations,
        total_adjustments=total_adjustments,
        adjustments_by_facade=adjustments_by_facade,
        sample_adjustments=sample_adjustments,
        parameters=parameters,
    )

    logger.info(f"Preview complete. Total adjustments: {total_adjustments}")
    return result


def process_weather_with_solar_data(
    weather_file_path: str,
    solar_file_path: str,
    threshold: float,
    delta_t: float,
    output_dir: str = "output",
) -> Dict[str, str]:
    """
    Main function to process weather data with solar irradiance adjustments.

    Args:
        weather_file_path: Path to the weather data file
        solar_file_path: Path to the solar irradiance HTML file
        threshold: Solar irradiance threshold in W/m²
        delta_t: Temperature increase in °C
        output_dir: Directory to save output files

    Returns:
        Dictionary mapping facade identifiers to output file paths
    """
    processor = CoreProcessor()
    return processor.process_all_facades(
        weather_file_path, solar_file_path, threshold, delta_t, output_dir
    )


# Example usage
if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(level=logging.INFO)

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
