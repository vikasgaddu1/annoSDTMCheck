# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules for pyreadstat
pyreadstat_hidden_imports = collect_submodules('pyreadstat')

a = Analysis(
    ['src\\sdtm_checker\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('src/sdtm_checker/gui', 'sdtm_checker/gui'),
    ] + collect_data_files('pyreadstat'),
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pandas',
        'openpyxl',
        'PyMuPDF',
        'PyYAML',
        'pyreadstat',
        'pyreadstat._readstat_writer',
        'pyreadstat._readstat_parser',
        'pyreadstat.pyreadstat',
    ] + pyreadstat_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='annocheck-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Temporarily set to True to see any startup errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/sdtm_checker/gui/resources/icon.ico' if os.path.exists('src/sdtm_checker/gui/resources/icon.ico') else None,
)
