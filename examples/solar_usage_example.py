#!/usr/bin/env python3
"""
Exemple d'utilisation du module solar pour parser et analyser des données d'irradiation solaire.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer src
sys.path.append(str(Path(__file__).parent.parent))

from src.solar import SolarDataAnalyzer, SolarDataParser


def main():
    """Exemple principal d'utilisation du module solar."""

    # Chemin vers le fichier de test
    test_file = Path("tests/data/solar_test_small.html")

    if not test_file.exists():
        print(f"Fichier de test non trouvé: {test_file}")
        return

    print("🌞 Exemple d'utilisation du module Solar")
    print("=" * 50)

    # 1. Parser le fichier HTML
    print("\n1. Parsing du fichier HTML...")
    parser = SolarDataParser()

    try:
        metadata, data_points = parser.parse_file(str(test_file))
        print(f"✅ Fichier parsé avec succès !")
        print(f"   - {len(data_points)} points de données")
        print(f"   - {len(metadata.facade_columns)} façades")
    except Exception as e:
        print(f"❌ Erreur lors du parsing: {e}")
        return

    # 2. Afficher les métadonnées
    print("\n2. Métadonnées extraites:")
    print(f"   - Titre: {metadata.title}")
    print(f"   - Objet: {metadata.object_name}")
    print(f"   - Date simulation: {metadata.simulation_date}")

    # 3. Analyser les orientations de façades
    print("\n3. Analyse des façades:")
    orientations = metadata.get_facade_orientations()
    building_bodies = metadata.get_building_bodies()
    print(f"   - Orientations: {', '.join(orientations)}")
    print(f"   - Corps de bâtiments: {', '.join(building_bodies)}")

    # 4. Analyser les données
    print("\n4. Analyse des données d'irradiation:")
    analyzer = SolarDataAnalyzer(data_points)

    # Statistiques par façade
    stats = analyzer.get_irradiance_stats()
    print("\n   Statistiques par façade:")
    for facade, facade_stats in stats.items():
        facade_short = facade.split(",")[1].strip()  # Extraire juste "f3$Building body"
        print(f"   - {facade_short}:")
        print(f"     • Max: {facade_stats['max']:.1f} W/m²")
        print(f"     • Moyenne: {facade_stats['mean']:.1f} W/m²")
        print(f"     • Total annuel: {facade_stats['total_kwh']:.1f} kWh")

    # 5. Périodes de forte irradiation
    print("\n5. Périodes de forte irradiation (> 100 W/m²):")
    peak_periods = analyzer.get_peak_irradiance_periods(threshold=100.0)
    print(f"   - {len(peak_periods)} périodes trouvées")

    if peak_periods:
        print("   - Exemples:")
        for i, period in enumerate(peak_periods[:3]):  # Afficher les 3 premières
            facade, max_value = period.get_max_facade_irradiance()
            facade_short = facade.split(",")[1].strip() if "," in facade else facade
            print(
                f"     • {period.timestamp.strftime('%d.%m.%Y %H:%M')}: "
                f"{max_value:.1f} W/m² ({facade_short})"
            )

    # 6. Totaux journaliers
    print("\n6. Totaux journaliers:")
    daily_totals = analyzer.get_daily_totals()
    for date, totals in daily_totals.items():
        total_day = sum(totals.values())
        print(f"   - {date}: {total_day:.1f} kWh total")

    # 7. Analyse de qualité
    print("\n7. Qualité des données:")
    quality = analyzer.validate_data_quality()
    print(f"   - Score de qualité: {quality['quality_score']:.1%}")
    print(f"   - Points de données: {quality['total_points']}")
    if quality["issues"]:
        print(f"   - Problèmes détectés: {len(quality['issues'])}")
        for issue in quality["issues"][:3]:  # Afficher les 3 premiers
            print(f"     • {issue}")
    else:
        print("   - ✅ Aucun problème majeur détecté")

    # 8. Export des données
    print("\n8. Export CSV:")
    output_file = Path("solar_example_export.csv")
    analyzer.export_to_csv(str(output_file))
    print(f"   - Données exportées vers: {output_file}")
    print(f"   - Taille du fichier: {output_file.stat().st_size} bytes")

    print("\n" + "=" * 50)
    print("✨ Exemple terminé avec succès !")
    print(f"📁 Rapport HTML disponible dans htmlcov/ (après 'make test-coverage')")
    print(f"📄 Documentation complète dans docs/solar_module.md")


if __name__ == "__main__":
    main()
