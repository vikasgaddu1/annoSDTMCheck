# Color Detection and Border Fix Summary

## Issues Fixed

### 1. Color Detection Issue
**Problem**: Text color RGB(15, 0, 255) was not being detected and standardized to RGB(0, 0, 255) (pure blue).

**Root Cause**: The old code was extracting color from `annot.colors['stroke']`, which is the border/stroke color, NOT the text color. For FreeText annotations, the actual text color is stored in the Default Appearance (DA) string in the PDF.

**Solution**: Created a new function `get_text_color_from_annotation()` that:
- Parses the DA (Default Appearance) string to extract the actual text color
- Looks for the RGB pattern: `"r g b rg"` where r, g, b are in 0-1 scale
- The `rg` operator in PDF sets RGB color for non-stroking operations (fills, text)
- Falls back to `annot.colors['stroke']` if DA parsing fails

### 2. Border Color Consistency
**Problem**: Border colors were appearing as blue or cyan RGB(190, 255, 255) instead of consistently black RGB(0, 0, 0).

**Solution**: The old working code already had the correct approach:
- Set border width and style using `annot.set_border(width=1, style="S")`
- Explicitly specify `border_color=(0, 0, 0)` in the `annot.update()` call
- This ensures borders are always black regardless of other color settings

## Code Changes

### File: `src/sdtm_checker/core/annotation_standardizer.py`

#### Added Function: `get_text_color_from_annotation()`

```python
def get_text_color_from_annotation(annot: fitz.Annot) -> Tuple[float, float, float]:
    """
    Extract text color from annotation's Default Appearance (DA) string.
    
    For FreeText annotations, the text color is stored in the DA string,
    not in annot.colors['stroke']. The DA string contains color information
    in the format: "r g b rg" or "r g b RG" where r, g, b are in 0-1 scale.
    
    Args:
        annot: PyMuPDF annotation object
        
    Returns:
        Tuple of (r, g, b) in 0-1 scale, defaults to (0, 0, 0) if not found
    """
```

This function:
1. Extracts the DA string from `annot.info.get('DA', '')`
2. Uses regex to find RGB color pattern: `([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg`
3. Returns the extracted RGB values in 0-1 scale
4. Falls back to `annot.colors['stroke']` if DA parsing fails
5. Logs debug information for troubleshooting

#### Updated Color Extraction in `standardize_pdf()` Method

**Before** (Old, working for borders but not detecting text color correctly):
```python
current_colors = annot.colors
original_font_color = current_colors.get('stroke', (0, 0, 0)) if current_colors else (0, 0, 0)
font_color = standardize_color(original_font_color)
```

**After** (New, detects text color correctly):
```python
# Use the new function to properly extract text color from DA string
original_font_color = get_text_color_from_annotation(annot)
font_color = standardize_color(original_font_color)
```

#### FreeText Annotation Update

The annotation update code remains similar to the old working version:

```python
# Set border width and style
annot.set_border(width=1, style="S")

# Update FreeText annotation with standardized appearance
annot.update(
    fontsize=font_size,
    fontname="helv",  # Helvetica (closest to Arial)
    text_color=font_color,  # Standardized text color (extracted from DA string)
    fill_color=bg_color,  # Cyan fill/background (0, 1, 1)
    border_color=(0, 0, 0)  # Black border
)
```

**Key Points:**
- `text_color=font_color` uses the extracted and standardized color
- `border_color=(0, 0, 0)` explicitly ensures black borders
- `fill_color=bg_color` uses cyan background RGB(0, 255, 255)

## How It Works

### Color Standardization Algorithm

The `standardize_color()` function uses normalization:

1. **Normalization**: Divides each RGB component by the maximum intensity
2. **Blue Detection**: If blue channel is dominant (>90% when normalized) and red/green are low (<30%), standardizes to pure blue RGB(0, 0, 255)
3. **Fallback Logic**: Uses absolute thresholds if normalization doesn't provide clear results

**Example for RGB(15, 0, 255):**
- Max intensity = 255 → Normalized: r=15/255≈0.059, g=0, b=1.0
- Blue is dominant (1.0 > 0.9) ✓
- Red is low (0.059 < 0.3) ✓
- Green is low (0 < 0.3) ✓
- **Result**: Standardized to RGB(0, 0, 255) ✓

### PDF Color Storage

**Understanding DA (Default Appearance) String:**
- Format: `"/Helv 10 Tf 0.0588 0 1 rg"`
- `/Helv 10 Tf` = Helvetica font, 10pt size
- `0.0588 0 1 rg` = RGB(15, 0, 255) in 0-1 scale
- `rg` operator = sets RGB for non-stroking (text, fills)
- `RG` operator = sets RGB for stroking (lines, borders)

**Why This Matters:**
- `annot.colors['stroke']` gives border color, NOT text color
- Text color must be extracted from the DA string
- This is a PDF specification requirement

## Testing

Verified with test cases:
- ✓ RGB(15, 0, 255) → RGB(0, 0, 255) - Blue with slight red tint
- ✓ RGB(0, 61, 255) → RGB(0, 0, 255) - Blue with slight green tint  
- ✓ RGB(0, 0, 255) → RGB(0, 0, 255) - Pure blue
- ✓ RGB(255, 0, 0) → RGB(255, 0, 0) - Red (unchanged)
- ✓ RGB(0, 255, 0) → RGB(0, 255, 0) - Green (unchanged)
- ✓ RGB(255, 165, 0) → RGB(255, 165, 0) - Orange (unchanged)
- ✓ RGB(0, 0, 0) → RGB(0, 0, 0) - Black (unchanged)

## Impact

✓ **Text colors** are correctly detected from DA string and standardized  
✓ **Border colors** are consistently black RGB(0, 0, 0)  
✓ **Background colors** remain cyan RGB(0, 255, 255)  
✓ **All other functionality** preserved (bookmarks, author, font size, etc.)  
✓ **Backward compatibility** maintained

## Related Files

- `src/sdtm_checker/core/annotation_standardizer.py` - Main implementation
- `src/sdtm_checker/core/text_dimension_calculator.py` - Has similar DA parsing for fonts
- `docs/ROBUST_COLOR_STANDARDIZATION.md` - Previous color standardization documentation

## Notes

- The DA string is the PDF standard way to store text appearance
- PyMuPDF's `annot.colors` dictionary doesn't contain text color for FreeText annotations
- The `border_color` parameter in `annot.update()` is essential for black borders
- Setting border before `update()` ensures it's visible with proper width


