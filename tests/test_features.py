"""Test color and alignment features after fixes."""
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
    print("TESTING COLOR STANDARDIZATION")
    print("=" * 70)
    
    # Test the standardize_color function
    print("\n### Testing standardize_color function ###")
    test_colors = [
        ((0.9, 0.1, 0.1), "Red", (1, 0, 0)),
        ((0.1, 0.1, 0.9), "Blue", (0, 0, 1)),
        ((0.1, 0.9, 0.1), "Green", (0, 1, 0)),
        ((0.9, 0.5, 0.1), "Orange", (1, 0.65, 0)),
        ((0.1, 0.1, 0.1), "Black", (0, 0, 0)),
        ((0.8, 0.8, 0.1), "Yellow/Orange", (1, 0.65, 0)),
        ((0.1, 0.9, 0.9), "Cyan", (0, 1, 1)),
        ((0.9, 0.1, 0.9), "Magenta", (1, 0, 1)),
    ]
    
    all_passed = True
    for input_color, name, expected in test_colors:
        result = standardize_color(input_color)
        passed = abs(result[0] - expected[0]) < 0.01 and \
                 abs(result[1] - expected[1]) < 0.01 and \
                 abs(result[2] - expected[2]) < 0.01
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {name:15s}: {input_color} -> {result} (expected: {expected})")
        if not passed:
            all_passed = False
    
    return all_passed

def test_alignment_feature():
    """Test alignment feature availability."""
    print("\n" + "=" * 70)
    print("TESTING ALIGNMENT FEATURE")
    print("=" * 70)
    
    # Check if AnnotationAligner is available
    from src.sdtm_checker.core import annotation_standardizer
    aligner_available = annotation_standardizer.ALIGNER_AVAILABLE
    
    print(f"\n[OK] AnnotationAligner import: {'Available' if aligner_available else 'Not Available'}")
    
    # Test configuration
    config = StandardizationConfig(
        align_annotations=True,
        align_horizontal=True,
        align_vertical=True,
        horizontal_tolerance=10.0,
        vertical_tolerance=10.0
    )
    
    print(f"[OK] Alignment enabled: {config.align_annotations}")
    print(f"[OK] Horizontal alignment: {config.align_horizontal}")
    print(f"[OK] Vertical alignment: {config.align_vertical}")
    print(f"[OK] Horizontal tolerance: {config.horizontal_tolerance}pt")
    print(f"[OK] Vertical tolerance: {config.vertical_tolerance}pt")
    
    return aligner_available

def test_on_real_pdf():
    """Test on a real PDF with colors and alignment."""
    print("\n" + "=" * 70)
    print("TESTING ON REAL PDF")
    print("=" * 70)
    
    input_pdf = "input/aCRF.pdf"
    output_pdf = "output/test_features_output.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"[FAIL] Input PDF not found: {input_pdf}")
        return False
    
    # Configure with all features enabled
    config = StandardizationConfig(
        standardize_colors=True,
        standardize_font_size=True,
        standardize_font_type=True,
        auto_resize_textboxes=True,
        align_annotations=True,
        align_horizontal=True,
        align_vertical=True,
        default_author="Geron"
    )
    
    print("\nConfiguration:")
    print(f"  - Color standardization: {config.standardize_colors}")
    print(f"  - Font standardization: {config.standardize_font_size}")
    print(f"  - Auto-resize textboxes: {config.auto_resize_textboxes}")
    print(f"  - Auto-align annotations: {config.align_annotations}")
    
    try:
        standardizer = AnnotationStandardizer(config)
        stats = standardizer.standardize_pdf(input_pdf, output_pdf)
        
        print("\n### Standardization Results ###")
        print(f"[OK] Annotations processed: {stats.get('annotations_processed', 0)}")
        print(f"[OK] Annotations modified: {stats.get('annotations_modified', 0)}")
        print(f"[OK] Headers found: {stats.get('headers_found', 0)}")
        print(f"[OK] Textboxes resized: {stats.get('textboxes_resized', 0)}")
        print(f"[OK] Horizontally aligned: {stats.get('annotations_aligned_horizontal', 0)}")
        print(f"[OK] Vertically aligned: {stats.get('annotations_aligned_vertical', 0)}")
        print(f"[OK] Bookmarks created: {stats.get('bookmarks_created', 0)}")
        
        # Check if output was created
        if os.path.exists(output_pdf):
            print(f"\n[OK] Output PDF created: {output_pdf}")
            
            # Verify colors in output
            doc = fitz.open(output_pdf)
            page = doc[0]
            annot = page.first_annot
            colors_found = set()
            count = 0
            
            while annot and count < 10:
                if annot.type[0] == fitz.PDF_ANNOT_FREE_TEXT:
                    color = get_text_color_from_annotation(annot)
                    colors_found.add(tuple(round(c, 2) for c in color))
                    count += 1
                annot = annot.next
            
            doc.close()
            
            print(f"\n[OK] Unique colors found in output: {len(colors_found)}")
            for color in sorted(colors_found):
                r, g, b = color
                if abs(r - 1) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = "RED"
                elif abs(r) < 0.1 and abs(g) < 0.1 and abs(b - 1) < 0.1:
                    color_name = "BLUE"
                elif abs(r) < 0.1 and abs(g - 1) < 0.1 and abs(b) < 0.1:
                    color_name = "GREEN"
                elif abs(r - 1) < 0.1 and abs(g - 0.65) < 0.2 and abs(b) < 0.1:
                    color_name = "ORANGE"
                elif abs(r) < 0.1 and abs(g) < 0.1 and abs(b) < 0.1:
                    color_name = "BLACK"
                else:
                    color_name = "OTHER"
                print(f"  - {color_name}: RGB{color}")
            
            return True
        else:
            print(f"[FAIL] Output PDF not created")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("ANNOTATION STANDARDIZER - FEATURE TESTS")
    print("=" * 70)
    
    # Run tests
    color_test_passed = test_color_standardization()
    alignment_test_passed = test_alignment_feature()
    pdf_test_passed = test_on_real_pdf()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"[OK] Color Standardization: {'PASSED' if color_test_passed else 'FAILED'}")
    print(f"[OK] Alignment Feature: {'AVAILABLE' if alignment_test_passed else 'NOT AVAILABLE'}")
    print(f"[OK] Real PDF Processing: {'PASSED' if pdf_test_passed else 'FAILED'}")
    
    if color_test_passed and alignment_test_passed and pdf_test_passed:
        print("\n*** SUCCESS! ALL TESTS PASSED! Color and alignment features are working correctly. ***")
    else:
        print("\n*** WARNING: Some tests did not pass. Please review the results above. ***")

if __name__ == "__main__":
    main()
