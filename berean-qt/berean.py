#!/usr/bin/env python
"""berean.py - main script for Berean
Copyright (C) 2014 Timothy Johnson <timothysw@objectmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os.path
import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

import mainwindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not hasattr(sys, "frozen"):
        app.cwd = os.path.dirname(__file__)
    else:
        app.cwd = os.path.dirname(sys.argv[0])
    splash = QSplashScreen(QPixmap(os.path.join(app.cwd, "images",
        "splash.png")))
    splash.show()
    app.processEvents()
    window = mainwindow.MainWindow(app)
    window.show()
    splash.finish(window)
    sys.exit(app.exec_())
