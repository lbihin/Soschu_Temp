import logging
import threading
import tkinter as tk
from typing import Any, Callable, List, Optional

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


class TriggerButton(tk.Button):
    """
    Bouton intelligent qui se désactive automatiquement si les éléments obligatoires
    ne sont pas présents et qui peut déclencher une fonction backend.
    """

    def __init__(
        self,
        parent,
        text="Execute",
        backend_function: Optional[Callable] = None,
        mandatory_elements: Optional[List] = None,
        validate_function: Optional[Callable] = None,
        success_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        loading_text="Processing...",
        run_in_thread=True,
        check_interval=500,  # ms
        **kwargs,
    ):
        """
        Initialise le bouton trigger.

        Args:
            parent: Widget parent
            text: Texte du bouton
            backend_function: Fonction à exécuter lors du clic
            mandatory_elements: Liste des éléments obligatoires à vérifier
            validate_function: Fonction personnalisée de validation (retourne bool)
            success_callback: Fonction appelée en cas de succès
            error_callback: Fonction appelée en cas d'erreur
            loading_text: Texte affiché pendant l'exécution
            run_in_thread: Si True, exécute la fonction backend dans un thread séparé
            check_interval: Intervalle de vérification des éléments obligatoires (ms)
            **kwargs: Arguments supplémentaires pour tk.Button
        """
        super().__init__(parent, text=text, command=self._on_click, **kwargs)

        self.original_text = text
        self.loading_text = loading_text
        self.backend_function = backend_function
        self.mandatory_elements = mandatory_elements or []
        self.validate_function = validate_function
        self.success_callback = success_callback
        self.error_callback = error_callback
        self.run_in_thread = run_in_thread
        self.check_interval = check_interval

        self.is_processing = False
        self._result_pending = None
        self._error_pending = None

        # Démarrer la vérification périodique
        self._schedule_validation_check()

    def _schedule_validation_check(self):
        """Programme la prochaine vérification de validation."""
        self._check_validation()
        self._check_pending_results()
        self.after(self.check_interval, self._schedule_validation_check)

    def _check_pending_results(self):
        """Vérifie s'il y a des résultats en attente à traiter."""
        if self._result_pending is not None:
            result = self._result_pending
            self._result_pending = None
            self._on_success(result)
        elif self._error_pending is not None:
            error = self._error_pending
            self._error_pending = None
            self._on_error(error)

    def _check_validation(self):
        """Vérifie si le bouton doit être activé ou désactivé."""
        if self.is_processing:
            return

        is_valid = self._validate_mandatory_elements()

        # Validation personnalisée supplémentaire (seulement si fournie)
        if is_valid and self.validate_function is not None:
            try:
                is_valid = bool(self.validate_function())
            except Exception as e:
                print(f"Erreur dans la fonction de validation: {e}")
                is_valid = False

        # Activer/désactiver le bouton
        self.config(state=tk.NORMAL if is_valid else tk.DISABLED)

    def _validate_mandatory_elements(self) -> bool:
        """
        Vérifie que tous les éléments obligatoires sont présents et valides.

        Returns:
            bool: True si tous les éléments sont valides
        """
        for element in self.mandatory_elements:
            if not self._is_element_valid(element):
                return False
        return True

    def _is_element_valid(self, element) -> bool:
        """
        Vérifie si un élément est valide.

        Args:
            element: Élément à vérifier (peut être un widget, un objet avec méthodes, etc.)

        Returns:
            bool: True si l'élément est valide
        """
        # Si c'est un widget Entry
        if hasattr(element, "get"):
            value = element.get().strip()
            return len(value) > 0

        # Si c'est un objet avec une méthode get_value
        if hasattr(element, "get_value"):
            value = element.get_value()
            return value is not None and str(value).strip() != ""

        # Si c'est un objet avec une méthode is_valid
        if hasattr(element, "is_valid"):
            return element.is_valid()

        # Si c'est un objet avec une méthode get_filename (FileSelector)
        if hasattr(element, "get_filename"):
            filename = element.get_filename().strip()
            return len(filename) > 0  # Version normale restaurée

        # Si c'est un callable (fonction de validation)
        if callable(element):
            try:
                return bool(element())
            except Exception:
                return False

        # Si c'est une valeur simple
        if isinstance(element, (str, int, float)):
            return element is not None and str(element).strip() != ""

        # Par défaut, considérer comme valide si l'objet existe
        return element is not None

    def _on_click(self):
        """Gestionnaire de clic du bouton."""
        if self.is_processing or not self.backend_function:
            return

        # Vérification finale avant exécution
        if not self._validate_mandatory_elements():
            if self.error_callback:
                self.error_callback("Éléments obligatoires manquants")
            return

        # Démarrer le traitement
        self._start_processing()

        if self.run_in_thread:
            # Exécuter dans un thread séparé
            thread = threading.Thread(target=self._execute_backend, daemon=True)
            thread.start()
        else:
            # Exécuter directement
            self._execute_backend()

    def _start_processing(self):
        """Démarre l'état de traitement."""
        logger.debug("Starting processing...")
        self.is_processing = True
        self.config(text=self.loading_text, state=tk.DISABLED)

    def _stop_processing(self):
        """Arrête l'état de traitement."""
        logger.debug("Stopping processing...")
        self.is_processing = False
        self.config(text=self.original_text)
        logger.debug(f"Reset text to: {self.original_text}")
        self._check_validation()  # Réévaluer l'état du bouton

    def _execute_backend(self):
        """Exécute la fonction backend."""
        logger.debug("Starting backend execution...")
        try:
            if not self.backend_function:
                raise ValueError("Aucune fonction backend définie")

            # Collecter les arguments depuis les éléments obligatoires
            args = self._collect_arguments()
            logger.debug(f"Collected {len(args)} arguments")

            # Exécuter la fonction backend
            if args:
                result = self.backend_function(*args)
            else:
                result = self.backend_function()

            logger.debug(f"Backend function completed with result: {result}")

            # Stocker le résultat pour traitement dans le thread principal
            self._result_pending = result

        except Exception as e:
            logger.error(f"Exception in backend execution: {e}")
            # Stocker l'erreur pour traitement dans le thread principal
            self._error_pending = e

    def _collect_arguments(self) -> List[Any]:
        """
        Collecte les arguments depuis les éléments obligatoires.

        Returns:
            List: Liste des valeurs des éléments obligatoires
        """
        args = []
        for element in self.mandatory_elements:
            if hasattr(element, "get_value"):
                args.append(element.get_value())
            elif hasattr(element, "get_filename"):
                args.append(element.get_filename())
            elif hasattr(element, "get"):
                args.append(element.get())
            else:
                args.append(element)
        return args

    def _on_success(self, result):
        """Gestionnaire de succès."""
        logger.debug(f"Success callback called with result: {result}")
        self._stop_processing()
        if self.success_callback:
            self.success_callback(result)
        logger.debug("Success callback completed")

    def _on_error(self, error):
        """Gestionnaire d'erreur."""
        logger.debug(f"Error callback called with error: {error}")
        self._stop_processing()
        if self.error_callback:
            self.error_callback(str(error))
        else:
            logger.error(f"Erreur lors de l'exécution: {error}")
        logger.debug("Error callback completed")

    def add_mandatory_element(self, element):
        """Ajoute un élément obligatoire à la liste."""
        if element not in self.mandatory_elements:
            self.mandatory_elements.append(element)

    def remove_mandatory_element(self, element):
        """Supprime un élément obligatoire de la liste."""
        if element in self.mandatory_elements:
            self.mandatory_elements.remove(element)

    def set_backend_function(self, func: Callable):
        """Définit ou change la fonction backend."""
        self.backend_function = func

    def force_validate(self):
        """Force une vérification immédiate de la validation."""
        self._check_validation()

    def simulate_click(self):
        """Simule un clic sur le bouton (utile pour les tests)."""
        if self.cget("state") == tk.NORMAL:
            self._on_click()
