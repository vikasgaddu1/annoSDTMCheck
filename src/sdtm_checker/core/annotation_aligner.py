"""Annotation aligner for PDF annotations.

This module provides functionality to automatically align annotations that are
close to each other horizontally or vertically, creating a cleaner and more
professional appearance.
"""

import fitz  # PyMuPDF
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from .annotation_utils import clean_annotation_content

logger = logging.getLogger(__name__)


@dataclass
class AlignmentOperation:
    """Record of a single annotation alignment operation."""
    page_num: int
    content_preview: str  # First 30 chars
    old_rect: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    new_rect: Tuple[float, float, float, float]
    alignment_type: str  # 'horizontal' or 'vertical'
    group_id: int  # Which group this annotation belongs to
    
    def __str__(self):
        align_desc = "horizontally" if self.alignment_type == 'horizontal' else "vertically"
        return (
            f"Page {self.page_num + 1} [Group {self.group_id}]: '{self.content_preview}' "
            f"aligned {align_desc} "
            f"({self.old_rect[0]:.1f}, {self.old_rect[1]:.1f}) -> "
            f"({self.new_rect[0]:.1f}, {self.new_rect[1]:.1f})"
        )


@dataclass
class AlignmentStats:
    """Statistics from annotation alignment operation."""
    total_annotations: int = 0
    horizontal_groups: int = 0
    vertical_groups: int = 0
    horizontal_aligned: int = 0
    vertical_aligned: int = 0
    errors: int = 0
    operations: List[AlignmentOperation] = field(default_factory=list)
    
    def __str__(self):
        return (
            f"Total annotations: {self.total_annotations}, "
            f"Horizontal groups: {self.horizontal_groups}, "
            f"Vertical groups: {self.vertical_groups}, "
            f"Horizontal aligned: {self.horizontal_aligned}, "
            f"Vertical aligned: {self.vertical_aligned}, "
            f"Errors: {self.errors}"
        )


