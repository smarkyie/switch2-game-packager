# -*- mode: python ; coding: utf-8 -*-
# macOS build: one-file CLI/GUI binary (dist/NSP-Box) plus a Finder-friendly
# app bundle (dist/NSP-Box.app) wrapping the same executable.
from pathlib import Path
project = Path(SPECPATH)
icon = str(project/'app.icns') if (project/'app.icns').exists() else None
a = Analysis([str(project/'src'/'app.py')], pathex=[str(project/'src')],
             binaries=[], datas=[(str(project/'src'/'assets'), 'assets')], hiddenimports=[], hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['numpy','scipy','matplotlib','pandas','pytest'],
             noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='NSP-Box',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, icon=icon)
app = BUNDLE(exe, name='NSP-Box.app', icon=icon,
             bundle_identifier='com.smarkyie.nspbox',
             info_plist={
                 'CFBundleDisplayName': 'NSP Box',
                 'CFBundleShortVersionString': '3.0.0',
                 'NSHighResolutionCapable': True,
                 'LSApplicationCategoryType': 'public.app-category.utilities',
             })
