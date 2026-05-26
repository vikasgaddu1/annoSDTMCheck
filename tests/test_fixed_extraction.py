"""Test if the fixed color extraction is working."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import fitz
import re


def get_text_color_fixed(annot):
    """Fixed version of color extraction."""
    # First try DA string
    da = annot.info.get('DA', '')
    if da:
        color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
        if color_match:
            r = float(color_match.group(1))
            g = float(color_match.group(2))
            b = float(color_match.group(3))
            if not (r == 0 and g == 0 and b == 0) and not (r == 1 and g == 1 and b == 1):
                return (r, g, b)
    
    # Try to get from appearance stream - FIXED VERSION
    try:
        xref = annot.xref
        doc = annot.parent.parent
        if xref > 0:
            ap_dict = doc.xref_get_key(xref, "AP")
            if ap_dict[0] == "dict":
                n_xref = doc.xref_get_key(xref, "AP/N")
                if n_xref[0] == "xref":
                    stream_xref = int(n_xref[1].split()[0])
                    stream = doc.xref_stream(stream_xref)
                    if stream:
                        stream_text = stream.decode('utf-8', errors='ignore')
                        # Look for text color within BT...ET block
                        bt_match = re.search(r'BT.*?ET', stream_text, re.DOTALL)
                        if bt_match:
                            text_block = bt_match.group(0)
                            # Find color commands within text block
                            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', text_block)
                            if color_match:
                                r = float(color_match.group(1))
                                g = float(color_match.group(2))
                                b = float(color_match.group(3))
                                print(f"    Found text color in BT block: RGB({r}, {g}, {b})")
                                return (r, g, b)
                        else:
                            print("    No BT...ET block found")
    except Exception as e:
        print(f"    Error: {e}")
    
    # Try stroke color as fallback
    colors = annot.colors
    if colors and 'stroke' in colors and colors['stroke']:
        stroke = colors['stroke']
        if stroke != (0, 0, 0) and stroke != (1, 1, 1):
            print(f"    Using stroke color: {stroke}")
            return stroke
    
    print("    Defaulting to black")
    return (0, 0, 0)


def main():
    print("TESTING FIXED COLOR EXTRACTION")
    print("=" * 50)
    
    input_pdf = "tests/incorrect.pdf"
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found")
        return
    
    doc = fitz.open(input_pdf)
    page = doc[0]
    annot = page.first_annot
    
    count = 0
    while annot and count < 3:
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            count += 1
            content = annot.info.get('content', '')[:30]
            print(f"\nAnnotation {count}: '{content}...'")
            
            # Test fixed extraction
            color = get_text_color_fixed(annot)
            r, g, b = int(color[0]*255), int(color[1]*255), int(color[2]*255)
            print(f"  Final color: RGB({r}, {g}, {b})")
            
            if r == 0 and g == 0 and b == 255:
                print("  [SUCCESS] Correctly extracted BLUE text color!")
            elif r == 0 and g == 255 and b == 255:
                print("  [PROBLEM] Still extracting CYAN background color!")
        
        annot = annot.next
    
    doc.close()


if __name__ == "__main__":
    main()
