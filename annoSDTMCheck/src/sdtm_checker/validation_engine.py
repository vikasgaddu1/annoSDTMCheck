from typing import List, Dict
from .results import ValidationResult, ValidationSeverity, ValidationCategory

from .dynamic_annotation_parser import AnnotationData
from .sdtm_reader import SDTMDataset
from .validators.base_validator import BaseValidator
from .validators.domain_validator import DomainValidator
from .validators.variable_validator import VariableValidator
from .validators.suppxx_validator import SuppxxValidator
from .validators.relrec_validator import RelrecValidator
from .validators.condition_validator import ConditionValidator


class ValidationEngine:
    """Engine for validating SDTM annotations."""

    def __init__(
        self,
        datasets: Dict[str, SDTMDataset],
        fuzzy_match_threshold: float = None,
        ignore_domains: List[str] = None,
        ignore_variables: List[str] = None
    ):
        """
        Initialize the validation engine.

        Args:
            datasets: Dictionary of SDTM datasets
            fuzzy_match_threshold: Threshold for fuzzy matching (0.0 to 1.0)
            ignore_domains: List of domains to ignore during validation
            ignore_variables: List of variables to ignore during validation
        """
        from .config_manager import ConfigurationManager

        # Get default configuration if not provided
        if fuzzy_match_threshold is None or ignore_variables is None:
            config = ConfigurationManager().get_config()

        self.datasets = datasets
        self.fuzzy_match_threshold = fuzzy_match_threshold if fuzzy_match_threshold is not None else config.annotation_patterns[
            "settings"]["fuzzy_threshold"]
        self.ignore_domains = ignore_domains or []
        self.ignore_variables = ignore_variables if ignore_variables is not None else config.validation.get(
            "ignore_variables", [])
        self.used_datasets = set()  # Track which datasets are referenced

        # Get DM variables once during initialization
        dm_dataset = datasets.get("DM")
        self.dm_variables = dm_dataset.get_variable_list() if dm_dataset else []

        # Initialize validators with appropriate parameters
        self.validators = [
            DomainValidator(ignore_domains=self.ignore_domains),
            VariableValidator(
                fuzzy_match_threshold=self.fuzzy_match_threshold,
                ignore_variables=self.ignore_variables
            ),
            SuppxxValidator(ignore_variables=self.ignore_variables),
            RelrecValidator(),
            ConditionValidator()
        ]

    def register_validator(self, validator: BaseValidator) -> None:
        """Register a validator."""
        self.validators.append(validator)

    def validate_annotation(self, annotation: AnnotationData) -> List[ValidationResult]:
        """
        Validate a single annotation against SDTM datasets using registered validators.

        Args:
            annotation: The annotation to validate

        Returns:
            List of validation results
        """
        results = []

        # Track used datasets
        if annotation.domain:
            self.used_datasets.add(annotation.domain)

        # Handle unmatched annotations
        if not annotation.pattern_type:
            results.append(ValidationResult(
                annotation=annotation,
                category=ValidationCategory.PATTERN_MATCH,
                severity=ValidationSeverity.INFO,
                message="Annotation did not match any known pattern",
                suggested_correction="Update configuration file with appropriate pattern"
            ))
            return results

        # If the variable is in DM domain variables, ensure domain is set to DM
        if annotation.variable_name and annotation.variable_name in self.dm_variables:
            annotation.domain = "DM"
            
        # Skip ALL validation if domain is in ignore list
        if annotation.domain and annotation.domain.upper() in [d.upper() for d in self.ignore_domains]:
            return results

        # Run domain validation for domain label annotations
        if annotation.label and annotation.domain:
            for validator in self.validators:
                if isinstance(validator, DomainValidator):
                    results.extend(validator.validate(
                        annotation, self.datasets))
                    break

        if annotation.is_comment:
            return results

        for validator in self.validators:
            if isinstance(validator, DomainValidator):
                continue
            results.extend(validator.validate(annotation, self.datasets))

        return results

    def validate_annotations(self, annotations: List[AnnotationData]) -> List[ValidationResult]:
        """
        Validate multiple annotations against SDTM datasets.

        Args:
            annotations: List of annotations to validate

        Returns:
            List of validation results
        """
        results = []
        for annotation in annotations:
            results.extend(self.validate_annotation(annotation))
        return results

    def get_unused_datasets(self, datasets: Dict[str, SDTMDataset]) -> List[str]:
        """
        Get a list of datasets that are never referenced in annotations.

        Args:
            datasets: Dictionary of SDTM datasets

        Returns:
            List of dataset names that are never referenced
        """
        all_datasets = set(datasets.keys())
        return sorted(list(all_datasets - self.used_datasets))

    def _is_valid_float(self, value: str) -> bool:
        """Check if a string can be converted to a float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _is_valid_int(self, value: str) -> bool:
        """Check if a string can be converted to an integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
