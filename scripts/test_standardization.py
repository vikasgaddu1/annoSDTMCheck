r"""
Test script for annotation standardization workflow.
Saves output PDF and XFDF to a test directory for manual verification.

Usage:
    python scripts/test_standardization.py <input_pdf_path> [output_dir]
    
Example:
    python scripts/test_standardization.py incorrect.pdf
    python scripts/test_standardization.py incorrect.pdf C:\MyTests
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

import fitz
from sdtm_checker.core.xfdf_color_updater import export_to_xfdf


def test_standardization(input_pdf_path: str, output_dir: str = r"C:\Users\vgaddu\test"):
    r"""
    Test annotation standardization and save outputs.
    
    Args:
        input_pdf_path: Path to input PDF with annotations
        output_dir: Directory to save output files (default: C:\Users\vgaddu\test)
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("ANNOTATION STANDARDIZATION TEST")
        logger.info("=" * 80)
        
        # Open input PDF
        logger.info(f"Opening input PDF: {input_pdf_path}")
        doc = fitz.open(input_pdf_path)
        annot_count = sum(1 for p in doc for a in (p.annots() or []))
        logger.info(f"✓ PDF opened: {len(doc)} pages, {annot_count} annotations")
        
        # Generate output filenames
        input_name = Path(input_pdf_path).stem
        output_pdf = output_path / f"{input_name}_standardized.pdf"
        output_xfdf = output_path / f"{input_name}_standardized.xfdf"
        
        logger.info(f"\nOutput files:")
        logger.info(f"  PDF:  {output_pdf}")
        logger.info(f"  XFDF: {output_xfdf}")
        
        # Step 1: Create standardized XFDF
        logger.info("\n" + "-" * 80)
        logger.info("STEP 1: Creating standardized XFDF with color extraction")
        logger.info("-" * 80)
        
        # Pass the output PDF name so XFDF references the correct file
        # Use 15pt tolerance for both horizontal and vertical alignment
        exported_count = export_to_xfdf(
            doc, 
            str(output_xfdf), 
            output_pdf_name=output_pdf.name,
            auto_resize=True,
            align_annotations=True,
            horizontal_tolerance=15.0,
            vertical_tolerance=15.0
        )
        
        logger.info(f"✓ XFDF created: {exported_count} annotations exported")
        logger.info(f"✓ XFDF references: {output_pdf.name}")
        
        # Step 2: Create clean PDF (remove all annotations)
        logger.info("\n" + "-" * 80)
        logger.info("STEP 2: Creating clean PDF for manual import")
        logger.info("-" * 80)
        
        # Close and reopen to get a fresh copy
        doc.close()
        doc = fitz.open(input_pdf_path)
        
        # Remove all annotations
        removed_count = 0
        for page in doc:
            annots = list(page.annots() or [])
            for annot in annots:
                page.delete_annot(annot)
                removed_count += 1
        
        logger.info(f"✓ Removed {removed_count} annotations from clean PDF")
        
        # Save clean PDF (delete old one first if it exists)
        pdf_renamed = False
        if output_pdf.exists():
            try:
                output_pdf.unlink()
                logger.info(f"✓ Deleted existing output PDF")
            except Exception as e:
                logger.warning(f"Could not delete existing PDF (may be open): {e}")
                # Try with a new name
                output_pdf = output_path / f"{input_name}_standardized_{Path(input_pdf_path).stat().st_mtime:.0f}.pdf"
                logger.info(f"Using alternative filename: {output_pdf}")
                pdf_renamed = True
        
        doc.save(str(output_pdf), garbage=4, deflate=True)
        doc.close()
        
        logger.info(f"✓ Clean PDF saved: {output_pdf}")
        
        # Rename XFDF file to match PDF filename
        if pdf_renamed:
            new_xfdf = output_path / f"{output_pdf.stem}.xfdf"
            logger.info(f"Renaming XFDF from {output_xfdf.name} to {new_xfdf.name}")
            
            # Move/rename the XFDF file
            try:
                output_xfdf.rename(new_xfdf)
                output_xfdf = new_xfdf
                logger.info(f"✓ XFDF renamed to: {output_xfdf.name}")
            except Exception as e:
                logger.warning(f"Could not rename XFDF: {e}")
                # Copy instead
                import shutil
                shutil.copy2(output_xfdf, new_xfdf)
                output_xfdf.unlink()
                output_xfdf = new_xfdf
                logger.info(f"✓ XFDF copied to: {output_xfdf.name}")
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETE!")
        logger.info("=" * 80)
        logger.info("\n🎯 EASY METHOD - Just Double-Click the XFDF!")
        logger.info("-" * 80)
        logger.info(f"1. Double-click: {output_xfdf}")
        logger.info("   → This will automatically open the PDF with annotations in Adobe Acrobat!")
        logger.info("\n2. In Adobe Acrobat, use 'Save As' to save the PDF with annotations")
        logger.info("\n✓ Done! Your PDF now has standardized annotations embedded.")
        logger.info("\n" + "-" * 80)
        logger.info("Alternative Method (Manual Import):")
        logger.info(f"1. Open: {output_pdf}")
        logger.info("2. Tools → Comment → More → Import Data")
        logger.info(f"3. Select: {output_xfdf}")
        logger.info("\n" + "-" * 80)
        logger.info("What to Verify:")
        logger.info("   ✓ Annotations appear in correct positions")
        logger.info("   ✓ Text colors are standardized (pure blue/red)")
        logger.info("   ✓ Headers are 12pt, regular text is 10pt")
        logger.info("   ✓ Background is cyan")
        logger.info("   ✓ Borders are black")
        logger.info("   ✓ Text is top-aligned (no extra spacing)")
        logger.info("   ✓ Annotations are auto-aligned (15pt tolerance)")
        logger.info("   ✓ Widths are auto-sized to fit text")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Error during test: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Missing required arguments")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} <input_pdf_path> [output_dir]")
        print("\nExample:")
        print(f"  python {sys.argv[0]} incorrect.pdf")
        print(f"  python {sys.argv[0]} incorrect.pdf D:\\MyTests")
        sys.exit(1)
    
    input_pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\vgaddu\test"
    
    success = test_standardization(input_pdf_path, output_dir)
    sys.exit(0 if success else 1)

