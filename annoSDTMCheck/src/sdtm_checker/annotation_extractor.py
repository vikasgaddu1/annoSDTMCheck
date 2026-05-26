"""
Module for extracting annotations from PDF files.
"""

from pathlib import Path
from typing import List, Tuple, Optional, Callable
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class AnnotationExtractor:
    """Class for extracting annotations from PDF files."""

    def __init__(self, pdf_path: Optional[str] = None, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Initialize the annotation extractor.

        Args:
            pdf_path: Optional path to a PDF file
            progress_callback: Optional function to call with progress updates (current, total)
        """
        self.pdf_path = pdf_path
        self.progress_callback = progress_callback

    def extract_annotations(self) -> List[Tuple[str, int, Optional[Tuple[float, float]]]]:
        """
        Extract annotations from the PDF file.

        Returns:
            List of tuples containing (annotation_text, page_number, position)
        """
        if not self.pdf_path:
            raise ValueError("No PDF file specified")

        annotations = []
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            for page_num in range(total_pages):
                page = doc[page_num]
                for annot in page.annots():
                    text = annot.info.get("content", "").strip()
                    if text:
                        rect = annot.rect
                        # Use top-left corner as position
                        position = (rect.x0, rect.y0)
                        annotations.append((text, page_num + 1, position))
                if self.progress_callback:
                    self.progress_callback(page_num + 1, total_pages)
            doc.close()
            return annotations
        except Exception as e:
            logger.error(f"Error extracting annotations: {str(e)}")
            raise

    def extract_from_pdf(self, pdf_path: str) -> List[Tuple[str, int, Optional[Tuple[float, float]]]]:
        """
        Extract annotations from a specific PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of tuples containing (annotation_text, page_number, position)
        """
        self.pdf_path = pdf_path
        return self.extract_annotations()

    def batch_process(self, pdf_dir: str, output_dir: str, format: str = 'xfdf') -> None:
        """
        Process multiple PDF files in a directory.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save extracted annotations
            format: Output format ('xfdf' or 'excel')
        """
        pdf_dir = Path(pdf_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                output_file = output_dir / f"{pdf_file.stem}.{format}"
                annotations = self.extract_from_pdf(str(pdf_file))

                if format == 'xfdf':
                    self.to_xfdf(annotations, str(output_file))
                else:
                    self.to_excel(annotations, str(output_file))

            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")

    def to_xfdf(self, annotations: List[Tuple[str, int, Optional[Tuple[float, float]]]], output_path: str) -> None:
        """
        Save annotations in XFDF format.

        Args:
            annotations: List of annotation tuples
            output_path: Path to save the XFDF file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">\n')
            f.write('  <annots>\n')

            for text, page, pos in annotations:
                f.write(
                    f'    <text page="{page}" rect="{pos[0]},{pos[1]},0,0">\n')
                f.write(f'      <contents>{text}</contents>\n')
                f.write('    </text>\n')

            f.write('  </annots>\n')
            f.write('</xfdf>')

    def to_excel(self, annotations: List[Tuple[str, int, Optional[Tuple[float, float]]]], output_path: str) -> None:
        """
        Save annotations in Excel format.

        Args:
            annotations: List of annotation tuples
            output_path: Path to save the Excel file
        """
        import pandas as pd

        data = []
        for text, page, pos in annotations:
            data.append({
                'Page': page,
                'Text': text,
                'X': pos[0] if pos else None,
                'Y': pos[1] if pos else None
            })

        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False)
