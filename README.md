# SDTM Annotation Checker

<div align="center">

**A powerful GUI application for validating and standardizing SDTM annotations in PDF CRFs**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

The SDTM Annotation Checker extracts annotations from annotated CRF PDFs, validates them against SDTM datasets, and generates comprehensive mismatch reports. The application also includes powerful PDF standardization features with configurable settings.

### Key Features

✅ **Annotation Validation**
- Extract annotations from PDF CRFs automatically
- Validate against SAS7BDAT SDTM datasets
- Support for complex patterns (RELREC, SUPPXX, conditionals)
- Fuzzy matching with configurable threshold
- Comprehensive Excel reports with statistics

✅ **PDF Standardization**
- Standardize annotation colors (blue, red, green, orange, black)
- **XFDF Color Workflow** - Reliable color application via XFDF import
- Apply cyan backgrounds to all annotations
- Black borders on rectangles
- Configurable author name
- Dual hierarchical bookmark structure
- Configurable bookmark labels
- **Auto-Resize Textboxes** - Automatically expand annotations to fit content
- **Auto-Align Annotations** - Align annotations for professional appearance

✅ **User-Friendly GUI**
- Intuitive tab-based interface
- File browser dialogs
- Real-time progress tracking
- Configuration management
- Results preview and export

---

## 🚀 Quick Start

### Option 1: Using Executable (Recommended)

1. **Download** `annocheck-gui.exe` from the `dist/` folder
2. **Double-click** to launch
3. **Configure** your files in the GUI
4. **Run** validation or standardization!

### Option 2: From Source

```bash
# Clone the repository
git clone <repository-url>
cd annoSDTMCheck

# Create virtual environment
py -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
py -m sdtm_checker
```

---

## 📖 Usage

### 1. Launch the Application

```bash
# Using executable
annocheck-gui.exe

# From source
py -m sdtm_checker
```

### 2. Configure Settings

Go to **Configuration Tab** and set:

**File Paths:**
- Annotated CRF PDF file
- SDTM datasets directory (SAS7BDAT files)
- Output directory for reports

**Validation Settings:**
- Generic Author Name (default: "Geron")
- Form Bookmark Label (default: "Form_bookmarks")
- SDTM Bookmark Label (default: "SDTM")
- Fuzzy matching threshold
- Domains/variables to ignore

### 3. Run Validation

1. Click **"Run Check"** button
2. Wait for processing (progress bar shows status)
3. View results in Excel report
4. Option to open report directly from GUI

### 4. Standardize PDFs

1. Select your annotated CRF file
2. Click **"Standardize Annotations"** button
3. Choose output location
4. Confirm settings
5. Get standardized PDF with:
   - Consistent colors
   - Cyan backgrounds
   - Custom author name
   - Hierarchical bookmarks

---

## 🎨 PDF Standardization Features

The **"Standardize Annotations"** button applies comprehensive formatting to all PDF annotations. Here's a complete list of what gets standardized:

### Font Properties

- **Font Type**: Helvetica (using Helvetica-BoldOblique variant)
- **Font Style**: Bold + Italic (applied to all annotations)
- **Font Size**:
  - **Headers**: 12pt (for annotations matching "XX = Label" pattern, e.g., "DM = Demographics")
  - **Regular Text**: 10pt (for all other annotations)

### Text Colors

Text colors are standardized to a consistent palette (only three colors supported):
- **Blue**: RGB(0, 0, 255) - Primary domain references
- **Red**: RGB(255, 0, 0) - Important flags
- **Green**: RGB(0, 124, 0) - Approved items

The standardization uses intelligent color detection that maps various shades to these standard colors based on dominant color channels. Colors that don't match blue, red, or green patterns are kept as-is (original color preserved).

**Note**: Cyan text color is not used since the background is cyan (would be invisible). Black is only used as a fallback for invalid colors, not as a standardized text color.

### Background Colors

- **Background Color**: Cyan RGB(0, 255, 255) - Applied to **all** annotations
- All annotations receive a cyan fill/background color for consistent appearance

### Border Properties

- **Border Color**: Black RGB(0, 0, 0)
- **Border Width**: 2 points
- **Border Style**: Solid (S)
- Applied to all rectangle annotations and other shape annotations

### Textbox Size (Auto-Resize)

