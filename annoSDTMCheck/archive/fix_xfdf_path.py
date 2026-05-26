"""
Fix XFDF file path references for Windows compatibility.

This script ensures the XFDF file has proper PDF references that work with Adobe Acrobat on Windows.
"""

import sys
import os
import re
from pathlib import Path


def fix_xfdf_path(xfdf_path: str, pdf_path: str = None):
    """
    Fix the PDF reference path in an XFDF file.
    
    Args:
        xfdf_path: Path to XFDF file to fix
        pdf_path: Path to PDF file (if not provided, uses same name as XFDF)
    """
    xfdf_path = Path(xfdf_path)
    
    if not xfdf_path.exists():
        print(f"Error: XFDF file not found: {xfdf_path}")
        return False
    
    # Determine PDF path
    if pdf_path:
        pdf_path = Path(pdf_path)
    else:
        # Use same name as XFDF but with .pdf extension
        pdf_path = xfdf_path.with_suffix('.pdf')
    
    if not pdf_path.exists():
        print(f"Warning: PDF file not found: {pdf_path}")
        print("Creating reference anyway (PDF must be in same directory as XFDF)")
    
    # Read XFDF content
    with open(xfdf_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get just the filename for the reference
    pdf_filename = pdf_path.name
    
    # Fix the href reference - multiple patterns to handle different formats
    patterns = [
        # Standard href attribute
        (r'<f\s+href="[^"]*"', f'<f href="{pdf_filename}"'),
        # Alternate format
        (r'<f\s+href=\'[^\']*\'', f'<f href="{pdf_filename}"'),
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write fixed content
    if content != original_content:
        # Create backup
        backup_path = xfdf_path.with_suffix('.xfdf.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"Created backup: {backup_path}")
        
        # Write fixed file
        with open(xfdf_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed XFDF file: {xfdf_path}")
        print(f"PDF reference set to: {pdf_filename}")
        return True
    else:
        print("No changes needed - XFDF already has correct format")
        # Still show current reference
        match = re.search(r'<f\s+href="([^"]*)"', content)
        if match:
            print(f"Current PDF reference: {match.group(1)}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("XFDF Path Fixer for Windows")
        print("=" * 60)
        print("\nUsage:")
        print("  python fix_xfdf_path.py <file.xfdf> [file.pdf]")
        print("\nExamples:")
        print("  python fix_xfdf_path.py output\\acrf_immp.xfdf")
        print("  python fix_xfdf_path.py output\\acrf_immp.xfdf output\\acrf_immp.pdf")
        print("\nThis will fix the PDF file reference in the XFDF to work with Adobe Acrobat.")
        return
    
    xfdf_path = sys.argv[1]
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_xfdf_path(xfdf_path, pdf_path)
    
    print("\nTo import in Adobe Acrobat:")
    print("  1. Open the PDF file")
    print("  2. Go to: Tools -> Comments -> More -> Import Data File")
    print("  3. Select the XFDF file")
    print("  4. Save the PDF")


if __name__ == "__main__":
    main()
