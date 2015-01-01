"""build.py - build script for Berean on Windows

To build Berean you need the following dependencies:
    Python 2.6 or 2.7
    wxPython 2.8 or higher (2.9 or higher recommended)
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

By default, old builds are moved to an archive subdirectory after the specified
builds have been completed. To disable this, pass the argument
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
from config import VERSION

_7ZIP_PATH = "C:\\Program Files\\7-Zip\\7z.exe"
INNO_SETUP_PATH = "C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"

os.chdir("src")
subprocess.call("setup.py py2exe", shell=True)
os.chdir("..")

if "--build-source-tar" in sys.argv:
    filename = "releases\\Berean_%s_source.tar" % VERSION
    if os.path.isfile(filename + ".gz"):
        os.remove(filename + ".gz")
    subprocess.call([_7ZIP_PATH, "a", "-ttar", filename, "src\\*.py"])
    for pathname in ("berean.iss", "berean-48.bmp", "build.py", "splash.xcf",
                     "src\\berean.pyw", "src\\images", "src\\license.txt",
                     "src\\locale", "src\\versions\\KJV.bbl"):
        subprocess.call([_7ZIP_PATH, "a", filename, pathname])
    subprocess.call([_7ZIP_PATH, "a", "-tgzip", filename + ".gz", filename])
    os.remove(filename)


def build_zip(portable=False):
    if not portable:
        filename = "releases\\Berean_%s.zip" % VERSION
    else:
        filename = "releases\\Berean_%s_Portable.zip" % VERSION
    if os.path.isfile(filename):
        os.remove(filename)
    subprocess.call([_7ZIP_PATH, "a", filename, ".\\src\\dist\\*"])


if "--build-zip" in sys.argv:
    build_zip()

if "--build-portable-zip" in sys.argv:
    filename = "releases\\Berean_%s_Portable.zip" % VERSION
    if "--build-zip" in sys.argv:
        shutil.copy("releases\\Berean_%s.zip" % VERSION, filename)
    else:
        build_zip(True)
    with open("releases\\portable.ini", 'w'):
        pass
    subprocess.call([_7ZIP_PATH, "a", filename, ".\\releases\\portable.ini"])
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
    for pathname in ("Berean*.tar.gz", "Berean*[0-9].zip",
                     "Berean*Portable.zip", "Berean*.exe"):
        filenames = sorted(glob.glob("releases\\%s" % pathname),
                           key=os.path.getmtime)
        while len(filenames) > 2:
            filename = filenames.pop(0)
            os.rename(filename,
                      "releases\\archive\\%s" % os.path.basename(filename))
