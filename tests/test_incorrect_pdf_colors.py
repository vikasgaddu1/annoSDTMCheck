"""Test color standardization on the problematic incorrect.pdf file."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer, 
    StandardizationConfig,
    get_text_color_from_annotation
)
import fitz


def main():
    print("=" * 70)
    print("TESTING COLOR STANDARDIZATION ON INCORRECT.PDF")
    print("=" * 70)
    
    input_pdf = "tests/incorrect.pdf"
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found")
        return
    
    # Check original colors
    print("\n### ORIGINAL COLORS IN INCORRECT.PDF ###")
    doc = fitz.open(input_pdf)
    page = doc[0]
    annot = page.first_annot
    
    annot_count = 0
    while annot:
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            annot_count += 1
            color = get_text_color_from_annotation(annot)
            content = annot.info.get('content', '')[:40]
            
            # Convert to RGB 0-255 for easier reading
            r, g, b = int(color[0]*255), int(color[1]*255), int(color[2]*255)
            print(f"Annot {annot_count}: RGB({r}, {g}, {b}) - '{content}...'")
        annot = annot.next
    doc.close()
    
    # Process with standardization
    print("\n### PROCESSING WITH STANDARDIZATION ###")
    config = StandardizationConfig(
        standardize_colors=True,
        standardize_font_size=True,
        standardize_font_type=True,
        default_author="Geron"
    )
    
    standardizer = AnnotationStandardizer(config)
    output_pdf = "output/incorrect_standardized.pdf"
    stats = standardizer.standardize_pdf(input_pdf, output_pdf)
    
    print(f"\nStats:")
    print(f"  Annotations processed: {stats['annotations_processed']}")
    print(f"  Annotations modified: {stats['annotations_modified']}")
    print(f"  Red annotations: {stats.get('red_annotations', 0)}")
    print(f"  Blue annotations: {stats.get('blue_annotations', 0)}")
    
    # Check standardized colors
    print("\n### COLORS AFTER STANDARDIZATION ###")
    doc = fitz.open(output_pdf)
    page = doc[0]
    annot = page.first_annot
    
    annot_count = 0
    red_count = 0
    blue_count = 0
    black_count = 0
    
    while annot:
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            annot_count += 1
            color = get_text_color_from_annotation(annot)
            content = annot.info.get('content', '')[:40]
            
            # Convert to RGB 0-255 for easier reading
            r, g, b = int(color[0]*255), int(color[1]*255), int(color[2]*255)
            
            # Identify standardized colors
            color_name = "OTHER"
            if r == 255 and g == 0 and b == 0:
                color_name = "RED"
                red_count += 1
            elif r == 0 and g == 0 and b == 255:
                color_name = "BLUE"
                blue_count += 1
            elif r == 0 and g == 0 and b == 0:
                color_name = "BLACK"
                black_count += 1
            elif r == 0 and g == 255 and b == 0:
                color_name = "GREEN"
            
            print(f"Annot {annot_count}: RGB({r}, {g}, {b}) [{color_name}] - '{content}...'")
        annot = annot.next
    doc.close()
    
    print("\n### SUMMARY ###")
    print(f"Total annotations: {annot_count}")
    print(f"Red: {red_count}")
    print(f"Blue: {blue_count}")
    print(f"Black: {black_count}")
    
    if red_count > 0 or blue_count > 0:
        print("\n[SUCCESS] Colors are being standardized!")
    else:
        print("\n[PROBLEM] Colors might not be standardizing correctly")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
