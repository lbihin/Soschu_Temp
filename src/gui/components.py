import tkinter as tk
from tkinter import filedialog


class FileSelector:
    """Composant réutilisable pour la sélection de fichiers avec filtrage par extension."""

    def __init__(
        self,
        parent,
        label_text,
        file_extension=None,
        file_description=None,
        row=0,
        entry_width=50,
    ):
        """
        Initialise le composant de sélection de fichier.

        Args:
            parent: Le widget parent (Frame)
            label_text: Le texte du label (ex: "Wetter (.dat):")
            file_extension: L'extension de fichier à filtrer (ex: ".dat")
            file_description: Description du type de fichier (ex: "Weather Data Files")
            row: La ligne dans la grille où placer le composant
            entry_width: Largeur du champ de saisie
        """
        self.parent = parent
        self.file_extension = file_extension
        self.file_description = file_description

        # Créer les widgets
        self.label = tk.Label(parent, text=label_text)
        self.entry = tk.Entry(parent, width=entry_width)
        self.button = tk.Button(parent, text="Browse...", command=self._select_file)

        # Placer les widgets dans la grille
        self.label.grid(row=row, column=0, sticky="w", pady=5)
        self.entry.grid(row=row, column=1, sticky="we", pady=5)
        self.button.grid(row=row, column=2, padx=5, pady=5)

    def _select_file(self):
        """Ouvre la boîte de dialogue de sélection de fichier."""
        if self.file_extension and self.file_description:
            filetypes = [
                (self.file_description, f"*{self.file_extension}"),
                ("All files", "*.*"),
            ]
        else:
            filetypes = [("All files", "*.*")]

        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, filename)

    def get_filename(self):
        """Retourne le nom de fichier actuellement sélectionné."""
        return self.entry.get()

    def set_filename(self, filename):
        """Définit le nom de fichier dans le champ de saisie."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, filename)

    def clear(self):
        """Vide le champ de saisie."""
        self.entry.delete(0, tk.END)
