"""Tests for MEZ/MESZ timezone handling in weather data."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.weather import WeatherDataPoint


class TestMEZTimezoneHandling:
    """Test cases for MEZ/MESZ timezone handling."""

    def test_winter_time_conversion(self):
        """Test datetime conversion during winter time (MEZ)."""
        # January - definitely winter time (MEZ)
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=1,
            day=15,
            hour=14,  # 14:00 MEZ
            temperature=5.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=3.5,
            cloud_cover=4,
            humidity_ratio=4.2,
            relative_humidity=70,
            direct_solar=250,
            diffuse_solar=100,
            atmospheric_radiation=350,
            terrestrial_radiation=-50,
            quality_flag=1,
        )

        dt = weather_point.to_datetime_mez_aware(2024)

        # Should be timezone-aware
        assert dt.tzinfo is not None
        assert str(dt.tzinfo) == "Europe/Berlin"

        # Should be 13:00 in datetime (hour 14 -> 13 in 0-23 format)
        assert dt.hour == 13
        assert dt.month == 1
        assert dt.day == 15

    def test_summer_time_conversion(self):
        """Test datetime conversion during summer time (MESZ)."""
        # July - definitely summer time (MESZ)
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=7,
            day=15,
            hour=14,  # 14:00 MESZ
            temperature=25.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=3.5,
            cloud_cover=2,
            humidity_ratio=12.0,
            relative_humidity=60,
            direct_solar=600,
            diffuse_solar=200,
            atmospheric_radiation=400,
            terrestrial_radiation=-80,
            quality_flag=1,
        )

        dt = weather_point.to_datetime_mez_aware(2024)

        # Should be timezone-aware
        assert dt.tzinfo is not None
        assert str(dt.tzinfo) == "Europe/Berlin"

        # Should be 13:00 in datetime (hour 14 -> 13 in 0-23 format)
        assert dt.hour == 13
        assert dt.month == 7
        assert dt.day == 15

    def test_naive_datetime_for_solar_comparison(self):
        """Test naive datetime conversion for solar data comparison."""
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=6,
            day=15,
            hour=12,  # 12:00 MESZ
            temperature=20.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=2.0,
            cloud_cover=3,
            humidity_ratio=8.5,
            relative_humidity=65,
            direct_solar=500,
            diffuse_solar=150,
            atmospheric_radiation=380,
            terrestrial_radiation=-70,
            quality_flag=1,
        )

        dt_aware = weather_point.to_datetime_mez_aware(2024)
        dt_naive = weather_point.to_datetime_naive(2024)

        # Timezone-aware should have timezone info
        assert dt_aware.tzinfo is not None

        # Naive should not have timezone info
        assert dt_naive.tzinfo is None

        # Time values should be the same (local time)
        assert dt_aware.hour == dt_naive.hour
        assert dt_aware.minute == dt_naive.minute
        assert dt_aware.day == dt_naive.day
        assert dt_aware.month == dt_naive.month
        assert dt_aware.year == dt_naive.year

    def test_dst_transition_detection(self):
        """Test detection of DST transition hours."""
        # Normal hour - should not be DST transition
        normal_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=6,
            day=15,
            hour=12,
            temperature=20.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=2.0,
            cloud_cover=3,
            humidity_ratio=8.5,
            relative_humidity=65,
            direct_solar=500,
            diffuse_solar=150,
            atmospheric_radiation=380,
            terrestrial_radiation=-70,
            quality_flag=1,
        )

        assert not normal_point.is_dst_transition_hour(2024)

    def test_to_dict_includes_both_datetime_formats(self):
        """Test that to_dict includes both timezone-aware and naive datetime."""
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=3,
            day=15,
            hour=10,
            temperature=10.0,
            pressure=1013,
            wind_direction=90,
            wind_speed=4.0,
            cloud_cover=5,
            humidity_ratio=6.0,
            relative_humidity=75,
            direct_solar=300,
            diffuse_solar=120,
            atmospheric_radiation=360,
            terrestrial_radiation=-60,
            quality_flag=2,
        )

        data_dict = weather_point.to_dict()

        # Should contain both datetime formats
        assert "datetime" in data_dict
        assert "datetime_mez_aware" in data_dict

        # datetime should be naive (for compatibility)
        assert data_dict["datetime"].tzinfo is None

        # datetime_mez_aware should have timezone
        assert data_dict["datetime_mez_aware"].tzinfo is not None

        # Should also include computed total solar irradiance
        assert "total_solar_irradiance" in data_dict
        assert data_dict["total_solar_irradiance"] == 420  # 300 + 120

    def test_hour_format_conversion(self):
        """Test proper conversion from 1-24 hour format to 0-23."""
        # Test hour 1 (should become hour 0)
        weather_point_1 = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=1,
            day=1,
            hour=1,  # 01:00 MEZ
            temperature=0.0,
            pressure=1013,
            wind_direction=0,
            wind_speed=0.0,
            cloud_cover=0,
            humidity_ratio=3.0,
            relative_humidity=80,
            direct_solar=0,
            diffuse_solar=0,
            atmospheric_radiation=300,
            terrestrial_radiation=-40,
            quality_flag=1,
        )

        dt1 = weather_point_1.to_datetime(2024)
        assert dt1.hour == 0  # hour 1 -> 0

        # Test hour 24 (should become hour 23)
        weather_point_24 = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=1,
            day=1,
            hour=24,  # 24:00 MEZ (midnight of next day)
            temperature=0.0,
            pressure=1013,
            wind_direction=0,
            wind_speed=0.0,
            cloud_cover=0,
            humidity_ratio=3.0,
            relative_humidity=80,
            direct_solar=0,
            diffuse_solar=0,
            atmospheric_radiation=300,
            terrestrial_radiation=-40,
            quality_flag=1,
        )

        dt24 = weather_point_24.to_datetime(2024)
        assert dt24.hour == 23  # hour 24 -> 23
