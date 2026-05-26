# PDF Annotation Standardization - Color Preservation Guide

## Overview

This solution standardizes PDF annotations while **preserving the original text colors** from the input PDF. It addresses the complex scenario where domain colors are assigned based on page order and carry across pages.

## Color Logic

### Why Preserve Colors?

Colors in the CRF follow a complex pattern:
- **First domain on a page** = Blue
- **Second domain on a page** = Red  
- **Third domain on a page** = Green
- **Domains span multiple pages** and retain their color

Because of this complexity, the script **preserves whatever colors exist** in the input PDF and only standardizes:
- Background → Cyan
- Borders → Black
- Font → Arial italic
- Sizes → 12pt (headers), 10pt (others)

## What Gets Standardized

| Element | Action |
|---------|--------|
| Text Color | **PRESERVED** (no changes) |
| Background | Changed to CYAN |
| Border | Changed to BLACK |
| Font | Changed to Arial italic |
| Font Size | 12pt for headers (XX = Label), 10pt for others |
| Text Case | UPPERCASE for non-headers |
| Author | Changed to "Geron" |

## Usage

### Quick Start
```batch
standardize_preserve.bat input\aCRF.pdf
```

### Full Command
```bash
py standardize_preserve_colors.py input\aCRF.pdf output\final.pdf output\color_report.json
```

## Output Files

1. **Standardized PDF** - With preserved colors and standardized formatting
2. **Color Report (JSON)** - Machine-readable color usage data
3. **Color Report (TXT)** - Human-readable color usage report

## Color Report

The color report helps you identify:
- All unique colors used in the PDF
- Which pages have which colors
- Which annotations use each color

### Report Format

```
================================================================================
PDF ANNOTATION COLOR USAGE REPORT
================================================================================

Total Unique Colors: 3

Unique Colors Found:
--------------------------------------------------------------------------------
  Blue: RGB(0.0, 0.0, 1.0)
  Red: RGB(1.0, 0.0, 0.0)
  Green: RGB(0.0, 0.5, 0.0)

================================================================================
COLOR USAGE BY PAGE
================================================================================

Page 2:
--------------------------------------------------------------------------------

  Blue:
    - SV=SUBJECT VISIT
    - SVOCCUR
    
  Red:
    - FA = FINDINGS ABOUT EVENTS OR INTERVENTIONS
    - FACAT
```

## Using the Color Report

### Identify Color Variations

The report helps you find annotations that might have slightly different shades:
- `RGB(0.0, 0.0, 1.0)` - Pure blue (correct)
- `RGB(0.1, 0.1, 0.9)` - Slightly off blue (needs correction)

### Manual Correction Workflow

1. Run the standardization and generate the report
2. Review the color report for variations
3. Note the page numbers with incorrect colors
4. Correct the colors in the **source PDF**
5. Re-run the standardization

## Test Results

From the latest run:
```
Statistics:
  Annotations modified:     1048
  Headers found (12pt):     156
  Text capitalized (10pt):  892
  Colors preserved:         1048
  Unique colors found:      3
  Bookmarks created:        144
```

## Important Notes

### Input PDF Never Modified
The input PDF is **never modified**. All changes are made to a copy.

### Color Preservation
Text colors from the input are **completely preserved**. The script does not:
- Change blue to red
- Change red to green
- Standardize shades
- Apply color logic

### What If Colors Are Wrong?
If the input PDF has incorrect colors:
1. The output will also have those incorrect colors
2. Use the color report to identify issues
3. Fix colors in the source PDF
4. Re-run the standardization

## Troubleshooting

### All Annotations Show Cyan
If all annotations in the report show "Cyan", this means:
- The input PDF has already been processed
- Original colors have been lost
- You need the truly original source PDF with blue/red/green colors

### Color Variations
If you see multiple shades of the same color:
- Example: `RGB(0.0, 0.0, 1.0)` and `RGB(0.05, 0.05, 0.95)`
- These are both "blue" but with slight variations
- The report helps you find and fix these

## Files

| File | Purpose |
|------|---------|
| `standardize_preserve_colors.py` | Main script with color preservation |
| `standardize_preserve.bat` | Windows batch file for easy execution |
| `COLOR_PRESERVATION_GUIDE.md` | This documentation |
| `output/*_color_report.json` | Machine-readable color report |
| `output/*_color_report.txt` | Human-readable color report |

## Example Workflow

1. **Prepare**: Ensure you have the original PDF with correct colors
2. **Standardize**: Run `standardize_preserve.bat input\aCRF.pdf`
3. **Review**: Check the color report for any variations
4. **Correct**: If needed, fix colors in source PDF and re-run
5. **Verify**: Review the standardized PDF and confirm colors are correct

## Summary

This solution:
- ✅ Preserves original text colors completely
- ✅ Applies cyan background to all
- ✅ Applies black borders to all
- ✅ Fixes font to Arial italic
- ✅ Fixes sizes (12pt headers, 10pt others)
- ✅ Generates detailed color reports
- ✅ Never modifies input PDF
- ✅ Creates hierarchical bookmarks

Perfect for maintaining complex cross-page color logic!

