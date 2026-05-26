# Changelog

All notable changes to the SDTM Annotation Checker project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-10-11

### Added
- **Integrated Help System**: Press F1 anywhere in the application for instant access to the User Guide
- **HTML Documentation Viewer**: All documentation now opens as beautifully formatted HTML in your default browser
  - No need for markdown editors
  - Professional styling with modern CSS
  - Print-friendly and searchable
- **Quick Start Guide**: New 5-minute setup guide accessible from Help menu
- **What's This? Mode**: Context-sensitive help system (Shift+F1) - click any UI element for detailed help
- **Enhanced Tooltips**: Comprehensive tooltips on all buttons, fields, and settings
- **Help Menu**: Complete menu with User Guide, Quick Start, What's This?, and About options

### Fixed
- **HTML Layout Issues**: Fixed "conical" shrinking layout in documentation
  - Container now maintains consistent 900px width
  - Proper box-sizing to prevent overflow
  - Improved paragraph and list processing
  - FAQ sections display correctly with proper spacing
  - Questions and answers appear on separate lines
- **Missing Quick Start**: Created missing Quick Start Guide referenced in Help menu
- **Documentation Paths**: Fixed file path resolution for both development and production environments

### Changed
- Help menu now opens documentation in browser instead of requiring markdown editor
- Improved markdown to HTML conversion with better formatting
- Enhanced CSS styling for documentation pages
- Reorganized documentation files into `docs/` folder

### Technical
- New module: `src/sdtm_checker/gui/html_viewer.py` - HTML conversion and browser opening
- Updated: `src/sdtm_checker/gui/main.py` - Simplified help menu functions
- Updated: `annocheck-gui.spec` - Ensured docs folder included in builds

## [1.2.0] - 2025-06-09

### Added
- **Configurable Bookmark Labels**: Customize bookmark structure labels
  - Form bookmark label (default: "Form_bookmarks")
  - SDTM bookmark label (default: "SDTM")
  - Configurable via GUI and YAML config
- **Dual Hierarchical Bookmark Structure**: Two-level bookmark organization
  - Form-based bookmarks for CRF navigation
  - SDTM domain-based bookmarks for data review
- **Enhanced PDF Standardization**: Improved color correction and annotation formatting

### Changed
- Updated configuration schema to support bookmark customization
- Improved PDF bookmark creation algorithm
- Enhanced standardization color handling

### Fixed
- Color preservation issues in PDF standardization
- Bookmark creation edge cases

## [1.1.0] - 2025-06-08

### Added
- **Configurable Generic Author Name**: Set custom author names for standardized annotations
  - Default: "Geron"
  - Configurable via GUI settings
  - Applied during PDF standardization
- **Author Filtering**: Filter annotations by author for validation
  - Enable/disable via checkbox
  - Specify author name or use "GENERIC" for all
- **Enhanced Validation Reporting**: Improved Excel report generation
  - Summary statistics sheet
  - Detailed validation results
  - Missing variables report
  - Invalid patterns report

### Changed
- Updated GUI with author configuration options
- Improved annotation extraction to preserve author information
- Enhanced YAML configuration schema

### Fixed
- Annotation author handling in standardization
- Configuration persistence issues
- GUI state management improvements

## [1.0.0] - 2025-06-07

### Added
- **Initial Release**: First stable version of SDTM Annotation Checker
- **Core Features**:
  - PDF annotation extraction from CRF files
  - SDTM dataset validation (SAS7BDAT format)
  - Excel report generation
  - Pattern-based annotation parsing
  - Fuzzy matching support
  - Case-sensitive/insensitive matching
- **GUI Application**:
  - PyQt6-based graphical interface
  - Configuration management
  - File browser dialogs
  - Progress tracking
  - Results preview
- **PDF Standardization**:
  - Annotation color standardization (cyan backgrounds)
  - Black borders on rectangles
  - Consistent text formatting
  - Bookmark creation
- **Configuration System**:
  - YAML-based configuration files
  - Pattern management
  - Validation settings
  - Path management
  - Save/load functionality
- **Pattern Support**:
  - DOMAIN.VARIABLE format (e.g., DM.SUBJID)
  - DOMAIN-VARIABLE format (e.g., VS-VSORRES)
  - Variable only format (e.g., SUBJID)
  - RELREC patterns
  - SUPPXX patterns
  - Conditional patterns
- **Validation Features**:
  - Domain and variable validation
  - Fuzzy matching with configurable threshold
  - Case sensitivity options
  - Ignore lists for domains/variables
  - Comprehensive error reporting
- **Logging & Auditing**:
  - Audit trail in JSON format
  - Daily log rotation
  - Error logging
  - Operation tracking

### Technical
- Python 3.8+ support
- PyQt6 for GUI
- PyMuPDF for PDF processing
- pandas for data manipulation
- pyreadstat for SAS file reading
- openpyxl for Excel generation
- PyYAML for configuration
- PyInstaller for executable builds

## [Unreleased]

### Planned Features
- Export to other formats (CSV, JSON)
- Batch processing of multiple PDFs
- Command-line interface improvements
- Database storage for validation history
- Enhanced reporting with charts
- PDF comparison tools
- API for integration with other systems

---

## Version History Summary

| Version | Date | Key Feature |
|---------|------|-------------|
| 1.2.1 | 2025-10-11 | Integrated Help System & HTML Viewer |
| 1.2.0 | 2025-06-09 | Configurable Bookmarks |
| 1.1.0 | 2025-06-08 | Configurable Author Names |
| 1.0.0 | 2025-06-07 | Initial Release |

---

## Upgrade Guide

### From 1.2.0 to 1.2.1
- No breaking changes
- Help menu now requires docs/ folder in distribution
- Configuration files remain compatible
- Recommended: Press F1 to explore new help system

### From 1.1.0 to 1.2.0
- No breaking changes
- New bookmark configuration options available
- Existing configurations automatically upgraded
- Recommended: Review bookmark label settings

### From 1.0.0 to 1.1.0
- No breaking changes
- New author configuration options available
- Existing configurations remain valid
- Recommended: Set generic author name in settings

---

## Support

For issues, questions, or feature requests:
- Press **F1** in the application for the User Guide
- Use **Help → Quick Start** for quick setup
- Review the [User Guide](docs/USER_GUIDE.md)
- Check the [Quick Start Guide](docs/QUICK_START_GUIDE.md)
- Examine logs in the `logs/` directory

---

**Maintained by**: Clinical Data Management Team  
**License**: MIT  
**Repository**: annoSDTMCheck



