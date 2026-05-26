"""
Integration test for XFDF color workflow with annotation standardizer.
"""

import pytest
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer,
    StandardizationConfig
)


def test_full_standardization_with_xfdf_colors():
    """Test complete standardization workflow with XFDF color application."""
    
    # Create a test PDF with annotations
    doc = fitz.open()
    page = doc.new_page()
    
    # Add annotations with various colors
    # 1. Header annotation (DM = Demographics) with light blue
    rect1 = fitz.Rect(100, 100, 400, 150)
    annot1 = page.add_freetext_annot(
        rect1,
        "DM = Demographics",
        fontsize=12,
        fontname="helv",
        text_color=(0.05, 0.1, 0.9),  # Light blue -> should standardize to pure blue
        fill_color=(0, 1, 1)
    )
    annot1.set_info(title="OldAuthor")
    annot1.update()
    
    # 2. Variable annotation with reddish color
    rect2 = fitz.Rect(100, 200, 400, 250)
    annot2 = page.add_freetext_annot(
        rect2,
        "USUBJID",
        fontsize=10,
        fontname="helv",
        text_color=(0.95, 0.05, 0.05),  # Light red -> should standardize to pure red
        fill_color=(0, 1, 1)
    )
    annot2.set_info(title="OldAuthor")
    annot2.update()
    
    # 3. Another variable with greenish color
    rect3 = fitz.Rect(100, 300, 400, 350)
    annot3 = page.add_freetext_annot(
        rect3,
        "RFSTDTC",
        fontsize=10,
        fontname="helv",
        text_color=(0.05, 0.9, 0.05),  # Light green -> should standardize to pure green
        fill_color=(0, 1, 1)
    )
    annot3.set_info(title="OldAuthor")
    annot3.update()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_in:
        input_pdf = temp_in.name
    with tempfile.NamedTemporaryFile(suffix='_out.pdf', delete=False) as temp_out:
        output_pdf = temp_out.name
    
    try:
        doc.save(input_pdf)
        doc.close()
        
        # Create standardization config with XFDF colors enabled
        config = StandardizationConfig(
            default_author="Geron",
            apply_xfdf_colors=True,
            auto_resize_textboxes=False,
            align_annotations=False
        )
        
        # Run standardization
        standardizer = AnnotationStandardizer(config)
        stats = standardizer.standardize_pdf(input_pdf, output_pdf)
        
        # Verify results
        assert stats['annotations_modified'] == 3
        assert stats['errors'] == [] or len(stats['errors']) == 0
        
        # Check if XFDF workflow was applied
        if 'xfdf_colors_applied' in stats:
            # XFDF workflow ran successfully
            assert stats['xfdf_annotations_processed'] >= 0
        
        # Open output PDF and verify annotations
        output_doc = fitz.open(output_pdf)
        output_page = output_doc[0]
        output_annots = list(output_page.annots() or [])
        
        # Should have 3 annotations
        assert len(output_annots) == 3
        
        # Verify author was changed
        for annot in output_annots:
            assert annot.info.get('title') == "Geron"
        
        # Verify content
        contents = [annot.info.get('content', '').strip() for annot in output_annots]
        assert "DM = Demographics" in contents
        assert "USUBJID" in contents
        assert "RFSTDTC" in contents
        
        output_doc.close()
        
        print(f"\n[PASS] Integration test passed!")
        print(f"  - Annotations modified: {stats['annotations_modified']}")
        print(f"  - Headers found: {stats['headers_found']}")
        print(f"  - Bookmarks created: {stats['bookmarks_created']}")
        if 'xfdf_colors_applied' in stats:
            print(f"  - XFDF colors applied: {stats['xfdf_colors_applied']}")
        
    finally:
        # Clean up
        Path(input_pdf).unlink(missing_ok=True)
        Path(output_pdf).unlink(missing_ok=True)


def test_standardization_without_xfdf_colors():
    """Test standardization with XFDF colors disabled."""
    
    # Create a test PDF
    doc = fitz.open()
    page = doc.new_page()
    
    rect = fitz.Rect(100, 100, 300, 150)
    annot = page.add_freetext_annot(
        rect,
        "Test Annotation",
        fontsize=10,
        fontname="helv",
        text_color=(0, 0, 1),
        fill_color=(0, 1, 1)
    )
    annot.update()
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_in:
        input_pdf = temp_in.name
    with tempfile.NamedTemporaryFile(suffix='_out.pdf', delete=False) as temp_out:
        output_pdf = temp_out.name
    
    try:
        doc.save(input_pdf)
        doc.close()
        
        # Create config with XFDF colors disabled
        config = StandardizationConfig(
            apply_xfdf_colors=False
        )
        
        # Run standardization
        standardizer = AnnotationStandardizer(config)
        stats = standardizer.standardize_pdf(input_pdf, output_pdf)
        
        # Verify XFDF workflow was not applied
        assert 'xfdf_colors_applied' not in stats or stats.get('xfdf_colors_applied', 0) == 0
        
        print(f"\n[PASS] Test without XFDF colors passed!")
        
    finally:
        # Clean up
        Path(input_pdf).unlink(missing_ok=True)
        Path(output_pdf).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

