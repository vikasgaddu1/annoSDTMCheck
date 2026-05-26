# Generic Author Name Configuration Feature

## Overview

The application now supports a configurable "Generic Author Name" field that allows users to specify which author name should be applied to all annotations during the standardization process.

## Feature Details

### Location

The "Generic Author Name" field is located in the **Validation Settings** tab of the GUI's configuration panel.

### Default Value

- **Default**: `Geron`
- Users can change this to any name they prefer

### How It Works

When you click the **"Standardize Annotations"** button:

1. The application reads the "Generic Author Name" from your configuration
2. All annotations in the PDF are updated to use this author name
3. The confirmation dialog displays the author name that will be applied
4. After standardization, all annotations will show the configured author name

## Usage

### Via GUI

1. Launch the application: `py -m sdtm_checker`
2. Go to the **Configuration** tab
3. Click on the **"Validation Settings"** sub-tab
4. Find the **"Generic Author Name"** field
5. Enter your desired author name (e.g., "John Doe", "Data Manager", etc.)
6. Click **"Save Configuration As..."** to save your settings
7. When you standardize annotations, your configured name will be used

### Via Configuration File

You can also edit the configuration file directly:

**File**: `config/config.yaml`

```yaml
validation:
  ignore_domains: []
  ignore_variables: ['STUDYID', 'USUBJID']
  generic_author_name: "Your Name Here"  # Change this
```

## Examples

### Example 1: Using a Personal Name

```yaml
validation:
  generic_author_name: "Jane Smith"
```

Result: All annotations will show "Jane Smith" as the author.

### Example 2: Using a Role Name

```yaml
validation:
  generic_author_name: "Clinical Data Manager"
```

Result: All annotations will show "Clinical Data Manager" as the author.

### Example 3: Using an Organization Name

```yaml
validation:
  generic_author_name: "Acme Pharma CRO"
```

Result: All annotations will show "Acme Pharma CRO" as the author.

## Benefits

1. **Consistency**: Ensures all annotations have a uniform author designation
2. **Flexibility**: Different teams can use different author names for their projects
3. **Traceability**: Makes it clear who (or which organization) standardized the annotations
4. **No Code Changes**: No need to modify code to change the author name

## Technical Details

### Configuration Structure

The author name is stored in the `validation` section of the configuration:

```python
@dataclass
class Configuration:
    validation: Dict[str, Any] = field(default_factory=lambda: {
        "ignore_domains": [],
        "ignore_variables": ["STUDYID", "USUBJID"],
        "generic_author_name": "Geron"  # ← New field
    })
```

### Integration Points

The generic author name is used by:

1. **GUI Configuration Tab** (`src/sdtm_checker/gui/config_tab.py`)
   - Provides the input field for editing
   - Loads/saves the value from/to configuration

2. **Annotation Standardizer** (`src/sdtm_checker/core/annotation_standardizer.py`)
   - Receives the author name via `StandardizationConfig`
   - Applies it to all annotations during standardization

3. **Main GUI** (`src/sdtm_checker/gui/main.py`)
   - Retrieves the author name from configuration
   - Passes it to the standardizer
   - Displays it in the confirmation dialog

### Default Behavior

If the field is:
- **Empty**: Falls back to "Geron"
- **Not specified**: Falls back to "Geron"
- **Whitespace only**: Falls back to "Geron"

This ensures the application always has a valid author name.

## Migration for Existing Users

If you have an existing `config.yaml` file that doesn't include the `generic_author_name` field:

1. The application will automatically use "Geron" as the default
2. The field will appear in the GUI with "Geron" as the placeholder
3. You can change it anytime and save your configuration

No action is required for existing installations - the feature will work seamlessly with default values.

## Command-Line Scripts

The standalone scripts in the `scripts/` directory still use hardcoded "Geron" as they don't have access to the configuration system. If you need custom author names for command-line usage, you can:

1. Edit the script directly
2. Or use the GUI which respects the configuration

## Troubleshooting

### Issue: Author name not changing

**Solution**: Make sure you:
1. Entered the name in the "Generic Author Name" field
2. Saved the configuration (via "Save Configuration As..." button)
3. Reloaded the application if it was already open

### Issue: Field is empty in GUI

**Solution**: 
- The field uses "Geron" as a placeholder - this is the default value
- You can leave it empty to use the default
- Type a new name to override the default

### Issue: Name reverts to "Geron"

**Solution**:
- Check that you saved the configuration after making changes
- Verify your `config/config.yaml` file contains the `generic_author_name` field
- Ensure the configuration file is not read-only

## Future Enhancements

Potential improvements:
- Per-domain author names (different authors for different SDTM domains)
- Author name history/favorites dropdown
- Validation for author name format
- Import author names from organizational directory

---

**Added**: October 11, 2025  
**Version**: 1.1.0

