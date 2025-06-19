"""
Tests for Weather data parser functionality.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.weather import WeatherDataParser, WeatherDataPoint, WeatherFileMetadata


class TestWeatherDataParser:
    """Tests for WeatherDataParser class."""

    def test_parser_initialization(self, weather_parser):
        """Test parser initialization."""
        assert hasattr(weather_parser, "logger")
        assert weather_parser.logger.name == "src.weather"

    def test_parse_file_nonexistent(self, weather_parser):
        """Test parsing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            weather_parser.parse_file("nonexistent_file.dat")

        assert "Weather file not found" in str(exc_info.value)

    def test_parse_file_success(self, weather_parser, sample_weather_file):
        """Test successful file parsing."""
        if not Path(sample_weather_file).exists():
            pytest.skip("Sample weather file not available")

        metadata, data_points = weather_parser.parse_file(sample_weather_file)

        # Test metadata
        assert isinstance(metadata, WeatherFileMetadata)
        assert metadata.rechtswert == 3951500
        assert metadata.hochwert == 2459500
        assert metadata.elevation == 245

        # Test data points
        assert isinstance(data_points, list)
        assert len(data_points) > 0
        assert all(isinstance(dp, WeatherDataPoint) for dp in data_points)

        # Should have 8760 data points for a full year
        assert len(data_points) == 8760

    def test_parse_metadata(self, weather_parser):
        """Test metadata parsing from header lines."""
        sample_lines = [
            "Koordinatensystem : Lambert konform konisch",
            "Rechtswert        : 3951500 Meter",
            "Hochwert          : 2459500 Meter",
            "Hoehenlage        : 245 Meter ueber NN",
            "Art des TRY       : mittleres Jahr",
            "Bezugszeitraum    : 2031-2060",
            "Datenbasis 1      : Beobachtungsdaten Zeitraum 1995-2012",
            "Datenbasis 2      : Klimasimulationen Zeitraum 1971-2000",
            "Datenbasis 3      : Klimasimulationen Zeitraum 2031-2060",
            "Erstellung des Datensatzes im Mai 2016",
            "",
            "     RW      HW MM DD HH     t    p  WR   WG N    x  RF    B    D   A    E IL",
            "3951500 2459500  1  1  1   7.4  987 208  1.6 7  6.4  95    0    0 345 -354  1",
        ]

        metadata = weather_parser._parse_metadata(sample_lines)

        assert metadata.coordinate_system == "Lambert konform konisch"
        assert metadata.rechtswert == 3951500
        assert metadata.hochwert == 2459500
        assert metadata.elevation == 245
        assert metadata.try_type == "mittleres Jahr"
        assert metadata.reference_period == "2031-2060"
        assert "Beobachtungsdaten" in metadata.data_basis_1
        assert "Klimasimulationen" in metadata.data_basis_2

    def test_parse_data_line(self, weather_parser):
        """Test parsing a single data line."""
        data_line = "3951500 2459500  1  1  1   7.4  987 208  1.6 7  6.4  95    0    0 345 -354  1"

        data_point = weather_parser._parse_data_line(data_line)

        assert data_point.rechtswert == 3951500
        assert data_point.hochwert == 2459500
        assert data_point.month == 1
        assert data_point.day == 1
        assert data_point.hour == 1
        assert data_point.temperature == 7.4
        assert data_point.pressure == 987
        assert data_point.wind_direction == 208
        assert data_point.wind_speed == 1.6
        assert data_point.cloud_cover == 7
        assert data_point.humidity_ratio == 6.4
        assert data_point.relative_humidity == 95
        assert data_point.direct_solar == 0
        assert data_point.diffuse_solar == 0
        assert data_point.atmospheric_radiation == 345
        assert data_point.terrestrial_radiation == -354
        assert data_point.quality_flag == 1

    def test_parse_data_line_invalid_fields(self, weather_parser):
        """Test parsing data line with wrong number of fields."""
        invalid_line = "3951500 2459500  1  1  1   7.4  987 208"  # Missing fields

        with pytest.raises(ValueError) as exc_info:
            weather_parser._parse_data_line(invalid_line)

        assert "Expected 17 fields" in str(exc_info.value)

    def test_parse_data_line_invalid_values(self, weather_parser):
        """Test parsing data line with invalid values."""
        invalid_line = "3951500 2459500  1  1  1   abc  987 208  1.6 7  6.4  95    0    0 345 -354  1"

        with pytest.raises(ValueError) as exc_info:
            weather_parser._parse_data_line(invalid_line)

        assert "Failed to parse data fields" in str(exc_info.value)

    def test_parse_data_lines(self, weather_parser):
        """Test parsing multiple data lines."""
        sample_lines = [
            "Koordinatensystem : Lambert konform konisch",
            "     RW      HW MM DD HH     t    p  WR   WG N    x  RF    B    D   A    E IL",
            "*** ",
            "3951500 2459500  1  1  1   7.4  987 208  1.6 7  6.4  95    0    0 345 -354  1",
            "3951500 2459500  1  1  2   8.6  987 207  1.9 7  6.9  96    0    0 346 -355  1",
            "3951500 2459500  1  1  3   9.5  987 202  2.3 8  7.3  96    0    0 340 -357  1",
            "",
            "invalid line that should be skipped",
        ]

        data_points = weather_parser._parse_data_lines(sample_lines)

        assert len(data_points) == 3
        assert data_points[0].hour == 1
        assert data_points[1].hour == 2
        assert data_points[2].hour == 3
        assert data_points[0].temperature == 7.4
        assert data_points[1].temperature == 8.6
        assert data_points[2].temperature == 9.5

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_parse_file_encoding_error(self, mock_exists, mock_file, weather_parser):
        """Test handling of encoding errors during file parsing."""
        mock_exists.return_value = True
        mock_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        with pytest.raises(ValueError) as exc_info:
            weather_parser.parse_file("test_file.dat")

        assert "Failed to parse weather file" in str(exc_info.value)

    def test_parse_metadata_missing_fields(self, weather_parser):
        """Test metadata parsing with missing fields."""
        minimal_lines = [
            "Koordinatensystem : Lambert konform konisch",
            "     RW      HW MM DD HH     t    p  WR   WG N    x  RF    B    D   A    E IL",
        ]

        metadata = weather_parser._parse_metadata(minimal_lines)

        # Should have defaults for missing fields
        assert metadata.coordinate_system == "Lambert konform konisch"
        assert metadata.rechtswert == 0  # Default
        assert metadata.elevation == 0  # Default
        assert metadata.try_type == ""  # Default

    def test_parse_metadata_no_numbers(self, weather_parser):
        """Test metadata parsing when numeric fields have no numbers."""
        lines_no_numbers = [
            "Rechtswert        : no numbers here",
            "Hochwert          : also no numbers",
            "Hoehenlage        : elevation without number",
            "     RW      HW MM DD HH     t    p  WR   WG N    x  RF    B    D   A    E IL",
        ]

        metadata = weather_parser._parse_metadata(lines_no_numbers)

        # Should default to 0 when no numbers found
        assert metadata.rechtswert == 0
        assert metadata.hochwert == 0
        assert metadata.elevation == 0
