"""
Tests for Weather data models (Pydantic models).
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.weather import WeatherDataPoint, WeatherFileMetadata


class TestWeatherDataPoint:
    """Tests for WeatherDataPoint Pydantic model."""

    def test_valid_weather_data_point_creation(self, sample_weather_data_point):
        """Test creating a valid weather data point."""
        assert sample_weather_data_point.rechtswert == 3951500
        assert sample_weather_data_point.hochwert == 2459500
        assert sample_weather_data_point.month == 6
        assert sample_weather_data_point.day == 15
        assert sample_weather_data_point.hour == 12
        assert sample_weather_data_point.temperature == 25.5
        assert sample_weather_data_point.pressure == 1013
        assert sample_weather_data_point.wind_direction == 180
        assert sample_weather_data_point.wind_speed == 3.2
        assert sample_weather_data_point.cloud_cover == 4
        assert sample_weather_data_point.humidity_ratio == 8.5
        assert sample_weather_data_point.relative_humidity == 65
        assert sample_weather_data_point.direct_solar == 600
        assert sample_weather_data_point.diffuse_solar == 150
        assert sample_weather_data_point.atmospheric_radiation == 350
        assert sample_weather_data_point.terrestrial_radiation == -400
        assert sample_weather_data_point.quality_flag == 1

    def test_total_solar_irradiance(self, sample_weather_data_point):
        """Test total solar irradiance calculation."""
        expected = 600 + 150  # direct + diffuse
        assert sample_weather_data_point.total_solar_irradiance() == expected

    def test_to_datetime(self, sample_weather_data_point):
        """Test datetime conversion."""
        dt = sample_weather_data_point.to_datetime(2023)
        assert dt == datetime(2023, 6, 15, 11)  # Hour 12 -> 11 (0-based)

    def test_to_dict(self, sample_weather_data_point):
        """Test conversion to dictionary with computed fields."""
        data_dict = sample_weather_data_point.to_dict()
        assert "total_solar_irradiance" in data_dict
        assert "datetime" in data_dict
        assert data_dict["total_solar_irradiance"] == 750
        assert data_dict["temperature"] == 25.5

    def test_is_daylight_hour(self, sample_weather_data_point):
        """Test daylight hour detection."""
        # Hour 12 should be daylight
        assert sample_weather_data_point.is_daylight_hour() is True

        # Test edge cases
        morning_point = WeatherDataPoint(
            **{**sample_weather_data_point.model_dump(), "hour": 6}
        )
        assert morning_point.is_daylight_hour() is True

        evening_point = WeatherDataPoint(
            **{**sample_weather_data_point.model_dump(), "hour": 18}
        )
        assert evening_point.is_daylight_hour() is True

        night_point = WeatherDataPoint(
            **{**sample_weather_data_point.model_dump(), "hour": 22}
        )
        assert night_point.is_daylight_hour() is False

    def test_is_high_solar(self, sample_weather_data_point):
        """Test high solar irradiance detection."""
        # Default threshold is 200.0
        assert sample_weather_data_point.is_high_solar() is True
        assert sample_weather_data_point.is_high_solar(800) is False
        assert sample_weather_data_point.is_high_solar(500) is True

    def test_invalid_temperature_validation(self, invalid_weather_data):
        """Test temperature validation."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherDataPoint(**invalid_weather_data["invalid_temperature"])

        error = exc_info.value
        assert "temperature" in str(error)

    def test_invalid_wind_direction_validation(self, invalid_weather_data):
        """Test wind direction validation."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherDataPoint(**invalid_weather_data["invalid_wind_direction"])

        error = exc_info.value
        assert "wind_direction" in str(error)

    def test_invalid_month_validation(self, invalid_weather_data):
        """Test month validation."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherDataPoint(**invalid_weather_data["invalid_month"])

        error = exc_info.value
        assert "month" in str(error)

    def test_valid_wind_direction_calm(self):
        """Test that wind direction 999 (calm) is valid."""
        data = {
            "rechtswert": 3951500,
            "hochwert": 2459500,
            "month": 6,
            "day": 15,
            "hour": 12,
            "temperature": 25.5,
            "pressure": 1013,
            "wind_direction": 999,  # Calm condition
            "wind_speed": 0.0,
            "cloud_cover": 4,
            "humidity_ratio": 8.5,
            "relative_humidity": 65,
            "direct_solar": 600,
            "diffuse_solar": 150,
            "atmospheric_radiation": 350,
            "terrestrial_radiation": -400,
            "quality_flag": 1,
        }

        point = WeatherDataPoint(**data)
        assert point.wind_direction == 999

    def test_pressure_validation(self):
        """Test pressure validation."""
        # Test extreme pressure values
        data = {
            "rechtswert": 3951500,
            "hochwert": 2459500,
            "month": 6,
            "day": 15,
            "hour": 12,
            "temperature": 25.5,
            "pressure": 500,  # Too low
            "wind_direction": 180,
            "wind_speed": 3.2,
            "cloud_cover": 4,
            "humidity_ratio": 8.5,
            "relative_humidity": 65,
            "direct_solar": 600,
            "diffuse_solar": 150,
            "atmospheric_radiation": 350,
            "terrestrial_radiation": -400,
            "quality_flag": 1,
        }

        with pytest.raises(ValidationError) as exc_info:
            WeatherDataPoint(**data)

        error = exc_info.value
        assert "pressure" in str(error)

    def test_model_serialization(self, sample_weather_data_point):
        """Test Pydantic model serialization."""
        # Test model_dump
        data_dict = sample_weather_data_point.model_dump()
        assert isinstance(data_dict, dict)
        assert "temperature" in data_dict

        # Test round-trip serialization
        new_point = WeatherDataPoint(**data_dict)
        assert new_point.temperature == sample_weather_data_point.temperature
        assert (
            new_point.total_solar_irradiance()
            == sample_weather_data_point.total_solar_irradiance()
        )


