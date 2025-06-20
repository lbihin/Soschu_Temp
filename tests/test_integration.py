"""
Integration tests for the complete Soschu Temperature tool pipeline.

This test suite covers the end-to-end functionality including weather data parsing,
solar irradiance parsing, core processing with facade-specific temperature adjustments,
and file generation workflow.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core import CoreProcessor, FacadeProcessor, process_weather_with_solar_data
from solar import SolarDataParser, load_solar_irridance_data
from weather import WeatherDataAnalyzer, WeatherDataParser, load_weather_data


class TestCoreIntegration:
    """Integration tests for the core processing functionality."""

    def test_end_to_end_processing_workflow(self, sample_weather_file):
        """Test the complete end-to-end processing workflow."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test the complete workflow
            output_files = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=200.0,
                delta_t=7.0,
                output_dir=temp_dir,
            )

            # Verify output files were generated
            assert isinstance(output_files, dict)
            assert len(output_files) > 0

            # Check that files were actually created and contain data
            for facade_key, file_path in output_files.items():
                file_obj = Path(file_path)
                assert file_obj.exists()
                assert file_obj.stat().st_size > 0

                # Verify file content structure
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

    def test_facade_processor_integration(self, sample_weather_file):
        """Test FacadeProcessor with real data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        # Load weather and solar data
        weather_metadata, weather_data = load_weather_data(sample_weather_file)
        solar_metadata, solar_data = load_solar_irridance_data(solar_file)

        # Test facade processor
        processor = FacadeProcessor(threshold=250.0, delta_t=5.0)

        # Use CoreProcessor to extract facade combinations
        core_processor = CoreProcessor()
        facade_combinations = core_processor._extract_facade_combinations(
            solar_metadata
        )
        if not facade_combinations:
            pytest.skip("No facade combinations found in solar data")

        facade_id, building_body = facade_combinations[0]

        adjusted_metadata, adjusted_weather_data = processor.process_facade_data(
            weather_metadata,
            weather_data,
            solar_metadata,
            solar_data,
            facade_id,
            building_body,
        )

        # Verify adjustments were made
        assert len(adjusted_weather_data) == len(weather_data)
        assert adjusted_metadata.data_basis_3 != weather_metadata.data_basis_3
        assert "Processed for" in adjusted_metadata.data_basis_3

        # Verify some temperatures were adjusted
        original_temps = [dp.temperature for dp in weather_data]
        adjusted_temps = [dp.temperature for dp in adjusted_weather_data]

        # Should have some differences (some temperatures increased)
        temp_differences = [
            adj - orig for orig, adj in zip(original_temps, adjusted_temps)
        ]
        adjustments_made = sum(1 for diff in temp_differences if diff > 0)
        assert adjustments_made > 0

    def test_core_processor_integration(self, sample_weather_file):
        """Test CoreProcessor with real data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            processor = CoreProcessor()

            output_files = processor.process_all_facades(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=300.0,
                delta_t=10.0,
                output_dir=temp_dir,
            )

            assert len(output_files) > 0

            # Test that each facade has its own file
            facade_files = set()
            for facade_key, file_path in output_files.items():
                # Extract facade info from key
                parts = facade_key.split("_")
                facade_id = parts[0]  # e.g., "f2", "f3", "f4"

                facade_files.add(facade_id)

                # Verify file naming convention
                assert facade_id in Path(file_path).name
                # Files should contain facade identifier but not necessarily "weather_"
                assert Path(file_path).suffix == ".dat"

            # Should have multiple facades
            assert len(facade_files) >= 2

    def test_different_threshold_scenarios(self, sample_weather_file):
        """Test processing with different threshold scenarios."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with very high threshold (minimal adjustments)
            output_files_high = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=1000.0,  # Very high
                delta_t=15.0,
                output_dir=f"{temp_dir}/high",
            )

            # Test with low threshold (many adjustments)
            output_files_low = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=50.0,  # Low
                delta_t=15.0,
                output_dir=f"{temp_dir}/low",
            )

            # Should generate same number of facade files
            assert len(output_files_high) == len(output_files_low)

            # Verify both sets exist and contain appropriate metadata
            for files_dict, threshold in [
                (output_files_high, 1000.0),
                (output_files_low, 50.0),
            ]:
                for file_path in files_dict.values():
                    assert Path(file_path).exists(), f"File should exist: {file_path}"
                    with open(file_path, "r", encoding="latin1") as f:
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


class TestDataLoadingIntegration:
    """Integration tests for data loading functions."""

    def test_load_weather_data_integration(self, sample_weather_file):
        """Test the complete load_weather_data function."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)

        # Test metadata
        assert metadata.rechtswert == 3951500
        assert metadata.hochwert == 2459500
        assert metadata.elevation == 245
        assert "Lambert" in metadata.coordinate_system

        # Test data points
        assert isinstance(data_points, list)
        assert len(data_points) == 8760  # Full year

        # Test analyzer creation from data points
        analyzer = WeatherDataAnalyzer(data_points)
        temp_stats = analyzer.get_temperature_stats()
        assert temp_stats["count"] == 8760
        assert -20 < temp_stats["min"] < 50  # Reasonable temperature range

    def test_load_solar_data_integration(self):
        """Test solar data loading integration."""
        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        metadata, data_points = load_solar_irridance_data(solar_file)

        # Test metadata
        assert metadata.title == "Solare Einstrahlung auf die Fassade"
        assert len(metadata.facade_columns) > 0

        # Test data points
        assert isinstance(data_points, list)
        assert len(data_points) > 0

        # Test that facade columns are present in data
        sample_point = data_points[0]
        assert len(sample_point.irradiance_values) > 0

        # Verify facade column names match metadata
        facade_keys = set()
        for point in data_points[:10]:  # Check first 10 points
            facade_keys.update(point.irradiance_values.keys())

        metadata_columns = set(metadata.facade_columns)
        assert facade_keys.issubset(metadata_columns)

    def test_parser_consistency_integration(self, sample_weather_file):
        """Test consistency between different parsing approaches."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        # Parse data using load_weather_data
        metadata_load, data_points_load = load_weather_data(sample_weather_file)

        # Parse data directly using parser
        parser = WeatherDataParser()
        metadata_direct, data_points_direct = parser.parse_file(sample_weather_file)

        # Results should be identical
        assert metadata_load.model_dump() == metadata_direct.model_dump()
        assert len(data_points_load) == len(data_points_direct)

        # Compare samples
        for i in [0, 100, 1000]:
            if i < len(data_points_load):
                assert (
                    data_points_load[i].model_dump()
                    == data_points_direct[i].model_dump()
                )


class TestWeatherAnalysisIntegration:
    """Integration tests for weather analysis with new data structure."""

    def test_analyzer_with_loaded_data(self, sample_weather_file):
        """Test WeatherDataAnalyzer with data from load_weather_data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)

        # Test basic analytics
        temp_stats = analyzer.get_temperature_stats()
        solar_stats = analyzer.get_solar_radiation_stats()
        wind_stats = analyzer.get_wind_stats()

        assert temp_stats["count"] == 8760
        assert solar_stats["total_max"] > 0
        assert wind_stats["max_speed"] >= 0

        # Test seasonal analysis
        summer_data = analyzer.filter_by_month(7)  # July
        winter_data = analyzer.filter_by_month(1)  # January

        summer_analyzer = WeatherDataAnalyzer(summer_data)
        winter_analyzer = WeatherDataAnalyzer(winter_data)

        summer_temp = summer_analyzer.get_temperature_stats()
        winter_temp = winter_analyzer.get_temperature_stats()

        # Summer should generally be warmer
        assert summer_temp["mean"] > winter_temp["mean"]

    def test_data_quality_with_new_structure(self, sample_weather_file):
        """Test data quality validation with new data loading structure."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)
        quality = analyzer.validate_data_quality()

        # Should have good data quality for the test file
        assert quality["data_quality"] == "Good"
        assert quality["total_points"] == 8760

    def test_high_solar_analysis_integration(self, sample_weather_file):
        """Test high solar irradiance analysis."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)

        # Test different thresholds
        thresholds = [100, 200, 300, 500]
        previous_count = len(data_points)

        for threshold in thresholds:
            high_solar = analyzer.get_high_solar_periods(threshold)
            current_count = len(high_solar)

            # Higher thresholds should have fewer or equal periods
            assert current_count <= previous_count
            previous_count = current_count

            # All returned periods should exceed threshold
            for dp in high_solar:
                assert dp.total_solar_irradiance() > threshold


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""

    def test_invalid_file_paths(self):
        """Test processing with invalid file paths."""
        with pytest.raises(FileNotFoundError):
            process_weather_with_solar_data(
                weather_file_path="nonexistent_weather.dat",
                solar_file_path="nonexistent_solar.html",
                threshold=200.0,
                delta_t=7.0,
            )

    def test_invalid_parameters(self, sample_weather_file):
        """Test processing with invalid parameters."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        # Test negative threshold
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should work but might not make sense
            output_files = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=-100.0,  # Negative threshold
                delta_t=5.0,
                output_dir=temp_dir,
            )
            # Should still generate files (all irradiance values > -100)
            assert len(output_files) > 0

    def test_empty_output_directory_creation(self, sample_weather_file):
        """Test that output directories are created properly."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_output_dir = f"{temp_dir}/deeply/nested/output/directory"

            output_files = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=200.0,
                delta_t=7.0,
                output_dir=nested_output_dir,
            )

            # Directory should be created and files should exist
            assert Path(nested_output_dir).exists()
            assert len(output_files) > 0

            for file_path in output_files.values():
                assert Path(file_path).exists()
                assert str(nested_output_dir) in str(file_path)


