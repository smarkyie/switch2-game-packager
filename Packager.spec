# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
project = Path(SPECPATH)
a = Analysis([str(project/'src'/'app.py')], pathex=[str(project/'src')],
             binaries=[], datas=[], hiddenimports=[], hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['numpy','scipy','matplotlib','pandas','pytest'],
             noarchive=False, optimize=0)
# Windows 10/11 supplies the Universal CRT/API-set DLLs. Do not collect copies
# accidentally discovered in unrelated PATH directories on the build machine.
a.binaries = [item for item in a.binaries
              if not Path(item[0]).name.lower().startswith('api-ms-win-')
              and Path(item[0]).name.lower() != 'ucrtbase.dll']
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='Switch2-XCI-Packager',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False,
          icon=str(project/'app.ico') if (project/'app.ico').exists() else None)
