"""
Pytest configuration et fixtures pour les tests du Soschu Temperature Tool.
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from preview import AdjustmentSample, PreviewData
from solar import SolarPoint
from weather import WeatherPoint


@pytest.fixture
def sample_weather_file():
    """Path to the sample weather data file."""
    return str(Path(__file__).parent / "data" / "TRY2045_488284093163_Jahr.dat")


@pytest.fixture
def sample_solar_file():
    """Path to the sample solar data file."""
    return str(
        Path(__file__).parent / "data" / "Solare Einstrahlung auf die Fassade.html"
    )


@pytest.fixture
def sample_weather_point():
    """Create a sample weather data point for testing."""
    return WeatherPoint(
        month=6,
        day=15,
        hour=12,
        temperature=25.5,
        raw_line="06  15  12  25.5  ...",
        year=2045,
    )


@pytest.fixture
def sample_solar_point():
    """Create a sample solar data point for testing."""
    return SolarPoint(
        month=6,
        day=15,
        hour=12,
        irradiance_by_facade={"f2": 750.0, "f3": 250.0, "f4": 100.0},
        is_dst=True,
        year=2045,
    )


@pytest.fixture
def sample_adjustment():
    """Create a sample adjustment for testing."""
    return AdjustmentSample(
        facade_id="f2",
        datetime_str="15.06.2045 12:00",
        weather_datetime_str="15.06 12:00",
        solar_datetime_str="15.06.2045 12:00 MESZ",
        original_temp=25.5,
        adjusted_temp=32.5,
        solar_irradiance=750.0,
        weather_datetime_utc=datetime(2045, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
        solar_datetime_utc=datetime(2045, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_weather_data():
    """Create a list of sample weather data points."""
    data_points = []

    # Create data for one day (24 hours)
    for hour in range(1, 25):
        # Simulate temperature variation throughout the day
        temp = 15 + 10 * abs(12 - hour) / 12

        data_point = WeatherPoint(
            month=6,
            day=15,
            hour=hour,  # Format 1-24
            temperature=temp,
            raw_line=f"06  15  {hour:02d}  {temp:.1f}  ...",
            year=2045,
        )
        data_points.append(data_point)

    return data_points


@pytest.fixture
def sample_solar_data():
    """Create a list of sample solar data points."""
    data_points = []

    # Create data for one day (24 hours)
    for hour in range(24):  # Format 0-23
        # Simulate solar irradiance (only during daylight hours)
        if 6 <= hour <= 18:
            f2_irradiance = max(0, 750 * (1 - abs(12 - hour) / 6))
            f3_irradiance = max(0, 250 * (1 - abs(12 - hour) / 6))
            f4_irradiance = max(0, 100 * (1 - abs(12 - hour) / 6))
        else:
            f2_irradiance = 0
            f3_irradiance = 0
            f4_irradiance = 0

        # Déterminer si heure d'été (MESZ)
        is_dst = (
            True  # Pour simplifier, on considère que juin est toujours en heure d'été
        )

        data_point = SolarPoint(
            month=6,
            day=15,
            hour=hour,  # Format 0-23
            irradiance_by_facade={
                "f2": f2_irradiance,
                "f3": f3_irradiance,
                "f4": f4_irradiance,
            },
            is_dst=is_dst,
            year=2045,
        )
        data_points.append(data_point)

    return data_points


@pytest.fixture
def sample_preview_data(sample_weather_data, sample_solar_data, sample_adjustment):
    """Create sample preview data for testing."""
    return PreviewData(
        facades=["f2", "f3", "f4"],
        total_adjustments=10,
        total_data_points=24,
        adjustments_by_facade={"f2": 5, "f3": 3, "f4": 2},
        sample_adjustments=[sample_adjustment],
        weather_data=sample_weather_data,
        solar_data=sample_solar_data,
        weather_file_header="Sample header",
        threshold=200.0,
        delta_t=7.0,
        weather_file_path="/path/to/weather.dat",
        solar_file_path="/path/to/solar.html",
    )


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
