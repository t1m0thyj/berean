"""build.py - build script for Berean on Windows

To build Berean you need the following dependencies:
    Python 2.6 or 2.7
    wxPython 2.9 or higher
    py2exe (0.6.9 recommended)

To build a tar.gz archive containing Berean source code, pass the command line
argument --build-source-tar to this script. You must have 7-Zip installed for
this to work.

To build a ZIP archive containing Berean built with py2exe, pass the argument
--build-zip. To build a portable version, pass the argument
--build-portable-zip. You must have 7-Zip installed for this to work.

To build an Inno Setup installer containing Berean built with py2exe, pass the
argument --build-installer. You must have Inno Setup installed for this to
work. You will also need to download Microsoft Visual C++ 2008 Redistributable
version 9.0.21022.8 (available at
http://www.microsoft.com/en-us/download/details.aspx?id=29) and put it in the
same directory where this script is.

By default, .po language files are compiled to .mo binary files if they have
not yet been converted. To disable this, pass the argument --no-compile-po.

Old builds are automatically moved to an archive subdirectory after the
specified builds have been completed. To disable this, pass the argument
--no-archive-old.

You will need to modify the path constants at the beginning of this script so
that they work on your computer.
"""

import glob
import os
import shutil
import subprocess
import sys

sys.path.append("src")
from settings import VERSION

_7ZIP_PATH = "C:\\Program Files\\7-Zip\\7z.exe"
INNO_SETUP_PATH = "C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"

if "--no-compile-po" not in sys.argv:
    os.chdir("src\\locale")
    subprocess.call("compile_po.py", shell=True)
    os.chdir("..\\..")

os.chdir("src")
subprocess.call("setup.py py2exe", shell=True)
os.chdir("..")

if "--build-source-tar" in sys.argv:
    tar_file = "releases\\Berean_%s_source.tar" % VERSION
    if os.path.isfile(tar_file + ".gz"):
        os.remove(tar_file + ".gz")
    subprocess.call([_7ZIP_PATH, "a", "-ttar", tar_file, "*.*", "src\\*.*", "src\\berean",
                     "src\\images", "src\\locale", "src\\locale\\*\\help", "src\\panes",
                     "src\\versions\\KJV.bbl", "src\\versions\\*\\*.py", "-x!.hg*",
                     "-x!vcredist_x86.exe", "-xr!*.pyc", "-x!src\\locale\\*\\LC_MESSAGES"])
    subprocess.call([_7ZIP_PATH, "a", "-tgzip", tar_file + ".gz", tar_file])
    os.remove(tar_file)


def build_zip(portable=False):
    if not portable:
        zip_file = "releases\\Berean_%s.zip" % VERSION
    else:
        zip_file = "releases\\Berean_%s_Portable.zip" % VERSION
    if os.path.isfile(zip_file):
        os.remove(zip_file)
    subprocess.call([_7ZIP_PATH, "a", zip_file, ".\\src\\dist\\*"])


if "--build-zip" in sys.argv:
    build_zip()

if "--build-portable-zip" in sys.argv:
    zip_file = "releases\\Berean_%s_Portable.zip" % VERSION
    if "--build-zip" in sys.argv:
        shutil.copy("releases\\Berean_%s.zip" % VERSION, zip_file)
    else:
        build_zip(True)
    with open("releases\\portable.ini", 'w'):
        pass
    subprocess.call([_7ZIP_PATH, "a", zip_file, ".\\releases\\portable.ini"])
    os.remove("releases\\portable.ini")

if "--build-installer" in sys.argv:
    with open("berean.iss", 'r') as fileobj:
        text = fileobj.read()
    with open("berean.iss", 'w') as fileobj2:
        index = text.index("#define MyAppVersion")
        fileobj2.write(text[:index] + "#define MyAppVersion \"%s\"" % VERSION +
                       text[text.index("\n", index):])
    subprocess.call([INNO_SETUP_PATH, "berean.iss"])

if "--no-archive-old" not in sys.argv:
    if not os.path.isdir("releases\\archive"):
        os.mkdir("releases\\archive")
    for pathname in ("Berean*.tar.gz", "Berean*[0-9].zip", "Berean*Portable.zip", "Berean*.exe"):
        filenames = sorted(glob.glob("releases\\%s" % pathname), key=os.path.getmtime)
        while len(filenames) > 2:
            filename = filenames.pop(0)
            os.rename(filename, "releases\\archive\\%s" % os.path.basename(filename))