# Feature Changelog

## Version 1.2.0 - October 11, 2025

### New Feature: Configurable Bookmark Labels

#### Summary
Added configurable bookmark labels for the two main bookmark sections in standardized PDFs. Users can now customize "Form_bookmarks" and "SDTM" to match their organization's terminology or language preferences.

#### Changes Made

##### 1. Configuration System
- **File**: `src/sdtm_checker/config_manager.py`
  - Added `form_bookmark_label` field (default: "Form_bookmarks")
  - Added `sdtm_bookmark_label` field (default: "SDTM")

##### 2. GUI Configuration Tab
- **File**: `src/sdtm_checker/gui/config_tab.py`
  - Added "Form Bookmark Label" text field in Validation Settings
  - Added "SDTM Bookmark Label" text field in Validation Settings
  - Both fields appear below "Generic Author Name"
  - Integrated with load/save configuration

##### 3. Annotation Standardizer
- **File**: `src/sdtm_checker/core/annotation_standardizer.py`
  - Added bookmark label fields to `StandardizationConfig` dataclass
  - Updated `_create_bookmarks()` to use configurable labels
  - Logging now shows custom label names

##### 4. Main GUI Window
- **File**: `src/sdtm_checker/gui/main.py`
  - Retrieves bookmark labels from configuration
  - Passes labels to `StandardizationConfig`
  - Confirmation dialog displays custom labels

##### 5. Configuration Templates
- **Files**: `config/config_template.yaml`, `config/config.yaml`
  - Both updated with default bookmark labels

##### 6. Documentation
- **New File**: `docs/BOOKMARK_LABELS_FEATURE.md` - Complete feature documentation

#### User Impact

**Before:**
- Bookmark labels were hardcoded as "Form_bookmarks" and "SDTM"
- No way to customize without code changes

**After:**
- Both bookmark labels are configurable via GUI
- Support for multilingual labels
- Organization-specific naming conventions
- Settings persist across sessions

#### Testing
- ✅ Fields appear in Validation Settings tab
- ✅ Labels load and save correctly
- ✅ Custom labels appear in bookmarks
- ✅ Confirmation dialog shows custom labels
- ✅ No linter errors

#### Files Changed
1. `src/sdtm_checker/config_manager.py`
2. `src/sdtm_checker/gui/config_tab.py`
3. `src/sdtm_checker/gui/main.py`
4. `src/sdtm_checker/core/annotation_standardizer.py`
5. `config/config_template.yaml`
6. `config/config.yaml`
7. `docs/BOOKMARK_LABELS_FEATURE.md`

---

## Version 1.1.0 - October 11, 2025

### New Feature: Configurable Generic Author Name

#### Summary
Added a configurable "Generic Author Name" field in the Validation Settings tab that allows users to specify which author name should be applied to all annotations during PDF standardization.

#### Changes Made

##### 1. Configuration System
- **File**: `src/sdtm_checker/config_manager.py`
  - Added `generic_author_name` field to `Configuration.validation` dict
  - Default value: `"Geron"`

##### 2. GUI Configuration Tab
- **File**: `src/sdtm_checker/gui/config_tab.py`
  - Added `QLineEdit` field for "Generic Author Name" in Validation Settings tab
  - Field appears below "Ignore Variables" field
  - Placeholder text shows "Geron" as the default
  - Integrated with `load_configuration()` to load saved values
  - Integrated with `save_configuration()` to persist user changes
  - Falls back to "Geron" if field is empty or whitespace-only

##### 3. Main GUI Window
- **File**: `src/sdtm_checker/gui/main.py`
  - Modified `standardize_annotations()` method to:
    - Retrieve author name from configuration
    - Pass it to `StandardizationConfig` constructor
    - Display it in the confirmation dialog
  - Confirmation dialog now shows dynamic author name instead of hardcoded "Geron"

##### 4. Configuration Templates
- **Files**: 
  - `config/config_template.yaml`
  - `config/config.yaml`
  - Both updated to include `generic_author_name: Geron` in validation section

##### 5. Documentation
- **New File**: `docs/GENERIC_AUTHOR_FEATURE.md`
  - Complete feature documentation
  - Usage examples
  - Configuration details
  - Troubleshooting guide
  
- **Updated Files**:
  - `README.md` - Mentioned configurable author in standardization section
  - `docs/STANDARDIZATION_UPDATE.md` - Added author configuration details

#### User Impact

**Before:**
- Author name was hardcoded as "Geron" in the code
- Changing it required code modification

**After:**
- Author name is configurable via GUI
- No code changes needed to customize author name
- Different projects can use different author names
- Settings persist across sessions

#### Usage Instructions

1. Launch the application: `py -m sdtm_checker`
2. Navigate to **Configuration** tab → **Validation Settings** sub-tab
3. Find the **"Generic Author Name"** field
4. Enter desired author name (e.g., "Jane Smith", "Clinical Data Team")
5. Click "Save Configuration As..." to save changes
6. When standardizing PDFs, your configured name will be used

#### Technical Details

**Data Flow:**
```
User Input (GUI)
    ↓
config_tab.py (saves to config)
    ↓
ConfigurationManager (persists to YAML)
    ↓
main.py (retrieves from config)
    ↓
StandardizationConfig (passes to standardizer)
    ↓
AnnotationStandardizer (applies to annotations)
```

**Default Behavior:**
- Empty field → "Geron"
- Whitespace only → "Geron"
- Not specified in config → "Geron"

#### Testing

- ✅ Field appears in Validation Settings tab
- ✅ Default value loads correctly
- ✅ Custom value can be entered and saved
- ✅ Configuration persists across application restarts
- ✅ Confirmation dialog shows correct author name
- ✅ Annotations receive correct author after standardization
- ✅ No linter errors introduced

#### Migration

**For Existing Users:**
- No action required
- Existing config files continue to work
- Default "Geron" value applies automatically
- Field becomes editable when configuration tab is opened

#### Files Changed

1. `src/sdtm_checker/config_manager.py` - Added field to Configuration dataclass
2. `src/sdtm_checker/gui/config_tab.py` - Added GUI field and load/save logic
3. `src/sdtm_checker/gui/main.py` - Updated to use configurable author
4. `config/config_template.yaml` - Added default value
5. `config/config.yaml` - Added default value
6. `README.md` - Updated documentation
7. `docs/STANDARDIZATION_UPDATE.md` - Updated documentation
8. `docs/GENERIC_AUTHOR_FEATURE.md` - New feature documentation

#### Related Issues/Requests

This feature addresses the need to:
- Avoid hardcoding organization-specific values
- Allow different teams to use appropriate author designations
- Maintain flexibility without code changes
- Support multi-organization deployments

---

## Version 1.0.0 - October 11, 2025

### Major Update: Comprehensive PDF Standardization

#### Summary
Integrated `anno.py` and `create_bookmarks.py` functionality into the main application with dual bookmark structure and color standardization.

#### Key Features
- Color standardization (blue, red, green, orange, black)
- Cyan backgrounds for all annotations
- Black borders on rectangles
- Dual bookmark structure (Form_bookmarks + SDTM)
- Form extraction and tracking
- Improved annotation processing

#### Files Changed
- `src/sdtm_checker/core/annotation_standardizer.py` - Major refactor
- `scripts/standardize_pdf_annotations.py` - New standalone script
- `scripts/create_pdf_bookmarks.py` - New standalone script
- Multiple documentation files created

See `docs/STANDARDIZATION_UPDATE.md` for full details.

---

**Maintained by**: Development Team  
**Last Updated**: October 11, 2025

