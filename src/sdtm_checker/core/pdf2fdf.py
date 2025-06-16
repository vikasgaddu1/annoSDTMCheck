"""PDF to XFDF conversion module for extracting annotations."""

import argparse
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
import xml.dom.minidom


def convert_pdf_to_xfdf(input_pdf_path: str, output_xfdf_path: str) -> None:
    """
    Convert PDF annotations to XFDF format.

    Args:
        input_pdf_path (str): Path to the input PDF file
        output_xfdf_path (str): Path where the XFDF file will be saved

    Raises:
        FileNotFoundError: If the input PDF file doesn't exist
        Exception: If there's an error during conversion
    """
    # Validate input file
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"PDF file not found: {input_pdf_path}")

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_xfdf_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        # 1. Open the PDF and collect all annotations
        doc = fitz.open(input_pdf_path)
        annots_el = ET.Element("annots")
        annotation_count = 0

        for page_num, page in enumerate(doc, start=1):
            for annot in page.annots() or ():
                # Extract annotation information
                info = annot.info
                content = info.get("content", "")
                author = info.get("title", "")
                rect = annot.rect  # a fitz.Rect

                # Only process annotations with content
                if content:
                    a_el = ET.SubElement(annots_el, "text", {
                        "page": str(page_num),
                        "rect": f"{rect.x0},{rect.y0},{rect.x1},{rect.y1}",
                        "title": author,
                        "type": str(annot.type[0])  # Store annotation type
                    })
                    a_el.text = content
                    annotation_count += 1

        # 2. Wrap in XFDF boilerplate
        xfdf = ET.Element("xfdf", xmlns="http://ns.adobe.com/xfdf/")
        ET.SubElement(xfdf, "f", href=os.path.abspath(input_pdf_path))
        xfdf.append(annots_el)

        # 3. Write the XML with pretty formatting
        xml_str = ET.tostring(xfdf, encoding='unicode')
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ')

        # Write the formatted XML to file
        with open(output_xfdf_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

        print(
            f"✓ Extracted {annotation_count} annotations from {input_pdf_path}")
        print(f"✓ Saved XFDF to {output_xfdf_path}")

        doc.close()

    except Exception as e:
        raise Exception(f"Error converting PDF to XFDF: {str(e)}")


def main():
    """Command-line interface for PDF to XFDF conversion."""
    parser = argparse.ArgumentParser(
        description="Extract annotations from PDF files to XFDF format"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input PDF file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Path for the output XFDF file (default: same name as input with .xfdf extension)"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for output files (default: same as input file)"
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input)
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}.xfdf"
        else:
            output_path = input_path.with_suffix('.xfdf')

    try:
        convert_pdf_to_xfdf(args.input, str(output_path))
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
