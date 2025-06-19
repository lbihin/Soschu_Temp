"""
Tests for Weather data analyzer functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.weather import WeatherDataAnalyzer, WeatherDataPoint


class TestWeatherDataAnalyzer:
    """Tests for WeatherDataAnalyzer class."""

    def test_analyzer_initialization(self, weather_analyzer, sample_data_points):
        """Test analyzer initialization."""
        assert weather_analyzer.data_points == sample_data_points
        assert hasattr(weather_analyzer, "logger")
        assert len(weather_analyzer.data_points) == 24  # One day of data

    def test_get_temperature_stats(self, weather_analyzer):
        """Test temperature statistics calculation."""
        stats = weather_analyzer.get_temperature_stats()

        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "count" in stats

        assert isinstance(stats["min"], float)
        assert isinstance(stats["max"], float)
        assert isinstance(stats["mean"], float)
        assert stats["count"] == 24

        # Check that min <= mean <= max
        assert stats["min"] <= stats["mean"] <= stats["max"]

    def test_get_solar_radiation_stats(self, weather_analyzer):
        """Test solar radiation statistics calculation."""
        stats = weather_analyzer.get_solar_radiation_stats()

        expected_keys = [
            "total_max",
            "total_mean",
            "direct_max",
            "direct_mean",
            "diffuse_max",
            "diffuse_mean",
            "total_annual_kwh_m2",
        ]

        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))

        # Solar radiation should be non-negative
        assert stats["total_max"] >= 0
        assert stats["direct_max"] >= 0
        assert stats["diffuse_max"] >= 0
        assert stats["total_mean"] >= 0

    def test_get_wind_stats(self, weather_analyzer):
        """Test wind statistics calculation."""
        stats = weather_analyzer.get_wind_stats()

        assert "max_speed" in stats
        assert "mean_speed" in stats
        assert "count" in stats

        assert isinstance(stats["max_speed"], float)
        assert isinstance(stats["mean_speed"], float)
        assert stats["count"] == 24

        # Wind speeds should be non-negative
        assert stats["max_speed"] >= 0
        assert stats["mean_speed"] >= 0
        assert stats["max_speed"] >= stats["mean_speed"]

    def test_filter_by_month(self, weather_analyzer):
        """Test filtering data by month."""
        # All sample data is for month 6
        june_data = weather_analyzer.filter_by_month(6)
        assert len(june_data) == 24
        assert all(dp.month == 6 for dp in june_data)

        # No data for other months
        january_data = weather_analyzer.filter_by_month(1)
        assert len(january_data) == 0

    def test_filter_by_hour_range(self, weather_analyzer):
        """Test filtering data by hour range."""
        # Test morning hours (6-12)
        morning_data = weather_analyzer.filter_by_hour_range(6, 12)
        expected_hours = list(range(6, 13))  # 6-12 inclusive
        actual_hours = [dp.hour for dp in morning_data]
        assert sorted(actual_hours) == expected_hours

        # Test single hour
        noon_data = weather_analyzer.filter_by_hour_range(12, 12)
        assert len(noon_data) == 1
        assert noon_data[0].hour == 12

        # Test invalid range
        invalid_data = weather_analyzer.filter_by_hour_range(25, 26)
        assert len(invalid_data) == 0

    def test_get_daylight_hours_data(self, weather_analyzer):
        """Test getting daylight hours data."""
        daylight_data = weather_analyzer.get_daylight_hours_data()

        # Should include hours 6-18
        expected_hours = list(range(6, 19))  # 6-18 inclusive
        actual_hours = [dp.hour for dp in daylight_data]
        assert sorted(actual_hours) == expected_hours
        assert len(daylight_data) == 13

    def test_export_to_json(self, weather_analyzer):
        """Test exporting data to JSON file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name

        try:
            weather_analyzer.export_to_json(tmp_path)

            # Verify file was created and contains valid JSON
            assert Path(tmp_path).exists()

            with open(tmp_path, "r") as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 24

            # Check first data point structure
            first_point = data[0]
            required_fields = [
                "rechtswert",
                "hochwert",
                "month",
                "day",
                "hour",
                "temperature",
            ]
            for field in required_fields:
                assert field in first_point

        finally:
            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

    def test_get_high_solar_periods(self, weather_analyzer):
        """Test getting high solar irradiance periods."""
        # Test with low threshold - should get daylight hours
        high_solar_low = weather_analyzer.get_high_solar_periods(50)
        assert len(high_solar_low) > 0

        # Test with very high threshold - should get few or no periods
        high_solar_high = weather_analyzer.get_high_solar_periods(1000)
        assert len(high_solar_high) <= len(high_solar_low)

        # All returned points should exceed threshold
        threshold = 200
        high_solar = weather_analyzer.get_high_solar_periods(threshold)
        for dp in high_solar:
            assert dp.total_solar_irradiance() > threshold

    def test_validate_data_quality(self, weather_analyzer):
        """Test data quality validation."""
        quality = weather_analyzer.validate_data_quality()

        expected_keys = [
            "total_points",
            "issues",
            "calm_wind_hours",
            "extreme_temperature_hours",
            "data_quality",
        ]

        for key in expected_keys:
            assert key in quality

        assert quality["total_points"] == 24
        assert isinstance(quality["issues"], list)
        assert isinstance(quality["calm_wind_hours"], int)
        assert isinstance(quality["extreme_temperature_hours"], int)
        assert quality["data_quality"] in ["Good", "Issues detected"]

        # Should detect that we don't have full year data
        assert len(quality["issues"]) > 0
        assert "Expected 8760 data points" in quality["issues"][0]

    def test_validate_data_quality_extreme_temperatures(self):
        """Test data quality validation with extreme temperatures."""
        # Create data with extreme temperature
        extreme_data = [
            WeatherDataPoint(
                rechtswert=3951500,
                hochwert=2459500,
                month=1,
                day=1,
                hour=1,
                temperature=-60.0,  # Extreme cold
                pressure=1013,
                wind_direction=180,
                wind_speed=2.0,
                cloud_cover=0,
                humidity_ratio=1.0,
                relative_humidity=50,
                direct_solar=0,
                diffuse_solar=0,
                atmospheric_radiation=300,
                terrestrial_radiation=-350,
                quality_flag=1,
            ),
            WeatherDataPoint(
                rechtswert=3951500,
                hochwert=2459500,
                month=7,
                day=1,
                hour=12,
                temperature=60.0,  # Extreme heat
                pressure=1013,
                wind_direction=180,
                wind_speed=2.0,
                cloud_cover=0,
                humidity_ratio=1.0,
                relative_humidity=30,
                direct_solar=800,
                diffuse_solar=200,
                atmospheric_radiation=300,
                terrestrial_radiation=-350,
                quality_flag=1,
            ),
        ]

        analyzer = WeatherDataAnalyzer(extreme_data)
        quality = analyzer.validate_data_quality()

        assert quality["extreme_temperature_hours"] == 2
        assert quality["data_quality"] == "Issues detected"

    def test_validate_data_quality_calm_wind(self):
        """Test data quality validation with calm wind periods."""
        # Create data with calm wind (direction 999)
        calm_data = [
            WeatherDataPoint(
                rechtswert=3951500,
                hochwert=2459500,
                month=1,
                day=1,
                hour=1,
                temperature=20.0,
                pressure=1013,
                wind_direction=999,  # Calm
                wind_speed=0.0,
                cloud_cover=0,
                humidity_ratio=5.0,
                relative_humidity=50,
                direct_solar=0,
                diffuse_solar=0,
                atmospheric_radiation=300,
                terrestrial_radiation=-350,
                quality_flag=1,
            )
        ]

        analyzer = WeatherDataAnalyzer(calm_data)
        quality = analyzer.validate_data_quality()

        assert quality["calm_wind_hours"] == 1

    def test_empty_data_analyzer(self):
        """Test analyzer behavior with empty data."""
        empty_analyzer = WeatherDataAnalyzer([])

        # Should handle empty data gracefully
        quality = empty_analyzer.validate_data_quality()
        assert quality["total_points"] == 0
        assert quality["data_quality"] == "Issues detected"

        # Filter methods should return empty lists
        assert len(empty_analyzer.filter_by_month(6)) == 0
        assert len(empty_analyzer.filter_by_hour_range(6, 18)) == 0
        assert len(empty_analyzer.get_daylight_hours_data()) == 0
        assert len(empty_analyzer.get_high_solar_periods()) == 0

    def test_single_data_point_stats(self):
        """Test statistics calculation with single data point."""
        single_point = [
            WeatherDataPoint(
                rechtswert=3951500,
                hochwert=2459500,
                month=6,
                day=15,
                hour=12,
                temperature=25.0,
                pressure=1013,
                wind_direction=180,
                wind_speed=3.0,
                cloud_cover=4,
                humidity_ratio=8.0,
                relative_humidity=60,
                direct_solar=500,
                diffuse_solar=100,
                atmospheric_radiation=300,
                terrestrial_radiation=-350,
                quality_flag=1,
            )
        ]

        analyzer = WeatherDataAnalyzer(single_point)

        temp_stats = analyzer.get_temperature_stats()
        assert temp_stats["min"] == temp_stats["max"] == temp_stats["mean"] == 25.0
        assert temp_stats["count"] == 1

        solar_stats = analyzer.get_solar_radiation_stats()
        assert solar_stats["total_max"] == 600  # 500 + 100
        assert solar_stats["total_mean"] == 600
