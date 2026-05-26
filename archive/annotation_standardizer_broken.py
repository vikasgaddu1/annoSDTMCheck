"""PDF annotation standardization and bookmark generation module."""

import fitz  # PyMuPDF
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

# Import annotation resizer and aligner
try:
    from .annotation_resizer import AnnotationResizer
    from .text_dimension_calculator import TextDimensionCalculator
    RESIZER_AVAILABLE = True
except ImportError:
    RESIZER_AVAILABLE = False
    logger.warning("AnnotationResizer not available")

try:
    from .annotation_aligner import AnnotationAligner
    ALIGNER_AVAILABLE = True
except ImportError:
    ALIGNER_AVAILABLE = False
    logger.warning("AnnotationAligner not available")


def is_header_annotation(text):
    """Check if annotation follows the pattern 'XX = Label' (e.g., 'DM = Demographics')
    
    Returns True only if:
    - Exactly 2 uppercase letters on the left
    - Followed by = sign
    - Right side does NOT contain quotes (single or double)
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Pattern: exactly 2 uppercase letters, followed by space(s), equals sign, space(s), and text
    pattern = r'^[A-Z]{2}\s*=\s*.+'
    
    if not re.match(pattern, text):
        return False
    
    # Check if right side of equals contains quotes (not a header if it does)
    if '=' in text:
        right_side = text.split('=', 1)[1].strip()
        if "'" in right_side or '"' in right_side:
            return False
    
    return True


def get_text_color_from_annotation(annot: fitz.Annot) -> Tuple[float, float, float]:
    """
    Extract text color from annotation's Default Appearance (DA) string or appearance stream.
    
    For FreeText annotations, the text color is stored in the DA string,
    not in annot.colors['stroke']. The DA string contains color information
    in the format: "r g b rg" or "r g b RG" where r, g, b are in 0-1 scale.
    
    If DA string doesn't contain color info, we extract it from the appearance stream.
    
    Args:
        annot: PyMuPDF annotation object
        
    Returns:
        Tuple of (r, g, b) in 0-1 scale, defaults to (0, 0, 0) if not found
    """
    import re
    
    try:
        # Get Default Appearance string
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
            # Parse DA string for color information
            # Format examples:
            # "/Helv 10 Tf 0.0588 0 1 rg" - blue-ish text color
            # "/Helv 10 Tf 0 0 0 rg" - black text color
            # The "rg" operator sets RGB color for non-stroking operations (fills, text)
            # The "RG" operator sets RGB color for stroking operations (lines, borders)
            
            # Look for RGB color pattern: three numbers followed by 'rg' (text color)
            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if color_match:
                r = float(color_match.group(1))
                g = float(color_match.group(2))
                b = float(color_match.group(3))
                
                # If DA has black (0 0 0) or white (1 1 1), try appearance stream instead
                # Some PDFs have incorrect DA but correct appearance stream
                if (r, g, b) not in [(0, 0, 0), (1, 1, 1)]:
                    logger.debug(f"Extracted text color from DA: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")
                    return (r, g, b)
        
        # Try extracting from appearance stream as it may have the actual color
        try:
            xref = annot.xref
            if xref > 0:
                doc = annot.parent.parent
                annot_dict = doc.xref_object(xref)
                
                # Look for appearance stream reference
                ap_match = re.search(r'/N\s+(\d+)\s+\d+\s+R', annot_dict)
                if ap_match:
                    ap_xref = int(ap_match.group(1))
                    ap_stream = doc.xref_stream(ap_xref)
                    
                    if ap_stream:
                        ap_text = ap_stream.decode('latin-1', errors='ignore')
                        
                        # Look for text color operators (rg = RGB for text/fills)
                        # Get the LAST rg color before text (BT...ET) as that's the text color
                        rg_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', ap_text)
                        if rg_matches:
                            # Find the text color (usually the second one, first is background)
                            for r_str, g_str, b_str in rg_matches:
                                r = float(r_str)
                                g = float(g_str)
                                b = float(b_str)
                                
                                # Skip cyan background color (0, 1, 1) and white (1, 1, 1)
                                # and light cyan variations
                                if (r, g, b) not in [(0, 1, 1), (1, 1, 1), (0.75, 1, 1), (0.85, 1, 1)]:
                                    logger.debug(f"Extracted text color from appearance stream: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")
                                    return (r, g, b)
        except Exception as e:
            logger.debug(f"Could not extract from appearance stream: {e}")
        
        # Fallback: try to get from annot.colors (but skip cyan)
        current_colors = annot.colors
        if current_colors and 'stroke' in current_colors:
            color = current_colors['stroke']
            # Skip cyan as it's the background color
            if color not in [(0, 1, 1), (0.75, 1, 1), (0.85, 1, 1)]:
                logger.debug(f"Using stroke color as fallback: {color}")
                return color
        
        # Default: black
        logger.debug("Could not extract text color, using black as default")
        return (0, 0, 0)
        
    except Exception as e:
        logger.warning(f"Error extracting text color from annotation: {e}")
        return (0, 0, 0)


def standardize_color(color):
    """
    Map various shades to standard colors (Blue, Red, Green, Yellow/Orange, Black).
    
    Uses a robust algorithm that identifies the dominant color channel and 
    standardizes based on relative intensities rather than fixed thresholds.
    
    Args:
        color: Tuple of (r, g, b) in 0-1 scale (PyMuPDF format)
        
    Returns:
        Standardized color tuple in 0-1 scale
    """
    if not color or len(color) != 3:
        return (0, 0, 0)  # Default to black
    
    r, g, b = color
    
    # Handle black/very dark colors first
    max_intensity = max(r, g, b)
    if max_intensity < 0.15:  # Very dark (RGB < 38 for any component)
        return (0, 0, 0)  # Pure black RGB(0, 0, 0)
    
    # Find the dominant channel(s)
    # Normalize by max intensity to handle different brightness levels
    r_norm = r / max_intensity if max_intensity > 0 else 0
    g_norm = g / max_intensity if max_intensity > 0 else 0
    b_norm = b / max_intensity if max_intensity > 0 else 0
    
    # Blue detection: blue is dominant, red and green are much lower
    # This catches: (0,0,255), (15,0,255), (0,61,255), etc.
    if b_norm > 0.9 and r_norm < 0.3 and g_norm < 0.3:
        return (0, 0, 1)  # Pure blue RGB(0, 0, 255)
    
    # Red detection: red is dominant, green and blue are much lower
    # This catches: (255,0,0), (255,50,50), etc.
    elif r_norm > 0.9 and g_norm < 0.3 and b_norm < 0.3:
        return (1, 0, 0)  # Pure red RGB(255, 0, 0)
    
    # Green detection: green is dominant, red and blue are much lower
    # This catches: (0,255,0), (50,255,50), etc.
    elif g_norm > 0.9 and r_norm < 0.3 and b_norm < 0.3:
        return (0, 1, 0)  # Pure green RGB(0, 255, 0)
    
    # Orange/Yellow detection: both red and green high, blue low
    # This catches: (255,165,0), (255,200,0), (255,255,0), etc.
    elif r_norm > 0.7 and g_norm > 0.5 and b_norm < 0.3:
        return (1, 0.65, 0)  # Standard orange RGB(255, 165, 0)
    
    # Cyan detection: blue and green high, red low
    elif b_norm > 0.8 and g_norm > 0.8 and r_norm < 0.2:
        return (0, 1, 1)  # Cyan RGB(0, 255, 255)
    
    # Magenta detection: red and blue high, green low
    elif r_norm > 0.8 and b_norm > 0.8 and g_norm < 0.2:
        return (1, 0, 1)  # Magenta RGB(255, 0, 255)
    
    # If no clear match, check absolute thresholds as fallback
    # This handles edge cases where normalization doesn't work well
    
    # Blue fallback: blue is strong, others are weak
    if b > 0.8 and r < 0.2 and g < 0.3:
        return (0, 0, 1)  # Pure blue
    
    # Red fallback: red is strong, others are weak
    elif r > 0.8 and g < 0.2 and b < 0.2:
        return (1, 0, 0)  # Pure red
    
    # Green fallback: green is strong, others are weak
    elif g > 0.8 and r < 0.2 and b < 0.2:
        return (0, 1, 0)  # Pure green
    
    # Default: keep original color if it doesn't match any category
    logger.debug(f"Color {color} (RGB {int(r*255)},{int(g*255)},{int(b*255)}) doesn't match standard colors, keeping original")
    return color


@dataclass
class StandardizationConfig:
    """Configuration for annotation standardization."""
    header_font: str = "Helvetica"  # Base14 font as Arial substitute
    header_size: int = 12
    header_bold: bool = True
    header_italic: bool = True
    
    text_font: str = "Helvetica"
    text_size: int = 10
    text_bold: bool = True
    text_italic: bool = True
    
    rectangle_border_color: Tuple[float, float, float] = (0, 0, 0)  # Black RGB
    background_color: Tuple[float, float, float] = (0, 1, 1)  # Cyan RGB(0, 255, 255)
    default_author: str = "Geron"
    
    # Bookmark labels
    form_bookmark_label: str = "Form_bookmarks"
    sdtm_bookmark_label: str = "SDTM"
    
    # Regex for header detection
    header_pattern: str = r'^([A-Z]{2})\s*=\s*([^=]+)$'
    
    # Auto-resize textboxes
    auto_resize_textboxes: bool = False
    resize_expand_width: bool = True
    resize_expand_height: bool = True
    resize_max_width_expansion: Optional[float] = 200.0
    resize_max_height_expansion: Optional[float] = 300.0
    
    # Recreate annotations (fixes color/font issues with PDFs that have appearance streams)
    recreate_annotations: bool = True  # Use delete-and-recreate approach for better color/font control
    
    # Auto-align annotations
    align_annotations: bool = False
    align_horizontal: bool = True
    align_vertical: bool = True
    horizontal_tolerance: float = 10.0  # points
    vertical_tolerance: float = 10.0    # points


@dataclass
class DomainBookmark:
    """Stores bookmark information for a domain."""
    domain_code: str
    domain_name: str
    pages: List[Tuple[int, str]] = field(default_factory=list)  # (page_num, form_name)


@dataclass
class FormInfo:
    """Stores form information for bookmarks."""
    page_num: int
    form_name: str
    domains: List[str] = field(default_factory=list)


class AnnotationStandardizer:
    """Standardizes PDF annotations and creates bookmarks."""
    
    def __init__(self, config: Optional[StandardizationConfig] = None):
        """Initialize the standardizer with optional configuration."""
        self.config = config or StandardizationConfig()
        self.logger = logging.getLogger(__name__)
        self.header_regex = re.compile(self.config.header_pattern)
        self.domain_bookmarks: Dict[str, DomainBookmark] = {}
        self.form_list: List[FormInfo] = []  # For Form_bookmarks section
        
    def standardize_pdf(self, input_path: str, output_path: str) -> Dict:
        """
        Main method to standardize annotations and create bookmarks.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path where standardized PDF will be saved
            
        Returns:
            Dictionary containing statistics about modifications
        """
        self.logger.info(f"Starting standardization of {input_path}")
        
        # Initialize statistics
        stats = {
            'annotations_modified': 0,
            'headers_found': 0,
            'text_capitalized': 0,
            'rectangles_styled': 0,
            'bookmarks_created': 0,
            'errors': []
        }
        
        try:
            # Open the PDF document
            doc = fitz.open(input_path)
            
            # Process all pages
            total_annots_on_pages = sum(1 for p in range(len(doc)) for _ in (doc[p].annots() or []))
            self.logger.info(f"Found {total_annots_on_pages} total annotations across {len(doc)} pages")
            
            # Track current form for Form_bookmarks section
            current_form_info = None
            current_form_domains = set()
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_headers = []
                form_name = self._extract_form_name(page)
                
                # Check if this is a new form
                if current_form_info is None or current_form_info.form_name != form_name:
                    # Save previous form if exists
                    if current_form_info is not None:
                        current_form_info.domains = list(current_form_domains)
                        self.form_list.append(current_form_info)
                    
                    # Start new form
                    current_form_info = FormInfo(
                        page_num=page_num,
                        form_name=form_name,
                        domains=[]
                    )
                    current_form_domains = set()
                
                # Get all annotations on the page
                annots_on_page = list(page.annots() or [])
                if page_num < 3 and annots_on_page:
                    self.logger.debug(f"Page {page_num + 1} has {len(annots_on_page)} annotations")
                
                # STEP 1: Collect annotation data if using recreate approach
                if self.config.recreate_annotations:
                    annots_data_list = []
                    
                    for annot in annots_on_page:
                        try:
                            annot_type = annot.type[0]
                            content = annot.info.get('content', '').strip()
                            
                            if annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                                # Extract and standardize color
                                original_font_color = get_text_color_from_annotation(annot)
                                font_color = standardize_color(original_font_color)
                                
                                # Determine font size
                                font_size = self.config.header_size if is_header_annotation(content) else self.config.text_size
                                
                                # Calculate new rect if auto-resize is enabled
                                new_rect = None
                                if self.config.auto_resize_textboxes and content and RESIZER_AVAILABLE:
                                    from .text_dimension_calculator import TextDimensionCalculator
                                    calculator = TextDimensionCalculator()
                                    old_rect = annot.rect
                                    
                                    fits = calculator.check_if_text_fits(content, old_rect, "hebi", float(font_size))
                                    if not fits:
                                        required_width, required_height = calculator.calculate_optimal_dimensions(
                                            content, "hebi", float(font_size), current_width=None
                                        )
                                        old_width = old_rect.width
                                        old_height = old_rect.height
                                        
                                        width_increase = required_width - old_width
                                        if self.config.resize_max_width_expansion is not None:
                                            width_increase = min(width_increase, self.config.resize_max_width_expansion)
                                        new_width = old_width + max(0, width_increase)
                                        
                                        height_increase = required_height - old_height
                                        if self.config.resize_max_height_expansion is not None:
                                            height_increase = min(height_increase, self.config.resize_max_height_expansion)
                                        new_height = old_height + max(0, height_increase)
                                        
                                        if abs(new_width - old_width) >= 1.0 or abs(new_height - old_height) >= 1.0:
                                            new_rect = fitz.Rect(
                                                old_rect.x0, old_rect.y0,
                                                old_rect.x0 + new_width, old_rect.y0 + new_height
                                            )
                                            if 'textboxes_resized' not in stats:
                                                stats['textboxes_resized'] = 0
                                            stats['textboxes_resized'] += 1
                                    
                                    if 'textboxes_checked' not in stats:
                                        stats['textboxes_checked'] = 0
                                    stats['textboxes_checked'] += 1
                                
                                # Store annotation data
                                annots_data_list.append({
                                    'rect': new_rect if new_rect else annot.rect,
                                    'content': content,
                                    'color': font_color,
                                    'fontsize': font_size,
                                    'fontname': "hebi",
                                    'author': self.config.default_author,
                                    'is_header': is_header_annotation(content)
                                })
                        except Exception as e:
                            self.logger.warning(f"Error collecting annotation data: {e}")
                    
                    # STEP 2: Delete all FreeText annotations
                    annot = page.first_annot
                    while annot:
                        next_annot = annot.next
                        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                            page.delete_annot(annot)
                        annot = next_annot
                    
                    # STEP 3: Recreate annotations with correct attributes
                    for annot_data in annots_data_list:
                        try:
                            # Create new FreeText annotation
                            new_annot = page.add_freetext_annot(
                                annot_data['rect'],
                                annot_data['content'],
                                fontsize=annot_data['fontsize'],
                                fontname=annot_data['fontname'],
                                text_color=annot_data['color'],
                                fill_color=self.config.background_color
                            )
                            
                            # Set border
                            new_annot.set_border(width=1, style="S")
                            
                            # Set author
                            new_annot.set_info(title=annot_data['author'])
                            
                            # Update to generate appearance stream
                            new_annot.update(
                                fontsize=annot_data['fontsize'],
                                fontname=annot_data['fontname'],
                                text_color=annot_data['color'],
                                fill_color=self.config.background_color
                            )
                            
                            stats['annotations_modified'] += 1
                            
                            # Track headers for bookmarks
                            if annot_data['is_header']:
                                content = annot_data['content'].replace('\r', '').replace('\n', ' ').strip()
                                header_match = self.header_regex.match(content)
                                if header_match:
                                    domain = header_match.group(1)
                                    label = header_match.group(2).strip()
                                    page_headers.append((domain, label, page_num))
                                    current_form_domains.add(domain)
                                    stats['headers_found'] += 1
                        except Exception as e:
                            self.logger.warning(f"Error recreating annotation: {e}")
                    
                    # Continue with non-FreeText annotations (other types weren't deleted)
                    for annot in list(page.annots() or []):
                        try:
                            # Get annotation info and type
                            annot_type = annot.type[0]
                            annot_type_name = annot.type[1] if len(annot.type) > 1 else f"Type{annot_type}"
                            content = annot.info.get('content', '').strip()
                            
                            # Skip FreeText - already handled above
                            if annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                                continue
                            
                            # Update author for non-FreeText annotations
                            annot.set_info(title=self.config.default_author)
                            
                            # Handle other annotation types
                            if annot_type not in [fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_STRIKEOUT, 
                                                    fitz.PDF_ANNOT_CARET, fitz.PDF_ANNOT_HIGHLIGHT,
                                                    fitz.PDF_ANNOT_UNDERLINE]:
                                # For other annotation types (Square, Circle, etc.)
                                try:
                                    annot.set_border(width=2, style="S")
                                except:
                                    pass
                                try:
                                    annot.set_colors(stroke=self.config.rectangle_border_color, fill=self.config.background_color)
                                except:
                                    try:
                                        annot.set_colors(stroke=self.config.rectangle_border_color)
                                    except:
                                        pass
                                stats['rectangles_styled'] += 1
                        except Exception as e:
                            self.logger.warning(f"Error processing non-FreeText annotation: {e}")
                
                # OLD APPROACH: Only used if recreate_annotations is False
                else:
                    for annot in annots_on_page:
                        try:
                            # Get annotation info and type
                            annot_type = annot.type[0]
                            annot_type_name = annot.type[1] if len(annot.type) > 1 else f"Type{annot_type}"
                            content = annot.info.get('content', '').strip()
                            
                            # Debug: log annotation types for first few
                            if stats['annotations_modified'] < 10:
                                self.logger.debug(f"Annotation type: {annot_type_name} ({annot_type}), Content: {content[:50]}")
                            
                            # Determine font size based on content
                            font_size = self.config.header_size if is_header_annotation(content) else self.config.text_size
                            
                            # Get current font color and standardize it
                            original_font_color = get_text_color_from_annotation(annot)
                            font_color = standardize_color(original_font_color)
                            
                            # Use cyan as background color for all annotations
                            bg_color = self.config.background_color
                            
                            # Update author
                            annot.set_info(title=self.config.default_author)
                            
                            # Handle FreeText annotations specially (can use update method)
                            if annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                                try:
                                    # Set border width and style
                                    annot.set_border(width=1, style="S")
                                    
                                    # Check if auto-resize is enabled and calculate new dimensions BEFORE updating
                                    new_rect = None
                                    if self.config.auto_resize_textboxes and content and RESIZER_AVAILABLE:
                                        from .text_dimension_calculator import TextDimensionCalculator
                                        
                                        calculator = TextDimensionCalculator()
                                        old_rect = annot.rect
                                    
                                    # Check if text fits with the STANDARDIZED font (hebi=bold+italic, with standardized size)
                                    # This is critical - we must use the font we're ABOUT TO apply, not the current font
                                    fits = calculator.check_if_text_fits(
                                        content, old_rect, "hebi", float(font_size)
                                    )
                                    
                                    if not fits:
                                        # Calculate required dimensions with STANDARDIZED font
                                        required_width, required_height = calculator.calculate_optimal_dimensions(
                                            content, "hebi", float(font_size), current_width=None
                                        )
                                        
                                        # Apply expansion limits
                                        old_width = old_rect.width
                                        old_height = old_rect.height
                                        
                                        width_increase = required_width - old_width
                                        if self.config.resize_max_width_expansion is not None:
                                            width_increase = min(width_increase, self.config.resize_max_width_expansion)
                                        new_width = old_width + max(0, width_increase)
                                        
                                        height_increase = required_height - old_height
                                        if self.config.resize_max_height_expansion is not None:
                                            height_increase = min(height_increase, self.config.resize_max_height_expansion)
                                        new_height = old_height + max(0, height_increase)
                                        
                                        # Only resize if there's a significant change
                                        if abs(new_width - old_width) >= 1.0 or abs(new_height - old_height) >= 1.0:
                                            new_rect = fitz.Rect(
                                                old_rect.x0,
                                                old_rect.y0,
                                                old_rect.x0 + new_width,
                                                old_rect.y0 + new_height
                                            )
                                            self.logger.debug(
                                                f"Page {page_num + 1}: Resizing '{content[:30]}...' "
                                                f"from ({old_width:.1f}x{old_height:.1f}) "
                                                f"to ({new_width:.1f}x{new_height:.1f})"
                                            )
                                            
                                            # Track resize stats
                                            if 'textboxes_checked' not in stats:
                                                stats['textboxes_checked'] = 0
                                                stats['textboxes_resized'] = 0
                                            stats['textboxes_resized'] += 1
                                    
                                    if 'textboxes_checked' not in stats:
                                        stats['textboxes_checked'] = 0
                                        stats['textboxes_resized'] = 0
                                    stats['textboxes_checked'] += 1
                                
                                # Apply resize BEFORE updating appearance
                                if new_rect:
                                    annot.set_rect(new_rect)
                                
                                # CRITICAL FIX: PyMuPDF's annot.update() doesn't properly honor text_color 
                                # for PDFs with existing appearance streams. We must manually fix the appearance stream.
                                
                                # First, update with our parameters
                                annot.update(
                                    fontsize=font_size,
                                    fontname="hebi",  # Helvetica-BoldOblique (bold + italic)
                                    text_color=font_color,  # Use standardized font color
                                    fill_color=bg_color,  # Cyan fill/background (0, 1, 1)
                                    border_color=(0, 0, 0)  # Black border
                                )
                                
                                # Now manually fix the DA string
                                r, g, b = font_color
                                da_string = f"{r} {g} {b} rg /Helv-BoldOblique {font_size} Tf"
                                
                                try:
                                    xref = annot.xref
                                    doc.xref_set_key(xref, "DA", f"({da_string})")
                                    self.logger.debug(f"Set DA: {da_string}")
                                except Exception as e:
                                    self.logger.warning(f"Could not set DA: {e}")
                                
                                # Manually fix the appearance stream's text color
                                try:
                                    import re
                                    xref = annot.xref
                                    annot_dict = doc.xref_object(xref)
                                    
                                    # Get appearance stream reference
                                    ap_match = re.search(r'/N\s+(\d+)\s+\d+\s+R', annot_dict)
                                    if ap_match:
                                        ap_xref = int(ap_match.group(1))
                                        ap_stream = doc.xref_stream(ap_xref)
                                        
                                        if ap_stream:
                                            ap_text = ap_stream.decode('latin-1', errors='ignore')
                                            
                                            # Replace all text color (rg) operators except cyan background
                                            # Pattern: find "r g b rg" where it's NOT cyan (0 1 1)
                                            def replace_color(match):
                                                r_old = float(match.group(1))
                                                g_old = float(match.group(2))
                                                b_old = float(match.group(3))
                                                
                                                # Keep cyan (background), replace everything else with our font_color
                                                if (abs(r_old - 0) < 0.01 and abs(g_old - 1) < 0.01 and abs(b_old - 1) < 0.01):
                                                    return match.group(0)  # Keep cyan
                                                elif (abs(r_old - 0.75) < 0.01 and abs(g_old - 1) < 0.01 and abs(b_old - 1) < 0.01):
                                                    return match.group(0)  # Keep light cyan
                                                else:
                                                    return f"{r} {g} {b} rg"  # Replace with standardized color
                                            
                                            new_ap_text = re.sub(
                                                r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg',
                                                replace_color,
                                                ap_text
                                            )
                                            
                                            if new_ap_text != ap_text:
                                                doc.update_stream(ap_xref, new_ap_text.encode('latin-1', errors='ignore'))
                                                self.logger.debug(f"Fixed appearance stream color")
                                except Exception as e:
                                    self.logger.warning(f"Could not fix appearance stream: {e}")
                               
                                stats['annotations_modified'] += 1
                            except Exception as e:
                                self.logger.warning(f"Could not fully update FreeText annotation: {e}")
                                stats['annotations_modified'] += 1
                        elif annot_type not in [fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_STRIKEOUT, 
                                                fitz.PDF_ANNOT_CARET, fitz.PDF_ANNOT_HIGHLIGHT,
                                                fitz.PDF_ANNOT_UNDERLINE]:
                            # For other annotation types (except Text, StrikeOut, Caret, Highlight, Underline which don't support borders/fills)
                            # Set colors and border where applicable (Square, Circle, etc.)
                            try:
                                # Set border first
                                annot.set_border(width=2, style="S")
                            except:
                                pass
                            
                            try:
                                # Try to set colors - stroke controls border color
                                annot.set_colors(stroke=self.config.rectangle_border_color, fill=bg_color)
                            except:
                                try:
                                    annot.set_colors(stroke=self.config.rectangle_border_color)
                                except:
                                    pass
                            
                            stats['annotations_modified'] += 1
                        else:
                            # For Text, StrikeOut, Caret, Highlight, Underline annotations, we can only update author and content
                            # Borders and fill colors are not supported for these annotation types
                            if annot_type in [fitz.PDF_ANNOT_STRIKEOUT, fitz.PDF_ANNOT_CARET]:
                                self.logger.info(f"Found {annot_type_name} annotation on page {page_num + 1}")
                            stats['annotations_modified'] += 1
                        
                        # Track headers and forms for bookmarks
                        if content:
                            content = content.replace('\r', '').replace('\n', ' ').strip()
                            header_match = self.header_regex.match(content)
                            
                            if header_match:
                                # This is a header annotation
                                domain_code = header_match.group(1)
                                domain_desc = header_match.group(2).strip()
                                
                                page_headers.append((domain_code, domain_desc))
                                stats['headers_found'] += 1
                                
                                # Track for bookmarks
                                if domain_code not in self.domain_bookmarks:
                                    self.domain_bookmarks[domain_code] = DomainBookmark(
                                        domain_code, domain_desc
                                    )
                                self.domain_bookmarks[domain_code].pages.append(
                                    (page_num, form_name)
                                )
                                
                                # Track domain for current form
                                current_form_domains.add(domain_code)
                                
                                self.logger.info(f"Found header: {domain_code} = {domain_desc} on page {page_num + 1}")
                        
                        # Apply changes to the annotation (not needed for FreeText since we already called update)
                        if annot_type != fitz.PDF_ANNOT_FREE_TEXT:
                            annot.update()
                        
                    except Exception as e:
                        error_msg = f"Error processing annotation on page {page_num + 1}: {str(e)}"
                        self.logger.error(error_msg)
                        stats['errors'].append(error_msg)
            
            # Don't forget the last form
            if current_form_info is not None:
                current_form_info.domains = list(current_form_domains)
                self.form_list.append(current_form_info)
            
            # Log auto-resize results if enabled
            if self.config.auto_resize_textboxes and RESIZER_AVAILABLE:
                checked = stats.get('textboxes_checked', 0)
                resized = stats.get('textboxes_resized', 0)
                if checked > 0:
                    self.logger.info(f"Auto-resize: checked {checked} textboxes, resized {resized}")
            elif self.config.auto_resize_textboxes and not RESIZER_AVAILABLE:
                self.logger.warning("Auto-resize requested but TextDimensionCalculator not available")
            
            # Create bookmarks
            stats['bookmarks_created'] = self._create_bookmarks(doc)
            
            # Align annotations if enabled
            if self.config.align_annotations and ALIGNER_AVAILABLE:
                try:
                    aligner = AnnotationAligner(
                        horizontal_tolerance=self.config.horizontal_tolerance,
                        vertical_tolerance=self.config.vertical_tolerance,
                        align_horizontal=self.config.align_horizontal,
                        align_vertical=self.config.align_vertical
                    )
                    
                    # Process each page
                    total_h_aligned = 0
                    total_v_aligned = 0
                    
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        annotations = list(page.annots() or [])
                        
                        if not annotations:
                            continue
                        
                        # Align horizontally
                        if self.config.align_horizontal:
                            h_ops = aligner._align_page_horizontal(annotations, page_num, dry_run=False)
                            total_h_aligned += len(h_ops)
                        
                        # Align vertically
                        if self.config.align_vertical:
                            v_ops = aligner._align_page_vertical(annotations, page_num, dry_run=False)
                            total_v_aligned += len(v_ops)
                    
                    stats['annotations_aligned_horizontal'] = total_h_aligned
                    stats['annotations_aligned_vertical'] = total_v_aligned
                    
                    if total_h_aligned > 0 or total_v_aligned > 0:
                        self.logger.info(
                            f"Auto-align: {total_h_aligned} horizontally aligned, "
                            f"{total_v_aligned} vertically aligned"
                        )
                
                except Exception as e:
                    self.logger.error(f"Error during alignment: {e}")
                    stats['errors'].append(f"Alignment error: {str(e)}")
            
            elif self.config.align_annotations and not ALIGNER_AVAILABLE:
                self.logger.warning("Auto-align requested but AnnotationAligner not available")
            
            # Save modified PDF
            doc.save(output_path)
            doc.close()
            
            self.logger.info(f"Standardization complete. Saved to {output_path}")
            self.logger.info(f"Stats: {stats}")
            
        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
            self.logger.error(error_msg)
            stats['errors'].append(error_msg)
            raise
            
        return stats
    
    def _extract_form_name(self, page: fitz.Page) -> str:
        """
        Extract form name from page.
        
        Looks for "Form: <form_name>" pattern in page text.
        Falls back to first significant line or page number.
        """
        try:
            # Get text from the page
            text = page.get_text()
            
            # Look for form name pattern: "Form: <form_name>"
            form_match = re.search(r'Form:\s*(.+?)(?:\n|$)', text)
            if form_match:
                return form_match.group(1).strip()
            
            # Fallback: look for potential form names in first few lines
            lines = text.strip().split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if line and len(line) > 3 and len(line) < 100:
                    # Likely a form title
                    return line
                    
            # Last resort: use page number
            return f"Page {page.number + 1}"
            
        except Exception as e:
            self.logger.warning(f"Could not extract form name: {e}")
            return f"Page {page.number + 1}"
    
    def _standardize_header(self, annot: fitz.Annot, content: str):
        """
        Apply header formatting.
        Headers keep their original content (domain code uppercase, description as-is).
        """
        try:
            # Headers keep their original content
            # Apply header font settings
            self._apply_font_style(
                annot, 
                self.config.header_size, 
                self.config.header_bold, 
                self.config.header_italic
            )
            self.logger.debug(f"Standardized header: {content}")
        except Exception as e:
            self.logger.error(f"Error standardizing header: {e}")
    
    def _standardize_text(self, annot: fitz.Annot, content: str):
        """
        Apply text formatting and capitalize content.
        """
        try:
            # Convert content to uppercase
            info = annot.info
            info["content"] = content.upper()
            annot.set_info(info)
            
            # Apply text font settings
            self._apply_font_style(
                annot,
                self.config.text_size,
                self.config.text_bold,
                self.config.text_italic
            )
            self.logger.debug(f"Capitalized text: {content} -> {content.upper()}")
        except Exception as e:
            self.logger.error(f"Error standardizing text: {e}")
    
    def _standardize_rectangle(self, annot: fitz.Annot):
        """
        Apply rectangle border standardization.
        """
        try:
            # Set stroke color to black, keep fill transparent
            colors = {
                "stroke": self.config.rectangle_border_color,
                "fill": None  # Keep fill transparent
            }
            annot.set_colors(colors)
            self.logger.debug("Standardized rectangle border to black")
        except Exception as e:
            self.logger.error(f"Error standardizing rectangle: {e}")
    
    def _apply_font_style(self, annot: fitz.Annot, size: int, bold: bool, italic: bool):
        """
        Apply font styling to annotation.
        
        Note: PyMuPDF's FreeText annotations have limited styling capabilities.
        For text annotations (popup notes), font styling is controlled by the PDF viewer.
        We can only modify the content, not the appearance of popup annotations.
        """
        try:
            # For FreeText annotations, we could set font properties
            # But for standard text annotations (popup notes), the appearance
            # is controlled by the PDF viewer and cannot be programmatically changed
            # This is a limitation of the PDF specification
            
            # Log that font styling was attempted
            self.logger.debug(f"Font style metadata recorded (size: {size}pt, bold: {bold}, italic: {italic})")
            
        except Exception as e:
            self.logger.warning(f"Could not apply font style: {e}")
    
    def _create_bookmarks(self, doc: fitz.Document) -> int:
        """
        Create dual hierarchical bookmark structure.
        
        Structure:
        1. <Form Bookmark Label> (parent) - configurable, default: "Form_bookmarks"
           - Form Name 1 (page X)
           - Form Name 2 (page Y)
        
        2. <SDTM Bookmark Label> (parent) - configurable, default: "SDTM"
           - DM (domain)
             - Form Name 1 (page X)
             - Form Name 2 (page Y)
           - AE (domain)
             - Form Name 3 (page Z)
        """
        try:
            # Build bookmark table of contents
            toc = []
            
            # 1. Create form bookmarks section (with configurable label)
            if self.form_list:
                toc.append([1, self.config.form_bookmark_label, 1])  # Level 1, title, page 1
                
                for form_info in self.form_list:
                    # Add form as level 2 bookmark
                    toc.append([2, form_info.form_name, form_info.page_num + 1])
                
                self.logger.info(f"Created '{self.config.form_bookmark_label}' section with {len(self.form_list)} forms")
            
            # 2. Create SDTM section with domain-based bookmarks (with configurable label)
            if self.domain_bookmarks:
                toc.append([1, self.config.sdtm_bookmark_label, 1])  # Level 1, title, page 1
                
                # Group forms by domain
                domain_forms = defaultdict(list)
                for form_info in self.form_list:
                    for domain in form_info.domains:
                        domain_forms[domain].append((form_info.page_num, form_info.form_name))
                
                # Add domain bookmarks
                for domain_code in sorted(self.domain_bookmarks.keys()):
                    bookmark = self.domain_bookmarks[domain_code]
                    
                    # Domain level bookmark (level 2)
                    # Use the first page where this domain appears
                    first_page = bookmark.pages[0][0] + 1 if bookmark.pages else 1
                    domain_title = f"{domain_code}"
                    domain_entry = [2, domain_title, first_page]
                    toc.append(domain_entry)
                    
                    # Add forms under this domain as level 3
                    if domain_code in domain_forms:
                        for page_num, form_name in domain_forms[domain_code]:
                            toc.append([3, form_name, page_num + 1])
                
                self.logger.info(f"Created '{self.config.sdtm_bookmark_label}' section with {len(self.domain_bookmarks)} domains")
            
            # Set the table of contents
            if toc:
                doc.set_toc(toc)
                self.logger.info(f"Created {len(toc)} total bookmarks")
                return len(toc)
            else:
                self.logger.info("No forms or domains found, no bookmarks created")
                return 0
                
        except Exception as e:
            self.logger.error(f"Error creating bookmarks: {e}")
            return 0
    
def process_pdf(input_path: str, output_path: Optional[str] = None, 
                config: Optional[StandardizationConfig] = None) -> Dict:
    """
    Convenience function to standardize a PDF.
    
    Args:
        input_path: Path to input PDF
        output_path: Path for output PDF (defaults to input_standardized.pdf)
        config: Optional configuration
        
    Returns:
        Statistics dictionary
    """
    if not output_path:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_standardized.pdf")
    
    standardizer = AnnotationStandardizer(config)
    return standardizer.standardize_pdf(input_path, output_path)


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"Processing: {input_file}")
        stats = process_pdf(input_file, output_file)
        
        print("\n=== Standardization Results ===")
        print(f"Annotations modified: {stats['annotations_modified']}")
        print(f"Headers found: {stats['headers_found']}")
        print(f"Text capitalized: {stats['text_capitalized']}")
        print(f"Rectangles styled: {stats['rectangles_styled']}")
        print(f"Bookmarks created: {stats['bookmarks_created']}")
        
        if stats['errors']:
            print("\n=== Errors ===")
            for error in stats['errors']:
                print(f"  - {error}")
    else:
        print("Usage: python annotation_standardizer.py <input_pdf> [output_pdf]")
