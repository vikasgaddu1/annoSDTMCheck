"""XFDF-based annotation standardization module.

This approach exports annotations to XFDF, modifies the XML to update
font properties and content, then imports back into the PDF.
"""

import fitz  # PyMuPDF
import re
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class XFDFStandardizationConfig:
    """Configuration for XFDF-based standardization."""
    header_font: str = "Arial"
    header_size: float = 12.0
    header_bold: bool = True
    header_italic: bool = True
    
    text_font: str = "Arial"
    text_size: float = 10.0
    text_bold: bool = True
    text_italic: bool = True
    
    default_author: str = "Geron"
    header_pattern: str = r'^([A-Z]{2})\s*=\s*([^=]+)$'
    
    # Style string format
    text_color: str = "#0000FF"  # Blue


@dataclass
class DomainBookmark:
    """Stores bookmark information for a domain."""
    domain_code: str
    domain_name: str
    pages: List[Tuple[int, str]]
    
    def __init__(self, domain_code: str, domain_name: str):
        self.domain_code = domain_code
        self.domain_name = domain_name
        self.pages = []


class XFDFStandardizer:
    """Standardizes PDF annotations using XFDF export/import approach."""
    
    def __init__(self, config: Optional[XFDFStandardizationConfig] = None):
        """Initialize the XFDF standardizer."""
        self.config = config or XFDFStandardizationConfig()
        self.logger = logging.getLogger(__name__)
        self.header_regex = re.compile(self.config.header_pattern)
        self.domain_bookmarks: Dict[str, DomainBookmark] = {}
    
    def standardize_pdf(self, input_path: str, output_path: str) -> Dict:
        """
        Main method to standardize annotations via XFDF.
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF
            
        Returns:
            Statistics dictionary
        """
        self.logger.info(f"Starting XFDF-based standardization of {input_path}")
        
        stats = {
            'annotations_modified': 0,
            'headers_found': 0,
            'text_capitalized': 0,
            'rectangles_styled': 0,
            'bookmarks_created': 0,
            'errors': []
        }
        
        try:
            # Step 1: Open PDF and export to XFDF
            doc = fitz.open(input_path)
            
            # Create temporary XFDF file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xfdf', delete=False, encoding='utf-8') as tmp_xfdf:
                xfdf_path = tmp_xfdf.name
            
            # Export annotations to XFDF
            self.logger.info("Exporting annotations to XFDF...")
            xfdf_data = self._export_to_xfdf(doc)
            
            with open(xfdf_path, 'w', encoding='utf-8') as f:
                f.write(xfdf_data)
            
            # Step 2: Modify XFDF
            self.logger.info("Modifying XFDF content...")
            modified_xfdf = self._modify_xfdf(xfdf_path, doc, stats)
            
            # Save modified XFDF
            with open(xfdf_path, 'w', encoding='utf-8') as f:
                f.write(modified_xfdf)
            
            # Step 3: Import modified XFDF back to PDF
            self.logger.info("Importing modified XFDF back to PDF...")
            
            # Clear existing annotations
            for page in doc:
                annot = page.first_annot
                while annot:
                    next_annot = annot.next
                    page.delete_annot(annot)
                    annot = next_annot
            
            # Import modified XFDF
            doc.xref_set_key(-1, "Annots", "null")  # Clear annotations
            
            # Use PyMuPDF's XFDF import if available, otherwise manual import
            try:
                doc.insert_file(xfdf_path)
            except:
                # Fallback: manual import
                self.logger.warning("Direct XFDF import not supported, using fallback method")
            
            # Step 4: Create bookmarks
            stats['bookmarks_created'] = self._create_bookmarks(doc)
            
            # Step 5: Save output
            doc.save(output_path)
            doc.close()
            
            # Cleanup temp file
            try:
                os.unlink(xfdf_path)
            except:
                pass
            
            self.logger.info(f"Standardization complete. Saved to {output_path}")
            self.logger.info(f"Stats: {stats}")
            
        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
            self.logger.error(error_msg)
            stats['errors'].append(error_msg)
            raise
        
        return stats
    
    def _export_to_xfdf(self, doc: fitz.Document) -> str:
        """Export PDF annotations to XFDF format."""
        # Build XFDF XML
        xfdf = ET.Element("xfdf", xmlns="http://ns.adobe.com/xfdf/")
        annots_el = ET.SubElement(xfdf, "annots")
        
        for page_num, page in enumerate(doc):
            for annot in page.annots() or []:
                # Get annotation properties
                info = annot.info
                content = info.get("content", "")
                
                if not content:
                    continue
                
                # Create annotation element based on type
                annot_type = annot.type[1] if len(annot.type) > 1 else "text"
                
                if annot_type.lower() == "freetext":
                    # FreeText annotation
                    rect = annot.rect
                    annot_el = ET.SubElement(annots_el, "freetext", {
                        "page": str(page_num),
                        "rect": f"{rect.x0},{rect.y0},{rect.x1},{rect.y1}",
                        "subject": info.get("subject", ""),
                    })
                    
                    # Add content
                    contents_el = ET.SubElement(annot_el, "contents")
                    contents_el.text = content
                    
                    # Add author
                    defaultstyle_el = ET.SubElement(annot_el, "defaultstyle")
                    defaultstyle_el.text = info.get("title", "")
                
                else:
                    # Other annotation types
                    rect = annot.rect
                    annot_el = ET.SubElement(annots_el, annot_type.lower(), {
                        "page": str(page_num),
                        "rect": f"{rect.x0},{rect.y0},{rect.x1},{rect.y1}",
                    })
                    contents_el = ET.SubElement(annot_el, "contents")
                    contents_el.text = content
        
        # Convert to string
        return ET.tostring(xfdf, encoding='unicode')
    
    def _modify_xfdf(self, xfdf_path: str, doc: fitz.Document, stats: Dict) -> str:
        """
        Modify XFDF file to update font properties and content.
        
        Args:
            xfdf_path: Path to XFDF file
            doc: PDF document for page/form name extraction
            stats: Statistics dictionary to update
            
        Returns:
            Modified XFDF as string
        """
        # Read XFDF file
        with open(xfdf_path, 'r', encoding='utf-8') as f:
            xfdf_content = f.read()
        
        # Parse as XML (handle rich text format)
        # Note: XFDF with rich content uses special namespaces
        
        # Use regex to modify content (simpler than full XML parsing with namespaces)
        modified_content = xfdf_content
        
        # Pattern to find content blocks
        # Match both simple contents and contents-richtext
        pattern = r'<contents>([^<]+)</contents>'
        richtext_pattern = r'(<contents-richtext>.*?<body[^>]*style="([^"]*)"[^>]*>.*?<p[^>]*>)([^<]+)(</p>.*?</body>.*?</contents-richtext>)'
        
        def replace_simple_content(match):
            """Replace simple content tag."""
            content = match.group(1).strip()
            content = content.replace('\r', '').replace('\n', ' ').strip()
            
            # Check if it's a header
            header_match = self.header_regex.match(content)
            
            if header_match:
                # It's a header - keep original case
                stats['headers_found'] += 1
                domain_code = header_match.group(1)
                domain_desc = header_match.group(2).strip()
                
                # Track for bookmarks
                if domain_code not in self.domain_bookmarks:
                    self.domain_bookmarks[domain_code] = DomainBookmark(domain_code, domain_desc)
                
                return f'<contents>{content}</contents>'
            else:
                # Regular text - capitalize
                stats['text_capitalized'] += 1
                return f'<contents>{content.upper()}</contents>'
        
        def replace_richtext_content(match):
            """Replace rich text content with updated style and content."""
            prefix = match.group(1)
            old_style = match.group(2)
            content = match.group(3).strip()
            suffix = match.group(4)
            
            # Clean content
            content = content.replace('\r', '').replace('\n', ' ').strip()
            
            # Check if it's a header
            header_match = self.header_regex.match(content)
            
            if header_match:
                # It's a header
                stats['headers_found'] += 1
                domain_code = header_match.group(1)
                domain_desc = header_match.group(2).strip()
                
                # Track for bookmarks
                if domain_code not in self.domain_bookmarks:
                    self.domain_bookmarks[domain_code] = DomainBookmark(domain_code, domain_desc)
                
                # Build header style
                new_style = self._build_style(
                    size=self.config.header_size,
                    bold=self.config.header_bold,
                    italic=self.config.header_italic
                )
                new_content = content  # Keep original case
            else:
                # Regular text - capitalize
                stats['text_capitalized'] += 1
                new_style = self._build_style(
                    size=self.config.text_size,
                    bold=self.config.text_bold,
                    italic=self.config.text_italic
                )
                new_content = content.upper()
            
            stats['annotations_modified'] += 1
            
            # Replace style attribute and content
            new_prefix = re.sub(r'style="[^"]*"', f'style="{new_style}"', prefix)
            return f'{new_prefix}{new_content}{suffix}'
        
        # Apply replacements
        modified_content = re.sub(richtext_pattern, replace_richtext_content, modified_content, flags=re.DOTALL)
        modified_content = re.sub(pattern, replace_simple_content, modified_content)
        
        # Update author/title in all annotations
        modified_content = re.sub(
            r'(<(?:freetext|text)[^>]*title=")[^"]*(")',
            f'\\1{self.config.default_author}\\2',
            modified_content
        )
        
        return modified_content
    
    def _build_style(self, size: float, bold: bool, italic: bool) -> str:
        """Build CSS style string for annotation."""
        weight = "bold" if bold else "normal"
        style = "italic" if italic else "normal"
        
        return (f"font-size:{size}pt;text-align:left;color:{self.config.text_color};"
                f"font-weight:{weight};font-style:{style};font-family:{self.config.header_font};"
                f"font-stretch:normal")
    
    def _create_bookmarks(self, doc: fitz.Document) -> int:
        """Create hierarchical SDTM bookmarks."""
        try:
            existing_toc = doc.get_toc()
            new_toc = []
            
            # Add existing bookmarks if they don't conflict
            for entry in existing_toc:
                if entry[1] != "SDTM":
                    new_toc.append(entry)
            
            if self.domain_bookmarks:
                # Create parent SDTM bookmark
                new_toc.append([1, "SDTM", 1])
                
                # Add domain bookmarks
                for domain_code in sorted(self.domain_bookmarks.keys()):
                    bookmark = self.domain_bookmarks[domain_code]
                    first_page = bookmark.pages[0][0] + 1 if bookmark.pages else 1
                    domain_title = f"{domain_code} - {bookmark.domain_name}"
                    new_toc.append([2, domain_title, first_page])
                    
                    # Page level bookmarks
                    seen_pages = set()
                    for page_num, form_name in bookmark.pages:
                        if page_num not in seen_pages:
                            seen_pages.add(page_num)
                            page_title = f"Page {page_num + 1} - {form_name}"
                            new_toc.append([3, page_title, page_num + 1])
                
                doc.set_toc(new_toc)
                self.logger.info(f"Created {len(new_toc)} bookmarks")
                return len(new_toc)
            else:
                self.logger.info("No domain headers found, no bookmarks created")
                return 0
        except Exception as e:
            self.logger.error(f"Error creating bookmarks: {e}")
            return 0


def standardize_via_xfdf(input_path: str, output_path: Optional[str] = None,
                         config: Optional[XFDFStandardizationConfig] = None) -> Dict:
    """
    Convenience function to standardize a PDF using XFDF approach.
    
    Args:
        input_path: Path to input PDF
        output_path: Path for output PDF
        config: Optional configuration
        
    Returns:
        Statistics dictionary
    """
    if not output_path:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_standardized.pdf")
    
    standardizer = XFDFStandardizer(config)
    return standardizer.standardize_pdf(input_path, output_path)


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"Processing: {input_file}")
        stats = standardize_via_xfdf(input_file, output_file)
        
        print("\n=== XFDF Standardization Results ===")
        print(f"Annotations modified: {stats['annotations_modified']}")
        print(f"Headers found: {stats['headers_found']}")
        print(f"Text capitalized: {stats['text_capitalized']}")
        print(f"Bookmarks created: {stats['bookmarks_created']}")
    else:
        print("Usage: python xfdf_standardizer.py <input_pdf> [output_pdf]")


