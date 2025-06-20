"""
Solar irradiance data parser for IDA Modeler HTML files.

This module provides functionality to parse HTML files containing solar irradiance data
exported from IDA Modeler, which includes hourly solar irradiance values for different
facade orientations of building bodies.

Performance optimized with lxml for fast parsing of large HTML files.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from lxml import html as lxml_html
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SolarDataPoint(BaseModel):
    """Represents a single hourly solar irradiance measurement for multiple facades."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    timestamp: datetime = Field(
        ..., description="Naive datetime with hours 1-24 format"
    )
    irradiance_values: Dict[str, float] = Field(
        default_factory=dict,
        description="Solar irradiance values for each facade [W/m²]",
    )

    @field_validator("irradiance_values")
    @classmethod
    def validate_irradiance_values(cls, v):
        """Validate that all irradiance values are non-negative."""
        for facade, value in v.items():
            if value < 0:
                raise ValueError(f"Irradiance value for {facade} must be non-negative")
        return v

    def to_datetime_for_gui(self) -> str:
        """
        Convert to formatted string for GUI display.

        Returns:
            String in format "DD.MM.YYYY HH:MM" for display using 1-24 hour format
        """
        # Convert 0-23 hour format to 1-24 for consistency
        display_hour = 24 if self.timestamp.hour == 0 else self.timestamp.hour
        # If hour was 0 (midnight), show as previous day hour 24
        if self.timestamp.hour == 0:
            prev_day = self.timestamp - timedelta(days=1)
            return f"{prev_day.day:02d}.{prev_day.month:02d}.{prev_day.year} 24:00"
        else:
            return f"{self.timestamp.day:02d}.{self.timestamp.month:02d}.{self.timestamp.year} {display_hour:02d}:00"

    def get_hour_24_format(self) -> int:
        """
        Get hour in 1-24 format for consistency with weather data.

        Returns:
            Hour in 1-24 format (midnight becomes 24 of previous day)
        """
        return 24 if self.timestamp.hour == 0 else self.timestamp.hour

    def get_total_irradiance(self) -> float:
        """Calculate total irradiance across all facades."""
        return sum(self.irradiance_values.values())

    def get_max_facade_irradiance(self) -> tuple[str, float]:
        """Get the facade with maximum irradiance and its value."""
        if not self.irradiance_values:
            return "", 0.0
        facade = max(
            self.irradiance_values.keys(), key=lambda k: self.irradiance_values[k]
        )
        return facade, self.irradiance_values[facade]

    def has_significant_irradiance(self, threshold: float = 10.0) -> bool:
        """Check if any facade has irradiance above threshold."""
        return any(value > threshold for value in self.irradiance_values.values())


