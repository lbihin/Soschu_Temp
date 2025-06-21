#!/usr/bin/env python3
"""
Script de test pour la nouvelle architecture simplifiée de Soschu.
Ce script teste les parsers et la logique métier avec des données de test.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from core_logic import SoschuProcessor


def test_with_sample_files():
    """Test avec les fichiers d'exemple du projet."""

    # Chemins vers les fichiers de test existants
    root_dir = Path(__file__).parent.parent
    weather_file = root_dir / "tests" / "data" / "TRY2045_488284093163_Jahr.dat"
    solar_file = (
        root_dir / "tests" / "data" / "Solare Einstrahlung auf die Fassade.html"
    )

    print("=== Test de la nouvelle architecture Soschu ===")

    # Vérifier que les fichiers existent
    if not weather_file.exists():
        print(f"❌ Fichier météo introuvable: {weather_file}")
        return False

    if not solar_file.exists():
        print(f"❌ Fichier solaire introuvable: {solar_file}")
        return False

    print(f"✅ Fichiers trouvés:")
    print(f"   Météo: {weather_file.name}")
    print(f"   Solaire: {solar_file.name}")

    try:
        # Créer le processeur
        processor = SoschuProcessor()

        # Test de prévisualisation
        print("\n📊 Test de prévisualisation...")
        preview_data = processor.preview_adjustments(
            weather_file=str(weather_file),
            solar_file=str(solar_file),
            threshold=200.0,
            delta_t=7.0,
        )

        print(f"✅ Prévisualisation terminée:")
        print(f"   Façades trouvées: {len(preview_data.facades)}")
        for facade in preview_data.facades:
            count = preview_data.adjustments_by_facade.get(facade, 0)
            print(f"   - {facade}: {count:,} ajustements")

        print(f"   Total ajustements: {preview_data.total_adjustments:,}")
        print(f"   Points de données: {preview_data.total_data_points:,}")
        print(f"   Échantillons collectés: {len(preview_data.sample_adjustments)}")

        # Afficher quelques échantillons
        print("\n📋 Échantillons d'ajustements:")
        for i, sample in enumerate(preview_data.sample_adjustments[:5]):
            print(
                f"   {i+1}. {sample.facade_id} - {sample.datetime_str}: "
                f"{sample.original_temp:.1f}°C → {sample.adjusted_temp:.1f}°C "
                f"(☀️ {sample.solar_irradiance:.0f} W/m²)"
            )

        # Test de génération
        print("\n📁 Test de génération de fichiers...")
        output_dir = root_dir / "test_output_simple"
        generated_files = processor.generate_files(
            preview_data=preview_data, output_dir=str(output_dir)
        )

        print(f"✅ Génération terminée:")
        for file_path in generated_files:
            file_size = Path(file_path).stat().st_size
            print(f"   - {Path(file_path).name} ({file_size:,} bytes)")

        print(f"\n🎉 Test terminé avec succès!")
        print(f"   Fichiers générés dans: {output_dir}")

        return True

    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_sample_files()
    sys.exit(0 if success else 1)
