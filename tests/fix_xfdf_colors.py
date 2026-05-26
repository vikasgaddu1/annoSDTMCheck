"""
XFDF Color Fixer - Assigns correct colors based on SDTM domains.

This script:
1. Reads an XFDF file exported from PDF
2. Identifies SDTM domains in annotation content
3. Assigns appropriate colors (Blue for most, Red for FA/AE/DS/DD/MH)
4. Standardizes fonts to Arial Bold Italic
5. Saves modified XFDF for re-import

Author: Assistant
Date: 2025
"""

import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

class XFDFColorFixer:
    """Fixes colors in XFDF files based on SDTM domain logic."""
    
    def __init__(self):
        self.header_pattern = re.compile(r'^([A-Z]{2})\s*=\s*([^=]+)$')
        
        # Domains that should have RED text
        self.red_domains = ['FA', 'AE', 'DS', 'DD', 'MH']
        
        # All other domains get BLUE text
        self.blue_domains = ['CM', 'DM', 'EX', 'SV', 'EG', 'IE', 'LB', 'PE', 'QS', 
                            'SC', 'TS', 'TV', 'VS', 'CE', 'DA', 'DV', 'HO', 'MB', 
                            'MO', 'RP', 'RS', 'TU', 'UR']
        
        self.stats = {
            'headers_found': 0,
            'text_capitalized': 0,
            'annotations_modified': 0,
            'red_annotations': 0,
            'blue_annotations': 0,
            'authors_changed': 0
        }
    
    def get_domain_from_text(self, text):
        """Extract SDTM domain from annotation text."""
        # Check if it's a header
        header_match = self.header_pattern.match(text)
        if header_match:
            return header_match.group(1)
        
        # Look for domain codes in the text
        text_upper = text.upper()
        
        # Check for patterns like "FA =" or "FACAT" or "in SUPPFA"
        for domain in self.red_domains + self.blue_domains:
            if f"{domain} =" in text_upper or \
               f"{domain}CAT" in text_upper or \
               f"SUPP{domain}" in text_upper or \
               text_upper.startswith(domain):
                return domain
        
        return None
    
    def get_color_for_domain(self, domain):
        """Get the appropriate color for a domain."""
        if domain in self.red_domains:
            self.stats['red_annotations'] += 1
            return "#FF0000"  # Red
        else:
            self.stats['blue_annotations'] += 1
            return "#0000FF"  # Blue
    
    def fix_xfdf_colors(self, input_xfdf: str, output_xfdf: str):
        """
        Fix colors in XFDF file based on SDTM domain logic.
        
        Args:
            input_xfdf: Path to input XFDF file
            output_xfdf: Path to save modified XFDF
        """
        print(f"Reading: {input_xfdf}")
        
        # Read XFDF content
        with open(input_xfdf, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process content
        modified = self._process_content(content)
        
        # Save
        with open(output_xfdf, 'w', encoding='utf-8') as f:
            f.write(modified)
        
        print(f"\nSaved to: {output_xfdf}")
        print("\nStatistics:")
        print(f"  Annotations modified: {self.stats['annotations_modified']}")
        print(f"  Headers found: {self.stats['headers_found']}")
        print(f"  Text capitalized: {self.stats['text_capitalized']}")
        print(f"  Blue annotations: {self.stats['blue_annotations']}")
        print(f"  Red annotations: {self.stats['red_annotations']}")
        print(f"  Authors changed: {self.stats['authors_changed']}")
        
        return modified
    
    def _process_content(self, content: str) -> str:
        """Process XFDF content to fix colors and styling."""
        
        # Pattern to match contents-richtext blocks
        richtext_pattern = (
            r'(<contents-richtext>\s*'
            r'<body[^>]*?style="([^"]*)"[^>]*?>\s*'
            r'<p[^>]*?>)'
            r'([^<]+)'
            r'(</p>\s*</body>\s*</contents-richtext>)'
        )
        
        def replace_richtext(match):
            """Replace rich text annotation with correct color."""
            prefix = match.group(1)
            old_style = match.group(2)
            text = match.group(3)
            suffix = match.group(4)
            
            # Clean text
            text = text.replace('\r', '').replace('\n', ' ').strip()
            
            # Get domain
            domain = self.get_domain_from_text(text)
            
            # Check if header
            is_header = self.header_pattern.match(text)
            
            # Determine color based on domain
            if domain:
                color = self.get_color_for_domain(domain)
            else:
                # Default to blue if no domain detected
                color = "#0000FF"
                self.stats['blue_annotations'] += 1
            
            if is_header:
                # Header: 12pt Arial bold italic with appropriate color
                new_style = (f"font-size:12.0pt;text-align:left;color:{color};"
                           "font-weight:bold;font-style:italic;font-family:Arial;font-stretch:normal")
                new_text = text  # Keep original case for headers
                self.stats['headers_found'] += 1
            else:
                # Regular text: 10pt Arial bold italic with appropriate color, UPPERCASE
                new_style = (f"font-size:10.0pt;text-align:left;color:{color};"
                           "font-weight:bold;font-style:italic;font-family:Arial;font-stretch:normal")
                new_text = text.upper()
                self.stats['text_capitalized'] += 1
            
            self.stats['annotations_modified'] += 1
            
            # Replace style in prefix
            new_prefix = re.sub(r'style="[^"]*"', f'style="{new_style}"', prefix)
            
            return f'{new_prefix}{new_text}{suffix}'
        
        # Apply rich text replacements
        modified = re.sub(richtext_pattern, replace_richtext, content, flags=re.DOTALL)
        
        # Also handle simple contents tags (for non-rich annotations)
        def replace_simple_content(match):
            """Replace simple content."""
            text = match.group(1).strip().replace('\r', '').replace('\n', ' ').strip()
            
            # For simple content, we can't change color easily
            # but we can still capitalize text
            if self.header_pattern.match(text):
                self.stats['headers_found'] += 1
                return f'<contents>{text}</contents>'
            else:
                self.stats['text_capitalized'] += 1
                return f'<contents>{text.upper()}</contents>'
        
        modified = re.sub(
            r'<contents>([^<]+)</contents>',
            replace_simple_content,
            modified
        )
        
        # Fix color attributes in freetext elements
        # Pattern: color="#RRGGBB" or color="0.r 0.g 0.b"
        def fix_color_attribute(match):
            """Fix color attribute based on annotation content."""
            full_element = match.group(0)
            
            # Extract the contents to determine domain
            contents_match = re.search(r'<contents>([^<]+)</contents>', full_element)
            if contents_match:
                text = contents_match.group(1).strip()
                domain = self.get_domain_from_text(text)
                
                if domain:
                    if domain in self.red_domains:
                        # Replace with red color
                        full_element = re.sub(
                            r'color="[^"]*"',
                            'color="1.0 0.0 0.0"',
                            full_element
                        )
                    else:
                        # Replace with blue color
                        full_element = re.sub(
                            r'color="[^"]*"',
                            'color="0.0 0.0 1.0"',
                            full_element
                        )
            
            return full_element
        
        # Fix colors in freetext elements
        modified = re.sub(
            r'<freetext[^>]*>.*?</freetext>',
            fix_color_attribute,
            modified,
            flags=re.DOTALL
        )
        
        # Change author to "Geron" in all annotations
        modified = re.sub(
            r'title="[^"]*"',
            'title="Geron"',
            modified,
            flags=re.IGNORECASE
        )
        
        # Count author changes
        self.stats['authors_changed'] = len(re.findall(r'title="Geron"', modified))
        
        return modified


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("XFDF Color Fixer for SDTM Annotations")
        print("=" * 60)
        print("\nUsage:")
        print("  python fix_xfdf_colors.py <input.xfdf> [output.xfdf]")
        print("\nExample:")
        print("  python fix_xfdf_colors.py acrf.xfdf acrf_fixed_colors.xfdf")
        print("\nThis will:")
        print("  • Fix colors based on SDTM domain:")
        print("    - RED for: FA, AE, DS, DD, MH domains")
        print("    - BLUE for: All other domains")
        print("  • Change fonts to Arial Bold Italic")
        print("  • Apply 12pt for headers, 10pt for text")
        print("  • Capitalize non-header text to UPPERCASE")
        print("  • Change all authors to 'Geron'")
        print("\nTo import modified XFDF:")
        print("  1. Open your PDF in Adobe Acrobat")
        print("  2. Go to Tools → Comments → Import Data File")
        print("  3. Select the modified XFDF file")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.xfdf', '_fixed_colors.xfdf')
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        return
    
    print("=" * 60)
    print("XFDF Color Fixer")
    print("=" * 60)
    
    fixer = XFDFColorFixer()
    fixer.fix_xfdf_colors(input_file, output_file)
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Color Assignment Logic")
    print("=" * 60)
    print("RED text domains: FA, AE, DS, DD, MH")
    print("BLUE text domains: All others (CM, DM, EX, SV, etc.)")
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Open your PDF in Adobe Acrobat Pro")
    print("2. Delete existing annotations (optional but recommended)")
    print("3. Go to: Tools → Comments → Import Data File")
    print(f"4. Select: {output_file}")
    print("5. Save your PDF")
    print("\nAll annotations will now have correct colors based on domain!")


if __name__ == "__main__":
    main()
