from dataclasses import dataclass
from typing import Optional, List, Tuple
import re
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnnotationError(Exception):
    """Base exception for annotation parsing errors."""


class InvalidAnnotationFormat(AnnotationError):
    """Raised when annotation text doesn't match any known format."""


class InvalidDomainName(AnnotationError):
    """Raised when domain name is invalid."""


class InvalidVariableName(AnnotationError):
    """Raised when variable name is invalid."""


class AnnotationPattern(Enum):
    """Enum for different annotation patterns."""
    DOMAIN_VAR = 1  # DM.SUBJID
    DOMAIN_VAR_HYPHEN = 2  # DM-SUBJID
    DOMAIN_VAR_VALUE = 3  # DM SUBJID = "value"
    DOMAIN_VAR_PIPE = 4  # DM|SUBJID
    DOMAIN_EQUALS = 5  # DOMAIN=DM VARIABLE=SUBJID
    VARIABLE_VALUE = 6  # VARIABLE = 'value'
    VARIABLE_LIST = 7  # VAR1, VAR2, VAR3
    SUPP_DOMAIN = 8  # VARIABLE in SUPPDOMAIN when VALUE
    VARIABLE_WHEN = 9  # VARIABLE when VALUE
    SINGLE_VARIABLE = 10  # VARIABLE
    BRACKET_VALUE = 11  # [VALUE]
    VARIABLE_RANGE = 12  # VAR1-VAR4
    VARIABLE_WITH_CONDITION = 13  # VAR1/VAR2 when COND = VALUE
    VARIABLE_VALUE_CONDITION = 14  # VAR = 'value' when COND = VALUE
    COMMENT = 15  # Question or comment format
    VAR_LIST_GENERIC = 16,  # VAR1, VAR2, ...
    VAR_LIST_WHEN = 17,  # VAR1, VAR2 when ...
    VAR_LIST_VALUE = 18,  # VAR1, VAR2 = 'value'
    VARIABLE_VALUE_GENERIC = 19  # VAR = value (generic)
    DOMAIN_LABEL = 20  # SV = Subject Visit
    NOT_SUBMITTED_COMMENT = 21  # NOT SUBMITTED
    DOMAIN_WHEN_CONDITION = 22,  # RELREC when FASPID = AESPID
    VARIABLE_WITH_TESTCD_CONDITION = 23  # PFORRES when PFTESTCD = CYTABNRM
    VARIABLE_IN_DOMAIN_WHEN = 24  # RELID in RELREC when FASEQ = AEGRPID


@dataclass
class AnnotationData:
    """Class to store annotation data extracted from PDFs."""
    page_number: int
    annotation_text: str
    domain: Optional[str] = None
    variable_name: Optional[str] = None
    value: Optional[str] = None
    position: Optional[Tuple[float, float]] = None
    pattern_type: Optional[AnnotationPattern] = None
    condition: Optional[str] = None  # For when conditions
    is_comment: bool = False  # For question/comment format
    label: Optional[str] = None  # For domain labels

    def validate(self) -> bool:
        """
        Validate the annotation data.

        Returns:
            bool: True if valid, False otherwise
        """
        # Skip validation for comments
        if self.is_comment:
            return True

        if not self.domain:
            return False

        # If it is a domain label, no need to check variable
        if self.label and self.domain and not self.variable_name:
            return True

        if not self.variable_name and not self.label:
            return False

        # Validate domain name (2-6 uppercase letters or SUPP + 2 uppercase letters)
        if not re.match(r'^([A-Z]{2,6}|SUPP[A-Z]{2,})$', self.domain):
            raise InvalidDomainName(
                f"Invalid domain name: {self.domain}. Domain names must be uppercase.")

        # Validate variable name (uppercase letters, numbers, underscore)
        if not re.match(r'^[A-Z0-9_]+$', self.variable_name):
            raise InvalidVariableName(
                f"Invalid variable name: {self.variable_name}. Variable names must be uppercase.")

        return True


