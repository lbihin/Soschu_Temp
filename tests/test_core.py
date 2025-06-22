"""
Tests unitaires pour le module core_logic.py

Ce module teste la classe SoschuProcessor et son traitement de données.
"""

import tempfile
from unittest.mock import patch

import pytest

from core import SoschuProcessor
from preview import PreviewData
from solar import SolarPoint
from weather import WeatherPoint


class TestSoschuProcessor:
    """Tests pour la classe SoschuProcessor."""

    def test_processor_creation(self):
        """Test la création du processeur."""
        processor = SoschuProcessor()
        assert processor is not None
        assert processor.weather_parser is not None
        assert processor.solar_parser is not None

    @patch("parser.WeatherParser.parse")
    @patch("parser.SolarParser.parse")
    def test_preview_adjustments_basic(self, mock_solar_parse, mock_weather_parse):
        """Test la méthode de prévisualisation des ajustements avec valeurs simulées."""
        # Configurer les mocks pour simuler les parsers
        mock_weather_header = "Mock header"

        # Créer des données météo simulées
        mock_weather_data = [
            WeatherPoint(
                month=6,
                day=15,
                hour=12,
                temperature=25.0,
                raw_line="06 15 12 25.0",
                year=2045,
            ),
            WeatherPoint(
                month=6,
                day=15,
                hour=13,
                temperature=26.0,
                raw_line="06 15 13 26.0",
                year=2045,
            ),
            WeatherPoint(
                month=6,
                day=15,
                hour=14,
                temperature=27.0,
                raw_line="06 15 14 27.0",
                year=2045,
            ),
        ]

        # Créer des données solaires simulées
        mock_solar_data = [
            SolarPoint(
                month=6,
                day=15,
                hour=11,
                irradiance_by_facade={"f2": 650.0, "f3": 200.0, "f4": 50.0},
                is_dst=True,
                year=2045,
            ),
            SolarPoint(
                month=6,
                day=15,
                hour=12,
                irradiance_by_facade={"f2": 750.0, "f3": 300.0, "f4": 80.0},
                is_dst=True,
                year=2045,
            ),
            SolarPoint(
                month=6,
                day=15,
                hour=13,
                irradiance_by_facade={"f2": 700.0, "f3": 250.0, "f4": 60.0},
                is_dst=True,
                year=2045,
            ),
        ]

        # Configurer les mocks pour renvoyer ces données
        mock_weather_parse.return_value = (mock_weather_header, mock_weather_data)
        mock_solar_parse.return_value = mock_solar_data

        # Exécuter la méthode de prévisualisation
        processor = SoschuProcessor()
        preview_data = processor.preview_adjustments(
            weather_file="mock_weather.dat",
            solar_file="mock_solar.html",
            threshold=200.0,
            delta_t=7.0,
        )

        # Vérifier le résultat
        assert isinstance(preview_data, PreviewData)
        assert preview_data.facades == ["f2", "f3", "f4"]
        assert preview_data.total_data_points == len(mock_weather_data)

        # Vérifier que les façades avec irradiance > seuil ont des ajustements
        # f2 et f3 devraient avoir des ajustements (irradiance > 200)
        assert preview_data.adjustments_by_facade["f2"] > 0
        assert preview_data.adjustments_by_facade["f3"] > 0
        # f4 ne devrait pas avoir d'ajustements (irradiance < 200)
        assert preview_data.adjustments_by_facade["f4"] == 0

    @patch("parser.WeatherParser.parse")
    @patch("parser.SolarParser.parse")
    def test_empty_data_handling(self, mock_solar_parse, mock_weather_parse):
        """Test la gestion des données vides."""
        # Configurer les mocks pour renvoyer des données vides
        mock_weather_parse.return_value = ("Header", [])
        mock_solar_parse.return_value = []

        # Exécuter la méthode
        processor = SoschuProcessor()
        preview_data = processor.preview_adjustments(
            weather_file="empty_weather.dat",
            solar_file="empty_solar.html",
            threshold=200.0,
            delta_t=7.0,
        )

        # Vérifier le résultat avec données vides
        assert isinstance(preview_data, PreviewData)
        assert preview_data.facades == []
        assert preview_data.total_data_points == 0
        assert preview_data.total_adjustments == 0
        assert preview_data.sample_adjustments == []

    @patch("parser.WeatherParser.parse")
    @patch("parser.SolarParser.parse")
    def test_threshold_effect(self, mock_solar_parse, mock_weather_parse):
        """Test l'effet du seuil sur les ajustements."""
        # Données météo simulées constantes
        mock_weather_data = [
            WeatherPoint(
                month=6,
                day=15,
                hour=12,
                temperature=25.0,
                raw_line="06 15 12 25.0",
                year=2045,
            ),
        ]

        # Données solaires simulées
        mock_solar_data = [
            SolarPoint(
                month=6,
                day=15,
                hour=11,
                irradiance_by_facade={"f2": 150.0, "f3": 250.0, "f4": 350.0},
                is_dst=True,
                year=2045,
            ),
        ]

        # Configurer les mocks
        mock_weather_parse.return_value = ("Header", mock_weather_data)
        mock_solar_parse.return_value = mock_solar_data

        # Test avec différents seuils
        processor = SoschuProcessor()

        # Seuil bas (toutes les façades devraient être ajustées)
        preview_low = processor.preview_adjustments(
            weather_file="mock_weather.dat",
            solar_file="mock_solar.html",
            threshold=100.0,
            delta_t=5.0,
        )

        # Seuil moyen (f3 et f4 devraient être ajustées)
        preview_med = processor.preview_adjustments(
            weather_file="mock_weather.dat",
            solar_file="mock_solar.html",
            threshold=200.0,
            delta_t=5.0,
        )

        # Seuil élevé (seulement f4 devrait être ajustée)
        preview_high = processor.preview_adjustments(
            weather_file="mock_weather.dat",
            solar_file="mock_solar.html",
            threshold=300.0,
            delta_t=5.0,
        )

        # Vérifier les effets du seuil
        assert preview_low.total_adjustments > preview_med.total_adjustments
        assert preview_med.total_adjustments > preview_high.total_adjustments

        # Vérifier spécifiquement les façades ajustées
        assert preview_low.adjustments_by_facade["f2"] > 0
        assert preview_low.adjustments_by_facade["f3"] > 0
        assert preview_low.adjustments_by_facade["f4"] > 0

        assert preview_med.adjustments_by_facade["f2"] == 0
        assert preview_med.adjustments_by_facade["f3"] > 0
        assert preview_med.adjustments_by_facade["f4"] > 0

        assert preview_high.adjustments_by_facade["f2"] == 0
        assert preview_high.adjustments_by_facade["f3"] == 0
        assert preview_high.adjustments_by_facade["f4"] > 0
