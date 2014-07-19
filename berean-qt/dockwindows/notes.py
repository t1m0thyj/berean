"""notes.py - notes pane class"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDockWidget, QTextEdit


class NotesDockWindow(QDockWidget):
    def __init__(self):
        super(NotesDockWindow, self).__init__()
        self.textedit = QTextEdit()
        self.textedit.sizeHint = lambda: QSize(-1, 270)
        self.setWidget(self.textedit)
