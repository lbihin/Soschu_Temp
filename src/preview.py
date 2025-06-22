from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from solar import SolarPoint
from weather import WeatherPoint


@dataclass
class AdjustmentSample:
    """Échantillon d'ajustement pour la prévisualisation."""

    facade_id: str
    datetime_str: str  # Format commun pour affichage
    weather_datetime_str: str  # Format date/heure pour le fichier météo DAT (1-24 MEZ)
    solar_datetime_str: (
        str  # Format date/heure pour le fichier solaire HTML (0-23 MEZ/MESZ)
    )
    original_temp: float
    adjusted_temp: float
    solar_irradiance: float
    weather_datetime_utc: Optional[datetime] = None  # Timestamp UTC du point météo
    solar_datetime_utc: Optional[datetime] = None  # Timestamp UTC du point solaire


@dataclass
class PreviewData:
    """Données pour la prévisualisation."""

    facades: List[str]
    total_adjustments: int
    total_data_points: int
    adjustments_by_facade: Dict[str, int]
    sample_adjustments: List[AdjustmentSample]

    # Données complètes pour la génération
    weather_data: List[WeatherPoint]
    solar_data: List[SolarPoint]
    weather_file_header: str
    threshold: float
    delta_t: float

    # Chemins des fichiers sources pour référence
    weather_file_path: str
    solar_file_path: str

    @property
    def total_facades(self) -> int:
        return len(self.facades)
