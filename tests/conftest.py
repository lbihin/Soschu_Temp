"""
Pytest configuration and fixtures for weather data tests.
"""

from pathlib import Path
from typing import List

import pytest

from src.weather import (
    WeatherDataAnalyzer,
    WeatherDataParser,
    WeatherDataPoint,
    WeatherFileMetadata,
    load_weather_data,
)


@pytest.fixture
def sample_weather_file():
    """Path to the sample weather data file."""
    return "tests/data/TRY2045_488284093163_Jahr.dat"


@pytest.fixture
def sample_weather_data_point():
    """Create a sample weather data point for testing."""
    return WeatherDataPoint(
        rechtswert=3951500,
        hochwert=2459500,
        month=6,
        day=15,
        hour=12,
        temperature=25.5,
        pressure=1013,
        wind_direction=180,
        wind_speed=3.2,
        cloud_cover=4,
        humidity_ratio=8.5,
        relative_humidity=65,
        direct_solar=600,
        diffuse_solar=150,
        atmospheric_radiation=350,
        terrestrial_radiation=-400,
        quality_flag=1,
    )


@pytest.fixture
def sample_metadata():
    """Create sample weather file metadata."""
    return WeatherFileMetadata(
        coordinate_system="Lambert konform konisch",
        rechtswert=3951500,
        hochwert=2459500,
        elevation=245,
        try_type="mittleres Jahr",
        reference_period="2031-2060",
        data_basis_1="Beobachtungsdaten Zeitraum 1995-2012",
        data_basis_2="Klimasimulationen Zeitraum 1971-2000",
        data_basis_3="Klimasimulationen Zeitraum 2031-2060",
        creation_date="Mai 2016",
    )


@pytest.fixture
def sample_data_points():
    """Create a list of sample weather data points."""
    data_points = []

    # Create data for one day (24 hours)
    for hour in range(1, 25):
        # Simulate temperature variation throughout the day
        temp = 15 + 10 * abs(12 - hour) / 12

        # Simulate solar radiation (only during daylight hours)
        if 6 <= hour <= 18:
            solar_direct = max(0, 500 * (1 - abs(12 - hour) / 6))
            solar_diffuse = max(0, 100 * (1 - abs(12 - hour) / 6))
        else:
            solar_direct = 0
            solar_diffuse = 0

        data_point = WeatherDataPoint(
            rechtswert=3951500,
            hochwert=2459500,
            month=6,
            day=15,
            hour=hour,
            temperature=temp,
            pressure=1013,
            wind_direction=180 + hour * 5,  # Varying wind direction
            wind_speed=2.0 + hour * 0.1,
            cloud_cover=hour % 9,
            humidity_ratio=6.0 + hour * 0.1,
            relative_humidity=60 + hour % 30,
            direct_solar=int(solar_direct),
            diffuse_solar=int(solar_diffuse),
            atmospheric_radiation=300,
            terrestrial_radiation=-350,
            quality_flag=1,
        )
        data_points.append(data_point)

    return data_points


@pytest.fixture
def weather_analyzer(sample_data_points):
    """Create a weather data analyzer with sample data."""
    return WeatherDataAnalyzer(sample_data_points)


@pytest.fixture
def weather_parser():
    """Create a weather data parser instance."""
    return WeatherDataParser()


@pytest.fixture
def invalid_weather_data():
    """Create invalid weather data for testing validation."""
    return {
        "invalid_temperature": {
            "rechtswert": 3951500,
            "hochwert": 2459500,
            "month": 6,
            "day": 15,
            "hour": 12,
            "temperature": -100.0,  # Invalid temperature
            "pressure": 1013,
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
        },
        "invalid_wind_direction": {
            "rechtswert": 3951500,
            "hochwert": 2459500,
            "month": 6,
            "day": 15,
            "hour": 12,
            "temperature": 25.5,
            "pressure": 1013,
            "wind_direction": 450,  # Invalid wind direction
            "wind_speed": 3.2,
            "cloud_cover": 4,
            "humidity_ratio": 8.5,
            "relative_humidity": 65,
            "direct_solar": 600,
            "diffuse_solar": 150,
            "atmospheric_radiation": 350,
            "terrestrial_radiation": -400,
            "quality_flag": 1,
        },
        "invalid_month": {
            "rechtswert": 3951500,
            "hochwert": 2459500,
            "month": 13,  # Invalid month
            "day": 15,
            "hour": 12,
            "temperature": 25.5,
            "pressure": 1013,
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
        },
    }
