"""tree.py - tree pane class"""

import wx

from info import *

_ = wx.GetTranslation

class TreePane(wx.TreeCtrl):
    def __init__(self, parent):
        super(TreePane, self).__init__(parent, -1, style=wx.TR_DEFAULT_STYLE |
            wx.BORDER_NONE | wx.TR_HIDE_ROOT)
        self._parent = parent

        self.skipevents = False

        root = self.AddRoot("")
        self.root_nodes = []
        for i in range(66):
            self.root_nodes.append(self.AppendItem(root, BOOK_NAMES[i]))
            if CHAPTER_LENGTHS > 1:
                self.SetItemHasChildren(self.root_nodes[-1], True)
        self.ExpandItem(parent.reference[0])

        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnItemExpanding)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

    def ExpandItem(self, book):
        item = self.root_nodes[book - 1]
        if (not self.GetChildrenCount(item)) and CHAPTER_LENGTHS[book - 1] > 1:
            for i in range(CHAPTER_LENGTHS[book - 1]):
                self.AppendItem(item, str(i + 1))
            self.Expand(item)

    def OnItemCollapsed(self, event):
        self.DeleteChildren(event.GetItem())

    def OnItemExpanding(self, event):
        item = event.GetItem()
        if not self.GetChildrenCount(item):
            self.ExpandItem(BOOK_NAMES.index(self.GetItemText(item)) + 1)

    def CollapseOtherItems(self, selected):
        for i in range(66):
            if i + 1 != selected and self.IsExpanded(self.root_nodes[i]):
                self.CollapseAndReset(self.root_nodes[i])

    def OnSelChanged(self, event):
        item = event.GetItem()
        if self.ItemHasChildren(item):
            self.ExpandItem(BOOK_NAMES.index(self.GetItemText(item)) + 1)
        else:
            parent = self.GetItemParent(item)
            if parent != self.GetRootItem():
                book = BOOK_NAMES.index(self.GetItemText(parent)) + 1
                chapter = int(self.GetItemText(item))
            else:
                book = BOOK_NAMES.index(self.GetItemText(item)) + 1
                chapter = 1
            self.CollapseOtherItems(book)
            if not self.skipevents:
                self._parent.LoadChapter(book, chapter)
