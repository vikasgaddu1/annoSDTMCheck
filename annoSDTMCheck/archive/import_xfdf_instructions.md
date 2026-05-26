# XFDF Import Instructions for Windows

## The Issue
When importing XFDF files in Adobe Acrobat on Windows, you may encounter the error:
```
Error attempting to read from file/vc07/...
Overlapped I/O event is not in a signaled state.
```

This is typically a path resolution issue between the XFDF and PDF files.

## Solution 1: Correct Import Method

1. **Ensure both files are in the same directory**
   - PDF file: `output\acrf_immp.pdf`
   - XFDF file: `output\acrf_immp.xfdf`

2. **Open Adobe Acrobat** (not Reader - you need full Acrobat)

3. **Open the PDF file first**
   - File → Open → Select `output\acrf_immp.pdf`

4. **Import the XFDF using the correct menu path:**
   - Go to: **Tools** → **Comments**
   - In the Comments toolbar, click **More** (three dots icon)
   - Select **Import Data File**
   - Choose the XFDF file from the same directory
   - Click **Open**

## Solution 2: Alternative Import Method

If the above doesn't work, try:

1. In Adobe Acrobat with the PDF open:
   - Press `Ctrl+Shift+5` to open Comments panel
   - Right-click in the comments list area
   - Select **Import Data File**
   - Choose the XFDF file

## Solution 3: Using FDF Instead

If XFDF continues to fail:

1. In Adobe Acrobat:
   - Open the PDF that has the original annotations
   - Go to Tools → Comments → More → Export All to Data File
   - Save as FDF format instead of XFDF
   - Import the FDF file into the target PDF

## Solution 4: Manual Path Fix

The script has already been fixed, but if needed:

1. Run: `py fix_xfdf_path.py output\acrf_immp.xfdf`
2. This ensures the XFDF has the correct relative path

## Important Notes

- **Both files MUST be in the same directory**
- The XFDF contains a relative reference: `<f href="acrf_immp.pdf"/>`
- Adobe Acrobat looks for the PDF relative to the XFDF location
- If you move files, keep them together

## Verification

After successful import:
- All annotations should appear with Arial bold italic font
- Headers should be 12pt, other text 10pt
- Author should show as "Geron"
- Text should be in UPPERCASE (except headers)

