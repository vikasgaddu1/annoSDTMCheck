"""
Simple XFDF modifier for standardizing annotation fonts and content.

This script:
1. Reads an XFDF file
2. Modifies font properties in <contents-richtext> sections  
3. Capitalizes non-header text
4. Updates author to "Geron"
5. Saves modified XFDF

You can then import the modified XFDF back into your PDF using Adobe Acrobat.
"""

import re
import sys
from pathlib import Path


class XFDFModifier:
    """Modifies XFDF files to standardize annotations."""
    
    def __init__(self):
        self.header_pattern = re.compile(r'^([A-Z]{2})\s*=\s*([^=]+)$')
        self.stats = {
            'headers_found': 0,
            'text_capitalized': 0,
            'annotations_modified': 0,
            'authors_changed': 0
        }
    
    def modify_xfdf(self, input_xfdf: str, output_xfdf: str):
        """
        Modify XFDF file to standardize annotations.
        
        Args:
            input_xfdf: Path to input XFDF file
            output_xfdf: Path to save modified XFDF
        """
        print(f"Reading: {input_xfdf}")
        
        # Read XFDF content
        with open(input_xfdf, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Modify content
        modified = self._process_content(content)
        
        # Save
        with open(output_xfdf, 'w', encoding='utf-8') as f:
            f.write(modified)
        
        print(f"\nSaved to: {output_xfdf}")
        print("\nStatistics:")
        print(f"  Annotations modified: {self.stats['annotations_modified']}")
        print(f"  Headers found: {self.stats['headers_found']}")
        print(f"  Text capitalized: {self.stats['text_capitalized']}")
        print(f"  Authors changed: {self.stats['authors_changed']}")
        
        return modified
    
    def _process_content(self, content: str) -> str:
        """Process XFDF content to apply standardization."""
        
        # Pattern to match contents-richtext blocks
        richtext_pattern = (
            r'(<contents-richtext>\s*'
            r'<body[^>]*?style="([^"]*)"[^>]*?>\s*'
            r'<p[^>]*?>)'
            r'([^<]+)'
            r'(</p>\s*</body>\s*</contents-richtext>)'
        )
        
        def replace_richtext(match):
            """Replace rich text annotation."""
            prefix = match.group(1)
            old_style = match.group(2)
            text = match.group(3)
            suffix = match.group(4)
            
            # Clean text
            text = text.replace('\r', '').replace('\n', ' ').strip()
            
            # Check if header
            is_header = self.header_pattern.match(text)
            
            if is_header:
                # Header: 12pt Arial bold italic
                new_style = ("font-size:12.0pt;text-align:left;color:#0000FF;"
                           "font-weight:bold;font-style:italic;font-family:Arial;font-stretch:normal")
                new_text = text  # Keep original case
                self.stats['headers_found'] += 1
            else:
                # Regular text: 10pt Arial bold italic, UPPERCASE
                new_style = ("font-size:10.0pt;text-align:left;color:#0000FF;"
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
        
        # Change author to "Geron" in all annotations
        # Pattern for author field in FreeText annotations
        original_modified = modified
        modified = re.sub(
            r'(<(?:freetext|text)[^>]*?)T\(([^)]+)\)',
            r'\1T(Geron)',
            modified,
            flags=re.IGNORECASE
        )
        
        # Count author changes
        self.stats['authors_changed'] = len(re.findall(r'T\(Geron\)', modified))
        
        return modified


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("XFDF Annotation Standardizer")
        print("=" * 60)
        print("\nUsage:")
        print("  python xfdf_modifier.py <input.xfdf> [output.xfdf]")
        print("\nExample:")
        print("  python xfdf_modifier.py acrf.xfdf acrf_standardized.xfdf")
        print("\nThis will:")
        print("  • Change fonts to Arial 12pt (headers) and 10pt (text)")
        print("  • Apply bold italic styling")
        print("  • Capitalize non-header text to UPPERCASE")
        print("  • Change all authors to 'Geron'")
        print("\nTo import modified XFDF:")
        print("  1. Open your PDF in Adobe Acrobat")
        print("  2. Go to Tools → Edit PDF → More → Import Comments")
        print("  3. Select the modified XFDF file")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.xfdf', '_standardized.xfdf')
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        return
    
    print("=" * 60)
    print("XFDF Annotation Standardizer")
    print("=" * 60)
    
    modifier = XFDFModifier()
    modifier.modify_xfdf(input_file, output_file)
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Open your PDF in Adobe Acrobat")
    print("2. Delete existing annotations (optional but recommended)")
    print("3. Go to: Tools → Edit PDF → More → Import Comments")
    print(f"4. Select: {output_file}")
    print("5. Save your PDF")
    print("\nAll annotations will now have standardized formatting!")


if __name__ == "__main__":
    main()


