# -*- mode: python ; coding: utf-8 -*-

import sys
sys.path.append('src')
from constants import VERSION

file_version_info = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={{version_tuple}},
    prodvers={{version_tuple}},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    VarFileInfo([VarStruct('Translation', [0, 1200])]),
    StringFileInfo(
      [
      StringTable(
        '000004b0',
        [StringStruct('Comments', ''),
        StringStruct('CompanyName', ''),
        StringStruct('FileDescription', 'An open source, cross-platform Bible study program'),
        StringStruct('FileVersion', '{{version_string}}'),
        StringStruct('InternalName', 'berean.exe'),
        StringStruct('LegalCopyright', 'Copyright \\xa9 2021 Timothy Johnson'),
        StringStruct('LegalTrademarks', ''),
        StringStruct('OriginalFilename', 'berean.exe'),
        StringStruct('ProductName', 'Berean'),
        StringStruct('ProductVersion', '{{version_string}}'),
        StringStruct('Assembly Version', '{{version_string}}')])
      ])
  ]
)
"""

major, minor, patch = [int(x) for x in VERSION.split('.')]
file_version_info = file_version_info.replace('{{version_string}}', '{}.{}.{}.0'.format(major, minor, patch))
file_version_info = file_version_info.replace('{{version_tuple}}', str(tuple([major, minor, patch, 0])))

with open('build/berean/file_version_info.txt', 'w') as fileobj:
    fileobj.write(file_version_info)

block_cipher = None

a = Analysis(['src/berean.pyw' if sys.platform == 'win32' else 'src/berean.py'],
             pathex=[],
             binaries=[],
             datas=[
                 ('src/images', 'images'),
                 ('src/versions/KJV.bbl', 'versions')
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
          disable_windowed_traceback=True,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='src/images/berean.ico',
          version='build/berean/file_version_info.txt')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='berean')
