"""
Standalone script to standardize PDF annotations with color correction and formatting.

This script applies:
- Color standardization (blue, red, green, orange, black)
- Cyan background for all annotations
- Author set to "Geron"
- Font size: 12pt for headers, 10pt for regular text
- Black borders on rectangles

Usage:
    python standardize_pdf_annotations.py input.pdf output.pdf
"""

import fitz  # PyMuPDF
import re
import os
import sys


def is_header_annotation(text):
    """Check if annotation follows the pattern 'XX = Label' (e.g., 'DM = Demographics')

    Returns True only if:
    - Exactly 2 uppercase letters on the left
    - Followed by = sign
    - Right side does NOT contain quotes (single or double)
    """
    if not text:
        return False

    text = text.strip()

    # Pattern: exactly 2 uppercase letters, followed by space(s), equals sign, space(s), and text
    pattern = r'^[A-Z]{2}\s*=\s*.+'

    if not re.match(pattern, text):
        return False

    # Check if right side of equals contains quotes (not a header if it does)
    if '=' in text:
        right_side = text.split('=', 1)[1].strip()
        if "'" in right_side or '"' in right_side:
            return False

    return True


def standardize_color(color):
    """Map various shades to standard colors (Blue, Red, Green, Yellow/Orange, Black)"""
    if not color or len(color) != 3:
        return (0, 0, 0)  # Default to black

    r, g, b = color

    # Blue shades: low red, high blue (with any green level)
    # This catches pure blue, cyan-ish blue, and any blue variations
    if r < 0.5 and b > 0.5:
        return (0, 0, 1)  # Pure blue RGB(0, 0, 255)

    # Red shades: high red, low green, low blue
    elif r > 0.5 and g < 0.5 and b < 0.5:
        return (1, 0, 0)  # Pure red RGB(255, 0, 0)

    # Green shades: low red, high green, low blue
    elif r < 0.5 and g > 0.5 and b < 0.5:
        return (0, 1, 0)  # Pure green RGB(0, 255, 0)

    # Yellow/Orange shades: high red, high green, low blue
    elif r > 0.5 and g > 0.5 and b < 0.5:
        return (1, 0.65, 0)  # Standard orange RGB(255, 165, 0)

    # Black shades: all low values
    elif r < 0.3 and g < 0.3 and b < 0.3:
        return (0, 0, 0)  # Pure black RGB(0, 0, 0)

    # Default: keep original color if it doesn't match any category
    return color


def inspect_pdf_annotations(pdf_path):
    """Inspect all annotations in the PDF to understand their types"""
    doc = fitz.open(pdf_path)
    print(f"PDF has {len(doc)} pages\n")
    
    annotation_types = {}
    sample_count = 0
    max_samples = 5
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        annots = page.annots()
        
        if annots:
            for annot in annots:
                annot_type = annot.type[1] if isinstance(annot.type, tuple) else str(annot.type)
                
                if annot_type not in annotation_types:
                    annotation_types[annot_type] = 0
                annotation_types[annot_type] += 1
                
                # Show some samples
                if sample_count < max_samples:
                    print(f"Sample {sample_count + 1}:")
                    print(f"  Page: {page_num + 1}")
                    print(f"  Type: {annot_type} (ID: {annot.type[0]})")
                    print(f"  Content: {annot.info.get('content', 'N/A')[:80]}")
                    print(f"  Author: {annot.info.get('title', 'N/A')}")
                    print(f"  Colors - stroke: {annot.colors.get('stroke')}, fill: {annot.colors.get('fill')}")
                    print("-" * 70)
                    sample_count += 1
    
    print("\n=== ANNOTATION TYPE SUMMARY ===")
    for annot_type, count in sorted(annotation_types.items()):
        print(f"{annot_type}: {count}")
    
    doc.close()
    return annotation_types