- **Auto-Resize**: Enabled by default
- **Width Expansion**: Automatically expands to fit content (max 200.0 points expansion)
- **Height Expansion**: Automatically expands to fit content (max 300.0 points expansion)
- Textboxes are checked and resized only if content doesn't fit with the standardized font
- **Skip Pages**: Users can specify page numbers to skip from auto-resizing
  - Format: Comma-separated page numbers (1-indexed), e.g., "1, 5, 10"
  - Configured in Configuration tab → Resize Settings → "Skip Pages"
  - Useful for pages with complex CRF layouts where auto-resizing may cause issues
  - Other standardization (colors, fonts, alignment) still applies to skipped pages

### Alignment (Auto-Align)

- **Horizontal Alignment**: Enabled by default with 1.0 point tolerance
- **Vertical Alignment**: Enabled by default with 10.0 point tolerance
- Aligns annotations on the same page for professional appearance
- **Skip Pages**: Users can specify page numbers to skip from auto-alignment
  - Format: Comma-separated page numbers (1-indexed), e.g., "1, 5, 10"
  - Configured in Configuration tab → Alignment Settings → "Skip Pages"
  - Useful for pages with complex CRF layouts where auto-alignment may cause issues
  - Other standardization (colors, fonts, resize) still applies to skipped pages

### Author Information

- **Author Name**: Configurable (default: "Geron")
- All annotations are updated with the specified author name
- Set via Configuration tab → "Generic Author Name"

### Bookmark Structure

Creates dual hierarchical bookmark navigation with **configurable titles**:

#### 1. Form-Based Navigation
```
<Your Custom Label> (default: "Form_bookmarks")
  ├── Demographics Form (Page 1)
  ├── Vital Signs Form (Page 5)
  └── Adverse Events Form (Page 12)
```

#### 2. Domain-Based Navigation
```
<Your Custom Label> (default: "SDTM")
  ├── DM (Demographics)
  │   ├── Demographics Form
  │   └── Subject Status Form
  ├── VS (Vital Signs)
  │   └── Vital Signs Form
  └── AE (Adverse Events)
      └── Adverse Events Form
```

**Configurable Bookmark Titles**: Users can customize both bookmark section labels:
- **Form Bookmark Label**: Configured in Configuration tab → Validation Settings → "Form Bookmark Label" (default: "Form_bookmarks")
- **SDTM Bookmark Label**: Configured in Configuration tab → Validation Settings → "SDTM Bookmark Label" (default: "SDTM")
- Supports multilingual labels and custom terminology

### XFDF Color Workflow

The application uses an advanced XFDF (XML Forms Data Format) workflow to ensure colors are reliably applied:

1. **Export** - Annotations exported to XFDF after standardization
2. **Update** - Colors standardized in XFDF format
3. **Import** - XFDF imported back to PDF

This approach ensures that font colors display correctly in Adobe Acrobat. The workflow is enabled by default but can be disabled in configuration if not needed.

See [XFDF Color Workflow Documentation](docs/XFDF_COLOR_WORKFLOW.md) for technical details.

### Summary

When you click **"Standardize Annotations"**, the following happens to every annotation:

1. ✅ Font set to Helvetica-BoldOblique (bold + italic)
2. ✅ Font size set to 12pt (headers) or 10pt (regular text)
3. ✅ Text color standardized to blue/red/green palette (only these three colors)
4. ✅ Background color set to cyan RGB(0, 255, 255)
5. ✅ Border color set to black RGB(0, 0, 0) with 2pt width
6. ✅ Textbox size auto-expanded to fit content (if needed, can skip specific pages)
7. ✅ Author name updated to configured value
8. ✅ Annotations aligned horizontally and vertically (can skip specific pages)
9. ✅ Dual bookmark structure created with configurable titles
10. ✅ Colors applied via XFDF workflow for reliability

---

## 🎯 Complete Feature List

This section documents **all functionalities** available in the SDTM Annotation Checker application.

### 1. Annotation Validation Features

#### 1.1 Annotation Extraction
- **PDF Annotation Extraction**: Automatically extracts all annotations from PDF CRFs
- **Multiple Annotation Types**: Supports FreeText, Text, Highlight, Underline, and other annotation types
- **Position Tracking**: Captures page numbers and coordinates for each annotation
- **Content Cleaning**: Automatically cleans and normalizes annotation text

#### 1.2 Supported Annotation Patterns
The application supports **24+ annotation patterns**, including:

