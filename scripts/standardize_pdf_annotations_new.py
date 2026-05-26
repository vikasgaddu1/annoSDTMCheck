"""
Standalone script to standardize PDF annotations using the core module.

This script applies:
- Color standardization (blue, red, green, orange, black)
- Cyan background for all annotations
- Author set to "Geron"
- Font size: 12pt for headers, 10pt for regular text
- Font type: Bold+Italic (hebi)
- Black borders on rectangles

Usage:
    python standardize_pdf_annotations.py input.pdf output.pdf
"""

import sys
import os

# Add parent directory to path to import sdtm_checker modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer, 
    StandardizationConfig
)


def main():
    """Main function for command-line usage."""
    # Check command line arguments
    if len(sys.argv) < 3:
        print("Usage: python standardize_pdf_annotations.py input.pdf output.pdf")
        print("\nThis script standardizes PDF annotations with:")
        print("- Color standardization (font colors mapped to pure colors)")
        print("- Font sizes: 12pt for headers, 10pt for regular text")
        print("- Font type: Bold+Italic")
        print("- Cyan background for all annotations")
        print("- Black borders")
        print("- Author set to 'Geron'")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    
    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print("PDF Annotation Standardizer")
    print(f"{'='*70}")
    print(f"Input:  {input_pdf}")
    print(f"Output: {output_pdf}")
    print()
    
    # Create configuration with all standardization enabled
    config = StandardizationConfig(
        standardize_colors=True,
        standardize_font_size=True,
        standardize_font_type=True,
        default_author="Geron"
    )
    
    # Create standardizer
    standardizer = AnnotationStandardizer(config)
    
    # Run standardization
    print("Processing...")
    try:
        stats = standardizer.standardize_pdf(input_pdf, output_pdf)
        
        # Display results
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}")
        print(f"Annotations processed: {stats['annotations_processed']}")
        print(f"Annotations modified: {stats['annotations_modified']}")
        print(f"Headers found: {stats['headers_found']}")
        
        # Display color statistics if available
        if stats.get('red_annotations', 0) > 0 or stats.get('blue_annotations', 0) > 0:
            print(f"\nColor Distribution:")
            print(f"  Red annotations: {stats.get('red_annotations', 0)}")
            print(f"  Blue annotations: {stats.get('blue_annotations', 0)}")
        
        # Display any errors
        if stats['errors']:
            print(f"\nWarnings/Errors ({len(stats['errors'])}):")
            for i, error in enumerate(stats['errors'][:5], 1):
                print(f"  {i}. {error}")
            if len(stats['errors']) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more")
        
        print(f"\n✓ Standardization complete!")
        print(f"Output saved to: {output_pdf}")
        
    except Exception as e:
        print(f"\nError during standardization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
