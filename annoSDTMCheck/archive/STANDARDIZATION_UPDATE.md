# PDF Standardization Feature Update

## Overview

The "Standardize Annotations" button in the GUI has been updated to include comprehensive annotation standardization and dual bookmark creation functionality.

## Changes Made

### 1. File Reorganization

**Moved to `scripts/` folder:**
- `anno.py` → `scripts/standardize_pdf_annotations.py`
- `create_bookmarks.py` → `scripts/create_pdf_bookmarks.py`

**Original files archived:**
- `anno.py` → `archive/anno_original.py`
- `create_bookmarks.py` → `archive/create_bookmarks_original.py`

### 2. Core Module Enhancements

Updated `src/sdtm_checker/core/annotation_standardizer.py` to include:

#### Color Standardization (from anno.py)
- **Cyan Background**: All annotations now have cyan (0, 255, 255) background
- **Color Mapping**: Font colors standardized to:
  - Blue RGB(0, 0, 255)
  - Red RGB(255, 0, 0)
  - Green RGB(0, 255, 0)
  - Orange RGB(255, 165, 0)
  - Black RGB(0, 0, 0)
- **Smart Detection**: Uses `is_header_annotation()` function to identify domain headers
- **Border Styling**: Black borders (2px) on all rectangles

#### Form Extraction (from create_bookmarks.py)
- **Pattern Recognition**: Detects "Form: <form_name>" in PDF text
- **Domain Tracking**: Associates each form with its SDTM domains
- **Fallback Logic**: Uses first significant line or page number if form name not found

#### Dual Bookmark Structure (from create_bookmarks.py)
Creates two hierarchical bookmark sections:

**1. Form_bookmarks**
```
Form_bookmarks
├── Demographics Form (page 1)
├── Vital Signs Form (page 5)
└── Adverse Events Form (page 12)
```

**2. SDTM**
```
SDTM
├── DM (Demographics)
│   ├── Demographics Form (page 1)
│   └── Subject Status Form (page 3)
├── VS (Vital Signs)
│   └── Vital Signs Form (page 5)
└── AE (Adverse Events)
    └── Adverse Events Form (page 12)
```

### 3. GUI Updates

Updated confirmation dialog to show:
- Author: Geron
- Background: Cyan for all annotations
- Colors: Standardized (blue, red, green, orange, black)
- Headers: 12pt (domain headers)
- Regular text: 10pt
- Rectangle borders: Black
- Bookmarks: Dual structure (Form_bookmarks + SDTM)

## Usage

### Via GUI (Recommended)

1. Launch the application: `py -m sdtm_checker`
2. Configure the annotated CRF file path
3. Click **"Standardize Annotations"** button
4. Choose output location in the save dialog
5. Confirm standardization settings
6. View statistics and open the result

### Via Command Line

**Standardize annotations only:**
```bash
cd scripts
python standardize_pdf_annotations.py ../input/aCRF.pdf ../output/aCRF_standardized.pdf
```

**Create bookmarks only:**
```bash
cd scripts
python create_pdf_bookmarks.py ../input/aCRF.pdf ../output/aCRF_with_bookmarks.pdf
```

**Combined workflow:**
```bash
cd scripts
python standardize_pdf_annotations.py ../input/aCRF.pdf ../output/temp.pdf
python create_pdf_bookmarks.py ../output/temp.pdf ../output/aCRF_final.pdf
```

## Benefits

1. **Consistency**: All annotations follow the same styling rules
2. **Navigation**: Dual bookmark structure for both form-based and domain-based navigation
3. **Flexibility**: Available as both GUI feature and standalone scripts
4. **Automation**: Scripts can be integrated into automated workflows
5. **Color Clarity**: Standardized colors improve readability and reduce confusion
6. **Configurable Author**: Generic Author Name can be customized per project/organization

## Technical Details

### Configuration

The standardization uses `StandardizationConfig` dataclass with defaults:
- `header_size`: 12pt
- `text_size`: 10pt
- `background_color`: Cyan (0, 1, 1)
- `rectangle_border_color`: Black (0, 0, 0)
- `default_author`: Configurable via GUI (default: "Geron")

**New Feature**: The author name is now configurable! Go to **Configuration → Validation Settings → Generic Author Name** to set your preferred author name. See [docs/GENERIC_AUTHOR_FEATURE.md](GENERIC_AUTHOR_FEATURE.md) for details.

### Annotation Types Supported

- FreeText (Type 2): Full formatting control
- Text/Popup (Type 0): Author and color updates
- Widgets (Type 13): Color and border updates
- Rectangle/Square (Type 4, 5): Border color standardization

### Domain Header Detection

Recognizes headers in format: `XX = Description`
- Must be exactly 2 uppercase letters
- Followed by equals sign
- Description must not contain quotes

## Testing

The functionality has been tested with:
- ✅ Annotation color standardization
- ✅ Cyan background application
- ✅ Form name extraction
- ✅ Domain tracking
- ✅ Dual bookmark creation
- ✅ GUI integration
- ✅ File save dialog

## Future Enhancements

Potential improvements:
- Custom color schemes via configuration
- Additional bookmark structures (by page range, etc.)
- Batch processing of multiple PDFs
- Preview before applying changes
- Undo/revert functionality

## Support

For issues or questions:
1. Check `scripts/README.md` for script documentation
2. Review `docs/USER_GUIDE.md` for GUI usage
3. Examine logs in `logs/` directory for debugging

---

**Last Updated**: October 11, 2025  
**Version**: 1.0.0

