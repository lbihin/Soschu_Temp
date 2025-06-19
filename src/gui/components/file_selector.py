import tkinter as tk
from tkinter import filedialog


class FileSelector(tk.Frame):
    """Composant réutilisable pour la sélection de fichiers avec filtrage par extension."""

    def __init__(
        self,
        parent,
        label_text,
        file_extension=None,
        file_description=None,
        entry_width=50,
        **kwargs,
    ):
        """
        Initialise le composant de sélection de fichier.

        Args:
            parent: Le widget parent
            label_text: Le texte du label (ex: "Wetter (.dat):")
            file_extension: L'extension de fichier à filtrer (ex: ".dat")
            file_description: Description du type de fichier (ex: "Weather Data Files")
            entry_width: Largeur du champ de saisie
            **kwargs: Arguments supplémentaires pour le Frame parent
        """
        super().__init__(parent, **kwargs)

        self.file_extension = file_extension
        self.file_description = file_description
        self.has_format_info = (
            file_extension is not None and file_description is not None
        )

        # Configuration de la grille interne
        self.grid_columnconfigure(1, weight=1)  # Entry column expands

        # Créer les widgets
        self.label = tk.Label(self, text=label_text)
        self.entry = tk.Entry(self, width=entry_width)
        self.button = tk.Button(self, text="Browse...", command=self._select_file)

        # Placer les widgets dans la grille interne
        self.label.grid(row=0, column=0, sticky="w", pady=(5, 0), padx=(0, 5))
        self.entry.grid(row=0, column=1, sticky="we", pady=(5, 0), padx=(0, 5))
        self.button.grid(row=0, column=2, pady=(5, 0))

        # Format info label (optionnel)
        self.format_label = None
        if self.has_format_info:
            format_text = f"Supported file formats: {self.file_extension}"
            self.format_label = tk.Label(
                self, text=format_text, font=("Arial", 8), fg="gray"
            )
            self.format_label.grid(
                row=1, column=1, sticky="w", pady=(0, 5), padx=(0, 5)
            )

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
