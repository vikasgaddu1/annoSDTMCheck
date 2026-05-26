from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any, Union
import re
import logging

logger = logging.getLogger(__name__)


class AnnotationError(Exception):
    """Base exception for annotation parsing errors."""


class InvalidDomainName(AnnotationError):
    """Raised when domain name is invalid."""


class InvalidVariableName(AnnotationError):
    """Raised when variable name is invalid."""


@dataclass
class AnnotationData:
    """Class to store annotation data extracted from PDFs."""
    page_number: int
    annotation_text: str
    domain: Optional[str] = None
    variable_name: Optional[str] = None
    value: Optional[str] = None
    position: Optional[Tuple[float, float]] = None
    pattern_type: Optional[Union[str, Any]] = None  # Can be string or enum
    condition: Optional[str] = None
    is_comment: bool = False
    label: Optional[str] = None
    # Dynamic fields that can be set from configuration
    test_cd_variable: Optional[str] = None
    test_cd_value: Optional[str] = None
    variable_name_end: Optional[str] = None
    variables: Optional[str] = None  # For comma/slash separated lists

    def validate(self) -> bool:
        """Validate the annotation data."""
        # Skip validation for comments
        if self.is_comment:
            return True

        # If it is a domain label, no need to check variable
        if self.label and self.domain and not self.variable_name:
            return True

        if not self.domain:
            return False

        if not self.variable_name and not self.label:
            return False

        # Validate domain name (2-6 uppercase letters or SUPP + 2 uppercase letters)
        if not re.match(r'^([A-Z]{2,6}|SUPP[A-Z]{2,})$', self.domain):
            raise InvalidDomainName(
                f"Invalid domain name: {self.domain}. Domain names must be uppercase.")

        # Validate variable name (uppercase letters, numbers, underscore)
        if self.variable_name and not re.match(r'^[A-Z0-9_]+$', self.variable_name):
            raise InvalidVariableName(
                f"Invalid variable name: {self.variable_name}. Variable names must be uppercase.")

        return True


