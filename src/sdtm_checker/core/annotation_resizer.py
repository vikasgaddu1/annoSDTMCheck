"""Annotation resizer for PDF textbox annotations.

This module provides functionality to automatically resize FreeText annotations
to ensure their content is fully visible without wrapping or truncation.
"""

import fitz  # PyMuPDF
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .text_dimension_calculator import TextDimensionCalculator, get_font_from_annotation
from .annotation_utils import clean_annotation_content

logger = logging.getLogger(__name__)


@dataclass
class ResizeOperation:
    """Record of a single annotation resize operation."""
    page_num: int
    content_preview: str  # First 50 chars
    old_rect: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    new_rect: Tuple[float, float, float, float]
    old_width: float
    old_height: float
    new_width: float
    new_height: float
    fontname: str
    fontsize: float
    
    def __str__(self):
        return (
            f"Page {self.page_num + 1}: '{self.content_preview}' "
            f"[{self.fontname} {self.fontsize}pt] "
            f"({self.old_width:.1f}x{self.old_height:.1f}) -> "
            f"({self.new_width:.1f}x{self.new_height:.1f})"
        )


@dataclass
class ResizeStats:
    """Statistics from annotation resize operation."""
    total_annotations: int = 0
    freetext_annotations: int = 0
    checked: int = 0
    resized: int = 0
    skipped: int = 0
    errors: int = 0
    operations: List[ResizeOperation] = field(default_factory=list)
    
    def __str__(self):
        return (
            f"Total annotations: {self.total_annotations}, "
            f"FreeText: {self.freetext_annotations}, "
            f"Checked: {self.checked}, "
            f"Resized: {self.resized}, "
            f"Skipped: {self.skipped}, "
            f"Errors: {self.errors}"
        )


