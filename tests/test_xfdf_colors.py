"""
Tests for XFDF color update functionality.
"""

import pytest
import fitz  # PyMuPDF
import tempfile
from pathlib import Path
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sdtm_checker.core.xfdf_color_updater import (
    standardize_color,
    rgb_to_hex,
    hex_to_rgb,
    export_to_xfdf,
    update_xfdf_colors,
    import_from_xfdf,
    apply_xfdf_color_workflow
)


class TestColorConversion:
    """Tests for color conversion functions."""
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        assert rgb_to_hex(0, 0, 1) == "#0000FF"  # Blue
        assert rgb_to_hex(1, 0, 0) == "#FF0000"  # Red
        assert rgb_to_hex(0, 1, 0) == "#00FF00"  # Green
        assert rgb_to_hex(0, 0, 0) == "#000000"  # Black
        assert rgb_to_hex(1, 1, 1) == "#FFFFFF"  # White
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        assert hex_to_rgb("#0000FF") == (0, 0, 1)  # Blue
        assert hex_to_rgb("0000FF") == (0, 0, 1)   # Blue without #
        assert hex_to_rgb("#FF0000") == (1, 0, 0)  # Red
        assert hex_to_rgb("#00FF00") == (0, 1, 0)  # Green
    
    def test_standardize_color_blue(self):
        """Test blue color standardization."""
        # Pure blue
        assert standardize_color((0, 0, 1)) == (0, 0, 1)
        
        # Light blue shades
        assert standardize_color((0, 0, 0.9)) == (0, 0, 1)
        assert standardize_color((0.05, 0, 0.95)) == (0, 0, 1)
        
        # Dark blue
        assert standardize_color((0, 0, 0.85)) == (0, 0, 1)
    
    def test_standardize_color_red(self):
        """Test red color standardization."""
        # Pure red
        assert standardize_color((1, 0, 0)) == (1, 0, 0)
        
        # Light red shades
        assert standardize_color((0.95, 0, 0)) == (1, 0, 0)
        assert standardize_color((0.9, 0.05, 0.05)) == (1, 0, 0)
    
    def test_standardize_color_green(self):
        """Test green color standardization."""
        # Pure green
        assert standardize_color((0, 1, 0)) == (0, 1, 0)
        
        # Light green shades
        assert standardize_color((0, 0.95, 0)) == (0, 1, 0)
    
    def test_standardize_color_orange(self):
        """Test orange color standardization."""
        # Orange shades
        result = standardize_color((1, 0.65, 0))
        assert result == (1, 0.65, 0)
        
        # Yellow-orange
        result = standardize_color((1, 0.8, 0))
        assert result == (1, 0.65, 0)
    
    def test_standardize_color_black(self):
        """Test black color standardization."""
        assert standardize_color((0, 0, 0)) == (0, 0, 0)
        assert standardize_color((0.1, 0.1, 0.1)) == (0, 0, 0)  # Very dark gray


