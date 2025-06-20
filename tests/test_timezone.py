"""
Test timezone synchronization logic using pytz-style calculations.

This module tests the timezone offset calculations that underlie
the synchronization between weather data (MEZ) and solar data (MEZ/MESZ).
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    import pytz

    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from core import is_dst_date


class TestTimezoneCalculations:
    """Test timezone offset calculations for weather/solar synchronization."""

    @pytest.mark.skipif(not PYTZ_AVAILABLE, reason="pytz not available")
    @pytest.mark.parametrize(
        "test_date,expected_weather_offset,expected_solar_offset,description",
        [
            # Winter cases (MEZ = UTC+1)
            (datetime(2024, 1, 15, 12, 0), 1, 1, "January - winter time"),
            (datetime(2024, 2, 20, 14, 0), 1, 1, "February - winter time"),
            (datetime(2024, 3, 30, 12, 0), 1, 1, "March 30 - before DST"),
            (datetime(2024, 11, 15, 12, 0), 1, 1, "November - back to winter"),
            (datetime(2024, 12, 21, 12, 0), 1, 1, "December - winter time"),
            # Summer cases (MESZ = UTC+2)
            (datetime(2024, 4, 1, 12, 0), 1, 2, "April - summer time"),
            (datetime(2024, 6, 21, 12, 0), 1, 2, "June - summer time"),
            (datetime(2024, 8, 15, 14, 0), 1, 2, "August - summer time"),
            (datetime(2024, 10, 26, 12, 0), 1, 2, "October 26 - still summer"),
            # Transition periods (approximate)
            (datetime(2024, 3, 31, 12, 0), 1, 2, "March 31 - DST starts"),
            (datetime(2024, 10, 27, 12, 0), 1, 1, "October 27 - DST ends"),
        ],
    )
    def test_timezone_offset_with_pytz(
        self, test_date, expected_weather_offset, expected_solar_offset, description
    ):
        """Test timezone offset calculations using pytz."""
        # Berlin timezone for solar data (follows local DST rules)
        tz_berlin = pytz.timezone("Europe/Berlin")

        # Weather data: constant MEZ (UTC+1)
        weather_utc_offset = 1

        # Solar data: follows Europe/Berlin timezone rules
        berlin_dt = tz_berlin.localize(test_date)
        utc_offset = berlin_dt.utcoffset()
        assert utc_offset is not None, f"Failed to get UTC offset for {test_date}"
        solar_utc_offset = utc_offset.total_seconds() / 3600

        # Calculate the adjustment needed
        offset_needed = int(solar_utc_offset - weather_utc_offset)

        assert (
            weather_utc_offset == expected_weather_offset
        ), f"{description}: weather offset"
        assert solar_utc_offset == expected_solar_offset, f"{description}: solar offset"

        # Expected offset should match the difference
        expected_offset = expected_solar_offset - expected_weather_offset
        assert offset_needed == expected_offset, f"{description}: offset calculation"

        # Log for verification
        print(f"\n{description}:")
        print(f"  Date: {test_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Weather UTC offset: +{weather_utc_offset}h")
        print(f"  Solar UTC offset: +{solar_utc_offset:.0f}h")
        print(f"  Offset needed: {offset_needed:+d}h")

    @pytest.mark.parametrize(
        "month,day,hour,expected_is_summer",
        [
            # Clear winter cases
            (1, 15, 12, False),
            (2, 20, 14, False),
            (11, 15, 10, False),
            (12, 21, 16, False),
            # Clear summer cases
            (4, 15, 12, True),
            (5, 20, 14, True),
            (6, 21, 12, True),
            (7, 15, 14, True),
            (8, 15, 10, True),
            (9, 20, 16, True),
            # Transition periods
            (3, 30, 12, False),  # Before DST
            (3, 31, 12, True),  # DST starts (approximate)
            (10, 26, 12, True),  # Still DST
            (10, 27, 12, False),  # DST ends (approximate)
        ],
    )
    def test_dst_detection_consistency(self, month, day, hour, expected_is_summer):
        """Test that our DST detection is consistent with expected behavior."""
        result = is_dst_date(month, day)
        assert (
            result == expected_is_summer
        ), f"{month:02d}-{day:02d}: expected {expected_is_summer}, got {result}"

    def test_weather_to_solar_hour_conversion(self):
        """Test the complete weather-to-solar hour conversion logic."""
        test_cases = [
            # (month, day, weather_hour, expected_solar_hour, description)
            # Winter: direct conversion (weather_hour - 1)
            (1, 15, 12, 11, "Winter: 12h MEZ -> 11h solar"),
            (2, 20, 14, 13, "Winter: 14h MEZ -> 13h solar"),
            (12, 21, 8, 7, "Winter: 8h MEZ -> 7h solar"),
            # Summer: weather hour + DST adjustment
            (6, 21, 12, 12, "Summer: 12h MEZ -> 12h solar (with DST)"),
            (7, 15, 14, 14, "Summer: 14h MEZ -> 14h solar (with DST)"),
            (8, 15, 8, 8, "Summer: 8h MEZ -> 8h solar (with DST)"),
            # Edge cases
            (1, 1, 1, 0, "Winter: first hour"),
            (1, 1, 24, 23, "Winter: last hour"),
            (6, 1, 1, 1, "Summer: first hour"),
            (6, 1, 24, 23, "Summer: last hour (clamped)"),
        ]

        for month, day, weather_hour, expected_solar_hour, description in test_cases:
            is_summer = is_dst_date(month, day)

            # Apply the same logic as in the core module
            if is_summer:
                # Summer: weather is MEZ, solar is MESZ
                # Weather 12h MEZ should find Solar 12h (which represents 13h MESZ in local time)
                target_solar_hour = weather_hour
            else:
                # Winter: both MEZ, direct conversion 1-24 -> 0-23
                target_solar_hour = weather_hour - 1

            # Apply bounds checking
            target_solar_hour = max(0, min(23, target_solar_hour))

            assert (
                target_solar_hour == expected_solar_hour
            ), f"{description}: expected {expected_solar_hour}, got {target_solar_hour}"

    @pytest.mark.skipif(not PYTZ_AVAILABLE, reason="pytz not available")
    def test_dst_transition_dates(self):
        """Test behavior around DST transition dates."""
        tz_berlin = pytz.timezone("Europe/Berlin")

        # Test dates around spring transition (last Sunday of March)
        spring_before = datetime(2024, 3, 30, 12, 0)  # Saturday before
        spring_day = datetime(2024, 3, 31, 12, 0)  # Sunday transition
        spring_after = datetime(2024, 4, 1, 12, 0)  # Monday after

        # Test dates around fall transition (last Sunday of October)
        fall_before = datetime(2024, 10, 26, 12, 0)  # Saturday before
        fall_day = datetime(2024, 10, 27, 12, 0)  # Sunday transition
        fall_after = datetime(2024, 10, 28, 12, 0)  # Monday after

        # Spring transition: MEZ -> MESZ
        before_dt = tz_berlin.localize(spring_before)
        day_dt = tz_berlin.localize(spring_day)
        after_dt = tz_berlin.localize(spring_after)

        # Should see the offset change
        before_offset = before_dt.utcoffset()
        day_offset = day_dt.utcoffset()
        after_offset = after_dt.utcoffset()

        assert (
            before_offset is not None and before_offset.total_seconds() / 3600 == 1
        )  # MEZ
        assert day_offset is not None and day_offset.total_seconds() / 3600 == 2  # MESZ
        assert (
            after_offset is not None and after_offset.total_seconds() / 3600 == 2
        )  # MESZ

        # Fall transition: MESZ -> MEZ
        before_dt = tz_berlin.localize(fall_before)
        day_dt = tz_berlin.localize(fall_day)
        after_dt = tz_berlin.localize(fall_after)

        # Should see the offset change back
        before_offset = before_dt.utcoffset()
        day_offset = day_dt.utcoffset()
        after_offset = after_dt.utcoffset()

        assert (
            before_offset is not None and before_offset.total_seconds() / 3600 == 2
        )  # MESZ
        assert day_offset is not None and day_offset.total_seconds() / 3600 == 1  # MEZ
        assert (
            after_offset is not None and after_offset.total_seconds() / 3600 == 1
        )  # MEZ