class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    def test_processing_performance(self, sample_weather_file):
        """Test that complete processing completes in reasonable time."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()

            output_files = process_weather_with_solar_data(
                weather_file_path=sample_weather_file,
                solar_file_path=solar_file,
                threshold=200.0,
                delta_t=7.0,
                output_dir=temp_dir,
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete processing in reasonable time
            assert processing_time < 30.0  # 30 seconds max
            assert len(output_files) > 0

            print(
                f"Processing took {processing_time:.2f} seconds for {len(output_files)} facades"
            )

    def test_memory_efficiency(self, sample_weather_file):
        """Test that processing doesn't consume excessive memory."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        solar_file = "tests/data/Solare Einstrahlung auf die Fassade.html"
        if not Path(solar_file).exists():
            pytest.skip("Sample solar file not available")

        # This is a basic memory test - in a real scenario you might use memory profilers
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                output_files = process_weather_with_solar_data(
                    weather_file_path=sample_weather_file,
                    solar_file_path=solar_file,
                    threshold=200.0,
                    delta_t=7.0,
                    output_dir=temp_dir,
                )

                # If we get here without memory errors, consider it a pass
                assert len(output_files) > 0

            except MemoryError:
                pytest.fail("Processing consumed too much memory")


if __name__ == "__main__":
    # Setup logging for test runs
    import logging

    logging.basicConfig(level=logging.INFO)

    # Run tests
    pytest.main([__file__, "-v"])
