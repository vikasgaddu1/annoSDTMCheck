# Configurable Bookmark Labels Feature

## Overview

The application now supports configurable bookmark labels, allowing users to customize the names of the two main bookmark sections in standardized PDFs.

## Feature Details

### Bookmark Sections

When standardizing a PDF, the application creates two hierarchical bookmark sections:

1. **Form Bookmark Section** (Default: "Form_bookmarks")
   - Organizes bookmarks by form names
   - Each form appears as a level-2 bookmark

2. **SDTM Bookmark Section** (Default: "SDTM")
   - Organizes bookmarks by SDTM domain codes
   - Each domain appears as a level-2 bookmark
   - Forms are nested under domains as level-3 bookmarks

### Configuration Location

Both labels are configurable in the **Validation Settings** tab:
- **Form Bookmark Label**: Name for the form-based bookmark section
- **SDTM Bookmark Label**: Name for the domain-based bookmark section

### Default Values

- **Form Bookmark Label**: `Form_bookmarks`
- **SDTM Bookmark Label**: `SDTM`

## Usage

### Via GUI

1. Launch the application: `py -m sdtm_checker`
2. Navigate to **Configuration** tab → **Validation Settings** sub-tab
3. Find the bookmark label fields:
   - **Form Bookmark Label**
   - **SDTM Bookmark Label**
4. Enter your desired labels
5. Save the configuration
6. When standardizing PDFs, your custom labels will be used

### Via Configuration File

Edit `config/config.yaml`:

```yaml
validation:
  generic_author_name: Geron
  form_bookmark_label: "Your Form Label"
  sdtm_bookmark_label: "Your Domain Label"
```

## Examples

### Example 1: Multilingual Labels

**English (Default):**
```yaml
form_bookmark_label: Form_bookmarks
sdtm_bookmark_label: SDTM
```

**Spanish:**
```yaml
form_bookmark_label: Formularios
sdtm_bookmark_label: Dominios_SDTM
```

**French:**
```yaml
form_bookmark_label: Formulaires
sdtm_bookmark_label: Domaines_SDTM
```

**Result in PDF:**
```
Formularios
  ├── Demográficos
  └── Signos Vitales

Dominios_SDTM
  ├── DM
  │   └── Demográficos
  └── VS
      └── Signos Vitales
```

### Example 2: Organization-Specific Labels

**Clinical Trial Organization:**
```yaml
form_bookmark_label: CRF_Pages
sdtm_bookmark_label: Data_Domains
```

**Result:**
```
CRF_Pages
  ├── Demographics Form
  └── Vital Signs Form

Data_Domains
  ├── DM
  └── VS
```

### Example 3: Detailed Labels

**Descriptive Labels:**
```yaml
form_bookmark_label: Forms_by_Name
sdtm_bookmark_label: SDTM_Domains_Structure
```

**Result:**
```
Forms_by_Name
  ├── Subject Demographics
  └── Vital Signs Assessment

SDTM_Domains_Structure
  ├── DM - Demographics
  └── VS - Vital Signs
```

### Example 4: Short Labels

**Compact Labels:**
```yaml
form_bookmark_label: Forms
sdtm_bookmark_label: Domains
```

**Result:**
```
Forms
  ├── Demographics
  └── Vital Signs

Domains
  ├── DM
  └── VS
```

## Benefits

1. **Multilingual Support**: Use labels in any language
2. **Organization Standards**: Match your organization's naming conventions
3. **User Preferences**: Customize to user/team preferences
4. **No Code Changes**: Configure without modifying source code
5. **Clarity**: Use descriptive labels that make sense to your team

## Bookmark Structure

### Form Bookmark Section
```
<Form Bookmark Label>              ← Level 1 (Configurable)
  ├── Form Name 1                  ← Level 2
  ├── Form Name 2                  ← Level 2
  └── Form Name 3                  ← Level 2
```

### SDTM Bookmark Section
```
<SDTM Bookmark Label>              ← Level 1 (Configurable)
  ├── DM                           ← Level 2 (Domain Code)
  │   ├── Demographics Form        ← Level 3 (Form)
  │   └── Subject Status Form      ← Level 3 (Form)
  ├── VS                           ← Level 2 (Domain Code)
  │   └── Vital Signs Form         ← Level 3 (Form)
  └── AE                           ← Level 2 (Domain Code)
      └── Adverse Events Form      ← Level 3 (Form)
```

