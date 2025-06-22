"""
Tests unitaires pour le module preview.py

Ce module teste les classes AdjustmentSample et PreviewData.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from preview import AdjustmentSample, PreviewData
from solar import SolarPoint
from weather import WeatherPoint


class TestAdjustmentSample:
    """Tests pour la classe AdjustmentSample."""

    def test_adjustment_sample_creation(self):
        """Test la création d'un échantillon d'ajustement."""
        sample = AdjustmentSample(
            facade_id="f2",
            datetime_str="15.06.2045 12:00",
            weather_datetime_str="15.06 12:00",
            solar_datetime_str="15.06.2045 11:00 MESZ",
            original_temp=25.0,
            adjusted_temp=32.0,
            solar_irradiance=750.0,
            weather_datetime_utc=datetime(2045, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            solar_datetime_utc=datetime(2045, 6, 15, 9, 0, 0, tzinfo=timezone.utc),
        )

        # Vérifier les valeurs
        assert sample.facade_id == "f2"
        assert sample.datetime_str == "15.06.2045 12:00"
        assert sample.weather_datetime_str == "15.06 12:00"
        assert sample.solar_datetime_str == "15.06.2045 11:00 MESZ"
        assert sample.original_temp == 25.0
        assert sample.adjusted_temp == 32.0
        assert sample.solar_irradiance == 750.0
        assert sample.weather_datetime_utc == datetime(
            2045, 6, 15, 10, 0, 0, tzinfo=timezone.utc
        )
        assert sample.solar_datetime_utc == datetime(
            2045, 6, 15, 9, 0, 0, tzinfo=timezone.utc
        )

        # Vérifier que l'ajustement est correct
        assert sample.adjusted_temp - sample.original_temp == 7.0


class TestPreviewData:
    """Tests pour la classe PreviewData."""

    def test_preview_data_creation(self):
        """Test la création d'un objet de prévisualisation."""
        # Créer des échantillons
        sample1 = AdjustmentSample(
            facade_id="f2",
            datetime_str="15.06.2045 12:00",
            weather_datetime_str="15.06 12:00",
            solar_datetime_str="15.06.2045 11:00 MESZ",
            original_temp=25.0,
            adjusted_temp=32.0,
            solar_irradiance=750.0,
        )

        sample2 = AdjustmentSample(
            facade_id="f3",
            datetime_str="15.06.2045 13:00",
            weather_datetime_str="15.06 13:00",
            solar_datetime_str="15.06.2045 12:00 MESZ",
            original_temp=26.0,
            adjusted_temp=33.0,
            solar_irradiance=650.0,
        )

        # Créer des données météo et solaires simulées
        weather_data = [
            WeatherPoint(month=6, day=15, hour=12, temperature=25.0, raw_line="raw1"),
            WeatherPoint(month=6, day=15, hour=13, temperature=26.0, raw_line="raw2"),
            WeatherPoint(month=6, day=15, hour=14, temperature=27.0, raw_line="raw3"),
        ]

        solar_data = [
            SolarPoint(
                month=6,
                day=15,
                hour=11,
                irradiance_by_facade={"f2": 750.0, "f3": 150.0},
            ),
            SolarPoint(
                month=6,
                day=15,
                hour=12,
                irradiance_by_facade={"f2": 800.0, "f3": 650.0},
            ),
        ]

        # Créer l'objet PreviewData
        preview_data = PreviewData(
            facades=["f2", "f3"],
            total_adjustments=2,
            total_data_points=3,
            adjustments_by_facade={"f2": 1, "f3": 1},
            sample_adjustments=[sample1, sample2],
            weather_data=weather_data,
            solar_data=solar_data,
            weather_file_header="Sample header",
            threshold=200.0,
            delta_t=7.0,
            weather_file_path="/path/to/weather.dat",
            solar_file_path="/path/to/solar.html",
        )

        # Vérifier les propriétés de base
        assert preview_data.facades == ["f2", "f3"]
        assert preview_data.total_adjustments == 2
        assert preview_data.total_data_points == 3
        assert preview_data.adjustments_by_facade == {"f2": 1, "f3": 1}
        assert len(preview_data.sample_adjustments) == 2

        # Vérifier les données complètes
        assert len(preview_data.weather_data) == 3
        assert len(preview_data.solar_data) == 2
        assert preview_data.weather_file_header == "Sample header"
        assert preview_data.threshold == 200.0
        assert preview_data.delta_t == 7.0
        assert preview_data.weather_file_path == "/path/to/weather.dat"
        assert preview_data.solar_file_path == "/path/to/solar.html"

        # Vérifier la propriété calculée
        assert preview_data.total_facades == 2

    def test_empty_preview_data(self):
        """Test avec des données de prévisualisation vides."""
        # Créer un objet PreviewData avec données minimales
        preview_data = PreviewData(
            facades=[],
            total_adjustments=0,
            total_data_points=0,
            adjustments_by_facade={},
            sample_adjustments=[],
            weather_data=[],
            solar_data=[],
            weather_file_header="",
            threshold=200.0,
            delta_t=7.0,
            weather_file_path="",
            solar_file_path="",
        )

        # Vérifier les valeurs
        assert preview_data.facades == []
        assert preview_data.total_adjustments == 0
        assert preview_data.total_data_points == 0
        assert preview_data.adjustments_by_facade == {}
        assert preview_data.sample_adjustments == []
        assert preview_data.total_facades == 0
