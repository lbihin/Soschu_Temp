from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from solar import SolarPoint
from weather import WeatherPoint


@dataclass
class AdjustmentSample:
    """Échantillon d'ajustement pour la prévisualisation."""

    facade_id: str
    datetime_str: str
    weather_datetime_str: str
    solar_datetime_str: str
    original_temp: float
    adjusted_temp: float
    solar_irradiance: float
    weather_datetime_utc: datetime | None = None
    solar_datetime_utc: datetime | None = None


@dataclass
class PreviewData:
    """Données pour la prévisualisation."""

    facades: list[str]
    total_adjustments: int
    total_data_points: int
    adjustments_by_facade: dict[str, int]
    sample_adjustments: list[AdjustmentSample]

    # Données complètes pour la génération
    weather_data: list[WeatherPoint]
    solar_data: list[SolarPoint]
    weather_file_header: str
    threshold: float
    delta_t: float

    # Chemins des fichiers sources pour référence
    weather_file_path: str
    solar_file_path: str

    @property
    def total_facades(self) -> int:
        return len(self.facades)