class AnnotationParser:
    """Parser for extracting SDTM annotations from PDF text."""

    def __init__(self, dm_variables: Optional[List[str]] = None, config: Optional[dict] = None):
        """
        Initialize the annotation parser.

        Args:
            dm_variables: List of DM domain variables
            config: Configuration dictionary containing annotation patterns
        """
        self.dm_variables = dm_variables if dm_variables is not None else []

        # Get patterns from configuration or use defaults
        if config and 'annotation_patterns' in config and 'patterns' in config['annotation_patterns']:
            self.patterns = {}
            self.pattern_configs = {}  # Store pattern configuration for group handling
            for pattern in config['annotation_patterns']['patterns']:
                # Try to match to enum, otherwise use pattern name as key
                try:
                    pattern_type = AnnotationPattern[pattern['name']]
                except KeyError:
                    # Pattern not in enum, use name as key
                    pattern_type = pattern['name']
                self.patterns[pattern_type] = pattern['regex']
                self.pattern_configs[pattern_type] = pattern
        else:
            # Fallback to default patterns if no configuration provided
            self.pattern_configs = {}  # Initialize even for default patterns
            self.patterns = {
                # More specific patterns first
                AnnotationPattern.DOMAIN_LABEL: r'^([A-Z]{2})\s*=\s*([^=]+)$',
                AnnotationPattern.VARIABLE_VALUE: r'^([A-Z0-9_]+)\s*=\s*\'([^\']+)\'$',
                AnnotationPattern.NOT_SUBMITTED_COMMENT: r'^NOT SUBMITTED$',
                AnnotationPattern.DOMAIN_WHEN_CONDITION: r'^(RELREC)\s+when\s+(.+)$',
                AnnotationPattern.VARIABLE_WITH_TESTCD_CONDITION: r'^([A-Z0-9_]+)\s+when\s+([A-Z0-9_]+)\s*=\s*([A-Z0-9_]+)$',
                AnnotationPattern.DOMAIN_EQUALS: r'^DOMAIN=([A-Z]{2})\s+VARIABLE=([A-Z0-9_]+)(?:\s+VALUE="([^"]*)")?$',
                AnnotationPattern.DOMAIN_VAR_VALUE: r'^([A-Z]{2})\s+([A-Z0-9_]+)\s*=\s*"([^"]*)"$',
                AnnotationPattern.SUPP_DOMAIN: r'^([A-Z0-9_]+)\s+in\s+(SUPP[A-Z]{2,})(?:\s+when\s+(.+))?$',
                AnnotationPattern.VAR_LIST_WHEN: r"^((?:[A-Z0-9_]+)(?:(?:/|,)\s*[A-Z0-9_]+)+)\s+when\s+(.+)$",
                AnnotationPattern.VARIABLE_VALUE_CONDITION: r"^([A-Z0-9_]+)\s*=\s*'?([^']+?)'?\s+when\s+(.+)$",
                AnnotationPattern.VARIABLE_WHEN: r"^([A-Z0-9_]+)\s+when\s+(.+)$",
                AnnotationPattern.VAR_LIST_VALUE: r"^((?:[A-Z0-9_]+)(?:(?:/|,)\s*[A-Z0-9_]+)+)\s*=\s*(['\"].*['\"])$",
                AnnotationPattern.VARIABLE_VALUE: r"^([A-Z0-9_]+)\s*=\s*'([^']+?)'?$",
                AnnotationPattern.VARIABLE_VALUE_GENERIC: r"^([A-Z0-9_]+)\s*=\s*(.+)$",
                AnnotationPattern.VAR_LIST_GENERIC: r"^((?:[A-Z0-9_]+)(?:(?:/|,)\s*[A-Z0-9_]+)+)$",
                AnnotationPattern.DOMAIN_VAR: r'^([A-Z]{2})\.([A-Z0-9_]+)$',
                AnnotationPattern.DOMAIN_VAR_HYPHEN: r'^([A-Z]{2})-([A-Z0-9_]+)$',
                AnnotationPattern.DOMAIN_VAR_PIPE: r'^([A-Z]{2})\|([A-Z0-9_]+)$',
                AnnotationPattern.SINGLE_VARIABLE: r"^([A-Z0-9_]+)$",
                AnnotationPattern.BRACKET_VALUE: r"^\[(NOT SUBMITTED|[^\]]+)\]$",
                AnnotationPattern.VARIABLE_RANGE: r"^([A-Z0-9_]+)-([A-Z0-9_]+)(?:\s+in\s+(SUPP[A-Z]{2,}))?$",
                AnnotationPattern.COMMENT: r"^(?:V\d+\.\d+|NOTE:.*|Custom domain instead of [A-Z]{2}\? [A-Z]{2}\?|Capture in [A-Z]{2}\?|.*\?)$"
            }

        # Compile patterns
        self.compiled_patterns = {
            pattern: re.compile(regex, re.IGNORECASE)
            for pattern, regex in self.patterns.items()
        }

    def parse_annotation(
        self,
        text: str,
        page_number: int,
        position: Optional[Tuple[float, float]] = None
    ) -> List[AnnotationData]:
        """
        Parse a single annotation text and return a list of AnnotationData objects.

        Args:
            text: The annotation text to parse
            page_number: The page number where the annotation was found
            position: Optional tuple of (x, y) coordinates

        Returns:
            List of AnnotationData objects. Empty if parsing fails.
        """
        text = text.strip()
        for pattern_type, pattern in self.compiled_patterns.items():
            match = pattern.search(text)
            if match:
                groups = match.groups()
                annotations = []
                base_annotation = {
                    'page_number': page_number,
                    'annotation_text': text,
                    'pattern_type': pattern_type,
                    'position': position
                }

                if pattern_type == AnnotationPattern.COMMENT or pattern_type == AnnotationPattern.NOT_SUBMITTED_COMMENT:
                    annotations.append(AnnotationData(
                        **base_annotation, is_comment=True))
                    return annotations

                if pattern_type == AnnotationPattern.DOMAIN_LABEL:
                    domain, label = groups
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, label=label, is_comment=False))
                    return annotations

                if pattern_type in [AnnotationPattern.DOMAIN_VAR, AnnotationPattern.DOMAIN_VAR_HYPHEN, AnnotationPattern.DOMAIN_VAR_PIPE]:
                    domain, variable_name = groups
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name))
                elif pattern_type == AnnotationPattern.DOMAIN_VAR_VALUE:
                    domain, variable_name, value = groups
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, value=value))
                elif pattern_type == AnnotationPattern.VARIABLE_WITH_TESTCD_CONDITION:
                    variable_name, test_cd_variable, test_cd_value = groups
                    domain = self._infer_domain_from_var(variable_name)
                    condition = f"{test_cd_variable} = {test_cd_value}"
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, condition=condition))
                elif pattern_type == AnnotationPattern.DOMAIN_EQUALS:
                    domain, variable_name = groups[:2]
                    value = groups[2] if len(
                        groups) > 2 and groups[2] else None
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, value=value))
                elif pattern_type == AnnotationPattern.DOMAIN_WHEN_CONDITION:
                    domain, condition = groups
                    # Split the condition into parts (e.g., "DSSEQ = AEGRPID")
                    condition_parts = [part.strip()
                                       for part in condition.split('=')]
                    if len(condition_parts) == 2:
                        # Create two separate records for the variables in the condition
                        var1, var2 = condition_parts[0], condition_parts[1]
                        annotations.append(AnnotationData(
                            **base_annotation, domain=domain, variable_name=var1, value=var2))
                        annotations.append(AnnotationData(
                            **base_annotation, domain=domain, variable_name=var2, value=var1))
                    else:
                        # If condition doesn't match expected format, create single record with condition
                        annotations.append(AnnotationData(
                            **base_annotation, domain=domain, condition=condition, variable_name="IDVAR"))
                elif pattern_type in [AnnotationPattern.VARIABLE_VALUE, AnnotationPattern.VARIABLE_VALUE_GENERIC, AnnotationPattern.VARIABLE_VALUE_CONDITION]:
                    variable_name, value = groups[0], groups[1]
                    domain = self._infer_domain_from_var(variable_name)
                    condition = groups[2] if pattern_type == AnnotationPattern.VARIABLE_VALUE_CONDITION else None
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, value=value, condition=condition))
                elif pattern_type in [AnnotationPattern.VAR_LIST_GENERIC, AnnotationPattern.VAR_LIST_VALUE, AnnotationPattern.VAR_LIST_WHEN]:
                    variables_str = groups[0]
                    variables = re.split(r'[,/]', variables_str)
                    value = groups[1] if pattern_type == AnnotationPattern.VAR_LIST_VALUE else None
                    condition = groups[1] if pattern_type == AnnotationPattern.VAR_LIST_WHEN else None
                    for var in variables:
                        var = var.strip()
                        if not var:
                            continue
                        domain = self._infer_domain_from_var(var)
                        annotations.append(AnnotationData(
                            **base_annotation, domain=domain, variable_name=var, value=value, condition=condition))
                elif pattern_type == AnnotationPattern.SUPP_DOMAIN:
                    variable_name, domain = groups[:2]
                    condition = groups[2] if len(
                        groups) > 2 and groups[2] else None
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, condition=condition))
                elif pattern_type == AnnotationPattern.VARIABLE_WHEN:
                    variable_name, condition = groups
                    domain = self._infer_domain_from_var(variable_name)
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, condition=condition))
                elif pattern_type == AnnotationPattern.SINGLE_VARIABLE:
                    variable_name = groups[0]
                    domain = self._infer_domain_from_var(variable_name)
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name))
                elif pattern_type == AnnotationPattern.VARIABLE_IN_DOMAIN_WHEN:
                    variable_name, domain, condition = groups
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name, condition=condition))
                elif pattern_type == AnnotationPattern.BRACKET_VALUE:
                    value = groups[0]
                    annotations.append(AnnotationData(
                        **base_annotation, value=value, is_comment=True))
                elif pattern_type == AnnotationPattern.VARIABLE_RANGE:
                    # This pattern might need more specific handling if it implies multiple variables
                    variable_name = groups[0]  # Use first variable
                    domain = groups[2] if len(
                        groups) > 2 and groups[2] else self._infer_domain_from_var(variable_name)
                    annotations.append(AnnotationData(
                        **base_annotation, domain=domain, variable_name=variable_name))
                # Handle string pattern types (from config that don't have enum values)
                elif isinstance(pattern_type, str):
                    if pattern_type == 'VARIABLE_IN_DOMAIN_WHEN':
                        variable_name, domain, condition = groups
                        annotations.append(AnnotationData(
                            **base_annotation, domain=domain, variable_name=variable_name, condition=condition))
                    else:
                        # Generic handling for other string patterns
                        # Try to infer structure from groups
                        if len(groups) >= 2:
                            # Assume first group is variable/domain, second is value/condition
                            domain = self._infer_domain_from_var(groups[0])
                            annotations.append(AnnotationData(
                                **base_annotation, domain=domain, variable_name=groups[0], 
                                value=groups[1] if len(groups) > 1 else None))
                        else:
                            # Single group - assume it's a variable
                            domain = self._infer_domain_from_var(groups[0])
                            annotations.append(AnnotationData(
                                **base_annotation, domain=domain, variable_name=groups[0]))

                # Validate all created annotations
                validated_annotations = []
                for ann in annotations:
                    try:
                        if ann.validate():
                            validated_annotations.append(ann)
                    except (InvalidDomainName, InvalidVariableName) as e:
                        logger.warning(
                            f"Invalid annotation created for text '{text}': {e}")
                return validated_annotations

        # Instead of returning an empty list, return an AnnotationData object with pattern_type=None
        logger.warning(f"No valid pattern found for: {text}")
        return [AnnotationData(
            page_number=page_number,
            annotation_text=text,
            pattern_type=None,
            position=position
        )]

    def _infer_domain_from_var(self, var_name: str) -> Optional[str]:
        """
        Infer domain name from variable name.

        Args:
            var_name: The variable name to infer domain from

        Returns:
            Inferred domain name or None if cannot be inferred
        """
        if not var_name or len(var_name) < 2:
            return None

        # Check if the variable is in DM variables list
        if var_name in self.dm_variables:
            return "DM"

        # For other domains, infer from the first two characters
        # Only if the variable doesn't exist in DM domain
        return var_name[:2].upper()  # e.g. "LB" from "LBORRES"

    def parse_annotations(
        self,
        annotations: List[Tuple[str, int, Optional[Tuple[float, float]]]]
    ) -> List[AnnotationData]:
        """
        Parse multiple annotations and return a list of AnnotationData objects.

        Args:
            annotations: List of tuples containing (text, page_number, position)

        Returns:
            List of AnnotationData objects

        Raises:
            AnnotationError: If any annotation fails to parse
        """
        results = []
        errors = []

        for text, page_number, position in annotations:
            try:
                parsed_list = self.parse_annotation(
                    text, page_number, position)
                if parsed_list:
                    results.extend(parsed_list)
            except InvalidAnnotationFormat as e:
                errors.append(f"Error on page {page_number}: {str(e)}")
                logger.warning(
                    f"Failed to parse annotation: {text} - {str(e)}")

        if errors:
            logger.error("Errors during annotation parsing:\n" +
                         "\n".join(errors))

        return results

    def get_supported_patterns(self) -> List[str]:
        """
        Get a list of supported annotation patterns.

        Returns:
            List of pattern descriptions
        """
        return [
            "DOMAIN.VARIABLE (e.g., DM.SUBJID)",
            "DOMAIN-VARIABLE (e.g., DM-SUBJID)",
            "DOMAIN VARIABLE = \"value\" (e.g., DM SUBJID = \"123\")",
            "DOMAIN|VARIABLE (e.g., DM|SUBJID)",
            "DOMAIN=DM VARIABLE=SUBJID [VALUE=\"value\"]",
            "VARIABLE = 'value' (e.g., SUBJID = '123')",
            "VAR1,VAR2,... = 'value' (e.g., FACAT,FAOBJ = 'value')",
            "VAR1/VAR2 (e.g., DSSTDTC/RFICDTC)",
            "VARIABLE in SUPPDOMAIN [when VALUE]",
            "VARIABLE when VALUE (e.g., VSORRES when VSTESTCD=HEIGHT)",
            "VAR1,VAR2,... when Cond (e.g. VSORRES,VSORRESU when VSTESTCD=HEIGHT)",
            "VARIABLE (single variable name)",
            "[VALUE] (bracketed value, treated as comment)",
            "NOTE: ... (comment)",
            "SV - Subject Visits (comment)"
        ]
