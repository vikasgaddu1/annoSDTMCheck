@echo off
setlocal EnableDelayedExpansion

echo ============================================
echo SDTM Annotation Checker Build Script
echo ============================================
echo.

:: Check if running from scripts directory
if exist build_exe.py (
    cd ..
    echo Changed to project root directory
)

:: Set Python path (use venv if available, otherwise system Python)
if exist .venv\Scripts\python.exe (
    set PYTHON_CMD=.venv\Scripts\python.exe
    set PYINSTALLER_CMD=.venv\Scripts\pyinstaller.exe
    echo Using virtual environment Python
) else (
    set PYTHON_CMD=python
    set PYINSTALLER_CMD=pyinstaller
    echo WARNING: Virtual environment not found, using system Python
)

:: Check if PyInstaller is installed
%PYTHON_CMD% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed!
    echo Please install it first using: pip install pyinstaller
    pause
    exit /b 1
)

:: Give user choice of build method
echo Choose build method:
echo 1) Use updated Python script (with hidden imports)
echo 2) Use spec file (more reliable for complex dependencies)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Building using Python script...
    %PYTHON_CMD% scripts\build_exe.py
) else if "%choice%"=="2" (
    echo.
    echo Building using spec file...
    %PYINSTALLER_CMD% annocheck-gui.spec --clean
) else (
    echo Invalid choice. Please run again and select 1 or 2.
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    echo Please check the error messages above.
    echo.
    echo If you're getting pyreadstat errors, try:
    echo 1. Ensure pyreadstat is properly installed: pip install --upgrade pyreadstat
    echo 2. Use the spec file option (choice 2) instead
    echo 3. Check that all dependencies are installed: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ============================================
echo Executable should be in the dist\ directory
echo.
pause 