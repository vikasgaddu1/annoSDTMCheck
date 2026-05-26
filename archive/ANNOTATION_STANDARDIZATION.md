# PDF Annotation Standardization

## Overview

The annotation standardization feature provides automated formatting of PDF annotations to ensure consistency across all annotated CRF documents. This feature also creates hierarchical bookmarks based on SDTM domain headers.

## Features

### 1. Annotation Formatting

**Headers** (Domain annotations matching `^([A-Z]{2})\s*=\s*([^=]+)$`)
- Font: Arial 12pt (Helvetica as substitute)
- Style: Bold Italic
- Case: Domain code remains UPPERCASE, description preserves original case
- Example: `DM = Demographics` (DM is uppercase, Demographics preserves case)

**Regular Text** (All other text annotations)
- Font: Arial 10pt (Helvetica as substitute)
- Style: Bold Italic
- Case: Automatically converted to UPPERCASE
- Example: `USUBJID` remains `USUBJID`

**Rectangles**
- Border: Black (RGB: 0, 0, 0)
- Fill: Transparent (preserved)

**Author**
- All annotations: Set to "Geron"

### 2. Bookmark Generation

The system creates a hierarchical bookmark structure:

```
SDTM (Parent)
├── AE - Adverse Events
│   ├── Page 5 - Form Name
│   └── Page 8 - Form Name
├── CM - Concomitant Medications
│   ├── Page 12 - Form Name
│   └── Page 15 - Form Name
└── DM - Demographics
    ├── Page 3 - Form Name
    └── Page 7 - Form Name
```

**Key Features:**
- Parent bookmark "SDTM" groups all domain bookmarks
- Each domain (DM, AE, CM, etc.) has a sub-bookmark
- Pages with multiple domains appear under each relevant domain
- Clicking a bookmark navigates to the corresponding page

## Usage

### Method 1: GUI (Recommended)

1. **Launch the application**
   ```
   py -m src.sdtm_checker.gui.main
   ```

2. **Configure the PDF path**
   - Go to the "Configuration" tab
   - Set the "Annotated CRF File" path to your PDF

3. **Click "Standardize Annotations"**
   - The button is located in the main button row
   - A dialog will ask you to confirm the standardization settings
   - Choose where to save the standardized PDF

4. **Review Results**
   - The dialog shows statistics:
     - Annotations modified
     - Headers found
     - Text capitalized
     - Rectangles styled
     - Bookmarks created
   - Click "Open PDF" to view the standardized document

### Method 2: Test Script

1. **Run from command line**
   ```
   py test_standardizer.py input\aCRF.pdf
   ```

2. **Specify output path (optional)**
   ```
   py test_standardizer.py input\aCRF.pdf output\aCRF_standardized.pdf
   ```

3. **Batch process multiple PDFs**
   ```
   py test_standardizer.py --batch input\
   ```

### Method 3: Python API

```python
from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer,
    StandardizationConfig,
    process_pdf
)

# Quick usage
stats = process_pdf("input/aCRF.pdf", "output/aCRF_standardized.pdf")
print(f"Modified {stats['annotations_modified']} annotations")

# Custom configuration
config = StandardizationConfig(
    default_author="Custom Author",
    header_size=14,
    text_size=11
)
standardizer = AnnotationStandardizer(config)
stats = standardizer.standardize_pdf("input.pdf", "output.pdf")
```

## Configuration

### Default Settings

The default configuration is defined in `StandardizationConfig`:

```python
@dataclass
class StandardizationConfig:
    header_font: str = "Helvetica"       # Base14 font
    header_size: int = 12                 # 12pt for headers
    header_bold: bool = True
    header_italic: bool = True
    
    text_font: str = "Helvetica"          # Base14 font
    text_size: int = 10                   # 10pt for text
    text_bold: bool = True
    text_italic: bool = True
    
    rectangle_border_color: Tuple[float, float, float] = (0, 0, 0)  # Black
    default_author: str = "Geron"
    
    # Regex for header detection
    header_pattern: str = r'^([A-Z]{2})\s*=\s*([^=]+)$'
```

### Customizing Settings

To use custom settings, create a configuration object:

```python
from src.sdtm_checker.core.annotation_standardizer import StandardizationConfig

config = StandardizationConfig(
    default_author="Your Name",
    header_size=14,
    text_size=11,
    header_pattern=r'^([A-Z]{2,3})\s*=\s*(.+)$'  # Allow 2-3 letter domains
)
```

## Technical Details

### Header Detection

The system uses a regular expression to identify domain headers:
```
^([A-Z]{2})\s*=\s*([^=]+)$
```

This matches:
- `DM = Demographics` ✓
- `AE = Adverse Events` ✓
- `CM=Concomitant Medications` ✓ (whitespace optional)
- `USUBJID` ✗ (not a header)
- `VS = Vital Signs (BP)` ✓

**Captured Groups:**
1. Domain code (e.g., "DM", "AE")
2. Domain description (e.g., "Demographics", "Adverse Events")

### Bookmark Structure

Bookmarks are created using PyMuPDF's table of contents (TOC) feature:
- Level 1: SDTM parent
- Level 2: Domain bookmarks (e.g., "DM - Demographics")
- Level 3: Page bookmarks (e.g., "Page 3 - Form Name")

### Font Handling

PyMuPDF uses **Base14 fonts** (built into PDF specification):
- "Helvetica" is used as an Arial substitute
- "Helvetica-Bold" for bold
- "Helvetica-BoldOblique" for bold italic
- These fonts are universally supported and don't require embedding

