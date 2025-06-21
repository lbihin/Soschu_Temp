"""
Logique métier simplifiée pour le Soschu Temperature Tool.

Ce module contient la logique principale pour:
1. Parsing des fichiers météo et solaire
2. Calcul des ajustements de température
3. Génération des données de prévisualisation
4. Création des fichiers de sortie
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz

logger = logging.getLogger(__name__)

# Définition de la timezone MEZ/MESZ (Europe/Berlin)
MEZ_TIMEZONE = pytz.timezone("Europe/Berlin")


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


@dataclass
class SolarPoint:
    """Point de données solaire simplifié."""

    month: int
    day: int
    hour: int  # 0-23 format (MEZ/MESZ)
    irradiance_by_facade: Dict[str, float]
    is_dst: bool = False  # Flag pour indiquer si c'est l'heure d'été
    year: int = 2045  # Année extraite du fichier HTML

    def to_datetime_utc(self) -> datetime:
        """
        Convertit l'heure HTML (0-23 MEZ/MESZ) vers UTC pour la comparaison.
        Les fichiers HTML tiennent compte du passage à l'heure d'été (MESZ).
        Utilise l'année extraite du fichier HTML.
        """
        # Créer un datetime naïf
        dt_naive = datetime(self.year, self.month, self.day, self.hour, 0, 0)

        # Appliquer la timezone MEZ/MESZ (Europe/Berlin)
        dt_local = MEZ_TIMEZONE.localize(dt_naive, is_dst=self.is_dst)

        # Convertir en UTC
        dt_utc = dt_local.astimezone(timezone.utc)

        return dt_utc

    def get_original_datetime_str(self) -> str:
        """Renvoie la date/heure au format original du fichier HTML (0-23 MEZ/MESZ)"""
        time_suffix = "MESZ" if self.is_dst else "MEZ"
        return f"{self.day:02d}.{self.month:02d}.{self.year} {self.hour:02d}:00 {time_suffix}"


@dataclass
class AdjustmentSample:
    """Échantillon d'ajustement pour la prévisualisation."""

    facade_id: str
    datetime_str: str  # Format commun pour affichage
    weather_datetime_str: str  # Format date/heure pour le fichier météo DAT (1-24 MEZ)
    solar_datetime_str: (
        str  # Format date/heure pour le fichier solaire HTML (0-23 MEZ/MESZ)
    )
    original_temp: float
    adjusted_temp: float
    solar_irradiance: float
    weather_datetime_utc: Optional[datetime] = None  # Timestamp UTC du point météo
    solar_datetime_utc: Optional[datetime] = None  # Timestamp UTC du point solaire


@dataclass
class PreviewData:
    """Données pour la prévisualisation."""

    facades: List[str]
    total_adjustments: int
    total_data_points: int
    adjustments_by_facade: Dict[str, int]
    sample_adjustments: List[AdjustmentSample]

    # Données complètes pour la génération
    weather_data: List[WeatherPoint]
    solar_data: List[SolarPoint]
    weather_file_header: str
    threshold: float
    delta_t: float

    @property
    def total_facades(self) -> int:
        return len(self.facades)


class WeatherParser:
    """Parser simplifié pour les fichiers météo .dat."""

    def parse(self, file_path: str, year: int = 2045) -> Tuple[str, List[WeatherPoint]]:
        """
        Parse le fichier météo et retourne le header et les données.

        Args:
            file_path: Chemin du fichier météo
            year: Année à utiliser (par défaut 2045)

        Returns:
            Tuple[header, weather_points]
        """
        with open(file_path, "r", encoding="iso-8859-1") as f:
            lines = f.readlines()

        # Trouver où commence les données (après "*** ")
        data_start = 0
        header_lines = []

        # Analyser le format du fichier pour déterminer la position exacte de la température
        format_line = None
        temp_position = (0, 0)  # (début, fin) de la position de température

        for i, line in enumerate(lines):
            if line.strip().startswith("Format:"):
                format_line = line.strip()

            if line.strip().startswith("***"):
                header_lines.append(line)
                data_start = i + 1
                break
            else:
                header_lines.append(line)

        # Si le format est spécifié, on l'analyse pour déterminer la position de la température
        if format_line:
            logger.info(f"Format détecté: {format_line}")
            # Le format indique que la température est au 6ème champ (f5.1)
            # Les positions sont calculables à partir de ce format

        header = "".join(header_lines)
        weather_points = []

        # Parser les lignes de données (ignorer les lignes vides et les commentaires)
        for line in lines[data_start:]:
            line = line.strip()
            if line and not line.startswith("*"):
                try:
                    parts = line.split()
                    if len(parts) >= 17:  # S'assurer qu'on a tous les champs
                        # Format: RW HW MM DD HH t p WR WG N x RF B D A E IL
                        weather_points.append(
                            WeatherPoint(
                                month=int(parts[2]),
                                day=int(parts[3]),
                                hour=int(parts[4]),  # Format 1-24
                                temperature=float(parts[5]),
                                raw_line=line + "\n",  # Ajouter le retour à la ligne
                                year=year,  # Utiliser l'année fournie
                            )
                        )
                except (ValueError, IndexError) as e:
                    logger.warning(f"Impossible de parser la ligne: {line}: {e}")

        logger.info(f"Parsed {len(weather_points)} weather points from {file_path}")
        return header, weather_points


