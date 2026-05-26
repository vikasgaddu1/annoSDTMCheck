# GUI Auto-Resize Integration

## Overview

The textbox auto-resize functionality has been integrated into the GUI's "Standardize Annotations" button. Users can now enable and configure automatic resizing of textbox annotations directly from the application interface.

## What Was Changed

### 1. Configuration Tab (`src/sdtm_checker/gui/config_tab.py`)

Added three new settings in the **Validation Settings** tab:

#### Auto-Resize Textboxes (Checkbox)
- **Location:** After "SDTM Bookmark Label"
- **Default:** Unchecked (disabled)
- **Description:** Enables automatic resizing of textbox annotations during standardization
- **Tooltip:** Explains that it detects insufficient space, calculates required dimensions, and expands boxes - with a warning about potential overlaps

#### Max Width Expansion (Spin Box)
- **Range:** 0 - 500 points
- **Default:** 200 points
- **Description:** Limits how much wider textboxes can grow
- **Tooltip:** Prevents boxes from becoming too wide

#### Max Height Expansion (Spin Box)
- **Range:** 0 - 500 points
- **Default:** 300 points
- **Description:** Limits how much taller textboxes can grow
- **Tooltip:** Prevents boxes from becoming too tall

### 2. Configuration Save/Load

**Save Configuration:**
```python
validation = {
    ...
    "auto_resize_textboxes": self.auto_resize_textboxes.isChecked(),
    "resize_max_width_expansion": self.resize_max_width.value(),
    "resize_max_height_expansion": self.resize_max_height.value()
}
```

**Load Configuration:**
```python
self.auto_resize_textboxes.setChecked(
    config.validation.get("auto_resize_textboxes", False))
self.resize_max_width.setValue(
    config.validation.get("resize_max_width_expansion", 200.0))
self.resize_max_height.setValue(
    config.validation.get("resize_max_height_expansion", 300.0))
```

### 3. Main Window (`src/sdtm_checker/gui/main.py`)

#### Updated Standardize Button Tooltip
Added "• Auto-resize textboxes (if enabled in settings)" to the feature list

#### Modified Confirmation Dialog
When auto-resize is enabled, the confirmation dialog now shows:
```
• Auto-Resize: Enabled (textboxes will be expanded to fit content)
```

#### Updated StandardizationConfig Creation
```python
standardizer_config = StandardizationConfig(
    default_author=author_name,
    form_bookmark_label=form_label,
    sdtm_bookmark_label=sdtm_label,
    auto_resize_textboxes=auto_resize,
    resize_max_width_expansion=max_width,
    resize_max_height_expansion=max_height
)
```

#### Enhanced Results Dialog
When resize is enabled, the success dialog shows additional statistics:
```
• Textboxes checked: 1044
• Textboxes resized: 640
```

## How to Use

### Step 1: Enable Auto-Resize

1. Open the application
2. Go to **Configuration** tab
3. Select **Validation Settings** sub-tab
4. Scroll to the bottom
5. Check the **"Auto-Resize Textboxes"** checkbox
6. Optionally adjust the max width/height expansion limits

### Step 2: Configure Limits (Optional)

- **Max Width Expansion:** Default 200pt
  - Increase if you have very long text
  - Decrease to be more conservative
  
- **Max Height Expansion:** Default 300pt
  - Increase if you have multi-line text
  - Decrease to limit vertical growth

### Step 3: Run Standardization

1. Select your input PDF in **File Paths** tab
2. Click **"Standardize Annotations"** button
3. Choose output file location
4. Review the confirmation dialog (will show auto-resize if enabled)
5. Click **Yes** to proceed

### Step 4: Review Results

The results dialog will show:
- How many textboxes were checked
- How many were resized
- All standard standardization statistics

## Configuration File Format

When saved, the configuration file will include:

```yaml
validation:
  auto_resize_textboxes: true
  resize_max_width_expansion: 200.0
  resize_max_height_expansion: 300.0
  generic_author_name: "Geron"
  form_bookmark_label: "Form_bookmarks"
  sdtm_bookmark_label: "SDTM"
```

## Example Workflow

### Scenario: Standardize PDF with Auto-Resize

1. **Configure Settings:**
   - Check "Auto-Resize Textboxes"
   - Set Max Width: 200pt
   - Set Max Height: 300pt

2. **Select Files:**
   - Input: `aCRF.pdf`
   - Output: `aCRF_standardized.pdf`

3. **Click "Standardize Annotations"**

