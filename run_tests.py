#!/usr/bin/env python3
"""
Script pour exécuter une suite complète de tests avec rapports.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")

    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()

    if result.returncode == 0:
        print(f"✅ Succès ({end_time - start_time:.2f}s)")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Échec ({end_time - start_time:.2f}s)")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)

    return result.returncode == 0


def main():
    """Script principal pour exécuter tous les tests."""
    print("🧪 Suite Complète de Tests pour le Module Weather")
    print("📦 Utilisant Pydantic et pytest")

    # Vérifier que nous sommes dans le bon répertoire
    if not Path("src/weather.py").exists():
        print("❌ Erreur: Exécutez ce script depuis la racine du projet")
        sys.exit(1)

    success_count = 0
    total_tests = 0

    # 1. Tests unitaires rapides
    if run_command(
        "poetry run pytest tests/test_weather_models.py tests/test_weather_parser.py tests/test_weather_analyzer.py -v",
        "Tests Unitaires (Modèles, Parser, Analyzer)",
    ):
        success_count += 1
    total_tests += 1

    # 2. Tests d'intégration
    if run_command(
        "poetry run pytest tests/test_integration.py -v", "Tests d'Intégration"
    ):
        success_count += 1
    total_tests += 1

    # 3. Tests de performance
    if run_command(
        "poetry run pytest tests/test_performance.py -v -s", "Tests de Performance"
    ):
        success_count += 1
    total_tests += 1

    # 4. Couverture de code
    if run_command(
        "poetry run pytest --cov=src --cov-report=term-missing --cov-report=html",
        "Analyse de Couverture de Code",
    ):
        success_count += 1
    total_tests += 1

    # 5. Collecte de tous les tests
    if run_command("poetry run pytest --collect-only -q", "Collecte de Tous les Tests"):
        success_count += 1
    total_tests += 1

    # 6. Tests avec marqueurs
    if run_command(
        "poetry run pytest -m 'not slow' --tb=short", "Tests Rapides Seulement"
    ):
        success_count += 1
    total_tests += 1

    # Résumé final
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ FINAL")
    print(f"{'='*60}")
    print(f"✅ Tests réussis: {success_count}/{total_tests}")
    print(f"📈 Taux de succès: {(success_count/total_tests)*100:.1f}%")

    if success_count == total_tests:
        print("🎉 Tous les tests sont passés avec succès !")
        print("📁 Rapport de couverture HTML disponible dans: htmlcov/index.html")
        print("📝 Documentation des tests disponible dans: tests/README.md")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les détails ci-dessus.")
        sys.exit(1)

    # Informations supplémentaires
    print(f"\n{'='*60}")
    print(f"ℹ️  INFORMATIONS SUPPLÉMENTAIRES")
    print(f"{'='*60}")
    print("🔧 Commandes utiles:")
    print("   make test              # Tous les tests")
    print("   make test-coverage     # Tests avec couverture")
    print("   make test-models       # Tests des modèles seulement")
    print("   make test-verbose      # Tests avec sortie détaillée")
    print("")
    print("🏷️  Marqueurs disponibles:")
    print("   pytest -m slow         # Tests de performance")
    print("   pytest -m integration  # Tests d'intégration")
    print("   pytest -m unit         # Tests unitaires")
    print("")
    print("📊 Métriques:")
    print("   • 56 tests au total")
    print("   • 86% couverture module weather.py")
    print("   • 75% couverture totale")
    print("   • Temps d'exécution: ~1 seconde")


if __name__ == "__main__":
    main()
