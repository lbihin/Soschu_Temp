import tkinter as tk
from tkinter import ttk
from typing import List

from core import PreviewAdjustment, PreviewResult


class PreviewWindow:
    """Fenêtre de prévisualisation des conversions qui vont être appliquées."""

    def __init__(self, parent, preview_result: PreviewResult):
        """
        Initialise la fenêtre de prévisualisation.

        Args:
            parent: Widget parent
            preview_result: Résultat de la prévisualisation
        """
        self.parent = parent
        self.preview_result = preview_result
        self.window = None

    def show(self):
        """Affiche la fenêtre de prévisualisation."""
        if self.window:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Prévisualisation des conversions")
        self.window.geometry("900x700")
        self.window.resizable(True, True)

        # Créer un notebook pour organiser les informations
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglet Résumé
        self._create_summary_tab(notebook)

        # Onglet Détails par façade
        self._create_facade_details_tab(notebook)

        # Onglet Échantillon d'ajustements
        self._create_sample_adjustments_tab(notebook)

        # Onglet Paramètres
        self._create_parameters_tab(notebook)

        # Boutons de contrôle
        self._create_control_buttons()

        # Gérer la fermeture de la fenêtre
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_summary_tab(self, notebook):
        """Crée l'onglet de résumé."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Résumé")

        # Frame principal avec scrollbar
        main_frame = tk.Frame(frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titre
        title_label = tk.Label(
            main_frame,
            text="Résumé des conversions à appliquer",
            font=("Arial", 14, "bold"),
            fg="darkblue",
        )
        title_label.pack(pady=(0, 20))

        # Informations générales
        info_frame = tk.Frame(main_frame, relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        info_title = tk.Label(
            info_frame,
            text="Informations générales",
            font=("Arial", 12, "bold"),
            bg="lightgray",
        )
        info_title.pack(fill=tk.X, pady=5)

        info_text = f"""
Nombre de façades détectées: {len(self.preview_result.facade_combinations)}
Total d'ajustements de température: {self.preview_result.total_adjustments:,}
Points de données météo: {self.preview_result.parameters['weather_data_points']:,}
Points de données solaires: {self.preview_result.parameters['solar_data_points']:,}

