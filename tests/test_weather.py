"""
Tests unitaires pour le module weather.py

Ce module teste la classe WeatherPoint et ses méthodes associées.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from weather import WeatherPoint


class TestWeatherPoint:
    """Tests pour la classe WeatherPoint."""

    def test_weather_point_creation(self):
        """Test la création d'un point de données météo."""
        # Créer un point météo avec valeurs de test
        weather_point = WeatherPoint(
            month=6,
            day=15,
            hour=12,  # Format 1-24
            temperature=25.5,
            raw_line="06  15  12  25.5  ...",  # Ligne simulée
            year=2045,
        )

        # Vérifier les valeurs
        assert weather_point.month == 6
        assert weather_point.day == 15
        assert weather_point.hour == 12
        assert weather_point.temperature == 25.5
        assert weather_point.raw_line == "06  15  12  25.5  ..."
        assert weather_point.year == 2045

    def test_to_datetime_utc(self):
        """Test la conversion en UTC d'un point météo."""
        # Créer un point météo pour tester la conversion
        weather_point = WeatherPoint(
            month=6,
            day=15,
            hour=12,  # Format 1-24 (11:00 en format 0-23)
            temperature=25.5,
            raw_line="06  15  12  25.5  ...",
            year=2045,
        )

        # Convertir en UTC
        dt_utc = weather_point.to_datetime_utc()

        # Vérifier que l'heure UTC est 1 heure en arrière (format 1-24 -> 0-23, puis MEZ -> UTC)
        # Heure 12 (1-24) = Heure 11 (0-23)
        # Heure 11 MEZ (UTC+1) = Heure 10 UTC
        assert dt_utc.day == 15
        assert dt_utc.month == 6
        assert dt_utc.hour == 10
        assert dt_utc.tzinfo == timezone.utc

    def test_get_original_datetime_str(self):
        """Test le formatage de la date/heure au format original."""
        # Test de formatage
        weather_point = WeatherPoint(
            month=6,
            day=15,
            hour=12,
            temperature=25.5,
            raw_line="06  15  12  25.5  ...",
            year=2045,
        )

        # Le format attendu est "DD.MM HH:00" (format 1-24 pour l'heure)
        assert weather_point.get_original_datetime_str() == "15.06 12:00"

        # Test avec heure à 1 chiffre
        weather_point2 = WeatherPoint(
            month=6,
            day=5,
            hour=9,
            temperature=20.0,
            raw_line="06  05  09  20.0  ...",
            year=2045,
        )

        # Vérifier que les zéros sont bien ajoutés
        assert weather_point2.get_original_datetime_str() == "05.06 09:00"

    def test_hour_format_conversion(self):
        """
        Test que les heures au format 1-24 sont converties correctement en UTC.
        Cas spécial: heure 24
        """
        # Test avec l'heure 24 (fin de journée)
        weather_point = WeatherPoint(
            month=6,
            day=15,
            hour=24,  # Format 1-24 (23:00 en format 0-23)
            temperature=25.5,
            raw_line="06  15  24  25.5  ...",
            year=2045,
        )

        # Convertir en UTC
        dt_utc = weather_point.to_datetime_utc()

        # Vérifier que l'heure 24 (format 1-24) est traitée comme 23:00 (format 0-23)
        # et convertie en UTC (23:00 MEZ = 22:00 UTC)
        assert dt_utc.day == 15  # Doit être le même jour
        assert dt_utc.hour == 22
        assert dt_utc.tzinfo == timezone.utc
