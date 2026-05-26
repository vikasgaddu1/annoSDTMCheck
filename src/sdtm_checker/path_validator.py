"""
File path validation system for SDTM Annotation Checker.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PathValidationResult:
    """Result of path validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class PathValidator:
    """Validates file paths and directory permissions."""

    def __init__(self):
        """Initialize the path validator."""
        self.required_paths = {
            "annotated_crf_file": "Annotated CRF File",
            "sdtm_directory": "SDTM Directory",
            "output_directory": "Output Directory",
            "default_output_file": "Default Output File"
        }

    def validate_paths(self, paths: Dict[str, str]) -> PathValidationResult:
        """
        Validate all paths in the configuration.

        Args:
            paths: Dictionary of path configurations

        Returns:
            PathValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        base_dir = os.getcwd()

        # Check required paths
        for path_key, path_name in self.required_paths.items():
            if path_key not in paths:
                errors.append(f"Missing required path: {path_name}")
                continue

            path_value = paths[path_key]
            if not path_value:
                errors.append(f"{path_name} cannot be empty")
                continue

            # Validate path format
            if not self._is_valid_path_format(path_value):
                errors.append(
                    f"Invalid path format for {path_name}: {path_value}")
                continue

            # Check for path traversal
            if not self.is_safe_path(base_dir, path_value):
                errors.append(
                    f"Path traversal detected for {path_name}: {path_value}")
                continue

            # Check directory existence and permissions
            if path_key != "default_output_file":
                dir_result = self._validate_directory(path_value, path_name)
                errors.extend(dir_result.errors)
                warnings.extend(dir_result.warnings)
            else:
                file_result = self._validate_output_file(
                    path_value, paths["output_directory"])
                errors.extend(file_result.errors)
                warnings.extend(file_result.warnings)

        return PathValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _is_valid_path_format(self, path: str) -> bool:
        """
        Check if path has valid format.

        Args:
            path: Path to validate

        Returns:
            True if path format is valid
        """
        try:
            # Check for invalid characters
            invalid_chars = '<>:"|?*'
            if any(char in path for char in invalid_chars):
                return False

            # Check for valid path structure
            path_obj = Path(path)

            # Check for absolute path on Windows
            if os.name == 'nt' and path_obj.is_absolute():
                if not path_obj.drive:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating path format: {e}")
            return False

    def _validate_directory(self, path: str, path_name: str) -> PathValidationResult:
        """
        Validate directory existence and permissions.

        Args:
            path: Directory path to validate
            path_name: Name of the path for error messages

        Returns:
            PathValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        try:
            path_obj = Path(path)

            # Check if directory exists
            if not path_obj.exists():
                errors.append(f"{path_name} does not exist: {path}")
                return PathValidationResult(False, errors, warnings)

            # Check if path is a directory
            if not path_obj.is_dir():
                errors.append(f"{path_name} is not a directory: {path}")
                return PathValidationResult(False, errors, warnings)

            # Check read permission
            if not os.access(path, os.R_OK):
                errors.append(f"No read permission for {path_name}: {path}")

            # Check write permission
            if not os.access(path, os.W_OK):
                errors.append(f"No write permission for {path_name}: {path}")

            # Check if directory is empty
            if not any(path_obj.iterdir()):
                warnings.append(f"{path_name} is empty: {path}")

            return PathValidationResult(len(errors) == 0, errors, warnings)

        except Exception as e:
            logger.error(f"Error validating directory: {e}")
            errors.append(f"Error validating {path_name}: {str(e)}")
            return PathValidationResult(False, errors, warnings)

    def _validate_output_file(self, filename: str, output_dir: str) -> PathValidationResult:
        """
        Validate output file path.

        Args:
            filename: Output file name
            output_dir: Output directory path

        Returns:
            PathValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        try:
            # Check file name format
            if not self._is_valid_filename(filename):
                errors.append(f"Invalid output file name: {filename}")
                return PathValidationResult(False, errors, warnings)

            # Check if output directory exists and is writable
            output_dir_result = self._validate_directory(
                output_dir, "Output Directory")
            if not output_dir_result.is_valid:
                errors.extend(output_dir_result.errors)
                return PathValidationResult(False, errors, warnings)

            # Check if file already exists
            file_path = Path(output_dir) / filename
            if file_path.exists():
                if not os.access(file_path, os.W_OK):
                    errors.append(
                        f"Output file exists but is not writable: {file_path}")
                else:
                    warnings.append(f"Output file already exists: {file_path}")

            return PathValidationResult(len(errors) == 0, errors, warnings)

        except Exception as e:
            logger.error(f"Error validating output file: {e}")
            errors.append(f"Error validating output file: {str(e)}")
            return PathValidationResult(False, errors, warnings)

    def _is_valid_filename(self, filename: str) -> bool:
        """
        Check if filename is valid.

        Args:
            filename: Filename to validate

        Returns:
            True if filename is valid
        """
        try:
            # Check for invalid characters
            invalid_chars = '<>:"/\\|?*'
            if any(char in filename for char in invalid_chars):
                return False

            # Check for valid file extension
            if not filename or '.' not in filename:
                return False

            # Check filename length
            if len(filename) > 255:  # Maximum filename length on most filesystems
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating filename: {e}")
            return False

    def is_safe_path(self, base_dir: str, user_path: str) -> bool:
        """
        Check if a path is safe and does not traverse outside the base directory.

        Args:
            base_dir: The base directory to check against
            user_path: The user-provided path to validate

        Returns:
            True if the path is safe, False otherwise
        """
        try:
            base_path = Path(base_dir).resolve()
            user_path_resolved = Path(user_path).resolve()

            return user_path_resolved.is_relative_to(base_path)
        except Exception as e:
            logger.error(f"Error checking safe path: {e}")
            return False
