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


def get_text_color_from_annotation(annot):
    """
    Extract text color from annotation's DA string or appearance stream.
    
    For FreeText annotations, the text color is stored in the DA string,
    not in annot.colors['stroke']. If DA doesn't have color info, 
    we extract it from the appearance stream.
    
    Returns:
        Tuple of (r, g, b) in 0-1 scale, defaults to (0, 0, 0) if not found
    """
    try:
        # Get Default Appearance string
        da = annot.info.get('DA', '')
        
        if not da:
            # Try getting it from the annotation dictionary
            try:
                xref = annot.xref
                da = annot.parent.parent.xref_get_key(xref, 'DA')
                if da:
                    da = da[1]  # Get the value part
            except:
                pass
        
        if da:
            # Look for RGB color pattern: three numbers followed by 'rg' (text color)
            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if color_match:
                r = float(color_match.group(1))
                g = float(color_match.group(2))
                b = float(color_match.group(3))
                
                # If DA has black (0 0 0) or white (1 1 1), try appearance stream instead
                # Some PDFs have incorrect DA but correct appearance stream
                if (r, g, b) not in [(0, 0, 0), (1, 1, 1)]:
                    return (r, g, b)
        
        # Try extracting from appearance stream as it may have the actual color
        try:
            xref = annot.xref
            if xref > 0:
                doc = annot.parent.parent
                annot_dict = doc.xref_object(xref)
                
                # Look for appearance stream reference
                ap_match = re.search(r'/N\s+(\d+)\s+\d+\s+R', annot_dict)
                if ap_match:
                    ap_xref = int(ap_match.group(1))
                    ap_stream = doc.xref_stream(ap_xref)
                    
                    if ap_stream:
                        ap_text = ap_stream.decode('latin-1', errors='ignore')
                        
                        # Look for text color operators (rg = RGB for text/fills)
                        rg_matches = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', ap_text)
                        if rg_matches:
                            # Find the text color (usually the second one, first is background)
                            for r_str, g_str, b_str in rg_matches:
                                r = float(r_str)
                                g = float(g_str)
                                b = float(b_str)
                                
                                # Skip cyan background color and white
                                if (r, g, b) not in [(0, 1, 1), (1, 1, 1), (0.75, 1, 1), (0.85, 1, 1)]:
                                    return (r, g, b)
        except Exception as e:
            pass
        
        # Fallback: try to get from annot.colors (but skip cyan)
        current_colors = annot.colors
        if current_colors and 'stroke' in current_colors:
            color = current_colors['stroke']
            # Skip cyan as it's the background color
            if color not in [(0, 1, 1), (0.75, 1, 1), (0.85, 1, 1)]:
                return color
        
        # Default: black
        return (0, 0, 0)
        
    except Exception as e:
        return (0, 0, 0)


def standardize_color(color):
    """
    Map various shades to standard colors (Blue, Red, Green, Yellow/Orange, Black).
    
    Uses a robust algorithm that identifies the dominant color channel and 
    standardizes based on relative intensities rather than fixed thresholds.
    """
    if not color or len(color) != 3:
        return (0, 0, 0)  # Default to black
    
    r, g, b = color
    
    # Handle black/very dark colors first
    max_intensity = max(r, g, b)
    if max_intensity < 0.15:  # Very dark (RGB < 38 for any component)
        return (0, 0, 0)  # Pure black RGB(0, 0, 0)
    
    # Find the dominant channel(s)
    # Normalize by max intensity to handle different brightness levels
    r_norm = r / max_intensity if max_intensity > 0 else 0
    g_norm = g / max_intensity if max_intensity > 0 else 0
    b_norm = b / max_intensity if max_intensity > 0 else 0
    
    # Blue detection: blue is dominant, red and green are much lower
    if b_norm > 0.9 and r_norm < 0.3 and g_norm < 0.3:
        return (0, 0, 1)  # Pure blue RGB(0, 0, 255)
    
    # Red detection: red is dominant, green and blue are much lower
    elif r_norm > 0.9 and g_norm < 0.3 and b_norm < 0.3:
        return (1, 0, 0)  # Pure red RGB(255, 0, 0)
    
    # Green detection: green is dominant, red and blue are much lower
    elif g_norm > 0.9 and r_norm < 0.3 and b_norm < 0.3:
        return (0, 1, 0)  # Pure green RGB(0, 255, 0)
    
    # Orange/Yellow detection: both red and green high, blue low
    elif r_norm > 0.7 and g_norm > 0.5 and b_norm < 0.3:
        return (1, 0.65, 0)  # Standard orange RGB(255, 165, 0)
    
    # Cyan detection: blue and green high, red low
    elif b_norm > 0.8 and g_norm > 0.8 and r_norm < 0.2:
        return (0, 1, 1)  # Cyan RGB(0, 255, 255)
    
    # Magenta detection: red and blue high, green low
    elif r_norm > 0.8 and b_norm > 0.8 and g_norm < 0.2:
        return (1, 0, 1)  # Magenta RGB(255, 0, 255)
    
    # If no clear match, check absolute thresholds as fallback
    
    # Blue fallback: blue is strong, others are weak
    if b > 0.8 and r < 0.2 and g < 0.3:
        return (0, 0, 1)  # Pure blue
    
    # Red fallback: red is strong, others are weak
    elif r > 0.8 and g < 0.2 and b < 0.2:
        return (1, 0, 0)  # Pure red
    
    # Green fallback: green is strong, others are weak
    elif g > 0.8 and r < 0.2 and b < 0.2:
        return (0, 1, 0)  # Pure green
    
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
                    # Use the new function to properly extract text color from DA string or appearance stream
                    original_font_color = get_text_color_from_annotation(annot)
                    font_color = standardize_color(original_font_color)

                    # Use cyan as background color for all annotations
                    bg_color = (0, 1, 1)  # Cyan RGB(0, 255, 255)

                    # Update author
                    annot.set_info(title="Geron")

                    # Handle FreeText annotations specially (can use update method)
                    if annot_type == fitz.PDF_ANNOT_FREE_TEXT:
                        try:
                            # CRITICAL FIX: For PDFs with appearance streams but empty DA strings,
                            # delete old appearance and set proper DA before update()
                            r, g, b = font_color
                            da_string = f"{r} {g} {b} rg /Helv {font_size} Tf"
                            
                            try:
                                xref = annot.xref
                                # Delete old appearance stream so update() will regenerate it
                                doc.xref_set_key(xref, "AP", "null")
                                # Set the DA string with correct color
                                doc.xref_set_key(xref, "DA", f"({da_string})")
                                print(f"    Set DA: {da_string}")
                            except Exception as e:
                                print(f"    Warning: Could not set DA/AP: {e}")
                            
                            # For FreeText, border_color in update() controls the border
                            annot.update(
                                fontsize=font_size,
                                fontname="helv",  # Helvetica (closest to Arial)
                                text_color=font_color,
                                fill_color=bg_color,
                                border_color=(0, 0, 0)  # Black border
                            )
                            
                            # Do NOT call annot.update() again - it may revert the color!
                            
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

