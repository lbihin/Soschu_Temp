"""
Weather data parser for TRY (Test Reference Year) files.

This module provides functionality to parse standardized German weather data files
in the TRY format, which contain hourly meteorological data for a full year.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from config import Config


class WeatherDataPoint(BaseModel):
    """Represents a single hourly weather measurement."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    # Location and time
    rechtswert: int = Field(..., description="Easting coordinate [m]")
    hochwert: int = Field(..., description="Northing coordinate [m]")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Day (1-31)")
    hour: int = Field(..., ge=1, le=24, description="Hour (1-24, MEZ)")

    # Meteorological parameters
    temperature: float = Field(..., description="Air temperature at 2m height [°C]")
    pressure: int = Field(..., description="Air pressure at site elevation [hPa]")
    wind_direction: int = Field(
        ...,
        ge=0,
        le=999,
        description="Wind direction at 10m height [degrees] (0-360, 999=calm)",
    )
    wind_speed: float = Field(..., ge=0, description="Wind speed at 10m height [m/s]")
    cloud_cover: int = Field(
        ..., ge=0, le=9, description="Cloud coverage [eighths] (0-8, 9=unknown)"
    )
    humidity_ratio: float = Field(
        ..., ge=0, description="Water vapor mixing ratio [g/kg]"
    )
    relative_humidity: int = Field(
        ..., ge=1, le=100, description="Relative humidity at 2m height [%] (1-100)"
    )

    # Solar radiation
    direct_solar: int = Field(
        ..., ge=0, description="Direct solar irradiance (horizontal) [W/m²]"
    )
    diffuse_solar: int = Field(
        ..., ge=0, description="Diffuse solar irradiance (horizontal) [W/m²]"
    )
    atmospheric_radiation: int = Field(
        ..., description="Atmospheric thermal radiation (horizontal) [W/m²]"
    )
    terrestrial_radiation: int = Field(
        ..., description="Terrestrial thermal radiation [W/m²] (negative)"
    )

    # Quality indicator
    quality_flag: int = Field(
        ..., ge=0, le=4, description="Quality bit for selection criteria (0-4)"
    )

    # Computed timestamp field - naive datetime with hours 1-24
    timestamp: datetime = Field(
        default_factory=lambda: datetime(2045, 1, 1, 0),  # Default will be overridden
        description="Computed naive datetime with hours 1-24 format",
    )

    @model_validator(mode="after")
    def set_timestamp(self):
        """Set timestamp after model creation using the month, day, and hour fields."""
        # Create naive datetime converting 1-24 hour format to datetime compatible format
        dt_hour = self.hour - 1  # Convert 1-24 to 0-23 for datetime compatibility

        # Create base datetime
        year = Config.get_year()  # Get year from configuration
        base_dt = datetime(year=year, month=self.month, day=self.day, hour=dt_hour)

        # Use object.__setattr__ to avoid triggering validation
        object.__setattr__(self, "timestamp", base_dt)
        return self

    @field_validator("wind_direction")
    @classmethod
    def validate_wind_direction(cls, v):
        """Validate wind direction is in valid range or calm indicator."""
        if not (0 <= v <= 360 or v == 999):
            raise ValueError("Wind direction must be 0-360 degrees or 999 for calm")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is in reasonable range."""
        if not -60 <= v <= 60:
            raise ValueError("Temperature must be between -60°C and 60°C")
        return v

    @field_validator("pressure")
    @classmethod
    def validate_pressure(cls, v):
        """Validate pressure is in reasonable range."""
        if not 800 <= v <= 1200:
            raise ValueError("Pressure must be between 800 and 1200 hPa")
        return v

    def to_datetime_for_gui(self) -> str:
        """
        Convert to formatted string for GUI display using original hour format (1-24).

        Returns:
            String in format "DD.MM.YYYY HH:MM" for display
        """
        if self.timestamp is None:
            return "Invalid timestamp"

        # Use the original hour field for display (1-24 format)
        # but get date from timestamp
        return f"{self.day:02d}.{self.month:02d} {self.hour:02d}:00"

    def to_datetime_for_file_output(self) -> datetime:
        """
        Convert to the format needed for TRY file output.

        Returns:
            Naive datetime maintaining the original 1-24 hour format
        """
        if self.timestamp is None:
            raise ValueError("Timestamp not set")
        return self.timestamp

    def total_solar_irradiance(self) -> int:
        """Calculate total solar irradiance (direct + diffuse)."""
        return self.direct_solar + self.diffuse_solar

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with computed fields."""
        data = self.model_dump()
        data["total_solar_irradiance"] = self.total_solar_irradiance()
        data["datetime"] = self.timestamp  # Naive datetime
        data["gui_datetime"] = self.to_datetime_for_gui()  # Formatted string for GUI
        return data

    def is_daylight_hour(self) -> bool:
        """Check if this data point represents daylight hours (6-18)."""
        return 6 <= self.hour <= 18

    def is_high_solar(self, threshold: float = 200.0) -> bool:
        """Check if solar irradiance exceeds threshold."""
        return self.total_solar_irradiance() > threshold

    def to_original_format_line(self, original_line: str) -> str:
        """
        Convert the weather data point back to its original format line,
        preserving the exact spacing and format of the original.

        Args:
            original_line: The original line from the file for this data point

        Returns:
            Formatted line with updated values but original format preserved
        """
        # For now, simply return the original line since we want exact preservation
        # This will be enhanced later to handle actual modifications
        return original_line

    def _format_standard_line(self) -> str:
        """Fallback method to format line in standard TRY format."""
        return (
            f"{self.rechtswert:7d} {self.hochwert:7d} "
            f"{self.month:2d} {self.day:2d} {self.hour:2d} "
            f"{self.temperature:5.1f} {self.pressure:4d} "
            f"{self.wind_direction:3d} {self.wind_speed:3.0f} "
            f"{self.cloud_cover:2d} {self.humidity_ratio:4.1f} "
            f"{self.relative_humidity:3d} {self.direct_solar:4d} "
            f"{self.diffuse_solar:4d} {self.atmospheric_radiation:4d} "
            f"{self.terrestrial_radiation:4d} {self.quality_flag:1d}\n"
        )


