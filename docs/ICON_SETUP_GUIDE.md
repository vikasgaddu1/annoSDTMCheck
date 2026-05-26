# Application Icon Setup Guide

## 📍 Icon Location

Your application icon is stored at:
```
annoSDTMCheck/
└── assets/
    └── icon.ico    ✅ Already exists!
```

---

## ✅ What's Already Configured

### 1. **Icon File Location**
- ✅ Icon stored in `assets/icon.ico`
- ✅ Centralized location for all assets
- ✅ Easy to update or replace

### 2. **PyInstaller Bundle Configuration**
The `annocheck-gui.spec` file is configured to:
- ✅ Bundle the assets folder with the executable
- ✅ Use icon for the .exe file itself
- ✅ Make icon available at runtime

**Spec file configuration:**
```python
# Bundle assets folder
datas = [('config', 'config'), ('assets', 'assets')]

# Set executable icon
icon=['assets\\icon.ico']
```

### 3. **Runtime Icon Loading**
The application code (`src/sdtm_checker/gui/main.py`) includes smart icon loading:
- ✅ Tries multiple locations automatically
- ✅ Works in development mode (running from source)
- ✅ Works in bundled executable (PyInstaller)
- ✅ Gracefully handles missing icon

**Icon search paths:**
1. Development: `../../assets/icon.ico`
2. PyInstaller: `sys._MEIPASS/assets/icon.ico`
3. Installed: `../assets/icon.ico`

---

## 🎨 Using Your Own Icon

### Option 1: Replace Existing Icon
Simply replace the file:
```bash
# Backup current icon (optional)
copy assets\icon.ico assets\icon.ico.backup

# Replace with your icon
copy your-new-icon.ico assets\icon.ico
```

**Requirements:**
- ✅ Format: `.ico` file
- ✅ Recommended sizes: 16x16, 32x32, 48x48, 256x256 pixels
- ✅ Transparent background (optional but recommended)

### Option 2: Create Icon from Image

#### Using Python (Pillow):
```python
from PIL import Image

# Open your image
img = Image.open('your-logo.png')

# Resize and save as .ico
img.save('assets/icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
```

#### Using Online Tools:
- [ConvertICO](https://convertico.com/)
- [ICO Convert](https://icoconvert.com/)
- [Favicon Generator](https://favicon.io/)

---

## 🏗️ How It Works

### Development Mode (Running from Source)
```
annoSDTMCheck/
├── assets/
│   └── icon.ico        ← Icon loaded from here
└── src/
    └── sdtm_checker/
        └── gui/
            └── main.py  ← Looks for ../../assets/icon.ico
```

### Bundled Executable (PyInstaller)
```
annocheck-gui.exe
├── (embedded icon)     ← Shows on taskbar/desktop
└── _internal/
    └── assets/
        └── icon.ico    ← Loaded at runtime for window
```

**Two uses of the icon:**
1. **Executable icon**: Set in spec file, embedded in .exe
2. **Window icon**: Loaded at runtime, shown in window title bar

---

## 🔧 Building with Icon

### Build Command:
```bash
cd scripts
build_exe.bat
```

Choose Option 2 (Spec file build) - this uses the configured spec file with icon bundling.

### Manual Build:
```bash
pyinstaller annocheck-gui.spec --clean
```

### Verify Icon is Bundled:
After building, check:
1. ✅ `dist/annocheck-gui.exe` has an icon (right-click → Properties → Icon)
2. ✅ When running, window title bar shows icon
3. ✅ Taskbar shows icon

---

## 🐛 Troubleshooting

### Icon Not Showing in Executable

**Problem**: Built .exe has default Python icon

**Solution**:
1. Verify `assets/icon.ico` exists
2. Check spec file has correct icon path:
   ```python
   icon=['assets\\icon.ico']
   ```
3. Rebuild with `--clean` flag:
   ```bash
   pyinstaller annocheck-gui.spec --clean
   ```

### Icon Not Showing in Window

**Problem**: Window title bar has no icon when running

**Solution**:
1. Check logs for icon loading messages
2. Verify assets folder is bundled:
   ```python
   datas = [('config', 'config'), ('assets', 'assets')]
   ```
3. Ensure icon file is valid (open in image viewer)

### Icon Quality Issues

**Problem**: Icon looks pixelated or blurry

**Solution**:
1. Create multi-resolution .ico file with sizes:
   - 16x16 (small icons)
   - 32x32 (standard)
   - 48x48 (large icons)
   - 256x256 (high DPI displays)
2. Use a proper .ico creation tool
3. Test on different DPI settings

---

## 📝 Icon Best Practices

### Design Guidelines:
- ✅ **Simple design**: Recognizable at small sizes
- ✅ **High contrast**: Visible on light and dark backgrounds
- ✅ **Professional**: Matches application purpose
- ✅ **Multi-size**: Include multiple resolutions
- ✅ **Square**: Works best as icon

### Technical Guidelines:
- ✅ **Format**: ICO (Windows), PNG with sizes for others
- ✅ **Sizes**: 16, 32, 48, 256 pixels
- ✅ **Transparency**: Supported and recommended
- ✅ **File size**: Keep under 100KB

---

## 🎯 Current Icon

The current `assets/icon.ico` is:
- ✅ Already configured and working
- ✅ Bundled in executable builds
- ✅ Loaded at runtime
- ✅ Shows in window and taskbar

**No additional setup needed!** Just build and the icon will be included.

---

## 🔄 Icon Update Workflow

When you want to change the icon:

1. **Create/obtain new icon**
   - Design or download new icon
   - Convert to .ico format with multiple sizes

2. **Replace icon file**
   ```bash
   copy new-icon.ico assets\icon.ico
   ```

3. **Test in development**
   ```bash
   py -m sdtm_checker
   ```
   - Check if icon appears in window

4. **Rebuild executable**
   ```bash
   cd scripts
   build_exe.bat
   ```
   - Choose Option 2 (Spec file build)

5. **Verify**
   - Check .exe file icon
   - Run .exe and check window icon
   - Check taskbar icon

---

## 📦 Package Data (For Distribution)

If distributing as Python package, update `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="sdtm_checker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "sdtm_checker": ["../../assets/*.ico"],
    },
    include_package_data=True,
    # ... rest of setup
)
```

---

## 🎨 Icon Resources

### Free Icon Sources:
- [Icons8](https://icons8.com/) - Free icons
- [Flaticon](https://www.flaticon.com/) - Vector icons
- [IconFinder](https://www.iconfinder.com/) - Icon marketplace
- [Icon Archive](https://iconarchive.com/) - Icon collection

### Icon Creation Tools:
- **GIMP** - Free, open-source image editor
- **Inkscape** - Vector graphics editor
- **IcoFX** - Dedicated icon editor
- **Greenfish Icon Editor** - Free Windows icon editor

---

## ✅ Summary

### What's Working:
- ✅ Icon file exists at `assets/icon.ico`
- ✅ PyInstaller spec configured to bundle assets
- ✅ Executable icon set in spec file
- ✅ Runtime icon loading implemented
- ✅ Multiple fallback paths for different scenarios
- ✅ Graceful handling if icon not found

### To Build with Icon:
```bash
cd scripts
build_exe.bat
```
Choose Option 2, and your icon will be included!

### To Replace Icon:
```bash
copy your-new-icon.ico assets\icon.ico
```
Then rebuild.

---

**Your icon setup is complete and ready to use!** 🎉

The icon will automatically:
- Show on the built executable file
- Appear in the window title bar
- Display on the taskbar
- Work in both development and production


