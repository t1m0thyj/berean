"""
setup.py - builds executable for Berean
Copyright (C) 2013 Timothy Johnson <timothysw@objectmail.com>
"""

import os
import shutil
from cx_Freeze import setup, Executable

_version = "1.4.6"
os.chdir(os.path.dirname(__file__))

includes = []
excludes = ["_gtkagg", "_tkagg", "bsddb", "curses", "email", "pywin.debugger",
			"pywin.debugger.dbgcon", "pywin.dialogs", "tcl",
			"Tkconstants", "Tkinter"]
packages = []
path = []

Target = Executable(script="berean.py",
					initScript=None,
					base="Win32GUI",
					targetName="berean.exe",
					compress=True,
					copyDependentFiles=True,
					appendScriptToExe=True,
					appendScriptToLibrary=False,
					icon="berean.ico")

if os.path.isdir("build\\exe.win32-2.7"):
	shutil.rmtree("build\\exe.win32-2.7")

setup(version=_version,
	  description="Berean",
	  author="Timothy Johnson",
	  name="Berean",
	  options={"build_exe":{"includes":includes,
							"excludes": excludes,
							"packages": packages,
							"path": path,
							"optimize": 2,
							"create_shared_zip": False}},
	  executables = [Target])

shutil.copytree("images", "build\\exe.win32-2.7\\images")
shutil.copytree("locale", "build\\exe.win32-2.7\\locale")
os.mkdir("build\\exe.win32-2.7\\versions")
shutil.copy2("versions\\KJV.bbl", "build\\exe.win32-2.7\\versions")
shutil.copy2("versions\\YLT.bbl", "build\\exe.win32-2.7\\versions")
shutil.copy2("license.txt", "build\\exe.win32-2.7")
shutil.copy2("build\\berean.manifest", "build\\exe.win32-2.7")