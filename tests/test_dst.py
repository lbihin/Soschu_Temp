#!/usr/bin/env python3
"""
Fonction précise pour détecter l'heure d'été avec pytz
"""

import pytz
from datetime import datetime


def is_dst_precise(month: int, day: int, year: int = 2024) -> bool:
    """
    Détermine précisément si une date est en heure d'été (MESZ)
    en utilisant pytz avec la timezone Europe/Berlin.

    Args:
        month: Mois (1-12)
        day: Jour (1-31)
        year: Année (optionnel, défaut 2024)

    Returns:
        True si la date est en MESZ (heure d'été), False sinon (MEZ)
    """
    try:
        tz = pytz.timezone("Europe/Berlin")
        dt = datetime(year, month, day, 12, 0)  # Midi pour éviter les ambiguïtés
        localized_dt = tz.localize(dt)
        # Si l'offset UTC est +2h, c'est MESZ (été), sinon c'est MEZ (hiver)
        return localized_dt.utcoffset().total_seconds() == 7200  # 2h = 7200s
    except:
        # En cas d'erreur, utiliser l'approximation simple
        return is_dst_simple(month, day)


def is_dst_simple(month: int, day: int) -> bool:
    """
    Approximation simple pour détecter l'heure d'été sans dépendances externes.
    MESZ du dernier dimanche de mars au dernier dimanche d'octobre.
    """
    if month < 3 or month > 10:
        return False  # Janvier, février, novembre, décembre = MEZ
    elif month > 3 and month < 10:
        return True  # Avril à septembre = MESZ
    elif month == 3:
        return day >= 25  # Fin mars, approximation
    elif month == 10:
        return day <= 25  # Début octobre, approximation
    else:
        return False


# Test les deux méthodes
if __name__ == "__main__":
    test_dates = [
        (3, 30),
        (3, 31),
        (4, 1),  # Transition printemps
        (6, 21),
        (8, 15),  # Été
        (10, 26),
        (10, 27),
        (10, 28),  # Transition automne
        (1, 15),
        (12, 21),  # Hiver
    ]

    print("Comparaison des méthodes de détection DST :")
    print("=" * 50)

    for month, day in test_dates:
        precise = is_dst_precise(month, day)
        simple = is_dst_simple(month, day)
        match = "✓" if precise == simple else "✗"
        print(f"{month:02d}-{day:02d}: Précise={precise}, Simple={simple} {match}")