**Basic Patterns:**
- `DOMAIN.VARIABLE` (e.g., `DM.SUBJID`)
- `DOMAIN-VARIABLE` (e.g., `DM-SUBJID`)
- `DOMAIN|VARIABLE` (e.g., `DM|SUBJID`)
- `DOMAIN VARIABLE = "value"` (e.g., `DM SUBJID = "123"`)
- `DOMAIN=DM VARIABLE=SUBJID [VALUE="value"]`
- `VARIABLE = 'value'` (e.g., `SUBJID = '123'`)
- `VARIABLE` (single variable name)

**Complex Patterns:**
- `VAR1,VAR2,... = 'value'` (e.g., `FACAT,FAOBJ = 'value'`)
- `VAR1/VAR2` (e.g., `DSSTDTC/RFICDTC`)
- `VAR1-VAR4` (variable ranges)
- `VARIABLE in SUPPDOMAIN [when VALUE]`
- `VARIABLE when VALUE` (e.g., `VSORRES when VSTESTCD=HEIGHT`)
- `VAR1,VAR2,... when COND` (e.g., `VSORRES,VSORRESU when VSTESTCD=HEIGHT`)
- `VAR1/VAR2 when COND = VALUE`
- `VAR = 'value' when COND = VALUE`
- `VARIABLE when TESTCD = VALUE` (e.g., `PFORRES when PFTESTCD = CYTABNRM`)
- `VARIABLE in DOMAIN when COND` (e.g., `RELID in RELREC when FASEQ = AEGRPID`)
- `DOMAIN when COND = VALUE` (e.g., `RELREC when FASPID = AESPID`)

**Comment Patterns:**
- `[VALUE]` (bracketed values, treated as comments)
- `NOTE: ...` (comment format)
- `DOMAIN = Label` (e.g., `SV = Subject Visits`)
- `NOT SUBMITTED` (comment markers)

#### 1.3 SDTM Dataset Validation
- **SAS7BDAT Support**: Reads SDTM datasets in SAS7BDAT format
- **Multi-Domain Support**: Validates against multiple SDTM domains simultaneously
- **Variable Existence Check**: Verifies that annotated variables exist in SDTM datasets
- **Domain Detection**: Automatically detects domain from annotation patterns
- **Dataset Coverage Analysis**: Identifies unused datasets and variables

#### 1.4 Fuzzy Matching
- **Configurable Threshold**: Adjustable similarity threshold (0.0 - 1.0, default: 0.85)
- **Typo Tolerance**: Handles minor typos and case variations
- **Smart Matching**: Uses string similarity algorithms for flexible validation
- **Enable/Disable**: Can be toggled on/off in configuration

#### 1.5 Domain and Variable Filtering
- **Ignore Domains**: Skip validation for specific domains (comma-separated list)
- **Ignore Variables**: Skip validation for specific variables (comma-separated list)
- **Use Cases**: Useful for standard identifiers (STUDYID, USUBJID) or domains not yet annotated

### 2. PDF Standardization Features

