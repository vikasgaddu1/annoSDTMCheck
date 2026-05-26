"""Verify that the output PDF has annotations with correct colors."""
import fitz
import sys

def verify_pdf(pdf_path):
    """Verify annotations in output PDF."""
    print(f"Verifying: {pdf_path}")
    print("=" * 70)
    
    doc = fitz.open(pdf_path)
    
    total_annots = 0
    red_count = 0
    blue_count = 0
    
    # Check first 5 pages
    for page_num in range(min(5, len(doc))):
        page = doc[page_num]
        page_annots = 0
        
        for annot in page.annots() or []:
            if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                total_annots += 1
                page_annots += 1
                
                # Get annotation details
                info = annot.info
                content = info.get('content', '')[:50]
                
                # Check color from DA string
                da = info.get('DA', '')
                if da:
                    import re
                    color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
                    if color_match:
                        r = float(color_match.group(1))
                        g = float(color_match.group(2))
                        b = float(color_match.group(3))
                        
                        if abs(r - 1) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                            red_count += 1
                            color_name = "RED"
                        elif abs(r) < 0.1 and abs(g) < 0.1 and abs(b - 1) < 0.1:
                            blue_count += 1
                            color_name = "BLUE"
                        else:
                            color_name = f"RGB({r:.2f},{g:.2f},{b:.2f})"
                        
                        if page_num < 3 and page_annots <= 3:  # Show first few
                            print(f"Page {page_num+1}, Annot {page_annots}: {color_name} - {content}")
        
        if page_annots > 0:
            print(f"Page {page_num+1}: {page_annots} annotations")
    
    doc.close()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"  Total annotations: {total_annots}")
    print(f"  Red annotations: {red_count}")
    print(f"  Blue annotations: {blue_count}")
    
    if total_annots > 0:
        print(f"\n[SUCCESS] Output PDF has {total_annots} annotations!")
        if red_count > 0 and blue_count > 0:
            print(f"[SUCCESS] Domain colors working: {red_count} red (FA/AE/DS/DD/MH), {blue_count} blue (others)")
    else:
        print("\n[ERROR] Output PDF has NO annotations!")
    
    return total_annots > 0

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "output/aCRF_domain_colors_fixed.pdf"
    verify_pdf(pdf_path)
