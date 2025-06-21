"""
Soschu Temperature Tool - Application principale simplifiée

Cette application permet d'ajuster des températures dans des fichiers météo .dat
basé sur l'irradiation solaire de façades depuis des fichiers HTML.

Architecture simplifiée:
1. Interface utilisateur simple (tkinter)
2. Logique métier centralisée
3. Parsers pour les fichiers d'entrée
4. Générateur de fichiers de sortie
"""

import logging
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

from core_logic import PreviewData, SoschuProcessor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SoschuApp:
    """Application principale simplifiée pour Soschu Temperature Tool."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Soschu Temperature Tool")
        self.root.geometry("800x450")  # Augmentation de la hauteur de la fenêtre
        self.root.resizable(True, True)  # Permettre le redimensionnement pour les tests

        # Variables pour stocker les fichiers et paramètres
        self.weather_file = tk.StringVar()
        self.solar_file = tk.StringVar()
        self.threshold = tk.StringVar(value="200")
        self.delta_t = tk.StringVar(value="7")

        # Variable pour stocker les données de prévisualisation
        self.preview_data: Optional[PreviewData] = None

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Frame principal avec padding
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Section sélection de fichiers
        files_frame = tk.LabelFrame(
            main_frame, text="Fichiers d'entrée", padx=15, pady=15
        )
        files_frame.pack(fill=tk.X, pady=(0, 15))

        # Configuration de la grille pour les fichiers
        files_frame.grid_columnconfigure(1, weight=1)

        # Fichier météo
        tk.Label(files_frame, text="Fichier météo (.dat):", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=8, padx=(0, 10)
        )
        tk.Entry(
            files_frame,
            textvariable=self.weather_file,
            state="readonly",
            font=("Arial", 9),
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)
        tk.Button(
            files_frame,
            text="Parcourir",
            command=self.select_weather_file,
            width=12,
            font=("Arial", 9),
        ).grid(row=0, column=2, padx=5, pady=8)

        # Fichier solaire
        tk.Label(files_frame, text="Fichier solaire (.html):", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=8, padx=(0, 10)
        )
        tk.Entry(
            files_frame,
            textvariable=self.solar_file,
            state="readonly",
            font=("Arial", 9),
        ).grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=8)
        tk.Button(
            files_frame,
            text="Parcourir",
            command=self.select_solar_file,
            width=12,
            font=("Arial", 9),
        ).grid(row=1, column=2, padx=5, pady=8)

        # Section paramètres
        params_frame = tk.LabelFrame(main_frame, text="Paramètres", padx=15, pady=15)
        params_frame.pack(fill=tk.X, pady=(0, 20))

        # Configuration de la grille pour les paramètres
        params_frame.grid_columnconfigure(1, weight=1)
        params_frame.grid_columnconfigure(3, weight=1)

        # Threshold
        tk.Label(params_frame, text="Seuil d'irradiation:", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=8
        )
        threshold_entry = tk.Entry(
            params_frame, textvariable=self.threshold, width=12, font=("Arial", 10)
        )
        threshold_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=8)
        tk.Label(params_frame, text="W/m²", font=("Arial", 10)).grid(
            row=0, column=2, sticky=tk.W, padx=(5, 20), pady=8
        )

        # Delta T
        tk.Label(
            params_frame, text="Augmentation température:", font=("Arial", 10)
        ).grid(row=0, column=3, sticky=tk.W, padx=(0, 10), pady=8)
        delta_entry = tk.Entry(
            params_frame, textvariable=self.delta_t, width=12, font=("Arial", 10)
        )
        delta_entry.grid(row=0, column=4, sticky=tk.W, padx=(0, 5), pady=8)
        tk.Label(params_frame, text="°C", font=("Arial", 10)).grid(
            row=0, column=5, sticky=tk.W, padx=(5, 0), pady=8
        )

        # Section bouton central - seulement prévisualiser
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 15), expand=True)  # Ajout de expand=True

        # Bouton prévisualiser centré
        self.preview_btn = tk.Button(
            button_frame,
            text="Prévisualiser les ajustements",
            command=self.preview_processing,
            bg="#4A90E2",
            fg="white",
            font=("Arial", 12, "bold"),
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=2,
            state=tk.DISABLED,  # Désactivé par défaut
        )
        self.preview_btn.pack(pady=20, expand=True)  # Augmentation du padding vertical

        # Ajouter une étiquette au-dessus du bouton pour le rendre plus visible
        preview_label = tk.Label(
            button_frame,
            text="Cliquez sur le bouton ci-dessous quand vous êtes prêt",
            font=("Arial", 10),
            fg="gray",
        )
        preview_label.pack(pady=(0, 5))

        # Barre de progression
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        self.progress.pack_forget()  # Masquer initialement

        # Activation dynamique du bouton
        def check_enable_preview(*args):
            if (
                self.weather_file.get()
                and self.solar_file.get()
                and self.threshold.get()
                and self.delta_t.get()
            ):
                try:
                    float(self.threshold.get())
                    float(self.delta_t.get())
                    self.preview_btn.config(state=tk.NORMAL)
                except ValueError:
                    self.preview_btn.config(state=tk.DISABLED)
            else:
                self.preview_btn.config(state=tk.DISABLED)

        self.weather_file.trace_add("write", check_enable_preview)
        self.solar_file.trace_add("write", check_enable_preview)
        self.threshold.trace_add("write", check_enable_preview)
        self.delta_t.trace_add("write", check_enable_preview)
        # Appel initial
        check_enable_preview()

    def select_weather_file(self):
        """Sélectionne le fichier météo."""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier météo",
            filetypes=[("Fichiers DAT", "*.dat"), ("Tous les fichiers", "*.*")],
        )
        if filename:
            self.weather_file.set(filename)

    def select_solar_file(self):
        """Sélectionne le fichier solaire."""
        filename = filedialog.askopenfilename(
            title="Sélectionner le fichier solaire",
            filetypes=[("Fichiers HTML", "*.html"), ("Tous les fichiers", "*.*")],
        )
        if filename:
            self.solar_file.set(filename)

    def validate_inputs(self) -> bool:
        """Valide les entrées utilisateur."""
        if not self.weather_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier météo")
            return False

        if not self.solar_file.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier solaire")
            return False

        try:
            float(self.threshold.get())
        except ValueError:
            messagebox.showerror("Erreur", "Le seuil d'irradiation doit être un nombre")
            return False

        try:
            float(self.delta_t.get())
        except ValueError:
            messagebox.showerror(
                "Erreur", "L'augmentation de température doit être un nombre"
            )
            return False

        return True

    def preview_processing(self):
        """Lance la prévisualisation sans thread."""
        if not self.validate_inputs():
            return

        self.preview_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()

        # Lancer le traitement directement (sans thread pour debug)
        logger.info("Lancement direct de la prévisualisation sans thread pour debug")
        processor = SoschuProcessor()

        try:
            self.preview_data = processor.preview_adjustments(
                weather_file=self.weather_file.get(),
                solar_file=self.solar_file.get(),
                threshold=float(self.threshold.get()),
                delta_t=float(self.delta_t.get()),
            )

            # Arrêter la progression
            self.progress.stop()
            self.progress.pack_forget()
            self.preview_btn.config(state=tk.NORMAL)

            logger.info(
                f"Prévisualisation directe terminée, données: {self.preview_data is not None}"
            )

            # Lancer directement le wizard
            if self.preview_data:
                logger.info("Lancement direct du wizard")
                self.show_preview_wizard()
            else:
                logger.error("Pas de données de prévisualisation")
                messagebox.showerror(
                    "Erreur", "Aucune donnée de prévisualisation générée"
                )

        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation directe: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.progress.stop()
            self.progress.pack_forget()
            self.preview_btn.config(state=tk.NORMAL)
            messagebox.showerror("Erreur de prévisualisation", str(e))

    def _do_preview(self):
        """Effectue la prévisualisation (dans le thread)."""
        try:
            logger.info("Début du traitement de prévisualisation")
            processor = SoschuProcessor()

            # Log des paramètres
            logger.info(f"Fichier météo: {self.weather_file.get()}")
            logger.info(f"Fichier solaire: {self.solar_file.get()}")
            logger.info(f"Seuil: {self.threshold.get()}, Delta T: {self.delta_t.get()}")

            self.preview_data = processor.preview_adjustments(
                weather_file=self.weather_file.get(),
                solar_file=self.solar_file.get(),
                threshold=float(self.threshold.get()),
                delta_t=float(self.delta_t.get()),
            )

            logger.info(
                f"Prévisualisation terminée avec succès: {self.preview_data is not None}"
            )
            if self.preview_data:
                logger.info(
                    f"Nombre de façades trouvées: {len(self.preview_data.facades)}"
                )

            # Revenir au thread principal pour l'UI
            logger.info("Programmation du callback _preview_completed")

            # Appel direct du callback pour assurer une exécution correcte
            logger.info("Appel direct du callback _preview_completed")
            self.root.after(0, self._preview_completed)

        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.root.after(0, lambda: self._preview_error(str(e)))

    def _preview_completed(self):
        """Appelé quand la prévisualisation est terminée (thread principal)."""
        self.progress.stop()
        self.progress.pack_forget()
        self.preview_btn.config(state=tk.NORMAL)

        logger.info(
            f"Prévisualisation terminée, données: {self.preview_data is not None}"
        )

        if self.preview_data:
            logger.info("Lancement du wizard de prévisualisation")
            self.show_preview_wizard()
        else:
            logger.error("Aucune donnée de prévisualisation disponible")
            messagebox.showerror("Erreur", "Aucune donnée de prévisualisation générée")

    def _preview_error(self, error_msg: str):
        """Appelé en cas d'erreur de prévisualisation (thread principal)."""
        self.progress.stop()
        self.progress.pack_forget()
        self.preview_btn.config(state=tk.NORMAL)
        messagebox.showerror("Erreur de prévisualisation", error_msg)

    def show_preview_wizard(self):
        """Affiche le wizard de prévisualisation avec navigation guidée."""
        logger.info("Entrée dans la méthode show_preview_wizard")

        if not self.preview_data:
            logger.error("Sortie prématurée - pas de données de prévisualisation")
            return

        logger.info("Création de la fenêtre wizard")
        try:
            # Créer la fenêtre wizard
            wizard = tk.Toplevel(self.root)
            wizard.title("Soschu Temperature Tool - Résumé")
            wizard.geometry("1000x700")
            wizard.minsize(900, 600)
            wizard.resizable(True, True)
            wizard.grab_set()  # Rendre la fenêtre modale

            # Centrer la fenêtre sur l'écran par rapport à la fenêtre principale
            wizard.transient(self.root)

            # Définir une icône et un style moderne
            wizard.configure(bg="#f5f5f5")

            logger.info("Fenêtre wizard créée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création du wizard: {e}")
            messagebox.showerror("Erreur", f"Impossible de créer l'assistant: {str(e)}")
            return

        # Variables pour la navigation
        current_step = tk.IntVar(value=0)

        # Créer le frame principal
        main_frame = tk.Frame(wizard, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Indicateur d'étapes simplifié (seulement pour la logique interne, pas visible)
        step_labels = ["1. Résumé", "2. Exemples", "3. Génération"]
        step_widgets = []

        # On ne crée pas de widgets visibles pour les étapes,
        # mais on garde la logique pour le fonctionnement interne
        for i, step_text in enumerate(step_labels):
            # Créer des étiquettes invisibles pour la logique
            label = tk.Label(main_frame)
            step_widgets.append(label)

        # Zone de contenu
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Frame pour chaque étape
        step_frames = []

        # Étape 1: Résumé
        step1_frame = tk.Frame(content_frame)
        step_frames.append(step1_frame)
        self._create_wizard_summary_step(step1_frame)

        # Étape 2: Exemples
        step2_frame = tk.Frame(content_frame)
        step_frames.append(step2_frame)
        self._create_wizard_examples_step(step2_frame)

        # Étape 3: Génération
        step3_frame = tk.Frame(content_frame)
        step_frames.append(step3_frame)
        self._create_wizard_generation_step(step3_frame, wizard)

        # Afficher la première étape
        step_frames[0].pack(fill=tk.BOTH, expand=True)

        # Boutons de navigation
        nav_frame = tk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(20, 0))

        def update_step_display():
            """Met à jour l'affichage des étapes."""
            step = current_step.get()

            # Masquer tous les frames
            for frame in step_frames:
                frame.pack_forget()

            # Afficher le frame actuel
            step_frames[step].pack(fill=tk.BOTH, expand=True)

            # Mettre à jour le titre de la fenêtre selon l'étape actuelle
            wizard.title(f"Soschu Temperature Tool - {step_labels[step]}")

            # Mettre à jour les boutons
            prev_btn.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
            next_btn.config(state=tk.NORMAL if step < 2 else tk.DISABLED)

        def prev_step():
            if current_step.get() > 0:
                current_step.set(current_step.get() - 1)
                update_step_display()

        def next_step():
            if current_step.get() < 2:
                current_step.set(current_step.get() + 1)
                update_step_display()

        # Boutons de navigation
        prev_btn = tk.Button(
            nav_frame,
            text="← Précédent",
            command=prev_step,
            width=12,
            state=tk.DISABLED,
        )
        prev_btn.pack(side=tk.LEFT)

        next_btn = tk.Button(nav_frame, text="Suivant →", command=next_step, width=12)
        next_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Bouton fermer
        close_btn = tk.Button(
            nav_frame, text="Fermer", command=wizard.destroy, width=12
        )
        close_btn.pack(side=tk.RIGHT)

    def _create_wizard_summary_step(self, parent):
        """Crée l'étape 1 du wizard: Résumé."""
        if not self.preview_data:
            return

        # Titre de l'étape
        title_frame = tk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            title_frame,
            text="Résumé des paramètres et résultats",
            font=("Arial", 14, "bold"),
        ).pack()

        tk.Label(
            title_frame,
            text="Vérifiez les paramètres et les statistiques avant de continuer",
            font=("Arial", 10),
            fg="gray",
        ).pack()

        # Contenu principal
        content_frame = tk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Texte de résumé
        text_widget = tk.Text(
            content_frame, wrap=tk.WORD, font=("Arial", 11), height=20
        )
        scrollbar = ttk.Scrollbar(
            content_frame, orient=tk.VERTICAL, command=text_widget.yview
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Contenu du résumé
        summary_text = f"""📋 PARAMÈTRES DE TRAITEMENT

Fichier météo: {Path(self.weather_file.get()).name}
Fichier solaire: {Path(self.solar_file.get()).name}
Seuil d'irradiation: {self.threshold.get()} W/m²
Augmentation température: {self.delta_t.get()}°C

🏢 FAÇADES DÉTECTÉES

{self.preview_data.total_facades} façade(s) trouvée(s):
"""

        for facade in self.preview_data.facades:
            adjustments = self.preview_data.adjustments_by_facade.get(facade, 0)
            percentage = (
                adjustments / max(self.preview_data.total_data_points, 1)
            ) * 100
            summary_text += (
                f"  • {facade}: {adjustments:,} ajustements ({percentage:.1f}%)\n"
            )

        summary_text += f"""
📊 STATISTIQUES GLOBALES

Total des ajustements: {self.preview_data.total_adjustments:,}
Points de données traités: {self.preview_data.total_data_points:,}
Pourcentage global d'ajustements: {(self.preview_data.total_adjustments / max(self.preview_data.total_data_points, 1) * 100):.1f}%

📁 FICHIERS À GÉNÉRER

{len(self.preview_data.facades)} fichier(s) seront créés:
"""

        for facade in self.preview_data.facades:
            filename = f"{facade.replace(' ', '_')}.dat"
            summary_text += f"  • {filename}\n"

        summary_text += "\n✅ Les fichiers générés contiendront les températures ajustées selon ces paramètres."

        text_widget.insert(tk.END, summary_text)
        text_widget.config(state=tk.DISABLED)

        # Pack les widgets
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_wizard_examples_step(self, parent):
        """Crée l'étape 2 du wizard: Exemples d'ajustements."""
        if not self.preview_data:
            return

        # Titre de l'étape
        title_frame = tk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            title_frame,
            text="Exemples d'ajustements de température",
            font=("Arial", 14, "bold"),
        ).pack()

        tk.Label(
            title_frame,
            text="Voici quelques exemples concrets des ajustements qui seront appliqués",
            font=("Arial", 10),
            fg="gray",
        ).pack()

        # Contenu principal
        content_frame = tk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Créer le treeview pour afficher les échantillons
        columns = (
            "Façade",
            "Date/Heure DAT",
            "Date/Heure HTML",
            "Temp. originale",
            "Temp. ajustée",
            "Irradiation",
        )
        tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=18)

        # Configurer les colonnes avec indication du format horaire
        tree.heading("Façade", text="Façade")
        tree.heading("Date/Heure DAT", text="Date/Heure DAT (1-24h MEZ)")
        tree.heading("Date/Heure HTML", text="Date/Heure HTML (0-23h MEZ/MESZ)")
        tree.heading("Temp. originale", text="Temp. originale")
        tree.heading("Temp. ajustée", text="Temp. ajustée")
        tree.heading("Irradiation", text="Irradiation")

        # Ajuster la largeur des colonnes
        tree.column("Façade", width=150)
        tree.column(
            "Date/Heure DAT", width=180
        )  # Augmenté pour accommoder le texte plus long
        tree.column(
            "Date/Heure HTML", width=220
        )  # Augmenté pour accommoder le texte plus long
        tree.column("Temp. originale", width=100)
        tree.column("Temp. ajustée", width=100)
        tree.column("Irradiation", width=100)

        # Ajouter les échantillons avec colorisation selon été/hiver
        for sample in self.preview_data.sample_adjustments:
            # Déterminer si c'est l'heure d'été (MESZ) ou l'heure d'hiver (MEZ)
            is_dst = "MESZ" in sample.solar_datetime_str

            # Appliquer des tags différents selon la saison
            tag = "summer" if is_dst else "winter"

            item_id = tree.insert(
                "",
                tk.END,
                values=(
                    sample.facade_id,
                    sample.weather_datetime_str,
                    sample.solar_datetime_str,
                    f"{sample.original_temp:.1f}°C",
                    f"{sample.adjusted_temp:.1f}°C",
                    f"{sample.solar_irradiance:.0f} W/m²",
                ),
                tags=(tag,),
            )

        # Configuration des tags pour la coloration
        tree.tag_configure(
            "summer", background="#FFFFE0"
        )  # Jaune pâle pour l'été (MESZ)
        tree.tag_configure(
            "winter", background="#E0F0FF"
        )  # Bleu pâle pour l'hiver (MEZ)

        # Scrollbar pour le treeview
        scrollbar_tree = ttk.Scrollbar(
            content_frame, orient=tk.VERTICAL, command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar_tree.set)

        # Option pour afficher les heures en UTC
        self.show_utc = tk.BooleanVar(value=False)

        # Fonction pour basculer entre les affichages d'heures
        def toggle_utc_display():
            # Effacer le contenu actuel
            for item in tree.get_children():
                tree.delete(item)

            # Réafficher les données avec le format approprié
            for sample in self.preview_data.sample_adjustments:
                # Déterminer si c'est l'heure d'été (MESZ) ou l'heure d'hiver (MEZ)
                is_dst = "MESZ" in sample.solar_datetime_str
                tag = "summer" if is_dst else "winter"

                if (
                    self.show_utc.get()
                    and sample.weather_datetime_utc
                    and sample.solar_datetime_utc
                ):
                    # Format UTC pour les deux colonnes
                    weather_time_str = sample.weather_datetime_utc.strftime(
                        "%d.%m.%Y %H:%M UTC"
                    )
                    solar_time_str = sample.solar_datetime_utc.strftime(
                        "%d.%m.%Y %H:%M UTC"
                    )
                else:
                    # Format original pour les deux colonnes
                    weather_time_str = sample.weather_datetime_str
                    solar_time_str = sample.solar_datetime_str

                tree.insert(
                    "",
                    tk.END,
                    values=(
                        sample.facade_id,
                        weather_time_str,
                        solar_time_str,
                        f"{sample.original_temp:.1f}°C",
                        f"{sample.adjusted_temp:.1f}°C",
                        f"{sample.solar_irradiance:.0f} W/m²",
                    ),
                    tags=(tag,),
                )

        # Créer un cadre pour l'option
        option_frame = tk.Frame(content_frame)
        option_frame.pack(fill=tk.X, pady=(0, 5))

        # Ajouter la case à cocher
        utc_check = tk.Checkbutton(
            option_frame,
            text="Afficher les heures en UTC (pour visualiser la correspondance exacte)",
            variable=self.show_utc,
            command=toggle_utc_display,
            font=("Arial", 9),
        )
        utc_check.pack(anchor="w", padx=5)

        # Pack les widgets principaux
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)

        # Note explicative avec légende
        note_frame = tk.Frame(parent)
        note_frame.pack(fill=tk.X, pady=(10, 0))

        # Afficher le nombre total d'exemples
        note_text = f"💡 Note: {len(self.preview_data.sample_adjustments)} échantillons représentatifs sur {self.preview_data.total_adjustments:,} ajustements totaux"
        tk.Label(note_frame, text=note_text, font=("Arial", 10), fg="gray").pack(
            anchor="w", padx=5
        )

        # Légende des couleurs
        legend_frame = tk.Frame(note_frame)
        legend_frame.pack(pady=5, anchor="w")

        # Légende heure d'été
        summer_frame = tk.Frame(legend_frame, bg="#FFFFE0", width=20, height=20)
        summer_frame.pack(side=tk.LEFT, padx=5)
        summer_label = tk.Label(
            legend_frame, text="Heure d'été (MESZ)", font=("Arial", 9)
        )
        summer_label.pack(side=tk.LEFT, padx=5)

        # Légende heure d'hiver
        winter_frame = tk.Frame(legend_frame, bg="#E0F0FF", width=20, height=20)
        winter_frame.pack(side=tk.LEFT, padx=15)
        winter_label = tk.Label(
            legend_frame, text="Heure d'hiver (MEZ)", font=("Arial", 9)
        )
        winter_label.pack(side=tk.LEFT, padx=5)

        # Ajouter un cadre d'information pour expliquer les différences de format horaire
        info_frame = tk.Frame(note_frame, relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, pady=10, padx=5)

        # Icône d'information
        info_label = tk.Label(info_frame, text=" ℹ️ ", font=("Arial", 16), fg="blue")
        info_label.pack(side=tk.LEFT, padx=5)

        # Message d'information
        message_frame = tk.Frame(info_frame)
        message_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)

        tk.Label(
            message_frame,
            text="Notes importantes sur les formats horaires:",
            font=("Arial", 10, "bold"),
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            message_frame,
            text="• Les fichiers DAT utilisent le format 1-24h en MEZ (heure fixe toute l'année)",
            font=("Arial", 9),
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            message_frame,
            text="• Les fichiers HTML utilisent le format 0-23h et alternent entre MEZ et MESZ",
            font=("Arial", 9),
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            message_frame,
            text="• Une même heure UTC peut donc être représentée différemment dans les deux formats",
            font=("Arial", 9),
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            message_frame,
            text="• Le système utilise l'UTC en interne pour garantir la correspondance exacte",
            font=("Arial", 9),
            justify=tk.LEFT,
            anchor="w",
        ).pack(fill=tk.X)

    def _create_wizard_generation_step(self, parent, wizard_window):
        """Crée l'étape 3 du wizard: Génération des fichiers."""
        # Titre de l'étape
        title_frame = tk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 30))

        tk.Label(
            title_frame,
            text="Génération des fichiers ajustés",
            font=("Arial", 14, "bold"),
        ).pack()

        tk.Label(
            title_frame,
            text="Choisissez le dossier de destination et lancez la génération",
            font=("Arial", 10),
            fg="gray",
        ).pack()

        # Contenu principal
        content_frame = tk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Zone de sélection du dossier
        folder_frame = tk.LabelFrame(
            content_frame, text="Dossier de destination", padx=20, pady=20
        )
        folder_frame.pack(fill=tk.X, pady=(0, 30))

        self.output_folder = tk.StringVar(value=str(Path.home() / "Desktop"))

        folder_inner_frame = tk.Frame(folder_frame)
        folder_inner_frame.pack(fill=tk.X)
        folder_inner_frame.grid_columnconfigure(0, weight=1)

        tk.Entry(
            folder_inner_frame,
            textvariable=self.output_folder,
            state="readonly",
            font=("Arial", 10),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        def select_output_folder():
            folder = filedialog.askdirectory(
                title="Sélectionner le dossier de destination"
            )
            if folder:
                self.output_folder.set(folder)

        tk.Button(
            folder_inner_frame, text="Parcourir", command=select_output_folder, width=12
        ).grid(row=0, column=1)

        # Zone de génération
        generation_frame = tk.LabelFrame(
            content_frame, text="Génération", padx=20, pady=20
        )
        generation_frame.pack(fill=tk.BOTH, expand=True)

        # Bouton de génération
        generate_btn = tk.Button(
            generation_frame,
            text="🚀 Générer les fichiers",
            command=lambda: self._start_generation_from_wizard(wizard_window),
            bg="#28a745",
            fg="white",
            font=("Arial", 14, "bold"),
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=3,
        )
        generate_btn.pack(pady=20)

        # Zone de statut
        self.generation_status = tk.Label(
            generation_frame,
            text="Prêt à générer les fichiers",
            font=("Arial", 11),
            fg="blue",
        )
        self.generation_status.pack(pady=(0, 10))

        # Barre de progression pour la génération
        self.generation_progress = ttk.Progressbar(
            generation_frame, mode="indeterminate"
        )
        self.generation_progress.pack(fill=tk.X, pady=10)
        self.generation_progress.pack_forget()

    def _start_generation_from_wizard(self, wizard_window):
        """Lance la génération depuis le wizard."""
        if not self.preview_data:
            messagebox.showerror(
                "Erreur", "Aucune donnée de prévisualisation disponible"
            )
            return

        output_dir = self.output_folder.get()
        if not output_dir:
            messagebox.showerror(
                "Erreur", "Veuillez sélectionner un dossier de destination"
            )
            return

        self.generation_status.config(text="Génération en cours...", fg="orange")
        self.generation_progress.pack(fill=tk.X, pady=10)
        self.generation_progress.start()

        # Lancer la génération dans un thread
        thread = threading.Thread(
            target=lambda: self._do_generation_wizard(output_dir, wizard_window)
        )
        thread.daemon = True
        thread.start()

    def _do_generation_wizard(self, output_dir: str, wizard_window):
        """Effectue la génération des fichiers depuis le wizard."""
        try:
            if not self.preview_data:
                raise ValueError("Aucune donnée de prévisualisation disponible")

            processor = SoschuProcessor()

            generated_files = processor.generate_files(
                preview_data=self.preview_data, output_dir=output_dir
            )

            # Revenir au thread principal
            self.root.after(
                0,
                lambda: self._generation_completed_wizard(
                    generated_files, wizard_window
                ),
            )

        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            self.root.after(0, lambda: self._generation_error_wizard(str(e)))

    def _generation_completed_wizard(self, generated_files: List[str], wizard_window):
        """Appelé quand la génération est terminée depuis le wizard."""
        self.generation_progress.stop()
        self.generation_progress.pack_forget()
        self.generation_status.config(
            text="✅ Génération terminée avec succès!", fg="green"
        )

        file_list = "\n".join([f"• {Path(f).name}" for f in generated_files])
        result = messagebox.askyesno(
            "Génération terminée",
            f"Fichiers générés avec succès:\n\n{file_list}\n\nVoulez-vous fermer l'assistant?",
            icon="question",
        )

        if result:
            wizard_window.destroy()

    def _generation_error_wizard(self, error_msg: str):
        """Appelé en cas d'erreur de génération depuis le wizard."""
        self.generation_progress.stop()
        self.generation_progress.pack_forget()
        self.generation_status.config(text="❌ Erreur lors de la génération", fg="red")
        messagebox.showerror("Erreur de génération", error_msg)

    def run(self):
        """Lance l'application."""

        # Fonction de debug pour afficher les dimensions de la fenêtre et la position des widgets après 1 seconde
        def check_dimensions():
            root_width = self.root.winfo_width()
            root_height = self.root.winfo_height()
            logging.info(f"Dimensions de la fenêtre: {root_width}x{root_height}")

            # Vérifier si le bouton est visible
            button_visible = False
            button_x = self.preview_btn.winfo_rootx() - self.root.winfo_rootx()
            button_y = self.preview_btn.winfo_rooty() - self.root.winfo_rooty()
            button_height = self.preview_btn.winfo_height()

            logging.info(
                f"Position du bouton Prévisualiser: x={button_x}, y={button_y}, height={button_height}"
            )
            if 0 <= button_y <= root_height:
                logging.info("Le bouton devrait être visible dans la fenêtre")
            else:
                logging.warning(
                    f"Le bouton est en dehors de la fenêtre (y={button_y}, window height={root_height})"
                )

        # Exécuter la vérification après que la fenêtre soit complètement chargée
        self.root.after(1000, check_dimensions)
        self.root.mainloop()


if __name__ == "__main__":
    app = SoschuApp()
    app.run()
