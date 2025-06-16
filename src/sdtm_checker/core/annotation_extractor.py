"""
Annotation extraction and conversion module.

This module provides functionality for extracting annotations from PDF files
and converting them to various formats (XFDF, Excel).
"""

import os
import fitz  # PyMuPDF
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from datetime import datetime


@dataclass
class Annotation:
    """Class to store annotation data."""
    page_number: int
    author: str
    content: str
    position: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    type: str
    timestamp: Optional[datetime] = None


class AnnotationExtractor:
    """Class for extracting and converting PDF annotations."""

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the annotation extractor.

        Args:
            cache_enabled: Whether to enable caching of extracted annotations
        """
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, List[Annotation]] = {}

    def extract_from_pdf(self, pdf_path: str) -> List[Annotation]:
        """
        Extract annotations from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of Annotation objects

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF file is corrupted or invalid
        """
        if self.cache_enabled and pdf_path in self._cache:
            return self._cache[pdf_path]

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            annotations = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                for annot in page.annots():
                    # Extract annotation data
                    content = annot.info.get("content", "").strip()
                    if not content:  # Skip empty annotations
                        continue

                    author = annot.info.get("title", "Unknown")
                    rect = annot.rect
                    annot_type = annot.type[0]  # Get first letter of type

                    # Create annotation object
                    annotation = Annotation(
                        page_number=page_num + 1,
                        author=author,
                        content=content,
                        position=(rect.x0, rect.y0, rect.x1, rect.y1),
                        type=annot_type,
                        timestamp=datetime.now()
                    )
                    annotations.append(annotation)

            doc.close()

            # Cache the result if enabled
            if self.cache_enabled:
                self._cache[pdf_path] = annotations

            return annotations

        except Exception as e:
            raise ValueError(f"Error processing PDF file: {str(e)}")

    def to_xfdf(self, annotations: List[Annotation], output_path: str) -> None:
        """
        Convert annotations to XFDF format.

        Args:
            annotations: List of Annotation objects
            output_path: Path where XFDF file will be saved

        Raises:
            Exception: If there's an error during conversion
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create XFDF structure
            xfdf = ET.Element("xfdf", {
                "xmlns": "http://ns.adobe.com/xfdf/",
                "xml:space": "preserve"
            })

            fields = ET.SubElement(xfdf, "fields")

            # Add each annotation
            for annot in annotations:
                field = ET.SubElement(fields, "field", {
                    "name": f"Page{annot.page_number}",
                    "page": str(annot.page_number)
                })

                value = ET.SubElement(field, "value")
                value.text = annot.content

                # Add position information
                position = ET.SubElement(field, "position")
                position.text = f"{annot.position[0]},{annot.position[1]},{annot.position[2]},{annot.position[3]}"

            # Write to file
            tree = ET.ElementTree(xfdf)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)

        except Exception as e:
            raise Exception(f"Error creating XFDF file: {str(e)}")

    def to_excel(self, annotations: List[Annotation], output_path: str, include_coordinates: bool = False) -> None:
        """
        Convert annotations to Excel format.

        Args:
            annotations: List of Annotation objects
            output_path: Path where Excel file will be saved
            include_coordinates: Whether to include coordinate columns

        Raises:
            Exception: If there's an error during conversion
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Convert annotations to DataFrame
            data = []
            for annot in annotations:
                row = {
                    "Page": annot.page_number,
                    "Author": annot.author,
                    "Content": annot.content,
                    "Type": annot.type
                }

                if include_coordinates:
                    row.update({
                        "X1": annot.position[0],
                        "Y1": annot.position[1],
                        "X2": annot.position[2],
                        "Y2": annot.position[3]
                    })

                data.append(row)

            df = pd.DataFrame(data)

            # Write to Excel with formatting
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Annotations")

                # Get the workbook and worksheet
                worksheet = writer.sheets["Annotations"]

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass

                    # Cap at 50 characters
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        except Exception as e:
            raise Exception(f"Error creating Excel file: {str(e)}")

    def to_parser_format(self, annotations: List[Annotation]) -> List[Tuple[str, int, Optional[Tuple[float, float]]]]:
        """
        Convert Annotation objects to the format expected by the parser.

        Args:
            annotations: List of Annotation objects

        Returns:
            List of tuples containing (text, page_number, position)
        """
        return [
            (
                annot.content,
                annot.page_number,
                (annot.position[0], annot.position[1]
                 ) if annot.position else None
            )
            for annot in annotations
        ]

    def batch_process(self, pdf_dir: str, output_dir: str, format: str = "xfdf") -> None:
        """
        Process multiple PDF files in a directory.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory where output files will be saved
            format: Output format ("xfdf" or "excel")

        Raises:
            ValueError: If format is invalid
            Exception: If there's an error during processing
        """
        if format not in ["xfdf", "excel"]:
            raise ValueError("Format must be 'xfdf' or 'excel'")

        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Process each PDF file
            for filename in os.listdir(pdf_dir):
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(pdf_dir, filename)
                    base_name = os.path.splitext(filename)[0]

                    # Extract annotations
                    annotations = self.extract_from_pdf(pdf_path)

                    if not annotations:
                        print(f"⚠ No annotations found in {filename}")
                        continue

                    # Save in specified format
                    if format == "xfdf":
                        output_path = os.path.join(
                            output_dir, f"{base_name}.xfdf")
                        self.to_xfdf(annotations, output_path)
                    else:
                        output_path = os.path.join(
                            output_dir, f"{base_name}.xlsx")
                        self.to_excel(annotations, output_path)

                    print(f"✓ Processed {filename}")

        except Exception as e:
            raise Exception(f"Error during batch processing: {str(e)}")
