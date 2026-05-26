"""Extract PDF annotations to Excel for review or XFDF generation.

This script extracts all FreeText annotations from a PDF and saves them to Excel
with complete details including position, colors, fonts, and borders.

Usage:
    python extract_annotations_to_excel.py input.pdf output.xlsx
"""

import fitz  # PyMuPDF
import pandas as pd
import sys
import re
from pathlib import Path


def rgb_to_string(color_tuple):
    """Convert PyMuPDF color tuple (0-1 scale) to RGB string."""
    if not color_tuple or len(color_tuple) != 3:
        return "N/A"
    r, g, b = color_tuple
    return f"RGB({int(r*255)}, {int(g*255)}, {int(b*255)})"


def get_text_color_from_da(annot):
    """Extract text color from Default Appearance string."""
    try:
        da = annot.info.get('DA', '')
        
        if not da:
            try:
                xref = annot.xref
                da = annot.parent.parent.xref_get_key(xref, 'DA')
                if da:
                    da = da[1]
            except:
                pass
        
        if da:
            color_match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if color_match:
                r = float(color_match.group(1))
                g = float(color_match.group(2))
                b = float(color_match.group(3))
                return (r, g, b)
        
        # Fallback to stroke color
        colors = annot.colors
        if colors and 'stroke' in colors:
            return colors['stroke']
        
        return (0, 0, 0)
    except:
        return (0, 0, 0)


def get_border_info(annot):
    """Extract border width and style from annotation."""
    try:
        border_dict = annot.border
        if border_dict:
            width = border_dict.get('width', 0)
            style = border_dict.get('style', 'S')
            dashes = border_dict.get('dashes', None)
            return width, style, dashes
        return 1, 'S', None
    except:
        return 1, 'S', None


def get_border_color(annot):
    """Extract border color from annotation."""
    try:
        colors = annot.colors
        if colors and 'stroke' in colors:
            return colors['stroke']
        return (0, 0, 0)
    except:
        return (0, 0, 0)


def extract_annotations_to_excel(pdf_path, excel_path):
    """
    Extract all FreeText annotations from PDF to Excel.
    
    Args:
        pdf_path: Path to input PDF file
        excel_path: Path to output Excel file
        
    Returns:
        Number of annotations extracted
    """
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    annotations_data = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        annots = page.annots()
        
        if not annots:
            continue
        
        for annot in annots:
            # Only extract FreeText annotations
            if annot.type[0] != fitz.PDF_ANNOT_FREE_TEXT:
                continue
            
            # Get annotation info
            info = annot.info
            rect = annot.rect
            
            # Extract colors
            text_color = get_text_color_from_da(annot)
            fill_color = annot.colors.get('fill', (0, 1, 1)) if annot.colors else (0, 1, 1)
            border_color = get_border_color(annot)
            
            # Extract border info
            border_width, border_style, border_dashes = get_border_info(annot)
            
            # Extract font info from DA string
            da = info.get('DA', '')
            font_name = "Helvetica"
            font_size = 10
            
            if da:
                # Extract font name
                font_match = re.search(r'/([A-Za-z0-9-]+)', da)
                if font_match:
                    font_name = font_match.group(1)
                
                # Extract font size
                size_match = re.search(r'(\d+(?:\.\d+)?)\s+Tf', da)
                if size_match:
                    font_size = float(size_match.group(1))
            
            # Build annotation data row
            annot_data = {
                'Page': page_num + 1,
                'Content': info.get('content', ''),
                'Text_Color': rgb_to_string(text_color),
                'Text_Color_R': int(text_color[0] * 255),
                'Text_Color_G': int(text_color[1] * 255),
                'Text_Color_B': int(text_color[2] * 255),
                'Background_Color': rgb_to_string(fill_color),
                'Background_R': int(fill_color[0] * 255),
                'Background_G': int(fill_color[1] * 255),
                'Background_B': int(fill_color[2] * 255),
                'Border_Color': rgb_to_string(border_color),
                'Border_R': int(border_color[0] * 255),
                'Border_G': int(border_color[1] * 255),
                'Border_B': int(border_color[2] * 255),
                'Border_Width': border_width,
                'Border_Style': border_style,
                'Position_X0': rect.x0,
                'Position_Y0': rect.y0,
                'Position_X1': rect.x1,
                'Position_Y1': rect.y1,
                'Width': rect.width,
                'Height': rect.height,
                'Font_Name': font_name,
                'Font_Size': font_size,
                'Author': info.get('title', ''),
                'Subject': info.get('subject', ''),
                'Creation_Date': info.get('creationDate', ''),
                'Modification_Date': info.get('modDate', '')
            }
            
            annotations_data.append(annot_data)
    
    doc.close()
    
    # Create DataFrame and save to Excel
    if annotations_data:
        df = pd.DataFrame(annotations_data)
        
        # Create Excel writer with some formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Annotations', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Annotations']
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✓ Extracted {len(annotations_data)} annotations to {excel_path}")
        return len(annotations_data)
    else:
        print("! No FreeText annotations found in PDF")
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python extract_annotations_to_excel.py input.pdf [output.xlsx]")
        print("\nExtracts all FreeText annotations from PDF to Excel with complete details.")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    
    if not Path(input_pdf).exists():
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)
    
    # Default output name if not provided
    if len(sys.argv) > 2:
        output_excel = sys.argv[2]
    else:
        output_excel = Path(input_pdf).stem + "_annotations.xlsx"
    
    try:
        count = extract_annotations_to_excel(input_pdf, output_excel)
        print(f"\n✓ Extraction complete!")
        print(f"  Input:  {input_pdf}")
        print(f"  Output: {output_excel}")
        print(f"  Count:  {count} annotations")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

