"""
Integration tests for the complete weather data processing pipeline.
"""

from pathlib import Path

import pytest

from src.weather import WeatherDataAnalyzer, WeatherDataParser, load_weather_data


class TestWeatherIntegration:
    """Integration tests for weather data processing."""

    def test_load_weather_data_integration(self, sample_weather_file):
        """Test the complete load_weather_data function."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)

        # Test metadata
        assert metadata.rechtswert == 3951500
        assert metadata.hochwert == 2459500
        assert metadata.elevation == 245
        assert "Lambert" in metadata.coordinate_system

        # Test analyzer
        assert isinstance(analyzer, WeatherDataAnalyzer)
        assert len(analyzer.data_points) == 8760  # Full year

        # Test some basic analytics
        temp_stats = analyzer.get_temperature_stats()
        assert temp_stats["count"] == 8760
        assert -20 < temp_stats["min"] < 50  # Reasonable temperature range
        assert -10 < temp_stats["max"] < 50

        solar_stats = analyzer.get_solar_radiation_stats()
        assert solar_stats["total_max"] > 0
        assert solar_stats["total_annual_kwh_m2"] > 0

    def test_end_to_end_weather_analysis(self, sample_weather_file):
        """Test end-to-end weather data analysis workflow."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        # Load data
        metadata, analyzer = load_weather_data(sample_weather_file)

        # Perform various analyses
        temp_stats = analyzer.get_temperature_stats()
        solar_stats = analyzer.get_solar_radiation_stats()
        wind_stats = analyzer.get_wind_stats()
        quality = analyzer.validate_data_quality()

        # Test seasonal data
        summer_data = analyzer.filter_by_month(7)  # July
        winter_data = analyzer.filter_by_month(1)  # January

        assert len(summer_data) > 0
        assert len(winter_data) > 0

        # Summer should generally be warmer
        summer_analyzer = WeatherDataAnalyzer(summer_data)
        winter_analyzer = WeatherDataAnalyzer(winter_data)

        summer_temp = summer_analyzer.get_temperature_stats()
        winter_temp = winter_analyzer.get_temperature_stats()

        # Summer mean should be higher than winter mean
        assert summer_temp["mean"] > winter_temp["mean"]

        # Test daylight vs nighttime solar radiation
        daylight_data = analyzer.get_daylight_hours_data()
        daylight_analyzer = WeatherDataAnalyzer(daylight_data)
        daylight_solar = daylight_analyzer.get_solar_radiation_stats()

        # Daylight hours should have higher average solar radiation
        assert daylight_solar["total_mean"] > solar_stats["total_mean"]

    def test_data_quality_validation_integration(self, sample_weather_file):
        """Test data quality validation on real data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)
        quality = analyzer.validate_data_quality()

        # Should have good data quality for the test file
        assert quality["data_quality"] == "Good"
        assert quality["total_points"] == 8760
        assert len(quality["issues"]) == 0

        # Check for reasonable values
        assert (
            quality["extreme_temperature_hours"] == 0
        )  # No extreme temps in test data
        assert quality["calm_wind_hours"] >= 0  # May or may not have calm periods

    def test_high_solar_analysis_integration(self, sample_weather_file):
        """Test high solar irradiance analysis on real data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)

        # Test different thresholds
        thresholds = [100, 200, 300, 500, 800]
        previous_count = len(analyzer.data_points)

        for threshold in thresholds:
            high_solar = analyzer.get_high_solar_periods(threshold)
            current_count = len(high_solar)

            # Higher thresholds should have fewer or equal periods
            assert current_count <= previous_count
            previous_count = current_count

            # All returned periods should exceed threshold
            for dp in high_solar:
                assert dp.total_solar_irradiance() > threshold

    def test_seasonal_analysis_integration(self, sample_weather_file):
        """Test seasonal analysis capabilities."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)

        # Analyze each month
        monthly_temps = []
        monthly_solar = []

        for month in range(1, 13):
            month_data = analyzer.filter_by_month(month)

            if len(month_data) > 0:
                month_analyzer = WeatherDataAnalyzer(month_data)
                temp_stats = month_analyzer.get_temperature_stats()
                solar_stats = month_analyzer.get_solar_radiation_stats()

                monthly_temps.append(temp_stats["mean"])
                monthly_solar.append(solar_stats["total_mean"])

        assert len(monthly_temps) == 12
        assert len(monthly_solar) == 12

        # Summer months (6-8) should generally be warmer
        summer_temp = sum(monthly_temps[5:8]) / 3  # June, July, August
        winter_temp = (
            sum([monthly_temps[11], monthly_temps[0], monthly_temps[1]]) / 3
        )  # Dec, Jan, Feb

        assert summer_temp > winter_temp

    def test_hourly_pattern_analysis(self, sample_weather_file):
        """Test hourly pattern analysis."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)

        # Analyze solar radiation patterns throughout the day
        hourly_solar = []

        for hour in range(1, 25):  # Hours 1-24
            hour_data = [dp for dp in analyzer.data_points if dp.hour == hour]
            if hour_data:
                hour_analyzer = WeatherDataAnalyzer(hour_data)
                solar_stats = hour_analyzer.get_solar_radiation_stats()
                hourly_solar.append((hour, solar_stats["total_mean"]))

        # Find peak solar hour
        peak_hour, peak_solar = max(hourly_solar, key=lambda x: x[1])

        # Peak should be around midday (10-14)
        assert 10 <= peak_hour <= 14

        # Night hours should have minimal solar radiation
        night_hours = [1, 2, 3, 22, 23, 24]
        night_solar = [solar for hour, solar in hourly_solar if hour in night_hours]

        for solar in night_solar:
            assert solar < 10  # Very low solar radiation at night

    def test_parser_and_analyzer_consistency(self, sample_weather_file):
        """Test consistency between parser and analyzer results."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        # Parse data directly
        parser = WeatherDataParser()
        metadata_direct, data_points_direct = parser.parse_file(sample_weather_file)

        # Load data through convenience function
        metadata_convenience, analyzer_convenience = load_weather_data(
            sample_weather_file
        )

        # Results should be identical
        assert metadata_direct.model_dump() == metadata_convenience.model_dump()
        assert len(data_points_direct) == len(analyzer_convenience.data_points)

        # Compare first and last data points
        assert (
            data_points_direct[0].model_dump()
            == analyzer_convenience.data_points[0].model_dump()
        )
        assert (
            data_points_direct[-1].model_dump()
            == analyzer_convenience.data_points[-1].model_dump()
        )

    def test_data_point_methods_integration(self, sample_weather_file):
        """Test WeatherDataPoint methods with real data."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, analyzer = load_weather_data(sample_weather_file)

        # Test methods on various data points
        test_points = [
            analyzer.data_points[0],  # First point
            analyzer.data_points[4000],  # Middle point
            analyzer.data_points[-1],  # Last point
        ]

        for dp in test_points:
            # Test datetime conversion
            dt = dp.to_datetime()
            assert dt.year == 2045
            assert 1 <= dt.month <= 12
            assert 1 <= dt.day <= 31
            assert 0 <= dt.hour <= 23

            # Test total solar irradiance
            total_solar = dp.total_solar_irradiance()
            assert total_solar == dp.direct_solar + dp.diffuse_solar
            assert total_solar >= 0

            # Test to_dict method
            data_dict = dp.to_dict()
            assert "total_solar_irradiance" in data_dict
            assert "datetime" in data_dict
            assert data_dict["total_solar_irradiance"] == total_solar

            # Test is_daylight_hour
            is_daylight = dp.is_daylight_hour()
            assert isinstance(is_daylight, bool)
            if 6 <= dp.hour <= 18:
                assert is_daylight is True
            else:
                assert is_daylight is False

            # Test is_high_solar
            is_high = dp.is_high_solar(200)
            assert isinstance(is_high, bool)
            assert is_high == (total_solar > 200)
