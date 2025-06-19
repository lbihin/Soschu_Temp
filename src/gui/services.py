import logging

from .components.computation_setting import ComputationSetting
from .components.file_selector import FileSelector
from .components.trigger_button import TriggerButton

# Configuration du logger pour ce module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_file_selector(
    parent,
    label_text,
    file_extension=None,
    file_description=None,
    row=0,
    entry_width=50,
    columnspan=3,
    sticky="ew",
    pady=5,
):
    """
    Crée et place un composant de sélection de fichier dans la grille du parent.

    Args:
        parent: Le widget parent (Frame)
        label_text: Le texte du label (ex: "Wetter (.dat):")
        file_extension: L'extension de fichier à filtrer (ex: ".dat")
        file_description: Description du type de fichier (ex: "Weather Data Files")
        row: La ligne dans la grille où placer le composant
        entry_width: Largeur du champ de saisie
        columnspan: Nombre de colonnes à occuper dans la grille parent
        sticky: Alignement dans la grille parent
        pady: Espacement vertical

    Returns:
        FileSelector: L'instance du composant créé
    """

    selector = FileSelector(
        parent,
        label_text,
        file_extension=file_extension,
        file_description=file_description,
        entry_width=entry_width,
    )

    # Placer le composant dans la grille du parent
    selector.grid(row=row, column=0, columnspan=columnspan, sticky=sticky, pady=pady)

    return selector


def create_computation_setting(
    parent,
    setting_name,
    default_value="",
    unit_text="",
    tooltip_description=None,
    row=0,
    column=0,
    validate_numeric=False,
    entry_width=15,
    sticky="w",
    padx=5,
    pady=5,
):
    """
    Crée et place un composant de paramètre de calcul dans la grille du parent.

    Args:
        parent: Widget parent
        setting_name: Nom du paramètre (affiché comme label)
        default_value: Valeur par défaut dans le champ de saisie
        unit_text: Texte de l'unité affiché après le champ
        tooltip_description: Description pour l'info-bulle (optionnel)
        row: Ligne dans la grille parent
        column: Colonne dans la grille parent
        validate_numeric: Si True, valide que l'entrée est numérique
        entry_width: Largeur du champ de saisie
        sticky: Alignement dans la grille parent
        padx: Espacement horizontal
        pady: Espacement vertical

    Returns:
        ComputationSetting: L'instance du composant créé
    """

    setting = ComputationSetting(
        parent,
        setting_name=setting_name,
        default_value=default_value,
        unit_text=unit_text,
        tooltip_description=tooltip_description,
        validate_numeric=validate_numeric,
        entry_width=entry_width,
    )

    # Placer le composant dans la grille du parent
    setting.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)

    return setting


def create_trigger_button(
    parent,
    text="Execute",
    execute_on_click=None,
    on_click_args=None,
    success_message=None,
    error_message=None,
    row=0,
    column=0,
    columnspan=1,
    sticky="ew",
    padx=5,
    pady=5,
    **kwargs,
):
    """
    Crée et place un bouton trigger qui se désactive automatiquement
    si les éléments obligatoires ne sont pas présents.

    Args:
        parent: Widget parent
        text: Texte du bouton
        execute_on_click: Fonction à exécuter lors du clic
        on_click_args: Liste des widgets dont il faut extraire les valeurs
        success_message: Message à afficher en cas de succès
        error_message: Message à afficher en cas d'erreur
        row: Ligne dans la grille parent
        column: Colonne dans la grille parent
        columnspan: Nombre de colonnes à occuper
        sticky: Alignement dans la grille parent
        padx: Espacement horizontal
        pady: Espacement vertical
        **kwargs: Arguments supplémentaires pour tk.Button (ex: font, relief, etc.)

    Returns:
        TriggerButton: L'instance du composant créé
    """

    def backend_wrapper(*args):
        """Fonction wrapper qui collecte les valeurs et exécute la fonction backend."""
        if not execute_on_click:
            return None

        collected_args = []
        if on_click_args:
            for widget in on_click_args:
                if hasattr(widget, "get_filename"):
                    # Pour les sélecteurs de fichier (FileSelector)
                    collected_args.append(widget.get_filename())
                elif hasattr(widget, "get"):
                    # Pour les Entry, Text, ComputationSetting, etc.
                    collected_args.append(widget.get())
                else:
                    # Fallback: ajouter le widget lui-même
                    collected_args.append(widget)

        return execute_on_click(*collected_args)

    def default_success_callback(result):
        if success_message:
            logger.info(f"Succès: {success_message}")
        logger.info(f"Résultat: {result}")

    def default_error_callback(error):
        if error_message:
            logger.error(f"Erreur: {error_message}")
        logger.error(f"Détail: {error}")

    # Séparer les arguments de positionnement/style des arguments Tkinter
    # Les kwargs contiennent uniquement les arguments pour tk.Button (font, relief, etc.)
    button = TriggerButton(
        parent=parent,
        text=text,
        backend_function=backend_wrapper,
        mandatory_elements=on_click_args or [],
        success_callback=default_success_callback,
        error_callback=default_error_callback,
        **kwargs,  # Seulement les arguments Tkinter valides
    )

    # Placer le composant dans la grille du parent
    button.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky=sticky,
        padx=padx,
        pady=pady,
    )

    return button


def create_preview_button(
    parent,
    text="Prévisualiser",
    preview_function=None,
    on_click_args=None,
    success_callback=None,
    error_callback=None,
    row=0,
    column=0,
    columnspan=1,
    sticky="ew",
    padx=5,
    pady=5,
    **kwargs,
):
    """
    Crée et place un bouton de prévisualisation qui affiche les conversions
    qui vont être appliquées sans les exécuter.

    Args:
        parent: Widget parent
        text: Texte du bouton
        preview_function: Fonction de prévisualisation à exécuter
        on_click_args: Liste des widgets dont il faut extraire les valeurs
        success_callback: Callback personnalisé de succès
        error_callback: Callback personnalisé d'erreur
        row: Ligne dans la grille parent
        column: Colonne dans la grille parent
        columnspan: Nombre de colonnes à occuper
        sticky: Alignement dans la grille parent
        padx: Espacement horizontal
        pady: Espacement vertical
        **kwargs: Arguments supplémentaires pour tk.Button

    Returns:
        TriggerButton: L'instance du composant créé
    """

    def preview_wrapper(*args):
        """Fonction wrapper qui collecte les valeurs et exécute la prévisualisation."""
        if not preview_function:
            return None

        collected_args = []
        if on_click_args:
            for widget in on_click_args:
                if hasattr(widget, "get_filename"):
                    # Pour les sélecteurs de fichier (FileSelector)
                    collected_args.append(widget.get_filename())
                elif hasattr(widget, "get"):
                    # Pour les Entry, Text, ComputationSetting, etc.
                    collected_args.append(widget.get())
                else:
                    # Fallback: ajouter le widget lui-même
                    collected_args.append(widget)

        return preview_function(*collected_args)

    def default_preview_success_callback(result):
        """Callback de succès par défaut."""
        logger.info("Prévisualisation terminée avec succès")
        return result

    def default_preview_error_callback(error):
        """Callback d'erreur par défaut."""
        logger.error(f"Erreur lors de la prévisualisation: {error}")

    button = TriggerButton(
        parent=parent,
        text=text,
        backend_function=preview_wrapper,
        mandatory_elements=on_click_args or [],
        success_callback=success_callback or default_preview_success_callback,
        error_callback=error_callback or default_preview_error_callback,
        **kwargs,
    )

    button.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky=sticky,
        padx=padx,
        pady=pady,
    )

    return button
