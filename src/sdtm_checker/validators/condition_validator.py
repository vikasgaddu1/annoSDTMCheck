from typing import List, Dict, Optional
from .base_validator import BaseValidator
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..results import ValidationResult, ValidationSeverity, ValidationCategory


class ConditionValidator(BaseValidator):
    """
    Validator for checking specific conditions,
    e.g., if a certain variable has a specific value.
    """

    def _parse_condition(self, condition_str: str) -> Optional[Dict[str, str]]:
        """
        Parse a condition string into a dictionary.
        Example: "PFTESTCD = CYTABNRM" -> {"PFTESTCD": "CYTABNRM"}
        """
        if '=' not in condition_str:
            return None
        parts = [p.strip() for p in condition_str.split('=')]
        if len(parts) != 2:
            return None
        return {parts[0]: parts[1]}

    def validate(
        self, annotation: AnnotationData, datasets: Dict[str, SDTMDataset]
    ) -> List[ValidationResult]:
        results = []
        if (
            annotation.domain == "PF"
            and annotation.variable_name == "PFORRES"
            and annotation.condition
        ):
            parsed_condition = self._parse_condition(annotation.condition)
            if parsed_condition and "PFTESTCD" in parsed_condition:
                if parsed_condition["PFTESTCD"] == "CYTABNRM":
                    # Condition is met, no error
                    return results
                else:
                    results.append(
                        ValidationResult(
                            annotation=annotation,
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.INCORRECT_VALUE,
                            message=(
                                "Conditional check failed for PFORRES: "
                                f"PFTESTCD is not CYTABNRM, but {parsed_condition['PFTESTCD']}"
                            ),
                        )
                    )
        return results
