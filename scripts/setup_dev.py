#!/usr/bin/env python
"""Development environment setup script for SDTM Annotation Checker."""

import os
import sys
import subprocess
import platform


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✓ {description} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error during {description}: {e}")
        return False
    return True


def main():
    """Set up the development environment."""
    print("=== SDTM Annotation Checker Development Setup ===\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"✗ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        sys.exit(1)
    print(f"✓ Python {python_version.major}.{python_version.minor} detected")
    
    # Create necessary directories
    directories = [
        "output/xfdf",
        "output/reports",
        "sdtm_data",
        "logs",
        ".cache"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print(f"✓ Created {len(directories)} directories")
    
    # Install dependencies
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return
    
    if not run_command("pip install -r requirements.txt", "Installing base requirements"):
        return
    
    # Install development dependencies
    if not run_command("pip install -e .[dev]", "Installing development dependencies"):
        print("Note: Development dependencies installation failed. You can install manually later.")
    
    # Set up pre-commit hooks (if available)
    if os.path.exists(".pre-commit-config.yaml"):
        run_command("pre-commit install", "Setting up pre-commit hooks")
    
    # Create local config from template
    if os.path.exists("config/config_template.yaml") and not os.path.exists("config/config.yaml"):
        try:
            with open("config/config_template.yaml", "r") as src:
                with open("config/config.yaml", "w") as dst:
                    dst.write(src.read())
            print("✓ Created config/config.yaml from template")
        except Exception as e:
            print(f"✗ Error creating config file: {e}")
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Activate your virtual environment")
    print("2. Place your CRF PDFs in the 'crf/' directory")
    print("3. Place your SDTM datasets in the 'sdtm_data/' directory")
    print("4. Edit 'config/config.yaml' to match your requirements")
    print("5. Run 'python -m src.sdtm_checker.core.pdf2fdf --help' to get started")


if __name__ == "__main__":
    main() 