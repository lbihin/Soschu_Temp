"""
Output generation module for the Soschu Temperature tool.

This module provides a clean separation between data processing and file output
using the Strategy pattern. It supports multiple output formats and can be
easily extended for new formats.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Protocol, Union

from weather import WeatherDataPoint, WeatherFileMetadata


class OutputStrategy(ABC):
    """Abstract base class for output generation strategies."""

    @abstractmethod
    def generate_output(
        self,
        file_path: Path,
        metadata: WeatherFileMetadata,
        data_points: List[WeatherDataPoint],
        **kwargs: Any,
    ) -> None:
        """
        Generate output file with given data.

        Args:
            file_path: Output file path
            metadata: File metadata
            data_points: Data points to write
            **kwargs: Additional strategy-specific parameters
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return the file extension for this output format."""
        pass


class TRYFormatStrategy(OutputStrategy):
    """Strategy for generating TRY format weather files."""

    def __init__(self, encoding: str = "latin1"):
        """
        Initialize TRY format strategy.

        Args:
            encoding: File encoding (default: latin1 for TRY files)
        """
        self.encoding = encoding
        self.logger = logging.getLogger(__name__)

    def generate_output(
        self,
        file_path: Path,
        metadata: WeatherFileMetadata,
        data_points: List[WeatherDataPoint],
        **kwargs: Any,
    ) -> None:
        """
        Generate TRY format output file.

        Args:
            file_path: Output file path
            metadata: Weather file metadata with original header/data lines
            data_points: List of weather data points
            **kwargs: Additional parameters (unused)
        """
        with open(file_path, "w", encoding=self.encoding) as f:
            # Write original header lines to preserve exact format
            for header_line in metadata.original_header_lines:
                f.write(header_line)

            # Write data lines, preserving original format but with updated values
            if len(metadata.original_data_lines) == len(data_points):
                # We have original lines - preserve their exact format
                for original_line, data_point in zip(
                    metadata.original_data_lines, data_points
                ):
                    modified_line = data_point.to_original_format_line(original_line)
                    f.write(modified_line)
            else:
                # Fallback to standard format if original lines not available
                self.logger.warning(
                    "Original data lines not available, using standard format"
                )
                for point in data_points:
                    f.write(point._format_standard_line())

    def get_file_extension(self) -> str:
        """Return the file extension for TRY format."""
        return ".dat"



class OutputGenerator:
    """
    Main output generator class using the Strategy pattern.

    This class provides a clean interface for generating output files in various
    formats while keeping the logic separated from data processing.
    """

    def __init__(self, strategy: OutputStrategy):
        """
        Initialize output generator with a specific strategy.

        Args:
            strategy: Output strategy to use
        """
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

    def set_strategy(self, strategy: OutputStrategy) -> None:
        """
        Change the output strategy.

        Args:
            strategy: New output strategy to use
        """
        self.strategy = strategy

    def generate_file(
        self,
        file_path: Union[str, Path],
        metadata: WeatherFileMetadata,
        data_points: List[WeatherDataPoint],
        **kwargs: Any,
    ) -> Path:
        """
        Generate output file using the current strategy.

        Args:
            file_path: Output file path (can be string or Path)
            metadata: File metadata
            data_points: Data points to write
            **kwargs: Additional strategy-specific parameters

        Returns:
            Path to the generated file

        Raises:
            ValueError: If file_path is invalid
            IOError: If file cannot be written
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        output_path = Path(file_path)

        # Ensure the file has the correct extension for the strategy
        expected_ext = self.strategy.get_file_extension()
        if not output_path.suffix:
            output_path = output_path.with_suffix(expected_ext)
        elif output_path.suffix != expected_ext:
            self.logger.warning(
                f"File extension {output_path.suffix} doesn't match strategy "
                f"extension {expected_ext}. Using provided extension."
            )

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.strategy.generate_output(output_path, metadata, data_points, **kwargs)
            self.logger.info(f"Successfully generated output file: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to generate output file {output_path}: {e}")
            raise

    def generate_multiple_files(
        self,
        base_path: Union[str, Path],
        file_configs: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> List[Path]:
        """
        Generate multiple output files with different configurations.

        Args:
            base_path: Base directory for output files
            file_configs: List of configurations, each containing:
                - filename: Base filename
                - metadata: WeatherFileMetadata
                - data_points: List[WeatherDataPoint]
                - suffix: Optional suffix for filename
            **kwargs: Additional strategy-specific parameters

        Returns:
            List of paths to generated files
        """
        base_directory = Path(base_path)
        generated_files = []

        for config in file_configs:
            filename = config["filename"]
            suffix = config.get("suffix", "")

            if suffix:
                # Insert suffix before file extension
                name_parts = filename.rsplit(".", 1)
                if len(name_parts) == 2:
                    filename = f"{name_parts[0]}_{suffix}.{name_parts[1]}"
                else:
                    filename = f"{filename}_{suffix}"

            output_path = base_directory / filename

            file_path = self.generate_file(
                output_path,
                config["metadata"],
                config["data_points"],
                **kwargs,
            )
            generated_files.append(file_path)

        return generated_files


# Factory function for creating common output generators
def create_try_generator() -> OutputGenerator:
    """Create an OutputGenerator for TRY format files."""
    return OutputGenerator(TRYFormatStrategy())

