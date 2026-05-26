from typing import List, Dict
from .base_validator import BaseValidator
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..validation_engine import ValidationResult, ValidationSeverity, ValidationCategory


class SuppxxValidator(BaseValidator):
    """Validator for checking if a variable exists in a SUPPxx domain."""

    def __init__(self, ignore_variables: List[str] = None):
        """
        Initialize the SUPPxx validator.

        Args:
            ignore_variables: List of variables to ignore during validation
        """
        self.ignore_variables = ignore_variables or []

    def validate(
        self,
        annotation: AnnotationData,
        datasets: Dict[str, SDTMDataset]
    ) -> List[ValidationResult]:
        """
        Check if the variable in the annotation exists in the SUPPxx domain dataset.

        Args:
            annotation: The annotation to validate
            datasets: The SDTM datasets

        Returns:
            A list of validation results
        """
        results = []
        if not annotation.domain or not annotation.variable_name:
            return results

        # Skip validation for ignored variables
        if annotation.variable_name.upper() in self.ignore_variables:
            return results

        # Only validate SUPP domains
        if not annotation.domain.startswith('SUPP'):
            return results

        if annotation.domain not in datasets:
            return results  # Handled by DomainValidator

        dataset = datasets[annotation.domain]
        variable_names = list(dataset.variables.keys())

        # In SUPPxx, variables are values in QNAM column
        if 'QNAM' not in variable_names:
            results.append(ValidationResult(
                annotation=annotation,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MISSING_VARIABLE,
                message=f"Domain {annotation.domain} is a SUPP domain but does not contain QNAM variable."
            ))
            return results

        qnam_values = dataset.df['QNAM'].unique()
        if annotation.variable_name not in qnam_values:
            results.append(ValidationResult(
                annotation=annotation,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MISSING_VARIABLE,
                message=f"Variable '{annotation.variable_name}' not found in QNAM of {annotation.domain}."
            ))
        return results
