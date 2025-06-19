from gui.components.file_selector import FileSelector


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
