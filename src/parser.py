from datetime import datetime, timedelta
import logging
import re
from typing import List, Tuple

from constants import MEZ_TIMEZONE
from solar import SolarPoint
from weather import WeatherPoint


logger = logging.getLogger(__name__)

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
        facade_pattern = r"Gesamte solare Einstrahlung,\s*(f[\da-zA-Z]+(?:\$[^\s,]+(?: [^\s,]+)?)?),\s*W/m2"
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
                # for j in range(1, min(len(facades) + 1, 5)):  # Limite à 5 lignes suivantes
                for j in range(1, len(facades) + 1):
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
