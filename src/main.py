import tkinter as tk

from gui.components.computation_setting import ComputationSetting
from gui.services import create_computation_setting, create_file_selector


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
        unit_text="ºC",
        tooltip_description="Temperaturerhöhung in Grad Celsius",
        validate_numeric=True,
        row=0,
        column=1,
        sticky="w",
        padx=5,
        pady=5,
    )


if __name__ == "__main__":
    main()
    tk.mainloop()

# ∆T Temperaturerhöhung (ºC)