## Technical Details

### Configuration Structure

```python
@dataclass
class StandardizationConfig:
    form_bookmark_label: str = "Form_bookmarks"
    sdtm_bookmark_label: str = "SDTM"
```

### Data Flow

```
User Input (GUI)
    ↓
config_tab.py (validation settings)
    ↓
Configuration (persisted to YAML)
    ↓
main.py (retrieves from config)
    ↓
StandardizationConfig (passes to standardizer)
    ↓
AnnotationStandardizer._create_bookmarks() (creates bookmarks)
    ↓
PDF Document (bookmark structure applied)
```

### Validation

- **Empty Values**: Fall back to defaults
  - Empty form label → "Form_bookmarks"
  - Empty SDTM label → "SDTM"
- **Whitespace Only**: Trimmed and fall back to defaults
- **Special Characters**: Most characters are supported by PDF specification

### Recommended Practices

✅ **Good Label Names:**
- "Forms", "CRF_Pages", "Formulaires"
- "SDTM", "Domains", "Data_Structure"
- Clear, concise, descriptive

❌ **Avoid:**
- Very long labels (>50 characters)
- Labels with only special characters
- Duplicate labels for both sections (confusing)

## Compatibility

### PDF Viewer Support

All major PDF viewers support bookmarks with custom labels:
- Adobe Acrobat Reader
- Foxit Reader
- PDF-XChange
- Browser PDF viewers (Chrome, Firefox, Edge)
- Mobile PDF apps

### Character Encoding

- Supports Unicode characters
- International characters work correctly
- Emoji are supported (though not recommended)

## Migration for Existing Users

If you have existing configurations without these fields:

1. **Automatic Defaults**: App uses "Form_bookmarks" and "SDTM"
2. **No Action Required**: Everything works with defaults
3. **Optional Customization**: Change labels anytime via GUI
4. **Backward Compatible**: Old PDFs remain unchanged

## Troubleshooting

### Issue: Labels not appearing in confirmation dialog

**Solution**: Save the configuration after entering the labels.

### Issue: Bookmarks show default labels instead of custom ones

**Solution**: 
1. Verify labels are saved in `config/config.yaml`
2. Restart the application if it was already open
3. Check that you saved the configuration after making changes

### Issue: Special characters appear incorrectly

**Solution**: 
- Avoid very unusual special characters
- Stick to alphanumeric and common punctuation
- Test with a sample PDF first

### Issue: Cannot see bookmark labels in PDF viewer

**Solution**:
- Ensure your PDF viewer has the bookmarks panel open
- In Adobe: View → Navigation Panels → Bookmarks
- In other viewers: Look for sidebar or navigation menu

## Use Cases

### Use Case 1: International Studies
Multi-country studies can use localized bookmark labels for different regions while maintaining the same data structure.

### Use Case 2: Regulatory Submissions
Different regulatory agencies might prefer different terminology - customize labels to match submission requirements.

### Use Case 3: Internal Standards
Organizations with established naming conventions can align PDF bookmarks with their internal documentation standards.

### Use Case 4: Training Materials
Educational materials can use more descriptive labels like "CRF_Forms" and "SDTM_Data_Domains" for clarity.

## Related Features

This feature works alongside:
- **Generic Author Name** - Customize annotation author
- **Dual Bookmark Structure** - Maintain both form and domain views
- **Form Extraction** - Automatic detection of form names
- **Domain Tracking** - Automatic detection of SDTM domains

See also:
- [Generic Author Feature](GENERIC_AUTHOR_FEATURE.md)
- [Standardization Update](STANDARDIZATION_UPDATE.md)
- [Feature Changelog](FEATURE_CHANGELOG.md)

## Future Enhancements

Potential improvements:
- Additional bookmark levels (sub-domains, visits, etc.)
- Template-based bookmark structures
- Import/export bookmark configurations
- Preview bookmark structure before applying
- Multiple language presets

---

**Added**: October 11, 2025  
**Version**: 1.2.0

