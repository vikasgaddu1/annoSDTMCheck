from abc import ABC, abstractmethod
from typing import List, Dict
from ..annotation_parser import AnnotationData
from ..sdtm_reader import SDTMDataset
from ..results import ValidationResult


class BaseValidator(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validate(self, annotation: AnnotationData, datasets: Dict[str, SDTMDataset]) -> List[ValidationResult]:
        """
        Validate an annotation.

        Args:
            annotation: The annotation to validate
            datasets: The SDTM datasets

        Returns:
            A list of validation results
        """
