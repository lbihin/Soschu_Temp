import tkinter as tk

from core import process_weather_with_solar_data
from gui.services import (
    create_computation_setting,
    create_file_selector,
    create_trigger_button,
)


def main():
    root = tk.Tk()
    root.title("Soschu Temparatur")
    root.geometry("800x200")
    root.resizable(False, False)

    # Create a frame for main content
    main_frame = tk.Frame(root, bg="#d0d0d0", padx=10, pady=10)

    # Create a frame for the parameters
    params_frame = tk.Frame(root, bg="#c0c0c0", padx=10, pady=10)

    # Create a grid layout for the main frame
    main_frame.grid(row=0, column=0, sticky="nsew")
    params_frame.grid(row=1, column=0, sticky="nsew")

    # Setup the grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_columnconfigure(0, weight=1)

    # Set up main_frame grid
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=4)

    # Create file input fields using create_file_selector function
    weather_selector = create_file_selector(
        parent=main_frame,
        label_text="Wetter:",
        file_extension=".dat",
        file_description="Weather Data Files",
        row=0,
    )

    solar_selector = create_file_selector(
        parent=main_frame,
        label_text="Solar:",
        file_extension=".html",
        file_description="HTML Files",
        row=1,
    )

    # Configure params_frame grid
    params_frame.grid_columnconfigure(0, weight=1)
    params_frame.grid_columnconfigure(1, weight=1)
    params_frame.grid_columnconfigure(2, weight=1)

    # Create computation settings in params_frame
    threshold_setting = create_computation_setting(
        parent=params_frame,
        setting_name="Schwellwert",
        default_value="200",
        unit_text="W/m²",
        tooltip_description="Sonnenschutzschwellwert in Watt pro Quadratmeter",
        validate_numeric=True,
        row=0,
        column=0,
        sticky="w",
        padx=5,
        pady=5,
    )

    delta_t_setting = create_computation_setting(
        parent=params_frame,
        setting_name="∆T Temperaturerhöhung",
        default_value="7",
        unit_text="K",
        tooltip_description="Temperaturerhöhung in Grad Celsius",
        validate_numeric=True,
        row=0,
        column=1,
        sticky="w",
        padx=5,
        pady=5,
    )  # Create Calculate button using TriggerButton

    def backend_calculation(weather_file, solar_file, threshold, delta_t):
        """Fonction backend pour les calculs."""
        # Extraction des valeurs depuis les objets ComputationSetting si nécessaire
        if hasattr(threshold, "get_numeric_value"):
            threshold_value = threshold.get_numeric_value()
            if threshold_value is None:
                raise ValueError(f"Invalid threshold value: {threshold.get_value()}")
        else:
            threshold_value = float(threshold)

        if hasattr(delta_t, "get_numeric_value"):
            delta_t_value = delta_t.get_numeric_value()
            if delta_t_value is None:
                raise ValueError(f"Invalid delta_t value: {delta_t.get_value()}")
        else:
            delta_t_value = float(delta_t)

        # Extraction des noms de fichiers si nécessaire
        if hasattr(weather_file, "get_filename"):
            weather_file_path = weather_file.get_filename()
        else:
            weather_file_path = weather_file

        if hasattr(solar_file, "get_filename"):
            solar_file_path = solar_file.get_filename()
        else:
            solar_file_path = solar_file

        if not weather_file_path or not solar_file_path:
            raise ValueError("Both weather and solar files must be selected")

        # Traitement principal avec la nouvelle fonctionnalité core
        output_files = process_weather_with_solar_data(
            weather_file_path=weather_file_path,
            solar_file_path=solar_file_path,
            threshold=threshold_value,
            delta_t=delta_t_value,
            output_dir="output",
        )

        print(f"Generated {len(output_files)} output files:")
        for facade, filepath in output_files.items():
            print(f"  {facade}: {filepath}")

        # Retourner un résultat pour déclencher le callback de succès
        return f"Calcul terminé! {len(output_files)} fichiers générés dans le dossier 'output'"

    calculate_button = create_trigger_button(
        parent=params_frame,
        text="Rechnen",
        execute_on_click=backend_calculation,
        on_click_args=[
            weather_selector,
            solar_selector,
            threshold_setting,
            delta_t_setting,
        ],
        success_message="Calcul terminé avec succès",
        error_message="Erreur lors du calcul",
        row=0,
        column=2,
        sticky="e",
        font=("Arial", 10, "bold"),
        relief=tk.RAISED,
    )


if __name__ == "__main__":
    main()
    tk.mainloop()
