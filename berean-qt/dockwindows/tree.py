"""tree.py - tree pane class"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem

from config import *


class TreeDockWindow(QDockWidget):
    def __init__(self):
        super(TreeDockWindow, self).__init__()
        self.treewidget = QTreeWidget()
        self.treewidget.setHeaderHidden(True)
        self.treewidget.sizeHint = lambda: QSize(150, -1)
        for i in range(66):
            item = QTreeWidgetItem(self.treewidget, [BOOK_NAMES[i]])
            if BOOK_LENGTHS[i] > 1:
                item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            self.treewidget.insertTopLevelItem(0, item)
        self.treewidget.itemActivated.connect(self.OnItemActivated)
        self.treewidget.itemCollapsed.connect(self.OnItemCollapsed)
        self.treewidget.itemExpanded.connect(self.OnItemExpanded)
        self.setWidget(self.treewidget)

    def add_children(self, book, expand=False):
        item = self.treewidget.topLevelItem(book - 1)
        if (not item.childCount()) and BOOK_LENGTHS[book - 1] > 1:
            for i in range(BOOK_LENGTHS[book - 1]):
                item.addChild(QTreeWidgetItem(item, [str(i + 1)]))
            if expand:
                item.setExpanded(True)

    def OnItemActivated(self, item, column):
        if item == 0 or item.childCount():
            return
        if self.treewidget.indexOfTopLevelItem(item) == -1:
            book = self.treewidget.indexOfTopLevelItem(item.parent()) + 1
            chapter = int(item.text(0))
        else:
            book = self.treewidget.indexOfTopLevelItem(item) + 1
            chapter = 1
        ##for i in range(66):
        ##    if self.IsExpanded(self.top_level_items[i]) and i + 1 != book:
        ##        self.Collapse(self.top_level_items[i])
        for i in range(self.parent().tabwidget.count()):
            webview = self.parent().tabwidget.widget(i)
            webview.setHtml(webview.get_html(book, chapter))

    def OnItemCollapsed(self, item):
        while item.childCount():
            item.removeChild(item.child(0))

    def OnItemExpanded(self, item):
        self.add_children(self.treewidget.indexOfTopLevelItem(item) + 1)
