from typing import List, Dict
from .base_validator import BaseValidator
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..validation_engine import ValidationResult, ValidationSeverity, ValidationCategory


class DomainValidator(BaseValidator):
    """Validator for checking if the domain exists and its label matches."""

    def __init__(self, ignore_domains: List[str] = None):
        """
        Initialize the domain validator.

        Args:
            ignore_domains: List of domains to ignore during validation
        """
        self.ignore_domains = ignore_domains or []

    def validate(self, annotation: AnnotationData, datasets: Dict[str, SDTMDataset]) -> List[ValidationResult]:
        """
        Check if the domain in the annotation exists in the SDTM datasets.
        Also, if the annotation is a domain label, check if it matches the dataset's label.

        Args:
            annotation: The annotation to validate
            datasets: The SDTM datasets

        Returns:
            A list of validation results
        """
        results = []
        if not annotation.domain:
            return results

        # Skip validation for ignored domains
        if annotation.domain.upper() in self.ignore_domains:
            return results

        if annotation.domain.upper() not in datasets:
            results.append(ValidationResult(
                annotation=annotation,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.WRONG_DOMAIN,
                message=f"Domain '{annotation.domain}' not found in SDTM datasets."
            ))
            return results

        # If annotation is for a domain label, check if it matches the dataset label
        if annotation.label:
            dataset = datasets.get(annotation.domain.upper())
            if dataset and dataset.label:
                # Case-insensitive and whitespace-insensitive comparison
                if annotation.label.strip().lower() != dataset.label.strip().lower():
                    results.append(ValidationResult(
                        annotation=annotation,
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.METADATA_MISMATCH,
                        message=(
                            f"Mismatched dataset label for domain '{annotation.domain}'. "
                            f"Expected '{dataset.label}', but found '{annotation.label}' in annotation."
                        )
                    ))
            elif dataset and not dataset.label:
                results.append(ValidationResult(
                    annotation=annotation,
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.METADATA_MISMATCH,
                    message=f"Dataset label for domain '{annotation.domain}' not found in the dataset file."
                ))

        return results
