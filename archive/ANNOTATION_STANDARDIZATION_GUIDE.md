# PDF Annotation Standardization Guide

## Overview

This project provides multiple methods to standardize PDF annotations for SDTM compliance. The annotations are formatted with specific fonts, sizes, colors, and text transformations.

## Method 1: Direct Standardization (RECOMMENDED)

**No manual import needed!** This method programmatically modifies the PDF annotations directly.

### Features
- Arial bold italic font
- 12pt for headers, 10pt for regular text
- UPPERCASE conversion for non-header text
- Author standardization to "Geron"
- SDTM bookmarks generation
- Blue color (#0000FF) for all annotations

### Usage

#### Option A: Using Batch File (Simplest)
```batch
standardize_direct.bat input\aCRF.pdf output\aCRF_standardized.pdf
```

#### Option B: Using Python Script
```bash
py standardize_annotations_direct.py input\aCRF.pdf output\aCRF_standardized.pdf
```

### Output
The script creates a new PDF with all annotations already standardized. No additional steps needed!

## Method 2: XFDF Export/Import (Manual)

This method exports annotations to XFDF format for manual import in Adobe Acrobat.

### Usage
```bash
py standardize_via_xfdf.py input\aCRF.pdf output\aCRF_standardized.pdf
```

### Manual Import Steps
1. Open the output PDF in Adobe Acrobat
2. Go to: Tools → Comments → More → Import Data File
3. Select the generated XFDF file
4. Save the PDF

## Files Description

### Core Scripts

| File | Description |
|------|-------------|
| `standardize_annotations_direct.py` | Direct PDF annotation modifier (recommended) |
| `standardize_via_xfdf.py` | XFDF export method (requires manual import) |
| `fix_xfdf_path.py` | Utility to fix XFDF path references |
| `xfdf_modifier.py` | XFDF content modifier |

### Batch Files

| File | Description |
|------|-------------|
| `standardize_direct.bat` | Windows batch file for easy direct standardization |
| `standardize_annotations.bat` | Legacy batch file for XFDF method |

### Documentation

| File | Description |
|------|-------------|
| `ANNOTATION_STANDARDIZATION_GUIDE.md` | This guide |
| `import_xfdf_instructions.md` | Detailed XFDF import instructions |
| `docs/XFDF_STANDARDIZATION_GUIDE.md` | Technical XFDF documentation |
| `docs/XFDF_TROUBLESHOOTING.md` | XFDF troubleshooting guide |

## Standardization Rules

### Headers (Domain definitions)
- Pattern: `XX = Description` (e.g., "DM = Demographics")
- Font: Arial Bold Italic, 12pt
- Color: Blue (#0000FF)
- Text: Preserved as-is (not converted to uppercase)

### Regular Annotations
- Font: Arial Bold Italic, 10pt
- Color: Blue (#0000FF)
- Text: Converted to UPPERCASE
- Author: "Geron"

### Bookmarks
Automatically generated SDTM bookmarks based on domain headers for easy navigation.

## Requirements

- Python 3.7+
- PyMuPDF library (`pip install PyMuPDF`)
- Adobe Acrobat (only for XFDF import method)

## Installation

1. Install Python requirements:
```bash
pip install PyMuPDF
```

2. Run the standardization:
```batch
standardize_direct.bat input\your_crf.pdf
```

## Troubleshooting

### Unicode Errors
If you see encoding errors on Windows, the scripts have been fixed to use ASCII-compatible output.

### XFDF Import Errors
If XFDF import fails in Adobe Acrobat:
1. Ensure both PDF and XFDF are in the same directory
2. Use the `fix_xfdf_path.py` utility
3. Try the direct standardization method instead

### Font Display Issues
The direct method uses PyMuPDF's font handling. If fonts don't display correctly:
1. Try the `--enhanced` flag for alternative font embedding
2. Use the XFDF method with manual Adobe Acrobat import

## Examples

### Basic Usage
```batch
REM Direct method (recommended)
standardize_direct.bat input\aCRF.pdf

REM XFDF method
py standardize_via_xfdf.py input\aCRF.pdf output\aCRF_xfdf.pdf
```

### Batch Processing
```python
# Process multiple PDFs
import glob
import subprocess

for pdf in glob.glob("input/*.pdf"):
    output = pdf.replace("input", "output").replace(".pdf", "_std.pdf")
    subprocess.run(["py", "standardize_annotations_direct.py", pdf, output])
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages in the console
3. Ensure all dependencies are installed
4. Try the alternative method if one doesn't work

## Version History

- v2.0: Added direct PDF modification (no XFDF import needed!)
- v1.5: Fixed Windows path issues in XFDF
- v1.0: Initial XFDF export/import method

