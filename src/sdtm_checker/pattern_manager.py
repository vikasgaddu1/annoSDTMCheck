"""
Pattern management system for SDTM Annotation Checker.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents an annotation pattern."""
    name: str
    description: str
    regex: str
    groups: Dict[str, int]
    compiled_regex: Optional[re.Pattern] = None

    def __post_init__(self):
        """Compile the regex pattern after initialization."""
        try:
            self.compiled_regex = re.compile(self.regex)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{self.regex}': {e}")
            raise ValueError(f"Invalid regex pattern: {e}")

    def match(self, text: str) -> Optional[Dict[str, str]]:
        """
        Match text against the pattern.

        Args:
            text: Text to match against the pattern

        Returns:
            Dictionary of group names and matched values, or None if no match
        """
        if not self.compiled_regex:
            return None

        match = self.compiled_regex.match(text)
        if not match:
            return None

        result = {}
        for group_name, group_index in self.groups.items():
            try:
                result[group_name] = match.group(group_index)
            except IndexError:
                logger.warning(
                    f"Group {group_name} (index {group_index}) not found in pattern match")
                result[group_name] = None

        return result


class PatternManager:
    """Manages annotation patterns, including validation, testing, and caching."""

    def __init__(self):
        """Initialize the pattern manager."""
        self.patterns: Dict[str, Pattern] = {}
        self._compiled_patterns: Dict[str, re.Pattern] = {}

    def add_pattern(self, pattern_data: Dict[str, Any]) -> None:
        """
        Add a new pattern to the manager.

        Args:
            pattern_data: Dictionary containing pattern information
                Required keys: name, description, regex, groups
        """
        try:
            pattern = Pattern(
                name=pattern_data["name"],
                description=pattern_data["description"],
                regex=pattern_data["regex"],
                groups=pattern_data["groups"]
            )

            if pattern.name in self.patterns:
                raise ValueError(
                    f"Pattern with name '{pattern.name}' already exists")

            self.patterns[pattern.name] = pattern
            logger.info(f"Added pattern: {pattern.name}")

        except KeyError as e:
            raise ValueError(f"Missing required field in pattern data: {e}")
        except Exception as e:
            logger.error(f"Error adding pattern: {e}")
            raise

    def remove_pattern(self, pattern_name: str) -> None:
        """
        Remove a pattern from the manager.

        Args:
            pattern_name: Name of the pattern to remove
        """
        if pattern_name not in self.patterns:
            raise ValueError(f"Pattern '{pattern_name}' not found")

        del self.patterns[pattern_name]
        logger.info(f"Removed pattern: {pattern_name}")

    def get_pattern(self, pattern_name: str) -> Optional[Pattern]:
        """
        Get a pattern by name.

        Args:
            pattern_name: Name of the pattern to retrieve

        Returns:
            Pattern object if found, None otherwise
        """
        return self.patterns.get(pattern_name)

    def get_all_patterns(self) -> List[Pattern]:
        """
        Get all registered patterns.

        Returns:
            List of all Pattern objects
        """
        return list(self.patterns.values())

    @lru_cache(maxsize=100)
    def test_pattern(self, pattern_name: str, test_text: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Test a pattern against sample text.

        Args:
            pattern_name: Name of the pattern to test
            test_text: Text to test against the pattern

        Returns:
            Tuple of (success, match_result)
            success: True if pattern exists and matches
            match_result: Dictionary of matched groups if successful, None otherwise
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False, None

        match_result = pattern.match(test_text)
        return match_result is not None, match_result

    def validate_pattern(self, pattern_data: Dict[str, Any]) -> List[str]:
        """
        Validate pattern data before adding.

        Args:
            pattern_data: Dictionary containing pattern information

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        # Check required fields
        required_fields = ["name", "description", "regex", "groups"]
        for field in required_fields:
            if field not in pattern_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        # Validate name
        if not pattern_data["name"].strip():
            errors.append("Pattern name cannot be empty")
        elif pattern_data["name"] in self.patterns:
            errors.append(
                f"Pattern name '{pattern_data['name']}' already exists")

        # Validate description
        if not pattern_data["description"].strip():
            errors.append("Pattern description cannot be empty")

        # Validate regex
        try:
            re.compile(pattern_data["regex"])
        except re.error as e:
            errors.append(f"Invalid regex pattern: {e}")

        # Validate groups
        if not isinstance(pattern_data["groups"], dict):
            errors.append("Groups must be a dictionary")
        else:
            for group_name, group_index in pattern_data["groups"].items():
                if not isinstance(group_index, int) or group_index < 1:
                    errors.append(
                        f"Invalid group index for '{group_name}': must be positive integer")

        return errors

    def clear_cache(self) -> None:
        """Clear the pattern testing cache."""
        self.test_pattern.cache_clear()
