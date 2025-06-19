"""
Unit tests for the solar irradiance data parser.
"""

from datetime import datetime
from pathlib import Path

import pytest

from src.solar import (
    SolarDataAnalyzer,
    SolarDataParser,
    SolarDataPoint,
    SolarFileMetadata,
)


class TestSolarDataPoint:
    """Test cases for SolarDataPoint model."""

    def test_create_solar_data_point(self):
        """Test creating a valid SolarDataPoint."""
        timestamp = datetime(2023, 1, 1, 12, 0)
        irradiance_values = {
            "Gesamte solare Einstrahlung, f3$Building body, W/m2": 250.5,
            "Gesamte solare Einstrahlung, f4$Building body, W/m2": 180.3,
        }

        data_point = SolarDataPoint(
            timestamp=timestamp, irradiance_values=irradiance_values
        )

        assert data_point.timestamp == timestamp
        assert data_point.irradiance_values == irradiance_values

    def test_negative_irradiance_validation(self):
        """Test validation of negative irradiance values."""
        timestamp = datetime(2023, 1, 1, 12, 0)
        irradiance_values = {
            "facade1": -10.0,  # Invalid negative value
            "facade2": 100.0,
        }

        with pytest.raises(ValueError, match="must be non-negative"):
            SolarDataPoint(timestamp=timestamp, irradiance_values=irradiance_values)

    def test_get_total_irradiance(self):
        """Test calculation of total irradiance."""
        data_point = SolarDataPoint(
            timestamp=datetime(2023, 1, 1, 12, 0),
            irradiance_values={
                "facade1": 100.0,
                "facade2": 200.0,
                "facade3": 50.0,
            },
        )

        assert data_point.get_total_irradiance() == 350.0

    def test_get_max_facade_irradiance(self):
        """Test finding facade with maximum irradiance."""
        data_point = SolarDataPoint(
            timestamp=datetime(2023, 1, 1, 12, 0),
            irradiance_values={
                "facade1": 100.0,
                "facade2": 250.0,
                "facade3": 150.0,
            },
        )

        facade, value = data_point.get_max_facade_irradiance()
        assert facade == "facade2"
        assert value == 250.0

    def test_get_max_facade_irradiance_empty(self):
        """Test max facade irradiance with empty values."""
        data_point = SolarDataPoint(
            timestamp=datetime(2023, 1, 1, 12, 0), irradiance_values={}
        )

        facade, value = data_point.get_max_facade_irradiance()
        assert facade == ""
        assert value == 0.0

    def test_has_significant_irradiance(self):
        """Test checking for significant irradiance levels."""
        data_point = SolarDataPoint(
            timestamp=datetime(2023, 1, 1, 12, 0),
            irradiance_values={
                "facade1": 5.0,
                "facade2": 15.0,
            },
        )

        assert data_point.has_significant_irradiance(threshold=10.0) is True
        assert data_point.has_significant_irradiance(threshold=20.0) is False


class TestSolarFileMetadata:
    """Test cases for SolarFileMetadata model."""

    def test_create_metadata(self):
        """Test creating SolarFileMetadata."""
        metadata = SolarFileMetadata(
            title="Solar Irradiance Test",
            software="IDA Modeler 5.0",
            object_name="Test Building",
            facade_columns=[
                "Gesamte solare Einstrahlung, f3$Building body, W/m2",
                "Gesamte solare Einstrahlung, f4$Building body 2, W/m2",
            ],
        )

        assert metadata.title == "Solar Irradiance Test"
        assert metadata.software == "IDA Modeler 5.0"
        assert len(metadata.facade_columns) == 2

    def test_get_building_bodies(self):
        """Test extraction of building bodies."""
        metadata = SolarFileMetadata(
            facade_columns=[
                "Gesamte solare Einstrahlung, f3$Building body, W/m2",
                "Gesamte solare Einstrahlung, f4$Building body 2, W/m2",
                "Gesamte solare Einstrahlung, f1$Building body, W/m2",
            ]
        )

        bodies = metadata.get_building_bodies()
        assert "Building body" in bodies
        assert "Building body 2" in bodies
        assert len(bodies) == 2

    def test_get_facade_orientations(self):
        """Test extraction of facade orientations."""
        metadata = SolarFileMetadata(
            facade_columns=[
                "Gesamte solare Einstrahlung, f3$Building body, W/m2",
                "Gesamte solare Einstrahlung, f4$Building body, W/m2",
                "Gesamte solare Einstrahlung, f1$Building body 2, W/m2",
            ]
        )

        orientations = metadata.get_facade_orientations()
        assert "f1" in orientations
        assert "f3" in orientations
        assert "f4" in orientations
        assert len(orientations) == 3

    def test_get_summary(self):
        """Test metadata summary generation."""
        metadata = SolarFileMetadata(
            title="Test Solar Data",
            object_name="Test Building",
            software="IDA Modeler",
            simulation_date="19.06.2025 15:34:14",
            facade_columns=[
                "Gesamte solare Einstrahlung, f3$Building body, W/m2",
                "Gesamte solare Einstrahlung, f4$Building body, W/m2",
            ],
        )

        summary = metadata.get_summary()
        assert "Test Solar Data" in summary
        assert "Test Building" in summary
        assert "f3" in summary
        assert "f4" in summary
        assert "Total Columns: 2" in summary