## Output

### Statistics Dictionary

The standardization returns a dictionary with the following keys:

```python
{
    'annotations_modified': 45,      # Total annotations processed
    'headers_found': 8,               # Domain headers detected
    'text_capitalized': 32,           # Text annotations capitalized
    'rectangles_styled': 5,           # Rectangles with black borders
    'bookmarks_created': 25,          # Total bookmarks added
    'errors': []                      # List of error messages
}
```

## Examples

### Example 1: Simple Standardization

```python
from src.sdtm_checker.core.annotation_standardizer import process_pdf

stats = process_pdf("input/aCRF.pdf")
print(f"Processed {stats['annotations_modified']} annotations")
print(f"Found {stats['headers_found']} domain headers")
```

### Example 2: With Custom Author

```python
from src.sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer,
    StandardizationConfig
)

config = StandardizationConfig(default_author="John Doe")
standardizer = AnnotationStandardizer(config)
stats = standardizer.standardize_pdf("input.pdf", "output.pdf")
```

### Example 3: Batch Processing

```python
from pathlib import Path
from src.sdtm_checker.core.annotation_standardizer import process_pdf

input_dir = Path("input")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

for pdf_file in input_dir.glob("*.pdf"):
    if "_standardized" not in pdf_file.name:
        output_file = output_dir / f"{pdf_file.stem}_standardized.pdf"
        stats = process_pdf(str(pdf_file), str(output_file))
        print(f"✓ {pdf_file.name}: {stats['annotations_modified']} annotations")
```

## Troubleshooting

### Issue: Headers Not Detected

**Problem:** Domain headers are not being identified as headers.

**Solution:**
- Check that headers match the pattern `^([A-Z]{2})\s*=\s*([^=]+)$`
- Ensure domain code is exactly 2 uppercase letters
- Verify there's an equals sign separating code and description

### Issue: Text Not Capitalizing

**Problem:** Some text annotations remain lowercase.

**Solution:**
- Verify the annotations have content (not empty)
- Check that they're text annotations (type 0)
- Ensure they don't match the header pattern

### Issue: Bookmarks Not Created

**Problem:** No bookmarks appear in the PDF.

**Solution:**
- Verify that domain headers were detected (check `headers_found` in stats)
- Open PDF in a viewer that supports bookmarks (Adobe Reader, Foxit, etc.)
- Check the logs for bookmark creation errors

### Issue: Font Doesn't Look Like Arial

**Problem:** Fonts appear different than expected.

**Solution:**
- The system uses Helvetica (Base14 font) as Arial substitute
- This is standard PDF practice and ensures universal compatibility
- For exact Arial rendering, custom font embedding would be required

## Best Practices

1. **Backup Original PDFs**
   - Always keep a copy of the original PDF
   - The backup script creates timestamped archives

2. **Test on Sample Pages First**
   - Extract a few pages and test standardization
   - Verify the results before processing the entire document

3. **Review Statistics**
   - Check that the number of headers found matches expectations
   - Verify annotation counts are reasonable

4. **Use Consistent Naming**
   - Save standardized PDFs with "_standardized" suffix
   - This prevents accidental overwriting

5. **Check Bookmarks**
   - Open the PDF and verify bookmark navigation
   - Ensure all domains are represented

## Limitations

### ⚠️ Important: Font Styling Limitation

**PDF popup text annotations (sticky notes) do not support programmatic font styling.** This is a limitation of the PDF specification, not PyMuPDF.

**What Works:**
- ✅ Content capitalization (text → UPPERCASE)
- ✅ Author changes (all → "Geron")
- ✅ Rectangle border styling (black borders)
- ✅ Bookmark creation

**What Doesn't Work:**
- ❌ Font family changes (Arial, Helvetica)
- ❌ Font size changes (12pt, 10pt)
- ❌ Bold/Italic styling for popup notes

The PDF specification does not store appearance data for popup annotations. Font rendering is controlled by the PDF viewer application (Adobe Reader, Foxit, etc.).

**See `KNOWN_LIMITATIONS.md` for details and workarounds.**

### Other Limitations

1. **Font Substitution**
   - Uses Helvetica instead of Arial (Base14 font limitation)
   - Appearance is nearly identical

2. **Annotation Types**
   - Currently supports text annotations and rectangles
   - Other annotation types (highlights, stamps) are not modified

3. **Form Name Detection**
   - Form names are extracted from page text
   - May default to "Page N" if no clear form title exists

4. **Performance**
   - Large PDFs (100+ pages) may take 10-30 seconds
   - Progress feedback is provided in the GUI

## Future Enhancements

Potential improvements for future versions:

1. **Custom Font Embedding**
   - Embed actual Arial font files
   - Requires font licensing considerations

2. **Progress Callbacks**
   - Real-time progress updates during standardization
   - Useful for large documents

3. **Selective Standardization**
   - Choose which aspects to standardize (fonts, colors, author)
   - More flexible configuration

4. **Undo Capability**
   - Ability to revert standardization
   - Would require storing original annotation data

5. **Configuration Profiles**
   - Save multiple standardization profiles
   - Quick switching between different standards

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in `logs/` directory
3. Examine error messages in the statistics dictionary
4. Verify PyMuPDF (fitz) version: `python -c "import fitz; print(fitz.__version__)"`

## References

- PyMuPDF Documentation: https://pymupdf.readthedocs.io/
- PDF Annotation Standards: ISO 32000-2 (PDF 2.0)
- Base14 Fonts: PDF Reference, Section 9.6.2.2

