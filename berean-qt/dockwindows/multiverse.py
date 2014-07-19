"""multiverse.py - multiverse pane class"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDockWidget, QTextBrowser


class MultiverseDockWindow(QDockWidget):
    def __init__(self):
        super(MultiverseDockWindow, self).__init__()
        self.textbrowser = QTextBrowser()
        self.textbrowser.setHtml("<html><body>Hello world!</body></html>")
        self.textbrowser.sizeHint = lambda: QSize(640, 400)
        self.setWidget(self.textbrowser)
