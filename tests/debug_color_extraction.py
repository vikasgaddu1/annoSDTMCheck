"""Debug color extraction from incorrect.pdf."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import fitz
import re


def debug_annotation_colors():
    """Debug what colors are in the annotations."""
    
    print("=" * 70)
    print("DEBUGGING COLOR EXTRACTION FROM INCORRECT.PDF")
    print("=" * 70)
    
    input_pdf = "tests/incorrect.pdf"
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found")
        return
    
    doc = fitz.open(input_pdf)
    page = doc[0]
    annot = page.first_annot
    
    annot_count = 0
    while annot and annot_count < 3:  # Check first 3 annotations
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            annot_count += 1
            content = annot.info.get('content', '')[:40]
            print(f"\n### Annotation {annot_count}: '{content}...' ###")
            
            # Check DA string
            da = annot.info.get('DA', '')
            print(f"DA string: '{da}'")
            if da:
                color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
                if color_match:
                    r, g, b = float(color_match.group(1)), float(color_match.group(2)), float(color_match.group(3))
                    print(f"  Color from DA: RGB({r}, {g}, {b})")
            
            # Check colors property
            colors = annot.colors
            print(f"Colors property: {colors}")
            if colors:
                if 'stroke' in colors:
                    print(f"  Stroke color: {colors['stroke']}")
                if 'fill' in colors:
                    print(f"  Fill color: {colors['fill']}")
            
            # Check appearance stream
            xref = annot.xref
            if xref > 0:
                ap_dict = doc.xref_get_key(xref, "AP")
                if ap_dict[0] == "dict":
                    n_xref = doc.xref_get_key(xref, "AP/N")
                    if n_xref[0] == "xref":
                        stream_xref = int(n_xref[1].split()[0])
                        stream = doc.xref_stream(stream_xref)
                        if stream:
                            stream_text = stream.decode('utf-8', errors='ignore')
                            print(f"Appearance stream (first 500 chars):")
                            print(stream_text[:500])
                            
                            # Find all color commands
                            rg_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', stream_text)
                            print(f"\nAll 'rg' (text color) commands found:")
                            for match in rg_matches:
                                r, g, b = float(match[0]), float(match[1]), float(match[2])
                                print(f"  RGB({r}, {g}, {b})")
                            
                            RG_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+RG', stream_text)
                            if RG_matches:
                                print(f"\nAll 'RG' (stroke color) commands found:")
                                for match in RG_matches:
                                    r, g, b = float(match[0]), float(match[1]), float(match[2])
                                    print(f"  RGB({r}, {g}, {b})")
        
        annot = annot.next
    
    doc.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    debug_annotation_colors()
