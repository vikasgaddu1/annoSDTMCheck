@echo off
echo Testing XFDF Standardization with Relative Paths
echo ==================================================
echo.
echo This will create:
echo   - output\aCRF_standardized.pdf
echo   - output\aCRF_standardized.xfdf
echo.
echo Both files will be in the same folder with relative path reference.
echo.

py standardize_via_xfdf.py input\aCRF.pdf output\aCRF_standardized.pdf

echo.
echo ==================================================
echo Done! Now try importing the XFDF in Adobe Acrobat.
echo.
pause


