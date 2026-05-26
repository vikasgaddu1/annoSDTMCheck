"""
Configuration management system for SDTM Annotation Checker.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from werkzeug.security import generate_password_hash, check_password_hash

from .encryption_handler import EncryptionHandler
from .security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class Configuration:
    """Configuration data structure."""
    paths: Dict[str, str] = field(default_factory=lambda: {
        "annotated_crf_file": "",
        "sdtm_directory": "sdtm_data/",
        "output_directory": "output/",
        "default_output_file": "validation_report.xlsx"
    })

    annotation_patterns: Dict[str, Any] = field(default_factory=lambda: {
        "patterns": [],
        "settings": {
            "fuzzy_matching": True,
            "fuzzy_threshold": 0.85
        }
    })

    validation: Dict[str, Any] = field(default_factory=lambda: {
        "ignore_domains": [],
        "ignore_variables": ["STUDYID", "USUBJID"],
        "generic_author_name": "Geron",
        "form_bookmark_label": "Form_bookmarks",
        "sdtm_bookmark_label": "SDTM",
        "auto_resize_textboxes": True,
        "resize_max_width_expansion": 200.0,
        "resize_max_height_expansion": 300.0,
        "resize_skip_pages": "",
        "align_annotations": True,
        "align_horizontal": True,
        "align_vertical": True,
        "horizontal_tolerance": 1.0,
        "vertical_tolerance": 10.0,
        "align_skip_pages": "",
        "apply_xfdf_colors": True,
        "standard_red_color": [255, 0, 0],
        "standard_blue_color": [0, 0, 255],
        "standard_green_color": [0, 124, 0],
        "background_color": [0, 255, 255],  # Cyan RGB
        "textbox_border_color": [0, 0, 0],  # Black RGB
        "normalize_quotes": True  # Normalize quotes around annotation values
    })


class ConfigurationManager:
    """Manages application configuration."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.yaml"
        self.password_file = self.config_dir / ".password"
        self.default_config_file = self.config_dir / "config_template.yaml"

        self.encryption = EncryptionHandler()
        self.audit_logger = AuditLogger()

        self._config: Optional[Configuration] = None
        self._current_config_path: Optional[Path] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Ensure backward compatibility: merge default settings if missing
                default_config = Configuration()
                migration_needed = False
                
                # Update annotation_patterns settings
                if config_data and 'annotation_patterns' in config_data:
                    if 'settings' in config_data['annotation_patterns']:
                        settings = config_data['annotation_patterns']['settings']
                        # Migrate old fuzzy_threshold value (0.8) to new default (0.85)
                        if settings.get('fuzzy_threshold') == 0.8:
                            settings['fuzzy_threshold'] = 0.85
                            migration_needed = True
                        # Ensure fuzzy_threshold exists with default
                        if 'fuzzy_threshold' not in settings:
                            settings['fuzzy_threshold'] = default_config.annotation_patterns['settings']['fuzzy_threshold']
                            migration_needed = True
                        # Ensure fuzzy_matching exists
                        if 'fuzzy_matching' not in settings:
                            settings['fuzzy_matching'] = default_config.annotation_patterns['settings']['fuzzy_matching']
                            migration_needed = True
                
                # Update validation settings
                if config_data and 'validation' in config_data:
                    default_validation = default_config.validation
                    # Merge missing validation settings with defaults
                    for key in default_validation.keys():
                        if key not in config_data['validation']:
                            config_data['validation'][key] = default_validation[key]
                            migration_needed = True
                        # Convert tuples to lists if needed (for old configs)
                        elif isinstance(config_data['validation'][key], tuple):
                            config_data['validation'][key] = list(config_data['validation'][key])
                            migration_needed = True
                
                self._config = Configuration(**config_data)
                self._current_config_path = self.config_file
                
                # Save migrated config back to file if migration occurred
                if migration_needed:
                    try:
                        self.save_configuration()
                        logger.info("Migrated configuration values and saved to file")
                    except Exception as e:
                        # If save fails, continue anyway - migration is in memory
                        logger.warning(f"Failed to save migrated configuration, but migration applied in memory: {e}")
                
                logger.info("Loaded configuration from file")
            else:
                self._load_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration."""
        try:
            if self.default_config_file.exists():
                with open(self.default_config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                self._config = Configuration(**config_data)
            else:
                self._config = Configuration()
            self._current_config_path = None
            logger.info("Loaded default configuration")
        except Exception as e:
            logger.error(f"Error loading default configuration: {e}")
            self._config = Configuration()
            self._current_config_path = None

    def get_config(self) -> Configuration:
        """Get current configuration."""
        if self._config is None:
            self._load_config()
        return self._config

    def get_current_config_path(self) -> Optional[str]:
        """Get the path of the currently loaded configuration file."""
        return str(self._current_config_path) if self._current_config_path else None

    def load_configuration(self, file_path: str) -> None:
        """
        Load configuration from a file.

        Args:
            file_path: Path to the configuration file to load
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {file_path}")

            with open(path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Ensure backward compatibility: merge default settings if missing
            default_config = Configuration()
            
            # Update annotation_patterns settings
            if config_data and 'annotation_patterns' in config_data:
                if 'settings' in config_data['annotation_patterns']:
                    settings = config_data['annotation_patterns']['settings']
                    # Migrate old fuzzy_threshold value (0.8) to new default (0.85)
                    if settings.get('fuzzy_threshold') == 0.8:
                        settings['fuzzy_threshold'] = 0.85
                    # Ensure fuzzy_threshold exists with default
                    if 'fuzzy_threshold' not in settings:
                        settings['fuzzy_threshold'] = default_config.annotation_patterns['settings']['fuzzy_threshold']
                    # Ensure fuzzy_matching exists
                    if 'fuzzy_matching' not in settings:
                        settings['fuzzy_matching'] = default_config.annotation_patterns['settings']['fuzzy_matching']
            
            # Update validation settings
            if config_data and 'validation' in config_data:
                default_validation = default_config.validation
                # Merge missing validation settings with defaults
                for key in default_validation.keys():
                    if key not in config_data['validation']:
                        config_data['validation'][key] = default_validation[key]
                    # Convert tuples to lists if needed (for old configs)
                    elif isinstance(config_data['validation'][key], tuple):
                        config_data['validation'][key] = list(config_data['validation'][key])

            self._config = Configuration(**config_data)
            self._current_config_path = path

            # Log the configuration load
            self.audit_logger.log_event(
                event_type="config_load",
                user=os.getlogin(),
                action="Loaded configuration from file",
                details={"file_path": str(path)}
            )

            logger.info(f"Loaded configuration from {path}")

        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            self.audit_logger.log_event(
                event_type="config_load",
                user=os.getlogin(),
                action="Failed to load configuration",
                details={"error": str(e), "file_path": file_path},
                status="failure"
            )
            raise

    def update_config(self, config_data: Dict[str, Any]) -> None:
        """
        Update configuration with new data.

        Args:
            config_data: New configuration data
        """
        try:
            # Create new configuration
            new_config = Configuration(**config_data)

            # Log the configuration change
            self.audit_logger.log_event(
                event_type="config_change",
                user=os.getlogin(),
                action="Updated configuration",
                details={
                    "changes": self._get_config_changes(self._config, new_config)
                }
            )

            # Update configuration
            self._config = new_config

            logger.info("Configuration updated successfully")

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            self.audit_logger.log_event(
                event_type="config_change",
                user=os.getlogin(),
                action="Failed to update configuration",
                details={"error": str(e)},
                status="failure"
            )
            raise

    def _get_config_changes(self, old_config: Configuration, new_config: Configuration) -> Dict[str, Any]:
        """Get changes between old and new configuration."""
        changes = {}

        # Compare paths
        for key, new_value in new_config.paths.items():
            old_value = old_config.paths.get(key)
            if old_value != new_value:
                changes[f"paths.{key}"] = {
                    "old": old_value,
                    "new": new_value
                }

        # Compare annotation patterns
        for key, new_value in new_config.annotation_patterns["settings"].items():
            old_value = old_config.annotation_patterns["settings"].get(key)
            if old_value != new_value:
                changes[f"annotation_patterns.settings.{key}"] = {
                    "old": old_value,
                    "new": new_value
                }

        # Compare validation settings
        for key, new_value in new_config.validation.items():
            old_value = old_config.validation.get(key)
            if old_value != new_value:
                changes[f"validation.{key}"] = {
                    "old": old_value,
                    "new": new_value
                }

        return changes

    def save_configuration(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            file_path: Optional path to save configuration to. If not provided,
                      will use current config path or prompt for new path.
        """
        try:
            if self._config is None:
                raise ValueError("No configuration to save")

            # Convert configuration to dictionary
            config_data = {
                "paths": self._config.paths,
                "annotation_patterns": self._config.annotation_patterns,
                "validation": self._config.validation
            }

            # Determine save path
            save_path = Path(
                file_path) if file_path else self._current_config_path

            # If no save path specified or using default config, require new path
            if save_path is None or save_path == self.default_config_file:
                raise ValueError(
                    "Must specify a save path when using default configuration")

            # Ensure .yaml extension
            if not save_path.suffix.lower() == '.yaml':
                save_path = save_path.with_suffix('.yaml')

            # Save to file
            with open(save_path, 'w') as f:
                yaml.dump(config_data, f)

            self._current_config_path = save_path
            logger.info(f"Configuration saved successfully to {save_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            self.audit_logger.log_event(
                event_type="config_save",
                user=os.getlogin(),
                action="Failed to save configuration",
                details={"error": str(e)},
                status="failure"
            )
            raise

    def reset_to_default(self) -> None:
        """Reset configuration to default values."""
        try:
            self._load_default_config()

            self.audit_logger.log_event(
                event_type="config_reset",
                user=os.getlogin(),
                action="Reset configuration to default",
                details={}
            )

            logger.info("Configuration reset to default")

        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            self.audit_logger.log_event(
                event_type="config_reset",
                user=os.getlogin(),
                action="Failed to reset configuration",
                details={"error": str(e)},
                status="failure"
            )
            raise

    def set_password(self, password: str) -> None:
        """
        Set configuration password.

        Args:
            password: New password
        """
        try:
            password_hash = generate_password_hash(password)
            with open(self.password_file, 'w') as f:
                f.write(password_hash)

            self.audit_logger.log_event(
                event_type="password_change",
                user=os.getlogin(),
                action="Changed configuration password",
                details={}
            )

            logger.info("Configuration password set")

        except Exception as e:
            logger.error(f"Error setting password: {e}")
            self.audit_logger.log_event(
                event_type="password_change",
                user=os.getlogin(),
                action="Failed to change configuration password",
                details={"error": str(e)},
                status="failure"
            )
            raise

    def check_password(self, password: str) -> bool:
        """
        Check if password is correct.

        Args:
            password: Password to check

        Returns:
            True if password is correct
        """
        try:
            if not self.password_file.exists():
                return True

            with open(self.password_file, 'r') as f:
                stored_hash = f.read().strip()

            return check_password_hash(stored_hash, password)

        except Exception as e:
            logger.error(f"Error checking password: {e}")
            return False

    def validate_configuration(self) -> Tuple[bool, list]:
        """
        Validate current configuration.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate paths
        for path_name, path_value in self._config.paths.items():
            if not path_value:
                errors.append(f"{path_name} is required")
            elif path_name != "default_output_file":
                path = Path(path_value)
                if not path.exists():
                    errors.append(
                        f"{path_name} directory does not exist: {path_value}")
                elif path_name == "output_directory" and not os.access(path, os.W_OK):
                    errors.append(
                        f"{path_name} directory is not writable: {path_value}")

        # Validate patterns
        for pattern in self._config.annotation_patterns["patterns"]:
            if not pattern.get("name"):
                errors.append("Pattern name is required")
            if not pattern.get("regex"):
                errors.append(
                    f"Pattern {pattern.get('name', 'Unnamed')} is missing regex")
            if not pattern.get("groups"):
                errors.append(
                    f"Pattern {pattern.get('name', 'Unnamed')} is missing groups")

        # Validate settings
        settings = self._config.annotation_patterns["settings"]
        if not isinstance(settings.get("fuzzy_matching"), bool):
            errors.append("fuzzy_matching must be a boolean")
        if not isinstance(settings.get("fuzzy_threshold"), (int, float)):
            errors.append("fuzzy_threshold must be a number")
        elif not 0 <= settings.get("fuzzy_threshold", 0) <= 1:
            errors.append("fuzzy_threshold must be between 0 and 1")

        return len(errors) == 0, errors
