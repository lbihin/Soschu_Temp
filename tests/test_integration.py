"""
Tests d'intégration pour le Soschu Temperature Tool.

Ce module teste le comportement complet de l'application en intégrant
les différents composants et modules ensemble.
"""

import tempfile
from parser import SolarParser, WeatherParser
from pathlib import Path

import pytest

from core import SoschuProcessor
from preview import PreviewData


@pytest.fixture
def sample_weather_file():
    """Fixture pour un fichier météo de test."""
    return str(Path(__file__).parent / "data" / "TRY2045_488284093163_Jahr.dat")


@pytest.fixture
def sample_solar_file():
    """Fixture pour un fichier solaire de test."""
    return str(
        Path(__file__).parent / "data" / "Solare Einstrahlung auf die Fassade.html"
    )


class TestEndToEndWorkflow:
    """Tests pour le workflow complet de l'application."""

    def test_complete_processing_pipeline(self, sample_weather_file, sample_solar_file):
        """Test le pipeline complet de traitement des données."""
        # Vérifier que les fichiers existent
        if not Path(sample_weather_file).exists():
            pytest.skip("Fichier météo d'exemple non disponible")
        if not Path(sample_solar_file).exists():
            pytest.skip("Fichier solaire d'exemple non disponible")

        # Initialiser le processeur
        processor = SoschuProcessor()

        # Créer un répertoire temporaire pour les fichiers de sortie
        with tempfile.TemporaryDirectory() as temp_dir:
            # Exécuter la prévisualisation
            preview_data = processor.preview_adjustments(
                weather_file=sample_weather_file,
                solar_file=sample_solar_file,
                threshold=200.0,
                delta_t=7.0,
            )

            # Vérifier la structure des données de prévisualisation
            assert isinstance(preview_data, PreviewData)
            assert len(preview_data.facades) > 0
            assert preview_data.total_data_points > 0

            # Vérifier que certaines façades ont des ajustements
            assert preview_data.total_adjustments > 0
            assert any(
                count > 0 for count in preview_data.adjustments_by_facade.values()
            )

            # Vérifier les échantillons d'ajustement
            assert len(preview_data.sample_adjustments) > 0
            for sample in preview_data.sample_adjustments:
                # La température ajustée devrait être plus élevée que l'originale
                assert sample.adjusted_temp > sample.original_temp
                # La différence devrait être égale à delta_t (7.0)
                assert sample.adjusted_temp - sample.original_temp == pytest.approx(7.0)

            # TODO: Ajouter test de génération de fichiers de sortie
            # Une fois que la méthode d'export est implémentée dans SoschuProcessor

    def test_data_synchronization(self, sample_weather_file, sample_solar_file):
        """Test la synchronisation entre les données météo et solaires."""
        # Vérifier que les fichiers existent
        if (
            not Path(sample_weather_file).exists()
            or not Path(sample_solar_file).exists()
        ):
            pytest.skip("Fichiers d'exemple non disponibles")

        # Parser les fichiers séparément
        weather_parser = WeatherParser()
        solar_parser = SolarParser()

        weather_header, weather_data = weather_parser.parse(sample_weather_file)
        solar_data = solar_parser.parse(sample_solar_file)

        # Vérifier qu'on a des données
        assert len(weather_data) > 0
        assert len(solar_data) > 0

        # Exécuter le processus complet
        processor = SoschuProcessor()
        preview_data = processor.preview_adjustments(
            weather_file=sample_weather_file,
            solar_file=sample_solar_file,
            threshold=200.0,
            delta_t=7.0,
        )

        # Vérifier que les données temporelles sont correctement alignées dans les échantillons
        for sample in preview_data.sample_adjustments:
            # Les horodatages UTC devraient être proches ou identiques
            if sample.weather_datetime_utc and sample.solar_datetime_utc:
                # Calculer la différence en heures
                time_diff = abs(
                    (
                        sample.weather_datetime_utc - sample.solar_datetime_utc
                    ).total_seconds()
                    / 3600
                )
                # La différence devrait être minimale (idéalement moins d'une heure)
                assert (
                    time_diff <= 1.0
                ), f"Écart temporel trop important: {time_diff} heures"


