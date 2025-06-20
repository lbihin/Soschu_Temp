"""
Tests for synchronization logic between weather and solar data.

This module tests the core synchronization logic that handles the timezone
differences between weather data (constant MEZ) and solar data (MEZ/MESZ).
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core import FacadeProcessor, is_dst_date


class TestTimeSynchronizationLogic:
    """Test the time synchronization logic between weather and solar data."""

    @pytest.fixture
    def facade_processor(self):
        """Create a facade processor for testing."""
        return FacadeProcessor(threshold=200.0, delta_t=7.0)

    @pytest.mark.parametrize(
        "month,day,expected_is_summer,description",
        [
            # Winter months (MEZ)
            (1, 15, False, "January - definitely winter"),
            (2, 20, False, "February - definitely winter"),
            (11, 15, False, "November - definitely winter"),
            (12, 21, False, "December - definitely winter"),
            # Summer months (MESZ)
            (4, 15, True, "April - definitely summer"),
            (5, 20, True, "May - definitely summer"),
            (6, 21, True, "June - definitely summer"),
            (7, 15, True, "July - definitely summer"),
            (8, 15, True, "August - definitely summer"),
            (9, 20, True, "September - definitely summer"),
            # Transition months - conservative approach
            (3, 25, False, "March 25 - before DST transition"),
            (3, 31, True, "March 31 - after DST transition"),
            (10, 25, True, "October 25 - before DST ends"),
            (10, 27, False, "October 27 - after DST ends"),
        ],
    )
    def test_dst_date_detection(self, month, day, expected_is_summer, description):
        """Test DST date detection function."""
        result = is_dst_date(month, day)
        assert (
            result == expected_is_summer
        ), f"{description}: expected {expected_is_summer}, got {result}"

    @pytest.mark.parametrize(
        "month,day,weather_hour,expected_solar_hour,season_desc",
        [
            # Winter cases (MEZ): Direct conversion 1-24h -> 0-23h
            (1, 15, 12, 11, "MEZ (winter)"),  # 12h weather -> 11h solar
            (2, 20, 14, 13, "MEZ (winter)"),  # 14h weather -> 13h solar
            (3, 25, 8, 7, "MEZ (winter)"),  # 8h weather -> 7h solar
            (11, 15, 16, 15, "MEZ (winter)"),  # 16h weather -> 15h solar
            (12, 21, 10, 9, "MEZ (winter)"),  # 10h weather -> 9h solar
            # Summer cases (MESZ): Weather MEZ + 1h DST adjustment
            (4, 15, 12, 12, "MESZ (summer)"),  # 12h weather (+1h DST) -> 12h solar
            (6, 21, 14, 14, "MESZ (summer)"),  # 14h weather (+1h DST) -> 14h solar
            (7, 15, 8, 8, "MESZ (summer)"),  # 8h weather (+1h DST) -> 8h solar
            (8, 15, 16, 16, "MESZ (summer)"),  # 16h weather (+1h DST) -> 16h solar
            (9, 20, 10, 10, "MESZ (summer)"),  # 10h weather (+1h DST) -> 10h solar
            # Edge cases
            (1, 1, 1, 0, "MEZ (winter)"),  # First hour
            (1, 1, 24, 23, "MEZ (winter)"),  # Last hour
            (6, 1, 1, 1, "MESZ (summer)"),  # First hour summer
            (6, 1, 24, 23, "MESZ (summer)"),  # Last hour summer (limited to 23)
        ],
    )
    def test_solar_hour_calculation(
        self,
        facade_processor,
        month,
        day,
        weather_hour,
        expected_solar_hour,
        season_desc,
    ):
        """Test the solar hour calculation logic."""
        from src.weather import WeatherDataPoint

        # Create a weather data point
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=month,
            day=day,
            hour=weather_hour,
            temperature=20.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=2.0,
            cloud_cover=4,
            humidity_ratio=8.0,
            relative_humidity=70,
            direct_solar=100,
            diffuse_solar=50,
            atmospheric_radiation=350,
            terrestrial_radiation=-50,
            quality_flag=1,
        )

        # Create a test lookup with the expected solar hour
        test_solar_dt = datetime(2025, month, day, expected_solar_hour, 0)
        solar_lookup = {test_solar_dt: 250.0}  # Above threshold

        # Test the synchronization
        result = facade_processor._get_solar_irradiance_for_datetime(
            solar_lookup, weather_point
        )

        # Should find the matching solar data
        assert (
            result[0] == 250.0
        ), f"Expected to find solar irradiance for {season_desc} case"
        assert (
            result[1] is not None
        ), f"Expected to find matched solar time for {season_desc} case"

    def test_synchronization_winter_detailed(self, facade_processor):
        """Detailed test for winter synchronization (MEZ to MEZ)."""
        from src.weather import WeatherDataPoint

        # Winter case: both weather and solar in MEZ
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=1,  # January - definitely winter
            day=15,
            hour=14,  # 14:00 MEZ
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

        # Solar data: 13:00 (weather 14h - 1h = 13h solar in 0-23 format)
        solar_lookup = {datetime(2025, 1, 15, 13, 0): 300.0}  # 13:00 solar

        result = facade_processor._get_solar_irradiance_for_datetime(
            solar_lookup, weather_point
        )

        assert result[0] == 300.0
        assert "01-15 13:00" in result[1]

    def test_synchronization_summer_detailed(self, facade_processor):
        """Detailed test for summer synchronization (MEZ to MESZ)."""
        from src.weather import WeatherDataPoint

        # Summer case: weather in MEZ, solar in MESZ
        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=7,  # July - definitely summer
            day=15,
            hour=14,  # 14:00 MEZ
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

        # Solar data: 14:00 (weather 14h MEZ = 15h MESZ = 14h in 0-23 format)
        solar_lookup = {
            datetime(2025, 7, 15, 14, 0): 450.0  # 14:00 solar (corresponds to 15h MESZ)
        }

        result = facade_processor._get_solar_irradiance_for_datetime(
            solar_lookup, weather_point
        )

        assert result[0] == 450.0
        assert "07-15 14:00" in result[1]

    def test_no_matching_solar_data(self, facade_processor):
        """Test behavior when no matching solar data is found."""
        from src.weather import WeatherDataPoint

        weather_point = WeatherDataPoint(
            rechtswert=488284,
            hochwert=93163,
            month=6,
            day=15,
            hour=12,
            temperature=20.0,
            pressure=1013,
            wind_direction=180,
            wind_speed=2.0,
            cloud_cover=4,
            humidity_ratio=8.0,
            relative_humidity=70,
            direct_solar=100,
            diffuse_solar=50,
            atmospheric_radiation=350,
            terrestrial_radiation=-50,
            quality_flag=1,
        )

        # Empty solar lookup
        solar_lookup = {}

        result = facade_processor._get_solar_irradiance_for_datetime(
            solar_lookup, weather_point
        )

        assert result == (None, None)


class TestTimezoneOffsetCalculation:
    """Test timezone offset calculations using pytz-like logic."""

    @pytest.mark.parametrize(
        "month,day,hour,expected_weather_offset,expected_solar_offset,expected_adjustment",
        [
            # Winter: both MEZ (UTC+1), no adjustment needed
            (1, 15, 12, 1, 1, 0),
            (2, 20, 14, 1, 1, 0),
            (11, 15, 10, 1, 1, 0),
            (12, 21, 16, 1, 1, 0),
            # Summer: weather MEZ (UTC+1), solar MESZ (UTC+2), +1h adjustment
            (4, 15, 12, 1, 2, 1),
            (6, 21, 14, 1, 2, 1),
            (8, 15, 10, 1, 2, 1),
            (9, 20, 16, 1, 2, 1),
        ],
    )
    def test_timezone_offset_logic(
        self,
        month,
        day,
        hour,
        expected_weather_offset,
        expected_solar_offset,
        expected_adjustment,
    ):
        """Test timezone offset calculation logic."""
        # Weather data is always MEZ (UTC+1)
        weather_utc_offset = 1

        # Solar data follows local time (MEZ/MESZ)
        is_summer = is_dst_date(month, day)
        solar_utc_offset = 2 if is_summer else 1

        # Calculate needed adjustment
        offset_needed = solar_utc_offset - weather_utc_offset

        assert weather_utc_offset == expected_weather_offset
        assert solar_utc_offset == expected_solar_offset
        assert offset_needed == expected_adjustment

        # The target solar hour should be weather hour + offset - 1 (for 0-23 conversion)
        # But in summer, we add the DST offset before converting
        if is_summer:
            target_solar_hour = (
                hour  # hour already includes DST adjustment conceptually
            )
        else:
            target_solar_hour = hour - 1  # direct conversion 1-24 -> 0-23

        # Validate bounds
        target_solar_hour = max(0, min(23, target_solar_hour))

        # This should match our expected calculation
        if is_summer:
            expected_target = hour if hour <= 23 else 23
        else:
            expected_target = max(0, hour - 1)

        assert target_solar_hour == expected_target
