"""
Example demonstrating MEZ/MESZ handling for weather and solar data comparison.

This example shows how to:
1. Compare weather data (MEZ) with solar data (MEZ/MESZ) using naive datetimes
2. Save data in their respective timezone-aware formats
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime

from weather import WeatherDataPoint


def demonstrate_mez_handling():
    """Demonstrate MEZ/MESZ handling for data comparison and storage."""

    # Example weather data point (from TRY file - always in MEZ format)
    weather_point = WeatherDataPoint(
        rechtswert=488284,
        hochwert=93163,
        month=6,  # June - summer time period
        day=15,
        hour=14,  # 14:00 in MEZ format
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

    print("=== MEZ/MESZ Handling Example ===\n")

    # 1. For comparison with solar data - use naive datetime
    comparison_dt = weather_point.to_datetime_for_comparison(2024)
    print(f"For comparison (naive): {comparison_dt}")
    print(f"  - Type: {type(comparison_dt)}")
    print(f"  - Timezone: {comparison_dt.tzinfo}")

    # 2. For storage - use timezone-aware datetime
    storage_dt = weather_point.to_datetime_for_storage(2024)
    print(f"\nFor storage (MEZ-aware): {storage_dt}")
    print(f"  - Type: {type(storage_dt)}")
    print(f"  - Timezone: {storage_dt.tzinfo}")
    print(f"  - UTC offset: {storage_dt.utcoffset()}")

    # 3. Legacy compatibility - naive datetime
    legacy_dt = weather_point.to_datetime(2024)
    print(f"\nLegacy format (naive): {legacy_dt}")
    print(f"  - Type: {type(legacy_dt)}")
    print(f"  - Timezone: {legacy_dt.tzinfo}")

    # 4. Demonstrate comparison scenario
    print(f"\n=== Comparison Scenario ===")

    # Simulate solar data timestamp (typically naive)
    solar_timestamp = datetime(2024, 6, 15, 13, 0)  # 13:00 naive
    print(f"Solar timestamp (naive): {solar_timestamp}")

    # Compare using naive datetimes
    can_compare = comparison_dt == solar_timestamp
    print(f"Can compare directly: {can_compare}")
    print(f"Weather time: {comparison_dt}")
    print(f"Solar time:   {solar_timestamp}")

    # 5. Demonstrate storage scenario
    print(f"\n=== Storage Scenario ===")

    # Convert to different formats for storage
    data_dict = weather_point.to_dict()

    print("Available datetime formats in data dictionary:")
    for key, value in data_dict.items():
        if "datetime" in key:
            print(f"  {key}: {value}")
            if hasattr(value, "tzinfo"):
                print(f"    - Timezone: {value.tzinfo}")

    # 6. Demonstrate DST transition detection
    print(f"\n=== DST Transition Detection ===")

    # Test with a potential DST transition hour
    dst_test_point = WeatherDataPoint(
        rechtswert=488284,
        hochwert=93163,
        month=3,  # March - potential spring forward
        day=31,  # Last Sunday in March (typical DST start)
        hour=3,  # 03:00 - hour after spring forward
        temperature=10.0,
        pressure=1013,
        wind_direction=90,
        wind_speed=2.0,
        cloud_cover=4,
        humidity_ratio=6.0,
        relative_humidity=75,
        direct_solar=200,
        diffuse_solar=100,
        atmospheric_radiation=350,
        terrestrial_radiation=-60,
        quality_flag=1,
    )

    is_dst_transition = dst_test_point.is_dst_transition_hour(2024)
    print(f"Is DST transition hour: {is_dst_transition}")

    dst_comparison_dt = dst_test_point.to_datetime_for_comparison(2024)
    dst_storage_dt = dst_test_point.to_datetime_for_storage(2024)

    print(f"DST test - comparison: {dst_comparison_dt}")
    print(f"DST test - storage: {dst_storage_dt}")

    return {
        "comparison_dt": comparison_dt,
        "storage_dt": storage_dt,
        "legacy_dt": legacy_dt,
        "solar_comparison_possible": can_compare,
    }


def compare_weather_solar_data(weather_point, solar_timestamp):
    """
    Example function showing how to compare weather and solar data.

    Args:
        weather_point: WeatherDataPoint instance
        solar_timestamp: datetime object from solar data (typically naive)

    Returns:
        dict with comparison results
    """
    # Get comparable datetime from weather data
    weather_comparison_dt = weather_point.to_datetime_for_comparison()

    # Direct comparison (both should be naive)
    times_match = weather_comparison_dt == solar_timestamp

    # Time difference calculation
    time_diff = abs((weather_comparison_dt - solar_timestamp).total_seconds())

    return {
        "weather_time": weather_comparison_dt,
        "solar_time": solar_timestamp,
        "times_match": times_match,
        "time_difference_seconds": time_diff,
        "within_tolerance": time_diff <= 3600,  # 1 hour tolerance
    }


def save_data_with_proper_timezones(weather_point, output_format="both"):
    """
    Example function showing how to save data with proper timezone handling.

    Args:
        weather_point: WeatherDataPoint instance
        output_format: 'naive', 'timezone_aware', or 'both'

    Returns:
        dict with formatted data for saving
    """
    result = {}

    if output_format in ("naive", "both"):
        # For comparison and legacy systems
        result["naive_datetime"] = weather_point.to_datetime_for_comparison()

    if output_format in ("timezone_aware", "both"):
        # For proper timezone-aware storage
        result["timezone_aware_datetime"] = weather_point.to_datetime_for_storage()

    # Add other data
    result.update(
        {
            "temperature": weather_point.temperature,
            "solar_irradiance": weather_point.total_solar_irradiance(),
            "coordinates": (weather_point.rechtswert, weather_point.hochwert),
        }
    )

    return result


if __name__ == "__main__":
    # Run the demonstration
    results = demonstrate_mez_handling()

    print(f"\n=== Summary ===")
    print(f"Comparison datetime: {results['comparison_dt']}")
    print(f"Storage datetime: {results['storage_dt']}")
    print(f"Solar comparison possible: {results['solar_comparison_possible']}")