class WeatherFileMetadata(BaseModel):
    """Metadata extracted from the weather file header."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    coordinate_system: str = Field(default="", description="Coordinate system used")
    rechtswert: int = Field(default=0, description="Easting coordinate [m]")
    hochwert: int = Field(default=0, description="Northing coordinate [m]")
    elevation: int = Field(default=0, description="Elevation above sea level [m]")
    try_type: str = Field(default="", description="Type of TRY data")
    reference_period: str = Field(default="", description="Reference time period")
    data_basis_1: str = Field(default="", description="First data basis description")
    data_basis_2: str = Field(default="", description="Second data basis description")
    data_basis_3: str = Field(default="", description="Third data basis description")
    creation_date: str = Field(default="", description="Dataset creation date")

    # Original format preservation (no stripping to preserve exact format)
    original_header_lines: List[str] = Field(
        default_factory=list,
        description="Original header lines for exact format preservation",
        json_schema_extra={"preserve_whitespace": True},
    )
    original_data_lines: List[str] = Field(
        default_factory=list,
        description="Original data lines for exact format preservation",
        json_schema_extra={"preserve_whitespace": True},
    )


class WeatherDataParser:
    """Parser for TRY weather data files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(
        self, file_path: str
    ) -> tuple[WeatherFileMetadata, List[WeatherDataPoint]]:
        """
        Parse a TRY weather data file.

        Args:
            file_path: Path to the weather data file

        Returns:
            Tuple containing metadata and list of data points

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Weather file not found: {file_path}")

        self.logger.info(f"Parsing weather file: {file_path}")

        try:
            with open(path, "r", encoding="latin1") as file:
                lines = file.readlines()

            metadata = self._parse_metadata(lines)
            data_points = self._parse_data_lines(lines)

            # Store original lines for format preservation (bypass Pydantic stripping)
            header_lines = self._extract_header_lines(lines)
            data_lines = self._extract_data_lines(lines)

            # Use object.__setattr__ to bypass Pydantic validation that strips whitespace
            object.__setattr__(metadata, "original_header_lines", header_lines)
            object.__setattr__(metadata, "original_data_lines", data_lines)

            self.logger.info(f"Successfully parsed {len(data_points)} data points")
            return metadata, data_points

        except Exception as e:
            self.logger.error(f"Error parsing weather file: {e}")
            raise ValueError(f"Failed to parse weather file: {e}")

    def _parse_metadata(self, lines: List[str]) -> WeatherFileMetadata:
        """Extract metadata from file header."""
        metadata = {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith("***") or line.startswith("     RW"):
                continue

            # Stop at data section
            if line[0].isdigit():
                break

            # Parse metadata fields
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if "Koordinatensystem" in key:
                    metadata["coordinate_system"] = value
                elif "Rechtswert" in key:
                    match = re.search(r"\d+", value)
                    metadata["rechtswert"] = int(match.group()) if match else 0
                elif "Hochwert" in key:
                    match = re.search(r"\d+", value)
                    metadata["hochwert"] = int(match.group()) if match else 0
                elif "Hoehenlage" in key:
                    match = re.search(r"\d+", value)
                    metadata["elevation"] = int(match.group()) if match else 0
                elif "Art des TRY" in key:
                    metadata["try_type"] = value
                elif "Bezugszeitraum" in key:
                    metadata["reference_period"] = value
                elif "Datenbasis 1" in key:
                    metadata["data_basis_1"] = value
                elif "Datenbasis 2" in key:
                    metadata["data_basis_2"] = value
                elif "Datenbasis 3" in key:
                    metadata["data_basis_3"] = value
                elif "Erstellung" in key:
                    metadata["creation_date"] = value

        return WeatherFileMetadata(**metadata)

    def _parse_data_lines(self, lines: List[str]) -> List[WeatherDataPoint]:
        """Parse data lines into WeatherDataPoint objects."""
        data_points = []
        data_started = False

        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comment lines
            if line.startswith("***"):
                continue

            # Detect start of data section by header line
            if (
                "RW" in line
                and "HW" in line
                and "MM" in line
                and "DD" in line
                and "HH" in line
            ):
                data_started = True
                continue

            # Skip all non-data lines before data section starts
            if not data_started:
                continue

            # Parse data line - should start with digit
            if line and line[0].isdigit():
                try:
                    data_point = self._parse_data_line(line)
                    data_points.append(data_point)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse line {line_num}: {line[:50]}... Error: {e}"
                    )
                    continue

        return data_points

    def _parse_data_line(self, line: str) -> WeatherDataPoint:
        """Parse a single data line into a WeatherDataPoint."""
        # Split the line into fields based on the format specification
        # Format: (i7,1x,i7,1x,i2,1x,i2,1x,i2,1x,f5.1,1x,i4,1x,3i,1x,f4.1,1x,i1,1x,f4.1,1x,i3,1x,i4,1x,i4,1x,i3,1x,i4,2x,i1)

        parts = line.split()
        if len(parts) != 17:
            raise ValueError(f"Expected 17 fields, got {len(parts)}: {line}")

        try:
            return WeatherDataPoint(
                rechtswert=int(parts[0]),
                hochwert=int(parts[1]),
                month=int(parts[2]),
                day=int(parts[3]),
                hour=int(parts[4]),
                temperature=float(parts[5]),
                pressure=int(parts[6]),
                wind_direction=int(parts[7]),
                wind_speed=float(parts[8]),
                cloud_cover=int(parts[9]),
                humidity_ratio=float(parts[10]),
                relative_humidity=int(parts[11]),
                direct_solar=int(parts[12]),
                diffuse_solar=int(parts[13]),
                atmospheric_radiation=int(parts[14]),
                terrestrial_radiation=int(parts[15]),
                quality_flag=int(parts[16]),
            )
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse data fields: {e}")

    def _extract_header_lines(self, lines: List[str]) -> List[str]:
        """Extract header lines from the file, including everything before data starts."""
        header_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if this is a data line (starts with digit)
            if stripped and stripped[0].isdigit():
                break

            # Include this line in header
            header_lines.append(line)

            # Also check if the next line after this one is a data line
            # This ensures we capture separator lines like "*** "
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if next_stripped and next_stripped[0].isdigit():
                    # This current line is the last header line before data
                    break

        return header_lines

    def _extract_data_lines(self, lines: List[str]) -> List[str]:
        """Extract data lines from the file."""
        data_lines = []
        data_started = False

        for line in lines:
            stripped = line.strip()

            # Detect start of data section by header line
            if (
                "RW" in stripped
                and "HW" in stripped
                and "MM" in stripped
                and "DD" in stripped
                and "HH" in stripped
            ):
                data_started = True
                continue

            # Collect data lines (start with digit)
            if data_started and stripped and stripped[0].isdigit():
                data_lines.append(line)

        return data_lines


def load_weather_data(
    file_path: str,
) -> tuple[WeatherFileMetadata, List[WeatherDataPoint]]:
    """
    Convenience function to load and analyze weather data.

    Args:
        file_path: Path to the weather data file

    Returns:
        Tuple containing metadata and data points instance
    """
    parser = WeatherDataParser()
    metadata, data_points = parser.parse_file(file_path)
    return metadata, data_points


class WeatherDataAnalyzer:
    """Analyzer for weather data with common calculations."""

    def __init__(self, data_points: List[WeatherDataPoint]):
        self.data_points = data_points
        self.logger = logging.getLogger(__name__)

    def get_temperature_stats(self) -> Dict[str, float]:
        """Calculate temperature statistics."""
        temps = [dp.temperature for dp in self.data_points]
        return {
            "min": min(temps),
            "max": max(temps),
            "mean": sum(temps) / len(temps),
            "count": len(temps),
        }

    def get_solar_radiation_stats(self) -> Dict[str, float]:
        """Calculate solar radiation statistics."""
        total_solar = [dp.total_solar_irradiance() for dp in self.data_points]
        direct_solar = [dp.direct_solar for dp in self.data_points]
        diffuse_solar = [dp.diffuse_solar for dp in self.data_points]

        return {
            "total_max": max(total_solar),
            "total_mean": sum(total_solar) / len(total_solar),
            "direct_max": max(direct_solar),
            "direct_mean": sum(direct_solar) / len(direct_solar),
            "diffuse_max": max(diffuse_solar),
            "diffuse_mean": sum(diffuse_solar) / len(diffuse_solar),
            "total_annual_kwh_m2": sum(total_solar) / 1000,  # Convert W·h to kWh
        }

    def get_wind_stats(self) -> Dict[str, float]:
        """Calculate wind statistics."""
        wind_speeds = [dp.wind_speed for dp in self.data_points]
        return {
            "max_speed": max(wind_speeds),
            "mean_speed": sum(wind_speeds) / len(wind_speeds),
            "count": len(wind_speeds),
        }

    def filter_by_month(self, month: int) -> List[WeatherDataPoint]:
        """Filter data points by month."""
        return [dp for dp in self.data_points if dp.month == month]

    def filter_by_hour_range(
        self, start_hour: int, end_hour: int
    ) -> List[WeatherDataPoint]:
        """Filter data points by hour range (inclusive)."""
        return [dp for dp in self.data_points if start_hour <= dp.hour <= end_hour]

    def get_daylight_hours_data(self) -> List[WeatherDataPoint]:
        """Get data points for typical daylight hours (6-18)."""
        return self.filter_by_hour_range(6, 18)

    def export_to_json(self, file_path: str) -> None:
        """Export all data points to JSON file."""
        with open(file_path, "w") as f:
            data = [dp.model_dump() for dp in self.data_points]
            import json

            json.dump(data, f, indent=2, default=str)

    def get_high_solar_periods(
        self, threshold: float = 200.0
    ) -> List[WeatherDataPoint]:
        """Get data points where solar irradiance exceeds threshold."""
        return [dp for dp in self.data_points if dp.is_high_solar(threshold)]

    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality and return summary."""
        issues = []
        total_points = len(self.data_points)

        # Check for missing hours (should be 8760 for full year)
        if total_points != 8760:
            issues.append(f"Expected 8760 data points, got {total_points}")

        # Check for unreasonable values
        extreme_temps = [
            dp for dp in self.data_points if dp.temperature < -50 or dp.temperature > 50
        ]
        if extreme_temps:
            issues.append(
                f"Found {len(extreme_temps)} data points with extreme temperatures"
            )

        # Check for calm wind periods (999 = calm)
        calm_periods = [dp for dp in self.data_points if dp.wind_direction == 999]

        return {
            "total_points": total_points,
            "issues": issues,
            "calm_wind_hours": len(calm_periods),
            "extreme_temperature_hours": len(extreme_temps),
            "data_quality": "Good" if not issues else "Issues detected",
        }
