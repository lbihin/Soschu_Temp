from gui.components.computation_setting import ComputationSetting
from gui.components.file_selector import FileSelector
from gui.components.trigger_button import TriggerButton


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
    backend_function=None,
    mandatory_elements=None,
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
        backend_function: Fonction à exécuter lors du clic
        mandatory_elements: Liste des éléments obligatoires à vérifier
        success_message: Message à afficher en cas de succès
        error_message: Message à afficher en cas d'erreur
        row: Ligne dans la grille parent
        column: Colonne dans la grille parent
        columnspan: Nombre de colonnes à occuper
        sticky: Alignement dans la grille parent
        padx: Espacement horizontal
        pady: Espacement vertical
        **kwargs: Arguments supplémentaires pour TriggerButton

    Returns:
        TriggerButton: L'instance du composant créé
    """

    def default_success_callback(result):
        if success_message:
            print(f"Succès: {success_message}")
        print(f"Résultat: {result}")

    def default_error_callback(error):
        if error_message:
            print(f"Erreur: {error_message}")
        print(f"Détail: {error}")

    button = TriggerButton(
        parent,
        text=text,
        backend_function=backend_function,
        mandatory_elements=mandatory_elements or [],
        success_callback=default_success_callback,
        error_callback=default_error_callback,
        **kwargs,
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
