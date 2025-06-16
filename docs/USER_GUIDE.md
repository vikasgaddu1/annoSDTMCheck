# SDTM Annotation Checker - User Guide
## Version 2.0

## 1. Introduction

Welcome to the SDTM Annotation Checker! This comprehensive tool validates annotated CRF PDFs against SDTM datasets, ensuring consistency and accuracy in clinical trial data management. The application provides a user-friendly graphical interface for easy and efficient validation workflows.

## 2. Installation

### 2.1 Prerequisites
- Windows operating system (for .exe version)
- Python 3.8 or higher (for source installation)
- pip (Python package installer, for source installation)
- Virtual environment (recommended for source installation)

### 2.2 Installation Options

#### Option 1: Using Executable (Recommended for Windows Users)
1. **Locate the executable:**
   - `annocheck-gui.exe` in the `dist` folder after building or from your distribution package

2. **Copy the executable to your desired location**

3. **Verify installation:**
   - Simply double-click `annocheck-gui.exe` to launch the application

#### Option 2: Source Installation
1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd annoSDTMCheck
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   py -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   py -m sdtm_checker
   ```

## 3. Getting Started

### 3.1 Quick Start
To launch the application:

```bash
# Using executable
annocheck-gui.exe

# Using source installation
py -m sdtm_checker
```

This launches the GUI where you can:
- Select PDF and SDTM files using file dialogs
- Configure validation settings
- Run validation and view results
- Manage configuration files

## 4. Configuration Management

### 4.1 Configuration File Structure
The tool uses YAML configuration files for customization:

```yaml
# File paths
paths:
  pdf_directory: "crf/"
  sdtm_directory: "sdtm_data/"
  output_directory: "output/"
  default_output_file: "validation_report.xlsx"

# Annotation patterns
annotation_patterns:
  patterns:
    - name: "DOMAIN_VAR"
      description: "Domain.Variable format (e.g., DM.SUBJID)"
      regex: "^([A-Z]{2})\.([A-Z0-9_]+)$"
      groups:
        domain: 1
        variable: 2
    - name: "DOMAIN_DASH_VAR"
      description: "Domain-Variable format (e.g., DM-SUBJID)"
      regex: "^([A-Z]{2})-([A-Z0-9_]+)$"
      groups:
        domain: 1
        variable: 2
    - name: "VARIABLE_ONLY"
      description: "Variable only (e.g., SUBJID)"
      regex: "^([A-Z0-9_]+)$"
      groups:
        variable: 1
  settings:
    case_sensitive: false
    fuzzy_matching: true
    fuzzy_threshold: 0.85

# Validation settings
validation:
  ignore_domains: []
  ignore_variables: ["STUDYID", "USUBJID"]
```

### 4.2 Using Configuration Files

In the GUI, use the Configuration tab to:
- Load existing YAML configuration files
- Edit configurations visually
- Save configurations for reuse
- Share configurations with team members

### 4.3 Configuration Management Features
- **Load Configuration**: Load existing YAML files
- **Save Configuration**: Save current settings
- **Reset to Default**: Restore default settings
- **Validation**: Automatic validation of configuration syntax
- **Pattern Testing**: Test regex patterns before saving

## 5. Graphical User Interface

### 5.1 Main Features
- **File Selection**: Browse and select PDF and SDTM files
- **Configuration Editor**: Visual configuration management
- **Progress Monitoring**: Real-time validation progress
- **Results Display**: Interactive results viewing

### 5.2 Configuration Tab
- **Path Management**: Set default directories
- **Pattern Editor**: Add/edit/test annotation patterns
- **Validation Settings**: Configure validation rules
- **Import/Export**: Share configurations with team

### 5.3 Validation Tab
- **Input Selection**: Choose CRF PDF and SDTM directory
- **Output Settings**: Specify report location and format
- **Validation Execution**: Run validation with progress tracking
- **Results Preview**: View summary of validation results

## 6. Advanced Features

### 6.1 Fuzzy Matching
The tool supports fuzzy matching for annotations with typos:

```yaml
annotation_patterns:
  settings:
    fuzzy_matching: true
    fuzzy_threshold: 0.85  # 85% similarity required
```

### 6.2 Custom Validation Rules
Customize validation behavior:

```yaml
validation:
  ignore_domains: ["RELREC", "SUPPAE"]  # Skip these domains
  ignore_variables: ["STUDYID", "USUBJID"]  # Skip these variables
