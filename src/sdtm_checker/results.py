from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .dynamic_annotation_parser import AnnotationData


class ValidationSeverity(Enum):
    """Severity levels for validation results."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationCategory(Enum):
    """Categories for validation results."""
    MISSING_VARIABLE = "Missing Variable"
    WRONG_DOMAIN = "Wrong Domain"
    TYPO_IN_VARIABLE = "Typo in Variable Name"
    FORMAT_MISMATCH = "Format Mismatch"
    MISSING_VALUE = "Missing Value in Column"
    INCORRECT_VALUE = "Incorrect Value"
    MISMATCHED_DOMAIN = "Mismatched Domain"
    METADATA_MISMATCH = "Metadata Mismatch"
    PATTERN_MATCH = "Pattern Match"


@dataclass
class ValidationResult:
    """Class to store validation results."""
    annotation: 'AnnotationData'
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    suggested_correction: Optional[str] = None
