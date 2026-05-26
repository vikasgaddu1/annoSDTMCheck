"""Text dimension calculator for PDF annotations.

This module provides functionality to calculate the required dimensions
for text content based on font properties, and to determine if text fits
within given annotation boundaries.
"""

import fitz  # PyMuPDF
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class TextDimensionCalculator:
    """Calculator for determining required text dimensions."""
    
    # Padding constants (in points)
    HORIZONTAL_PADDING = 4.0
    VERTICAL_PADDING = 2.0
    LINE_SPACING_FACTOR = 1.2  # Line height = fontsize * 1.2
    
    def __init__(self, horizontal_padding: float = HORIZONTAL_PADDING,
                 vertical_padding: float = VERTICAL_PADDING,
                 line_spacing_factor: float = LINE_SPACING_FACTOR):
        """
        Initialize the text dimension calculator.
        
        Args:
            horizontal_padding: Horizontal padding in points (left + right)
            vertical_padding: Vertical padding in points (top + bottom)
            line_spacing_factor: Multiplier for line height (fontsize × factor)
        """
        self.horizontal_padding = horizontal_padding
        self.vertical_padding = vertical_padding
        self.line_spacing_factor = line_spacing_factor
        
    def calculate_text_dimensions(
        self, 
        text: str, 
        fontname: str, 
        fontsize: float,
        max_width: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate required dimensions for text content.
        
        Args:
            text: Text content to measure
            fontname: Font name (e.g., 'helv', 'Times-Roman')
            fontsize: Font size in points
            max_width: Optional maximum width constraint
            
        Returns:
            Tuple of (required_width, required_height) in points
        """
        if not text or not text.strip():
            return (self.horizontal_padding * 2, fontsize + self.vertical_padding * 2)
        
        try:
            # Calculate text width using PyMuPDF
            text_width = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
            
            # Calculate line height
            line_height = fontsize * self.line_spacing_factor
            
            # If no max width constraint, return single-line dimensions
            if max_width is None:
                required_width = text_width + self.horizontal_padding * 2
                required_height = line_height + self.vertical_padding * 2
                return (required_width, required_height)
            
            # Calculate available width (excluding padding)
            available_width = max_width - (self.horizontal_padding * 2)
            
            if available_width <= 0:
                logger.warning(f"Max width {max_width} is too small for padding")
                available_width = max_width * 0.8  # Use 80% of max width
            
            # Determine number of lines needed
            if text_width <= available_width:
                # Fits in one line
                num_lines = 1
                required_width = text_width + self.horizontal_padding * 2
            else:
                # Need to wrap text - estimate based on character count
                # This is a rough estimation; actual wrapping depends on word boundaries
                num_lines = max(1, int((text_width / available_width) + 0.5))
                required_width = max_width
            
            # Calculate total height
            required_height = (num_lines * line_height) + self.vertical_padding * 2
            
            return (required_width, required_height)
            
        except Exception as e:
            logger.error(f"Error calculating text dimensions: {e}")
            # Return safe fallback dimensions
            fallback_width = len(text) * fontsize * 0.6 + self.horizontal_padding * 2
            fallback_height = fontsize * self.line_spacing_factor + self.vertical_padding * 2
            return (fallback_width, fallback_height)
    
    def check_if_text_fits(
        self,
        text: str,
        rect: fitz.Rect,
        fontname: str,
        fontsize: float
    ) -> bool:
        """
        Check if text fits within the given rectangle.
        
        Args:
            text: Text content to check
            rect: Rectangle boundary (fitz.Rect object)
            fontname: Font name
            fontsize: Font size in points
            
        Returns:
            True if text fits, False otherwise
        """
        if not text or not text.strip():
            return True
        
        try:
            # Get current dimensions
            current_width = rect.width
            current_height = rect.height
            
            # Calculate required dimensions with current width as max
            required_width, required_height = self.calculate_text_dimensions(
                text, fontname, fontsize, max_width=current_width
            )
            
            # Check if it fits
            fits_width = required_width <= current_width + 0.5  # Small tolerance
            fits_height = required_height <= current_height + 0.5
            
            if not fits_width or not fits_height:
                logger.debug(
                    f"Text doesn't fit: required ({required_width:.1f}×{required_height:.1f}) "
                    f"vs current ({current_width:.1f}×{current_height:.1f})"
                )
            
            return fits_width and fits_height
            
        except Exception as e:
            logger.error(f"Error checking if text fits: {e}")
            return True  # Assume it fits if we can't check
    
    def get_word_wrapped_lines(
        self,
        text: str,
        fontname: str,
        fontsize: float,
        max_width: float
    ) -> list[str]:
        """
        Split text into lines that fit within max_width.
        
        This performs actual word wrapping, respecting word boundaries.
        
        Args:
            text: Text to wrap
            fontname: Font name
            fontsize: Font size in points
            max_width: Maximum width per line (excluding padding)
            
        Returns:
            List of text lines
        """
        if not text or not text.strip():
            return []
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Try adding word to current line
            test_line = ' '.join(current_line + [word])
            test_width = fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                # Word doesn't fit, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, force it
                    lines.append(word)
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def calculate_optimal_dimensions(
        self,
        text: str,
        fontname: str,
        fontsize: float,
        current_width: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate optimal dimensions considering word wrapping.
        
        If current_width is provided, text will be wrapped at that width.
        Otherwise, returns single-line dimensions.
        
        Args:
            text: Text content
            fontname: Font name
            fontsize: Font size in points
            current_width: Optional current width to maintain
            
        Returns:
            Tuple of (width, height) in points
        """
        if not text or not text.strip():
            return (self.horizontal_padding * 2, fontsize + self.vertical_padding * 2)
        
        try:
            line_height = fontsize * self.line_spacing_factor
            
            if current_width is None:
                # No width constraint - single line
                text_width = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
                width = text_width + self.horizontal_padding * 2
                height = line_height + self.vertical_padding * 2
            else:
                # Wrap at current width
                available_width = current_width - (self.horizontal_padding * 2)
                lines = self.get_word_wrapped_lines(text, fontname, fontsize, available_width)
                
                # Calculate actual width needed (might be less than current_width)
                max_line_width = max(
                    fitz.get_text_length(line, fontname=fontname, fontsize=fontsize)
                    for line in lines
                )
                
                width = min(current_width, max_line_width + self.horizontal_padding * 2)
                height = len(lines) * line_height + self.vertical_padding * 2
            
            return (width, height)
            
        except Exception as e:
            logger.error(f"Error calculating optimal dimensions: {e}")
            # Fallback
            return self.calculate_text_dimensions(text, fontname, fontsize, current_width)


def get_font_from_annotation(annot: fitz.Annot) -> Tuple[str, float]:
    """
    Extract font name and size from annotation.
    
    Parses the DA (Default Appearance) string to get font properties.
    
    Args:
        annot: PyMuPDF annotation object
        
    Returns:
        Tuple of (fontname, fontsize), defaults to ('hebi', 10.0) if not found
        (hebi = Helvetica Bold-Italic, matching standardization settings)
    """
    try:
        # Try to get default appearance string
        da = annot.info.get('DA', '')
        
        if not da:
            # Try getting it from the annotation dictionary
            try:
                xref = annot.xref
                da = annot.parent.parent.xref_get_key(xref, 'DA')
                if da:
                    da = da[1]  # Get the value part
            except:
                pass
        
        if da:
            # Parse DA string (format: "/Font-Name font-size Tf")
            # Example: "/Helv 10 Tf 0 0 0 rg"
            import re
            font_match = re.search(r'/(\w+)\s+([\d.]+)\s+Tf', da)
            if font_match:
                fontname = font_match.group(1).lower()
                fontsize = float(font_match.group(2))
                return (fontname, fontsize)
        
        # Fallback: use standardized defaults (bold+italic)
        logger.debug("Could not extract font from annotation, using defaults (hebi)")
        return ('hebi', 10.0)
        
    except Exception as e:
        logger.warning(f"Error extracting font from annotation: {e}")
        return ('hebi', 10.0)

