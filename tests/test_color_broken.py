"""Test if font color standardization is broken."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer, 
    StandardizationConfig,
    standardize_color,
    get_text_color_from_annotation
)
import fitz


def test_color_standardization():
    """Test color standardization functionality."""
    
    print("=" * 70)
    print("TESTING FONT COLOR STANDARDIZATION")
    print("=" * 70)
    
    # First test the color standardization function directly
    print("\n### Testing standardize_color function ###")
    test_colors = [
        ((0.9, 0.1, 0.1), "Red"),
        ((0.1, 0.1, 0.9), "Blue"),
        ((0.1, 0.9, 0.1), "Green"),
        ((0.9, 0.5, 0.1), "Orange"),
        ((0.1, 0.1, 0.1), "Black"),
    ]
    
    for color, name in test_colors:
        standardized = standardize_color(color)
        print(f"{name}: {color} -> {standardized}")
    
    # Now test on actual PDF
    print("\n### Testing on actual PDF ###")
    
    input_pdf = "input/aCRF.pdf"
    if not os.path.exists(input_pdf):
        # Create test PDF with colored annotations
        print("Creating test PDF with colored annotations...")
        doc = fitz.open()
        page = doc.new_page()
        
        # Add annotations with different colors
        colors = [
            ((0.9, 0.1, 0.2), "Red annotation"),
            ((0.1, 0.2, 0.9), "Blue annotation"),
            ((0.1, 0.9, 0.2), "Green annotation"),
        ]
        
        y = 100
        for color, text in colors:
            annot = page.add_freetext_annot(
                fitz.Rect(100, y, 400, y+30),
                text,
                fontsize=12,
                text_color=color,
                fill_color=(1, 1, 1)
            )
            annot.update()
            y += 50
        
        input_pdf = "output/test_colors_input.pdf"
        doc.save(input_pdf)
        doc.close()
        print(f"Created test PDF: {input_pdf}")
    
    # Check original colors
    print("\n### Original Colors ###")
    doc = fitz.open(input_pdf)
    page = doc[0]
    annot = page.first_annot
    count = 0
    original_colors = []
    while annot and count < 5:
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            color = get_text_color_from_annotation(annot)
            content = annot.info.get('content', '')[:30]
            print(f"Annot {count+1}: Color={color}, Content='{content}...'")
            original_colors.append(color)
            count += 1
        annot = annot.next
    doc.close()
    
    # Process with color standardization
    config = StandardizationConfig(
        standardize_colors=True,
        standardize_font_size=True,
        standardize_font_type=True,
        default_author="Geron"
    )
    
    standardizer = AnnotationStandardizer(config)
    output_pdf = "output/test_colors_output.pdf"
    stats = standardizer.standardize_pdf(input_pdf, output_pdf)
    
    print(f"\nProcessing stats: {stats}")
    print(f"Red annotations: {stats.get('red_annotations', 0)}")
    print(f"Blue annotations: {stats.get('blue_annotations', 0)}")
    
    # Check processed colors
    print("\n### After Standardization ###")
    doc = fitz.open(output_pdf)
    page = doc[0]
    annot = page.first_annot
    count = 0
    while annot and count < 5:
        if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
            color = get_text_color_from_annotation(annot)
            content = annot.info.get('content', '')[:30]
            
            # Check if it's a standard color
            is_red = abs(color[0] - 1) < 0.01 and abs(color[1]) < 0.01 and abs(color[2]) < 0.01
            is_blue = abs(color[0]) < 0.01 and abs(color[1]) < 0.01 and abs(color[2] - 1) < 0.01
            is_green = abs(color[0]) < 0.01 and abs(color[1] - 1) < 0.01 and abs(color[2]) < 0.01
            is_black = abs(color[0]) < 0.01 and abs(color[1]) < 0.01 and abs(color[2]) < 0.01
            
            color_name = "Unknown"
            if is_red: color_name = "RED"
            elif is_blue: color_name = "BLUE"
            elif is_green: color_name = "GREEN"
            elif is_black: color_name = "BLACK"
            
            print(f"Annot {count+1}: Color={color} [{color_name}], Content='{content}...'")
            count += 1
        annot = annot.next
    doc.close()
    
    print("\n" + "=" * 70)
    print("Check if colors are being standardized properly!")


if __name__ == "__main__":
    test_color_standardization()
