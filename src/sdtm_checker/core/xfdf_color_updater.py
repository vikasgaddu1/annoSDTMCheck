"""
XFDF Color Updater Module

This module handles exporting PDF annotations to XFDF format,
updating colors with standardized values, and importing back to PDF.

The XFDF import approach ensures that font colors are reliably
applied in Adobe Acrobat, which handles XFDF natively.
"""

import fitz  # PyMuPDF
import re
import logging
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Optional, List
import xml.etree.ElementTree as ET
import xml.dom.minidom

logger = logging.getLogger(__name__)

# Import standardization functions
try:
    from .annotation_standardizer import (
        StandardizationConfig,
        get_text_color_from_annotation,
        standardize_color,
        is_header_annotation
    )
    from .text_dimension_calculator import TextDimensionCalculator
    from .annotation_utils import clean_annotation_content
    from .annotation_aligner import AnnotationAligner
except ImportError:
    logger.warning("Could not import from annotation_standardizer, text_dimension_calculator, or annotation_aligner")
    StandardizationConfig = None
    TextDimensionCalculator = None
    AnnotationAligner = None


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """
    Convert RGB values (0-1 scale) to hex color string.
    
    Args:
        r, g, b: RGB values in 0-1 scale (PyMuPDF format)
        
    Returns:
        Hex color string like "#0000FF"
    """
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """
    Convert hex color string to RGB tuple (0-1 scale).
    
    Args:
        hex_color: Hex color string like "#0000FF" or "0000FF"
        
    Returns:
        Tuple of (r, g, b) in 0-1 scale
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def standardize_color(color: Tuple[float, float, float], color_config=None) -> Tuple[float, float, float]:
    """
    Map various shades to standard colors (Blue, Red, Green).
    
    This is the same logic used in annotation_standardizer.py.
    
    Args:
        color: Tuple of (r, g, b) in 0-1 scale (PyMuPDF format)
        color_config: Optional dict with 'standard_red_color', 'standard_blue_color', 
                     'standard_green_color' as lists [r, g, b] in 0-255 scale.
                     If None, uses default values for backward compatibility.
        
    Returns:
        Standardized color tuple in 0-1 scale
    """
    if not color or len(color) != 3:
        return (0, 0, 0)  # Default to black
    
    # Get standard colors from config or use defaults
    if color_config:
        # Convert from 0-255 scale to 0-1 scale
        std_red = tuple(c / 255.0 for c in color_config.get("standard_red_color", [255, 0, 0]))
        std_blue = tuple(c / 255.0 for c in color_config.get("standard_blue_color", [0, 0, 255]))
        std_green = tuple(c / 255.0 for c in color_config.get("standard_green_color", [0, 124, 0]))
    else:
        # Default values for backward compatibility
        std_red = (1, 0, 0)  # RGB(255, 0, 0)
        std_blue = (0, 0, 1)  # RGB(0, 0, 255)
        std_green = (0, 124/255, 0)  # RGB(0, 124, 0)
    
    r, g, b = color
    
    # Find the dominant channel(s)
    # Normalize by max intensity to handle different brightness levels
    max_intensity = max(r, g, b)
    if max_intensity == 0:
        return color  # Keep original if all channels are zero
    
    r_norm = r / max_intensity if max_intensity > 0 else 0
    g_norm = g / max_intensity if max_intensity > 0 else 0
    b_norm = b / max_intensity if max_intensity > 0 else 0
    
    # Blue detection: blue is dominant, red and green are much lower
    if b_norm > 0.9 and r_norm < 0.3 and g_norm < 0.3:
        return std_blue
    
    # Red detection: red is dominant, green and blue are much lower
    elif r_norm > 0.9 and g_norm < 0.3 and b_norm < 0.3:
        return std_red
    
    # Green detection: green is dominant, red and blue are much lower
    elif g_norm > 0.9 and r_norm < 0.3 and b_norm < 0.3:
        return std_green
    
    # Cyan detection: blue and green high, red low
    elif b_norm > 0.8 and g_norm > 0.8 and r_norm < 0.2:
        return (0, 1, 1)  # Cyan RGB(0, 255, 255)
    
    # Magenta detection: red and blue high, green low
    elif r_norm > 0.8 and b_norm > 0.8 and g_norm < 0.2:
        return (1, 0, 1)  # Magenta RGB(255, 0, 255)
    
    # If no clear match, check absolute thresholds as fallback
    
    # Blue fallback: blue is strong, others are weak
    if b > 0.8 and r < 0.2 and g < 0.3:
        return std_blue
    
    # Red fallback: red is strong, others are weak
    elif r > 0.8 and g < 0.2 and b < 0.2:
        return std_red
    
    # Green fallback: green is strong, others are weak
    elif g > 0.8 and r < 0.2 and b < 0.2:
        return std_green
    
    # Default: keep original color if it doesn't match any category
    logger.debug(f"Color {color} (RGB {int(r*255)},{int(g*255)},{int(b*255)}) doesn't match standard colors, keeping original")
    return color


def normalize_annotation_quotes(content: str, enable_quote_normalization: bool = True) -> str:
    """
    Normalize quotes around annotation values and spacing around '=' signs.
    
    Rules:
    - Normalize spacing around '=' (add spaces if missing: VAR=value → VAR = value)
    - Skip normalization for header annotations (e.g., "DM = Demographics")
    - Skip normalization for RELREC annotations (e.g., "RELREC when FASPID = AESPID")
    - For other annotations, wrap values in double quotes:
      - VAR = value → VAR = "value"
      - VAR = 'value' → VAR = "value"
      - VAR = 'value or VAR = value' → VAR = "value" (handle missing quotes)
      - VAR = "value" → keep as is
      - VAR = NULL → VAR = NULL (NULL remains unquoted)
    
    Args:
        content: Annotation content string
        enable_quote_normalization: If False, return content unchanged
        
    Returns:
        Normalized annotation content
    """
    if not enable_quote_normalization or not content:
        return content
    
    content = content.strip()
    
    # Check if it's a header annotation (e.g., "DM = Demographics")
    if is_header_annotation(content):
        # Still normalize spacing around '=' for headers
        content = re.sub(r'([A-Z0-9_]+)=([^=])', r'\1 = \2', content)
        return content
    
    # Check if it's a RELREC annotation (pattern: "RELREC when ...")
    relrec_pattern = re.compile(r'^RELREC\s+when\s+', re.IGNORECASE)
    if relrec_pattern.match(content):
        # Still normalize spacing around '=' for RELREC
        content = re.sub(r'([A-Z0-9_]+)=([^=])', r'\1 = \2', content)
        return content
    
    # Normalize spacing around '=' signs first
    # Pattern: match VAR=value (no spaces) and add spaces
    content = re.sub(r'([A-Z0-9_]+)=([^=\s])', r'\1 = \2', content)
    
    # Pattern to match assignments: VAR = value
    # We need to handle various cases:
    # 1. VAR = value (no quotes)
    # 2. VAR = 'value' (single quotes)
    # 3. VAR = "value" (double quotes - keep as is)
    # 4. VAR = 'value (missing closing quote)
    # 5. VAR = value' (missing opening quote)
    # 6. Complex: VAR when COND = VALUE (normalize VALUE)
    # 7. VAR = NULL (should remain unquoted)
    
    def normalize_value_quotes(match):
        """Normalize quotes for a single assignment."""
        var_part = match.group(1)  # Variable name before '='
        value_part = match.group(2)  # Value after '='
        
        # Strip whitespace from value
        value_part = value_part.strip()
        
        # If already properly double-quoted, keep as is
        if value_part.startswith('"') and value_part.endswith('"'):
            return f'{var_part} = {value_part}'
        
        # Remove any existing quotes (single or double, complete or incomplete)
        # Handle cases like: 'value, "value, value', value"
        cleaned_value = value_part
        if cleaned_value.startswith("'") or cleaned_value.startswith('"'):
            cleaned_value = cleaned_value[1:]
        if cleaned_value.endswith("'") or cleaned_value.endswith('"'):
            cleaned_value = cleaned_value[:-1]
        
        # Strip whitespace again after removing quotes
        cleaned_value = cleaned_value.strip()
        
        # Check if value is NULL (case-insensitive) - don't quote NULL
        if cleaned_value.upper() == 'NULL':
            return f'{var_part} = NULL'
        
        # Wrap in double quotes
        return f'{var_part} = "{cleaned_value}"'
    
    # Pattern to match assignments: VAR = VALUE
    # Handle quoted values properly: if value starts with quote, capture until matching quote
    # For unquoted values, stop at keywords (when/and/or) or next variable assignment
    # We'll process in two passes: first quoted values, then unquoted
    
    # First pass: Handle quoted values (single or double quotes)
    # Pattern matches: VAR = 'value' or VAR = "value"
    # The pattern captures from opening quote to closing quote (or end if missing)
    # Use lookahead to ensure we stop correctly at whitespace/keywords after closing quote
    # Pattern: match opening quote, content (non-greedy), optional closing quote, then lookahead for stop condition
    # Handle both cases: 'value' (with closing quote) and 'value (missing closing quote)
    quoted_pattern = r'([A-Z0-9_]+)\s*=\s*((?:["\'])[^"\']*?(?:["\'])?)(?=\s+(?:when|and|or|[A-Z0-9_]+\s*=)|$)'
    
    def process_quoted_match(m):
        var_part = m.group(1)
        quoted_value = m.group(2).strip()
        
        # Extract the actual value by removing quotes
        cleaned = quoted_value
        if cleaned.startswith("'") or cleaned.startswith('"'):
            cleaned = cleaned[1:]
        if cleaned.endswith("'") or cleaned.endswith('"'):
            cleaned = cleaned[:-1]
        cleaned = cleaned.strip()
        
        # Check for NULL (case-insensitive) - don't quote NULL
        if cleaned.upper() == 'NULL':
            return f'{var_part} = NULL'
        
        return f'{var_part} = "{cleaned}"'
    
    # Process quoted values first (this handles 'BLAST' correctly)
    content = re.sub(quoted_pattern, process_quoted_match, content, flags=re.IGNORECASE)
    
    # Second pass: Handle unquoted values
    # Pattern: VAR = VALUE where VALUE stops at keywords or next assignment
    # We need to avoid matching values that are already processed (those with quotes)
    # So we match unquoted values that don't start with quotes
    unquoted_pattern = r'([A-Z0-9_]+)\s*=\s*([^\s"\'=]+(?:\s+[^\s"\'=]+)*?)(?=\s+(?:when|and|or|[A-Z0-9_]+\s*=)|$)'
    
    def process_unquoted_match(m):
        var_part = m.group(1)
        value_part = m.group(2).strip()
        
        # Skip if this looks like it was already processed (has quotes)
        if '"' in value_part or "'" in value_part:
            return m.group(0)  # Return unchanged
        
        # Check for NULL (case-insensitive) - don't quote NULL
        if value_part.upper() == 'NULL':
            return f'{var_part} = NULL'
        
        return f'{var_part} = "{value_part}"'
    
    # Process unquoted values
    content = re.sub(unquoted_pattern, process_unquoted_match, content, flags=re.IGNORECASE)
    
    return content


def export_to_xfdf(doc: fitz.Document, xfdf_path: str, config=None, output_pdf_name: str = None, 
                   auto_resize: bool = True, align_annotations: bool = True,
                   horizontal_tolerance: float = 1.0, vertical_tolerance: float = 10.0,
                   resize_skip_pages: Optional[List[int]] = None,
                   align_skip_pages: Optional[List[int]] = None,
                   normalize_quotes: bool = True) -> int:
    """
    Export PDF annotations to XFDF format with optional auto-resizing and alignment.
    
    Args:
        doc: PyMuPDF Document object
        xfdf_path: Path where XFDF file will be saved
        config: Optional configuration object (values from config take precedence over function parameters)
        output_pdf_name: Optional output PDF filename to reference in XFDF
        auto_resize: If True, auto-adjust annotation width to fit text (overridden by config if provided)
        align_annotations: If True, align annotations within tolerance (overridden by config if provided)
        horizontal_tolerance: Y-axis tolerance for horizontal alignment (in points) (overridden by config if provided)
        vertical_tolerance: X-axis tolerance for vertical alignment (in points) (overridden by config if provided)
        
    Returns:
        Number of annotations exported
    """
    logger.info(f"Exporting annotations to XFDF: {xfdf_path}")
    
    # Override function parameters with config values if config is provided
    if config:
        auto_resize = getattr(config, 'auto_resize_textboxes', auto_resize)
        align_annotations = getattr(config, 'align_annotations', align_annotations)
        horizontal_tolerance = getattr(config, 'horizontal_tolerance', horizontal_tolerance)
        vertical_tolerance = getattr(config, 'vertical_tolerance', vertical_tolerance)
        resize_skip_pages = getattr(config, 'resize_skip_pages', resize_skip_pages)
        align_skip_pages = getattr(config, 'align_skip_pages', align_skip_pages)
        normalize_quotes = getattr(config, 'normalize_quotes', normalize_quotes)
    
    # Get author from config, default to "Geron"
    author_name = "Geron"
    if config:
        author_name = getattr(config, 'default_author', 'Geron')
        if not author_name or author_name.strip() == "":
            author_name = "Geron"
    
    logger.info(f"Using author name: {author_name}")
    
    # Initialize text dimension calculator for auto-resizing
    calculator = None
    if auto_resize and TextDimensionCalculator:
        calculator = TextDimensionCalculator()
        logger.info("Auto-resize enabled for annotation widths")
    
    # Log alignment settings
    if align_annotations:
        logger.info(f"Auto-align enabled: horizontal_tol={horizontal_tolerance}pt, vertical_tol={vertical_tolerance}pt")
    
    try:
        # Step 1: Collect all annotations and calculate alignment if enabled
        aligned_rects = {}  # Map: (page_num, annot_index) -> aligned_rect
        
        if align_annotations:
            logger.info("Step 1: Calculating alignment for annotations...")
            
            for page_num in range(len(doc)):
                # Skip alignment if this page is in the skip list
                skip_this_page = (
                    align_skip_pages is not None 
                    and page_num in align_skip_pages
                )
                if skip_this_page:
                    continue
                
                page = doc[page_num]
                annots = list(page.annots() or [])
                
                # Filter to FreeText only
                freetext_annots = [(i, a) for i, a in enumerate(annots) if a.type[0] == fitz.PDF_ANNOT_FREE_TEXT]
                
                if len(freetext_annots) < 2:
                    continue
                
                # Group by horizontal proximity (for horizontal alignment)
                from collections import defaultdict
                y_groups = defaultdict(list)
                
                for idx, annot in freetext_annots:
                    y0 = annot.rect.y0
                    # Find existing group within tolerance
                    found_group = False
                    for group_y in list(y_groups.keys()):
                        if abs(y0 - group_y) <= horizontal_tolerance:
                            y_groups[group_y].append((idx, annot))
                            found_group = True
                            break
                    if not found_group:
                        y_groups[y0].append((idx, annot))
                
                # Align each group horizontally
                for group_y, group in y_groups.items():
                    if len(group) >= 2:
                        # Calculate average Y position
                        avg_y0 = sum(a.rect.y0 for _, a in group) / len(group)
                        
                        for idx, annot in group:
                            if abs(annot.rect.y0 - avg_y0) > 0.5:
                                # Create aligned rectangle (preserve width and height)
                                aligned_rect = fitz.Rect(
                                    annot.rect.x0,
                                    avg_y0,
                                    annot.rect.x1,
                                    avg_y0 + annot.rect.height
                                )
                                aligned_rects[(page_num, idx)] = aligned_rect
                                logger.debug(f"Page {page_num}, Annot {idx}: Aligned Y from {annot.rect.y0:.1f} to {avg_y0:.1f}")
                
                # Group by vertical proximity (for vertical alignment)
                x_groups = defaultdict(list)
                
                for idx, annot in freetext_annots:
                    x0 = annot.rect.x0
                    # Find existing group within tolerance
                    found_group = False
                    for group_x in list(x_groups.keys()):
                        if abs(x0 - group_x) <= vertical_tolerance:
                            x_groups[group_x].append((idx, annot))
                            found_group = True
                            break
                    if not found_group:
                        x_groups[x0].append((idx, annot))
                
                # Align each group vertically
                for group_x, group in x_groups.items():
                    if len(group) >= 2:
                        # Calculate average X position
                        avg_x0 = sum(a.rect.x0 for _, a in group) / len(group)
                        
                        for idx, annot in group:
                            if abs(annot.rect.x0 - avg_x0) > 0.5:
                                # Get current rect (might already be aligned horizontally)
                                current_rect = aligned_rects.get((page_num, idx), annot.rect)
                                
                                # Create aligned rectangle (preserve width and height)
                                aligned_rect = fitz.Rect(
                                    avg_x0,
                                    current_rect.y0,
                                    avg_x0 + current_rect.width,
                                    current_rect.y1
                                )
                                aligned_rects[(page_num, idx)] = aligned_rect
                                logger.debug(f"Page {page_num}, Annot {idx}: Aligned X from {annot.rect.x0:.1f} to {avg_x0:.1f}")
        
        # Step 2: Export to XFDF with aligned coordinates
        logger.info("Step 2: Exporting annotations to XFDF with standardized properties...")
        
        # Start XFDF structure
        xfdf_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xfdf_lines.append('<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">')
        
        # Use provided output PDF name, or fall back to document name
        if output_pdf_name:
            pdf_name = output_pdf_name
        else:
            pdf_name = "document.pdf" if doc.name is None or doc.name == "" else Path(doc.name).name
        
        xfdf_lines.append(f'  <f href="{pdf_name}"/>')
        xfdf_lines.append('  <annots>')
        
        annot_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            annots = list(page.annots() or [])
            
            for annot_idx, annot in enumerate(annots):
                try:
                    annot_type = annot.type[0]
                    
                    # Only process FreeText annotations for now
                    if annot_type != fitz.PDF_ANNOT_FREE_TEXT:
                        continue
                    
                    info = annot.info
                    
                    # Use aligned rect if available, otherwise use original
                    rect = aligned_rects.get((page_num, annot_idx), annot.rect)
                    
                    # Clean annotation content
                    content = info.get('content', '')
                    content = clean_annotation_content(content)
                    # Use author from config instead of annotation's existing author
                    author = author_name
                    
                    if not content:
                        continue
                    
                    # Normalize quotes around values (before resizing/alignment)
                    content = normalize_annotation_quotes(content, normalize_quotes)
                    
                    # Get annotation colors
                    colors = annot.colors
                    bg_color = colors.get('fill') if colors else None
                    
                    # Get text color from DA string and appearance stream
                    da = info.get('DA', '')
                    text_color = (0, 0, 0)  # Default black
                    font_size = 10
                    
                    if da:
                        # Extract text color from DA
                        color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
                        if color_match:
                            text_color = (
                                float(color_match.group(1)),
                                float(color_match.group(2)),
                                float(color_match.group(3))
                            )
                        
                        # Extract font size
                        size_match = re.search(r'(\d+(?:\.\d+)?)\s+Tf', da)
                        if size_match:
                            font_size = float(size_match.group(1))
                    
                    # Try to extract actual color from appearance stream if DA shows black
                    if text_color == (0, 0, 0):
                        try:
                            xref = annot.xref
                            if xref > 0:
                                annot_dict = doc.xref_object(xref)
                                ap_match = re.search(r'/N\s+(\d+)\s+\d+\s+R', annot_dict)
                                if ap_match:
                                    ap_xref = int(ap_match.group(1))
                                    
                                    # Helper function to extract colors from stream and follow Form XObjects
                                    def extract_colors_from_stream(doc, xref, depth=0, max_depth=5):
                                        """Recursively extract colors from appearance stream, following Form XObjects"""
                                        if depth > max_depth:
                                            return []
                                        
                                        colors = []
                                        try:
                                            stream = doc.xref_stream(xref)
                                            if stream:
                                                text = stream.decode('latin-1', errors='ignore')
                                                
                                                # Extract direct color commands
                                                rg_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', text)
                                                for r_str, g_str, b_str in rg_matches:
                                                    colors.append((float(r_str), float(g_str), float(b_str)))
                                                
                                                # Check for Form XObject references (e.g., /MWFOForm Do or /Form Do)
                                                form_refs = re.findall(r'/(\w+)\s+Do', text)
                                                if form_refs and not colors:  # Only follow if no colors found yet
                                                    # Get the object to find XObject resources
                                                    obj = doc.xref_object(xref)
                                                    
                                                    # Look for XObject references in resources
                                                    xobj_matches = re.findall(r'/(\w+)\s+(\d+)\s+\d+\s+R', obj)
                                                    for form_name, form_xref in xobj_matches:
                                                        if form_name in form_refs or form_name == 'Form':
                                                            # Recursively check this Form XObject
                                                            nested_colors = extract_colors_from_stream(doc, int(form_xref), depth + 1, max_depth)
                                                            colors.extend(nested_colors)
                                        except:
                                            pass
                                        
                                        return colors
                                    
                                    # Extract colors from appearance stream (including nested forms)
                                    all_colors = extract_colors_from_stream(doc, ap_xref)
                                    
                                    # Find the first acceptable text color
                                    for r, g, b in all_colors:
                                        # Filter out background/border colors
                                        if (r, g, b) not in [(0, 1, 1), (1, 1, 1), (0, 0, 0), (0.75, 1, 1), (0.85, 1, 1)]:
                                            text_color = (r, g, b)
                                            logger.info(f"Annotation {annot_count+1}: Extracted color from appearance stream: RGB({int(r*255)},{int(g*255)},{int(b*255)})")
                                            break
                        except Exception as e:
                            logger.debug(f"Error extracting color from appearance: {e}")
                    
                    # Standardize the text color
                    color_config = None
                    if config and hasattr(config, 'color_config'):
                        color_config = config.color_config
                    standardized_text_color = standardize_color(text_color, color_config)
                    if text_color != standardized_text_color:
                        logger.info(f"Annotation {annot_count+1}: Standardized RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)}) -> RGB({int(standardized_text_color[0]*255)},{int(standardized_text_color[1]*255)},{int(standardized_text_color[2]*255)})")
                    
                    # Standardize font size based on header pattern
                    # Headers like "AE = Adverse Events" should be 12pt, others 10pt
                    if is_header_annotation(content):
                        font_size = 12
                        logger.debug(f"Annotation {annot_count+1}: Detected as header, setting font size to 12pt")
                    else:
                        font_size = 10
                    
                    # Get background color from config (default to cyan)
                    if config and hasattr(config, 'background_color'):
                        bg_color_tuple = config.background_color
                    else:
                        bg_color_tuple = (0, 1, 1)  # Default cyan RGB(0, 255, 255) in 0-1 scale
                    bg_hex = rgb_to_hex(*bg_color_tuple)
                    
                    # Get border color from config (default to black)
                    if config and hasattr(config, 'rectangle_border_color'):
                        border_color_tuple = config.rectangle_border_color
                    else:
                        border_color_tuple = (0, 0, 0)  # Default black RGB(0, 0, 0) in 0-1 scale
                    border_hex = rgb_to_hex(*border_color_tuple)
                    border_rgb_str = f"{border_color_tuple[0]} {border_color_tuple[1]} {border_color_tuple[2]}"
                    
                    # Create freetext element with correct template format - all on proper lines
                    text_hex = rgb_to_hex(*standardized_text_color)
                    
                    # Use proper XML escaping for content
                    import html
                    escaped_content = html.escape(content)
                    
                    # Auto-resize: Calculate optimal width for the text
                    # Skip resizing if this page is in the skip list
                    skip_this_page = (
                        resize_skip_pages is not None 
                        and page_num in resize_skip_pages
                    )
                    if calculator and not skip_this_page:
                        try:
                            # Calculate required width for single-line text
                            fontname = "hebi"  # Arial Bold Italic
                            required_width, required_height = calculator.calculate_optimal_dimensions(
                                content, fontname, font_size, current_width=None
                            )
                            
                            # Only expand width if needed (keep height same)
                            new_width = max(rect.width, required_width)
                            
                            # Add small padding (5 points)
                            new_width += 5
                            
                            # Update rect with new width (preserve x0, y0, y1)
                            new_rect = fitz.Rect(rect.x0, rect.y0, rect.x0 + new_width, rect.y1)
                            
                            if abs(new_width - rect.width) > 1:
                                logger.debug(f"Annotation {annot_count+1}: Resized width from {rect.width:.1f} to {new_width:.1f}")
                                rect = new_rect
                        except Exception as e:
                            logger.debug(f"Could not calculate optimal width: {e}")
                    
                    # XFDF expects coordinates as: left,bottom,right,top
                    # PyMuPDF rect has: x0,y0,x1,y1 where (x0,y0) is top-left and (x1,y1) is bottom-right
                    # We need to flip Y coordinates for XFDF
                    page_height = page.rect.height
                    xfdf_rect = f"{rect.x0},{page_height - rect.y1},{rect.x1},{page_height - rect.y0}"
                    
                    # Use the exact format from user's working annotation
                    # Add flags="print" and subject attributes
                    xfdf_lines.append(f'    <freetext color="{bg_hex}" flags="print" page="{page_num}" rect="{xfdf_rect}" subject="VOID" title="{author}">')
                    
                    # Add contents-richtext as SINGLE LINE to avoid whitespace being rendered as spaces
                    # PDF viewers treat literal whitespace in rich text blocks as actual space
                    xfdf_lines.append(f'      <contents-richtext><body xmlns="http://www.w3.org/1999/xhtml" xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:APIVersion="Acrobat:21.7.0" xfa:spec="2.0.2" style="font-size:{font_size}pt;text-align:left;color:{text_hex};font-weight:bold;font-style:italic;font-family:Arial;font-stretch:normal"><p dir="ltr">{escaped_content}</p></body></contents-richtext>')
                    
                    # defaultappearance: Use config-based border color
                    xfdf_lines.append(f'      <defaultappearance>{border_rgb_str} rg /Arial,BoldItalic {int(font_size)} Tf</defaultappearance>')
                    
                    # defaultstyle: Use config-based border color
                    xfdf_lines.append(f'      <defaultstyle>font: italic bold Arial,sans-serif {font_size}pt; text-align:left; color:{border_hex} </defaultstyle>')
                    
                    xfdf_lines.append('    </freetext>')
                    
                    annot_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error exporting annotation on page {page_num + 1}: {e}")
                    continue
        
        xfdf_lines.append('  </annots>')
        xfdf_lines.append('</xfdf>')
        
        # Write XFDF file
        with open(xfdf_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xfdf_lines))
        
        logger.info(f"Exported {annot_count} annotations to XFDF")
        return annot_count
        
    except Exception as e:
        logger.error(f"Error exporting to XFDF: {e}")
        raise


def update_xfdf_colors(xfdf_path: str, output_path: str) -> Dict[str, int]:
    """
    Update colors in XFDF file using standardize_color() logic.
    
    Args:
        xfdf_path: Path to input XFDF file
        output_path: Path where modified XFDF will be saved
        
    Returns:
        Dictionary with statistics about color updates
    """
    logger.info(f"Updating colors in XFDF: {xfdf_path}")
    
    stats = {
        'annotations_processed': 0,
        'colors_standardized': 0,
        'colors_unchanged': 0
    }
    
    try:
        # Read XFDF content
        with open(xfdf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match contents-richtext blocks with color
        richtext_pattern = (
            r'(<body[^>]*?style="[^"]*?color:)([^;]+)(;[^"]*"[^>]*?>\s*<p[^>]*?>)'
            r'([^<]+)'
            r'(</p>\s*</body>)'
        )
        
        def replace_color(match):
            """Replace color in rich text with standardized color."""
            prefix = match.group(1)  # Up to "color:"
            old_color_str = match.group(2)  # The color value
            middle = match.group(3)  # Rest of style and opening tags
            text = match.group(4)  # The text content
            suffix = match.group(5)  # Closing tags
            
            stats['annotations_processed'] += 1
            
            try:
                # Parse the color (could be hex or rgb)
                if old_color_str.startswith('#'):
                    # Hex format
                    old_color = hex_to_rgb(old_color_str)
                else:
                    # Might be rgb() format or other - try to extract
                    rgb_match = re.search(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', old_color_str)
                    if rgb_match:
                        old_color = (
                            int(rgb_match.group(1)) / 255.0,
                            int(rgb_match.group(2)) / 255.0,
                            int(rgb_match.group(3)) / 255.0
                        )
                    else:
                        # Can't parse, keep original
                        logger.debug(f"Could not parse color: {old_color_str}")
                        stats['colors_unchanged'] += 1
                        return match.group(0)
                
                # Standardize the color
                # Note: This function is called from update_xfdf_colors which doesn't have config
                # So we use None for backward compatibility
                new_color = standardize_color(old_color, None)
                
                # Check if color changed
                if new_color != old_color:
                    stats['colors_standardized'] += 1
                    logger.info(
                        f"Standardized color in '{text[:40]}...': "
                        f"RGB({int(old_color[0]*255)},{int(old_color[1]*255)},{int(old_color[2]*255)}) → "
                        f"RGB({int(new_color[0]*255)},{int(new_color[1]*255)},{int(new_color[2]*255)})"
                    )
                else:
                    stats['colors_unchanged'] += 1
                    logger.debug(
                        f"Color unchanged for '{text[:40]}...': "
                        f"RGB({int(old_color[0]*255)},{int(old_color[1]*255)},{int(old_color[2]*255)}) "
                        f"(already standardized)"
                    )
                
                # Convert to hex
                new_color_hex = rgb_to_hex(*new_color)
                
                # Reconstruct with new color
                return f'{prefix}{new_color_hex}{middle}{text}{suffix}'
                
            except Exception as e:
                logger.warning(f"Error processing color for annotation: {e}")
                stats['colors_unchanged'] += 1
                return match.group(0)
        
        # Apply color replacements
        modified = re.sub(richtext_pattern, replace_color, content, flags=re.DOTALL)
        
        # Save modified XFDF
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        
        logger.info(
            f"Updated XFDF colors: {stats['colors_standardized']} standardized, "
            f"{stats['colors_unchanged']} unchanged"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error updating XFDF colors: {e}")
        raise


def import_from_xfdf(doc: fitz.Document, xfdf_path: str) -> int:
    """
    Import XFDF annotations back into PDF document.
    
    This uses PyMuPDF's ability to parse XFDF and recreate annotations.
    
    Args:
        doc: PyMuPDF Document object
        xfdf_path: Path to XFDF file to import
        
    Returns:
        Number of annotations imported
    """
    logger.info(f"Importing XFDF: {xfdf_path}")
    
    try:
        # Parse XFDF
        tree = ET.parse(xfdf_path)
        root = tree.getroot()
        
        # Namespace handling
        ns = {'xfdf': 'http://ns.adobe.com/xfdf/'}
        annots_el = root.find('xfdf:annots', ns)
        if annots_el is None:
            annots_el = root.find('annots')
        
        if annots_el is None:
            logger.warning("No annotations found in XFDF")
            return 0
        
        import_count = 0
        
        # Process each freetext annotation
        for freetext in annots_el.findall('.//freetext'):
            try:
                # Get annotation properties
                page_num = int(freetext.get('page', '0'))
                rect_str = freetext.get('rect', '')
                title = freetext.get('title', 'Unknown')
                
                # Parse rectangle
                rect_parts = [float(x.strip()) for x in rect_str.split(',')]
                rect = fitz.Rect(rect_parts[0], rect_parts[1], rect_parts[2], rect_parts[3])
                
                # Get content
                contents_el = freetext.find('contents')
                content = contents_el.text if contents_el is not None and contents_el.text else ''
                content = clean_annotation_content(content)
                
                # Get rich text styling
                richtext_el = freetext.find('.//contents-richtext/body')
                font_size = 10
                text_color = (0, 0, 0)
                
                if richtext_el is not None:
                    style = richtext_el.get('style', '')
                    
                    # Extract font size
                    size_match = re.search(r'font-size:\s*([\d.]+)pt', style)
                    if size_match:
                        font_size = float(size_match.group(1))
                    
                    # Extract color
                    color_match = re.search(r'color:\s*#([0-9A-Fa-f]{6})', style)
                    if color_match:
                        text_color = hex_to_rgb('#' + color_match.group(1))
                
                # Get page
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} out of range, skipping annotation")
                    continue
                
                page = doc[page_num]
                
                # Find existing annotation at this position and update it
                # This is more reliable than deleting and recreating
                updated = False
                for annot in page.annots() or []:
                    if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                        # Check if this is the same annotation (similar position with more tolerance)
                        # Allow up to 5 points difference to account for any shifts during standardization
                        position_match = (
                            abs(annot.rect.x0 - rect.x0) < 5 and 
                            abs(annot.rect.y0 - rect.y0) < 5 and
                            abs(annot.rect.x1 - rect.x1) < 5 and
                            abs(annot.rect.y1 - rect.y1) < 5
                        )
                        
                        if position_match:
                            existing_content = annot.info.get('content', '')
                            existing_content = clean_annotation_content(existing_content)
                            # More flexible content matching - just check if they're similar
                            content_match = (
                                existing_content == content or 
                                existing_content.upper() == content.upper()
                            )
                            
                            if content_match:
                                # Update the annotation using PyMuPDF's update method with text_color
                                # This is more reliable than trying to set DA string directly
                                try:
                                    # Use annot.update() with text_color parameter
                                    # Note: We need to use the fontname that was set during standardization
                                    annot.update(
                                        fontsize=font_size,
                                        fontname="hebi",  # Bold+Italic (same as standardizer)
                                        text_color=text_color,
                                        # Keep existing fill and border colors
                                        fill_color=annot.colors.get('fill') if annot.colors else None,
                                        border_color=annot.colors.get('stroke') if annot.colors else (0, 0, 0)
                                    )
                                    updated = True
                                    import_count += 1
                                    logger.debug(
                                        f"Updated annotation on page {page_num + 1}: "
                                        f"'{existing_content[:30]}...' with color "
                                        f"RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)})"
                                    )
                                    break
                                except Exception as e:
                                    logger.warning(f"Could not update annotation: {e}")
                                    # Try alternative method using xref
                                    try:
                                        xref = annot.xref
                                        # Build DA string
                                        new_da = f"/Helv {font_size} Tf {text_color[0]} {text_color[1]} {text_color[2]} rg"
                                        # Set DA using xref
                                        page.parent.xref_set_key(xref, "DA", f"({new_da})")
                                        annot.update()
                                        updated = True
                                        import_count += 1
                                        logger.debug(f"Updated annotation via xref on page {page_num + 1}")
                                        break
                                    except Exception as e2:
                                        logger.warning(f"Alternative update method also failed: {e2}")
                
                if not updated:
                    logger.debug(
                        f"Could not find matching annotation to update on page {page_num + 1} "
                        f"at position ({rect.x0:.1f}, {rect.y0:.1f})"
                    )
                
            except Exception as e:
                logger.warning(f"Error importing annotation: {e}")
                continue
        
        logger.info(f"Imported {import_count} annotations from XFDF")
        return import_count
        
    except Exception as e:
        logger.error(f"Error importing from XFDF: {e}")
        raise


def apply_xfdf_color_workflow(doc: fitz.Document) -> Dict[str, int]:
    """
    Apply complete XFDF color workflow: export → update colors → import.
    
    Args:
        doc: PyMuPDF Document object
        
    Returns:
        Dictionary with statistics about the workflow
    """
    logger.info("Starting XFDF color workflow")
    
    stats = {
        'exported': 0,
        'colors_standardized': 0,
        'imported': 0,
        'success': False
    }
    
    try:
        # Create temporary files for XFDF processing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xfdf', delete=False, encoding='utf-8') as temp_xfdf:
            temp_xfdf_path = temp_xfdf.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_updated.xfdf', delete=False, encoding='utf-8') as temp_updated:
            temp_updated_path = temp_updated.name
        
        try:
            # Step 1: Export to XFDF
            stats['exported'] = export_to_xfdf(doc, temp_xfdf_path)
            
            if stats['exported'] == 0:
                logger.info("No annotations to process")
                stats['success'] = True
                return stats
            
            # Step 2: Update colors in XFDF
            color_stats = update_xfdf_colors(temp_xfdf_path, temp_updated_path)
            stats['colors_standardized'] = color_stats['colors_standardized']
            
            # Step 3: Import back to PDF
            stats['imported'] = import_from_xfdf(doc, temp_updated_path)
            
            stats['success'] = True
            logger.info(
                f"XFDF color workflow complete: "
                f"{stats['exported']} exported, "
                f"{stats['colors_standardized']} colors standardized, "
                f"{stats['imported']} imported"
            )
            
        finally:
            # Clean up temporary files
            try:
                Path(temp_xfdf_path).unlink(missing_ok=True)
                Path(temp_updated_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not clean up temporary files: {e}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in XFDF color workflow: {e}")
        stats['success'] = False
        return stats


def create_standardized_xfdf(doc: fitz.Document, config: StandardizationConfig, xfdf_path: str, output_pdf_path: str = None) -> Dict:
    """
    Export PDF to XFDF, extract colors from richtext, standardize, and create clean XFDF.
    
    This function:
    1. Exports annotations to XFDF using PyMuPDF's export capability
    2. Parses the exported XFDF to extract colors from richtext spans
    3. Standardizes the colors
    4. Creates a new clean XFDF file using the correct template format
    
    Args:
        doc: PyMuPDF Document object
        config: StandardizationConfig object with standardization settings
        xfdf_path: Path where XFDF file will be saved
        
    Returns:
        Dictionary with statistics about exported annotations
    """
    logger.info(f"Creating standardized XFDF: {xfdf_path}")
    
    stats = {
        'exported': 0,
        'standardized': 0
    }
    
    try:
        # The export_to_xfdf function now handles color extraction and standardization
        # Get alignment settings from config if available
        horizontal_tol = getattr(config, 'horizontal_tolerance', 1.0)
        vertical_tol = getattr(config, 'vertical_tolerance', 10.0)
        auto_resize = getattr(config, 'auto_resize_textboxes', True)
        auto_align = getattr(config, 'align_annotations', True)
        resize_skip_pages = getattr(config, 'resize_skip_pages', None)
        align_skip_pages = getattr(config, 'align_skip_pages', None)
        
        # Export with all features enabled
        annot_count = export_to_xfdf(
            doc, 
            xfdf_path, 
            config,
            output_pdf_name=Path(output_pdf_path).name if output_pdf_path else None,
            auto_resize=auto_resize,
            align_annotations=auto_align,
            horizontal_tolerance=horizontal_tol,
            vertical_tolerance=vertical_tol,
            resize_skip_pages=resize_skip_pages,
            align_skip_pages=align_skip_pages
        )
        stats['exported'] = annot_count
        
        # Update file reference if output PDF path is provided
        if output_pdf_path and annot_count > 0:
            with open(xfdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the default document.pdf reference with the actual output file
            pdf_name = Path(output_pdf_path).name
            content = content.replace('</xfdf>', f'  <f href="{pdf_name}"/>\n</xfdf>')
            
            with open(xfdf_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        logger.info(f"Created standardized XFDF with {annot_count} annotations")
        return stats
        
    except Exception as e:
        logger.error(f"Error creating standardized XFDF: {e}")
        raise


def import_standardized_xfdf(doc: fitz.Document, xfdf_path: str, clear_existing: bool = True, config=None) -> Dict:
    """
    Import standardized XFDF annotations into PDF document.
    
    This function clears existing annotations (if requested) and creates new annotations
    from the XFDF file with all standardized properties (colors, fonts, borders).
    
    Args:
        doc: PyMuPDF Document object
        xfdf_path: Path to standardized XFDF file to import
        clear_existing: If True, delete all existing annotations before importing
        config: Optional StandardizationConfig object with color settings
        
    Returns:
        Dictionary with statistics about imported annotations
    """
    logger.info(f"Importing standardized XFDF: {xfdf_path}")
    
    stats = {
        'imported': 0,
        'errors': []
    }
    
    try:
        # Clear existing annotations if requested
        if clear_existing:
            logger.info("Clearing existing annotations...")
            for page_num in range(len(doc)):
                page = doc[page_num]
                annots = list(page.annots() or [])
                for annot in annots:
                    try:
                        page.delete_annot(annot)
                    except Exception as e:
                        logger.warning(f"Could not delete annotation on page {page_num + 1}: {e}")
        
        # Parse XFDF
        tree = ET.parse(xfdf_path)
        root = tree.getroot()
        
        # Namespace handling - try multiple approaches
        ns = {'xfdf': 'http://ns.adobe.com/xfdf/'}
        annots_el = root.find('xfdf:annots', ns)
        if annots_el is None:
            annots_el = root.find('annots')
        
        if annots_el is None:
            logger.warning("No annotations found in XFDF")
            return stats
        
        # Count freetext annotations found - try both namespace-aware and regular search
        freetext_annots = annots_el.findall('.//xfdf:freetext', ns)
        if not freetext_annots:
            freetext_annots = annots_el.findall('.//freetext')
        logger.info(f"Found {len(freetext_annots)} freetext annotations in XFDF")
        
        # Process each freetext annotation
        for idx, freetext in enumerate(freetext_annots):
            try:
                # Get annotation properties
                page_num = int(freetext.get('page', '0'))
                rect_str = freetext.get('rect', '')
                title = freetext.get('title', 'Geron')
                bg_color_str = freetext.get('color', '#00FFFF')  # Default cyan in hex format
                border_width = freetext.get('width', '1')
                border_style = freetext.get('style', 'solid')
                
                logger.info(f"Processing annotation {idx + 1}: page={page_num}, rect={rect_str}, title={title}")
                
                if not rect_str:
                    logger.warning(f"Annotation {idx + 1} has no rect attribute, skipping")
                    stats['errors'].append(f"Annotation {idx + 1} missing rect attribute")
                    continue
                
                # Parse rectangle
                try:
                    rect_parts = [float(x.strip()) for x in rect_str.split(',')]
                    if len(rect_parts) != 4:
                        logger.warning(f"Annotation {idx + 1} has invalid rect format: {rect_str}")
                        stats['errors'].append(f"Annotation {idx + 1} invalid rect format")
                        continue
                    rect = fitz.Rect(rect_parts[0], rect_parts[1], rect_parts[2], rect_parts[3])
                except Exception as e:
                    logger.warning(f"Annotation {idx + 1} failed to parse rect '{rect_str}': {e}")
                    stats['errors'].append(f"Annotation {idx + 1} rect parse error: {e}")
                    continue
                
                # Parse background color - XFDF can use hex format (#RRGGBB) or RGB values
                try:
                    bg_color_str = bg_color_str.strip()
                    if bg_color_str.startswith('#'):
                        # Hex format - convert to RGB 0-1 scale
                        bg_color = hex_to_rgb(bg_color_str)
                    else:
                        # RGB values - check if 0-255 or 0-1 scale
                        bg_color_parts = [float(x.strip()) for x in bg_color_str.split()]
                        if len(bg_color_parts) == 3:
                            # Check if values are > 1 (likely 0-255 scale) or <= 1 (0-1 scale)
                            if max(bg_color_parts) > 1.0:
                                # Convert from 0-255 to 0-1 scale for PyMuPDF
                                bg_color = (bg_color_parts[0]/255.0, bg_color_parts[1]/255.0, bg_color_parts[2]/255.0)
                            else:
                                # Already in 0-1 scale
                                bg_color = tuple(bg_color_parts)
                        else:
                            bg_color = (0, 1, 1)  # Default cyan
                except Exception as e:
                    logger.warning(f"Annotation {idx + 1} failed to parse color '{bg_color_str}': {e}")
                    bg_color = (0, 1, 1)  # Default to cyan
                
                # Get content - try namespace-aware and regular search
                contents_el = freetext.find('xfdf:contents', ns)
                if contents_el is None:
                    contents_el = freetext.find('contents')
                
                content = ''
                if contents_el is not None:
                    # Get text content - handle both direct text and tail
                    content = contents_el.text if contents_el.text else ''
                    if not content and contents_el.tail:
                        content = contents_el.tail
                    logger.debug(f"Annotation {idx + 1} content from contents element: '{content}'")
                else:
                    logger.debug(f"Annotation {idx + 1} no contents element found")
                
                # If still no content, try getting from richtext span as fallback
                if not content:
                    span_el = freetext.find('.//span')
                    if span_el is not None and span_el.text:
                        content = span_el.text
                        logger.debug(f"Annotation {idx + 1} content from span: '{content}'")
                
                if not content:
                    # Debug: log the entire freetext element
                    logger.debug(f"Annotation {idx + 1} freetext element XML: {ET.tostring(freetext, encoding='unicode')}")
                    logger.warning(f"Annotation {idx + 1} has no content, skipping")
                    stats['errors'].append(f"Annotation {idx + 1} missing content")
                    continue
                
                # Clean annotation content (handles HTML/XML entities, whitespace, etc.)
                content = clean_annotation_content(content)
                
                # Debug: Log the annotation structure for all annotations to see the issue
                annot_xml = ET.tostring(freetext, encoding='unicode')
                logger.debug(f"Annotation {idx + 1} XML structure (first 500 chars):\n{annot_xml[:500]}")
                
                # Check if contents-richtext exists
                has_richtext = 'contents-richtext' in annot_xml
                logger.debug(f"Annotation {idx + 1} has contents-richtext: {has_richtext}")
                
                # Get rich text styling
                richtext_el = freetext.find('.//contents-richtext/body')
                font_size = 10
                text_color = (0, 0, 0)
                
                if richtext_el is not None:
                    style = richtext_el.get('style', '')
                    
                    # Extract font size
                    size_match = re.search(r'font-size:\s*([\d.]+)pt', style)
                    if size_match:
                        font_size = float(size_match.group(1))
                    
                    # Try to extract text color from the XML string directly
                    # This is more reliable than navigating the parsed tree with namespaces
                    annot_str = ET.tostring(freetext, encoding='unicode')
                    
                    # Look for span style with color
                    span_match = re.search(r'<span[^>]*style="([^"]*)"', annot_str)
                    if span_match:
                        span_style = span_match.group(1)
                        logger.debug(f"Found span style in XML: {span_style}")
                        
                        # Extract color from style
                        color_match = re.search(r'color:\s*#([0-9A-Fa-f]{6})', span_style)
                        if color_match:
                            text_color = hex_to_rgb('#' + color_match.group(1))
                            logger.info(f"Extracted text color from span: #{color_match.group(1)} = RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)})")
                        else:
                            # Try RGB format
                            rgb_match = re.search(r'color:\s*rgb\((\d+),\s*(\d+),\s*(\d+)\)', span_style)
                            if rgb_match:
                                text_color = (
                                    int(rgb_match.group(1)) / 255.0,
                                    int(rgb_match.group(2)) / 255.0,
                                    int(rgb_match.group(3)) / 255.0
                                )
                                logger.info(f"Extracted text color from span RGB: RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)})")
                            else:
                                logger.warning(f"No color found in span style: {span_style}")
                    else:
                        logger.warning("No span element with style found in annotation XML")
                    
                    # If not found in span, try body style as fallback
                    if text_color == (0, 0, 0):
                        color_match = re.search(r'color:\s*#([0-9A-Fa-f]{6})', style)
                        if color_match:
                            text_color = hex_to_rgb('#' + color_match.group(1))
                            logger.debug(f"Extracted text color from body: {color_match.group(1)}")
                
                # Get defaultappearance if available
                da_el = freetext.find('defaultappearance')
                da_string = da_el.text if da_el is not None and da_el.text else None
                
                # Get page
                if page_num >= len(doc):
                    logger.warning(f"Annotation {idx + 1}: Page {page_num} out of range (PDF has {len(doc)} pages), skipping")
                    stats['errors'].append(f"Annotation {idx + 1} page {page_num} out of range")
                    continue
                
                page = doc[page_num]
                
                # Create new annotation with standardized properties
                try:
                    logger.info(f"Creating annotation on page {page_num}: content='{content[:50]}...', "
                               f"text_color=RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)}), "
                               f"bg_color=RGB({int(bg_color[0]*255)},{int(bg_color[1]*255)},{int(bg_color[2]*255)})")
                    
                    # Create FreeText annotation with original rectangle
                    # PyMuPDF will auto-size the content within the rectangle
                    new_annot = page.add_freetext_annot(
                        rect,
                        content,
                        fontsize=font_size,
                        fontname="hebi",  # Helvetica-BoldOblique (bold + italic)
                        text_color=text_color,
                        fill_color=bg_color,
                        align=0  # Left align (0=left, 1=center, 2=right)
                    )
                    
                    logger.debug(f"Annotation created successfully, setting properties...")
                    
                    # Set border properties
                    try:
                        new_annot.set_border(width=float(border_width), style="S" if border_style == "solid" else border_style)
                    except Exception as e:
                        logger.debug(f"Could not set border: {e}")
                        try:
                            new_annot.set_border(width=1, style="S")
                        except:
                            pass
                    
                    # Set border color from config (default to black)
                    if config and hasattr(config, 'rectangle_border_color'):
                        border_color_tuple = config.rectangle_border_color
                    else:
                        border_color_tuple = (0, 0, 0)  # Default black RGB(0, 0, 0) in 0-1 scale
                    try:
                        new_annot.set_colors(stroke=border_color_tuple)
                    except Exception as e:
                        logger.debug(f"Could not set border color: {e}")
                    
                    # Set author
                    try:
                        new_annot.set_info(title=title)
                    except Exception as e:
                        logger.debug(f"Could not set author: {e}")
                    
                    # Set defaultappearance if available - this is critical for text color
                    if da_string:
                        try:
                            xref = new_annot.xref
                            # Set DA string directly - this controls text color
                            doc.xref_set_key(xref, "DA", f"({da_string})")
                            logger.debug(f"Set DA string: {da_string}")
                        except Exception as e:
                            logger.debug(f"Could not set DA: {e}")
                    else:
                        # If no DA string, create one from text_color
                        r, g, b = text_color
                        da_string = f"{r} {g} {b} rg /Helv {font_size} Tf"
                        try:
                            xref = new_annot.xref
                            doc.xref_set_key(xref, "DA", f"({da_string})")
                            logger.debug(f"Created DA string from text_color: {da_string}")
                        except Exception as e:
                            logger.debug(f"Could not set DA from text_color: {e}")
                    
                    # Update annotation to ensure appearance is generated with correct colors
                    # Get border color from config (default to black)
                    if config and hasattr(config, 'rectangle_border_color'):
                        border_color_tuple = config.rectangle_border_color
                    else:
                        border_color_tuple = (0, 0, 0)  # Default black RGB(0, 0, 0) in 0-1 scale
                    try:
                        new_annot.update(
                            fontsize=font_size,
                            fontname="hebi",
                            text_color=text_color,
                            fill_color=bg_color,
                            border_color=border_color_tuple
                        )
                        logger.info(f"Updated annotation with text_color=RGB({int(text_color[0]*255)},{int(text_color[1]*255)},{int(text_color[2]*255)}), "
                                   f"bg_color=RGB({int(bg_color[0]*255)},{int(bg_color[1]*255)},{int(bg_color[2]*255)})")
                    except Exception as e:
                        logger.debug(f"Could not update annotation: {e}")
                    
                    # After update, ensure DA string is still set correctly
                    try:
                        xref = new_annot.xref
                        r, g, b = text_color
                        da_string_final = f"{r} {g} {b} rg /Helv {font_size} Tf"
                        doc.xref_set_key(xref, "DA", f"({da_string_final})")
                        logger.debug(f"Re-set DA string after update: {da_string_final}")
                    except Exception as e:
                        logger.debug(f"Could not re-set DA after update: {e}")
                    
                    stats['imported'] += 1
                    logger.debug(f"Successfully imported annotation {idx + 1}")
                    
                except Exception as e:
                    error_msg = f"Error creating annotation {idx + 1} on page {page_num + 1}: {e}"
                    logger.error(error_msg, exc_info=True)
                    stats['errors'].append(error_msg)
                    continue
                    
            except Exception as e:
                error_msg = f"Error processing annotation {idx + 1}: {e}"
                logger.error(error_msg, exc_info=True)
                stats['errors'].append(error_msg)
                continue
        
        logger.info(f"Imported {stats['imported']} annotations from standardized XFDF")
        if stats['errors']:
            logger.warning(f"Encountered {len(stats['errors'])} errors during import")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error importing standardized XFDF: {e}")
        stats['errors'].append(str(e))
        raise

