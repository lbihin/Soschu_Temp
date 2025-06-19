from solar import SolarDataParser


def get_solar_irradiance_data_points(solar_file_path: str):
    """Load solar irradiance data points from a file."""
    parser = SolarDataParser()
    _, data_points = parser.parse_file(solar_file_path)

    if not data_points:
        raise ValueError("No data points found in the file")

    return data_points