"""
Tests for the core functionality of the Soschu Temperature tool.
"""

import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core import CoreProcessor, FacadeProcessor, process_weather_with_solar_data


@pytest.fixture
def facade_processor():
    """Create a facade processor for testing."""
    return FacadeProcessor(threshold=200.0, delta_t=7.0)


@pytest.fixture
def core_processor():
    """Create a core processor for testing."""
    return CoreProcessor()


@pytest.fixture
def weather_file_path():
    """Path to the test weather data file."""
    return Path("tests/data/TRY2045_488284093163_Jahr.dat")


@pytest.fixture
def solar_file_path():
    """Path to the test solar HTML file."""
    return Path("tests/data/Solare Einstrahlung auf die Fassade.html")


@pytest.fixture
def solar_metadata():
    """Solar metadata fixture for testing."""
    from solar import SolarFileMetadata

    return SolarFileMetadata(
        title="Solare Einstrahlung auf die Fassade",
        system_path="C:\\Users\\Test\\TEST.idm",
        simulation_date="19.06.2025 15:34:14 [59]",
        save_date="19.06.2025 15:18:26",
        facade_columns=[
            "Gesamte solare Einstrahlung, f2$Building body, W/m2",
            "Gesamte solare Einstrahlung, f3$Building body, W/m2",
            "Gesamte solare Einstrahlung, f4$Building body, W/m2",
        ],
    )


@pytest.fixture
def solar_data_points():
    """Sample solar data points for testing."""
    from datetime import datetime

    from solar import SolarDataPoint

    points = []
    for hour in range(24):
        point = SolarDataPoint(
            timestamp=datetime(2025, 6, 15, hour),
            irradiance_values={
                "Gesamte solare Einstrahlung, f2$Building body, W/m2": (
                    150.0 if 6 <= hour <= 18 else 0.0
                ),
                "Gesamte solare Einstrahlung, f3$Building body, W/m2": (
                    250.0 if 8 <= hour <= 16 else 0.0
                ),
                "Gesamte solare Einstrahlung, f4$Building body, W/m2": (
                    180.0 if 7 <= hour <= 17 else 0.0
                ),
            },
        )
        points.append(point)
    return points


class TestFacadeProcessor:
    """Test the FacadeProcessor class."""

    def test_facade_processor_initialization(self, facade_processor):
        """Test facade processor initialization."""
        assert facade_processor.threshold == 200.0
        assert facade_processor.delta_t == 7.0

    def test_find_facade_column(self, facade_processor, solar_metadata):
        """Test facade column finding."""
        # Should find the correct column for f2
        column = facade_processor._find_facade_column(
            solar_metadata, "f2", "Building body"
        )
        assert column == "Gesamte solare Einstrahlung, f2$Building body, W/m2"

        # Should not find non-existent facade
        column = facade_processor._find_facade_column(
            solar_metadata, "f99", "Building body"
        )
        assert column is None

    def test_create_solar_lookup(self, facade_processor, solar_data_points):
        """Test solar lookup table creation."""
        facade_column = "Gesamte solare Einstrahlung, f2$Building body, W/m2"
        lookup = facade_processor._create_solar_lookup(
            solar_data_points[:100], facade_column
        )

        assert isinstance(lookup, dict)
        assert len(lookup) > 0

        # Check that lookup uses correct key format (datetime objects)
        for key in lookup.keys():
            assert isinstance(key, datetime)
            # Check that datetime components are in valid ranges
            assert 1 <= key.month <= 12
            assert 1 <= key.day <= 31
            assert 0 <= key.hour <= 23  # Solar data uses 0-23 format

    def test_get_solar_irradiance_for_datetime(self, facade_processor):
        """Test solar irradiance retrieval."""
        # Create a test lookup with datetime keys
        lookup = {
            datetime(2025, 1, 1, 11, 0): 150.5,  # 11:00 solar = 12:00 weather (hour 12)
            datetime(
                2025, 6, 15, 13, 0
            ): 350.2,  # 13:00 solar = 14:00 weather (hour 14)
        }

        # Create weather data points for testing
        from src.weather import WeatherDataPoint

        weather_point_1 = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=1,
            day=1,
            hour=12,
            temperature=5.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=2.0,
            cloud_cover=4,
            humidity_ratio=4.0,
            relative_humidity=70,
            direct_solar=100,
            diffuse_solar=50,
            atmospheric_radiation=350,
            terrestrial_radiation=-50,
            quality_flag=1,
        )

        weather_point_2 = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=6,
            day=15,
            hour=14,
            temperature=25.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=3.0,
            cloud_cover=2,
            humidity_ratio=12.0,
            relative_humidity=60,
            direct_solar=500,
            diffuse_solar=150,
            atmospheric_radiation=400,
            terrestrial_radiation=-80,
            quality_flag=1,
        )

        weather_point_nonexistent = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=12,
            day=31,
            hour=24,
            temperature=0.0,
            pressure=1013,
            wind_direction=0,
            wind_speed=0.0,
            cloud_cover=0,
            humidity_ratio=2.0,
            relative_humidity=80,
            direct_solar=0,
            diffuse_solar=0,
            atmospheric_radiation=300,
            terrestrial_radiation=-40,
            quality_flag=1,
        )

        # Test existing values
        result1 = facade_processor._get_solar_irradiance_for_datetime(
            lookup, weather_point_1
        )
        assert result1[0] == 150.5  # Check the irradiance value
        assert result1[1] == "01-01 11:00"  # Check the matched time string

        result2 = facade_processor._get_solar_irradiance_for_datetime(
            lookup, weather_point_2
        )
        assert result2[0] == 350.2  # Check the irradiance value
        assert result2[1] == "06-15 13:00"  # Check the matched time string

        # Test non-existing values
        result3 = facade_processor._get_solar_irradiance_for_datetime(
            lookup, weather_point_nonexistent
        )
        assert result3[0] is None  # Should return None for non-existent data
        assert result3[1] is None  # Should return None for time string too