class SolarParser:
    """Parser simplifié pour les fichiers solaire HTML."""

    def parse(self, file_path: str, year: int = 2045) -> List[SolarPoint]:
        """Parse le fichier HTML et retourne les données solaires."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Rechercher les façades dans les headers du tableau
        # Pattern: "Gesamte solare Einstrahlung, f3$Building body, W/m2"
        facade_pattern = r"Gesamte solare Einstrahlung, (f\d+\$Building body\d*), W/m2"
        facades = re.findall(facade_pattern, content)

        # Nettoyer les noms de façades (remplacer $ par espace)
        facades = [facade.replace("$", " ") for facade in facades]

        logger.info(f"Found facades: {facades}")

        solar_points = []

        # Rechercher les lignes de données avec regex
        # Pattern pour les lignes complètes avec date et valeurs
        data_pattern = r"<td class=value>(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2})"

        # Diviser le contenu en lignes pour faciliter le parsing
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]

            # Chercher une ligne avec date/heure
            date_match = re.search(data_pattern, line)
            if date_match:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3))
                hour = int(date_match.group(4))  # Format 0-23 dans le HTML
                minute = int(date_match.group(5))

                # Déterminer si c'est l'heure d'été (MESZ) ou l'heure d'hiver (MEZ)
                dt_naive = datetime(year, month, day, hour, minute)
                dt_aware = MEZ_TIMEZONE.localize(dt_naive)
                is_dst = dt_aware.dst() != timedelta(0)

                # Chercher les valeurs dans les lignes suivantes
                irradiance_values = {}

                # Rechercher les valeurs numériques dans les lignes suivantes
                for j in range(
                    1, min(len(facades) + 1, 5)
                ):  # Limite à 5 lignes suivantes
                    if i + j < len(lines):
                        value_line = lines[i + j]
                        value_match = re.search(
                            r"<td class=value>([0-9.]+)", value_line
                        )
                        if value_match and j - 1 < len(facades):
                            try:
                                value = float(value_match.group(1))
                                facade_name = facades[j - 1]
                                irradiance_values[facade_name] = value
                            except (ValueError, IndexError):
                                pass

                # Si on a trouvé des valeurs, créer le point solaire
                if irradiance_values:
                    solar_points.append(
                        SolarPoint(
                            month=month,
                            day=day,
                            hour=hour,  # Format 0-23
                            irradiance_by_facade=irradiance_values,
                            is_dst=is_dst,  # Ajouter le drapeau d'heure d'été
                            year=year,  # Ajouter l'année extraite du fichier HTML
                        )
                    )

                    # Log pour le debugging
                    dst_info = "MESZ" if is_dst else "MEZ"
                    logger.debug(
                        f"Parsed solar point: {year}, {month:02d}/{day:02d} {hour:02d}:{minute:02d} ({dst_info})"
                    )

                # Avancer dans le fichier
                i += len(facades) + 1
            else:
                i += 1

        logger.info(
            f"Parsed {len(solar_points)} solar points with {len(facades)} facades"
        )
        return solar_points


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
            filename = f"{facade.replace(' ', '_')}.dat"
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

                    # Méthode ultra-précise pour remplacer uniquement la température
                    # tout en préservant exactement le format original (espaces, tabulations)
                    raw_line = weather_point.raw_line

                    # Analysons manuellement pour localiser précisément la température
                    # La température est le 6ème champ, après HH (heure)

                    # Étape 1: Extraire et compter les caractères non-espaces jusqu'au 5ème champ
                    parts = []
                    current_part = ""
                    in_part = False

                    for char in raw_line:
                        if not char.isspace():
                            current_part += char
                            in_part = True
                        elif in_part:
                            parts.append(current_part)
                            current_part = ""
                            in_part = False
                            if (
                                len(parts) == 5
                            ):  # Nous avons atteint la fin du 5ème champ
                                break

                    # Étape 2: Trouver la position exacte où commence le champ de température
                    position = 0
                    field_count = 0
                    in_field = False

                    for i, char in enumerate(raw_line):
                        if not char.isspace() and not in_field:
                            in_field = True
                        elif char.isspace() and in_field:
                            field_count += 1
                            in_field = False
                            if field_count == 5:  # Fin du 5ème champ
                                position = i + 1
                                break

                    # Étape 3: Chercher le début exact de la valeur de température
                    while position < len(raw_line) and raw_line[position].isspace():
                        position += 1

                    # Étape 4: Trouver la fin du champ de température
                    temp_start = position
                    while position < len(raw_line) and not raw_line[position].isspace():
                        position += 1
                    temp_end = position

                    # Étape 5: Remplacer la température en conservant le format
                    original_temp_str = raw_line[temp_start:temp_end]
                    new_temp_str = f"{adjusted_temp:.1f}"

                    # Conserver la même largeur
                    if len(new_temp_str) < len(original_temp_str):
                        # Aligner à droite pour préserver le formatage
                        new_temp_str = (
                            " " * (len(original_temp_str) - len(new_temp_str))
                            + new_temp_str
                        )
                    elif len(new_temp_str) > len(original_temp_str):
                        # Cas rare, mais gérons-le
                        logger.warning(
                            f"La nouvelle température {new_temp_str} est plus longue que l'originale {original_temp_str}"
                        )
                        # Tronquer si nécessaire
                        new_temp_str = new_temp_str[: len(original_temp_str)]

                    # Reconstruire la ligne en préservant tout le formatage original
                    adjusted_line = (
                        raw_line[:temp_start] + new_temp_str + raw_line[temp_end:]
                    )

                    f.write(adjusted_line)

            generated_files.append(str(output_file))
            logger.info(f"Generated file: {output_file}")

        return generated_files