class AnnotationAligner:
    """Aligns annotations that are close to each other."""
    
    def __init__(self, 
                 horizontal_tolerance: float = 10.0,
                 vertical_tolerance: float = 10.0,
                 align_horizontal: bool = True,
                 align_vertical: bool = True):
        """
        Initialize the annotation aligner.
        
        Args:
            horizontal_tolerance: Max vertical distance in points to consider "horizontally aligned"
            vertical_tolerance: Max horizontal distance in points to consider "vertically aligned"
            align_horizontal: Whether to perform horizontal alignment
            align_vertical: Whether to perform vertical alignment
        """
        self.horizontal_tolerance = horizontal_tolerance
        self.vertical_tolerance = vertical_tolerance
        self.align_horizontal = align_horizontal
        self.align_vertical = align_vertical
    
    def align_annotations(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
        dry_run: bool = False
    ) -> AlignmentStats:
        """
        Align annotations in a PDF file.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path for output PDF (if None, modifies in place)
            dry_run: If True, only detect and report without modifying
            
        Returns:
            AlignmentStats object with operation details
        """
        stats = AlignmentStats()
        
        try:
            doc = fitz.open(pdf_path)
            logger.info(f"Processing {len(doc)} pages from {pdf_path}")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get all annotations on this page
                annotations = list(page.annots() or [])
                stats.total_annotations += len(annotations)
                
                if not annotations:
                    continue
                
                # Perform horizontal alignment
                if self.align_horizontal:
                    h_ops = self._align_page_horizontal(
                        annotations, page_num, dry_run
                    )
                    stats.horizontal_aligned += len(h_ops)
                    stats.operations.extend(h_ops)
                
                # Perform vertical alignment
                if self.align_vertical:
                    v_ops = self._align_page_vertical(
                        annotations, page_num, dry_run
                    )
                    stats.vertical_aligned += len(v_ops)
                    stats.operations.extend(v_ops)
            
            # Save if not dry run
            if not dry_run and output_path:
                doc.save(output_path)
                logger.info(f"Saved modified PDF to {output_path}")
            elif not dry_run and not output_path:
                doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                logger.info(f"Updated PDF in place: {pdf_path}")
            
            doc.close()
            
            logger.info(f"Alignment complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
        
        return stats
    
    def _align_page_horizontal(
        self,
        annotations: List[fitz.Annot],
        page_num: int,
        dry_run: bool
    ) -> List[AlignmentOperation]:
        """
        Align annotations horizontally on a single page.
        
        Args:
            annotations: List of annotations on the page
            page_num: Page number (0-indexed)
            dry_run: If True, don't actually modify annotations
            
        Returns:
            List of AlignmentOperation objects
        """
        operations = []
        
        # Group annotations by vertical proximity (y-coordinate)
        groups = self._group_by_y_proximity(annotations, self.horizontal_tolerance)
        
        for group_id, group in enumerate(groups):
            if len(group) < 2:
                continue  # Need at least 2 annotations to align
            
            # Calculate average y-coordinate (top edge)
            avg_y0 = sum(annot.rect.y0 for annot in group) / len(group)
            
            # Align each annotation to the average
            for annot in group:
                old_rect = annot.rect
                
                # Skip if already very close to average
                if abs(old_rect.y0 - avg_y0) < 0.5:
                    continue
                
                # Create new rectangle with aligned y-coordinate
                height = old_rect.height
                new_rect = fitz.Rect(
                    old_rect.x0,
                    avg_y0,
                    old_rect.x1,
                    avg_y0 + height
                )
                
                # Create operation record
                content = annot.info.get('content', '')
                content = clean_annotation_content(content)
                operation = AlignmentOperation(
                    page_num=page_num,
                    content_preview=content[:30] + ('...' if len(content) > 30 else ''),
                    old_rect=(old_rect.x0, old_rect.y0, old_rect.x1, old_rect.y1),
                    new_rect=(new_rect.x0, new_rect.y0, new_rect.x1, new_rect.y1),
                    alignment_type='horizontal',
                    group_id=group_id
                )
                operations.append(operation)
                
                # Apply alignment if not dry run
                if not dry_run:
                    try:
                        annot.set_rect(new_rect)
                        annot.update()
                        logger.debug(f"Applied alignment: {operation}")
                    except Exception as e:
                        logger.error(f"Failed to apply alignment: {e}")
        
        return operations
    
    def _align_page_vertical(
        self,
        annotations: List[fitz.Annot],
        page_num: int,
        dry_run: bool
    ) -> List[AlignmentOperation]:
        """
        Align annotations vertically on a single page.
        
        Args:
            annotations: List of annotations on the page
            page_num: Page number (0-indexed)
            dry_run: If True, don't actually modify annotations
            
        Returns:
            List of AlignmentOperation objects
        """
        operations = []
        
        # Group annotations by horizontal proximity (x-coordinate)
        groups = self._group_by_x_proximity(annotations, self.vertical_tolerance)
        
        for group_id, group in enumerate(groups):
            if len(group) < 2:
                continue  # Need at least 2 annotations to align
            
            # Calculate average x-coordinate (left edge)
            avg_x0 = sum(annot.rect.x0 for annot in group) / len(group)
            
            # Align each annotation to the average
            for annot in group:
                old_rect = annot.rect
                
                # Skip if already very close to average
                if abs(old_rect.x0 - avg_x0) < 0.5:
                    continue
                
                # Create new rectangle with aligned x-coordinate
                width = old_rect.width
                new_rect = fitz.Rect(
                    avg_x0,
                    old_rect.y0,
                    avg_x0 + width,
                    old_rect.y1
                )
                
                # Create operation record
                content = annot.info.get('content', '')
                content = clean_annotation_content(content)
                operation = AlignmentOperation(
                    page_num=page_num,
                    content_preview=content[:30] + ('...' if len(content) > 30 else ''),
                    old_rect=(old_rect.x0, old_rect.y0, old_rect.x1, old_rect.y1),
                    new_rect=(new_rect.x0, new_rect.y0, new_rect.x1, new_rect.y1),
                    alignment_type='vertical',
                    group_id=group_id
                )
                operations.append(operation)
                
                # Apply alignment if not dry run
                if not dry_run:
                    try:
                        annot.set_rect(new_rect)
                        annot.update()
                        logger.debug(f"Applied alignment: {operation}")
                    except Exception as e:
                        logger.error(f"Failed to apply alignment: {e}")
        
        return operations
    
    def _group_by_y_proximity(
        self,
        annotations: List[fitz.Annot],
        tolerance: float
    ) -> List[List[fitz.Annot]]:
        """
        Group annotations by vertical proximity (y-coordinate).
        
        Annotations are grouped together if their y-coordinates are within
        the tolerance distance.
        
        Args:
            annotations: List of annotations to group
            tolerance: Maximum distance in points
            
        Returns:
            List of annotation groups
        """
        if not annotations:
            return []
        
        # Sort by y-coordinate
        sorted_annots = sorted(annotations, key=lambda a: a.rect.y0)
        
        groups = []
        current_group = [sorted_annots[0]]
        
        for annot in sorted_annots[1:]:
            # Calculate average y of current group
            avg_y = sum(a.rect.y0 for a in current_group) / len(current_group)
            
            # Check if this annotation is close enough to the group
            if abs(annot.rect.y0 - avg_y) <= tolerance:
                current_group.append(annot)
            else:
                # Start a new group
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [annot]
        
        # Add the last group
        if len(current_group) >= 2:
            groups.append(current_group)
        
        return groups
    
    def _group_by_x_proximity(
        self,
        annotations: List[fitz.Annot],
        tolerance: float
    ) -> List[List[fitz.Annot]]:
        """
        Group annotations by horizontal proximity (x-coordinate).
        
        Annotations are grouped together if their x-coordinates are within
        the tolerance distance.
        
        Args:
            annotations: List of annotations to group
            tolerance: Maximum distance in points
            
        Returns:
            List of annotation groups
        """
        if not annotations:
            return []
        
        # Sort by x-coordinate
        sorted_annots = sorted(annotations, key=lambda a: a.rect.x0)
        
        groups = []
        current_group = [sorted_annots[0]]
        
        for annot in sorted_annots[1:]:
            # Calculate average x of current group
            avg_x = sum(a.rect.x0 for a in current_group) / len(current_group)
            
            # Check if this annotation is close enough to the group
            if abs(annot.rect.x0 - avg_x) <= tolerance:
                current_group.append(annot)
            else:
                # Start a new group
                if len(current_group) >= 2:
                    groups.append(current_group)
                current_group = [annot]
        
        # Add the last group
        if len(current_group) >= 2:
            groups.append(current_group)
        
        return groups
    
    def generate_report(self, stats: AlignmentStats) -> str:
        """
        Generate a text report of alignment operations.
        
        Args:
            stats: AlignmentStats object from alignment operation
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ANNOTATION ALIGNMENT REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Summary: {stats}")
        lines.append("")
        
        if stats.operations:
            # Group by page and type
            by_page_type = defaultdict(lambda: {'horizontal': [], 'vertical': []})
            for op in stats.operations:
                by_page_type[op.page_num][op.alignment_type].append(op)
            
            lines.append("Alignment Operations:")
            lines.append("-" * 80)
            
            for page_num in sorted(by_page_type.keys()):
                lines.append(f"\nPage {page_num + 1}:")
                
                h_ops = by_page_type[page_num]['horizontal']
                if h_ops:
                    lines.append(f"  Horizontal alignments: {len(h_ops)}")
                    for op in h_ops:
                        lines.append(f"    {op}")
                
                v_ops = by_page_type[page_num]['vertical']
                if v_ops:
                    lines.append(f"  Vertical alignments: {len(v_ops)}")
                    for op in v_ops:
                        lines.append(f"    {op}")
            
            lines.append("")
        
        if stats.errors > 0:
            lines.append(f"⚠ {stats.errors} error(s) occurred during processing")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