```

### 6.3 Multiple Export Formats
Export annotations in different formats:

- **XFDF**: XML-based annotation format for archival
- **Excel**: Spreadsheet format for analysis and review

## 7. Understanding Results

### 7.1 Validation Report Structure
The Excel report contains multiple sheets:

1. **Summary**: Overall validation statistics
2. **Validation Results**: Detailed findings with severity levels
3. **Annotation Inventory**: Complete list of extracted annotations
4. **Dataset Information**: SDTM dataset metadata

### 7.2 Severity Levels
- **ERROR**: Critical issues requiring immediate attention
- **WARNING**: Potential issues that should be reviewed
- **INFO**: Informational messages and successful validations

### 7.3 Common Validation Results
- **Missing Variable**: Annotated variable not found in SDTM dataset
- **Domain Mismatch**: Variable found in different domain than annotated
- **Fuzzy Match**: Variable found with similar but not exact name
- **Successful Match**: Perfect match between annotation and SDTM variable

## 8. Troubleshooting

### 8.1 Common Issues and Solutions

#### Issue: Application Won't Start
```
Error: Application failed to start
```
**Solution:**
- Verify all required files are present
- Check Windows permissions
- Try running as administrator
- Check for antivirus blocking

#### Issue: PDF Processing Errors
```
Error: Cannot extract annotations from PDF
```
**Solution:**
- Verify PDF file is not corrupted
- Check file permissions
- Ensure PDF contains annotations (not just text)

#### Issue: SDTM Dataset Reading Errors
```
Error: Cannot read SDTM dataset
```
**Solution:**
- Verify .sas7bdat files are valid
- Check file permissions
- Ensure sufficient disk space

#### Issue: Configuration Errors
```
Error: Invalid configuration file
```
**Solution:**
- Validate YAML syntax
- Check required fields are present
- Use GUI configuration editor for validation

### 8.2 Log Files
The application creates log files:
- `file_access.log`: File access and processing log
- `application.log`: General application log

## 9. Best Practices

### 9.1 File Organization
```
project/
├── crf/                    # Annotated PDF files
├── sdtm_data/              # SDTM datasets (.sas7bdat)
├── config/                 # Configuration files
├── output/                 # Generated reports
└── logs/                   # Log files
```

### 9.2 Configuration Management
- Use descriptive names for custom patterns
- Test patterns before saving
- Share configurations with team members
- Keep backup of working configurations

### 9.3 Quality Assurance
- Review validation results systematically
- Address ERROR severity items first
- Investigate WARNING items case by case

### 9.4 Performance Optimization
- Process large datasets efficiently by monitoring memory usage
- Use appropriate fuzzy matching thresholds
- Close unnecessary applications when processing large files

## 10. Security Features

### 10.1 Path Validation
The application includes security features:
- Path traversal prevention
- File permission validation
- Safe file handling

### 10.2 Data Protection
- Encryption support for sensitive data
- Secure temporary file handling
- Audit logging for file access

## 11. Support and Resources

### 11.1 Documentation
- `README.md`: Project overview and quick start
- `PRD_CONSOLIDATED.md`: Complete product requirements
- `TECHNICAL_SPEC.md`: Technical implementation details

### 11.2 Getting Help
1. Check this user guide for common issues
2. Review log files for error details
3. Enable verbose logging in the GUI settings
4. Contact support with detailed error information

### 11.3 Reporting Issues
When reporting issues, include:
- Steps to reproduce the issue
- Error messages from the GUI
- Log file contents
- System information (OS, Python version)
- Sample files (if possible)

## 12. Frequently Asked Questions

**Q: Do I need Python installed to use the executable?**
A: No, the executable version is standalone and does not require a separate Python installation.

**Q: Can I use the application on non-Windows systems?**
A: The .exe version is for Windows. For other operating systems, use the source installation method.

**Q: What PDF annotation types are supported?**
A: Text annotations, highlights, comments, and other PyMuPDF-compatible annotation types.

**Q: Can I process multiple PDFs at once?**
A: Currently, the tool processes one PDF at a time. You can run multiple validations sequentially through the GUI.

**Q: How do I customize annotation patterns?**
A: Use the GUI configuration editor in the Configuration tab to add, edit, or remove custom regex patterns.

**Q: What SDTM file formats are supported?**
A: Currently supports .sas7bdat files (SAS datasets). XPT support is planned for future releases.

**Q: Can I share configurations with my team?**
A: Yes, configuration files are portable YAML files that can be shared and version controlled.

**Q: How do I handle large datasets?**
A: The application is optimized for memory efficiency and can handle large SDTM datasets. Monitor system memory usage for very large files.

**Q: Can I validate against Define.xml?**
A: Define.xml validation is planned for future releases. Current version validates against SDTM datasets directly.

**Q: Is there a way to automate validations?**
A: The current version is GUI-based. For automation needs, you can use the Python module directly in scripts. 