"""
File operation error handling system for SDTM Annotation Checker.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)
file_access_logger = logging.getLogger("file_access")


@dataclass
class FileOperationResult:
    """Result of a file operation."""
    success: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    backup_path: Optional[str] = None


class FileOperationHandler:
    """Handles file operations and their errors."""

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize the file operation handler.

        Args:
            backup_dir: Directory to store backup files (optional)
        """
        self.backup_dir = backup_dir
        if backup_dir:
            os.makedirs(backup_dir, exist_ok=True)

    def save_file(self, file_path: str, content: str, create_backup: bool = True) -> FileOperationResult:
        """
        Save content to a file with error handling.

        Args:
            file_path: Path to the file
            content: Content to write
            create_backup: Whether to create a backup before saving

        Returns:
            FileOperationResult containing operation status and messages
        """
        try:
            file_path = Path(file_path)

            # Check if file exists and create backup if needed
            backup_path = None
            if create_backup and file_path.exists():
                backup_result = self._create_backup(file_path)
                if not backup_result.success:
                    return FileOperationResult(
                        success=False,
                        error=f"Failed to create backup: {backup_result.error}"
                    )
                backup_path = backup_result.backup_path

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            file_access_logger.info(f"Saved file: {file_path}")
            return FileOperationResult(
                success=True,
                backup_path=backup_path
            )

        except PermissionError as e:
            error_msg = f"Permission denied when saving file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

        except OSError as e:
            error_msg = f"Error saving file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

    def load_file(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Load content from a file with error handling.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (content, error_message)
        """
        try:
            file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                return None, error_msg

            # Check if path is a file
            if not file_path.is_file():
                error_msg = f"Path is not a file: {file_path}"
                logger.error(error_msg)
                return None, error_msg

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_access_logger.info(f"Loaded file: {file_path}")
            return content, None

        except PermissionError as e:
            error_msg = f"Permission denied when reading file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return None, error_msg

        except OSError as e:
            error_msg = f"Error reading file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return None, error_msg

    def delete_file(self, file_path: str, create_backup: bool = True) -> FileOperationResult:
        """
        Delete a file with error handling.

        Args:
            file_path: Path to the file
            create_backup: Whether to create a backup before deleting

        Returns:
            FileOperationResult containing operation status and messages
        """
        try:
            file_path = Path(file_path)

            # Check if file exists
            if not file_path.exists():
                return FileOperationResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )

            # Create backup if needed
            backup_path = None
            if create_backup:
                backup_result = self._create_backup(file_path)
                if not backup_result.success:
                    return FileOperationResult(
                        success=False,
                        error=f"Failed to create backup: {backup_result.error}"
                    )
                backup_path = backup_result.backup_path

            # Delete file
            file_path.unlink()

            file_access_logger.info(f"Deleted file: {file_path}")
            return FileOperationResult(
                success=True,
                backup_path=backup_path
            )

        except PermissionError as e:
            error_msg = f"Permission denied when deleting file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

        except OSError as e:
            error_msg = f"Error deleting file: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

    def move_file(self, source_path: str, target_path: str, create_backup: bool = True) -> FileOperationResult:
        """
        Move a file with error handling.

        Args:
            source_path: Source file path
            target_path: Target file path
            create_backup: Whether to create a backup before moving

        Returns:
            FileOperationResult containing operation status and messages
        """
        try:
            source_path = Path(source_path)
            target_path = Path(target_path)

            # Check if source file exists
            if not source_path.exists():
                return FileOperationResult(
                    success=False,
                    error=f"Source file not found: {source_path}"
                )

            # Create backup if needed
            backup_path = None
            if create_backup:
                backup_result = self._create_backup(source_path)
                if not backup_result.success:
                    return FileOperationResult(
                        success=False,
                        error=f"Failed to create backup: {backup_result.error}"
                    )
                backup_path = backup_result.backup_path

            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source_path), str(target_path))

            file_access_logger.info(
                f"Moved file: {source_path} -> {target_path}")
            return FileOperationResult(
                success=True,
                backup_path=backup_path
            )

        except PermissionError as e:
            error_msg = f"Permission denied when moving file: {source_path} -> {target_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

        except OSError as e:
            error_msg = f"Error moving file: {source_path} -> {target_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

    def check_permissions(self, input_files: List[str], output_dirs: List[str]) -> List[str]:
        """
        Check read/write permissions for files and directories.

        Args:
            input_files: List of file paths to check for read access
            output_dirs: List of directory paths to check for write access

        Returns:
            List of error messages. An empty list means all checks passed.
        """
        errors = []

        for file_path in input_files:
            p = Path(file_path)
            if not p.exists():
                errors.append(f"Input file does not exist: {file_path}")
            elif not os.access(p, os.R_OK):
                errors.append(
                    f"No read permission for input file: {file_path}")

        for dir_path in output_dirs:
            p = Path(dir_path)
            if not p.exists():
                # Try to create the directory if it doesn't exist
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    errors.append(
                        f"Could not create output directory: {dir_path} ({e})")
            elif not os.access(p, os.W_OK):
                errors.append(
                    f"No write permission for output directory: {dir_path}")

        return errors

    def _create_backup(self, file_path: Path) -> FileOperationResult:
        """
        Create a backup of a file.

        Args:
            file_path: Path to the file

        Returns:
            FileOperationResult containing operation status and messages
        """
        try:
            if not self.backup_dir:
                return FileOperationResult(
                    success=False,
                    error="Backup directory not configured"
                )

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = Path(self.backup_dir) / backup_name

            # Copy file to backup location
            shutil.copy2(file_path, backup_path)

            return FileOperationResult(
                success=True,
                backup_path=str(backup_path)
            )

        except PermissionError as e:
            error_msg = f"Permission denied when creating backup: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)

        except OSError as e:
            error_msg = f"Error creating backup: {file_path}"
            logger.error(f"{error_msg}: {e}")
            return FileOperationResult(success=False, error=error_msg)
