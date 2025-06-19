"""
Solar irradiance data parser for IDA Modeler HTML files.

This module provides functionality to parse HTML files containing solar irradiance data
exported from IDA Modeler, which includes hourly solar irradiance values for different
facade orientations of building bodies.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SolarDataPoint(BaseModel):
    """Represents a single hourly solar irradiance measurement for multiple facades."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    timestamp: datetime = Field(..., description="Date and time of measurement")
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
    software: str = Field(default="", description="Software name and version")
    license_info: str = Field(default="", description="License information")
    object_name: str = Field(default="", description="Object/project name")
    system_path: str = Field(default="", description="System file path")
    description: str = Field(default="", description="Project description")
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

    def get_summary(self) -> str:
        """Get formatted summary of metadata."""
        bodies = self.get_building_bodies()
        orientations = self.get_facade_orientations()

        return (
            f"Solar Irradiance Data Summary\n"
            f"Title: {self.title}\n"
            f"Object: {self.object_name}\n"
            f"Software: {self.software}\n"
            f"Simulation: {self.simulation_date}\n"
            f"Building Bodies: {', '.join(bodies)}\n"
            f"Facade Orientations: {', '.join(orientations)}\n"
            f"Total Columns: {len(self.facade_columns)}"
        )


class SolarDataParser:
    """Parser for IDA Modeler solar irradiance HTML files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(
        self, file_path: str
    ) -> tuple[SolarFileMetadata, List[SolarDataPoint]]:
        """
        Parse a solar irradiance HTML file.

        Args:
            file_path: Path to the HTML file

        Returns:
            Tuple containing metadata and list of data points

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Solar file not found: {file_path}")

        self.logger.info(f"Parsing solar irradiance file: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            soup = BeautifulSoup(content, "html.parser")
            metadata = self._parse_metadata(soup)
            data_points = self._parse_data_table(soup)

            self.logger.info(f"Successfully parsed {len(data_points)} data points")
            return metadata, data_points

        except Exception as e:
            self.logger.error(f"Error parsing solar file: {e}")
            raise ValueError(f"Failed to parse solar file: {e}")

    def _parse_metadata(self, soup: BeautifulSoup) -> SolarFileMetadata:
        """Extract metadata from HTML soup."""
        metadata = {}

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        # Extract metadata from header table
        header_table = soup.find("table", {"border": "0"})
        if header_table:
            rows = header_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)

                    if "Lizenz" in key:
                        metadata["license_info"] = value
                        if "Software" in key or "Dummy" in key:
                            metadata["software"] = key
                    elif "Objekt" in key:
                        metadata["object_name"] = value
                    elif "System" in key:
                        metadata["system_path"] = value
                    elif "Beschreibung" in key:
                        metadata["description"] = value
                    elif "Simuliert" in key:
                        metadata["simulation_date"] = value
                    elif "Gespeichert" in key:
                        metadata["save_date"] = value
                elif len(cells) == 1:
                    text = cells[0].get_text(strip=True)
                    if "Software" in text or "IDA" in text or "Dummy" in text:
                        metadata["software"] = text

        # Extract facade columns from data table header
        data_table = soup.find("table", class_="rep")
        if data_table and isinstance(data_table, Tag):
            metadata["facade_columns"] = self._extract_facade_columns(data_table)

        return SolarFileMetadata(**metadata)

    def _extract_facade_columns(self, table: Tag) -> List[str]:
        """Extract facade column names from table header."""
        columns = []

        # Look for header rows - find tr elements that contain td elements
        header_rows = []
        for row in table.find_all("tr"):
            if isinstance(row, Tag):
                # Check if this row contains column headers
                cells = row.find_all("td")
                if cells:
                    header_rows.append(row)

        # Take first few rows as potential headers
        for row in header_rows[:3]:  # Check first 3 rows for headers
            cells = row.find_all("td")
            for cell in cells:
                if isinstance(cell, Tag):
                    text = cell.get_text(strip=True)
                    # Look for solar irradiance patterns
                    if "Gesamte solare Einstrahlung" in text and "W/m2" in text:
                        columns.append(text)

        return columns

    def _parse_data_table(self, soup: BeautifulSoup) -> List[SolarDataPoint]:
        """Parse data table into SolarDataPoint objects."""
        data_points = []

        data_table = soup.find("table", class_="rep")
        if not data_table or not isinstance(data_table, Tag):
            raise ValueError("No data table found in HTML")

        # Get column headers
        facade_columns = self._extract_facade_columns(data_table)
        if not facade_columns:
            raise ValueError("No facade columns found in table")

        # Parse data rows - find all tr elements and filter for data rows
        all_rows = data_table.find_all("tr")
        data_rows = []

        # Skip header rows - look for rows with timestamp-like content
        for row in all_rows:
            if isinstance(row, Tag):
                cells = row.find_all("td")
                if cells and len(cells) > 1:
                    first_cell_text = cells[0].get_text(strip=True)
                    # Check if first cell looks like a timestamp
                    if re.search(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}", first_cell_text):
                        data_rows.append(row)

        for row_num, row in enumerate(data_rows, 1):
            try:
                cells = row.find_all("td")
                if len(cells) < 2:  # Need at least timestamp + 1 value
                    continue

                # Parse timestamp from first cell
                timestamp_text = cells[0].get_text(strip=True)
                timestamp = self._parse_timestamp(timestamp_text)

                # Parse irradiance values
                irradiance_values = {}
                for i, column in enumerate(facade_columns):
                    if i + 1 < len(cells):  # +1 because first cell is timestamp
                        value_text = cells[i + 1].get_text(strip=True)
                        try:
                            value = float(value_text)
                            irradiance_values[column] = value
                        except ValueError:
                            self.logger.warning(
                                f"Invalid irradiance value '{value_text}' in row {row_num}"
                            )
                            irradiance_values[column] = 0.0

                data_point = SolarDataPoint(
                    timestamp=timestamp, irradiance_values=irradiance_values
                )
                data_points.append(data_point)

            except Exception as e:
                self.logger.warning(f"Failed to parse row {row_num}: {e}")
                continue

        return data_points

    def _parse_timestamp(self, timestamp_text: str) -> datetime:
        """Parse timestamp from various formats."""
        # Common formats: "01.01.2023 01:00", "1.1.2023 1:00"
        try:
            # Try German format with dots
            return datetime.strptime(timestamp_text, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                # Try without leading zeros
                parts = timestamp_text.split()
                if len(parts) == 2:
                    date_part, time_part = parts
                    # Parse date part
                    day, month, year = date_part.split(".")
                    hour, minute = time_part.split(":")
                    return datetime(
                        int(year), int(month), int(day), int(hour), int(minute)
                    )
            except (ValueError, IndexError):
                pass

        raise ValueError(f"Cannot parse timestamp: {timestamp_text}")


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

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
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
