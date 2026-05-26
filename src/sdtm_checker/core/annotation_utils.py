"""
Utility functions for cleaning and processing annotation content.
"""

import html
import re


def clean_annotation_content(text: str) -> str:
    """
    Clean annotation content by handling all forms of whitespace entities.
    
    This function handles:
    - HTML/XML numeric entities (&#xD;, &#xA;, &#13;, &#10;, etc.)
    - Literal carriage return and line feed characters (\r, \n)
    - Tabs and other whitespace characters
    - Zero-width and special Unicode spaces
    - Multiple consecutive spaces
    
    Args:
        text: The annotation content to clean
        
    Returns:
        Cleaned annotation content with normalized whitespace
    """
    if not text:
        return text
    
    # First unescape HTML/XML entities (handles &#xD;, &#xA;, etc.)
    text = html.unescape(text)
    
    # Replace various forms of whitespace
    # Handle both literal characters and any remaining entities
    text = text.replace('\r\n', ' ')  # Windows line ending
    text = text.replace('\r', ' ')    # Mac line ending
    text = text.replace('\n', ' ')    # Unix line ending
    text = text.replace('\t', ' ')    # Tab
    
    # Handle zero-width and special Unicode spaces
    text = re.sub(r'[\u200B\u200C\u200D\uFEFF]', '', text)  # Zero-width spaces
    text = re.sub(r'[\u2000-\u200A\u2028\u2029]', ' ', text)  # Various Unicode spaces
    
    # Normalize multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    
    # Final trim
    return text.strip()

