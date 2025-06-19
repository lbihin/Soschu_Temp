from gui.components import FileSelector


def create_file_selector(
    parent, label_text, file_extension=None, file_description=None, row=0, entry_width=50
):
    """
    Crée un composant de sélection de fichier.

    Args:
        parent: Le widget parent (Frame)
        label_text: Le texte du label (ex: "Wetter (.dat):")
        file_extension: L'extension de fichier à filtrer (ex: ".dat")
        file_description: Description du type de fichier (ex: "Weather Data Files")
        row: La ligne dans la grille où placer le composant
        entry_width: Largeur du champ de saisie
    """
    return FileSelector(
        parent,
        label_text,
        file_extension=file_extension,
        file_description=file_description,
        row=row,
        entry_width=entry_width,
    )