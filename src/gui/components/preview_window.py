import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List, Optional

from preview import PreviewAdjustmentData, PreviewService, PreviewSummaryData

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)


class PreviewWindow:
    """Fenêtre de prévisualisation des conversions qui vont être appliquées."""

    def __init__(
        self,
        parent,
        preview_result: PreviewService,
        generate_callback: Optional[Callable] = None,
    ):
        """
        Initialise la fenêtre de prévisualisation.

        Args:
            parent: Widget parent
            preview_result: Résultat de la prévisualisation
            generate_callback: Fonction à appeler pour générer les fichiers
        """
        self.parent = parent
        self.summary_data = self._generate_preview_summary(preview_result)
        self.samples_data = self._generate_preview_samples(preview_result)
        self.preview_result = preview_result
        self.generate_callback = generate_callback
        self.window = None

    def _generate_preview_summary(
        self, preview_service: PreviewService
    ) -> PreviewSummaryData:
        """Génèrate the data for the summary tab."""
        return preview_service.get_summary()

    def _generate_preview_samples(
        self, preview_service: PreviewService
    ) -> List[PreviewAdjustmentData]:
        """Génère les échantillons d'ajustements pour l'onglet de prévisualisation."""
        return preview_service.get_samples()

    def show(self):
        """Affiche la fenêtre de prévisualisation."""
        if self.window:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Prévisualisation des conversions")
        self.window.geometry("1200x700")  # Agrandir pour les nouvelles colonnes
        self.window.resizable(True, True)

        # Créer un notebook pour organiser les informations
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglet Résumé
        self._create_summary_tab(notebook)

        # Onglet Échantillon d'ajustements
        self._create_sample_adjustments_tab(notebook)

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
Fichiers d´entrée:
    • Météo: {self.summary_data.weather_filename}
    • IDA ICE: {self.summary_data.solar_filename}

Résumé des données:
    • Nombre de Façades à traiter: {self.summary_data.count_facades}
    • Total d'ajustements de température: {self.summary_data.count_adjustments}
    • Nombre de points fichier météo: {self.summary_data.count_weather_data_points}
    • Nombre  de points fichier irradiance solaire: {self.summary_data.count_weather_data_points}

