"""
Integration tests for solar data parsing with real files.
"""

import time
from pathlib import Path

import pytest

from src.solar import SolarDataAnalyzer, SolarDataParser


class TestSolarIntegrationWithRealFile:
    """Integration tests using the real solar HTML file."""

    @pytest.fixture
    def solar_file_path(self):
        """Path to the test solar HTML file."""
        return Path("tests/data/Solare Einstrahlung auf die Fassade.html")

    def test_parse_real_solar_file(self, solar_file_path):
        """Test parsing the test solar irradiance HTML file."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        # Test metadata extraction
        assert metadata.title == "Solare Einstrahlung auf die Fassade"
        assert metadata.simulation_date == "19.06.2025 15:34:14 [59]"
        assert metadata.save_date == "19.06.2025 15:18:26"
        assert len(metadata.facade_columns) == 3

        # Test that facade columns follow expected pattern
        for column in metadata.facade_columns:
            assert "Gesamte solare Einstrahlung" in column
            assert "W/m2" in column
            assert "Building body" in column

        # Test data points
        assert len(data_points) == 8760  # We have 8760 data rows in test file

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
        """Test metadata analysis functionality."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        # Test building bodies extraction
        building_bodies = metadata.get_building_bodies()
        assert len(building_bodies) > 0
        assert all("Building body" in body for body in building_bodies)

        # Test facade orientations
        orientations = metadata.get_facade_orientations()
        assert len(orientations) > 0
        assert all(orient.startswith("f") for orient in orientations)

    def test_real_file_data_analysis(self, solar_file_path):
        """Test data analysis functionality."""
        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(solar_file_path))

        analyzer = SolarDataAnalyzer(data_points)

        # Test statistics calculation
        stats = analyzer.get_irradiance_stats()
        assert len(stats) == len(metadata.facade_columns)

        for facade, stat in stats.items():
            assert "min" in stat
            assert "max" in stat
            assert "mean" in stat
            assert "total_kwh" in stat
            assert stat["min"] >= 0
            assert stat["max"] >= stat["min"]

        # Test real data analysis
        assert analyzer.validate_data_quality()["has_data"] is True

    def test_lxml_parser_performance(self, solar_file_path):
        """Test lxml parser performance."""
        parser = SolarDataParser()
        start_time = time.time()
        metadata, data_points = parser.parse_file(str(solar_file_path))
        parse_time = time.time() - start_time

        print(f"\nParser Performance:")
        print(f"Parse time: {parse_time:.4f}s")
        print(f"Data points: {len(data_points)}")
        print(f"Facade columns: {len(metadata.facade_columns)}")

        # Verify reasonable performance
        assert parse_time < 1.0  # Should be very fast for small files
        assert len(data_points) > 0
        assert len(metadata.facade_columns) > 0

    def test_large_file_parsing_performance(self):
        """Test performance on large file if available."""
        large_file_path = Path("tests/data/Solare Einstrahlung auf die Fassade.html")

        if not large_file_path.exists():
            pytest.skip(
                "Large test file not available"
            )  # Test with different row limits to verify scalability
        row_limits = [100, 500, 1000]

        for max_rows in row_limits:
            parser = SolarDataParser(max_rows=max_rows)

            start_time = time.time()
            metadata, data_points = parser.parse_file(str(large_file_path))
            parse_time = time.time() - start_time

            print(f"\nLarge File Performance ({max_rows} rows):")
            print(f"File size: {large_file_path.stat().st_size / 1024 / 1024:.2f} MB")
            print(f"Parse time: {parse_time:.4f}s")
            print(f"Rows per second: {len(data_points) / parse_time:.0f}")
            print(f"Facade columns found: {len(metadata.facade_columns)}")

            # Verify reasonable performance (should be much faster than 1s per 1000 rows)
            assert parse_time < 1.0  # Should parse quickly
            assert len(data_points) <= max_rows
            assert len(metadata.facade_columns) > 0

            # Verify data quality
            analyzer = SolarDataAnalyzer(data_points)
            quality = analyzer.validate_data_quality()
            assert quality["has_data"] is True

    def test_parser_fallback_behavior(self):
        """Test that parser handles missing lxml gracefully."""
        # This test verifies the error message when lxml is not available
        # For now, since we require lxml, we just test normal operation

        small_file = Path("tests/data/solar_test_small.html")
        if not small_file.exists():
            pytest.skip("Test file not available")

        parser = SolarDataParser()
        metadata, data_points = parser.parse_file(str(small_file))

        assert len(data_points) > 0
        assert len(metadata.facade_columns) > 0

    def test_max_rows_limiting(self):
        """Test that max_rows parameter works correctly."""
        large_file_path = Path("tests/data/Solare Einstrahlung auf die Fassade.html")

        if not large_file_path.exists():
            pytest.skip("Large test file not available")

        # Test with small limit
        parser = SolarDataParser(max_rows=50)
        metadata, data_points = parser.parse_file(str(large_file_path))

        assert len(data_points) <= 50
        assert len(data_points) > 0  # Should have found some data

        # Test with larger limit
        parser = SolarDataParser(max_rows=200)
        metadata, data_points = parser.parse_file(str(large_file_path))

        assert len(data_points) <= 200
        assert len(data_points) >= 50  # Should be more than the previous test