class TestScenarioSpecifiques:
    """Tests de différents scénarios spécifiques."""

    def test_seuil_ajustement(self, sample_weather_file, sample_solar_file):
        """Test l'effet du seuil sur les ajustements de température."""
        # Vérifier que les fichiers existent
        if (
            not Path(sample_weather_file).exists()
            or not Path(sample_solar_file).exists()
        ):
            pytest.skip("Fichiers d'exemple non disponibles")

        # Initialiser le processeur
        processor = SoschuProcessor()

        # Tester avec différentes valeurs de seuil
        seuils = [50.0, 200.0, 500.0]
        resultats = []

        for seuil in seuils:
            preview = processor.preview_adjustments(
                weather_file=sample_weather_file,
                solar_file=sample_solar_file,
                threshold=seuil,
                delta_t=7.0,
            )
            resultats.append(preview.total_adjustments)

        # Vérifier que le nombre d'ajustements diminue lorsque le seuil augmente
        assert (
            resultats[0] >= resultats[1] >= resultats[2]
        ), "Le nombre d'ajustements devrait diminuer avec l'augmentation du seuil"

    def test_delta_t_impact(self, sample_weather_file, sample_solar_file):
        """Test l'impact du delta_t sur les ajustements de température."""
        # Vérifier que les fichiers existent
        if (
            not Path(sample_weather_file).exists()
            or not Path(sample_solar_file).exists()
        ):
            pytest.skip("Fichiers d'exemple non disponibles")

        # Initialiser le processeur
        processor = SoschuProcessor()

        # Tester avec une valeur fixe de seuil et deux valeurs de delta_t
        preview1 = processor.preview_adjustments(
            weather_file=sample_weather_file,
            solar_file=sample_solar_file,
            threshold=200.0,
            delta_t=5.0,
        )

        preview2 = processor.preview_adjustments(
            weather_file=sample_weather_file,
            solar_file=sample_solar_file,
            threshold=200.0,
            delta_t=10.0,
        )

        # Vérifier que le nombre d'ajustements est identique (dépend uniquement du seuil)
        assert preview1.total_adjustments == preview2.total_adjustments

        # Vérifier que la différence d'ajustement est bien appliquée
        if preview1.sample_adjustments:
            for i in range(min(3, len(preview1.sample_adjustments))):
                sample1 = preview1.sample_adjustments[i]
                sample2 = preview2.sample_adjustments[i]

                # Même point mais delta_t différent
                assert sample1.facade_id == sample2.facade_id
                assert sample1.original_temp == sample2.original_temp

                # La différence entre ajusté et original devrait correspondre au delta_t
                assert sample1.adjusted_temp - sample1.original_temp == pytest.approx(
                    5.0
                )
                assert sample2.adjusted_temp - sample2.original_temp == pytest.approx(
                    10.0
                )


class TestPerformanceIntegration:
    """Tests de performance."""

    def test_processing_time(self, sample_weather_file, sample_solar_file):
        """Test que le processus s'exécute dans un temps raisonnable."""
        # Vérifier que les fichiers existent
        if (
            not Path(sample_weather_file).exists()
            or not Path(sample_solar_file).exists()
        ):
            pytest.skip("Fichiers d'exemple non disponibles")

        import time

        # Initialiser le processeur
        processor = SoschuProcessor()

        # Mesurer le temps d'exécution
        start_time = time.time()

        # Exécuter la prévisualisation
        preview_data = processor.preview_adjustments(
            weather_file=sample_weather_file,
            solar_file=sample_solar_file,
            threshold=200.0,
            delta_t=7.0,
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # Vérifier que le traitement s'est fait dans un temps raisonnable
        assert (
            processing_time < 30.0
        ), f"Temps de traitement trop long: {processing_time:.2f} secondes"
        print(
            f"Temps de traitement: {processing_time:.2f} secondes pour {preview_data.total_data_points} points de données"
        )


if __name__ == "__main__":
    # Setup logging for test runs
    import logging

    logging.basicConfig(level=logging.INFO)

    # Run tests
    pytest.main([__file__, "-v"])
