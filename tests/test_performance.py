"""
Performance tests for weather data processing.
"""

import time
from pathlib import Path

import pytest

from src.weather import WeatherDataAnalyzer, WeatherDataParser, load_weather_data


@pytest.mark.slow
class TestWeatherPerformance:
    """Performance tests for weather data processing."""

    def test_file_parsing_performance(self, sample_weather_file):
        """Test that file parsing completes within reasonable time."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        start_time = time.time()
        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)
        end_time = time.time()

        parsing_time = end_time - start_time

        # Should parse 8760 data points in less than 5 seconds
        assert parsing_time < 5.0
        assert len(analyzer.data_points) == 8760

        print(
            f"Parsed {len(analyzer.data_points)} data points in {parsing_time:.3f} seconds"
        )

    def test_statistics_calculation_performance(self, sample_weather_file):
        """Test that statistics calculation is fast."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)

        # Time various statistics calculations
        functions_to_time = [
            analyzer.get_temperature_stats,
            analyzer.get_solar_radiation_stats,
            analyzer.get_wind_stats,
            analyzer.validate_data_quality,
            lambda: analyzer.filter_by_month(6),
            lambda: analyzer.get_daylight_hours_data(),
            lambda: analyzer.get_high_solar_periods(300),
        ]

        total_time = 0
        for operation in functions_to_time:
            start_time = time.time()
            result = operation()
            end_time = time.time()

            operation_time = end_time - start_time
            total_time += operation_time

            # Each operation should complete in less than 1 second
            assert operation_time < 1.0

        # All operations combined should complete in less than 3 seconds
        assert total_time < 3.0

        print(f"All statistics operations completed in {total_time:.3f} seconds")

    def test_data_point_validation_performance(self):
        """Test that data point validation is efficient."""
        # Create many data points to test validation performance
        data_points = []

        start_time = time.time()

        for i in range(1000):
            # This should be fast due to Pydantic's optimizations
            from src.weather import WeatherDataPoint

            dp = WeatherDataPoint(
                rechtswert=3951500,
                hochwert=2459500,
                month=(i % 12) + 1,
                day=(i % 28) + 1,
                hour=(i % 24) + 1,
                temperature=20.0 + (i % 20),
                pressure=1013,
                wind_direction=(i % 360),
                wind_speed=i % 10,
                cloud_cover=i % 9,
                humidity_ratio=5.0 + (i % 5),
                relative_humidity=50 + (i % 40),
                direct_solar=i % 1000,
                diffuse_solar=i % 200,
                atmospheric_radiation=300,
                terrestrial_radiation=-350,
                quality_flag=i % 5,
            )
            data_points.append(dp)

        end_time = time.time()
        creation_time = end_time - start_time

        # Creating 1000 validated data points should be fast
        assert creation_time < 2.0
        assert len(data_points) == 1000

        print(f"Created and validated 1000 data points in {creation_time:.3f} seconds")

    def test_large_dataset_filtering_performance(self, sample_weather_file):
        """Test filtering performance on large dataset."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)

        # Test various filtering operations
        filters = [
            lambda: analyzer.filter_by_month(6),
            lambda: analyzer.filter_by_hour_range(10, 14),
            lambda: analyzer.get_daylight_hours_data(),
            lambda: analyzer.get_high_solar_periods(100),
            lambda: analyzer.get_high_solar_periods(500),
        ]

        for i, filter_func in enumerate(filters):
            start_time = time.time()
            result = filter_func()
            end_time = time.time()

            filter_time = end_time - start_time

            # Each filter operation should complete quickly
            assert filter_time < 0.5
            assert isinstance(result, list)

            print(
                f"Filter operation {i+1} completed in {filter_time:.3f} seconds, {len(result)} results"
            )

    def test_memory_usage_reasonable(self, sample_weather_file):
        """Test that memory usage is reasonable for full year data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        import sys

        # Get initial memory usage
        initial_size = sys.getsizeof([])

        # Load data
        metadata, data_points = load_weather_data(sample_weather_file)
        analyzer = WeatherDataAnalyzer(data_points)

        # Check memory usage of data points
        data_size = sys.getsizeof(analyzer.data_points)

        # Should be reasonable (less than 50MB for 8760 data points)
        assert data_size < 50 * 1024 * 1024  # 50MB

        # Test that individual data points are not too large
        if analyzer.data_points:
            point_size = sys.getsizeof(analyzer.data_points[0])
            assert point_size < 10 * 1024  # 10KB per data point

            print(f"Data points list size: {data_size / (1024*1024):.2f} MB")
            print(f"Individual data point size: ~{point_size} bytes")