class SolarFileMetadata(BaseModel):
    """Metadata extracted from the solar irradiance HTML file."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    title: str = Field(default="", description="Report title")
    system_path: str = Field(default="", description="System file path")
    simulation_date: str = Field(default="", description="Simulation date")
    save_date: str = Field(default="", description="File save date")
    facade_columns: List[str] = Field(
        default_factory=list, description="List of facade column identifiers"
    )

    def get_building_bodies(self) -> List[str]:
        """Extract unique building body identifiers from facade columns."""
        bodies = set()
        for column in self.facade_columns:
            # Extract building body from patterns like "f3$Building body" or "f3$Building body 2"
            match = re.search(r"Building body(?:\s+(\d+))?", column)
            if match:
                number = match.group(1)
                if number:
                    bodies.add(f"Building body {number}")
                else:
                    bodies.add("Building body")
        return sorted(list(bodies))

    def get_facade_orientations(self) -> List[str]:
        """Extract facade orientations (f1, f2, f3, f4, etc.) from columns."""
        orientations = set()
        for column in self.facade_columns:
            # Extract facade orientation like "f3"
            match = re.search(r"(f\d+)", column)
            if match:
                orientations.add(match.group(1))
        return sorted(list(orientations))


class SolarDataParser:
    """High-performance parser for IDA Modeler solar irradiance HTML files using lxml."""

    def __init__(self, max_rows: Optional[int] = None):
        """
        Initialize the parser.

        Args:
            max_rows: Maximum number of data rows to parse (None for all)
        """
        self.logger = logging.getLogger(__name__)
        self.max_rows = max_rows

    def parse_file(
        self, file_path: str
    ) -> tuple[SolarFileMetadata, List[SolarDataPoint]]:
        """
        Parse a solar irradiance HTML file using lxml for optimal performance.

        Args:
            file_path: Path to the HTML file

        Returns:
            Tuple containing metadata and list of data points

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
            ImportError: If lxml is not available
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Solar file not found: {file_path}")

        self.logger.info(f"Parsing solar irradiance file: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as file:
                tree = lxml_html.parse(file)

            metadata = self._parse_metadata(tree)
            data_points = self._parse_data_table(tree, metadata.facade_columns)

            self.logger.info(f"Successfully parsed {len(data_points)} data points")
            return metadata, data_points

        except Exception as e:
            self.logger.error(f"Error parsing solar file: {e}")
            raise ValueError(f"Failed to parse solar file: {e}")

    def _parse_metadata(self, tree) -> SolarFileMetadata:
        """Extract metadata using lxml XPath."""
        metadata = {}

        # Extract title
        title_elements = tree.xpath("//title/text()")
        if title_elements:
            metadata["title"] = title_elements[0].strip()

        # Extract metadata from header table (table with border="0")
        header_rows = tree.xpath('//table[@border="0"]//tr')

        for row in header_rows:
            cells = row.xpath("./td/text()")

            # Skip the row with 'Software' header
            if len(cells) < 2:
                continue

            key = cells[0].strip()
            value = cells[1].strip()

            if "System" in key:
                metadata["system_path"] = value
            elif "Simuliert" in key:
                metadata["simulation_date"] = value
            elif "Gespeichert" in key:
                metadata["save_date"] = value

        # Extract facade columns from data table header
        metadata["facade_columns"] = self._extract_facade_columns(tree)

        return SolarFileMetadata(**metadata)

    def _extract_facade_columns(self, tree) -> List[str]:
        """Extract facade column names using XPath."""
        columns = []

        # Look for cells in the data table that contain solar irradiance headers
        xpath_patterns = [
            '//table[@class="rep"]//td[contains(text(), "Gesamte solare Einstrahlung") and contains(text(), "W/m2")]/text()',
            '//table[@class="rep"]//td[contains(text(), "Gesamte solare Einstrahlung")]/text()',
        ]

        for pattern in xpath_patterns:
            headers = tree.xpath(pattern)
            for header in headers:
                header_text = header.strip()
                if (
                    "Gesamte solare Einstrahlung" in header_text
                    and "W/m2" in header_text
                ):
                    columns.append(header_text)

            if columns:  # If we found headers, stop trying other patterns
                break

        return columns

    def _parse_data_table(
        self, tree, facade_columns: List[str]
    ) -> List[SolarDataPoint]:
        """Parse data table using lxml XPath - optimized for large tables."""
        data_points = []

        if not facade_columns:
            self.logger.warning("No facade columns found, trying to detect from data")
            facade_columns = self._detect_columns_from_data(tree)

        if not facade_columns:
            raise ValueError("No facade columns found in table")

        # Find data rows that contain timestamp patterns (dd.mm.yyyy hh:mm)
        timestamp_pattern = r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}"
        data_rows = tree.xpath('//table[@class="rep"]//tr')

        row_count = 0
        for row in data_rows:
            # Get all cell text content from this row
            cells = row.xpath("./td/text()")

            if not cells or len(cells) < 2:
                continue

            # Check if first cell contains a timestamp
            first_cell = cells[0].strip()
            if not re.search(timestamp_pattern, first_cell):
                continue

            try:
                # Parse timestamp
                timestamp = self._parse_timestamp(first_cell)

                # Parse irradiance values
                irradiance_values = {}
                for i, column in enumerate(facade_columns):
                    if i + 1 < len(cells):  # +1 because first cell is timestamp
                        value_text = cells[i + 1].strip()
                        try:
                            value = float(value_text)
                            irradiance_values[column] = value
                        except ValueError:
                            self.logger.warning(
                                f"Invalid irradiance value '{value_text}' in row {row_count + 1}"
                            )
                            irradiance_values[column] = 0.0

                data_point = SolarDataPoint(
                    timestamp=timestamp, irradiance_values=irradiance_values
                )
                data_points.append(data_point)
                row_count += 1

                # Respect max_rows limit
                if self.max_rows and row_count >= self.max_rows:
                    self.logger.info(f"Reached max_rows limit: {self.max_rows}")
                    break

                # Log progress for large files
                if row_count % 5000 == 0:
                    self.logger.info(f"Parsed {row_count} data rows...")

            except Exception as e:
                self.logger.warning(f"Failed to parse row {row_count + 1}: {e}")
                continue

        # IDA workaround: IDA files do not provide a data point for the first hour (00:00)
        # to overcome this, we duplicate the data point of the first hour (01:00) to 00:00
        data_points = self._apply_ida_workaround(data_points)

        return data_points

    def _apply_ida_workaround(
        self, data_points: List[SolarDataPoint]
    ) -> List[SolarDataPoint]:
        """
        Apply IDA workaround for missing 00:00 hour data.

        IDA files do not provide a data point for the first hour (00:00).
        To overcome this, we duplicate the data point of the first hour (01:00) to 00:00.

        Args:
            data_points: List of parsed solar data points

        Returns:
            List of data points with 00:00 hour added if necessary
        """
        if not data_points:
            return data_points

        # Check if we need to apply the workaround
        first_dp = data_points[0]
        if first_dp.timestamp.hour != 1:
            # No workaround needed - either starts at 00:00 or some other hour
            return data_points

        self.logger.debug(
            f"Applying IDA workaround: duplicating {first_dp.timestamp} data to 00:00"
        )

        # Create 00:00 data point based on 01:00 data
        zero_hour_dp = SolarDataPoint(
            timestamp=datetime(
                year=first_dp.timestamp.year,
                month=first_dp.timestamp.month,
                day=first_dp.timestamp.day,
                hour=0,
                minute=0,
            ),
            irradiance_values=first_dp.irradiance_values.copy(),
        )

        # Insert at the beginning
        result = [zero_hour_dp] + data_points

        self.logger.debug(
            f"IDA workaround applied: added 00:00 data point with {len(zero_hour_dp.irradiance_values)} facade values"
        )

        return result

    def _detect_columns_from_data(self, tree) -> List[str]:
        """Try to detect column structure from data rows when headers are not found."""
        timestamp_pattern = r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}"
        data_rows = tree.xpath('//table[@class="rep"]//tr')

        for row in data_rows:
            cells = row.xpath("./td/text()")
            if len(cells) >= 2:
                first_cell = cells[0].strip()
                if re.search(timestamp_pattern, first_cell):
                    # Generate column names based on count
                    column_count = len(cells) - 1  # Exclude timestamp column
                    return [f"facade_column_{i+1}" for i in range(column_count)]

        return []

    def _parse_timestamp(self, timestamp_text: str) -> datetime:
        """
        Parse timestamp from various formats and convert to standardized format.

        Solar data typically uses 0-23 hours. We convert to datetime maintaining
        the actual time but add a method to get the 1-24 equivalent when needed.
        """
        parsed_dt = None

        try:
            # Try German format with dots
            parsed_dt = datetime.strptime(timestamp_text, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                # Try without leading zeros
                parts = timestamp_text.split()
                if len(parts) == 2:
                    date_part, time_part = parts
                    day, month, year = date_part.split(".")
                    hour, minute = time_part.split(":")
                    parsed_dt = datetime(
                        int(year), int(month), int(day), int(hour), int(minute)
                    )
            except (ValueError, IndexError):
                pass

        if parsed_dt is None:
            raise ValueError(f"Cannot parse timestamp: {timestamp_text}")

        return parsed_dt


def load_solar_irridance_data(
    solar_file_path: str,
) -> tuple[SolarFileMetadata, List["SolarDataPoint"]]:
    """Load solar irradiance data points from a file."""
    parser = SolarDataParser()
    metadata, data_points = parser.parse_file(solar_file_path)

    if not data_points:
        raise ValueError("No data points found in the file")

    return metadata, data_points


class SolarDataAnalyzer:
    """Analyzer for solar irradiance data with common calculations."""

    def __init__(self, data_points: List[SolarDataPoint]):
        self.data_points = data_points
        self.logger = logging.getLogger(__name__)

    def get_irradiance_stats(self) -> Dict[str, Any]:
        """Calculate irradiance statistics for all facades."""
        if not self.data_points:
            return {}

        # Get all facade columns
        all_facades = set()
        for dp in self.data_points:
            all_facades.update(dp.irradiance_values.keys())

        stats = {}
        for facade in all_facades:
            values = [dp.irradiance_values.get(facade, 0.0) for dp in self.data_points]

            stats[facade] = {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "total_kwh": sum(values) / 1000,  # Convert W·h to kWh
                "peak_hours_count": sum(1 for v in values if v > 100),
            }

        return stats

    def get_daily_totals(self) -> Dict[str, Dict[str, float]]:
        """Calculate daily irradiance totals for each facade."""
        daily_totals = {}

        for dp in self.data_points:
            date_key = dp.timestamp.strftime("%Y-%m-%d")

            if date_key not in daily_totals:
                daily_totals[date_key] = {}

            for facade, value in dp.irradiance_values.items():
                if facade not in daily_totals[date_key]:
                    daily_totals[date_key][facade] = 0.0
                daily_totals[date_key][facade] += value / 1000  # Convert to kWh

        return daily_totals

    def get_peak_irradiance_periods(
        self, threshold: float = 200.0
    ) -> List[SolarDataPoint]:
        """Get data points where any facade exceeds irradiance threshold."""
        return [
            dp
            for dp in self.data_points
            if any(value > threshold for value in dp.irradiance_values.values())
        ]

    def filter_by_facade_pattern(self, pattern: str) -> List[SolarDataPoint]:
        """Filter data points to include only facades matching pattern."""
        filtered_points = []

        for dp in self.data_points:
            filtered_values = {
                facade: value
                for facade, value in dp.irradiance_values.items()
                if pattern in facade
            }

            if filtered_values:
                filtered_point = SolarDataPoint(
                    timestamp=dp.timestamp, irradiance_values=filtered_values
                )
                filtered_points.append(filtered_point)

        return filtered_points

    def get_building_body_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate statistics grouped by building body."""
        building_stats = {}

        # Group facades by building body
        for dp in self.data_points:
            for facade, value in dp.irradiance_values.items():
                # Extract building body identifier
                match = re.search(r"Building body(?:\s+(\d+))?", facade)
                if match:
                    body_name = match.group(0)

                    if body_name not in building_stats:
                        building_stats[body_name] = {
                            "total_irradiance": 0.0,
                            "max_hourly": 0.0,
                            "facade_count": 0,
                        }

                    building_stats[body_name]["total_irradiance"] += value / 1000
                    building_stats[body_name]["max_hourly"] = max(
                        building_stats[body_name]["max_hourly"], value
                    )

        # Count facades per building body
        facade_counts = {}
        if self.data_points:
            for facade in self.data_points[0].irradiance_values.keys():
                match = re.search(r"Building body(?:\s+(\d+))?", facade)
                if match:
                    body_name = match.group(0)
                    facade_counts[body_name] = facade_counts.get(body_name, 0) + 1

        for body_name in building_stats:
            building_stats[body_name]["facade_count"] = facade_counts.get(body_name, 0)

        return building_stats

    def export_to_csv(self, file_path: str) -> None:
        """Export data to CSV format."""
        import csv
        from pathlib import Path

        # Create directory if it doesn't exist
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            if not self.data_points:
                return

            # Get all facade columns
            all_facades = set()
            for dp in self.data_points:
                all_facades.update(dp.irradiance_values.keys())
            all_facades = sorted(list(all_facades))

            # Write CSV
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

            # Header
            header = ["Timestamp"] + all_facades
            writer.writerow(header)

            # Data rows
            for dp in self.data_points:
                row = [dp.timestamp.strftime("%Y-%m-%d %H:%M")]
                for facade in all_facades:
                    row.append(str(dp.irradiance_values.get(facade, 0.0)))
                writer.writerow(row)

    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality and return summary."""
        issues = []
        total_points = len(self.data_points)

        if total_points == 0:
            return {"issues": ["No data points found"], "quality_score": 0.0}

        # Check for missing timestamps (gaps)
        if total_points > 1:
            sorted_points = sorted(self.data_points, key=lambda x: x.timestamp)
            gaps = []
            for i in range(1, len(sorted_points)):
                time_diff = sorted_points[i].timestamp - sorted_points[i - 1].timestamp
                if time_diff.total_seconds() > 3600:  # More than 1 hour gap
                    gaps.append(
                        f"Gap from {sorted_points[i-1].timestamp} to {sorted_points[i].timestamp}"
                    )

            if gaps:
                issues.extend(gaps[:5])  # Limit to first 5 gaps

        # Check for negative values
        negative_count = 0
        for dp in self.data_points:
            for value in dp.irradiance_values.values():
                if value < 0:
                    negative_count += 1

        if negative_count > 0:
            issues.append(f"Found {negative_count} negative irradiance values")

        # Check for unreasonably high values (> 1500 W/m²)
        extreme_count = 0
        for dp in self.data_points:
            for value in dp.irradiance_values.values():
                if value > 1500:
                    extreme_count += 1

        if extreme_count > 0:
            issues.append(
                f"Found {extreme_count} extremely high irradiance values (>1500 W/m²)"
            )

        # Calculate quality score
        quality_score = max(0.0, 1.0 - len(issues) * 0.1)

        return {
            "total_points": total_points,
            "issues": issues,
            "quality_score": quality_score,
            "has_data": total_points > 0,
        }
