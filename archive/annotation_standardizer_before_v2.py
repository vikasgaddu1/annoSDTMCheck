"""
PDF Annotation Standardizer with Complete Fix
- Font color standardization 
- Font size (12pt headers, 10pt regular)
- Font type (Bold+Italic)
- Uses delete-and-recreate approach to fix appearance stream issues
"""
import logging
import re
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

# Try to import optional features
try:
    from .text_dimension_calculator import TextDimensionCalculator
    RESIZER_AVAILABLE = True
except ImportError:
    RESIZER_AVAILABLE = False
    
try:
    from .annotation_aligner import AnnotationAligner
    ALIGNER_AVAILABLE = True
except ImportError:
    ALIGNER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_header_annotation(text: str) -> bool:
    """Check if annotation is a header (XX = Label format)."""
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
    Extract text color from annotation's DA string or appearance stream.
    
    For FreeText annotations, the text color might be stored in:
    1. The DA (Default Appearance) string
    2. The appearance stream
    
    Returns:
        Tuple of (r, g, b) in 0-1 scale, defaults to (0, 0, 0) if not found
    """
    try:
        # Get DA string from annotation info
        da = annot.info.get('DA', '')
        
        # If not in info, try getting from annotation dictionary
        if not da:
            try:
                xref = annot.xref
                da = annot.parent.parent.xref_get_key(xref, 'DA')
                if da:
                    da = da[1]  # Get the value part
            except:
                pass
        
        # Parse DA string for color information
        if da:
            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if color_match:
                r = float(color_match.group(1))
                g = float(color_match.group(2))
                b = float(color_match.group(3))
                
                # If DA has black (0 0 0) or white (1 1 1), it might be a default
                # Try appearance stream for actual color
                if (r, g, b) not in [(0, 0, 0), (1, 1, 1)]:
                    logger.debug(f"Extracted text color from DA: RGB({int(r*255)}, {int(g*255)}, {int(b*255)})")
                    return (r, g, b)
        
        # Try extracting from appearance stream
        # This is necessary for PDFs where the actual color is only in the appearance
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
                        # Find colors that are NOT cyan background
                        rg_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', ap_text)
                        if rg_matches:
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


def standardize_color(color: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Map various shades to standard colors using normalization algorithm.
    
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
    
    # Normalize by max intensity to handle different brightness levels
    r_norm = r / max_intensity if max_intensity > 0 else 0
    g_norm = g / max_intensity if max_intensity > 0 else 0
    b_norm = b / max_intensity if max_intensity > 0 else 0
    
    # Blue detection: blue is dominant, red and green are much lower
    if b_norm > 0.9 and r_norm < 0.3 and g_norm < 0.3:
        return (0, 0, 1)  # Pure blue RGB(0, 0, 255)
    
    # Red detection: red is dominant, green and blue are much lower
    elif r_norm > 0.9 and g_norm < 0.3 and b_norm < 0.3:
        return (1, 0, 0)  # Pure red RGB(255, 0, 0)
    
    # Green detection: green is dominant, red and blue are much lower
    elif g_norm > 0.9 and r_norm < 0.3 and b_norm < 0.3:
        return (0, 1, 0)  # Pure green RGB(0, 255, 0)
    
    # Orange/Yellow detection: both red and green high, blue low
    elif r_norm > 0.7 and g_norm > 0.5 and b_norm < 0.3:
        return (1, 0.65, 0)  # Standard orange RGB(255, 165, 0)
    
    # Cyan detection: blue and green high, red low
    elif b_norm > 0.8 and g_norm > 0.8 and r_norm < 0.2:
        return (0, 1, 1)  # Cyan RGB(0, 255, 255)
    
    # Magenta detection: red and blue high, green low
    elif r_norm > 0.8 and b_norm > 0.8 and g_norm < 0.2:
        return (1, 0, 1)  # Magenta RGB(255, 0, 255)
    
    # If no clear match, check absolute thresholds as fallback
    
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
    # Font settings
    header_font: str = "hebo"  # Helvetica-Bold (changed from hebi to ensure bold shows)
    header_size: int = 12
    text_font: str = "hebo"  # Helvetica-Bold (changed from hebi to ensure bold shows)
    text_size: int = 10
    
    # Colors
    background_color: Tuple[float, float, float] = (0, 1, 1)  # Cyan RGB(0, 255, 255)
    border_color: Tuple[float, float, float] = (0, 0, 0)  # Black
    default_author: str = "Geron"
    
    # Processing options
    standardize_colors: bool = True
    standardize_font_size: bool = True
    standardize_font_type: bool = True
    
    # Bookmark labels
    form_bookmark_label: str = "Form_bookmarks"
    sdtm_bookmark_label: str = "SDTM"
    
    # Auto-resize textboxes (not implemented in delete-recreate approach yet)
    auto_resize_textboxes: bool = False
    resize_max_width_expansion: float = 200.0
    resize_max_height_expansion: float = 300.0
    
    # Auto-align annotations (not implemented in delete-recreate approach yet)
    align_annotations: bool = False
    align_horizontal: bool = True
    align_vertical: bool = True
    horizontal_tolerance: float = 10.0
    vertical_tolerance: float = 10.0
    

class AnnotationStandardizer:
    """
    Standardizes PDF annotations using delete-and-recreate approach.
    Fixes: font color, font size, and font type.
    """
    
    def __init__(self, config: Optional[StandardizationConfig] = None):
        """Initialize the standardizer with optional configuration."""
        self.config = config or StandardizationConfig()
        self.logger = logging.getLogger(__name__)
        
    def standardize_pdf(self, input_path: str, output_path: str) -> Dict:
        """
        Main method to standardize annotations.
        Uses delete-and-recreate approach for reliable color/font control.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path where standardized PDF will be saved
            
        Returns:
            Dictionary containing statistics about modifications
        """
        self.logger.info(f"Starting standardization of {input_path}")
        
        # Initialize statistics
        stats = {
            'annotations_processed': 0,
            'annotations_modified': 0,
            'headers_found': 0,
            'text_capitalized': 0,  # For GUI compatibility
            'rectangles_styled': 0,
            'bookmarks_created': 0,  # TODO: Implement bookmark creation
            'red_annotations': 0,
            'blue_annotations': 0,
            'errors': [],
            # Optional stats for advanced features
            'textboxes_checked': 0,
            'textboxes_resized': 0,
            'annotations_aligned_horizontal': 0,
            'annotations_aligned_vertical': 0
        }
        
        try:
            # Open the PDF document
            doc = fitz.open(input_path)
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # STEP 1: Collect all FreeText annotation data
                annots_data = []
                annot = page.first_annot
                
                while annot:
                    if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                        try:
                            content = annot.info.get('content', '').strip()
                            
                            # Extract current color
                            original_color = get_text_color_from_annotation(annot)
                            
                            # Standardize color if enabled
                            if self.config.standardize_colors:
                                font_color = standardize_color(original_color)
                            else:
                                font_color = original_color
                            
                            # Determine font size
                            is_header = is_header_annotation(content)
                            if self.config.standardize_font_size:
                                font_size = self.config.header_size if is_header else self.config.text_size
                            else:
                                # Try to keep original size
                                font_size = self.config.text_size
                            
                            # Determine font name
                            if self.config.standardize_font_type:
                                font_name = self.config.header_font if is_header else self.config.text_font
                            else:
                                font_name = "helv"  # Default
                            
                            # Store annotation data
                            annots_data.append({
                                'rect': annot.rect,
                                'content': content,
                                'color': font_color,
                                'fontsize': font_size,
                                'fontname': font_name,
                                'author': self.config.default_author,
                                'is_header': is_header
                            })
                            
                            stats['annotations_processed'] += 1
                            
                            # Track color statistics
                            r, g, b = font_color
                            if abs(r - 1) < 0.01 and abs(g) < 0.01 and abs(b) < 0.01:
                                stats['red_annotations'] += 1
                            elif abs(r) < 0.01 and abs(g) < 0.01 and abs(b - 1) < 0.01:
                                stats['blue_annotations'] += 1
                            
                            if is_header:
                                stats['headers_found'] += 1
                                
                        except Exception as e:
                            self.logger.warning(f"Error collecting annotation data: {e}")
                            stats['errors'].append(str(e))
                    
                    annot = annot.next
                
                # STEP 2: Delete all FreeText annotations
                if annots_data:
                    self.logger.debug(f"Page {page_num + 1}: Deleting {len(annots_data)} annotations")
                    annot = page.first_annot
                    while annot:
                        next_annot = annot.next
                        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                            page.delete_annot(annot)
                        annot = next_annot
                    
                    # STEP 3: Recreate annotations with correct attributes
                    self.logger.debug(f"Page {page_num + 1}: Recreating {len(annots_data)} annotations")
                    for annot_data in annots_data:
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
                            
                            # Fix bold font in appearance stream (PyMuPDF limitation workaround)
                            fix_bold_font_in_appearance_stream(
                                new_annot, 
                                annot_data['fontname'], 
                                annot_data['fontsize']
                            )
                            
                            stats['annotations_modified'] += 1
                            
                        except Exception as e:
                            self.logger.warning(f"Error recreating annotation: {e}")
                            stats['errors'].append(str(e))
                
                # Handle non-FreeText annotations (rectangles, etc.)
                annot = page.first_annot
                while annot:
                    if annot.type[0] != fitz.PDF_ANNOT_FREE_TEXT:
                        try:
                            # Update author
                            annot.set_info(title=self.config.default_author)
                            
                            # Handle rectangles, circles, etc.
                            if annot.type[0] not in [fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_STRIKEOUT, 
                                                    fitz.PDF_ANNOT_CARET, fitz.PDF_ANNOT_HIGHLIGHT,
                                                    fitz.PDF_ANNOT_UNDERLINE]:
                                try:
                                    annot.set_border(width=2, style="S")
                                    annot.set_colors(stroke=self.config.border_color, fill=self.config.background_color)
                                except:
                                    pass
                        except Exception as e:
                            self.logger.debug(f"Could not update non-FreeText annotation: {e}")
                    
                    annot = annot.next
            
            # Save the modified PDF
            self.logger.info(f"Saving to {output_path}")
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            self.logger.info(f"Standardization complete: {stats['annotations_modified']} annotations modified")
            
        except Exception as e:
            self.logger.error(f"Error during standardization: {e}")
            stats['errors'].append(str(e))
        
        return stats


def fix_bold_font_in_appearance_stream(annot: fitz.Annot, fontname: str = "hebo", 
                                      fontsize: int = 12) -> bool:
    """
    Fix bold font in annotation by modifying the appearance stream directly.
    PyMuPDF doesn't always apply bold fonts correctly, so we need to fix it manually.
    
    Args:
        annot: The annotation object
        fontname: Font name (hebo for Helvetica-Bold, hebi for Helvetica-BoldOblique, etc.)
        fontsize: Font size
        
    Returns:
        True if successfully fixed, False otherwise
    """
    try:
        # Get the annotation's xref
        xref = annot.xref
        if xref <= 0:
            return False
            
        doc = annot.parent.parent  # Get document from annotation
        
        # Get text color for DA string
        try:
            text_color = annot.colors.get('stroke', (0, 0, 0))
            if text_color is None:
                text_color = (0, 0, 0)
            r, g, b = text_color
        except:
            r, g, b = 0, 0, 0
        
        # Map abbreviated font names to full PostScript names for DA string
        font_ps_map = {
            'hebo': 'Helv-Bold',      # Helvetica-Bold
            'hebi': 'Helv-BoldOblique',  # Helvetica-BoldOblique (Bold+Italic)
            'tibo': 'TiBo',          # Times-Bold
            'tibi': 'TiBi',          # Times-BoldItalic
            'cobo': 'CoBo',          # Courier-Bold
        }
        
        ps_font = font_ps_map.get(fontname.lower(), fontname.upper())
        
        # Set the DA string with proper font
        da_string = f"{r:.3f} {g:.3f} {b:.3f} rg /{ps_font} {fontsize} Tf"
        doc.xref_set_key(xref, "DA", f"({da_string})")
        
        # Fix the appearance stream
        ap_dict = doc.xref_get_key(xref, "AP")
        if ap_dict[0] == "dict":
            n_xref = doc.xref_get_key(xref, "AP/N")
            if n_xref[0] == "xref":
                ap_xref = int(n_xref[1].split()[0])
                
                # Get the current appearance stream
                stream = doc.xref_stream(ap_xref)
                if stream:
                    stream_str = stream.decode('utf-8', errors='ignore')
                    
                    # Map abbreviated font names to proper bold names in stream
                    font_map = {
                        'hebo': 'HeBo',  # Helvetica-Bold
                        'hebi': 'HeBi',  # Helvetica-BoldOblique  
                        'tibo': 'TiBo',  # Times-Bold
                        'tibi': 'TiBi',  # Times-BoldItalic
                        'cobo': 'CoBo',  # Courier-Bold
                        'helv': 'Helv',  # Keep regular Helvetica
                        'heit': 'HeIt',  # Helvetica-Oblique
                    }
                    
                    mapped_font = font_map.get(fontname.lower(), fontname.upper())
                    
                    # Replace font references in the stream
                    new_stream = re.sub(
                        r'/\w+\s+(\d+(?:\.\d+)?)\s+Tf',
                        f'/{mapped_font} \\1 Tf',
                        stream_str
                    )
                    
                    # Update the stream if modified
                    if new_stream != stream_str:
                        doc.update_stream(ap_xref, new_stream.encode('utf-8'))
                        return True
                        
    except Exception as e:
        logging.debug(f"Could not fix bold font in appearance stream: {e}")
        
    return False


# Convenience function for standalone usage
def standardize_pdf(input_path: str, output_path: str, config: Optional[StandardizationConfig] = None) -> Dict:
    """
    Convenience function to standardize a PDF.
    
    Args:
        input_path: Path to input PDF
        output_path: Path for output PDF
        config: Optional configuration object
        
    Returns:
        Statistics dictionary
    """
    standardizer = AnnotationStandardizer(config)
    return standardizer.standardize_pdf(input_path, output_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python annotation_standardizer_new.py input.pdf output.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Use default configuration (all fixes enabled)
    config = StandardizationConfig()
    
    # Run standardization
    stats = standardize_pdf(input_file, output_file, config)
    
    # Print results
    print(f"\nStandardization Complete:")
    print(f"  Annotations processed: {stats['annotations_processed']}")
    print(f"  Annotations modified: {stats['annotations_modified']}")
    print(f"  Headers found: {stats['headers_found']}")
    print(f"  Red annotations: {stats['red_annotations']}")
    print(f"  Blue annotations: {stats['blue_annotations']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
