from typing import List, Dict
from difflib import SequenceMatcher
from .base_validator import BaseValidator
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..results import ValidationResult, ValidationSeverity, ValidationCategory


class VariableValidator(BaseValidator):
    """Validator for checking if a variable exists in a domain."""

    def __init__(self, fuzzy_match_threshold: float = None, ignore_variables: List[str] = None):
        """
        Initialize the variable validator.

        Args:
            fuzzy_match_threshold: Threshold for fuzzy matching (0.0 to 1.0)
            ignore_variables: List of variables to ignore during validation
        """
        from ..config_manager import ConfigurationManager

        # Get default configuration if not provided
        if fuzzy_match_threshold is None or ignore_variables is None:
            config = ConfigurationManager().get_config()

        self.fuzzy_match_threshold = fuzzy_match_threshold if fuzzy_match_threshold is not None else config.annotation_patterns[
            "settings"]["fuzzy_threshold"]
        self.ignore_variables = ignore_variables if ignore_variables is not None else config.validation.get(
            "ignore_variables", [])

    def validate(
        self,
        annotation: AnnotationData,
        datasets: Dict[str, SDTMDataset]
    ) -> List[ValidationResult]:
        """
        Validate if a variable exists in a domain.

        Args:
            annotation: The annotation to validate
            datasets: Dictionary of SDTM datasets

        Returns:
            List of validation results
        """
        results = []

        # Skip validation if no variable name or if it's in ignored variables
        if not annotation.variable_name:
            return results

        if annotation.variable_name in self.ignore_variables:
            return results

        # Skip validation for SUPP domains - handled by SuppxxValidator
        if annotation.domain and annotation.domain.startswith('SUPP'):
            return results
        
        # Get the dataset for the domain
        dataset = datasets.get(annotation.domain)
        if not dataset:
            return results  # Domain validation will handle this error

        # Check if variable exists in dataset
        if annotation.variable_name not in dataset.variables:
            # Try fuzzy matching
            best_match = None
            best_ratio = 0

            for var_name in dataset.variables:
                ratio = SequenceMatcher(
                    None, annotation.variable_name.lower(), var_name.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = var_name

            if best_match and best_ratio >= self.fuzzy_match_threshold:
                results.append(ValidationResult(
                    annotation=annotation,
                    category=ValidationCategory.TYPO_IN_VARIABLE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Variable '{annotation.variable_name}' not found in {annotation.domain}, but similar to '{best_match}' (similarity: {best_ratio:.2f})"
                ))
            else:
                results.append(ValidationResult(
                    annotation=annotation,
                    category=ValidationCategory.MISSING_VARIABLE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Variable '{annotation.variable_name}' not found in {annotation.domain}"
                ))

        return results
