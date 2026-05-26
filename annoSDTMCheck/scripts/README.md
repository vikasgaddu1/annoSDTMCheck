# Utility Scripts

This directory contains standalone utility scripts for PDF annotation processing.

## Available Scripts

### 1. standardize_pdf_annotations.py

Standardizes PDF annotations with comprehensive color correction and formatting.

**Features:**
- Color standardization (blue, red, green, orange, black)
- Cyan background for all annotations
- Author set to "Geron"
- Font size: 12pt for headers (XX = Name), 10pt for regular text
- Black borders on rectangles

**Usage:**
```bash
python standardize_pdf_annotations.py input.pdf [output.pdf]

# With inspection mode
python standardize_pdf_annotations.py input.pdf output.pdf --inspect
```

**Example:**
```bash
python standardize_pdf_annotations.py ../input/aCRF.pdf ../output/aCRF_standardized.pdf
```

---

### 2. create_pdf_bookmarks.py

Creates hierarchical bookmarks in annotated CRF PDFs based on form names and SDTM domains.

**Features:**
- Creates two bookmark sections:
  1. **Form_bookmarks** - Organized by form names
  2. **SDTM** - Organized by domain codes with forms nested under each domain

**Usage:**
```bash
python create_pdf_bookmarks.py input.pdf [output.pdf]
```

**Example:**
```bash
python create_pdf_bookmarks.py ../output/aCRF_standardized.pdf ../output/aCRF_with_bookmarks.pdf
```

**Requirements:**
- PDF must contain annotations with domain headers in format: `XX = DOMAIN NAME` (e.g., `DM = Demographics`)
- Forms should be labeled in the PDF text as: `Form: <form_name>`

---

### 3. build_exe.py / build_exe.bat

Creates standalone executable for the GUI application.

**Usage (Windows):**
```bash
build_exe.bat
```

Then select:
- Option 1: Fast build (recommended for testing)
- Option 2: Spec file build (most reliable, includes all dependencies)

---

### 4. create_backup.py

Creates timestamped backup of the project directory.

**Usage:**
```bash
python create_backup.py
```

Creates a ZIP archive in the `archive/` directory with format: `backup_YYYY-MM-DD.zip`

---

## Notes

- All scripts require PyMuPDF (fitz) to be installed: `pip install PyMuPDF`
- Scripts can be run from any directory, but paths are relative to where they're executed
- For GUI-integrated functionality, use the "Standardize Annotations" button in the main application

## Integration with GUI

The functionality from `standardize_pdf_annotations.py` and `create_pdf_bookmarks.py` has been integrated into the main GUI application under the **"Standardize Annotations"** button, which:
- Applies all standardization from `standardize_pdf_annotations.py`
- Creates dual bookmark structure from `create_pdf_bookmarks.py`
- Provides a file save dialog for output
- Shows detailed statistics after completion

These standalone scripts remain available for command-line usage and automation workflows.

