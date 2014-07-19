"""toolbar.py - toolbar classes"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QAction, QComboBox, QSlider, QToolBar


class ToolBar(QToolBar):
    def __init__(self, parent):
        super(QToolBar, self).__init__()
        self.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea)
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.verse_entry = QComboBox()
        self.verse_entry.setEditable(True)
        self.verse_entry.setMinimumWidth(150)
        self.verse_entry.lineEdit().setText("Genesis 1")
        self.addWidget(self.verse_entry)
        parent.action_go_to_verse.setPriority(QAction.LowPriority)
        self.addAction(parent.action_go_to_verse)
        self.addSeparator()
        self.addAction(parent.action_go_back)
        self.addAction(parent.action_go_forward)
        self.addSeparator()
        parent.action_print.setPriority(QAction.LowPriority)
        self.addAction(parent.action_print)
        parent.action_copy.setPriority(QAction.LowPriority)
        self.addAction(parent.action_copy)
        self.addSeparator()
        parent.action_add_to_favorites.setPriority(QAction.LowPriority)
        self.addAction(parent.action_add_to_favorites)
        parent.action_manage_favorites.setPriority(QAction.LowPriority)
        self.addAction(parent.action_manage_favorites)


class ZoomBar(QToolBar):
    def __init__(self, parent):
        super(QToolBar, self).__init__()
        self.setIconSize(QSize(16, 16))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.addAction(parent.action_zoom_in)
        self.slider = QSlider(Qt.Horizontal)
        self.addWidget(self.slider)
        self.addAction(parent.action_zoom_out)

