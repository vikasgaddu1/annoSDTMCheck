# Annotation Alignment Feature

## Overview

The annotation alignment feature automatically aligns PDF annotations that are close to each other horizontally or vertically, creating a cleaner and more professional appearance for annotated CRFs.

## What It Does

When annotations are almost aligned but not quite (within a configurable tolerance), this feature:

1. **Groups nearby annotations** - Identifies annotations that should be aligned together
2. **Calculates optimal position** - Determines the average position for the group
3. **Aligns annotations** - Moves annotations to the common position
4. **Preserves dimensions** - Only adjusts position, not size

## Alignment Types

### Horizontal Alignment

Aligns the **top edges** (Y-coordinates) of annotations that are vertically close to each other.

**Example:**
```
Before:                After:
┌─────┐               ┌─────┐
│ VAR1│ ← 100.5       │ VAR1│ ← 100.0
└─────┘               └─────┘

  ┌─────┐               ┌─────┐
  │ VAR2│ ← 101.2       │ VAR2│ ← 100.0
  └─────┘               └─────┘

    ┌─────┐               ┌─────┐
    │ VAR3│ ← 99.8        │ VAR3│ ← 100.0
    └─────┘               └─────┘
```

**Use Cases:**
- Variable labels in the same row
- Form field annotations
- Table row annotations

### Vertical Alignment

Aligns the **left edges** (X-coordinates) of annotations that are horizontally close to each other.

**Example:**
```
Before:          After:

VAR1 ← 50.3      VAR1 ← 50.0
VAR2 ← 49.8      VAR2 ← 50.0
VAR3 ← 50.5      VAR3 ← 50.0
```

**Use Cases:**
- Variable labels in a column
- Left-aligned form fields
- Table column annotations

## Configuration Options

### Basic Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `align_annotations` | Boolean | `False` | Master switch to enable/disable alignment |
| `align_horizontal` | Boolean | `True` | Enable horizontal alignment |
| `align_vertical` | Boolean | `True` | Enable vertical alignment |

### Tolerance Settings

| Setting | Type | Default | Range | Description |
|---------|------|---------|-------|-------------|
| `horizontal_tolerance` | Float | `10.0 pt` | 1-50 pt | Max **vertical** distance for horizontal grouping |
| `vertical_tolerance` | Float | `10.0 pt` | 1-50 pt | Max **horizontal** distance for vertical grouping |

**Note:** The tolerance naming refers to what type of alignment it controls:
- `horizontal_tolerance` = vertical distance for horizontal alignment
- `vertical_tolerance` = horizontal distance for vertical alignment

### Tolerance Guidelines

| Tolerance | Effect | Best For |
|-----------|--------|----------|
| **1-5 pt** | Very strict - only aligns very close annotations | Precision alignment, minimal changes |
| **5-10 pt** | Moderate - balances precision and grouping | General use, most forms |
| **10-20 pt** | Lenient - groups more annotations | Complex forms, many near-alignments |
| **20+ pt** | Very lenient - may over-group | Experimental use only |

**Recommended:** Start with 10pt and adjust based on results.

## Usage

### Method 1: GUI (Recommended)

1. **Open Configuration Tab**
   - Launch the application
   - Go to "Configuration" → "Validation Settings"

2. **Enable Alignment**
   - Check "Auto-Align Annotations"
   - Select alignment types (Horizontal, Vertical, or both)
   - Adjust tolerance values if needed

3. **Apply to PDF**
   - Set the "Annotated CRF File" path
   - Click "Standardize Annotations"
   - Alignment will be applied automatically

4. **Review Results**
   - The completion dialog shows alignment statistics:
     - Annotations aligned horizontally
     - Annotations aligned vertically

### Method 2: Test Script

For testing or batch processing:

```bash
python scripts/test_annotation_alignment.py input/aCRF.pdf output/aCRF_aligned.pdf
```

**Interactive Testing:**
```bash
python scripts/test_annotation_alignment.py input/aCRF.pdf
```

This runs through 5 test modes:
1. Dry run (preview changes)
2. Full alignment (apply changes)
3. Horizontal-only alignment
4. Vertical-only alignment
5. Custom tolerance testing

### Method 3: Python API

