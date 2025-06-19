import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Classe pour créer des info-bulles (tooltips) sur les widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Affiche l'info-bulle."""
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        """Cache l'info-bulle."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ComputationSetting(tk.Frame):
    """Composant pour les paramètres de calcul avec label, input, unité et tooltip optionnel."""

    def __init__(
        self,
        parent,
        setting_name,
        default_value="",
        unit_text="",
        tooltip_description=None,
        entry_width=15,
        validate_numeric=False,
        **kwargs,
    ):
        """
        Initialise le composant de paramètre de calcul.

        Args:
            parent: Widget parent
            setting_name: Nom du paramètre (affiché comme label)
            default_value: Valeur par défaut dans le champ de saisie
            unit_text: Texte de l'unité affiché après le champ
            tooltip_description: Description pour l'info-bulle (optionnel)
            entry_width: Largeur du champ de saisie
            validate_numeric: Si True, valide que l'entrée est numérique
            **kwargs: Arguments supplémentaires pour le Frame parent
        """
        super().__init__(parent, **kwargs)

        self.setting_name = setting_name
        self.unit_text = unit_text
        self.validate_numeric = validate_numeric

        # Configuration de la grille interne
        self.grid_columnconfigure(1, weight=0)  # Entry column doesn't expand
        self.grid_columnconfigure(2, weight=0)  # Unit column doesn't expand

        # Créer les widgets
        self.label = tk.Label(self, text=f"{setting_name}:")

        # Validation numérique optionnelle
        if validate_numeric:
            vcmd = (self.register(self._validate_numeric), "%P")
            self.entry = tk.Entry(
                self, width=entry_width, validate="key", validatecommand=vcmd
            )
        else:
            self.entry = tk.Entry(self, width=entry_width)

        # Insérer la valeur par défaut
        if default_value:
            self.entry.insert(0, str(default_value))

        self.unit_label = tk.Label(self, text=unit_text, font=("Arial", 9))

        # Placer les widgets dans la grille interne
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.entry.grid(row=0, column=1, sticky="w", padx=(0, 5), pady=2)
        self.unit_label.grid(row=0, column=2, sticky="w", pady=2)

        # Ajouter tooltip si fourni
        self.tooltip = None
        if tooltip_description:
            self.tooltip = ToolTip(self.label, tooltip_description)

    def _validate_numeric(self, value):
        """Valide que l'entrée est numérique (entier ou décimal)."""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_value(self):
        """Retourne la valeur actuelle du champ de saisie."""
        return self.entry.get()

    def get_numeric_value(self):
        """Retourne la valeur numérique du champ (float) ou None si invalide."""
        try:
            return float(self.get_value())
        except ValueError:
            return None

    def set_value(self, value):
        """Définit la valeur du champ de saisie."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, str(value))

    def clear(self):
        """Vide le champ de saisie."""
        self.entry.delete(0, tk.END)

    def is_valid(self):
        """Vérifie si la valeur est valide (pour les champs numériques)."""
        if not self.validate_numeric:
            return True
        return self.get_numeric_value() is not None

    def set_enabled(self, enabled=True):
        """Active ou désactive le champ de saisie."""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.entry.config(state=state)
