"""
Integration tests for solar data parsing with real files.
"""

from pathlib import Path

import pytest

from src.solar import SolarDataAnalyzer, SolarDataParser


class TestSolarIntegrationWithRealFile:
    """Integration tests using the real solar HTML file."""

    @pytest.fixture
    def solar_file_path(self):
        """Path to the test solar HTML file."""
        return Path("tests/data/solar_test_small.html")

    def test_parse_real_solar_file(self, solar_file_path):
        """Test parsing the test solar irradiance HTML file."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        # Test metadata extraction
        assert metadata.title == "Solare Einstrahlung auf die Fassade"
        assert metadata.object_name == "Solare Einstrahlung auf die Fassade"
        assert len(metadata.facade_columns) == 3

        # Test that facade columns follow expected pattern
        for column in metadata.facade_columns:
            assert "Gesamte solare Einstrahlung" in column
            assert "W/m2" in column
            assert "Building body" in column

        # Test data points
        assert len(data_points) == 6  # We have 6 data rows in test file

        # Check first data point structure
        first_point = data_points[0]
        assert first_point.timestamp is not None
        assert isinstance(first_point.irradiance_values, dict)
        assert len(first_point.irradiance_values) == len(metadata.facade_columns)

        # All irradiance values should be non-negative
        for dp in data_points:
            for value in dp.irradiance_values.values():
                assert value >= 0

    def test_real_file_metadata_analysis(self, solar_file_path):
        """Test metadata analysis on test file."""
        parser = SolarDataParser()
        metadata, _ = parser.parse_file(str(solar_file_path))

        # Test building body extraction
        building_bodies = metadata.get_building_bodies()
        assert len(building_bodies) == 1  # Only "Building body" in our test file
        assert "Building body" in building_bodies

        # Test facade orientation extraction
        orientations = metadata.get_facade_orientations()
        assert len(orientations) == 3  # f2, f3, f4
        assert "f2" in orientations
        assert "f3" in orientations
        assert "f4" in orientations

        # Test summary generation
        summary = metadata.get_summary()
        assert "Solar Irradiance Data Summary" in summary
        assert len(summary) > 50  # Should be a meaningful summary

    def test_real_file_data_analysis(self, solar_file_path):
        """Test data analysis on test file."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        analyzer = SolarDataAnalyzer(data_points)

        # Test irradiance statistics
        stats = analyzer.get_irradiance_stats()
        assert len(stats) == len(metadata.facade_columns)

        for facade, facade_stats in stats.items():
            assert "min" in facade_stats
            assert "max" in facade_stats
            assert "mean" in facade_stats
            assert facade_stats["min"] >= 0
            assert facade_stats["max"] >= facade_stats["min"]

        # Test daily totals calculation
        daily_totals = analyzer.get_daily_totals()
        assert len(daily_totals) == 1  # Only one day in test file
        assert "2023-01-01" in daily_totals

        # Test peak irradiance periods
        peak_periods = analyzer.get_peak_irradiance_periods(threshold=100.0)
        assert len(peak_periods) >= 2  # 12:00 and 16:00 should exceed 100 W/m²

        # Test building body statistics
        building_stats = analyzer.get_building_body_stats()
        assert len(building_stats) == 1  # Only one building body
        assert "Building body" in building_stats

    def test_real_file_data_quality(self, solar_file_path):
        """Test data quality validation on test file."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        analyzer = SolarDataAnalyzer(data_points)
        quality = analyzer.validate_data_quality()

        assert quality["total_points"] == 6
        assert quality["has_data"] is True
        assert 0.0 <= quality["quality_score"] <= 1.0

        # Check that we don't have major data quality issues
        issues = quality["issues"]
        # Should not have many negative values in real solar data
        negative_issues = [issue for issue in issues if "negative" in issue.lower()]
        assert len(negative_issues) == 0  # Solar irradiance should not be negative

    def test_real_file_export_functionality(self, solar_file_path, tmp_path):
        """Test export functionality with test file."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        analyzer = SolarDataAnalyzer(data_points)

        # Test CSV export
        csv_path = tmp_path / "solar_export.csv"
        analyzer.export_to_csv(str(csv_path))

        assert csv_path.exists()
        assert csv_path.stat().st_size > 0

        # Read back the CSV to verify format
        import csv

        with open(csv_path, "r", encoding="utf-8", newline="") as csvfile:
            reader = csv.reader(csvfile)
            lines = list(reader)

        assert len(lines) == 7  # Header + 6 data rows

        # Check header format
        header = lines[0]
        assert header[0] == "Timestamp"
        assert len(header) == len(metadata.facade_columns) + 1  # +1 for timestamp

    def test_real_file_performance(self, solar_file_path):
        """Test parsing performance on test file."""
        import time

        parser = SolarDataParser()

        start_time = time.time()
        metadata, data_points = parser.parse_file(str(solar_file_path))
        parse_time = time.time() - start_time

        # Parsing should be very fast for small test file (< 1 second)
        assert parse_time < 1.0, f"Parsing took {parse_time:.2f} seconds, too slow"

        # Analysis should also be fast
        start_time = time.time()
        analyzer = SolarDataAnalyzer(data_points)
        stats = analyzer.get_irradiance_stats()
        analysis_time = time.time() - start_time

        assert (
            analysis_time < 0.5
        ), f"Analysis took {analysis_time:.2f} seconds, too slow"
        assert len(stats) == 3  # Three facades in test file