```python
from sdtm_checker.core.annotation_aligner import AnnotationAligner

# Create aligner
aligner = AnnotationAligner(
    horizontal_tolerance=10.0,
    vertical_tolerance=10.0,
    align_horizontal=True,
    align_vertical=True
)

# Dry run to preview
stats = aligner.align_annotations("input.pdf", dry_run=True)
print(aligner.generate_report(stats))

# Apply alignment
stats = aligner.align_annotations("input.pdf", "output.pdf", dry_run=False)
print(f"Aligned {stats.horizontal_aligned} horizontally, {stats.vertical_aligned} vertically")
```

### Method 4: Integrated with Standardization

Alignment is automatically applied during annotation standardization when enabled:

```python
from sdtm_checker.core.annotation_standardizer import (
    AnnotationStandardizer,
    StandardizationConfig
)

config = StandardizationConfig(
    align_annotations=True,
    align_horizontal=True,
    align_vertical=True,
    horizontal_tolerance=10.0,
    vertical_tolerance=10.0
)

standardizer = AnnotationStandardizer(config)
stats = standardizer.standardize_pdf("input.pdf", "output.pdf")

print(f"Horizontally aligned: {stats.get('annotations_aligned_horizontal', 0)}")
print(f"Vertically aligned: {stats.get('annotations_aligned_vertical', 0)}")
```

## How It Works

### Algorithm Overview

1. **Page-by-Page Processing**
   - Each page is processed independently
   - All annotations on the page are collected

2. **Grouping by Proximity**
   - Annotations are sorted by coordinate (Y for horizontal, X for vertical)
   - Adjacent annotations within tolerance are grouped together
   - Groups require at least 2 annotations

3. **Calculate Average Position**
   - For each group, calculate the average coordinate
   - This becomes the target alignment position

4. **Apply Alignment**
   - Each annotation's position is adjusted to the average
   - Width and height are preserved
   - Only the relevant coordinate is changed

5. **Update PDF**
   - Annotations are updated using `annot.set_rect()`
   - Changes are saved to the output file

### Example Walkthrough

**Input:** 3 annotations with Y-coordinates: 100.5, 101.2, 99.8 (tolerance = 10pt)

1. **Sort by Y:** [99.8, 100.5, 101.2]
2. **Group:** All within 10pt of average → one group
3. **Average:** (99.8 + 100.5 + 101.2) / 3 = 100.5
4. **Align:** All moved to Y = 100.5

**Result:** Perfectly aligned annotations

## Best Practices

### When to Use Alignment

✅ **Good Use Cases:**
- Variable labels that should be aligned
- Form fields in tables
- Annotations added manually with slight misalignment
- Cleaning up bulk-imported annotations

❌ **Avoid Using When:**
- Annotations are intentionally offset
- CRF has irregular layout
- Annotations overlap with form content
- Very low tolerance might miss valid groupings

### Configuration Tips

1. **Start Conservative**
   - Begin with default settings (10pt tolerance)
   - Review results before adjusting

2. **Use Dry Run First**
   - Always test with dry_run=True
   - Review alignment report before applying

3. **Adjust by PDF Type**
   - Simple forms: Lower tolerance (5-10pt)
   - Complex forms: Higher tolerance (10-15pt)
   - Messy annotations: Higher tolerance (15-20pt)

4. **Selective Alignment**
   - If only rows need alignment: Enable horizontal only
   - If only columns need alignment: Enable vertical only
   - For general cleanup: Enable both

### Quality Checks

After alignment, verify:

1. **Visual Inspection**
   - Open aligned PDF and check appearance
   - Ensure no overlaps with form content
   - Verify annotations are appropriately grouped

2. **Stats Review**
   - Check number of annotations aligned
   - Compare to expected alignment needs
   - Look for unexpected group sizes

3. **Tolerance Adjustment**
   - If too few aligned: Increase tolerance
   - If too many grouped: Decrease tolerance
   - If mixed results: Use type-specific alignment

## Integration with Other Features

### Alignment + Standardization

When combined with annotation standardization:
1. Standardization applies first (fonts, colors, borders)
2. Auto-resize runs (if enabled)
3. Alignment runs last (positioning)
4. Bookmarks are created

This order ensures optimal results.

### Alignment + Auto-Resize

These features work well together:
- Auto-resize adjusts box dimensions for content
- Alignment adjusts position for cleaner layout
- Order matters: resize before alignment

