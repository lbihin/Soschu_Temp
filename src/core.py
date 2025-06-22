"""
Logique métier simplifiée pour le Soschu Temperature Tool.

Ce module contient la logique principale pour:
1. Parsing des fichiers météo et solaire
2. Calcul des ajustements de température
3. Génération des données de prévisualisation
4. Création des fichiers de sortie
"""

import logging
from parser import SolarParser, WeatherParser
from pathlib import Path
from typing import List

from preview import AdjustmentSample, PreviewData

logger = logging.getLogger(__name__)


class SoschuProcessor:
    """Processeur principal pour les ajustements de température."""

    def __init__(self):
        self.weather_parser = WeatherParser()
        self.solar_parser = SolarParser()

    def preview_adjustments(
        self, weather_file: str, solar_file: str, threshold: float, delta_t: float
    ) -> PreviewData:
        """Génère la prévisualisation des ajustements."""

        # Parser les fichiers
        weather_header, weather_data = self.weather_parser.parse(weather_file)
        solar_data = self.solar_parser.parse(solar_file)

        # Récupérer l'année depuis les données solaires (si disponible)
        year_from_solar = 2045  # Valeur par défaut
        if solar_data and hasattr(solar_data[0], "year"):
            year_from_solar = solar_data[0].year
            logger.info(f"Année extraite du fichier solar: {year_from_solar}")

            # Appliquer l'année aux données météo
            for weather_point in weather_data:
                weather_point.year = year_from_solar

        # Créer un index des données solaires pour un accès rapide (basé sur UTC)
        solar_index = {}
        for solar_point in solar_data:
            # Convertir en UTC pour la comparaison
            utc_dt = solar_point.to_datetime_utc()
            key = (utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
            solar_index[key] = solar_point

        # Calculer les ajustements
        facades = []
        if solar_data:
            facades = list(solar_data[0].irradiance_by_facade.keys())

        adjustments_by_facade = {facade: 0 for facade in facades}
        sample_adjustments = []
        total_adjustments = 0

        # Structure pour collecter des exemples par façade et par type d'heure (été/hiver)
        max_samples_per_type = 3  # Nombre maximal d'exemples par type et par façade
        samples_by_facade_and_season = {
            facade: {"winter": [], "summer": []} for facade in facades
        }
        # Pour stocker tous les ajustements possibles
        all_adjustments_by_facade_season = {
            facade: {"winter": [], "summer": []} for facade in facades
        }

        # Pour suivre les jours déjà utilisés pour les exemples
        days_used_by_facade_season = {
            facade: {"winter": set(), "summer": set()} for facade in facades
        }

        logger.info("Collecte des exemples d'ajustements pour prévisualisation...")

        # Premier passage: collecter tous les ajustements possibles
        for weather_point in weather_data:
            # Convertir en UTC pour la comparaison
            utc_dt = weather_point.to_datetime_utc()
            key = (utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)

            if key in solar_index:
                solar_point = solar_index[key]

                for facade, irradiance in solar_point.irradiance_by_facade.items():
                    if irradiance > threshold:
                        adjustments_by_facade[facade] += 1
                        total_adjustments += 1

                        # Formats date/heure dans leurs formats originaux respectifs
                        weather_datetime_str = (
                            weather_point.get_original_datetime_str()
                        )  # Format 1-24 MEZ
                        solar_datetime_str = (
                            solar_point.get_original_datetime_str()
                        )  # Format 0-23 MEZ/MESZ

                        # Format commun pour affichage
                        datetime_str = weather_datetime_str

                        # Créer l'échantillon
                        sample = AdjustmentSample(
                            facade_id=facade,
                            datetime_str=datetime_str,
                            weather_datetime_str=weather_datetime_str,
                            solar_datetime_str=solar_datetime_str,
                            original_temp=weather_point.temperature,
                            adjusted_temp=weather_point.temperature + delta_t,
                            solar_irradiance=irradiance,
                            weather_datetime_utc=utc_dt,
                            solar_datetime_utc=solar_point.to_datetime_utc(),
                        )

                        # Déterminer si c'est l'heure d'été ou d'hiver
                        season_type = "summer" if solar_point.is_dst else "winter"

                        # Ajouter à la collection des ajustements possibles
                        all_adjustments_by_facade_season[facade][season_type].append(
                            sample
                        )

        # Créer la liste finale des échantillons pour l'affichage
        sample_adjustments = []

        # Sélectionner des échantillons bien espacés pour chaque façade et type de saison
        total_possible_adjustments = 0
        for facade in facades:
            for season_type in ["winter", "summer"]:
                total_possible_adjustments += len(
                    all_adjustments_by_facade_season[facade][season_type]
                )

                if all_adjustments_by_facade_season[facade][season_type]:
                    logger.info(
                        f"Sélection d'échantillons pour {facade} ({season_type}): {len(all_adjustments_by_facade_season[facade][season_type])} disponibles"
                    )

                    # Trier les ajustements par date/heure
                    all_adjustments_by_facade_season[facade][season_type].sort(
                        key=lambda x: (
                            x.weather_datetime_utc.month,
                            x.weather_datetime_utc.day,
                            x.weather_datetime_utc.hour,
                        )
                    )

                    # Pour garantir des exemples bien espacés, on essaie de prendre des échantillons de différentes parties de l'année
                    available_samples = all_adjustments_by_facade_season[facade][
                        season_type
                    ]
                    selected_samples = []

                    if len(available_samples) <= max_samples_per_type:
                        # Si nous avons peu d'échantillons, prenons-les tous
                        selected_samples = available_samples
                    else:
                        # Diviser l'ensemble des ajustements en segments et prendre un échantillon de chaque segment
                        segment_size = len(available_samples) // max_samples_per_type

                        for i in range(max_samples_per_type):
                            idx = i * segment_size + (
                                segment_size // 2
                            )  # Prendre un échantillon au milieu de chaque segment
                            if idx < len(available_samples):
                                selected_samples.append(available_samples[idx])

                    # Vérifier que les échantillons sont suffisamment espacés (différents jours si possible)
                    final_samples = []
                    used_days = set()

                    for sample in selected_samples:
                        day_key = (
                            sample.weather_datetime_utc.month,
                            sample.weather_datetime_utc.day,
                        )

                        # Si ce jour est déjà utilisé et qu'on a d'autres options, chercher un autre jour
                        if day_key in used_days and len(final_samples) < len(
                            available_samples
                        ):
                            # Chercher un échantillon d'un autre jour
                            for alt_sample in available_samples:
                                alt_day_key = (
                                    alt_sample.weather_datetime_utc.month,
                                    alt_sample.weather_datetime_utc.day,
                                )
                                if alt_day_key not in used_days:
                                    sample = alt_sample
                                    day_key = alt_day_key
                                    break

                        used_days.add(day_key)
                        final_samples.append(sample)

                    # Ajouter les échantillons sélectionnés à notre collection finale
                    sample_adjustments.extend(final_samples)
                    logger.debug(
                        f"Ajouté {len(final_samples)} échantillons espacés pour {facade} ({season_type})"
                    )
                else:
                    logger.info(
                        f"Pas d'exemple de {season_type} disponible pour la façade {facade}"
                    )

        logger.info(
            f"Collecté {len(sample_adjustments)} exemples représentatifs sur {total_possible_adjustments} ajustements possibles"
        )

        return PreviewData(
            facades=facades,
            total_adjustments=total_adjustments,
            total_data_points=len(weather_data),
            adjustments_by_facade=adjustments_by_facade,
            sample_adjustments=sample_adjustments,
            weather_data=weather_data,
            solar_data=solar_data,
            weather_file_header=weather_header,
            threshold=threshold,
            delta_t=delta_t,
            weather_file_path=weather_file,  # Ajouter le chemin du fichier météo
            solar_file_path=solar_file,  # Ajouter le chemin du fichier solaire
        )

    def generate_files(self, preview_data: PreviewData, output_dir: str) -> List[str]:
        """Génère les fichiers de sortie basés sur les données de prévisualisation."""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Créer un index des données solaires (basé sur UTC)
        solar_index = {}
        for solar_point in preview_data.solar_data:
            # Convertir en UTC pour la comparaison
            utc_dt = solar_point.to_datetime_utc()
            key = (utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
            solar_index[key] = solar_point

        # Générer un fichier par façade
        for facade in preview_data.facades:
            # Récupérer le nom de base du fichier météo original
            weather_file_name = Path(preview_data.weather_file_path).stem

            # Créer le nouveau format de nom de fichier: <nom du fichier .dat>_<facade building body>.dat
            filename = f"{weather_file_name}_{facade.replace(' ', '_')}.dat"
            output_file = output_path / filename

            with open(output_file, "w", encoding="iso-8859-1") as f:
                # Écrire le header
                f.write(preview_data.weather_file_header)

                # Écrire les données ajustées
                for weather_point in preview_data.weather_data:
                    # Convertir en UTC pour la comparaison
                    utc_dt = weather_point.to_datetime_utc()
                    key = (
                        utc_dt.year,
                        utc_dt.month,
                        utc_dt.day,
                        utc_dt.hour,
                        utc_dt.minute,
                    )

                    # Vérifier s'il faut ajuster la température pour cette façade
                    adjusted_temp = weather_point.temperature
                    if key in solar_index:
                        solar_point = solar_index[key]
                        irradiance = solar_point.irradiance_by_facade.get(facade, 0)

                        if irradiance > preview_data.threshold:
                            adjusted_temp = (
                                weather_point.temperature + preview_data.delta_t
                            )
                            logger.debug(
                                f"Ajustement pour {facade}: {weather_point.get_original_datetime_str()} (DAT) -> "
                                f"{solar_point.get_original_datetime_str()} (HTML), "
                                f"Irradiance: {irradiance:.1f}, "
                                f"Temp: {weather_point.temperature:.1f} -> {adjusted_temp:.1f}"
                            )

                    adjusted_temperature_str = f"{adjusted_temp:.1f}".rjust(5)
                    raw_line = weather_point.raw_line

                    # Reconstruire la ligne en préservant tout le formatage original
                    adjusted_line = (
                        raw_line[:25] + adjusted_temperature_str + raw_line[25 + 5 :]
                    )

                    f.write(adjusted_line)

            generated_files.append(str(output_file))
            logger.info(f"Generated file: {output_file}")

        return generated_files
