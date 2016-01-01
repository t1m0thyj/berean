"""tree.py - tree pane class"""

import wx

from config import BOOK_NAMES, BOOK_LENGTHS


class TreePane(wx.TreeCtrl):
    def __init__(self, parent):
        super(TreePane, self).__init__(parent, style=wx.TR_DEFAULT_STYLE | wx.BORDER_NONE |
                                       wx.TR_TWIST_BUTTONS | wx.TR_NO_LINES |
                                       wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_HIDE_ROOT)
        self._parent = parent

        root = self.AddRoot("")
        self.top_level_items = []
        for i in range(66):
            self.top_level_items.append(self.AppendItem(root, BOOK_NAMES[i]))
            if BOOK_LENGTHS[i] > 1:
                self.SetItemHasChildren(self.top_level_items[i], True)
        self.add_children(parent.reference[0], True)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnItemExpanding)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnWindowDestroy)

    def add_children(self, book, expand=False):
        item = self.top_level_items[book - 1]
        if (not self.GetChildrenCount(item)) and BOOK_LENGTHS[book - 1] > 1:
            for i in range(BOOK_LENGTHS[book - 1]):
                self.AppendItem(item, str(i + 1))
            if expand:
                self.Expand(item)

    def OnItemExpanding(self, event):
        self.add_children(self.top_level_items.index(event.GetItem()) + 1)

    def OnSelChanged(self, event):
        item = event.GetItem()
        if self.ItemHasChildren(item):
            self.add_children(self.top_level_items.index(event.GetItem()) + 1, True)
        else:
            parent = self.GetItemParent(item)
            if parent != self.GetRootItem():
                book = self.top_level_items.index(parent) + 1
                chapter = int(self.GetItemText(item))
            else:
                book = self.top_level_items.index(event.GetItem()) + 1
                chapter = 1
            for i in range(66):
                if self.IsExpanded(self.top_level_items[i]) and i + 1 != book:
                    self.Collapse(self.top_level_items[i])
            if not self.IsFrozen():
                self._parent.load_chapter(book, chapter)

    def OnWindowDestroy(self, event):
        self.Unbind(wx.EVT_TREE_SEL_CHANGED)  # Eliminate flicker
        event.Skip()

    def select_chapter(self, book, chapter):
        self.Freeze()
        if book != self._parent.reference[0]:
            self.add_children(book, True)
        if BOOK_LENGTHS[book - 1] > 1:
            item = self.top_level_items[book - 1]
            child, cookie = self.GetFirstChild(item)
            i = 1
            while i < chapter:
                child, cookie = self.GetNextChild(item, cookie)
                i += 1
            self.SelectItem(child)
            self.ScrollTo(child)
        else:
            self.SelectItem(self.top_level_items[book - 1])
            self.ScrollTo(self.top_level_items[book - 1])
        self.Thaw()