## Statistics and Reporting

### Alignment Statistics

```python
stats = AlignmentStats(
    total_annotations=50,
    horizontal_groups=3,      # Number of groups created
    vertical_groups=2,
    horizontal_aligned=8,     # Number of annotations moved
    vertical_aligned=5,
    errors=0
)
```

### Report Format

The generated report includes:
- Summary statistics
- Page-by-page breakdown
- Group information
- Before/after coordinates
- Content preview for each aligned annotation

Example:
```
================================================================================
ANNOTATION ALIGNMENT REPORT
================================================================================

Summary: Total annotations: 50, Horizontal groups: 3, Vertical groups: 2, 
         Horizontal aligned: 8, Vertical aligned: 5, Errors: 0

Alignment Operations:
--------------------------------------------------------------------------------

Page 1:
  Horizontal alignments: 3
    Page 1 [Group 0]: 'USUBJID' aligned horizontally (50.0, 100.5) -> (50.0, 100.0)
    Page 1 [Group 0]: 'RFSTDTC' aligned horizontally (150.0, 101.2) -> (150.0, 100.0)
    Page 1 [Group 0]: 'RFENDTC' aligned horizontally (250.0, 99.8) -> (250.0, 100.0)

  Vertical alignments: 2
    Page 1 [Group 0]: 'VAR1' aligned vertically (50.5, 100.0) -> (50.0, 100.0)
    Page 1 [Group 0]: 'VAR2' aligned vertically (49.8, 150.0) -> (50.0, 150.0)

================================================================================
```

## Troubleshooting

### No Alignments Detected

**Problem:** Stats show 0 alignments

**Solutions:**
- Increase tolerance values
- Check if annotations are already well-aligned
- Verify PDF has annotations

### Too Many Alignments

**Problem:** Unrelated annotations being grouped

**Solutions:**
- Decrease tolerance values
- Use type-specific alignment (horizontal or vertical only)
- Review annotation layout in PDF

### Annotations Overlap Form Content

**Problem:** Aligned annotations cover form text

**Solutions:**
- Use lower tolerance to create smaller groups
- Manually adjust annotations before alignment
- Disable alignment for problem pages

### Unexpected Grouping

**Problem:** Annotations grouped incorrectly

**Solutions:**
- Review tolerance settings
- Check annotation coordinates in PDF
- Consider if annotations should be pre-processed

## Technical Details

### Coordinate System

PDF coordinates:
- Origin (0,0) is at **bottom-left** of page
- X increases **right**
- Y increases **up**

For horizontal alignment:
- Groups by similar Y (vertical position)
- Aligns Y-coordinates (top edges)
- X-coordinates unchanged

For vertical alignment:
- Groups by similar X (horizontal position)
- Aligns X-coordinates (left edges)
- Y-coordinates unchanged

### Grouping Algorithm

```python
def group_by_proximity(annotations, tolerance):
    sorted_annots = sort_by_coordinate(annotations)
    groups = []
    current_group = [sorted_annots[0]]
    
    for annot in sorted_annots[1:]:
        avg_coord = average(current_group)
        if abs(annot.coord - avg_coord) <= tolerance:
            current_group.append(annot)
        else:
            if len(current_group) >= 2:
                groups.append(current_group)
            current_group = [annot]
    
    if len(current_group) >= 2:
        groups.append(current_group)
    
    return groups
```

### Performance

- **Speed:** ~100-500 annotations/second
- **Memory:** Minimal (processes page-by-page)
- **File Size:** No significant impact (position changes only)

## Version History

- **v1.0** (2025-10-17): Initial implementation
  - Horizontal and vertical alignment
  - Configurable tolerance
  - Dry run support
  - Integration with standardization
  - GUI controls
  - Test script

## See Also

- [Textbox Auto-Resize](TEXTBOX_AUTO_RESIZE.md) - Complementary sizing feature
- [Annotation Standardization](../archive/ANNOTATION_STANDARDIZATION.md) - Core standardization
- [User Guide](USER_GUIDE.md) - General application usage
- [Quick Start Guide](QUICK_START_GUIDE.md) - Getting started

## Support

For issues or questions:
1. Check this documentation
2. Review test script examples
3. Test with dry_run=True first
4. Adjust tolerance gradually
5. Report persistent issues with example PDFs



