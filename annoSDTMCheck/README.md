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
- Apply cyan backgrounds to all annotations
- Black borders on rectangles
- Configurable author name
- Dual hierarchical bookmark structure
- Configurable bookmark labels

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

### Color Standardization
Annotations are mapped to standard colors:
- **Blue** RGB(0, 0, 255) - Primary domain references
- **Red** RGB(255, 0, 0) - Important flags
- **Green** RGB(0, 255, 0) - Approved items
- **Orange** RGB(255, 165, 0) - Warnings/notes
- **Black** RGB(0, 0, 0) - General text
- **Cyan Background** RGB(0, 255, 255) - All annotations

### Bookmark Structure

The standardized PDF includes dual bookmark navigation:

#### 1. Form-Based Navigation
```
<Your Custom Label>
  ├── Demographics Form (Page 1)
  ├── Vital Signs Form (Page 5)
  └── Adverse Events Form (Page 12)
```

#### 2. Domain-Based Navigation
```
<Your Custom Label>
  ├── DM (Demographics)
  │   ├── Demographics Form
  │   └── Subject Status Form
  ├── VS (Vital Signs)
  │   └── Vital Signs Form
  └── AE (Adverse Events)
      └── Adverse Events Form
```

### Configurable Settings

All standardization features are configurable:
- **Author Name**: Set organization/person name
- **Bookmark Labels**: Use any terminology
- **Font Sizes**: 12pt for headers, 10pt for text
- **Colors**: Standardized palette

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