Paramètres de traitement:
    • Seuil d'irradiance: {self.summary_data.threshold} W/m²
    • Augmentation de température: {self.summary_data.delta_t} K
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

        # Créer un Treeview pour afficher les façades
        tree_frame = tk.Frame(facade_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            tree_frame, columns=("adjustments", "percentage"), show="tree headings"
        )
        tree.heading("#0", text="Façade")
        tree.heading("#1", text="Ajustements")
        tree.heading("#2", text="% des données")

        tree.column("#0", width=100, anchor="center")
        tree.column("#1", width=150, anchor="center")
        tree.column("#2", width=150, anchor="center")

        # Ajouter les données

        # Configure tags for alternating row colors
        tree.tag_configure("oddrow", background="#f0f0f0")
        tree.tag_configure("evenrow", background="white")

        # Add the data with alternating background colors
        for i, (facade_name, (adjustments, percentage)) in enumerate(
            self.summary_data.table.items()
        ):
            tree.insert(
                "",
                tk.END,
                text=facade_name,
                values=(f"{adjustments}", f"{percentage:.1f}%"),
                tags=("oddrow" if i % 2 else "evenrow"),
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
        notebook.add(frame, text="Synchronisation météo/solaire")

        # Titre
        title_label = tk.Label(
            frame,
            text="Exemples d'ajustements de température par façade et saison",
            font=("Arial", 12, "bold"),
            fg="darkgreen",
        )
        title_label.pack(pady=10)

        # Note explicative
        note_text = (
            "Échantillons stratifiés pour vérifier la synchronisation météo/solaire.\n"
            "🌞 Période chaude (Mars-Septembre): correspond généralement à l'heure d'été\n"
            "❄️ Période froide (Octobre-Février): correspond généralement à l'heure d'hiver\n"
            "📅 Les colonnes météo/solaire montrent la correspondance temporelle (décalage +1h possible avec heure d'été/hiver)\n"
            "Cette stratification permet de vérifier la cohérence temporelle sur toute l'année."
        )
        note_label = tk.Label(
            frame, text=note_text, font=("Arial", 9), fg="darkblue", justify=tk.LEFT
        )
        note_label.pack(pady=(0, 10))

        # Créer un Treeview hiérarchique pour les ajustements
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree = ttk.Treeview(
            tree_frame,
            columns=(
                "weather_time",
                "solar_time",
                "original_temp",
                "adjusted_temp",
                "solar",
                "threshold",
            ),
            show="tree headings",
        )
        tree.heading("#0", text="Façade / Saison")
        tree.heading("weather_time", text="Météo (heure)")
        tree.heading("solar_time", text="Solaire (heure)")
        tree.heading("original_temp", text="Temp. orig. (°C)")
        tree.heading("adjusted_temp", text="Temp. ajustée (°C)")
        tree.heading("solar", text="Irradiance (W/m²)")
        tree.heading("threshold", text="Seuil (W/m²)")

        tree.column("#0", width=280)  # Agrandir pour le texte complet
        tree.column("weather_time", width=120, anchor="center")
        tree.column("solar_time", width=120, anchor="center")
        tree.column("original_temp", width=110, anchor="center")
        tree.column("adjusted_temp", width=110, anchor="center")
        tree.column("solar", width=120, anchor="center")
        tree.column("threshold", width=100, anchor="center")

        # Organiser les échantillons par façade et saison
        for sample in self.samples_data:
            # Obtenir les données à afficher
            data = sample.get_preview_samples()
            facade_name = data.get("facade_name", "Inconnu")
            threshold = data.get("threshold", 0.0)
            delta_t = data.get("delta_t", 0.0)

            w_samples = data.get("samples", {})
            # Organiser les échantillons par saison
            summer_samples = w_samples.get("summer", [])
            winter_samples = w_samples.get("winter", [])

            # Créer les noeuds pour l´hiver
            for w_sample in winter_samples:
                # Set weather timestamp in MEZ
                weather_timestamp = w_sample.timestamp_with_timezone_as_str()

                # Set IDA ICE timestamp in MEZ/MESZ
                ida_ice_timestamp = w_sample.timestamp.strftime("%d-%m-%Y %H:%M")

                temperature = w_sample.temperature
                adjusted_tempeture = w_sample.adjusted_temperature

                node = tree.insert(
                    "",
                    tk.END,
                    text=f"{facade_name} - ❄️ Période heure d´hiver",
                    values=(
                        weather_timestamp,
                        ida_ice_timestamp,
                        f"{temperature:.1f}",
                        f"{adjusted_tempeture:.1f}",
                        f"{delta_t:.1f}",
                        f"{threshold:.1f}",
                    ),
                )
                tree.item(node, open=True)
            # Créer les noeuds pour l'été
            for s_sample in summer_samples:
                # Set weather timestamp in MEZ
                weather_timestamp = s_sample.timestamp.strftime("%d-%m-%Y %H:%M")

                # Set IDA ICE timestamp in MEZ/MESZ
                ida_ice_timestamp = s_sample.timestamp.strftime("%d-%m-%Y %H:%M")

                temperature = s_sample.temperature
                adjusted_tempeture = s_sample.adjusted_temperature

                node = tree.insert(
                    "",
                    tk.END,
                    text=f"{facade_name} - 🌞 Période heure d´été",
                    values=(
                        weather_timestamp,
                        ida_ice_timestamp,
                        f"{temperature:.1f}",
                        f"{adjusted_tempeture:.1f}",
                        f"{delta_t:.1f}",
                        f"{threshold:.1f}",
                    ),
                )
                tree.item(node, open=True)

        # for facade_name, samples in self.samples_data.items():
        #     summer_sample, winter_sample = self.samples_data.get_samples()
        # facade_samples = {}
        # for adj in self.preview_result.sample_adjustments:
        #     facade_key = f"{adj.facade_id} - {adj.building_body}"
        #     if facade_key not in facade_samples:
        #         facade_samples[facade_key] = {"summer": [], "winter": []}

        #     # Déterminer la saison basée sur le mois (approximation de l'heure d'été/hiver)
        #     month = int(adj.datetime_str.split("-")[0])
        #     season = "summer" if 3 <= month <= 9 else "winter"
        #     facade_samples[facade_key][season].append(adj)

        # # Ajouter les données organisées au tree
        # for facade_name, seasons in facade_samples.items():
        #     facade_node = tree.insert(
        #         "", tk.END, text=facade_key, values=("", "", "", "", "", "")
        #     )

        #     for season_name, adjustments in seasons.items():
        #         if not adjustments:
        #             continue

        #         season_display = (
        #             "🌞 Période heure d´été"
        #             if season_name == "summer"
        #             else "❄️ Période heure d´hiver"
        #         )
        #         season_node = tree.insert(
        #             facade_node,
        #             tk.END,
        #             text=season_display,
        #             values=("", "", "", "", "", ""),
        #         )

        #         for adj in adjustments:
        #             # Déterminer si les heures correspondent ou s'il y a un décalage
        #             weather_time = adj.weather_datetime
        #             solar_time = adj.solar_datetime or "N/A"

        #             tree.insert(
        #                 season_node,
        #                 tk.END,
        #                 text="",
        #                 values=(
        #                     weather_time,
        #                     solar_time,
        #                     f"{adj.original_temp:.1f}",
        #                     f"{adj.adjusted_temp:.1f}",
        #                     f"{adj.solar_irradiance:.1f}",
        #                     f"{adj.threshold:.1f}",
        #                 ),
        #             )

        # Expand facade nodes by default

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.HORIZONTAL, command=tree.xview
        )
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # # Note en bas avec statistiques améliorées
        # total_samples = len(self.preview_result.sample_adjustments)
        # facade_count = len(facade_samples)
        # note_text = f"Affichage de {total_samples} échantillons stratifiés sur {facade_count} façade(s) - Total: {self.preview_result.total_adjustments:,} ajustements"
        # note_label = tk.Label(frame, text=note_text, font=("Arial", 10), fg="gray")
        # note_label.pack(pady=5)

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

        # Bouton Générer les fichiers (toujours visible)
        generate_button = tk.Button(
            button_frame,
            text="Générer les fichiers",
            command=self._generate_files,
            font=("Arial", 10, "bold"),
            width=20,
            bg="lightgreen" if self.generate_callback else "lightgray",
            relief=tk.RAISED,
            state=tk.NORMAL if self.generate_callback else tk.DISABLED,
        )
        generate_button.pack(side=tk.RIGHT, padx=5)

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

    def _generate_files(self):
        """Lance la génération des fichiers."""
        if not self.generate_callback:
            logger.error("Aucune fonction de génération définie")
            messagebox.showerror("Erreur", "Aucune fonction de génération définie")
            return

        # Confirmation avant génération
        total_adjustments = self.summary_data.count_adjustments
        response = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous générer les fichiers avec {total_adjustments} ajustements de température ?",
            icon="question",
        )

        if not response:
            logger.info("Génération annulée par l'utilisateur")
            return

        try:
            # Désactiver temporairement la fenêtre si elle existe
            if self.window:
                self.window.config(cursor="wait")
                self.window.update()

            logger.info("Début de la génération des fichiers...")

            # Appeler la fonction de génération
            result = self.generate_callback()

            # Remettre le curseur normal
            if self.window:
                self.window.config(cursor="")

            # Afficher le résultat
            if result:
                logger.info(f"Génération terminée: {result}")
                messagebox.showinfo(
                    "Succès", f"Génération terminée avec succès!\n\n{result}"
                )
                # Fermer la fenêtre de prévisualisation après succès
                self._on_close()
            else:
                logger.warning("Génération terminée mais aucun résultat retourné")
                messagebox.showinfo("Terminé", "Génération terminée")

        except Exception as e:
            # Remettre le curseur normal en cas d'erreur
            if self.window:
                self.window.config(cursor="")
            logger.error(f"Erreur lors de la génération: {e}")
            messagebox.showerror(
                "Erreur", f"Erreur lors de la génération des fichiers:\n{str(e)}"
            )

    def _on_close(self):
        """Gestionnaire de fermeture de la fenêtre."""
        if self.window:
            self.window.destroy()
            self.window = None


def show_preview_window(
    parent, preview_result: PreviewService, generate_callback: Optional[Callable] = None
):
    """
    Fonction utilitaire pour afficher la fenêtre de prévisualisation.

    Args:
        parent: Widget parent
        preview_result: Résultat de la prévisualisation
        generate_callback: Fonction à appeler pour générer les fichiers
    """
    preview_window = PreviewWindow(parent, preview_result, generate_callback)
    preview_window.show()
