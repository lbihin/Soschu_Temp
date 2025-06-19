# Soschu Temp

Weather and solar data processing tool with robust Python backend.

## Features

- Parse TRY weather data files
- Parse IDA Modeler solar irradiance HTML files
- Comprehensive data validation using Pydantic
- Full test suite with pytest
- Developer-friendly tooling

## Usage

```python
from src.weather import WeatherDataParser
from src.solar import SolarDataParser

# Parse weather data
weather_parser = WeatherDataParser()
weather_metadata, weather_data = weather_parser.parse_file("data.dat")

# Parse solar data
solar_parser = SolarDataParser()
solar_metadata, solar_data = solar_parser.parse_file("solar.html")
```

## Testing

Run tests with:
```bash
make test
# or
poetry run pytest
```