class TestWeatherFileMetadata:
    """Tests for WeatherFileMetadata Pydantic model."""

    def test_valid_metadata_creation(self, sample_metadata):
        """Test creating valid metadata."""
        assert sample_metadata.coordinate_system == "Lambert konform konisch"
        assert sample_metadata.rechtswert == 3951500
        assert sample_metadata.hochwert == 2459500
        assert sample_metadata.elevation == 245
        assert sample_metadata.try_type == "mittleres Jahr"
        assert sample_metadata.reference_period == "2031-2060"

    def test_metadata_defaults(self):
        """Test metadata with default values."""
        metadata = WeatherFileMetadata()
        assert metadata.coordinate_system == ""
        assert metadata.rechtswert == 0
        assert metadata.hochwert == 0
        assert metadata.elevation == 0
        assert metadata.try_type == ""
        assert metadata.reference_period == ""

    def test_get_location_string(self, sample_metadata):
        """Test location string formatting."""
        location = sample_metadata.get_location_string()
        assert location == "3951500, 2459500"

    def test_get_summary(self, sample_metadata):
        """Test summary formatting."""
        summary = sample_metadata.get_summary()
        assert "TRY Weather Data Summary" in summary
        assert "3951500, 2459500" in summary
        assert "245m" in summary
        assert "mittleres Jahr" in summary
        assert "2031-2060" in summary

    def test_metadata_serialization(self, sample_metadata):
        """Test metadata serialization."""
        data_dict = sample_metadata.model_dump()
        assert isinstance(data_dict, dict)
        assert "coordinate_system" in data_dict

        # Test round-trip
        new_metadata = WeatherFileMetadata(**data_dict)
        assert new_metadata.coordinate_system == sample_metadata.coordinate_system
        assert new_metadata.elevation == sample_metadata.elevation

    def test_string_whitespace_stripping(self):
        """Test that whitespace is automatically stripped."""
        metadata = WeatherFileMetadata(
            coordinate_system="  Lambert konform konisch  ",
            try_type="   mittleres Jahr   ",
        )
        assert metadata.coordinate_system == "Lambert konform konisch"
        assert metadata.try_type == "mittleres Jahr"
