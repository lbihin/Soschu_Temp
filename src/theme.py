"""
Système de thème adaptatif pour Soschu Temperature Tool.

Détecte automatiquement le mode sombre/clair du système et fournit
une palette de couleurs cohérente pour l'interface tkinter.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    """Palette de couleurs pour un thème."""

    # Arrière-plans
    bg_primary: str
    bg_secondary: str
    bg_input: str
    bg_nav: str
    bg_oddrow: str

    # Texte
    fg_primary: str
    fg_secondary: str
    fg_heading: str

    # Boutons d'action
    accent_primary: str
    accent_primary_fg: str
    accent_success: str
    accent_success_fg: str
    accent_danger: str
    accent_danger_fg: str

    # Statuts
    status_ok: str
    status_error: str
    status_progress: str
    status_ready: str

    # Tags saisonniers (treeview)
    summer_bg: str
    winter_bg: str

    # Info / tooltip
    info_fg: str
    tooltip_bg: str
    tooltip_fg: str

    # Treeview
    heading_bg: str


LIGHT = ColorPalette(
    bg_primary="#f5f5f5",
    bg_secondary="white",
    bg_input="white",
    bg_nav="#f5f5f5",
    bg_oddrow="#f0f0f0",
    fg_primary="black",
    fg_secondary="#666666",
    fg_heading="#1a3a5c",
    accent_primary="#4A90E2",
    accent_primary_fg="white",
    accent_success="#28a745",
    accent_success_fg="white",
    accent_danger="#dc3545",
    accent_danger_fg="white",
    status_ok="#1e8e3e",
    status_error="#d93025",
    status_progress="#e67700",
    status_ready="#1a73e8",
    summer_bg="#FFFFE0",
    winter_bg="#E0F0FF",
    info_fg="#1a73e8",
    tooltip_bg="#ffffe0",
    tooltip_fg="black",
    heading_bg="#e0e0e0",
)

DARK = ColorPalette(
    bg_primary="#2b2b2b",
    bg_secondary="#3c3c3c",
    bg_input="#4a4a4a",
    bg_nav="#2b2b2b",
    bg_oddrow="#383838",
    fg_primary="#e0e0e0",
    fg_secondary="#999999",
    fg_heading="#8ab4f8",
    accent_primary="#5BA0F2",
    accent_primary_fg="white",
    accent_success="#3CB371",
    accent_success_fg="white",
    accent_danger="#FF6B6B",
    accent_danger_fg="white",
    status_ok="#3CB371",
    status_error="#FF6B6B",
    status_progress="#FFA500",
    status_ready="#8ab4f8",
    summer_bg="#3d3d28",
    winter_bg="#283848",
    info_fg="#8ab4f8",
    tooltip_bg="#4a4a4a",
    tooltip_fg="#e0e0e0",
    heading_bg="#444444",
)


def _detect_dark_mode() -> bool:
    """Détecte si le système est en mode sombre."""
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return result.stdout.strip().lower() == "dark"
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0
        except (ImportError, OSError):
            return False

    return False


def get_theme() -> ColorPalette:
    """Retourne la palette de couleurs adaptée au thème système."""
    return DARK if _detect_dark_mode() else LIGHT
