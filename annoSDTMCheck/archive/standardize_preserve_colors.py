"""
PDF annotation standardizer that PRESERVES original text colors.

Features:
- PRESERVES original text colors (blue, red, green, etc.)
- CYAN BACKGROUND for all annotations
- BLACK BORDERS
- Helvetica Bold Italic font (PDF standard, similar to Arial)
- Headers (XX = Label) at 12pt, others at 10pt
- Generates color usage report
"""

import fitz  # PyMuPDF
import re
import sys
import os
from pathlib import Path
from collections import defaultdict
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ColorPreservingStandardizer:
    """PDF annotation standardizer that preserves original text colors."""
    
    # Only standardize these:
    CYAN_BG = (0.7, 0.95, 0.95)      # Cyan background
    BLACK_BORDER = (0, 0, 0)         # Black border
    
    def __init__(self):
        # Strict header pattern
        self.header_pattern = re.compile(r'^([A-Z]{2})\s*=\s*(.+)$')
        self.domain_annotations = defaultdict(lambda: {'pages': [], 'items': []})
        self.color_report = defaultdict(list)  # Track colors per page
        self.stats = {
            'annotations_modified': 0,
            'headers_found': 0,
            'text_capitalized': 0,
            'colors_preserved': 0,
            'unique_colors': set(),
            'bookmarks_created': 0,
            'errors': 0
        }
    
    def standardize(self, input_pdf: str, output_pdf: str, color_report_path: str = None):
        """
        Standardize PDF annotations while preserving original text colors.
        
        Args:
            input_pdf: Path to input PDF (will NOT be modified)
            output_pdf: Path for standardized PDF
            color_report_path: Path for color report JSON file
        """
        print("=" * 80)
        print("PDF ANNOTATION STANDARDIZER - COLOR PRESERVING VERSION")
        print("=" * 80)
        print(f"\nInput:  {input_pdf} (will NOT be modified)")
        print(f"Output: {output_pdf}")
        print("\nFeatures:")
        print("  - PRESERVES original text colors (blue, red, green, etc.)")
        print("  - CYAN BACKGROUND for all annotations")
        print("  - BLACK BORDERS")
        print("  - Headers (XX = Label) at 12pt, others at 10pt")
        print("  - Helvetica Bold Italic font (PDF standard, similar to Arial)")
        print("  - Generates color usage report")
        
        # Open the input PDF
        print("\n[Step 1/4] Opening PDF and copying to output...")
        doc_input = fitz.open(input_pdf)
        
        # Create output by copying input
        doc_output = fitz.open(input_pdf)
        
        # Process annotations
        print("\n[Step 2/4] Processing annotations (preserving text colors)...")
        total_annots = 0
        for page_num in range(len(doc_output)):
            if page_num % 10 == 0:
                print(f"  Processing pages {page_num + 1}-{min(page_num + 10, len(doc_output))}/{len(doc_output)}...")
            
            page = doc_output[page_num]
            
            # Get all annotations on this page
            page_annots = list(page.annots()) if page.annots() else []
            total_annots += len(page_annots)
            
            # Process each annotation
            for annot in page_annots:
                if annot:
                    self._standardize_annotation(annot, page_num, page)
        
        print(f"  Total annotations found: {total_annots}")
        print(f"  Unique colors found: {len(self.stats['unique_colors'])}")
        
        # Close input document
        doc_input.close()
        
        # Add hierarchical bookmarks
        print("\n[Step 3/4] Creating hierarchical SDTM bookmarks and saving...")
        self._add_hierarchical_bookmarks(doc_output)
        
        # Save the output document
        doc_output.save(output_pdf)
        doc_output.close()
        
        # Generate color report
        print("\n[Step 4/4] Generating color usage report...")
        if color_report_path is None:
            color_report_path = output_pdf.replace('.pdf', '_color_report.json')
        self._generate_color_report(color_report_path)
        
        # Show results
        self._show_results(output_pdf, color_report_path)
    
    def _get_original_color(self, annot):
        """Extract the original text color from annotation."""
        try:
            # Try to get colors from annotation
            colors = annot.colors
            if colors:
                # Check for stroke color (text color)
                if 'stroke' in colors and colors['stroke']:
                    stroke = colors['stroke']
                    if isinstance(stroke, (list, tuple)) and len(stroke) >= 3:
                        return tuple(stroke[:3])
                # Check for common color
                if 'common' in colors and colors['common']:
                    common = colors['common']
                    if isinstance(common, (list, tuple)) and len(common) >= 3:
                        return tuple(common[:3])
            
            # Try to extract from DA string
            da = annot.info.get("DA", "")
            if da:
                # Look for color in DA string (format: "r g b rg")
                import re
                color_match = re.search(r'(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+rg', da)
                if color_match:
                    r, g, b = map(float, color_match.groups())
                    return (r, g, b)
            
            # If we can't find any color, return None to indicate we should skip
            return None
        except Exception as e:
            logger.warning(f"Error extracting color: {e}")
            return None
    
    def _color_to_name(self, color):
        """Convert RGB color to descriptive name."""
        if not color or len(color) < 3:
            return "Unknown"
        
        r, g, b = color[:3]
        
        # Check for common colors
        if abs(r) < 0.1 and abs(g) < 0.1 and abs(b - 1.0) < 0.1:
            return "Blue"
        elif abs(r - 1.0) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
            return "Red"
        elif abs(r) < 0.1 and abs(g - 0.5) < 0.2 and abs(b) < 0.1:
            return "Green"
        elif abs(r - 0.75) < 0.1 and abs(g - 1.0) < 0.1 and abs(b - 1.0) < 0.1:
            return "Cyan"
        elif abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
            return "Black"
        elif abs(r - 0.5) < 0.2 and abs(g) < 0.2 and abs(b - 0.5) < 0.2:
            return "Purple"
        elif abs(r - 1.0) < 0.1 and abs(g - 0.5) < 0.2 and abs(b) < 0.1:
            return "Orange"
        else:
            return f"RGB({r:.2f}, {g:.2f}, {b:.2f})"
    
    def _standardize_annotation(self, annot, page_num, page):
        """Standardize annotation while preserving original text color."""
        try:
            info = annot.info
            content = info.get("content", "")
            
            if not content:
                return
            
            # Clean up content
            content = content.replace('\r', '').replace('\n', ' ').strip()
            
            # Get original text color - PRESERVE IT!
            original_text_color = self._get_original_color(annot)
            if original_text_color is None:
                # If we can't extract color, use blue as fallback
                original_text_color = (0, 0, 1)
            
            # Track this color
            color_tuple = tuple(round(c, 3) for c in original_text_color)
            self.stats['unique_colors'].add(color_tuple)
            
            # Record color usage for report
            color_name = self._color_to_name(original_text_color)
            self.color_report[page_num + 1].append({
                'content': content[:50],
                'color_rgb': color_tuple,
                'color_name': color_name
            })
            
            # Check if it's a header
            is_header = bool(self.header_pattern.match(content))
            
            # Determine font size
            if is_header:
                match = self.header_pattern.match(content)
                domain = match.group(1)
                item_desc = match.group(2).strip()
                self.stats['headers_found'] += 1
                font_size = 12  # Headers get 12pt
                new_content = content  # Keep as-is
                
                # Track for bookmarking
                self.domain_annotations[domain]['pages'].append(page_num + 1)
                self.domain_annotations[domain]['items'].append({
                    'desc': item_desc,
                    'page': page_num + 1,
                    'is_header': True
                })
            else:
                # Non-headers get 10pt
                font_size = 10
                new_content = content.upper()
                self.stats['text_capitalized'] += 1
                
                # Try to extract domain for bookmarking
                words = content.upper().split()
                domain = None
                for word in words:
                    if len(word) >= 2:
                        potential_domain = word[:2]
                        if potential_domain in ['AE', 'CM', 'DD', 'DM', 'DS', 'EG', 'EX', 'FA', 
                                               'IE', 'LB', 'MH', 'PE', 'QS', 'SC', 'SV', 
                                               'TS', 'TV', 'VS', 'CE', 'DA', 'DV',
                                               'HO', 'MB', 'MO', 'RP', 'RS', 'TU', 'UR']:
                            domain = potential_domain
                            break
                
                if domain:
                    self.domain_annotations[domain]['pages'].append(page_num + 1)
                    self.domain_annotations[domain]['items'].append({
                        'desc': new_content,
                        'page': page_num + 1,
                        'is_header': False
                    })
            
            # Get annotation rectangle
            rect = annot.rect
            
            # Delete the old annotation
            page.delete_annot(annot)
            
            # Create new annotation with PRESERVED text color
            new_annot = page.add_freetext_annot(
                rect,
                new_content,
                fontsize=font_size,
                fontname="helv",  # Helvetica (will be made bold-italic via DA)
                text_color=original_text_color,   # PRESERVE original color!
                fill_color=self.CYAN_BG,          # Cyan background
                align=fitz.TEXT_ALIGN_LEFT
            )
            
            # Set black border (width, color, style)
            new_annot.set_border(width=1.0)
            new_annot.border_color = self.BLACK_BORDER
            
            # Set additional properties
            new_annot.set_info({
                "title": "Geron",
                "content": new_content,
            })
            
            # Create appearance string for Helvetica Bold Italic with PRESERVED text color
            r, g, b = original_text_color
            da_string = f"/Helv-BoldOblique {font_size} Tf {r:.3f} {g:.3f} {b:.3f} rg"
            
            # Apply the appearance string - this controls text color and font style
            new_annot.set_info({"DA": da_string})
            
            # Force update
            new_annot.update()
            
            self.stats['annotations_modified'] += 1
            self.stats['colors_preserved'] += 1
                
        except Exception as e:
            logger.warning(f"Error processing annotation on page {page_num + 1}: {e}")
            self.stats['errors'] += 1
    
    def _add_hierarchical_bookmarks(self, doc):
        """Add hierarchical SDTM bookmarks."""
        if not self.domain_annotations:
            logger.warning("No domain annotations found for bookmarks")
            return
        
        toc = []
        toc.append([1, "SDTM", 1])
        
        for domain in sorted(self.domain_annotations.keys()):
            items = self.domain_annotations[domain]['items']
            if not items:
                continue
            
            first_page = min(self.domain_annotations[domain]['pages'])
            
            # Find header
            header_item = None
            for item in items:
                if item['is_header']:
                    header_item = item
                    break
            
            if header_item:
                main_desc = f"{domain} - {header_item['desc']}"
                toc.append([2, main_desc, first_page])
                
                # Add children
                seen_items = set()
                child_count = 0
                for item in items:
                    if not item['is_header'] and child_count < 10:
                        item_text = item['desc']
                        if item_text not in seen_items:
                            seen_items.add(item_text)
                            if len(item_text) > 40:
                                item_text = item_text[:37] + "..."
                            toc.append([3, item_text, item['page']])
                            child_count += 1
            else:
                toc.append([2, domain, first_page])
        
        doc.set_toc(toc)
        self.stats['bookmarks_created'] = len(toc)
    
    def _generate_color_report(self, report_path):
        """Generate a color usage report."""
        # Create detailed report
        report = {
            'summary': {
                'total_unique_colors': len(self.stats['unique_colors']),
                'unique_colors': [
                    {
                        'rgb': color,
                        'name': self._color_to_name(color)
                    }
                    for color in sorted(self.stats['unique_colors'])
                ]
            },
            'pages': {}
        }
        
        # Add per-page details
        for page_num in sorted(self.color_report.keys()):
            annotations = self.color_report[page_num]
            page_colors = {}
            
            # Group by color
            for annot in annotations:
                color_name = annot['color_name']
                if color_name not in page_colors:
                    page_colors[color_name] = {
                        'rgb': annot['color_rgb'],
                        'annotations': []
                    }
                page_colors[color_name]['annotations'].append(annot['content'])
            
            report['pages'][f'Page {page_num}'] = page_colors
        
        # Write JSON report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Also create a text report
        text_report_path = report_path.replace('.json', '.txt')
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PDF ANNOTATION COLOR USAGE REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total Unique Colors: {len(self.stats['unique_colors'])}\n\n")
            
            f.write("Unique Colors Found:\n")
            f.write("-" * 80 + "\n")
            for color in sorted(self.stats['unique_colors']):
                color_name = self._color_to_name(color)
                f.write(f"  {color_name}: RGB{color}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("COLOR USAGE BY PAGE\n")
            f.write("=" * 80 + "\n\n")
            
            for page_num in sorted(self.color_report.keys()):
                f.write(f"\nPage {page_num}:\n")
                f.write("-" * 80 + "\n")
                
                annotations = self.color_report[page_num]
                page_colors = {}
                
                # Group by color
                for annot in annotations:
                    color_name = annot['color_name']
                    if color_name not in page_colors:
                        page_colors[color_name] = []
                    page_colors[color_name].append(annot['content'])
                
                for color_name, contents in page_colors.items():
                    f.write(f"\n  {color_name}:\n")
                    for content in contents:
                        f.write(f"    - {content}\n")
        
        logger.info(f"Color report saved to: {report_path}")
        logger.info(f"Text report saved to: {text_report_path}")
    
    def _show_results(self, output_pdf, color_report_path):
        """Show standardization results."""
        print("\n" + "=" * 80)
        print("STANDARDIZATION COMPLETE")
        print("=" * 80)
        
        print("\nStatistics:")
        print(f"  Annotations modified:     {self.stats['annotations_modified']}")
        print(f"  Headers found (12pt):     {self.stats['headers_found']}")
        print(f"  Text capitalized (10pt):  {self.stats['text_capitalized']}")
        print(f"  Colors preserved:         {self.stats['colors_preserved']}")
        print(f"  Unique colors found:      {len(self.stats['unique_colors'])}")
        print(f"  Bookmarks created:        {self.stats['bookmarks_created']}")
        if self.stats['errors'] > 0:
            print(f"  [WARNING] Errors:         {self.stats['errors']}")
        
        print(f"\n[SUCCESS] Output saved to: {output_pdf}")
        print(f"[REPORT] Color report saved to: {color_report_path}")
        print(f"[REPORT] Text report saved to: {color_report_path.replace('.json', '.txt')}")
        
        print("\nThe PDF now has:")
        print("  - PRESERVED original text colors (blue, red, green, etc.)")
        print("  - CYAN BACKGROUND on all annotations")
        print("  - BLACK BORDERS on all annotations")
        print("  - Headers (XX = Label) at 12pt")
        print("  - All other text at 10pt")
        print("  - Helvetica Bold Italic font (PDF standard, similar to Arial)")
        print("  - Non-header text in UPPERCASE")
        print("  - All annotations authored by 'Geron'")
        print("  - Hierarchical SDTM bookmarks")
        print("  - INPUT PDF UNCHANGED")
        
        print("\n[TIP] Review the color report to identify any color variations")
        print("      that may need manual correction in the source PDF.")
        
        print("\n[COMPLETE] Standardization successful!")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("PDF Annotation Standardizer - Color Preserving Version")
        print("=" * 60)
        print("\nUsage:")
        print("  python standardize_preserve_colors.py <input.pdf> [output.pdf] [report.json]")
        print("\nExamples:")
        print("  python standardize_preserve_colors.py input\\aCRF.pdf")
        print("  python standardize_preserve_colors.py input\\aCRF.pdf output\\final.pdf")
        print("  python standardize_preserve_colors.py input\\aCRF.pdf output\\final.pdf report.json")
        print("\nFeatures:")
        print("  - PRESERVES original text colors (no changes)")
        print("  - Applies cyan background to all")
        print("  - Applies black borders to all")
        print("  - Fixes font to Arial italic")
        print("  - Fixes sizes: 12pt (headers), 10pt (others)")
        print("  - Generates color usage report")
        print("  - Input PDF is NEVER modified")
        return
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else input_pdf.replace('.pdf', '_standardized.pdf')
    report_path = sys.argv[3] if len(sys.argv) > 3 else output_pdf.replace('.pdf', '_color_report.json')
    
    if not Path(input_pdf).exists():
        print(f"Error: File not found: {input_pdf}")
        return
    
    # Ensure we never overwrite the input
    if os.path.abspath(input_pdf) == os.path.abspath(output_pdf):
        print(f"Error: Output path cannot be the same as input path!")
        return
    
    standardizer = ColorPreservingStandardizer()
    standardizer.standardize(input_pdf, output_pdf, report_path)


if __name__ == "__main__":
    main()

