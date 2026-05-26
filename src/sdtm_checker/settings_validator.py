"""
Settings validation system for SDTM Annotation Checker.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Validation rule for a setting."""
    name: str
    type: type
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None


@dataclass
class ValidationResult:
    """Result of settings validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class SettingsValidator:
    """Validates configuration settings."""

    def __init__(self):
        """Initialize the settings validator."""
        self.rules = {
            # Pattern settings
            "fuzzy_matching": ValidationRule(
                name="Fuzzy Matching",
                type=bool,
                required=True
            ),
            "fuzzy_threshold": ValidationRule(
                name="Fuzzy Threshold",
                type=float,
                required=True,
                min_value=0.0,
                max_value=1.0
            ),

            # Validation settings
            "ignore_domains": ValidationRule(
                name="Ignore Domains",
                type=list,
                required=False,
                custom_validator=self._validate_domain_list
            ),
            "ignore_variables": ValidationRule(
                name="Ignore Variables",
                type=list,
                required=False,
                custom_validator=self._validate_variable_list
            ),

            # Output settings
            "output_format": ValidationRule(
                name="Output Format",
                type=str,
                required=True,
                allowed_values=["xlsx", "csv", "json"]
            ),
            "include_timestamp": ValidationRule(
                name="Include Timestamp",
                type=bool,
                required=True
            ),
            "max_results": ValidationRule(
                name="Max Results",
                type=int,
                required=True,
                min_value=1,
                max_value=10000
            )
        }

    def validate_settings(self, settings: Dict[str, Any]) -> ValidationResult:
        """
        Validate all settings in the configuration.

        Args:
            settings: Dictionary of settings to validate

        Returns:
            ValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        # Check required settings
        for setting_key, rule in self.rules.items():
            if rule.required and setting_key not in settings:
                errors.append(f"Missing required setting: {rule.name}")
                continue

            if setting_key in settings:
                value = settings[setting_key]
                result = self._validate_setting(setting_key, value, rule)
                errors.extend(result.errors)
                warnings.extend(result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_setting(self, key: str, value: Any, rule: ValidationRule) -> ValidationResult:
        """
        Validate a single setting value.

        Args:
            key: Setting key
            value: Setting value
            rule: Validation rule

        Returns:
            ValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        try:
            # Check type
            if not isinstance(value, rule.type):
                errors.append(
                    f"{rule.name} must be of type {rule.type.__name__}")
                return ValidationResult(False, errors, warnings)

            # Check numeric range
            if rule.type in (int, float) and value is not None:
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(
                        f"{rule.name} must be greater than or equal to {rule.min_value}")
                if rule.max_value is not None and value > rule.max_value:
                    errors.append(
                        f"{rule.name} must be less than or equal to {rule.max_value}")

            # Check allowed values
            if rule.allowed_values is not None and value not in rule.allowed_values:
                errors.append(
                    f"{rule.name} must be one of: {', '.join(map(str, rule.allowed_values))}")

            # Run custom validator if provided
            if rule.custom_validator is not None:
                custom_result = rule.custom_validator(value)
                if not custom_result.is_valid:
                    errors.extend(custom_result.errors)
                    warnings.extend(custom_result.warnings)

            return ValidationResult(len(errors) == 0, errors, warnings)

        except Exception as e:
            logger.error(f"Error validating setting {key}: {e}")
            errors.append(f"Error validating {rule.name}: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _validate_domain_list(self, domains: List[str]) -> ValidationResult:
        """
        Validate list of domains to ignore.

        Args:
            domains: List of domain names

        Returns:
            ValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        if not isinstance(domains, list):
            errors.append("Ignore Domains must be a list")
            return ValidationResult(False, errors, warnings)

        for domain in domains:
            if not isinstance(domain, str):
                errors.append(
                    f"Domain must be a string, got {type(domain).__name__}")
                continue

            if not domain:
                errors.append("Domain cannot be empty")
                continue

            if not domain.isupper():
                warnings.append(f"Domain should be uppercase: {domain}")

            if len(domain) != 2:
                warnings.append(f"Domain should be 2 characters: {domain}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_variable_list(self, variables: List[str]) -> ValidationResult:
        """
        Validate list of variables to ignore.

        Args:
            variables: List of variable names

        Returns:
            ValidationResult containing validation status and messages
        """
        errors = []
        warnings = []

        if not isinstance(variables, list):
            errors.append("Ignore Variables must be a list")
            return ValidationResult(False, errors, warnings)

        for variable in variables:
            if not isinstance(variable, str):
                errors.append(
                    f"Variable must be a string, got {type(variable).__name__}")
                continue

            if not variable:
                errors.append("Variable cannot be empty")
                continue

            if not variable.isupper():
                warnings.append(f"Variable should be uppercase: {variable}")

            if not variable.replace("_", "").isalnum():
                errors.append(
                    f"Variable contains invalid characters: {variable}")

        return ValidationResult(len(errors) == 0, errors, warnings)
