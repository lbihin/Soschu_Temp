# Soschu Temp

Tool for adjusting supply air temperature based on solar irradiance with natural window ventilation and automatic sun protection systems.

## Contexte métier / Business Context

### Phénomène: Zulufttemperatur durch die Öffnungsflügeln bei heruntergelassenem Sonnenschutz

Bei heruntergelassenen Sonnenschutz wird die durch gekippte Öffnungsflügel einströmende Zuluft als wärmer wahrgenommen als die tatsächliche Außenluft. Dieser Effekt ist darauf zurückzuführen, dass Sonnenschutz die Solareinstrahlung absorbieren und dadurch die Luft im Zwischenraum zwischen Sonnenschutz und Fenster erwärmt. Die Temperaturerhöhung wird zusätzlich verstärkt, wenn die erwärmte Luft durch Konvektion aufsteigt und sich im oberen Bereich der Außenlaibungen sowie an den Sonnenschutzmaterialien, -schienen und Öffnungselementen ansammelt.

Diese Temperaturerhöhung zwischen Außenluft und Zuluft durch die Öffnungsflügel wird in unserer thermischen Simulation berücksichtigt.

### Tool-Beschreibung / Tool Description

Dieses Tool ist für Projekte mit natürlicher Fensterlüftung und automatisch gesteuerten Sonnenschutzsystemen (Schwellwertregelung) konzipiert. Es ermöglicht die Erstellung einer angepassten Wetterdatei (.dat), die – abhängig von der Fassadenausrichtung – die Erhöhung der Temperatur der einströmenden Außenluft berücksichtigt. Dies betrifft Räume, die über Öffnungselemente im oberen Bereich (z. B. Oberlichter oder Fenster in Kippstellung) belüftet werden, wenn der Sonnenschutz aktiv / abgesenkt ist.

### Wichtige Hinweise / Important Notes

- Für die Generierung dieser Wetterdatei muss zwingend das Jahr 2023 als Simulationsjahr in der Software EQUA IDA ICE verwendet werden.
- Das Tool ist ausschließlich für die Simulation von Räumen mit einer einzigen Fassadenausrichtung oder einer dominanten Hauptfassade geeignet. Die angepasste Wetterdatei berücksichtigt die solare Einstrahlung und den Schwellwert nur für eine Fassade.

## Features

- Parse TRY weather data files
- Parse IDA Modeler solar irradiance HTML files
- Calculate temperature adjustments based on solar irradiance thresholds
- Process facade-specific data and adjustments
- Generate adjusted weather files (.dat) for thermal simulation
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