class TestCoreProcessor:
    """Test the CoreProcessor class."""

    def test_core_processor_initialization(self, core_processor):
        """Test core processor initialization."""
        assert isinstance(core_processor, CoreProcessor)

    def test_extract_facade_combinations(self, core_processor, solar_metadata):
        """Test facade combination extraction."""
        combinations = core_processor._extract_facade_combinations(solar_metadata)

        assert isinstance(combinations, list)
        assert len(combinations) > 0

        # Check format of combinations
        for facade_id, building_body in combinations:
            assert facade_id.startswith("f")
            assert "Building body" in building_body

    def test_process_all_facades_integration(self, weather_file_path, solar_file_path):
        """Test the complete facade processing workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process a subset to speed up test
            processor = CoreProcessor()

            # Mock the parsing to limit data size for testing
            original_parse_weather = processor.__class__.__dict__.get(
                "_load_weather_data"
            )

            output_files = processor.process_all_facades(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=200.0,
                delta_t=5.0,
                output_dir=temp_dir,
            )

            assert isinstance(output_files, dict)
            assert len(output_files) > 0

            # Check that files were actually created
            for facade_key, file_path in output_files.items():
                assert Path(file_path).exists()
                assert Path(file_path).suffix == ".dat"
                # Check that facade identifier is in the filename
                assert any(
                    facade_id in Path(file_path).name
                    for facade_id in ["f2", "f3", "f4"]
                )


class TestMainFunction:
    """Test the main processing function."""

    def test_process_weather_with_solar_data(self, weather_file_path, solar_file_path):
        """Test the main processing function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = process_weather_with_solar_data(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=250.0,
                delta_t=3.0,
                output_dir=temp_dir,
            )

            assert isinstance(output_files, dict)
            assert len(output_files) > 0

            # Verify file creation
            for facade_key, file_path in output_files.items():
                file_obj = Path(file_path)
                assert file_obj.exists()
                assert file_obj.stat().st_size > 0  # File should not be empty

                # Check file content structure
                with open(file_obj, "r", encoding="latin1") as f:
                    content = f.read()
                    # Check that it's a TRY format file
                    assert "Koordinatensystem" in content or "Format:" in content
                    # Check that it contains weather data
                    lines = content.strip().split("\n")
                    data_lines = [
                        line
                        for line in lines
                        if not line.startswith(
                            (
                                "Koordinatensystem",
                                "Rechtswert",
                                "Hochwert",
                                "Hoehenlage",
                                "Erstellung",
                                "Art",
                                "Bezugszeitraum",
                                "Datenbasis",
                                "Format:",
                                "Reihenfolge",
                                "RW",
                                "HW",
                                "MM",
                                "t",
                                "p",
                                "WR",
                                "WG",
                                "N",
                                "x",
                                "RF",
                                "B",
                                "D",
                                "A",
                                "E",
                                "IL",
                                "***",
                            )
                        )
                        and line.strip()
                    ]
                    assert len(data_lines) > 0, "Should contain weather data lines"

    def test_process_with_invalid_files(self):
        """Test processing with invalid file paths."""
        with pytest.raises(FileNotFoundError):
            process_weather_with_solar_data(
                weather_file_path="nonexistent_weather.dat",
                solar_file_path="nonexistent_solar.html",
                threshold=200.0,
                delta_t=7.0,
            )

    def test_process_with_different_thresholds(
        self, weather_file_path, solar_file_path
    ):
        """Test processing with different threshold values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with high threshold (should make few adjustments)
            output_files_high = process_weather_with_solar_data(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=1000.0,  # Very high threshold
                delta_t=10.0,
                output_dir=f"{temp_dir}/high",
            )

            # Test with low threshold (should make many adjustments)
            output_files_low = process_weather_with_solar_data(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=50.0,  # Low threshold
                delta_t=10.0,
                output_dir=f"{temp_dir}/low",
            )

            # Both should generate the same number of files (same facades)
            assert len(output_files_high) == len(output_files_low)

            # Verify files exist
            for files_dict in [output_files_high, output_files_low]:
                for file_path in files_dict.values():
                    assert Path(file_path).exists()


class TestDataIntegrity:
    """Test data integrity after processing."""

    def test_weather_data_integrity(self, weather_file_path, solar_file_path):
        """Test that weather data maintains integrity after processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = process_weather_with_solar_data(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=200.0,
                delta_t=7.0,
                output_dir=temp_dir,
            )

            # Pick one file to test in detail
            test_file_path = list(output_files.values())[0]

            with open(test_file_path, "r", encoding="latin1") as f:
                lines = f.readlines()

            # Find start of data (after header)
            data_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("     RW"):
                    data_start = i + 1
                    break

            # Count data lines
            data_lines = lines[data_start:]
            # Filter to only numeric data lines (not empty lines or other text)
            data_lines = [
                line
                for line in data_lines
                if line.strip() and line.strip()[0].isdigit()
            ]

            # Should have 8760 hours (full year)
            assert len(data_lines) == 8760

            # Test a few random data lines for format
            import random

            test_lines = random.sample(data_lines, 10)

            for line in test_lines:
                parts = line.split()
                assert len(parts) == 17  # All weather data fields should be present

                # Test that coordinates are preserved
                assert parts[0] == "3951500"  # rechtswert
                assert parts[1] == "2459500"  # hochwert

                # Test that month/day/hour are valid
                month = int(parts[2])
                day = int(parts[3])
                hour = int(parts[4])
                assert 1 <= month <= 12
                assert 1 <= day <= 31
                assert 1 <= hour <= 24

                # Test that temperature is reasonable (could be adjusted)
                temp = float(parts[5])
                assert -50 <= temp <= 60  # Reasonable temperature range


# Performance tests
class TestPerformance:
    """Test performance characteristics."""

    def test_processing_performance(self, weather_file_path, solar_file_path):
        """Test that processing completes in reasonable time."""
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()

            output_files = process_weather_with_solar_data(
                weather_file_path=str(weather_file_path),
                solar_file_path=str(solar_file_path),
                threshold=200.0,
                delta_t=7.0,
                output_dir=temp_dir,
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete processing in reasonable time (adjust as needed)
            assert processing_time < 30.0  # 30 seconds max
            assert len(output_files) > 0

            # Log performance for monitoring
            print(
                f"Processing took {processing_time:.2f} seconds for {len(output_files)} facades"
            )


if __name__ == "__main__":
    # Setup logging for test runs
    logging.basicConfig(level=logging.INFO)

    # Run basic test
    pytest.main([__file__, "-v"])