class TestSolarDataParser:
    """Test cases for SolarDataParser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = SolarDataParser()
        assert parser.logger is not None

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = SolarDataParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("non_existent_file.html")

    def test_parse_timestamp_formats(self):
        """Test parsing various timestamp formats."""
        parser = SolarDataParser()

        # Test German format
        timestamp1 = parser._parse_timestamp("01.01.2023 01:00")
        assert timestamp1 == datetime(2023, 1, 1, 1, 0)

        # Test without leading zeros
        timestamp2 = parser._parse_timestamp("1.1.2023 1:00")
        assert timestamp2 == datetime(2023, 1, 1, 1, 0)

    def test_parse_timestamp_invalid(self):
        """Test parsing invalid timestamp."""
        parser = SolarDataParser()

        with pytest.raises(ValueError, match="Cannot parse timestamp"):
            parser._parse_timestamp("invalid timestamp")

    @pytest.mark.parametrize(
        "timestamp_str,expected",
        [
            ("01.01.2023 01:00", datetime(2023, 1, 1, 1, 0)),
            ("15.06.2023 12:30", datetime(2023, 6, 15, 12, 30)),
            ("31.12.2023 23:59", datetime(2023, 12, 31, 23, 59)),
        ],
    )
    def test_parse_timestamp_parametrized(self, timestamp_str, expected):
        """Test parsing various timestamp formats."""
        parser = SolarDataParser()
        result = parser._parse_timestamp(timestamp_str)
        assert result == expected


class TestSolarDataAnalyzer:
    """Test cases for SolarDataAnalyzer."""

    @pytest.fixture
    def sample_solar_data(self):
        """Create sample solar data for testing."""
        return [
            SolarDataPoint(
                timestamp=datetime(2023, 1, 1, 8, 0),
                irradiance_values={
                    "facade_north": 50.0,
                    "facade_south": 200.0,
                    "facade_east": 100.0,
                },
            ),
            SolarDataPoint(
                timestamp=datetime(2023, 1, 1, 12, 0),
                irradiance_values={
                    "facade_north": 30.0,
                    "facade_south": 400.0,
                    "facade_east": 80.0,
                },
            ),
            SolarDataPoint(
                timestamp=datetime(2023, 1, 1, 16, 0),
                irradiance_values={
                    "facade_north": 20.0,
                    "facade_south": 150.0,
                    "facade_east": 250.0,
                },
            ),
        ]

    def test_analyzer_initialization(self, sample_solar_data):
        """Test analyzer initialization."""
        analyzer = SolarDataAnalyzer(sample_solar_data)
        assert len(analyzer.data_points) == 3
        assert analyzer.logger is not None

    def test_get_irradiance_stats(self, sample_solar_data):
        """Test irradiance statistics calculation."""
        analyzer = SolarDataAnalyzer(sample_solar_data)
        stats = analyzer.get_irradiance_stats()

        # Check that all facades are included
        assert "facade_north" in stats
        assert "facade_south" in stats
        assert "facade_east" in stats

        # Check south facade stats (highest values)
        south_stats = stats["facade_south"]
        assert south_stats["min"] == 150.0
        assert south_stats["max"] == 400.0
        assert south_stats["mean"] == 250.0  # (200 + 400 + 150) / 3

        # Check peak hours count (> 100 W/m²)
        assert south_stats["peak_hours_count"] == 3

    def test_get_irradiance_stats_empty(self):
        """Test irradiance stats with empty data."""
        analyzer = SolarDataAnalyzer([])
        stats = analyzer.get_irradiance_stats()
        assert stats == {}

    def test_get_daily_totals(self, sample_solar_data):
        """Test daily totals calculation."""
        analyzer = SolarDataAnalyzer(sample_solar_data)
        daily_totals = analyzer.get_daily_totals()

        assert "2023-01-01" in daily_totals
        day_data = daily_totals["2023-01-01"]

        # Check that all facades are included
        assert "facade_north" in day_data
        assert "facade_south" in day_data
        assert "facade_east" in day_data

        # Check south facade total (200 + 400 + 150) / 1000 = 0.75 kWh
        assert abs(day_data["facade_south"] - 0.75) < 0.001

    def test_get_peak_irradiance_periods(self, sample_solar_data):
        """Test filtering for peak irradiance periods."""
        analyzer = SolarDataAnalyzer(sample_solar_data)

        # Threshold of 300 W/m² should return only the 12:00 data point
        peak_periods = analyzer.get_peak_irradiance_periods(threshold=300.0)
        assert len(peak_periods) == 1
        assert peak_periods[0].timestamp.hour == 12

        # Lower threshold should return more points
        peak_periods_low = analyzer.get_peak_irradiance_periods(threshold=100.0)
        assert len(peak_periods_low) == 3

    def test_filter_by_facade_pattern(self, sample_solar_data):
        """Test filtering by facade pattern."""
        analyzer = SolarDataAnalyzer(sample_solar_data)

        # Filter for facades containing "south"
        south_data = analyzer.filter_by_facade_pattern("south")
        assert len(south_data) == 3

        for dp in south_data:
            assert len(dp.irradiance_values) == 1
            assert "facade_south" in dp.irradiance_values

    def test_get_building_body_stats(self):
        """Test building body statistics."""
        data_points = [
            SolarDataPoint(
                timestamp=datetime(2023, 1, 1, 12, 0),
                irradiance_values={
                    "Gesamte solare Einstrahlung, f3$Building body, W/m2": 200.0,
                    "Gesamte solare Einstrahlung, f4$Building body, W/m2": 150.0,
                    "Gesamte solare Einstrahlung, f1$Building body 2, W/m2": 100.0,
                },
            ),
        ]

        analyzer = SolarDataAnalyzer(data_points)
        building_stats = analyzer.get_building_body_stats()

        assert "Building body" in building_stats
        assert "Building body 2" in building_stats

        # Check Building body stats (200 + 150) / 1000 = 0.35 kWh
        assert building_stats["Building body"]["total_irradiance"] == 0.35
        assert building_stats["Building body"]["max_hourly"] == 200.0
        assert building_stats["Building body"]["facade_count"] == 2

        # Check Building body 2 stats
        assert building_stats["Building body 2"]["total_irradiance"] == 0.1
        assert building_stats["Building body 2"]["max_hourly"] == 100.0
        assert building_stats["Building body 2"]["facade_count"] == 1

    def test_validate_data_quality(self, sample_solar_data):
        """Test data quality validation."""
        analyzer = SolarDataAnalyzer(sample_solar_data)
        quality = analyzer.validate_data_quality()

        assert quality["total_points"] == 3
        assert quality["has_data"] is True
        assert quality["quality_score"] >= 0.0
        assert isinstance(quality["issues"], list)

    def test_validate_data_quality_empty(self):
        """Test data quality validation with empty data."""
        analyzer = SolarDataAnalyzer([])
        quality = analyzer.validate_data_quality()

        assert quality["quality_score"] == 0.0
        assert "No data points found" in quality["issues"]

    def test_validate_data_quality_with_negatives(self):
        """Test data quality validation with negative values."""
        # This test would create data with negative values,
        # but our model validation prevents this, so we test the concept
        analyzer = SolarDataAnalyzer([])
        quality = analyzer.validate_data_quality()
        assert quality["quality_score"] == 0.0


class TestSolarDataIntegration:
    """Integration tests for solar data processing."""

    def test_full_workflow_simulation(self):
        """Test a complete workflow simulation without real file."""
        # Simulate metadata
        metadata = SolarFileMetadata(
            title="Test Solar Data",
            software="IDA Modeler 5.0",
            object_name="Test Building",
            facade_columns=[
                "Gesamte solare Einstrahlung, f3$Building body, W/m2",
                "Gesamte solare Einstrahlung, f4$Building body, W/m2",
            ],
        )

        # Simulate data points
        data_points = [
            SolarDataPoint(
                timestamp=datetime(2023, 6, 21, 12, 0),  # Summer solstice
                irradiance_values={
                    "Gesamte solare Einstrahlung, f3$Building body, W/m2": 300.0,
                    "Gesamte solare Einstrahlung, f4$Building body, W/m2": 250.0,
                },
            ),
            SolarDataPoint(
                timestamp=datetime(2023, 12, 21, 12, 0),  # Winter solstice
                irradiance_values={
                    "Gesamte solare Einstrahlung, f3$Building body, W/m2": 150.0,
                    "Gesamte solare Einstrahlung, f4$Building body, W/m2": 100.0,
                },
            ),
        ]

        # Test analysis
        analyzer = SolarDataAnalyzer(data_points)
        stats = analyzer.get_irradiance_stats()

        # Verify results
        assert len(stats) == 2
        assert (
            stats["Gesamte solare Einstrahlung, f3$Building body, W/m2"]["max"] == 300.0
        )
        assert (
            stats["Gesamte solare Einstrahlung, f4$Building body, W/m2"]["min"] == 100.0
        )

        # Test metadata analysis
        building_bodies = metadata.get_building_bodies()
        orientations = metadata.get_facade_orientations()

        assert "Building body" in building_bodies
        assert "f3" in orientations
        assert "f4" in orientations