class DynamicAnnotationParser:
    """Dynamic parser for extracting SDTM annotations from PDF text."""

    def __init__(self, dm_variables: Optional[List[str]] = None, config: Optional[dict] = None):
        """Initialize the dynamic annotation parser."""
        self.dm_variables = dm_variables if dm_variables is not None else []
        self.patterns = []
        
        # Load patterns from configuration
        if config and 'annotation_patterns' in config and 'patterns' in config['annotation_patterns']:
            for pattern_config in config['annotation_patterns']['patterns']:
                self.patterns.append({
                    'name': pattern_config['name'],
                    'description': pattern_config.get('description', ''),
                    'regex': re.compile(pattern_config['regex'], re.IGNORECASE),
                    'groups': pattern_config.get('groups', {}),
                    'is_comment': self._is_comment_pattern(pattern_config)
                })
        
        # Settings from config
        self.settings = {}
        if config and 'annotation_patterns' in config and 'settings' in config['annotation_patterns']:
            self.settings = config['annotation_patterns']['settings']

    def _is_comment_pattern(self, pattern_config: dict) -> bool:
        """Determine if a pattern represents a comment."""
        name = pattern_config.get('name', '').lower()
        desc = pattern_config.get('description', '').lower()
        
        # Check for comment indicators
        comment_indicators = ['comment', 'note', 'not submitted', 'bracket', 'question']
        return any(indicator in name or indicator in desc for indicator in comment_indicators)

    def parse_annotation(
        self,
        text: str,
        page_number: int,
        position: Optional[Tuple[float, float]] = None
    ) -> List[AnnotationData]:
        """Parse a single annotation text dynamically based on configuration."""
        text = text.strip()
        
        for pattern in self.patterns:
            match = pattern['regex'].match(text)
            if match:
                # Handle the match dynamically based on group configuration
                return self._handle_match(match, pattern, text, page_number, position)
        
        # No pattern matched
        logger.warning(f"No valid pattern found for: {text} (Parser has {len(self.patterns)} patterns)")
        return [AnnotationData(
            page_number=page_number,
            annotation_text=text,
            pattern_type=None,
            position=position
        )]

    def _handle_match(
        self, 
        match: re.Match, 
        pattern: dict, 
        text: str, 
        page_number: int, 
        position: Optional[Tuple[float, float]]
    ) -> List[AnnotationData]:
        """Handle a regex match dynamically based on pattern configuration."""
        annotations = []
        
        # Create base annotation
        base_annotation = AnnotationData(
            page_number=page_number,
            annotation_text=text,
            pattern_type=pattern['name'],
            position=position,
            is_comment=pattern['is_comment']
        )
        
        # Extract data based on group definitions
        groups = pattern['groups']
        for field_name, group_index in groups.items():
            if field_name == 'dummy':  # Skip dummy groups
                continue
                
            try:
                value = match.group(group_index)
                if value:
                    setattr(base_annotation, field_name, value)
            except (IndexError, AttributeError) as e:
                logger.warning(f"Error extracting group {group_index} for field {field_name}: {e}")
        
        # Handle special cases
        annotations = self._post_process_annotation(base_annotation, pattern)
        
        # Validate annotations
        validated = []
        for ann in annotations:
            try:
                if ann.validate():
                    validated.append(ann)
            except (InvalidDomainName, InvalidVariableName) as e:
                logger.warning(f"Invalid annotation: {e}")
        
        return validated

    def _post_process_annotation(
        self, 
        annotation: AnnotationData, 
        pattern: dict
    ) -> List[AnnotationData]:
        """Post-process annotation to handle special cases."""
        annotations = []
        
        # Handle variable lists (comma or slash separated)
        if hasattr(annotation, 'variables') and annotation.variables:
            # Split variables and create separate annotations
            var_list = re.split(r'[,/]', annotation.variables)
            for var in var_list:
                var = var.strip()
                if var:
                    new_ann = AnnotationData(
                        page_number=annotation.page_number,
                        annotation_text=annotation.annotation_text,
                        pattern_type=annotation.pattern_type,
                        position=annotation.position,
                        variable_name=var,
                        domain=annotation.domain or self._infer_domain_from_var(var),
                        value=annotation.value,
                        condition=annotation.condition,
                        is_comment=annotation.is_comment
                    )
                    annotations.append(new_ann)
        else:
            # Standard processing
            # Infer domain if not specified
            if annotation.variable_name and not annotation.domain:
                annotation.domain = self._infer_domain_from_var(annotation.variable_name)
            
            # Handle TESTCD conditions
            if annotation.test_cd_variable and annotation.test_cd_value:
                annotation.condition = f"{annotation.test_cd_variable} = {annotation.test_cd_value}"
            
            annotations.append(annotation)
        
        return annotations

    def _infer_domain_from_var(self, var_name: str) -> Optional[str]:
        """Infer domain name from variable name."""
        if not var_name or len(var_name) < 2:
            return None
        
        # Check if variable is in DM variables list
        if var_name in self.dm_variables:
            return "DM"
        
        # Infer from first two characters
        return var_name[:2].upper()

    def parse_annotations(
        self,
        annotations: List[Tuple[str, int, Optional[Tuple[float, float]]]]
    ) -> List[AnnotationData]:
        """Parse multiple annotations."""
        results = []
        errors = []
        
        for text, page_number, position in annotations:
            try:
                parsed_list = self.parse_annotation(text, page_number, position)
                if parsed_list:
                    results.extend(parsed_list)
            except Exception as e:
                errors.append(f"Error on page {page_number}: {str(e)}")
                logger.warning(f"Failed to parse annotation: {text} - {str(e)}")
        
        if errors:
            logger.error("Errors during annotation parsing:\n" + "\n".join(errors))
        
        return results

    def get_supported_patterns(self) -> List[str]:
        """Get list of supported patterns from configuration."""
        return [f"{p['name']}: {p['description']}" for p in self.patterns]


# For backward compatibility, create alias
AnnotationParser = DynamicAnnotationParser 