class AnnotationResizer:
    """Resizes FreeText annotations to fit their content."""
    
    def __init__(self, 
                 calculator: Optional[TextDimensionCalculator] = None,
                 expand_width: bool = True,
                 expand_height: bool = True,
                 max_width_expansion: Optional[float] = 200.0,
                 max_height_expansion: Optional[float] = 300.0):
        """
        Initialize the annotation resizer.
        
        Args:
            calculator: Text dimension calculator instance
            expand_width: Whether to expand annotation width
            expand_height: Whether to expand annotation height
            max_width_expansion: Maximum width expansion in points (None = unlimited)
            max_height_expansion: Maximum height expansion in points (None = unlimited)
        """
        self.calculator = calculator or TextDimensionCalculator()
        self.expand_width = expand_width
        self.expand_height = expand_height
        self.max_width_expansion = max_width_expansion
        self.max_height_expansion = max_height_expansion
    
    def resize_annotations(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        dry_run: bool = False
    ) -> ResizeStats:
        """
        Resize annotations in a PDF file.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path for output PDF (if None, modifies in place)
            dry_run: If True, only detect and report without modifying
            
        Returns:
            ResizeStats object with operation details
        """
        stats = ResizeStats()
        
        try:
            doc = fitz.open(pdf_path)
            logger.info(f"Processing {len(doc)} pages from {pdf_path}")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                for annot in page.annots() or []:
                    stats.total_annotations += 1
                    
                    # Only process FreeText annotations
                    if annot.type[0] != fitz.PDF_ANNOT_FREE_TEXT:
                        continue
                    
                    stats.freetext_annotations += 1
                    
                    try:
                        # Process this annotation
                        resize_op = self._process_annotation(annot, page_num, dry_run)
                        
                        if resize_op:
                            stats.resized += 1
                            stats.operations.append(resize_op)
                            logger.info(f"Resized: {resize_op}")
                        else:
                            stats.skipped += 1
                        
                        stats.checked += 1
                        
                    except Exception as e:
                        stats.errors += 1
                        logger.error(f"Error processing annotation on page {page_num + 1}: {e}")
            
            # Save if not dry run
            if not dry_run and output_path:
                doc.save(output_path)
                logger.info(f"Saved modified PDF to {output_path}")
            elif not dry_run and not output_path:
                doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                logger.info(f"Updated PDF in place: {pdf_path}")
            
            doc.close()
            
            logger.info(f"Resize complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
        
        return stats
    
    def _process_annotation(
        self,
        annot: fitz.Annot,
        page_num: int,
        dry_run: bool
    ) -> Optional[ResizeOperation]:
        """
        Process a single annotation, resizing if needed.
        
        Args:
            annot: Annotation to process
            page_num: Page number (0-indexed)
            dry_run: If True, don't actually resize
            
        Returns:
            ResizeOperation if resized, None if skipped
        """
        # Get annotation content
        content = annot.info.get('content', '')
        content = clean_annotation_content(content)
        if not content:
            return None
        
        # Get current rectangle
        old_rect = annot.rect
        old_width = old_rect.width
        old_height = old_rect.height
        
        # Get font properties
        fontname, fontsize = get_font_from_annotation(annot)
        
        # Check if text fits
        if self.calculator.check_if_text_fits(content, old_rect, fontname, fontsize):
            return None  # Text fits, no resize needed
        
        # Calculate required dimensions
        if self.expand_width and self.expand_height:
            # Let both dimensions expand as needed
            required_width, required_height = self.calculator.calculate_optimal_dimensions(
                content, fontname, fontsize, current_width=None
            )
        elif self.expand_height:
            # Keep width, expand height
            required_width, required_height = self.calculator.calculate_optimal_dimensions(
                content, fontname, fontsize, current_width=old_width
            )
        elif self.expand_width:
            # Expand width to fit single line, adjust height
            required_width, required_height = self.calculator.calculate_optimal_dimensions(
                content, fontname, fontsize, current_width=None
            )
        else:
            # No expansion allowed
            return None
        
        # Apply expansion limits
        new_width = old_width
        new_height = old_height
        
        if self.expand_width:
            width_increase = required_width - old_width
            if self.max_width_expansion is not None:
                width_increase = min(width_increase, self.max_width_expansion)
            new_width = old_width + width_increase
        
        if self.expand_height:
            height_increase = required_height - old_height
            if self.max_height_expansion is not None:
                height_increase = min(height_increase, self.max_height_expansion)
            new_height = old_height + height_increase
        
        # Check if we actually need to resize
        if abs(new_width - old_width) < 1.0 and abs(new_height - old_height) < 1.0:
            return None  # No significant change needed
        
        # Create new rectangle (preserve top-left corner)
        new_rect = fitz.Rect(
            old_rect.x0,
            old_rect.y0,
            old_rect.x0 + new_width,
            old_rect.y0 + new_height
        )
        
        # Create operation record
        operation = ResizeOperation(
            page_num=page_num,
            content_preview=content[:50] + ('...' if len(content) > 50 else ''),
            old_rect=(old_rect.x0, old_rect.y0, old_rect.x1, old_rect.y1),
            new_rect=(new_rect.x0, new_rect.y0, new_rect.x1, new_rect.y1),
            old_width=old_width,
            old_height=old_height,
            new_width=new_width,
            new_height=new_height,
            fontname=fontname,
            fontsize=fontsize
        )
        
        # Apply resize if not dry run
        if not dry_run:
            try:
                annot.set_rect(new_rect)
                annot.update()
                logger.debug(f"Applied resize: {operation}")
            except Exception as e:
                logger.error(f"Failed to apply resize: {e}")
                raise
        
        return operation
    
    def generate_report(self, stats: ResizeStats) -> str:
        """
        Generate a text report of resize operations.
        
        Args:
            stats: ResizeStats object from resize operation
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ANNOTATION RESIZE REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Summary: {stats}")
        lines.append("")
        
        if stats.operations:
            lines.append("Resize Operations:")
            lines.append("-" * 80)
            for op in stats.operations:
                lines.append(str(op))
            lines.append("")
        
        if stats.errors > 0:
            lines.append(f"⚠ {stats.errors} error(s) occurred during processing")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

