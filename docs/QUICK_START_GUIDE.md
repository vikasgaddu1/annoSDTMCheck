# SDTM Annotation Checker - Quick Start Guide

## Get Started in 5 Minutes

This quick start guide will help you get up and running with the SDTM Annotation Checker quickly.

## Step 1: Launch the Application

- Double-click `annocheck-gui.exe` (or run from source with `python -m sdtm_checker.gui`)
- The main window will open with the Configuration tab

## Step 2: Configure File Paths

In the **File Paths** tab:

1. **Annotated CRF File**: Click "Browse..." to select your PDF file with SDTM annotations
2. **SDTM Directory**: Click "Browse..." to select the folder containing your SAS7BDAT files
3. **Output Directory**: Select where you want the validation report to be saved
4. **Default Output File**: The default filename for your Excel report (e.g., `validation_report.xlsx`)

### Example Paths:
```
Annotated CRF: C:\Projects\Study123\CRF\annotated_crf.pdf
SDTM Directory: C:\Projects\Study123\SDTM\
Output Directory: C:\Projects\Study123\output\
```

## Step 3: Configure Validation Settings (Optional)

Switch to the **Validation Settings** tab:

### Fuzzy Matching
- **Enable** if you want to allow minor variations in variable names (recommended)
- **Fuzzy Threshold**: Set to 0.8 (80% similarity) for balanced matching
  - Higher values = stricter matching
  - Lower values = more lenient matching

### Annotation Author Filter
- **Enable** to validate only annotations from specific authors
- Leave **blank** (or enter "GENERIC") to validate all annotations
- Enter a specific name to filter by that author

### Case Sensitivity
- **Enable** if variable names must match exactly (SUBJID ≠ subjid)
- **Disable** for case-insensitive matching (recommended)

## Step 4: Run Validation

1. Click the **"Run Check"** button at the bottom
2. A progress bar will show the validation status:
   - Extracting annotations from PDF
   - Parsing SDTM patterns
   - Validating against datasets
   - Generating report
3. Wait for completion (usually 30 seconds to 2 minutes depending on file size)

## Step 5: Review Results

After completion:
- A success message will appear
- An Excel report will be generated in your output directory
- The report contains:
  - **Summary Sheet**: Overall statistics and validation results
  - **Detailed Results**: Page-by-page annotation validation
  - **Missing Variables**: Variables in CRF but not in SDTM datasets
  - **Invalid Patterns**: Annotations that couldn't be parsed

## Understanding the Report

### Status Columns:
- **✓ Valid**: Annotation found in SDTM dataset
- **✗ Invalid**: Annotation not found (variable doesn't exist)
- **⚠ Warning**: Possible issue (fuzzy match or case mismatch)

### Common Issues:
1. **"Variable not found"**: Check if the SDTM domain exists and has the variable
2. **"Domain file not found"**: Ensure SAS7BDAT files are in the SDTM directory
3. **"Pattern not recognized"**: Check annotation format (should be DOMAIN.VARIABLE or DOMAIN-VARIABLE)

## Additional Features

### Standardize Annotations
- Click **"Standardize Annotations"** to:
  - Fix annotation colors (standard cyan for all)
  - Correct annotation formatting
  - Apply consistent author names
  - Preserve original PDF content

### Save/Load Configurations
- Click **"Save Configuration As..."** to save settings for reuse
- Click **"Load Configuration..."** to load previously saved settings
- Great for working with multiple studies or projects

### Pattern Management
- Switch to the **Pattern Management** tab to:
  - View all annotation patterns being used
  - Add custom patterns for your organization
  - Edit or delete existing patterns
  - Test patterns against sample annotations

## Keyboard Shortcuts

- **F1**: Open User Guide
- **Shift+F1**: What's This? mode (click elements for help)

## Need More Help?

- Press **F1** to open the comprehensive User Guide
- Use **Shift+F1** to enable "What's This?" mode and click on any element for detailed help
- Check the **About** dialog (Help menu) for version information

## Quick Tips

### Best Practices:
1. **Always test with a small PDF first** to verify your configuration
2. **Save your configuration** for each project to avoid re-entering settings
3. **Enable fuzzy matching** to catch minor typos in annotations
4. **Review the report** for patterns in validation failures
5. **Use case-insensitive matching** unless your organization requires exact case matching

### Common Annotation Formats:
- `DM.SUBJID` - Domain.Variable format
- `DM-SUBJID` - Domain-Variable format  
- `VS.VSORRES` - Vital Signs observation result
- `AE-AESTDTC` - Adverse Event start date/time

### Troubleshooting Quick Checks:
1. **PDF opens?** - Ensure the PDF isn't password-protected
2. **SDTM files exist?** - Check .sas7bdat files are in the directory
3. **Annotations visible?** - Open PDF in Adobe Acrobat to verify annotations
4. **Output directory writable?** - Ensure you have permission to write to the output folder

## What's Next?

- Explore advanced features in the full User Guide (press F1)
- Customize annotation patterns for your organization
- Set up project-specific configurations
- Automate your validation workflow

---

**Version**: 1.2.0  
**Last Updated**: October 2025

For detailed documentation, press **F1** to open the User Guide.



