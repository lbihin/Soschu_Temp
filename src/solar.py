from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from constants import MEZ_TIMEZONE


@dataclass
class SolarPoint:
    """Point de données solaire simplifié."""

    month: int
    day: int
    hour: int  # 0-23 format (MEZ/MESZ)
    irradiance_by_facade: Dict[str, float]
    is_dst: bool = False  # Flag pour indiquer si c'est l'heure d'été
    year: int = 2045  # Année extraite du fichier HTML

    def to_datetime_utc(self) -> datetime:
        """
        Convertit l'heure HTML (0-23 MEZ/MESZ) vers UTC pour la comparaison.
        Les fichiers HTML tiennent compte du passage à l'heure d'été (MESZ).
        Utilise l'année extraite du fichier HTML.
        """
        # Créer un datetime naïf
        dt_naive = datetime(self.year, self.month, self.day, self.hour, 0, 0)

        # Appliquer la timezone MEZ/MESZ (Europe/Berlin)
        dt_local = MEZ_TIMEZONE.localize(dt_naive, is_dst=self.is_dst)

        # Convertir en UTC
        dt_utc = dt_local.astimezone(timezone.utc)

        return dt_utc

    def get_original_datetime_str(self) -> str:
        """Renvoie la date/heure au format original du fichier HTML (0-23 MEZ/MESZ)"""
        time_suffix = "MESZ" if self.is_dst else "MEZ"
        return f"{self.day:02d}.{self.month:02d}.{self.year} {self.hour:02d}:00 {time_suffix}"