def standardize_annotations(input_path, output_path):
    """Standardize all annotations in the PDF according to requirements"""
    doc = fitz.open(input_path)
    
    modifications_count = 0
    errors_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        annots_list = []
        
        # Collect all annotations first
        annot = page.first_annot
        while annot:
            annots_list.append({
                'annot': annot,
                'type': annot.type,
                'info': annot.info.copy(),
                'rect': annot.rect,
                'colors': annot.colors.copy() if annot.colors else {},
                'border': annot.border if hasattr(annot, 'border') else None,
                'opacity': annot.opacity if hasattr(annot, 'opacity') else 1.0
            })
            annot = annot.next
        
        if annots_list:
            print(f"Processing page {page_num + 1} ({len(annots_list)} annotations)...")
            
            for annot_data in annots_list:
                try:
                    annot = annot_data['annot']
                    annot_type = annot.type[0] if isinstance(annot.type, tuple) else annot.type
                    content = annot_data['info'].get('content', '')
                    
                    # Determine font size based on content
                    font_size = 12 if is_header_annotation(content) else 10

                    # Get current font color and standardize it
                    current_colors = annot_data['colors']
                    original_font_color = current_colors.get('stroke', (0, 0, 0))
                    font_color = standardize_color(original_font_color)

                    # Use cyan as background color for all annotations
                    bg_color = (0, 1, 1)  # Cyan RGB(0, 255, 255)

                    # Update author
                    annot.set_info(title="Geron")

                    # Handle FreeText annotations specially (can use update method)
                    if annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                        try:
                            # For FreeText, border_color in update() controls the border
                            annot.update(
                                fontsize=font_size,
                                fontname="helv",  # Helvetica (closest to Arial)
                                text_color=font_color,
                                fill_color=bg_color,
                                border_color=(0, 0, 0)  # Black border
                            )
                            modifications_count += 1
                        except Exception as e:
                            print(f"    Warning: Could not fully update FreeText annotation: {e}")
                            modifications_count += 1
                    else:
                        # For other annotation types, set colors and border where applicable
                        try:
                            # Set border first
                            annot.set_border(width=2, style="S")
                        except:
                            pass

                        try:
                            # Try to set colors - stroke controls border color
                            annot.set_colors(stroke=(0, 0, 0), fill=bg_color)
                        except:
                            try:
                                annot.set_colors(stroke=(0, 0, 0))
                            except:
                                pass

                        modifications_count += 1
                    
                    # Update the annotation
                    annot.update()
                    
                except Exception as e:
                    errors_count += 1
                    print(f"    Error processing annotation: {e}")
                    continue
    
    # Save the modified PDF
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    
    print(f"\n{'='*70}")
    print(f"Successfully modified {modifications_count} annotations")
    if errors_count > 0:
        print(f"WARNING: {errors_count} annotations had errors")
    print(f"Output saved to: {output_path}")
    print(f"{'='*70}")


def main():
    """Main entry point for the script"""
    if len(sys.argv) < 2:
        print("Usage: python standardize_pdf_annotations.py <input.pdf> [output.pdf]")
        print("\nStandardizes PDF annotations with:")
        print("  - Color correction (blue, red, green, orange, black)")
        print("  - Cyan backgrounds")
        print("  - Author set to 'Geron'")
        print("  - Font sizes: 12pt for headers, 10pt for text")
        print("  - Black borders on rectangles")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Auto-generate output filename
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_standardized{ext}"
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("PDF ANNOTATION STANDARDIZATION TOOL")
    print("=" * 70)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print("=" * 70)
    
    # Optional: inspect annotations first
    if "--inspect" in sys.argv:
        print("\n" + "=" * 70)
        print("INSPECTING PDF ANNOTATIONS")
        print("=" * 70)
        inspect_pdf_annotations(input_file)
    
    print("\n" + "=" * 70)
    print("STANDARDIZING ANNOTATIONS")
    print("=" * 70)
    standardize_annotations(input_file, output_file)


if __name__ == "__main__":
    main()