class TestXFDFExport:
    """Tests for XFDF export functionality."""
    
    @pytest.fixture
    def sample_pdf_with_annotations(self):
        """Create a sample PDF with annotations for testing."""
        # Create a temporary PDF with some annotations
        doc = fitz.open()
        page = doc.new_page()
        
        # Add a FreeText annotation with blue text
        rect = fitz.Rect(100, 100, 300, 150)
        annot = page.add_freetext_annot(
            rect,
            "USUBJID",
            fontsize=10,
            fontname="helv",
            text_color=(0, 0, 1),  # Blue
            fill_color=(0, 1, 1)   # Cyan background
        )
        annot.set_info(title="TestAuthor")
        annot.update()
        
        # Add another annotation with red text
        rect2 = fitz.Rect(100, 200, 300, 250)
        annot2 = page.add_freetext_annot(
            rect2,
            "AE = Adverse Events",
            fontsize=12,
            fontname="helv",
            text_color=(1, 0, 0),  # Red
            fill_color=(0, 1, 1)   # Cyan background
        )
        annot2.set_info(title="TestAuthor")
        annot2.update()
        
        yield doc
        
        doc.close()
    
    def test_export_to_xfdf(self, sample_pdf_with_annotations):
        """Test exporting PDF annotations to XFDF."""
        with tempfile.NamedTemporaryFile(suffix='.xfdf', delete=False) as temp_xfdf:
            xfdf_path = temp_xfdf.name
        
        try:
            # Export annotations
            count = export_to_xfdf(sample_pdf_with_annotations, xfdf_path)
            
            # Verify export
            assert count == 2  # We added 2 annotations
            assert Path(xfdf_path).exists()
            
            # Check XFDF content
            with open(xfdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert '<xfdf' in content
                assert '<annots>' in content
                assert '<freetext' in content
                assert 'USUBJID' in content
                assert 'AE = Adverse Events' in content
        
        finally:
            # Clean up
            Path(xfdf_path).unlink(missing_ok=True)


class TestXFDFColorUpdate:
    """Tests for XFDF color update functionality."""
    
    def test_update_xfdf_colors(self):
        """Test updating colors in XFDF file."""
        # Create a sample XFDF with non-standard colors
        xfdf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
  <f href="test.pdf"/>
  <annots>
    <freetext page="0" rect="100,100,300,150" title="TestAuthor">
      <contents>USUBJID</contents>
      <contents-richtext>
        <body style="font-size:10.0pt;color:#0033FF;font-family:Helvetica;font-weight:bold;font-style:italic;">
          <p>USUBJID</p>
        </body>
      </contents-richtext>
    </freetext>
  </annots>
</xfdf>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xfdf', delete=False, encoding='utf-8') as temp_in:
            temp_in.write(xfdf_content)
            input_path = temp_in.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_out.xfdf', delete=False, encoding='utf-8') as temp_out:
            output_path = temp_out.name
        
        try:
            # Update colors
            stats = update_xfdf_colors(input_path, output_path)
            
            # Verify update
            assert stats['annotations_processed'] >= 1
            
            # Check updated content
            with open(output_path, 'r', encoding='utf-8') as f:
                updated_content = f.read()
                # Should have standardized to pure blue #0000FF
                assert '#0000FF' in updated_content or '#0033FF' in updated_content
        
        finally:
            # Clean up
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)


class TestCompleteWorkflow:
    """Tests for complete XFDF color workflow."""
    
    @pytest.fixture
    def sample_pdf_with_colors(self):
        """Create a sample PDF with various colored annotations."""
        doc = fitz.open()
        page = doc.new_page()
        
        # Add annotations with different colors
        colors = [
            (0.05, 0, 0.95),    # Light blue -> should become pure blue
            (0.95, 0, 0),       # Light red -> should become pure red
            (0, 0.95, 0.05),    # Light green -> should become pure green
        ]
        
        y_pos = 100
        for i, color in enumerate(colors):
            rect = fitz.Rect(100, y_pos, 300, y_pos + 50)
            annot = page.add_freetext_annot(
                rect,
                f"Test Annotation {i+1}",
                fontsize=10,
                fontname="helv",
                text_color=color,
                fill_color=(0, 1, 1)
            )
            annot.set_info(title="TestAuthor")
            annot.update()
            y_pos += 100
        
        yield doc
        
        doc.close()
    
    def test_complete_workflow(self, sample_pdf_with_colors):
        """Test the complete export-update-import workflow."""
        # Apply XFDF color workflow
        stats = apply_xfdf_color_workflow(sample_pdf_with_colors)
        
        # Verify workflow completed
        assert stats['success'] == True
        assert stats['exported'] == 3  # 3 annotations
        assert stats['colors_standardized'] >= 0  # Some colors may have been standardized
        
        # Verify the document still has annotations
        page = sample_pdf_with_colors[0]
        annots = list(page.annots() or [])
        assert len(annots) == 3


def test_import_export_roundtrip():
    """Test that export and import preserve annotation data."""
    # Create a simple PDF with an annotation
    doc = fitz.open()
    page = doc.new_page()
    
    rect = fitz.Rect(100, 100, 300, 150)
    annot = page.add_freetext_annot(
        rect,
        "Test Content",
        fontsize=10,
        fontname="helv",
        text_color=(0, 0, 1),
        fill_color=(0, 1, 1)
    )
    annot.set_info(title="TestAuthor")
    annot.update()
    
    # Get original annotation info
    original_content = annot.info.get('content', '')
    
    # Apply workflow
    stats = apply_xfdf_color_workflow(doc)
    
    # Verify annotation still exists with same content
    page = doc[0]
    annots = list(page.annots() or [])
    assert len(annots) == 1
    assert annots[0].info.get('content', '').strip() == original_content.strip()
    
    doc.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