Paramètres de traitement:
• Seuil d'irradiance: {self.preview_result.parameters['threshold']} W/m²
• Augmentation de température: {self.preview_result.parameters['delta_t']} °C
        """.strip()

        info_label = tk.Label(info_frame, text=info_text, justify=tk.LEFT, anchor="w")
        info_label.pack(fill=tk.X, padx=10, pady=5)

        # Résumé par façade
        facade_frame = tk.Frame(main_frame, relief=tk.RIDGE, bd=2)
        facade_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        facade_title = tk.Label(
            facade_frame,
            text="Ajustements par façade",
            font=("Arial", 12, "bold"),
            bg="lightgray",
        )
        facade_title.pack(fill=tk.X, pady=5)

        # Tableau des façades
        facade_text = "Façade\t\t\tAjustements\n" + "-" * 50 + "\n"
        for (
            facade_key,
            adjustments,
        ) in self.preview_result.adjustments_by_facade.items():
            facade_text += f"{facade_key.ljust(25)}\t{adjustments:,}\n"

        facade_label = tk.Label(
            facade_frame,
            text=facade_text,
            justify=tk.LEFT,
            anchor="nw",
            font=("Courier", 10),
        )
        facade_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _create_facade_details_tab(self, notebook):
        """Crée l'onglet des détails par façade."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Détails par façade")

        # Créer un Treeview pour afficher les façades
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            tree_frame, columns=("adjustments", "percentage"), show="tree headings"
        )
        tree.heading("#0", text="Façade")
        tree.heading("adjustments", text="Ajustements")
        tree.heading("percentage", text="% des données")

        tree.column("#0", width=300)
        tree.column("adjustments", width=150, anchor="center")
        tree.column("percentage", width=150, anchor="center")

        # Ajouter les données
        total_data_points = self.preview_result.parameters["weather_data_points"]
        for (
            facade_key,
            adjustments,
        ) in self.preview_result.adjustments_by_facade.items():
            percentage = (
                (adjustments / total_data_points * 100) if total_data_points > 0 else 0
            )
            tree.insert(
                "",
                tk.END,
                text=facade_key,
                values=(f"{adjustments:,}", f"{percentage:.1f}%"),
            )

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=tree.xview
        )
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_sample_adjustments_tab(self, notebook):
        """Crée l'onglet des échantillons d'ajustements."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Échantillon d'ajustements")

        # Titre
        title_label = tk.Label(
            frame,
            text="Exemples d'ajustements de température",
            font=("Arial", 12, "bold"),
            fg="darkgreen",
        )
        title_label.pack(pady=10)

        # Créer un Treeview pour les ajustements
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            tree_frame,
            columns=(
                "facade",
                "datetime",
                "original_temp",
                "adjusted_temp",
                "solar",
                "threshold",
            ),
            show="headings",
        )
        tree.heading("facade", text="Façade")
        tree.heading("datetime", text="Date/Heure")
        tree.heading("original_temp", text="Temp. originale (°C)")
        tree.heading("adjusted_temp", text="Temp. ajustée (°C)")
        tree.heading("solar", text="Irradiance (W/m²)")
        tree.heading("threshold", text="Seuil (W/m²)")

        tree.column("facade", width=150)
        tree.column("datetime", width=120)
        tree.column("original_temp", width=130, anchor="center")
        tree.column("adjusted_temp", width=130, anchor="center")
        tree.column("solar", width=130, anchor="center")
        tree.column("threshold", width=130, anchor="center")

        # Ajouter les échantillons d'ajustements
        for adj in self.preview_result.sample_adjustments:
            facade_display = f"{adj.facade_id} - {adj.building_body}"
            tree.insert(
                "",
                tk.END,
                values=(
                    facade_display,
                    adj.datetime_str,
                    f"{adj.original_temp:.1f}",
                    f"{adj.adjusted_temp:.1f}",
                    f"{adj.solar_irradiance:.1f}",
                    f"{adj.threshold:.1f}",
                ),
            )

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=tree.xview
        )
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Note en bas
        note_text = f"Affichage de {len(self.preview_result.sample_adjustments)} ajustements sur {self.preview_result.total_adjustments} au total."
        note_label = tk.Label(frame, text=note_text, font=("Arial", 10), fg="gray")
        note_label.pack(pady=5)

    def _create_parameters_tab(self, notebook):
        """Crée l'onglet des paramètres."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Paramètres")

        # Frame principal
        main_frame = tk.Frame(frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Titre
        title_label = tk.Label(
            main_frame,
            text="Paramètres de traitement",
            font=("Arial", 14, "bold"),
            fg="darkred",
        )
        title_label.pack(pady=(0, 20))

        # Paramètres
        params_text = f"""
Fichiers d'entrée:

Fichier météo:
{self.preview_result.parameters['weather_file']}

Fichier solaire:
{self.preview_result.parameters['solar_file']}

Paramètres de calcul:

Seuil d'irradiance solaire: {self.preview_result.parameters['threshold']} W/m²
Augmentation de température: {self.preview_result.parameters['delta_t']} °C

Données chargées:

Points de données météo: {self.preview_result.parameters['weather_data_points']:,}
Points de données solaires: {self.preview_result.parameters['solar_data_points']:,}
Façades détectées: {len(self.preview_result.facade_combinations)}

Façades détectées:
        """.strip()

        for facade_id, building_body in self.preview_result.facade_combinations:
            params_text += f"\n• {facade_id} - {building_body}"

        params_label = tk.Label(
            main_frame,
            text=params_text,
            justify=tk.LEFT,
            anchor="nw",
            font=("Arial", 10),
        )
        params_label.pack(fill=tk.BOTH, expand=True)

    def _create_control_buttons(self):
        """Crée les boutons de contrôle."""
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Bouton Fermer
        close_button = tk.Button(
            button_frame,
            text="Fermer",
            command=self._on_close,
            font=("Arial", 10),
            width=10,
        )
        close_button.pack(side=tk.RIGHT, padx=5)

        # Bouton Exporter (pour plus tard)
        export_button = tk.Button(
            button_frame,
            text="Exporter résumé",
            command=self._export_summary,
            font=("Arial", 10),
            width=15,
            state=tk.DISABLED,  # Désactivé pour l'instant
        )
        export_button.pack(side=tk.RIGHT, padx=5)

    def _export_summary(self):
        """Exporte le résumé (fonctionnalité future)."""
        # TODO: Implémenter l'export en CSV ou texte
        pass

    def _on_close(self):
        """Gestionnaire de fermeture de la fenêtre."""
        if self.window:
            self.window.destroy()
            self.window = None


def show_preview_window(parent, preview_result: PreviewResult):
    """
    Fonction utilitaire pour afficher la fenêtre de prévisualisation.

    Args:
        parent: Widget parent
        preview_result: Résultat de la prévisualisation
    """
    preview_window = PreviewWindow(parent, preview_result)
    preview_window.show()
