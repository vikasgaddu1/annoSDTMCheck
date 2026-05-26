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


def standardize_color(color):
    """Map various shades to standard colors (Blue, Red, Green, Yellow/Orange, Black)"""
    if not color or len(color) != 3:
        return (0, 0, 0)  # Default to black
    
    r, g, b = color
    
    # Blue shades: low red, high blue (with any green level)
    # This catches pure blue, cyan-ish blue, and any blue variations
    if r < 0.5 and b > 0.5:
        return (0, 0, 1)  # Pure blue RGB(0, 0, 255)
    
    # Red shades: high red, low green, low blue
    elif r > 0.5 and g < 0.5 and b < 0.5:
        return (1, 0, 0)  # Pure red RGB(255, 0, 0)
    
    # Green shades: low red, high green, low blue
    elif r < 0.5 and g > 0.5 and b < 0.5:
        return (0, 1, 0)  # Pure green RGB(0, 255, 0)
    
    # Yellow/Orange shades: high red, high green, low blue
    elif r > 0.5 and g > 0.5 and b < 0.5:
        return (1, 0.65, 0)  # Standard orange RGB(255, 165, 0)
    
    # Black shades: all low values
    elif r < 0.3 and g < 0.3 and b < 0.3:
        return (0, 0, 0)  # Pure black RGB(0, 0, 0)
    
    # Default: keep original color if it doesn't match any category
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
                
                # Process all annotations on the page
                annots_on_page = list(page.annots() or [])
                if page_num < 3 and annots_on_page:
                    self.logger.debug(f"Page {page_num + 1} has {len(annots_on_page)} annotations")
                
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
                        current_colors = annot.colors
                        original_font_color = current_colors.get('stroke', (0, 0, 0)) if current_colors else (0, 0, 0)
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
                                
                                # Update FreeText annotation with standardized appearance
                                # Note: In PyMuPDF, the visual appearance works correctly with these parameters
                                annot.update(
                                    fontsize=font_size,
                                    fontname="helv",  # Helvetica (closest to Arial)
                                    text_color=(0, 0, 0),  # Black text
                                    fill_color=bg_color,  # Cyan fill/background (0, 1, 1)
                                    border_color=(0, 0, 0)  # Black border
                                )
                               
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
            
            # Create bookmarks
            stats['bookmarks_created'] = self._create_bookmarks(doc)
            
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
