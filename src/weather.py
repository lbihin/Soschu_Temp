from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class WeatherPoint:
    """Point de données météo simplifié."""

    month: int
    day: int
    hour: int  # 1-24 format
    temperature: float
    raw_line: str  # Ligne originale pour la réécriture
    year: int = 2045  # Année par défaut, peut être modifiée lors du parsing

    def to_datetime_utc(self) -> datetime:
        """
        Convertit l'heure MEZ 1-24 vers UTC pour la comparaison.
        Les fichiers .dat utilisent l'heure MEZ fixe (sans passage à l'heure d'été).
        """
        # Convertir l'heure 1-24 en format 0-23
        hour_0_23 = self.hour - 1

        # Créer un datetime naïf en MEZ
        dt_naive = datetime(self.year, self.month, self.day, hour_0_23, 0, 0)

        # Créer un datetime avec timezone MEZ (UTC+1) fixe sans tenir compte de l'heure d'été
        dt_mez = dt_naive.replace(tzinfo=timezone(timedelta(hours=1)))

        # Convertir en UTC
        dt_utc = dt_mez.astimezone(timezone.utc)

        return dt_utc

    def get_original_datetime_str(self) -> str:
        """Renvoie la date/heure au format original du fichier DAT (1-24 MEZ)"""
        return f"{self.day:02d}.{self.month:02d} {self.hour:02d}:00"
