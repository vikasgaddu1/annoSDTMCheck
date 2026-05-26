@echo off
REM Build SDTM Annotation Checker executable
REM This script creates a standalone Windows executable

echo ================================================================================
echo SDTM Annotation Checker - EXE Builder
echo ================================================================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install PyInstaller if needed
echo Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
echo --------------------------------------------------------------------------------

REM Build with PyInstaller
pyinstaller ^
    --name=SDTM_Annotation_Checker ^
    --onefile ^
    --windowed ^
    --add-data="src;src" ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=fitz ^
    --hidden-import=pymupdf ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=yaml ^
    --hidden-import=lxml ^
    --hidden-import=pyreadstat ^
    --hidden-import=pyreadstat._readstat_writer ^
    --hidden-import=pyreadstat.pyreadstat ^
    --collect-all=pymupdf ^
    --collect-all=pyreadstat ^
    --noupx ^
    src/sdtm_checker/__main__.py

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo BUILD FAILED
    echo ================================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo BUILD SUCCESSFUL!
echo ================================================================================
echo.
echo Executable location:
echo   dist\SDTM_Annotation_Checker.exe
echo.
echo To run:
echo   .\dist\SDTM_Annotation_Checker.exe
echo.
echo ================================================================================
pause

