"""setup.py - builds py2exe executable for Berean"""

import glob
import os
import shutil

from distutils.core import setup
import py2exe

from config import VERSION

MANIFEST = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity name="berean" processorArchitecture="x86" type="win32" version="1.0.0.0"/>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity name="Microsoft.VC90.CRT" processorArchitecture="x86" publicKeyToken="1fc8b3b9a1e18e3b" type="win32" version="9.0.21022.8"/>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity language="*" name="Microsoft.Windows.Common-Controls" processorArchitecture="x86" publicKeyToken="6595b64144ccf1df" type="win32" version="6.0.0.0"/>
    </dependentAssembly>
  </dependency>
</assembly>
"""
mo_files = [(folder, [os.path.join(folder, "berean.mo")]) for folder in
            glob.glob("locale\\*\\LC_MESSAGES")]
help_files = [(folder, glob.glob("%s\\*.*" % folder)) for folder in
              glob.glob("locale\\*\\help")]

if os.path.isdir("dist"):
    shutil.rmtree("dist")
setup(options={"py2exe": {"compressed": 1,
                          "optimize": 2,
                          "bundle_files": 3,
                          "excludes": ["_ssl", "doctest", "pdb", "unittest",
                                       "inspect", "email"],
                          "dll_excludes": ["msvcp90.dll", "w9xpopen.exe"]}},
      windows=[{"script": "berean.py",
                "name": "Berean",
                "version": VERSION,
                "company_name": "Timothy Johnson",
                "copyright": "Copyright \xa9 2011-2015 Timothy Johnson",
                "description": "Berean",
                "icon_resources": [(1, "images\\berean.ico")],
                "other_resources": [(24, 1, MANIFEST)]}],
      data_files=[("images", glob.glob("images\\*.*")),
                  ("images\\flags", glob.glob("images\\flags\\*.*")),
                  ("versions", ["versions\\KJV.bbl", "versions\\WEB.bbl"]),
                  ("", ["license.txt"])] + mo_files + help_files,
      zipfile=None)
for imagedir in ("dist\\images", "dist\\images\\flags"):
    thumbs_db = os.path.join(imagedir, "Thumbs.db")
    if os.path.isfile(thumbs_db):  # Remove WinXP thumbnail caches in dist dir
        os.remove(thumbs_db)
