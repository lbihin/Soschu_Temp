"""
Tests de comparaison des fichiers de sortie pour le Soschu Temperature Tool.

Ce module compare les fichiers générés par le processeur avec les fichiers
de référence validés manuellement.
"""

import filecmp
import os
import tempfile
from pathlib import Path

import pytest

from core import SoschuProcessor


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


@pytest.fixture
def reference_output_dir():
    """Chemin vers le répertoire contenant les fichiers de sortie de référence."""
    return str(Path(__file__).parent / "data" / "outputs")


class TestOutputFileComparison:
    """Tests de comparaison des fichiers de sortie."""

    @pytest.mark.integration
    def test_generated_files_match_reference(
        self, sample_weather_file, sample_solar_file, reference_output_dir
    ):
        """Vérifie que les fichiers générés correspondent aux fichiers de référence."""
        # Vérifier que les fichiers d'entrée existent
        assert Path(
            sample_weather_file
        ).exists(), "Le fichier météo d'exemple n'existe pas"
        assert Path(
            sample_solar_file
        ).exists(), "Le fichier solaire d'exemple n'existe pas"

        # Vérifier que le répertoire de référence existe
        assert Path(
            reference_output_dir
        ).exists(), "Le répertoire de référence n'existe pas"

        # Initialiser le processeur
        processor = SoschuProcessor()

        # Créer un répertoire temporaire pour les fichiers de sortie générés
        with tempfile.TemporaryDirectory() as temp_dir:
            # Générer les données de prévisualisation
            preview_data = processor.preview_adjustments(
                weather_file=sample_weather_file,
                solar_file=sample_solar_file,
                threshold=200.0,
                delta_t=7.0,
            )

            # Générer les fichiers
            generated_files = processor.generate_files(preview_data, temp_dir)

            # Vérifier que des fichiers ont été générés
            assert len(generated_files) > 0, "Aucun fichier n'a été généré"

            # Lister les fichiers de référence
            reference_files = [
                str(p) for p in Path(reference_output_dir).glob("*") if p.is_file()
            ]

            # Vérifier que le nombre de fichiers générés correspond au nombre de fichiers de référence
            assert len(generated_files) == len(reference_files), (
                f"Le nombre de fichiers générés ({len(generated_files)}) ne correspond pas "
                f"au nombre de fichiers de référence ({len(reference_files)})"
            )

            # Pour chaque fichier généré, trouver son correspondant dans les fichiers de référence et comparer
            for gen_file_path in generated_files:
                gen_file_name = Path(gen_file_path).name
                ref_file_path = str(Path(reference_output_dir) / gen_file_name)

                # Vérifier que le fichier de référence correspondant existe
                assert Path(
                    ref_file_path
                ).exists(), f"Le fichier de référence correspondant à {gen_file_name} n'existe pas"

                # Comparer les deux fichiers
                are_identical = filecmp.cmp(gen_file_path, ref_file_path, shallow=False)

                # En cas d'échec, afficher les différences
                if not are_identical:
                    # Lire les deux fichiers pour trouver les différences
                    with open(
                        gen_file_path, "r", encoding="iso-8859-1"
                    ) as gen_file, open(
                        ref_file_path, "r", encoding="iso-8859-1"
                    ) as ref_file:

                        gen_lines = gen_file.readlines()
                        ref_lines = ref_file.readlines()

                        # Trouver la première différence
                        diff_line_num = None
                        for i, (gen_line, ref_line) in enumerate(
                            zip(gen_lines, ref_lines)
                        ):
                            if gen_line != ref_line:
                                diff_line_num = i + 1
                                break

                        if diff_line_num is None and len(gen_lines) != len(ref_lines):
                            diff_line_num = min(len(gen_lines), len(ref_lines)) + 1

                        message = (
                            f"Fichier {gen_file_name} diffère du fichier de référence"
                        )
                        if diff_line_num is not None:
                            message += f" à la ligne {diff_line_num}"

                        pytest.fail(message)

                assert (
                    are_identical
                ), f"Le fichier {gen_file_name} diffère du fichier de référence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
