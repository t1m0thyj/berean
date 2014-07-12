"""setup.py - builds py2exe executable for Berean"""

import glob
import os
import shutil

from distutils.core import setup
import py2exe

from config import VERSION

os.chdir(os.path.dirname(__file__))
manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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

if os.path.isdir("dist"):
    shutil.rmtree("dist")
excludes = ["_gtkagg", "_tkagg", "bsddb", "curses", "email", "pywin.debugger",
    "pywin.debugger.dbgcon", "pywin.dialogs", "tcl", "Tkconstants", "Tkinter"]
dll_excludes = ["libgdk-win32-2.0-0.dll", "libgobject-2.0-0.dll", "tcl85.dll",
    "tk85.dll", "msvcr80.dll", "UxTheme.dll", "msvcp90.dll", "w9xpopen.exe"]
setup(options={"py2exe": {"compressed": 1,
		"optimize": 2,
        "bundle_files": 3,
        "excludes": excludes,
        "dll_excludes": dll_excludes}},
    windows=[{"script": "berean.py",
		"name": "Berean",
		"version": VERSION,
		"company_name": "Timothy Johnson",
		"copyright": "Copyright \xa9 2011-2014 Timothy Johnson",
		"description": "Berean",
		"icon_resources": [(1, "images\\berean.ico")],
		"other_resources": [(24, 1, manifest)]}],
    data_files=[("images", glob.glob("images\\*.*")),
        ("images\\flags", glob.glob("images\\flags\\*.*")),
        ("locale\\en_US\\help", glob.glob("locale\\en_US\\help\\*.*")),
        ("versions", ["versions\\KJV.bbl"]),
        ("", ["license.txt"])],
	zipfile=None)
if os.path.isdir("build"):
    shutil.rmtree("build")
