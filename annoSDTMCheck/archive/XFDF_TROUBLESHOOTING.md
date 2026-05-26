# XFDF Import Troubleshooting

## Common Issues and Solutions

### Error: "Overlapped I/O event is not in a signaled state"

**Symptoms:**
- Adobe Acrobat shows this error when trying to import XFDF
- Error message includes file path to XFDF file

**Cause:**
This error typically occurs when:
1. The XFDF file contains a relative path to the PDF instead of an absolute path
2. The PDF file is on a network drive and Adobe Acrobat has trouble accessing it
3. File permissions or network connectivity issues

**Solutions:**

#### Solution 1: Use Relative Paths with Both Files in Same Directory (RECOMMENDED)
Keep the PDF and XFDF in the same folder and use just the filename:

**Best approach:**
```
output/
├── aCRF_standardized.pdf
└── aCRF_standardized.xfdf  (references just "aCRF_standardized.pdf")
```

XFDF content:
```xml
<f href="aCRF_standardized.pdf"/>
```

The updated script now automatically does this - both files are saved to the output folder with matching names and relative references.

#### Solution 2: Use Absolute Paths
The XFDF file references the PDF with an absolute path:

```xml
<f href="file:///vc07/Biometrics/GRN163L_imetelstat/ToolDevelopment/annoSDTMCheck/output/aCRF.pdf"/>
```

Note: Absolute paths can still cause issues on network drives.

#### Solution 2: Copy to Local Drive
Copy both the PDF and XFDF files to your local drive (e.g., `C:\temp\`) and import from there:

```
C:\temp\
├── aCRF.pdf
└── aCRF_standardized.xfdf
```

Then update the XFDF:
```xml
<f href="file:///C:/temp/aCRF.pdf"/>
```

#### Solution 3: Same Directory
Ensure the PDF and XFDF are in the same directory, then:
1. Open the PDF first in Adobe Acrobat
2. With the PDF open, import the XFDF: `Tools → Comments → Import Data File`

### Error: "The file is damaged and could not be repaired"

**Cause:** The XFDF file is malformed or contains invalid XML.

**Solution:**
1. Open the XFDF file in a text editor
2. Check for:
   - Proper XML structure
   - Closing tags
   - Valid UTF-8 encoding
   - Special characters properly escaped

### Error: "No comments to import"

**Cause:** 
- The XFDF file is empty or doesn't contain annotations
- The XFDF format is not recognized by Adobe Acrobat

**Solution:**
1. Check that the XFDF file contains `<annots>` section with content
2. Verify the XFDF was generated correctly from a PDF with annotations

### Error: "Could not find the associated PDF file"

**Cause:** The path in the `<f href="..."/>` tag doesn't point to an existing PDF file.

**Solution:**
1. Check the path in the XFDF file (line 3)
2. Update it to the correct absolute path
3. Ensure the PDF file actually exists at that location

## Best Practices

### 1. Always Use Absolute Paths
```xml
<f href="file:///full/path/to/file.pdf"/>
```

### 2. Test with Local Files First
Before working with network drives, test the workflow with files on your C: drive.

### 3. Check File Permissions
Ensure you have read/write access to both the PDF and XFDF files.

### 4. Use the Updated Scripts
The latest version of `standardize_via_xfdf.py` automatically handles absolute paths correctly.

### 5. Verify Before Importing
Before importing in Adobe Acrobat:
- Open the XFDF file in a text editor
- Check line 3: `<f href="..."/>`
- Verify the path is correct and absolute

## Quick Fix for Existing XFDF Files

If you have an XFDF file with a relative path, manually edit it:

1. Open the XFDF file in Notepad or VS Code
2. Find line 3: `<f href="aCRF.pdf"/>`
3. Replace with absolute path: `<f href="file:///vc07/Biometrics/.../aCRF.pdf"/>`
4. Save and try importing again

## Network Drive Considerations

When working with files on network drives (\\vc07\, \\server\, etc.):

1. **Map the network drive** to a letter (e.g., Z:)
   - Right-click "This PC" → "Map network drive"
   - Then use: `file:///Z:/path/to/file.pdf`

2. **Or use UNC path notation:**
   - `file://vc07/Biometrics/...` (no backslashes in XFDF)

3. **Or copy to local drive** for importing (most reliable)

## Contact

If you continue to have issues:
1. Check the XFDF file contents
2. Verify PDF file location
3. Try copying both files to a local drive
4. Ensure Adobe Acrobat (not Reader) is being used