4. **Confirmation Dialog Shows:**
   ```
   The following standardization will be applied:
   
   • Author: Geron
   • Background: Cyan for all annotations
   • Colors: Standardized (blue, red, green, orange, black)
   • Headers: 12pt (domain headers)
   • Regular text: 10pt
   • Rectangle borders: Black
   • Bookmarks: Dual structure (Form_bookmarks + SDTM)
   • Auto-Resize: Enabled (textboxes will be expanded to fit content)
   
   Do you want to proceed?
   ```

5. **Results Dialog Shows:**
   ```
   Standardization Complete!
   
   • Annotations modified: 1044
   • Headers found: 102
   • Text capitalized: 942
   • Rectangles styled: 0
   • Bookmarks created: 285
   
   • Textboxes checked: 1044
   • Textboxes resized: 640
   
   Output saved to:
   T:\output\aCRF_standardized.pdf
   ```

## Important Notes

### ⚠️ Overlap Warning

The auto-resize feature **may cause textboxes to overlap with CRF form content**. This is because:
- Boxes are expanded in place (top-left corner preserved)
- No collision detection is performed
- Form text is not analyzed

**Recommendations:**
- Review the output PDF carefully
- Start with conservative expansion limits
- Disable auto-resize if overlaps are problematic
- Future versions may include overlap detection

### 💡 Best Practices

1. **Test First:** Try on a sample page before processing entire documents
2. **Conservative Limits:** Start with lower expansion values (100pt width, 150pt height)
3. **Review Output:** Always check the standardized PDF
4. **Document Settings:** Save configurations for different document types
5. **Backup Original:** Keep original PDFs before standardization

### 🔍 When to Use Auto-Resize

**Good Use Cases:**
- Text is clearly cut off or wrapped in original
- Annotations are consistently too small
- PDF will be reviewed after standardization
- Overlaps can be manually fixed if needed

**When to Avoid:**
- Form has dense layout with little white space
- Annotations are near form borders
- Many annotations are close to each other
- Production PDFs where overlaps are unacceptable

## Technical Details

### Integration Points

1. **Config Tab UI** → User Input
2. **Config Manager** → Save/Load Settings
3. **Main Window** → Pass Settings to Standardizer
4. **Annotation Standardizer** → Apply Resize Logic
5. **Results Display** → Show Statistics

### Data Flow

```
User Settings (GUI)
    ↓
Configuration File (YAML)
    ↓
StandardizationConfig Object
    ↓
AnnotationStandardizer
    ↓
AnnotationResizer + TextDimensionCalculator
    ↓
Modified PDF + Statistics
    ↓
Results Dialog (GUI)
```

## Future Enhancements

Possible improvements for future versions:

1. **Overlap Detection:**
   - Detect when resized boxes overlap with form content
   - Highlight problematic annotations in report

2. **Smart Relocation:**
   - Automatically move annotations to nearby empty space
   - Preserve visibility while avoiding overlaps

3. **AI-Assisted Positioning:**
   - Use vision AI to analyze page layout
   - Get intelligent placement suggestions
   - Apply recommended positions

4. **Preview Mode:**
   - Show before/after comparison in GUI
   - Allow selective resize (pick which annotations to resize)
   - Visual overlay showing potential overlaps

5. **Custom Rules:**
   - Per-domain resize limits
   - Page-specific settings
   - Annotation type filters

## Troubleshooting

### Issue: Auto-Resize Not Working

**Check:**
- Is the checkbox enabled in Validation Settings?
- Are there any FreeText annotations in the PDF?
- Check the log output for error messages

### Issue: Boxes Still Too Small

**Solutions:**
- Increase max width/height expansion values
- Check if font size is larger than expected
- Some fonts may calculate differently

### Issue: Too Many Overlaps

**Solutions:**
- Reduce max width/height expansion values
- Disable auto-resize and handle manually
- Use resize detection mode (dry-run) to identify problem annotations

### Issue: Settings Not Saved

**Check:**
- Click "Save Configuration" after changing settings
- Verify configuration file has write permissions
- Check logs for save errors

## Summary

The auto-resize feature is now fully integrated into the GUI workflow. Users can:
- ✅ Enable/disable via checkbox
- ✅ Configure expansion limits
- ✅ See confirmation before processing
- ✅ View detailed statistics after completion
- ✅ Save/load settings per configuration
- ✅ All settings persist across sessions

This provides a user-friendly interface for the powerful auto-resize functionality while maintaining awareness of potential overlap issues.