See the [PDF Standardization Features](#-pdf-standardization-features) section above for complete details.

**Summary:**
- Font standardization (Helvetica-BoldOblique, 12pt/10pt)
- Color standardization (Blue, Red, Green only)
- Cyan backgrounds for all annotations
- Black borders (2pt width)
- Auto-resize textboxes with configurable limits
- Auto-align annotations (horizontal/vertical)
- Skip pages functionality for resize/alignment
- Configurable author name
- Dual bookmark structure with configurable titles
- XFDF color workflow for reliable color application

### 3. Pattern Management

#### 3.1 Custom Pattern Creation
- **Add Patterns**: Create custom annotation patterns via GUI
- **Pattern Editor**: Dialog-based editor for pattern configuration
- **Regex Support**: Full regex pattern support with capture groups
- **Pattern Testing**: Test patterns against sample text before saving
- **Pattern Validation**: Validates regex syntax and group definitions

#### 3.2 Pattern Configuration
- **Pattern Name**: Descriptive name for the pattern
- **Description**: Optional description of pattern purpose
- **Regex Pattern**: Regular expression matching annotation format
- **Capture Groups**: Dictionary mapping group names to capture group indices
- **Example**: `{"domain": 1, "variable": 2}` for pattern `^([A-Z]{2})\.([A-Z0-9_]+)$`

#### 3.3 Pattern Operations
- **Edit Patterns**: Modify existing patterns
- **Delete Patterns**: Remove unused patterns
- **Test Patterns**: Interactive testing dialog
- **Pattern List**: View all configured patterns in a list

### 4. Report Generation

#### 4.1 Excel Report Structure
Reports include multiple sheets:

**Summary Sheet:**
- Total annotations processed
- Match/mismatch statistics
- Domain coverage summary
- Variable coverage summary
- Validation success rate

**Mismatches Sheet:**
- Detailed list of validation failures
- Annotation text and location (page, coordinates)
- Expected vs actual values
- Domain and variable information
- Severity classification (Error, Warning, Info)

**SDTM Variables Sheet:**
- Complete list of variables per domain
- Variable attributes and metadata
- Coverage analysis
- Unused variables identification

**Unmatched Annotations Sheet:**
- Annotations that couldn't be matched to SDTM variables
- Pattern type information
- Suggestions for resolution

**Unused Datasets Sheet:**
- SDTM datasets that weren't referenced in annotations
- Helps identify missing annotations

#### 4.2 Report Features
- **Auto-Column Sizing**: Automatically adjusts column widths
- **Color Coding**: Severity-based color coding (red/yellow/green)
- **Formatted Output**: Professional Excel formatting with headers
- **Timestamp**: Includes generation timestamp
- **Statistics**: Comprehensive statistics and summaries

### 5. Configuration Management

#### 5.1 Configuration Tabs

**File Paths Tab:**
- Annotated CRF File (PDF)
- SDTM Directory (folder containing .sas7bdat files)
- Output Directory (for reports and standardized PDFs)
- Default Output File (Excel report filename)

**Pattern Management Tab:**
- View all annotation patterns
- Add/Edit/Delete patterns
- Test patterns interactively

**Validation Settings Tab:**
- **General Settings:**
  - Fuzzy Matching (enable/disable)
  - Fuzzy Threshold (0.0 - 1.0)
  - Ignore Domains (comma-separated)
  - Ignore Variables (comma-separated)
  - Generic Author Name
  - Form Bookmark Label
  - SDTM Bookmark Label
  - Normalize Quotes (enable/disable)
- **Resize Settings:**
  - Auto-Resize Textboxes (enable/disable)
  - Max Width Expansion (points)
  - Max Height Expansion (points)
  - Skip Pages (comma-separated page numbers)
- **Alignment Settings:**
  - Auto-Align Annotations (enable/disable)
  - Horizontal Alignment (enable/disable)
  - Vertical Alignment (enable/disable)
  - Horizontal Tolerance (points)
  - Vertical Tolerance (points)
  - Skip Pages (comma-separated page numbers)

#### 5.2 Configuration Operations
- **Save Configuration As...**: Save current settings to a named file
- **Load Configuration...**: Load settings from a saved file
- **Reset to Default**: Restore all settings to defaults
- **Multiple Configs**: Maintain different configs for different projects
- **Auto-Save**: Configuration automatically saved on changes
- **Config Validation**: Validates file paths and settings before saving

### 6. GUI Features

#### 6.1 Main Window
- **Tab-Based Interface**: Organized configuration tabs
- **Progress Bar**: Real-time progress tracking during operations
- **Status Bar**: Shows current configuration file and status
- **Log Viewer**: Integrated log output with dark theme
- **Window State Persistence**: Remembers window size and position

#### 6.2 Main Buttons
- **Run Check**: Validates annotations against SDTM datasets
- **Standardize Annotations**: Standardizes PDF annotations and creates bookmarks
- **Save Configuration As...**: Saves current configuration
- **Load Configuration...**: Loads saved configuration
- **Reset to Default**: Resets all settings

#### 6.3 Log Viewer
- **Real-Time Logging**: Shows application logs in real-time
- **Dark Theme**: Easy-to-read dark color scheme
- **Clear Log**: Button to clear log messages
- **Copy to Clipboard**: Copy all log messages to clipboard
- **Timestamped Entries**: Each log entry includes timestamp
- **Log Levels**: Shows INFO, WARNING, ERROR levels

#### 6.4 Help System
- **F1 Key**: Opens User Guide in browser
- **Quick Start Guide**: 5-minute setup guide (Help menu)
- **What's This? Mode**: Shift+F1 for context-sensitive help
- **Tooltips**: Hover tooltips on all UI elements
- **About Dialog**: Version and feature information
- **HTML Documentation**: All docs open as formatted HTML

#### 6.5 Menu Bar
- **Help Menu**:
  - User Guide (F1)
  - Quick Start Guide
  - What's This? (Shift+F1)
  - About

### 7. File Management

#### 7.1 File Browser Dialogs
- **PDF File Selection**: Browse for annotated CRF PDFs
- **Directory Selection**: Browse for SDTM directory and output directory
- **File Filters**: Filter by file type (.pdf, .sas7bdat, .xlsx, .yaml)
- **Recent Paths**: Remembers recently used paths

#### 7.2 File Validation
- **Path Validation**: Checks if files/directories exist
- **File Type Validation**: Verifies file extensions
- **SDTM Dataset Detection**: Automatically detects .sas7bdat files
- **Error Messages**: Clear error messages for invalid paths

### 8. Error Handling and Validation

#### 8.1 Input Validation
- **File Path Validation**: Ensures files exist before processing
- **Configuration Validation**: Validates all settings before operations
- **Pattern Validation**: Validates regex patterns and capture groups
- **Page Number Validation**: Validates skip page numbers

#### 8.2 Error Reporting
- **User-Friendly Messages**: Clear, actionable error messages
- **Error Logging**: Detailed error logging for debugging
- **Exception Handling**: Graceful handling of errors
- **Progress Indication**: Shows progress even during errors

### 9. Advanced Features

#### 9.1 Threading
- **Background Processing**: Validation runs in separate thread
- **Non-Blocking UI**: UI remains responsive during processing
- **Progress Updates**: Real-time progress updates via signals
- **Cancellation Support**: Can cancel long-running operations

#### 9.2 State Management
- **UI State Cache**: Remembers UI state between sessions
- **Window State**: Saves window size, position, and geometry
- **Configuration Persistence**: Auto-saves configuration changes
- **Session Recovery**: Can recover from crashes

#### 9.3 Performance
- **Efficient PDF Processing**: Optimized PDF annotation extraction
- **Batch Processing**: Processes multiple annotations efficiently
- **Memory Management**: Efficient memory usage for large PDFs
- **Progress Tracking**: Shows progress for long operations

### 10. Integration Features

#### 10.1 SDTM Dataset Integration
- **Multiple Format Support**: Reads SAS7BDAT files
- **Domain Auto-Detection**: Automatically detects domains from filenames
- **Variable Extraction**: Extracts variable names and metadata
- **Dataset Validation**: Validates dataset structure

#### 10.2 PDF Integration
- **PyMuPDF Integration**: Uses PyMuPDF (fitz) for PDF operations
- **Annotation Manipulation**: Full annotation creation/modification
- **XFDF Support**: Export/import annotations via XFDF format
- **Bookmark Creation**: Creates hierarchical PDF bookmarks

### 11. Export and Output

#### 11.1 Report Export
- **Excel Format**: Exports validation reports as .xlsx files
- **Multiple Sheets**: Organized into multiple sheets
- **Formatted Output**: Professional formatting with colors and styles
- **Auto-Naming**: Automatic timestamp-based naming

#### 11.2 PDF Export
- **Standardized PDFs**: Saves standardized PDFs with consistent formatting
- **XFDF Export**: Optionally exports annotations as XFDF files
- **Output Location**: Configurable output directory
- **File Naming**: Automatic naming with "_standardized" suffix

---

## 📁 Project Structure

```
annoSDTMCheck/
├── src/sdtm_checker/          # Main application code
│   ├── gui/                   # PyQt6 GUI components
│   ├── core/                  # Core functionality
│   ├── validators/            # Validation logic
│   └── __main__.py            # Entry point
├── config/                    # Configuration files
│   ├── config_template.yaml   # Default settings
│   └── config.yaml            # Active configuration
├── scripts/                   # Utility scripts
│   ├── standardize_pdf_annotations.py
│   ├── create_pdf_bookmarks.py
│   └── build_exe.py
├── docs/                      # Documentation
│   ├── USER_GUIDE.md          # Comprehensive user guide
│   ├── QUICK_START_GUIDE.md   # 5-minute quick start
│   └── FEATURE_CHANGELOG.md   # Version history
├── assets/                    # Application resources
│   └── icon.ico               # Application icon
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔧 Configuration

### Configuration File Format

```yaml
# Validation Settings
validation:
  ignore_domains: []
  ignore_variables: ['STUDYID', 'USUBJID']
  generic_author_name: "Geron"
  form_bookmark_label: "Form_bookmarks"
  sdtm_bookmark_label: "SDTM"

# File Paths
paths:
  annotated_crf_file: ''
  sdtm_directory: 'sdtm_data/'
  output_directory: 'output/'
  default_output_file: 'validation_report.xlsx'

# Annotation Patterns
annotation_patterns:
  settings:
    fuzzy_matching: true
    fuzzy_threshold: 0.8
  patterns:
    - name: DOMAIN_VAR
      regex: ^([A-Z]{2})\.([A-Z0-9_]+)$
      groups:
        domain: 1
        variable: 2
```

### Managing Configurations

- **Save**: Click "Save Configuration As..." to create named configs
- **Load**: Click "Load Configuration..." to switch between configs
- **Reset**: Click "Reset to Default" to restore defaults
- **Multiple Configs**: Maintain different configs for different projects

---

## 🛠️ Building Executable

To create a standalone .exe file:

```bash
cd scripts
build_exe.bat
```

Choose Option 2 (Spec file build) for the most reliable build.

The executable will be created in `dist/annocheck-gui.exe` (~100MB, includes all dependencies).

---

## 📊 Validation Report

The generated Excel report includes:

1. **Summary Sheet**
   - Total annotations processed
   - Match/mismatch statistics
   - Domains and variables coverage

2. **Mismatches Sheet**
   - Annotation text and location
   - Expected vs actual values
   - Domain and variable details
   - Validation status

3. **SDTM Variables Sheet**
   - Complete variable list per domain
   - Variable attributes
   - Coverage analysis

---

## 🎯 Use Cases

### Clinical Data Management
- Validate CRF annotations before database lock
- Ensure consistency between CRFs and SDTM
- Standardize PDF formats for submissions

### Quality Assurance
- Automated validation reduces manual effort
- Comprehensive reports for audit trails
- Consistent formatting across studies

### Regulatory Submissions
- Standardized PDFs meet submission requirements
- Clear bookmark navigation for reviewers
- Configurable labels for different agencies

### International Studies
- Multilingual bookmark labels
- Organization-specific branding
- Team-based author identification

---

## 📚 Documentation

### In-App Help (Recommended)
The application includes a comprehensive Help menu that opens documentation in your browser:
- **Press F1** or **Help → User Guide** - Complete usage instructions
- **Help → Quick Start Guide** - Get started in 5 minutes
- **Press Shift+F1** or **Help → What's This?** - Context-sensitive help for any UI element
- **Help → About** - Version and feature information

### Documentation Files
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive usage instructions
- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Fast 5-minute setup guide
- **[CHANGELOG](CHANGELOG.md)** - Complete version history and release notes
- **[Feature Changelog](docs/FEATURE_CHANGELOG.md)** - Feature-specific documentation
- **[Scripts README](scripts/README.md)** - Standalone script documentation

---

## 🔄 Recent Updates

### Version 1.2.1 (Current)
- ✨ **Integrated Help System** - Press F1 for instant documentation in browser
- ✨ **HTML Documentation Viewer** - All docs open as beautifully formatted HTML
- ✨ **Quick Start Guide** - 5-minute setup guide accessible from Help menu
- ✨ **What's This? Mode** - Context-sensitive help (Shift+F1)
- 🐛 **Fixed HTML Layout** - Documentation displays correctly without shrinking
- 📝 **Enhanced Tooltips** - Comprehensive help on every UI element

### Version 1.2.0
- ✨ Configurable bookmark labels
- ✨ Dual hierarchical bookmark structure
- 🎨 Enhanced PDF standardization
- 📝 Improved documentation

### Version 1.1.0
- ✨ Configurable author name
- 🐛 Bug fixes and improvements
- 📊 Enhanced validation reporting

---

## 🛡️ System Requirements

- **OS**: Windows 10+ (executable), Windows/macOS/Linux (source)
- **Python**: 3.8 or higher (source installation)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 200MB for application + space for data files

---

## 📦 Dependencies

Core dependencies:
- PyQt6 - GUI framework
- PyMuPDF - PDF processing
- pandas - Data manipulation
- pyreadstat - SAS file reading
- openpyxl - Excel report generation
- PyYAML - Configuration management

---

## 🤝 Support

For issues or questions:
1. Press **F1** in the app to open the User Guide, or check the [User Guide](docs/USER_GUIDE.md)
2. Use **Help → Quick Start** in the app, or review [Quick Start](docs/QUICK_START_GUIDE.md)
3. Examine logs in `logs/` directory
4. Check configuration in `config/config.yaml`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

Built with:
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [pandas](https://pandas.pydata.org/) - Data analysis
- [pyreadstat](https://github.com/Roche/pyreadstat) - SAS file reading

---

<div align="center">

**Made with ❤️ for Clinical Data Management**

[Documentation](docs/USER_GUIDE.md) • [Quick Start](docs/QUICK_START_GUIDE.md) • [Changelog](CHANGELOG.md)

</div>
