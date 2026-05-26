"""Create timestamped backup of entire project."""

import zipfile
import datetime
from pathlib import Path
import sys

def create_backup():
    """Create timestamped backup of entire project."""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = project_root / "archive" / backup_name
    
    # Ensure archive directory exists
    backup_path.parent.mkdir(exist_ok=True)
    
    print(f"Creating backup: {backup_path}")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all source files
        src_dir = project_root / "src"
        if src_dir.exists():
            for file_path in src_dir.rglob("*.py"):
                arcname = file_path.relative_to(project_root)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
        
        # Add config files
        config_dir = project_root / "config"
        if config_dir.exists():
            for file_path in config_dir.rglob("*.yaml"):
                arcname = file_path.relative_to(project_root)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
        
        # Add other important files
        important_files = [
            "requirements.txt",
            "README.md",
            "setup.py",
            "pytest.ini"
        ]
        
        for filename in important_files:
            file_path = project_root / filename
            if file_path.exists():
                zipf.write(file_path, filename)
                print(f"  Added: {filename}")
        
        # Add GUI files
        gui_files = [
            "src/sdtm_checker/gui/main.py",
            "src/sdtm_checker/gui/config_tab.py",
            "src/sdtm_checker/gui/ui_state_cache.py"
        ]
        for filepath in gui_files:
            full_path = project_root / filepath
            if full_path.exists() and filepath not in [str(f.relative_to(project_root)) for f in src_dir.rglob("*.py")]:
                zipf.write(full_path, filepath)
                print(f"  Added: {filepath}")
    
    print(f"\nBackup created successfully: {backup_path}")
    print(f"Backup size: {backup_path.stat().st_size / 1024:.2f} KB")
    return backup_path

if __name__ == "__main__":
    backup_path = create_backup()
