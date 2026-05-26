"""
SDTM Annotation Checker

A tool for validating CRF annotations against SDTM datasets.
"""

from .annotation_extractor import AnnotationExtractor
from .dynamic_annotation_parser import DynamicAnnotationParser as AnnotationParser, AnnotationData
from .sdtm_reader import SDTMDatasetManager
from .validation_engine import ValidationEngine
from .results import ValidationResult, ValidationSeverity, ValidationCategory
from .report_generator import ReportGenerator
from .config_manager import ConfigurationManager, Configuration
from .pattern_manager import PatternManager, Pattern

__all__ = [
    "AnnotationExtractor",
    "AnnotationParser",
    "AnnotationData",
    "SDTMDatasetManager",
    "ValidationEngine",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationCategory",
    "ReportGenerator",
    "ConfigurationManager",
    "Configuration",
    "PatternManager",
    "Pattern",
]

__version__ = "0.2.0"
__author__ = "Your Name"
