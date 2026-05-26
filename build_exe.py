"""
Build script for creating SDTM Annotation Checker executable.

This script creates a standalone Windows executable using PyInstaller.

Usage:
    python build_exe.py
"""

import subprocess
import sys
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller."""
    
    print("=" * 80)
    print("SDTM Annotation Checker - EXE Builder")
    print("=" * 80)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"[OK] PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")
    
    print()
    print("Building executable...")
    print("-" * 80)
    
    # PyInstaller command - use spec file if it exists, otherwise use command line
    spec_file = Path("SDTM_Annotation_Checker.spec")
    if spec_file.exists():
        print("Using existing spec file: SDTM_Annotation_Checker.spec")
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--clean",  # Clean PyInstaller cache
            str(spec_file)
        ]
    else:
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--name=SDTM_Annotation_Checker",
            "--onefile",  # Single EXE file
            "--windowed",  # No console window
            "--icon=NONE",  # No icon for now
            "--add-data=src;src",  # Include source files
            "--hidden-import=PyQt6",
            "--hidden-import=PyQt6.QtCore",
            "--hidden-import=PyQt6.QtGui",
            "--hidden-import=PyQt6.QtWidgets",
            "--hidden-import=fitz",
            "--hidden-import=pymupdf",
            "--hidden-import=pandas",
            "--hidden-import=openpyxl",
            "--hidden-import=yaml",
            "--hidden-import=lxml",
            "--hidden-import=pyreadstat",
            "--hidden-import=pyreadstat._readstat_writer",
            "--hidden-import=pyreadstat.pyreadstat",
            "--collect-all=pymupdf",
            "--collect-all=pyreadstat",
            "--noupx",  # Don't use UPX compression
            "src/sdtm_checker/__main__.py"
        ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        print()
        print("=" * 80)
        print("[OK] BUILD SUCCESSFUL!")
        print("=" * 80)
        print()
        print("Executable location:")
        print(f"  dist/SDTM_Annotation_Checker.exe")
        print()
        print("To run:")
        print(f"  .\\dist\\SDTM_Annotation_Checker.exe")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print("[ERROR] BUILD FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)

