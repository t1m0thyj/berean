"""search.py - search pane class"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDockWidget, QTextBrowser


class SearchDockWindow(QDockWidget):
    def __init__(self):
        super(SearchDockWindow, self).__init__()
        self.textbrowser = QTextBrowser()
        self.textbrowser.setHtml("<html><body>Hello world!</body></html>")
        self.textbrowser.sizeHint = lambda: QSize(300, -1)
        self.setWidget(self.textbrowser)
