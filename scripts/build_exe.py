#!/usr/bin/env python3
"""
Build script for creating SDTM Annotation Checker executable.

This script automates the process of creating a distributable executable
using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build the executable."""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("Building SDTM Annotation Checker executable...")
    print(f"Project root: {project_root}")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Clean previous builds
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    if dist_dir.exists():
        print("Cleaning previous dist directory...")
        try:
            shutil.rmtree(dist_dir)
        except PermissionError:
            print("Warning: Could not remove dist directory (files may be in use)")
    
    if build_dir.exists():
        print("Cleaning previous build directory...")
        try:
            shutil.rmtree(build_dir)
        except PermissionError:
            print("Warning: Could not remove build directory (files may be in use)")
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=annocheck-gui",
        "--add-data=config;config",
        "--add-data=assets;assets",
        "--add-data=docs;docs",
        "--add-data=VALIDATION_SETTINGS_QUICK_START.md;.",
        "--icon=assets/icon.ico" if (project_root / "assets" / "icon.ico").exists() else "",
        # Hidden imports for pyreadstat
        "--hidden-import=pyreadstat._readstat_writer",
        "--hidden-import=pyreadstat._readstat_parser",
        "--hidden-import=pyreadstat.pyreadstat",
        "--hidden-import=pyreadstat.worker",
        # Collect all data from pyreadstat
        "--collect-all=pyreadstat",
        # Additional hidden imports that might be needed
        "--hidden-import=pandas._libs.tslibs.base",
        "src/sdtm_checker/__main__.py"
    ]
    
    # Remove empty icon parameter if no icon file exists
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build completed successfully!")
        
        # Show output location
        exe_path = dist_dir / "annocheck-gui.exe"
        if exe_path.exists():
            print(f"Executable created at: {exe_path}")
            print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    
    except FileNotFoundError:
        print("PyInstaller not found. Please install it first:")
        print("pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    main() 