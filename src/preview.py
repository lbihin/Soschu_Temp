from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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


@dataclass
class PreviewSummaryData:
    """Données résumées pour l'onglet de résumé de la prévisualisation."""

    weather_filename: str
    solar_filename: str
    count_facades: int
    count_adjustments: int
    count_weather_data_points: int
    threshold: float
    delta_t: float
    table: dict[str, tuple[int, float]]


@dataclass
class PreviewSamplePoint:
    """Point d'échantillon individuel pour la prévisualisation."""

    timestamp: datetime
    temperature: float
    adjusted_temperature: float
    timezone_str: str = "MEZ"

    def timestamp_with_timezone_as_str(self) -> str:
        return f"{self.timestamp.strftime('%d-%m-%Y %H:%M')} {self.timezone_str}"


@dataclass
class PreviewAdjustmentData:
    """Données d'ajustement par façade pour la prévisualisation."""

    facade_name: str
    threshold: float
    delta_t: float
    samples: dict[str, list[PreviewSamplePoint]] = field(default_factory=dict)

    def get_preview_samples(self) -> dict:
        return {
            "facade_name": self.facade_name,
            "threshold": self.threshold,
            "delta_t": self.delta_t,
            "samples": self.samples,
        }


class PreviewService:
    """Service qui transforme PreviewData en données formatées pour l'UI."""

    def __init__(self, preview_data: PreviewData) -> None:
        self._data = preview_data

    def get_summary(self) -> PreviewSummaryData:
        table: dict[str, tuple[int, float]] = {}
        for facade in self._data.facades:
            adjustments = self._data.adjustments_by_facade.get(facade, 0)
            percentage = (adjustments / max(self._data.total_data_points, 1)) * 100
            table[facade] = (adjustments, percentage)

        return PreviewSummaryData(
            weather_filename=Path(self._data.weather_file_path).name,
            solar_filename=Path(self._data.solar_file_path).name,
            count_facades=self._data.total_facades,
            count_adjustments=self._data.total_adjustments,
            count_weather_data_points=self._data.total_data_points,
            threshold=self._data.threshold,
            delta_t=self._data.delta_t,
            table=table,
        )

    def get_samples(self) -> list[PreviewAdjustmentData]:
        facade_samples: dict[str, dict[str, list[PreviewSamplePoint]]] = {}

        for sample in self._data.sample_adjustments:
            if sample.facade_id not in facade_samples:
                facade_samples[sample.facade_id] = {"summer": [], "winter": []}

            is_summer = False
            if sample.weather_datetime_utc:
                is_summer = 3 <= sample.weather_datetime_utc.month <= 9

            tz_str = "MESZ" if is_summer else "MEZ"
            dt = sample.weather_datetime_utc or datetime.now()

            point = PreviewSamplePoint(
                timestamp=dt,
                temperature=sample.original_temp,
                adjusted_temperature=sample.adjusted_temp,
                timezone_str=tz_str,
            )

            season = "summer" if is_summer else "winter"
            facade_samples[sample.facade_id][season].append(point)

        return [
            PreviewAdjustmentData(
                facade_name=facade,
                threshold=self._data.threshold,
                delta_t=self._data.delta_t,
                samples=samples,
            )
            for facade, samples in facade_samples.items()
        ]
