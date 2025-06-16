from typing import List, Dict
import re
from .base_validator import BaseValidator
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..validation_engine import ValidationResult, ValidationSeverity, ValidationCategory


class RelrecValidator(BaseValidator):
    """Validator for checking RELREC domain annotations."""

    def validate(self, annotation: AnnotationData, datasets: Dict[str, SDTMDataset]) -> List[ValidationResult]:
        """
        Validate RELREC annotations.
        e.g., RELREC when FASPID = AESPID
        Checks if FASPID and AESPID are in IDVAR column of RELREC.

        Args:
            annotation: The annotation to validate
            datasets: The SDTM datasets

        Returns:
            A list of validation results
        """
        results = []
        if annotation.domain != 'RELREC' or not annotation.condition:
            return results

        if annotation.domain not in datasets:
            return results  # Handled by DomainValidator

        dataset = datasets[annotation.domain]

        if 'IDVAR' not in dataset.variables:
            results.append(ValidationResult(
                annotation=annotation,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.MISSING_VARIABLE,
                message=f"Domain {annotation.domain} does not contain IDVAR variable."
            ))
            return results

        # Extract variables from condition, e.g., "FASPID = AESPID"
        condition_vars = re.findall(r'([A-Z0-9_]+)', annotation.condition)
        idvar_values = dataset.df['IDVAR'].unique()

        for var in condition_vars:
            if var not in idvar_values:
                results.append(ValidationResult(
                    annotation=annotation,
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.MISSING_VARIABLE,
                    message=f"Variable '{var}' from condition not found in IDVAR of {annotation.domain}."
                ))
        return results
