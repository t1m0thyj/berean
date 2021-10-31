# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

a = Analysis([os.path.join('src', 'berean.pyw' if sys.platform == 'win32' else 'berean.py')],
             pathex=[],
             binaries=[],
             datas=[
                 (os.path.join('src', 'images'), 'images'),
                 (os.path.join('src', 'versions', 'KJV.bbl'), 'versions')
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='berean',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon=os.path.join('src', 'images', 'berean.ico'))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='berean')
